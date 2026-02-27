"""Re-attempt tripod deletion with immediate verification."""
import requests
import time

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
H = {"Accept": "application/geo+json"}

OLD_IDS = ["04p0", "04vg", "0560"]

# Step 1: Check current state
print("=== PRE-DELETE STATE ===")
for oid in OLD_IDS:
    r = requests.get(f"{BASE}/systems/{oid}", auth=AUTH, headers=H)
    if r.ok:
        d = r.json()
        name = d.get("properties", {}).get("name", "?")
        links = d.get("links", [])
        parent_links = [l for l in links if l.get("rel") == "parent"]
        print(f"  {oid}: {r.status_code} name={name} parent_links={len(parent_links)}")
        if parent_links:
            print(f"         parent href: {parent_links[0].get('href','?')}")
    else:
        print(f"  {oid}: {r.status_code}")

# Check if they exist as subsystems under their parents
PARENT_MAP = {"04p0": "04ng", "04vg": "04o0", "0560": "04og"}
print("\n=== SUBSYSTEM CHECK ===")
for oid, pid in PARENT_MAP.items():
    r = requests.get(f"{BASE}/systems/{pid}/subsystems?limit=50", auth=AUTH, headers=H)
    if r.ok:
        items = r.json().get("items", r.json().get("features", []))
        sub_ids = [i["id"] for i in items]
        print(f"  {oid} in subsystems of {pid}: {oid in sub_ids}")
        # Also list all subsystems
        for i in items:
            mark = " <-- THIS ONE" if i["id"] == oid else ""
            print(f"    {i['id']} = {i.get('properties',{}).get('name','?')}{mark}")

# Step 2: Delete with cascade
print("\n=== DELETING (with cascade) ===")
for oid in OLD_IDS:
    r = requests.delete(f"{BASE}/systems/{oid}?cascade=true", auth=AUTH)
    print(f"  DELETE /systems/{oid}?cascade=true: {r.status_code}")

time.sleep(2)

# Step 3: Verify immediately
print("\n=== POST-DELETE VERIFY (2s wait) ===")
for oid in OLD_IDS:
    r = requests.get(f"{BASE}/systems/{oid}", auth=AUTH, headers=H)
    print(f"  GET /systems/{oid}: {r.status_code}")

# Check listing
r = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=H)
items = r.json().get("items", r.json().get("features", []))
listed_ids = {i["id"] for i in items}
print(f"\n  Total in listing: {len(items)}")
for oid in OLD_IDS:
    print(f"  {oid} in listing: {oid in listed_ids}")

# Check subsystems
print("\n=== POST-DELETE SUBSYSTEM CHECK ===")
for oid, pid in PARENT_MAP.items():
    r = requests.get(f"{BASE}/systems/{pid}/subsystems?limit=50", auth=AUTH, headers=H)
    if r.ok:
        items2 = r.json().get("items", r.json().get("features", []))
        sub_ids2 = [i["id"] for i in items2]
        print(f"  {oid} still subsystem of {pid}: {oid in sub_ids2}")
    else:
        print(f"  GET subsystems of {pid}: {r.status_code}")

# New subsystem IDs still intact?
print("\n=== NEW IDS STILL VALID? ===")
for nid in ["05cg", "05d0", "05dg"]:
    r = requests.get(f"{BASE}/systems/{nid}", auth=AUTH, headers=H)
    if r.ok:
        d = r.json()
        name = d.get("properties", {}).get("name", "?")
        print(f"  {nid}: {r.status_code} name={name}")
    else:
        print(f"  {nid}: {r.status_code}")
