# ODAS Acoustic Array — CSAPI Data Model Ingestion Report

**Date:** February 20, 2026  
**Server:** `http://45.55.99.236:8080/sensorhub/api` (OSH SensorHub)  
**Repository:** [OS4CSAPI/ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer)  
**Commits:** `59fa053` (data model doc), `0444796` (ingestion scripts), `cbbece2` (original report)

---

## 1. Objective

Populate the OSH SensorHub server with a fully-realized CSAPI sample dataset representing the **ODAS (Open embeddeD Audition System)** microphone array platform — a 7-microphone circular PDM MEMS array on an XMOS xCORE-200 board that performs real-time sound source localization (SSL), tracking (SST), geographic bearing estimation, and multi-array 3D triangulation.

The goal was to exercise **all 9 CSAPI resource types** with richly-described, scientifically accurate sample data, producing the most complete end-to-end dataset on the server.

---

## 2. Source Material

| Document | Purpose |
|---|---|
| `sosa-ssn-csapi-data-model.md` | Full SOSA/SSN → CSAPI mapping with JSON payloads for all resources |
| `IROS2017-multi-array-localization.pdf` | Lauzon et al. — Ray-to-Ray triangulation methodology |
| `initial-planning-notes.md` | ODAS architecture research and CSAPI mapping analysis |
| ODAS GitHub wiki | SRP-PHAT beamforming, particle filter tracking algorithms |

---

## 3. Ingestion Architecture

The work was split into two scripts due to fundamental differences in payload format between CSAPI Part 1 and Part 2 resources:

### `ingest-odas-data-model.py` — Part 1 Resources (1,148 lines)

Creates the foundational system hierarchy using GeoJSON payloads (`Content-Type: application/geo+json` for most, `application/json` for Properties).

**Execution order (dependency chain):**
1. **Procedures** — No dependencies
2. **Platform** — No dependencies
3. **Subsystems** — Depends on Platform ID
4. **Properties** — No dependencies
5. **Deployments** — No dependencies
6. **Sampling Features** — Depends on Platform ID

### `ingest-part2.py` — Part 2 Resources (558 lines)

Creates datastreams, observations, control streams, and commands using the correct OSH-specific payload formats (all `Content-Type: application/json`). References Part 1 system IDs by hardcoded server-assigned values.

**Execution order:**
7. **Datastreams** — Depends on Part 1 subsystem IDs
8. **Observations** — Depends on Datastream IDs (from Phase 7)
9. **Control Streams & Commands** — Depends on Actuator ID (from Part 1)

---

## 4. Complete Resource Inventory

### 4.1 Procedures (5)

| Server ID | Name | Algorithm |
|---|---|---|
| `0480` | PDM MEMS Microphone Audio Capture | PDM → PCM decimation, 16 kHz, 256-sample frames |
| `048g` | SRP-PHAT Steered Response Power Beamforming | GCC-PHAT cross-correlation, hemisphere scan, up to 4 sources |
| `0490` | Particle Filter Sound Source Tracking | Sequential Monte Carlo, H=500 particles, excitation-damping model |
| `049g` | Multi-Array Ray-to-Ray 3D Triangulation | Schneider & Eberly 2002, K(K-1)/2 pair intersections |
| `04a0` | ODAS Runtime Configuration Actuation | Parameter validation, atomic/batch updates |

### 4.2 Platform (1)

| Server ID | Name |
|---|---|
| `04fg` | ODAS — XMOS xCORE-200 Microphone Array Board #001 |

### 4.3 Subsystems (13)

| Server ID | Type | Name | Parent |
|---|---|---|---|
| `04g0` | Sensor | 7-Microphone Circular PDM Array | Platform `04fg` |
| `04gg`–`04jg` | Sensor | Microphones #1–#7 (center + 6 ring) | Mic Array `04g0` |
| `04k0` | System | ODAS DSP Processing Pipeline | Platform `04fg` |
| `04kg` | Sensor | ODAS SSL Module (Sound Source Localizer) | DSP `04k0` |
| `04l0` | Sensor | ODAS SST Module (Sound Source Tracker) | DSP `04k0` |
| `04lg` | Actuator | ODAS Runtime Configuration Controller | Platform `04fg` |
| `04m0` | System | Multi-Array 3D Triangulation Engine | Platform `04fg` |

