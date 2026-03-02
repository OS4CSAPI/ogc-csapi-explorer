#!/usr/bin/env python3
"""
reparent_string_alpha.py — Move "Sensor String Alpha" from being a subdeployment
of "Sensor Field 001" (042g) to being a subdeployment of "Sensor Network/Net
Deployment" (SNET, 0420).

Current hierarchy:
  SNET (0420) → Field 001 (042g) → String Alpha (0430) → Node 1/2/3

Target hierarchy:
  SNET (0420) → String Alpha (0430) → Node 1/2/3
  SNET (0420) → Field 001 (042g)     [now a leaf]

Approach (OSH server has no reparent API):
  1. Save full JSON for String Alpha + 3 Node subdeployments
  2. DELETE bottom-up: Node 3, Node 2, Node 1, String Alpha
  3. POST String Alpha under SNET (/deployments/{snet_id}/subdeployments)
  4. POST Node 1, 2, 3 under new String Alpha
  5. Verify all 4 resources exist with correct parent

Usage:
    python reparent_string_alpha.py              # execute migration
    python reparent_string_alpha.py --dry-run    # print plan without executing
"""

import argparse
import base64
import json
import socket
import ssl as _ssl
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ═════════════════════════════════════════════════════════════════════════════
#  Configuration
# ═════════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"
ORACLE_IP = "129.80.248.53"

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

# Auth header
_auth = base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()

# Known IDs (from live server state)
SNET_ID         = "0420"     # New parent
FIELD_001_ID    = "042g"     # Old parent
STRING_ALPHA_ID = "0430"     # Deployment being reparented
NODE_1_ID       = "043g"
NODE_2_ID       = "0440"
NODE_3_ID       = "044g"


# ═════════════════════════════════════════════════════════════════════════════
#  HTTP helpers
# ═════════════════════════════════════════════════════════════════════════════

def _request(method, url, body=None, accept="application/geo+json", content_type=None):
    headers = {
        "Authorization": f"Basic {_auth}",
        "Accept": accept,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = content_type or "application/geo+json"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, context=_ssl_ctx, timeout=30) as resp:
            raw = resp.read().decode()
            location = resp.headers.get("Location", "")
            if resp.status == 201:
                new_id = location.rstrip("/").split("/")[-1] if location else ""
                return {"_status": 201, "_id": new_id, "_location": location}
            if resp.status == 204 or not raw.strip():
                return {"_status": resp.status}
            result = json.loads(raw)
            result["_status"] = resp.status
            return result
    except HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode()
        except Exception:
            pass
        return {"_status": e.code, "_error": body_text[:500]}


def get(path):
    return _request("GET", f"{BASE_URL}/{path}")


def delete(path):
    return _request("DELETE", f"{BASE_URL}/{path}")


def post(path, body):
    return _request("POST", f"{BASE_URL}/{path}", body=body)


# ═════════════════════════════════════════════════════════════════════════════
#  Main migration
# ═════════════════════════════════════════════════════════════════════════════

