"""
ODAS CSAPI Scenario Pack v2.5 – Bootstrap Ingestion Script
============================================================
Registers all v2.5 resources on OSH SensorHub:
  - 6 doctrine-aligned deployments (ICO → RSO → SSO → Net → Field → String)
  - 3 new systems (Monitoring Site, Monitoring Team, String Processor)
  - 2 new procedures (SENREP, Triangulate+Track Chain)
  - 3 new datastreams (Track State, Predicted Position, SENREP)
  - 2 SensorML process objects

Prerequisite: v2.3 base resources already registered (AZ-MA-NET, AZ-MA-1/2/3, etc.)

Usage:
  python scripts/bootstrap_v25.py [--dry-run]
"""
import json
import sys
import urllib.request
import base64
import time

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = base64.b64encode(b"ogc:ogc").decode()
DRY_RUN = "--dry-run" in sys.argv

# ── Tracking ──────────────────────────────────────────────────────────
created = []
skipped = []
failed = []

def api(method, path, body=None, expect=None, content_type="application/geo+json"):
    """Generic API call. Returns (status, data|None).
    Does NOT follow redirects — a 302 means payload was rejected.
    """
    url = f"{BASE}/{path}" if not path.startswith("http") else path
    data_bytes = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data_bytes, method=method)
    req.add_header("Authorization", f"Basic {AUTH}")
    req.add_header("Accept", "application/json")
    if body:
        req.add_header("Content-Type", content_type)

    # Use a custom opener that does NOT follow redirects
    class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None  # Don't follow
    opener = urllib.request.build_opener(NoRedirectHandler)

    try:
        resp = opener.open(req)
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
            body_text = e.read().decode()[:300]
        except Exception:
            pass
        if e.code == 302:
            loc = e.headers.get("Location", "")
            return 302, f"REDIRECT → {loc} (payload rejected by server)"
        return e.code, body_text


def find_resource(collection, uid_or_name, by="uid"):
    """Search for existing resource by UID."""
    if by == "uid":
        status, data = api("GET", f"{collection}?uid={uid_or_name}&limit=1")
    else:
        status, data = api("GET", f"{collection}?q={uid_or_name}&limit=5")
    if status == 200 and isinstance(data, dict):
        items = data.get("items", [])
        if items:
            return items[0]
    return None


def create_resource(collection, payload, label):
    """POST a new resource. Skip if UID already exists."""
    uid = payload.get("properties", {}).get("uid", "")
    if uid:
        existing = find_resource(collection, uid)
        if existing:
            eid = existing.get("id", "?")
            print(f"  SKIP {label} — already exists (id={eid})")
            skipped.append(label)
            return eid

    if DRY_RUN:
        print(f"  DRY-RUN: would POST to {collection}: {label}")
        return None

    status, data = api("POST", collection, payload)
    if status in (200, 201):
        rid = ""
        if isinstance(data, dict):
            rid = data.get("id", "")
        print(f"  CREATE {label} → HTTP {status} (id={rid})")
        created.append(label)
        return rid
    else:
        print(f"  FAIL {label} → HTTP {status}: {data}")
        failed.append(f"{label} → HTTP {status}")
        return None


def create_nested(parent_collection, parent_id, child_collection, payload, label):
    """POST nested resource under parent."""
    path = f"{parent_collection}/{parent_id}/{child_collection}"
    uid = payload.get("properties", {}).get("uid", "")

    # Check if already exists at root level
    if uid:
        existing = find_resource(child_collection, uid)
        if existing:
            eid = existing.get("id", "?")
            print(f"  SKIP {label} — already exists (id={eid})")
            skipped.append(label)
            return eid

    if DRY_RUN:
        print(f"  DRY-RUN: would POST to {path}: {label}")
        return None

    status, data = api("POST", path, payload)
    if status in (200, 201):
        rid = ""
        if isinstance(data, dict):
            rid = data.get("id", "")
        print(f"  CREATE {label} → HTTP {status} (id={rid})")
        created.append(label)
        return rid
    else:
        print(f"  FAIL {label} → HTTP {status}: {data}")
        failed.append(f"{label} → HTTP {status}")
        return None


def reorder_type_first(obj):
    """Recursively ensure 'type' is the first key in all dicts (OSH S-15 quirk)."""
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