**System hierarchy:**
```
Platform: XMOS xCORE-200 Board (04fg)
├── Sensor: 7-Mic Circular Array (04g0)
│   ├── Sensor: Mic #1 Center (04gg)
│   ├── Sensor: Mic #2 Ring 0° (04h0)
│   ├── Sensor: Mic #3 Ring 60° (04hg)
│   ├── Sensor: Mic #4 Ring 120° (04i0)
│   ├── Sensor: Mic #5 Ring 180° (04ig)
│   ├── Sensor: Mic #6 Ring 240° (04j0)
│   └── Sensor: Mic #7 Ring 300° (04jg)
├── System: DSP Pipeline (04k0)
│   ├── Sensor: SSL Module (04kg)    ← 2 datastreams
│   └── Sensor: SST Module (04l0)    ← 1 datastream
├── Actuator: Config Controller (04lg) ← 1 control stream
└── System: Triangulation Engine (04m0) ← 1 datastream
```

### 4.4 Properties (7)

| Server ID | Label | Definition URI |
|---|---|---|
| `040g` | Sound Source Direction of Arrival | `urn:x-odas:property:sound-source-doa` |
| `0410` | Sound Source Energy | `urn:x-odas:property:sound-source-energy` |
| `041g` | Sound Source Activity Level | `urn:x-odas:property:source-activity-level` |
| `0420` | Geographic Line of Bearing | `urn:x-odas:property:geographic-bearing` |
| `042g` | Triangulated 3D Source Position | `urn:x-odas:property:triangulated-position` |
| `0430` | Detection Energy Threshold | `urn:x-odas:property:detection-threshold` |
| `043g` | Tracking New Source Sensitivity | `urn:x-odas:property:tracking-sensitivity` |

### 4.5 Deployments (5)

| Server ID | Name | Geometry |
|---|---|---|
| `049g` | Conference Room 3A — Single Array | Point (-77.0365, 38.8977, 2.5m) |
| `04a0` | Campus Perimeter — 3-Array Triangulation | Polygon (300m × 300m) |
| `04ag` | Array Position — North (sub-deployment) | Point (-77.0365, 38.8985, 1.0m) |
| `04b0` | Array Position — Southeast (sub-deployment) | Point (-77.0355, 38.8975, 1.0m) |
| `04bg` | Array Position — Southwest (sub-deployment) | Point (-77.0375, 38.8975, 1.0m) |

### 4.6 Sampling Features (3)

| Server ID | Name | Type |
|---|---|---|
| `050g` | Conference Room 3A — Acoustic Environment | SF_SamplingSurface (FOI) |
| `0510` | Array #001 Acoustic Monitoring Zone | SF_SamplingSurface (Sample) |
| `051g` | Campus Perimeter — Outdoor Acoustic Environment | SF_SamplingSurface (FOI) |

### 4.7 Datastreams (5)

| Server ID | Name | Parent System | Schema Fields |
|---|---|---|---|
| `071g2` | SSL Potential Sources — Array #001 | SSL Module `04kg` | numSources + 4× {x, y, z, energy} |
| `07202` | SST Tracked Sources — Array #001 | SST Module `04l0` | numTracks + 2× {id, tag, x, y, z, activity} |
| `072g2` | Geographic Lines of Bearing — Array #001 | SSL Module `04kg` | numBearings + 2× {sourceId, azimuth, elevation, energy} |
| `07302` | Triangulated 3D Source Positions | Tri Engine `04m0` | latitude, longitude, altitude, accuracy, confidence, numArrays |
| `073g2` | System Health and Status — Array #001 | DSP Pipeline `04k0` | cpuLoad, usbConnected, activeTrackCount, bufferHealth, threshold |

All datastreams use `obsFormat: "application/swe+json"` with nested `DataRecord` schemas (not `DataArray`, which proved more reliable with OSH).

### 4.8 Observations (21)

| Datastream | Count | Simulated Scenario |
|---|---|---|
| SSL Pots (`071g2`) | 5 | Speaker at ~70° azimuth + faint noise at ~210°, 8ms frame intervals |
| SST Tracks (`07202`) | 5 | Single tracked source (ID 42, "dynamic"), activity 0.92→0.96 |
| Geographic LOBs (`072g2`) | 5 | True-north bearing 70.0°→71.2°, matched to tracked source |
| Triangulated Positions (`07302`) | 3 | Position near (38.8985°N, 77.0355°W), accuracy improving 1.2→1.0m |
| System Status (`073g2`) | 3 | CPU 23.5→27.7%, USB connected, 1 active track, buffer ~98% |

All observations use realistic timestamps starting `2026-02-20T14:30:00Z` with physically plausible data progression.

### 4.9 Control Streams (1)

| Server ID | Name | Parent System | Parameters |
|---|---|---|---|
| `045g` | Detection Parameters Control — Array #001 | Actuator `04lg` | energyThreshold, trackingSensitivity, framesToConfirm, reason |

