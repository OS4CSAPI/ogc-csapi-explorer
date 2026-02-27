#!/usr/bin/env python3
"""
Deployment Hierarchy Migration Script
======================================
Fixes the flat deployment structure by:
1. Deleting the 15 flat subsystem deployments
2. Re-creating them as proper subdeployments via POST /deployments/{parentId}/subdeployments
3. Creating the 3 node deployments as subdeployments of AOI
4. Enriching deployments with system @link associations via PUT

Server: http://45.55.99.236:8080/sensorhub/api
Date: 2026-02-27
"""
import requests, json, time, sys

BASE = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
GEO_CT = {"Content-Type": "application/geo+json", "Accept": "application/json"}
GEO_H = {"Accept": "application/geo+json"}

DRY_RUN = "--dry-run" in sys.argv

# ── Current server IDs (from id_map.json) ──

# Deployment IDs
DEP_AOI = "04cg"      # AZ-DEP-AOI-001
DEP_NET = "04d0"      # AZ-DEP-NET-001
DEP_MA1 = "04dg"      # AZ-DEP-AZ-MA-1
DEP_MA2 = "04e0"      # AZ-DEP-AZ-MA-2
DEP_MA3 = "04eg"      # AZ-DEP-AZ-MA-3

# System IDs
SYS_NET   = "04n0"    # AZ-MA-NET
SYS_MA1   = "04ng"    # AZ-MA-1
SYS_MA2   = "04o0"    # AZ-MA-2
SYS_MA3   = "04og"    # AZ-MA-3

# Subsystem IDs per node (for deployment enrichment)
SUBSYS = {
    "AZ-MA-1": {"MICARRAY": "04pg", "EDGE": "04q0", "COMMS": "04qg", "POWER": "04r0", "ACTUATOR": "04rg"},
    "AZ-MA-2": {"MICARRAY": "0500", "EDGE": "050g", "COMMS": "0510", "POWER": "051g", "ACTUATOR": "0520"},
    "AZ-MA-3": {"MICARRAY": "056g", "EDGE": "0570", "COMMS": "057g", "POWER": "0580", "ACTUATOR": "058g"},
}

# Sub-deployments to migrate: (current_server_id, logical_name, parent_node_dep_id, system_logical_suffix, node_key)
SUB_DEPS = [
    # AZ-MA-1 group
    ("04f0", "Deployment AZ-MA-1-MICARRAY", DEP_MA1, "MICARRAY", "AZ-MA-1"),
    ("04fg", "Deployment AZ-MA-1-EDGE",     DEP_MA1, "EDGE",     "AZ-MA-1"),
    ("04g0", "Deployment AZ-MA-1-COMMS",    DEP_MA1, "COMMS",    "AZ-MA-1"),
    ("04gg", "Deployment AZ-MA-1-POWER",    DEP_MA1, "POWER",    "AZ-MA-1"),
    ("04h0", "Deployment AZ-MA-1-ACTUATOR", DEP_MA1, "ACTUATOR", "AZ-MA-1"),
    # AZ-MA-2 group
    ("04hg", "Deployment AZ-MA-2-MICARRAY", DEP_MA2, "MICARRAY", "AZ-MA-2"),
    ("04i0", "Deployment AZ-MA-2-EDGE",     DEP_MA2, "EDGE",     "AZ-MA-2"),
    ("04ig", "Deployment AZ-MA-2-COMMS",    DEP_MA2, "COMMS",    "AZ-MA-2"),
    ("04j0", "Deployment AZ-MA-2-POWER",    DEP_MA2, "POWER",    "AZ-MA-2"),
    ("04jg", "Deployment AZ-MA-2-ACTUATOR", DEP_MA2, "ACTUATOR", "AZ-MA-2"),
    # AZ-MA-3 group
    ("04k0", "Deployment AZ-MA-3-MICARRAY", DEP_MA3, "MICARRAY", "AZ-MA-3"),
    ("04kg", "Deployment AZ-MA-3-EDGE",     DEP_MA3, "EDGE",     "AZ-MA-3"),
    ("04l0", "Deployment AZ-MA-3-COMMS",    DEP_MA3, "COMMS",    "AZ-MA-3"),
    ("04lg", "Deployment AZ-MA-3-POWER",    DEP_MA3, "POWER",    "AZ-MA-3"),
    ("04m0", "Deployment AZ-MA-3-ACTUATOR", DEP_MA3, "ACTUATOR", "AZ-MA-3"),
]

# Node deployments to re-register as subdeployments of AOI
NODE_DEPS = [
    (DEP_MA1, "Deployment AZ-MA-1", SYS_MA1, "AZ-MA-1"),
    (DEP_MA2, "Deployment AZ-MA-2", SYS_MA2, "AZ-MA-2"),
    (DEP_MA3, "Deployment AZ-MA-3", SYS_MA3, "AZ-MA-3"),
]

