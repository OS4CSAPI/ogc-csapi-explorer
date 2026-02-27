"""Update ghost entry names back to something reasonable and document findings."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
SML_CT = {"Content-Type": "application/sml+json", "Accept": "application/json"}
GEO_H = {"Accept": "application/geo+json"}

def ordered(d):
    o = {}
    if "type" in d: o["type"] = d["type"]
    for k,v in d.items():
        if k != "type": o[k] = v
    return json.dumps(o)

# Re-POST with original names so the listing doesn't show "CLEANUP" / "DELETE-ME"
GHOSTS = [
    {"uid": "urn:os4csapi:system:odas:az-ma-1:tripod", "old_id": "04p0",
     "name": "AZ-MA-1 TRIPOD", "desc": "[Ghost] Server index artifact – use subsystem 05cg instead"},
    {"uid": "urn:os4csapi:system:odas:az-ma-2:tripod", "old_id": "04vg",
     "name": "AZ-MA-2 TRIPOD", "desc": "[Ghost] Server index artifact – use subsystem 05d0 instead"},
    {"uid": "urn:os4csapi:system:odas:az-ma-3:tripod", "old_id": "0560",
     "name": "AZ-MA-3 TRIPOD", "desc": "[Ghost] Server index artifact – use subsystem 05dg instead"},
]

for g in GHOSTS:
    sml = {
        "type": "PhysicalSystem",
        "uniqueId": g["uid"],
        "label": g["name"],
        "description": g["desc"],
    }
    r = requests.post(f"{BASE}/systems", data=ordered(sml),
        headers=SML_CT, auth=AUTH, allow_redirects=False)
    print(f"  POST {g['old_id']}: {r.status_code} (name restored to '{g['name']}')")

# Verify
r = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=GEO_H)
items = r.json().get("items", r.json().get("features", []))
old_ids = {"04p0", "04vg", "0560"}
print(f"\nListing: {len(items)} total")
for it in items:
    if it["id"] in old_ids:
        p = it.get("properties", {})
        print(f"  {it['id']} = {p.get('name','?')} | {p.get('description','')[:60]}")
