#!/usr/bin/env python3
"""Test CSAPI server endpoints to discover actual data model relationships."""

import json
import urllib.request
import urllib.error
import ssl

BASE = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH = "Basic b3M0Y3NhcGk6b2djMTM0bW0="

ctx = ssl.create_default_context()

def fetch(path):
    """Fetch a URL and return (status, json_body_or_None)."""
    url = BASE + path
    req = urllib.request.Request(url, headers={
        "Authorization": AUTH,
        "Accept": "application/json"
    })
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        body = resp.read().decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = body
        return resp.status, data
    except urllib.error.HTTPError as e:
        body = None
        try:
            body = e.read().decode("utf-8")
            body = json.loads(body)
        except:
            pass
        return e.code, body
    except Exception as e:
        return f"ERR:{e}", None

results = []

def test(label, path, detail=False):
    status, data = fetch(path)
    count = "N/A"
    notable = []
    if isinstance(data, dict):
        if "items" in data:
            items = data["items"]
            count = len(items)
            if count > 0:
                # Check first item for notable fields
                first = items[0]
                for key in sorted(first.keys()):
                    if "@" in key or key == "links":
                        notable.append(key)
        elif detail:
            for key in sorted(data.keys()):
                if "@" in key or key == "links":
                    notable.append(key)
            # Check links array
            if "links" in data and isinstance(data["links"], list):
                link_rels = [l.get("rel", "?") for l in data["links"]]
                notable.append(f"link_rels={link_rels}")
            # Check specific fields
            for field in ["systemKind@link", "system@id", "platform@link",
                          "deployedSystems@link", "foi@id", "datastream@id",
                          "procedure@link", "deployment@link"]:
                if field in data:
                    notable.append(f"{field}={data[field]}")
    
    notable_str = ", ".join(notable) if notable else ""
    results.append((label, path, status, count, notable_str))
    print(f"  {status:>5}  count={str(count):>5}  {path}")
    if notable_str:
        print(f"         notable: {notable_str}")
    return status, data

# ── 1. Systems navigation (NWS KTUS 0520) ──
print("\n=== 1. Systems navigation (NWS KTUS 0520) ===")
test("sys subsystems", "/systems/0520/subsystems?limit=5")
test("sys datastreams", "/systems/0520/datastreams?limit=5")
test("sys controlstreams", "/systems/0520/controlstreams?limit=5")
test("sys samplingFeatures", "/systems/0520/samplingFeatures?limit=5")
test("sys deployments", "/systems/0520/deployments?limit=5")
test("sys procedures", "/systems/0520/procedures?limit=5")

# ── 2. Deployment navigation ──
print("\n=== 2. Deployment navigation ===")
test("deploy root subdeployments", "/deployments/04mg/subdeployments?limit=5")
test("deploy leaf subdeployments", "/deployments/04ng/subdeployments?limit=5")
test("deploy root systems", "/deployments/04mg/systems?limit=5")
_, dep_detail = test("deploy leaf detail", "/deployments/04ng", detail=True)
if isinstance(dep_detail, dict):
    print(f"    FULL KEYS: {sorted(dep_detail.keys())}")

# ── 3. Procedure navigation ──
print("\n=== 3. Procedure navigation ===")
test("procedure 049g detail", "/procedures/049g", detail=True)

# List procedures to find NWS procedure
print("\n  -- Listing procedures --")
_, procs = test("procedures list", "/procedures?limit=50")
nws_proc_id = None
if isinstance(procs, dict) and "items" in procs:
    for p in procs["items"]:
        name = p.get("name", "") or p.get("label", "") or ""
        uid = p.get("uniqueId", "") or p.get("definition", "") or ""
        pid = p.get("id", "")
        print(f"    proc id={pid}  name={name}  uid={uid}")
        if "NWS" in name.upper() or "ASOS" in name.upper() or "NWS" in uid.upper():
            nws_proc_id = pid
    if nws_proc_id:
        print(f"\n  Found NWS procedure: {nws_proc_id}")
        test("nws proc systems", f"/procedures/{nws_proc_id}/systems?limit=5")
        test("nws proc datastreams", f"/procedures/{nws_proc_id}/datastreams?limit=5")
    else:
        print("  No NWS procedure found; testing 049g sub-endpoints anyway")
        test("proc 049g systems", "/procedures/049g/systems?limit=5")
        test("proc 049g datastreams", "/procedures/049g/datastreams?limit=5")

