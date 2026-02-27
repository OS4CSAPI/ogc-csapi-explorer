"""Test whether DELETE on a parent system cascades to its children on OSH SensorHub.
Uses explicit headers and ensures 'type' is the first JSON property (OSH requirement).
"""
import requests
import json

BASE = 'http://45.55.99.236:8080/sensorhub/api'
AUTH = ('ogc', 'ogc')
SML_CT = {'Content-Type': 'application/sml+json', 'Accept': 'application/json'}

def ordered_json(d):
    """Ensure 'type' is first key in JSON output (OSH SensorHub requirement)."""
    ordered = {}
    if 'type' in d:
        ordered['type'] = d['type']
    for k, v in d.items():
        if k != 'type':
            ordered[k] = v
    return json.dumps(ordered)

# 1) Create a test parent system
parent_sml = {
    'type': 'PhysicalSystem',
    'uniqueId': 'urn:test:cascade:parent',
    'label': 'TEST-CASCADE-PARENT',
    'definition': 'http://www.w3.org/ns/ssn/System',
}
r = requests.post(f'{BASE}/systems', data=ordered_json(parent_sml), headers=SML_CT, auth=AUTH, allow_redirects=False)
print(f'Create parent: {r.status_code}')
parent_loc = r.headers.get('Location', '')
print(f'Location: {parent_loc}')
parent_id = parent_loc.rstrip('/').split('/')[-1] if '/systems/' in parent_loc else ''
print(f'Parent ID: {parent_id}')

if not parent_id:
    print('ABORT: Could not create parent')
    print(f'Response body: {r.text[:200]}')
    exit(1)

# 2) Create a test child subsystem
child_sml = {
    'type': 'PhysicalSystem',
    'uniqueId': 'urn:test:cascade:child',
    'label': 'TEST-CASCADE-CHILD',
    'definition': 'http://www.w3.org/ns/ssn/System',
}
r2 = requests.post(f'{BASE}/systems/{parent_id}/subsystems', data=ordered_json(child_sml), headers=SML_CT, auth=AUTH, allow_redirects=False)
print(f'Create child: {r2.status_code}')
child_loc = r2.headers.get('Location', '')
child_id = child_loc.rstrip('/').split('/')[-1] if '/systems/' in child_loc else ''
print(f'Child ID: {child_id}')

if not child_id:
    print('ABORT: Could not create child')
    print(f'Response body: {r2.text[:200]}')
    exit(1)

# 3) Verify child exists under parent
r3 = requests.get(f'{BASE}/systems/{parent_id}/subsystems', auth=AUTH, headers={'Accept': 'application/geo+json'})
items = r3.json().get('items', r3.json().get('features', []))
print(f'Subsystems of parent: {len(items)}')

# 4) DELETE the parent only (not recursive)
r4 = requests.delete(f'{BASE}/systems/{parent_id}', auth=AUTH)
print(f'Delete parent: {r4.status_code}')

# 5) Check if child still exists
r5 = requests.get(f'{BASE}/systems/{child_id}', auth=AUTH, headers={'Accept': 'application/geo+json'})
print(f'Child after parent delete: HTTP {r5.status_code}')
if r5.status_code == 200:
    print('>>> CHILD SURVIVED - no cascade delete!')
    # Cleanup child
    r6 = requests.delete(f'{BASE}/systems/{child_id}', auth=AUTH)
    print(f'Cleanup child: {r6.status_code}')
elif r5.status_code == 404:
    print('>>> CHILD GONE - cascade delete confirmed!')
else:
    print(f'>>> Unexpected: {r5.status_code}')
    print(f'Body: {r5.text[:200]}')

# Cleanup parent just in case
requests.delete(f'{BASE}/systems/{parent_id}', auth=AUTH)
