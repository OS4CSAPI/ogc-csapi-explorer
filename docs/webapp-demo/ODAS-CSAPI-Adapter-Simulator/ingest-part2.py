#!/usr/bin/env python3
"""
ODAS Acoustic Array — Part 2 Resource Ingestion
Creates Datastreams, Observations, ControlStreams, and Commands on existing Part 1 systems.

Uses the correct OSH SensorHub payload formats:
 - Datastreams: { schema: { obsFormat: "application/swe+json", recordSchema: {...} } }
 - ControlStreams: { schema: { commandFormat: "application/swe+json", parametersSchema: {...} } }
 - Observations: Content-Type: application/json, body: { phenomenonTime, resultTime, result }
 - Commands: Content-Type: application/json, body: { issueTime, parameters }

OSH Quirks handled:
 - S-9:  Only obsFormat "application/swe+json" is accepted (not "application/json")
 - S-15: "type" MUST be the first property in every SWE Common JSON object
 - S-2:  Observations can only be POSTed to REST-created (writable) datastreams
"""

import requests
import json
import math
import sys
from datetime import datetime, timezone, timedelta

# ─── Configuration ───────────────────────────────────────────────────────────
BASE_URL = "http://45.55.99.236:8080/sensorhub/api"
AUTH = ("ogc", "ogc")
HEADERS_JSON = {"Content-Type": "application/json"}

# ─── Known Part 1 System IDs (created by ingest-odas-data-model.py) ────────
# These are the server-assigned IDs for the existing subsystems/sensors
SYSTEM_IDS = {
    "ssl_module":       "04kg",   # SSL Sensor (under DSP pipeline)
    "sst_module":       "04l0",   # SST Sensor (under DSP pipeline)
    "dsp_pipeline":     "04k0",   # DSP Pipeline system
    "tri_engine":       "04m0",   # Triangulation Engine system
    "config_actuator":  "04lg",   # Config Actuator (for control streams)
}

# Track newly created Part 2 resource IDs
ids = {}


# ─── Helper ──────────────────────────────────────────────────────────────────

