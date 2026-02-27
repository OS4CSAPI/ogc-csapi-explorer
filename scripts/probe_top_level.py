"""Investigate why subsystems don't appear in top-level /systems?q= searches."""
import requests
import json

BASE = 'http://45.55.99.236:8080/sensorhub/api'
AUTH = ('ogc', 'ogc')
H = {'Accept': 'application/geo+json'}

# 1) Is AZ-MA-1 (04ng) directly accessible?
r = requests.get(f'{BASE}/systems/04ng', auth=AUTH, headers=H)
print(f'GET /systems/04ng: HTTP {r.status_code}')
if r.ok:
    d = r.json()
    name = d.get('properties', {}).get('name', '?')
    links = d.get('links', [])
    parent = [l for l in links if l.get('rel') == 'parent']
    print(f'  name: {name}')
    print(f'  parent links: {parent}')

# 2) Total systems count (no filter)
print('\n=== Total systems (no filter) ===')
r2 = requests.get(f'{BASE}/systems?limit=1', auth=AUTH, headers=H)
d2 = r2.json()
nm = d2.get('numberMatched', 'N/A')
nr = d2.get('numberReturned', 'N/A')
print(f'  numberMatched={nm}, numberReturned={nr}')

# Walk pages to count all
all_ids = []
offset = 0
while True:
    r3 = requests.get(f'{BASE}/systems?limit=100&offset={offset}', auth=AUTH, headers=H)
    items = r3.json().get('items', r3.json().get('features', []))
    if not items:
        break
    for it in items:
        all_ids.append((it.get('id', '?'), it.get('properties', {}).get('name', '?')))
    offset += len(items)
    if len(items) < 100:
        break

print(f'  Total systems via pagination: {len(all_ids)}')

# 3) Check which ones have parent links (subsystems visible at top-level)
print(f'\n=== Checking all {len(all_ids)} systems for rel=parent ===')
root_systems = []
subsystems_visible_at_top = []
for sid, sname in all_ids:
    r4 = requests.get(f'{BASE}/systems/{sid}', auth=AUTH, headers=H)
    if r4.ok:
        links = r4.json().get('links', [])
        parent = [l for l in links if l.get('rel') == 'parent']
        if parent:
            subsystems_visible_at_top.append((sid, sname, parent[0].get('href', '')))
        else:
            root_systems.append((sid, sname))

print(f'  Root systems (no parent): {len(root_systems)}')
for sid, sname in root_systems:
    print(f'    {sid} = {sname}')

print(f'\n  Subsystems visible at top-level (have parent): {len(subsystems_visible_at_top)}')
for sid, sname, phref in subsystems_visible_at_top:
    print(f'    {sid} = {sname}  →  parent: {phref}')

# 4) Now count total subsystems that are NOT in the top-level list
print(f'\n=== Subsystems NOT in top-level list ===')
top_level_ids = set(sid for sid, _ in all_ids)
hidden_subsystems = []
# Check each root system's subsystems
for sid, sname in root_systems:
    r5 = requests.get(f'{BASE}/systems/{sid}/subsystems?limit=100', auth=AUTH, headers=H)
    if r5.ok:
        subs = r5.json().get('items', r5.json().get('features', []))
        for sub in subs:
            sub_id = sub.get('id', '?')
            sub_name = sub.get('properties', {}).get('name', '?')
            if sub_id not in top_level_ids:
                hidden_subsystems.append((sub_id, sub_name, sid, sname))

# Also check subsystems that ARE visible at top level
for sid, sname, _ in subsystems_visible_at_top:
    r5 = requests.get(f'{BASE}/systems/{sid}/subsystems?limit=100', auth=AUTH, headers=H)
    if r5.ok:
        subs = r5.json().get('items', r5.json().get('features', []))
        for sub in subs:
            sub_id = sub.get('id', '?')
            sub_name = sub.get('properties', {}).get('name', '?')
            if sub_id not in top_level_ids:
                hidden_subsystems.append((sub_id, sub_name, sid, sname))

print(f'  Subsystems NOT in top-level /systems: {len(hidden_subsystems)}')
for sub_id, sub_name, par_id, par_name in hidden_subsystems[:30]:
    print(f'    {sub_id} = {sub_name}  (child of {par_name})')
if len(hidden_subsystems) > 30:
    print(f'    ... and {len(hidden_subsystems) - 30} more')
