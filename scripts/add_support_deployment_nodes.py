#!/usr/bin/env python3
"""
add_support_deployment_nodes.py — Create dedicated deployment nodes with
platform@link for SET-A, Monitoring Site, and Relay / Repeater.

These systems are currently associated via deployedSystemUIDs (a weak UID-based
reference), but have no dedicated deployment node with a platform@link (the
strong 1:1 link that CSAPI uses for geometry sync).

New deployment nodes created:
  1. "SET-A Emplacement" → child of SSO, platform@link → SET-A system
  2. "Monitoring Site Node 1 Emplacement" → child of SNET, platform@link → Mon Site system
  3. "Relay / Repeater 001 Emplacement" → child of SNET, platform@link → Relay system

Usage:
    python add_support_deployment_nodes.py                # create (skip if exists)
    python add_support_deployment_nodes.py --dry-run      # print what would happen
"""

import argparse
import base64
import json
import socket
import ssl as _ssl
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ═════════════════════════════════════════════════════════════════════════════
#  Configuration (same as bootstrap_v4.py)
# ═════════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"
ORACLE_IP = "129.80.248.53"

VALID_TIME_START = "2026-02-27T00:00:00Z"
DEPLOY_VALID_START = "2026-03-02T00:00:00Z"  # today

# DNS monkey-patch: resolve DuckDNS hostname to Oracle Cloud IP
_real_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "os4csapi-osh.duckdns.org":
        return _real_getaddrinfo(ORACLE_IP, port, *args, **kwargs)
    return _real_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _patched_getaddrinfo

# Self-signed cert context
_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE


# ═════════════════════════════════════════════════════════════════════════════
#  New Deployment Node Definitions
# ═════════════════════════════════════════════════════════════════════════════

# Parent deployment UIDs (looked up at runtime)
SSO_UID  = "urn:os4csapi:deployment:sso:ft-huachuca:001"
SNET_UID = "urn:os4csapi:deployment:snet:ft-huachuca:001"

# System UIDs being linked
SET_A_UID       = "urn:os4csapi:system:set:ft-huachuca:001"
MON_SITE_UID    = "urn:os4csapi:system:monitoring-site-node:ft-huachuca:001"
RELAY_UID       = "urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001"

NEW_DEPLOYMENT_NODES = [
    {
        "uid": "urn:os4csapi:deployment:set:ft-huachuca:001",
        "name": "SET-A Emplacement",
        "description": (
            "Deployment node for the Sensor Employment Team (SET-A). "
            "Represents the physical emplacement of the SET location / TOC "
            "from which sensor data is received, analyzed, and SENREP reports "
            "are generated."
        ),
        "parent_deployment_uid": SSO_UID,
        "system_uid": SET_A_UID,
        "system_title": "Sensor Employment Team (SET-A)",
        "geometry": {"type": "Point", "coordinates": [-110.2524769, 31.6380757]},
    },
    {
        "uid": "urn:os4csapi:deployment:monsite:ft-huachuca:001",
        "name": "Monitoring Site Node 1 Emplacement",
        "description": (
            "Deployment node for Monitoring Site Node 1. "
            "Represents the physical emplacement of the monitoring site's "
            "equipment and communications infrastructure enabling SET data "
            "reception and processing."
        ),
        "parent_deployment_uid": SNET_UID,
        "system_uid": MON_SITE_UID,
        "system_title": "Monitoring Site Node 1",
        "geometry": {"type": "Point", "coordinates": [-110.2525675, 31.6383956]},
    },
    {
        "uid": "urn:os4csapi:deployment:relay:ft-huachuca:001",
        "name": "Relay / Repeater 001 Emplacement",
        "description": (
            "Deployment node for VHF Relay / Repeater 001. "
            "Represents the physical emplacement of the VHF radio repeater "
            "that forwards sensor transmissions to the monitoring site."
        ),
        "parent_deployment_uid": SNET_UID,
        "system_uid": RELAY_UID,
        "system_title": "Relay / Repeater 001",
        "geometry": {"type": "Point", "coordinates": [-110.2554653, 31.6429133]},
    },
]


# ═════════════════════════════════════════════════════════════════════════════
#  Engine
# ═════════════════════════════════════════════════════════════════════════════

