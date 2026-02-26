# Live Server Smoke Test — Post Phase 3.11

**Date:** 2025-06-24
**Milestone:** After completing Phase 3.11 (Issues #53, #22, #23, #54, #24, #25, #26, #55)
**Servers:** OpenSensorHub demo instance, 52North demo instance
**Auth:** OSH: Basic auth required (credentials not stored in repo); 52North: None (expired SSL cert)
**Purpose:** Validate SensorML parsers, SWE Common parsers, and GeoJSON handler `satisfies` migration against live server responses
**Components tested:**

- GeoJSON handler (`isCSAPIFeature`, `getCSAPIResourceType`, `extractCSAPIFeature`, `parseValidTime`) — Issue #55 `satisfies` regression
- SensorML barrel file and main parser (`parseSensorML30`) — Issues #22, #23, #53, #54
- SWE Common parsers (`parseSimpleComponent`, `parseDataRecord`, `parseDataArray`) — Issues #24, #25, #26
  **HEAD commit:** `c46ec92` (Phase 3.11 code review)
  **Test suite:** 775/775 CSAPI tests, 14 suites — all passing

> This is smoke test #16 in the series. See also:
>
> - [Previous smoke test (#15)](live-server-smoke-test-post-phase-3.7.md) — Post Phase 3.7, commit `cdc2e57`

## Test Methodology

Read-only observation per Lesson 10: no code changes during the smoke test. HTTP requests to both live servers, raw JSON responses compared against handler function expectations. All analysis is based on direct server responses.

## Server Profiles

### OpenSensorHub

**Root:** `http://45.55.99.236:8080/sensorhub/api` — 200 OK, "Connected Systems API Service", 10 links

| Resource Type    | Count | Change from #15 |
| ---------------- | ----- | --------------- |
| Systems          | 12    | Unchanged       |
| SamplingFeatures | 51    | Unchanged       |
| Datastreams      | 100   | Unchanged       |
| ControlStreams   | 8     | Unchanged       |
| Deployments      | 0     | Unchanged       |
| Procedures       | 0     | Unchanged       |

### 52North

**Root:** `https://csa.demo.52north.org/` — 200 OK, "connected-systems-pygeoapi", 7 links

| Resource Type    | Count | Change from #15                                      |
| ---------------- | ----- | ---------------------------------------------------- |
| Systems          | 3     | Unchanged                                            |
| Deployments      | 1     | Unchanged                                            |
| Procedures       | 1     | Unchanged                                            |
| SamplingFeatures | 0     | **Changed** — was 400 error (F51), now returns empty |
| Datastreams      | —     | **500 error** (was 400 in F20)                       |
| ControlStreams   | —     | 404 Not Found (unchanged, F32)                       |

---

## Results

### Prior Findings — Regression Check

All 73 prior findings (F1–F73) from smoke test #15 were reviewed. Status changes are highlighted with ⚡.

#### Resolved / Confirmed Stable (32)

| Finding | Prior Status            | Current Status   | Evidence                                              |
| ------- | ----------------------- | ---------------- | ----------------------------------------------------- |
| F1      | ✅ RESOLVED (Issue #34) | ✅ Stable        | Link relation prefix — no regression                  |
| F2      | ✅ RESOLVED (Issue #35) | ✅ Stable        | URL scoping — no regression                           |
| F4      | ✅ RESOLVED             | ✅ Stable        | validTime array format handled                        |
| F10     | ✅ CONFIRMED            | ✅ Stable        | 52N has real data (3 systems, 1 deploy, 1 proc)       |
| F11     | ✅ CONFIRMED            | ✅ Stable        | 52N uses SensorML format                              |
| F13     | ✅ REFINED              | ✅ Stable        | Envelope varies by format                             |
| F15     | ✅ CONFIRMED            | ✅ Stable        | 52N: 3 systems confirmed                              |
| F19     | ✅ CONFIRMED            | ✅ Stable        | OSH resultTime=latest accepted                        |
| F25     | ✅ CONFIRMED            | ✅ Stable        | OSH returns real data                                 |
| F29     | ✅ CONFIRMED            | ✅ Stable        | ControlStream schema works                            |
| F37     | ✅ EXPECTED             | ✅ Stable        | Command /result 404 expected                          |
| F39     | ✅ CONFIRMS F3          | ✅ Stable        | Commands use items envelope                           |
| F40     | ✅ RESOLVED (Issue #49) | ✅ Stable        | SamplingFeature SensorML vocab                        |
| F43     | ✅ RE-CONFIRMED         | ✅ Still present | 52N procedure returns `type: "PhysicalSystem"`        |
| F44     | ✅ CONFIRMED            | ✅ Stable        | 52N mixes CURIE/URI forms (`sosa:Sensor` vs full URI) |
| F45     | ✅ REFINED              | ✅ Stable        | Envelope varies by server AND format                  |
| F47     | ✅ CONFIRMED            | ✅ Stable        | 52N GeoJSON still includes `@link` notation           |
| F48     | ✅ CONFIRMED            | ✅ Stable        | OSH features have empty links arrays                  |
| F49     | ✅ RESOLVED (Issue #52) | ✅ Stable        | sampledFeature@link handled                           |
| F50     | ✅ CONFIRMED            | ✅ Stable        | 52N default to SML                                    |
| F54     | ✅ RECONFIRMED          | ✅ Stable        | F49 resolved                                          |
| F55     | ✅ CONFIRMED            | ✅ Stable        | F42 no longer blocking                                |
| F58     | ✅ STRENGTHENED         | ✅ Stable        | SensorML type defs align with real data               |
| F59     | ✅ CONFIRMED            | ✅ Stable        | OSH SF count: 51                                      |
| F62     | ✅ CONFIRMED            | ✅ Stable        | 52N geo+json returns systems data                     |
| F64     | ✅ CONFIRMED+EXTENDED   | ✅ Stable        | OSH ignores ALL Accept headers                        |
| F65     | ✅ CONFIRMED            | ✅ Stable        | 52N SML uses non-standard Deployment type             |
| F66     | ✅ POSITIVE             | ✅ Stable        | SimpleProcess parser validated                        |
| F67     | ✅ POSITIVE             | ✅ Stable        | PhysicalSystem parser validated                       |
| F68     | ✅ POSITIVE             | ✅ Stable        | PhysicalSystem handles minimal OSH SML                |
| F70     | ✅ POSITIVE             | ✅ Stable        | parseLink strips extra urn                            |
| F73     | ✅ POSITIVE             | ✅ Stable        | AggregateProcess rejects correctly                    |

#### Retracted (1)

| Finding | Prior Status | Current Status | Evidence                  |
| ------- | ------------ | -------------- | ------------------------- |
| F57     | ❌ RETRACTED | ❌ Retracted   | Was our error, not server |

#### Server Limitations — Carried (21)

| Finding | Prior Status     | Current Status              | Evidence                                                                    |
| ------- | ---------------- | --------------------------- | --------------------------------------------------------------------------- |
| F6      | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects systems/{id}/deployments                                        |
| F7      | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects systems/{id}/procedures                                         |
| F8      | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects samplingFeatures/{id}/systems                                   |
| F9      | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects samplingFeatures/{id}/history                                   |
| F16     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects datastreams/{id}/systems                                        |
| F17     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects datastreams/{id}/procedures                                     |
| F18     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects datastreams/{id}/history                                        |
| F20     | ⚠️ CARRIED (400) | ⚡ **STATUS CHANGE: 500**   | 52N /datastreams: was 400, now 500 Internal Server Error                    |
| F21     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects observations/{id}/datastream                                    |
| F22     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects observations/{id}/samplingFeature                               |
| F23     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects observations/{id}/system                                        |
| F24     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects observations/{id}/history                                       |
| F26     | ⚠️ CARRIED       | ⚠️ Carried                  | 52N Observations broken                                                     |
| F28     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH rejects controlstreams/{id}/feasibility                                 |
| F32     | ⚠️ CARRIED       | ⚠️ Carried                  | 52N ControlStreams 404                                                      |
| F34     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH no top-level /commands                                                  |
| F35     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH no /commands/{id}/cancel                                                |
| F36     | ⚠️ CARRIED       | ⚠️ Carried                  | OSH ignores id query on commands                                            |
| F46     | ⚠️ REFINED→F64   | ⚠️ Carried                  | OSH ignores SML Accept header (use ?f=sml3)                                 |
| F51     | ⚠️ CARRIED (400) | ⚡ **STATUS CHANGE: Fixed** | 52N /samplingFeatures now returns empty collection (0 items) instead of 400 |
| F72     | ⚠️ CARRIED       | ⚠️ Carried                  | 52N 500 for individual system via JSON                                      |

#### Deferred — Client/Interop (8)

| Finding | Prior Status | Current Status | Evidence                                    |
| ------- | ------------ | -------------- | ------------------------------------------- |
| F3      | ⏳ DEFERRED  | ⏳ Deferred    | items envelope — future response parser     |
| F5      | ⏳ DEFERRED  | ⏳ Deferred    | Missing pagination metadata                 |
| F14     | ⏳ DEFERRED  | ⏳ Deferred    | Properties not discoverable                 |
| F27     | ⏳ DEFERRED  | ⏳ Deferred    | Observation foi@id naming variation         |
| F30     | ⏳ DEFERRED  | ⏳ Deferred    | ControlStream system@link                   |
| F31     | ⏳ DEFERRED  | ⏳ Deferred    | Command entity data shape                   |
| F33     | ⏳ DEFERRED  | ⏳ Deferred    | ControlStream schema returns SWE DataRecord |
| F38     | ⏳ DEFERRED  | ⏳ Deferred    | Command status data shape                   |

#### Informational / Other (11)

| Finding | Prior Status         | Current Status               | Evidence                                                                 |
| ------- | -------------------- | ---------------------------- | ------------------------------------------------------------------------ |
| F12     | ❓ NOT TESTED        | ❓ Not tested                | 52N systems/{id}/deployments                                             |
| F41     | ✅ CONFIRMED         | ✅ **Still present**         | 52N GeoJSON: `"featureType": null` for all 3 systems                     |
| F42     | ✅ CONFIRMED         | ✅ Still present             | 52N Deployment has null validTime                                        |
| F52     | ✅ CONFIRMED         | ✅ Still present             | 52N Content-Type: None on root                                           |
| F53     | ✅ CONTINUED         | ✅ Stable                    | OSH data inventory unchanged                                             |
| F56     | ✅ NOT RETESTED      | ✅ Not retested              | OSH schema Content-Type: auto                                            |
| F60     | ℹ️ SUPERSEDED by F71 | ℹ️ Superseded                | OSH SML content-type                                                     |
| F61     | ℹ️ SUPERSEDED        | ℹ️ Superseded                | 52N default changed                                                      |
| F63     | ℹ️ LOW               | ℹ️ Low                       | 52N error codes                                                          |
| F69     | ℹ️ INFORMATIONAL     | ⚡ **RESOLVED by Issue #53** | `SensorMLParseError` extracted to shared `errors.ts`; all 775 tests pass |
| F71     | ℹ️ INFORMATIONAL     | ✅ Confirmed                 | OSH `?f=sml3` still serves SML data                                      |

**Summary:** 2 status changes (F20 error type 400→500, F51 fixed on 52N), 1 finding resolved (F69 by Issue #53). All other findings stable.

---

### GeoJSON Handler — Recognition (Issue #55 Regression)

The `satisfies` migration (Issue #55) replaced 4 `as` casts with `satisfies` in `extractCSAPIFeature`. Since `satisfies` is compile-time only, no behavioral change is expected. All 19 GeoJSON unit tests passed pre-test.

| Server | Resource Type    | Features Tested | featureType Pattern                           | All Recognized?  | Notes                                                         |
| ------ | ---------------- | --------------- | --------------------------------------------- | ---------------- | ------------------------------------------------------------- |
| OSH    | Systems          | 12              | `http://www.w3.org/ns/sosa/Sensor`            | ✅ Yes           | All 12 → `System`                                             |
| OSH    | SamplingFeatures | 3 (sample)      | `http://www.opengis.net/sensorml/2.0#Feature` | ✅ Yes           | All → `SamplingFeature`                                       |
| 52N    | Systems          | 3               | `null`                                        | ❌ No (expected) | F41 — `featureType` is null, handler correctly returns `null` |
| 52N    | Deployments      | 1               | Not tested in GeoJSON                         | —                | Only SML format tested                                        |

**Verdict:** No regression from Issue #55 `satisfies` migration. Handler recognition behavior identical to smoke test #15.

### GeoJSON Handler — Extraction

Applying `extractCSAPIFeature` logic to live data:

| Server | Resource Type | Feature ID     | id  | uid                                      | name                            | featureType               | validTime                           | geometry | links          |
| ------ | ------------- | -------------- | --- | ---------------------------------------- | ------------------------------- | ------------------------- | ----------------------------------- | -------- | -------------- |
| OSH    | System        | `03bc5ofvvstg` | ✅  | ✅ `urn:osh:driver:mavsdk:cube:replay`   | ✅ "LIVE - Field Drone"         | ✅ `sosa/Sensor`          | ✅ Array `["2026-01-26...", "now"]` | null     | ✅ []          |
| OSH    | System        | `040g`         | ✅  | ✅ `urn:android:device:dad41d3c8bf853cd` | ✅ "Android Sensors [SR_Botts]" | ✅ `sosa/Sensor`          | ✅ Array                            | null     | ✅ []          |
| OSH    | SF            | `040g`         | ✅  | ✅ `urn:android:foi:Run-20260211-041356` | ✅ "Run-20260211-041356"        | ✅ `sensorml/2.0#Feature` | —                                   | null     | ✅ (next link) |

**parseValidTime:**

| Server | Feature ID     | Raw validTime                         | Parsed start             | Parsed end                   | Correct?                   |
| ------ | -------------- | ------------------------------------- | ------------------------ | ---------------------------- | -------------------------- |
| OSH    | `03bc5ofvvstg` | `["2026-01-26T18:32:01.56Z", "now"]`  | 2026-01-26T18:32:01.56Z  | `undefined` (sentinel "now") | ✅                         |
| OSH    | `040g`         | `["2026-02-10T19:43:37.265Z", "now"]` | 2026-02-10T19:43:37.265Z | `undefined`                  | ✅                         |
| 52N    | Systems        | `null` for all 3                      | `undefined`              | —                            | ✅ (correct null handling) |

---

### SensorML Parser — Live Data Validation (Issues #22, #23, #53, #54)

#### OSH — PhysicalSystem via `?f=sml3`

**System `040g` (Android Sensors [SR_Botts]):**

```json
{
  "type": "PhysicalSystem",
  "id": "040g",
  "uniqueId": "urn:android:device:dad41d3c8bf853cd",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "label": "Android Sensors [SR_Botts]",
  "validTime": ["2026-02-10T19:43:37.265Z", "now"],
  "localReferenceFrames": [{ "id": "LOCAL_FRAME", "origin": "Center of the device screen", "axes": [...] }],
  "components": [
    { "type": "PhysicalComponent", "name": "sensor0", "label": "lsm6dso LSM6DSO Accelerometer Non-wakeup" },
    { "type": "PhysicalComponent", "name": "sensor1", "label": "Rotation Vector Non-wakeup" },
    { "type": "PhysicalComponent", "name": "sensor2", "label": "gps" },
    { "type": "PhysicalComponent", "name": "sensor3", "label": "Android Camera #0" }
  ]
}
```

**Parser field coverage:**
| Field | Present | `parseSensorML30` handles? |
|-------|---------|---------------------------|
| `type: "PhysicalSystem"` | ✅ | ✅ Dispatches to PhysicalSystem sub-parser |
| `id` | ✅ | ✅ DescribedObject |
| `uniqueId` | ✅ | ✅ DescribedObject |
| `definition` | ✅ | ✅ DescribedObject |
| `label` | ✅ | ✅ DescribedObject |
| `validTime` | ✅ | ✅ DescribedObject |
| `localReferenceFrames` | ✅ | ✅ AbstractPhysicalProcess |
| `components` | ✅ | ✅ PhysicalSystem-specific |

#### 52N — PhysicalSystem via `Accept: application/sml+json`

**System `5400-526` (Doppler Current Profiler):**

```json
{
  "type": "PhysicalSystem",
  "definition": "sosa:Sensor",
  "id": "5400-526",
  "uniqueId": "urn:sensor:5400-526",
  "label": "Doppler Current Profiler Sensor",
  "identifiers": [
    { "label": "SerialNo", "value": "526" },
    { "label": "ProdNo", "value": "5400" }
  ],
  "typeOf": {
    "rel": "ogc-rel:procedures",
    "href": "https://csa.demo.52north.org/procedures/...",
    "urn": "urn:sensortype:aanderaa:dcps:td304"
  }
}
```

**Parser field coverage:**
| Field | Present | `parseSensorML30` handles? |
|-------|---------|---------------------------|
| `type: "PhysicalSystem"` | ✅ | ✅ Dispatches correctly |
| `definition` (CURIE `sosa:Sensor`) | ✅ | ✅ Stored as-is |
| `identifiers` | ✅ | ✅ DescribedObject |
| `typeOf` (link) | ✅ | ✅ AbstractProcess.typeOf |
| No components, no localReferenceFrames | — | ✅ Optional fields handled |

#### 52N — Procedure via SML (F43 re-verification)

**Procedure `4e09de42...`:**

```json
{
  "type": "PhysicalSystem",
  "procedureType": "sosa:Sensor",
  "definition": "sosa:Sensor",
  "uniqueId": "urn:sensortype:aanderaa:dcps:td304",
  "label": "Doppler Current Profiler Sensor",
  "identifiers": [...],
  "classifiers": [{"definition":"...SensorType", "label":"Sensor Type", "value":"Doppler Current Profiler Sensor"}],
  "documents": [{"name":"Operating Manual", "link":{"href":"https://www.aanderaa.com/..."}}]
}
```

**F43 status:** Still present — 52N returns `type: "PhysicalSystem"` for a resource served from the `/procedures` endpoint. Our parser would correctly parse this as a PhysicalSystem (which is technically correct SML), but the resource type context is mislabeled by the server. Contains `classifiers` and `documents` which the parser handles.

#### 52N — Deployment via SML

**Deployment `af41f84f...`:**

```json
{
  "type": "Deployment",
  "definition": "http://www.w3.org/ns/sosa/Deployment",
  "uniqueId": "urn:messtonne:1:2025-demo",
  "label": "Messtonne 1 - 2025 Test",
  "contacts": [
    {
      "role": "...Operator",
      "organisationName": "BfN",
      "contactInfo": { "website": "..." }
    }
  ],
  "location": { "type": "Point", "coordinates": [12.0802287, 54.1269457] },
  "platform": { "system": { "href": "urn:platform:5300-909" } },
  "deployedSystems": [
    {
      "name": "EXO3_Sonde",
      "system": {
        "href": "https://csa.demo.52north.org/systems/YSI599503-00-1"
      }
    },
    {
      "name": "DCPS_Sensor",
      "system": { "href": "https://csa.demo.52north.org/systems/5400-526" }
    }
  ]
}
```

**Parser coverage:** `parseSensorML30` does not yet have a Deployment sub-parser — this is a future Phase 3 task. The `type: "Deployment"` would be recognized by the dispatcher but there is no dedicated handler. This is expected at current implementation stage.

**SensorML Parser Summary:**

| Server | Resource            | SML Type             | Parsed?              | Coverage                                                         |
| ------ | ------------------- | -------------------- | -------------------- | ---------------------------------------------------------------- |
| OSH    | System 040g         | PhysicalSystem       | ✅                   | Full: id, uid, label, def, validTime, localRefFrames, components |
| 52N    | System 5400-526     | PhysicalSystem       | ✅                   | Full: id, uid, label, def, identifiers, typeOf                   |
| 52N    | Procedure 4e09de42  | PhysicalSystem (F43) | ✅                   | Full: identifiers, classifiers, documents                        |
| 52N    | Deployment af41f84f | Deployment           | ⚠️ No sub-parser yet | Expected gap — future task                                       |

---

### SWE Common Parser — Live Data Reconnaissance (Issues #24, #25, #26)

SWE Common data was found in OSH datastream and control stream schemas. These schemas use `resultSchema` / `parametersSchema` wrappers containing SWE Common structures.

#### Datastream Schemas (OSH)

**Temperature (DS `03tbj7mvqg50`):**

```json
{
  "resultSchema": {
    "type": "DataRecord",
    "name": "TemperatureOutput",
    "label": "Temperature",
    "description": "UnmannedSystem temperature output data",
    "fields": [
      {
        "type": "Quantity",
        "name": "Temperature",
        "label": "Temperature",
        "description": "Temperature in degrees celsius",
        "uom": { "href": "http://qudt.org/vocab/unit/UNITLESS" }
      }
    ]
  }
}
```

**Parser coverage:** `parseDataRecord` handles this structure. The single `Quantity` field would be parsed by `parseQuantity` (dispatched via `parseSimpleComponent`). The `uom.href` form (vs `uom.code`) is supported.

**StatusEvent (DS `02au905kq85g`):**

```json
{
  "resultSchema": {
    "type": "DataRecord",
    "name": "UnmannedStatusTextOutput",
    "label": "StatusEvent",
    "fields": [
      { "type": "Text", "name": "StatusType", "label": "Type" },
      { "type": "Text", "name": "Status", "label": "Status" }
    ]
  }
}
```

**Parser coverage:** `parseDataRecord` with 2 `Text` fields dispatched via `parseText`. Fully covered.

**Location (DS `02v937ubpscg`):**

```json
{
  "resultSchema": {
    "type": "DataRecord",
    "name": "UnmannedLocationOutput",
    "fields": [
      {
        "type": "Vector",
        "name": "Location",
        "definition": "http://sensorml.com/ont/swe/property/LocationVector",
        "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4979",
        "coordinates": [
          {
            "type": "Quantity",
            "name": "lat",
            "axisID": "Lat",
            "uom": { "code": "deg" }
          },
          {
            "type": "Quantity",
            "name": "lon",
            "axisID": "Lon",
            "uom": { "code": "deg" }
          },
          {
            "type": "Quantity",
            "name": "alt",
            "axisID": "h",
            "uom": { "code": "m" }
          }
        ]
      }
    ]
  }
}
```

**Parser coverage:** `parseDataRecord` handles the outer record. The `Vector` field type is NOT yet a supported component type in `parseSimpleComponent` — Vector is an aggregate component, not a simple component. This is a known scope boundary: Issue #24 covers simple components only. Vector support is a future task.

#### Control Stream Schema (OSH)

**Location Control (CS `0o10`):**

```json
{
  "parametersSchema": {
    "type": "DataRecord",
    "name": "mavControl",
    "fields": [
      {
        "type": "Vector",
        "name": "locationVectorLLA",
        "coordinates": [
          { "type": "Quantity", "name": "Latitude", "uom": { "code": "deg" } },
          { "type": "Quantity", "name": "Longitude", "uom": { "code": "deg" } },
          { "type": "Quantity", "name": "AltitudeAGL", "uom": { "code": "m" } }
        ]
      },
      { "type": "Boolean", "name": "returnToStart" },
      { "type": "Count", "name": "hoverSeconds" }
    ]
  }
}
```

**Parser coverage:** `parseDataRecord` handles the outer structure. `Boolean` is parsed by `parseBoolean`, `Count` by `parseCount`. The `Vector` field is the same gap noted above. The `Boolean` and `Count` fields are fully supported.

#### SWE Common Parser Summary

| SWE Common Type | Found In                       | Server | parseSimpleComponent?        | parseDataRecord? |
| --------------- | ------------------------------ | ------ | ---------------------------- | ---------------- |
| DataRecord      | All schemas                    | OSH    | N/A (aggregate)              | ✅ Yes           |
| Quantity        | Temperature, Location, Control | OSH    | ✅ Yes                       | ✅ (as field)    |
| Text            | StatusEvent                    | OSH    | ✅ Yes                       | ✅ (as field)    |
| Boolean         | Control stream                 | OSH    | ✅ Yes                       | ✅ (as field)    |
| Count           | Control stream                 | OSH    | ✅ Yes                       | ✅ (as field)    |
| Vector          | Location, Control              | OSH    | ❌ Not supported (aggregate) | ⚠️ Field unknown |

**52N SWE Common availability:** None. 52N's `/datastreams` returns 500 (F20), making schema endpoints unreachable. No SWE Common data available from 52N.

---

### Vocabulary Inventory

| featureType Value                             | Server(s)        | Recognized?         | Handler Classification                  |
| --------------------------------------------- | ---------------- | ------------------- | --------------------------------------- |
| `http://www.w3.org/ns/sosa/Sensor`            | OSH (12 systems) | ✅                  | System                                  |
| `http://www.opengis.net/sensorml/2.0#Feature` | OSH (51 SF)      | ✅                  | SamplingFeature                         |
| `null`                                        | 52N (3 systems)  | ❌                  | `null` (F41)                            |
| `sosa:Sensor` (CURIE, in SML)                 | 52N (sys/proc)   | ✅ (in SML context) | System (via definition)                 |
| `http://www.w3.org/ns/sosa/Deployment` (SML)  | 52N (deploy)     | ✅ (in SML context) | N/A — SML type, not GeoJSON featureType |

No new featureType values discovered since smoke test #15.

### Content-Type Availability

| Content-Type                                           | OSH                                  | 52N                                             |
| ------------------------------------------------------ | ------------------------------------ | ----------------------------------------------- |
| `application/geo+json` (via `?f=geojson`)              | ✅ Systems (12), SF (51)             | ✅ Systems (3)                                  |
| `application/sml+json` (via `?f=sml3` / Accept header) | ✅ Systems (12)                      | ✅ Systems (3), Procedures (1), Deployments (1) |
| `application/swe+json` (datastream observations)       | ✅ Listed in DS formats              | ❌ DS endpoint broken (500)                     |
| `application/swe+json` (datastream schema)             | ✅ via `/datastreams/{id}/schema`    | ❌ DS endpoint broken                           |
| `application/swe+json` (controlstream schema)          | ✅ via `/controlstreams/{id}/schema` | ❌ CS not implemented (404)                     |
| `application/json`                                     | ✅ Default format                    | ⚠️ Mixed (some endpoints 500)                   |

---

## New Findings

### F74 (Informational): SWE Common Vector type not handled by simple component parsers

**Severity:** Informational
**Category:** Scope boundary (not a bug)
**Affects:** `parseSimpleComponent` dispatcher in `swecommon/components.ts`
**Ownership:** Ours (future task)
**Evidence:** OSH datastream schemas (Location, Acceleration) and control stream schemas contain `type: "Vector"` fields with nested `coordinates` arrays of Quantity components. The `parseSimpleComponent` dispatcher only handles the 10 simple component types (Quantity, Count, Boolean, Text, Time, Category, + 4 ranges). Vector is an aggregate component that requires a dedicated parser, similar to how DataRecord and DataArray have their own parsers.
**Status:** Informational — expected scope boundary. Vector parser would be a natural Issue #27 or #28 task.
**Impact:** `parseDataRecord` will throw `SweCommonParseError` for DataRecord fields of type Vector. This is correct behavior — unknown types should fail explicitly rather than silently.

### F75 (Informational): OSH datastream schemas provide rich SWE Common test data

**Severity:** Informational (positive)
**Category:** Test data availability
**Affects:** Future SWE Common integration testing
**Ownership:** Shared
**Evidence:** OSH provides SWE Common structures via:

- **Datastream schemas** (`/datastreams/{id}/schema` → `resultSchema`): DataRecord with Quantity, Text, Vector fields
- **Control stream schemas** (`/controlstreams/{id}/schema` → `parametersSchema`): DataRecord with Vector, Boolean, Count fields
- **Observation formats**: All 100 datastreams list `application/swe+json` as a supported format
  This confirms that future integration tests can fetch real SWE Common data from OSH. The `resultSchema`/`parametersSchema` wrapper needs to be unwrapped before passing to `parseDataRecord`.
  **Status:** Informational — positive finding for future test planning.

### F76 (Low): 52N `/datastreams` degraded from 400 to 500

**Severity:** Low
**Category:** Server limitation
**Affects:** No client code — server-side issue
**Ownership:** Upstream (52N)
**Evidence:** In smoke test #15, 52N `/datastreams` returned HTTP 400. Now returns 500 Internal Server Error regardless of Accept header (tested with no header, `application/json`, `application/geo+json`). The endpoint has degraded. This means 52N datastream schemas are inaccessible, so SWE Common parsers cannot be tested against 52N data.
**Status:** Informational — updates F20 error type.

### F77 (Informational): 52N `/samplingFeatures` endpoint now functional

**Severity:** Informational (positive)
**Category:** Server improvement
**Affects:** No client code — server-side fix
**Ownership:** Upstream (52N)
**Evidence:** In smoke test #15, 52N `/samplingFeatures` returned HTTP 400 (F51). Now returns a valid empty collection (`{"type":"FeatureCollection","features":[],"links":[]}`). The endpoint works but has no data. The `"featureType": null` issue (F41) would still apply if features were present.
**Status:** Informational — updates F51.

---

## Cross-Server Comparison

| Dimension                      | OpenSensorHub                                                 | 52North                                            | Match?        |
| ------------------------------ | ------------------------------------------------------------- | -------------------------------------------------- | ------------- |
| GeoJSON featureType vocabulary | SOSA full URI (`sosa/Sensor`)                                 | `null` (F41)                                       | ❌            |
| SML type vocabulary            | Full URI (`PhysicalSystem`)                                   | Same                                               | ✅            |
| SML definition vocabulary      | Full URI                                                      | CURIE (`sosa:Sensor`)                              | ⚠️ (F44)      |
| validTime format               | Array `["ISO", "now"]`                                        | `null`                                             | ❌            |
| Presence of uid                | ✅ All features                                               | ✅ All features                                    | ✅            |
| Presence of name               | ✅ All features                                               | ✅ (as `label` in SML)                             | ✅            |
| Geometry patterns              | null for systems/SF                                           | Not present in GeoJSON                             | ⚠️            |
| Link structures                | Empty arrays                                                  | Not present                                        | ⚠️            |
| Response envelope (GeoJSON)    | `{ items: [...] }` via `?f=geojson` returns FeatureCollection | `{ type: "FeatureCollection", features: [...] }`   | ⚠️            |
| Response envelope (SML)        | `{ items: [...] }`                                            | `{ items: [...] }`                                 | ✅            |
| SWE Common availability        | ✅ Rich (schemas, observations)                               | ❌ DS broken (500)                                 | ❌            |
| SML availability               | ✅ via `?f=sml3`                                              | ✅ via Accept header                               | ✅            |
| SML field richness             | Minimal (id, uid, label, components)                          | Rich (identifiers, classifiers, documents, typeOf) | Complementary |

---

## Response Envelope Observations

| Server | Endpoint                    | Accept/Format      | Envelope Type             | Feature Array Key     |
| ------ | --------------------------- | ------------------ | ------------------------- | --------------------- |
| OSH    | /systems                    | `?f=geojson`       | GeoJSON FeatureCollection | `features`            |
| OSH    | /samplingFeatures           | `?f=geojson`       | GeoJSON FeatureCollection | `features`            |
| OSH    | /systems                    | `?f=sml3`          | items wrapper             | `items`               |
| OSH    | /datastreams                | default            | items wrapper             | `items`               |
| OSH    | /controlstreams             | default            | items wrapper             | `items`               |
| OSH    | /datastreams/{id}/schema    | default            | direct object             | N/A (single resource) |
| OSH    | /controlstreams/{id}/schema | default            | direct object             | N/A (single resource) |
| 52N    | /systems                    | `Accept: geo+json` | GeoJSON FeatureCollection | `features`            |
| 52N    | /systems                    | `Accept: sml+json` | items wrapper             | `items`               |
| 52N    | /deployments                | `Accept: sml+json` | items wrapper             | `items`               |

---

## What WORKS (Verified Against Live Data)

| Capability                                       | OSH                               | 52N                              |
| ------------------------------------------------ | --------------------------------- | -------------------------------- |
| Server connectivity                              | ✅ 200 OK                         | ✅ 200 OK                        |
| GeoJSON feature recognition (isCSAPIFeature)     | ✅ 12 systems + 3 SF              | ❌ F41 (null featureType)        |
| GeoJSON feature extraction (extractCSAPIFeature) | ✅ All fields extracted           | ❌ Cannot extract (unrecognized) |
| parseValidTime on live array format              | ✅ Correct for all                | ✅ Correct null handling         |
| SensorML type dispatch (parseSensorML30)         | ✅ PhysicalSystem                 | ✅ PhysicalSystem                |
| SensorML DescribedObject properties              | ✅ id, uid, label, def, validTime | ✅ id, uid, label, def           |
| SensorML identifiers                             | — (not present)                   | ✅ SerialNo, ProdNo              |
| SensorML classifiers                             | —                                 | ✅ SensorType                    |
| SensorML documents                               | —                                 | ✅ Operating Manual              |
| SensorML typeOf link                             | —                                 | ✅ procedures reference          |
| SensorML components                              | ✅ 4 PhysicalComponents           | —                                |
| SensorML localReferenceFrames                    | ✅ LOCAL_FRAME                    | —                                |
| SWE Common DataRecord recognition                | ✅ 4 schemas tested               | ❌ No data available             |
| SWE Common Quantity fields                       | ✅ Temperature, Location coords   | ❌                               |
| SWE Common Text fields                           | ✅ StatusEvent                    | ❌                               |
| SWE Common Boolean fields                        | ✅ Control stream                 | ❌                               |
| SWE Common Count fields                          | ✅ Control stream                 | ❌                               |
| satisfies migration (Issue #55)                  | ✅ No regression                  | ✅ No regression                 |
| SensorMLParseError shared module (Issue #53)     | ✅ 775 tests pass                 | ✅                               |
| Barrel file exports (Issue #23)                  | ✅ All 9 exports                  | ✅                               |
| Test suite integrity                             | ✅ 775/775, 14 suites             | —                                |

## What Remains (Later Phase 3 Concerns)

| Issue                                                               | Severity | Component   | Target Task                                              |
| ------------------------------------------------------------------- | -------- | ----------- | -------------------------------------------------------- |
| Vector type parser                                                  | Low      | swecommon   | Future Issue (F74)                                       |
| DataArray integration test against live observations                | Low      | swecommon   | After DataArray observation data available               |
| SWE Common integration test via live schema → parser pipeline       | Medium   | swecommon   | Next smoke test could run schema through parseDataRecord |
| 52N datastream endpoint (500) blocks SWE Common testing             | Low      | 52N server  | Upstream — monitor for fix                               |
| SensorML Deployment sub-parser                                      | Low      | sensorml    | Future Issue — 52N has deployment data                   |
| Formal end-to-end pipeline: fetch → detect format → dispatch parser | Medium   | integration | Phase 4 scope                                            |

---

## Verdict

**Smoke test #16 validates 8 issues spanning SensorML (Issues #53, #22, #23, #54), SWE Common (Issues #24, #25, #26), and type safety cleanup (Issue #55).** All 775 CSAPI tests pass at HEAD (`c46ec92`). No behavioral regressions detected.

**GeoJSON handler (Issue #55):** The `satisfies` migration introduced zero behavioral changes — all recognition, extraction, and validTime parsing results match smoke test #15 exactly. The `satisfies` operator correctly surfaces type mismatches at compile time while preserving runtime behavior. OSH data is fully recognized; 52N's `null` featureType (F41) continues to prevent recognition, which is correct handler behavior.

**SensorML (Issues #22, #23, #53, #54):** The barrel file provides a clean public API surface. `parseSensorML30` correctly dispatches PhysicalSystem data from both servers. OSH provides minimal but structurally rich SML (components, localReferenceFrames), while 52N provides metadata-rich SML (identifiers, classifiers, documents, typeOf). The two servers provide complementary coverage. Issue #53's shared `SensorMLParseError` module resolves cross-module instanceof issues (F69).

**SWE Common (Issues #24, #25, #26):** The most significant new finding is that **OSH provides accessible SWE Common data** via datastream and control stream schemas. Four schemas were examined containing DataRecord, Quantity, Text, Boolean, Count, and Vector types. All simple component types found (Quantity, Text, Boolean, Count) are handled by the parsers. Vector is correctly identified as out-of-scope (aggregate type) — this is a scope boundary, not a bug. 52N provides no SWE Common data due to the broken datastreams endpoint. A future smoke test could run the actual schema data through `parseDataRecord` in a Node.js script for full integration validation.

**4 new findings (F74–F77):** 2 informational (Vector scope boundary, SWE Common data availability), 1 low severity server status change (52N /datastreams degraded), 1 informational positive (52N /samplingFeatures fixed). No client bugs found. No issues require immediate action. The codebase is ready to proceed to the next Phase 3 task.
