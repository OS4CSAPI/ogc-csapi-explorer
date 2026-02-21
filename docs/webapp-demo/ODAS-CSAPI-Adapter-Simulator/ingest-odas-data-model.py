#!/usr/bin/env python3
"""
ODAS Acoustic Array — Complete CSAPI Data Model Ingestion Script
Populates an OSH (OpenSensorHub) server with a fully-populated SOSA/SSN data model
for the ODAS microphone array system, covering all 9 CSAPI resource types.

Usage:
    python ingest-odas-data-model.py [--base-url URL] [--user USER] [--password PASS]
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone, timedelta

# ─── Configuration ───────────────────────────────────────────────────────────
BASE_URL = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
HEADERS_GEOJSON = {"Content-Type": "application/geo+json"}
HEADERS_JSON = {"Content-Type": "application/json"}
HEADERS_OMJSON = {"Content-Type": "application/om+json"}
HEADERS_SWEJSON = {"Content-Type": "application/swe+json"}

# Track all created resource IDs
ids = {}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def post(endpoint, payload, headers=HEADERS_GEOJSON, label="resource"):
    """POST a resource and return the server-assigned ID."""
    url = f"{BASE_URL}/{endpoint}"
    r = requests.post(url, json=payload, headers=headers, auth=AUTH)
    if r.status_code == 201:
        loc = r.headers.get("Location", "")
        rid = loc.rstrip("/").split("/")[-1]
        print(f"  ✓ Created {label}: {rid}  (Location: {loc})")
        return rid
    elif r.status_code == 409:
        # Conflict — resource with this uid already exists. Try to find it.
        print(f"  ⚠ Conflict for {label} — already exists. Attempting lookup...")
        uid = None
        if isinstance(payload, dict):
            uid = payload.get("properties", {}).get("uid") or payload.get("uid") or payload.get("uniqueId")
        if uid:
            search_url = f"{BASE_URL}/{endpoint.split('/')[0]}?uid={uid}"
            sr = requests.get(search_url, auth=AUTH)
            if sr.status_code == 200:
                items = sr.json().get("items", [])
                if items:
                    rid = items[0]["id"]
                    print(f"    → Found existing: {rid}")
                    return rid
        print(f"    → Could not resolve. Status: {r.status_code}, Body: {r.text[:300]}")
        return None
    else:
        print(f"  ✗ FAILED {label}: {r.status_code} — {r.text[:500]}")
        return None


def put_schema(datastream_id, schema_payload, label="schema"):
    """PUT a datastream schema."""
    url = f"{BASE_URL}/datastreams/{datastream_id}/schema"
    r = requests.put(url, json=schema_payload, headers=HEADERS_JSON, auth=AUTH)
    if r.status_code in (200, 201, 204):
        print(f"  ✓ Set schema for datastream {datastream_id}")
        return True
    else:
        print(f"  ⚠ Schema PUT {label}: {r.status_code} — {r.text[:300]}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: PROCEDURES (no dependencies)
# ═══════════════════════════════════════════════════════════════════════════════
def create_procedures():
    print("\n══════ PHASE 1: PROCEDURES ══════")

    ids["proc_audio"] = post("procedures", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:procedure:pdm-mems-audio-capture",
            "featureType": "http://www.w3.org/ns/sosa/Procedure",
            "name": "PDM MEMS Microphone Audio Capture",
            "description": "Pulse Density Modulation (PDM) microphone sampling procedure. Each MEMS microphone produces a 1-bit PDM bitstream at a high oversampling rate. The XMOS xCORE decimation filter converts PDM to PCM at the target sample rate (16000 Hz default). Frame size: 256 samples, hop size: 128 samples. USB Audio Class 1.0 transport to host."
        }
    }, label="Procedure: PDM Audio Capture")

    ids["proc_ssl"] = post("procedures", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:procedure:srp-phat-beamforming",
            "featureType": "http://www.w3.org/ns/sosa/Procedure",
            "name": "SRP-PHAT Steered Response Power Beamforming",
            "description": "Sound Source Localization via Steered Response Power with Phase Transform. For each audio frame: (1) Compute generalized cross-correlation (GCC-PHAT) for all microphone pairs. (2) Scan a virtual hemisphere of candidate directions at configurable angular resolution. (3) For each candidate direction, sum the cross-correlation values for all mic pairs at the expected time delay. (4) The direction with highest accumulated energy is the DOA estimate. Outputs up to 4 potential sources per frame as unit-sphere vectors (x,y,z) with energy E. Input: multi-channel PCM audio. Output: SSL pots {x, y, z, E}[0..3]."
        }
    }, label="Procedure: SRP-PHAT SSL")

    ids["proc_sst"] = post("procedures", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:procedure:particle-filter-tracking",
            "featureType": "http://www.w3.org/ns/sosa/Procedure",
            "name": "Particle Filter Sound Source Tracking",
            "description": "Sound Source Tracking via sequential Monte Carlo (particle filtering). Steps: (1) Prediction via excitation-damping model with three motion states (stationary 10%, constant velocity 40%, acceleration 50%). (2) Instantaneous probability computed by comparing energy to threshold E_T. (3) Observation assignation via Bayesian hypothesis testing (H1: false detection, H2: new source, H3: existing source). (4) Instantiation: initialize H=500 particles from Gaussian distribution when P(new) > T_new for F_new consecutive frames. (5) Removal: destroy filter when P(false) < T_remove for F_remove frames. (6) Weight update using observation likelihood. (7) Resampling when effective particle count drops below threshold. Output: tracked sources with persistent ID, tag, direction (x,y,z), activity level."
        }
    }, label="Procedure: Particle Filter SST")

    ids["proc_tri"] = post("procedures", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:procedure:ray-to-ray-triangulation",
            "featureType": "http://www.w3.org/ns/sosa/Procedure",
            "name": "Multi-Array Ray-to-Ray 3D Triangulation",
            "description": "3D source position estimation from distributed microphone array DOAs (IROS 2017, Lauzon et al.). For K arrays at known positions L_k with DOA unit vectors q_k: (1) For each pair of arrays (a,b), compute the nearest point Z_ab on the two skew DOA lines using the Ray-to-Ray shortest distance algorithm (Schneider and Eberly 2002). (2) Average all K(K-1)/2 pair intersection points to get estimated position. (3) Use this as initialization mean for the particle filter. (4) Particle filter refines position estimate over time with excitation-damping motion model. Requires NTP synchronization between arrays. Minimum 2 arrays; 3+ recommended for robust estimation."
        }
    }, label="Procedure: Ray-to-Ray Triangulation")

    ids["proc_config"] = post("procedures", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:procedure:odas-config-actuation",
            "featureType": "http://www.w3.org/ns/sosa/Procedure",
            "name": "ODAS Runtime Configuration Actuation",
            "description": "Procedure for modifying ODAS pipeline parameters at runtime. Validates parameter values against permitted ranges, applies changes to the active processing pipeline, and confirms the new state. Supports atomic parameter updates (single parameter) and batch updates (multiple parameters in one command). Controllable parameters include: energy threshold E_T, new-source probability threshold T_new, frames-to-confirm F_new, removal threshold T_remove, particle count H, microphone gain, and frame rate."
        }
    }, label="Procedure: Config Actuation")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: TOP-LEVEL SYSTEM (Platform)
# ═══════════════════════════════════════════════════════════════════════════════
def create_platform():
    print("\n══════ PHASE 2: PLATFORM (top-level system) ══════")

    ids["platform"] = post("systems", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:platform:xcore-mic-board-001",
            "featureType": "http://www.w3.org/ns/sosa/Platform",
            "name": "ODAS — XMOS xCORE-200 Microphone Array Board #001",
            "description": "7-microphone circular PDM MEMS array on XMOS xCORE-200 multicore microcontroller board. USB Audio Class 1.0 interface. Hosts the physical microphone sensors and runs the ODAS DSP processing pipeline for sound source localization (SSL), tracking (SST), and geographic bearing estimation. Part of the ODAS (Open embeddeD Audition System) acoustic sensing platform.",
            "validTime": ["2026-01-15T00:00:00Z", None]
        }
    }, label="Platform: XMOS xCORE Board")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: SUBSYSTEMS (under Platform)
# ═══════════════════════════════════════════════════════════════════════════════
def create_subsystems():
    print("\n══════ PHASE 3: SUBSYSTEMS ══════")

    platform_id = ids.get("platform")
    if not platform_id:
        print("  ✗ Cannot create subsystems — platform not created")
        return

    # --- Composite Microphone Array Sensor ---
    ids["mic_array"] = post(f"systems/{platform_id}/subsystems", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:sensor:mic-array-001",
            "featureType": "http://www.w3.org/ns/sosa/Sensor",
            "name": "7-Microphone Circular PDM Array",
            "description": "Circular arrangement of 7 PDM MEMS microphones with 38mm diameter. Functions as a phased array for spatial sound field sampling. Each microphone captures omnidirectional audio; the spatial geometry enables beamforming and direction-of-arrival estimation via cross-correlation of microphone pairs. Center mic at (0,0,0); ring mics at 19mm radius spaced 60 degrees apart.",
            "validTime": ["2026-01-15T00:00:00Z", None],
            "systemKind@link": {
                "href": f"{BASE_URL}/procedures/{ids['proc_audio']}",
                "rel": "systemKind",
                "title": "PDM MEMS Microphone Audio Capture"
            }
        }
    }, label="Sensor: 7-Mic Array")

    # --- Individual Microphones (7) ---
    mic_array_id = ids.get("mic_array")
    if mic_array_id:
        mic_positions = [
            ("Center", "0.000, 0.000, 0.000"),
            ("Ring 0deg", "0.019, 0.000, 0.000"),
            ("Ring 60deg", "0.0095, 0.0164, 0.000"),
            ("Ring 120deg", "-0.0095, 0.0164, 0.000"),
            ("Ring 180deg", "-0.019, 0.000, 0.000"),
            ("Ring 240deg", "-0.0095, -0.0164, 0.000"),
            ("Ring 300deg", "0.0095, -0.0164, 0.000"),
        ]
        for i, (pos_label, coords) in enumerate(mic_positions, 1):
            ids[f"mic_{i}"] = post(f"systems/{mic_array_id}/subsystems", {
                "type": "Feature",
                "geometry": None,
                "properties": {
                    "uid": f"urn:x-odas:sensor:mic-001-ch{i}",
                    "featureType": "http://www.w3.org/ns/sosa/Sensor",
                    "name": f"Microphone #{i} ({pos_label})",
                    "description": f"PDM MEMS microphone at array position {pos_label}. Relative coordinates: ({coords}) meters. Omnidirectional sensitivity pattern. SNR: 65 dB. Sensitivity: -26 dBFS. Frequency response: 100 Hz — 10 kHz.",
                    "validTime": ["2026-01-15T00:00:00Z", None],
                    "systemKind@link": {
                        "href": f"{BASE_URL}/procedures/{ids['proc_audio']}",
                        "rel": "systemKind",
                        "title": "PDM MEMS Microphone Audio Capture"
                    }
                }
            }, label=f"Sensor: Mic #{i}")

    # --- ODAS DSP Processing Pipeline (composite system) ---
    ids["dsp_pipeline"] = post(f"systems/{platform_id}/subsystems", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:system:odas-dsp-001",
            "featureType": "http://www.w3.org/ns/ssn/System",
            "name": "ODAS DSP Processing Pipeline",
            "description": "Software processing pipeline implementing sound source localization (SSL), tracking (SST), and separation (SSS). Runs on host processor, receives raw audio from the XMOS board via USB, outputs structured JSON over TCP sockets. Contains SSL and SST processing modules as subsystems.",
            "validTime": ["2026-01-15T00:00:00Z", None]
        }
    }, label="System: ODAS DSP Pipeline")

    # --- SSL Module (under DSP pipeline) ---
    dsp_id = ids.get("dsp_pipeline")
    if dsp_id:
        ids["ssl_module"] = post(f"systems/{dsp_id}/subsystems", {
            "type": "Feature",
            "geometry": None,
            "properties": {
                "uid": "urn:x-odas:sensor:ssl-001",
                "featureType": "http://www.w3.org/ns/sosa/Sensor",
                "name": "ODAS SSL Module (Sound Source Localizer)",
                "description": "Steered Response Power with Phase Transform (SRP-PHAT) beamformer. Scans a virtual hemisphere around the microphone array, counting the sum of microphone-pair cross-correlations at each point. Outputs up to 4 potential sound source directions per frame as unit-sphere vectors with associated energy values. Frame rate: ~125 Hz (16000 Hz sample rate / 128 hop size).",
                "validTime": ["2026-01-15T00:00:00Z", None],
                "systemKind@link": {
                    "href": f"{BASE_URL}/procedures/{ids['proc_ssl']}",
                    "rel": "systemKind",
                    "title": "SRP-PHAT Steered Response Power Beamforming"
                }
            }
        }, label="Sensor: SSL Module")

        # --- SST Module (under DSP pipeline) ---
        ids["sst_module"] = post(f"systems/{dsp_id}/subsystems", {
            "type": "Feature",
            "geometry": None,
            "properties": {
                "uid": "urn:x-odas:sensor:sst-001",
                "featureType": "http://www.w3.org/ns/sosa/Sensor",
                "name": "ODAS SST Module (Sound Source Tracker)",
                "description": "Particle filter-based sound source tracker. Assigns persistent identity to detected sound sources across frames. Manages source birth (instantiation from Gaussian), tracking (weight update + resampling), and death (removal). Uses excitation-damping motion model with three states: stationary (10%), constant velocity (40%), acceleration (50%). H=500 particles per filter. Output: tracked sources with persistent ID, tag, direction (x,y,z), activity level.",
                "validTime": ["2026-01-15T00:00:00Z", None],
                "systemKind@link": {
                    "href": f"{BASE_URL}/procedures/{ids['proc_sst']}",
                    "rel": "systemKind",
                    "title": "Particle Filter Sound Source Tracking"
                }
            }
        }, label="Sensor: SST Module")

    # --- Configuration Actuator (under platform) ---
    ids["config_actuator"] = post(f"systems/{platform_id}/subsystems", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:actuator:config-001",
            "featureType": "http://www.w3.org/ns/sosa/Actuator",
            "name": "ODAS Runtime Configuration Controller",
            "description": "Actuator interface for modifying ODAS runtime parameters. Controls detection thresholds (E_T), tracking sensitivity (T_new, F_new), particle count (H), microphone gain, and frame processing rate. Acts on system configuration properties to tune the processing pipeline for environmental conditions. Supports synchronous (immediate) and asynchronous (deferred) command execution.",
            "validTime": ["2026-01-15T00:00:00Z", None],
            "systemKind@link": {
                "href": f"{BASE_URL}/procedures/{ids['proc_config']}",
                "rel": "systemKind",
                "title": "ODAS Runtime Configuration Actuation"
            }
        }
    }, label="Actuator: Config Controller")

    # --- Triangulation Engine (under platform) ---
    ids["tri_engine"] = post(f"systems/{platform_id}/subsystems", {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:x-odas:system:triangulation-engine-001",
            "featureType": "http://www.w3.org/ns/ssn/System",
            "name": "Multi-Array 3D Triangulation Engine",
            "description": "Central fusion system that collects DOA vectors from multiple distributed microphone arrays and estimates 3D source positions using Ray-to-Ray intersection (Schneider and Eberly 2002) with particle filtering refinement. Requires NTP-synchronized timestamps from each array. Minimum 2 arrays, 3+ recommended. Based on Lauzon et al. IROS 2017 methodology. Expected accuracy: 1-2m horizontal at 10m array spacing with sigma_phi = 0.0961 rad.",
            "validTime": ["2026-01-15T00:00:00Z", None],
            "systemKind@link": {
                "href": f"{BASE_URL}/procedures/{ids['proc_tri']}",
                "rel": "systemKind",
                "title": "Multi-Array Ray-to-Ray 3D Triangulation"
            }
        }
    }, label="System: Triangulation Engine")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: PROPERTIES
# ═══════════════════════════════════════════════════════════════════════════════
def create_properties():
    print("\n══════ PHASE 4: PROPERTIES ══════")

    ids["prop_doa"] = post("properties", {
        "label": "Sound Source Direction of Arrival",
        "description": "The instantaneous direction from which a sound source is perceived by a microphone array. Expressed as a unit vector (x, y, z) on the unit sphere centered on the array, or equivalently as azimuth and elevation angles. The primary observable output of the SSL module.",
        "uniqueId": "urn:x-odas:property:sound-source-doa",
        "baseProperty": "http://qudt.org/vocab/quantitykind/Angle",
        "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest"
    }, headers=HEADERS_JSON, label="Property: Sound Source DOA")

    ids["prop_energy"] = post("properties", {
        "label": "Sound Source Energy",
        "description": "The accumulated beamformer response energy at the detected direction of arrival. Proportional to the signal-to-noise ratio of the source. Values range from 0 (noise floor) to 1+ (strong source). The energy threshold E_T (default: 600 unnormalized) discriminates real sources from noise.",
        "uniqueId": "urn:x-odas:property:sound-source-energy",
        "baseProperty": "http://qudt.org/vocab/quantitykind/Energy",
        "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest"
    }, headers=HEADERS_JSON, label="Property: Sound Energy")

    ids["prop_activity"] = post("properties", {
        "label": "Sound Source Activity Level",
        "description": "The tracking activity level of a sound source, representing the tracker confidence that the source is currently producing sound. Ranges from 0.0 (inactive/lost) to 1.0 (highly active). Derived from particle filter weight diversity and observation assignment probabilities.",
        "uniqueId": "urn:x-odas:property:source-activity-level",
        "baseProperty": "http://qudt.org/vocab/quantitykind/DimensionlessRatio",
        "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest"
    }, headers=HEADERS_JSON, label="Property: Activity Level")

    ids["prop_bearing"] = post("properties", {
        "label": "Geographic Line of Bearing",
        "description": "The true geographic azimuth bearing from a sensor array to a detected sound source. Computed by transforming the array-local DOA unit vector to a geographic azimuth using the array known position and orientation. Expressed in degrees clockwise from true north (0-360).",
        "uniqueId": "urn:x-odas:property:geographic-bearing",
        "baseProperty": "http://qudt.org/vocab/quantitykind/Angle",
        "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest"
    }, headers=HEADERS_JSON, label="Property: Geographic Bearing")

    ids["prop_tripos"] = post("properties", {
        "label": "Triangulated 3D Source Position",
        "description": "The estimated 3D geographic position of a sound source, derived from multi-array triangulation. Computed via Ray-to-Ray intersection of DOA vectors from 2+ distributed arrays. Includes estimated uncertainty based on DOA angle variance (sigma_phi approx 0.0961 rad / ~5.5 degrees) and array geometry.",
        "uniqueId": "urn:x-odas:property:triangulated-position",
        "baseProperty": "http://qudt.org/vocab/quantitykind/Position",
        "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest"
    }, headers=HEADERS_JSON, label="Property: Triangulated Position")

    ids["prop_threshold"] = post("properties", {
        "label": "Detection Energy Threshold",
        "description": "The energy threshold E_T that discriminates real sound sources from noise in the SSL module. Observations with energy below this threshold are classified as noise. Default value: 600. Lowering increases sensitivity but also false detections; raising reduces sensitivity but improves precision.",
        "uniqueId": "urn:x-odas:property:detection-threshold",
        "baseProperty": "http://qudt.org/vocab/quantitykind/Energy",
        "objectType": "http://www.w3.org/ns/ssn/System"
    }, headers=HEADERS_JSON, label="Property: Detection Threshold")

    ids["prop_sensitivity"] = post("properties", {
        "label": "Tracking New Source Sensitivity",
        "description": "The probability threshold T_new that must be exceeded for F_new consecutive frames to instantiate a new tracked source. Default: T_new=0.75, F_new=10 frames. Lower values create tracks more readily; higher values require stronger evidence before starting a new track.",
        "uniqueId": "urn:x-odas:property:tracking-sensitivity",
        "baseProperty": "http://qudt.org/vocab/quantitykind/DimensionlessRatio",
        "objectType": "http://www.w3.org/ns/ssn/System"
    }, headers=HEADERS_JSON, label="Property: Tracking Sensitivity")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: DEPLOYMENTS
# ═══════════════════════════════════════════════════════════════════════════════
def create_deployments():
    print("\n══════ PHASE 5: DEPLOYMENTS ══════")

    ids["deploy_single"] = post("deployments", {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [-77.0365, 38.8977, 2.5]
        },
        "properties": {
            "uid": "urn:x-odas:deployment:office-array-001",
            "featureType": "http://www.w3.org/ns/sosa/Deployment",
            "name": "Conference Room 3A — Single Array Deployment",
            "description": "Deployment of XMOS microphone array board #001 on the ceiling of Conference Room 3A, Building 7. Array is mounted facing downward at 2.5m height, centered over the conference table. Orientation: array X-axis aligned with geographic north. Purpose: meeting room occupancy sensing and speaker localization for smart building applications. Carpeted floor, acoustic ceiling tiles, glass wall on south side. Typical background noise: HVAC at ~35 dBA.",
            "validTime": ["2026-02-01T09:00:00Z", None],
            "platform@link": {
                "href": f"{BASE_URL}/systems/{ids.get('platform')}",
                "rel": "platform",
                "title": "ODAS \u2014 XMOS xCORE-200 Microphone Array Board #001"
            },
            "deployedSystems@link": [{
                "href": f"{BASE_URL}/systems/{ids.get('platform')}",
                "rel": "deployedSystem",
                "title": "ODAS \u2014 XMOS xCORE-200 Microphone Array Board #001"
            }]
        }
    }, label="Deployment: Single Array (Conference Room)")

    # --- Multi-array parent deployment ---
    ids["deploy_multi"] = post("deployments", {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-77.0380, 38.8970],
                [-77.0350, 38.8970],
                [-77.0350, 38.8990],
                [-77.0380, 38.8990],
                [-77.0380, 38.8970]
            ]]
        },
        "properties": {
            "uid": "urn:x-odas:deployment:campus-triangulation",
            "featureType": "http://www.w3.org/ns/sosa/Deployment",
            "name": "Campus Perimeter — 3-Array Triangulation Deployment",
            "description": "Deployment of three distributed microphone arrays in a triangular configuration (10m spacing) for 3D sound source localization via DOA triangulation. Based on Lauzon et al. IROS 2017 methodology. Arrays positioned on the ground facing upward. Central fusion node performs Ray-to-Ray intersection. Expected horizontal accuracy: 1-2m. NTP synchronization required between all nodes.",
            "validTime": ["2026-02-15T00:00:00Z", None],
            "platform@link": {
                "href": f"{BASE_URL}/systems/{ids.get('platform')}",
                "rel": "platform",
                "title": "ODAS \u2014 XMOS xCORE-200 Microphone Array Board #001"
            },
            "deployedSystems@link": [{
                "href": f"{BASE_URL}/systems/{ids.get('platform')}",
                "rel": "deployedSystem",
                "title": "ODAS \u2014 XMOS xCORE-200 Microphone Array Board #001"
            }]
        }
    }, label="Deployment: 3-Array Triangulation (parent)")

    # --- Sub-deployments for each array position ---
    multi_id = ids.get("deploy_multi")
    if multi_id:
        array_positions = [
            ("North", -77.0365, 38.8985, "urn:x-odas:deployment:array-north"),
            ("Southeast", -77.0355, 38.8975, "urn:x-odas:deployment:array-southeast"),
            ("Southwest", -77.0375, 38.8975, "urn:x-odas:deployment:array-southwest"),
        ]
        for name, lon, lat, uid in array_positions:
            ids[f"deploy_{name.lower()}"] = post(f"deployments/{multi_id}/subdeployments", {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat, 1.0]
                },
                "properties": {
                    "uid": uid,
                    "featureType": "http://www.w3.org/ns/sosa/Deployment",
                    "name": f"Array Position — {name}",
                    "description": f"Sub-deployment placing one XMOS microphone array board at the {name.lower()} position of the triangulation triangle. Array mounted on tripod at 1.0m height, facing upward. GPS coordinates surveyed to ±0.5m accuracy.",
                    "validTime": ["2026-02-15T00:00:00Z", None],
                    "platform@link": {
                        "href": f"{BASE_URL}/systems/{ids.get('platform')}",
                        "rel": "platform",
                        "title": "ODAS — XMOS xCORE-200 Microphone Array Board #001"
                    },
                    "deployedSystems@link": [{
                        "href": f"{BASE_URL}/systems/{ids.get('platform')}",
                        "rel": "deployedSystem",
                        "title": "ODAS — XMOS xCORE-200 Microphone Array Board #001"
                    }]
                }
            }, label=f"Sub-deployment: {name}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: SAMPLING FEATURES
# ═══════════════════════════════════════════════════════════════════════════════
def create_sampling_features():
    print("\n══════ PHASE 6: SAMPLING FEATURES ══════")

    platform_id = ids.get("platform")
    sf_endpoint = f"systems/{platform_id}/samplingFeatures" if platform_id else "samplingFeatures"

    ids["foi_room"] = post(sf_endpoint, {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-77.0366, 38.8976],
                [-77.0364, 38.8976],
                [-77.0364, 38.8978],
                [-77.0366, 38.8978],
                [-77.0366, 38.8976]
            ]]
        },
        "properties": {
            "uid": "urn:x-odas:foi:conference-room-3a",
            "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingSurface",
            "name": "Conference Room 3A — Acoustic Environment",
            "description": "The acoustic environment of Conference Room 3A, Building 7. Approximately 8m x 6m x 3m. Carpeted floor, acoustic ceiling tiles, glass wall on south side. Typical background noise: HVAC at ~35 dBA. This is the ultimate feature of interest whose acoustic properties we characterize through microphone array observations."
        }
    }, label="SamplingFeature: Conference Room 3A (FOI)")

    ids["sf_zone"] = post(sf_endpoint, {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-77.0367, 38.8975],
                [-77.0363, 38.8975],
                [-77.0363, 38.8979],
                [-77.0367, 38.8979],
                [-77.0367, 38.8975]
            ]]
        },
        "properties": {
            "uid": "urn:x-odas:sample:monitoring-zone-001",
            "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingSurface",
            "name": "Array #001 Acoustic Monitoring Zone",
            "description": "The effective acoustic monitoring zone of microphone array #001. Defined by the hemisphere of directions the array can resolve (full 2-pi steradian hemisphere below the ceiling-mounted array). Effective range depends on source loudness vs. background noise: approximately 5-10m for normal speech (60 dBA), 20-50m for machinery or drone propellers (80+ dBA). This sampling feature represents the spatial sample through which the room acoustic environment is observed."
        }
    }, label="SamplingFeature: Monitoring Zone (Sample)")

    ids["sf_campus"] = post(sf_endpoint, {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-77.0385, 38.8965],
                [-77.0345, 38.8965],
                [-77.0345, 38.8995],
                [-77.0385, 38.8995],
                [-77.0385, 38.8965]
            ]]
        },
        "properties": {
            "uid": "urn:x-odas:foi:campus-perimeter-zone",
            "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingSurface",
            "name": "Campus Perimeter — Outdoor Acoustic Environment",
            "description": "The outdoor acoustic environment of the campus perimeter area monitored by the 3-array triangulation deployment. Approximately 300m x 300m open area with scattered buildings. Background noise: ambient outdoor (~45 dBA). Primary targets: drone detection (propeller noise 70-85 dBA at 50m), vehicle tracking, and emergency siren localization."
        }
    }, label="SamplingFeature: Campus Outdoor FOI")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: DATASTREAMS (under specific sensors)
# ═══════════════════════════════════════════════════════════════════════════════
def create_datastreams():
    print("\n══════ PHASE 7: DATASTREAMS ══════")

    # --- SSL Pots DataStream (under SSL module) ---
    ssl_id = ids.get("ssl_module")
    if ssl_id:
        ids["ds_ssl"] = post(f"systems/{ssl_id}/datastreams", {
            "name": "SSL Potential Sources — Array #001",
            "description": "Raw Sound Source Localization output from array #001. Each observation contains up to 4 potential source directions as unit-sphere vectors with energy values. Updated at frame rate (~125 Hz: 16000 Hz sample rate / 128 hop size).",
            "outputName": "ssl_pots",
            "observedProperties": [
                {
                    "definition": "urn:x-odas:property:sound-source-doa",
                    "label": "Sound Source Direction of Arrival",
                    "description": "Unit-sphere direction vector (x, y, z) to detected source"
                },
                {
                    "definition": "urn:x-odas:property:sound-source-energy",
                    "label": "Sound Source Energy",
                    "description": "Accumulated beamformer response energy"
                }
            ],
            "resultType": "record",
            "validTime": ["2026-02-01T09:00:00Z", None]
        }, headers=HEADERS_JSON, label="DataStream: SSL Pots")

        # Set schema for SSL datastream
        if ids.get("ds_ssl"):
            put_schema(ids["ds_ssl"], {
                "obsFormat": "application/om+json",
                "resultSchema": {
                    "type": "DataRecord",
                    "name": "ssl_pots",
                    "label": "SSL Potential Sources",
                    "description": "Up to 4 potential sound source detections per frame",
                    "fields": [
                        {
                            "type": "Count",
                            "name": "numSources",
                            "label": "Number of detected sources",
                            "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                        },
                        {
                            "type": "DataArray",
                            "name": "sources",
                            "label": "Potential Sources Array",
                            "definition": "http://sensorml.com/ont/swe/property/ArrayOfVectors",
                            "elementCount": {
                                "type": "Count",
                                "value": 4
                            },
                            "elementType": {
                                "type": "DataRecord",
                                "name": "source",
                                "label": "Potential Source",
                                "fields": [
                                    {
                                        "type": "Quantity",
                                        "name": "x",
                                        "label": "DOA X Component",
                                        "definition": "http://sensorml.com/ont/swe/property/DirectionX",
                                        "uom": {"code": "1"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "y",
                                        "label": "DOA Y Component",
                                        "definition": "http://sensorml.com/ont/swe/property/DirectionY",
                                        "uom": {"code": "1"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "z",
                                        "label": "DOA Z Component",
                                        "definition": "http://sensorml.com/ont/swe/property/DirectionZ",
                                        "uom": {"code": "1"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "energy",
                                        "label": "Beamformer Energy",
                                        "definition": "urn:x-odas:property:sound-source-energy",
                                        "uom": {"code": "1"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            }, label="SSL schema")

    # --- SST Tracks DataStream (under SST module) ---
    sst_id = ids.get("sst_module")
    if sst_id:
        ids["ds_sst"] = post(f"systems/{sst_id}/datastreams", {
            "name": "SST Tracked Sources — Array #001",
            "description": "Sound Source Tracking output. Each observation contains currently tracked sources with persistent IDs, direction vectors, activity levels, and classification tags. Sources are born when detection exceeds T_new for F_new frames and die when below T_remove for F_remove frames.",
            "outputName": "sst_tracks",
            "observedProperties": [
                {
                    "definition": "urn:x-odas:property:sound-source-doa",
                    "label": "Sound Source Direction of Arrival"
                },
                {
                    "definition": "urn:x-odas:property:source-activity-level",
                    "label": "Sound Source Activity Level"
                }
            ],
            "resultType": "record",
            "validTime": ["2026-02-01T09:00:00Z", None]
        }, headers=HEADERS_JSON, label="DataStream: SST Tracks")

        if ids.get("ds_sst"):
            put_schema(ids["ds_sst"], {
                "obsFormat": "application/om+json",
                "resultSchema": {
                    "type": "DataRecord",
                    "name": "sst_tracks",
                    "label": "SST Tracked Sources",
                    "description": "Currently tracked sources with persistent identity",
                    "fields": [
                        {
                            "type": "Count",
                            "name": "numTracks",
                            "label": "Number of active tracks",
                            "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                        },
                        {
                            "type": "DataArray",
                            "name": "tracks",
                            "label": "Tracked Sources Array",
                            "definition": "http://sensorml.com/ont/swe/property/ArrayOfVectors",
                            "elementCount": {
                                "type": "Count",
                                "value": 4
                            },
                            "elementType": {
                                "type": "DataRecord",
                                "name": "track",
                                "label": "Tracked Source",
                                "fields": [
                                    {
                                        "type": "Count",
                                        "name": "id",
                                        "label": "Track ID",
                                        "definition": "http://sensorml.com/ont/swe/property/TrackID"
                                    },
                                    {
                                        "type": "Text",
                                        "name": "tag",
                                        "label": "Classification Tag",
                                        "definition": "http://sensorml.com/ont/swe/property/Classification"
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "x",
                                        "label": "DOA X",
                                        "definition": "http://sensorml.com/ont/swe/property/DirectionX",
                                        "uom": {"code": "1"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "y",
                                        "label": "DOA Y",
                                        "definition": "http://sensorml.com/ont/swe/property/DirectionY",
                                        "uom": {"code": "1"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "z",
                                        "label": "DOA Z",
                                        "definition": "http://sensorml.com/ont/swe/property/DirectionZ",
                                        "uom": {"code": "1"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "activity",
                                        "label": "Activity Level",
                                        "definition": "urn:x-odas:property:source-activity-level",
                                        "uom": {"code": "1"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            }, label="SST schema")

    # --- Geographic LOB DataStream (also under SSL module) ---
    if ssl_id:
        ids["ds_lob"] = post(f"systems/{ssl_id}/datastreams", {
            "name": "Geographic Lines of Bearing — Array #001",
            "description": "Transformed SSL output projected into geographic coordinates. Each observation contains Lines of Bearing (LOBs) as true azimuth bearings from the array known geographic position. Primary geospatial data stream for map visualization. Derived from SSL unit-sphere vectors via coordinate rotation using array orientation.",
            "outputName": "geographic_lob",
            "observedProperties": [
                {
                    "definition": "urn:x-odas:property:geographic-bearing",
                    "label": "Geographic Line of Bearing"
                },
                {
                    "definition": "urn:x-odas:property:sound-source-energy",
                    "label": "Sound Source Energy"
                }
            ],
            "resultType": "record",
            "validTime": ["2026-02-01T09:00:00Z", None]
        }, headers=HEADERS_JSON, label="DataStream: Geographic LOBs")

        if ids.get("ds_lob"):
            put_schema(ids["ds_lob"], {
                "obsFormat": "application/om+json",
                "resultSchema": {
                    "type": "DataRecord",
                    "name": "geographic_lob",
                    "label": "Geographic Lines of Bearing",
                    "fields": [
                        {
                            "type": "Count",
                            "name": "numBearings",
                            "label": "Number of bearings",
                            "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                        },
                        {
                            "type": "DataArray",
                            "name": "bearings",
                            "label": "LOB Array",
                            "definition": "http://sensorml.com/ont/swe/property/ArrayOfVectors",
                            "elementCount": {
                                "type": "Count",
                                "value": 4
                            },
                            "elementType": {
                                "type": "DataRecord",
                                "name": "bearing",
                                "label": "Line of Bearing",
                                "fields": [
                                    {
                                        "type": "Count",
                                        "name": "sourceId",
                                        "label": "Source Track ID",
                                        "definition": "http://sensorml.com/ont/swe/property/TrackID"
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "azimuth",
                                        "label": "True Azimuth Bearing",
                                        "definition": "http://sensorml.com/ont/swe/property/TrueHeading",
                                        "uom": {"code": "deg"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "elevation",
                                        "label": "Elevation Angle",
                                        "definition": "http://sensorml.com/ont/swe/property/ElevationAngle",
                                        "uom": {"code": "deg"}
                                    },
                                    {
                                        "type": "Quantity",
                                        "name": "energy",
                                        "label": "Source Energy",
                                        "definition": "urn:x-odas:property:sound-source-energy",
                                        "uom": {"code": "1"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            }, label="LOB schema")

    # --- Triangulated Position DataStream (under triangulation engine) ---
    tri_id = ids.get("tri_engine")
    if tri_id:
        ids["ds_tri"] = post(f"systems/{tri_id}/datastreams", {
            "name": "Triangulated 3D Source Positions",
            "description": "Estimated 3D positions of sound sources from multi-array triangulation. Each observation contains the fused position estimate with uncertainty, contributing array IDs, and Ray-to-Ray intersection quality metrics. Only populated when 2+ arrays observe the same source simultaneously.",
            "outputName": "triangulated_positions",
            "observedProperties": [
                {
                    "definition": "urn:x-odas:property:triangulated-position",
                    "label": "Triangulated 3D Source Position"
                }
            ],
            "resultType": "record",
            "validTime": ["2026-02-15T00:00:00Z", None]
        }, headers=HEADERS_JSON, label="DataStream: Triangulated Positions")

        if ids.get("ds_tri"):
            put_schema(ids["ds_tri"], {
                "obsFormat": "application/om+json",
                "resultSchema": {
                    "type": "DataRecord",
                    "name": "triangulated_positions",
                    "label": "Triangulated Source Position",
                    "fields": [
                        {
                            "type": "Quantity",
                            "name": "latitude",
                            "label": "Latitude",
                            "definition": "http://sensorml.com/ont/swe/property/GeodeticLatitude",
                            "uom": {"code": "deg"},
                            "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4326"
                        },
                        {
                            "type": "Quantity",
                            "name": "longitude",
                            "label": "Longitude",
                            "definition": "http://sensorml.com/ont/swe/property/Longitude",
                            "uom": {"code": "deg"},
                            "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4326"
                        },
                        {
                            "type": "Quantity",
                            "name": "altitude",
                            "label": "Altitude (m)",
                            "definition": "http://sensorml.com/ont/swe/property/AltitudeAGL",
                            "uom": {"code": "m"}
                        },
                        {
                            "type": "Quantity",
                            "name": "horizontalAccuracy",
                            "label": "Horizontal Accuracy (m)",
                            "definition": "http://sensorml.com/ont/swe/property/HorizontalAccuracy",
                            "uom": {"code": "m"}
                        },
                        {
                            "type": "Quantity",
                            "name": "confidence",
                            "label": "Confidence",
                            "definition": "http://sensorml.com/ont/swe/property/QualityIndex",
                            "uom": {"code": "1"}
                        },
                        {
                            "type": "Count",
                            "name": "numContributingArrays",
                            "label": "Number of Contributing Arrays",
                            "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                        }
                    ]
                }
            }, label="Triangulation schema")

    # --- System Status DataStream (under DSP pipeline) ---
    dsp_id = ids.get("dsp_pipeline")
    if dsp_id:
        ids["ds_status"] = post(f"systems/{dsp_id}/datastreams", {
            "name": "System Health and Status — Array #001",
            "description": "Periodic system health reports: CPU load, audio buffer health, active track count, current parameter values, USB connection state. Published every 5 seconds.",
            "outputName": "system_status",
            "observedProperties": [],
            "resultType": "record",
            "validTime": ["2026-02-01T09:00:00Z", None]
        }, headers=HEADERS_JSON, label="DataStream: System Status")

        if ids.get("ds_status"):
            put_schema(ids["ds_status"], {
                "obsFormat": "application/om+json",
                "resultSchema": {
                    "type": "DataRecord",
                    "name": "system_status",
                    "label": "System Health Status",
                    "fields": [
                        {
                            "type": "Quantity",
                            "name": "cpuLoad",
                            "label": "CPU Load",
                            "definition": "http://sensorml.com/ont/swe/property/SystemLoad",
                            "uom": {"code": "%"}
                        },
                        {
                            "type": "Boolean",
                            "name": "usbConnected",
                            "label": "USB Connection Active",
                            "definition": "http://sensorml.com/ont/swe/property/ConnectionStatus"
                        },
                        {
                            "type": "Count",
                            "name": "activeTrackCount",
                            "label": "Active Sound Source Tracks",
                            "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                        },
                        {
                            "type": "Quantity",
                            "name": "bufferHealth",
                            "label": "Audio Buffer Health",
                            "definition": "http://sensorml.com/ont/swe/property/BufferLevel",
                            "uom": {"code": "%"}
                        },
                        {
                            "type": "Quantity",
                            "name": "currentThreshold",
                            "label": "Current Energy Threshold (E_T)",
                            "definition": "urn:x-odas:property:detection-threshold",
                            "uom": {"code": "1"}
                        }
                    ]
                }
            }, label="Status schema")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: OBSERVATIONS (sample data under datastreams)
# ═══════════════════════════════════════════════════════════════════════════════
def create_observations():
    print("\n══════ PHASE 8: OBSERVATIONS ══════")

    now = datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc)

    # SSL observations (3 frames of simulated data)
    ds_ssl = ids.get("ds_ssl")
    if ds_ssl:
        for frame_idx in range(5):
            t = now + timedelta(milliseconds=frame_idx * 8)
            ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"
            rt = (t + timedelta(milliseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.") + f"{(t + timedelta(milliseconds=1)).microsecond // 1000:03d}Z"

            # Simulate a speaker at ~70deg azimuth + faint noise source
            import math
            az_rad = math.radians(70 + frame_idx * 0.3)
            x1, y1 = round(math.sin(az_rad), 4), round(math.cos(az_rad), 4)
            e1 = round(0.85 + frame_idx * 0.01, 4)

            az2_rad = math.radians(210 + frame_idx * 0.1)
            x2, y2 = round(math.sin(az2_rad), 4), round(math.cos(az2_rad), 4)
            e2 = round(0.25 - frame_idx * 0.02, 4)

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "numSources": 2,
                    "sources": [
                        {"x": x1, "y": y1, "z": 0.0, "energy": e1},
                        {"x": x2, "y": y2, "z": 0.0, "energy": e2},
                        {"x": 0.0, "y": 0.0, "z": 0.0, "energy": 0.0},
                        {"x": 0.0, "y": 0.0, "z": 0.0, "energy": 0.0}
                    ]
                }
            }
            post(f"datastreams/{ds_ssl}/observations",
                 obs, headers=HEADERS_OMJSON,
                 label=f"SSL Obs frame {frame_idx}")

    # SST observations
    ds_sst = ids.get("ds_sst")
    if ds_sst:
        for frame_idx in range(5):
            t = now + timedelta(milliseconds=frame_idx * 8)
            ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"
            rt = (t + timedelta(milliseconds=4)).strftime("%Y-%m-%dT%H:%M:%S.") + f"{(t + timedelta(milliseconds=4)).microsecond // 1000:03d}Z"

            import math
            az_rad = math.radians(70 + frame_idx * 0.3)
            x1, y1 = round(math.sin(az_rad), 4), round(math.cos(az_rad), 4)
            activity = round(0.92 + frame_idx * 0.01, 4)

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "numTracks": 1,
                    "tracks": [
                        {"id": 42, "tag": "dynamic", "x": x1, "y": y1, "z": 0.0, "activity": activity},
                        {"id": 0, "tag": "", "x": 0.0, "y": 0.0, "z": 0.0, "activity": 0.0},
                        {"id": 0, "tag": "", "x": 0.0, "y": 0.0, "z": 0.0, "activity": 0.0},
                        {"id": 0, "tag": "", "x": 0.0, "y": 0.0, "z": 0.0, "activity": 0.0}
                    ]
                }
            }
            post(f"datastreams/{ds_sst}/observations",
                 obs, headers=HEADERS_OMJSON,
                 label=f"SST Obs frame {frame_idx}")

    # LOB observations
    ds_lob = ids.get("ds_lob")
    if ds_lob:
        for frame_idx in range(5):
            t = now + timedelta(milliseconds=frame_idx * 8)
            ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"
            rt = (t + timedelta(milliseconds=6)).strftime("%Y-%m-%dT%H:%M:%S.") + f"{(t + timedelta(milliseconds=6)).microsecond // 1000:03d}Z"

            azimuth = round(70.0 + frame_idx * 0.3, 2)
            energy = round(0.85 + frame_idx * 0.01, 4)

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "numBearings": 1,
                    "bearings": [
                        {"sourceId": 42, "azimuth": azimuth, "elevation": 0.0, "energy": energy},
                        {"sourceId": 0, "azimuth": 0.0, "elevation": 0.0, "energy": 0.0},
                        {"sourceId": 0, "azimuth": 0.0, "elevation": 0.0, "energy": 0.0},
                        {"sourceId": 0, "azimuth": 0.0, "elevation": 0.0, "energy": 0.0}
                    ]
                }
            }
            post(f"datastreams/{ds_lob}/observations",
                 obs, headers=HEADERS_OMJSON,
                 label=f"LOB Obs frame {frame_idx}")

    # Triangulated position observations
    ds_tri = ids.get("ds_tri")
    if ds_tri:
        for frame_idx in range(3):
            t = now + timedelta(milliseconds=frame_idx * 50)
            ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"
            rt = (t + timedelta(milliseconds=25)).strftime("%Y-%m-%dT%H:%M:%S.") + f"{(t + timedelta(milliseconds=25)).microsecond // 1000:03d}Z"

            lat = round(38.8985 + frame_idx * 0.00001, 6)
            lon = round(-77.0355 + frame_idx * 0.00001, 6)
            alt = round(15.2 + frame_idx * 0.1, 1)
            accuracy = round(1.2 - frame_idx * 0.1, 2)
            confidence = round(0.82 + frame_idx * 0.03, 2)

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": alt,
                    "horizontalAccuracy": accuracy,
                    "confidence": confidence,
                    "numContributingArrays": 3
                }
            }
            post(f"datastreams/{ds_tri}/observations",
                 obs, headers=HEADERS_OMJSON,
                 label=f"Triangulation Obs {frame_idx}")

    # System status observations
    ds_status = ids.get("ds_status")
    if ds_status:
        for i in range(3):
            t = now + timedelta(seconds=i * 5)
            ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"

            obs = {
                "phenomenonTime": ts,
                "resultTime": ts,
                "result": {
                    "cpuLoad": round(23.5 + i * 2.1, 1),
                    "usbConnected": True,
                    "activeTrackCount": 1,
                    "bufferHealth": round(98.0 - i * 0.5, 1),
                    "currentThreshold": 600.0
                }
            }
            post(f"datastreams/{ds_status}/observations",
                 obs, headers=HEADERS_OMJSON,
                 label=f"Status Obs {i}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: CONTROL STREAMS & COMMANDS (under actuator)
# ═══════════════════════════════════════════════════════════════════════════════
def create_control_streams_and_commands():
    print("\n══════ PHASE 9: CONTROL STREAMS & COMMANDS ══════")

    actuator_id = ids.get("config_actuator")
    if not actuator_id:
        print("  ✗ Cannot create control streams — actuator not created")
        return

    ids["cs_detection"] = post(f"systems/{actuator_id}/controlstreams", {
        "name": "Detection Parameters Control — Array #001",
        "description": "Control stream for adjusting SSL/SST detection parameters at runtime. Accepts commands to modify energy threshold (E_T), new source probability threshold (T_new), frames-to-confirm (F_new), and false positive probability (P_false). Changes take effect on the next processed frame.",
        "inputName": "detection_params",
        "controlledProperties": [
            {
                "definition": "urn:x-odas:property:detection-threshold",
                "label": "Detection Energy Threshold"
            },
            {
                "definition": "urn:x-odas:property:tracking-sensitivity",
                "label": "Tracking New Source Sensitivity"
            }
        ],
        "validTime": ["2026-02-01T09:00:00Z", None]
    }, headers=HEADERS_JSON, label="ControlStream: Detection Params")

    # --- Commands ---
    cs_id = ids.get("cs_detection")
    if cs_id:
        # Command 1: Lower threshold
        ids["cmd_lower_threshold"] = post(f"controlstreams/{cs_id}/commands", {
            "issueTime": "2026-02-20T14:35:00Z",
            "executionTime": "2026-02-20T14:35:00.005Z",
            "sender": "urn:x-odas:user:operator-1",
            "parameters": {
                "energyThreshold": 400,
                "reason": "Lowering threshold to detect quieter sources in low-noise environment"
            }
        }, headers=HEADERS_JSON, label="Command: Lower Threshold")

        # Command 2: Increase tracking sensitivity
        ids["cmd_sensitivity"] = post(f"controlstreams/{cs_id}/commands", {
            "issueTime": "2026-02-20T14:40:00Z",
            "executionTime": "2026-02-20T14:40:00.003Z",
            "sender": "urn:x-odas:user:operator-1",
            "parameters": {
                "trackingSensitivity": 0.6,
                "framesToConfirm": 8,
                "reason": "Increasing sensitivity for surveillance scenario"
            }
        }, headers=HEADERS_JSON, label="Command: Increase Sensitivity")

        # Command 3: Reset to defaults
        ids["cmd_reset"] = post(f"controlstreams/{cs_id}/commands", {
            "issueTime": "2026-02-20T15:00:00Z",
            "executionTime": "2026-02-20T15:00:00.002Z",
            "sender": "urn:x-odas:user:operator-1",
            "parameters": {
                "energyThreshold": 600,
                "trackingSensitivity": 0.75,
                "framesToConfirm": 10,
                "reason": "Resetting all parameters to defaults"
            }
        }, headers=HEADERS_JSON, label="Command: Reset Defaults")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("ODAS Acoustic Array — CSAPI Data Model Ingestion")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # Test connection
    try:
        r = requests.get(BASE_URL, auth=AUTH, timeout=10)
        r.raise_for_status()
        print(f"✓ Server reachable: {r.json().get('title', 'unknown')}\n")
    except Exception as e:
        print(f"✗ Cannot reach server: {e}")
        sys.exit(1)

    # Execute all phases in dependency order
    create_procedures()       # Phase 1: No dependencies
    create_platform()         # Phase 2: No dependencies
    create_subsystems()       # Phase 3: Depends on platform
    create_properties()       # Phase 4: No dependencies
    create_deployments()      # Phase 5: No dependencies
    create_sampling_features()  # Phase 6: Depends on platform
    create_datastreams()      # Phase 7: Depends on subsystems
    create_observations()     # Phase 8: Depends on datastreams
    create_control_streams_and_commands()  # Phase 9: Depends on actuator

    # Summary
    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)
    created = {k: v for k, v in ids.items() if v is not None}
    failed = {k: v for k, v in ids.items() if v is None}
    print(f"  Created: {len(created)} resources")
    print(f"  Failed:  {len(failed)} resources")

    if created:
        print("\n  Resource IDs:")
        for k, v in created.items():
            print(f"    {k}: {v}")

    if failed:
        print("\n  Failed resources:")
        for k in failed:
            print(f"    {k}")

    print("\n" + "=" * 70)
    print("Done.")
