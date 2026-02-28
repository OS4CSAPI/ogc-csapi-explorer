"""Check if tripods appear in the full system listing (no search filter)."""
import requests

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")

r = requests.get(f"{BASE}/systems?limit=100&f=json", auth=AUTH)
items = r.json().get("items", [])
print(f"Total systems in listing: {len(items)}")

tripods = [i for i in items if "tripod" in i.get("properties", {}).get("name", "").lower()]
print(f"Tripods in listing: {len(tripods)}")
for t in tripods:
    print(f"  {t['id']} = {t['properties']['name']}")

# Also check: does the listing include the OLD ids?
old_ids = {"04p0", "04vg", "0560"}
new_ids = {"05cg", "05d0", "05dg"}
listed_ids = {i["id"] for i in items}
print(f"\nOld IDs in listing: {old_ids & listed_ids}")
print(f"New IDs in listing: {new_ids & listed_ids}")

# Try direct GET on each old id
for oid in sorted(old_ids):
    r2 = requests.get(f"{BASE}/systems/{oid}?f=json", auth=AUTH)
    print(f"GET /systems/{oid}: {r2.status_code}")