class DeploymentNodeCreator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        cred = base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()
        self.auth_header = f"Basic {cred}"
        self.stats = {"created": 0, "skipped": 0, "errors": 0}
        self._uid_cache: dict[str, str] = {}

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _request(self, method: str, url: str, body: dict | None = None,
                 accept: str = "application/json",
                 content_type: str | None = None) -> dict | str | None:
        headers = {
            "Authorization": self.auth_header,
            "Accept": accept,
        }
        data = None
        if body is not None:
            ct = content_type or ("application/geo+json" if "geometry" in body else "application/json")
            headers["Content-Type"] = ct
            data = json.dumps(body).encode()

        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30, context=_ssl_ctx) as resp:
                raw = resp.read().decode()
                location = resp.headers.get("Location", "")
                if location:
                    new_id = location.rstrip("/").split("/")[-1]
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

    def _get(self, path: str):
        return self._request("GET", f"{BASE_URL}/{path}")

    def _post(self, path: str, body: dict, content_type: str | None = None):
        return self._request("POST", f"{BASE_URL}/{path}", body=body, content_type=content_type)

    def find_by_uid(self, collection: str, uid: str) -> str | None:
        cache_key = f"{collection}:{uid}"
        if cache_key in self._uid_cache:
            return self._uid_cache[cache_key]
        result = self._get(f"{collection}?uid={uid}")
        if result and "items" in result:
            for item in result["items"]:
                props = item.get("properties", item)
                if props.get("uid") == uid:
                    sid = item.get("id", props.get("id"))
                    self._uid_cache[cache_key] = sid
                    return sid
        return None

    # ── Main logic ────────────────────────────────────────────────────────────

    def run(self):
        print("=" * 70)
        print("  Add Deployment Nodes for SET-A, Monitoring Site, Relay")
        print("=" * 70)
        if self.dry_run:
            print("  (DRY RUN — no changes will be made)\n")

        for node_def in NEW_DEPLOYMENT_NODES:
            uid = node_def["uid"]
            name = node_def["name"]

            # 1. Check if already exists
            existing = self.find_by_uid("deployments", uid)
            if existing:
                print(f"  SKIP {name} — already exists ({existing})")
                self.stats["skipped"] += 1
                continue

            # 2. Resolve parent deployment ID
            parent_dep_uid = node_def["parent_deployment_uid"]
            parent_dep_id = self.find_by_uid("deployments", parent_dep_uid)
            if not parent_dep_id:
                if self.dry_run:
                    parent_dep_id = "DRY-PARENT"
                else:
                    print(f"  ERROR: Parent deployment {parent_dep_uid} not found!")
                    self.stats["errors"] += 1
                    continue

            # 3. Resolve linked system ID (for platform@link href)
            system_uid = node_def["system_uid"]
            system_id = self.find_by_uid("systems", system_uid)
            if not system_id:
                if self.dry_run:
                    system_id = "DRY-SYSTEM"
                else:
                    print(f"  ERROR: System {system_uid} not found!")
                    self.stats["errors"] += 1
                    continue

            # 4. Build the GeoJSON Feature body
            body = {
                "type": "Feature",
                "properties": {
                    "uid": uid,
                    "featureType": "sosa:Deployment",
                    "name": name,
                    "description": node_def["description"],
                    "validTime": [DEPLOY_VALID_START, ".."],
                    "platform@link": {
                        "href": f"/sensorhub/api/systems/{system_id}",
                        "title": node_def["system_title"],
                        "uid": system_uid,
                        "type": "application/geo+json",
                    },
                },
                "geometry": node_def["geometry"],
            }

            post_path = f"deployments/{parent_dep_id}/subdeployments"

            print(f"\n  CREATE: {name}")
            print(f"    UID:     {uid}")
            print(f"    Parent:  {parent_dep_uid.split(':')[-2]}:{parent_dep_uid.split(':')[-1]} ({parent_dep_id})")
            print(f"    System:  {node_def['system_title']} ({system_id})")
            print(f"    Coords:  {node_def['geometry']['coordinates']}")
            print(f"    POST →   {post_path}")

            if not self.dry_run:
                try:
                    result = self._post(post_path, body)
                    new_id = result.get("id") if result else "?"
                    print(f"    → Created! id={new_id}")
                    self._uid_cache[f"deployments:{uid}"] = new_id
                    self.stats["created"] += 1
                except RuntimeError as e:
                    print(f"    ERROR: {e}")
                    self.stats["errors"] += 1
            else:
                print(f"    → (dry run — would POST)")
                self.stats["created"] += 1

        # ── Verify ────────────────────────────────────────────────────────────
        if not self.dry_run:
            print("\n" + "─" * 70)
            print("  VERIFY: Check deployment → system linkage via /systems/{id}/deployments")
            print("─" * 70)
            for node_def in NEW_DEPLOYMENT_NODES:
                system_uid = node_def["system_uid"]
                system_id = self.find_by_uid("systems", system_uid)
                if not system_id:
                    print(f"  ✗ {node_def['system_title']}: system not found")
                    continue
                dep_list = self._get(f"systems/{system_id}/deployments")
                if dep_list and "items" in dep_list:
                    deps = dep_list["items"]
                    if deps:
                        dep_name = deps[0].get("properties", {}).get("name", deps[0].get("name", "?"))
                        print(f"  ✓ {node_def['system_title']} → deployed in: {dep_name}")
                    else:
                        print(f"  ✗ {node_def['system_title']} → no deployments found")
                else:
                    print(f"  ✗ {node_def['system_title']} → query failed")

        # ── Summary ───────────────────────────────────────────────────────────
        print("\n" + "=" * 70)
        s = self.stats
        print(f"  Done: {s['created']} created, {s['skipped']} skipped, {s['errors']} errors")
        print("=" * 70)

        return s["errors"] == 0


# ═════════════════════════════════════════════════════════════════════════════
#  Main
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Add deployment nodes for SET-A, Mon Site, Relay")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without making changes")
    args = parser.parse_args()

    creator = DeploymentNodeCreator(dry_run=args.dry_run)
    ok = creator.run()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
