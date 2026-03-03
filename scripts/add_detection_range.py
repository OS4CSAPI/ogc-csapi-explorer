#!/usr/bin/env python3
"""
Add detection-range datastreams to each MA node and post a single
observation with the range values.

This replaces hardcoded frontend detection range config with data
that flows through the CSAPI standard.

Each MA node gets:
  1. A new datastream: "AZ-MA-{n} Detection Capabilities"
     outputName: az_ma_{n}_detection_capabilities
  2. One observation with min/nominal/max range values

The frontend discovers these via GET /systems/{id}/datastreams and reads
the latest observation.
"""

import json, time, urllib.request, ssl, sys

BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = "os4csapi:ogc134mm"

# System IDs and their node numbers
NODES = [
    {"system_id": "0420", "n": 1, "uid": "urn:os4csapi:system:odas:az-ma-1"},
    {"system_id": "0490", "n": 2, "uid": "urn:os4csapi:system:odas:az-ma-2"},
    {"system_id": "049g", "n": 3, "uid": "urn:os4csapi:system:odas:az-ma-3"},
]

# Detection range values (identical for all 3 nodes — same hardware)
DETECTION_RANGE = {
    "minRange_m": 667,
    "nominalRange_m": 1833,
    "maxRange_m": 3000,
    "shape": "circular",
    "confidence": 0.7,
    "basis": "estimated",
}

_ODAS = "https://os4csapi.org/def/odas"
_CSAPI = "https://os4csapi.org/def/csapi"

DATASTREAM_SCHEMA = {
    "obsFormat": "application/om+json",
    "resultSchema": {
        "type": "DataRecord",
        "name": "detection_capabilities",
        "definition": f"{_CSAPI}/detectionCapabilitiesRecordOSH",
        "label": "Detection Capabilities",
        "description": "Static detection range characteristics for this sensor node.",
        "fields": [
            {"type": "Time", "name": "timestamp",
             "definition": f"{_ODAS}/time/epochSeconds",
             "label": "Epoch seconds",
             "referenceTime": "1970-01-01T00:00:00Z", "uom": {"code": "s"}},
            {"type": "Text", "name": "shape",
             "definition": f"{_CSAPI}/detectionShape",
             "label": "Detection area shape"},
            {"type": "Quantity", "name": "minRange_m",
             "definition": f"{_CSAPI}/detectionMinRange",
             "label": "Minimum detection range", "uom": {"code": "m"},
             "constraint": {"intervals": [[0.0, 100000.0]]}},
            {"type": "Quantity", "name": "nominalRange_m",
             "definition": f"{_CSAPI}/detectionNominalRange",
             "label": "Nominal detection range", "uom": {"code": "m"},
             "constraint": {"intervals": [[0.0, 100000.0]]}},
            {"type": "Quantity", "name": "maxRange_m",
             "definition": f"{_CSAPI}/detectionMaxRange",
             "label": "Maximum detection range", "uom": {"code": "m"},
             "constraint": {"intervals": [[0.0, 100000.0]]}},
            {"type": "Quantity", "name": "confidence",
             "definition": f"{_CSAPI}/detectionConfidence",
             "label": "Detection confidence", "uom": {"code": "1"},
             "constraint": {"intervals": [[0.0, 1.0]]}},
            {"type": "Text", "name": "basis",
             "definition": f"{_CSAPI}/detectionBasis",
             "label": "Basis of estimate"},
        ]
    }
}

ctx = ssl.create_default_context()

def _headers(content_type=None):
    import base64
    h = {"Authorization": "Basic " + base64.b64encode(AUTH.encode()).decode()}
    if content_type:
        h["Content-Type"] = content_type
    return h


def _request(method, url, body=None, ct="application/json"):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_headers(ct if body else None), method=method)
    for attempt in range(6):
        try:
            resp = urllib.request.urlopen(req, context=ctx, timeout=15)
            loc = resp.headers.get("Location")
            raw = resp.read().decode() if resp.length else ""
            return resp.status, loc, raw
        except urllib.error.HTTPError as e:
            return e.code, None, e.read().decode() if e.fp else ""
        except Exception as ex:
            if attempt < 5:
                wait = 2 ** attempt
                print(f"  [retry {attempt+1}] {ex} — waiting {wait}s")
                time.sleep(wait)
            else:
                raise


