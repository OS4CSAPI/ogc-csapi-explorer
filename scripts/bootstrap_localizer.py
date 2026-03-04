#!/usr/bin/env python3
"""
bootstrap_localizer.py — Register the LOB Localizer on the OS4CSAPI server.

Creates three resources (skip-if-exists):
  1. Procedure:  urn:os4csapi:procedure:lob-wls-triangulation:v1
  2. System:     urn:os4csapi:system:fusion:az-string-alpha-localizer  (typeOf → procedure)
  3. DataStream: az_string_alpha_location_estimate  (9-field Location Estimate schema)

Usage:
    python bootstrap_localizer.py              # create everything (skip if exists)
    python bootstrap_localizer.py --clean      # delete then recreate
    python bootstrap_localizer.py --dry-run    # print what would happen

Requires: Python 3.10+, no external dependencies (stdlib only).
"""

import argparse
import base64
import json
import socket
import ssl as _ssl
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"
ORACLE_IP = "129.80.248.53"

# ── UIDs ──────────────────────────────────────────────────────────────────
PROCEDURE_UID = "urn:os4csapi:procedure:lob-wls-triangulation:v1"
SYSTEM_UID    = "urn:os4csapi:system:fusion:az-string-alpha-localizer"
OUTPUT_NAME   = "az_string_alpha_location_estimate"

# ── Definition namespaces ─────────────────────────────────────────────────
_ODAS  = "https://os4csapi.org/def/odas"
_CSAPI = "https://os4csapi.org/def/csapi"
_FUSION = "https://os4csapi.org/def/fusion"

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions
# ═══════════════════════════════════════════════════════════════════════════

PROCEDURE_DEF = {
    "type": "Feature",
    "properties": {
        "uid": PROCEDURE_UID,
        "name": "WLS LOB Triangulation v1",
        "description": (
            "Weighted least-squares bearing-only geolocation. "
            "Consumes N≥2 lines of bearing from acoustic sensor nodes, "
            "computes optimal intersection point with inverse-variance weighting, "
            "and produces a location estimate with CEP50 uncertainty."
        ),
    },
}

SYSTEM_DEF = {
    "type": "Feature",
    "properties": {
        "uid": SYSTEM_UID,
        "name": "AZ-String-Alpha LOB Triangulator",
        "description": (
            "Software fusion agent. Consumes LOB observations from "
            "AZ-MA-1/2/3 via CSAPI GET, computes UAS position via "
            "WLS bearing intersection, and publishes location estimates "
            "via CSAPI POST."
        ),
        "typeOf": PROCEDURE_UID,
    },
}

DATASTREAM_DEF = {
    "name": "UAS Location Estimate",
    "outputName": OUTPUT_NAME,
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "name": "location_estimate",
            "definition": f"{_FUSION}/locationEstimate",
            "label": "UAS Location Estimate",
            "fields": [
                {
                    "type": "Time",
                    "name": "timestamp",
                    "definition": f"{_ODAS}/time/epochSeconds",
                    "label": "Epoch seconds",
                    "referenceTime": "1970-01-01T00:00:00Z",
                    "uom": {"code": "s"},
                },
                {
                    "type": "Count",
                    "name": "trackId",
                    "definition": f"{_ODAS}/trackId",
                    "label": "Track ID",
                },
                {
                    "type": "Quantity",
                    "name": "estimatedLat",
                    "definition": f"{_FUSION}/estimatedLat",
                    "label": "Estimated latitude",
                    "uom": {"code": "deg"},
                    "constraint": {"intervals": [[-90.0, 90.0]]},
                },
                {
                    "type": "Quantity",
                    "name": "estimatedLon",
                    "definition": f"{_FUSION}/estimatedLon",
                    "label": "Estimated longitude",
                    "uom": {"code": "deg"},
                    "constraint": {"intervals": [[-180.0, 180.0]]},
                },
                {
                    "type": "Quantity",
                    "name": "cep50_m",
                    "definition": f"{_FUSION}/cep50",
                    "label": "CEP50 (m)",
                    "description": "Circular error probable — 50% of fixes fall within this radius",
                    "uom": {"code": "m"},
                },
                {
                    "type": "Text",
                    "name": "classification",
                    "definition": f"{_ODAS}/classification",
                    "label": "Classification",
                },
                {
                    "type": "Count",
                    "name": "numContributingLobs",
                    "definition": f"{_FUSION}/numContributingLobs",
                    "label": "Contributing LOBs",
                },
                {
                    "type": "Text",
                    "name": "contributingSensors",
                    "definition": f"{_FUSION}/contributingSensors",
                    "label": "Contributing sensors",
                    "description": "Comma-separated list of sensor names that contributed LOBs",
                },
                {
                    "type": "Quantity",
                    "name": "residual_m",
                    "definition": f"{_FUSION}/residual",
                    "label": "Residual (m)",
                    "description": "Mean perpendicular distance from each bearing line to the estimated point",
                    "uom": {"code": "m"},
                },
            ],
        },
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  Networking
# ═══════════════════════════════════════════════════════════════════════════

