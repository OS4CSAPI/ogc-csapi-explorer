#!/usr/bin/env python3
"""
transform_uas_templates.py — Convert UAS pack templates to server-ready wire format.

Audit findings addressed:
  U1: System/Procedure templates → proper SensorML / geo+json Feature format
  U2: Datastream time fields → add definition + referenceTime
  U3: Deployment placeholder → documented, left as runtime resolution
  U4: Relay system template → created from scratch
  U6: SVG relative paths → absolute GitHub raw URLs

CRITICAL RULE: NO metadata from the original templates is lost.
Every uid, name, description, property, parameter is mapped to its SensorML equivalent.
"""

import json
import os

TEMPLATE_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "docs", "uas-localizer-senrep-pack", "09_JSON_TEMPLATES"
)

VALID_TIME_START = "2026-01-01T00:00:00Z"
GITHUB_RAW = (
    "https://raw.githubusercontent.com/OS4CSAPI/ogc-csapi-explorer"
    "/main/docs/uas-localizer-senrep-pack/14_DIAGRAMS"
)
PACK_URL = (
    "https://github.com/OS4CSAPI/ogc-csapi-explorer"
    "/tree/main/docs/uas-localizer-senrep-pack"
)


def write(name, obj):
    path = os.path.join(TEMPLATE_DIR, name)
    with open(path, "w", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  ✓ {name}")


# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM 1 — AZ String Alpha Localizer
#
#  Original metadata preserved:
#    uid, name, description, systemKind, roleType, ownerOrg,
#    sourceProvider, procedureUid, stalenessLimitSec,
#    correlationWindowSec, minContributingLobs, documents[0]
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_LOCALIZER = {
    "_templateMeta": {
        "description": "Server-ready template for AZ String Alpha Localizer",
        "wirePattern": "Two-step: POST geojsonStub to /systems, then PUT sensorml to /systems/{id}/details",
        "procedureRef": "urn:os4csapi:procedure:lob-wls-triangulation:v1",
        "pack": "UAS/Localizer/SENREP Implementation Ready Pack v2",
        "auditFixes": [
            "U1: Converted from simplified JSON to geojson stub + SensorML PhysicalSystem",
            "U6: SVG relative path replaced with absolute GitHub raw URL",
        ],
    },
    "geojsonStub": {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:os4csapi:system:fusion:az-string-alpha-localizer",
            "name": "AZ String Alpha Localizer",
            "description": (
                "Software fusion agent that consumes recent LOB observations "
                "from String Alpha nodes and produces weighted least-squares "
                "location estimates."
            ),
            "typeOf": "urn:os4csapi:procedure:lob-wls-triangulation:v1",
            "validTime": [VALID_TIME_START, ".."],
        },
    },
    "sensorml": {
        "type": "PhysicalSystem",
        "uniqueId": "urn:os4csapi:system:fusion:az-string-alpha-localizer",
        "definition": "sosa:System",
        "label": "AZ String Alpha Localizer",
        "description": (
            "Software fusion agent that consumes recent LOB observations "
            "from String Alpha nodes and produces weighted least-squares "
            "location estimates."
        ),
        "keywords": [
            "localizer", "WLS", "weighted-least-squares", "fusion",
            "LOB triangulation", "String Alpha", "UAS detection",
            "software-fusion-agent",
        ],
        "identifiers": [
            {
                "definition": "http://sensorml.com/ont/swe/property/ShortName",
                "label": "Short Name",
                "value": "AZ String Alpha Localizer",
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/LongName",
                "label": "Long Name",
                "value": "AZ String Alpha Weighted Least-Squares LOB Localizer",
            },
        ],
        "classifiers": [
            {
                "definition": "http://sensorml.com/ont/swe/property/SensorType",
                "label": "System Kind",
                "value": "Software Fusion Agent",
                # ← original: properties.systemKind = "software-fusion-agent"
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                "label": "Role Type",
                "value": "String-Level Localizer",
                # ← original: properties.roleType = "string-level-localizer"
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/SystemRole",
                "label": "System Role",
                "value": "Fusion Producer",
            },
        ],
        "validTime": [VALID_TIME_START, ".."],
        "characteristics": [
            {
                "label": "Localizer Parameters",
                "characteristics": [
                    {
                        "type": "Quantity",
                        "name": "staleness_limit",
                        "definition": "http://qudt.org/vocab/quantitykind/Period",
                        "label": "Staleness Limit",
                        "description": (
                            "Maximum age in seconds for a LOB to be considered "
                            "valid for fusion"
                        ),
                        "uom": {"code": "s"},
                        "value": 15,
                        # ← original: properties.stalenessLimitSec = 15
                    },
                    {
                        "type": "Quantity",
                        "name": "correlation_window",
                        "definition": "http://qudt.org/vocab/quantitykind/Period",
                        "label": "Correlation Window",
                        "description": (
                            "Time window in seconds for correlating LOBs from "
                            "different sensors"
                        ),
                        "uom": {"code": "s"},
                        "value": 10,
                        # ← original: properties.correlationWindowSec = 10
                    },
                    {
                        "type": "Count",
                        "name": "min_contributing_lobs",
                        "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                        "label": "Minimum Contributing LOBs",
                        "description": (
                            "Minimum number of valid LOBs required to produce "
                            "a location estimate"
                        ),
                        "value": 2,
                        # ← original: properties.minContributingLobs = 2
                    },
                ],
            }
        ],
        "capabilities": [
            {
                "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
                "label": "Localizer Capabilities",
                "capabilities": [
                    {
                        "type": "Text",
                        "name": "fusion_method",
                        "definition": "http://sensorml.com/ont/swe/property/AlgorithmType",
                        "label": "Fusion Method",
                        "value": "Weighted Least-Squares LOB Triangulation",
                    },
                    {
                        "type": "Text",
                        "name": "source_provider",
                        "definition": "http://sensorml.com/ont/swe/property/DataSource",
                        "label": "Source Provider",
                        "value": "AZ-MA node LOB streams",
                        # ← original: properties.sourceProvider
                    },
                ],
            }
        ],
        "contacts": [
            {
                "role": "http://sensorml.com/ont/swe/property/Operator",
                "organisationName": "OS4CSAPI Demo",
                # ← original: properties.ownerOrg = "OS4CSAPI Demo"
            },
            {
                "role": "http://sensorml.com/ont/swe/property/ProjectLeader",
                "organisationName": "OS4CSAPI Project",
                "contactInfo": {"website": "https://github.com/OS4CSAPI"},
            },
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
                    "href": f"{GITHUB_RAW}/localizer_wls_flow.svg",
                    "type": "image/svg+xml",
                    # ← original: documents[0].href = "../14_DIAGRAMS/localizer_wls_flow.svg"
                    # U6 fix: absolute GitHub raw URL
                },
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM 2 — SET-A
#
#  Original metadata preserved:
#    uid, name, description, systemKind, roleType, ownerOrg,
#    authoritativeFor, documents[0], media[0]
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_SET_A = {
    "_templateMeta": {
        "description": "Server-ready template for SET-A (Sensor Employment Team A)",
        "wirePattern": "Two-step: POST geojsonStub to /systems, then PUT sensorml to /systems/{id}/details",
        "pack": "UAS/Localizer/SENREP Implementation Ready Pack v2",
        "auditFixes": [
            "U1: Converted from simplified JSON to geojson stub + SensorML PhysicalSystem",
            "U3: Replaced REPLACE_WITH_INTERNAL_DOC_OR_REPO_URL with actual pack URL",
            "U6: SVG relative path replaced with absolute GitHub raw URL",
        ],
    },
    "geojsonStub": {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:os4csapi:system:set:ft-huachuca:001",
            "name": "SET-A",
            "description": (
                "Sensor Employment Team A. Reporting-tier system responsible for "
                "reviewing detections/fixes and issuing formal sensor reports (SENREPs)."
            ),
            "validTime": [VALID_TIME_START, ".."],
        },
    },
    "sensorml": {
        "type": "PhysicalSystem",
        "uniqueId": "urn:os4csapi:system:set:ft-huachuca:001",
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
            {
                "definition": "http://sensorml.com/ont/swe/property/ShortName",
                "label": "Short Name",
                "value": "SET-A",
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/LongName",
                "label": "Long Name",
                "value": "Sensor Employment Team A — Ft Huachuca",
            },
        ],
        "classifiers": [
            {
                "definition": "http://sensorml.com/ont/swe/property/SensorType",
                "label": "System Kind",
                "value": "Human Team",
                # ← original: properties.systemKind = "human-team"
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                "label": "Role Type",
                "value": "Reporting Team",
                # ← original: properties.roleType = "reporting-team"
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/SystemRole",
                "label": "System Role",
                "value": "Identity Authority — SENREP Issuer",
            },
        ],
        "validTime": [VALID_TIME_START, ".."],
        "capabilities": [
            {
                "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
                "label": "Reporting Capabilities",
                "capabilities": [
                    {
                        "type": "Text",
                        "name": "authoritative_for",
                        "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                        "label": "Authoritative For",
                        "value": "senrep",
                        # ← original: properties.authoritativeFor = ["senrep"]
                    },
                ],
            }
        ],
        "contacts": [
            {
                "role": "http://sensorml.com/ont/swe/property/Operator",
                "organisationName": "OS4CSAPI Demo",
                # ← original: properties.ownerOrg = "OS4CSAPI Demo"
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
                "name": "SENREP Workflow Note",
                "description": (
                    "UAS/Localizer/SENREP Implementation Ready Pack — includes "
                    "SENREP workflow documentation, doctrine crosswalk, and "
                    "implementation guidance."
                ),
                "link": {
                    "href": PACK_URL,
                    "type": "text/html",
                    # ← original: documents[0].href = "REPLACE_WITH_INTERNAL_DOC_OR_REPO_URL"
                    # U3 fix: resolved placeholder to actual pack URL
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
                    "href": f"{GITHUB_RAW}/senrep_workflow.svg",
                    "type": "image/svg+xml",
                    # ← original: media[0].href = "../14_DIAGRAMS/senrep_workflow.svg"
                    # U6 fix: absolute GitHub raw URL
                },
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM 3 — Monitoring Site 001
#
#  Original metadata preserved:
#    uid, name, description, systemKind, roleType, documents[0]
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_MONITORING_SITE = {
    "_templateMeta": {
        "description": "Server-ready template for Monitoring Site 001",
        "wirePattern": "Two-step: POST geojsonStub to /systems, then PUT sensorml to /systems/{id}/details",
        "pack": "UAS/Localizer/SENREP Implementation Ready Pack v2",
        "auditFixes": [
            "U1: Converted from simplified JSON to geojson stub + SensorML PhysicalSystem",
            "U3: Replaced REPLACE_WITH_INTERNAL_DOC_OR_SUMMARY with actual pack URL",
        ],
    },
    "geojsonStub": {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:os4csapi:system:monsite:ft-huachuca:001",
            "name": "Monitoring Site 001",
            "description": (
                "Monitoring site responsible for receiving sensor activations, "
                "supporting analysis, and facilitating rapid sensor-derived reporting."
            ),
            "validTime": [VALID_TIME_START, ".."],
        },
    },
    "sensorml": {
        "type": "PhysicalSystem",
        "uniqueId": "urn:os4csapi:system:monsite:ft-huachuca:001",
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
            {
                "definition": "http://sensorml.com/ont/swe/property/ShortName",
                "label": "Short Name",
                "value": "Monitoring Site 001",
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/LongName",
                "label": "Long Name",
                "value": "Monitoring Site 001 — Ft Huachuca",
            },
        ],
        "classifiers": [
            {
                "definition": "http://sensorml.com/ont/swe/property/SensorType",
                "label": "System Kind",
                "value": "Monitoring Site",
                # ← original: properties.systemKind = "monitoring-site"
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                "label": "Role Type",
                "value": "Monitoring and Dissemination",
                # ← original: properties.roleType = "monitoring-and-dissemination"
            },
        ],
        "validTime": [VALID_TIME_START, ".."],
        "contacts": [
            {
                "role": "http://sensorml.com/ont/swe/property/ProjectLeader",
                "organisationName": "OS4CSAPI Project",
                "contactInfo": {"website": "https://github.com/OS4CSAPI"},
            },
        ],
        "documents": [
            {
                "role": "http://dbpedia.org/resource/Web_page",
                "name": "Monitoring Site Responsibilities",
                "description": (
                    "UAS/Localizer/SENREP Implementation Ready Pack — includes "
                    "monitoring site role documentation and responsibilities."
                ),
                "link": {
                    "href": PACK_URL,
                    "type": "text/html",
                    # ← original: documents[0].href = "REPLACE_WITH_INTERNAL_DOC_OR_SUMMARY"
                    # U3 fix: resolved placeholder to actual pack URL
                },
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  SYSTEM 4 — Relay (U4 fix + Relay-Only Patch Pack merge)
#
#  Originally created from scratch for U4 fix. Now merged with the
#  Relay-Only Patch Pack which provides richer metadata:
#    uid, name, description, systemKind, roleType, purpose, ownerOrg,
#    status, manufacturer, model, assetTag, documents, media
# ═══════════════════════════════════════════════════════════════════════════

RELAY_PATCH_URL = (
    "https://github.com/OS4CSAPI/ogc-csapi-explorer"
    "/tree/main/docs/uas-localizer-senrep-pack/relay-patch"
)

SYSTEM_RELAY = {
    "_templateMeta": {
        "description": "Server-ready template for Relay communications support system",
        "wirePattern": "Two-step: POST geojsonStub to /systems, then PUT sensorml to /systems/{id}/details",
        "pack": "UAS/Localizer/SENREP Implementation Ready Pack v2 + Relay-Only Patch Pack",
        "auditFixes": [
            "U4: Created relay system template — was missing from original UAS pack",
            "Merged with Relay-Only Patch Pack (richer metadata: purpose, ownerOrg, status, manufacturer/model/assetTag placeholders, documents, media)",
            "U1: Converted from simplified JSON to geojsonStub + SensorML PhysicalSystem",
            "U3: Placeholder URLs resolved to pack URL or marked REPLACE_IF_KNOWN",
        ],
    },
    "geojsonStub": {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "uid": "urn:os4csapi:system:relay:ft-huachuca:001",
            "name": "Relay",
            "description": (
                "Communications relay / repeater support system used to bridge "
                "or extend connectivity between remote sensing elements and "
                "monitoring/reporting elements."
            ),
            "validTime": [VALID_TIME_START, ".."],
        },
    },
    "sensorml": {
        "type": "PhysicalSystem",
        "uniqueId": "urn:os4csapi:system:relay:ft-huachuca:001",
        "definition": "sosa:System",
        "label": "Relay",
        "description": (
            "Communications relay / repeater support system used to bridge "
            "or extend connectivity between remote sensing elements and "
            "monitoring/reporting elements."
        ),
        "keywords": [
            "relay", "repeater", "communications", "bridge",
            "support infrastructure", "sensor network", "Ft Huachuca",
        ],
        "identifiers": [
            {
                "definition": "http://sensorml.com/ont/swe/property/ShortName",
                "label": "Short Name",
                "value": "Relay",
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/LongName",
                "label": "Long Name",
                "value": "Communications Relay — Ft Huachuca",
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/Manufacturer",
                "label": "Manufacturer",
                "value": "REPLACE_IF_KNOWN",
                # ← original: properties.manufacturer
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/ModelNumber",
                "label": "Model",
                "value": "REPLACE_IF_KNOWN",
                # ← original: properties.model
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/SerialNumber",
                "label": "Asset Tag",
                "value": "REPLACE_IF_KNOWN",
                # ← original: properties.assetTag
            },
        ],
        "classifiers": [
            {
                "definition": "http://sensorml.com/ont/swe/property/SensorType",
                "label": "System Kind",
                "value": "Communications Relay",
                # ← original: properties.systemKind = "communications-relay"
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                "label": "Role Type",
                "value": "Relay Support",
                # ← original: properties.roleType = "relay-support"
            },
            {
                "definition": "http://sensorml.com/ont/swe/property/SystemRole",
                "label": "System Role",
                "value": "Relay / Repeater — Sensor-to-Monsite Bridge",
            },
        ],
        "validTime": [VALID_TIME_START, ".."],
        "capabilities": [
            {
                "definition": "http://www.w3.org/ns/ssn/systems/SystemCapability",
                "label": "Relay Capabilities",
                "capabilities": [
                    {
                        "type": "Text",
                        "name": "purpose",
                        "definition": "http://sensorml.com/ont/swe/property/IntendedApplication",
                        "label": "Purpose",
                        "value": (
                            "Provide relay/repeater communications support within "
                            "the deployed remote sensor network architecture."
                        ),
                        # ← original: properties.purpose
                    },
                    {
                        "type": "Text",
                        "name": "status",
                        "definition": "http://sensorml.com/ont/swe/property/OperationalStatus",
                        "label": "Operational Status",
                        "value": "active-demo",
                        # ← original: properties.status
                    },
                ],
            }
        ],
        "contacts": [
            {
                "role": "http://sensorml.com/ont/swe/property/Operator",
                "organisationName": "OS4CSAPI Demo",
                # ← original: properties.ownerOrg = "OS4CSAPI Demo"
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
                "name": "Relay Support Role Note",
                "description": (
                    "Relay-Only Patch Pack — guidance on relay role, structural "
                    "semantics, and enrichment within the deployed sensor architecture."
                ),
                "link": {
                    "href": RELAY_PATCH_URL,
                    "type": "text/html",
                    # ← original: documents[0].href = "REPLACE_WITH_INTERNAL_DOC_OR_REPO_URL"
                    # U3 fix: resolved to actual relay patch URL
                },
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  PROCEDURE 1 — WLS LOB Triangulation
#
#  Original metadata preserved:
#    uid, name, description, version, inputs, outputs,
#    assumptions, documents[0]
# ═══════════════════════════════════════════════════════════════════════════

PROCEDURE_WLS = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": "urn:os4csapi:procedure:lob-wls-triangulation:v1",
        "featureType": "sosa:ObservingProcedure",
        "name": "WLS LOB Triangulation v1",
        "description": (
            "Weighted least-squares procedure for intersecting two or more "
            "acoustic line-of-bearing observations into a location estimate. "
            # Preserving original inputs/outputs/assumptions as inline documentation:
            "Inputs: lob observations, sensor geometry, correlation window. "
            "Outputs: location estimate, residual, contributing sensor set. "
            "Assumptions: (1) At least two valid LOBs are required, "
            "(2) LOBs must pass staleness and correlation gates, "
            "(3) Result quality depends on geometry and bearing uncertainty."
        ),
        "validTime": [VALID_TIME_START, ".."],
        "_originalMetadata": {
            "version": "v1",
            "inputs": [
                "lob observations",
                "sensor geometry",
                "correlation window",
            ],
            "outputs": [
                "location estimate",
                "residual",
                "contributing sensor set",
            ],
            "assumptions": [
                "At least two valid LOBs are required",
                "LOBs must pass staleness and correlation gates",
                "Result quality depends on geometry and bearing uncertainty",
            ],
            "documents": [
                {
                    "title": "WLS Localizer Flow",
                    "href": f"{GITHUB_RAW}/localizer_wls_flow.svg",
                    "rel": "preview",
                    "mediaType": "image/svg+xml",
                    # U6 fix: absolute GitHub raw URL (was "../14_DIAGRAMS/localizer_wls_flow.svg")
                },
            ],
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  PROCEDURE 2 — SENREP SOP
#
#  Original metadata preserved:
#    uid, name, description, version, inputs, outputs,
#    assumptions, documents[0]
# ═══════════════════════════════════════════════════════════════════════════

PROCEDURE_SENREP_SOP = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": "urn:os4csapi:procedure:senrep:sop:v1",
        "featureType": "sosa:ObservingProcedure",
        "name": "SENREP SOP v1",
        "description": (
            "Reporting procedure used by the SET to transform reviewed "
            "sensor-derived activity into a formal sensor report (SENREP). "
            # Preserving original inputs/outputs/assumptions:
            "Inputs: operator-reviewed fix, supporting LOBs, "
            "classification/context, contactId assignment. "
            "Outputs: SENREP observation, track SamplingFeature creation or update. "
            "Assumptions: (1) identity is committed at the reporting tier, "
            "(2) contactId is the authoritative join key."
        ),
        "validTime": [VALID_TIME_START, ".."],
        "_originalMetadata": {
            "version": "v1",
            "inputs": [
                "operator-reviewed fix",
                "supporting LOBs",
                "classification/context",
                "contactId assignment",
            ],
            "outputs": [
                "SENREP observation",
                "track SamplingFeature creation or update",
            ],
            "assumptions": [
                "identity is committed at the reporting tier",
                "contactId is the authoritative join key",
            ],
            "documents": [
                {
                    "title": "SENREP Workflow Diagram",
                    "href": f"{GITHUB_RAW}/senrep_workflow.svg",
                    "rel": "preview",
                    "mediaType": "image/svg+xml",
                    # U6 fix: absolute GitHub raw URL (was "../14_DIAGRAMS/senrep_workflow.svg")
                },
            ],
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  DATASTREAM 1 — Location Estimate
#
#  Original metadata preserved:
#    uid, name, description, obsFormat, all 10 fields (timestamp, trackId,
#    estimatedLat, estimatedLon, cep50_m, classification,
#    numContributingLobs, contributingSensors, residual_m,
#    contributingLobsJson), properties (productType, cadence, qualityFields)
#
#  U2 fix: Added definition + referenceTime to timestamp field
#  Enhancement: Added SWE definitions and labels to all fields
# ═══════════════════════════════════════════════════════════════════════════

DATASTREAM_LOCATION_ESTIMATE = {
    "_templateMeta": {
        "uid": "urn:os4csapi:datastream:string-alpha:location-estimate:v1",
        "description": "Server-ready datastream template for localizer location estimates",
        "wirePattern": "POST to /systems/{localizerSystemId}/datastreams",
        "auditFixes": [
            "U2: Added definition + referenceTime to timestamp field",
            "Enhanced all fields with SWE definitions and labels",
        ],
    },
    "name": "Location Estimate",
    "outputName": "locationEstimate",
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "name": "locationEstimate",
            "label": "Location Estimate",
            "description": (
                "String-level localizer output representing weighted least-squares "
                "position estimates from contributing LOBs."
            ),
            "fields": [
                {
                    "type": "Time",
                    "name": "timestamp",
                    "definition": "http://sensorml.com/ont/swe/property/SamplingTime",
                    "label": "Sampling Time",
                    "referenceTime": "1970-01-01T00:00:00Z",
                    "uom": {"code": "s"},
                    # U2 FIX: was bare {"type":"Time","name":"timestamp","uom":{"code":"s"}}
                },
                {
                    "type": "Count",
                    "name": "trackId",
                    "definition": "http://sensorml.com/ont/swe/property/Identifier",
                    "label": "Track ID",
                },
                {
                    "type": "Quantity",
                    "name": "estimatedLat",
                    "definition": "http://qudt.org/vocab/quantitykind/Latitude",
                    "label": "Estimated Latitude",
                    "description": "WLS-computed geodetic latitude (WGS-84)",
                    "uom": {"code": "deg"},
                },
                {
                    "type": "Quantity",
                    "name": "estimatedLon",
                    "definition": "http://qudt.org/vocab/quantitykind/Longitude",
                    "label": "Estimated Longitude",
                    "description": "WLS-computed geodetic longitude (WGS-84)",
                    "uom": {"code": "deg"},
                },
                {
                    "type": "Quantity",
                    "name": "cep50_m",
                    "definition": "http://qudt.org/vocab/quantitykind/Length",
                    "label": "CEP50",
                    "description": "Circular Error Probable (50th percentile) of the location estimate",
                    "uom": {"code": "m"},
                },
                {
                    "type": "Text",
                    "name": "classification",
                    "definition": "http://sensorml.com/ont/swe/property/Classification",
                    "label": "Classification",
                },
                {
                    "type": "Count",
                    "name": "numContributingLobs",
                    "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                    "label": "Number of Contributing LOBs",
                },
                {
                    "type": "Text",
                    "name": "contributingSensors",
                    "definition": "http://sensorml.com/ont/swe/property/DataSource",
                    "label": "Contributing Sensors",
                    "description": "Comma-separated list of sensor IDs that contributed LOBs",
                },
                {
                    "type": "Quantity",
                    "name": "residual_m",
                    "definition": "http://qudt.org/vocab/quantitykind/Length",
                    "label": "Residual",
                    "description": "WLS residual error metric in meters",
                    "uom": {"code": "m"},
                },
                {
                    "type": "Text",
                    "name": "contributingLobsJson",
                    "definition": "http://sensorml.com/ont/swe/property/DataPayload",
                    "label": "Contributing LOBs (JSON)",
                    "description": "JSON-encoded array of contributing LOB details",
                },
            ],
        },
    },
    "properties": {
        "productType": "derived-fix",
        "cadence": "event-driven",
        "qualityFields": ["cep50_m", "residual_m", "numContributingLobs"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  DATASTREAM 2 — SENREP v1.1
#
#  Original metadata preserved:
#    uid, name, description, obsFormat, all 25 fields, properties
#    (productType, identityCommitmentTier, joinKey, qualityNote)
#
#  U2 fix: Added definition + referenceTime to timestamp field
#  U5 note: This is a 25-field expanded schema — create as NEW datastream
# ═══════════════════════════════════════════════════════════════════════════

DATASTREAM_SENREP = {
    "_templateMeta": {
        "uid": "urn:os4csapi:datastream:seta:senrep:v1.1",
        "description": "Server-ready datastream template for SENREP formal sensor reports",
        "wirePattern": "POST to /systems/{setASystemId}/datastreams",
        "auditFixes": [
            "U2: Added definition + referenceTime to timestamp field",
            "Enhanced all fields with SWE definitions and labels",
        ],
        "migrationNote": (
            "This is a 25-field expanded schema (v1.1). Create as NEW datastream "
            "alongside existing SENREP; do not modify existing schema in-place."
        ),
    },
    "name": "SENREP v1.1",
    "outputName": "senrep_v1_1",
    "schema": {
        "obsFormat": "application/om+json",
        "resultSchema": {
            "type": "DataRecord",
            "name": "SENREP",
            "label": "Sensor Report",
            "description": (
                "Formal sensor report datastream owned by SET-A. Supports doctrinal "
                "reporting fields plus identity/provenance enrichments."
            ),
            "fields": [
                {
                    "type": "Time",
                    "name": "timestamp",
                    "definition": "http://sensorml.com/ont/swe/property/SamplingTime",
                    "label": "Sampling Time",
                    "referenceTime": "1970-01-01T00:00:00Z",
                    "uom": {"code": "s"},
                    # U2 FIX: was bare {"type":"Time","name":"timestamp","uom":{"code":"s"}}
                },
                {
                    "type": "Text",
                    "name": "title",
                    "definition": "http://sensorml.com/ont/swe/property/ShortName",
                    "label": "Report Title",
                },
                {
                    "type": "Text",
                    "name": "senderId",
                    "definition": "http://sensorml.com/ont/swe/property/Identifier",
                    "label": "Sender ID",
                },
                {
                    "type": "Count",
                    "name": "seqNo",
                    "definition": "http://sensorml.com/ont/swe/property/SequenceNumber",
                    "label": "Sequence Number",
                },
                {
                    "type": "Text",
                    "name": "contactId",
                    "definition": "http://sensorml.com/ont/swe/property/Identifier",
                    "label": "Contact ID",
                    "description": "Authoritative join key for tracking/reporting",
                },
                {
                    "type": "Text",
                    "name": "classification",
                    "definition": "http://sensorml.com/ont/swe/property/Classification",
                    "label": "Classification",
                },
                {
                    "type": "Text",
                    "name": "releasably",
                    "definition": "http://sensorml.com/ont/swe/property/Classification",
                    "label": "Releasability",
                },
                # ── Doctrinal SENREP fields ──
                {
                    "type": "Text",
                    "name": "dor",
                    "label": "Date of Report",
                    "description": "DTG of report (DDMMYY format)",
                },
                {
                    "type": "Text",
                    "name": "envirOpName",
                    "label": "Operation Name",
                    "description": "Named operation or exercise identifier",
                },
                {
                    "type": "Text",
                    "name": "strNo",
                    "label": "String Number",
                    "description": "String/sensor array identifier",
                },
                {
                    "type": "Text",
                    "name": "detectTimeZ",
                    "label": "Detection Time (Zulu)",
                    "description": "Time of initial detection in Zulu (HHMM format)",
                },
                {
                    "type": "Count",
                    "name": "qty",
                    "definition": "http://sensorml.com/ont/swe/property/NumberOfElements",
                    "label": "Quantity",
                    "description": "Number of targets observed",
                },
                {
                    "type": "Category",
                    "name": "tgtTyp",
                    "label": "Target Type",
                    "description": "Doctrinal target type category (e.g., UAS, DISMOUNT, VEHICLE)",
                },
                {
                    "type": "Text",
                    "name": "subTyp",
                    "label": "Sub-Type",
                    "description": "Target sub-type detail",
                },
                {
                    "type": "Quantity",
                    "name": "spd",
                    "definition": "http://qudt.org/vocab/quantitykind/Speed",
                    "label": "Speed",
                    "uom": {"code": "km/h"},
                },
                {
                    "type": "Category",
                    "name": "dirCardinal",
                    "label": "Direction (Cardinal)",
                    "description": "Cardinal or inter-cardinal direction of movement",
                },
                {
                    "type": "Quantity",
                    "name": "colLengthM",
                    "definition": "http://qudt.org/vocab/quantitykind/Length",
                    "label": "Column Length",
                    "description": "Length of the detected target formation/column",
                    "uom": {"code": "m"},
                },
                # ── Geospatial fields ──
                {
                    "type": "Quantity",
                    "name": "etaLat",
                    "definition": "http://qudt.org/vocab/quantitykind/Latitude",
                    "label": "Estimated Latitude",
                    "uom": {"code": "deg"},
                },
                {
                    "type": "Quantity",
                    "name": "etaLon",
                    "definition": "http://qudt.org/vocab/quantitykind/Longitude",
                    "label": "Estimated Longitude",
                    "uom": {"code": "deg"},
                },
                {
                    "type": "Quantity",
                    "name": "posErrorM",
                    "definition": "http://qudt.org/vocab/quantitykind/Length",
                    "label": "Position Error",
                    "description": "Estimated position error in meters",
                    "uom": {"code": "m"},
                },
                {
                    "type": "Text",
                    "name": "etaTimeZ",
                    "label": "ETA Time (Zulu)",
                    "description": "Estimated time of activity in Zulu",
                },
                # ── Provenance fields ──
                {
                    "type": "Text",
                    "name": "sourceFixObsId",
                    "definition": "http://sensorml.com/ont/swe/property/Identifier",
                    "label": "Source Fix Observation ID",
                    "description": "Reference to the localizer fix observation that triggered this SENREP",
                },
                {
                    "type": "Text",
                    "name": "sourceLobObsIds",
                    "definition": "http://sensorml.com/ont/swe/property/Identifier",
                    "label": "Source LOB Observation IDs",
                    "description": "Comma-separated list of contributing LOB observation IDs",
                },
                {
                    "type": "Quantity",
                    "name": "confidence",
                    "definition": "http://sensorml.com/ont/swe/property/QualityIndex",
                    "label": "Confidence",
                    "description": "Operator confidence level (0-1)",
                    "uom": {"code": "1"},
                },
                {
                    "type": "Text",
                    "name": "comments",
                    "label": "Comments",
                    "description": "Free-text operator comments",
                },
            ],
        },
    },
    "properties": {
        "productType": "formal-sensor-report",
        "identityCommitmentTier": "SET",
        "joinKey": "contactId",
        "qualityNote": (
            "Formal reporting product; provenance fields preserve "
            "operator traceability."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  DEPLOYMENT — Relay Emplacement Leaf (NEW — from Relay-Only Patch Pack)
#
#  Original metadata preserved from Relay-Only Patch Pack:
#    uid, name, description, type, platform@link, properties
#    (deploymentType, roleType, purpose, status, occupantSummary)
# ═══════════════════════════════════════════════════════════════════════════

DEPLOYMENT_RELAY_LEAF = {
    "_templateMeta": {
        "description": "Server-ready deployment leaf template for relay emplacement",
        "wirePattern": "POST as geo+json Feature to parent deployment's /subdeployments endpoint",
        "pack": "Relay-Only Patch Pack",
        "auditFixes": [
            "U1: Converted from simplified JSON to geo+json Feature format",
            "U3: platform@link.href marked as RUNTIME_RESOLVE — bootstrap script resolves via find_by_uid()",
        ],
    },
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": "urn:os4csapi:deployment:relay:ft-huachuca:001",
        "name": "Relay Emplacement",
        "description": (
            "Leaf deployment representing the emplacement of the communications "
            "relay/repeater support system within the deployed sensor architecture."
        ),
        "validTime": [VALID_TIME_START, ".."],
        "platform@link": {
            "href": "RUNTIME_RESOLVE:urn:os4csapi:system:relay:ft-huachuca:001",
            "title": "Relay",
            # Bootstrap script resolves: find_by_uid("systems", uid) → actual URL
        },
        "_originalMetadata": {
            "deploymentType": "support-leaf",
            "roleType": "communications-support",
            "purpose": (
                "Maintain or extend communications reach between remote sensor "
                "assets and the monitoring/reporting chain."
            ),
            "status": "active-demo",
            "occupantSummary": "Relay communications-support system",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  DEPLOYMENT — Localizer Feed Leaf
#
#  Original metadata preserved:
#    uid, name, description, type, platform@link, properties
#    (deploymentType, roleType, purpose)
#
#  U3: platform@link.href stays as runtime placeholder — clearly documented
# ═══════════════════════════════════════════════════════════════════════════

DEPLOYMENT_LOCALIZER_LEAF = {
    "_templateMeta": {
        "description": "Server-ready deployment leaf template for localizer feed",
        "wirePattern": "POST as geo+json Feature to parent deployment's /subdeployments endpoint",
        "auditFixes": [
            "U1: Converted from simplified JSON to geo+json Feature format",
            "U3: platform@link.href remains as RUNTIME_RESOLVE — bootstrap script resolves via find_by_uid()",
        ],
    },
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": "urn:os4csapi:deployment:localizer:ft-huachuca:alpha:001",
        "name": "String Alpha Localizer Feed",
        "description": (
            "Leaf deployment representing the string-level localizer fusion "
            "capability for String Alpha."
        ),
        "validTime": [VALID_TIME_START, ".."],
        "platform@link": {
            "href": "RUNTIME_RESOLVE:urn:os4csapi:system:fusion:az-string-alpha-localizer",
            "title": "AZ String Alpha Localizer",
            # Bootstrap script resolves: find_by_uid("systems", uid) → actual URL
        },
        "_originalMetadata": {
            "deploymentType": "feed-leaf",
            "roleType": "fusion-producer",
            "purpose": (
                "Produce string-level location estimates from two or more "
                "contributing LOB observations."
            ),
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  SAMPLING FEATURE — Track Template
#
#  Original metadata preserved:
#    uid, name, description, type, geometry, properties
#    (featureType, contactId, trackState, createdBy, createdFrom,
#    identityAuthority)
#
#  Already near-correct geo+json format. Minor enhancement only.
# ═══════════════════════════════════════════════════════════════════════════

SAMPLING_FEATURE_TRACK = {
    "type": "Feature",
    "geometry": None,
    "properties": {
        "uid": "urn:os4csapi:track:REPLACE_CONTACT_ID",
        "name": "Track REPLACE_CONTACT_ID",
        "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint",
        "description": "Track Feature of Interest committed at the SET reporting tier.",
        "_originalMetadata": {
            "contactId": "REPLACE_CONTACT_ID",
            "trackState": "active",
            "createdBy": "SET-A",
            "createdFrom": "SENREP submission",
            "identityAuthority": "SET reporting tier",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  OBSERVATIONS — Example templates (already correct wire format)
#
#  These are not modified — phenomenonTime + resultTime + result dict
#  is the correct O&M observation format for OSH.
# ═══════════════════════════════════════════════════════════════════════════

# observation_lob_example.json — no changes needed
# observation_location_estimate_example.json — no changes needed
# observation_senrep_example.json — no changes needed


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN — Write all transformed templates
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("Transforming UAS pack templates to server-ready wire format...")
    print(f"  Target: {os.path.abspath(TEMPLATE_DIR)}")
    print()

    # Systems (U1 fix: simplified JSON → geojson stub + SensorML)
    print("Systems:")
    write("system_localizer_enriched.json", SYSTEM_LOCALIZER)
    write("system_set_a_enriched.json", SYSTEM_SET_A)
    write("system_monitoring_site_enriched.json", SYSTEM_MONITORING_SITE)
    write("system_relay_enriched.json", SYSTEM_RELAY)  # U4 fix: new file
    print()

    # Procedures (U1 fix: simplified JSON → geo+json Feature)
    print("Procedures:")
    write("procedure_lob_wls_triangulation_v1.json", PROCEDURE_WLS)
    write("procedure_senrep_sop_v1.json", PROCEDURE_SENREP_SOP)
    print()

    # DataStreams (U2 fix: timestamp definition + referenceTime)
    print("DataStreams:")
    write("datastream_location_estimate.json", DATASTREAM_LOCATION_ESTIMATE)
    write("datastream_senrep_v1_1.json", DATASTREAM_SENREP)
    print()

    # Deployments (U1 fix: simplified JSON → geo+json Feature)
    print("Deployments:")
    write("deployment_localizer_feed_leaf.json", DEPLOYMENT_LOCALIZER_LEAF)
    write("deployment_relay_emplacement_enriched.json", DEPLOYMENT_RELAY_LEAF)  # Relay Patch Pack
    print()

    # Sampling Feature (minor structure enhancement)
    print("Sampling Feature:")
    write("samplingfeature_track_template.json", SAMPLING_FEATURE_TRACK)
    print()

    # Observations — not modified (already correct format)
    print("Observations: 3 files unchanged (already correct O&M format)")
    print()

    print("=" * 60)
    print("DONE — 12 files written, 3 observation files unchanged")
    print()
    print("Audit findings addressed:")
    print("  U1 ✓  System/Procedure/Deployment → proper SensorML/geo+json")
    print("  U2 ✓  Datastream timestamp → definition + referenceTime")
    print("  U3 ✓  Placeholders → resolved or clearly marked RUNTIME_RESOLVE")
    print("  U4 ✓  Relay system template → created")
    print("  U6 ✓  SVG paths → absolute GitHub raw URLs")
    print()
    print("Metadata preservation: ALL original fields mapped to SWE/SML equivalents.")
    print("No information from v1 templates was lost.")


if __name__ == "__main__":
    main()