# Coordinates per node
COORDS = {
    "AZ-MA-1": [-110.272897, 31.663006],
    "AZ-MA-2": [-110.269314, 31.660119],
    "AZ-MA-3": [-110.275432, 31.658871],
    "NET":     [-110.272547, 31.660665],  # centroid
}

stats = {"deleted": 0, "created": 0, "enriched": 0, "failed": 0, "skipped": 0}
new_id_map = {}  # old_server_id → new_server_id

def log(msg, indent=0):
    prefix = "  " * indent
    flag = "[DRY-RUN] " if DRY_RUN else ""
    print(f"{flag}{prefix}{msg}")


def get_deployment(dep_id):
    """Fetch a deployment's full GeoJSON."""
    r = requests.get(f"{BASE}/deployments/{dep_id}", auth=AUTH, headers=GEO_H)
    if r.status_code == 200:
        return r.json()
    return None


def delete_deployment(dep_id, name):
    """Delete a deployment."""
    if DRY_RUN:
        log(f"Would DELETE /deployments/{dep_id} ({name})", 1)
        stats["deleted"] += 1
        return True
    r = requests.delete(f"{BASE}/deployments/{dep_id}", auth=AUTH)
    if r.status_code in (200, 204):
        log(f"✓ DELETE /deployments/{dep_id} ({name}) → {r.status_code}", 1)
        stats["deleted"] += 1
        return True
    else:
        log(f"✗ DELETE /deployments/{dep_id} ({name}) → {r.status_code}: {r.text[:200]}", 1)
        stats["failed"] += 1
        return False


def create_subdeployment(parent_dep_id, geo_body, name):
    """POST a subdeployment under a parent deployment."""
    if DRY_RUN:
        log(f"Would POST /deployments/{parent_dep_id}/subdeployments ({name})", 1)
        stats["created"] += 1
        return "dry-run-id"
    r = requests.post(
        f"{BASE}/deployments/{parent_dep_id}/subdeployments",
        json=geo_body,
        headers=GEO_CT,
        auth=AUTH,
        allow_redirects=False,
    )
    if r.status_code in (200, 201):
        loc = r.headers.get("Location", "")
        new_id = loc.rstrip("/").split("/")[-1] if "/" in loc else "?"
        log(f"✓ POST subdeployment ({name}) → {r.status_code}, new ID: {new_id}", 1)
        stats["created"] += 1
        return new_id
    else:
        log(f"✗ POST subdeployment ({name}) → {r.status_code}: {r.text[:200]}", 1)
        stats["failed"] += 1
        return None


def enrich_deployment(dep_id, body, name):
    """PUT to update a deployment with @link properties."""
    if DRY_RUN:
        links = [k for k in body.get("properties", {}) if "@link" in k]
        log(f"Would PUT /deployments/{dep_id} ({name}, links: {links})", 1)
        stats["enriched"] += 1
        return True
    r = requests.put(
        f"{BASE}/deployments/{dep_id}",
        json=body,
        headers=GEO_CT,
        auth=AUTH,
    )
    if r.status_code in (200, 204):
        log(f"✓ PUT /deployments/{dep_id} ({name}) enriched → {r.status_code}", 1)
        stats["enriched"] += 1
        return True
    else:
        log(f"✗ PUT /deployments/{dep_id} ({name}) → {r.status_code}: {r.text[:200]}", 1)
        stats["failed"] += 1
        return False


def make_deployment_geojson(name, uid, coords, description=None, valid_time=None):
    """Build a minimal deployment GeoJSON body."""
    body = {
        "type": "Feature",
        "properties": {
            "uid": uid,
            "featureType": "sosa:Deployment",
            "name": name,
            "validTime": valid_time or ["2026-02-26T00:00:00Z", ".."],
        },
        "geometry": {
            "type": "Point",
            "coordinates": coords,
        },
    }
    if description:
        body["properties"]["description"] = description
    return body


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: Snapshot current deployment data (preserve UIDs, descriptions, etc.)
# ═══════════════════════════════════════════════════════════════════════

print("═══ Phase 1: Snapshot current deployments ═══\n")

snapshots = {}
all_dep_ids = [d[0] for d in SUB_DEPS]
for dep_id, name, *_ in SUB_DEPS:
    data = get_deployment(dep_id)
    if data:
        snapshots[dep_id] = data
        props = data.get("properties", {})
        log(f"Snapshotted {dep_id} ({props.get('name', '?')})", 1)
    else:
        log(f"⚠ Could not snapshot {dep_id} ({name})", 1)
        stats["skipped"] += 1