# DNS monkey-patch: resolve DuckDNS → Oracle Cloud IP (self-signed cert)
_real_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "os4csapi-osh.duckdns.org":
        return _real_getaddrinfo(ORACLE_IP, port, *args, **kwargs)
    return _real_getaddrinfo(host, port, *args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo

_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

_AUTH_HEADER = "Basic " + base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()

_MAX_RETRIES = 5
_RETRY_DELAY = 3


def _with_retry(fn, label="request"):
    for attempt in range(_MAX_RETRIES):
        try:
            return fn()
        except HTTPError:
            raise
        except (URLError, OSError, ConnectionError, TimeoutError) as e:
            if attempt < _MAX_RETRIES - 1:
                wait = _RETRY_DELAY * (attempt + 1)
                print(f"  ↻ Retry {label} in {wait}s ({type(e).__name__})")
                time.sleep(wait)
            else:
                raise


def api_get(path: str) -> dict | None:
    def fn():
        url = f"{BASE_URL}/{path}"
        req = Request(url, headers={
            "Authorization": _AUTH_HEADER,
            "Accept": "application/json",
        })
        try:
            with urlopen(req, timeout=15, context=_ssl_ctx) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            if e.code == 404:
                return None
            raise
    return _with_retry(fn, f"GET {path}")


def api_post(path: str, body: dict,
             content_type: str = "application/json") -> dict | None:
    def fn():
        url = f"{BASE_URL}/{path}"
        data = json.dumps(body).encode()
        req = Request(url, data=data, method="POST", headers={
            "Authorization": _AUTH_HEADER,
            "Content-Type": content_type,
            "Accept": "application/json",
        })
        try:
            with urlopen(req, timeout=30, context=_ssl_ctx) as resp:
                location = resp.headers.get("Location", "")
                raw = resp.read().decode()
                if location:
                    new_id = location.rstrip("/").split("/")[-1]
                    return {"id": new_id, "_location": location}
                if resp.status == 204 or not raw.strip():
                    return None
                return json.loads(raw)
        except HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code} POST {url}: {body_text[:300]}")
    return _with_retry(fn, f"POST {path}")


def api_delete(path: str) -> bool:
    def fn():
        url = f"{BASE_URL}/{path}"
        req = Request(url, method="DELETE", headers={
            "Authorization": _AUTH_HEADER,
        })
        try:
            with urlopen(req, timeout=15, context=_ssl_ctx) as resp:
                return resp.status in (200, 204)
        except HTTPError as e:
            if e.code == 404:
                return False
            raise
    return _with_retry(fn, f"DELETE {path}")


# ═══════════════════════════════════════════════════════════════════════════
#  Lookup helpers
# ═══════════════════════════════════════════════════════════════════════════

def find_by_uid(collection: str, uid: str) -> dict | None:
    """Find a resource by UID in a collection. Returns {id, ...} or None."""
    result = api_get(f"{collection}?uid={uid}")
    if result and "items" in result:
        for item in result["items"]:
            props = item.get("properties", item)
            if props.get("uid") == uid:
                return item
    return None


def find_datastream(system_id: str, output_name: str) -> dict | None:
    """Find a datastream on a system by outputName."""
    result = api_get(f"systems/{system_id}/datastreams")
    if result and "items" in result:
        for ds in result["items"]:
            if ds.get("outputName") == output_name:
                return ds
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  Bootstrap logic
# ═══════════════════════════════════════════════════════════════════════════

