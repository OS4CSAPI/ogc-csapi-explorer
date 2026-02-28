"""Count all subsystems recursively to see what's hidden from /systems."""
import requests
BASE = 'http://45.55.99.236:8080/sensorhub/api'
AUTH = ('ogc', 'ogc')
H = {'Accept': 'application/geo+json'}

def get_subs(parent_id):
    r = requests.get(f'{BASE}/systems/{parent_id}/subsystems?limit=100', auth=AUTH, headers=H)
    if not r.ok:
        return []
    return r.json().get('items', r.json().get('features', []))

# AZ-MA-NET subtree
print('=== AZ-MA-NET (04n0) subsystems ===')
net_subs = get_subs('04n0')
print(f'Direct children: {len(net_subs)}')
for s in net_subs:
    sid = s['id']
    name = s.get('properties', {}).get('name', '?')
    print(f'  {sid} = {name}')
    # Check grandchildren
    gc = get_subs(sid)
    if gc:
        print(f'    └─ {len(gc)} subsystems:')
        for g in gc:
            gid = g['id']
            gname = g.get('properties', {}).get('name', '?')
            print(f'       {gid} = {gname}')

# Total subsystem count
top_ids = set()
r = requests.get(f'{BASE}/systems?limit=100', auth=AUTH, headers=H)
for it in r.json().get('items', r.json().get('features', [])):
    top_ids.add(it['id'])

print(f'\nTop-level /systems count: {len(top_ids)}')

# Recursively count all
visited = set()
def count_tree(pid, depth=0):
    subs = get_subs(pid)
    for s in subs:
        sid = s['id']
        if sid in visited:
            continue
        visited.add(sid)
        in_top = sid in top_ids
        name = s.get('properties', {}).get('name', '?')
        marker = ' ← IN TOP-LEVEL' if in_top else ' ✗ NOT in top-level'
        print(f'{"  " * (depth+1)}{sid} = {name}{marker}')
        count_tree(sid, depth + 1)

print('\n=== Full tree walk from AZ-MA-NET ===')
count_tree('04n0')
print(f'\nTotal unique subsystems found: {len(visited)}')
print(f'Of those, in top-level list: {len(visited & top_ids)}')
print(f'Hidden from top-level: {len(visited - top_ids)}')
