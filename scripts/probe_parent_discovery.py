"""Probe OSH server to understand parent/child system relationships and discover
what fields are available for parent discovery."""
import requests
import json

BASE = 'http://45.55.99.236:8080/sensorhub/api'
AUTH = ('ogc', 'ogc')
H = {'Accept': 'application/geo+json'}
SML_H = {'Accept': 'application/sml+json'}

# 1) Fetch the tripod system detail
print('=== AZ-MA-1 TRIPOD (04p0) GeoJSON detail ===')
r = requests.get(f'{BASE}/systems/04p0', auth=AUTH, headers=H)
data = r.json()
print(json.dumps(data, indent=2)[:2000])

# Check for any link/parent fields
print('\n=== Checking all top-level keys ===')
for k in sorted(data.keys()):
    if 'link' in k.lower() or 'parent' in k.lower() or 'attach' in k.lower():
        print(f'  KEY: {k} = {data[k]}')
props = data.get('properties', {})
for k in sorted(props.keys()):
    if 'link' in k.lower() or 'parent' in k.lower() or 'attach' in k.lower():
        print(f'  PROP: {k} = {props[k]}')
if 'links' in data:
    print(f'  links array: {json.dumps(data["links"], indent=2)}')

# 2) Fetch SensorML for the tripod
print('\n=== AZ-MA-1 TRIPOD (04p0) SensorML ===')
r2 = requests.get(f'{BASE}/systems/04p0?f=sml3', auth=AUTH, headers=SML_H)
if r2.ok:
    sml = r2.json()
    # Check for attachedTo, parent, components, etc.
    for key in sorted(sml.keys()):
        if key in ('attachedTo', 'parent', 'parentSystem', 'links',
                    'attachedTo@link', 'parent@link', 'parent@id',
                    'components', 'connections'):
            print(f'  SML KEY: {key} = {json.dumps(sml[key])[:300]}')
    print(f'  All top-level SML keys: {sorted(sml.keys())}')
else:
    print(f'  SML fetch failed: {r2.status_code}')

# 3) Check AZ-MA-1 subsystems
print('\n=== AZ-MA-1 (04ng) subsystems ===')
r3 = requests.get(f'{BASE}/systems/04ng/subsystems?limit=20', auth=AUTH, headers=H)
items = r3.json().get('items', r3.json().get('features', []))
for it in items:
    sid = it.get('id', '?')
    name = it.get('properties', {}).get('name', '?')
    print(f'  {sid} = {name}')

# 4) Top-level systems
print('\n=== Top-level /systems?q=az ===')
r4 = requests.get(f'{BASE}/systems?limit=20&q=az', auth=AUTH, headers=H)
data4 = r4.json()
items = data4.get('items', data4.get('features', []))
for it in items:
    sid = it.get('id', '?')
    name = it.get('properties', {}).get('name', '?')
    print(f'  {sid} = {name}')
# Check numberMatched
print(f'  numberMatched: {data4.get("numberMatched", "N/A")}')

# 5) Check if server supports parent= filter
print('\n=== parent= filter test ===')
for param in ['parent=04ng', 'parent=none', 'parent=04n0']:
    r5 = requests.get(f'{BASE}/systems?{param}&limit=5', auth=AUTH, headers=H)
    items5 = r5.json().get('items', r5.json().get('features', []))
    names = [it.get('properties', {}).get('name', '?') for it in items5]
    print(f'  ?{param}: HTTP {r5.status_code}, {len(items5)} results: {names}')

# 6) Check if server supports GET /systems/{childId} with parent info in links
print('\n=== Check links array in feature response ===')
r6 = requests.get(f'{BASE}/systems/04p0', auth=AUTH, headers={'Accept': 'application/json'})
if r6.ok:
    d6 = r6.json()
    if 'links' in d6:
        print(f'  JSON links: {json.dumps(d6["links"], indent=2)[:500]}')
    else:
        print(f'  No links array in application/json response')
    print(f'  Top keys: {sorted(d6.keys())}')
