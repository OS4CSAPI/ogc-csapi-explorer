#!/usr/bin/env python3
"""
ODAS — Fix Resource Associations
Adds @link fields to connect Systems↔Procedures and Deployments↔Systems.

These associations were missing from the original ingestion, causing the
CSAPI Explorer Detail view to show 0 Deployments and 0 Procedures.

Approach: GET each resource, add @link fields, PUT back.
"""

import requests
import json
import sys

BASE_URL = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
HEADERS_GEOJSON = {"Content-Type": "application/geo+json"}
HEADERS_JSON = {"Content-Type": "application/json"}

# ─── ID Maps ─────────────────────────────────────────────────────────────────

# Systems (from Part 1 ingestion)
SYSTEMS = {
    "platform":         "04fg",
    "mic_array":        "04g0",
    "mic_1":            "04gg",
    "mic_2":            "04h0",
    "mic_3":            "04hg",
    "mic_4":            "04i0",
    "mic_5":            "04ig",
    "mic_6":            "04j0",
    "mic_7":            "04jg",
    "dsp_pipeline":     "04k0",
    "ssl_module":       "04kg",
    "sst_module":       "04l0",
    "config_actuator":  "04lg",
    "tri_engine":       "04m0",
}

# Procedures (from Part 1 ingestion)
PROCEDURES = {
    "proc_audio":   "0480",  # PDM MEMS Microphone Audio Capture
    "proc_ssl":     "048g",  # SRP-PHAT Steered Response Power Beamforming
    "proc_sst":     "0490",  # Particle Filter Sound Source Tracking
    "proc_tri":     "049g",  # Multi-Array Ray-to-Ray 3D Triangulation (procedure)
    "proc_config":  "04a0",  # ODAS Runtime Configuration Actuation (procedure)
}

# Deployments (from Part 1 ingestion)
DEPLOYMENTS = {
    "single_array":     "049g",  # Conference Room (deployment, same ID series as proc_tri)
    "multi_array":      "04a0",  # Campus Perimeter (deployment, same ID series as proc_config)
    "sub_north":        "04ag",
    "sub_southeast":    "04b0",
    "sub_southwest":    "04bg",
}

# Sampling Features (from Part 1 ingestion)
SAMPLING_FEATURES = {
    "conference_room":  "050g",
    "monitoring_zone":  "0510",
    "campus_perimeter": "051g",
}

# ─── System → Procedure mapping ─────────────────────────────────────────────
# Maps system ID → procedure ID (which procedure does this system implement?)
SYSTEM_PROCEDURE_MAP = {
    # Mic array + individual mics all implement the audio capture procedure
    "04g0": "0480",   # Mic Array → PDM Audio
    "04gg": "0480",   # Mic #1 → PDM Audio
    "04h0": "0480",   # Mic #2 → PDM Audio
    "04hg": "0480",   # Mic #3 → PDM Audio
    "04i0": "0480",   # Mic #4 → PDM Audio
    "04ig": "0480",   # Mic #5 → PDM Audio
    "04j0": "0480",   # Mic #6 → PDM Audio
    "04jg": "0480",   # Mic #7 → PDM Audio
    # DSP modules implement their specific algorithm procedures
    "04kg": "048g",   # SSL Module → SRP-PHAT
    "04l0": "0490",   # SST Module → Particle Filter
    # Actuator implements config procedure
    "04lg": "04a0",   # Config Actuator → Config Actuation (procedure ID 04a0)
    # Triangulation engine implements triangulation procedure
    "04m0": "049g",   # Tri Engine → Ray-to-Ray Triangulation (procedure ID 049g)
}

# Procedure names for link titles
PROCEDURE_NAMES = {
    "0480": "PDM MEMS Microphone Audio Capture",
    "048g": "SRP-PHAT Steered Response Power Beamforming",
    "0490": "Particle Filter Sound Source Tracking",
    "049g": "Multi-Array Ray-to-Ray 3D Triangulation",
    "04a0": "ODAS Runtime Configuration Actuation",
}

