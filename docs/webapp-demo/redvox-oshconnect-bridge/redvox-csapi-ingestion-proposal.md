# RedVox → CSAPI Ingestion Bridge: Proposal & Architecture

**Date:** 2025-02-19  
**Status:** Proposal / Pre-Implementation  
**Author:** OS4CSAPI Team

---

## Executive Summary

This document proposes a proof-of-concept pipeline that ingests real-world multi-sensor data from [RedVox](https://www.redvox.io/) recording devices into an OGC Connected Systems API (CSAPI) server via [OSHConnect-Python](https://github.com/Botts-Innovative-Research/OSHConnect-Python). The goal is to demonstrate end-to-end data flow: from a real sensor recording to proper CSAPI resources (Systems, DataStreams, Observations) that the ogc-csapi-explorer demo app can discover, browse, and visualize.

---

## 1. The Idea

### Problem
The CSAPI ecosystem has mature read-side tooling (our ogc-client library, the demo explorer app) but few demonstrations of **real-world sensor data being ingested** through the write path of the API. Existing data on test servers (OSH drone data, 52North weather data) was created by other means, not by a CSAPI client pushing observations.

### Proposal
Use a single Python script that:
1. Loads a RedVox DataWindow file (real multi-sensor recording from a mobile device)
2. Maps RedVox concepts to CSAPI resources
3. Uses OSHConnect-Python to push everything into an OpenSensorHub CSAPI server
4. The demo explorer then discovers and displays the data through normal CSAPI Part 1/Part 2 read operations

This creates a **complete round-trip demonstration** of the Connected Systems API standard.

---

## 2. Component Overview

### 2.1 RedVox SDK (`redvox==3.2.0`)

**What it is:** A Python SDK for loading and analyzing data from RedVox infrasound recording devices (typically smartphones running the RedVox Infrasound Recorder app).

**Repository:** https://github.com/RedVoxInc/redvox-examples  
**Data Portal:** https://redvox.io/#/reports

**Key Concepts:**
- **DataWindow** — A time-bounded collection of station recordings, serialized as `.pkl.lz4` (pickle + LZ4 compression)
- **Station** — A single recording device (phone/tablet) identified by a station ID
- **Sensors** — Each station contains multiple sensor channels:

| Sensor | Type | Typical Sample Rate | Fields |
|--------|------|-------------------|--------|
| Audio (microphone) | Single-channel | 800 Hz (infrasound-optimized) | amplitude |
| Barometer | Single-channel | ~1 Hz | pressure (Pa) |
| Accelerometer | 3-axis vector | ~100 Hz | x, y, z (m/s²) |
| Gyroscope | 3-axis vector | ~100 Hz | x, y, z (rad/s) |
| Magnetometer | 3-axis vector | ~100 Hz | x, y, z (µT) |
| Location (GPS) | Multi-field | Variable | lat, lon, altitude, speed, bearing |
| Health | Multi-field | ~1 Hz | battery %, temperature, network type |

**Sample Dataset:** `dw_1648830257000498_2.pkl.lz4`  
- Recorded during a **SpaceX rocket launch** at Kennedy Space Center  
- Downloaded from: https://redvox.io/#/reports/E328  
- Contains multiple stations with all sensor types active  
- Timestamps in microseconds since Unix epoch (UTC)

### 2.2 OSHConnect-Python

**What it is:** The official Python client library for OpenSensorHub / Connected Systems API, developed by Botts Innovative Research (the creators of OpenSensorHub).

**Repository:** https://github.com/Botts-Innovative-Research/OSHConnect-Python  
**Documentation:** https://botts-innovative-research.github.io/OSHConnect-Python/  
**License:** MPL-2.0  
**Last Updated:** ~October 2025 (v0.x, pre-1.0)

**Key Capabilities:**

| Feature | Class/Method | Notes |
|---------|-------------|-------|
| Server connection | `Node(address, port, protocol, username, password)` | Connects to any CSAPI server |
| System creation | `System(name, label, urn, parent_node)` → `insert_self()` | POST to `/systems` with SensorML |
| DataStream creation | `DataRecordSchema` → `system.add_insert_datastream(schema)` | POST to `/systems/{id}/datastreams` |
| Observation insert | `datastream.insert_observation_dict({...})` | POST to `/datastreams/{id}/observations` |
| Control streams | `system.add_and_insert_control_stream(schema)` | Full control stream lifecycle |
| WebSocket streaming | `datastream.insert_data(data)` | Real-time push via WS |
| MQTT support | `datastream.subscribe_mqtt(topic)` | Pub/sub messaging |
| System discovery | `node.discover_systems()` | GET from `/systems` |
| DataStream discovery | `system.discover_datastreams()` | GET from `/systems/{id}/datastreams` |
| Config persistence | `app.save_config()` / `OSHConnect.load_config()` | shelve-based |

**Architecture:**
- Uses Pydantic models for all CSAPI resources (`SystemResource`, `DatastreamResource`, `ObservationResource`, etc.)
- `ConnectedSystemsRequestBuilder` — fluent builder for HTTP requests
- `APIHelper` — abstract base for REST operations (GET/POST/PUT/DELETE)
- `StreamableResource[T]` — generic base for WebSocket-capable resources
- Node → System → DataStream/ControlStream hierarchy mirrors CSAPI resource model

**Installation:** `pip install oshconnect` (or from source: `pip install -e .`)

### 2.3 Target Server

**OpenSensorHub instance** at `http://45.55.99.236:8080/sensorhub/api`
- Already used by the demo explorer
- Has existing drone data (FCU Field Drone CubePilot) and weather observations
- Supports CSAPI Part 1 and Part 2
- Auth: Basic auth (admin credentials)

### 2.4 Demo Explorer (ogc-csapi-explorer)

**The read side of this demonstration.**  
Once data is ingested, the demo app at `http://localhost:5174` (or deployed) will:
- Discover the new RedVox Systems on the Systems page
- Browse DataStreams under each System
- View Observations (parsed via Part 2 parsers)
- Display sensor metadata and schemas
- Show the data on the Map page (for location-enabled stations)

---

## 3. Data Mapping: RedVox → CSAPI

### 3.1 Resource Mapping

```
RedVox DataWindow
  └── Station (phone/device)          →  CSAPI System
        ├── Audio sensor               →  CSAPI DataStream (scalar, high-rate)
        ├── Barometer sensor            →  CSAPI DataStream (scalar, ~1Hz)
        ├── Accelerometer sensor        →  CSAPI DataStream (3-axis vector)
        ├── Gyroscope sensor            →  CSAPI DataStream (3-axis vector)
        ├── Magnetometer sensor         →  CSAPI DataStream (3-axis vector)
        ├── Location sensor             →  CSAPI DataStream (record: lat/lon/alt/speed)
        └── Health sensor               →  CSAPI DataStream (record: battery/temp)
              └── Sensor readings       →  CSAPI Observations (per DataStream)
```

### 3.2 System Mapping

Each RedVox Station becomes a CSAPI System:

```python
System(
    name="redvox_station_{station_id}",
    label="RedVox Station {station_id} – SpaceX Launch Recording",
    urn="urn:redvox:station:{station_id}",
    description="Mobile infrasound recording device, RedVox SDK",
    parent_node=node
)
```

### 3.3 DataStream Schema Examples

**Barometer (scalar):**
```python
DataRecordSchema(
    label="Barometer",
    description="Atmospheric pressure from device barometer",
    fields=[
        TimeSchema(label="timestamp", description="Sample timestamp"),
        QuantitySchema(label="pressure", description="Atmospheric pressure", uom="Pa")
    ]
)
```

**Accelerometer (3-axis vector):**
```python
DataRecordSchema(
    label="Accelerometer",
    description="3-axis accelerometer from device IMU",
    fields=[
        TimeSchema(label="timestamp", description="Sample timestamp"),
        QuantitySchema(label="accel_x", description="X-axis acceleration", uom="m/s2"),
        QuantitySchema(label="accel_y", description="Y-axis acceleration", uom="m/s2"),
        QuantitySchema(label="accel_z", description="Z-axis acceleration", uom="m/s2")
    ]
)
```

**Location (multi-field record):**
```python
DataRecordSchema(
    label="Location",
    description="GPS location from device",
    fields=[
        TimeSchema(label="timestamp", description="Fix timestamp"),
        QuantitySchema(label="latitude", description="Latitude", uom="deg"),
        QuantitySchema(label="longitude", description="Longitude", uom="deg"),
        QuantitySchema(label="altitude", description="Altitude above WGS84", uom="m"),
        QuantitySchema(label="speed", description="Ground speed", uom="m/s")
    ]
)
```

### 3.4 Observation Format

Each observation follows OSH requirements:

```python
datastream.insert_observation_dict({
    "resultTime": "2022-04-01T19:04:17.000Z",
    "phenomenonTime": "2022-04-01T19:04:17.000Z",
    "result": {
        "timestamp": 1648839857.000,
        "pressure": 101325.4
    }
})
```

---

## 4. Architecture: Single Python Pipeline

### 4.1 Why Not Two Phases?

Initially, a two-phase approach was considered:
1. **Phase 1 (Python):** Extract RedVox data → intermediate JSON files
2. **Phase 2 (TypeScript):** Read JSONs → POST via our ogc-client library

OSHConnect-Python **eliminates Phase 2** entirely. Since both RedVox SDK and OSHConnect are Python libraries, the entire pipeline is a single script with no language boundary, no intermediate files, and no serialization overhead.

### 4.2 Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                  Python Ingestion Script                  │
│                                                           │
│  1. Load DataWindow (.pkl.lz4)                           │
│     └─ redvox.common.data_window.DataWindow.load()       │
│                                                           │
│  2. Connect to OSH                                        │
│     └─ OSHConnect → Node(45.55.99.236:8080, auth)        │
│                                                           │
│  3. For each Station in DataWindow:                       │
│     a. Create System → system.insert_self()               │
│     b. For each sensor (audio, baro, accel, gyro, etc.): │
│        i.  Build DataRecordSchema for sensor type         │
│        ii. system.add_insert_datastream(schema)           │
│     c. For each sensor's readings:                        │
│        i.  Convert timestamps (µs → ISO 8601)            │
│        ii. datastream.insert_observation_dict(obs)        │
│                                                           │
│  4. Done — resources are now live on OSH server           │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              OSH Server (45.55.99.236:8080)               │
│                                                           │
│  /systems          → RedVox Station systems               │
│  /datastreams      → Audio, Baro, Accel, etc.            │
│  /observations     → Actual sensor readings               │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│           ogc-csapi-explorer (Demo App)                   │
│                                                           │
│  • Discovers new Systems on Systems page                  │
│  • Browses DataStreams under each System                   │
│  • Views Observations via Part 2 parsers                  │
│  • Displays location data on Map page                     │
│  • Shows sensor metadata, schemas, badges                 │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Plan

### 5.1 Prerequisites

| Requirement | Status |
|-------------|--------|
| Python 3.10+ | Install if needed |
| `pip install redvox==3.2.0` | Install |
| `pip install oshconnect` (or clone + `pip install -e .`) | Install |
| Download `dw_1648830257000498_2.pkl.lz4` from https://redvox.io/#/reports/E328 | Download |
| OSH server accessible at `45.55.99.236:8080` | Already available |
| Admin credentials for OSH server | Available |

### 5.2 Proposed Script Structure

```
redvox-bridge/
├── README.md                    # Setup and usage instructions
├── requirements.txt             # redvox==3.2.0, oshconnect
├── ingest.py                    # Main ingestion script
├── sensor_schemas.py            # DataRecordSchema definitions per sensor type
├── redvox_extract.py            # Helpers to extract readings from DataWindow
└── data/                        # Place .pkl.lz4 files here (gitignored)
    └── .gitkeep
```

### 5.3 Target Sensor Subset (Phase 1)

For the initial proof-of-concept, focus on a **core subset** of sensors:

| Sensor | Priority | Rationale |
|--------|----------|-----------|
| Barometer | **P0** | Simplest schema (scalar), low data volume, high scientific value for infrasound |
| Location | **P0** | Enables Map page display in explorer |
| Accelerometer | **P1** | Demonstrates 3-axis vector schema |
| Audio | **P2** | High sample rate (800 Hz), may need batching/downsampling |
| Gyroscope | **P2** | Similar to accelerometer, additive value |
| Magnetometer | **P2** | Similar to accelerometer, additive value |
| Health | **P3** | Nice-to-have, battery/temp monitoring |

### 5.4 Open Questions

1. **Audio sample rate:** 800 Hz means ~48,000 observations per minute per station. Should we downsample, or batch-insert? OSHConnect supports WebSocket streaming which may help.

2. **Observation batching:** OSH supports batch insert. For high-volume sensors, we may want to send N observations per request rather than one-at-a-time.

3. **Timestamp handling:** RedVox uses microseconds since Unix epoch. OSH expects ISO 8601. Conversion is straightforward but we should validate timezone handling (RedVox is UTC).

4. **Multiple stations:** The SpaceX dataset may contain multiple stations. Start with one station, then expand.

5. **Data cleanup:** Should we provide a cleanup script that removes the created Systems/DataStreams/Observations from the OSH server? Useful for re-running the demo.

6. **OSHConnect maturity:** The library is pre-1.0 (v0.x). We may hit rough edges. The `api_helpers.py` has comprehensive endpoint coverage but higher-level abstractions are still evolving.

---

## 6. Strategic Value

### 6.1 For the CSAPI Ecosystem
- **First public demonstration** of a full ingest pipeline using real sensor data through CSAPI
- Validates both the read path (ogc-client library + explorer) and write path (OSHConnect-Python)
- Exercises CSAPI Part 1 (resource CRUD) and Part 2 (observations, schemas) in a realistic scenario

### 6.2 For the Project
- Adds a compelling "real data" story to the demo
- SpaceX launch recordings are genuinely interesting — infrasound signatures of rocket launches
- GPS locations enable the Map page to show station positions at Kennedy Space Center
- Multiple sensor types exercise different schema patterns (scalar, vector, record)

### 6.3 For the Community
- Bridges two independent ecosystems (RedVox scientific instruments + OGC standards)
- Shows that CSAPI is practical for real-world multi-sensor data
- Provides a template that others can adapt for their own sensor data ingestion

### 6.4 Library Interoperability Demonstration
- **OSHConnect-Python** (Botts) handles the write path → creates CSAPI resources
- **ogc-client** (camptocamp fork) handles the read path → discovers and displays resources
- Two independent libraries, two different organizations, interoperating through the CSAPI standard
- This is exactly what OGC standards are meant to enable

---

## 7. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| OSHConnect-Python has breaking bugs (pre-1.0) | Medium | Fall back to raw HTTP requests via `api_helpers.py` — the low-level API is solid |
| OSH server rejects schemas | Low | Test with minimal schema first, iterate |
| Audio data volume overwhelms server | Medium | Start with barometer+location only, add audio later with downsampling |
| RedVox data format changes | Low | Pinned to `redvox==3.2.0`, dataset is static |
| Network issues with OSH server | Low | Server has been stable throughout project |

---

## 8. References

- **RedVox SDK:** https://github.com/RedVoxInc/redvox-python-sdk
- **RedVox Examples:** https://github.com/RedVoxInc/redvox-examples
- **RedVox Data Portal:** https://redvox.io/#/reports
- **SpaceX Launch Dataset:** https://redvox.io/#/reports/E328
- **OSHConnect-Python:** https://github.com/Botts-Innovative-Research/OSHConnect-Python
- **OSHConnect Docs:** https://botts-innovative-research.github.io/OSHConnect-Python/
- **OSHConnect Architecture:** https://docs.google.com/document/d/1pIaeQw0ocU6ApNgqTVRZuSwjJAbhCcmweMq6RiVYEic/edit
- **OpenSensorHub:** https://opensensorhub.org/
- **OGC Connected Systems API:** https://ogcapi.ogc.org/connectedsystems/
- **ogc-client (CSAPI_2 fork):** https://github.com/OS4CSAPI/ogc-client-CSAPI_2
- **Demo Explorer:** https://github.com/OS4CSAPI/ogc-csapi-explorer
- **OSH Test Server:** http://45.55.99.236:8080/sensorhub/api
