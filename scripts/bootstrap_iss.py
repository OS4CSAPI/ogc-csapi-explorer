#!/usr/bin/env python3
"""
bootstrap_iss.py — Register the ISS dual-product publisher on the OS4CSAPI server.

Creates EIGHT resources (skip-if-exists):
  Procedures:
    1. urn:os4csapi:procedure:sgp4-propagation:v1
    2. urn:os4csapi:procedure:orbit-track-generation:v1

  Systems  (geo+json stub POST → SensorML PUT for rich metadata):
    3. urn:os4csapi:system:iss-position-publisher:v1     (typeOf → sgp4 procedure)
    4. urn:os4csapi:system:iss-orbittrack-publisher:v1    (typeOf → orbit-track procedure)

  DataStreams:
    5. issPosition      (11-field SWE DataRecord) under position system
    6. issOrbitTrack     (7-field SWE DataRecord)  under orbit-track system

  Deployment tree (5 nodes):
    7. urn:os4csapi:deployment:orbital-tracking-demo:v1
       └─ urn:os4csapi:deployment:leo-objects:v1
          └─ urn:os4csapi:deployment:iss-tracking-role:v1
             ├─ urn:os4csapi:deployment:iss-position-feed:v1     (platform@link → pos system)
             └─ urn:os4csapi:deployment:iss-orbittrack-feed:v1   (platform@link → track system)

Usage:
    python bootstrap_iss.py              # create everything (skip if exists)
    python bootstrap_iss.py --clean      # delete then recreate
    python bootstrap_iss.py --clean-only # delete only (teardown)
    python bootstrap_iss.py --dry-run    # print what would happen

Requires: Python 3.10+, no external dependencies (stdlib only).
"""

import argparse
import base64
import json
import socket
import ssl as _ssl
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ═══════════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════════

BASE_URL  = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH_USER = "os4csapi"
AUTH_PASS = "ogc134mm"
ORACLE_IP = "129.80.248.53"

# ── UIDs ──────────────────────────────────────────────────────────────────
PROC_SGP4_UID   = "urn:os4csapi:procedure:sgp4-propagation:v1"
PROC_ORBIT_UID  = "urn:os4csapi:procedure:orbit-track-generation:v1"
SYS_POS_UID     = "urn:os4csapi:system:iss-position-publisher:v1"
SYS_TRACK_UID   = "urn:os4csapi:system:iss-orbittrack-publisher:v1"
DS_POS_OUTPUT   = "issPosition"
DS_TRACK_OUTPUT = "issOrbitTrack"

# Deployment tree root
DEPLOY_ROOT_UID = "urn:os4csapi:deployment:orbital-tracking-demo:v1"

VALID_TIME_START = "2026-01-01T00:00:00Z"

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — Procedures (geo+json Features)
# ═══════════════════════════════════════════════════════════════════════════

PROCEDURE_SGP4 = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": PROC_SGP4_UID,
        "featureType": "sosa:ObservingProcedure",
        "name": "SGP4 Propagation v1",
        "description": (
            "Derives ISS geodetic position (WGS-84) from NORAD orbital elements "
            "using the Simplified General Perturbations Model 4 (SGP4). "
            "Input: OMM/TLE element set + target UTC epoch. "
            "Output: lat_deg, lon_deg, alt_km, velocity_km_s. "
            "Uses WGS-72 gravity model with iterative geodetic conversion. "
            "TLE source: CelesTrak OMM JSON endpoint. "
            "Reference implementation: python-sgp4 (Brandon Rhodes). "
            "See: https://celestrak.org/NORAD/documentation/gp-data-formats.php"
        ),
        "validTime": [VALID_TIME_START, ".."],
    },
}

PROCEDURE_ORBIT_TRACK = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": PROC_ORBIT_UID,
        "featureType": "sosa:ObservingProcedure",
        "name": "Orbit Track Generation v1",
        "description": (
            "Generates a predicted ground-track product for one full orbital period "
            "(~100 minutes) by propagating SGP4 positions at 60-second intervals from "
            "the current epoch forward. Each track product is an array of "
            "{lat_deg, lon_deg, alt_km, timestamp} points. Product is regenerated "
            "every 5 minutes to incorporate any TLE updates. "
            "Reference implementation: python-sgp4 (Brandon Rhodes)."
        ),
        "validTime": [VALID_TIME_START, ".."],
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — Systems
#
#  Two-step approach:
#    1. POST a geo+json Feature stub (name, uid, typeOf)
#    2. PUT the full SensorML body for rich metadata
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_POS_STUB = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": SYS_POS_UID,
        "name": "ISS Position Publisher",
        "description": (
            "Software publisher that computes ISS geodetic position from NORAD "
            "orbital elements using SGP4 propagation and emits real-time position "
            "observations (lat, lon, alt, velocity) every 30 seconds."
        ),
        "typeOf": PROC_SGP4_UID,
        "validTime": [VALID_TIME_START, ".."],
    },
}