# ── 4. Datastream navigation ──
print("\n=== 4. Datastream navigation ===")
_, ds_detail = test("ds 04qg detail", "/datastreams/04qg", detail=True)
if isinstance(ds_detail, dict):
    print(f"    FULL KEYS: {sorted(ds_detail.keys())}")
test("ds observations", "/datastreams/04qg/observations?limit=2")
test("ds systems", "/datastreams/04qg/systems?limit=5")

# ── 5. Observation navigation ──
print("\n=== 5. Observation navigation ===")
_, obs_resp = test("obs from ds", "/datastreams/04qg/observations?limit=1")
if isinstance(obs_resp, dict) and "items" in obs_resp and len(obs_resp["items"]) > 0:
    obs = obs_resp["items"][0]
    print(f"    OBS KEYS: {sorted(obs.keys())}")
    for k in ["datastream@id", "system@id", "foi@id", "phenomenonTime", "resultTime", "result"]:
        if k in obs:
            val = obs[k]
            if isinstance(val, dict) and len(str(val)) > 200:
                val = "{...}"
            print(f"    {k} = {val}")

# ── 6. Property navigation ──
print("\n=== 6. Property navigation ===")
_, props = test("properties list", "/properties?limit=5")
if isinstance(props, dict) and "items" in props:
    items = props["items"]
    if len(items) > 0:
        prop_id = items[0].get("id", "")
        prop_name = items[0].get("label", "") or items[0].get("name", "")
        print(f"    First property: id={prop_id} name={prop_name}")
        if prop_id:
            test("prop systems", f"/properties/{prop_id}/systems?limit=5")
            test("prop datastreams", f"/properties/{prop_id}/datastreams?limit=5")

# ── 7. Simulator system (SET Ft Huachuca 040g) ──
print("\n=== 7. Simulator system (SET Ft Huachuca 040g) ===")
test("sim subsystems", "/systems/040g/subsystems?limit=5")
test("sim datastreams", "/systems/040g/datastreams?limit=5")
test("sim deployments", "/systems/040g/deployments?limit=5")
test("sim procedures", "/systems/040g/procedures?limit=5")

# ── 8. System 0520 detail ──
print("\n=== 8. System 0520 detail ===")
_, sys_detail = test("sys 0520 detail", "/systems/0520", detail=True)
if isinstance(sys_detail, dict):
    print(f"    FULL KEYS: {sorted(sys_detail.keys())}")
    if "links" in sys_detail:
        print("    LINKS:")
        for link in sys_detail["links"]:
            print(f"      rel={link.get('rel','?')}  href={link.get('href','?')}  title={link.get('title','')}")

# ── Also fetch deployment root detail ──
print("\n=== BONUS: Deployment root 04mg detail ===")
_, dep_root = test("deploy root detail", "/deployments/04mg", detail=True)
if isinstance(dep_root, dict):
    print(f"    FULL KEYS: {sorted(dep_root.keys())}")
    if "links" in dep_root:
        print("    LINKS:")
        for link in dep_root["links"]:
            print(f"      rel={link.get('rel','?')}  href={link.get('href','?')}  title={link.get('title','')}")

# ── Summary table ──
print("\n\n" + "="*120)
print(f"{'Label':<30} {'Path':<55} {'Status':>6} {'Count':>6}  Notable")
print("-"*120)
for label, path, status, count, notable in results:
    print(f"{label:<30} {path:<55} {str(status):>6} {str(count):>6}  {notable}")
print("="*120)
