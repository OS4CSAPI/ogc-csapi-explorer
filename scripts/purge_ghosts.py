"""Try to purge ghost entries by re-creating then deleting with same UID."""
import requests, json, time

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
SML_CT = {"Content-Type": "application/sml+json", "Accept": "application/json"}
GEO_H = {"Accept": "application/geo+json"}

GHOSTS = [
    {"uid": "urn:os4csapi:system:odas:az-ma-1:tripod", "old_id": "04p0", "name": "CLEANUP-1"},
    {"uid": "urn:os4csapi:system:odas:az-ma-2:tripod", "old_id": "04vg", "name": "CLEANUP-2"},
    {"uid": "urn:os4csapi:system:odas:az-ma-3:tripod", "old_id": "0560", "name": "CLEANUP-3"},
]

def ordered_sml(d):
    ordered = {}
    if "type" in d:
        ordered["type"] = d["type"]
    for k, v in d.items():
        if k != "type":
            ordered[k] = v
    return json.dumps(ordered)

for g in GHOSTS:
    sml = {
        "type": "PhysicalSystem",
        "uniqueId": g["uid"],
        "label": g["name"],
    }
    print(f"\n=== {g['uid']} (old_id={g['old_id']}) ===")

    # Try POST /systems with same UID
    r = requests.post(f"{BASE}/systems",
        data=ordered_sml(sml),
        headers=SML_CT,
        auth=AUTH,
        allow_redirects=False)

    print(f"  POST /systems: {r.status_code}")
    print(f"  Content-Type: {r.headers.get('content-type', '?')}")
    if r.status_code in (200, 201):
        loc = r.headers.get("Location", "")
        new_id = loc.rstrip("/").split("/")[-1] if "/" in loc else "?"
        print(f"  Location: {loc}")
        print(f"  New ID: {new_id}")

        # Now delete this entry
        r2 = requests.delete(f"{BASE}/systems/{new_id}?cascade=true", auth=AUTH)
        print(f"  DELETE /systems/{new_id}: {r2.status_code}")
    elif r.status_code == 409:
        print("  Conflict — UID collision")
        body = r.text[:400]
        print(f"  Body: {body}")
    elif r.status_code == 302:
        loc = r.headers.get("Location", "")
        print(f"  Redirect to: {loc}")
        # Server already has this UID — extract existing ID
        eid = loc.rstrip("/").split("/")[-1] if "/" in loc else "?"
        print(f"  Existing ID: {eid}")
        # Try deleting that
        r2 = requests.delete(f"{BASE}/systems/{eid}?cascade=true", auth=AUTH)
        print(f"  DELETE /systems/{eid}: {r2.status_code}")
    else:
        body = r.text[:400] if r.text else ""
        print(f"  Unexpected: {body}")

time.sleep(2)

# Check final state
print("\n\n=== FINAL LISTING CHECK ===")
r = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=GEO_H)
items = r.json().get("items", r.json().get("features", []))
old_ids = {"04p0", "04vg", "0560"}
tripods = [i for i in items if i["id"] in old_ids or "tripod" in i.get("properties",{}).get("name","").lower()]
print(f"Total systems: {len(items)}")
print(f"Tripod/ghost entries: {len(tripods)}")
for t in tripods:
    print(f"  {t['id']} = {t.get('properties',{}).get('name','?')}")