### 4.10 Commands (3 dispatched)

| Command | issueTime | Action |
|---|---|---|
| Lower Threshold | 2026-02-20T14:35:00Z | E_T: 600 → 400 (quiet environment) |
| Increase Sensitivity | 2026-02-20T14:40:00Z | T_new: 0.75 → 0.6, F_new: 10 → 8 (surveillance) |
| Reset Defaults | 2026-02-20T15:00:00Z | All parameters back to defaults |

All commands returned **202 Accepted** (async dispatch per S-14 — see Section 6).

---

## 5. Totals

| Resource Type | Count | CSAPI Part |
|---|---|---|
| Procedures | 5 | Part 1 |
| Systems (Platform + Subsystems) | 14 | Part 1 |
| Properties | 7 | Part 1 |
| Deployments | 5 | Part 1 |
| Sampling Features | 3 | Part 1 |
| Datastreams | 5 | Part 2 |
| Observations | 21 | Part 2 |
| Control Streams | 1 | Part 2 |
| Commands | 3 | Part 2 |
| **Total** | **64** | **All 9 types** |

---

## 6. OSH Server Quirks Encountered

Several server-specific behaviors were discovered during ingestion that diverge from the CSAPI standard or require specific payload formats. These are documented as **S-** numbered findings cross-referenced with other project testing:

### S-2: Observations require REST-created datastreams

Observations can only be POSTed to datastreams that were created via the REST API (writable). Driver-managed datastreams reject observation POSTs. This is why `ingest-part2.py` creates its own datastreams rather than using any pre-existing ones.

### S-9: Only `obsFormat: "application/swe+json"` accepted

Datastream creation rejects `obsFormat: "application/json"` (400 Bad Request) and `obsFormat: "application/om+json"` (500 Internal Server Error). Only `"application/swe+json"` produces a 201 Created.

### S-10: ControlStream response field names differ from create

The CREATE payload uses `commandFormat` + `parametersSchema`, but the server's GET response returns `cmdFormat` + `commandSchema`. This asymmetry must be handled by any client implementation.

### S-14: Commands use async dispatch (fire-and-forget)

Command POSTs wait approximately 30 seconds for an actuator acknowledgment before returning **202 Accepted** with an HTML error body. Commands are NOT persisted as queryable resources — `GET /controlstreams/{id}/commands` always returns `{"items": []}`. This is expected behavior for systems without a real actuator connected.

### S-15: `type` must be first JSON property in SWE Common objects

OSH uses a streaming/ordered JSON parser for SWE Common. If `"type": "DataRecord"` (or `"Quantity"`, `"Count"`, etc.) is not the first property in each JSON object, the server fails to parse the schema correctly. All schemas in both scripts ensure `type` appears first.

### Content-Type requirements

| Resource | Content-Type |
|---|---|
| Systems, Deployments, Sampling Features | `application/geo+json` |
| Properties | `application/json` |
| Datastreams, Observations, Control Streams, Commands | `application/json` |

The original Part 1 script used `application/om+json` for observations, which caused 302 redirects (silent rejection). The corrected Part 2 script uses `application/json` for all Part 2 resources.

### 302 Redirect = Silent Rejection

OSH returns **302 Found** (redirect to HTML landing page) when a POST payload is malformed but the endpoint exists. Python `requests` follows this redirect by default, making it appear as a 200 success when it's actually a rejection. Both scripts use `allow_redirects=False` to catch this.

---

## 7. Payload Format Discovery

The critical discovery was the correct datastream creation format. The initial script used a flat structure with top-level `observedProperties`, `resultType`, and `validTime` — which the server silently rejected (302).

### Wrong format (Part 1 script, not working for OSH):
```json
{
  "name": "...",
  "outputName": "...",
  "observedProperties": [...],
  "resultType": "record",
  "validTime": [...]
}
```

### Correct format (Part 2 script, confirmed 201):
```json
{
  "name": "...",
  "outputName": "...",
  "schema": {
    "obsFormat": "application/swe+json",
    "recordSchema": {
      "type": "DataRecord",
      "fields": [...]
    }
  }
}
```

Similarly for control streams:
```json
{
  "name": "...",
  "inputName": "...",
  "schema": {
    "commandFormat": "application/swe+json",
    "parametersSchema": {
      "type": "DataRecord",
      "fields": [...]
    }
  }
}
```

