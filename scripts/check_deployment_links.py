#!/usr/bin/env python3
"""Deep check on deployment↔system associations and hierarchy."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
GEO = {"Accept": "application/geo+json"}
JSON_H = {"Accept": "application/json"}

# ── 1. Check deployed systems for key deployments ──
print("=== DeployedSystems (deployment → systems) ===\n")

dep_map = {
    "04cg": "AOI Deployment",
    "04d0": "Network Deployment",
    "04dg": "Deployment AZ-MA-1",
    "04e0": "Deployment AZ-MA-2",
    "04eg": "Deployment AZ-MA-3",
}

for dep_id, name in dep_map.items():
    # Try /deployments/{id}/deployedSystems
    r = requests.get(f"{BASE}/deployments/{dep_id}/deployedSystems", auth=AUTH, headers=GEO)
    print(f"  {dep_id} ({name}):")
    print(f"    GET /deployments/{dep_id}/deployedSystems → HTTP {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        items = data.get("items", data.get("features", []))
        print(f"    count: {len(items)}")
        for item in items:
            props = item.get("properties", {})
            print(f"      {item.get('id')} = {props.get('name', '?')}")
    print()

# ── 2. Check subdeployments from the hierarchy root ──
print("=== Subdeployments ===\n")

for dep_id, name in dep_map.items():
    r = requests.get(f"{BASE}/deployments/{dep_id}/subdeployments?limit=50", auth=AUTH, headers=GEO)
    if r.status_code == 200:
        items = r.json().get("items", r.json().get("features", []))
        sub_names = [s.get("properties", {}).get("name", "?") for s in items]
        print(f"  {dep_id} ({name}): {len(items)} subdeployments")
        for sn in sub_names:
            print(f"    - {sn}")
    else:
        print(f"  {dep_id} ({name}): HTTP {r.status_code}")
    print()

# ── 3. Check ALL deployment links ──
print("=== Deployment link rels ===\n")
r = requests.get(f"{BASE}/deployments?limit=50", auth=AUTH, headers=GEO)
deps = r.json().get("items", r.json().get("features", []))
for d in deps:
    did = d["id"]
    name = d.get("properties", {}).get("name", "?")
    links = d.get("links", [])
    rels = [l.get("rel") for l in links]
    non_standard = [l for l in links if l.get("rel") not in ["self", "collection", "alternate", "canonical"]]
    if non_standard:
        print(f"  {did} ({name}): {[l.get('rel') for l in non_standard]}")

# ── 4. Check if our subsystem deployments exist (sub-deployments under node deployments) ──
print("\n=== Subsystem-level deployments ===\n")
sub_deps = {
    "04f0": "Deployment AZ-MA-1-MICARRAY",
    "04fg": "Deployment AZ-MA-1-EDGE",
    "04g0": "Deployment AZ-MA-1-COMMS",
    "04gg": "Deployment AZ-MA-1-POWER",
    "04h0": "Deployment AZ-MA-1-ACTUATOR",
}
for dep_id, name in sub_deps.items():
    # Check if this is a subdeployment of anything
    r = requests.get(f"{BASE}/deployments/{dep_id}", auth=AUTH, headers=GEO)
    if r.status_code == 200:
        data = r.json()
        links = data.get("links", [])
        parent_link = [l for l in links if l.get("rel") == "parent"]
        print(f"  {dep_id} ({name}):")
        print(f"    parent link: {json.dumps(parent_link) if parent_link else 'NONE'}")
        # Check deployed systems
        r2 = requests.get(f"{BASE}/deployments/{dep_id}/deployedSystems", auth=AUTH, headers=GEO)
        if r2.status_code == 200:
            items = r2.json().get("items", r2.json().get("features", []))
            print(f"    deployed systems: {len(items)}")
        else:
            print(f"    deployed systems: HTTP {r2.status_code}")