# Also snapshot node deployments
for dep_id, name, _, _ in NODE_DEPS:
    data = get_deployment(dep_id)
    if data:
        snapshots[dep_id] = data
        log(f"Snapshotted {dep_id} ({name})", 1)

print(f"\n  Snapshotted: {len(snapshots)} deployments\n")


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: Delete all 18 flat deployments (15 sub-deps + 3 node deps)
# Order: sub-deployments first, then node deployments
# ═══════════════════════════════════════════════════════════════════════

print("═══ Phase 2: Delete 18 flat deployments ═══\n")

log("Deleting 15 sub-deployments...")
for dep_id, name, _, _, _ in SUB_DEPS:
    delete_deployment(dep_id, name)

log("\nDeleting 3 node deployments...")
for dep_id, name, _, _ in NODE_DEPS:
    delete_deployment(dep_id, name)

if not DRY_RUN:
    time.sleep(2)  # Let the server settle


# ═══════════════════════════════════════════════════════════════════════
# PHASE 3: Re-create node deployments as subdeployments of AOI
# ═══════════════════════════════════════════════════════════════════════

print("\n═══ Phase 3: Re-create node deployments as subdeployments of AOI ═══\n")

for dep_id, name, sys_id, node_key in NODE_DEPS:
    snap = snapshots.get(dep_id)
    if not snap:
        log(f"⚠ No snapshot for {dep_id} ({name}), skipping", 1)
        stats["skipped"] += 1
        continue

    body = dict(snap)
    body.pop("id", None)
    body.pop("links", None)
    new_id = create_subdeployment(DEP_AOI, body, name)
    if new_id:
        new_id_map[dep_id] = new_id
        log(f"Node {name}: {dep_id} → {new_id}", 2)

if not DRY_RUN:
    time.sleep(1)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 4: Re-create 15 sub-deployments under their NEW node dep IDs
# ═══════════════════════════════════════════════════════════════════════

print("\n═══ Phase 4: Re-create 15 sub-deployments as nested resources ═══\n")

for old_id, name, old_parent_dep_id, suffix, node_key in SUB_DEPS:
    # Use the NEW node deployment ID (from Phase 3 remapping)
    actual_parent_id = new_id_map.get(old_parent_dep_id, old_parent_dep_id)

    snap = snapshots.get(old_id)
    if snap:
        body = dict(snap)
        body.pop("id", None)
        body.pop("links", None)
    else:
        uid_suffix = name.lower().replace(" ", "-").replace("deployment-", "dep:")
        uid = f"urn:os4csapi:deployment:{uid_suffix}:ft-huachuca:001"
        coords = COORDS.get(node_key, [-110.272547, 31.660665])
        body = make_deployment_geojson(name, uid, coords)

    new_id = create_subdeployment(actual_parent_id, body, name)
    if new_id:
        new_id_map[old_id] = new_id

if not DRY_RUN:
    time.sleep(2)


# ═══════════════════════════════════════════════════════════════════════
# PHASE 5: Enrich deployments with system @link associations
# ═══════════════════════════════════════════════════════════════════════

print("\n═══ Phase 5: Enrich deployments with system associations ═══\n")

def sys_link(sys_id, name, rel="deployedSystem"):
    return {"href": f"{BASE}/systems/{sys_id}", "rel": rel, "title": name}

# 5a. Enrich AOI deployment
log("Enriching AOI Deployment...")
aoi_data = get_deployment(DEP_AOI)
if aoi_data:
    aoi_data.pop("links", None)
    aoi_data["properties"]["deployedSystems@link"] = [
        sys_link(SYS_MA1, "AZ-MA-1"),
        sys_link(SYS_MA2, "AZ-MA-2"),
        sys_link(SYS_MA3, "AZ-MA-3"),
        sys_link(SYS_NET, "AZ-MA-NET"),
    ]
    aoi_data["properties"]["description"] = "Area of Interest deployment covering Fort Huachuca acoustic sensor range. Encompasses all 3 monitoring arrays and the network coordination system."
    enrich_deployment(DEP_AOI, aoi_data, "AOI Deployment")

# 5b. Enrich Network deployment
log("Enriching Network Deployment...")
net_data = get_deployment(DEP_NET)
if net_data:
    net_data.pop("links", None)
    net_data["properties"]["deployedSystems@link"] = [
        sys_link(SYS_NET, "AZ-MA-NET"),
    ]
    net_data["properties"]["description"] = "Network-level deployment for the AZ-MA-NET coordination system managing triangulation and cross-array communication."
    enrich_deployment(DEP_NET, net_data, "Network Deployment")