def run(dry_run=False):
    print("=" * 70)
    print("  REPARENT: Sensor String Alpha")
    print("  FROM: Field 001 (042g) → TO: SNET (0420)")
    if dry_run:
        print("  *** DRY RUN — no changes will be made ***")
    print("=" * 70)
    print()

    # ── Step 1: Fetch and save all current data ──────────────────────────
    print("Step 1: Fetching current deployment data...")

    string_alpha = get(f"deployments/{STRING_ALPHA_ID}")
    if string_alpha.get("_status", 200) != 200 and "id" not in string_alpha:
        print(f"  ERROR: Could not fetch String Alpha: {string_alpha}")
        sys.exit(1)
    print(f"  ✓ String Alpha (0430): {string_alpha.get('properties', {}).get('name', '?')}")

    nodes = {}
    for nid, label in [(NODE_1_ID, "Node 1"), (NODE_2_ID, "Node 2"), (NODE_3_ID, "Node 3")]:
        data = get(f"deployments/{nid}")
        if "id" not in data:
            print(f"  ERROR: Could not fetch {label} ({nid}): {data}")
            sys.exit(1)
        nodes[nid] = data
        name = data.get("properties", {}).get("name", "?")
        coords = data.get("geometry", {}).get("coordinates", []) if data.get("geometry") else []
        print(f"  ✓ {label} ({nid}): {name}  coords={coords}")

    # Save backup
    backup = {
        "string_alpha": string_alpha,
        "nodes": nodes,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    backup_path = "scripts/reparent_backup.json"
    with open(backup_path, "w") as f:
        json.dump(backup, f, indent=2)
    print(f"\n  Backup saved to {backup_path}")

    # ── Step 2: Verify current parent ────────────────────────────────────
    print("\nStep 2: Verifying current parentage...")
    subs_of_field = get(f"deployments/{FIELD_001_ID}/subdeployments?limit=50")
    field_sub_ids = [item.get("id") for item in subs_of_field.get("items", [])]
    if STRING_ALPHA_ID in field_sub_ids:
        print(f"  ✓ String Alpha IS a subdeployment of Field 001 ({field_sub_ids})")
    else:
        print(f"  WARNING: String Alpha NOT found in Field 001 subs: {field_sub_ids}")
        print("  Proceeding anyway (may already be reparented)...")

    # ── Step 3: Delete bottom-up ─────────────────────────────────────────
    print("\nStep 3: Deleting deployments bottom-up...")
    delete_order = [
        (NODE_3_ID, "Node 3 — AZ-MA-3"),
        (NODE_2_ID, "Node 2 — AZ-MA-2"),
        (NODE_1_ID, "Node 1 — AZ-MA-1"),
        (STRING_ALPHA_ID, "Sensor String Alpha"),
    ]

    for dep_id, label in delete_order:
        if dry_run:
            print(f"  [DRY RUN] Would DELETE /deployments/{dep_id}  ({label})")
        else:
            result = delete(f"deployments/{dep_id}")
            status = result.get("_status", 0)
            if status in (200, 204):
                print(f"  ✓ Deleted {label} ({dep_id}) — HTTP {status}")
            else:
                print(f"  ✗ FAILED to delete {label} ({dep_id}): {result}")
                print("  ABORTING — check server state manually!")
                sys.exit(1)
            time.sleep(0.3)  # Brief pause between deletes

    # ── Step 4: Recreate String Alpha under SNET ─────────────────────────
    print("\nStep 4: Creating String Alpha under SNET...")

    # Build the POST body (strip server-added fields like id, links)
    sa_body = {
        "type": "Feature",
        "properties": {
            "uid": string_alpha["properties"]["uid"],
            "featureType": string_alpha["properties"].get("featureType", "sosa:Deployment"),
            "name": string_alpha["properties"]["name"],
            "description": string_alpha["properties"].get("description", ""),
            "validTime": string_alpha["properties"].get("validTime", ["2026-02-27T00:00:00Z", ".."]),
        },
        "geometry": string_alpha.get("geometry"),
    }

    if dry_run:
        print(f"  [DRY RUN] Would POST to /deployments/{SNET_ID}/subdeployments")
        print(f"            body.properties.name = {sa_body['properties']['name']}")
        new_sa_id = STRING_ALPHA_ID  # pretend
    else:
        result = post(f"deployments/{SNET_ID}/subdeployments", sa_body)
        status = result.get("_status", 0)
        new_sa_id = result.get("_id", "")
        if status == 201 and new_sa_id:
            print(f"  ✓ Created String Alpha under SNET — new ID: {new_sa_id}")
        elif status == 409:
            # Conflict = already exists (UID match). Look it up.
            print(f"  ⚠ 409 Conflict (UID already exists). Looking up by UID...")
            # Try fetching it from SNET subdeployments
            snet_subs = get(f"deployments/{SNET_ID}/subdeployments?limit=50")
            for item in snet_subs.get("items", []):
                if item.get("properties", {}).get("uid") == sa_body["properties"]["uid"]:
                    new_sa_id = item.get("id", "")
                    print(f"  ✓ Found existing String Alpha under SNET: {new_sa_id}")
                    break
            if not new_sa_id:
                print(f"  ✗ Could not find by UID. Result: {result}")
                sys.exit(1)
        else:
            print(f"  ✗ FAILED: {result}")
            sys.exit(1)
        time.sleep(0.3)

    # ── Step 5: Recreate Node 1, 2, 3 under new String Alpha ────────────
    print(f"\nStep 5: Creating Nodes under String Alpha ({new_sa_id})...")

    node_order = [
        (NODE_1_ID, "Node 1 — AZ-MA-1"),
        (NODE_2_ID, "Node 2 — AZ-MA-2"),
        (NODE_3_ID, "Node 3 — AZ-MA-3"),
    ]
    new_node_ids = {}

    for old_id, label in node_order:
        node_data = nodes[old_id]
        node_body = {
            "type": "Feature",
            "properties": {
                "uid": node_data["properties"]["uid"],
                "featureType": node_data["properties"].get("featureType", "sosa:Deployment"),
                "name": node_data["properties"]["name"],
                "description": node_data["properties"].get("description", ""),
                "validTime": node_data["properties"].get("validTime", ["2026-01-15T00:00:00Z", ".."]),
            },
            "geometry": node_data.get("geometry"),
        }

        # Preserve platform@link
        plat = node_data["properties"].get("platform@link")
        if plat:
            node_body["properties"]["platform@link"] = plat

        if dry_run:
            print(f"  [DRY RUN] Would POST {label} to /deployments/{new_sa_id}/subdeployments")
            new_node_ids[old_id] = old_id
        else:
            result = post(f"deployments/{new_sa_id}/subdeployments", node_body)
            status = result.get("_status", 0)
            nid = result.get("_id", "")
            if status == 201 and nid:
                print(f"  ✓ Created {label} — new ID: {nid}")
                new_node_ids[old_id] = nid
            elif status == 409:
                # UID conflict — look up
                print(f"  ⚠ 409 Conflict for {label}. Looking up by UID...")
                sa_subs = get(f"deployments/{new_sa_id}/subdeployments?limit=50")
                for item in sa_subs.get("items", []):
                    if item.get("properties", {}).get("uid") == node_body["properties"]["uid"]:
                        nid = item.get("id", "")
                        print(f"  ✓ Found existing {label}: {nid}")
                        new_node_ids[old_id] = nid
                        break
                if old_id not in new_node_ids:
                    print(f"  ✗ Could not find by UID. Result: {result}")
                    sys.exit(1)
            else:
                print(f"  ✗ FAILED: {result}")
                sys.exit(1)
            time.sleep(0.3)

    # ── Step 6: Verify ───────────────────────────────────────────────────
    print("\nStep 6: Verification...")

    if dry_run:
        print("  [DRY RUN] Skipping verification.")
        print("\n✅ DRY RUN complete. No changes were made.")
        return

    # Check String Alpha is under SNET
    snet_subs = get(f"deployments/{SNET_ID}/subdeployments?limit=50")
    snet_sub_ids = [item.get("id") for item in snet_subs.get("items", [])]
    if new_sa_id in snet_sub_ids:
        print(f"  ✓ String Alpha ({new_sa_id}) IS a subdeployment of SNET")
    else:
        print(f"  ✗ String Alpha ({new_sa_id}) NOT found in SNET subs: {snet_sub_ids}")

    # Check nodes are under new String Alpha
    sa_subs = get(f"deployments/{new_sa_id}/subdeployments?limit=50")
    sa_sub_ids = [item.get("id") for item in sa_subs.get("items", [])]
    for old_id, label in node_order:
        nid = new_node_ids.get(old_id, "")
        if nid in sa_sub_ids:
            print(f"  ✓ {label} ({nid}) IS a subdeployment of String Alpha")
        else:
            print(f"  ✗ {label} ({nid}) NOT found in String Alpha subs: {sa_sub_ids}")

    # Check platform@link preserved on nodes
    for old_id, label in node_order:
        nid = new_node_ids.get(old_id, "")
        if not nid:
            continue
        node = get(f"deployments/{nid}")
        plat = node.get("properties", {}).get("platform@link")
        if plat and plat.get("href"):
            print(f"  ✓ {label} ({nid}) has platform@link → {plat['href']}")
        else:
            print(f"  ✗ {label} ({nid}) MISSING platform@link!")

    # Check Field 001 no longer has String Alpha
    field_subs = get(f"deployments/{FIELD_001_ID}/subdeployments?limit=50")
    field_sub_ids = [item.get("id") for item in field_subs.get("items", [])]
    if not field_sub_ids:
        print(f"  ✓ Field 001 has no subdeployments (expected — now a leaf node)")
    else:
        print(f"  ⚠ Field 001 still has subdeployments: {field_sub_ids}")

    # Summary
    print("\n" + "=" * 70)
    print("  REPARENT COMPLETE")
    print(f"  String Alpha: {STRING_ALPHA_ID} → {new_sa_id}")
    for old_id, label in node_order:
        nid = new_node_ids.get(old_id, old_id)
        print(f"  {label}: {old_id} → {nid}")
    print(f"  New parent: SNET ({SNET_ID})")
    print(f"  Old parent: Field 001 ({FIELD_001_ID}) — now a leaf node")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reparent Sensor String Alpha from Field 001 to SNET")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without executing")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
