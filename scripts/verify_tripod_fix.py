"""Quick verification that tripod fix worked."""
import requests
BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
H = {"Accept": "application/geo+json"}

# Check old IDs are gone
print("=== Old IDs ===")
for old_id in ["04p0", "04vg", "0560"]:
    r = requests.get(f"{BASE}/systems/{old_id}", auth=AUTH, headers=H)
    print(f"  GET /systems/{old_id}: HTTP {r.status_code}")

# Top-level search
print("\n=== q=az (top-level) ===")
r = requests.get(f"{BASE}/systems?q=az&limit=20", auth=AUTH, headers=H)
items = r.json().get("items", r.json().get("features", []))
print(f"  {len(items)} results")
for it in items:
    sid = it.get("id", "?")
    name = it.get("properties", {}).get("name", "?")
    print(f"    {sid} = {name}")

print("\n=== q=tripod (top-level) ===")
r2 = requests.get(f"{BASE}/systems?q=tripod&limit=20", auth=AUTH, headers=H)
items2 = r2.json().get("items", r2.json().get("features", []))
print(f"  {len(items2)} results")
for it in items2:
    sid = it.get("id", "?")
    name = it.get("properties", {}).get("name", "?")
    print(f"    {sid} = {name}")

# New IDs as subsystems
print("\n=== New subsystem-only IDs ===")
for new_id, parent_id, label in [("05cg", "04ng", "MA-1"), ("05d0", "04o0", "MA-2"), ("05dg", "04og", "MA-3")]:
    r3 = requests.get(f"{BASE}/systems/{new_id}", auth=AUTH, headers=H)
    if r3.ok:
        d = r3.json()
        name = d.get("properties", {}).get("name", "?")
        links = d.get("links", [])
        parent = [l for l in links if l.get("rel") == "parent"]
        in_top = new_id in [it.get("id") for it in items]
        print(f"  {new_id} = {name}  parent_link={bool(parent)}  in_top_level={in_top}")
    else:
        print(f"  {new_id}: HTTP {r3.status_code}")

# Full top-level count
print("\n=== Top-level total ===")
r4 = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=H)
items4 = r4.json().get("items", r4.json().get("features", []))
print(f"  {len(items4)} systems")
az_count = sum(1 for it in items4 if "az" in it.get("properties", {}).get("name", "").lower())
print(f"  Of those, {az_count} contain 'az' in name")
