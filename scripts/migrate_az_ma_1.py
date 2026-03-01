"""
AZ-MA-1 Migration Script -- DO (DigitalOcean) -> Oracle OSH
===========================================================
Migrates the complete AZ-MA-1 resource tree from the DO development
server to the Oracle production SensorHub:

  Phase 1: POST 9 procedures  (GeoJSON)
  Phase 2: POST AZ-MA-1 top-level system  (SensorML)
  Phase 3: POST 13 subsystems as nested members  (SensorML)
  Phase 4: POST 7 datastreams under correct parent systems  (JSON)
  Phase 5: POST 4 control streams under actuator subsystem  (JSON)
  Phase 6: POST ~7,465 observations in batches  (JSON)
  Phase 7: Link AZ-MA-1 to String Alpha deployment  (dual-write PUT)

Prerequisites:
  - Oracle OSH has v2.5 bootstrap resources (deployments, etc.)
  - Backup data in scripts/migration_backup/ (procedures, datastreams,
    controlstreams, observations, system SensorML files)

Usage:
  python scripts/migrate_az_ma_1.py [--dry-run] [--skip-obs]

Options:
  --dry-run    Validate without writing to Oracle
  --skip-obs   Skip Phase 6 (observation bulk ingest)

Source: http://45.55.99.236:8080/sensorhub/api  (DO, auth ogc:ogc)
Target: https://os4csapi-osh.duckdns.org/sensorhub/api  (Oracle, auth os4csapi:ogc134mm)
"""

import json
import sys
import os
import time
import socket
import urllib.request
import urllib.error
import base64
import ssl

# ── Configuration ─────────────────────────────────────────────────────
ORACLE_BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
ORACLE_AUTH = base64.b64encode(b"os4csapi:ogc134mm").decode()
ORACLE_IP = "129.80.248.53"  # Direct IP when DuckDNS is flaky

DO_BASE = "http://45.55.99.236:8080/sensorhub/api"
DO_AUTH = base64.b64encode(b"ogc:ogc").decode()

DRY_RUN = "--dry-run" in sys.argv
SKIP_OBS = "--skip-obs" in sys.argv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(SCRIPT_DIR, "migration_backup")

# SSL context that trusts the Oracle cert
SSL_CTX = ssl.create_default_context()

# ── Process-level DNS override (acts like a hosts-file entry) ─────────
# DuckDNS resolution is unreliable; resolve the hostname to the known IP
# directly inside this process.  SNI and cert validation still use the
# hostname, so TLS works correctly.
_orig_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == "os4csapi-osh.duckdns.org":
        return _orig_getaddrinfo(ORACLE_IP, port, family, type, proto, flags)
    return _orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _patched_getaddrinfo

# ── Tee stdout to a log file so output is captured regardless of shell ─
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migration_log.txt")
class _Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()
    def flush(self):
        for s in self.streams:
            s.flush()

_log_file = open(LOG_PATH, "w", encoding="utf-8")
sys.stdout = _Tee(sys.__stdout__, _log_file)
sys.stderr = _Tee(sys.__stderr__, _log_file)

# ── Tracking ──────────────────────────────────────────────────────────
created = []
skipped = []
failed = []
id_map_do_to_oracle = {}  # DO_id -> Oracle_id

# ── Subsystem order (parent -> child nesting) ─────────────────────────
# These are the 13 subsystems in the order they should be posted
# as members of the AZ-MA-1 system (id 04ng on DO).
SUBSYSTEM_FILES = [
    "AZ-MA-1_Tripod_Platform_sml.json",  # 04p0
    "AZ-MA-1_MICARRAY_sml.json",          # 04pg
    "AZ-MA-1_EDGE_sml.json",              # 04q0
    "AZ-MA-1_COMMS_sml.json",             # 04qg
    "AZ-MA-1_POWER_sml.json",             # 04r0
    "AZ-MA-1_ACTUATOR_sml.json",          # 04rg
    "AZ-MA-1_MIC1_sml.json",              # 04s0
    "AZ-MA-1_MIC2_sml.json",              # 04sg
    "AZ-MA-1_MIC3_sml.json",              # 04t0
    "AZ-MA-1_MIC4_sml.json",              # 04tg
    "AZ-MA-1_MIC5_sml.json",              # 04u0
    "AZ-MA-1_MIC6_sml.json",              # 04ug
    "AZ-MA-1_MIC7_sml.json",              # 04v0
]

