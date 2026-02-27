"""Compare UIDs between ghost entries and new subsystem entries."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
H = {"Accept": "application/geo+json"}

# Get ghost UIDs from listing
r = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=H)
data = r.json()
items = data.get("items", data.get("features", []))
OLD_IDS = {"04p0", "04vg", "0560"}

print("=== Ghost entries (from listing) ===")
ghost_uids = {}
for it in items:
    if it["id"] in OLD_IDS:
        uid = it.get("properties", {}).get("uid", "?")
        ghost_uids[it["id"]] = uid
        print(f"  {it['id']}: uid={uid}")

# Get new subsystem UIDs
print("\n=== New subsystem entries ===")
for nid in ["05cg", "05d0", "05dg"]:
    r2 = requests.get(f"{BASE}/systems/{nid}", auth=AUTH, headers=H)
    if r2.ok:
        d = r2.json()
        uid = d.get("properties", {}).get("uid", "?")
        name = d.get("properties", {}).get("name", "?")
        print(f"  {nid}: uid={uid}  name={name}")

# Try: can we PUT to the ghost IDs to update them?
print("\n=== Try PUT on ghost ID 04p0 ===")
r3 = requests.put(f"{BASE}/systems/04p0",
    auth=AUTH,
    headers={"Content-Type": "application/sml+json"},
    json={"type": "SimpleProcess", "uniqueId": "urn:os4csapi:system:odas:az-ma-1:tripod:DELETED", "name": "DELETED"})
print(f"  PUT /systems/04p0: {r3.status_code} {r3.text[:200] if r3.text else ''}")

# Try: POST with same UID to see what server does
print("\n=== Try POST /systems with same UID as ghost ===")
r4 = requests.post(f"{BASE}/systems",
    auth=AUTH,
    headers={"Content-Type": "application/sml+json"},
    json={
        "type": "PhysicalSystem",
        "uniqueId": "urn:os4csapi:system:odas:az-ma-1:tripod",
        "name": "TEMP_CLEANUP"
    })
print(f"  POST /systems: {r4.status_code}")
if r4.status_code == 201:
    loc = r4.headers.get("Location", "?")
    print(f"  Location: {loc}")
    # Extract new id and delete it
    new_id = loc.rstrip("/").split("/")[-1]
    print(f"  New ID: {new_id}")
    # Now delete this new one
    r5 = requests.delete(f"{BASE}/systems/{new_id}", auth=AUTH)
    print(f"  DELETE /systems/{new_id}: {r5.status_code}")
elif r4.status_code == 409:
    print("  Conflict - UID already exists (expected if ghost blocks it)")
    print(f"  Response: {r4.text[:300]}")
else:
    print(f"  Response: {r4.text[:300]}")
