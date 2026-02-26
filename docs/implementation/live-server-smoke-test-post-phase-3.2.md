# Live Server Smoke Test — Post Phase 3.2

**Date:** 2026-02-15  
**Milestone:** After completing Phase 3.2 (Issues #49, #15, #16, #51)  
**Servers:** OpenSensorHub demo instance, 52North demo instance  
**Auth:** OSH: Basic auth required (credentials not stored in repo); 52North: None (expired SSL cert)  
**Purpose:** Validate GeoJSON handler improvements (SensorML vocabulary extension, unified validation surface) and verify format detector / validator extensions against real server data  
**Components tested:** `src/ogc-api/csapi/formats/geojson.ts` (6 public functions), `src/shared/mime-type.ts` (5 format detectors), `src/ogc-api/csapi/helpers.ts` (13 validators)

> This is smoke test #11 in the series (second Phase 3 smoke test). See also:
>
> - [Previous smoke test](live-server-smoke-test-post-phase-3.1.md) — Phase 3.1, 48 findings, first Phase 3 test
> - [Phase 2.8 smoke test](live-server-smoke-test-post-phase-2.8.md) — Phase 2.8, final Phase 2 URL builder test
> - [Phase 3 smoke test rationale](phase-3-smoke-test-rationale.md)

## Test Methodology

Fetched real responses from both servers using PowerShell `Invoke-RestMethod`, saved as JSON files, then ran all GeoJSON handler functions against every feature using a Node.js validation script (`__smoke_test_handler.mjs`). No code changes were made during the smoke test — read-only observation per Lesson 10.

**Changes since last smoke test (Phase 3.1):**

- **Issue #49:** SensorML vocabulary extension — `SENSORML_NS`, `toSensormlLocalName()`, `SENSORML_SAMPLING_FEATURE_LOCAL_NAMES` added to `geojson.ts`. Direct fix for F40.
- **Issue #15:** Format detector extensions — 5 new MIME-type detection functions in `mime-type.ts`.
- **Issue #16:** Validator extensions — `ValidationError` type + 13 validation functions in `helpers.ts`.
- **Issue #51:** Unified GeoJSON validation surface — `validateCSAPIFeature` now delegates to per-type helpers validators.

**Unit tests:** 450 CSAPI (4 suites) + 31 mime-type (1 suite) — all passing. tsc clean.

---

## Server Profiles

### OpenSensorHub

| Property    | Value                                    |
| ----------- | ---------------------------------------- |
| URL         | `http://45.55.99.236:8080/sensorhub/api` |
| Auth        | Basic (credentials not stored in repo)   |
| Root status | ✅ 200 — 10 links in root document       |

| Resource Type    | Endpoint            | Count | Has Data? | Change from Phase 3.1 |
| ---------------- | ------------------- | ----- | --------- | --------------------- |
| Systems          | `/systems`          | 5+    | ✅ Yes    | Unchanged             |
| Deployments      | `/deployments`      | 0     | ❌ Empty  | Unchanged             |
| Procedures       | `/procedures`       | 0     | ❌ Empty  | Unchanged             |
| SamplingFeatures | `/samplingFeatures` | 5+    | ✅ Yes    | Unchanged             |
| DataStreams      | `/datastreams`      | 3+    | ✅ Yes    | Unchanged             |
| Observations     | `/observations`     | 10+   | ✅ Yes    | Unchanged             |
| ControlStreams   | `/controlstreams`   | 8+    | ✅ Yes    | Unchanged             |
| Properties       | `/properties`       | 0     | ❌ Empty  | Unchanged             |

### 52North

| Property    | Value                                                  |
| ----------- | ------------------------------------------------------ |
| URL         | `https://csa.demo.52north.org`                         |
| Auth        | None required                                          |
| SSL         | Expired certificate — requires `-SkipCertificateCheck` |
| Root status | ✅ 200 — 7 links in root document                      |

| Resource Type    | Endpoint            | Count | Has Data? | Change from Phase 3.1                                                 |
| ---------------- | ------------------- | ----- | --------- | --------------------------------------------------------------------- |
| Systems          | `/systems`          | 3     | ✅ Yes    | Unchanged                                                             |
| Deployments      | `/deployments`      | 1     | ✅ Yes    | Unchanged                                                             |
| Procedures       | `/procedures`       | 1     | ✅ Yes    | Unchanged                                                             |
| SamplingFeatures | `/samplingFeatures` | 0     | ❌ Empty  | **Change: endpoint now returns 200 (was 404 for featuresOfInterest)** |
| DataStreams      | `/datastreams`      | —     | ❌ 500    | Unchanged                                                             |
| Observations     | `/observations`     | —     | ❌ 500    | Unchanged                                                             |
| ControlStreams   | `/controlstreams`   | —     | ❌ 404    | Unchanged                                                             |
| Properties       | `/properties`       | 0     | ❌ Empty  | Unchanged                                                             |

**Key change:** 52North's `/samplingFeatures` endpoint now returns 200 (previously only `/featuresOfInterest` existed, which returned 404). The endpoint is functional but empty (0 items).

---

## Results

### Prior Findings — Regression Check

All 48 findings from the Phase 3.1 smoke test re-evaluated:

| Finding | Title                                            | Prior Status                | Current Status            | Evidence                                                                                                                               |
| ------- | ------------------------------------------------ | --------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| F1      | Link relation prefix mismatch                    | Fixed (Issue #34)           | ✅ Still fixed            | No regression                                                                                                                          |
| F2      | Top-level vs. collection-scoped URLs             | Fixed (Issue #35)           | ✅ Still fixed            | No regression                                                                                                                          |
| F3      | Response envelope uses `items`                   | Deferred to Phase 3         | ⏳ Still deferred         | OSH: `{items:[...]}`, 52N GeoJSON: `{type:"FeatureCollection", features:[...]}`                                                        |
| F4      | `validTime` is an array                          | Addressed by Phase 3        | ✅ **Still addressed**    | `parseValidTime()` correctly handles `["ISO","now"]` on all 5 OSH systems                                                              |
| F5      | Missing pagination metadata                      | Deferred to Phase 3         | ⏳ Still deferred         | Both servers use link-based pagination only                                                                                            |
| F6      | OSH rejects `systems/{id}/deployments`           | Server limitation           | ⚠️ Still present          | Not retested (unchanged)                                                                                                               |
| F7      | OSH rejects `systems/{id}/procedures`            | Server limitation           | ⚠️ Still present          | Not retested (unchanged)                                                                                                               |
| F8      | OSH rejects `samplingFeatures/{id}/systems`      | Server limitation           | ⚠️ Still present          | Not retested (unchanged)                                                                                                               |
| F9      | OSH rejects `samplingFeatures/{id}/history`      | Server limitation           | ⚠️ Still present          | Not retested (unchanged)                                                                                                               |
| F10     | 52North now has real data                        | Informational               | ✅ Confirmed              | 3 systems, 1 deployment, 1 procedure                                                                                                   |
| F11     | 52North uses SensorML format                     | Phase 3 concern             | ✅ Confirmed              | **Now the default** — 52N returns `application/sml+json` without explicit `f=` parameter                                               |
| F12     | 52North `systems/{id}/deployments` works         | Informational               | ✅ Still true             | Not retested (unchanged)                                                                                                               |
| F13     | Both servers use `items` envelope                | Revised in 3.1              | ⚠️ Still revised          | Envelope varies by server AND format                                                                                                   |
| F14     | Properties not discoverable via links            | Shared concern              | ⏳ Still present          | Neither server exposes properties in root links                                                                                        |
| F15     | 52North adds third system                        | Informational               | ✅ Still true             | 3 systems confirmed                                                                                                                    |
| F16     | OSH rejects `datastreams/{id}/systems`           | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F17     | OSH rejects `datastreams/{id}/procedures`        | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F18     | OSH rejects `datastreams/{id}/history`           | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F19     | `resultTime=latest` accepted by OSH              | Resolved                    | ✅ Still valid            | Not retested                                                                                                                           |
| F20     | 52North DataStreams still broken (500)           | Server limitation           | ⚠️ Still present          | GET `/datastreams?limit=3` → 500                                                                                                       |
| F21     | OSH rejects `observations/{id}/datastream`       | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F22     | OSH rejects `observations/{id}/samplingFeature`  | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F23     | OSH rejects `observations/{id}/system`           | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F24     | OSH rejects `observations/{id}/history`          | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F25     | `resultTime=latest` returns real data            | Informational               | ✅ Still valid            | Not retested                                                                                                                           |
| F26     | 52North Observations broken (500)                | Server limitation           | ⚠️ Still present          | GET `/observations?limit=3` → 500                                                                                                      |
| F27     | Observation `foi@id` naming variation            | Phase 3 concern             | ⏳ Still deferred         | Not yet in scope                                                                                                                       |
| F28     | OSH rejects `controlstreams/{id}/feasibility`    | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F29     | ControlStream schema works                       | Informational               | ✅ Still valid            | Not retested                                                                                                                           |
| F30     | ControlStream `system@link` cross-reference      | Phase 3 concern             | ⏳ Still deferred         | Not yet in scope                                                                                                                       |
| F31     | Command entity data shape                        | Phase 3 concern             | ⏳ Still deferred         | Not yet in scope                                                                                                                       |
| F32     | 52North ControlStreams not implemented (404)     | Server limitation           | ⚠️ Still present          | `/controlstreams?limit=3` → 404                                                                                                        |
| F33     | ControlStream schema returns SWE DataRecord      | Phase 3 concern             | ⏳ Still deferred         | Not yet in scope                                                                                                                       |
| F34     | OSH no top-level `/commands`                     | Shared concern              | ⚠️ Still present          | Not retested                                                                                                                           |
| F35     | OSH no `/commands/{id}/cancel`                   | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F36     | OSH ignores `id` query param on commands         | Server limitation           | ⚠️ Still present          | Not retested                                                                                                                           |
| F37     | Command `/result` returns 404                    | Expected behavior           | ✅ Still valid            | Not retested                                                                                                                           |
| F38     | Command status data shape                        | Phase 3 concern             | ⏳ Still deferred         | Not yet in scope                                                                                                                       |
| F39     | Commands use `items` envelope                    | Informational               | ✅ Confirms F3            | Not retested                                                                                                                           |
| **F40** | **OSH SamplingFeatures use non-SOSA vocabulary** | **Critical — needs design** | ✅ **FIXED by Issue #49** | **All 5 OSH SamplingFeatures now recognized as SamplingFeature** via SensorML `http://www.opengis.net/sensorml/2.0#Feature` vocabulary |
| F41     | 52N Systems have null featureType in GeoJSON     | Critical — needs design     | ⚠️ **Still present**      | All 3 52N systems still have `featureType: null` in GeoJSON format                                                                     |
| F42     | 52N Deployment has null validTime                | Server limitation           | ⚠️ Still present          | `validTime: null` on 52N deployment — correctly rejected                                                                               |
| F43     | 52N Procedures misclassified as System           | Interop concern             | ⚠️ Still present          | `sosa:Sensor` from `/procedures` → classified as System                                                                                |
| F44     | 52N uses both CURIE and full URI forms           | Positive validation         | ✅ Still validated        | Both forms correctly handled                                                                                                           |
| F45     | Response envelope varies by server AND format    | Informational               | ✅ **Updated**            | 52N now defaults to `application/sml+json` (was `application/json`); envelope still varies by format                                   |
| F46     | OSH ignores SensorML Accept header               | Informational               | ✅ Still true             | OSH returns `Content-Type: application/json` for `f=application/sml+json`                                                              |
| F47     | 52N GeoJSON includes `@link` notation            | Phase 3 concern             | ⏳ Still present          | `systemKind@link`, `platform@link`, `deployedSystems@link` all present                                                                 |
| F48     | OSH features have empty links arrays             | Low                         | ✅ Still true             | No per-feature links on either server                                                                                                  |

**Summary:** 0 regressions. **F40 is now FIXED** — the critical SensorML vocabulary gap has been resolved by Issue #49. All 5 OSH SamplingFeatures are now recognized. F41 (null featureType) and F43 (misclassification) remain.

---

### GeoJSON Handler — Recognition

| Server | Resource Type         | Features Tested | All Recognized?        | Classification                 | Change from Phase 3.1                  |
| ------ | --------------------- | --------------- | ---------------------- | ------------------------------ | -------------------------------------- |
| OSH    | Systems               | 5               | ✅ Yes                 | All → System                   | Unchanged                              |
| OSH    | SamplingFeatures      | 5               | ✅ **Yes**             | All → SamplingFeature          | **FIXED — was 0/5 in Phase 3.1 (F40)** |
| OSH    | Deployments           | 0               | —                      | Empty collection               | Unchanged                              |
| OSH    | Procedures            | 0               | —                      | Empty collection               | Unchanged                              |
| 52N    | Systems (GeoJSON)     | 3               | ❌ No                  | All → null (featureType: null) | Unchanged (F41)                        |
| 52N    | Deployments (GeoJSON) | 1               | ✅ Yes                 | → Deployment                   | Unchanged                              |
| 52N    | Procedures (GeoJSON)  | 1               | ⚠️ Yes (misclassified) | → System (not Procedure)       | Unchanged (F43)                        |

**Recognition rate: 12 of 15 features recognized (80%).** Up from 47% in Phase 3.1. The improvement is entirely due to Issue #49 fixing F40 — OSH SamplingFeatures are now recognized via the SensorML namespace.

**Detailed recognition results:**

| Server | Feature ID     | featureType                                   | isCSAPIFeature | getCSAPIResourceType         |
| ------ | -------------- | --------------------------------------------- | -------------- | ---------------------------- |
| OSH    | 03bc5ofvvstg   | `http://www.w3.org/ns/sosa/Sensor`            | ✅ true        | System                       |
| OSH    | 02sv18sqotc0   | `http://www.w3.org/ns/sosa/Sensor`            | ✅ true        | System                       |
| OSH    | 03hsjcf4odig   | `http://www.w3.org/ns/sosa/Sensor`            | ✅ true        | System                       |
| OSH    | 040g           | `http://www.w3.org/ns/sosa/Sensor`            | ✅ true        | System                       |
| OSH    | 0410           | `http://www.w3.org/ns/sosa/Sensor`            | ✅ true        | System                       |
| OSH    | 040g           | `http://www.opengis.net/sensorml/2.0#Feature` | ✅ **true**    | **SamplingFeature**          |
| OSH    | 0410           | `http://www.opengis.net/sensorml/2.0#Feature` | ✅ **true**    | **SamplingFeature**          |
| OSH    | 042g           | `http://www.opengis.net/sensorml/2.0#Feature` | ✅ **true**    | **SamplingFeature**          |
| OSH    | 043g           | `http://www.opengis.net/sensorml/2.0#Feature` | ✅ **true**    | **SamplingFeature**          |
| OSH    | 0440           | `http://www.opengis.net/sensorml/2.0#Feature` | ✅ **true**    | **SamplingFeature**          |
| 52N    | 5400-526       | `null`                                        | ❌ false       | null                         |
| 52N    | YSI599503-00-1 | `null`                                        | ❌ false       | null                         |
| 52N    | 5300-909       | `null`                                        | ❌ false       | null                         |
| 52N    | af41f84f-...   | `http://www.w3.org/ns/sosa/Deployment`        | ✅ true        | Deployment                   |
| 52N    | 4e09de42-...   | `sosa:Sensor`                                 | ✅ true        | System (⚠️ from /procedures) |

---

### GeoJSON Handler — Validation

| Server | Resource Type         | Features Tested | All Valid?         | Errors                                   | Change from Phase 3.1                                 |
| ------ | --------------------- | --------------- | ------------------ | ---------------------------------------- | ----------------------------------------------------- |
| OSH    | Systems               | 5               | ✅ Yes             | 0 errors                                 | Unchanged                                             |
| OSH    | SamplingFeatures      | 5               | ❌ **No**          | `sampledFeature@link: required` × 5      | **NEW — features now recognized but fail validation** |
| 52N    | Systems (GeoJSON)     | 3               | ❌ No              | `featureType (non-empty string)` × 3     | Unchanged (F41)                                       |
| 52N    | Deployments (GeoJSON) | 1               | ❌ No              | `validTime: required for Deployment` × 1 | Unchanged (F42)                                       |
| 52N    | Procedures (GeoJSON)  | 1               | ✅ Yes (as System) | 0 errors                                 | Unchanged                                             |

**Validation details for OSH SamplingFeatures (new result):**

All 5 OSH SamplingFeatures are now recognized as SamplingFeature (F40 fixed) but fail validation because they lack the `sampledFeature@link` property required by `validateSamplingFeature()`:

```json
{
  "type": "Feature",
  "id": "040g",
  "geometry": null,
  "properties": {
    "uid": "urn:android:foi:Run-20260211-041356",
    "featureType": "http://www.opengis.net/sensorml/2.0#Feature",
    "name": "Run-20260211-041356"
  }
}
```

The `sampledFeature@link` property is required by the OGC CSAPI Part 1 spec for SamplingFeatures. OSH does not include it in the GeoJSON representation. This is the first time this validation rule has fired against real data — previously, OSH SamplingFeatures were not recognized at all (F40).

---

### GeoJSON Handler — Extraction

| Server | Resource Type         | Features Tested | All Extracted?     | Issues                                      | Change from Phase 3.1                  |
| ------ | --------------------- | --------------- | ------------------ | ------------------------------------------- | -------------------------------------- |
| OSH    | Systems               | 5               | ✅ Yes             | All properties correct                      | Unchanged                              |
| OSH    | SamplingFeatures      | 5               | ❌ No              | Blocked by validation (sampledFeature@link) | **NEW — recognized but can't extract** |
| 52N    | Systems (GeoJSON)     | 3               | ❌ No              | Blocked by validation (null featureType)    | Unchanged (F41)                        |
| 52N    | Deployments (GeoJSON) | 1               | ❌ No              | Blocked by validation (null validTime)      | Unchanged (F42)                        |
| 52N    | Procedures (GeoJSON)  | 1               | ✅ Yes (as System) | All properties correct                      | Unchanged                              |

**Extraction rate: 6 of 15 features (40%).** Same as Phase 3.1. The newly-recognized OSH SamplingFeatures can't be extracted because validation blocks them at the `sampledFeature@link` check.

**Successful extraction details (OSH Systems):**

| Feature ID   | id  | uid (valid URI?)                                   | name                               | validTime                                | geometry | links |
| ------------ | --- | -------------------------------------------------- | ---------------------------------- | ---------------------------------------- | -------- | ----- |
| 03bc5ofvvstg | ✅  | ✅ `urn:osh:driver:mavsdk:cube:replay`             | ✅ "LIVE - Field Drone"            | ✅ `{start: 2026-01-26, end: undefined}` | not set  | []    |
| 02sv18sqotc0 | ✅  | ✅ `urn:android:device:aedeee0ae1212e2a:blue2:...` | ✅ "LIVE - Android Phone [Blue 2]" | ✅ `{start: 2026-01-26, end: undefined}` | not set  | []    |
| 03hsjcf4odig | ✅  | ✅ `urn:android:device:0bfc411401e3d722:blue1:...` | ✅ "LIVE - Android Phone [Blue 1]" | ✅ `{start: 2026-01-26, end: undefined}` | not set  | []    |
| 040g         | ✅  | ✅ `urn:android:device:dad41d3c8bf853cd`           | ✅ "Android Sensors [SR_Botts]"    | ✅ `{start: 2026-02-10, end: undefined}` | not set  | []    |
| 0410         | ✅  | ✅ `urn:osh:sensor:kestrel:FE:BB:D9:8B:53:23`      | ✅ "Kestrel Weather [SR_Cardy]"    | ✅ `{start: 2026-02-10, end: undefined}` | not set  | []    |

**Successful extraction details (52N Procedure as System):**

| Feature ID   | id  | uid (valid URI?)                        | name                                 | validTime   | geometry | links |
| ------------ | --- | --------------------------------------- | ------------------------------------ | ----------- | -------- | ----- |
| 4e09de42-... | ✅  | ✅ `urn:sensortype:aanderaa:dcps:td304` | ✅ "Doppler Current Profiler Sensor" | not present | not set  | []    |

---

### parseValidTime — Live Data

| Server               | Features With validTime | All Parsed? | Format Observed                       | Issues                                                                                  |
| -------------------- | ----------------------- | ----------- | ------------------------------------- | --------------------------------------------------------------------------------------- |
| OSH Systems          | 5                       | ✅ Yes      | `["2026-mm-ddThh:mm:ss.sssZ", "now"]` | All parsed to `{start: Date, end: undefined}`                                           |
| OSH SamplingFeatures | 0                       | —           | No validTime on SamplingFeatures      | —                                                                                       |
| 52N Systems          | 0                       | —           | `validTime: null`                     | `parseValidTime(null)` → `undefined` (correct)                                          |
| 52N Deployment       | 1 (null)                | —           | `validTime: null`                     | `parseValidTime(null)` → `undefined` (correct but triggers Deployment validation error) |
| 52N Procedure        | 0                       | —           | No validTime property                 | —                                                                                       |

**parseValidTime working correctly.** No change from Phase 3.1.

---

### Vocabulary Inventory

| featureType Value                             | Server(s) | Endpoint                         | Vocabulary          | Recognized?     | Handler Classification | Change from Phase 3.1 |
| --------------------------------------------- | --------- | -------------------------------- | ------------------- | --------------- | ---------------------- | --------------------- |
| `http://www.w3.org/ns/sosa/Sensor`            | OSH       | /systems                         | SOSA (full URI)     | ✅ Yes          | System                 | Unchanged             |
| `http://www.opengis.net/sensorml/2.0#Feature` | OSH       | /samplingFeatures                | SensorML (full URI) | ✅ **Yes**      | **SamplingFeature**    | **FIXED (Issue #49)** |
| `null`                                        | 52N       | /systems (GeoJSON)               | N/A                 | ❌ No           | null                   | Unchanged             |
| `http://www.w3.org/ns/sosa/Deployment`        | 52N       | /deployments (GeoJSON)           | SOSA (full URI)     | ✅ Yes          | Deployment             | Unchanged             |
| `sosa:Sensor`                                 | 52N       | /procedures (GeoJSON)            | SOSA (CURIE)        | ✅ Yes          | System (⚠️)            | Unchanged             |
| `sosa:Sensor`                                 | 52N       | /systems (SensorML `definition`) | SOSA (CURIE)        | ✅ Yes (in SML) | System                 | Unchanged             |
| `sosa:Platform`                               | 52N       | /systems (SensorML `definition`) | SOSA (CURIE)        | ✅ Yes (in SML) | System                 | Unchanged             |

**Vocabulary coverage: 2 vocabularies supported (SOSA + SensorML), 5 of 7 observed values recognized.** The SensorML vocabulary gap (F40) is now closed. The remaining unrecognized value is `null` (F41 — server issue, not vocabulary gap).

---

### Content-Type Availability

| Content-Type                 | OSH                                           | 52N                                                    | Notes                                             |
| ---------------------------- | --------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------- |
| `application/json` (default) | ✅ 200                                        | ⚠️ **Changed** — default is now `application/sml+json` | 52N default format changed since Phase 3.1        |
| `application/geo+json`       | ✅ 200 (returns `application/json`)           | ✅ 200 (returns `application/geo+json`)                | Must use explicit `f=application/geo+json` on 52N |
| `application/sml+json`       | ⚠️ 200 (returns `application/json` — ignores) | ✅ 200 (returns `application/sml+json`)                | OSH still ignores SensorML request (F46)          |
| `application/swe+json`       | ✅ 200 (schema endpoint)                      | ❌ 500 (datastreams broken)                            | —                                                 |

**Key change:** 52North now defaults to `application/sml+json` as its response content type. In Phase 3.1, the default was `application/json`. This means GeoJSON data from 52North requires explicit `f=application/geo+json`.

---

### Format Detector — Content-Type Validation

The 5 new MIME-type detection functions (Issue #15) were validated against observed server Content-Type headers:

| Function              | Test Value                           | Expected | Result                                            |
| --------------------- | ------------------------------------ | -------- | ------------------------------------------------- |
| `isMimeTypeSmlJson`   | `application/sml+json` (52N default) | true     | ✅ Correct                                        |
| `isMimeTypeSmlJson`   | `application/json` (OSH default)     | false    | ✅ Correct                                        |
| `isMimeTypeSweJson`   | —                                    | —        | Not testable (no live SWE JSON feature responses) |
| `isMimeTypeSweText`   | —                                    | —        | Not testable                                      |
| `isMimeTypeSweCsv`    | —                                    | —        | Not testable                                      |
| `isMimeTypeSweBinary` | —                                    | —        | Not testable                                      |

**Note:** Format detectors validated through unit tests (31 passing). Only `isMimeTypeSmlJson` is currently observable against live servers. SWE format detectors will become testable when SWE Common parsers are built.

---

### Validator Extensions — Live Data Validation

The 13 new validators (Issue #16) were indirectly tested through `validateCSAPIFeature` (Issue #51 delegates to these). Direct validator behavior against live data:

| Validator                 | Live Features Tested                      | Result      | Notes                                                           |
| ------------------------- | ----------------------------------------- | ----------- | --------------------------------------------------------------- |
| `validateSystem`          | 5 OSH Systems + 1 52N Procedure-as-System | ✅ All pass | uid, name, featureType all valid                                |
| `validateDeployment`      | 1 52N Deployment                          | ❌ Fails    | Correctly rejects `validTime: null`                             |
| `validateProcedure`       | 0                                         | —           | No Procedure-classified features available                      |
| `validateSamplingFeature` | 5 OSH SamplingFeatures                    | ❌ All fail | Correctly requires `sampledFeature@link` (absent from OSH data) |
| `validateProperty`        | 0                                         | —           | No properties data on either server                             |
| `validateDatastream`      | —                                         | —           | Not in GeoJSON handler scope                                    |
| `validateObservation`     | —                                         | —           | Not in GeoJSON handler scope                                    |
| `validateControlStream`   | —                                         | —           | Not in GeoJSON handler scope                                    |
| `validateCommand`         | —                                         | —           | Not in GeoJSON handler scope                                    |

---

## New Findings

### F49 (Moderate): OSH SamplingFeatures lack `sampledFeature@link` — validation blocks extraction

**Severity:** Moderate  
**Category:** Shared (server omits spec-required property; validator correctly enforces it)  
**Affects:** `validateCSAPIFeature()` → `validateSamplingFeature()` in `helpers.ts` / `geojson.ts`  
**Ownership:** Shared  
**Evidence:**

```json
{
  "type": "Feature",
  "id": "040g",
  "geometry": null,
  "properties": {
    "uid": "urn:android:foi:Run-20260211-041356",
    "featureType": "http://www.opengis.net/sensorml/2.0#Feature",
    "name": "Run-20260211-041356"
  }
}
```

All 5 OSH SamplingFeatures are now recognized (thanks to Issue #49/F40 fix) but fail validation because they lack `sampledFeature@link`. The OGC CSAPI Part 1 spec lists `sampledFeature` as a required association for SamplingFeature resources. Our `validateSamplingFeature()` correctly enforces this.

However, OSH does not include `sampledFeature@link` in the GeoJSON representation. This creates a situation where 100% of OSH SamplingFeatures are recognized but 0% pass validation, meaning extraction is completely blocked for this resource type.

**Options:**

1. Downgrade `sampledFeature@link` from error to warning — allows extraction but weakens spec compliance
2. Accept the current behavior — validation is correct per spec; OSH data is non-compliant
3. Add a "lenient mode" option to `extractCSAPIFeature` that extracts despite validation warnings

**Status:** Needs design decision — the validator is spec-correct, but the practical effect is that no OSH SamplingFeatures can be extracted.

### F50 (Informational): 52North default content type changed to `application/sml+json`

**Severity:** Informational  
**Category:** Interoperability concern  
**Affects:** Future response parser content negotiation  
**Ownership:** Upstream (server configuration change)  
**Evidence:**

```
GET https://csa.demo.52north.org/systems?limit=1
  Response Content-Type: application/sml+json
  (Was: application/json in Phase 3.1)
```

52North's default response format has changed from `application/json` (which returned GeoJSON FeatureCollection) to `application/sml+json` (which returns SensorML JSON). To get GeoJSON format, clients must now explicitly request `f=application/geo+json`.

**Impact:** The response parser (future Phase 3 task) must implement content negotiation. It cannot assume GeoJSON as the default format. The format detector functions from Issue #15 become more important for determining which parser to invoke.

**Status:** Informational — important input for response parser design

### F51 (Informational): 52North `/samplingFeatures` endpoint now functional

**Severity:** Informational  
**Category:** Positive change  
**Affects:** SamplingFeatures URL builder methods  
**Ownership:** Upstream  
**Evidence:**

```
GET https://csa.demo.52north.org/samplingFeatures?limit=3 → 200, {items: [], links: []}
  (Was: 404 in Phase 3.1 — only /featuresOfInterest existed then)
```

52North now exposes `/samplingFeatures` (the CSAPI Part 1 endpoint name) and it returns 200 with an empty collection. The old `/featuresOfInterest` endpoint still returns 404. This is a positive alignment with the spec.

**Status:** Informational — positive server improvement

---

## Cross-Server Comparison

| Dimension                                 | OpenSensorHub                                 | 52North                                           | Match?             |
| ----------------------------------------- | --------------------------------------------- | ------------------------------------------------- | ------------------ |
| Root API status                           | ✅ 200                                        | ✅ 200                                            | ✅                 |
| Default content type                      | `application/json`                            | `application/sml+json`                            | ❌ **Changed**     |
| GeoJSON format                            | Always (ignores format request)               | Only with explicit `f=application/geo+json`       | ❌                 |
| featureType on Systems                    | `http://www.w3.org/ns/sosa/Sensor` (full URI) | `null` in GeoJSON                                 | ❌                 |
| featureType on SamplingFeatures           | `http://www.opengis.net/sensorml/2.0#Feature` | N/A (empty)                                       | —                  |
| featureType on Deployments                | N/A (empty)                                   | `http://www.w3.org/ns/sosa/Deployment` (full URI) | —                  |
| featureType on Procedures                 | N/A (empty)                                   | `sosa:Sensor` (CURIE)                             | —                  |
| validTime format                          | Array `["ISO-8601", "now"]`                   | `null` on all features                            | ❌                 |
| uid field                                 | ✅ URN on all features                        | ✅ URN on all features                            | ✅                 |
| name field                                | ✅ Present on all features                    | ✅ Present on all features                        | ✅                 |
| `sampledFeature@link` on SamplingFeatures | ❌ Not present                                | N/A (empty)                                       | —                  |
| Per-feature links                         | Not present                                   | Not present                                       | ✅                 |
| Response envelope (GeoJSON)               | `{items:[...]}`                               | `{type:"FeatureCollection", features:[...]}`      | ❌                 |
| SensorML support                          | ❌ Ignores request                            | ✅ Full support (now default)                     | ❌                 |
| SamplingFeatures endpoint                 | ✅ `/samplingFeatures` (has data)             | ✅ `/samplingFeatures` (empty, newly functional)  | ✅ (endpoint name) |

---

## Response Envelope Observations (Phase 3 Reference)

| Server | Format                          | Envelope Type             | Feature Array Key | Pagination                        | Links Location    |
| ------ | ------------------------------- | ------------------------- | ----------------- | --------------------------------- | ----------------- |
| OSH    | application/json (default)      | Flat object               | `items`           | `links[rel="next"]` with offset   | Top-level `links` |
| 52N    | application/sml+json (default)  | Flat object               | `items`           | `links` (empty for small results) | Top-level `links` |
| 52N    | application/geo+json (explicit) | GeoJSON FeatureCollection | `features`        | `links` (empty for small results) | Top-level `links` |

**Change from Phase 3.1:** 52North's default is now SensorML JSON (`{items:[...]}`) rather than JSON/GeoJSON. The response parser must detect the format before choosing the correct extraction key.

---

## What WORKS (Verified Against Live Data)

| Capability                                              | OSH                                         | 52N                             | Notes                                                 |
| ------------------------------------------------------- | ------------------------------------------- | ------------------------------- | ----------------------------------------------------- |
| `isCSAPIFeature()` — SOSA full URI                      | ✅ 5/5 Systems                              | —                               |                                                       |
| `isCSAPIFeature()` — SOSA CURIE                         | —                                           | ✅ 1/1 Procedure                |                                                       |
| `isCSAPIFeature()` — SensorML vocabulary                | ✅ **5/5 SamplingFeatures**                 | —                               | **NEW — Issue #49 fix**                               |
| `getCSAPIResourceType()` — System                       | ✅ 5/5                                      | —                               |                                                       |
| `getCSAPIResourceType()` — SamplingFeature (SensorML)   | ✅ **5/5**                                  | —                               | **NEW — Issue #49 fix**                               |
| `getCSAPIResourceType()` — Deployment                   | —                                           | ✅ 1/1                          |                                                       |
| `validateCSAPIFeature()` — System (clean)               | ✅ 5/5 (0 errors)                           | —                               | Now delegates to `validateSystem()` (Issue #51)       |
| `validateCSAPIFeature()` — SamplingFeature (spec check) | ✅ Correctly enforces `sampledFeature@link` | —                               | **NEW — previously unrecognized**                     |
| `validateCSAPIFeature()` — Deployment (spec check)      | —                                           | ✅ Correctly enforces validTime |                                                       |
| `extractCSAPIFeature()` — System                        | ✅ 5/5                                      | —                               | id, uid, name, validTime all correct                  |
| `extractCSAPIFeature()` — Procedure-as-System           | —                                           | ✅ 1/1                          | Extracts correctly for classified type                |
| `parseValidTime()` — array format                       | ✅ 5/5                                      | —                               | All `["ISO","now"]` → `{start: Date, end: undefined}` |
| `parseValidTime(null)`                                  | —                                           | ✅ Returns undefined            | Correct behavior                                      |
| `isValidUri()` — URN format                             | ✅ All uids                                 | ✅ All uids                     | Both servers use URN                                  |
| Format detector — `isMimeTypeSmlJson`                   | —                                           | ✅ Matches 52N default CT       | Validated against observed header                     |
| All 450 CSAPI unit tests                                | ✅                                          | —                               |                                                       |
| All 31 mime-type unit tests                             | ✅                                          | —                               |                                                       |

---

## What Remains (Later Phase 3 Concerns)

| Issue                                                    | Severity | Component                            | Target Task           |
| -------------------------------------------------------- | -------- | ------------------------------------ | --------------------- |
| Null featureType fallback (F41)                          | Critical | geojson.ts or response parser        | Needs design decision |
| Endpoint-context classification tiebreaker (F43)         | Moderate | geojson.ts or response parser        | Needs design decision |
| `sampledFeature@link` enforcement vs real data (F49)     | Moderate | helpers.ts validator or lenient mode | Needs design decision |
| Response envelope parsing (F3/F45)                       | Moderate | Response parser                      | Phase 3 task          |
| Content negotiation (F50)                                | Moderate | Response parser                      | Phase 3 task          |
| `@link` notation parsing (F47)                           | Moderate | Response parser                      | Phase 3 task          |
| SensorML parser (52N has data, OSH does not)             | Moderate | Future SensorML parser               | Phase 3 task          |
| SWE Common parser (OSH schema endpoint works)            | Moderate | Future SWE parser                    | Phase 3 task          |
| Pagination helpers                                       | Low      | Response parser                      | Phase 3 task          |
| F6-F9, F16-F18, F21-F24, F28, F34-F36 server limitations | Various  | N/A                                  | Upstream              |
| 52N DataStreams/Observations still broken                | Moderate | N/A                                  | Upstream (F20, F26)   |

---

## Verdict

**F40 is confirmed fixed. The SensorML vocabulary extension (Issue #49) works correctly against all real OSH SamplingFeatures.** This was the most critical finding from Phase 3.1 — a 100% recognition failure on OSH SamplingFeatures. All 5 features are now correctly recognized as `SamplingFeature` via the `http://www.opengis.net/sensorml/2.0#Feature` vocabulary. Recognition rate improved from 47% to 80%.

**However, fixing F40 exposed a new practical issue (F49).** The newly-recognized SamplingFeatures fail validation because OSH does not include the spec-required `sampledFeature@link` property. Our validator is spec-correct, but the effect is that 0% of OSH SamplingFeatures can be extracted. This is a design decision: should the handler be lenient for real-world data, or strict for spec compliance? Both positions are defensible.

**The unified validation surface (Issue #51) is working correctly.** `validateCSAPIFeature` now delegates to the per-type helpers validators, and the delegation chain produces the expected errors for each resource type. The validation error format (`ValidationError[]` with `severity`, `path`, `message`) is clean and consistent.

**A notable server-side change:** 52North's default content type changed from `application/json` to `application/sml+json`. This means the future response parser must implement content negotiation rather than assuming GeoJSON. The format detector functions from Issue #15 become more important for routing responses to the correct parser.

**Cumulative statistics:**

- 11 smoke tests completed (9 Phase 2 + 2 Phase 3)
- 51 total findings (F1–F51)
- 0 handler bugs found (all validation behavior matches design intent)
- 1 critical fix confirmed (F40 → Issue #49)
- 1 new design decision needed (F49 — sampledFeature@link strictness)
- 481 unit tests passing (450 CSAPI + 31 mime-type)
- Phase 3 GeoJSON handler validated against 15 real features from 2 servers
