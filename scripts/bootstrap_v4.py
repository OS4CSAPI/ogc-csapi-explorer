#!/usr/bin/env python3
"""
bootstrap_v4.py — Authoritative bootstrap for OS4CSAPI OSH server (DuckDNS Oracle).

Self-contained: ALL data is inline (no external files).
Recreates the entire Oracle state from scratch:
  - 6 top-level systems (SET-A, Monitoring Site, Relay, AZ-MA-1/2/3)
  - 39 MA node subsystems (13 each × 3 nodes)
  - 7-level deployment hierarchy (ICO → R&S → SSO → SNET → Field → String Alpha → Nodes 1-3)
  - platform@link on Nodes 1-3 → AZ-MA-1/2/3
  - 22 datastreams (1 SENREP on SET-A, 7 per MA node × 3)
  - 9 control streams (3 per MA node × 3)
  - deployedSystemUIDs on SSO and SNET

Supersedes bootstrap_v3.1.py.

Usage:
    python bootstrap_v4.py                 # create everything (skip if exists)
    python bootstrap_v4.py --clean         # delete everything, then recreate
    python bootstrap_v4.py --clean-only    # delete everything, don't recreate
    python bootstrap_v4.py --dry-run       # print what would happen
    python bootstrap_v4.py --fix-uids      # only fix deployedSystemUIDs on SNET
"""

import argparse
import base64
import json
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ═════════════════════════════════════════════════════════════════════════════
#  Configuration
# ═════════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"

# DuckDNS → Oracle Cloud IP (self-signed cert)
ORACLE_IP = "129.80.248.53"

VALID_TIME_START     = "2026-02-27T00:00:00Z"
AZMA1_VALID_START    = "2026-01-01T00:00:00Z"
NODE1_VALID_START    = "2026-01-15T00:00:00Z"
NODE2_VALID_START    = "2026-01-15T00:00:00Z"
NODE3_VALID_START    = "2026-01-15T00:00:00Z"

# ═════════════════════════════════════════════════════════════════════════════
#  System definitions
# ═════════════════════════════════════════════════════════════════════════════

SYSTEMS = [
    {
        "uid":  "urn:os4csapi:system:set:ft-huachuca:001",
        "name": "Sensor Employment Team (SET-A)",
        "description": "SET responsible for receiving sensor data, conducting analysis, and generating SENREP reports.",
        "featureType": "sosa:Platform",
        "geometry": {"type": "Point", "coordinates": [-110.2524769, 31.6380757]},
        "validTime": [VALID_TIME_START, ".."],
    },
    {
        "uid":  "urn:os4csapi:system:monitoring-site-node:ft-huachuca:001",
        "name": "Monitoring Site Node 1",
        "description": "Operational monitoring node (equipment + comms) that enables SET data reception and processing.",
        "featureType": "sosa:Platform",
        "geometry": {"type": "Point", "coordinates": [-110.2525675, 31.6383956]},
        "validTime": [VALID_TIME_START, ".."],
    },
    {
        "uid":  "urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001",
        "name": "Relay / Repeater 001",
        "description": "VHF radio repeater forwarding sensor transmissions to the monitoring site.",
        "featureType": "sosa:Platform",
        "geometry": {"type": "Point", "coordinates": [-110.2554653, 31.6429133]},
        "validTime": [VALID_TIME_START, ".."],
    },
    {
        "uid":  "urn:os4csapi:system:odas:az-ma-1",
        "name": "ODAS Mic Array Node AZ-MA-1",
        "description": "ODAS 7-microphone circular PDM MEMS array node deployed at Ft. Huachuca, AZ. "
                       "Position 1 (north). Performs real-time sound source localization (SSL), "
                       "sound source tracking (SST), and line-of-bearing (LOB) estimation using "
                       "the ODAS (Open embeddeD Audition System) DSP pipeline. Subsystems include "
                       "tripod platform, mic array, edge processor, comms module, power supply, "
                       "and pan-tilt actuator.",
        "featureType": "sosa:System",
        "geometry": {"type": "Point", "coordinates": [-110.272897, 31.663006]},
        "validTime": [AZMA1_VALID_START, ".."],
    },
]

# Coordinates for each MA node system
_MA_COORDS = {
    2: [-110.272897, 31.662006],  # ~110m south of MA-1
    3: [-110.272897, 31.661006],  # ~110m south of MA-2
}

# Add AZ-MA-2 and AZ-MA-3 (identical hardware, different positions along string)
for _n, _pos in [(2, "center"), (3, "south")]:
    SYSTEMS.append({
        "uid":  f"urn:os4csapi:system:odas:az-ma-{_n}",
        "name": f"ODAS Mic Array Node AZ-MA-{_n}",
        "description": (
            f"ODAS 7-microphone circular PDM MEMS array node deployed at Ft. Huachuca, AZ. "
            f"Position {_n} ({_pos}). Performs real-time sound source localization (SSL), "
            "sound source tracking (SST), and line-of-bearing (LOB) estimation using "
            "the ODAS (Open embeddeD Audition System) DSP pipeline. Subsystems include "
            "tripod platform, mic array, edge processor, comms module, power supply, "
            "and pan-tilt actuator."
        ),
        "featureType": "sosa:System",
        "geometry": {"type": "Point", "coordinates": _MA_COORDS[_n]},
        "validTime": [AZMA1_VALID_START, ".."],
    })

# ═════════════════════════════════════════════════════════════════════════════
#  MA Node Subsystems (created as /systems/{parent_id}/subsystems)
# ═════════════════════════════════════════════════════════════════════════════

AZMA1_COORD = [-110.272897, 31.663006]  # All subsystems share the same point

AZMA1_SUBSYSTEMS = [
    {
        "uid": "urn:os4csapi:platform:az-ma-1:tripod",
        "featureType": "sosa:Platform",
        "name": "AZ-MA-1 Tripod Platform",
        "description": "Portable aluminum survey-grade tripod platform for AZ-MA-1. "
                       "Provides stable, leveled mounting at 1.5m height for the microphone array "
                       "and associated electronics. Weather-resistant, rated for field deployment.",
    },
    {
        "uid": "urn:os4csapi:system:odas:az-ma-1:micarray",
        "featureType": "sosa:Sensor",
        "name": "AZ-MA-1 MICARRAY",
        "description": "7-microphone circular PDM MEMS array for AZ-MA-1. 38mm diameter phased "
                       "array using XMOS xCORE-200 multicore controller. Captures omnidirectional "
                       "audio on all 7 channels simultaneously at 48 kHz / 24-bit. Spatial geometry "
                       "enables beamforming and cross-correlation-based DOA estimation.",
    },
    {
        "uid": "urn:os4csapi:system:odas:az-ma-1:edge",
        "featureType": "sosa:Platform",
        "name": "AZ-MA-1 EDGE",
        "description": "Edge compute module for AZ-MA-1. Runs the ODAS DSP pipeline "
                       "(SSL -> SST -> LOB) on a low-power ARM/x86 SBC. Processes 7-channel "
                       "48 kHz audio in real-time and publishes results via JSON socket output.",
    },
    {
        "uid": "urn:os4csapi:system:odas:az-ma-1:comms",
        "featureType": "sosa:Platform",
        "name": "AZ-MA-1 COMMS",
        "description": "Communications module for AZ-MA-1. Provides mesh-network connectivity "
                       "(Wi-Fi / Ethernet) between the edge processor and the central fusion node "
                       "(AZ-MA-NET). Supports JSON socket output from ODAS for SST/SSL data relay.",
    },
    {
        "uid": "urn:os4csapi:system:odas:az-ma-1:power",
        "featureType": "sosa:Platform",
        "name": "AZ-MA-1 POWER",
        "description": "Power supply module for AZ-MA-1. Provides regulated DC power to the "
                       "microphone array, edge processor, comms module, and pan-tilt actuator. "
                       "Supports both battery (LiFePO4) and solar panel input for sustained "
                       "field operation.",
    },
    {
        "uid": "urn:os4csapi:system:odas:az-ma-1:actuator",
        "featureType": "sosa:Actuator",
        "name": "AZ-MA-1 ACTUATOR",
        "description": "Pan-tilt actuator for AZ-MA-1. Motorised two-axis gimbal that slews "
                       "the microphone array to face the strongest tracked sound source. Receives "
                       "bearing commands from the edge processor based on ODAS SST output.",
    },
]

