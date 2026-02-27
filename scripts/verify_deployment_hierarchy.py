#!/usr/bin/env python3
"""Verify deployment hierarchy after migration."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
GEO = {"Accept": "application/geo+json"}

# 1. Check parent links on node and sub-deployments
print("=== Parent links ===\n")
for dep_id, name in [("04dg", "AZ-MA-1"), ("04e0", "AZ-MA-2"), ("04f0", "MA-1-MICARRAY"), ("04k0", "MA-3-MICARRAY")]:
    r = requests.get(f"{BASE}/deployments/{dep_id}", auth=AUTH, headers=GEO)
    d = r.json()
    props = d.get("properties", {})
    links = d.get("links", [])
    parent = [l for l in links if l.get("rel") == "parent"]
    subdeps = [l for l in links if l.get("rel") == "subdeployments"]
    print(f"  {dep_id} ({name}):")
    if parent:
        print(f"    parent: {parent[0].get('href', '?')}")
    else:
        print(f"    parent: NONE")
    if subdeps:
        print(f"    subdeployments link: YES")
    # Show all properties
    for k, v in props.items():
        if "@link" in k or k == "description":
            val = json.dumps(v) if isinstance(v, (list, dict)) else str(v)
            print(f"    {k} = {val[:100]}")
    print()

# 2. Verify only AOI, NET, and smoke tests appear at top level
print("=== Top-level listing ===\n")
r = requests.get(f"{BASE}/deployments?limit=50", auth=AUTH, headers=GEO)
items = r.json().get("items", r.json().get("features", []))
print(f"  Total: {len(items)}")
for it in items:
    n = it.get("properties", {}).get("name", "?")
    links = it.get("links", [])
    has_parent = any(l.get("rel") == "parent" for l in links)
    marker = " [HAS PARENT - should not be top-level!]" if has_parent else ""
    print(f"  {it['id']} = {n}{marker}")

# 3. Check recursive subdeployments from AOI
print("\n=== Full tree from AOI (04cg) ===\n")
r = requests.get(f"{BASE}/deployments/04cg/subdeployments?limit=50", auth=AUTH, headers=GEO)
nodes = r.json().get("items", r.json().get("features", []))
print(f"  AOI (04cg) → {len(nodes)} subdeployments")
for node in nodes:
    nid = node["id"]
    nn = node.get("properties", {}).get("name", "?")
    print(f"    {nid} = {nn}")
    r2 = requests.get(f"{BASE}/deployments/{nid}/subdeployments?limit=50", auth=AUTH, headers=GEO)
    if r2.status_code == 200:
        subs = r2.json().get("items", r2.json().get("features", []))
        for s in subs:
            sn = s.get("properties", {}).get("name", "?")
            print(f"      {s['id']} = {sn}")
