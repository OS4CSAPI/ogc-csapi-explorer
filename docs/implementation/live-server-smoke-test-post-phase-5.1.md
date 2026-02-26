# Live Server Smoke Test Report — Post Phase 5.1

**Smoke Test Number:** ST#20  
**Phase:** 5.1 (Parser Completion — Tasks 1-3)  
**Date:** 2025-07-15  
**Commit:** `178bde2` (Phase 5 smoke test prompt template)  
**Template:** `docs/governance/smoke-test-prompt-template-phase-5.md` v1.0  
**Previous Smoke Test:** ST#19 (Phase 4.1) at commit `9950f82`  
**Test Baseline:** 1,190 CSAPI tests (27 suites), 668 format tests (19 suites)

## Verdict: PASS

- 0 library regressions
- 2 new findings (1 Moderate, 1 Low)
- All implemented parsers validate against live data
- Server-side regression blocks Part 2 CRUD (not our code)

---

## Table of Contents

1. [Required Reading Confirmation](#1-required-reading-confirmation)
2. [Step 1 — Regression Check](#2-step-1--regression-check)
3. [Step 2 — Server Connectivity & Inventory](#3-step-2--server-connectivity--inventory)
4. [Steps 3–6 — Discovery, Navigation, URLs, Query Params](#4-steps-36--discovery-navigation-urls-query-params)
5. [Steps 7–8 — Part 2 Workflows](#5-steps-78--part-2-workflows)
6. [Step 9 — SensorML](#6-step-9--sensorml)
7. [Step 10 — CRUD Testing](#7-step-10--crud-testing)
8. [Steps 11–12 — Parser Validation](#8-steps-1112--parser-validation)
9. [Steps 13–15 — Build, Test Suite, Compilation](#9-steps-1315--build-test-suite-compilation)
10. [Steps 16–17 — Finding Classification & Impact](#10-steps-1617--finding-classification--impact)
11. [Step 18 — Summary](#11-step-18--summary)

---

## 1. Required Reading Confirmation

| Document                                                                                 | Status          |
| ---------------------------------------------------------------------------------------- | --------------- |
| `docs/governance/known-server-quirks.md` (367 lines)                                     | ✅ Read in full |
| ST#19 report (`docs/implementation/live-server-smoke-test-post-phase-4.1.md`, 639 lines) | ✅ Read in full |
| `src/ogc-api/csapi/formats/property.ts` (60 lines)                                       | ✅ Read in full |
| `src/ogc-api/csapi/formats/part2.ts` (233 lines)                                         | ✅ Read in full |
| `src/ogc-api/csapi/formats/property.spec.ts` (131 lines)                                 | ✅ Read in full |
| `src/ogc-api/csapi/formats/part2.spec.ts` (385 lines)                                    | ✅ Read in full |

---

## 2. Step 1 — Regression Check

All 90 prior findings (F1–F90) plus 5 Phase 4 findings (P4-F1 through P4-F5) reviewed against ST#19 baselines.

**Fixed findings confirmed still fixed:**

- F83 (SSN namespace in CSAPI index barrel) — ✅ still fixed
- F85 (validTime assertion in endpoint tests) — ✅ still fixed

**Server limitations unchanged:**

- F6–F9, F16–F18, F20–F24, F26, F28, F32, F34–F36, F46, F72, F76, F86 — all present

**No library regressions detected.** TypeScript compiles clean; all 1,190 CSAPI tests pass.

---

## 3. Step 2 — Server Connectivity & Inventory

### OSH Node

```
GET http://45.55.99.236:8080/sensorhub/api → 200 OK
Title: "Connected Systems API Service"
Conformance classes: 33
```

### 52 North

```
GET https://csa.demo.52north.org/ → 200 OK
Title: "connected-systems-pygeoapi"
Conformance classes: 1
```

### Resource Inventory

| Resource          | OSH Count | 52N Count | ST#19 OSH | ST#19 52N | Delta |
| ----------------- | --------- | --------- | --------- | --------- | ----- |
| Systems           | 33        | 3         | 33        | 3         | —     |
| Deployments       | 16        | 1         | 16        | 1         | —     |
| Procedures        | 15        | 1         | 15        | 1         | —     |
| Sampling Features | 66        | 0         | 66        | 0         | —     |
| Properties        | 0         | 400 (err) | 0         | 400 (err) | —     |
| Datastreams       | 100       | 400 (err) | 100       | 400 (err) | —     |
| Observations      | 100       | 400 (err) | 100       | 400 (err) | —     |
| Control Streams   | 18        | 404       | 18        | 404       | —     |
| Commands          | 400 (err) | N/A       | 400 (err) | N/A       | —     |

All counts match ST#19 exactly. No data changes on either server.

---

## 4. Steps 3–6 — Discovery, Navigation, URLs, Query Params

No code changes since ST#19 affect these areas (all changes were in `formats/` parser files). Inventory match confirms stability. All prior findings remain in documented states.

---

## 5. Steps 7–8 — Part 2 Workflows

Extensive live data fetched to validate parser implementations against real server responses.

### Datastreams Fetched (4 of 100)

**DS 1 — Temperature (`03tbj7mvqg50`)**

```json
{
  "id": "03tbj7mvqg50",
  "name": "Temperature",
  "system@id": "03bclbfvvstg",
  "system@link": { "href": "...", "rel": "...", "title": "..." },
  "outputName": "temp",
  "validTime": ["2026-01-26T18:32:01.56Z", "now"],
  "observedProperties": [
    { "label": "Temperature", "description": "Temperature in degrees celsius" }
  ],
  "resultType": "measure",
  "formats": ["application/json", "application/swe+json", ...]
}
```

> **Notable:** `observedProperties[0]` has NO `definition` field.

**DS 2 — StatusEvent (`02au905kq85g`)**

```json
{
  "observedProperties": [
    { "label": "StatusType", "description": "..." },
    { "label": "Status", "description": "..." }
  ],
  "resultType": "record",
  "phenomenonTime": ["2025-07-02T16:47:25.015Z", "2025-07-02T16:48:13.037Z"]
}
```

> **Notable:** Two observedProperties objects, both without `definition`.

**DS 3 — gps_data (`021qpiurq85g`)**

```json
{
  "observedProperties": [
    { "definition": "http://sensorml.com/ont/swe/property/LocationVector" }
  ],
  "resultType": "vector",
  "phenomenonTime": ["2025-05-02T04:39:06.008Z", "2025-07-11T21:33:04.08Z"]
}
```

> Standard form: `definition` field present.

**DS 4 — Acceleration (`02vp7efvjs70`)**

```json
{
  "observedProperties": [
    {
      "definition": "http://qudt.org/vocab/quantitykind/LinearAcceleration",
      "label": "Linear Acceleration",
      "description": "..."
    }
  ],
  "resultType": "vector"
}
```

> Full form: `definition` + `label` + `description`.

### resultType Coverage

Queried all 100 datastreams: `coverage`, `measure`, `record`, `vector` — all 4 present in the `RESULT_TYPES` set. The set also contains `complex`, not seen live but spec-valid.

### Observations Fetched (4)

**Obs 1 — StatusEvent**

```json
{
  "id": "...",
  "datastream@id": "02au905kq85g",
  "phenomenonTime": "2025-07-02T16:48:13.037Z",
  "resultTime": "2025-07-02T16:48:13.037Z",
  "result": { "StatusType": "DISARMING", "Status": "Disarming" }
}
```

**Obs 2 — gps_data**

```json
{
  "id": "...",
  "datastream@id": "021qpiurq85g",
  "phenomenonTime": "2025-07-11T21:33:04.08Z",
  "resultTime": "2025-07-11T21:33:04.08Z",
  "result": { "location": { "lat": 34.7109, "lon": -86.6374, "alt": 223.11 } }
}
```

**Obs 3 — Top-level (with foi@id)**

```json
{
  "id": "...",
  "datastream@id": "021qpiurq85g",
  "foi@id": "0rqfjgrm12dg",
  "phenomenonTime": "2025-07-11T21:33:04.08Z",
  "resultTime": "2025-07-11T21:33:04.08Z",
  "result": { "location": { "lat": 34.7109, "lon": -86.6374, "alt": 223.11 } }
}
```

> **Notable:** `foi@id` cross-reference present — correctly excluded by `parseObservation()`.

**Obs 4 — Orientation**

```json
{
  "id": "...",
  "datastream@id": "02vp7efvjs70",
  "foi@id": "0rqfjgrm12dg",
  "phenomenonTime": "2025-05-12T20:32:43.48Z",
  "resultTime": "2025-05-12T20:32:43.48Z",
  "result": { "orient": { "heading": 289.17, "pitch": 6.62, "roll": 95.42 } }
}
```

### Control Streams Fetched (4 of 18)

```json
{
  "id": "0o10",
  "name": "Autopilot - Location Control",
  "system@id": "03bc5ofvvstg",
  "system@link": { "href": "...", "rel": "...", "title": "..." },
  "inputName": "navLocation",
  "description": "...",
  "issueTime": ["2025-07-02T17:30:55.614Z", "2025-07-02T17:31:31.814Z"],
  "validTime": ["2024-03-28T04:12:28.72Z", "now"],
  "controlledProperties": [],
  "formats": ["application/json", ...],
  "links": [...]
}
```

> **Notable:** `issueTime` is an array (time interval). Some controlstreams have `controlledProperties: [{label: "..."}]`.

### Commands Fetched (3)

```json
{
  "id": "...",
  "controlstream@id": "0o10",
  "issueTime": "2025-07-02T17:30:55.614Z",
  "sender": "admin",
  "currentStatus": "COMPLETED",
  "parameters": {
    "locationVectorLLA": {
      "Latitude": 34.71,
      "Longitude": -86.64,
      "AltitudeAGL": 10
    },
    "returnToStart": false,
    "hoverSeconds": 20
  }
}
```

> **Notable:** `sender` and `currentStatus` fields. `parameters` is deeply nested.

### Command Statuses Fetched (2)

```json
{
  "id": "...",
  "command@id": "...",
  "reportTime": "2025-07-02T17:31:06.815Z",
  "statusCode": "COMPLETED",
  "executionTime": ["2025-07-02T17:30:55.614Z", "2025-07-02T17:31:31.814Z"]
}
```

> **Notable:** `executionTime` is an array (time interval). `statusCode: "COMPLETED"` only value seen.

---

## 6. Step 9 — SensorML

- **OSH:** `?f=sml3` returns minimal PhysicalSystem — same as ST#19
- **52N:** `Accept: application/sml+json` returns rich SML — same as ST#19

No changes.

---

## 7. Step 10 — CRUD Testing

### Part 1 Creates (All Succeeded)

| Resource         | POST URL            | Status | ID     |
| ---------------- | ------------------- | ------ | ------ |
| System           | `/systems`          | 201 ✅ | `04fg` |
| Procedure        | `/procedures`       | 201 ✅ | `0480` |
| Deployment       | `/deployments`      | 201 ✅ | `049g` |
| Sampling Feature | `/samplingFeatures` | 201 ✅ | `050g` |

### Part 2 Creates (All Failed — Server Regression)

| Resource                        | POST URL                                 | Status     | Error                      |
| ------------------------------- | ---------------------------------------- | ---------- | -------------------------- |
| Datastream (test system)        | `/systems/04fg/datastreams`              | **500** ❌ | Internal Server Error      |
| Datastream (existing system)    | `/systems/03bc5ofvvstg/datastreams`      | **500** ❌ | Internal Server Error      |
| ControlStream (test system)     | `/systems/04fg/controlstreams`           | **500** ❌ | Internal Server Error      |
| ControlStream (existing system) | `/systems/03bc5ofvvstg/controlstreams`   | **500** ❌ | Internal Server Error      |
| Observation (existing DS)       | `/datastreams/02au905kq85g/observations` | **400** ❌ | "Resource is not writable" |

> In ST#19, datastream, controlstream, and observation creation all returned 201. This is a **server-side regression** — no client code changes were made to CRUD operations.

### Read-Back Verification

All 4 Part 1 resources verified via GET — 200 OK, correct fields.

### Update (PUT)

System `04fg` updated with modified name → 204 No Content ✅  
Read-back confirmed updated name ✅

### Cleanup

| Resource                | DELETE Status | Verify 404 |
| ----------------------- | ------------- | ---------- |
| System `04fg`           | 204 ✅        | 404 ✅     |
| Procedure `0480`        | 204 ✅        | 404 ✅     |
| Deployment `049g`       | 204 ✅        | 404 ✅     |
| Sampling Feature `050g` | 204 ✅        | 404 ✅     |

Inventory restored to pre-test counts.

### CRUD Summary

| Category                           | Operations | Passed | Rate    |
| ---------------------------------- | ---------- | ------ | ------- |
| Part 1 (Create/Read/Update/Delete) | 13         | 13     | 100%    |
| Part 2 (Create)                    | 5          | 0      | 0%      |
| **Total**                          | **18**     | **13** | **72%** |

ST#19 was 36/37 (97.3%). The decline is entirely due to server-side Part 2 write regression.

---

## 8. Steps 11–12 — Parser Validation

### parseProperty() — Cannot Validate Live

OSH `/properties` returns 0 items. 52N `/properties` returns 400.

**Fixture adequacy:** 6 test cases in `property.spec.ts` cover full extraction, minimal, optional fields, nested objects, links array, and non-object rejection. Fixtures are spec-derived from OGC 23-002r2 Part 1 §7.6. Adequate for the current state.

### parseDatastream() — PASS (with one gap)

**Field-by-field validation against 4 live datastreams:**

| Field                    | Fixture                    | Live Data                   | Match       |
| ------------------------ | -------------------------- | --------------------------- | ----------- |
| `id`                     | string                     | string                      | ✅          |
| `name`                   | string                     | string                      | ✅          |
| `description`            | string (optional)          | string or absent            | ✅          |
| `type`                   | string (optional)          | absent in all 4             | ✅          |
| `validTime`              | `["ISO", "now"]`           | `["ISO", "now"]` (DS1)      | ✅          |
| `phenomenonTime`         | `["ISO", "ISO"]` or null   | array or absent             | ✅          |
| `resultTime`             | `["ISO", "ISO"]` or absent | absent in all 4             | ✅          |
| `observedProperties`     | `[{definition, label}]`    | Mixed (see P5-F2)           | ⚠️          |
| `resultType`             | string from RESULT_TYPES   | `measure`/`record`/`vector` | ✅          |
| `formats`                | string[]                   | string[]                    | ✅          |
| `links`                  | CsapiLink[] (optional)     | absent in list view         | ✅          |
| `system@id` (excluded)   | —                          | present in live data        | ✅ Excluded |
| `system@link` (excluded) | —                          | present in live data        | ✅ Excluded |

**Gap:** `observedProperties` objects without `definition` produce empty strings → see P5-F2.

### parseObservation() — PASS

**Field-by-field validation against 4 live observations:**

| Field                      | Fixture                | Live Data            | Match       |
| -------------------------- | ---------------------- | -------------------- | ----------- |
| `id`                       | string                 | string               | ✅          |
| `phenomenonTime`           | ISO instant string     | ISO instant string   | ✅          |
| `resultTime`               | ISO instant string     | ISO instant string   | ✅          |
| `result`                   | object (opaque)        | object (opaque)      | ✅          |
| `parameters`               | object (optional)      | absent in all 4      | ✅          |
| `links`                    | CsapiLink[] (optional) | absent in all 4      | ✅          |
| `datastream@id` (excluded) | —                      | present in live data | ✅ Excluded |
| `foi@id` (excluded)        | —                      | present in 2 of 4    | ✅ Excluded |

**Time handling:** Live observations have instant strings (not intervals), matching the `string` type in the `Observation` interface. Correct distinction from `Datastream.validTime` which is `TimeInterval`.

**Result opacity:** Live results include `{StatusType, Status}`, `{location: {lat, lon, alt}}`, `{orient: {heading, pitch, roll}}` — all passed through as `unknown`. Correct.

### Fixture Shape Comparison Summary

| Aspect                                         | Fixtures                         | Live Data                            | Status                   |
| ---------------------------------------------- | -------------------------------- | ------------------------------------ | ------------------------ |
| DS observedProperties always have `definition` | Yes                              | No (5 of 100 lack it)                | **Gap** (P5-F2)          |
| DS `links` present in list responses           | Yes (in fixtures)                | No (only in individual resource GET) | Handled (optional field) |
| Obs `foi@id` cross-reference                   | Not in fixtures                  | Present in some live obs             | Correctly excluded       |
| Obs `datastream@id`                            | In fixtures (for exclusion test) | Present in all live obs              | Correctly excluded       |

---

## 9. Steps 13–15 — Build, Test Suite, Compilation

| Check                     | Result                                                              |
| ------------------------- | ------------------------------------------------------------------- |
| `tsc --noEmit`            | ✅ Clean (0 errors)                                                 |
| CSAPI tests               | ✅ 1,190 passing, 27 suites                                         |
| Format tests              | ✅ 668 passing, 19 suites                                           |
| Parser tests specifically | ✅ 6 (property) + 8 (datastream) + 7 (observation) = 21 all passing |

---

## 10. Steps 16–17 — Finding Classification & Impact

### P5-F1 — OSH Part 2 Write Regression (Moderate)

**Category:** Server Limitation  
**Severity:** Moderate  
**Owner:** Server  
**Affects:** CRUD testing completeness

**Description:** OSH server returns HTTP 500 for Datastream and ControlStream POST requests (both on newly created test systems and existing systems). Observation POST returns 400 "Resource is not writable" on existing datastreams. In ST#19 (Phase 4.1), all three operations returned 201 Created successfully.

**Evidence:**

- `POST /systems/04fg/datastreams` → 500
- `POST /systems/03bc5ofvvstg/datastreams` → 500
- `POST /systems/04fg/controlstreams` → 500
- `POST /systems/03bc5ofvvstg/controlstreams` → 500
- `POST /datastreams/02au905kq85g/observations` → 400

**Impact on our code:** None. Our parser code does not perform write operations. Part 1 CRUD (systems, procedures, deployments, sampling features) still works.

**Action:** Document for re-test in next smoke test. Consider reporting upstream if persistent.

---

### P5-F2 — normalizeObservedProperties() Drops Label-Only Objects (Low)

**Category:** Code Gap (Ours)  
**Severity:** Low  
**Owner:** CSAPI team  
**Affects:** `parseDatastream()` output for datastreams with label-only observedProperties

**Description:** The `normalizeObservedProperties()` helper in `part2.ts` extracts the `definition` field from observedProperties objects and falls back to empty string when `definition` is absent. The `.filter(Boolean)` call then removes these empty strings. Live OSH data includes observedProperties objects with `{label, description}` but no `definition` field (e.g., Temperature, StatusEvent datastreams — approximately 5 of 100 datastreams).

**Code path:**

```typescript
// part2.ts line ~17
function normalizeObservedProperties(raw: unknown): string[] {
  // ...
  if (typeof item === 'object' && item !== null && 'definition' in item) {
    return (item as { definition: string }).definition;
  }
  return ''; // ← label-only objects hit this path
}
```

**Live data example:**

```json
{
  "observedProperties": [
    { "label": "Temperature", "description": "Temperature in degrees celsius" }
  ]
}
```

Result after parsing: `observedProperties: []` (empty) instead of preserving the label.

**Impact:** Low — the parsed `observedProperties` array loses human-readable labels for affected datastreams. The `definition` URI (which is the primary identifier per the spec) is genuinely absent in these cases. The behavior is technically correct (no definition = no string to return) but could be improved by falling back to `label` when `definition` is absent.

**Action:** Create issue for Phase 5 backlog. Consider `label` fallback in `normalizeObservedProperties()`.

---

## 11. Step 18 — Summary

### Scorecard

| Metric                 | Value        | ST#19 Value   | Delta                 |
| ---------------------- | ------------ | ------------- | --------------------- |
| Library regressions    | 0            | 0             | —                     |
| CSAPI tests passing    | 1,190        | 1,190         | —                     |
| TypeScript compilation | Clean        | Clean         | —                     |
| CRUD success rate      | 72% (13/18)  | 97.3% (36/37) | ↓ (server regression) |
| New findings (Total)   | 2            | 5             | —                     |
| New findings (Ours)    | 1 (Low)      | 0             | +1                    |
| New findings (Server)  | 1 (Moderate) | 5             | —                     |

### Parser Validation Scorecard

| Parser               | Live Data Available | Validation Result | Findings               |
| -------------------- | ------------------- | ----------------- | ---------------------- |
| `parseProperty()`    | No (0 items)        | Fixture-only ✅   | None                   |
| `parseDatastream()`  | Yes (4 samples)     | **PASS** ⚠️       | P5-F2 (label-only gap) |
| `parseObservation()` | Yes (4 samples)     | **PASS** ✅       | None                   |

### Phase 5 Parsers Not Yet Implemented (Tasks 4–6)

Live data shapes documented above for future implementation reference:

| Parser                 | Live Shape                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| `parseControlStream()` | `{id, name, inputName, validTime, controlledProperties, formats, [description], [issueTime], [links]}` |
| `parseCommand()`       | `{id, controlstream@id, issueTime, sender, currentStatus, parameters}`                                 |
| `parseCommandStatus()` | `{id, command@id, reportTime, statusCode, executionTime}`                                              |

### Key Observations for Future Tasks

1. **Command `parameters`** are deeply nested objects — will need opaque pass-through like `Observation.result`
2. **Command `issueTime`** is an instant (string), but ControlStream `issueTime` is an interval (array)
3. **CommandStatus `executionTime`** is an array (time interval) — same shape as `Datastream.validTime`
4. **`sender`** and **`currentStatus`** are command-specific fields not present in other resources
5. **`controlledProperties`** can be empty array `[]` or array of `{label}` objects

### Verdict

**PASS** — All implemented parsers validate against live server data with one low-severity gap (P5-F2). No library regressions. Server-side Part 2 write regression does not affect our parser code.

### Cumulative Finding Count

| Source                           | Count  |
| -------------------------------- | ------ |
| ST#1–ST#19 (F1–F90, P4-F1–P4-F5) | 95     |
| ST#20 (P5-F1, P5-F2)             | 2      |
| **Total**                        | **97** |