# Individual microphones (MIC1-MIC7)
for i in range(1, 8):
    pos = "center" if i == 7 else f"perimeter"
    AZMA1_SUBSYSTEMS.append({
        "uid": f"urn:os4csapi:system:odas:az-ma-1:mic{i}",
        "featureType": "sosa:Sensor",
        "name": f"AZ-MA-1 MIC{i}",
        "description": f"MEMS PDM omnidirectional microphone element #{i} "
                       f"(position {i} ({pos})) in the AZ-MA-1 7-channel circular array. "
                       "Digital Pulse-Density Modulation output at 48 kHz / 24-bit.",
    })

# ── Clone utility: replicate MA-1 definitions for other nodes ─────────────

def _clone_for_node(obj, n):
    """Deep-clone with az-ma-1/AZ-MA-1/az_ma_1 → az-ma-{n}/AZ-MA-{n}/az_ma_{n}."""
    if isinstance(obj, str):
        return obj.replace("az-ma-1", f"az-ma-{n}").replace("AZ-MA-1", f"AZ-MA-{n}").replace("az_ma_1", f"az_ma_{n}")
    if isinstance(obj, dict):
        return {k: _clone_for_node(v, n) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clone_for_node(item, n) for item in obj]
    return obj

# Subsystem coordinates and definitions for MA-2 and MA-3
AZMA2_COORD = [-110.272897, 31.662006]  # ~110m south of MA-1
AZMA3_COORD = [-110.272897, 31.661006]  # ~110m south of MA-2

AZMA2_SUBSYSTEMS = _clone_for_node(AZMA1_SUBSYSTEMS, 2)
AZMA3_SUBSYSTEMS = _clone_for_node(AZMA1_SUBSYSTEMS, 3)

# Mapping: parent system UID → (coord, subsystem defs)
ALL_MA_SUBSYSTEMS = {
    "urn:os4csapi:system:odas:az-ma-1": (AZMA1_COORD, AZMA1_SUBSYSTEMS),
    "urn:os4csapi:system:odas:az-ma-2": (AZMA2_COORD, AZMA2_SUBSYSTEMS),
    "urn:os4csapi:system:odas:az-ma-3": (AZMA3_COORD, AZMA3_SUBSYSTEMS),
}

# ═════════════════════════════════════════════════════════════════════════════
#  Deployment hierarchy
#    ICO → R&S → SSO → SNET → Field 001 → String Alpha → Nodes 1-3
# ═════════════════════════════════════════════════════════════════════════════