# Map subsystem short-names to their DO ids (from new_id_map.json)
SUBSYSTEM_DO_IDS = {
    "AZ-MA-1_Tripod_Platform_sml.json": "04p0",
    "AZ-MA-1_MICARRAY_sml.json": "04pg",
    "AZ-MA-1_EDGE_sml.json": "04q0",
    "AZ-MA-1_COMMS_sml.json": "04qg",
    "AZ-MA-1_POWER_sml.json": "04r0",
    "AZ-MA-1_ACTUATOR_sml.json": "04rg",
    "AZ-MA-1_MIC1_sml.json": "04s0",
    "AZ-MA-1_MIC2_sml.json": "04sg",
    "AZ-MA-1_MIC3_sml.json": "04t0",
    "AZ-MA-1_MIC4_sml.json": "04tg",
    "AZ-MA-1_MIC5_sml.json": "04u0",
    "AZ-MA-1_MIC6_sml.json": "04ug",
    "AZ-MA-1_MIC7_sml.json": "04v0",
}

# Procedure files (in procedures/ subdir)
PROCEDURE_FILES = [
    "proc_0480.json",
    "proc_048g.json",
    "proc_0490.json",
    "proc_049g.json",
    "proc_04a0.json",
    "proc_04b0.json",
    "proc_04bg.json",
    "proc_04c0.json",
    "proc_04cg.json",
]

# Datastream files and their parent system UIDs
# All 7 datastreams belong to parent system AZ-MA-1 (urn:os4csapi:system:odas:az-ma-1)
DATASTREAM_FILES = [
    "ds_07fg2.json",
    "ds_07g02.json",
    "ds_07gg2.json",
    "ds_07h02.json",
    "ds_07hg2.json",
    "ds_07i02.json",
    "ds_07ig2.json",
]
DS_PARENT_UID = "urn:os4csapi:system:odas:az-ma-1"

# Control streams -- all belong to ACTUATOR subsystem
CS_FILES = [
    "cs_04d0.json",
    "cs_04dg.json",
    "cs_04e0.json",
    "cs_04eg.json",
]
CS_PARENT_UID = "urn:os4csapi:system:odas:az-ma-1:actuator"

# Observations -- only 4 datastreams have observations
OBS_FILES = [
    "obs_07h02.json",   # Track Updates      -- 1,864 obs
    "obs_07hg2.json",   # Classification      -- 1,868 obs
    "obs_07i02.json",   # Health             -- 1,867 obs
    "obs_07ig2.json",   # Scene Summary      -- 1,866 obs
]

# Procedure DO-ID -> Oracle procedure mapping
# These will be populated dynamically during Phase 1.
PROC_DO_TO_ORACLE = {}

# Deployment UID for String Alpha (already exists on Oracle from bootstrap)
STRING_ALPHA_UID = "urn:os4csapi:deployment:string:ft-huachuca:001"

# ── Observation batch size ────────────────────────────────────────────
OBS_BATCH_SIZE = 50  # POST observations in batches of 50

# ══════════════════════════════════════════════════════════════════════
#  API HELPERS
# ══════════════════════════════════════════════════════════════════════

def reorder_type_first(obj):
    """Recursively ensure 'type' is the first key in all dicts (OSH SensorML quirk)."""
    if isinstance(obj, dict):
        result = {}
        if "type" in obj:
            result["type"] = reorder_type_first(obj["type"])
        for k, v in obj.items():
            if k != "type":
                result[k] = reorder_type_first(v)
        return result
    elif isinstance(obj, list):
        return [reorder_type_first(item) for item in obj]
    return obj


MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 15]  # seconds between retries


def oracle_api(method, path, body=None, content_type="application/geo+json"):
    """Call Oracle OSH API with retry on connection errors.

    Returns (status, data|error_text).
    Retries up to MAX_RETRIES times on connection/timeout errors.
    """
    url = f"{ORACLE_BASE}/{path}" if not path.startswith("http") else path
    data_bytes = json.dumps(body).encode() if body else None

    for attempt in range(MAX_RETRIES + 1):
        req = urllib.request.Request(url, data=data_bytes, method=method)
        req.add_header("Authorization", f"Basic {ORACLE_AUTH}")
        req.add_header("Accept", "application/json")
        if body:
            req.add_header("Content-Type", content_type)

        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(
            NoRedirectHandler,
            urllib.request.HTTPSHandler(context=SSL_CTX)
        )

        try:
            resp = opener.open(req, timeout=30)
            status = resp.status
            loc = resp.headers.get("Location", "")
            if loc and status in (201,):
                rid = loc.rstrip("/").split("/")[-1]
                return status, {"id": rid, "Location": loc}
            try:
                rdata = json.loads(resp.read())
            except Exception:
                rdata = None
            return status, rdata
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode()[:500]
            except Exception:
                pass
            if e.code == 302:
                loc = e.headers.get("Location", "")
                return 302, f"REDIRECT -> {loc} (payload rejected)"
            return e.code, body_text
        except (urllib.error.URLError, TimeoutError, OSError, ConnectionError) as e:
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[attempt]
                print(f"    RETRY ({attempt+1}/{MAX_RETRIES}): connection error, waiting {wait}s: {e}")
                time.sleep(wait)
            else:
                return 0, f"CONNECTION_ERROR after {MAX_RETRIES} retries: {e}"