def create_datastream_for_system(system_uid, ds_payload, label):
    """Find system by UID, then POST datastream under it."""
    existing = find_resource("systems", system_uid)
    if not existing:
        print(f"  FAIL {label} — parent system {system_uid} not found!")
        failed.append(f"{label} — parent not found")
        return None

    sys_id = existing.get("id", "")

    # Check if this datastream already exists under the system
    status, data = api("GET", f"systems/{sys_id}/datastreams?limit=50")
    if status == 200 and isinstance(data, dict):
        for ds in data.get("items", []):
            if ds.get("name") == ds_payload.get("name"):
                did = ds.get("id", "?")
                print(f"  SKIP {label} — already exists (id={did})")
                skipped.append(label)
                return did

    if DRY_RUN:
        print(f"  DRY-RUN: would POST datastream to systems/{sys_id}/datastreams: {label}")
        return None

    # POST datastream under system (reorder type-first per OSH S-15)
    url = f"systems/{sys_id}/datastreams"
    status, data = api("POST", url, reorder_type_first(ds_payload), content_type="application/json")
    if status in (200, 201):
        rid = ""
        if isinstance(data, dict):
            rid = data.get("id", "")
        print(f"  CREATE {label} → HTTP {status} (id={rid})")
        created.append(label)
        return rid
    else:
        print(f"  FAIL {label} → HTTP {status}: {data}")
        failed.append(f"{label} → HTTP {status}")
        return None


# ═══════════════════════════════════════════════════════════════════════
#  STEP 1: DOCTRINE DEPLOYMENT HIERARCHY
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 1: Doctrine Deployment Hierarchy")
print("  ICO → RSO → SSO → Sensor Net → Sensor Field → Sensor String")
print("=" * 60)

# Top-level: ICO
ico_payload = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-110.277897, 31.649006], [-110.253897, 31.649006],
            [-110.253897, 31.667006], [-110.277897, 31.667006],
            [-110.277897, 31.649006]
        ]]
    },
    "properties": {
        "featureType": "sosa:Deployment",
        "uid": "urn:os4csapi:deployment:ico:ft-huachuca:001",
        "name": "Intelligence Collection Operation (derived from ICP)",
        "description": "Top-level intelligence collection operation context derived from the intelligence collection plan (ICP).",
        "validTime": ["2026-02-27T00:00:00Z", ".."]
    }
}
ico_id = create_resource("deployments", ico_payload, "AZ-DEP-ICO-001")

# RSO (child of ICO)
rso_payload = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-110.277897, 31.649006], [-110.253897, 31.649006],
            [-110.253897, 31.667006], [-110.277897, 31.667006],
            [-110.277897, 31.649006]
        ]]
    },
    "properties": {
        "featureType": "sosa:Deployment",
        "uid": "urn:os4csapi:deployment:rso:ft-huachuca:001",
        "name": "Reconnaissance & Surveillance Operation (derived from R&S plan)",
        "description": "R&S operational context (sensorized subset or full R&S depending on modeling scope).",
        "validTime": ["2026-02-27T00:00:00Z", ".."]
    }
}
if ico_id:
    rso_id = create_nested("deployments", ico_id, "subdeployments", rso_payload, "AZ-DEP-RSO-001")
else:
    rso_id = create_resource("deployments", rso_payload, "AZ-DEP-RSO-001")

# SSO (child of RSO)
sso_payload = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-110.277897, 31.649006], [-110.253897, 31.649006],
            [-110.253897, 31.667006], [-110.277897, 31.667006],
            [-110.277897, 31.649006]
        ]]
    },
    "properties": {
        "featureType": "sosa:Deployment",
        "uid": "urn:os4csapi:deployment:sso:ft-huachuca:001",
        "name": "Sensor Surveillance Operation (derived from SSP)",
        "description": "Sensor Surveillance Operation context for remote sensors (SSP execution context).",
        "validTime": ["2026-02-27T00:00:00Z", ".."]
    }
}
if rso_id:
    sso_id = create_nested("deployments", rso_id, "subdeployments", sso_payload, "AZ-DEP-SSO-001")
else:
    sso_id = create_resource("deployments", sso_payload, "AZ-DEP-SSO-001")

