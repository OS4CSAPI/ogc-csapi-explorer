#!/usr/bin/env python3
"""
link_procedures.py — Add typeOf linkages between Systems and Procedures.

Adds the SOSA `typeOf` property to all systems and subsystems that implement
a known procedure. This makes the system→procedure relationship visible in
the CSAPI Explorer, SensorML descriptions, and any other client.

Linkage map:
  Top-level:
    AZ-MA-1/2/3 → processing-chain:v1  (the overall DSP pipeline)

  Subsystems:
    micarray     → pdm-mems-audio-capture
    mic1–mic7    → pdm-mems-audio-capture
    edge         → processing-chain:v1  (runs the ODAS pipeline)
    actuator     → odas-config-actuation

    tripod, comms, power → no procedure (infrastructure, not instruments)

Approach: GET each system, add typeOf to properties, PUT back.
Verified: SensorHub OSH Node accepts and persists `typeOf` on PUT.
"""

import json
import base64
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

# ═════════════════════════════════════════════════════════════════════════════
#  Procedure UIDs (9 procedures already on the server)
# ═════════════════════════════════════════════════════════════════════════════

PROC_AUDIO_CAPTURE  = "urn:x-odas:procedure:pdm-mems-audio-capture"
PROC_SRP_PHAT       = "urn:x-odas:procedure:srp-phat-beamforming"
PROC_PARTICLE_FILTER = "urn:x-odas:procedure:particle-filter-tracking"
PROC_TRIANGULATION  = "urn:x-odas:procedure:ray-to-ray-triangulation"
PROC_CONFIG_ACTUATION = "urn:x-odas:procedure:odas-config-actuation"
PROC_PROCESSING_CHAIN = "urn:os4csapi:procedure:odas:az-ma-1:processing-chain:v1"

# ═════════════════════════════════════════════════════════════════════════════
#  Linkage Map: system UID suffix → procedure UID
# ═════════════════════════════════════════════════════════════════════════════

# Top-level MA systems → processing chain (the node's primary function)
TOP_LEVEL_PROCEDURE = PROC_PROCESSING_CHAIN

# Subsystem suffix → procedure
SUBSYSTEM_PROCEDURE_MAP = {
    "micarray":  PROC_AUDIO_CAPTURE,
    "mic1":      PROC_AUDIO_CAPTURE,
    "mic2":      PROC_AUDIO_CAPTURE,
    "mic3":      PROC_AUDIO_CAPTURE,
    "mic4":      PROC_AUDIO_CAPTURE,
    "mic5":      PROC_AUDIO_CAPTURE,
    "mic6":      PROC_AUDIO_CAPTURE,
    "mic7":      PROC_AUDIO_CAPTURE,
    "edge":      PROC_PROCESSING_CHAIN,
    "actuator":  PROC_CONFIG_ACTUATION,
    # tripod, comms, power → no procedure (infrastructure)
}

# ═════════════════════════════════════════════════════════════════════════════
#  Network setup
# ═════════════════════════════════════════════════════════════════════════════

_real_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "os4csapi-osh.duckdns.org":
        return _real_getaddrinfo(ORACLE_IP, port, *args, **kwargs)
    return _real_getaddrinfo(host, port, *args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo

_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

_cred = base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()

# ═════════════════════════════════════════════════════════════════════════════
#  HTTP helpers
# ═════════════════════════════════════════════════════════════════════════════

def _request(method, path, body=None, accept="application/geo+json"):
    headers = {
        "Authorization": f"Basic {_cred}",
        "Accept": accept,
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/geo+json"
        data = json.dumps(body).encode()

    req = Request(f"{BASE_URL}/{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30, context=_ssl_ctx) as resp:
            raw = resp.read().decode()
            if resp.status == 204 or not raw.strip():
                return resp.status, None
            return resp.status, json.loads(raw)
    except HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode()[:300]
        except Exception:
            pass
        return e.code, body_text


def get(path, accept="application/geo+json"):
    status, data = _request("GET", path, accept=accept)
    return data if status == 200 else None


def put(path, body):
    return _request("PUT", path, body)


# ═════════════════════════════════════════════════════════════════════════════
#  Core logic
# ═════════════════════════════════════════════════════════════════════════════

def link_system(system_id, procedure_uid, label=""):
    """Add typeOf to a single system. Returns True if updated."""
    # GET current
    sys_data = get(f"systems/{system_id}")
    if not sys_data:
        print(f"  ✗ {label} ({system_id}) — GET failed")
        return False

    props = sys_data.get("properties", {})
    current_typeof = props.get("typeOf")

    if current_typeof == procedure_uid:
        print(f"  · {label} ({system_id}) — already linked to {procedure_uid.split(':')[-1]}")
        return False

    if current_typeof:
        print(f"  ⚠ {label} ({system_id}) — has typeOf={current_typeof}, overwriting")

    # Add typeOf
    sys_data["properties"]["typeOf"] = procedure_uid

    # Remove server-generated fields
    sys_data.pop("id", None)
    sys_data.pop("links", None)

    # PUT back
    status, result = put(f"systems/{system_id}", sys_data)
    if status == 204:
        # Verify
        check = get(f"systems/{system_id}")
        verified_typeof = check.get("properties", {}).get("typeOf") if check else None
        if verified_typeof == procedure_uid:
            proc_short = procedure_uid.split(":")[-1]
            print(f"  ✓ {label} ({system_id}) → {proc_short}")
            return True
        else:
            print(f"  ✗ {label} ({system_id}) — PUT 204 but typeOf not persisted!")
            return False
    else:
        print(f"  ✗ {label} ({system_id}) — PUT failed: {status} {result}")
        return False


def run():
    print("=" * 70)
    print("  link_procedures.py — System → Procedure Linkage")
    print("=" * 70)

    updated = 0
    skipped = 0
    errors = 0

    # ── Top-level MA systems ──────────────────────────────────────────────
    print("\n── Top-Level MA Systems ──")

    # MA system IDs (from bootstrap — discovered at ingestion)
    ma_systems = {
        "0420": "AZ-MA-1",
        "0490": "AZ-MA-2",
        "049g": "AZ-MA-3",
    }

    for sys_id, name in ma_systems.items():
        if link_system(sys_id, TOP_LEVEL_PROCEDURE, label=name):
            updated += 1
        else:
            skipped += 1

    # ── Subsystems (3 MA nodes × 13 subsystems each) ─────────────────────
    print("\n── Subsystems ──")

    for sys_id, name in ma_systems.items():
        print(f"\n  {name} subsystems:")
        subs = get(f"systems/{sys_id}/subsystems", accept="application/json")
        if not subs or "items" not in subs:
            print(f"    ✗ Failed to list subsystems for {name}")
            errors += 1
            continue

        for sub in subs["items"]:
            sub_id = sub.get("id")
            sub_props = sub.get("properties", sub)
            sub_name = sub_props.get("name", "?")
            sub_uid = sub_props.get("uid", "")

            # Extract subsystem type suffix (e.g. "micarray", "edge", "mic3")
            suffix = sub_uid.split(":")[-1] if sub_uid else ""

            procedure_uid = SUBSYSTEM_PROCEDURE_MAP.get(suffix)
            if procedure_uid:
                if link_system(sub_id, procedure_uid, label=f"  {sub_name}"):
                    updated += 1
                else:
                    skipped += 1
            else:
                print(f"    · {sub_name} ({sub_id}) — no procedure (infrastructure)")
                skipped += 1

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print(f"  Done: {updated} linked, {skipped} skipped, {errors} errors")
    print(f"{'─' * 70}")

    return errors == 0


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
