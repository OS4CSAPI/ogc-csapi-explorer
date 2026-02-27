"""Check what the listing returns for ghost tripod entries."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
H = {"Accept": "application/geo+json"}
OLD_IDS = {"04p0", "04vg", "0560"}

r = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=H)
data = r.json()
items = data.get("items", data.get("features", []))

print(f"Total items in listing: {len(items)}")
print(f"\n=== Ghost entries (old tripod IDs) ===")
for it in items:
    sid = it.get("id", "?")
    if sid in OLD_IDS:
        print(f"\n--- {sid} ---")
        print(json.dumps(it, indent=2)[:800])

# Also test: what does the server return for /systems?q=tripod
print(f"\n\n=== Search: q=tripod ===")
r2 = requests.get(f"{BASE}/systems?q=tripod&limit=20", auth=AUTH, headers=H)
data2 = r2.json()
items2 = data2.get("items", data2.get("features", []))
print(f"Results: {len(items2)}")
for it in items2:
    print(f"  {it.get('id','?')} = {it.get('properties',{}).get('name','?')}")

# Fresh test: use different Accept header
print(f"\n=== Using Accept: application/json ===")
H2 = {"Accept": "application/json"}
for oid in sorted(OLD_IDS):
    r3 = requests.get(f"{BASE}/systems/{oid}", auth=AUTH, headers=H2)
    print(f"  GET {oid} (app/json): {r3.status_code} content-type={r3.headers.get('content-type','?')}")
    if r3.ok and r3.text:
        print(f"    body preview: {r3.text[:200]}")

print(f"\n=== Using Accept: application/sml+json ===")
H3 = {"Accept": "application/sml+json"}
for oid in sorted(OLD_IDS):
    r4 = requests.get(f"{BASE}/systems/{oid}", auth=AUTH, headers=H3)
    print(f"  GET {oid} (sml+json): {r4.status_code}")
