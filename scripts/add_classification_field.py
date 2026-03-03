"""Add 'classification' Text field to the LOB datastream schema on the server."""

import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = ("os4csapi", "ogc134mm")

LOB_DS_IDS = ["0420", "0460", "049g"]

CLASSIFICATION_FIELD = {
    "type": "Text",
    "name": "classification",
    "definition": "https://os4csapi.org/def/odas/classification",
    "label": "Classification",
}


def main():
    s = requests.Session()
    s.auth = AUTH
    s.verify = False

    for ds_id in LOB_DS_IDS:
        r = s.get(f"{BASE}/datastreams/{ds_id}", timeout=20)
        ds = r.json()
        name = ds.get("name", "?")
        print(f"[{ds_id}] {name}")

        r2 = s.get(f"{BASE}/datastreams/{ds_id}/schema", timeout=20)
        schema = r2.json()
        fields = schema.get("resultSchema", {}).get("fields", [])

        if any(f.get("name") == "classification" for f in fields):
            print("  classification field already exists")
            continue

        fields.append(CLASSIFICATION_FIELD)
        schema["resultSchema"]["fields"] = fields

        r3 = s.put(
            f"{BASE}/datastreams/{ds_id}/schema",
            json=schema,
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        print(f"  PUT schema: HTTP {r3.status_code}")
        if r3.status_code not in (200, 204):
            print(f"  Response: {r3.text[:300]}")

    # Verify
    print("\nVerifying schemas...")
    for ds_id in LOB_DS_IDS:
        r = s.get(f"{BASE}/datastreams/{ds_id}/schema", timeout=20)
        schema = r.json()
        field_names = [f["name"] for f in schema.get("resultSchema", {}).get("fields", [])]
        has_class = "classification" in field_names
        print(f"  [{ds_id}] fields: {field_names} -> classification: {'YES' if has_class else 'NO'}")

    s.close()


if __name__ == "__main__":
    main()
