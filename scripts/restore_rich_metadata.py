#!/usr/bin/env python3
"""
Restore rich SensorML metadata to all MA systems and subsystems.

The server has the correct systems/subsystems with names and descriptions,
but is missing: keywords, identifiers, classifiers, characteristics,
capabilities, contacts, and documents (photos, papers, links).

This script reads the backup SML JSON files, maps them to current server
system IDs via uniqueId (UID), and PUTs the enriched SensorML back.
"""

import json
import os
import sys
import urllib.request
import ssl

API_BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = "os4csapi:ogc134mm"

# Base64-encoded auth
import base64
AUTH_HEADER = "Basic " + base64.b64encode(AUTH.encode()).decode()

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "migration_backup")

# UID → current server system ID mapping (from live server query)
UID_TO_ID = {
    # Top-level MA nodes
    "urn:os4csapi:system:odas:az-ma-1": "0420",
    "urn:os4csapi:system:odas:az-ma-2": "0490",
    "urn:os4csapi:system:odas:az-ma-3": "049g",
    # AZ-MA-1 subsystems
    "urn:os4csapi:platform:az-ma-1:tripod": "042g",
    "urn:os4csapi:system:odas:az-ma-1:micarray": "0430",
    "urn:os4csapi:system:odas:az-ma-1:edge": "043g",
    "urn:os4csapi:system:odas:az-ma-1:comms": "0440",
    "urn:os4csapi:system:odas:az-ma-1:power": "044g",
    "urn:os4csapi:system:odas:az-ma-1:actuator": "0450",
    "urn:os4csapi:system:odas:az-ma-1:mic1": "045g",
    "urn:os4csapi:system:odas:az-ma-1:mic2": "0460",
    "urn:os4csapi:system:odas:az-ma-1:mic3": "046g",
    "urn:os4csapi:system:odas:az-ma-1:mic4": "0470",
    "urn:os4csapi:system:odas:az-ma-1:mic5": "047g",
    "urn:os4csapi:system:odas:az-ma-1:mic6": "0480",
    "urn:os4csapi:system:odas:az-ma-1:mic7": "048g",
    # AZ-MA-2 subsystems
    "urn:os4csapi:platform:az-ma-2:tripod": "04a0",
    "urn:os4csapi:system:odas:az-ma-2:micarray": "04ag",
    "urn:os4csapi:system:odas:az-ma-2:edge": "04b0",
    "urn:os4csapi:system:odas:az-ma-2:comms": "04bg",
    "urn:os4csapi:system:odas:az-ma-2:power": "04c0",
    "urn:os4csapi:system:odas:az-ma-2:actuator": "04cg",
    "urn:os4csapi:system:odas:az-ma-2:mic1": "04d0",
    "urn:os4csapi:system:odas:az-ma-2:mic2": "04dg",
    "urn:os4csapi:system:odas:az-ma-2:mic3": "04e0",
    "urn:os4csapi:system:odas:az-ma-2:mic4": "04eg",
    "urn:os4csapi:system:odas:az-ma-2:mic5": "04f0",
    "urn:os4csapi:system:odas:az-ma-2:mic6": "04fg",
    "urn:os4csapi:system:odas:az-ma-2:mic7": "04g0",
    # AZ-MA-3 subsystems
    "urn:os4csapi:platform:az-ma-3:tripod": "04gg",
    "urn:os4csapi:system:odas:az-ma-3:micarray": "04h0",
    "urn:os4csapi:system:odas:az-ma-3:edge": "04hg",
    "urn:os4csapi:system:odas:az-ma-3:comms": "04i0",
    "urn:os4csapi:system:odas:az-ma-3:power": "04ig",
    "urn:os4csapi:system:odas:az-ma-3:actuator": "04j0",
    "urn:os4csapi:system:odas:az-ma-3:mic1": "04jg",
    "urn:os4csapi:system:odas:az-ma-3:mic2": "04k0",
    "urn:os4csapi:system:odas:az-ma-3:mic3": "04kg",
    "urn:os4csapi:system:odas:az-ma-3:mic4": "04l0",
    "urn:os4csapi:system:odas:az-ma-3:mic5": "04lg",
    "urn:os4csapi:system:odas:az-ma-3:mic6": "04m0",
    "urn:os4csapi:system:odas:az-ma-3:mic7": "04mg",
}

# SSL context that accepts self-signed certs (DuckDNS/Caddy)
ctx = ssl.create_default_context()
ctx.check_hostname = True
ctx.verify_mode = ssl.CERT_REQUIRED


def put_sml(system_id: str, sml_body: dict) -> bool:
    """PUT SensorML JSON to update a system's metadata."""
    url = f"{API_BASE}/systems/{system_id}"
    data = json.dumps(sml_body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/sml+json",
            "Accept": "application/json",
        },
    )
    try:
        resp = urllib.request.urlopen(req, context=ctx)
        code = resp.getcode()
        if code in (200, 204):
            return True
        else:
            print(f"  WARNING: HTTP {code} for {system_id}")
            return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        print(f"  ERROR: HTTP {e.code} for {system_id}: {body}")
        return False


def main():
    # Collect all backup SML files
    sml_files = sorted(
        f for f in os.listdir(BACKUP_DIR)
        if f.endswith("_sml.json") and not f.startswith(".")
    )
    print(f"Found {len(sml_files)} backup SML files in {BACKUP_DIR}")

    success = 0
    skipped = 0
    failed = 0

    for filename in sml_files:
        filepath = os.path.join(BACKUP_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            sml = json.load(f)

        uid = sml.get("uniqueId")
        if not uid:
            print(f"SKIP {filename}: no uniqueId")
            skipped += 1
            continue

        server_id = UID_TO_ID.get(uid)
        if not server_id:
            print(f"SKIP {filename}: UID {uid} not in mapping")
            skipped += 1
            continue

        # Update the ID in the SML body to match the server
        sml["id"] = server_id

        # Check if this backup has any rich fields
        rich_fields = [
            "keywords", "identifiers", "classifiers", "characteristics",
            "capabilities", "contacts", "documents"
        ]
        has_rich = any(sml.get(field) for field in rich_fields)
        if not has_rich:
            print(f"SKIP {filename}: no rich metadata to restore")
            skipped += 1
            continue

        rich_present = [f for f in rich_fields if sml.get(f)]
        print(f"PUT  {filename} → {server_id} (UID: {uid})")
        print(f"     Rich fields: {', '.join(rich_present)}")

        if put_sml(server_id, sml):
            print(f"     ✓ OK")
            success += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {success} restored, {skipped} skipped, {failed} failed")
    print(f"Total backup files processed: {len(sml_files)}")


if __name__ == "__main__":
    main()