DEPLOYMENT_TREE = {
    "uid":  "urn:os4csapi:deployment:ico:ft-huachuca:001",
    "name": "Intelligence Collection Operation (derived from ICP)",
    "description": "Top-level intelligence collection operation context derived from the "
                   "intelligence collection plan (ICP). (v3.0 Part 1 doctrinal-aligned refactor; "
                   "sensors added in Part 2)",
    "geometry": {"type": "Point", "coordinates": [-110.25324665, 31.63936508]},
    "properties": {},
    "children": [
        {
            "uid":  "urn:os4csapi:deployment:rso:ft-huachuca:001",
            "name": "Reconnaissance and Surveillance Operation",
            "description": "Reconnaissance and surveillance operation under the ICO context. "
                           "Contains SSO and associated subdeployments.",
            "geometry": {"type": "Point", "coordinates": [-110.25324665, 31.63936508]},
            "properties": {},
            "children": [
                {
                    "uid":  "urn:os4csapi:deployment:sso:ft-huachuca:001",
                    "name": "Sensor Surveillance Operation (derived from SSP)",
                    "description": "Sensor Surveillance Operation context for remote sensors "
                                   "(SSP execution context).",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-110.2524769, 31.6380757], [-110.2540164, 31.64065445]]
                    },
                    "properties": {
                        "deployedSystemUIDs": "urn:os4csapi:system:set:ft-huachuca:001"
                    },
                    "children": [
                        {
                            "uid":  "urn:os4csapi:deployment:snet:ft-huachuca:001",
                            "name": "Sensor Network/Net Deployment",
                            "description": "Network-level grouping of sensors along communication paths.",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [
                                    [-110.2525675, 31.6383956],
                                    [-110.2554653, 31.6429133]
                                ]
                            },
                            "properties": {
                                "deployedSystemUIDs": "urn:os4csapi:system:monitoring-site-node:ft-huachuca:001,"
                                                      "urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001"
                            },
                            "children": [
                                {
                                    "uid":  "urn:os4csapi:deployment:field:ft-huachuca:001",
                                    "name": "Sensor Field 001",
                                    "description": "A defined lateral boundary containing sensor capabilities.",
                                    "geometry": None,
                                    "properties": {},
                                    "children": [
                                        {
                                            "uid":  "urn:os4csapi:deployment:string:ft-huachuca:001",
                                            "name": "Sensor String Alpha (line-of-emplacement)",
                                            "description": "Physical line of emplacement for sensors in Field 001.",
                                            "geometry": None,
                                            "properties": {},
                                            "children": [
                                                {
                                                    "uid": "urn:os4csapi:deployment:node:ft-huachuca:alpha:001",
                                                    "name": "Node 1 \u2014 AZ-MA-1",
                                                    "description": "AZ-MA-1 Monitoring Array deployed as Node 1 on "
                                                                   "Sensor String Alpha, Ft Huachuca ODAS",
                                                    "geometry": {
                                                        "type": "Point",
                                                        "coordinates": [-110.272897, 31.663006]
                                                    },
                                                    "properties": {
                                                        "platform@link": {
                                                            "title": "ODAS Mic Array Node AZ-MA-1",
                                                            "uid": "urn:os4csapi:system:odas:az-ma-1",
                                                            "type": "application/geo+json"
                                                        }
                                                    },
                                                    "validTime": [NODE1_VALID_START, ".."],
                                                    "children": []
                                                },
                                                {
                                                    "uid": "urn:os4csapi:deployment:node:ft-huachuca:alpha:002",
                                                    "name": "Node 2 \u2014 AZ-MA-2",
                                                    "description": "AZ-MA-2 Monitoring Array deployed as Node 2 on "
                                                                   "Sensor String Alpha, Ft Huachuca ODAS",
                                                    "geometry": {
                                                        "type": "Point",
                                                        "coordinates": [-110.272897, 31.662006]
                                                    },
                                                    "properties": {
                                                        "platform@link": {
                                                            "title": "ODAS Mic Array Node AZ-MA-2",
                                                            "uid": "urn:os4csapi:system:odas:az-ma-2",
                                                            "type": "application/geo+json"
                                                        }
                                                    },
                                                    "validTime": [NODE2_VALID_START, ".."],
                                                    "children": []
                                                },
                                                {
                                                    "uid": "urn:os4csapi:deployment:node:ft-huachuca:alpha:003",
                                                    "name": "Node 3 \u2014 AZ-MA-3",
                                                    "description": "AZ-MA-3 Monitoring Array deployed as Node 3 on "
                                                                   "Sensor String Alpha, Ft Huachuca ODAS",
                                                    "geometry": {
                                                        "type": "Point",
                                                        "coordinates": [-110.272897, 31.661006]
                                                    },
                                                    "properties": {
                                                        "platform@link": {
                                                            "title": "ODAS Mic Array Node AZ-MA-3",
                                                            "uid": "urn:os4csapi:system:odas:az-ma-3",
                                                            "type": "application/geo+json"
                                                        }
                                                    },
                                                    "validTime": [NODE3_VALID_START, ".."],
                                                    "children": []
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# ═════════════════════════════════════════════════════════════════════════════
#  Datastream schemas  (SENREP on SET-A,  7 streams on AZ-MA-1)
# ═════════════════════════════════════════════════════════════════════════════

# --- Reusable field builders ---

def _time_field(name="timestamp"):
    return {"type": "Time", "name": name,
            "definition": "https://os4csapi.org/def/odas/time/epochSeconds",
            "label": "Epoch seconds",
            "referenceTime": "1970-01-01T00:00:00Z", "uom": {"code": "s"}}

def _count(name, defn, label):
    return {"type": "Count", "name": name, "definition": defn, "label": label}

def _qty(name, defn, label, uom, lo=None, hi=None):
    f = {"type": "Quantity", "name": name, "definition": defn, "label": label, "uom": {"code": uom}}
    if lo is not None and hi is not None:
        f["constraint"] = {"intervals": [[lo, hi]]}
    return f

def _cat(name, defn, label, vals):
    return {"type": "Category", "name": name, "definition": defn, "label": label,
            "constraint": {"values": vals}}

def _text(name, defn, label):
    return {"type": "Text", "name": name, "definition": defn, "label": label}


# ── SENREP ────────────────────────────────────────────────────────────────────

SENREP_DATASTREAM = {
    "system_uid": "urn:os4csapi:system:set:ft-huachuca:001",
    "name": "SENREP (Sensor Report)",
    "description": "Doctrinal SENREP-style sensor report produced by SET.",
    "outputName": "senrep",
    "validTime": [VALID_TIME_START, "now"],
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "name": "senrep",
            "definition": "https://os4csapi.org/def/csapi/senrepRecordOSH",
            "label": "SENREP (Sensor Report)",
            "description": "Doctrinal SENREP-style report fields.",
            "fields": [
                _time_field(),
                _text("title",         "https://os4csapi.org/def/csapi/reportTitle",    "Title"),
                _text("senderId",      "https://os4csapi.org/def/csapi/senderId",       "Sender ID"),
                _count("seqNo",        "https://os4csapi.org/def/csapi/seqNo",          "Sequence number"),
                _text("classification","https://os4csapi.org/def/csapi/classification", "Classification"),
                _text("releasably",    "https://os4csapi.org/def/csapi/releasably",     "Releasability"),
                _text("dor",           "https://os4csapi.org/def/csapi/dateOfReport",   "Date of report"),
                _text("envirOpName",   "https://os4csapi.org/def/csapi/envirOpName",    "Environment/OpName"),
                _text("strNo",         "https://os4csapi.org/def/csapi/strNo",          "Sensor string number"),
                _text("detectTimeZ",   "https://os4csapi.org/def/csapi/detectTimeZ",    "Detection time (Z)"),
                _count("qty",          "https://os4csapi.org/def/csapi/qty",            "Quantity"),
                _cat("tgtTyp",         "https://os4csapi.org/def/csapi/tgtTyp",         "Target type",
                     ["VEHICL","UAS","PERS","UNKN"]),
                _text("subTyp",        "https://os4csapi.org/def/csapi/subTyp",         "Subtype"),
                _qty("spd",            "https://os4csapi.org/def/csapi/spd",            "Speed", "km/h"),
                _cat("dirCardinal",    "https://os4csapi.org/def/csapi/dirCardinal",    "Direction (cardinal)",
                     ["N","NE","E","SE","S","SW","W","NW"]),
                _qty("colLengthM",     "https://os4csapi.org/def/csapi/colLengthM",     "Column length", "m"),
                _qty("etaLat",         "https://os4csapi.org/def/csapi/etaLat",         "ETA lat",  "deg", -90.0, 90.0),
                _qty("etaLon",         "https://os4csapi.org/def/csapi/etaLon",         "ETA lon",  "deg", -180.0, 180.0),
                _text("etaTimeZ",      "https://os4csapi.org/def/csapi/etaTimeZ",       "ETA time (Z)"),
                _text("comments",      "https://os4csapi.org/def/csapi/comments",       "Comments"),
            ]
        }
    },
}

# ── AZ-MA-1 Datastreams ──────────────────────────────────────────────────────

_ODAS = "https://os4csapi.org/def/odas"
_CSAPI = "https://os4csapi.org/def/csapi"

AZMA1_DATASTREAMS = [
    {
        "system_uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1 Classification Probabilities",
        "description": "Class probs.",
        "outputName": "az_ma_1_classification_probabilities",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "obsFormat": "application/om+json",
            "resultSchema": {
                "type": "DataRecord",
                "name": "az_ma_1_classification_probabilities",
                "definition": f"{_ODAS}/class/probabilitiesRecordOSH",
                "label": "Class probabilities",
                "fields": [
                    _time_field(),
                    _count("trackId",      f"{_ODAS}/trackId",        "Track ID"),
                    _qty("p_uas",          f"{_ODAS}/p_uas",          "P(UAS)",       "1", 0.0, 1.0),
                    _qty("p_vehicle",      f"{_ODAS}/p_vehicle",      "P(vehicle)",   "1", 0.0, 1.0),
                    _qty("p_footsteps",    f"{_ODAS}/p_footsteps",    "P(footsteps)", "1", 0.0, 1.0),
                    _qty("p_impulsive",    f"{_ODAS}/p_impulsive",    "P(impulsive)", "1", 0.0, 1.0),
                    _qty("p_unknown",      f"{_ODAS}/p_unknown",      "P(unknown)",   "1", 0.0, 1.0),
                ]
            }
        },
    },
    {
        "system_uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1 Health",
        "description": "Health.",
        "outputName": "az_ma_1_health",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "obsFormat": "application/om+json",
            "resultSchema": {
                "type": "DataRecord",
                "name": "az_ma_1_health",
                "definition": f"{_CSAPI}/health/statusRecordOSH",
                "label": "Health",
                "fields": [
                    _time_field(),
                    _qty("cpuLoad",    f"{_CSAPI}/cpuLoad",     "CPU load",   "1",   0.0, 1.0),
                    _qty("memUsedMB",  f"{_CSAPI}/memUsedMB",   "Mem used",   "MB"),
                    _qty("tempC",      f"{_CSAPI}/tempC",       "Temp",       "Cel"),
                    _qty("latencyMs",  f"{_CSAPI}/latencyMs",   "Latency",    "ms"),
                    _qty("uptimeS",    f"{_CSAPI}/uptimeS",     "Uptime",     "s"),
                ]
            }
        },
    },
    {
        "system_uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1 LOB",
        "description": "LOB derived.",
        "outputName": "az_ma_1_lob",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "obsFormat": "application/om+json",
            "resultSchema": {
                "type": "DataRecord",
                "name": "az_ma_1_lob",
                "definition": f"{_ODAS}/track/lobRecordOSH",
                "label": "LOB",
                "fields": [
                    _time_field(),
                    _count("trackId",       f"{_ODAS}/trackId",        "Track ID"),
                    _qty("bearingTrue",     f"{_ODAS}/bearingTrue",    "Bearing true",    "deg", 0.0, 360.0),
                    _qty("bearingStdDev",   f"{_ODAS}/bearingStdDev",  "Bearing std dev", "deg"),
                    _qty("sensorLat",       f"{_CSAPI}/sensorLat",     "Sensor lat",      "deg", -90.0, 90.0),
                    _qty("sensorLon",       f"{_CSAPI}/sensorLon",     "Sensor lon",      "deg", -180.0, 180.0),
                ]
            }
        },
    },
    {
        "system_uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1 Scene Summary",
        "description": "Scene summary.",
        "outputName": "az_ma_1_scene_summary",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "obsFormat": "application/om+json",
            "resultSchema": {
                "type": "DataRecord",
                "name": "az_ma_1_scene_summary",
                "definition": f"{_CSAPI}/scene/summaryRecordOSH",
                "label": "Scene summary",
                "fields": [
                    _time_field(),
                    _count("odasTimeStamp", f"{_ODAS}/frameIndex",      "ODAS timeStamp/frame index"),
                    _count("trackCount",    f"{_CSAPI}/trackCount",     "Active track count"),
                    _qty("activityLevel",   f"{_CSAPI}/activityLevel",  "Activity level", "1", 0.0, 1.0),
                ]
            }
        },
    },
    {
        "system_uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1 SSL Potential Sources",
        "description": "SSL raw.",
        "outputName": "az_ma_1_ssl_potential_sources",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "obsFormat": "application/om+json",
            "resultSchema": {
                "type": "DataRecord",
                "name": "az_ma_1_ssl_potential_sources",
                "definition": f"{_ODAS}/ssl/potentialSourcesRecordOSH",
                "label": "SSL potential sources",
                "fields": [
                    _time_field(),
                    _count("odasTimeStamp", f"{_ODAS}/frameIndex", "ODAS timeStamp/frame index"),
                    {
                        "type": "DataArray",
                        "name": "src",
                        "definition": f"{_ODAS}/ssl/potentialSourceArray",
                        "label": "Potential sources",
                        "elementCount": {"type": "Count", "name": "elementCount"},
                        "elementType": {
                            "type": "DataRecord",
                            "name": "element",
                            "definition": f"{_ODAS}/ssl/potentialSource",
                            "label": "SSL potential source",
                            "fields": [
                                _qty("x", f"{_ODAS}/directionCosineX", "Direction cosine X", "1", -1.0, 1.0),
                                _qty("y", f"{_ODAS}/directionCosineY", "Direction cosine Y", "1", -1.0, 1.0),
                                _qty("z", f"{_ODAS}/directionCosineZ", "Direction cosine Z", "1", -1.0, 1.0),
                                _qty("E", f"{_ODAS}/relativeEnergy",   "Relative energy (ODAS)", "1"),
                            ]
                        }
                    }
                ]
            }
        },
    },
    {
        "system_uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1 SST Tracked Sources",
        "description": "SST raw.",
        "outputName": "az_ma_1_sst_tracked_sources",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "obsFormat": "application/om+json",
            "resultSchema": {
                "type": "DataRecord",
                "name": "az_ma_1_sst_tracked_sources",
                "definition": f"{_ODAS}/sst/trackedSourcesRecordOSH",
                "label": "SST tracked sources",
                "fields": [
                    _time_field(),
                    _count("odasTimeStamp", f"{_ODAS}/frameIndex", "ODAS timeStamp/frame index"),
                    {
                        "type": "DataArray",
                        "name": "src",
                        "definition": f"{_ODAS}/sst/trackedSourceArray",
                        "label": "Tracked sources",
                        "elementCount": {"type": "Count", "name": "elementCount"},
                        "elementType": {
                            "type": "DataRecord",
                            "name": "element",
                            "definition": f"{_ODAS}/sst/trackedSource",
                            "label": "SST tracked source",
                            "fields": [
                                _count("id",  f"{_ODAS}/trackId",    "Track ID"),
                                {"type": "Text", "name": "tag",
                                 "definition": f"{_ODAS}/trackTag", "label": "Track tag",
                                 "constraint": {"values": ["dynamic", "static", ""]}},
                                _qty("x",        f"{_ODAS}/directionCosineX", "Direction cosine X", "1", -1.0, 1.0),
                                _qty("y",        f"{_ODAS}/directionCosineY", "Direction cosine Y", "1", -1.0, 1.0),
                                _qty("z",        f"{_ODAS}/directionCosineZ", "Direction cosine Z", "1", -1.0, 1.0),
                                _qty("activity", f"{_ODAS}/trackActivity",    "Activity",           "1"),
                            ]
                        }
                    }
                ]
            }
        },
    },
    {
        "system_uid": "urn:os4csapi:system:odas:az-ma-1",
        "name": "AZ-MA-1 Track Updates",
        "description": "Per-track updates.",
        "outputName": "az_ma_1_track_updates",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "obsFormat": "application/om+json",
            "resultSchema": {
                "type": "DataRecord",
                "name": "az_ma_1_track_updates",
                "definition": f"{_ODAS}/track/updateRecordOSH",
                "label": "Track update",
                "fields": [
                    _time_field(),
                    _count("odasTimeStamp", f"{_ODAS}/frameIndex",      "ODAS timeStamp/frame index"),
                    _count("id",            f"{_ODAS}/trackId",         "Track ID"),
                    {"type": "Text", "name": "tag",
                     "definition": f"{_ODAS}/trackTag", "label": "Track tag",
                     "constraint": {"values": ["dynamic", "static", ""]}},
                    _qty("x",              f"{_ODAS}/directionCosineX", "Direction cosine X", "1", -1.0, 1.0),
                    _qty("y",              f"{_ODAS}/directionCosineY", "Direction cosine Y", "1", -1.0, 1.0),
                    _qty("z",              f"{_ODAS}/directionCosineZ", "Direction cosine Z", "1", -1.0, 1.0),
                    _qty("activity",       f"{_ODAS}/trackActivity",    "Activity",           "1"),
                    _qty("bearingTrue",    f"{_ODAS}/bearingTrue",      "Bearing true",       "deg", 0.0, 360.0),
                    _qty("elevation",      f"{_ODAS}/elevation",        "Elevation",          "deg", -90.0, 90.0),
                    _qty("bearingStdDev",  f"{_ODAS}/bearingStdDev",    "Bearing std dev",    "deg"),
                    _cat("classLabel",     f"{_ODAS}/classLabel",       "Class label",
                         ["uas", "vehicle", "footsteps", "impulsive", "unknown"]),
                    _qty("classConfidence",f"{_ODAS}/classConfidence",  "Class confidence",   "1", 0.0, 1.0),
                ]
            }
        },
    },
]