def find_on_oracle(collection, uid):
    """Search Oracle for existing resource by UID."""
    status, data = oracle_api("GET", f"{collection}?uid={uid}&limit=1")
    if status == 200 and isinstance(data, dict):
        items = data.get("items", [])
        if items:
            return items[0]
    return None


def find_deployment_recursive(uid, path="deployments"):
    """Recursively search the deployment tree for a UID.

    The OSH /deployments endpoint only returns top-level deployments.
    Sub-deployments live under deployments/{id}/subdeployments, so we
    must walk the tree.
    """
    status, data = oracle_api("GET", path)
    if status != 200 or not isinstance(data, dict):
        return None
    for item in data.get("items", []):
        item_uid = item.get("properties", {}).get("uid", "")
        if item_uid == uid:
            return item
        # Recurse into subdeployments
        dep_id = item.get("id", "")
        if dep_id:
            found = find_deployment_recursive(uid, f"deployments/{dep_id}/subdeployments")
            if found:
                return found
    return None


def find_nested_on_oracle(parent_collection, parent_id, child_collection, uid):
    """Search Oracle for nested resource by UID."""
    path = f"{parent_collection}/{parent_id}/{child_collection}"
    status, data = oracle_api("GET", path)
    if status == 200 and isinstance(data, dict):
        for item in data.get("items", []):
            item_uid = ""
            if "properties" in item:
                item_uid = item["properties"].get("uid", "")
            elif "uniqueId" in item:
                item_uid = item.get("uniqueId", "")
            if item_uid == uid:
                return item
    return None