And for observations (simple flat result matching schema field names):
```json
{
  "phenomenonTime": "2026-02-20T14:30:00.000+00:00",
  "resultTime": "2026-02-20T14:30:00.001+00:00",
  "result": {
    "numSources": 2,
    "source0": {"x": 0.9397, "y": 0.342, "z": 0.0, "energy": 0.85},
    "source1": {"x": -0.5, "y": -0.866, "z": 0.0, "energy": 0.25}
  }
}
```

The reference implementation was found in `demo/src/pages/SmokeTestPage.vue` (lines 120-210), which contains the only confirmed 201-returning payloads in the codebase.

---

## 8. Data Model Design Decisions

### Nested DataRecords vs DataArrays

The data model uses **named nested DataRecords** (`source0`, `source1`, `source2`, `source3`) rather than a single `DataArray` with `elementCount: 4`. This was chosen because:

1. The SmokeTestPage.vue reference implementation uses DataRecords (proven working)
2. DataArrays require careful `elementCount`/`elementType` nesting that may trigger S-15 ordering issues
3. Named fields make observation result JSON more readable and self-documenting

### Observation Data Realism

All observation data follows physically plausible progressions:
- **SSL**: Speaker at azimuth 70° drifting slowly (0.3°/frame), energy stable at 0.85–0.89
- **SST**: Single persistent track (ID 42), activity increasing 0.92→0.96 as tracker gains confidence
- **LOB**: Geographic bearings matching SSL directions after coordinate transform
- **Triangulation**: Position converging with improving accuracy (1.2m → 1.0m) as particle filter refines
- **Status**: CPU load rising slightly (23.5% → 27.7%), buffer healthy, USB connected

### Temporal Design

- SSL/SST/LOB frames: 8ms intervals (matching ODAS ~125 Hz frame rate at 16 kHz / 128 hop)
- Triangulation: 50ms intervals (cross-array fusion runs slower)
- System status: 5-second intervals (periodic health check)
- Commands: sparse, operator-initiated at +5min, +10min, +30min offsets

---

## 9. Verification

A verification script confirmed all resources were queryable via the API:

```
SSL Module (04kg): 2 datastreams, 10 observations
SST Module (04l0): 1 datastream, 5 observations
DSP Pipeline (04k0): 4 datastreams (inherited from children), 18 observations
Triangulation Engine (04m0): 1 datastream, 3 observations
Config Actuator (04lg): 1 control stream
```

Note: The DSP Pipeline (`04k0`) shows 4 datastreams because OSH propagates child-system datastreams to parent systems. The 5th datastream (System Status) is directly owned by the DSP Pipeline, while SSP Pots and Geographic LOBs belong to the SSL child, and SST Tracks belongs to the SST child. All appear under the DSP Pipeline via inheritance.

---

## 10. Files in This Directory

| File | Description |
|---|---|
| `.gitkeep` | Directory placeholder |
| `initial-planning-notes.md` | ODAS research, architecture analysis, CSAPI mapping strategy |
| `IROS2017-multi-array-localization.pdf` | Lauzon et al. paper on multi-array 3D acoustic localization |
| `sosa-ssn-csapi-data-model.md` | Complete SOSA/SSN → CSAPI data model with JSON payloads |
| `ingest-odas-data-model.py` | Part 1 ingestion script (procedures, systems, properties, deployments, sampling features) |
| `ingest-part2.py` | Part 2 ingestion script (datastreams, observations, control streams, commands) |
| `fix-associations.py` | One-time script to add `@link` association fields to existing server resources |
| `ingestion-report.md` | This report |

---

## 11. Cross-Resource Associations (`@link` Fields)

### Problem

After initial ingestion, the CSAPI Explorer Detail view for any system showed **"Deployments: 0 / None found"** and **"Procedures: 0 / None found"**. The original payloads lacked `@link` association fields that connect systems to their procedures and deployments to their deployed systems.

### CSAPI Association Mechanism

The CSAPI spec defines several `@link` property fields for cross-resource references:

| Field | Location | Purpose | Format |
|---|---|---|---|
| `systemKind@link` | System properties | Links System → Procedure | `{ href, rel: "systemKind", title }` |
| `platform@link` | Deployment properties | Links Deployment → Platform System | `{ href, rel: "platform", title }` |
| `deployedSystems@link` | Deployment properties | Links Deployment → Deployed Systems | `[{ href, rel: "deployedSystem", title }]` |

### What Was Added

**12 systems** received `systemKind@link` pointing to their procedure:

