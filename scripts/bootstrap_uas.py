#!/usr/bin/env python3
"""
bootstrap_uas.py — Register UAS/Localizer/SENREP resources on the OS4CSAPI server.

This script enriches EXISTING systems with SensorML metadata and creates
NEW datastreams, procedures, and deployment leaves.  It never deletes or
overwrites data that is already on the server.

Resources handled (skip-if-exists / update-if-exists):

  Procedures:
    1. urn:os4csapi:procedure:lob-wls-triangulation:v1  (exists — skip)
    2. urn:os4csapi:procedure:senrep:sop:v1              (create)

  Systems (all 4 exist — PUT SensorML enrichment):
    3. urn:os4csapi:system:fusion:az-string-alpha-localizer     (id=04o0)
    4. urn:os4csapi:system:set:ft-huachuca:001                  (id=040g)
    5. urn:os4csapi:system:monitoring-site-node:ft-huachuca:001 (id=0410)
    6. urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001   (id=041g)

  DataStreams (additive — existing streams untouched):
    7. locationEstimate  (10-field SWE DataRecord) under localizer
    8. senrep_v1_1       (25-field SWE DataRecord) under SET-A

  Deployment leaves:
    9. urn:os4csapi:deployment:localizer:ft-huachuca:alpha:001   (create)
       parent = String Alpha (urn:os4csapi:deployment:string:ft-huachuca:001)
   10. urn:os4csapi:deployment:relay:ft-huachuca:001             (exists — skip)

  Not bootstrapped (runtime template only):
    - samplingfeature_track_template.json — created per-contact at SENREP time

Usage:
    python bootstrap_uas.py              # enrich + create (skip if exists)
    python bootstrap_uas.py --dry-run    # print what would happen
    python bootstrap_uas.py --clean      # delete UAS-specific resources then recreate
    python bootstrap_uas.py --clean-only # delete UAS-specific resources only

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

VALID_TIME_START = "2026-01-01T00:00:00Z"
# Some systems were bootstrapped with later validTimes; SML PUT requires >=
VALID_TIME_SML   = "2026-07-01T00:00:00Z"

# ── UIDs (as they exist on the server) ────────────────────────────────────
PROC_WLS_UID       = "urn:os4csapi:procedure:lob-wls-triangulation:v1"
PROC_SENREP_UID    = "urn:os4csapi:procedure:senrep:sop:v1"

SYS_LOCALIZER_UID  = "urn:os4csapi:system:fusion:az-string-alpha-localizer"
SYS_SETA_UID       = "urn:os4csapi:system:set:ft-huachuca:001"
SYS_MONSITE_UID    = "urn:os4csapi:system:monitoring-site-node:ft-huachuca:001"
SYS_RELAY_UID      = "urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001"

DS_LOC_OUTPUT      = "locationEstimate"
DS_SENREP_OUTPUT   = "senrep_v1_1"

DEPLOY_LOCALIZER_FEED_UID = "urn:os4csapi:deployment:localizer:ft-huachuca:alpha:001"
DEPLOY_RELAY_UID          = "urn:os4csapi:deployment:relay:ft-huachuca:001"

# Parent deployment for localizer feed leaf
DEPLOY_STRING_ALPHA_UID   = "urn:os4csapi:deployment:string:ft-huachuca:001"

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — Procedures (geo+json Features)
# ═══════════════════════════════════════════════════════════════════════════

PROCEDURE_SENREP_SOP = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": PROC_SENREP_UID,
        "featureType": "sosa:ObservingProcedure",
        "name": "SENREP SOP v1",
        "description": (
            "Reporting procedure used by the SET to transform reviewed "
            "sensor-derived activity into a formal sensor report (SENREP). "
            "Inputs: operator-reviewed fix, supporting LOBs, "
            "classification/context, contactId assignment. "
            "Outputs: SENREP observation, track SamplingFeature creation or update. "
            "Assumptions: (1) identity is committed at the reporting tier, "
            "(2) contactId is the authoritative join key."
        ),
        "validTime": [VALID_TIME_START, ".."],
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — System SensorML bodies (for PUT enrichment)
#
#  NOTE: uniqueId must match the server's existing UID, not the template UID.
#  For monitoring-site and relay, the server UIDs differ from the template.
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_LOCALIZER_SML = {
    "type": "PhysicalSystem",
    "uniqueId": SYS_LOCALIZER_UID,
    "definition": "sosa:System",
    "label": "AZ String Alpha Localizer",
    "description": (
        "Software fusion agent that consumes recent LOB observations from "
        "String Alpha nodes and produces weighted least-squares location estimates."
    ),
    "keywords": [
        "localizer", "WLS", "weighted-least-squares", "fusion",
        "LOB triangulation", "String Alpha", "UAS detection",
        "software-fusion-agent",
    ],
    "identifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/ShortName",
         "label": "Short Name", "value": "AZ String Alpha Localizer"},
        {"definition": "http://sensorml.com/ont/swe/property/LongName",
         "label": "Long Name",
         "value": "AZ String Alpha Weighted Least-Squares LOB Localizer"},
    ],
    "classifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/SensorType",
         "label": "System Kind", "value": "Software Fusion Agent"},
        {"definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
         "label": "Role Type", "value": "String-Level Localizer"},
        {"definition": "http://sensorml.com/ont/swe/property/SystemRole",
         "label": "System Role", "value": "Fusion Producer"},
    ],
    "validTime": [VALID_TIME_SML, ".."],
    "characteristics": [
        {
            "label": "Localizer Parameters",
            "characteristics": [
                {"type": "Quantity", "name": "staleness_limit",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Staleness Limit",
                 "description": "Maximum age in seconds for a LOB to be considered valid for fusion",
                 "uom": {"code": "s"}, "value": 15},
                {"type": "Quantity", "name": "correlation_window",
                 "definition": "http://qudt.org/vocab/quantitykind/Period",
                 "label": "Correlation Window",
                 "description": "Time window in seconds for correlating LOBs from different sensors",
                 "uom": {"code": "s"}, "value": 10},
                {"type": "Count", "name": "min_contributing_lobs",
                 "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                 "label": "Minimum Contributing LOBs",
                 "description": "Minimum number of valid LOBs required to produce a location estimate",
                 "value": 2},
            ],
        }
    ],
    "capabilities": [
        {
            "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
            "label": "Localizer Capabilities",
            "capabilities": [
                {"type": "Text", "name": "fusion_method",
                 "definition": "http://sensorml.com/ont/swe/property/AlgorithmType",
                 "label": "Fusion Method",
                 "value": "Weighted Least-Squares LOB Triangulation"},
                {"type": "Text", "name": "source_provider",
                 "definition": "http://sensorml.com/ont/swe/property/DataSource",
                 "label": "Source Provider",
                 "value": "AZ-MA node LOB streams"},
            ],
        }
    ],
    "contacts": [
        {"role": "http://sensorml.com/ont/swe/property/Operator",
         "organisationName": "OS4CSAPI Demo"},
        {"role": "http://sensorml.com/ont/swe/property/ProjectLeader",
         "organisationName": "OS4CSAPI Project",
         "contactInfo": {"website": "https://github.com/OS4CSAPI"}},
    ],
    "documents": [
        {
            "role": "http://dbpedia.org/resource/Diagram",
            "name": "Localizer Architecture Diagram",
            "description": (
                "WLS localizer data flow diagram showing LOB ingestion, "
                "correlation, and fix output."
            ),
            "link": {
                "href": "https://raw.githubusercontent.com/OS4CSAPI/ogc-csapi-explorer/main/docs/uas-localizer-senrep-pack/14_DIAGRAMS/localizer_wls_flow.svg",
                "type": "image/svg+xml",
            },
        }
    ],
}

SYSTEM_SETA_SML = {
    "type": "PhysicalSystem",
    "uniqueId": SYS_SETA_UID,
    "definition": "sosa:System",
    "label": "SET-A",
    "description": (
        "Sensor Employment Team A. Reporting-tier system responsible for "
        "reviewing detections/fixes and issuing formal sensor reports (SENREPs)."
    ),
    "keywords": [
        "SET", "Sensor Employment Team", "SENREP", "reporting",
        "identity commitment", "human-team", "Ft Huachuca",
    ],
    "identifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/ShortName",
         "label": "Short Name", "value": "SET-A"},
        {"definition": "http://sensorml.com/ont/swe/property/LongName",
         "label": "Long Name",
         "value": "Sensor Employment Team A \u2014 Ft Huachuca"},
    ],
    "classifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/SensorType",
         "label": "System Kind", "value": "Human Team"},
        {"definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
         "label": "Role Type", "value": "Reporting Team"},
        {"definition": "http://sensorml.com/ont/swe/property/SystemRole",
         "label": "System Role",
         "value": "Identity Authority \u2014 SENREP Issuer"},
    ],
    "validTime": [VALID_TIME_SML, ".."],
    "capabilities": [
        {
            "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
            "label": "Reporting Capabilities",
            "capabilities": [
                {"type": "Text", "name": "authoritative_for",
                 "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                 "label": "Authoritative For", "value": "senrep"},
            ],
        }
    ],
    "contacts": [
        {"role": "http://sensorml.com/ont/swe/property/Operator",
         "organisationName": "OS4CSAPI Demo"},
        {"role": "http://sensorml.com/ont/swe/property/ProjectLeader",
         "organisationName": "OS4CSAPI Project",
         "contactInfo": {"website": "https://github.com/OS4CSAPI"}},
    ],
    "documents": [
        {
            "role": "http://dbpedia.org/resource/Web_page",
            "name": "SENREP Workflow Note",
            "description": (
                "UAS/Localizer/SENREP Implementation Ready Pack \u2014 includes "
                "SENREP workflow documentation, doctrine crosswalk, and "
                "implementation guidance."
            ),
            "link": {
                "href": "https://github.com/OS4CSAPI/ogc-csapi-explorer/tree/main/docs/uas-localizer-senrep-pack",
                "type": "text/html",
            },
        },
        {
            "role": "http://dbpedia.org/resource/Diagram",
            "name": "SENREP Workflow Diagram",
            "description": (
                "Diagram showing the SENREP creation workflow from detection "
                "through formal report issuance."
            ),
            "link": {
                "href": "https://raw.githubusercontent.com/OS4CSAPI/ogc-csapi-explorer/main/docs/uas-localizer-senrep-pack/14_DIAGRAMS/senrep_workflow.svg",
                "type": "image/svg+xml",
            },
        },
    ],
}

SYSTEM_MONSITE_SML = {
    "type": "PhysicalSystem",
    "uniqueId": SYS_MONSITE_UID,  # server UID (not template UID)
    "definition": "sosa:System",
    "label": "Monitoring Site 001",
    "description": (
        "Monitoring site responsible for receiving sensor activations, "
        "supporting analysis, and facilitating rapid sensor-derived reporting."
    ),
    "keywords": [
        "monitoring site", "dissemination", "sensor management",
        "analysis support", "Ft Huachuca",
    ],
    "identifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/ShortName",
         "label": "Short Name", "value": "Monitoring Site 001"},
        {"definition": "http://sensorml.com/ont/swe/property/LongName",
         "label": "Long Name",
         "value": "Monitoring Site 001 \u2014 Ft Huachuca"},
    ],
    "classifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/SensorType",
         "label": "System Kind", "value": "Monitoring Site"},
        {"definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
         "label": "Role Type", "value": "Monitoring and Dissemination"},
    ],
    "validTime": [VALID_TIME_SML, ".."],
    "contacts": [
        {"role": "http://sensorml.com/ont/swe/property/ProjectLeader",
         "organisationName": "OS4CSAPI Project",
         "contactInfo": {"website": "https://github.com/OS4CSAPI"}},
    ],
    "documents": [
        {
            "role": "http://dbpedia.org/resource/Web_page",
            "name": "Monitoring Site Responsibilities",
            "description": (
                "UAS/Localizer/SENREP Implementation Ready Pack \u2014 includes "
                "monitoring site role documentation and responsibilities."
            ),
            "link": {
                "href": "https://github.com/OS4CSAPI/ogc-csapi-explorer/tree/main/docs/uas-localizer-senrep-pack",
                "type": "text/html",
            },
        }
    ],
}

SYSTEM_RELAY_SML = {
    "type": "PhysicalSystem",
    "uniqueId": SYS_RELAY_UID,  # server UID (not template UID)
    "definition": "sosa:System",
    "label": "Relay",
    "description": (
        "Communications relay / repeater support system used to bridge or "
        "extend connectivity between remote sensing elements and "
        "monitoring/reporting elements."
    ),
    "keywords": [
        "relay", "repeater", "communications", "bridge",
        "support infrastructure", "sensor network", "Ft Huachuca",
    ],
    "identifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/ShortName",
         "label": "Short Name", "value": "Relay"},
        {"definition": "http://sensorml.com/ont/swe/property/LongName",
         "label": "Long Name",
         "value": "Communications Relay \u2014 Ft Huachuca"},
        {"definition": "http://sensorml.com/ont/swe/property/Manufacturer",
         "label": "Manufacturer", "value": "REPLACE_IF_KNOWN"},
        {"definition": "http://sensorml.com/ont/swe/property/ModelNumber",
         "label": "Model", "value": "REPLACE_IF_KNOWN"},
        {"definition": "http://sensorml.com/ont/swe/property/SerialNumber",
         "label": "Asset Tag", "value": "REPLACE_IF_KNOWN"},
    ],
    "classifiers": [
        {"definition": "http://sensorml.com/ont/swe/property/SensorType",
         "label": "System Kind", "value": "Communications Relay"},
        {"definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
         "label": "Role Type", "value": "Relay Support"},
        {"definition": "http://sensorml.com/ont/swe/property/SystemRole",
         "label": "System Role",
         "value": "Relay / Repeater \u2014 Sensor-to-Monsite Bridge"},
    ],
    "validTime": [VALID_TIME_SML, ".."],
    "capabilities": [
        {
            "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
            "label": "Relay Capabilities",
            "capabilities": [
                {"type": "Text", "name": "purpose",
                 "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                 "label": "Purpose",
                 "value": (
                     "Provide relay/repeater communications support within "
                     "the deployed remote sensor network architecture."
                 )},
                {"type": "Text", "name": "status",
                 "definition": "http://sensorml.com/ont/swe/property/OperationalStatus",
                 "label": "Operational Status", "value": "active-demo"},
            ],
        }
    ],
    "contacts": [
        {"role": "http://sensorml.com/ont/swe/property/Operator",
         "organisationName": "OS4CSAPI Demo"},
        {"role": "http://sensorml.com/ont/swe/property/ProjectLeader",
         "organisationName": "OS4CSAPI Project",
         "contactInfo": {"website": "https://github.com/OS4CSAPI"}},
    ],
    "documents": [
        {
            "role": "http://dbpedia.org/resource/Web_page",
            "name": "Relay Support Role Note",
            "description": (
                "Relay-Only Patch Pack \u2014 guidance on relay role, structural "
                "semantics, and enrichment within the deployed sensor architecture."
            ),
            "link": {
                "href": "https://github.com/OS4CSAPI/ogc-csapi-explorer/tree/main/docs/uas-localizer-senrep-pack/relay-patch",
                "type": "text/html",
            },
        }
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — DataStreams
#
#  obsFormat: application/om+json
#  Timestamp: sensorml.com SamplingTime + epoch seconds + referenceTime
# ═══════════════════════════════════════════════════════════════════════════

DATASTREAM_LOCATION_ESTIMATE = {
    "name": "Location Estimate",
    "outputName": DS_LOC_OUTPUT,
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "name": "locationEstimate",
            "label": "Location Estimate",
            "description": (
                "String-level localizer output representing weighted "
                "least-squares position estimates from contributing LOBs."
            ),
            "fields": [
                {"type": "Time", "name": "timestamp",
                 "definition": "http://sensorml.com/ont/swe/property/SamplingTime",
                 "label": "Sampling Time",
                 "referenceTime": "1970-01-01T00:00:00Z",
                 "uom": {"code": "s"}},
                {"type": "Count", "name": "trackId",
                 "definition": "http://sensorml.com/ont/swe/property/Identifier",
                 "label": "Track ID"},
                {"type": "Quantity", "name": "estimatedLat",
                 "definition": "http://qudt.org/vocab/quantitykind/Latitude",
                 "label": "Estimated Latitude",
                 "description": "WLS-computed geodetic latitude (WGS-84)",
                 "uom": {"code": "deg"}},
                {"type": "Quantity", "name": "estimatedLon",
                 "definition": "http://qudt.org/vocab/quantitykind/Longitude",
                 "label": "Estimated Longitude",
                 "description": "WLS-computed geodetic longitude (WGS-84)",
                 "uom": {"code": "deg"}},
                {"type": "Quantity", "name": "cep50_m",
                 "definition": "http://qudt.org/vocab/quantitykind/Length",
                 "label": "CEP50",
                 "description": "Circular Error Probable (50th percentile) of the location estimate",
                 "uom": {"code": "m"}},
                {"type": "Text", "name": "classification",
                 "definition": "http://sensorml.com/ont/swe/property/Classification",
                 "label": "Classification"},
                {"type": "Count", "name": "numContributingLobs",
                 "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                 "label": "Number of Contributing LOBs"},
                {"type": "Text", "name": "contributingSensors",
                 "definition": "http://sensorml.com/ont/swe/property/DataSource",
                 "label": "Contributing Sensors",
                 "description": "Comma-separated list of sensor IDs that contributed LOBs"},
                {"type": "Quantity", "name": "residual_m",
                 "definition": "http://qudt.org/vocab/quantitykind/Length",
                 "label": "Residual",
                 "description": "WLS residual error metric in meters",
                 "uom": {"code": "m"}},
                {"type": "Text", "name": "contributingLobsJson",
                 "definition": "http://sensorml.com/ont/swe/property/DataPayload",
                 "label": "Contributing LOBs (JSON)",
                 "description": "JSON-encoded array of contributing LOB details"},
            ],
        },
    },
}

DATASTREAM_SENREP_V1_1 = {
    "name": "SENREP v1.1",
    "outputName": DS_SENREP_OUTPUT,
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "name": "SENREP",
            "label": "Sensor Report",
            "description": (
                "Formal sensor report datastream owned by SET-A. Supports "
                "doctrinal reporting fields plus identity/provenance enrichments."
            ),
            "fields": [
                {"type": "Time", "name": "timestamp",
                 "definition": "http://sensorml.com/ont/swe/property/SamplingTime",
                 "label": "Sampling Time",
                 "referenceTime": "1970-01-01T00:00:00Z",
                 "uom": {"code": "s"}},
                {"type": "Text", "name": "title",
                 "definition": "http://sensorml.com/ont/swe/property/ShortName",
                 "label": "Report Title"},
                {"type": "Text", "name": "senderId",
                 "definition": "http://sensorml.com/ont/swe/property/Identifier",
                 "label": "Sender ID"},
                {"type": "Count", "name": "seqNo",
                 "definition": "http://sensorml.com/ont/swe/property/SequenceNumber",
                 "label": "Sequence Number"},
                {"type": "Text", "name": "contactId",
                 "definition": "http://sensorml.com/ont/swe/property/Identifier",
                 "label": "Contact ID",
                 "description": "Authoritative join key for tracking/reporting"},
                {"type": "Text", "name": "classification",
                 "definition": "http://sensorml.com/ont/swe/property/Classification",
                 "label": "Classification"},
                {"type": "Text", "name": "releasably",
                 "definition": "http://sensorml.com/ont/swe/property/Classification",
                 "label": "Releasability"},
                {"type": "Text", "name": "dor",
                 "label": "Date of Report",
                 "description": "DTG of report (DDMMYY format)"},
                {"type": "Text", "name": "envirOpName",
                 "label": "Operation Name",
                 "description": "Named operation or exercise identifier"},
                {"type": "Text", "name": "strNo",
                 "label": "String Number",
                 "description": "String/sensor array identifier"},
                {"type": "Text", "name": "detectTimeZ",
                 "label": "Detection Time (Zulu)",
                 "description": "Time of initial detection in Zulu (HHMM format)"},
                {"type": "Count", "name": "qty",
                 "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                 "label": "Quantity",
                 "description": "Number of targets observed"},
                {"type": "Category", "name": "tgtTyp",
                 "label": "Target Type",
                 "description": "Doctrinal target type category (e.g., UAS, DISMOUNT, VEHICLE)"},
                {"type": "Text", "name": "subTyp",
                 "label": "Sub-Type",
                 "description": "Target sub-type detail"},
                {"type": "Quantity", "name": "spd",
                 "definition": "http://qudt.org/vocab/quantitykind/Speed",
                 "label": "Speed", "uom": {"code": "km/h"}},
                {"type": "Category", "name": "dirCardinal",
                 "label": "Direction (Cardinal)",
                 "description": "Cardinal or inter-cardinal direction of movement"},
                {"type": "Quantity", "name": "colLengthM",
                 "definition": "http://qudt.org/vocab/quantitykind/Length",
                 "label": "Column Length",
                 "description": "Length of the detected target formation/column",
                 "uom": {"code": "m"}},
                {"type": "Quantity", "name": "etaLat",
                 "definition": "http://qudt.org/vocab/quantitykind/Latitude",
                 "label": "Estimated Latitude", "uom": {"code": "deg"}},
                {"type": "Quantity", "name": "etaLon",
                 "definition": "http://qudt.org/vocab/quantitykind/Longitude",
                 "label": "Estimated Longitude", "uom": {"code": "deg"}},
                {"type": "Quantity", "name": "posErrorM",
                 "definition": "http://qudt.org/vocab/quantitykind/Length",
                 "label": "Position Error",
                 "description": "Estimated position error in meters",
                 "uom": {"code": "m"}},
                {"type": "Text", "name": "etaTimeZ",
                 "label": "ETA Time (Zulu)",
                 "description": "Estimated time of activity in Zulu"},
                {"type": "Text", "name": "sourceFixObsId",
                 "definition": "http://sensorml.com/ont/swe/property/Identifier",
                 "label": "Source Fix Observation ID",
                 "description": "Reference to the localizer fix observation that triggered this SENREP"},
                {"type": "Text", "name": "sourceLobObsIds",
                 "definition": "http://sensorml.com/ont/swe/property/Identifier",
                 "label": "Source LOB Observation IDs",
                 "description": "Comma-separated list of contributing LOB observation IDs"},
                {"type": "Quantity", "name": "confidence",
                 "definition": "http://sensorml.com/ont/swe/property/QualityIndex",
                 "label": "Confidence",
                 "description": "Operator confidence level (0-1)",
                 "uom": {"code": "1"}},
                {"type": "Text", "name": "comments",
                 "label": "Comments",
                 "description": "Free-text operator comments"},
            ],
        },
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  Resource definitions — Deployment leaf
# ═══════════════════════════════════════════════════════════════════════════

DEPLOYMENT_LOCALIZER_FEED = {
    "uid": DEPLOY_LOCALIZER_FEED_UID,
    "name": "String Alpha Localizer Feed",
    "description": (
        "Leaf deployment representing the string-level localizer fusion "
        "capability for String Alpha."
    ),
    "geometry": None,
    "platform_link_sys_uid": SYS_LOCALIZER_UID,
    "platform_link_title": "AZ String Alpha Localizer",
}

# UIDs for clean teardown (only resources this script creates)
CLEAN_DEPLOYMENT_UIDS = [
    DEPLOY_LOCALIZER_FEED_UID,
]

# ═══════════════════════════════════════════════════════════════════════════
#  Networking — DNS override + SSL + Auth
# ═══════════════════════════════════════════════════════════════════════════

_real_getaddrinfo = socket.getaddrinfo


def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "os4csapi-osh.duckdns.org":
        return _real_getaddrinfo(ORACLE_IP, port, *args, **kwargs)
    return _real_getaddrinfo(host, port, *args, **kwargs)


socket.getaddrinfo = _patched_getaddrinfo

_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

_AUTH_HEADER = "Basic " + base64.b64encode(
    f"{AUTH_USER}:{AUTH_PASS}".encode()
).decode()

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


# ═══════════════════════════════════════════════════════════════════════════
#  HTTP helpers
# ═══════════════════════════════════════════════════════════════════════════

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
    """PUT (update) a resource.  Returns True on success."""
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
    """Find a resource by UID in a collection.  Returns server ID or None."""
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
#  Clean helpers — only deletes resources THIS script creates
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
            _uid_cache.pop(f"{collection}:{uid}", None)
        except Exception as e:
            print(f"  ERROR deleting {collection}/{existing_id}: {e}")
            stats["errors"] += 1
    else:
        stats["deleted"] += 1


def clean_all(stats: dict, dry_run: bool):
    """Delete resources created by this script (safe order)."""
    print("\n\u2500\u2500 Clean: Deployment leaves \u2500\u2500")
    for uid in CLEAN_DEPLOYMENT_UIDS:
        clean_resource("deployments", uid, stats, dry_run)

    print("\n\u2500\u2500 Clean: DataStreams \u2500\u2500")
    # DataStreams via parent system
    for sys_uid, output_name in [
        (SYS_LOCALIZER_UID, DS_LOC_OUTPUT),
        (SYS_SETA_UID, DS_SENREP_OUTPUT),
    ]:
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

    # NOTE: We do NOT delete the 4 systems (they were pre-existing)
    # NOTE: We do NOT delete the WLS procedure (pre-existing)

    print("\n\u2500\u2500 Clean: Procedures \u2500\u2500")
    clean_resource("procedures", PROC_SENREP_UID, stats, dry_run)


# ═══════════════════════════════════════════════════════════════════════════
#  Bootstrap logic
# ═══════════════════════════════════════════════════════════════════════════

def bootstrap(clean: bool = False, clean_only: bool = False, dry_run: bool = False):
    stats = {"created": 0, "skipped": 0, "deleted": 0, "patched": 0, "errors": 0}

    # ── Clean phase ──────────────────────────────────────────────────
    if clean or clean_only:
        print("\n" + "=" * 60)
        print("  CLEAN PHASE \u2014 deleting UAS-specific resources")
        print("=" * 60)
        clean_all(stats, dry_run)
        if clean_only:
            _print_summary(stats, dry_run)
            return stats

    # ── Phase 1: Procedures ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 1: Procedures")
    print("=" * 60)

    # WLS Triangulation — expect it to exist
    existing = find_by_uid("procedures", PROC_WLS_UID)
    if existing:
        print(f"  \u2713 WLS LOB Triangulation v1 already exists: {existing}")
        stats["skipped"] += 1
    else:
        print(f"  WARNING: WLS procedure not found — it should already exist!")
        stats["errors"] += 1

    # SENREP SOP — create if missing
    existing = find_by_uid("procedures", PROC_SENREP_UID)
    if existing:
        print(f"  \u2713 SENREP SOP v1 already exists: {existing}")
        stats["skipped"] += 1
    else:
        print(f"  POST procedure: SENREP SOP v1")
        if not dry_run:
            result = api_post("procedures", PROCEDURE_SENREP_SOP,
                              content_type="application/geo+json")
            pid = result["id"]
            _uid_cache[f"procedures:{PROC_SENREP_UID}"] = pid
            print(f"  \u2713 Created: {pid}")
            stats["created"] += 1
        else:
            print(f"  (dry-run) Would create procedure: {PROC_SENREP_UID}")
            stats["created"] += 1

    # ── Phase 2: Systems (SML enrichment — all 4 exist) ─────────────
    print("\n" + "=" * 60)
    print("  PHASE 2: Systems (SensorML enrichment)")
    print("=" * 60)

    sys_ids = {}
    for sml_body, sys_uid, label in [
        (SYSTEM_LOCALIZER_SML, SYS_LOCALIZER_UID, "AZ String Alpha Localizer"),
        (SYSTEM_SETA_SML, SYS_SETA_UID, "SET-A"),
        (SYSTEM_MONSITE_SML, SYS_MONSITE_UID, "Monitoring Site 001"),
        (SYSTEM_RELAY_SML, SYS_RELAY_UID, "Relay"),
    ]:
        existing_id = find_by_uid("systems", sys_uid)
        if existing_id:
            print(f"  \u2713 {label} exists: {existing_id}")
            sys_ids[sys_uid] = existing_id

            # Query the system's current validTime so the PUT updates
            # the existing version instead of creating a new one.
            current_vt = None
            if not dry_run:
                sys_info = api_get(f"systems/{existing_id}")
                if sys_info:
                    props = sys_info.get("properties", sys_info)
                    current_vt = props.get("validTime")

            if current_vt:
                sml_body = {**sml_body, "validTime": current_vt}
                print(f"    validTime matched to existing: {current_vt[0]}")

            print(f"    PUT SensorML enrichment...")
            if not dry_run:
                try:
                    api_put(f"systems/{existing_id}", sml_body)
                    print(f"    \u2713 SensorML metadata applied")
                    stats["patched"] += 1
                except RuntimeError as e:
                    print(f"    ERROR applying SensorML: {e}")
                    stats["errors"] += 1
            else:
                print(f"    (dry-run) Would PUT SensorML")
                stats["patched"] += 1
        else:
            print(f"  WARNING: {label} ({sys_uid}) not found on server!")
            print(f"    This system should have been created during MA bootstrap.")
            stats["errors"] += 1

    # ── Phase 3: DataStreams (additive — new outputNames) ────────────
    print("\n" + "=" * 60)
    print("  PHASE 3: DataStreams (additive)")
    print("=" * 60)

    for ds_def, sys_uid, output_name, label in [
        (DATASTREAM_LOCATION_ESTIMATE, SYS_LOCALIZER_UID, DS_LOC_OUTPUT,
         "Location Estimate (10-field)"),
        (DATASTREAM_SENREP_V1_1, SYS_SETA_UID, DS_SENREP_OUTPUT,
         "SENREP v1.1 (25-field)"),
    ]:
        sys_id = sys_ids.get(sys_uid)
        if not sys_id:
            print(f"  SKIP {label} \u2014 parent system not found")
            stats["errors"] += 1
            continue

        existing_ds = find_datastream(sys_id, output_name)
        if existing_ds:
            ds_id = existing_ds.get("id")
            print(f"  \u2713 {label} already exists: {ds_id}")
            stats["skipped"] += 1
        else:
            print(f"  POST datastream: {label} under system {sys_id}")
            if not dry_run:
                try:
                    result = api_post(f"systems/{sys_id}/datastreams", ds_def)
                    ds_id = result["id"]
                    print(f"  \u2713 Created: {ds_id}")
                    stats["created"] += 1
                except RuntimeError as e:
                    print(f"  ERROR creating datastream: {e}")
                    stats["errors"] += 1
            else:
                print(f"  (dry-run) Would create datastream: {output_name}")
                stats["created"] += 1

    # ── Phase 4: Deployment leaves ───────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE 4: Deployment Leaves")
    print("=" * 60)

    # 4a: Localizer Feed leaf → under String Alpha
    loc_feed = DEPLOYMENT_LOCALIZER_FEED
    existing_dep = find_by_uid("deployments", loc_feed["uid"])
    if existing_dep:
        print(f"  \u2713 Localizer Feed already exists: {existing_dep}")
        stats["skipped"] += 1
    else:
        parent_id = find_by_uid("deployments", DEPLOY_STRING_ALPHA_UID)
        if not parent_id:
            print(f"  ERROR: Parent deployment String Alpha ({DEPLOY_STRING_ALPHA_UID}) not found")
            stats["errors"] += 1
        else:
            # Resolve platform@link
            localizer_sys_id = sys_ids.get(SYS_LOCALIZER_UID)
            if not localizer_sys_id and not dry_run:
                print(f"  ERROR: Localizer system not found for platform@link")
                stats["errors"] += 1
            else:
                body = {
                    "type": "Feature",
                    "geometry": loc_feed["geometry"],
                    "properties": {
                        "uid": loc_feed["uid"],
                        "featureType": "sosa:Deployment",
                        "name": loc_feed["name"],
                        "description": loc_feed["description"],
                        "validTime": [VALID_TIME_START, ".."],
                        "platform@link": {
                            "href": f"/sensorhub/api/systems/{localizer_sys_id or 'DRY'}",
                            "title": loc_feed["platform_link_title"],
                            "uid": loc_feed["platform_link_sys_uid"],
                            "type": "application/sml+json",
                        },
                    },
                }

                post_path = f"deployments/{parent_id}/subdeployments"
                print(f"  POST Localizer Feed \u2192 {post_path}")
                if not dry_run:
                    try:
                        result = api_post(post_path, body,
                                          content_type="application/geo+json")
                        new_id = result["id"]
                        _uid_cache[f"deployments:{loc_feed['uid']}"] = new_id
                        print(f"  \u2713 Created: {new_id}")
                        stats["created"] += 1
                    except RuntimeError as e:
                        print(f"  ERROR: {e}")
                        stats["errors"] += 1
                else:
                    print(f"  (dry-run) Would create deployment leaf")
                    stats["created"] += 1

    # 4b: Relay Emplacement — expect it to exist already
    existing_relay_dep = find_by_uid("deployments", DEPLOY_RELAY_UID)
    if existing_relay_dep:
        print(f"  \u2713 Relay Emplacement already exists: {existing_relay_dep}")
        stats["skipped"] += 1
    else:
        print(f"  WARNING: Relay deployment ({DEPLOY_RELAY_UID}) not found!")
        print(f"    It should have been created during MA bootstrap.")
        stats["errors"] += 1

    # ── Summary ──────────────────────────────────────────────────────
    _print_summary(stats, dry_run)

    if not dry_run:
        print("\n  Resource Summary:")
        print("  " + "-" * 50)

        # Procedures
        for label, uid in [
            ("Proc WLS Triangulation", PROC_WLS_UID),
            ("Proc SENREP SOP", PROC_SENREP_UID),
        ]:
            rid = find_by_uid("procedures", uid)
            print(f"    {label:30s} {rid or 'NOT FOUND'}")

        # Systems
        for label, uid in [
            ("Sys Localizer", SYS_LOCALIZER_UID),
            ("Sys SET-A", SYS_SETA_UID),
            ("Sys Monitoring Site", SYS_MONSITE_UID),
            ("Sys Relay", SYS_RELAY_UID),
        ]:
            rid = find_by_uid("systems", uid)
            print(f"    {label:30s} {rid or 'NOT FOUND'}")

        # DataStreams
        loc_sys = sys_ids.get(SYS_LOCALIZER_UID)
        if loc_sys:
            ds = find_datastream(loc_sys, DS_LOC_OUTPUT)
            print(f"    {'DS Location Estimate':30s} {ds.get('id') if ds else 'NOT FOUND'}")
        seta_sys = sys_ids.get(SYS_SETA_UID)
        if seta_sys:
            ds = find_datastream(seta_sys, DS_SENREP_OUTPUT)
            print(f"    {'DS SENREP v1.1':30s} {ds.get('id') if ds else 'NOT FOUND'}")

        # Deployments
        for label, uid in [
            ("Deploy Localizer Feed", DEPLOY_LOCALIZER_FEED_UID),
            ("Deploy Relay Emplacement", DEPLOY_RELAY_UID),
        ]:
            rid = find_by_uid("deployments", uid)
            print(f"    {label:30s} {rid or 'NOT FOUND'}")

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
        description="Bootstrap UAS/Localizer/SENREP resources on the OS4CSAPI server")
    parser.add_argument("--clean", action="store_true",
                        help="Delete UAS-specific resources then recreate")
    parser.add_argument("--clean-only", action="store_true",
                        help="Delete UAS-specific resources only (teardown)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without executing")
    args = parser.parse_args()

    print("=" * 60)
    print("  OS4CSAPI \u2014 UAS/Localizer/SENREP Bootstrap")
    print("=" * 60)
    print(f"  Server:     {BASE_URL}")
    print(f"  Procedures: {PROC_WLS_UID} (exists)")
    print(f"              {PROC_SENREP_UID} (create)")
    print(f"  Systems:    {SYS_LOCALIZER_UID}")
    print(f"              {SYS_SETA_UID}")
    print(f"              {SYS_MONSITE_UID}")
    print(f"              {SYS_RELAY_UID}")
    print(f"  DataStreams: {DS_LOC_OUTPUT}, {DS_SENREP_OUTPUT}")
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