def post(endpoint, payload, label="resource", timeout=30):
    """POST a resource with allow_redirects=False so 302s are caught."""
    url = f"{BASE_URL}/{endpoint}"
    r = requests.post(url, json=payload, headers=HEADERS_JSON, auth=AUTH,
                      allow_redirects=False, timeout=timeout)
    if r.status_code == 201:
        loc = r.headers.get("Location", "")
        rid = loc.rstrip("/").split("/")[-1]
        print(f"  ✓ Created {label}: {rid}")
        return rid
    elif r.status_code == 202:
        # OSH async dispatch for commands — 202 Accepted (S-14)
        print(f"  ✓ Dispatched {label} (202 Accepted — async, no persisted ID)")
        return "dispatched"
    elif r.status_code == 302:
        loc = r.headers.get("Location", "")
        print(f"  ✗ REDIRECT {label}: 302 → {loc}")
        print(f"    (Server rejected payload — check schema format)")
        return None
    elif r.status_code == 409:
        print(f"  ⚠ Conflict for {label} — already exists")
        return None
    else:
        body = r.text[:800] if r.text else "(empty)"
        print(f"  ✗ FAILED {label}: {r.status_code}")
        print(f"    {body}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: DATASTREAMS
# ═══════════════════════════════════════════════════════════════════════════════

def create_datastreams():
    print("\n══════ PHASE 7: DATASTREAMS ══════")

    # ─── DS 1: SSL Potential Sources (under SSL module) ───
    ssl_id = SYSTEM_IDS["ssl_module"]

    ids["ds_ssl"] = post(f"systems/{ssl_id}/datastreams", {
        "name": "SSL Potential Sources — Array #001",
        "outputName": "ssl_pots",
        "schema": {
            "obsFormat": "application/swe+json",
            "recordSchema": {
                "type": "DataRecord",
                "label": "SSL Potential Sources",
                "description": "Up to 4 potential sound source detections per frame from SRP-PHAT beamformer",
                "fields": [
                    {
                        "type": "Count",
                        "name": "numSources",
                        "label": "Number of detected sources",
                        "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                    },
                    {
                        "type": "DataRecord",
                        "name": "source0",
                        "label": "Potential Source #0",
                        "fields": [
                            {"type": "Quantity", "name": "x", "label": "DOA X", "definition": "http://sensorml.com/ont/swe/property/DirectionX", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "y", "label": "DOA Y", "definition": "http://sensorml.com/ont/swe/property/DirectionY", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "z", "label": "DOA Z", "definition": "http://sensorml.com/ont/swe/property/DirectionZ", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "energy", "label": "Beamformer Energy", "definition": "urn:x-odas:property:sound-source-energy", "uom": {"code": "1"}}
                        ]
                    },
                    {
                        "type": "DataRecord",
                        "name": "source1",
                        "label": "Potential Source #1",
                        "fields": [
                            {"type": "Quantity", "name": "x", "label": "DOA X", "definition": "http://sensorml.com/ont/swe/property/DirectionX", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "y", "label": "DOA Y", "definition": "http://sensorml.com/ont/swe/property/DirectionY", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "z", "label": "DOA Z", "definition": "http://sensorml.com/ont/swe/property/DirectionZ", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "energy", "label": "Beamformer Energy", "definition": "urn:x-odas:property:sound-source-energy", "uom": {"code": "1"}}
                        ]
                    },
                    {
                        "type": "DataRecord",
                        "name": "source2",
                        "label": "Potential Source #2",
                        "fields": [
                            {"type": "Quantity", "name": "x", "label": "DOA X", "definition": "http://sensorml.com/ont/swe/property/DirectionX", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "y", "label": "DOA Y", "definition": "http://sensorml.com/ont/swe/property/DirectionY", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "z", "label": "DOA Z", "definition": "http://sensorml.com/ont/swe/property/DirectionZ", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "energy", "label": "Beamformer Energy", "definition": "urn:x-odas:property:sound-source-energy", "uom": {"code": "1"}}
                        ]
                    },
                    {
                        "type": "DataRecord",
                        "name": "source3",
                        "label": "Potential Source #3",
                        "fields": [
                            {"type": "Quantity", "name": "x", "label": "DOA X", "definition": "http://sensorml.com/ont/swe/property/DirectionX", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "y", "label": "DOA Y", "definition": "http://sensorml.com/ont/swe/property/DirectionY", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "z", "label": "DOA Z", "definition": "http://sensorml.com/ont/swe/property/DirectionZ", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "energy", "label": "Beamformer Energy", "definition": "urn:x-odas:property:sound-source-energy", "uom": {"code": "1"}}
                        ]
                    }
                ]
            }
        }
    }, label="DataStream: SSL Pots")

    # ─── DS 2: SST Tracked Sources (under SST module) ───
    sst_id = SYSTEM_IDS["sst_module"]

    ids["ds_sst"] = post(f"systems/{sst_id}/datastreams", {
        "name": "SST Tracked Sources — Array #001",
        "outputName": "sst_tracks",
        "schema": {
            "obsFormat": "application/swe+json",
            "recordSchema": {
                "type": "DataRecord",
                "label": "SST Tracked Sources",
                "description": "Currently tracked sources with persistent identity from particle filter",
                "fields": [
                    {
                        "type": "Count",
                        "name": "numTracks",
                        "label": "Number of active tracks",
                        "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                    },
                    {
                        "type": "DataRecord",
                        "name": "track0",
                        "label": "Tracked Source #0",
                        "fields": [
                            {"type": "Count", "name": "id", "label": "Track ID", "definition": "http://sensorml.com/ont/swe/property/TrackID"},
                            {"type": "Text", "name": "tag", "label": "Classification Tag", "definition": "http://sensorml.com/ont/swe/property/Classification"},
                            {"type": "Quantity", "name": "x", "label": "DOA X", "definition": "http://sensorml.com/ont/swe/property/DirectionX", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "y", "label": "DOA Y", "definition": "http://sensorml.com/ont/swe/property/DirectionY", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "z", "label": "DOA Z", "definition": "http://sensorml.com/ont/swe/property/DirectionZ", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "activity", "label": "Activity Level", "definition": "urn:x-odas:property:source-activity-level", "uom": {"code": "1"}}
                        ]
                    },
                    {
                        "type": "DataRecord",
                        "name": "track1",
                        "label": "Tracked Source #1",
                        "fields": [
                            {"type": "Count", "name": "id", "label": "Track ID", "definition": "http://sensorml.com/ont/swe/property/TrackID"},
                            {"type": "Text", "name": "tag", "label": "Classification Tag", "definition": "http://sensorml.com/ont/swe/property/Classification"},
                            {"type": "Quantity", "name": "x", "label": "DOA X", "definition": "http://sensorml.com/ont/swe/property/DirectionX", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "y", "label": "DOA Y", "definition": "http://sensorml.com/ont/swe/property/DirectionY", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "z", "label": "DOA Z", "definition": "http://sensorml.com/ont/swe/property/DirectionZ", "uom": {"code": "1"}},
                            {"type": "Quantity", "name": "activity", "label": "Activity Level", "definition": "urn:x-odas:property:source-activity-level", "uom": {"code": "1"}}
                        ]
                    }
                ]
            }
        }
    }, label="DataStream: SST Tracks")

    # ─── DS 3: Geographic Lines of Bearing (under SSL module) ───
    ids["ds_lob"] = post(f"systems/{ssl_id}/datastreams", {
        "name": "Geographic Lines of Bearing — Array #001",
        "outputName": "geographic_lob",
        "schema": {
            "obsFormat": "application/swe+json",
            "recordSchema": {
                "type": "DataRecord",
                "label": "Geographic Lines of Bearing",
                "description": "SSL output projected into geographic coordinates as true-north azimuths",
                "fields": [
                    {
                        "type": "Count",
                        "name": "numBearings",
                        "label": "Number of bearings",
                        "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"
                    },
                    {
                        "type": "DataRecord",
                        "name": "bearing0",
                        "label": "Bearing #0",
                        "fields": [
                            {"type": "Count", "name": "sourceId", "label": "Source Track ID", "definition": "http://sensorml.com/ont/swe/property/TrackID"},
                            {"type": "Quantity", "name": "azimuth", "label": "True Azimuth", "definition": "http://sensorml.com/ont/swe/property/TrueHeading", "uom": {"code": "deg"}},
                            {"type": "Quantity", "name": "elevation", "label": "Elevation Angle", "definition": "http://sensorml.com/ont/swe/property/ElevationAngle", "uom": {"code": "deg"}},
                            {"type": "Quantity", "name": "energy", "label": "Source Energy", "definition": "urn:x-odas:property:sound-source-energy", "uom": {"code": "1"}}
                        ]
                    },
                    {
                        "type": "DataRecord",
                        "name": "bearing1",
                        "label": "Bearing #1",
                        "fields": [
                            {"type": "Count", "name": "sourceId", "label": "Source Track ID", "definition": "http://sensorml.com/ont/swe/property/TrackID"},
                            {"type": "Quantity", "name": "azimuth", "label": "True Azimuth", "definition": "http://sensorml.com/ont/swe/property/TrueHeading", "uom": {"code": "deg"}},
                            {"type": "Quantity", "name": "elevation", "label": "Elevation Angle", "definition": "http://sensorml.com/ont/swe/property/ElevationAngle", "uom": {"code": "deg"}},
                            {"type": "Quantity", "name": "energy", "label": "Source Energy", "definition": "urn:x-odas:property:sound-source-energy", "uom": {"code": "1"}}
                        ]
                    }
                ]
            }
        }
    }, label="DataStream: Geographic LOBs")

    # ─── DS 4: Triangulated 3D Positions (under triangulation engine) ───
    tri_id = SYSTEM_IDS["tri_engine"]

    ids["ds_tri"] = post(f"systems/{tri_id}/datastreams", {
        "name": "Triangulated 3D Source Positions",
        "outputName": "triangulated_positions",
        "schema": {
            "obsFormat": "application/swe+json",
            "recordSchema": {
                "type": "DataRecord",
                "label": "Triangulated Source Position",
                "description": "3D position from multi-array Ray-to-Ray intersection",
                "fields": [
                    {"type": "Quantity", "name": "latitude", "label": "Latitude", "definition": "http://sensorml.com/ont/swe/property/GeodeticLatitude", "uom": {"code": "deg"}, "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                    {"type": "Quantity", "name": "longitude", "label": "Longitude", "definition": "http://sensorml.com/ont/swe/property/Longitude", "uom": {"code": "deg"}, "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                    {"type": "Quantity", "name": "altitude", "label": "Altitude (m AGL)", "definition": "http://sensorml.com/ont/swe/property/AltitudeAGL", "uom": {"code": "m"}},
                    {"type": "Quantity", "name": "horizontalAccuracy", "label": "Horizontal Accuracy", "definition": "http://sensorml.com/ont/swe/property/HorizontalAccuracy", "uom": {"code": "m"}},
                    {"type": "Quantity", "name": "confidence", "label": "Confidence", "definition": "http://sensorml.com/ont/swe/property/QualityIndex", "uom": {"code": "1"}},
                    {"type": "Count", "name": "numContributingArrays", "label": "Contributing Arrays", "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"}
                ]
            }
        }
    }, label="DataStream: Triangulated Positions")

    # ─── DS 5: System Health Status (under DSP pipeline) ───
    dsp_id = SYSTEM_IDS["dsp_pipeline"]

    ids["ds_status"] = post(f"systems/{dsp_id}/datastreams", {
        "name": "System Health and Status — Array #001",
        "outputName": "system_status",
        "schema": {
            "obsFormat": "application/swe+json",
            "recordSchema": {
                "type": "DataRecord",
                "label": "System Health Status",
                "description": "Periodic health report: CPU load, USB, tracks, buffer, threshold",
                "fields": [
                    {"type": "Quantity", "name": "cpuLoad", "label": "CPU Load", "definition": "http://sensorml.com/ont/swe/property/SystemLoad", "uom": {"code": "%"}},
                    {"type": "Boolean", "name": "usbConnected", "label": "USB Connection Active", "definition": "http://sensorml.com/ont/swe/property/ConnectionStatus"},
                    {"type": "Count", "name": "activeTrackCount", "label": "Active Tracks", "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"},
                    {"type": "Quantity", "name": "bufferHealth", "label": "Buffer Health", "definition": "http://sensorml.com/ont/swe/property/BufferLevel", "uom": {"code": "%"}},
                    {"type": "Quantity", "name": "currentThreshold", "label": "Energy Threshold (E_T)", "definition": "urn:x-odas:property:detection-threshold", "uom": {"code": "1"}}
                ]
            }
        }
    }, label="DataStream: System Status")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: OBSERVATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_observations():
    print("\n══════ PHASE 8: OBSERVATIONS ══════")

    now = datetime(2026, 2, 20, 14, 30, 0, tzinfo=timezone.utc)

    # --- SSL Observations (5 frames) ---
    ds_ssl = ids.get("ds_ssl")
    if ds_ssl:
        for i in range(5):
            t = now + timedelta(milliseconds=i * 8)
            ts = t.isoformat(timespec="milliseconds")
            rt = (t + timedelta(milliseconds=1)).isoformat(timespec="milliseconds")

            # Simulate speaker at ~70° azimuth + faint noise source
            az1 = math.radians(70 + i * 0.3)
            x1, y1 = round(math.sin(az1), 4), round(math.cos(az1), 4)
            e1 = round(0.85 + i * 0.01, 4)

            az2 = math.radians(210 + i * 0.1)
            x2, y2 = round(math.sin(az2), 4), round(math.cos(az2), 4)
            e2 = round(0.25 - i * 0.02, 4)

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "numSources": 2,
                    "source0": {"x": x1, "y": y1, "z": 0.0, "energy": e1},
                    "source1": {"x": x2, "y": y2, "z": 0.0, "energy": e2},
                    "source2": {"x": 0.0, "y": 0.0, "z": 0.0, "energy": 0.0},
                    "source3": {"x": 0.0, "y": 0.0, "z": 0.0, "energy": 0.0}
                }
            }
            post(f"datastreams/{ds_ssl}/observations", obs, label=f"SSL Obs frame {i}")
    else:
        print("  ⏭ Skipping SSL observations — no datastream ID")

    # --- SST Observations (5 frames) ---
    ds_sst = ids.get("ds_sst")
    if ds_sst:
        for i in range(5):
            t = now + timedelta(milliseconds=i * 8)
            ts = t.isoformat(timespec="milliseconds")
            rt = (t + timedelta(milliseconds=4)).isoformat(timespec="milliseconds")

            az1 = math.radians(70 + i * 0.3)
            x1, y1 = round(math.sin(az1), 4), round(math.cos(az1), 4)
            act = round(0.92 + i * 0.01, 4)

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "numTracks": 1,
                    "track0": {"id": 42, "tag": "dynamic", "x": x1, "y": y1, "z": 0.0, "activity": act},
                    "track1": {"id": 0, "tag": "", "x": 0.0, "y": 0.0, "z": 0.0, "activity": 0.0}
                }
            }
            post(f"datastreams/{ds_sst}/observations", obs, label=f"SST Obs frame {i}")
    else:
        print("  ⏭ Skipping SST observations — no datastream ID")

    # --- LOB Observations (5 frames) ---
    ds_lob = ids.get("ds_lob")
    if ds_lob:
        for i in range(5):
            t = now + timedelta(milliseconds=i * 8)
            ts = t.isoformat(timespec="milliseconds")
            rt = (t + timedelta(milliseconds=6)).isoformat(timespec="milliseconds")

            azimuth = round(70.0 + i * 0.3, 2)
            energy = round(0.85 + i * 0.01, 4)

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "numBearings": 1,
                    "bearing0": {"sourceId": 42, "azimuth": azimuth, "elevation": 0.0, "energy": energy},
                    "bearing1": {"sourceId": 0, "azimuth": 0.0, "elevation": 0.0, "energy": 0.0}
                }
            }
            post(f"datastreams/{ds_lob}/observations", obs, label=f"LOB Obs frame {i}")
    else:
        print("  ⏭ Skipping LOB observations — no datastream ID")

    # --- Triangulated Position Observations (3 frames) ---
    ds_tri = ids.get("ds_tri")
    if ds_tri:
        for i in range(3):
            t = now + timedelta(milliseconds=i * 50)
            ts = t.isoformat(timespec="milliseconds")
            rt = (t + timedelta(milliseconds=25)).isoformat(timespec="milliseconds")

            obs = {
                "phenomenonTime": ts,
                "resultTime": rt,
                "result": {
                    "latitude": round(38.8985 + i * 0.00001, 6),
                    "longitude": round(-77.0355 + i * 0.00001, 6),
                    "altitude": round(15.2 + i * 0.1, 1),
                    "horizontalAccuracy": round(1.2 - i * 0.1, 2),
                    "confidence": round(0.82 + i * 0.03, 2),
                    "numContributingArrays": 3
                }
            }
            post(f"datastreams/{ds_tri}/observations", obs, label=f"Tri Obs {i}")
    else:
        print("  ⏭ Skipping triangulation observations — no datastream ID")

    # --- System Status Observations (3 frames, 5-sec intervals) ---
    ds_status = ids.get("ds_status")
    if ds_status:
        for i in range(3):
            t = now + timedelta(seconds=i * 5)
            ts = t.isoformat(timespec="milliseconds")

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
            post(f"datastreams/{ds_status}/observations", obs, label=f"Status Obs {i}")
    else:
        print("  ⏭ Skipping status observations — no datastream ID")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: CONTROL STREAMS & COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

