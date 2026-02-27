#!/usr/bin/env python3
"""Check what endpoints/rels the server actually advertises."""
import requests, json

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")

# 1. API Root links
r = requests.get(BASE, auth=AUTH, headers={"Accept": "application/json"})
print("=== API Root Links ===")
for link in r.json().get("links", []):
    rel = link.get("rel", "?")
    href = link.get("href", "")
    print(f"  {rel:30s} → {href}")

# 2. Single deployment links
print("\n=== Single Deployment (04dg) Links ===")
r2 = requests.get(f"{BASE}/deployments/04dg", auth=AUTH, headers={"Accept": "application/json"})
for link in r2.json().get("links", []):
    rel = link.get("rel", "?")
    href = link.get("href", "")
    print(f"  {rel:30s} → {href}")

# 3. Single system links
print("\n=== Single System (04ng) Links ===")
r3 = requests.get(f"{BASE}/systems/04ng", auth=AUTH, headers={"Accept": "application/json"})
for link in r3.json().get("links", []):
    rel = link.get("rel", "?")
    href = link.get("href", "")
    print(f"  {rel:30s} → {href}")

# 4. Check the Phase1 bootstrap results report for deployed system link info
print("\n=== Phase1 bootstrap deployed system links check ===")
# What did the bootstrap actually do? Check if the links are in deployment SML body
r4 = requests.get(f"{BASE}/deployments/04dg", auth=AUTH, headers={"Accept": "application/geo+json"})
d = r4.json()
props = d.get("properties", {})
print("Deployment AZ-MA-1 properties keys:")
for k, v in props.items():
    print(f"  {k} = {json.dumps(v) if isinstance(v, (list, dict)) else v}")