def bootstrap(clean: bool = False, dry_run: bool = False):
    stats = {"created": 0, "skipped": 0, "deleted": 0, "errors": 0}

    # ── 1. Procedure ─────────────────────────────────────────────────────
    print("\n── Step 1: Procedure ──")
    existing_proc = find_by_uid("procedures", PROCEDURE_UID)

    if clean and existing_proc:
        proc_id = existing_proc.get("id", existing_proc.get("properties", {}).get("id"))
        print(f"  DELETE procedure {proc_id}")
        if not dry_run:
            api_delete(f"procedures/{proc_id}")
            stats["deleted"] += 1
        existing_proc = None

    if existing_proc:
        proc_id = existing_proc.get("id", existing_proc.get("properties", {}).get("id"))
        print(f"  ✓ Procedure already exists: {proc_id}")
        stats["skipped"] += 1
    else:
        print(f"  POST procedure: {PROCEDURE_UID}")
        if not dry_run:
            result = api_post("procedures", PROCEDURE_DEF, content_type="application/geo+json")
            proc_id = result["id"]
            print(f"  ✓ Created procedure: {proc_id}")
            stats["created"] += 1
        else:
            proc_id = "<dry-run>"
            print(f"  (dry-run) Would create procedure")

    # ── 2. System ────────────────────────────────────────────────────────
    print("\n── Step 2: System ──")
    existing_sys = find_by_uid("systems", SYSTEM_UID)

    if clean and existing_sys:
        sys_id = existing_sys.get("id", existing_sys.get("properties", {}).get("id"))
        print(f"  DELETE system {sys_id}")
        if not dry_run:
            api_delete(f"systems/{sys_id}")
            stats["deleted"] += 1
        existing_sys = None

    if existing_sys:
        sys_id = existing_sys.get("id", existing_sys.get("properties", {}).get("id"))
        print(f"  ✓ System already exists: {sys_id}")
        stats["skipped"] += 1
    else:
        print(f"  POST system: {SYSTEM_UID}")
        if not dry_run:
            result = api_post("systems", SYSTEM_DEF, content_type="application/geo+json")
            sys_id = result["id"]
            print(f"  ✓ Created system: {sys_id}")
            stats["created"] += 1
        else:
            sys_id = "<dry-run>"
            print(f"  (dry-run) Would create system")

    # ── 3. DataStream ────────────────────────────────────────────────────
    print("\n── Step 3: DataStream ──")
    if sys_id == "<dry-run>":
        print(f"  (dry-run) Would create datastream under system {sys_id}")
    else:
        existing_ds = find_datastream(sys_id, OUTPUT_NAME)

        if clean and existing_ds:
            ds_id = existing_ds.get("id")
            print(f"  DELETE datastream {ds_id}")
            if not dry_run:
                api_delete(f"datastreams/{ds_id}")
                stats["deleted"] += 1
            existing_ds = None

        if existing_ds:
            ds_id = existing_ds.get("id")
            print(f"  ✓ DataStream already exists: {ds_id}")
            stats["skipped"] += 1
        else:
            print(f"  POST datastream: {OUTPUT_NAME}")
            if not dry_run:
                result = api_post(
                    f"systems/{sys_id}/datastreams",
                    DATASTREAM_DEF,
                )
                ds_id = result["id"]
                print(f"  ✓ Created datastream: {ds_id}")
                stats["created"] += 1
            else:
                ds_id = "<dry-run>"
                print(f"  (dry-run) Would create datastream")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n── Summary ──")
    print(f"  Created: {stats['created']}  Skipped: {stats['skipped']}  "
          f"Deleted: {stats['deleted']}  Errors: {stats['errors']}")

    if not dry_run and sys_id != "<dry-run>":
        print(f"\n  System ID:     {sys_id}")
        print(f"  DataStream ID: {ds_id}")
        print(f"\n  ➜ Use DS ID '{ds_id}' as LOCALIZER_DS in localizer.py")
        print(f"  ➜ Add '{ds_id}' to ALL_DS_IDS in clear_observations.py")

    return stats


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Bootstrap the LOB Localizer on the OS4CSAPI server")
    parser.add_argument("--clean", action="store_true", help="Delete then recreate all resources")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = parser.parse_args()

    print("=" * 60)
    print("  OS4CSAPI — LOB Localizer Bootstrap")
    print("=" * 60)
    print(f"  Server:    {BASE_URL}")
    print(f"  Procedure: {PROCEDURE_UID}")
    print(f"  System:    {SYSTEM_UID}")
    print(f"  Output:    {OUTPUT_NAME}")
    if args.dry_run:
        print(f"  Mode:      DRY RUN")
    elif args.clean:
        print(f"  Mode:      CLEAN + RECREATE")

    try:
        bootstrap(clean=args.clean, dry_run=args.dry_run)
    except Exception as e:
        print(f"\n  ✗ FATAL: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