# SNET (child of SSO)
snet_payload = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-110.277897, 31.649006], [-110.253897, 31.649006],
            [-110.253897, 31.667006], [-110.277897, 31.667006],
            [-110.277897, 31.649006]
        ]]
    },
    "properties": {
        "featureType": "sosa:Deployment",
        "uid": "urn:os4csapi:deployment:snet:ft-huachuca:001",
        "name": "Sensor Network/Net Deployment",
        "description": "Integrated sensor network (strings + relays + monitoring site) operating over AOI.",
        "validTime": ["2026-02-27T00:00:00Z", ".."]
    }
}
if sso_id:
    snet_id = create_nested("deployments", sso_id, "subdeployments", snet_payload, "AZ-DEP-SNET-001")
else:
    snet_id = create_resource("deployments", snet_payload, "AZ-DEP-SNET-001")

# FIELD (child of SNET)
field_payload = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-110.273897, 31.654006], [-110.255897, 31.654006],
            [-110.255897, 31.665006], [-110.273897, 31.665006],
            [-110.273897, 31.654006]
        ]]
    },
    "properties": {
        "featureType": "sosa:Deployment",
        "uid": "urn:os4csapi:deployment:field:ft-huachuca:001",
        "name": "Sensor Field 001",
        "description": "Geographic grouping of sensor strings in a sub-area of the AOI.",
        "validTime": ["2026-02-27T00:00:00Z", ".."]
    }
}
if snet_id:
    field_id = create_nested("deployments", snet_id, "subdeployments", field_payload, "AZ-DEP-FIELD-001")
else:
    field_id = create_resource("deployments", field_payload, "AZ-DEP-FIELD-001")

# STRING (child of FIELD)
string_payload = {
    "type": "Feature",
    "geometry": {
        "type": "LineString",
        "coordinates": [
            [-110.272897, 31.663006],
            [-110.257897, 31.655006],
            [-110.269897, 31.650006]
        ]
    },
    "properties": {
        "featureType": "sosa:Deployment",
        "uid": "urn:os4csapi:deployment:string:alpha:ft-huachuca:001",
        "name": "Sensor String Alpha (line-of-emplacement)",
        "description": "Sensor string emplaced along a line to cover a target route/NAI.",
        "validTime": ["2026-02-27T00:00:00Z", ".."]
    }
}
if field_id:
    string_id = create_nested("deployments", field_id, "subdeployments", string_payload, "AZ-DEP-STRING-ALPHA")
else:
    string_id = create_resource("deployments", string_payload, "AZ-DEP-STRING-ALPHA")


# ═══════════════════════════════════════════════════════════════════════
#  STEP 2: NEW SYSTEMS
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 2: New Systems (Monitoring Site, Monitoring Team, String Processor)")
print("=" * 60)

mon_site_payload = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-110.264897, 31.661006]},
    "properties": {
        "featureType": "sosa:Platform",
        "uid": "urn:os4csapi:platform:ft-huachuca:monitoring-site-1",
        "name": "Monitoring Site 1 (Ft Huachuca NE Range)",
        "description": "Monitoring site used by sensor surveillance operators."
    }
}
create_resource("systems", mon_site_payload, "AZ-MON-SITE-1")

mon_team_payload = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-110.264897, 31.661006]},
    "properties": {
        "featureType": "sosa:System",
        "uid": "urn:os4csapi:system:human:monitoring-team-a",
        "name": "Monitoring Team A (2-person SSO shift)",
        "description": "Human monitoring team that reviews individual sensor outputs and issues doctrinal SENREP reports."
    }
}
mon_team_id = create_resource("systems", mon_team_payload, "AZ-MON-TEAM-A")

strproc_payload = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-110.264897, 31.661006]},
    "properties": {
        "featureType": "sosa:System",
        "uid": "urn:os4csapi:system:process:string-processor-alpha",
        "name": "String Processor Alpha (LOB→Triangulation→Track)",
        "description": "Processing component that consumes per-sensor LOB observations and produces triangulated track state and predictions."
    }
}
strproc_id = create_resource("systems", strproc_payload, "AZ-STRPROC-ALPHA")


# ═══════════════════════════════════════════════════════════════════════
#  STEP 3: NEW PROCEDURES
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 3: New Procedures (SENREP, Triangulate+Track Chain)")
print("=" * 60)