def load_backup(subdir, filename):
    """Load a JSON backup file."""
    path = os.path.join(BACKUP_DIR, subdir, filename) if subdir else os.path.join(BACKUP_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_server_fields(obj):
    """Remove server-generated fields that shouldn't be in a POST payload."""
    if isinstance(obj, dict):
        # Remove fields that are generated server-side
        for key in ["id", "links", "system@id", "system@link",
                     "phenomenonTime", "resultTime", "formats"]:
            obj.pop(key, None)
        # Recursively process nested dicts
        for k, v in obj.items():
            strip_server_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            strip_server_fields(item)
    return obj


def strip_self_links(obj):
    """Remove only self/canonical links from link arrays.
    Keep cross-reference links (procedure@link, deployment@link, etc.)."""
    if isinstance(obj, dict):
        if "links" in obj and isinstance(obj["links"], list):
            obj["links"] = [
                link for link in obj["links"]
                if link.get("rel") not in ("canonical", "alternate", "self",
                                            "system", "observations", "commands",
                                            "schema")
            ]
            if not obj["links"]:
                del obj["links"]
    return obj


# ══════════════════════════════════════════════════════════════════════
#  PHASE 1: MIGRATE PROCEDURES
# ══════════════════════════════════════════════════════════════════════
def phase1_procedures():
    print("\n" + "=" * 70)
    print("PHASE 1: Migrate 9 Procedures (GeoJSON)")
    print("=" * 70)

    for fname in PROCEDURE_FILES:
        proc = load_backup("procedures", fname)
        do_id = proc.get("id", fname.replace("proc_", "").replace(".json", ""))
        uid = proc.get("properties", {}).get("uid", "")
        label = proc.get("properties", {}).get("name", fname)

        # Check if already exists on Oracle
        existing = find_on_oracle("procedures", uid)
        if existing:
            oracle_id = existing.get("id", "?")
            print(f"  SKIP {label} -- already exists (oracle id={oracle_id})")
            skipped.append(f"proc:{label}")
            id_map_do_to_oracle[f"proc_{do_id}"] = oracle_id
            PROC_DO_TO_ORACLE[do_id] = oracle_id
            continue

        # Strip server-generated fields
        payload = {
            "type": "Feature",
            "geometry": proc.get("geometry"),
            "properties": {
                k: v for k, v in proc.get("properties", {}).items()
            }
        }
        # Remove DO-specific links
        payload.get("properties", {}).pop("links", None)

        if DRY_RUN:
            print(f"  DRY-RUN: would POST procedure: {label}")
            id_map_do_to_oracle[f"proc_{do_id}"] = "DRY"
            PROC_DO_TO_ORACLE[do_id] = "DRY"
            continue

        status, data = oracle_api("POST", "procedures", payload)
        if status in (200, 201):
            oracle_id = data.get("id", "") if isinstance(data, dict) else ""
            print(f"  CREATE {label} -> HTTP {status} (oracle id={oracle_id})")
            created.append(f"proc:{label}")
            id_map_do_to_oracle[f"proc_{do_id}"] = oracle_id
            PROC_DO_TO_ORACLE[do_id] = oracle_id
        else:
            print(f"  FAIL {label} -> HTTP {status}: {data}")
            failed.append(f"proc:{label} -> HTTP {status}")


# ══════════════════════════════════════════════════════════════════════
#  PHASE 2: MIGRATE AZ-MA-1 TOP-LEVEL SYSTEM
# ══════════════════════════════════════════════════════════════════════
def phase2_toplevel_system():
    print("\n" + "=" * 70)
    print("PHASE 2: Migrate AZ-MA-1 Top-Level System (SensorML)")
    print("=" * 70)

    sml = load_backup(None, "AZ-MA-1_sml.json")
    uid = sml.get("uniqueId", "")
    label = sml.get("label", "AZ-MA-1")
    do_id = sml.get("id", "04ng")

    existing = find_on_oracle("systems", uid)
    if existing:
        oracle_id = existing.get("id", "?")
        print(f"  SKIP {label} -- already exists (oracle id={oracle_id})")
        skipped.append(f"sys:{label}")
        id_map_do_to_oracle[f"sys_{do_id}"] = oracle_id
        return oracle_id

    # Build POST payload -- strip server 'id' field
    payload = reorder_type_first(sml)
    payload.pop("id", None)

    if DRY_RUN:
        print(f"  DRY-RUN: would POST system: {label}")
        id_map_do_to_oracle[f"sys_{do_id}"] = "DRY"
        return "DRY"

    status, data = oracle_api("POST", "systems", payload, content_type="application/sml+json")
    if status in (200, 201):
        oracle_id = data.get("id", "") if isinstance(data, dict) else ""
        print(f"  CREATE {label} -> HTTP {status} (oracle id={oracle_id})")
        created.append(f"sys:{label}")
        id_map_do_to_oracle[f"sys_{do_id}"] = oracle_id
        return oracle_id
    else:
        print(f"  FAIL {label} -> HTTP {status}: {data}")
        failed.append(f"sys:{label} -> HTTP {status}")
        return None


# ══════════════════════════════════════════════════════════════════════
#  PHASE 3: MIGRATE 13 SUBSYSTEMS AS NESTED MEMBERS
# ══════════════════════════════════════════════════════════════════════
def phase3_subsystems(parent_oracle_id):
    print("\n" + "=" * 70)
    print("PHASE 3: Migrate 13 Subsystems as Nested Members (SensorML)")
    print("=" * 70)

    if not parent_oracle_id or parent_oracle_id == "DRY":
        # If parent wasn't created, try to find it
        existing = find_on_oracle("systems", "urn:os4csapi:system:odas:az-ma-1")
        if existing:
            parent_oracle_id = existing.get("id")
        elif DRY_RUN:
            # In dry-run mode, show what we would do
            for fn in SUBSYSTEM_FILES:
                s = load_backup(None, fn)
                print(f"  DRY-RUN: would POST subsystem: {s.get('label', fn)} -> systems/<parent>/members")
                did = SUBSYSTEM_DO_IDS.get(fn, s.get('id', ''))
                id_map_do_to_oracle[f"sys_{did}"] = "DRY"
            return
        else:
            print("  ABORT -- parent AZ-MA-1 system not found on Oracle")
            return

    for fname in SUBSYSTEM_FILES:
        sml = load_backup(None, fname)
        uid = sml.get("uniqueId", "")
        label = sml.get("label", fname)
        do_id = SUBSYSTEM_DO_IDS.get(fname, sml.get("id", ""))

        # Check if already nested under parent
        existing = find_nested_on_oracle("systems", parent_oracle_id, "members", uid)
        if existing:
            oracle_id = existing.get("id", "?")
            print(f"  SKIP {label} -- already nested (oracle id={oracle_id})")
            skipped.append(f"sub:{label}")
            id_map_do_to_oracle[f"sys_{do_id}"] = oracle_id
            continue

        payload = reorder_type_first(sml)
        payload.pop("id", None)

        if DRY_RUN:
            print(f"  DRY-RUN: would POST subsystem: {label} -> systems/{parent_oracle_id}/members")
            id_map_do_to_oracle[f"sys_{do_id}"] = "DRY"
            continue

        path = f"systems/{parent_oracle_id}/members"
        status, data = oracle_api("POST", path, payload, content_type="application/sml+json")
        if status in (200, 201):
            oracle_id = data.get("id", "") if isinstance(data, dict) else ""
            print(f"  CREATE {label} -> HTTP {status} (oracle id={oracle_id})")
            created.append(f"sub:{label}")
            id_map_do_to_oracle[f"sys_{do_id}"] = oracle_id
        else:
            print(f"  FAIL {label} -> HTTP {status}: {data}")
            failed.append(f"sub:{label} -> HTTP {status}")
            # Retry with fallback content-type
            if status == 400:
                print(f"    Retrying with application/json ...")
                status2, data2 = oracle_api("POST", path, payload, content_type="application/json")
                if status2 in (200, 201):
                    oracle_id = data2.get("id", "") if isinstance(data2, dict) else ""
                    print(f"    RETRY OK {label} -> HTTP {status2} (oracle id={oracle_id})")
                    created.append(f"sub:{label} (retry)")
                    failed.pop()  # Remove the earlier failure
                    id_map_do_to_oracle[f"sys_{do_id}"] = oracle_id


# ══════════════════════════════════════════════════════════════════════
#  PHASE 4: MIGRATE 7 DATASTREAMS
# ══════════════════════════════════════════════════════════════════════
def phase4_datastreams():
    print("\n" + "=" * 70)
    print("PHASE 4: Migrate 7 Datastreams (JSON)")
    print("=" * 70)

    # Find the AZ-MA-1 system on Oracle
    parent = find_on_oracle("systems", DS_PARENT_UID)
    if not parent:
        if DRY_RUN:
            for fn in DATASTREAM_FILES:
                d = load_backup("datastreams", fn)
                print(f"  DRY-RUN: would POST datastream: {d.get('name', fn)} -> systems/<parent>/datastreams")
                did = d.get('id', '')
                id_map_do_to_oracle[f"ds_{did}"] = "DRY"
            return
        print("  ABORT -- parent system AZ-MA-1 not found on Oracle")
        return
    parent_id = parent.get("id")
    print(f"  Parent system AZ-MA-1 on Oracle: id={parent_id}")

    for fname in DATASTREAM_FILES:
        ds = load_backup("datastreams", fname)
        do_id = ds.get("id", "")
        ds_name = ds.get("name", "")
        output_name = ds.get("outputName", "")
        label = ds_name or fname

        # Check if already exists under parent
        existing_path = f"systems/{parent_id}/datastreams?limit=50"
        status, data = oracle_api("GET", existing_path)
        already_exists = False
        if status == 200 and isinstance(data, dict):
            for existing_ds in data.get("items", []):
                if existing_ds.get("outputName") == output_name or existing_ds.get("name") == ds_name:
                    oracle_ds_id = existing_ds.get("id", "?")
                    print(f"  SKIP {label} -- already exists (oracle id={oracle_ds_id})")
                    skipped.append(f"ds:{label}")
                    id_map_do_to_oracle[f"ds_{do_id}"] = oracle_ds_id
                    already_exists = True
                    break
        if already_exists:
            continue

        # Load the schema for this datastream
        schema_fname = f"schema_{do_id}.json"
        try:
            schema = load_backup("datastreams", schema_fname)
        except FileNotFoundError:
            print(f"  WARN: no schema file for {label}, posting without schema")
            schema = None

        # Build the POST payload
        # Key fields: name, outputName, schema (obsFormat + resultSchema)
        payload = {
            "name": ds_name,
            "outputName": output_name,
        }

        # Add optional fields
        if ds.get("description"):
            payload["description"] = ds["description"]
        if ds.get("validTime"):
            payload["validTime"] = ds["validTime"]
        if ds.get("observedProperties"):
            payload["observedProperties"] = ds["observedProperties"]

        # Re-map cross-reference links using Oracle IDs
        # procedure@link -- remap DO procedure ID to Oracle
        if ds.get("procedure@link"):
            proc_href = ds["procedure@link"].get("href", "")
            do_proc_id = proc_href.rstrip("/").split("/")[-1]
            oracle_proc_id = PROC_DO_TO_ORACLE.get(do_proc_id)
            if oracle_proc_id and oracle_proc_id != "DRY":
                payload["procedure@link"] = {
                    "href": f"/sensorhub/api/procedures/{oracle_proc_id}",
                    "title": ds["procedure@link"].get("title", ""),
                    "type": "application/geo+json"
                }

        # deployment@link -- find String Alpha on Oracle and use leaf deployment
        # The DO server used AZ-DEP-AZ-MA-1 (a deployment specific to AZ-MA-1).
        # On Oracle, AZ-MA-1 doesn't have its own deployment yet.
        # We'll link to String Alpha which is the parent deployment context.
        string_dep = find_deployment_recursive(STRING_ALPHA_UID)
        if string_dep:
            dep_id = string_dep.get("id", "")
            payload["deployment@link"] = {
                "href": f"/sensorhub/api/deployments/{dep_id}",
                "title": "Sensor String Alpha",
                "type": "application/geo+json"
            }

        # Schema must be included for datastream creation
        if schema:
            payload["schema"] = reorder_type_first(schema)

        if DRY_RUN:
            print(f"  DRY-RUN: would POST datastream: {label} -> systems/{parent_id}/datastreams")
            id_map_do_to_oracle[f"ds_{do_id}"] = "DRY"
            continue

        path = f"systems/{parent_id}/datastreams"
        status, data = oracle_api("POST", path, reorder_type_first(payload), content_type="application/json")
        if status in (200, 201):
            oracle_id = data.get("id", "") if isinstance(data, dict) else ""
            print(f"  CREATE {label} -> HTTP {status} (oracle id={oracle_id})")
            created.append(f"ds:{label}")
            id_map_do_to_oracle[f"ds_{do_id}"] = oracle_id
        else:
            print(f"  FAIL {label} -> HTTP {status}: {data}")
            failed.append(f"ds:{label} -> HTTP {status}")


# ══════════════════════════════════════════════════════════════════════
#  PHASE 5: MIGRATE 4 CONTROL STREAMS
# ══════════════════════════════════════════════════════════════════════
def phase5_controlstreams():
    print("\n" + "=" * 70)
    print("PHASE 5: Migrate 4 Control Streams (JSON)")
    print("=" * 70)

    # Find the ACTUATOR subsystem on Oracle
    parent = find_on_oracle("systems", CS_PARENT_UID)
    if not parent:
        if DRY_RUN:
            for fn in CS_FILES:
                c = load_backup("controlstreams", fn)
                print(f"  DRY-RUN: would POST controlstream: {c.get('name', fn)} -> systems/<parent>/controlstreams")
                cid = c.get('id', '')
                id_map_do_to_oracle[f"cs_{cid}"] = "DRY"
            return
        print("  ABORT -- parent system ACTUATOR not found on Oracle")
        return
    parent_id = parent.get("id")
    print(f"  Parent system ACTUATOR on Oracle: id={parent_id}")

    for fname in CS_FILES:
        cs = load_backup("controlstreams", fname)
        do_id = cs.get("id", "")
        cs_name = cs.get("name", "")
        input_name = cs.get("inputName", "")
        label = cs_name or fname

        # Check if already exists under parent
        existing_path = f"systems/{parent_id}/controlstreams?limit=50"
        status, data = oracle_api("GET", existing_path)
        already_exists = False
        if status == 200 and isinstance(data, dict):
            for existing_cs in data.get("items", []):
                if existing_cs.get("inputName") == input_name or existing_cs.get("name") == cs_name:
                    oracle_cs_id = existing_cs.get("id", "?")
                    print(f"  SKIP {label} -- already exists (oracle id={oracle_cs_id})")
                    skipped.append(f"cs:{label}")
                    id_map_do_to_oracle[f"cs_{do_id}"] = oracle_cs_id
                    already_exists = True
                    break
        if already_exists:
            continue

        # Load the schema
        schema_fname = f"schema_{do_id}.json"
        try:
            schema = load_backup("controlstreams", schema_fname)
        except FileNotFoundError:
            schema = None

        # Build POST payload
        payload = {
            "name": cs_name,
            "inputName": input_name,
        }
        if cs.get("validTime"):
            payload["validTime"] = cs["validTime"]
        if cs.get("controlledProperties"):
            payload["controlledProperties"] = cs["controlledProperties"]
        if schema:
            payload["schema"] = reorder_type_first(schema)

        if DRY_RUN:
            print(f"  DRY-RUN: would POST controlstream: {label} -> systems/{parent_id}/controlstreams")
            id_map_do_to_oracle[f"cs_{do_id}"] = "DRY"
            continue

        path = f"systems/{parent_id}/controlstreams"
        status, data = oracle_api("POST", path, reorder_type_first(payload), content_type="application/json")
        if status in (200, 201):
            oracle_id = data.get("id", "") if isinstance(data, dict) else ""
            print(f"  CREATE {label} -> HTTP {status} (oracle id={oracle_id})")
            created.append(f"cs:{label}")
            id_map_do_to_oracle[f"cs_{do_id}"] = oracle_id
        else:
            print(f"  FAIL {label} -> HTTP {status}: {data}")
            failed.append(f"cs:{label} -> HTTP {status}")


# ══════════════════════════════════════════════════════════════════════
#  PHASE 6: MIGRATE OBSERVATIONS (Bulk)
# ══════════════════════════════════════════════════════════════════════
def phase6_observations():
    print("\n" + "=" * 70)
    print("PHASE 6: Migrate ~7,465 Observations in Batches")
    print("=" * 70)

    if SKIP_OBS:
        print("  SKIPPED (--skip-obs flag)")
        return

    total_posted = 0
    total_failed = 0

    for obs_fname in OBS_FILES:
        # Extract DO datastream ID from filename
        do_ds_id = obs_fname.replace("obs_", "").replace(".json", "")
        oracle_ds_id = id_map_do_to_oracle.get(f"ds_{do_ds_id}")

        if not oracle_ds_id or oracle_ds_id == "DRY":
            # Try to find datastream on Oracle by looking up name
            ds_meta = load_backup("datastreams", f"ds_{do_ds_id}.json")
            ds_name = ds_meta.get("name", "")
            # Find parent system, then find datastream
            parent = find_on_oracle("systems", DS_PARENT_UID)
            if parent:
                parent_id = parent.get("id")
                st, ddata = oracle_api("GET", f"systems/{parent_id}/datastreams?limit=50")
                if st == 200 and isinstance(ddata, dict):
                    for d in ddata.get("items", []):
                        if d.get("name") == ds_name:
                            oracle_ds_id = d.get("id")
                            break

        if not oracle_ds_id or oracle_ds_id == "DRY":
            print(f"  SKIP obs for DO ds {do_ds_id} -- Oracle datastream not found")
            continue

        # Load observations
        obs_data = load_backup("observations", obs_fname)
        items = obs_data.get("items", [])
        print(f"\n  Datastream {do_ds_id} -> Oracle {oracle_ds_id}: {len(items)} observations")

        if DRY_RUN:
            print(f"    DRY-RUN: would POST {len(items)} observations")
            continue

        # Check if there are already observations on Oracle for this datastream
        st, existing_obs = oracle_api("GET", f"datastreams/{oracle_ds_id}/observations?limit=1")
        if st == 200 and isinstance(existing_obs, dict):
            existing_count = len(existing_obs.get("items", []))
            if existing_count > 0:
                print(f"    WARN: Oracle datastream already has observations -- posting anyway (idempotent by phenomenonTime)")

        # POST observations one at a time (OSH doesn't support batch POST for observations)
        batch_ok = 0
        batch_fail = 0
        path = f"datastreams/{oracle_ds_id}/observations"

        for i, obs in enumerate(items):
            # Strip server-generated fields from observation
            obs_payload = {
                "phenomenonTime": obs.get("phenomenonTime"),
                "resultTime": obs.get("resultTime"),
                "result": obs.get("result"),
            }
            # Include optional fields
            if obs.get("featureOfInterest@id"):
                obs_payload["featureOfInterest@id"] = obs["featureOfInterest@id"]

            status, data = oracle_api("POST", path, obs_payload, content_type="application/json")
            if status in (200, 201):
                batch_ok += 1
            else:
                batch_fail += 1
                if batch_fail <= 3:
                    print(f"    FAIL obs [{i}] -> HTTP {status}: {str(data)[:100]}")
                elif batch_fail == 4:
                    print(f"    ... suppressing further failure messages")

            # Progress indicator
            if (i + 1) % 500 == 0:
                print(f"    Progress: {i+1}/{len(items)} (ok={batch_ok}, fail={batch_fail})")

            # Throttle to avoid overwhelming the server
            # 50ms per request + 2s pause every 200 requests
            time.sleep(0.05)
            if (i + 1) % 200 == 0:
                time.sleep(2)

        print(f"    Done: {batch_ok} created, {batch_fail} failed")
        total_posted += batch_ok
        total_failed += batch_fail
        created.append(f"obs:{do_ds_id} ({batch_ok} observations)")
        if batch_fail > 0:
            failed.append(f"obs:{do_ds_id} ({batch_fail} failures)")

    print(f"\n  TOTAL observations: {total_posted} created, {total_failed} failed")


# ══════════════════════════════════════════════════════════════════════
#  PHASE 7: LINK AZ-MA-1 TO STRING ALPHA DEPLOYMENT (Dual-Write)
# ══════════════════════════════════════════════════════════════════════
def phase7_deployment_link():
    print("\n" + "=" * 70)
    print("PHASE 7: Link AZ-MA-1 -> String Alpha Deployment (dual-write)")
    print("=" * 70)

    # Find String Alpha deployment on Oracle
    string_dep = find_deployment_recursive(STRING_ALPHA_UID)
    if not string_dep:
        if DRY_RUN:
            print("  DRY-RUN: would PUT deployment String Alpha with dual-write links")
            return
        print("  ABORT -- String Alpha deployment not found on Oracle")
        return

    dep_id = string_dep.get("id")
    print(f"  String Alpha deployment: id={dep_id}")

    # Find AZ-MA-1 system on Oracle
    az_system = find_on_oracle("systems", DS_PARENT_UID)
    if not az_system:
        print("  ABORT -- AZ-MA-1 system not found on Oracle")
        return

    sys_id = az_system.get("id")
    sys_uid = DS_PARENT_UID
    print(f"  AZ-MA-1 system: id={sys_id}")

    # GET current deployment payload
    status, dep_data = oracle_api("GET", f"deployments/{dep_id}")
    if status != 200 or not dep_data:
        print(f"  FAIL -- cannot GET deployment: HTTP {status}")
        return

    # Build dual-write PUT payload
    # Strategy: include BOTH deployedSystems@link (OGC standard) and
    # platform@link (OSH-compatible fallback)
    put_payload = dep_data

    # Add platform@link (OSH understands this today)
    put_payload["properties"]["platform@link"] = {
        "href": f"/sensorhub/api/systems/{sys_id}",
        "uid": sys_uid,
        "title": "ODAS Mic Array Node AZ-MA-1",
        "type": "application/geo+json"
    }

    # Add deployedSystems@link (OGC standard -- OSH currently strips it,
    # but we write it so it activates when the conformance gap is fixed)
    put_payload["properties"]["deployedSystems@link"] = [
        {
            "href": f"/sensorhub/api/systems/{sys_id}",
            "uid": sys_uid,
            "title": "ODAS Mic Array Node AZ-MA-1",
            "type": "application/geo+json"
        }
    ]

    if DRY_RUN:
        print(f"  DRY-RUN: would PUT deployment {dep_id} with dual-write links")
        return

    status, data = oracle_api("PUT", f"deployments/{dep_id}", put_payload)
    if status in (200, 204):
        print(f"  UPDATE String Alpha deployment -> HTTP {status} (dual-write)")
        created.append("deployment-link:String Alpha <-> AZ-MA-1")
    else:
        print(f"  FAIL deployment link -> HTTP {status}: {data}")
        failed.append(f"deployment-link -> HTTP {status}")

    # Verify the link was saved
    time.sleep(0.5)
    status, verify = oracle_api("GET", f"deployments/{dep_id}")
    if status == 200 and isinstance(verify, dict):
        props = verify.get("properties", {})
        has_platform = "platform@link" in props
        has_deployed = "deployedSystems@link" in props
        print(f"  Verify: platform@link={'YES' if has_platform else 'NO'}, "
              f"deployedSystems@link={'YES' if has_deployed else 'NO (expected -- OSH strips it)'}")


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("AZ-MA-1 MIGRATION: DO -> Oracle OSH")
    print(f"  Source: {DO_BASE}")
    print(f"  Target: {ORACLE_BASE}")
    if DRY_RUN:
        print("  MODE: DRY-RUN (no writes)")
    if SKIP_OBS:
        print("  MODE: Skipping observations")
    print("=" * 70)

    # Validate Oracle connectivity
    print("\nValidating Oracle connectivity...")
    status, _ = oracle_api("GET", "")
    if status != 200:
        print(f"  FATAL: Oracle API returned HTTP {status}")
        sys.exit(1)
    print("  Oracle API OK")

    # Run phases
    t0 = time.time()

    phase1_procedures()
    parent_id = phase2_toplevel_system()
    phase3_subsystems(parent_id)
    phase4_datastreams()
    phase5_controlstreams()
    phase6_observations()
    phase7_deployment_link()

    elapsed = time.time() - t0

    # Save ID map
    map_path = os.path.join(BACKUP_DIR, "migration_id_map.json")
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(id_map_do_to_oracle, f, indent=2)
    print(f"\n  ID map saved to {map_path}")

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"MIGRATION COMPLETE -- {elapsed:.1f}s")
    print(f"  Created:  {len(created)}")
    print(f"  Skipped:  {len(skipped)} (already existed)")
    print(f"  Failed:   {len(failed)}")
    if failed:
        print("\nFailed details:")
        for f_item in failed:
            print(f"  - {f_item}")
    print("=" * 70)


if __name__ == "__main__":
    main()