AZMA2_DATASTREAMS = _clone_for_node(AZMA1_DATASTREAMS, 2)
AZMA3_DATASTREAMS = _clone_for_node(AZMA1_DATASTREAMS, 3)

ALL_DATASTREAMS = [SENREP_DATASTREAM] + AZMA1_DATASTREAMS + AZMA2_DATASTREAMS + AZMA3_DATASTREAMS

# ═════════════════════════════════════════════════════════════════════════════
#  Control stream schemas (on MA node ACTUATOR subsystems)
# ═════════════════════════════════════════════════════════════════════════════

AZMA1_CONTROL_STREAMS = [
    {
        "subsystem_uid": "urn:os4csapi:system:odas:az-ma-1:actuator",
        "name": "AZ-MA-1 ODAS Control ControlStream",
        "inputName": "odasControl",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "commandFormat": "application/json",
            "parametersSchema": {
                "type": "DataRecord",
                "name": "odasControl",
                "definition": f"{_CSAPI}/commands/odasControlParams",
                "label": "ODAS Control Params",
                "fields": [
                    _cat("module",    f"{_CSAPI}/module",    "Module",
                         ["sne", "ssl", "sst", "sss", "classify", "general"]),
                    _text("parameter", f"{_CSAPI}/parameter", "Parameter path"),
                    _text("value",     f"{_CSAPI}/value",     "Value string"),
                    _cat("applyMode",  f"{_CSAPI}/applyMode", "Apply",
                         ["immediate", "nextFrame", "nextRestart"]),
                ]
            }
        },
    },
    {
        "subsystem_uid": "urn:os4csapi:system:odas:az-ma-1:actuator",
        "name": "AZ-MA-1 Request Snapshot ControlStream",
        "inputName": "snapshot",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "commandFormat": "application/json",
            "parametersSchema": {
                "type": "DataRecord",
                "name": "snapshot",
                "definition": f"{_CSAPI}/commands/requestSnapshotParams",
                "label": "Snapshot Params",
                "fields": [
                    _count("trackId",    f"{_ODAS}/trackId",       "Track ID"),
                    _qty("durationMs",   f"{_CSAPI}/durationMs",   "Duration", "ms", 10.0, 60000.0),
                    _cat("format",       f"{_CSAPI}/format",       "Format",
                         ["wav", "flac", "json"]),
                ]
            }
        },
    },
    {
        "subsystem_uid": "urn:os4csapi:system:odas:az-ma-1:actuator",
        "name": "AZ-MA-1 Start Stop ControlStream",
        "inputName": "startStop",
        "validTime": [AZMA1_VALID_START, "now"],
        "schema": {
            "commandFormat": "application/json",
            "parametersSchema": {
                "type": "DataRecord",
                "name": "startStop",
                "definition": f"{_CSAPI}/commands/startStopParams",
                "label": "Start/Stop Params",
                "fields": [
                    _cat("action",  f"{_CSAPI}/action",  "Action",
                         ["start", "stop", "restart"]),
                    _text("modules", f"{_CSAPI}/modules", "Modules CSV"),
                ]
            }
        },
    },
]

