# Live Server Smoke Test — Post Phase 6.1

**Date:** 2026-02-25
**Milestone:** After completing Phase 6.1 (Issues #129–#133)
**Servers:** OpenSensorHub demo instance, 52North demo instance
**Auth:** OSH: Basic auth required (credentials not stored in repo); 52North: None (expired SSL cert)
**Purpose:** Validate that all Phase 6.1 work (type guard cleanup, test expansion) introduces no regressions against live servers and that our parsers, CRUD operations, and discovery mechanisms remain correct.
**Finding Series:** Phase 6.1 (P6.1-F1, P6.1-F2, ...)
**Smoke Test Number:** ST#24

> This is smoke test #24 in the series. See also:
>
> - [Previous smoke test (ST#23)](live-server-smoke-test-post-phase-5.5.md)
> - [Phase 6 Architecture Verification](phase-6-architecture-verification.md)

## Test Methodology

Full end-to-end smoke test covering:

1. Automated test suite execution (all 61 suites)
2. TypeScript type checking and linting
3. Live server connectivity, conformance, and resource inventory on both servers
4. Parser spot-checks against live data (classifyFeature, parseValidTime, parseDatastream, parseObservation, parseControlStream, parseProperty)
5. SensorML content negotiation on both servers
6. Full CRUD cycle (create → read → delete) on OSH
7. Prior findings regression check
8. Cross-server comparison

## Pre-Test State

| Property       | Value                                                                      |
| -------------- | -------------------------------------------------------------------------- |
| Branch         | phase-6                                                                    |
| HEAD           | `56f9ddc`                                                                  |
| Working tree   | Clean                                                                      |
| Last 5 commits | `56f9ddc` test(endpoint): expand CSAPI section from 3 to 7 test cases      |
|                | `6853143` test(factory): expand factory.spec.ts from 2 to 6 test cases     |
|                | `efbff10` test: validate parseProperty against live OSH Property resources |
|                | `4172490` fix: replace double cast with runtime type guard in factory.ts   |
|                | `ccd8bca` chore: remove placeholder file from failed auto-close attempt    |

### Issues Validated

| Issue | Title                                                   | Commit                |
| ----- | ------------------------------------------------------- | --------------------- |
| #129  | Remove stale `as any` cast in factory.ts                | merged into `4172490` |
| #130  | Replace double cast with runtime type guard             | `4172490`             |
| #131  | Validate parseProperty against live OSH data            | `efbff10`             |
| #132  | Expand factory.spec.ts from 2 to 6 test cases           | `6853143`             |
| #133  | Expand endpoint.spec.ts CSAPI section from 3 to 7 tests | `56f9ddc`             |

## Automated Test Results

### CI Compliance

| Gate            | Command                                  | Expected | Actual                                | Status |
| --------------- | ---------------------------------------- | -------- | ------------------------------------- | ------ |
| C1 — TypeScript | `npx tsc --noEmit`                       | exit 0   | exit 0 (clean)                        | ✅     |
| C2 — ESLint     | `npx eslint .`                           | exit 0   | exit 0 (clean)                        | ✅     |
| C3 — Node tests | `npx jest --config jest.node.config.cjs` | all pass | **61 suites, 1730 passed, 4 skipped** | ✅     |

### Test Count Progression

| Metric        | ST#23 (Phase 5.5)          | ST#24 (Phase 6.1) | Delta                  |
| ------------- | -------------------------- | ----------------- | ---------------------- |
| Test Suites   | 29 CSAPI / 61 total        | 61 total          | 0                      |
| Tests Passed  | 1,283 CSAPI / ~1700+ total | 1,730 total       | +447 across all phases |
| Tests Skipped | —                          | 4                 | —                      |
| tsc Errors    | 0                          | 0                 | 0                      |

## Server Profiles

### OpenSensorHub (OSH)

| Property            | Value                                    |
| ------------------- | ---------------------------------------- |
| URL                 | `http://45.55.99.236:8080/sensorhub/api` |
| Auth                | Basic (credentials not in repo)          |
| Title               | "Connected Systems API Service"          |
| Links count         | 10                                       |
| Conformance classes | **33** (up from 20+ in ST#18)            |

**Root document links:**

- `service-desc` → openapi Part 1 YAML
- `service-desc` → openapi Part 2 YAML
- `conformance` → `/conformance`
- `collections` → `/collections`
- `systems` → `/systems`
- `deployments` → `/deployments`
- `procedures` → `/procedures`
- `samplingFeatures` → `/samplingFeatures`
- `datastreams` → `/datastreams`
- `observations` → `/observations`

**Conformance classes (33 total):**

| Category           | Classes                                                                                                                    |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| OGC API Common     | 4 (core, html, json, oas30)                                                                                                |
| OGC API Common 2   | 3 (collections, html, json)                                                                                                |
| OGC API Features 1 | 3 (core, geojson, html)                                                                                                    |
| OGC API Features 4 | 1 (create-replace-delete)                                                                                                  |
| CSAPI Part 1       | 11 (core, system, subsystem, deployment, subdeployment, procedure, sf, property, create-replace-delete, geojson, sensorml) |
| CSAPI Part 2       | 8 (datastream, controlstream, system-history, system-event, create-replace-delete, json, swecommon-json, swecommon-text)   |

### 52North (52N)

| Property            | Value                                           |
| ------------------- | ----------------------------------------------- |
| URL                 | `https://csa.demo.52north.org/`                 |
| Auth                | None                                            |
| SSL                 | Expired cert (`-SkipCertificateCheck` required) |
| Title               | "connected-systems-pygeoapi"                    |
| Links count         | 7                                               |
| Conformance classes | **1** (up from 0 in previous tests)             |

**Conformance class:** `http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core`

> **Change detected:** 52N now advertises 1 conformance class (OGC API Common Core) where it previously advertised 0. This is a server-side improvement, not a regression.

## Resource Inventory

### OSH Resource Inventory (vs ST#23 Baseline)

| Endpoint          | Accept/`?f=` | ST#23 Count | ST#24 Count | Changed?     |
| ----------------- | ------------ | ----------- | ----------- | ------------ |
| /systems          | `?f=json`    | 33          | **35**      | ⚠️ +2        |
| /deployments      | `?f=json`    | 16          | **19**      | ⚠️ +3        |
| /procedures       | `?f=json`    | 15          | **21**      | ⚠️ +6        |
| /samplingFeatures | `?f=json`    | 66          | **70**      | ⚠️ +4        |
| /properties       | `?f=json`    | 0           | **7**       | ⚠️ +7 (new!) |
| /datastreams      | `?f=json`    | 100         | **200+**    | ⚠️ +100+     |
| /observations     | `?f=json`    | 100         | **200+**    | ⚠️ +100+     |
| /controlstreams   | `?f=json`    | 8           | **20**      | ⚠️ +12       |

> **All counts increased** — this is expected for a live demo server that accumulates smoke test data over multiple test sessions. No endpoints were lost or broken. The properties endpoint now has data (7 items) where it was previously empty.

### 52N Resource Inventory (vs ST#23 Baseline)

| Endpoint          | Accept Header | ST#23 Count | ST#24 Count   | Changed?          |
| ----------------- | ------------- | ----------- | ------------- | ----------------- |
| /systems          | `geo+json`    | 3           | **3**         | No                |
| /deployments      | `geo+json`    | 1           | **1**         | No                |
| /procedures       | `geo+json`    | 1           | **1**         | No                |
| /samplingFeatures | `geo+json`    | 0           | **0**         | No                |
| /properties       | `geo+json`    | 0           | **400 error** | ⚠️ Regression?    |
| /datastreams      | `geo+json`    | 500/400     | **400**       | No (still broken) |
| /observations     | `geo+json`    | 400         | **400**       | No (still broken) |
| /controlstreams   | —             | 404         | **404**       | No (still broken) |
| /commands         | —             | 404         | **404**       | No (still broken) |

> 52N `/properties` with `Accept: application/geo+json` now returns 400 `InvalidMimetype` instead of empty collection. This is a server-side change. All Part 2 endpoints remain broken as expected.

## Parser Spot-Check

### classifyFeature Regression Check

| Server | Resource ID    | featureType                              | Expected Classification   | Correct? |
| ------ | -------------- | ---------------------------------------- | ------------------------- | -------- |
| OSH    | `03bc5ofvvstg` | `http://www.w3.org/ns/sosa/Sensor`       | System (Sensor)           | ✅       |
| OSH    | `02sv18sqotc0` | `http://www.w3.org/ns/sosa/Sensor`       | System (Sensor)           | ✅       |
| 52N    | `5400-526`     | `null` (GeoJSON) / `sosa:Sensor` (SML)   | System (via SML fallback) | ✅       |
| 52N    | `5300-909`     | `null` (GeoJSON) / `sosa:Platform` (SML) | System (Platform)         | ✅       |

### parseValidTime Regression Check

| Server | Resource                  | validTime Format                     | Parser Handles? |
| ------ | ------------------------- | ------------------------------------ | --------------- |
| OSH    | System `03bc5ofvvstg`     | `["2026-01-26T18:32:01.56Z", "now"]` | ✅ Array format |
| OSH    | Datastream `03tbj7mvqg50` | `["2026-01-26T18:32:01Z", "now"]`    | ✅ Array format |
| 52N    | System `5400-526`         | `null`                               | ✅ Null handled |
| 52N    | Deployment `af41f84f-...` | `null`                               | ✅ Null handled |

### parseDatastream Regression Check (OSH Only — 52N Part 2 Broken)

| DS ID          | outputName  | validTime         | resultType | observedProps | Correct? |
| -------------- | ----------- | ----------------- | ---------- | ------------- | -------- |
| `03tbj7mvqg50` | Temperature | array (start+now) | `measure`  | present       | ✅       |
| `02au905kq85g` | StatusEvent | array (start+now) | `record`   | present       | ✅       |
| `021qpiurq85g` | gps_data    | array (start+now) | `vector`   | present       | ✅       |

### parseObservation Regression Check (OSH Only)

| Obs ID               | phenomenonTime             | resultTime                 | result shape                       | datastream@id | Correct? |
| -------------------- | -------------------------- | -------------------------- | ---------------------------------- | ------------- | -------- |
| `0829d6supc31trqfo0` | `2026-01-14T12:35:34.519Z` | `2026-01-14T12:35:34.519Z` | `{location: {lat, lon, alt}}`      | `083g`        | ✅       |
| `081pd6supc3314v9o0` | `2026-01-14T12:35:34.815Z` | `2026-01-14T12:35:34.815Z` | `{orient: {heading, pitch, roll}}` | `0840`        | ✅       |

### parseControlStream Regression Check (OSH Only)

| CS ID  | inputName          | validTime                         | controlledProperties  | Correct? |
| ------ | ------------------ | --------------------------------- | --------------------- | -------- |
| `040g` | `smoke-test-input` | `["2026-02-16T23:24:36Z", "now"]` | `[{label: "Active"}]` | ✅       |
| `0410` | `smoke-test-input` | `["2026-02-16T23:29:03Z", "now"]` | `[{label: "Active"}]` | ✅       |

### parseProperty Regression Check (OSH Only — Validated in Issue #131)

| Property ID | label                             | definition | objectType | Correct? |
| ----------- | --------------------------------- | ---------- | ---------- | -------- |
| `040g`      | Sound Source Direction of Arrival | —          | —          | ✅       |
| `0410`      | Sound Source Energy               | —          | —          | ✅       |
| `041g`      | Sound Source Activity Level       | —          | —          | ✅       |
| `0420`      | Geographic Line of Bearing        | —          | —          | ✅       |
| `042g`      | Triangulated 3D Source Position   | —          | —          | ✅       |
| `0430`      | Detection Energy Threshold        | —          | —          | ✅       |
| `043g`      | Tracking New Source Sensitivity   | —          | —          | ✅       |

> All 7 properties parse correctly. Properties were empty in ST#23 but now have data — this is new coverage, not a regression.

## SensorML Content Negotiation

### OSH (`?f=sml3`)

| Field      | Value                                         |
| ---------- | --------------------------------------------- |
| type       | `PhysicalSystem`                              |
| id         | `03bc5ofvvstg`                                |
| uniqueId   | `urn:osh:driver:mavsdk:cube:replay`           |
| definition | `http://www.w3.org/ns/sosa/Sensor` (full URI) |
| label      | `LIVE - Field Drone`                          |
| validTime  | `["2026-01-26T18:32:01.56Z", "now"]`          |

Structure: Minimal — `{type, id, uniqueId, definition, label, validTime}`. No identifiers/classifiers/components. Consistent with prior observations.

### 52N (`Accept: application/sml+json`)

| Field       | Value                                |
| ----------- | ------------------------------------ |
| type        | `PhysicalSystem`                     |
| id          | `5400-526`                           |
| uniqueId    | `urn:sensor:5400-526`                |
| definition  | `sosa:Sensor` (CURIE — not full URI) |
| label       | `Doppler Current Profiler Sensor`    |
| validTime   | `null`                               |
| identifiers | 2                                    |
| classifiers | 0                                    |

Structure: Rich — includes identifiers, documents, typeOf. Consistent with prior observations.

## Schema Spot-Check

### Datastream Schema: Temperature (`03tbj7mvqg50`)

```json
{
  "obsFormat": "application/om+json",
  "resultSchema": {
    "type": "DataRecord",
    "name": "TemperatureOutput",
    "label": "Temperature",
    "fields": [
      {
        "type": "Quantity",
        "name": "Temperature",
        "uom": { "href": "http://qudt.org/vocab/unit/UNITLESS" }
      }
    ]
  }
}
```

SWE Common DataRecord with 1 Quantity field — consistent with prior schema observations.

## CRUD Smoke Cycle (OSH)

| Operation                 | HTTP Status | Expected | Regression? |
| ------------------------- | ----------- | -------- | ----------- |
| POST /systems (with uid)  | **201**     | 201      | No ✅       |
| GET /systems/04n0         | **200**     | 200      | No ✅       |
| DELETE /systems/04n0      | **204**     | 204      | No ✅       |
| GET /systems/04n0 (after) | **404**     | 404      | No ✅       |

**Details:**

- Created system `04n0` with `uid: urn:smoke-test:p6.1:20260225111731`
- Read back confirmed: `name: P6.1-smoke-test-temp`, `featureType: http://www.w3.org/ns/sosa/Sensor`
- Deleted successfully, confirmed 404 after deletion
- All test data cleaned up — no orphaned resources

> **Note:** Initial POST without `uid` returned 400 "Missing feature UID" — this is expected behavior (known quirk, documented in `known-server-quirks.md`).

## Cross-Server Comparison

| Dimension              | OSH                    | 52N                                 | Match?  |
| ---------------------- | ---------------------- | ----------------------------------- | ------- |
| Conformance classes    | 33                     | 1                                   | ❌      |
| Discovery convention   | Plain rel names        | OGC API Common links only           | ❌      |
| Default content type   | `application/json`     | `application/sml+json`              | ❌      |
| Content negotiation    | `?f=` parameter        | `Accept` header                     | ❌      |
| featureType vocabulary | Full URIs              | Mixed: null / CURIEs / full URIs    | ❌      |
| validTime format       | Array `["ISO", "now"]` | Mostly `null`                       | ❌      |
| SML access             | `?f=sml3`              | `Accept: application/sml+json`      | ❌      |
| SML richness           | Minimal                | Rich                                | ❌      |
| Part 1 endpoints       | ✅ All work            | ✅ systems, deployments, procedures | Partial |
| Part 2 endpoints       | ✅ All work            | ❌ All broken                       | ❌      |
| Write operations       | ✅ Full CRUD           | Not tested                          | —       |
| Auth                   | Basic                  | None                                | —       |
| SSL                    | HTTP                   | HTTPS (expired)                     | —       |

> All differences are consistent with prior smoke tests. No new interoperability concerns.

## Prior Findings — Regression Check

### Phase 5 Findings (P5-F series)

| Finding | Category               | ST#23 Status        | ST#24 Status          | Changed? |
| ------- | ---------------------- | ------------------- | --------------------- | -------- |
| P5-F1   | Server limitation      | Resolved            | **Still Resolved** ✅ | No       |
| P5-F2   | Server data quality    | Open                | **Unchanged**         | No       |
| P5-F3   | Server data quality    | Open                | **Unchanged**         | No       |
| P5-F4   | Server data quality    | Open                | **Unchanged**         | No       |
| P5-F5   | Parser/Model alignment | New (Informational) | **Unchanged**         | No       |

### Key Prior Findings Spot-Check (Phase 2–4)

| Finding | Category          | Previous Status       | ST#24 Status  | Evidence                                                                     |
| ------- | ----------------- | --------------------- | ------------- | ---------------------------------------------------------------------------- |
| F3      | Server limitation | Open                  | **Unchanged** | 52N conformance: now 1 class (OGC API Common Core), still zero CSAPI classes |
| F34     | Server limitation | Open                  | **Unchanged** | OSH `/commands` top-level: still not implemented                             |
| F41     | Server limitation | Open                  | **Unchanged** | 52N systems GeoJSON: `featureType: null` for all 3 systems                   |
| F44     | Interoperability  | Open                  | **Unchanged** | 52N mixes CURIEs and full URIs                                               |
| F84     | Server bug        | Open (filed upstream) | **Unchanged** | 52N procedure `featureType: sosa:Sensor` misclassification                   |

> No prior findings changed status. All are consistent with their documented behavior.

## New Findings

### P6.1-F1 (Informational): 52N `/properties` Now Returns 400 for `geo+json`

**Severity:** Informational
**Category:** Server limitation
**Affects:** 52North `/properties` endpoint
**Ownership:** Upstream
**Evidence:** `GET https://csa.demo.52north.org/properties` with `Accept: application/geo+json` returns `400 InvalidMimetype: "invalid mimetype supplied! expected [] got 'application/geo+json'"`. Previously returned empty collection.
**Status:** Informational — 52N server-side change. Does not affect our library.

### P6.1-F2 (Informational): OSH Conformance Classes Grew from ~20 to 33

**Severity:** Informational
**Category:** Server improvement
**Affects:** OSH conformance endpoint
**Ownership:** Upstream
**Evidence:** `/conformance` now returns 33 classes including `swecommon-text` and `system-event` classes not previously observed.
**Status:** Informational — server-side improvement. Our `checkHasConnectedSystems` already handles dynamic conformance detection.

### P6.1-F3 (Informational): 52N Conformance Classes Grew from 0 to 1

**Severity:** Informational
**Category:** Server improvement
**Affects:** 52N conformance endpoint
**Ownership:** Upstream
**Evidence:** `/conformance` now returns 1 class: `ogcapi-common-1/1.0/conf/core`. Previously returned 0.
**Status:** Informational — server-side improvement. Still zero CSAPI-specific conformance classes.

## What WORKS (Verified)

| Capability                                           | Status |
| ---------------------------------------------------- | ------ |
| Server connectivity (both)                           | ✅     |
| Conformance detection (both)                         | ✅     |
| Resource discovery (OSH: plain rel)                  | ✅     |
| Collection listing (both)                            | ✅     |
| Part 1 resource listing (both, where endpoints work) | ✅     |
| Part 2 resource listing (OSH)                        | ✅     |
| classifyFeature (both — full URI + CURIE + null)     | ✅     |
| parseValidTime (both — array + null)                 | ✅     |
| parseDatastream (OSH)                                | ✅     |
| parseObservation (OSH)                               | ✅     |
| parseControlStream (OSH)                             | ✅     |
| parseProperty (OSH — 7 resources)                    | ✅     |
| SensorML negotiation (both)                          | ✅     |
| SWE Common schema parsing (OSH)                      | ✅     |
| CRUD: Create (OSH)                                   | ✅     |
| CRUD: Read (OSH)                                     | ✅     |
| CRUD: Delete (OSH)                                   | ✅     |
| isCollectionInfo type guard (#130)                   | ✅     |
| factory.spec.ts 6 tests (#132)                       | ✅     |
| endpoint.spec.ts 7 CSAPI tests (#133)                | ✅     |
| property.spec.ts 8 tests incl. live data (#131)      | ✅     |

## CRUD Summary

| Operation | Systems | Deployments | Procedures | SFs | Datastreams | Observations | ControlStreams | Commands |
| --------- | ------- | ----------- | ---------- | --- | ----------- | ------------ | -------------- | -------- |
| Create    | ✅      | —           | —          | —   | —           | —            | —              | —        |
| Read      | ✅      | —           | —          | —   | —           | ✅           | ✅             | —        |
| Delete    | ✅      | —           | —          | —   | —           | —            | —              | —        |

> CRUD cycle focused on systems (create→read→delete) as a regression check. Full CRUD testing across all resource types was performed in ST#23.

## Comparison: Phase 5.5 → Phase 6.1

| Dimension               | Phase 5.5 (ST#23) | Phase 6.1 (ST#24)     |
| ----------------------- | ----------------- | --------------------- |
| Total tests             | ~1,700+           | 1,730                 |
| CSAPI test suites       | 29                | 29+ (61 total)        |
| Issues validated        | #99–#113          | #129–#133             |
| New findings            | 1 (P5-F5)         | 3 (all informational) |
| Library regressions     | 0                 | **0**                 |
| OSH conformance classes | ~20+              | 33                    |
| 52N conformance classes | 0                 | 1                     |
| OSH properties          | 0                 | 7                     |
| Parser regressions      | 0                 | **0**                 |
| CRUD regressions        | 0                 | **0**                 |
| tsc errors              | 0                 | 0                     |
| ESLint errors           | 0                 | 0                     |

## Verdict

**PASS — Zero library regressions. All Phase 6.1 work validated against both live servers.**

All automated tests pass (61 suites, 1,730 tests, 0 failures). TypeScript and ESLint are clean. Both live servers are reachable and respond correctly to all tested endpoints. The CRUD cycle (create → read → delete) completes successfully on OSH with no behavioral changes. All parser spot-checks produce correct output from live data — classifyFeature handles both servers' vocabulary formats, parseValidTime handles arrays and nulls, and all Part 2 parsers (datastream, observation, controlstream, property) extract fields correctly from OSH responses.

The three new findings (P6.1-F1 through P6.1-F3) are all informational and server-side — two are improvements (OSH and 52N added conformance classes) and one is a 52N behavior change (properties endpoint now rejects geo+json). None affect our library code. All five prior Phase 5 findings retain their documented status with no changes.

Phase 6.1 work (Issues #129–#133) focused on code quality improvements — removing unsafe casts, adding a runtime type guard, validating parsers against live data, and expanding test coverage. These changes are confirmed to introduce no runtime regressions against either live server.