senrep_proc_payload = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "featureType": "sosa:ObservingProcedure",
        "uid": "urn:os4csapi:procedure:senrep:sop:v1",
        "name": "SENREP Generation Procedure (Human-in-the-loop)",
        "description": "Human procedure for issuing SENREP when multi-sensor patterns indicate reportable activity."
    }
}
create_resource("procedures", senrep_proc_payload, "AZ-PROC-SENREP")

triang_chain_payload = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "featureType": "sosa:Procedure",
        "uid": "urn:os4csapi:procedure:triangulate-track-from-lobs:v1",
        "name": "Triangulate + Track from LOBs (Process Chain)",
        "description": "String-level processing chain to associate LOBs, triangulate, filter, and predict."
    }
}
create_resource("procedures", triang_chain_payload, "AZ-PROC-TRIANG-CHAIN")


# ═══════════════════════════════════════════════════════════════════════
#  STEP 4: NEW DATASTREAMS (Track State, Predicted Position, SENREP)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 4: New Datastreams (under String Processor & Monitoring Team)")
print("=" * 60)

# Track State schema (SWE Common)
track_state_schema = {
    "type": "DataRecord",
    "definition": "https://os4csapi.org/def/csapi/trackStateRecordOSH",
    "label": "Track State (string-level)",
    "fields": [
        {"name": "timestamp", "type": "Time", "definition": "https://os4csapi.org/def/odas/time/epochSeconds", "label": "Epoch seconds", "uom": {"code": "s"}, "referenceTime": "1970-01-01T00:00:00Z"},
        {"name": "globalTrackId", "type": "Text", "definition": "https://os4csapi.org/def/odas/globalTrackId", "label": "Global track ID"},
        {"name": "lat", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/lat", "label": "Latitude", "uom": {"code": "deg"}},
        {"name": "lon", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/lon", "label": "Longitude", "uom": {"code": "deg"}},
        {"name": "velEastMS", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/velEastMS", "label": "Velocity East", "uom": {"code": "m/s"}},
        {"name": "velNorthMS", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/velNorthMS", "label": "Velocity North", "uom": {"code": "m/s"}},
        {"name": "speedMS", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/speedMS", "label": "Speed", "uom": {"code": "m/s"}},
        {"name": "headingDeg", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/headingDeg", "label": "Heading", "uom": {"code": "deg"}},
        {"name": "posErrorM", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/posErrorM", "label": "Position error", "uom": {"code": "m"}},
        {"name": "trackConfidence", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/trackConfidence", "label": "Track confidence", "uom": {"code": "1"}},
        {"name": "nSensors", "type": "Count", "definition": "https://os4csapi.org/def/csapi/nSensors", "label": "Contributing sensors"},
        {"name": "method", "type": "Text", "definition": "https://os4csapi.org/def/csapi/method", "label": "Method"},
    ]
}

predicted_pos_schema = {
    "type": "DataRecord",
    "definition": "https://os4csapi.org/def/csapi/predictedPositionRecordOSH",
    "label": "Predicted Position (string-level)",
    "fields": [
        {"name": "timestamp", "type": "Time", "definition": "https://os4csapi.org/def/odas/time/epochSeconds", "label": "Epoch seconds", "uom": {"code": "s"}, "referenceTime": "1970-01-01T00:00:00Z"},
        {"name": "globalTrackId", "type": "Text", "definition": "https://os4csapi.org/def/odas/globalTrackId", "label": "Global track ID"},
        {"name": "predTime", "type": "Time", "definition": "https://os4csapi.org/def/csapi/predTime", "label": "Prediction time", "uom": {"code": "s"}, "referenceTime": "1970-01-01T00:00:00Z"},
        {"name": "lat", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/lat", "label": "Latitude", "uom": {"code": "deg"}},
        {"name": "lon", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/lon", "label": "Longitude", "uom": {"code": "deg"}},
        {"name": "posErrorM", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/posErrorM", "label": "Position error", "uom": {"code": "m"}},
        {"name": "horizonS", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/horizonS", "label": "Horizon", "uom": {"code": "s"}},
        {"name": "model", "type": "Text", "definition": "https://os4csapi.org/def/csapi/filterModel", "label": "Model"},
    ]
}

senrep_schema = {
    "type": "DataRecord",
    "definition": "https://os4csapi.org/def/csapi/senrepRecordOSH",
    "label": "SENREP (Sensor Report)",
    "fields": [
        {"name": "timestamp", "type": "Time", "definition": "https://os4csapi.org/def/odas/time/epochSeconds", "label": "Epoch seconds", "uom": {"code": "s"}, "referenceTime": "1970-01-01T00:00:00Z"},
        {"name": "title", "type": "Text", "definition": "https://os4csapi.org/def/csapi/reportTitle", "label": "Title"},
        {"name": "senderId", "type": "Text", "definition": "https://os4csapi.org/def/csapi/senderId", "label": "Sender ID"},
        {"name": "seqNo", "type": "Count", "definition": "https://os4csapi.org/def/csapi/seqNo", "label": "Sequence number"},
        {"name": "classification", "type": "Text", "definition": "https://os4csapi.org/def/csapi/classification", "label": "Classification"},
        {"name": "releasably", "type": "Text", "definition": "https://os4csapi.org/def/csapi/releasably", "label": "Releasability"},
        {"name": "dor", "type": "Text", "definition": "https://os4csapi.org/def/csapi/dateOfReport", "label": "Date of report"},
        {"name": "envirOpName", "type": "Text", "definition": "https://os4csapi.org/def/csapi/envirOpName", "label": "Environment/OpName"},
        {"name": "strNo", "type": "Text", "definition": "https://os4csapi.org/def/csapi/strNo", "label": "Sensor string number"},
        {"name": "detectTimeZ", "type": "Text", "definition": "https://os4csapi.org/def/csapi/detectTimeZ", "label": "Detection time (Z)"},
        {"name": "qty", "type": "Count", "definition": "https://os4csapi.org/def/csapi/qty", "label": "Quantity"},
        {"name": "tgtTyp", "type": "Category", "definition": "https://os4csapi.org/def/csapi/tgtTyp", "label": "Target type"},
        {"name": "subTyp", "type": "Text", "definition": "https://os4csapi.org/def/csapi/subTyp", "label": "Subtype"},
        {"name": "spd", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/spd", "label": "Speed", "uom": {"code": "km/h"}},
        {"name": "dirCardinal", "type": "Category", "definition": "https://os4csapi.org/def/csapi/dirCardinal", "label": "Direction (cardinal)"},
        {"name": "colLengthM", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/colLengthM", "label": "Column length", "uom": {"code": "m"}},
        {"name": "etaLat", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/etaLat", "label": "ETA lat", "uom": {"code": "deg"}},
        {"name": "etaLon", "type": "Quantity", "definition": "https://os4csapi.org/def/csapi/etaLon", "label": "ETA lon", "uom": {"code": "deg"}},
        {"name": "etaTimeZ", "type": "Text", "definition": "https://os4csapi.org/def/csapi/etaTimeZ", "label": "ETA time (Z)"},
        {"name": "comments", "type": "Text", "definition": "https://os4csapi.org/def/csapi/comments", "label": "Comments"},
    ]
}

# String Processor – Track State
track_state_ds = {
    "name": "StringProc Track State",
    "outputName": "track_state",
    "schema": {
        "obsFormat": "application/swe+json",
        "recordSchema": track_state_schema
    }
}
create_datastream_for_system(
    "urn:os4csapi:system:process:string-processor-alpha",
    track_state_ds,
    "StringProc Track State"
)

# String Processor – Predicted Position
predicted_pos_ds = {
    "name": "StringProc Predicted Position",
    "outputName": "predicted_position",
    "schema": {
        "obsFormat": "application/swe+json",
        "recordSchema": predicted_pos_schema
    }
}
create_datastream_for_system(
    "urn:os4csapi:system:process:string-processor-alpha",
    predicted_pos_ds,
    "StringProc Predicted Position"
)

# Monitoring Team – SENREP
senrep_ds = {
    "name": "Monitoring SENREP",
    "outputName": "senrep",
    "schema": {
        "obsFormat": "application/swe+json",
        "recordSchema": senrep_schema
    }
}
create_datastream_for_system(
    "urn:os4csapi:system:human:monitoring-team-a",
    senrep_ds,
    "Monitoring SENREP"
)


# ═══════════════════════════════════════════════════════════════════════
#  STEP 5: SEED SAMPLE OBSERVATIONS
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 5: Seed Sample Observations (1 each for Track State, Predicted Position, SENREP)")
print("=" * 60)

sample_obs = [
    {
        "system_uid": "urn:os4csapi:system:process:string-processor-alpha",
        "ds_name": "StringProc Track State",
        "label": "Track State sample obs",
        "obs": {
            "resultTime": "2026-02-27T20:10:01Z",
            "phenomenonTime": "2026-02-27T20:10:01Z",
            "result": {
                "timestamp": 1772223001,
                "globalTrackId": "urn:os4csapi:sample:globaltrack:GT-0001",
                "lat": 31.6582, "lon": -110.2641,
                "velEastMS": 2.2, "velNorthMS": 0.8,
                "speedMS": 2.343, "headingDeg": 70.9,
                "posErrorM": 25.0, "trackConfidence": 0.85,
                "nSensors": 3, "method": "triangulate+cv-filter"
            }
        }
    },
    {
        "system_uid": "urn:os4csapi:system:process:string-processor-alpha",
        "ds_name": "StringProc Predicted Position",
        "label": "Predicted Position sample obs",
        "obs": {
            "resultTime": "2026-02-27T20:10:01Z",
            "phenomenonTime": "2026-02-27T20:10:01Z",
            "result": {
                "timestamp": 1772223001,
                "globalTrackId": "urn:os4csapi:sample:globaltrack:GT-0001",
                "predTime": 1772223011,
                "lat": 31.6583, "lon": -110.2637,
                "posErrorM": 35.0, "horizonS": 10,
                "model": "constant-velocity"
            }
        }
    },
    {
        "system_uid": "urn:os4csapi:system:human:monitoring-team-a",
        "ds_name": "Monitoring SENREP",
        "label": "SENREP sample obs",
        "obs": {
            "resultTime": "2026-02-27T20:10:00Z",
            "phenomenonTime": "2026-02-27T20:10:00Z",
            "result": {
                "timestamp": 1772223000,
                "title": "SENREP",
                "senderId": "OS4CSAPI",
                "seqNo": 101,
                "classification": "U",
                "releasably": "REL",
                "dor": "260227",
                "envirOpName": "FT-HUACHUCA",
                "strNo": "AZ-STRING-ALPHA",
                "detectTimeZ": "2010Z",
                "qty": 1,
                "tgtTyp": "UAS",
                "subTyp": "ROTARY",
                "spd": 45,
                "dirCardinal": "SE",
                "colLengthM": 0,
                "etaLat": 31.659,
                "etaLon": -110.263,
                "etaTimeZ": "2025Z",
                "comments": "Demo SENREP: UAS detected by string; operator assessed movement SE."
            }
        }
    }
]

for entry in sample_obs:
    sys_resource = find_resource("systems", entry["system_uid"])
    if not sys_resource:
        print(f"  SKIP {entry['label']} — parent system not found")
        continue

    sys_id = sys_resource.get("id", "")
    # Find the target datastream
    status, data = api("GET", f"systems/{sys_id}/datastreams?limit=50")
    ds_id = None
    if status == 200 and isinstance(data, dict):
        for ds in data.get("items", []):
            if ds.get("name") == entry["ds_name"]:
                ds_id = ds.get("id")
                break

    if not ds_id:
        print(f"  SKIP {entry['label']} — datastream '{entry['ds_name']}' not found")
        continue

    if DRY_RUN:
        print(f"  DRY-RUN: would POST observation to datastreams/{ds_id}/observations: {entry['label']}")
        continue

    obs_payload = entry["obs"]
    url = f"datastreams/{ds_id}/observations"
    req = urllib.request.Request(f"{BASE}/{url}", data=json.dumps(obs_payload).encode(), method="POST")
    req.add_header("Authorization", f"Basic {AUTH}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        print(f"  CREATE {entry['label']} → HTTP {resp.status}")
        created.append(entry["label"])
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode()[:200]
        except Exception:
            pass
        print(f"  FAIL {entry['label']} → HTTP {e.code}: {body_text}")
        failed.append(f"{entry['label']} → HTTP {e.code}")


# ═══════════════════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"BOOTSTRAP v2.5 COMPLETE")
print(f"  Created:  {len(created)}")
print(f"  Skipped:  {len(skipped)} (already existed)")
print(f"  Failed:   {len(failed)}")
if failed:
    print("\nFailed details:")
    for f in failed:
        print(f"  - {f}")
print("=" * 60)