# System names for link titles
SYSTEM_NAMES = {
    "04fg": "ODAS — XMOS xCORE-200 Microphone Array Board #001",
    "04g0": "7-Microphone Circular PDM Array",
    "04k0": "ODAS DSP Processing Pipeline",
    "04kg": "ODAS SSL Module",
    "04l0": "ODAS SST Module",
    "04lg": "ODAS Runtime Configuration Controller",
    "04m0": "Multi-Array 3D Triangulation Engine",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_resource(endpoint, rid):
    """GET a resource by ID."""
    url = f"{BASE_URL}/{endpoint}/{rid}"
    r = requests.get(url, auth=AUTH, timeout=10)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"  ! GET {endpoint}/{rid} failed: {r.status_code}")
        return None


def put_resource(endpoint, rid, payload, label="resource"):
    """PUT (update) a resource."""
    url = f"{BASE_URL}/{endpoint}/{rid}"
    # Systems and deployments use geo+json
    ct = HEADERS_GEOJSON
    r = requests.put(url, json=payload, headers=ct, auth=AUTH,
                     allow_redirects=False, timeout=15)
    if r.status_code in (200, 204):
        print(f"  OK Updated {label}")
        return True
    elif r.status_code == 302:
        print(f"  ! REDIRECT for {label}: 302 (server rejected)")
        return False
    else:
        body = r.text[:500] if r.text else "(empty)"
        print(f"  ! FAILED {label}: {r.status_code} — {body}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE A: Link Systems → Procedures (systemKind@link)
# ═══════════════════════════════════════════════════════════════════════════════

def link_systems_to_procedures():
    print("\n====== PHASE A: Link Systems -> Procedures (systemKind@link) ======")

    for sys_id, proc_id in SYSTEM_PROCEDURE_MAP.items():
        proc_name = PROCEDURE_NAMES.get(proc_id, "Unknown")
        label = f"System {sys_id} -> Procedure {proc_id}"

        # GET current system
        data = get_resource("systems", sys_id)
        if not data:
            continue

        # Add systemKind@link to properties
        data["properties"]["systemKind@link"] = {
            "href": f"{BASE_URL}/procedures/{proc_id}",
            "rel": "systemKind",
            "title": proc_name
        }

        # Remove server-added fields that shouldn't be in PUT
        data.pop("id", None)
        data.pop("links", None)

        # PUT back
        put_resource("systems", sys_id, data, label=label)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE B: Link Deployments → Systems (deployedSystems@link, platform@link)
# ═══════════════════════════════════════════════════════════════════════════════

def link_deployments_to_systems():
    print("\n====== PHASE B: Link Deployments -> Systems ======")

    # --- Single Array Deployment (Conference Room) ---
    dep_id = DEPLOYMENTS["single_array"]
    data = get_resource("deployments", dep_id)
    if data:
        data["properties"]["platform@link"] = {
            "href": f"{BASE_URL}/systems/{SYSTEMS['platform']}",
            "rel": "platform",
            "title": SYSTEM_NAMES["04fg"]
        }
        data["properties"]["deployedSystems@link"] = [
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['platform']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04fg"]
            },
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['mic_array']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04g0"]
            },
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['dsp_pipeline']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04k0"]
            },
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['ssl_module']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04kg"]
            },
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['sst_module']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04l0"]
            },
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['config_actuator']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04lg"]
            },
        ]
        # Also link sampling features
        data["properties"]["featuresOfInterest@link"] = [
            {
                "href": f"{BASE_URL}/samplingFeatures/{SAMPLING_FEATURES['conference_room']}",
                "rel": "featureOfInterest",
                "title": "Conference Room 3A — Acoustic Environment"
            }
        ]
        data["properties"]["samplingFeatures@link"] = [
            {
                "href": f"{BASE_URL}/samplingFeatures/{SAMPLING_FEATURES['monitoring_zone']}",
                "rel": "samplingFeature",
                "title": "Array #001 Acoustic Monitoring Zone"
            }
        ]
        data.pop("id", None)
        data.pop("links", None)
        put_resource("deployments", dep_id, data,
                     label=f"Deployment {dep_id} (Single Array)")

    # --- Multi-Array Triangulation Deployment (Campus Perimeter) ---
    dep_id = DEPLOYMENTS["multi_array"]
    data = get_resource("deployments", dep_id)
    if data:
        data["properties"]["platform@link"] = {
            "href": f"{BASE_URL}/systems/{SYSTEMS['platform']}",
            "rel": "platform",
            "title": SYSTEM_NAMES["04fg"]
        }
        data["properties"]["deployedSystems@link"] = [
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['platform']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04fg"]
            },
            {
                "href": f"{BASE_URL}/systems/{SYSTEMS['tri_engine']}",
                "rel": "deployedSystem",
                "title": SYSTEM_NAMES["04m0"]
            },
        ]
        data["properties"]["featuresOfInterest@link"] = [
            {
                "href": f"{BASE_URL}/samplingFeatures/{SAMPLING_FEATURES['campus_perimeter']}",
                "rel": "featureOfInterest",
                "title": "Campus Perimeter — Outdoor Acoustic Environment"
            }
        ]
        data.pop("id", None)
        data.pop("links", None)
        put_resource("deployments", dep_id, data,
                     label=f"Deployment {dep_id} (Multi-Array)")

    # --- Sub-deployments (each deploys one array at its position) ---
    for sub_key, sub_id in [("sub_north", "04ag"), ("sub_southeast", "04b0"), ("sub_southwest", "04bg")]:
        data = get_resource("deployments", sub_id)
        if data:
            data["properties"]["platform@link"] = {
                "href": f"{BASE_URL}/systems/{SYSTEMS['platform']}",
                "rel": "platform",
                "title": SYSTEM_NAMES["04fg"]
            }
            data["properties"]["deployedSystems@link"] = [
                {
                    "href": f"{BASE_URL}/systems/{SYSTEMS['platform']}",
                    "rel": "deployedSystem",
                    "title": SYSTEM_NAMES["04fg"]
                },
            ]
            data.pop("id", None)
            data.pop("links", None)
            put_resource("deployments", sub_id, data,
                         label=f"Sub-deployment {sub_id} ({sub_key})")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE C: Verify associations via navigation endpoints
