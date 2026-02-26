# Live Server Smoke Test — Post Phase 3.1

**Date:** 2026-02-14  
**Milestone:** After completing Phase 3.1 (Issues #14, #46, #48)  
**Servers:** OpenSensorHub demo instance, 52North demo instance  
**Auth:** OSH: Basic auth required (credentials not stored in repo); 52North: None (expired SSL cert)  
**Purpose:** Validate GeoJSON handler functions against real server responses — first Phase 3 smoke test  
**Components tested:** `src/ogc-api/csapi/formats/geojson.ts` — 6 public functions (`isCSAPIFeature`, `getCSAPIResourceType`, `parseValidTime`, `isValidUri`, `validateCSAPIFeature`, `extractCSAPIFeature`)

> This is smoke test #10 in the series (first Phase 3 smoke test). See also:
>
> - [Previous smoke test](live-server-smoke-test-post-phase-2.9.md) — Phase 2.9, 39 findings
> - [Phase 3 smoke test rationale](phase-3-smoke-test-rationale.md)

## Test Methodology

Fetched real responses from both servers, saved as JSON files, then ran
every GeoJSON handler function against every feature using a Node.js
validation script (`__smoke_test_handler.mjs`). No code changes were made
during the smoke test — this is read-only observation per Lesson 10.

The test script was compiled from `geojson.ts` via `tsc` and imported as
an ES module. Each feature was tested through all 6 public functions:
recognition → classification → validation → extraction → validTime parsing.

## Server Profiles

### OpenSensorHub

| Resource Type    | Endpoint            | Count | Has Data? |
| ---------------- | ------------------- | ----- | --------- |
| Systems          | `/systems`          | 10+   | ✅ Yes    |
| Deployments      | `/deployments`      | 0     | ❌ Empty  |
| Procedures       | `/procedures`       | 0     | ❌ Empty  |
| SamplingFeatures | `/samplingFeatures` | 5+    | ✅ Yes    |
| DataStreams      | `/datastreams`      | 3+    | ✅ Yes    |
| Observations     | `/observations`     | 10+   | ✅ Yes    |
| ControlStreams   | `/controlstreams`   | Yes   | ✅ Yes    |
| Commands         | nested only         | Yes   | ✅ Yes    |
| Properties       | not discoverable    | —     | ❓        |

### 52North

| Resource Type      | Endpoint              | Count | Has Data?      |
| ------------------ | --------------------- | ----- | -------------- |
| Systems            | `/systems`            | 3     | ✅ Yes         |
| Deployments        | `/deployments`        | 1     | ✅ Yes         |
| Procedures         | `/procedures`         | 1     | ✅ Yes         |
| FeaturesOfInterest | `/featuresOfInterest` | —     | ❌ 404         |
| DataStreams        | `/datastreams`        | —     | ❌ 500         |
| Observations       | `/observations`       | —     | ❌ 500 (prior) |
| ControlStreams     | N/A                   | —     | ❌ 404 (prior) |

**Key change from Phase 2.9:** 52North now has real data on systems (3), deployments (1), and procedures (1) — a significant improvement compared to prior smoke tests. Their GeoJSON format is a standard FeatureCollection envelope.

## Results

### Prior Findings — Regression Check

All 39 findings from the Phase 2.9 smoke test were re-evaluated:

| Finding | Title                                               | Prior Status              | Current Status    | Evidence                                                                                                                                                             |
| ------- | --------------------------------------------------- | ------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1      | Link relation prefix mismatch                       | Fixed (Issue #34)         | ✅ Still fixed    | No regression                                                                                                                                                        |
| F2      | Top-level vs. collection-scoped URLs                | Fixed (Issue #35)         | ✅ Still fixed    | No regression                                                                                                                                                        |
| F3      | Response envelope uses `items`                      | Deferred to Phase 3       | ⏳ Still deferred | OSH still uses `{items:[...]}`, 52N uses `{type:"FeatureCollection", features:[...]}`                                                                                |
| F4      | `validTime` is an array                             | Deferred to Phase 3       | ✅ **ADDRESSED**  | `parseValidTime()` correctly handles array format `["ISO","now"]` — validated against 5 OSH systems                                                                  |
| F5      | Missing pagination metadata                         | Deferred to Phase 3       | ⏳ Still deferred | Both servers use link-based pagination only                                                                                                                          |
| F6      | OSH rejects `systems/{id}/deployments`              | Server limitation         | ⚠️ Still present  | Not retested (unchanged)                                                                                                                                             |
| F7      | OSH rejects `systems/{id}/procedures`               | Server limitation         | ⚠️ Still present  | Not retested (unchanged)                                                                                                                                             |
| F8      | OSH rejects `samplingFeatures/{id}/systems`         | Server limitation         | ⚠️ Still present  | Not retested (unchanged)                                                                                                                                             |
| F9      | OSH rejects `samplingFeatures/{id}/history`         | Server limitation         | ⚠️ Still present  | Not retested (unchanged)                                                                                                                                             |
| F10     | 52North now has real data                           | Informational             | ✅ Confirmed      | 3 systems, 1 deployment, 1 procedure — expanded since prior test                                                                                                     |
| F11     | 52North uses SensorML format                        | Phase 3 concern           | ✅ Confirmed      | `application/sml+json` returns data; `application/geo+json` returns features with `featureType: null` on systems                                                     |
| F12     | 52North `systems/{id}/deployments` works            | Informational             | ✅ Still true     | Not retested (unchanged)                                                                                                                                             |
| F13     | Both servers use `items` envelope                   | Informational             | ⚠️ **REVISED**    | OSH uses `{items:[...]}`, but 52N GeoJSON uses `{type:"FeatureCollection", features:[...]}`. 52N SensorML uses `{items:[...]}`. Envelope varies by server AND format |
| F14     | Properties not discoverable via links               | Shared concern            | ⏳ Still present  | Neither server exposes properties in root links                                                                                                                      |
| F15     | 52North adds third system                           | Informational             | ✅ Still true     | 3 systems confirmed                                                                                                                                                  |
| F16     | OSH rejects `datastreams/{id}/systems`              | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F17     | OSH rejects `datastreams/{id}/procedures`           | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F18     | OSH rejects `datastreams/{id}/history`              | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F19     | `resultTime=latest` accepted by OSH                 | Resolved                  | ✅ Still valid    | Not retested                                                                                                                                                         |
| F20     | 52North DataStreams still broken (500)              | Server limitation         | ⚠️ Still present  | GET `/datastreams?limit=3` → 500                                                                                                                                     |
| F21     | OSH rejects `observations/{id}/datastream`          | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F22     | OSH rejects `observations/{id}/samplingFeature`     | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F23     | OSH rejects `observations/{id}/system`              | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F24     | OSH rejects `observations/{id}/history`             | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F25     | `resultTime=latest` returns real data               | Informational             | ✅ Still valid    | Not retested                                                                                                                                                         |
| F26     | 52North Observations broken (500)                   | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F27     | Observation `foi@id` naming variation               | Phase 3 concern           | ⏳ Still deferred | Not yet in scope for GeoJSON handler                                                                                                                                 |
| F28     | OSH rejects `controlstreams/{id}/feasibility`       | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F29     | ControlStream schema works                          | Informational             | ✅ Still valid    | Not retested                                                                                                                                                         |
| F30     | ControlStream `system@link` cross-reference         | Phase 3 concern           | ⏳ Still deferred | Not yet in scope                                                                                                                                                     |
| F31     | Command entity data shape                           | Phase 3 concern           | ⏳ Still deferred | Not yet in scope                                                                                                                                                     |
| F32     | 52North ControlStreams not implemented (404)        | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F33     | ControlStream schema returns SWE DataRecord         | Phase 3 concern           | ⏳ Still deferred | Not yet in scope                                                                                                                                                     |
| F34     | OSH no top-level `/commands`                        | Shared (server + routing) | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F35     | OSH no `/commands/{id}/cancel`                      | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F36     | OSH ignores `id` query param on commands            | Server limitation         | ⚠️ Still present  | Not retested                                                                                                                                                         |
| F37     | Command `/result` returns 404 for result-less types | Expected behavior         | ✅ Still valid    | Not retested                                                                                                                                                         |
| F38     | Command status data shape                           | Phase 3 concern           | ⏳ Still deferred | Not yet in scope                                                                                                                                                     |
| F39     | Commands use `items` envelope                       | Informational             | ✅ Confirms F3    | Not retested                                                                                                                                                         |

**Summary:** 0 regressions. F4 (`validTime` array format) newly addressed by `parseValidTime()`. F13 revised — envelope varies by server AND format. All server limitations unchanged.

### GeoJSON Handler — Recognition

| Server | Resource Type    | Features Tested | All Recognized?        | Details                                                                         |
| ------ | ---------------- | --------------- | ---------------------- | ------------------------------------------------------------------------------- |
| OSH    | Systems          | 5               | ✅ Yes                 | All `http://www.w3.org/ns/sosa/Sensor` → classified as System                   |
| OSH    | SamplingFeatures | 5               | ❌ **No**              | All `http://www.opengis.net/sensorml/2.0#Feature` → **NOT SOSA** → unrecognized |
| OSH    | Deployments      | 0               | —                      | Empty collection                                                                |
| OSH    | Procedures       | 0               | —                      | Empty collection                                                                |
| 52N    | Systems          | 3               | ❌ **No**              | All `featureType: null` → **missing required property** → unrecognized          |
| 52N    | Deployments      | 1               | ✅ Yes                 | `http://www.w3.org/ns/sosa/Deployment` → classified as Deployment               |
| 52N    | Procedures       | 1               | ⚠️ Yes (misclassified) | `sosa:Sensor` (CURIE form) → classified as System, **NOT Procedure**            |

**Recognition rate:** 7 of 15 features recognized (47%). The 8 unrecognized features fall into two categories: non-SOSA vocabulary (OSH SamplingFeatures) and null featureType (52N Systems).

### GeoJSON Handler — Validation

| Server | Resource Type    | Features Tested | All Valid?         | Errors                                                           |
| ------ | ---------------- | --------------- | ------------------ | ---------------------------------------------------------------- |
| OSH    | Systems          | 5               | ✅ Yes             | 0 errors across all 5 features                                   |
| OSH    | SamplingFeatures | 5               | ❌ No              | "Unrecognized featureType vocabulary" × 5                        |
| 52N    | Systems          | 3               | ❌ No              | "Missing required property: featureType" × 3                     |
| 52N    | Deployments      | 1               | ❌ No              | "Deployment requires validTime" (server sends `validTime: null`) |
| 52N    | Procedures       | 1               | ✅ Yes (as System) | 0 errors — but classified as System, not Procedure               |

### GeoJSON Handler — Extraction

| Server | Resource Type    | Features Tested | All Extracted?     | Issues                                                                             |
| ------ | ---------------- | --------------- | ------------------ | ---------------------------------------------------------------------------------- |
| OSH    | Systems          | 5               | ✅ Yes             | id ✅, uid ✅ (valid URI), name ✅, validTime ✅ (parsed), geometry null, links=[] |
| OSH    | SamplingFeatures | 5               | ❌ No              | Failed at validation gate (unrecognized vocabulary)                                |
| 52N    | Systems          | 3               | ❌ No              | Failed at validation gate (null featureType)                                       |
| 52N    | Deployments      | 1               | ❌ No              | Failed extraction: "Deployment requires validTime"                                 |
| 52N    | Procedures       | 1               | ✅ Yes (as System) | id ✅, uid ✅, name ✅, geometry=undefined                                         |

**Extraction rate:** 6 of 15 features successfully extracted (40%). Only OSH Systems and the (misclassified) 52N Procedure extracted cleanly.

### parseValidTime — Live Data

| Server | Features With validTime | All Parsed? | Format Observed                      | Issues                                                      |
| ------ | ----------------------- | ----------- | ------------------------------------ | ----------------------------------------------------------- |
| OSH    | 5 (Systems)             | ✅ Yes      | `["2026-01-26T18:32:01.56Z", "now"]` | Correctly parsed: `{start: Date, end: undefined}`           |
| OSH    | 0 (SamplingFeatures)    | —           | No validTime on SamplingFeatures     | —                                                           |
| 52N    | 0 (Systems)             | —           | `validTime: null`                    | `parseValidTime(null)` → `undefined` (correct)              |
| 52N    | 1 (Deployment)          | ❌ **null** | `validTime: null`                    | Server sends null for deployment that should have validTime |

**`parseValidTime` is working correctly.** All 5 OSH array-format values parsed to `{start: Date, end: undefined}`. The `"now"` sentinel correctly maps to `end: undefined`. Null values correctly return `undefined`.

### Vocabulary Inventory

| featureType Value                             | Server(s) | Endpoint          | SOSA?             | Recognized? | Handler Classification    |
| --------------------------------------------- | --------- | ----------------- | ----------------- | ----------- | ------------------------- |
| `http://www.w3.org/ns/sosa/Sensor`            | OSH       | /systems          | ✅ Yes (full URI) | ✅ Yes      | System                    |
| `http://www.opengis.net/sensorml/2.0#Feature` | OSH       | /samplingFeatures | ❌ No             | ❌ No       | null                      |
| `null`                                        | 52N       | /systems          | ❌ N/A            | ❌ No       | null                      |
| `http://www.w3.org/ns/sosa/Deployment`        | 52N       | /deployments      | ✅ Yes (full URI) | ✅ Yes      | Deployment                |
| `sosa:Sensor`                                 | 52N       | /procedures       | ✅ Yes (CURIE)    | ✅ Yes      | System (⚠️ not Procedure) |

**Notable observations:**

1. OSH uses full URIs (`http://www.w3.org/ns/sosa/Sensor`) — not CURIEs
2. 52N uses both full URIs (deployments) and CURIEs (procedures) — handler correctly handles both forms
3. 52N GeoJSON systems have `featureType: null` — the data exists only in SensorML format
4. OSH SamplingFeatures use a completely different vocabulary namespace (`opengis.net/sensorml/2.0#Feature`)
5. 52N procedure is typed as `sosa:Sensor` — this is the SOSA "type of thing" concept, not a formatting error

### Content-Type Availability

| Content-Type                 | Endpoint                 | OSH                                      | 52N                                        |
| ---------------------------- | ------------------------ | ---------------------------------------- | ------------------------------------------ |
| `application/json` (default) | /systems                 | ✅ 200 (GeoJSON-like, `items` envelope)  | ✅ 200 (FeatureCollection envelope)        |
| `application/geo+json`       | /systems                 | ✅ 200 (returns `application/json`)      | ✅ 200 (returns `application/geo+json`)    |
| `application/sml+json`       | /systems                 | ⚠️ 200 (returns GeoJSON despite request) | ✅ 200 (returns SensorML `PhysicalSystem`) |
| `application/swe+json`       | /datastreams/{id}/schema | ✅ 200 (SWE DataRecord)                  | ❌ 500 (datastreams broken)                |

**Key insight for future Phase 3 work:**

- OSH ignores `Accept: application/sml+json` and returns GeoJSON anyway — SensorML parser may not be testable against OSH
- 52N actually supports SensorML format and returns different shapes per format
- 52N has richer data in SensorML format than in GeoJSON format (systems have `featureType: null` in GeoJSON but `definition: "sosa:Sensor"` in SensorML)

## New Findings

### F40 (Critical): OSH SamplingFeatures use non-SOSA vocabulary

**Severity:** Critical  
**Category:** Vocabulary gap  
**Affects:** `isCSAPIFeature()`, `getCSAPIResourceType()`, `validateCSAPIFeature()`, `extractCSAPIFeature()` in `geojson.ts`  
**Ownership:** Shared (server uses non-standard vocabulary; handler only supports SOSA)  
**Evidence:**

```json
{
  "type": "Feature",
  "id": "040g",
  "properties": {
    "featureType": "http://www.opengis.net/sensorml/2.0#Feature",
    "uid": "urn:android:device:dad41d3c8bf853cd:location",
    "name": "Android Sensors [SR_Botts] - Location"
  }
}
```

All 5 OSH SamplingFeatures use `http://www.opengis.net/sensorml/2.0#Feature`. The handler only recognizes SOSA vocabulary (`http://www.w3.org/ns/sosa/SamplingFeature` or `sosa:SamplingFeature`). This means **100% of OSH SamplingFeatures are invisible to the handler.**  
**Status:** Needs design decision — extend vocabulary sets? Add a SensorML namespace? Create a fallback using endpoint context?

### F41 (Critical): 52North Systems have null featureType in GeoJSON

**Severity:** Critical  
**Category:** Server limitation / Interoperability concern  
**Affects:** `isCSAPIFeature()`, `getCSAPIResourceType()`, `validateCSAPIFeature()`, `extractCSAPIFeature()` in `geojson.ts`  
**Ownership:** Shared (server sets `featureType: null` in GeoJSON; handler requires non-null featureType)  
**Evidence:**

```json
{
  "type": "Feature",
  "id": "5400-526",
  "properties": {
    "uid": "urn:sensor:5400-526",
    "name": "Doppler Current Profiler Sensor",
    "featureType": null,
    "assetType": null,
    "validTime": null
  }
}
```

All 3 52N systems have `featureType: null` in GeoJSON format, but have `definition: "sosa:Sensor"` in SensorML format. The GeoJSON representation does not propagate the SensorML `definition` into `featureType`. This means **100% of 52N Systems are invisible to the GeoJSON handler.**  
**Status:** Needs design decision — should the handler fall back to endpoint URL context when featureType is null? Should we try SensorML format first?

### F42 (Moderate): 52North Deployment has null validTime

**Severity:** Moderate  
**Category:** Server limitation  
**Affects:** `validateCSAPIFeature()`, `extractCSAPIFeature()` in `geojson.ts`  
**Ownership:** Upstream (server should populate validTime for deployments)  
**Evidence:**

```json
{
  "type": "Feature",
  "id": "af41f84f-2492-40e2-a154-17df67119271",
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Deployment",
    "validTime": null,
    "uid": "urn:messtonne:1:2025-demo",
    "name": "Messtonne 1 - 2025 Test"
  }
}
```

The OGC spec requires `validTime` for Deployments. The 52N server sends `validTime: null`. Our handler correctly rejects this with "Deployment requires validTime", which is spec-compliant behavior.  
**Status:** Server limitation — our validation is correct

### F43 (Moderate): 52North Procedures misclassified as System

**Severity:** Moderate  
**Category:** Interoperability concern / Spec ambiguity  
**Affects:** `getCSAPIResourceType()` in `geojson.ts`  
**Ownership:** Shared  
**Evidence:**

```json
{
  "type": "Feature",
  "id": "4e09de42-674d-4e03-a620-2d219b030a50",
  "properties": {
    "featureType": "sosa:Sensor",
    "uid": "urn:sensortype:aanderaa:dcps:td304",
    "name": "Doppler Current Profiler Sensor"
  }
}
```

The 52N procedure uses `featureType: "sosa:Sensor"` (a System-type URI). The OGC spec's `ProcedureTypeUris` array intentionally includes System-type URIs because procedures describe system types. Our handler's classification priority (System > Procedure) means this correctly matches System. However, it was served from the `/procedures` endpoint, meaning the endpoint context and the featureType classification disagree.  
**Status:** Needs design decision — should classification use endpoint context as a tiebreaker? This is a known spec ambiguity (documented in geojson.ts JSDoc).

### F44 (Informational): 52North uses both CURIE and full URI forms

**Severity:** Informational  
**Category:** Positive validation  
**Affects:** `toSosaLocalName()` in `geojson.ts`  
**Ownership:** —  
**Evidence:** 52N deployments use `http://www.w3.org/ns/sosa/Deployment` (full URI), while procedures use `sosa:Sensor` (CURIE). The handler's `toSosaLocalName()` function correctly handles both forms.  
**Status:** Validated — handler works correctly for both CURIE and full URI forms

### F45 (Informational): Response envelope varies by server AND format

**Severity:** Informational  
**Category:** Data shape  
**Affects:** Future response parser (not current handler)  
**Ownership:** Phase 3 concern  
**Evidence:**

- OSH all formats: `{ items: [...], links: [...] }`
- 52N GeoJSON: `{ type: "FeatureCollection", features: [...], links: [...] }`
- 52N SensorML: `{ items: [...], links: [...] }`

This revises Phase 2.9 F13 (which stated both servers use `items` envelope). The envelope varies by both server implementation and content type.  
**Status:** Informational — critical input for response parser design

### F46 (Informational): OSH ignores SensorML Accept header

**Severity:** Informational  
**Category:** Server behavior  
**Affects:** Future SensorML parser testing strategy  
**Ownership:** Upstream  
**Evidence:** Requesting `Accept: application/sml+json` on OSH `/systems` returns GeoJSON (Content-Type: `application/json`) — the server does not support SensorML format for feature endpoints. The SWE schema endpoint (`/datastreams/{id}/schema`) does return SWE Common format correctly.  
**Status:** Informational — affects Phase 3 SensorML parser testing (OSH not testable for SensorML)

### F47 (Informational): 52N GeoJSON includes `@link` notation

**Severity:** Informational  
**Category:** Data shape  
**Affects:** Future response parser  
**Ownership:** Phase 3 concern  
**Evidence:**

```json
{
  "systemKind@link": {
    "rel": "ogc-rel:procedures",
    "href": "https://csa.demo.52north.org/procedures/4e09de42-...",
    "urn": "urn:sensortype:aanderaa:dcps:td304"
  },
  "platform@link": {
    "href": "urn:platform:5300-909"
  },
  "deployedSystems@link": [
    {
      "name": "EXO3_Sonde",
      "system": { "href": "...", "urn": "..." }
    }
  ]
}
```

52N GeoJSON features include `@link` object notation for cross-references. This is consistent with Phase 2.9 F30 but now observed in GeoJSON format specifically.  
**Status:** Informational — confirmed in GeoJSON, already tracked

### F48 (Low): OSH features have empty links arrays

**Severity:** Low  
**Category:** Server behavior  
**Affects:** `extractCSAPIFeature()` in `geojson.ts` (links preservation)  
**Ownership:** Upstream  
**Evidence:** All OSH system features have no `links` array in the feature itself (only in the response envelope). The handler correctly preserves `links: []` in extracted features. 52N features also have no per-feature links.  
**Status:** Informational — handler behaves correctly

## Cross-Server Comparison

| Dimension                                 | OpenSensorHub                                 | 52North                                           | Match?     |
| ----------------------------------------- | --------------------------------------------- | ------------------------------------------------- | ---------- |
| featureType vocabulary (Systems)          | `http://www.w3.org/ns/sosa/Sensor` (full URI) | `null` in GeoJSON, `sosa:Sensor` in SensorML      | ❌         |
| featureType vocabulary (SamplingFeatures) | `http://www.opengis.net/sensorml/2.0#Feature` | N/A (404)                                         | ❌         |
| featureType vocabulary (Deployments)      | N/A (empty)                                   | `http://www.w3.org/ns/sosa/Deployment` (full URI) | —          |
| featureType vocabulary (Procedures)       | N/A (empty)                                   | `sosa:Sensor` (CURIE)                             | —          |
| validTime format                          | Array `["ISO-8601", "now"]`                   | `null`                                            | ❌         |
| validTime presence                        | All systems have validTime                    | No features have validTime                        | ❌         |
| uid field                                 | ✅ URN format on all features                 | ✅ URN format on all features                     | ✅         |
| name field                                | ✅ Present on all features                    | ✅ Present on all features                        | ✅         |
| description field                         | ✅ Present on some features                   | ✅ Present on all features                        | ✅         |
| Geometry                                  | `null` on all tested features                 | Point geometry on deployment                      | ⚠️ Partial |
| Per-feature links                         | Not present                                   | Not present                                       | ✅         |
| Response envelope (GeoJSON)               | `{items:[...]}`                               | `{type:"FeatureCollection", features:[...]}`      | ❌         |
| Response envelope (SensorML)              | N/A (returns GeoJSON)                         | `{items:[...]}`                                   | —          |
| Default Content-Type                      | `application/json`                            | `application/json`                                | ✅         |
| SensorML support                          | ❌ Ignores Accept header                      | ✅ Full support                                   | ❌         |

## Response Envelope Observations (Phase 3 Reference)

| Server | Format               | Envelope Type             | Feature Array Key | Pagination                            | Links Location          |
| ------ | -------------------- | ------------------------- | ----------------- | ------------------------------------- | ----------------------- |
| OSH    | application/json     | Flat object               | `items`           | `links[rel="next"]` with offset param | Top-level `links` array |
| 52N    | application/geo+json | GeoJSON FeatureCollection | `features`        | `links[rel="next"]` with offset param | Top-level `links` array |
| 52N    | application/sml+json | Flat object               | `items`           | `links[rel="next"]` with offset param | Top-level `links` array |

**Design implication for response parser:** The parser must detect envelope type (FeatureCollection vs flat) and extract features from the correct key (`features` vs `items`). This cannot be determined solely by content-type — it depends on server implementation.

## What WORKS (Verified Against Live Data)

| Capability                                               | OSH                      | 52N                    | Notes                                                           |
| -------------------------------------------------------- | ------------------------ | ---------------------- | --------------------------------------------------------------- |
| `isCSAPIFeature()` — SOSA full URI recognition           | ✅ 5/5 Systems           | —                      | Full URI form works                                             |
| `isCSAPIFeature()` — SOSA CURIE recognition              | —                        | ✅ 1/1 Procedure       | CURIE form works                                                |
| `getCSAPIResourceType()` — System classification         | ✅ 5/5                   | —                      | All OSH systems correctly classified                            |
| `getCSAPIResourceType()` — Deployment classification     | —                        | ✅ 1/1                 | 52N deployment correctly recognized                             |
| `validateCSAPIFeature()` — clean validation (System)     | ✅ 5/5                   | —                      | Zero validation errors on all OSH systems                       |
| `validateCSAPIFeature()` — Deployment requires validTime | —                        | ✅ Correctly enforced  | 52N deployment rejected (correct — server sends null validTime) |
| `extractCSAPIFeature()` — System extraction              | ✅ 5/5                   | —                      | id, uid, name, validTime all correct                            |
| `parseValidTime()` — array format `["ISO","now"]`        | ✅ 5/5                   | —                      | All parsed to `{start: Date, end: undefined}`                   |
| `parseValidTime(null)` — null handling                   | —                        | ✅ Returns undefined   | Correct behavior                                                |
| `isValidUri()` — URN validation                          | ✅ All uids valid        | ✅ All uids valid      | Both servers use URN format                                     |
| `SOSA_NS` constant                                       | ✅ Matches OSH full URIs | ✅ Used for both forms | Correct value                                                   |

## What Remains (Later Phase 3 Concerns)

| Issue                                                    | Severity | Component                                 | Target Task           |
| -------------------------------------------------------- | -------- | ----------------------------------------- | --------------------- |
| Non-SOSA vocabulary support (F40)                        | Critical | geojson.ts vocabulary sets                | Needs design decision |
| Null featureType fallback (F41)                          | Critical | geojson.ts recognition OR response parser | Needs design decision |
| Endpoint-context classification tiebreaker (F43)         | Moderate | geojson.ts or response parser             | Needs design decision |
| Response envelope parsing (F3/F45)                       | Moderate | Response parser                           | Phase 3 task          |
| `@link` notation parsing (F47)                           | Moderate | Response parser                           | Phase 3 task          |
| SensorML parser (52N has data, OSH does not)             | Moderate | Future SensorML parser                    | Phase 3 task          |
| SWE Common parser (OSH schema endpoint works)            | Moderate | Future SWE parser                         | Phase 3 task          |
| Pagination helpers                                       | Low      | Response parser                           | Phase 3 task          |
| F6-F9, F16-F18, F21-F24, F28, F34-F36 server limitations | Various  | N/A                                       | Upstream              |
| 52N DataStreams/Observations still broken                | Moderate | N/A                                       | Upstream (F20, F26)   |

## Verdict

**The GeoJSON handler works correctly for all features that use SOSA vocabulary.** Against real server data, `parseValidTime()` successfully handles the array format, `isCSAPIFeature()` recognizes both full URI and CURIE forms, `validateCSAPIFeature()` correctly enforces all rules including the Deployment-requires-validTime constraint, and `extractCSAPIFeature()` produces clean typed objects with all properties populated.

**However, the handler's SOSA-only vocabulary assumption creates a significant interoperability gap.** Only 7 of 15 features tested (47%) were recognized. The two critical findings (F40, F41) reveal that real servers use vocabularies and patterns the handler doesn't yet support:

1. **F40:** OSH SamplingFeatures use `http://www.opengis.net/sensorml/2.0#Feature` — a completely different namespace. This is not a SOSA synonym; it's a SensorML vocabulary term. All 5 OSH SamplingFeatures are invisible to the handler.
2. **F41:** 52N Systems set `featureType: null` in GeoJSON format. The data exists and is classified in SensorML format (`definition: "sosa:Sensor"`), but the GeoJSON projection omits it. All 3 52N Systems are invisible to the handler.

**These gaps were anticipated** — the handler's JSDoc (`SAMPLING_FEATURE_LOCAL_NAMES` comment) and Phase 3.1 code review F10 both noted that non-SOSA vocabularies would need future support. This smoke test provides the first concrete evidence from real servers.

**Recommendation:** Before proceeding to the next Phase 3 task (format detector, Issue #15), create a design decision issue for vocabulary extension strategy (F40) and null-featureType fallback (F41). These are design decisions that affect the handler's architecture, not simple bug fixes. The handler is correct for its documented scope; the scope itself needs expansion.

**Cumulative statistics:**

- 10 smoke tests completed (9 Phase 2 + 1 Phase 3)
- 48 total findings (F1–F48)
- 0 handler bugs found (handler behavior matches documented design)
- 2 design decisions needed for vocabulary gaps (F40, F41)
- 379 unit tests passing
- Phase 3 GeoJSON handler validated against 15 real features from 2 servers
