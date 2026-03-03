"""
Fix LOB datastream schemas: delete old (no classification) → recreate with classification field.

All 3 LOB datastreams have 0 observations (cleared earlier), so nothing is lost.
The new schema adds a 'classification' Text field as field #7.

NOTE: 0420 was already deleted by the probe script. This script handles the remaining
two AND recreates all three with the correct schema.
"""
import json, ssl, base64, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
AUTH = "Basic " + base64.b64encode(b"os4csapi:ogc134mm").decode()
BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"

_ODAS = "https://os4csapi.org/def/odas"
_CSAPI = "https://os4csapi.org/def/csapi"

# Mapping: (old_ds_id, system_id, node_label, output_name)
LOB_STREAMS = [
    ("0420", "0420", "AZ-MA-1", "az_ma_1_lob"),
    ("0460", "0490", "AZ-MA-2", "az_ma_2_lob"),
    ("049g", "049g", "AZ-MA-3", "az_ma_3_lob"),
]


def _make_schema(node_label, output_name):
    """Build the corrected LOB schema with classification field."""
    return {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "name": output_name,
            "definition": f"{_ODAS}/track/lobRecordOSH",
            "label": "LOB",
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
                    "name": "bearingTrue",
                    "definition": f"{_ODAS}/bearingTrue",
                    "label": "Bearing true",
                    "uom": {"code": "deg"},
                    "constraint": {"intervals": [[0.0, 360.0]]},
                },
                {
                    "type": "Quantity",
                    "name": "bearingStdDev",
                    "definition": f"{_ODAS}/bearingStdDev",
                    "label": "Bearing std dev",
                    "uom": {"code": "deg"},
                },
                {
                    "type": "Quantity",
                    "name": "sensorLat",
                    "definition": f"{_CSAPI}/sensorLat",
                    "label": "Sensor lat",
                    "uom": {"code": "deg"},
                    "constraint": {"intervals": [[-90.0, 90.0]]},
                },
                {
                    "type": "Quantity",
                    "name": "sensorLon",
                    "definition": f"{_CSAPI}/sensorLon",
                    "label": "Sensor lon",
                    "uom": {"code": "deg"},
                    "constraint": {"intervals": [[-180.0, 180.0]]},
                },
                # ── NEW FIELD ──
                {
                    "type": "Text",
                    "name": "classification",
                    "definition": f"{_ODAS}/classification",
                    "label": "Classification",
                },
            ],
        },
    }


def _req(url, method="GET", data=None, content_type=None):
    """Make an authenticated request with retry."""
    headers = {"Authorization": AUTH, "Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    body = json.dumps(data).encode() if data else None
    for attempt in range(5):
        try:
            req = Request(url, headers=headers, data=body, method=method)
            r = urlopen(req, timeout=20, context=ctx)
            if r.status == 204:
                return None
            return json.loads(r.read().decode())
        except HTTPError as e:
            if e.code == 404:
                return "NOT_FOUND"
            raise
        except Exception as e:
            if attempt < 4:
                wait = 3 * (attempt + 1)
                print(f"    retry in {wait}s: {e}")
                time.sleep(wait)
            else:
                raise


def main():
    for old_id, sys_id, label, out_name in LOB_STREAMS:
        print(f"\n{'='*60}")
        print(f"  {label} LOB  (old DS id: {old_id}, system: {sys_id})")
        print(f"{'='*60}")

        # Step 1: Delete old datastream (if it still exists)
        check = _req(f"{BASE}/datastreams/{old_id}")
        if check == "NOT_FOUND":
            print(f"  [skip] {old_id} already deleted")
        else:
            print(f"  [delete] {old_id}...")
            _req(f"{BASE}/datastreams/{old_id}", method="DELETE")
            print(f"  [deleted] {old_id}")
            time.sleep(1)

        # Step 2: Create new datastream with corrected schema
        schema = _make_schema(label, out_name)
        payload = {
            "name": f"{label} LOB",
            "description": "LOB derived with classification field.",
            "outputName": out_name,
            "validTime": ["2026-01-01T00:00:00Z", "now"],
            "schema": schema,
        }

        url = f"{BASE}/systems/{sys_id}/datastreams"
        print(f"  [create] POST {url}")
        headers = {"Authorization": AUTH, "Content-Type": "application/sml+json", "Accept": "application/json"}

        body = json.dumps(payload).encode()
        for attempt in range(5):
            try:
                req = Request(url, headers=headers, data=body, method="POST")
                r = urlopen(req, timeout=20, context=ctx)
                loc = r.headers.get("Location", "")
                new_id = loc.rstrip("/").split("/")[-1] if loc else "?"
                print(f"  [created] new DS id: {new_id}  (HTTP {r.status})")
                break
            except HTTPError as e:
                body_text = e.read().decode() if hasattr(e, "read") else ""
                print(f"  [error] HTTP {e.code}: {body_text[:300]}")
                # Try application/json content type instead
                if attempt == 0:
                    headers["Content-Type"] = "application/json"
                    print("  [retry] switching Content-Type to application/json")
                elif attempt < 4:
                    time.sleep(3)
                else:
                    raise
            except Exception as e:
                if attempt < 4:
                    print(f"  [retry] {e}")
                    time.sleep(3 * (attempt + 1))
                else:
                    raise

    # Verify all LOB datastreams
    print(f"\n{'='*60}")
    print("  VERIFICATION")
    print(f"{'='*60}")

    # List all datastreams to find the new LOB ones
    all_ds = _req(f"{BASE}/datastreams?limit=100")
    for item in all_ds.get("items", []):
        name = item.get("name", "")
        if "LOB" in name:
            ds_id = item["id"]
            # Fetch schema
            schema = _req(f"{BASE}/datastreams/{ds_id}/schema")
            fields = schema.get("resultSchema", {}).get("fields", [])
            field_names = [f["name"] for f in fields]
            has_class = "classification" in field_names
            print(f"  {ds_id}: {name:25s}  fields={field_names}")
            print(f"         classification: {'YES' if has_class else 'NO'}")


if __name__ == "__main__":
    main()