# ═══════════════════════════════════════════════════════════════════════════════

def verify_associations():
    print("\n====== PHASE C: Verify Associations ======")

    # Check system 04fg deployments
    r = requests.get(f"{BASE_URL}/systems/{SYSTEMS['platform']}/deployments",
                     auth=AUTH, timeout=10)
    items = r.json().get("items", [])
    print(f"  Platform deployments: {len(items)}")
    for i in items:
        print(f"    {i['id']}  {i['properties']['name']}")

    # Check system 04kg procedures
    r = requests.get(f"{BASE_URL}/systems/{SYSTEMS['ssl_module']}/procedures",
                     auth=AUTH, timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data.get("items", [])
        print(f"  SSL module procedures: {len(items)}")
        for i in items:
            print(f"    {i['id']}  {i['properties']['name']}")
    else:
        print(f"  SSL module procedures: endpoint returned {r.status_code}")
        # Maybe the endpoint is just the procedure itself
        # Try a different approach — check the system JSON for the link
        r2 = requests.get(f"{BASE_URL}/systems/{SYSTEMS['ssl_module']}", auth=AUTH)
        sk = r2.json().get("properties", {}).get("systemKind@link", "NONE")
        print(f"  SSL module systemKind@link = {sk}")

    # Check deployment 049g systems
    r = requests.get(f"{BASE_URL}/deployments/{DEPLOYMENTS['single_array']}/systems",
                     auth=AUTH, timeout=10)
    if r.status_code == 200:
        items = r.json().get("items", [])
        print(f"  Single array deployment systems: {len(items)}")
        for i in items:
            print(f"    {i['id']}  {i['properties']['name']}")
    else:
        print(f"  Single array deployment systems: endpoint returned {r.status_code}")

    # Check procedure 048g implementing systems
    r = requests.get(f"{BASE_URL}/procedures/{PROCEDURES['proc_ssl']}/systems",
                     auth=AUTH, timeout=10)
    if r.status_code == 200:
        items = r.json().get("items", [])
        print(f"  SRP-PHAT procedure implementing systems: {len(items)}")
        for i in items:
            print(f"    {i['id']}  {i['properties']['name']}")
    else:
        print(f"  SRP-PHAT procedure systems: endpoint returned {r.status_code}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("ODAS — Fix Resource Associations")
    print(f"Target: {BASE_URL}")
    print("=" * 70)

    # Test connection
    try:
        r = requests.get(BASE_URL, auth=AUTH, timeout=10)
        r.raise_for_status()
        print(f"Server reachable: {r.json().get('title', 'unknown')}")
    except Exception as e:
        print(f"Cannot reach server: {e}")
        sys.exit(1)

    link_systems_to_procedures()
    link_deployments_to_systems()
    verify_associations()

    print("\n" + "=" * 70)
    print("Done.")