def create_datastream(system_id, n):
    """Create detection-capabilities datastream on a system."""
    url = f"{BASE}/systems/{system_id}/datastreams"
    body = {
        "name": f"AZ-MA-{n} Detection Capabilities",
        "description": f"Static detection range characteristics for AZ-MA-{n}.",
        "outputName": f"az_ma_{n}_detection_capabilities",
        "validTime": ["2026-01-01T00:00:00Z", "now"],
        "schema": DATASTREAM_SCHEMA,
    }
    code, loc, raw = _request("POST", url, body)
    if code == 201:
        ds_id = loc.rstrip("/").split("/")[-1] if loc else "?"
        print(f"  ✓ Datastream created: {ds_id} ({loc})")
        return ds_id
    elif code == 409:
        # Already exists — find it
        print(f"  ⚠ Already exists (409), finding existing DS...")
        code2, _, raw2 = _request("GET", f"{url}?outputName=az_ma_{n}_detection_capabilities")
        if code2 == 200:
            items = json.loads(raw2).get("items", [])
            if items:
                ds_id = items[0]["id"]
                print(f"  ✓ Found existing: {ds_id}")
                return ds_id
        print(f"  ✗ Could not find existing DS: {code2} {raw2[:200]}")
        return None
    else:
        print(f"  ✗ Failed to create DS: HTTP {code} — {raw[:200]}")
        return None


def post_observation(ds_id, n):
    """Post one observation with the detection range values."""
    url = f"{BASE}/datastreams/{ds_id}/observations"
    now = time.time()
    body = {
        "phenomenonTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "resultTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "result": {
            "timestamp": now,
            "shape": DETECTION_RANGE["shape"],
            "minRange_m": DETECTION_RANGE["minRange_m"],
            "nominalRange_m": DETECTION_RANGE["nominalRange_m"],
            "maxRange_m": DETECTION_RANGE["maxRange_m"],
            "confidence": DETECTION_RANGE["confidence"],
            "basis": DETECTION_RANGE["basis"],
        }
    }
    code, loc, raw = _request("POST", url, body)
    if code == 201:
        obs_id = loc.rstrip("/").split("/")[-1] if loc else "?"
        print(f"  ✓ Observation posted: {obs_id}")
        return obs_id
    else:
        print(f"  ✗ Failed to post obs: HTTP {code} — {raw[:200]}")
        return None


def verify(ds_id):
    """Read back the latest observation to confirm."""
    url = f"{BASE}/datastreams/{ds_id}/observations?limit=1"
    code, _, raw = _request("GET", url)
    if code == 200 and raw:
        try:
            data = json.loads(raw)
            items = data.get("items", [])
            if items:
                result = items[0].get("result", {})
                print(f"  ✓ Verified: maxRange={result.get('maxRange_m')}m, "
                      f"shape={result.get('shape')}, confidence={result.get('confidence')}")
                return True
        except json.JSONDecodeError:
            pass
    print(f"  ⚠ Verification inconclusive: HTTP {code} (data may still be persisted)")
    return False


def main():
    print("=" * 60)
    print("Adding detection-range datastreams to MA nodes")
    print("=" * 60)

    created = {}
    for node in NODES:
        n = node["n"]
        sid = node["system_id"]
        print(f"\n── AZ-MA-{n} (system {sid}) ──")

        ds_id = create_datastream(sid, n)
        if not ds_id:
            print(f"  ABORT for MA-{n}")
            continue

        obs_id = post_observation(ds_id, n)
        if not obs_id:
            continue

        time.sleep(1)
        verify(ds_id)
        created[f"MA-{n}"] = ds_id

    print(f"\n{'=' * 60}")
    print("Summary:")
    for name, dsid in created.items():
        print(f"  {name}: datastream {dsid}")
    print(f"{'=' * 60}")

    if len(created) == 3:
        print("\n✓ All 3 detection-capabilities datastreams created and populated.")
        print("  Frontend can now discover detection ranges via the CSAPI API.")
    else:
        print(f"\n⚠ Only {len(created)}/3 completed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