def create_control_streams_and_commands():
    print("\n══════ PHASE 9: CONTROL STREAMS & COMMANDS ══════")

    actuator_id = SYSTEM_IDS["config_actuator"]

    # --- ControlStream: Detection Parameters ---
    ids["cs_detection"] = post(f"systems/{actuator_id}/controlstreams", {
        "name": "Detection Parameters Control — Array #001",
        "inputName": "detection_params",
        "schema": {
            "commandFormat": "application/swe+json",
            "parametersSchema": {
                "type": "DataRecord",
                "label": "Detection Parameter Command",
                "description": "Runtime-adjustable detection and tracking parameters",
                "fields": [
                    {"type": "Quantity", "name": "energyThreshold", "label": "Energy Threshold (E_T)", "definition": "urn:x-odas:property:detection-threshold", "uom": {"code": "1"}},
                    {"type": "Quantity", "name": "trackingSensitivity", "label": "Tracking Sensitivity (T_new)", "definition": "urn:x-odas:property:tracking-sensitivity", "uom": {"code": "1"}},
                    {"type": "Count", "name": "framesToConfirm", "label": "Frames to Confirm (F_new)", "definition": "http://sensorml.com/ont/swe/property/NumberOfSamples"},
                    {"type": "Text", "name": "reason", "label": "Change Reason", "definition": "http://sensorml.com/ont/swe/property/Description"}
                ]
            }
        }
    }, label="ControlStream: Detection Params")

    # --- Commands ---
    cs_id = ids.get("cs_detection")
    if cs_id:
        # Command 1: Lower threshold for quiet environment
        # NOTE: Commands use async dispatch (S-14). Server waits ~30s for
        # actuator acknowledgment before returning 202 Accepted. No persisted
        # resource ID is returned — fire-and-forget.
        print("  ℹ Commands use async dispatch (~30s each, 202 Accepted)...")

        ids["cmd_lower"] = post(f"controlstreams/{cs_id}/commands", {
            "issueTime": "2026-02-20T14:35:00Z",
            "parameters": {
                "energyThreshold": 400.0,
                "trackingSensitivity": 0.75,
                "framesToConfirm": 10,
                "reason": "Lowering threshold to detect quieter sources in low-noise environment"
            }
        }, label="Command: Lower Threshold", timeout=45)

        # Command 2: Increase sensitivity for surveillance
        ids["cmd_sensitive"] = post(f"controlstreams/{cs_id}/commands", {
            "issueTime": "2026-02-20T14:40:00Z",
            "parameters": {
                "energyThreshold": 400.0,
                "trackingSensitivity": 0.6,
                "framesToConfirm": 8,
                "reason": "Increasing sensitivity for surveillance scenario"
            }
        }, label="Command: Increase Sensitivity", timeout=45)

        # Command 3: Reset to defaults
        ids["cmd_reset"] = post(f"controlstreams/{cs_id}/commands", {
            "issueTime": "2026-02-20T15:00:00Z",
            "parameters": {
                "energyThreshold": 600.0,
                "trackingSensitivity": 0.75,
                "framesToConfirm": 10,
                "reason": "Resetting all parameters to defaults"
            }
        }, label="Command: Reset Defaults", timeout=45)
    else:
        print("  ⏭ Skipping commands — no control stream ID")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("ODAS Acoustic Array — Part 2 Resource Ingestion")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    # Test connection
    try:
        r = requests.get(BASE_URL, auth=AUTH, timeout=10)
        r.raise_for_status()
        print(f"✓ Server reachable: {r.json().get('title', 'unknown')}")
    except Exception as e:
        print(f"✗ Cannot reach server: {e}")
        sys.exit(1)

    # Verify Part 1 systems exist
    print("\n── Verifying Part 1 systems ──")
    for label, sid in SYSTEM_IDS.items():
        r = requests.get(f"{BASE_URL}/systems/{sid}", auth=AUTH, timeout=10)
        if r.status_code == 200:
            name = r.json().get("properties", {}).get("name", "?")
            print(f"  ✓ {label} ({sid}): {name}")
        else:
            print(f"  ✗ {label} ({sid}): {r.status_code} — NOT FOUND")
            print(f"    Cannot proceed without Part 1 systems. Run ingest-odas-data-model.py first.")
            sys.exit(1)

    # Execute Part 2 phases
    create_datastreams()
    create_observations()
    create_control_streams_and_commands()

    # Summary
    print("\n" + "=" * 70)
    print("PART 2 INGESTION SUMMARY")
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
