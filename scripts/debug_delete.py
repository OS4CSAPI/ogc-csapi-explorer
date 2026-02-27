"""Debug the DELETE failure — the server creates but refuses to delete."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
GEO_H = {"Accept": "application/geo+json"}
SML_H = {"Accept": "application/sml+json"}

OLD_IDS = ["04p0", "04vg", "0560"]

# Step 1: Can we GET the entries?
print("=== Direct GET ===")
for oid in OLD_IDS:
    for h_name, h in [("geo+json", GEO_H), ("sml+json", SML_H)]:
        r = requests.get(f"{BASE}/systems/{oid}", auth=AUTH, headers=h)
        name = ""
        if r.ok:
            try:
                d = r.json()
                name = d.get("properties", d).get("name", d.get("label", "?"))
            except:
                name = "(non-json)"
        print(f"  GET /systems/{oid} ({h_name}): {r.status_code} {name}")

# Step 2: Try DELETE without cascade
print("\n=== DELETE without cascade ===")
for oid in OLD_IDS:
    r = requests.delete(f"{BASE}/systems/{oid}", auth=AUTH)
    print(f"  DELETE /systems/{oid}: {r.status_code} {r.text[:100] if r.text else ''}")

# Step 3: Try DELETE with explicit Accept
print("\n=== DELETE with Accept header ===")
for oid in OLD_IDS:
    r = requests.delete(f"{BASE}/systems/{oid}",
        auth=AUTH,
        headers={"Accept": "application/json"})
    print(f"  DELETE /systems/{oid}: {r.status_code} {r.text[:100] if r.text else ''}")

# Step 4: Re-create one and immediately GET + DELETE
print("\n=== Re-create, GET, then DELETE 04p0 ===")
sml = {"type": "PhysicalSystem", "uniqueId": "urn:os4csapi:system:odas:az-ma-1:tripod", "label": "DELETE-ME"}
r = requests.post(f"{BASE}/systems",
    data=json.dumps(sml),
    headers={"Content-Type": "application/sml+json", "Accept": "application/json"},
    auth=AUTH, allow_redirects=False)
print(f"  POST: {r.status_code} Location={r.headers.get('Location','?')}")

# Immediate GET
r2 = requests.get(f"{BASE}/systems/04p0", auth=AUTH, headers=GEO_H)
print(f"  GET: {r2.status_code}")
if r2.ok:
    try:
        print(f"  Name: {r2.json().get('properties',{}).get('name','?')}")
    except:
        pass

# DELETE using full URL from Location header  
loc = r.headers.get("Location", "")
if loc:
    full_url = f"http://45.55.99.236:8080/sensorhub/api{loc}"
    print(f"  DELETE (full URL): {full_url}")
    r3 = requests.delete(full_url, auth=AUTH)
    print(f"  Result: {r3.status_code}")

# Also try the path-based delete
r4 = requests.delete(f"{BASE}{loc}", auth=AUTH)
print(f"  DELETE {BASE}{loc}: {r4.status_code}")

# Step 5: Check listing one more time
print("\n=== Listing summary ===")
r5 = requests.get(f"{BASE}/systems?limit=100", auth=AUTH, headers=GEO_H)
items = r5.json().get("items", r5.json().get("features", []))
old_set = set(OLD_IDS)
for it in items:
    if it["id"] in old_set:
        print(f"  GHOST: {it['id']} = {it.get('properties',{}).get('name','?')}")
print(f"  Total: {len(items)} systems, {sum(1 for i in items if i['id'] in old_set)} ghosts")