AZMA2_CONTROL_STREAMS = _clone_for_node(AZMA1_CONTROL_STREAMS, 2)
AZMA3_CONTROL_STREAMS = _clone_for_node(AZMA1_CONTROL_STREAMS, 3)

ALL_CONTROL_STREAMS = AZMA1_CONTROL_STREAMS + AZMA2_CONTROL_STREAMS + AZMA3_CONTROL_STREAMS


# ═════════════════════════════════════════════════════════════════════════════
#  Bootstrap Engine
# ═════════════════════════════════════════════════════════════════════════════

import socket
import ssl as _ssl

# DNS monkey-patch: resolve DuckDNS hostname to Oracle Cloud IP
_real_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "os4csapi-osh.duckdns.org":
        return _real_getaddrinfo(ORACLE_IP, port, *args, **kwargs)
    return _real_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _patched_getaddrinfo

# Self-signed cert context
_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE


class Bootstrap:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        cred = base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()
        self.auth_header = f"Basic {cred}"
        self.stats = {"created": 0, "deleted": 0, "skipped": 0, "errors": 0, "patched": 0}
        # Cache: uid → server id
        self._uid_cache: dict[str, str] = {}

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _request(self, method: str, url: str, body: dict | None = None,
                 accept: str = "application/json",
                 content_type: str | None = None) -> dict | str | None:
        headers = {
            "Authorization": self.auth_header,
            "Accept": accept,
        }
        data = None
        if body is not None:
            ct = content_type or ("application/geo+json" if "geometry" in body else "application/json")
            headers["Content-Type"] = ct
            data = json.dumps(body).encode()

        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30, context=_ssl_ctx) as resp:
                raw = resp.read().decode()
                location = resp.headers.get("Location", "")
                if location:
                    new_id = location.rstrip("/").split("/")[-1]
                    if not raw.strip() or resp.status in (201, 204):
                        return {"id": new_id, "_location": location}
                    try:
                        result = json.loads(raw)
                        if isinstance(result, dict) and "id" not in result:
                            result["id"] = new_id
                        return result
                    except json.JSONDecodeError:
                        return {"id": new_id, "_location": location}
                if resp.status == 204 or not raw.strip():
                    return None
                return json.loads(raw)
        except HTTPError as e:
            if e.code == 404:
                return None
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code} {method} {url}: {body_text[:300]}")

    def _get(self, path: str, accept: str = "application/json"):
        return self._request("GET", f"{BASE_URL}/{path}", accept=accept)

    def _post(self, path: str, body: dict, content_type: str | None = None):
        return self._request("POST", f"{BASE_URL}/{path}", body=body, content_type=content_type)

    def _put(self, path: str, body: dict, content_type: str | None = None):
        return self._request("PUT", f"{BASE_URL}/{path}", body=body, content_type=content_type)

    def _delete(self, path: str):
        return self._request("DELETE", f"{BASE_URL}/{path}")

    # ── Lookup helpers ────────────────────────────────────────────────────────

    def find_by_uid(self, collection: str, uid: str) -> str | None:
        """Return the server ID for a resource with the given UID, or None."""
        cache_key = f"{collection}:{uid}"
        if cache_key in self._uid_cache:
            return self._uid_cache[cache_key]
        result = self._get(f"{collection}?uid={uid}")
        if result and "items" in result:
            for item in result["items"]:
                props = item.get("properties", item)
                if props.get("uid") == uid:
                    sid = item.get("id", props.get("id"))
                    self._uid_cache[cache_key] = sid
                    return sid
        return None

    # ── Phase 0: Clean ────────────────────────────────────────────────────────

    def clean(self):
        """Delete all known resources by UID lookup."""
        print("\n" + "=" * 70)
        print("  PHASE 0: CLEAN — Deleting all known resources")
        print("=" * 70)

        # 1. Delete datastreams on all systems
        for sys_def in SYSTEMS:
            sid = self.find_by_uid("systems", sys_def["uid"])
            if sid:
                ds_list = self._get(f"systems/{sid}/datastreams")
                if ds_list and "items" in ds_list:
                    for ds in ds_list["items"]:
                        ds_id = ds.get("id")
                        if ds_id:
                            print(f"  DELETE datastream {ds.get('name', '?')} ({ds_id})")
                            if not self.dry_run:
                                try:
                                    self._delete(f"datastreams/{ds_id}")
                                    self.stats["deleted"] += 1
                                except RuntimeError as e:
                                    print(f"    WARNING: {e}")
                                    self.stats["errors"] += 1
                            else:
                                self.stats["deleted"] += 1

        # 2. Delete control streams on all ACTUATOR subsystems
        for _n in range(1, 4):
            actuator_uid = f"urn:os4csapi:system:odas:az-ma-{_n}:actuator"
            actuator_id = self.find_by_uid("systems", actuator_uid)
            if actuator_id:
                cs_list = self._get(f"systems/{actuator_id}/controlstreams")
                if cs_list and "items" in cs_list:
                    for cs in cs_list["items"]:
                        cs_id = cs.get("id")
                        if cs_id:
                            print(f"  DELETE controlstream {cs.get('name', '?')} ({cs_id})")
                            if not self.dry_run:
                                try:
                                    self._delete(f"controlstreams/{cs_id}")
                                    self.stats["deleted"] += 1
                                except RuntimeError as e:
                                    print(f"    WARNING: {e}")
                                    self.stats["errors"] += 1
                            else:
                                self.stats["deleted"] += 1

        # 3. Delete deployments bottom-up
        dep_uids = self._collect_deployment_uids(DEPLOYMENT_TREE)
        dep_uids.reverse()
        for uid in dep_uids:
            did = self.find_by_uid("deployments", uid)
            if did:
                short = uid.split(":")[-2] + ":" + uid.split(":")[-1]
                print(f"  DELETE deployment {short} ({did})")
                if not self.dry_run:
                    try:
                        self._delete(f"deployments/{did}")
                        self.stats["deleted"] += 1
                    except RuntimeError as e:
                        print(f"    WARNING: {e}")
                        self.stats["errors"] += 1
                else:
                    self.stats["deleted"] += 1
            else:
                print(f"  SKIP deployment {uid} (not found)")

        # 4. Delete subsystems on all MA nodes
        for parent_uid, (_, sub_defs) in ALL_MA_SUBSYSTEMS.items():
            parent_id = self.find_by_uid("systems", parent_uid)
            if parent_id:
                for sub_def in reversed(sub_defs):
                    sub_id = self.find_by_uid("systems", sub_def["uid"])
                    if sub_id:
                        print(f"  DELETE subsystem {sub_def['name']} ({sub_id})")
                        if not self.dry_run:
                            try:
                                self._delete(f"systems/{sub_id}")
                                self.stats["deleted"] += 1
                            except RuntimeError as e:
                                print(f"    WARNING: {e}")
                                self.stats["errors"] += 1
                        else:
                            self.stats["deleted"] += 1

        # 5. Delete top-level systems (reverse order so children first)
        for sys_def in reversed(SYSTEMS):
            uid = sys_def["uid"]
            sid = self.find_by_uid("systems", uid)
            if sid:
                print(f"  DELETE system {sys_def['name']} ({sid})")
                if not self.dry_run:
                    try:
                        self._delete(f"systems/{sid}")
                        self.stats["deleted"] += 1
                    except RuntimeError as e:
                        print(f"    WARNING: {e}")
                        self.stats["errors"] += 1
                else:
                    self.stats["deleted"] += 1
            else:
                print(f"  SKIP system {uid} (not found)")

        if not self.dry_run:
            time.sleep(1)

    def _collect_deployment_uids(self, node: dict) -> list[str]:
        uids = [node["uid"]]
        for child in node.get("children", []):
            uids.extend(self._collect_deployment_uids(child))
        return uids

    # ── Phase 1: Create systems ───────────────────────────────────────────────

    def create_systems(self):
        print("\n" + "=" * 70)
        print("  PHASE 1: Create Top-Level Systems")
        print("=" * 70)

        for sys_def in SYSTEMS:
            uid = sys_def["uid"]
            existing = self.find_by_uid("systems", uid)
            if existing:
                print(f"  SKIP {sys_def['name']} — already exists ({existing})")
                self.stats["skipped"] += 1
                continue

            body = {
                "type": "Feature",
                "properties": {
                    "uid": uid,
                    "featureType": sys_def.get("featureType", "sosa:Platform"),
                    "name": sys_def["name"],
                    "description": sys_def["description"],
                    "validTime": sys_def.get("validTime", [VALID_TIME_START, ".."]),
                },
                "geometry": sys_def["geometry"],
            }

            print(f"  CREATE system: {sys_def['name']}")
            if not self.dry_run:
                try:
                    result = self._post("systems", body)
                    new_id = result.get("id") if result else "?"
                    print(f"    → id={new_id}")
                    self._uid_cache[f"systems:{uid}"] = new_id
                    self.stats["created"] += 1
                except RuntimeError as e:
                    print(f"    ERROR: {e}")
                    self.stats["errors"] += 1
            else:
                print(f"    → (dry run)")
                self.stats["created"] += 1

    # ── Phase 2: Create MA node subsystems ────────────────────────────────────

    def create_subsystems(self):
        print("\n" + "=" * 70)
        print("  PHASE 2: Create MA Node Subsystems (3 nodes × 13 each)")
        print("=" * 70)

        for parent_uid, (coord, sub_defs) in ALL_MA_SUBSYSTEMS.items():
            parent_label = parent_uid.split(":")[-1].upper()
            parent_id = self.find_by_uid("systems", parent_uid)
            if not parent_id:
                if self.dry_run:
                    parent_id = f"DRY-{parent_label}"
                else:
                    print(f"  ERROR: {parent_uid} not found — cannot create subsystems")
                    self.stats["errors"] += 1
                    continue

            for sub_def in sub_defs:
                uid = sub_def["uid"]
                existing = self.find_by_uid("systems", uid)
                if existing:
                    print(f"  SKIP {sub_def['name']} — already exists ({existing})")
                    self.stats["skipped"] += 1
                    continue

                body = {
                    "type": "Feature",
                    "properties": {
                        "uid": uid,
                        "featureType": sub_def["featureType"],
                        "name": sub_def["name"],
                        "description": sub_def["description"],
                        "validTime": [AZMA1_VALID_START, ".."],
                    },
                    "geometry": {"type": "Point", "coordinates": coord},
                }

                print(f"  CREATE subsystem: {sub_def['name']}")
                if not self.dry_run:
                    try:
                        result = self._post(f"systems/{parent_id}/subsystems", body)
                        new_id = result.get("id") if result else "?"
                        print(f"    → id={new_id}")
                        self._uid_cache[f"systems:{uid}"] = new_id
                        self.stats["created"] += 1
                    except RuntimeError as e:
                        print(f"    ERROR: {e}")
                        self.stats["errors"] += 1
                else:
                    print(f"    → (dry run)")
                    self.stats["created"] += 1

    # ── Phase 3: Create deployment tree ───────────────────────────────────────

    def create_deployments(self):
        print("\n" + "=" * 70)
        print("  PHASE 3: Create Deployment Hierarchy (nested POST)")
        print("=" * 70)

        self._create_deployment_node(DEPLOYMENT_TREE, parent_path=None, depth=0)

    def _create_deployment_node(self, node: dict, parent_path: str | None, depth: int):
        uid = node["uid"]
        indent = "  " + "  " * depth
        short = uid.split(":")[-2] + ":" + uid.split(":")[-1]

        existing = self.find_by_uid("deployments", uid)
        if existing:
            print(f"{indent}SKIP {node['name']} — already exists ({existing})")
            self.stats["skipped"] += 1
            child_path = f"deployments/{existing}/subdeployments"
            for child in node.get("children", []):
                self._create_deployment_node(child, child_path, depth + 1)
            return

        body = {
            "type": "Feature",
            "properties": {
                "uid": uid,
                "featureType": "sosa:Deployment",
                "name": node["name"],
                "description": node["description"],
                "validTime": node.get("validTime", [VALID_TIME_START, ".."]),
            },
            "geometry": node["geometry"],
        }
        # Add extra properties (deployedSystemUIDs, platform@link, etc.)
        for k, v in node.get("properties", {}).items():
            if k == "platform@link":
                # For platform@link we need to resolve the href at runtime
                azma1_id = self.find_by_uid("systems", v["uid"]) if not self.dry_run else "DRY"
                body["properties"]["platform@link"] = {
                    "href": f"/sensorhub/api/systems/{azma1_id}",
                    "title": v["title"],
                    "uid": v["uid"],
                    "type": v["type"],
                }
            else:
                body["properties"][k] = v

        post_path = parent_path or "deployments"

        print(f"{indent}CREATE deployment: {node['name']} ({short})")
        print(f"{indent}  POST → {post_path}")

        new_id = None
        if not self.dry_run:
            try:
                result = self._post(post_path, body)
                new_id = result.get("id") if result else "?"
                print(f"{indent}  → id={new_id}")
                self._uid_cache[f"deployments:{uid}"] = new_id
                self.stats["created"] += 1
            except RuntimeError as e:
                print(f"{indent}  ERROR: {e}")
                self.stats["errors"] += 1
                return
        else:
            new_id = f"DRY-{short}"
            print(f"{indent}  → (dry run)")
            self.stats["created"] += 1

        if new_id and node.get("children"):
            child_path = f"deployments/{new_id}/subdeployments" if not self.dry_run else f"{post_path}/DRY/subdeployments"
            for child in node["children"]:
                self._create_deployment_node(child, child_path, depth + 1)

    # ── Phase 4: Create datastreams ───────────────────────────────────────────

    def create_datastreams(self):
        print("\n" + "=" * 70)
        print(f"  PHASE 4: Create Datastreams ({len(ALL_DATASTREAMS)} total)")
        print("=" * 70)

        for ds_def in ALL_DATASTREAMS:
            sys_uid = ds_def["system_uid"]
            sys_id = self.find_by_uid("systems", sys_uid)
            if not sys_id:
                if self.dry_run:
                    sys_id = "DRY"
                else:
                    print(f"  ERROR: System {sys_uid} not found — cannot create {ds_def['name']}")
                    self.stats["errors"] += 1
                    continue

            # Check if already exists
            if not self.dry_run:
                existing_ds = self._get(f"systems/{sys_id}/datastreams")
                if existing_ds and "items" in existing_ds:
                    for ds in existing_ds["items"]:
                        if ds.get("outputName") == ds_def["outputName"] or ds.get("name") == ds_def["name"]:
                            print(f"  SKIP {ds_def['name']} — already exists ({ds.get('id')})")
                            self.stats["skipped"] += 1
                            break
                    else:
                        pass  # not found, proceed to create
                    if any(ds.get("outputName") == ds_def["outputName"] or ds.get("name") == ds_def["name"]
                           for ds in existing_ds["items"]):
                        continue

            body = {
                "name": ds_def["name"],
                "description": ds_def["description"],
                "outputName": ds_def["outputName"],
                "validTime": ds_def["validTime"],
                "schema": ds_def["schema"],
            }

            print(f"  CREATE datastream: {ds_def['name']} on system {sys_id}")
            if not self.dry_run:
                try:
                    result = self._post(f"systems/{sys_id}/datastreams", body)
                    new_id = result.get("id") if result else "?"
                    print(f"    → id={new_id}")
                    self.stats["created"] += 1
                except RuntimeError as e:
                    print(f"    ERROR: {e}")
                    self.stats["errors"] += 1
            else:
                print(f"    → (dry run)")
                self.stats["created"] += 1

    # ── Phase 5: Create control streams ───────────────────────────────────────

    def create_control_streams(self):
        print("\n" + "=" * 70)
        print(f"  PHASE 5: Create Control Streams ({len(ALL_CONTROL_STREAMS)} total)")
        print("=" * 70)

        for cs_def in ALL_CONTROL_STREAMS:
            sub_uid = cs_def["subsystem_uid"]
            sub_id = self.find_by_uid("systems", sub_uid)
            if not sub_id:
                if self.dry_run:
                    sub_id = "DRY"
                else:
                    print(f"  ERROR: Subsystem {sub_uid} not found — cannot create {cs_def['name']}")
                    self.stats["errors"] += 1
                    continue

            # Check if already exists
            if not self.dry_run:
                existing_cs = self._get(f"systems/{sub_id}/controlstreams")
                if existing_cs and "items" in existing_cs:
                    if any(cs.get("inputName") == cs_def["inputName"] or cs.get("name") == cs_def["name"]
                           for cs in existing_cs["items"]):
                        print(f"  SKIP {cs_def['name']} — already exists")
                        self.stats["skipped"] += 1
                        continue

            body = {
                "name": cs_def["name"],
                "inputName": cs_def["inputName"],
                "validTime": cs_def["validTime"],
                "schema": cs_def["schema"],
            }

            print(f"  CREATE controlstream: {cs_def['name']} on subsystem {sub_id}")
            if not self.dry_run:
                try:
                    result = self._post(f"systems/{sub_id}/controlstreams", body)
                    new_id = result.get("id") if result else "?"
                    print(f"    → id={new_id}")
                    self.stats["created"] += 1
                except RuntimeError as e:
                    print(f"    ERROR: {e}")
                    self.stats["errors"] += 1
            else:
                print(f"    → (dry run)")
                self.stats["created"] += 1

    # ── Fix UIDs (targeted patch) ─────────────────────────────────────────────

    def fix_snet_uids(self):
        """Fix deployedSystemUIDs on the SNET deployment if wrong."""
        print("\n" + "=" * 70)
        print("  FIX: Verify deployedSystemUIDs on SNET")
        print("=" * 70)

        snet_uid = "urn:os4csapi:deployment:snet:ft-huachuca:001"
        snet_id = self.find_by_uid("deployments", snet_uid)
        if not snet_id:
            print("  SNET not found — nothing to fix")
            return

        current = self._get(f"deployments/{snet_id}", accept="application/geo+json")
        if not current:
            print("  ERROR: Could not read SNET")
            self.stats["errors"] += 1
            return

        current_uids = current.get("properties", {}).get("deployedSystemUIDs", "")
        correct_uids = ("urn:os4csapi:system:monitoring-site-node:ft-huachuca:001,"
                        "urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001")

        if current_uids == correct_uids:
            print(f"  deployedSystemUIDs already correct — skip")
            self.stats["skipped"] += 1
            return

        print(f"  CURRENT: {current_uids}")
        print(f"  CORRECT: {correct_uids}")

        body = {
            "type": "Feature",
            "properties": {
                "uid": current["properties"]["uid"],
                "featureType": current["properties"].get("featureType", "sosa:Deployment"),
                "name": current["properties"]["name"],
                "description": current["properties"]["description"],
                "validTime": current["properties"]["validTime"],
                "deployedSystemUIDs": correct_uids,
            },
            "geometry": current["geometry"],
        }

        if not self.dry_run:
            try:
                self._put(f"deployments/{snet_id}", body)
                print(f"  → PATCHED {snet_id}")
                self.stats["patched"] += 1
            except RuntimeError as e:
                print(f"  ERROR: {e}")
                self.stats["errors"] += 1
        else:
            print(f"  → (dry run) would patch {snet_id}")
            self.stats["patched"] += 1

    # ── Verify ────────────────────────────────────────────────────────────────

    def verify(self):
        """Quick verification of created resources."""
        print("\n" + "=" * 70)
        print("  VERIFY: Checking server state")
        print("=" * 70)

        if self.dry_run:
            print("  (skipped in dry-run mode)")
            return True

        all_ok = True

        # Systems
        for sys_def in SYSTEMS:
            sid = self.find_by_uid("systems", sys_def["uid"])
            status = f"OK ({sid})" if sid else "MISSING!"
            if not sid:
                all_ok = False
            print(f"  System {sys_def['name']}: {status}")

        # Subsystems (all MA nodes)
        for parent_uid, (_, sub_defs) in ALL_MA_SUBSYSTEMS.items():
            for sub_def in sub_defs:
                sid = self.find_by_uid("systems", sub_def["uid"])
                status = f"OK ({sid})" if sid else "MISSING!"
                if not sid:
                    all_ok = False
                print(f"  Subsystem {sub_def['name']}: {status}")

        # Deployment tree
        dep_uids = self._collect_deployment_uids(DEPLOYMENT_TREE)
        for uid in dep_uids:
            did = self.find_by_uid("deployments", uid)
            short = uid.split(":")[-2] + ":" + uid.split(":")[-1]
            status = f"OK ({did})" if did else "MISSING!"
            if not did:
                all_ok = False
            print(f"  Deployment {short}: {status}")

        # Datastreams
        for ds_def in ALL_DATASTREAMS:
            sys_id = self.find_by_uid("systems", ds_def["system_uid"])
            if sys_id:
                ds_list = self._get(f"systems/{sys_id}/datastreams")
                found = False
                if ds_list and "items" in ds_list:
                    for ds in ds_list["items"]:
                        if ds.get("outputName") == ds_def["outputName"]:
                            print(f"  Datastream {ds_def['name']}: OK ({ds.get('id')})")
                            found = True
                            break
                if not found:
                    print(f"  Datastream {ds_def['name']}: MISSING!")
                    all_ok = False

        # Control streams (all MA nodes)
        for _n in range(1, 4):
            act_uid = f"urn:os4csapi:system:odas:az-ma-{_n}:actuator"
            act_id = self.find_by_uid("systems", act_uid)
            if act_id:
                cs_list = self._get(f"systems/{act_id}/controlstreams")
                cs_count = len(cs_list.get("items", [])) if cs_list else 0
                status = f"OK ({cs_count}/3)" if cs_count >= 3 else f"INCOMPLETE ({cs_count}/3)"
                if cs_count < 3:
                    all_ok = False
                print(f"  Control streams on AZ-MA-{_n} ACTUATOR: {status}")
            else:
                print(f"  Control streams on AZ-MA-{_n} ACTUATOR: MISSING (no actuator)")
                all_ok = False

        # Platform@link on all deployment nodes
        for _n in range(1, 4):
            node_uid = f"urn:os4csapi:deployment:node:ft-huachuca:alpha:00{_n}"
            node_id = self.find_by_uid("deployments", node_uid)
            if node_id:
                node_data = self._get(f"deployments/{node_id}", accept="application/geo+json")
                if node_data:
                    plink = node_data.get("properties", {}).get("platform@link")
                    if plink and "systems" in plink.get("href", ""):
                        print(f"  Node {_n} platform@link: OK ({plink['href']})")
                    else:
                        print(f"  Node {_n} platform@link: MISSING!")
                        all_ok = False

        # SNET UIDs
        snet_id = self.find_by_uid("deployments", "urn:os4csapi:deployment:snet:ft-huachuca:001")
        if snet_id:
            snet = self._get(f"deployments/{snet_id}", accept="application/geo+json")
            if snet:
                uids_val = snet.get("properties", {}).get("deployedSystemUIDs", "")
                if "monitoring-site-node" in uids_val and "relay:vhf-repeater" in uids_val:
                    print(f"  SNET deployedSystemUIDs: OK")
                else:
                    print(f"  SNET deployedSystemUIDs: WRONG — {uids_val}")
                    all_ok = False

        return all_ok

    # ── Run ───────────────────────────────────────────────────────────────────

    def run_full(self, clean: bool = False, clean_only: bool = False, fix_uids: bool = False):
        mode = "DRY RUN" if self.dry_run else "LIVE"
        print(f"\n{'#' * 70}")
        print(f"  bootstrap_v4.py — OSH Server Bootstrap [{mode}]")
        print(f"  Server: {BASE_URL}")
        print(f"  Time:   {datetime.now(timezone.utc).isoformat()}")
        print(f"{'#' * 70}")

        if fix_uids:
            self.fix_snet_uids()
        elif clean_only:
            self.clean()
        else:
            if clean:
                self.clean()
            self.create_systems()
            self.create_subsystems()
            self.create_deployments()
            self.create_datastreams()
            self.create_control_streams()
            self.fix_snet_uids()
            self.verify()

        # Summary
        print(f"\n{'─' * 70}")
        print(f"  Summary: created={self.stats['created']}  deleted={self.stats['deleted']}  "
              f"patched={self.stats['patched']}  skipped={self.stats['skipped']}  "
              f"errors={self.stats['errors']}")
        if self.dry_run:
            print(f"  (DRY RUN — no changes were made)")
        print(f"{'─' * 70}\n")

        return self.stats["errors"] == 0


# ═════════════════════════════════════════════════════════════════════════════
#  CLI
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Bootstrap OS4CSAPI OSH server v4")
    parser.add_argument("--clean", action="store_true", help="Delete all then recreate")
    parser.add_argument("--clean-only", action="store_true", help="Delete all, don't recreate")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    parser.add_argument("--fix-uids", action="store_true", help="Only fix SNET deployedSystemUIDs")
    args = parser.parse_args()

    bs = Bootstrap(dry_run=args.dry_run)
    ok = bs.run_full(
        clean=args.clean,
        clean_only=args.clean_only,
        fix_uids=args.fix_uids,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
