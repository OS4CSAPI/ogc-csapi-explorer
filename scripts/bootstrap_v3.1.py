#!/usr/bin/env python3
"""
bootstrap_v3.1.py — Authoritative bootstrap for OS4CSAPI OSH server (DuckDNS).

Self-contained: ALL data is inline (no external files).
Uses nested POST for deployment hierarchy (proven reliable on this server).
Fixes deployedSystemUIDs with correct full URIs.

Usage:
    python bootstrap_v3.1.py                 # create everything (skip if exists)
    python bootstrap_v3.1.py --clean         # delete everything, then recreate
    python bootstrap_v3.1.py --clean-only    # delete everything, don't recreate
    python bootstrap_v3.1.py --dry-run       # print what would happen
    python bootstrap_v3.1.py --fix-uids      # only fix deployedSystemUIDs on SNET
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"

VALID_TIME_START = "2026-02-27T00:00:00Z"

# ─── System definitions ──────────────────────────────────────────────────────

SYSTEMS = [
    {
        "uid":  "urn:os4csapi:system:set:ft-huachuca:001",
        "name": "Sensor Employment Team (SET-A)",
        "description": "SET responsible for receiving sensor data, conducting analysis, and generating SENREP reports.",
        "geometry": {
            "type": "Point",
            "coordinates": [-110.2524769, 31.6380757]
        },
        "has_senrep": True,
    },
    {
        "uid":  "urn:os4csapi:system:monitoring-site-node:ft-huachuca:001",
        "name": "Monitoring Site Node 1",
        "description": "Operational monitoring node (equipment + comms) that enables SET data reception and processing.",
        "geometry": {
            "type": "Point",
            "coordinates": [-110.2525675, 31.6383956]
        },
    },
    {
        "uid":  "urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001",
        "name": "Relay / Repeater 001",
        "description": "VHF radio repeater forwarding sensor transmissions to the monitoring site.",
        "geometry": {
            "type": "Point",
            "coordinates": [-110.2554653, 31.6429133]
        },
    },
]

# ─── Deployment hierarchy (nested via subdeployments POST) ────────────────────
# Tree structure: ICO → RSO → SSO → SNET → Field → String
# Each node knows its children via the "children" key.

DEPLOYMENT_TREE = {
    "uid":  "urn:os4csapi:deployment:ico:ft-huachuca:001",
    "name": "Intelligence Collection Operation (derived from ICP)",
    "description": "Top-level intelligence collection operation context derived from the intelligence collection plan (ICP). (v3.0 Part 1 doctrinal-aligned refactor; sensors added in Part 2)",
    "geometry": None,
    "properties": {},
    "children": [
        {
            "uid":  "urn:os4csapi:deployment:rso:ft-huachuca:001",
            "name": "Reconnaissance and Surveillance Operation",
            "description": "Reconnaissance and surveillance operation under the ICO context. Contains SSO and associated subdeployments.",
            "geometry": None,
            "properties": {},
            "children": [
                {
                    "uid":  "urn:os4csapi:deployment:sso:ft-huachuca:001",
                    "name": "Sensor Surveillance Operation (derived from SSP)",
                    "description": "Sensor Surveillance Operation context for remote sensors (SSP execution context).",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-110.2524769, 31.6380757]
                    },
                    "properties": {
                        "deployedSystemUIDs": "urn:os4csapi:system:set:ft-huachuca:001"
                    },
                    "children": [
                        {
                            "uid":  "urn:os4csapi:deployment:snet:ft-huachuca:001",
                            "name": "Sensor Network/Net Deployment",
                            "description": "Network-level grouping of sensors along communication paths.",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [-110.2525675, 31.6383956],
                                    [-110.2554653, 31.6429133]
                                ]
                            },
                            "properties": {
                                "deployedSystemUIDs": "urn:os4csapi:system:monitoring-site-node:ft-huachuca:001,urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001"
                            },
                            "children": [
                                {
                                    "uid":  "urn:os4csapi:deployment:field:ft-huachuca:001",
                                    "name": "Sensor Field 001",
                                    "description": "Geographic grouping of sensor strings in a sub-area of the AOI.",
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": [[
                                            [-110.253, 31.6375],
                                            [-110.252, 31.6375],
                                            [-110.252, 31.639],
                                            [-110.253, 31.639],
                                            [-110.253, 31.6375]
                                        ]]
                                    },
                                    "properties": {},
                                    "children": [
                                        {
                                            "uid":  "urn:os4csapi:deployment:string:ft-huachuca:001",
                                            "name": "Sensor String Alpha (line-of-emplacement)",
                                            "description": "Physical line of emplacement for sensors in Field 001.",
                                            "geometry": {
                                                "type": "LineString",
                                                "coordinates": [
                                                    [-110.2528, 31.6378],
                                                    [-110.2522, 31.6378],
                                                    [-110.2522, 31.6387],
                                                    [-110.2528, 31.6387]
                                                ]
                                            },
                                            "properties": {},
                                            "children": []
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# ─── SENREP datastream schema (inline, captured from live server) ─────────────

SENREP_SCHEMA = {
    "obsFormat": "application/om+json",
    "resultSchema": {
        "type": "DataRecord",
        "name": "senrep",
        "definition": "https://os4csapi.org/def/csapi/senrepRecordOSH",
        "label": "SENREP (Sensor Report)",
        "description": "Doctrinal SENREP-style report fields.",
        "fields": [
            {"type": "Time",     "name": "timestamp",    "definition": "https://os4csapi.org/def/odas/time/epochSeconds",    "label": "Epoch seconds",            "referenceTime": "1970-01-01T00:00:00Z", "uom": {"code": "s"}},
            {"type": "Text",     "name": "title",        "definition": "https://os4csapi.org/def/csapi/reportTitle",         "label": "Title"},
            {"type": "Text",     "name": "senderId",     "definition": "https://os4csapi.org/def/csapi/senderId",            "label": "Sender ID"},
            {"type": "Count",    "name": "seqNo",        "definition": "https://os4csapi.org/def/csapi/seqNo",               "label": "Sequence number"},
            {"type": "Text",     "name": "classification","definition": "https://os4csapi.org/def/csapi/classification",     "label": "Classification"},
            {"type": "Text",     "name": "releasably",   "definition": "https://os4csapi.org/def/csapi/releasably",          "label": "Releasability"},
            {"type": "Text",     "name": "dor",          "definition": "https://os4csapi.org/def/csapi/dateOfReport",        "label": "Date of report"},
            {"type": "Text",     "name": "envirOpName",  "definition": "https://os4csapi.org/def/csapi/envirOpName",         "label": "Environment/OpName"},
            {"type": "Text",     "name": "strNo",        "definition": "https://os4csapi.org/def/csapi/strNo",               "label": "Sensor string number"},
            {"type": "Text",     "name": "detectTimeZ",  "definition": "https://os4csapi.org/def/csapi/detectTimeZ",         "label": "Detection time (Z)"},
            {"type": "Count",    "name": "qty",          "definition": "https://os4csapi.org/def/csapi/qty",                 "label": "Quantity"},
            {"type": "Category", "name": "tgtTyp",       "definition": "https://os4csapi.org/def/csapi/tgtTyp",              "label": "Target type",              "constraint": {"values": ["VEHICL","UAS","PERS","UNKN"]}},
            {"type": "Text",     "name": "subTyp",       "definition": "https://os4csapi.org/def/csapi/subTyp",              "label": "Subtype"},
            {"type": "Quantity", "name": "spd",          "definition": "https://os4csapi.org/def/csapi/spd",                 "label": "Speed",                    "uom": {"code": "km/h"}},
            {"type": "Category", "name": "dirCardinal",  "definition": "https://os4csapi.org/def/csapi/dirCardinal",         "label": "Direction (cardinal)",     "constraint": {"values": ["N","NE","E","SE","S","SW","W","NW"]}},
            {"type": "Quantity", "name": "colLengthM",   "definition": "https://os4csapi.org/def/csapi/colLengthM",          "label": "Column length",            "uom": {"code": "m"}},
            {"type": "Quantity", "name": "etaLat",       "definition": "https://os4csapi.org/def/csapi/etaLat",              "label": "ETA lat",                  "uom": {"code": "deg"}, "constraint": {"intervals": [[-90.0, 90.0]]}},
            {"type": "Quantity", "name": "etaLon",       "definition": "https://os4csapi.org/def/csapi/etaLon",              "label": "ETA lon",                  "uom": {"code": "deg"}, "constraint": {"intervals": [[-180.0, 180.0]]}},
            {"type": "Text",     "name": "etaTimeZ",     "definition": "https://os4csapi.org/def/csapi/etaTimeZ",            "label": "ETA time (Z)"},
            {"type": "Text",     "name": "comments",     "definition": "https://os4csapi.org/def/csapi/comments",            "label": "Comments"},
        ]
    }
}

SENREP_DATASTREAM = {
    "name": "SENREP (Sensor Report)",
    "description": "Doctrinal SENREP-style sensor report produced by SET.",
    "outputName": "senrep",
    "validTime": [VALID_TIME_START, "now"],
    "schema": SENREP_SCHEMA,
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Bootstrap engine
# ═══════════════════════════════════════════════════════════════════════════════

import base64

class Bootstrap:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        cred = base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()
        self.auth_header = f"Basic {cred}"
        self.stats = {"created": 0, "deleted": 0, "skipped": 0, "errors": 0, "patched": 0}

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _request(self, method: str, url: str, body: dict | None = None,
                 accept: str = "application/json") -> dict | str | None:
        headers = {
            "Authorization": self.auth_header,
            "Accept": accept,
        }
        data = None
        if body is not None:
            headers["Content-Type"] = "application/geo+json" if "geometry" in body else "application/json"
            data = json.dumps(body).encode()

        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                # For POST/PUT, capture the Location header to extract new resource ID
                location = resp.headers.get("Location", "")
                if location:
                    new_id = location.rstrip("/").split("/")[-1]
                    # Return a synthetic result with the id
                    if not raw.strip() or resp.status in (201, 204):
                        return {"id": new_id, "_location": location}
                    try:
                        result = json.loads(raw)
                        if isinstance(result, dict) and "id" not in result:
                            result["id"] = new_id
                        return result
                    except json.JSONDecodeError:
                        return {"id": new_id, "_location": location}
                if resp.status == 204 or not raw.strip():
                    return None
                return json.loads(raw)
        except HTTPError as e:
            if e.code == 404:
                return None
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code} {method} {url}: {body_text[:300]}")

    def _get(self, path: str, accept: str = "application/json"):
        return self._request("GET", f"{BASE_URL}/{path}", accept=accept)

    def _post(self, path: str, body: dict):
        return self._request("POST", f"{BASE_URL}/{path}", body=body)

    def _put(self, path: str, body: dict):
        return self._request("PUT", f"{BASE_URL}/{path}", body=body)

    def _delete(self, path: str):
        return self._request("DELETE", f"{BASE_URL}/{path}")

    # ── Lookup helpers ────────────────────────────────────────────────────────

    def find_by_uid(self, collection: str, uid: str) -> str | None:
        """Return the server ID for a resource with the given UID, or None."""
        result = self._get(f"{collection}?uid={uid}")
        if result and "items" in result:
            for item in result["items"]:
                props = item.get("properties", item)
                if props.get("uid") == uid:
                    return item.get("id", props.get("id"))
        return None

    def find_all(self, collection: str) -> list[dict]:
        """Return all items in the collection."""
        result = self._get(collection)
        if result and "items" in result:
            return result["items"]
        return []

    # ── Phase 0: Clean ────────────────────────────────────────────────────────

    def clean(self):
        """Delete all known resources by UID lookup."""
        print("\n" + "=" * 60)
        print("  PHASE 0: CLEAN — Deleting all known resources")
        print("=" * 60)

        # Delete SENREP datastream first (child of SET-A system)
        set_a_uid = SYSTEMS[0]["uid"]
        set_a_id = self.find_by_uid("systems", set_a_uid)
        if set_a_id:
            ds_list = self._get(f"systems/{set_a_id}/datastreams")
            if ds_list and "items" in ds_list:
                for ds in ds_list["items"]:
                    ds_id = ds.get("id")
                    if ds_id:
                        print(f"  DELETE datastream {ds.get('name', '?')} ({ds_id})")
                        if not self.dry_run:
                            try:
                                self._delete(f"datastreams/{ds_id}")
                                self.stats["deleted"] += 1
                            except RuntimeError as e:
                                print(f"    WARNING: {e}")
                                self.stats["errors"] += 1
                        else:
                            self.stats["deleted"] += 1

        # Delete deployments — walk tree bottom-up
        dep_uids = self._collect_deployment_uids(DEPLOYMENT_TREE)
        dep_uids.reverse()  # delete children first
        for uid in dep_uids:
            did = self.find_by_uid("deployments", uid)
            if did:
                print(f"  DELETE deployment {uid.split(':')[-2]}:{uid.split(':')[-1]} ({did})")
                if not self.dry_run:
                    try:
                        self._delete(f"deployments/{did}")
                        self.stats["deleted"] += 1
                    except RuntimeError as e:
                        print(f"    WARNING: {e}")
                        self.stats["errors"] += 1
                else:
                    self.stats["deleted"] += 1
            else:
                print(f"  SKIP deployment {uid} (not found)")

        # Delete systems
        for sys_def in reversed(SYSTEMS):
            uid = sys_def["uid"]
            sid = self.find_by_uid("systems", uid)
            if sid:
                print(f"  DELETE system {sys_def['name']} ({sid})")
                if not self.dry_run:
                    try:
                        self._delete(f"systems/{sid}")
                        self.stats["deleted"] += 1
                    except RuntimeError as e:
                        print(f"    WARNING: {e}")
                        self.stats["errors"] += 1
                else:
                    self.stats["deleted"] += 1
            else:
                print(f"  SKIP system {uid} (not found)")

        # Short pause to let server settle after deletes
        if not self.dry_run:
            time.sleep(1)

    def _collect_deployment_uids(self, node: dict) -> list[str]:
        """Depth-first collect all deployment UIDs."""
        uids = [node["uid"]]
        for child in node.get("children", []):
            uids.extend(self._collect_deployment_uids(child))
        return uids

    # ── Phase 1: Create systems ───────────────────────────────────────────────

    def create_systems(self):
        print("\n" + "=" * 60)
        print("  PHASE 1: Create Systems")
        print("=" * 60)

        for sys_def in SYSTEMS:
            uid = sys_def["uid"]
            existing = self.find_by_uid("systems", uid)
            if existing:
                print(f"  SKIP {sys_def['name']} — already exists ({existing})")
                self.stats["skipped"] += 1
                continue

            body = {
                "type": "Feature",
                "properties": {
                    "uid": uid,
                    "featureType": "sosa:Platform",
                    "name": sys_def["name"],
                    "description": sys_def["description"],
                    "validTime": [VALID_TIME_START, ".."],
                },
                "geometry": sys_def["geometry"],
            }

            print(f"  CREATE system: {sys_def['name']}")
            if not self.dry_run:
                try:
                    result = self._post("systems", body)
                    new_id = result.get("id") if result else "?"
                    print(f"    → id={new_id}")
                    self.stats["created"] += 1
                except RuntimeError as e:
                    print(f"    ERROR: {e}")
                    self.stats["errors"] += 1
            else:
                print(f"    → (dry run)")
                self.stats["created"] += 1

    # ── Phase 2: Create deployment tree (nested POST) ─────────────────────────

    def create_deployments(self):
        print("\n" + "=" * 60)
        print("  PHASE 2: Create Deployment Hierarchy (nested POST)")
        print("=" * 60)

        self._create_deployment_node(DEPLOYMENT_TREE, parent_path=None, depth=0)

    def _create_deployment_node(self, node: dict, parent_path: str | None, depth: int):
        """Recursively create a deployment and its children."""
        uid = node["uid"]
        indent = "  " + "  " * depth
        short_name = uid.split(":")[-2] + ":" + uid.split(":")[-1]

        existing = self.find_by_uid("deployments", uid)
        if existing:
            print(f"{indent}SKIP {node['name']} — already exists ({existing})")
            self.stats["skipped"] += 1
            # Still need to recurse for children
            child_path = f"deployments/{existing}/subdeployments"
            for child in node.get("children", []):
                self._create_deployment_node(child, child_path, depth + 1)
            return

        body = {
            "type": "Feature",
            "properties": {
                "uid": uid,
                "featureType": "sosa:Deployment",
                "name": node["name"],
                "description": node["description"],
                "validTime": [VALID_TIME_START, ".."],
            },
            "geometry": node["geometry"],
        }
        # Add extra properties (e.g. deployedSystemUIDs)
        for k, v in node.get("properties", {}).items():
            body["properties"][k] = v

        # Determine POST path
        if parent_path is None:
            post_path = "deployments"
        else:
            post_path = parent_path

        print(f"{indent}CREATE deployment: {node['name']} ({short_name})")
        print(f"{indent}  POST → {post_path}")

        new_id = None
        if not self.dry_run:
            try:
                result = self._post(post_path, body)
                new_id = result.get("id") if result else "?"
                print(f"{indent}  → id={new_id}")
                self.stats["created"] += 1
            except RuntimeError as e:
                print(f"{indent}  ERROR: {e}")
                self.stats["errors"] += 1
                return  # Can't create children if parent failed
        else:
            new_id = f"DRY-{short_name}"
            print(f"{indent}  → (dry run)")
            self.stats["created"] += 1

        # Recurse for children using nested subdeployments endpoint
        if new_id and node.get("children"):
            if self.dry_run:
                child_path = f"{post_path}/DRY/subdeployments"
            else:
                child_path = f"deployments/{new_id}/subdeployments"
            for child in node["children"]:
                self._create_deployment_node(child, child_path, depth + 1)

    # ── Phase 3: Create SENREP datastream ─────────────────────────────────────

    def create_senrep(self):
        print("\n" + "=" * 60)
        print("  PHASE 3: Create SENREP Datastream on SET-A")
        print("=" * 60)

        set_a_uid = SYSTEMS[0]["uid"]
        set_a_id = self.find_by_uid("systems", set_a_uid)
        if not set_a_id:
            if self.dry_run:
                set_a_id = "DRY-SET-A"
            else:
                print("  ERROR: SET-A system not found — can't create datastream")
                self.stats["errors"] += 1
                return

        # Check if datastream already exists
        existing_ds = self._get(f"systems/{set_a_id}/datastreams") if not self.dry_run else None
        if existing_ds and "items" in existing_ds:
            for ds in existing_ds["items"]:
                if ds.get("outputName") == "senrep" or "SENREP" in ds.get("name", ""):
                    print(f"  SKIP SENREP — already exists ({ds.get('id')})")
                    self.stats["skipped"] += 1
                    return

        body = {
            "name": SENREP_DATASTREAM["name"],
            "description": SENREP_DATASTREAM["description"],
            "outputName": SENREP_DATASTREAM["outputName"],
            "validTime": SENREP_DATASTREAM["validTime"],
            "schema": SENREP_DATASTREAM["schema"],
        }

        print(f"  CREATE SENREP datastream on system {set_a_id}")
        if not self.dry_run:
            try:
                result = self._post(f"systems/{set_a_id}/datastreams", body)
                new_id = result.get("id") if result else "?"
                print(f"    → id={new_id}")
                self.stats["created"] += 1
            except RuntimeError as e:
                print(f"    ERROR: {e}")
                self.stats["errors"] += 1
        else:
            print(f"    → (dry run)")
            self.stats["created"] += 1

    # ── Fix UIDs (targeted patch) ─────────────────────────────────────────────

    def fix_snet_uids(self):
        """Fix the wrong deployedSystemUIDs on the SNET deployment."""
        print("\n" + "=" * 60)
        print("  FIX: Correct deployedSystemUIDs on SNET")
        print("=" * 60)

        snet_uid = "urn:os4csapi:deployment:snet:ft-huachuca:001"
        snet_id = self.find_by_uid("deployments", snet_uid)
        if not snet_id:
            print("  SNET not found — nothing to fix")
            return

        # Read current state
        current = self._get(f"deployments/{snet_id}", accept="application/geo+json")
        if not current:
            print("  ERROR: Could not read SNET")
            self.stats["errors"] += 1
            return

        current_uids = current.get("properties", {}).get("deployedSystemUIDs", "")
        correct_uids = "urn:os4csapi:system:monitoring-site-node:ft-huachuca:001,urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001"

        if current_uids == correct_uids:
            print(f"  deployedSystemUIDs already correct — skip")
            self.stats["skipped"] += 1
            return

        print(f"  CURRENT: {current_uids}")
        print(f"  CORRECT: {correct_uids}")

        # PUT the full resource with corrected UIDs
        body = {
            "type": "Feature",
            "properties": {
                "uid": current["properties"]["uid"],
                "featureType": current["properties"].get("featureType", "sosa:Deployment"),
                "name": current["properties"]["name"],
                "description": current["properties"]["description"],
                "validTime": current["properties"]["validTime"],
                "deployedSystemUIDs": correct_uids,
            },
            "geometry": current["geometry"],
        }

        if not self.dry_run:
            try:
                self._put(f"deployments/{snet_id}", body)
                print(f"  → PATCHED {snet_id}")
                self.stats["patched"] += 1
            except RuntimeError as e:
                print(f"  ERROR: {e}")
                self.stats["errors"] += 1
        else:
            print(f"  → (dry run) would patch {snet_id}")
            self.stats["patched"] += 1

    # ── Verify ────────────────────────────────────────────────────────────────

    def verify(self):
        """Quick verification of created resources."""
        print("\n" + "=" * 60)
        print("  VERIFY: Checking server state")
        print("=" * 60)

        if self.dry_run:
            print("  (skipped in dry-run mode)")
            return True

        all_ok = True

        # Check systems
        for sys_def in SYSTEMS:
            sid = self.find_by_uid("systems", sys_def["uid"])
            status = f"OK ({sid})" if sid else "MISSING!"
            if not sid:
                all_ok = False
            print(f"  System {sys_def['name']}: {status}")

        # Check deployment tree
        dep_uids = self._collect_deployment_uids(DEPLOYMENT_TREE)
        for uid in dep_uids:
            did = self.find_by_uid("deployments", uid)
            short = uid.split(":")[-2] + ":" + uid.split(":")[-1]
            status = f"OK ({did})" if did else "MISSING!"
            if not did:
                all_ok = False
            print(f"  Deployment {short}: {status}")

        # Check SENREP
        set_a_id = self.find_by_uid("systems", SYSTEMS[0]["uid"])
        if set_a_id:
            ds = self._get(f"systems/{set_a_id}/datastreams")
            has_senrep = False
            if ds and "items" in ds:
                for d in ds["items"]:
                    if "SENREP" in d.get("name", ""):
                        has_senrep = True
                        print(f"  SENREP datastream: OK ({d.get('id')})")
            if not has_senrep:
                print(f"  SENREP datastream: MISSING!")
                all_ok = False

        # Check SNET UIDs
        snet_id = self.find_by_uid("deployments", "urn:os4csapi:deployment:snet:ft-huachuca:001")
        if snet_id:
            snet = self._get(f"deployments/{snet_id}", accept="application/geo+json")
            if snet:
                uids_val = snet.get("properties", {}).get("deployedSystemUIDs", "")
                if "monitoring-site-node" in uids_val and "relay:vhf-repeater" in uids_val:
                    print(f"  SNET deployedSystemUIDs: OK")
                else:
                    print(f"  SNET deployedSystemUIDs: WRONG — {uids_val}")
                    all_ok = False

        return all_ok

    # ── Run ───────────────────────────────────────────────────────────────────

    def run_full(self, clean: bool = False, clean_only: bool = False, fix_uids: bool = False):
        mode = "DRY RUN" if self.dry_run else "LIVE"
        print(f"\n{'#' * 60}")
        print(f"  bootstrap_v3.1.py — OSH Server Bootstrap [{mode}]")
        print(f"  Server: {BASE_URL}")
        print(f"  Time:   {datetime.now(timezone.utc).isoformat()}")
        print(f"{'#' * 60}")

        if fix_uids:
            self.fix_snet_uids()
        elif clean_only:
            self.clean()
        else:
            if clean:
                self.clean()
            self.create_systems()
            self.create_deployments()
            self.create_senrep()
            self.fix_snet_uids()
            self.verify()

        # Summary
        print(f"\n{'─' * 60}")
        print(f"  Summary: created={self.stats['created']}  deleted={self.stats['deleted']}  "
              f"patched={self.stats['patched']}  skipped={self.stats['skipped']}  "
              f"errors={self.stats['errors']}")
        if self.dry_run:
            print(f"  (DRY RUN — no changes were made)")
        print(f"{'─' * 60}\n")

        return self.stats["errors"] == 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bootstrap OS4CSAPI OSH server v3.1")
    parser.add_argument("--clean", action="store_true", help="Delete all then recreate")
    parser.add_argument("--clean-only", action="store_true", help="Delete all, don't recreate")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    parser.add_argument("--fix-uids", action="store_true", help="Only fix SNET deployedSystemUIDs")
    args = parser.parse_args()

    bs = Bootstrap(dry_run=args.dry_run)
    ok = bs.run_full(
        clean=args.clean,
        clean_only=args.clean_only,
        fix_uids=args.fix_uids,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
