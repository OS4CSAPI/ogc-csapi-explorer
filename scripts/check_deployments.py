#!/usr/bin/env python3
"""Check deployment resources, their system links, and hierarchy on the server."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
GEO = {"Accept": "application/geo+json"}
SML = {"Accept": "application/sml+json"}

# ── 1. Get all deployments ──
r = requests.get(f"{BASE}/deployments?limit=50", auth=AUTH, headers=GEO)
deps = r.json().get("items", r.json().get("features", []))
print(f"=== Total deployments: {len(deps)} ===\n")

for d in deps:
    did = d["id"]
    props = d.get("properties", {})
    links = d.get("links", [])
    interesting = [l for l in links if l.get("rel") not in ["self", "collection", "alternate"]]
    print(f"  {did} = {props.get('name', '?')}")
    if interesting:
        for lk in interesting:
            print(f"    link: rel={lk.get('rel')}  href={lk.get('href')}")

# ── 2. Check system→deployment links for key systems ──
print("\n=== System → Deployment associations ===\n")
key_systems = {
    "04n0": "AZ-MA-NET",
    "04ng": "AZ-MA-1",
    "04o0": "AZ-MA-2",
    "04og": "AZ-MA-3",
}
for sid, name in key_systems.items():
    # Check if system has deployment links
    r = requests.get(f"{BASE}/systems/{sid}", auth=AUTH, headers=GEO)
    if r.status_code == 200:
        sys_data = r.json()
        sys_links = sys_data.get("links", [])
        dep_links = [l for l in sys_links if "deploy" in l.get("rel", "").lower() or "deploy" in l.get("href", "").lower()]
        all_rels = [l.get("rel") for l in sys_links]
        print(f"  {sid} ({name})")
        print(f"    all link rels: {all_rels}")
        if dep_links:
            print(f"    deployment links: {json.dumps(dep_links, indent=6)}")
        else:
            print(f"    deployment links: NONE")
    else:
        print(f"  {sid} ({name}): HTTP {r.status_code}")

# ── 3. Check if deployments have system associations (SML format) ──
print("\n=== Deployment SML details (first 3) ===\n")
for d in deps[:3]:
    did = d["id"]
    name = d.get("properties", {}).get("name", "?")
    r = requests.get(f"{BASE}/deployments/{did}", auth=AUTH, headers=SML)
    if r.status_code == 200:
        sml = r.json()
        print(f"  {did} ({name}):")
        print(f"    type: {sml.get('type')}")
        # Check for system/platform references
        for key in ["deployedSystems", "deployedPlatforms", "components", "members", "featuresOfInterest"]:
            if key in sml:
                print(f"    {key}: {json.dumps(sml[key])}")
        # See what keys exist
        print(f"    top-level keys: {list(sml.keys())}")
        print()
    else:
        print(f"  {did} ({name}): HTTP {r.status_code}")

# ── 4. Check subdeployments ──
print("\n=== Subdeployment check (root-level deployments only) ===\n")
root_deps = [d for d in deps if "AZ-MA-" in d.get("properties", {}).get("name", "") and "MICARRAY" not in d.get("properties", {}).get("name", "") and "EDGE" not in d.get("properties", {}).get("name", "") and "COMMS" not in d.get("properties", {}).get("name", "") and "POWER" not in d.get("properties", {}).get("name", "") and "ACTUATOR" not in d.get("properties", {}).get("name", "")]
for d in root_deps:
    did = d["id"]
    name = d.get("properties", {}).get("name", "?")
    r = requests.get(f"{BASE}/deployments/{did}/subdeployments?limit=50", auth=AUTH, headers=GEO)
    if r.status_code == 200:
        subs = r.json().get("items", r.json().get("features", []))
        sub_names = [s.get("properties", {}).get("name", "?") for s in subs]
        print(f"  {did} ({name}): {len(subs)} subdeployments = {sub_names}")
    else:
        print(f"  {did} ({name}): subdeployments HTTP {r.status_code}")