SYSTEM_TRACK_STUB = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": SYS_TRACK_UID,
        "name": "ISS Orbit Track Publisher",
        "description": (
            "Software publisher that generates predicted ISS orbit ground-track "
            "products. Propagates one full orbital period (~93 minutes) of future "
            "positions at 60-second intervals using SGP4."
        ),
        "typeOf": PROC_ORBIT_UID,
        "validTime": [VALID_TIME_START, ".."],
    },
}

# SensorML bodies for PUT (rich metadata) — loaded inline from the template content
SYSTEM_POS_SML = {
    "type": "PhysicalSystem",
    "uniqueId": SYS_POS_UID,
    "definition": "sosa:System",
    "label": "ISS Position Publisher",
    "description": (
        "Software publisher that computes ISS geodetic position from NORAD "
        "orbital elements using SGP4 propagation and emits real-time position "
        "observations (lat, lon, alt, velocity) every 30 seconds. Fetches "
        "Two-Line Element sets from CelesTrak, propagates with the SGP4 model, "
        "and publishes via CSAPI/OSH."
    ),
    "keywords": [
        "ISS", "Zarya", "NORAD 25544", "satellite", "SGP4",
        "orbital propagation", "space station", "LEO",
        "position publisher", "CelesTrak",
    ],
    "identifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/ShortName",
         "label": "Short Name", "value": "ISS Position Publisher"},
        {"definition": "http://sensorml.com/ont/swe/property/LongName",
         "label": "Long Name", "value": "International Space Station SGP4 Position Feed"},
        {"definition": "http://sensorml.com/ont/swe/property/ModelNumber",
         "label": "NORAD Catalog Number", "value": "25544"},
        {"definition": "http://sensorml.com/ont/swe/property/SerialNumber",
         "label": "COSPAR ID", "value": "1998-067A"},
    ],
    "classifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/SensorType",
         "label": "Platform Type", "value": "Space Station"},
        {"definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
         "label": "Orbit Class", "value": "Low Earth Orbit (LEO)"},
        {"definition": "http://sensorml.com/ont/swe/property/SystemRole",
         "label": "System Role", "value": "Position Publisher"},
    ],
    "validTime": [VALID_TIME_START, ".."],
    "characteristics": [
        {
            "label": "Orbital Parameters",
            "characteristics": [
                {"type": "Quantity", "name": "orbital_period",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Orbital Period", "uom": {"code": "min"}, "value": 92.7},
                {"type": "Quantity", "name": "inclination",
                 "definition": "http://qudt.org/vocab/quantitykind/Angle",
                 "label": "Inclination", "uom": {"code": "deg"}, "value": 51.6},
                {"type": "Quantity", "name": "altitude_min",
                 "definition": "http://qudt.org/vocab/quantitykind/Height",
                 "label": "Altitude (perigee)", "uom": {"code": "km"}, "value": 408.0},
                {"type": "Quantity", "name": "altitude_max",
                 "definition": "http://qudt.org/vocab/quantitykind/Height",
                 "label": "Altitude (apogee)", "uom": {"code": "km"}, "value": 420.0},
            ],
        }
    ],
    "capabilities": [
        {
            "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
            "label": "Publisher Capabilities",
            "capabilities": [
                {"type": "Quantity", "name": "update_interval",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Position Update Interval", "uom": {"code": "s"}, "value": 30.0},
                {"type": "Text", "name": "propagation_model",
                 "definition": "http://sensorml.com/ont/swe/property/AlgorithmType",
                 "label": "Propagation Model",
                 "value": "SGP4 (Simplified General Perturbations 4)"},
                {"type": "Text", "name": "tle_source",
                 "definition": "http://sensorml.com/ont/swe/property/DataSource",
                 "label": "TLE Source", "value": "CelesTrak (celestrak.org)"},
                {"type": "Quantity", "name": "tle_refresh",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "TLE Refresh Interval", "uom": {"code": "s"}, "value": 3600.0},
            ],
        }
    ],
    "contacts": [
        {
            "role": "http://sensorml.com/ont/swe/property/Operator",
            "organisationName": "NASA \u2014 National Aeronautics and Space Administration",
            "contactInfo": {
                "website": "https://www.nasa.gov/international-space-station/",
                "address": {
                    "city": "Washington",
                    "administrativeArea": "DC",
                    "country": "United States",
                },
            },
        },
        {
            "role": "http://sensorml.com/ont/swe/property/DataProvider",
            "organisationName": "CelesTrak",
            "contactInfo": {"website": "https://celestrak.org"},
        },
        {
            "role": "http://sensorml.com/ont/swe/property/ProjectLeader",
            "organisationName": "OS4CSAPI Project",
            "contactInfo": {"website": "https://github.com/OS4CSAPI"},
        },
    ],
    "documents": [
        {
            "role": "http://dbpedia.org/resource/Web_page",
            "name": "NASA ISS Overview",
            "description": "Official NASA International Space Station overview and fact sheet.",
            "link": {
                "href": "https://www.nasa.gov/international-space-station/space-station-overview/",
                "type": "text/html",
            },
        },
        {
            "role": "http://dbpedia.org/resource/Web_page",
            "name": "CelesTrak GP Data Formats",
            "description": "Documentation for NORAD general perturbations (GP) element set formats including OMM JSON.",
            "link": {
                "href": "https://celestrak.org/NORAD/documentation/gp-data-formats.php",
                "type": "text/html",
            },
        },
        {
            "role": "http://dbpedia.org/resource/Software",
            "name": "python-sgp4",
            "description": "Python implementation of SGP4 satellite propagation. Used by this publisher for orbital position computation.",
            "link": {
                "href": "https://github.com/brandon-rhodes/python-sgp4",
                "type": "text/html",
            },
        },
        {
            "role": "http://dbpedia.org/resource/Photograph",
            "name": "ISS Photograph",
            "description": "Official NASA photograph of the International Space Station in orbit.",
            "link": {
                "href": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/International_Space_Station_after_undocking_of_STS-132.jpg/1280px-International_Space_Station_after_undocking_of_STS-132.jpg",
                "type": "image/jpeg",
            },
        },
        {
            "role": "http://dbpedia.org/resource/Web_page",
            "name": "ISS \u2014 Wikipedia",
            "description": "Wikipedia article on the International Space Station with comprehensive technical specifications.",
            "link": {
                "href": "https://en.wikipedia.org/wiki/International_Space_Station",
                "type": "text/html",
            },
        },
    ],
}

SYSTEM_TRACK_SML = {
    "type": "PhysicalSystem",
    "uniqueId": SYS_TRACK_UID,
    "definition": "sosa:System",
    "label": "ISS Orbit Track Publisher",
    "description": (
        "Software publisher that generates predicted ISS orbit ground-track products. "
        "Propagates one full orbital period (~93 minutes) of future positions at "
        "60-second intervals using SGP4, producing a polyline of lat/lon/alt points "
        "representing the predicted ground track. Published every 5 minutes."
    ),
    "keywords": [
        "ISS", "orbit track", "ground track", "SGP4",
        "orbital prediction", "LEO", "trajectory", "NORAD 25544",
    ],
    "identifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/ShortName",
         "label": "Short Name", "value": "ISS Orbit Track Publisher"},
        {"definition": "http://sensorml.com/ont/swe/property/LongName",
         "label": "Long Name",
         "value": "International Space Station Predicted Orbit Ground Track"},
        {"definition": "http://sensorml.com/ont/swe/property/ModelNumber",
         "label": "NORAD Catalog Number", "value": "25544"},
    ],
    "classifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/SensorType",
         "label": "Product Type", "value": "Orbit Ground Track"},
        {"definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
         "label": "Application",
         "value": "Orbital Prediction / Situational Awareness"},
        {"definition": "http://sensorml.com/ont/swe/property/SystemRole",
         "label": "System Role", "value": "Track Product Generator"},
    ],
    "validTime": [VALID_TIME_START, ".."],
    "characteristics": [
        {
            "label": "Track Generation Parameters",
            "characteristics": [
                {"type": "Quantity", "name": "prediction_horizon",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Prediction Horizon", "uom": {"code": "min"}, "value": 100.0},
                {"type": "Quantity", "name": "sample_interval",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Track Point Interval", "uom": {"code": "s"}, "value": 60.0},
                {"type": "Count", "name": "points_per_track",
                 "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                 "label": "Points Per Track", "value": 100},
            ],
        }
    ],
    "capabilities": [
        {
            "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
            "label": "Track Publisher Capabilities",
            "capabilities": [
                {"type": "Quantity", "name": "publish_interval",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Track Publish Interval", "uom": {"code": "s"}, "value": 300.0},
                {"type": "Text", "name": "propagation_model",
                 "definition": "http://sensorml.com/ont/swe/property/AlgorithmType",
                 "label": "Propagation Model",
                 "value": "SGP4 (Simplified General Perturbations 4)"},
            ],
        }
    ],
    "contacts": [
        {
            "role": "http://sensorml.com/ont/swe/property/Operator",
            "organisationName": "NASA \u2014 National Aeronautics and Space Administration",
            "contactInfo": {
                "website": "https://www.nasa.gov/international-space-station/",
            },
        },
        {
            "role": "http://sensorml.com/ont/swe/property/ProjectLeader",
            "organisationName": "OS4CSAPI Project",
            "contactInfo": {"website": "https://github.com/OS4CSAPI"},
        },
    ],
    "documents": [
        {
            "role": "http://dbpedia.org/resource/Web_page",
            "name": "CelesTrak GP Data Formats",
            "description": "Documentation for NORAD GP element set formats used as input to track generation.",
            "link": {
                "href": "https://celestrak.org/NORAD/documentation/gp-data-formats.php",
                "type": "text/html",
            },
        },
        {
            "role": "http://dbpedia.org/resource/Photograph",
            "name": "ISS Photograph",
            "description": "Official NASA photograph of the International Space Station in orbit.",
            "link": {
                "href": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/International_Space_Station_after_undocking_of_STS-132.jpg/1280px-International_Space_Station_after_undocking_of_STS-132.jpg",
                "type": "image/jpeg",
            },
        },
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — DataStreams
#
#  obsFormat: application/om+json  (matches oshconnect insert_observation_dict)
#  uses resultSchema (not recordSchema) per O&M JSON convention
# ═══════════════════════════════════════════════════════════════════════════

DATASTREAM_POSITION = {
    "name": "ISS Position (SGP4)",
    "outputName": DS_POS_OUTPUT,
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "label": "ISS Geodetic Position Fix",
            "description": "Real-time ISS position derived from SGP4 propagation of NORAD TLE elements.",
            "fields": [
                {"type": "Time", "name": "timestamp",
                 "definition": "http://sensorml.com/ont/swe/property/SamplingTime",
                 "label": "Sampling Time",
                 "referenceTime": "1970-01-01T00:00:00Z",
                 "uom": {"code": "s"}},
                {"type": "Quantity", "name": "lat_deg",
                 "definition": "http://qudt.org/vocab/quantitykind/Latitude",
                 "label": "Latitude", "description": "Geodetic latitude (WGS-84)",
                 "uom": {"code": "deg"}},
                {"type": "Quantity", "name": "lon_deg",
                 "definition": "http://qudt.org/vocab/quantitykind/Longitude",
                 "label": "Longitude", "description": "Geodetic longitude (WGS-84)",
                 "uom": {"code": "deg"}},
                {"type": "Quantity", "name": "alt_km",
                 "definition": "http://qudt.org/vocab/quantitykind/Height",
                 "label": "Altitude", "description": "Altitude above WGS-84 ellipsoid",
                 "uom": {"code": "km"}},
                {"type": "Quantity", "name": "velocity_km_s",
                 "definition": "http://qudt.org/vocab/quantitykind/Speed",
                 "label": "Orbital Velocity", "description": "ECI velocity magnitude",
                 "uom": {"code": "km/s"}},
                {"type": "Count", "name": "noradId",
                 "definition": "http://sensorml.com/ont/swe/property/Identifier",
                 "label": "NORAD Catalog Number"},
                {"type": "Text", "name": "assetName",
                 "definition": "http://sensorml.com/ont/swe/property/ShortName",
                 "label": "Asset Name"},
                {"type": "Text", "name": "sourceEpoch",
                 "definition": "http://sensorml.com/ont/swe/property/ReferenceTime",
                 "label": "TLE Epoch",
                 "description": "ISO 8601 epoch of the source TLE element set"},
                {"type": "Quantity", "name": "sourceAgeSec",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "TLE Age",
                 "description": "Seconds since TLE epoch — indicates propagation confidence",
                 "uom": {"code": "s"}},
                {"type": "Quantity", "name": "posErrorM",
                 "definition": "http://qudt.org/vocab/quantitykind/Length",
                 "label": "Estimated Position Error",
                 "description": "Rough SGP4 position error estimate based on TLE age (~1km at epoch, growing ~1-2km/day)",
                 "uom": {"code": "m"}},
                {"type": "Text", "name": "method",
                 "definition": "http://sensorml.com/ont/swe/property/AlgorithmType",
                 "label": "Propagation Method"},
            ],
        },
    },
}

DATASTREAM_ORBIT_TRACK = {
    "name": "ISS Orbit Ground Track",
    "outputName": DS_TRACK_OUTPUT,
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "label": "ISS Predicted Orbit Ground Track",
            "description": "Predicted ground track for one full orbital period (~100 min) computed via SGP4 propagation at 60s intervals.",
            "fields": [
                {"type": "Time", "name": "computedAt",
                 "definition": "http://sensorml.com/ont/swe/property/SamplingTime",
                 "label": "Computation Time",
                 "referenceTime": "1970-01-01T00:00:00Z",
                 "uom": {"code": "s"}},
                {"type": "Count", "name": "noradId",
                 "definition": "http://sensorml.com/ont/swe/property/Identifier",
                 "label": "NORAD Catalog Number"},
                {"type": "Text", "name": "assetName",
                 "definition": "http://sensorml.com/ont/swe/property/ShortName",
                 "label": "Asset Name"},
                {"type": "Quantity", "name": "durationMin",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Track Duration",
                 "description": "Total duration of predicted track in minutes",
                 "uom": {"code": "min"}},
                {"type": "Count", "name": "numPoints",
                 "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                 "label": "Number of Track Points"},
                {"type": "Text", "name": "method",
                 "definition": "http://sensorml.com/ont/swe/property/AlgorithmType",
                 "label": "Propagation Method"},
                {"type": "Text", "name": "trackPointsJson",
                 "definition": "http://sensorml.com/ont/swe/property/DataPayload",
                 "label": "Track Points (JSON)",
                 "description": (
                     "JSON-encoded array of {timestamp, lat_deg, lon_deg, alt_km} objects "
                     "representing the predicted ground track. Encoded as Text for maximum "
                     "portability across SWE implementations."
                 )},
            ],
        },
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — Deployment tree
# ═══════════════════════════════════════════════════════════════════════════

DEPLOYMENT_TREE = {
    "uid": "urn:os4csapi:deployment:orbital-tracking-demo:v1",
    "name": "Orbital Tracking Demo",
    "description": (
        "Top-level deployment context for orbital object tracking demonstrations. "
        "Contains tracked LEO objects and associated tracking products."
    ),
    "geometry": None,
    "properties": {},
    "validTime": [VALID_TIME_START, ".."],
    "children": [
        {
            "uid": "urn:os4csapi:deployment:leo-objects:v1",
            "name": "LEO Objects",
            "description": "Grouping node for Low Earth Orbit tracked objects.",
            "geometry": None,
            "properties": {},
            "validTime": [VALID_TIME_START, ".."],
            "children": [
                {
                    "uid": "urn:os4csapi:deployment:iss-tracking-role:v1",
                    "name": "ISS Tracking Role",
                    "description": (
                        "Operational role branch for ISS (NORAD 25544 / ZARYA) tracking "
                        "products including position feeds and orbit-track predictions."
                    ),
                    "geometry": None,
                    "properties": {},
                    "validTime": [VALID_TIME_START, ".."],
                    "children": [
                        {
                            "uid": "urn:os4csapi:deployment:iss-position-feed:v1",
                            "name": "ISS Position Feed",
                            "description": "Leaf deployment linking the ISS Position Publisher system to the tracking hierarchy.",
                            "geometry": None,
                            "properties": {
                                "platform@link": {
                                    "title": "ISS Position Publisher",
                                    "uid": SYS_POS_UID,
                                    "type": "application/sml+json",
                                },
                            },
                            "validTime": [VALID_TIME_START, ".."],
                            "children": [],
                        },
                        {
                            "uid": "urn:os4csapi:deployment:iss-orbittrack-feed:v1",
                            "name": "ISS Orbit Track Feed",
                            "description": "Leaf deployment linking the ISS Orbit Track Publisher system to the tracking hierarchy.",
                            "geometry": None,
                            "properties": {
                                "platform@link": {
                                    "title": "ISS Orbit Track Publisher",
                                    "uid": SYS_TRACK_UID,
                                    "type": "application/sml+json",
                                },
                            },
                            "validTime": [VALID_TIME_START, ".."],
                            "children": [],
                        },
                    ],
                },
            ],
        },
    ],
}

# All deployment UIDs (leaf-first) for clean teardown
ALL_DEPLOYMENT_UIDS = [
    "urn:os4csapi:deployment:iss-position-feed:v1",
    "urn:os4csapi:deployment:iss-orbittrack-feed:v1",
    "urn:os4csapi:deployment:iss-tracking-role:v1",
    "urn:os4csapi:deployment:leo-objects:v1",
    "urn:os4csapi:deployment:orbital-tracking-demo:v1",
]

# ═══════════════════════════════════════════════════════════════════════════
#  Networking
# ═══════════════════════════════════════════════════════════════════════════

# DNS monkey-patch: resolve DuckDNS → Oracle Cloud IP
_real_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "os4csapi-osh.duckdns.org":
        return _real_getaddrinfo(ORACLE_IP, port, *args, **kwargs)
    return _real_getaddrinfo(host, port, *args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo

_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

_AUTH_HEADER = "Basic " + base64.b64encode(f"{AUTH_USER}:{AUTH_PASS}".encode()).decode()

_MAX_RETRIES = 5
_RETRY_DELAY = 3


def _with_retry(fn, label="request"):
    for attempt in range(_MAX_RETRIES):
        try:
            return fn()
        except HTTPError:
            raise
        except (URLError, OSError, ConnectionError, TimeoutError) as e:
            if attempt < _MAX_RETRIES - 1:
                wait = _RETRY_DELAY * (attempt + 1)
                print(f"  \u21bb Retry {label} in {wait}s ({type(e).__name__})")
                time.sleep(wait)
            else:
                raise


def api_get(path: str) -> dict | None:
    def fn():
        url = f"{BASE_URL}/{path}"
        req = Request(url, headers={
            "Authorization": _AUTH_HEADER,
            "Accept": "application/json",
        })
        try:
            with urlopen(req, timeout=15, context=_ssl_ctx) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            if e.code == 404:
                return None
            raise
    return _with_retry(fn, f"GET {path}")


def api_post(path: str, body: dict,
             content_type: str = "application/json") -> dict | None:
    def fn():
        url = f"{BASE_URL}/{path}"
        data = json.dumps(body).encode()
        req = Request(url, data=data, method="POST", headers={
            "Authorization": _AUTH_HEADER,
            "Content-Type": content_type,
            "Accept": "application/json",
        })
        try:
            with urlopen(req, timeout=30, context=_ssl_ctx) as resp:
                location = resp.headers.get("Location", "")
                raw = resp.read().decode()
                if location:
                    new_id = location.rstrip("/").split("/")[-1]
                    return {"id": new_id, "_location": location}
                if resp.status == 204 or not raw.strip():
                    return None
                return json.loads(raw)
        except HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code} POST {url}: {body_text[:400]}")
    return _with_retry(fn, f"POST {path}")


def api_put(path: str, body: dict,
            content_type: str = "application/sml+json") -> bool:
    """PUT (update) a resource. Returns True on success."""
    def fn():
        url = f"{BASE_URL}/{path}"
        data = json.dumps(body).encode()
        req = Request(url, data=data, method="PUT", headers={
            "Authorization": _AUTH_HEADER,
            "Content-Type": content_type,
            "Accept": "application/json",
        })
        try:
            with urlopen(req, timeout=30, context=_ssl_ctx) as resp:
                return resp.status in (200, 204)
        except HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            raise RuntimeError(f"HTTP {e.code} PUT {url}: {body_text[:400]}")
    return _with_retry(fn, f"PUT {path}")


def api_delete(path: str) -> bool:
    def fn():
        url = f"{BASE_URL}/{path}"
        req = Request(url, method="DELETE", headers={
            "Authorization": _AUTH_HEADER,
        })
        try:
            with urlopen(req, timeout=15, context=_ssl_ctx) as resp:
                return resp.status in (200, 204)
        except HTTPError as e:
            if e.code == 404:
                return False
            raise
    return _with_retry(fn, f"DELETE {path}")


# ═══════════════════════════════════════════════════════════════════════════
#  Lookup helpers
# ═══════════════════════════════════════════════════════════════════════════

_uid_cache: dict[str, str] = {}


def find_by_uid(collection: str, uid: str) -> str | None:
    """Find a resource by UID in a collection. Returns server ID or None."""
    cache_key = f"{collection}:{uid}"
    if cache_key in _uid_cache:
        return _uid_cache[cache_key]

    result = api_get(f"{collection}?uid={uid}")
    if result and "items" in result:
        for item in result["items"]:
            props = item.get("properties", item)
            if props.get("uid") == uid:
                item_id = item.get("id") or props.get("id")
                if item_id:
                    _uid_cache[cache_key] = str(item_id)
                    return str(item_id)
    return None


def find_datastream(system_id: str, output_name: str) -> dict | None:
    """Find a datastream on a system by outputName."""
    result = api_get(f"systems/{system_id}/datastreams")
    if result and "items" in result:
        for ds in result["items"]:
            if ds.get("outputName") == output_name:
                return ds
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  Clean (teardown) helpers
# ═══════════════════════════════════════════════════════════════════════════

def clean_resource(collection: str, uid: str, stats: dict, dry_run: bool):
    """Delete a resource by UID if it exists."""
    existing_id = find_by_uid(collection, uid)
    if not existing_id:
        return
    print(f"  DELETE {collection}/{existing_id} ({uid})")
    if not dry_run:
        try:
            api_delete(f"{collection}/{existing_id}")
            stats["deleted"] += 1
            # Invalidate cache
            _uid_cache.pop(f"{collection}:{uid}", None)
        except Exception as e:
            print(f"  ERROR deleting {collection}/{existing_id}: {e}")
            stats["errors"] += 1
    else:
        stats["deleted"] += 1


def clean_all(stats: dict, dry_run: bool):
    """Delete all ISS resources in safe order (deployments → datastreams → systems → procedures)."""
    print("\n\u2500\u2500 Clean: Deployments \u2500\u2500")
    for uid in ALL_DEPLOYMENT_UIDS:
        clean_resource("deployments", uid, stats, dry_run)

    print("\n\u2500\u2500 Clean: DataStreams \u2500\u2500")
    # DataStreams must be deleted via their parent system
    for sys_uid, output_name in [(SYS_POS_UID, DS_POS_OUTPUT), (SYS_TRACK_UID, DS_TRACK_OUTPUT)]:
        sys_id = find_by_uid("systems", sys_uid)
        if sys_id:
            ds = find_datastream(sys_id, output_name)
            if ds:
                ds_id = ds.get("id")
                print(f"  DELETE datastreams/{ds_id} ({output_name})")
                if not dry_run:
                    try:
                        api_delete(f"datastreams/{ds_id}")
                        stats["deleted"] += 1
                    except Exception as e:
                        print(f"  ERROR deleting DS {ds_id}: {e}")
                        stats["errors"] += 1
                else:
                    stats["deleted"] += 1

    print("\n\u2500\u2500 Clean: Systems \u2500\u2500")
    for uid in [SYS_POS_UID, SYS_TRACK_UID]:
        clean_resource("systems", uid, stats, dry_run)

    print("\n\u2500\u2500 Clean: Procedures \u2500\u2500")
    for uid in [PROC_SGP4_UID, PROC_ORBIT_UID]:
        clean_resource("procedures", uid, stats, dry_run)


# ═══════════════════════════════════════════════════════════════════════════
#  Deployment tree creation (recursive)
# ═══════════════════════════════════════════════════════════════════════════

def create_deployment_node(node: dict, parent_path: str | None, depth: int,
                           stats: dict, dry_run: bool):
    """Recursively create a deployment node and its children."""
    uid = node["uid"]
    indent = "  " + "  " * depth
    short = uid.split(":")[-2] + ":" + uid.split(":")[-1]

    existing_id = find_by_uid("deployments", uid)
    if existing_id:
        print(f"{indent}SKIP {node['name']} \u2014 already exists ({existing_id})")
        stats["skipped"] += 1
        child_path = f"deployments/{existing_id}/subdeployments"
        for child in node.get("children", []):
            create_deployment_node(child, child_path, depth + 1, stats, dry_run)
        return

    # Build geo+json Feature body
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

    # Resolve extra properties (platform@link, etc.)
    for k, v in node.get("properties", {}).items():
        if k == "platform@link":
            if dry_run:
                sys_id = "DRY"
            else:
                sys_id = find_by_uid("systems", v["uid"])
                if not sys_id:
                    print(f"{indent}ERROR: System {v['uid']} not found for platform@link")
                    stats["errors"] += 1
                    return
            body["properties"]["platform@link"] = {
                "href": f"/sensorhub/api/systems/{sys_id}",
                "title": v["title"],
                "uid": v["uid"],
                "type": v["type"],
            }
        else:
            body["properties"][k] = v

    post_path = parent_path or "deployments"

    print(f"{indent}CREATE deployment: {node['name']} ({short})")
    print(f"{indent}  POST \u2192 {post_path}")

    new_id = None
    if not dry_run:
        try:
            result = api_post(post_path, body, content_type="application/geo+json")
            new_id = result.get("id") if result else "?"
            print(f"{indent}  \u2192 id={new_id}")
            _uid_cache[f"deployments:{uid}"] = new_id
            stats["created"] += 1
        except RuntimeError as e:
            print(f"{indent}  ERROR: {e}")
            stats["errors"] += 1
            return
    else:
        new_id = f"DRY-{short}"
        print(f"{indent}  \u2192 (dry run)")
        stats["created"] += 1

    if new_id and node.get("children"):
        if dry_run:
            child_path = f"{post_path}/DRY/subdeployments"
        else:
            child_path = f"deployments/{new_id}/subdeployments"
        for child in node["children"]:
            create_deployment_node(child, child_path, depth + 1, stats, dry_run)


# ═══════════════════════════════════════════════════════════════════════════
#  Bootstrap logic
# ═══════════════════════════════════════════════════════════════════════════

def bootstrap(clean: bool = False, clean_only: bool = False, dry_run: bool = False):
    stats = {"created": 0, "skipped": 0, "deleted": 0, "patched": 0, "errors": 0}

    # ── Clean phase (if requested) ───────────────────────────────────
    if clean or clean_only:
        print("\n" + "=" * 60)
        print("  CLEAN PHASE — deleting existing ISS resources")
        print("=" * 60)
        clean_all(stats, dry_run)
        if clean_only:
            _print_summary(stats, dry_run)
            return stats

    # ── Phase 1: Procedures ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 1: Procedures")
    print("=" * 60)

    for proc_def, proc_uid, label in [
        (PROCEDURE_SGP4, PROC_SGP4_UID, "SGP4 Propagation"),
        (PROCEDURE_ORBIT_TRACK, PROC_ORBIT_UID, "Orbit Track Generation"),
    ]:
        existing = find_by_uid("procedures", proc_uid)
        if existing:
            print(f"  \u2713 {label} already exists: {existing}")
            stats["skipped"] += 1
        else:
            print(f"  POST procedure: {label}")
            if not dry_run:
                result = api_post("procedures", proc_def,
                                  content_type="application/geo+json")
                pid = result["id"]
                _uid_cache[f"procedures:{proc_uid}"] = pid
                print(f"  \u2713 Created: {pid}")
                stats["created"] += 1
            else:
                print(f"  (dry-run) Would create procedure: {proc_uid}")
                stats["created"] += 1

    # ── Phase 2: Systems (stub POST + SML PUT) ──────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 2: Systems (geo+json stub + SensorML metadata)")
    print("=" * 60)

    sys_ids = {}
    for stub, sml, sys_uid, label in [
        (SYSTEM_POS_STUB, SYSTEM_POS_SML, SYS_POS_UID, "ISS Position Publisher"),
        (SYSTEM_TRACK_STUB, SYSTEM_TRACK_SML, SYS_TRACK_UID, "ISS Orbit Track Publisher"),
    ]:
        existing = find_by_uid("systems", sys_uid)
        if existing:
            print(f"  \u2713 {label} already exists: {existing}")
            sys_ids[sys_uid] = existing
            stats["skipped"] += 1
            # Still apply SML update in case metadata needs refreshing
            print(f"    PUT SensorML metadata update...")
            if not dry_run:
                try:
                    api_put(f"systems/{existing}", sml)
                    print(f"    \u2713 SensorML metadata updated")
                    stats["patched"] += 1
                except RuntimeError as e:
                    print(f"    ERROR updating SensorML: {e}")
                    stats["errors"] += 1
            else:
                print(f"    (dry-run) Would update SensorML")
                stats["patched"] += 1
        else:
            print(f"  POST system stub: {label}")
            if not dry_run:
                result = api_post("systems", stub,
                                  content_type="application/geo+json")
                sid = result["id"]
                _uid_cache[f"systems:{sys_uid}"] = sid
                sys_ids[sys_uid] = sid
                print(f"  \u2713 Created stub: {sid}")
                stats["created"] += 1

                # Apply rich SensorML metadata
                print(f"    PUT SensorML metadata...")
                try:
                    api_put(f"systems/{sid}", sml)
                    print(f"    \u2713 SensorML metadata applied")
                    stats["patched"] += 1
                except RuntimeError as e:
                    print(f"    ERROR applying SensorML: {e}")
                    stats["errors"] += 1
            else:
                sys_ids[sys_uid] = "<dry-run>"
                print(f"  (dry-run) Would create system + PUT SensorML")
                stats["created"] += 1
                stats["patched"] += 1

    # ── Phase 3: DataStreams ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 3: DataStreams")
    print("=" * 60)

    for ds_def, sys_uid, output_name, label in [
        (DATASTREAM_POSITION, SYS_POS_UID, DS_POS_OUTPUT, "ISS Position (SGP4)"),
        (DATASTREAM_ORBIT_TRACK, SYS_TRACK_UID, DS_TRACK_OUTPUT, "ISS Orbit Ground Track"),
    ]:
        sys_id = sys_ids.get(sys_uid)
        if not sys_id or sys_id == "<dry-run>":
            print(f"  (dry-run) Would create datastream: {label}")
            stats["created"] += 1
            continue

        existing_ds = find_datastream(sys_id, output_name)
        if existing_ds:
            ds_id = existing_ds.get("id")
            print(f"  \u2713 {label} already exists: {ds_id}")
            stats["skipped"] += 1
        else:
            print(f"  POST datastream: {label} under system {sys_id}")
            if not dry_run:
                result = api_post(f"systems/{sys_id}/datastreams", ds_def)
                ds_id = result["id"]
                print(f"  \u2713 Created: {ds_id}")
                stats["created"] += 1
            else:
                print(f"  (dry-run) Would create datastream: {output_name}")
                stats["created"] += 1

    # ── Phase 4: Deployment tree ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 4: Deployment Hierarchy")
    print("=" * 60)

    create_deployment_node(DEPLOYMENT_TREE, parent_path=None, depth=0,
                           stats=stats, dry_run=dry_run)

    # ── Summary ──────────────────────────────────────────────────────
    _print_summary(stats, dry_run)

    if not dry_run:
        print("\n  Resource IDs:")
        for label, uid in [
            ("Procedure SGP4", PROC_SGP4_UID),
            ("Procedure Orbit", PROC_ORBIT_UID),
            ("System Position", SYS_POS_UID),
            ("System Track", SYS_TRACK_UID),
            ("Deploy Root", DEPLOY_ROOT_UID),
        ]:
            rid = find_by_uid(
                "procedures" if "procedure" in uid else
                "deployments" if "deployment" in uid else
                "systems", uid
            )
            print(f"    {label:20s} {rid or 'NOT FOUND'}")

        # Print datastream IDs
        pos_sys = sys_ids.get(SYS_POS_UID)
        track_sys = sys_ids.get(SYS_TRACK_UID)
        if pos_sys:
            ds = find_datastream(pos_sys, DS_POS_OUTPUT)
            print(f"    {'DS Position':20s} {ds.get('id') if ds else 'NOT FOUND'}")
        if track_sys:
            ds = find_datastream(track_sys, DS_TRACK_OUTPUT)
            print(f"    {'DS Orbit Track':20s} {ds.get('id') if ds else 'NOT FOUND'}")

        print(f"\n  \u279c Set env vars for iss_publisher_v3.py:")
        print(f"    POS_SYSTEM_UID={SYS_POS_UID}")
        print(f"    POS_DS_NAME=ISS Position (SGP4)")
        print(f"    TRACK_SYSTEM_UID={SYS_TRACK_UID}")
        print(f"    TRACK_DS_NAME=ISS Orbit Ground Track")

    return stats


def _print_summary(stats: dict, dry_run: bool):
    print("\n" + "\u2500" * 60)
    prefix = "(DRY RUN) " if dry_run else ""
    print(f"  {prefix}Summary:")
    print(f"    Created:  {stats['created']}")
    print(f"    Patched:  {stats['patched']}")
    print(f"    Skipped:  {stats['skipped']}")
    print(f"    Deleted:  {stats['deleted']}")
    print(f"    Errors:   {stats['errors']}")


# ═══════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap the ISS dual-product publisher on the OS4CSAPI server")
    parser.add_argument("--clean", action="store_true",
                        help="Delete then recreate all resources")
    parser.add_argument("--clean-only", action="store_true",
                        help="Delete all ISS resources (teardown only)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without executing")
    args = parser.parse_args()

    print("=" * 60)
    print("  OS4CSAPI \u2014 ISS Publisher Bootstrap")
    print("=" * 60)
    print(f"  Server:     {BASE_URL}")
    print(f"  Procedures: {PROC_SGP4_UID}")
    print(f"              {PROC_ORBIT_UID}")
    print(f"  Systems:    {SYS_POS_UID}")
    print(f"              {SYS_TRACK_UID}")
    print(f"  Outputs:    {DS_POS_OUTPUT}, {DS_TRACK_OUTPUT}")
    if args.dry_run:
        print(f"  Mode:       DRY RUN")
    elif args.clean_only:
        print(f"  Mode:       CLEAN ONLY (teardown)")
    elif args.clean:
        print(f"  Mode:       CLEAN + RECREATE")

    try:
        bootstrap(clean=args.clean, clean_only=args.clean_only,
                  dry_run=args.dry_run)
    except Exception as e:
        print(f"\n  \u2717 FATAL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