# 5c. Enrich node deployments (use new IDs if they were re-registered)
for old_dep_id, name, sys_id, node_key in NODE_DEPS:
    actual_id = new_id_map.get(old_dep_id, old_dep_id)
    log(f"Enriching {name} (ID: {actual_id})...")
    dep_data = get_deployment(actual_id)
    if dep_data:
        dep_data.pop("links", None)
        dep_data["properties"]["deployedSystems@link"] = [sys_link(sys_id, node_key)]
        dep_data["properties"]["platform@link"] = sys_link(sys_id, node_key, rel="platform")
        dep_data["properties"]["description"] = f"Node-level deployment for {node_key} monitoring array at Fort Huachuca."
        enrich_deployment(actual_id, dep_data, name)
    else:
        log(f"⚠ Could not fetch {actual_id} for enrichment", 1)
        stats["failed"] += 1

# 5d. Enrich sub-deployments with their specific subsystem
for old_id, dep_name, _, suffix, node_key in SUB_DEPS:
    actual_id = new_id_map.get(old_id, old_id)
    subsys_id = SUBSYS.get(node_key, {}).get(suffix)
    if not subsys_id:
        log(f"⚠ No subsystem ID for {node_key}/{suffix}, skipping", 1)
        continue

    dep_data = get_deployment(actual_id)
    if dep_data:
        dep_data.pop("links", None)
        subsys_name = f"{node_key}-{suffix}"
        dep_data["properties"]["deployedSystems@link"] = [sys_link(subsys_id, subsys_name)]
        dep_data["properties"]["description"] = f"Subsystem deployment for {subsys_name} component of {node_key} array."
        enrich_deployment(actual_id, dep_data, dep_name)
    else:
        log(f"⚠ Could not fetch {actual_id} for enrichment", 1)
        stats["failed"] += 1


# ═══════════════════════════════════════════════════════════════════════
# PHASE 6: Verification
# ═══════════════════════════════════════════════════════════════════════

print("\n═══ Phase 6: Verification ═══\n")

if DRY_RUN:
    log("Skipping verification in dry-run mode")
else:
    # Check subdeployment hierarchy
    log("Checking AOI subdeployments...")
    r = requests.get(f"{BASE}/deployments/{DEP_AOI}/subdeployments?limit=50", auth=AUTH, headers=GEO_H)
    if r.status_code == 200:
        items = r.json().get("items", r.json().get("features", []))
        log(f"AOI has {len(items)} subdeployments:", 1)
        for it in items:
            log(f"  {it['id']} = {it.get('properties', {}).get('name', '?')}", 2)
    else:
        log(f"AOI subdeployments: HTTP {r.status_code}", 1)

    # Check node deployment subdeployments
    for old_dep_id, name, _, node_key in NODE_DEPS:
        actual_id = new_id_map.get(old_dep_id, old_dep_id)
        r = requests.get(f"{BASE}/deployments/{actual_id}/subdeployments?limit=50", auth=AUTH, headers=GEO_H)
        if r.status_code == 200:
            items = r.json().get("items", r.json().get("features", []))
            log(f"{name} ({actual_id}) has {len(items)} subdeployments", 1)
            for it in items:
                log(f"  {it['id']} = {it.get('properties', {}).get('name', '?')}", 2)
        else:
            log(f"{name} subdeployments: HTTP {r.status_code}", 1)

    # Check @link properties
    log("\nChecking @link properties on enriched deployments...")
    for dep_id in [DEP_AOI, DEP_NET] + [new_id_map.get(d[0], d[0]) for d in NODE_DEPS]:
        r = requests.get(f"{BASE}/deployments/{dep_id}", auth=AUTH, headers=GEO_H)
        if r.status_code == 200:
            d = r.json()
            props = d.get("properties", {})
            link_keys = [k for k in props if "@link" in k]
            name = props.get("name", "?")
            log(f"  {dep_id} ({name}): @link keys = {link_keys}", 1)

    # Total deployment count
    r = requests.get(f"{BASE}/deployments?limit=100", auth=AUTH, headers=GEO_H)
    items = r.json().get("items", r.json().get("features", []))
    log(f"\nTotal deployments in listing: {len(items)}")


# ═══════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════

print("\n═══ Summary ═══\n")
print(f"  Deleted:  {stats['deleted']}")
print(f"  Created:  {stats['created']}")
print(f"  Enriched: {stats['enriched']}")
print(f"  Failed:   {stats['failed']}")
print(f"  Skipped:  {stats['skipped']}")

if new_id_map:
    print(f"\n  ID remapping ({len(new_id_map)} entries):")
    for old_id, new_id in new_id_map.items():
        print(f"    {old_id} → {new_id}")

if DRY_RUN:
    print("\n  ⚠ This was a DRY RUN — no changes were made to the server.")
    print("  Re-run without --dry-run to apply changes.")
