"""Try to move ghost entries to subsystem index by POST as subsystem with same UID."""
import requests, json, time

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
SML_CT = {"Content-Type": "application/sml+json", "Accept": "application/json"}
GEO_H = {"Accept": "application/geo+json"}

def ordered(d):
    o = {}
    if "type" in d: o["type"] = d["type"]
    for k, v in d.items():
        if k != "type": o[k] = v
    return json.dumps(o)

ITEMS = [
    {"uid": "urn:os4csapi:system:odas:az-ma-1:tripod", "parent_id": "04ng", "old_id": "04p0"},
    {"uid": "urn:os4csapi:system:odas:az-ma-2:tripod", "parent_id": "04o0", "old_id": "04vg"},
    {"uid": "urn:os4csapi:system:odas:az-ma-3:tripod", "parent_id": "04og", "old_id": "0560"},
]

for item in ITEMS:
    print(f"\n=== {item['uid']} (ghost={item['old_id']}) ===")

    sml = {
        "type": "PhysicalSystem",
        "uniqueId": item["uid"],
        "label": f"MOVE-TO-SUB-{item['old_id']}",
    }

    # POST as subsystem under parent
    r = requests.post(f"{BASE}/systems/{item['parent_id']}/subsystems",
        data=ordered(sml),
        headers=SML_CT,
        auth=AUTH,
        allow_redirects=False)

    print(f"  POST /systems/{item['parent_id']}/subsystems: {r.status_code}")
    if r.status_code in (200, 201):
        loc = r.headers.get("Location", "")
        new_id = loc.rstrip("/").split("/")[-1] if "/" in loc else "?"
        print(f"  Location: {loc}")
        print(f"  ID: {new_id} (old was {item['old_id']})")
    elif r.status_code == 302:
        loc = r.headers.get("Location", "")
        eid = loc.rstrip("/").split("/")[-1] if "/" in loc else "?"
        print(f"  Redirect: existing ID={eid}")
    elif r.status_code == 409:
        print(f"  Conflict: {r.text[:200]}")
    else:
        ct = r.headers.get("content-type", "?")
        body = r.text[:200] if r.text and "html" not in ct.lower() else f"(content-type: {ct})"
        print(f"  Response: {body}")

time.sleep(2)

# Check listing
print("\n\n=== FINAL LISTING CHECK ===")
r = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=GEO_H)
items = r.json().get("items", r.json().get("features", []))
old_ids = {"04p0", "04vg", "0560"}
tripod_entries = [i for i in items if i["id"] in old_ids or "tripod" in i.get("properties",{}).get("name","").lower()]
print(f"Total: {len(items)} systems")
print(f"Tripod/ghost entries in top-level: {len(tripod_entries)}")
for t in tripod_entries:
    print(f"  {t['id']} = {t.get('properties',{}).get('name','?')}")

# Also check if old IDs are now in subsystem list
print("\n=== Subsystem check for ghost IDs ===")
for item in ITEMS:
    r = requests.get(f"{BASE}/systems/{item['parent_id']}/subsystems?limit=50", auth=AUTH, headers=GEO_H)
    subs = r.json().get("items", r.json().get("features", []))
    ghost_in_subs = [s for s in subs if s["id"] == item["old_id"]]
    tripod_in_subs = [s for s in subs if "tripod" in s.get("properties",{}).get("name","").lower()]
    print(f"  {item['parent_id']}: ghost {item['old_id']} in subs: {bool(ghost_in_subs)}, tripod subs: {len(tripod_in_subs)}")
    for t in tripod_in_subs:
        print(f"    {t['id']} = {t.get('properties',{}).get('name','?')}")