| System | Procedure | Link |
|---|---|---|
| Mic Array (`04g0`) | PDM Audio Capture (`0480`) | ✅ Persisted |
| Mics #1–#7 (`04gg`–`04jg`) | PDM Audio Capture (`0480`) | ✅ Persisted |
| SSL Module (`04kg`) | SRP-PHAT Beamforming (`048g`) | ✅ Persisted |
| SST Module (`04l0`) | Particle Filter Tracking (`0490`) | ✅ Persisted |
| Config Actuator (`04lg`) | Config Actuation (`04a0`) | ✅ Persisted |
| Triangulation Engine (`04m0`) | Ray-to-Ray Triangulation (`049g`) | ✅ Persisted |

**5 deployments** received `platform@link` and `deployedSystems@link`:

| Deployment | Platform | deployedSystems |
|---|---|---|
| Single Array (`049g`) | Platform (`04fg`) ✅ | Platform (`04fg`) ❌ Dropped |
| Multi-Array (`04a0`) | Platform (`04fg`) ✅ | Platform (`04fg`) ❌ Dropped |
| North sub (`04ag`) | Platform (`04fg`) ✅ | Platform (`04fg`) ❌ Dropped |
| SE sub (`04b0`) | Platform (`04fg`) ✅ | Platform (`04fg`) ❌ Dropped |
| SW sub (`04bg`) | Platform (`04fg`) ✅ | Platform (`04fg`) ❌ Dropped |

### OSH Server Behavior

| Feature | Status | Notes |
|---|---|---|
| `systemKind@link` persistence | ✅ Works | GET returns the field after PUT |
| `platform@link` persistence | ✅ Works | GET returns the field after PUT |
| `deployedSystems@link` persistence | ❌ Silently dropped | PUT returns 204 but field not in subsequent GET |
| `/systems/{id}/procedures` | ❌ 400 | "Invalid resource name" — endpoint not implemented |
| `/systems/{id}/deployments` | ❌ 400 | "Invalid resource name" — endpoint not implemented |
| `/deployments/{id}/systems` | ❌ 400 | "Invalid resource name" — endpoint not implemented |
| `/deployments?system={id}` | ❌ 500 | Internal server error (crash) |
| System `links` array | ⚠️ Partial | Only includes `subsystems`, `samplingFeatures`, `datastreams`, `controlstreams` |

---

## 12. Explorer `@link` Fallback

### Problem

The CSAPI Explorer (`ResourceDetail.vue`) relies exclusively on **navigation endpoints** (e.g., `/systems/{id}/procedures`) to populate related-resource panels. Since OSH doesn't implement these endpoints (returns 400), the panels always showed "0 / None found".

### Solution

Added a `tryLinkFallback()` function to `demo/src/components/ResourceDetail.vue` that activates when a navigation endpoint returns HTTP 400. It uses the `@link` property fields instead:

| Relation | Fallback Strategy |
|---|---|
| System → Procedures | Follow `systemKind@link.href` to fetch the linked procedure |
| System → Deployments | Fetch `/deployments?limit=100`, filter client-side by `platform@link.href` matching system URL |
| Deployment → Systems | Follow `deployedSystems@link[]` hrefs (limited by OSH dropping the field) |
| Procedure → Systems | Fetch `/systems?limit=100`, filter by `systemKind@link.href` matching procedure URL |

The fallback is triggered only on 400 responses, preserving normal behavior on spec-compliant servers.

### Files Modified

| File | Change |
|---|---|
| `demo/src/components/ResourceDetail.vue` | Added `tryLinkFallback()` (~105 lines), modified `fetchRelation()` 400 handler |
| `docs/.../fix-associations.py` | One-time script to add `@link` fields to existing server resources |
| `docs/.../ingest-odas-data-model.py` | Updated to include `@link` fields in original creation payloads |

---

## 13. Reproducing the Ingestion

To re-run the ingestion on a fresh server:

```bash
# Part 1: Create foundational resources (procedures, systems, properties, etc.)
python ingest-odas-data-model.py

# Note the server-assigned system IDs from Part 1 output, then update
# the SYSTEM_IDS dict in ingest-part2.py if they differ from:
#   ssl_module: 04kg, sst_module: 04l0, dsp_pipeline: 04k0,
#   tri_engine: 04m0, config_actuator: 04lg

# Part 2: Create datastreams, observations, control streams, commands
python ingest-part2.py
```

Both scripts are idempotent for Part 1 (409 Conflict on duplicate UIDs) but Part 2 observations will create duplicates on re-run (observations have no UID deduplication).

**Requirements:** Python 3.8+, `requests` library (`pip install requests`).

**Server credentials:** HTTP Basic Auth, username `ogc`, password `ogc`.

**Expected runtime:** Part 1 ≈ 15 seconds, Part 2 ≈ 30 seconds (+ ~90 seconds if commands are dispatched, due to S-14 async wait).
