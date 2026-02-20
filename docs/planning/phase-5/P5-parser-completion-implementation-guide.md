# Phase 5: Parser Completion — Implementation Guide

**Version:** 1.0  
**Date:** February 19, 2026  
**Status:** Draft — Pending Review  
**Scope:** 9 parser gaps only (from [Parsing Coverage Audit](../../research/phase-5/parsing-coverage-audit.md))

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Context](#2-architecture-context)
3. [Design Principles](#3-design-principles)
4. [Resource Parser Implementations](#4-resource-parser-implementations)
   - 4.1 [parseProperty()](#41-parseproperty)
   - 4.2 [parseDatastream()](#42-parsedatastream)
   - 4.3 [parseObservation()](#43-parseobservation)
   - 4.4 [parseControlStream()](#44-parsecontrolstream)
   - 4.5 [parseCommand()](#45-parsecommand)
   - 4.6 [parseCommandStatus()](#46-parsecommandstatus)
5. [Schema Response Parsers](#5-schema-response-parsers)
   - 5.1 [parseDatastreamSchemaResponse()](#51-parsedatastreamschemaresponse)
   - 5.2 [parseControlStreamSchemaResponse()](#52-parsecontrolstreamschemaresponse)
6. [Recursive Delegation Fix](#6-recursive-delegation-fix)
7. [Shared Utilities](#7-shared-utilities)
8. [Integration Points](#8-integration-points)
9. [Testing Strategy](#9-testing-strategy)
10. [Server Quirks Cross-Reference](#10-server-quirks-cross-reference)
11. [Risk Register](#11-risk-register)

---

## 1. Executive Summary

This guide covers the implementation of **9 parser gaps** identified by the Parsing Coverage Audit. The work adds:

- **6 resource parse functions** — `parseProperty()`, `parseDatastream()`, `parseObservation()`, `parseControlStream()`, `parseCommand()`, `parseCommandStatus()`
- **2 schema response parse functions** — `parseDatastreamSchemaResponse()`, `parseControlStreamSchemaResponse()`
- **1 recursive delegation fix** in 2 files — `physical-system.ts` and `aggregate-process.ts`

**Estimated volume:** ~300–500 lines of implementation, ~400–600 lines of tests.

**What this guide does NOT cover:** QueryBuilder methods (complete), URL building (complete), format detection (complete), GeoJSON handler extensions (complete), SWE Common parsers (complete), SensorML parsers (complete except Gap #9), collection envelope handling (complete), content negotiation, integration tests, or any work outside the 9 parser gaps.

**Relationship to main guide:** The [CSAPI Implementation Guide](../csapi-implementation-guide.md) (Version 7.0, 4,715 lines) covers the entire CSAPI contribution across all phases. This guide is a narrowly scoped supplement covering only the Phase 5 parser completion work.

---

## 2. Architecture Context

### Where the New Parsers Fit

```
src/ogc-api/csapi/formats/
├── geojson.ts          ← Part 1 GeoJSON parser (extractCSAPIFeature) — COMPLETE
├── response.ts         ← Collection envelope (parseCollectionResponse<T>) — COMPLETE
├── classification.ts   ← Resource type classification — COMPLETE
├── constants.ts        ← Content-Type constants — COMPLETE
├── part2.ts            ← NEW: Part 2 resource parsers (Gaps #2–#6)
├── property.ts         ← NEW: Property parser (Gap #1)
├── schema-response.ts  ← NEW: Schema response parsers (Gaps #7–#8)
├── sensorml/           ← SensorML parsers — COMPLETE (Gap #9 fix here)
│   ├── parser.ts       ← parseSensorML30() — the dispatch target for Gap #9
│   ├── physical-system.ts    ← parseComponentEntry() — FIX NEEDED (Gap #9)
│   ├── aggregate-process.ts  ← parseComponentEntry() — FIX NEEDED (Gap #9)
│   ├── simple-process.ts     ← COMPLETE
│   └── ...
└── swecommon/          ← SWE Common parsers — COMPLETE
    ├── parser.ts       ← parseSWEComponent() — used by parseObservation()
    └── ...
```

### Data Flow: How Items Get Parsed Today

```
API Response (JSON)
  → parseCollectionResponse<T>(body)     // extracts items[] from envelope
    → For Part 1 GeoJSON:
        items.map(extractCSAPIFeature)    // field-level parsing, type-safe output
    → For Part 2 / Property:
        items passed through as raw T     // ← THE GAP: no field-level parsing
```

### Data Flow: After Phase 5

```
API Response (JSON)
  → parseCollectionResponse<T>(body)     // extracts items[] from envelope
    → For Part 1 GeoJSON:
        items.map(extractCSAPIFeature)    // unchanged
    → For Part 2:
        items.map(parseDatastream)        // NEW: field-level parsing
        items.map(parseObservation)       // NEW
        items.map(parseControlStream)     // NEW
        items.map(parseCommand)           // NEW
        items.map(parseCommandStatus)     // NEW
    → For Property:
        items.map(parseProperty)          // NEW: flat JSON parsing
    → For schema endpoints:
        parseDatastreamSchemaResponse()   // NEW: wrapper parsing
        parseControlStreamSchemaResponse()// NEW
```

### Existing Interfaces (Already Defined)

All 6 resource type interfaces already exist in `src/ogc-api/csapi/model.ts`. No new resource interfaces are needed — only 2 new schema response interfaces.

| Interface | Location | Fields |
|-----------|----------|--------|
| `Property` | model.ts L401–417 | `id`, `label`, `description`, `uniqueId`, `baseProperty`, `objectType`, `statistic`, `links` |
| `Datastream` | model.ts L433–462 | `id`, `name`, `description`, `validTime`, `formats`, `outputName`, `observedProperties`, `phenomenonTime`, `resultTime`, `resultType`, `live`, `type`, `links` |
| `Observation` | model.ts L475–494 | `id`, `phenomenonTime`, `resultTime`, `parameters`, `result`, `links` |
| `ControlStream` | model.ts L506–523 | `id`, `name`, `description`, `validTime`, `formats`, `inputName`, `controlledProperties`, `issueTime`, `executionTime`, `live`, `async`, `links` |
| `Command` | model.ts L535–548 | `id`, `issueTime`, `executionTime`, `sender`, `currentStatus`, `parameters`, `links` |
| `CommandStatus` | model.ts L560–575 | `id`, `reportTime`, `statusCode`, `percentCompletion`, `executionTime`, `message`, `links` |

---

## 3. Design Principles

All new parsers must follow these principles, established by prior phases and documented in [Validation-Extraction Decoupling](../../implementation/design-notes-validation-extraction-decoupling.md):

### 3.1 Tolerant Extraction (Postel's Law)

> *"Be liberal in what you accept."*

Parsers extract what they can from the input without gating on validation. If a field is missing, use the interface default (undefined, null, empty array). If a field has an unexpected shape, fall back gracefully. Never throw on malformed data — only throw on structurally unusable input (e.g., input is not an object).

**Why:** Real servers deviate from the spec. OSH omits `validTime` on Deployments (F85). 52North returns `null` for required fields. Blocking extraction on validation made 100% of OSH SamplingFeatures inaccessible (F49). Validators were removed entirely in Phase 3.

### 3.2 Recognize → Extract Pattern

Follow the pattern established by `extractCSAPIFeature()`:

1. **Check structural minimum** — Is the input a non-null object? (Throw if not.)
2. **Extract fields** — Pull each field with type-appropriate fallbacks.
3. **Transform values** — Parse time fields, normalize enums, expand cross-references.
4. **Return typed result** — Use TypeScript `satisfies` for compile-time validation.

No validation gate between recognition and extraction.

### 3.3 Consistent Patterns

New parsers must be consistent with existing parsers in:
- **Error handling** — Same throw conditions as `extractCSAPIFeature()` and `parseSensorML30()`
- **Field transformation** — Same `parseValidTime()` for all time intervals
- **JSDoc** — Same documentation density as SensorML sub-parsers (Phase 3.5 pattern)
- **Return typing** — `satisfies` operator for interface conformance
- **Conditional spread** — `...(field !== undefined ? { field } : {})` for optional fields

### 3.4 No Upstream Precedent Required

The upstream `ogc-client` has no Part 2 parsers and no Property parser. There is no existing pattern to follow beyond what we have already established in Phases 1–4. The new parsers are net-new code, not extensions of upstream patterns.

---

## 4. Resource Parser Implementations

### 4.1 `parseProperty()`

**Gap:** #1 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/property.ts` (new file)  
**Input:** Raw JSON object from `/properties` endpoint `items` array  
**Output:** `Property` interface

#### Input Shape (OGC 23-001, `DerivedProperty` schema)

Property is the **only Part 1 resource that is NOT a GeoJSON Feature**. It arrives as a flat JSON object based on the SWE Common `DerivedProperty` schema, not wrapped in a GeoJSON `Feature` envelope.

```json
{
  "uniqueId": "urn:x-]ogc:def:property:noaa::AirTemperature",
  "label": "Air Temperature",
  "description": "Temperature of the ambient air",
  "baseProperty": "http://qudt.org/vocab/quantitykind/Temperature",
  "objectType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
  "statistic": "http://www.opengis.net/def/property/OGC/0/Mean",
  "links": [
    { "rel": "self", "href": "/properties/air-temp", "type": "application/json" }
  ]
}
```

> **Note:** No live server has ever returned Property resources. Both OSH and 52North return 0 items for `/properties` (confirmed ST#6). The parser will be built from the OGC spec definition alone. See [validTime coverage analysis](../../research/phase-5/validtime-coverage-analysis.md).

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `id` | `string \| undefined` | `string \| undefined` | Direct pass-through (server-assigned, may be absent) |
| `label` | `string` | `string` | Direct extraction; fall back to empty string |
| `description` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `uniqueId` | `string` | `string` | Direct extraction; fall back to empty string |
| `baseProperty` | `string` | `string` | Direct extraction; fall back to empty string |
| `objectType` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `statistic` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `links` | `array \| undefined` | `ResourceLink[] \| undefined` | Extract if array; omit if absent |

**No `validTime`.** Property has no `validTime` per OGC 23-001 (`DerivedProperty` → `AbstractSweIdentifiable` → `AbstractSWE`). See [validTime coverage analysis](../../research/phase-5/validtime-coverage-analysis.md).

#### Implementation Sketch

```typescript
export function parseProperty(json: unknown): Property {
  if (typeof json !== 'object' || json === null) {
    throw new Error('parseProperty: input must be a non-null object');
  }

  const obj = json as Record<string, unknown>;

  return {
    ...(typeof obj.id === 'string' ? { id: obj.id } : {}),
    label: typeof obj.label === 'string' ? obj.label : '',
    ...(typeof obj.description === 'string' ? { description: obj.description } : {}),
    uniqueId: typeof obj.uniqueId === 'string' ? obj.uniqueId : '',
    baseProperty: typeof obj.baseProperty === 'string' ? obj.baseProperty : '',
    ...(typeof obj.objectType === 'string' ? { objectType: obj.objectType } : {}),
    ...(typeof obj.statistic === 'string' ? { statistic: obj.statistic } : {}),
    ...(Array.isArray(obj.links) ? { links: obj.links as ResourceLink[] } : {}),
  } satisfies Property;
}
```

#### Test Cases

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Full Property | All fields present | All fields extracted |
| 2 | Minimal Property | Only required fields (`uniqueId`, `label`, `baseProperty`) | Optional fields omitted |
| 3 | Missing label | `label` absent | Falls back to empty string |
| 4 | Non-object input | `null`, `42`, `"string"` | Throws Error |
| 5 | Empty object | `{}` | Returns defaults (empty strings for required fields) |
| 6 | Extra fields ignored | Fields not in interface | Extra fields not in output |

---

### 4.2 `parseDatastream()`

**Gap:** #2 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts` (new file, shared with Gaps #3–#6)  
**Input:** Raw JSON object from `/datastreams` endpoint `items` array  
**Output:** `Datastream` interface

#### Input Shape (OGC 23-002, `dataStream` schema)

```json
{
  "id": "0ocb",
  "name": "FCU Simulated Weather Station - Weather",
  "system@id": "0o0o",
  "system@link": {
    "href": "http://45.55.99.236:8080/sensorhub/api/systems/0o0o?f=json",
    "uid": "urn:osh:sensor:simweather:001",
    "type": "application/geo+json"
  },
  "outputName": "weather",
  "validTime": ["2026-01-26T18:32:01.56Z", "now"],
  "observedProperties": [
    { "definition": "http://mmisw.org/ont/cf/parameter/air_temperature", "label": "Air Temperature" }
  ],
  "formats": [
    "application/om+json",
    "application/swe+json",
    "application/swe+csv",
    "application/swe+xml",
    "application/swe+binary"
  ],
  "phenomenonTime": ["2026-01-26T18:32:01.56Z", "2026-02-19T14:22:03.12Z"],
  "resultTime": ["2026-01-26T18:32:01.56Z", "2026-02-19T14:22:03.12Z"],
  "resultType": "record",
  "live": true,
  "links": [
    { "rel": "self", "href": "/datastreams/0ocb", "type": "application/json" }
  ]
}
```

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `id` | `string` | `string` | Direct extraction |
| `name` | `string` | `string` | Direct extraction; fall back to empty string |
| `description` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `validTime` | `[string, string] \| null` | `TimeInterval \| undefined` | `parseValidTime()` — handles `"now"` sentinel, null, array, object formats |
| `formats` | `string[]` | `string[]` | Extract if array; fall back to empty array |
| `outputName` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `observedProperties` | `array \| null` | `string[]` | Extract `definition` URIs from objects; fall back to empty array |
| `phenomenonTime` | `[string, string] \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| `resultTime` | `[string, string] \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| `resultType` | `string \| null` | `enum \| null` | Validate against known values; null if unknown |
| `live` | `boolean \| null` | `boolean \| null` | Direct extraction |
| `type` | `string \| undefined` | `'status' \| 'observation' \| undefined` | Conditional extraction |
| `links` | `array` | `ResourceLink[]` | Extract if array; fall back to empty array |

**Cross-references (NOT extracted into interface):**
- `system@id` — present in raw JSON but not in `Datastream` interface; ignored by parser
- `system@link` — link object; same — not in interface

**`observedProperties` normalization:** The server returns an array of objects `{ definition, label, description }`. The `Datastream` interface declares `observedProperties: string[]`. The parser extracts the `definition` URI from each object to produce the string array. If the server returns a plain string array (spec allows both), pass through directly.

#### Time Fields

Datastream has **three** time-interval fields. All use the same `[start, end]` array format ("timePeriod" in the OpenAPI spec). All are parsed with the same `parseValidTime()` function:

| Field | Nullable? | Semantics |
|-------|-----------|-----------|
| `validTime` | Optional (may be absent) | When the datastream is/was valid |
| `phenomenonTime` | `null` allowed (readOnly) | Time range of all observations |
| `resultTime` | `null` allowed (readOnly) | Time range of all result timestamps |

See [validTime coverage analysis](../../research/phase-5/validtime-coverage-analysis.md) for the full `validTime` landscape.

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | Full Datastream | All fields present, verify each transformation |
| 2 | Minimal Datastream | Required fields only (`id`, `name`, `formats`) |
| 3 | `validTime` with `"now"` | `["2026-01-26T18:32:01.56Z", "now"]` → `{ start: Date, end: undefined }` |
| 4 | `observedProperties` as objects | Array of `{ definition, label }` → array of definition strings |
| 5 | `observedProperties` as strings | Direct pass-through |
| 6 | `phenomenonTime` null | Returns null, not undefined |
| 7 | Non-object input | Throws Error |
| 8 | Cross-reference fields ignored | `system@id` not in output |

---

### 4.3 `parseObservation()`

**Gap:** #3 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Input:** Raw JSON object from `/observations` endpoint `items` array  
**Output:** `Observation` interface

#### Input Shape (OGC 23-002, `observation` schema)

```json
{
  "id": "0o1abc123",
  "datastream@id": "0ocb",
  "phenomenonTime": "2026-02-19T14:22:03.12Z",
  "resultTime": "2026-02-19T14:22:03.12Z",
  "parameters": { "quality": "good" },
  "result": {
    "temperature": 22.5,
    "humidity": 65.3,
    "pressure": 1013.25
  }
}
```

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `id` | `string` | `string` | Direct extraction |
| `phenomenonTime` | `string \| undefined` | `string \| undefined` | Direct pass-through (ISO 8601 instant, NOT a time interval) |
| `resultTime` | `string` | `string` | Direct extraction |
| `parameters` | `object \| undefined` | `Record<string, unknown> \| undefined` | Conditional extraction |
| `result` | `unknown \| undefined` | `unknown \| undefined` | Pass-through (schema-dependent shape) |
| `links` | `array \| undefined` | `ResourceLink[] \| undefined` | Conditional extraction |

**Important distinction:** Observation time fields are **instants** (single ISO 8601 strings), NOT time intervals (arrays). This is different from Datastream/ControlStream time fields. The `Observation` interface stores them as strings, not `TimeInterval`.

**Cross-references (NOT extracted into interface):**
- `datastream@id` — present in raw JSON, not in current `Observation` interface; ignored by parser
- `samplingFeature@id` — may be present; not in interface; ignored

**`result` field:** The result's structure depends on the datastream's observation schema. It can be a simple scalar, a record (object), a vector, or a coverage. The parser passes it through as `unknown` because the shape varies by datastream. Consumers who need typed results should use `validateAgainstSchema()` (SWE Common parser) with the datastream's schema.

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | Full Observation | All fields present |
| 2 | Minimal Observation | Only `id`, `resultTime` (required per spec) |
| 3 | Complex result | Nested record as `result` — pass-through verified |
| 4 | Missing phenomenonTime | Optional field absent |
| 5 | Non-object input | Throws Error |
| 6 | Cross-reference fields ignored | `datastream@id` not in output |

---

### 4.4 `parseControlStream()`

**Gap:** #4 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Input:** Raw JSON object from `/controlstreams` endpoint `items` array  
**Output:** `ControlStream` interface

#### Input Shape (OGC 23-002, `controlStream` schema)

Real server example (OSH, ST#9 F30):

```json
{
  "id": "0o10",
  "name": "FCU Field Drone CubePilot - Location Control",
  "system@id": "0o30",
  "system@link": {
    "href": "http://45.55.99.236:8080/sensorhub/api/systems/0o30?f=json",
    "uid": "urn:osh:driver:mavsdk:cube",
    "type": "application/geo+json"
  },
  "inputName": "mavControl",
  "validTime": ["2026-01-14T04:49:19.134Z", "now"],
  "issueTime": ["2026-01-14T12:42:21.910351Z", "2026-01-14T13:11:31.196096Z"],
  "executionTime": ["2026-01-14T12:42:21.928726Z", "2026-01-14T13:11:31.196096Z"],
  "controlledProperties": [],
  "formats": [
    "application/json",
    "application/swe+json",
    "application/swe+csv",
    "application/swe+xml",
    "application/swe+binary"
  ],
  "live": true,
  "async": true
}
```

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `id` | `string` | `string` | Direct extraction |
| `name` | `string` | `string` | Direct extraction; fall back to empty string |
| `description` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `validTime` | `[string, string] \| null` | `TimeInterval \| undefined` | `parseValidTime()` |
| `formats` | `string[]` | `string[]` | Extract if array; fall back to empty array |
| `inputName` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `controlledProperties` | `array \| null` | `string[]` | Extract `definition` URIs from objects or pass strings; fall back to empty array |
| `issueTime` | `[string, string] \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| `executionTime` | `[string, string] \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| `live` | `boolean \| null` | `boolean \| null` | Direct extraction |
| `async` | `boolean` | `boolean` | Direct extraction; fall back to false |
| `links` | `array` | `ResourceLink[]` | Extract if array; fall back to empty array |

**Cross-references (NOT extracted):** `system@id`, `system@link` — not in `ControlStream` interface.

#### Structural Parallel to Datastream

ControlStream mirrors Datastream's shape closely. Both share the `baseStream` schema in the OpenAPI spec. The key differences:

| Datastream | ControlStream |
|-----------|---------------|
| `outputName` | `inputName` |
| `observedProperties` | `controlledProperties` |
| `phenomenonTime` / `resultTime` | `issueTime` / `executionTime` |
| `resultType` | — (absent) |
| — | `async` |

This structural parallel suggests extracting shared parsing logic (see [§7 Shared Utilities](#7-shared-utilities)).

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | Full ControlStream | All fields from real OSH response (F30) |
| 2 | Minimal ControlStream | Only `id`, `name`, `formats`, `async` |
| 3 | Empty `controlledProperties` | Returns empty array |
| 4 | `validTime` with `"now"` | Parses correctly |
| 5 | `executionTime` null | Returns null |
| 6 | Non-object input | Throws Error |

---

### 4.5 `parseCommand()`

**Gap:** #5 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Input:** Raw JSON object from `/commands` endpoint `items` array  
**Output:** `Command` interface

#### Input Shape (OGC 23-002, `command` schema)

Real server example (OSH, ST#10 F31):

```json
{
  "id": "0o1qr7kupc33cgmqj0",
  "controlstream@id": "0o10",
  "issueTime": "2026-01-14T12:42:21.910351Z",
  "sender": "urn:osh:process:datasink:commandstream#drone",
  "currentStatus": "COMPLETED",
  "parameters": {
    "locationVectorLLA": {
      "Latitude": 24.180652098637896,
      "Longitude": 120.64924139592034,
      "AltitudeAGL": 105.0
    },
    "returnToStart": false,
    "hoverSeconds": 0
  }
}
```

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `id` | `string` | `string` | Direct extraction |
| `issueTime` | `string` | `string` | Direct pass-through (ISO 8601 instant) |
| `executionTime` | `[string, string] \| undefined` | `TimeInterval \| undefined` | `parseValidTime()` — only present when command has been executed |
| `sender` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `currentStatus` | `string \| undefined` | `CommandStatusCode \| undefined` | Validate against `CommandStatusCodes` enum; fall back to undefined if invalid |
| `parameters` | `object` | `Record<string, unknown>` | Direct extraction; fall back to empty object |
| `links` | `array \| undefined` | `ResourceLink[] \| undefined` | Conditional extraction |

**Cross-references (NOT extracted):** `controlstream@id` — present in raw JSON, not in `Command` interface.

**`currentStatus` normalization:** The server returns a string. The `Command` interface types this as `CommandStatusCode`, which is a union of 9 string literals (`'PENDING' | 'ACCEPTED' | ... | 'COMPLETED'`). The parser should validate the string against `CommandStatusCodes` (the `as const` array defined in model.ts L53–66). If the value is not a recognized status code, fall back to undefined rather than throwing.

**`issueTime` vs `executionTime` asymmetry:** `issueTime` is an ISO 8601 instant (single string). `executionTime` is a time period (array of two strings). Different types require different parsing — `issueTime` is passed through as-is, `executionTime` is parsed with `parseValidTime()`.

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | Full Command | All fields from real OSH response (F31) |
| 2 | Minimal Command | Only `id`, `issueTime`, `parameters` (required per spec) |
| 3 | `currentStatus` valid | `"COMPLETED"` → `'COMPLETED'` |
| 4 | `currentStatus` invalid | Unknown string → `undefined` |
| 5 | `executionTime` present | Parsed to `TimeInterval` |
| 6 | `executionTime` absent | Not in output |
| 7 | Complex parameters | Nested object pass-through |
| 8 | Non-object input | Throws Error |

---

### 4.6 `parseCommandStatus()`

**Gap:** #6 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Input:** Raw JSON object from `/commandStatuses` endpoint `items` array  
**Output:** `CommandStatus` interface

#### Input Shape (OGC 23-002, `commandStatus` schema)

Real server example (OSH, ST#10 F38):

```json
{
  "id": "0o507bcujr5gcdi2racar7kupc33emq3o0",
  "command@id": "0o1qr7kupc33cgmqj0",
  "reportTime": "2026-01-14T12:42:21.928728Z",
  "statusCode": "COMPLETED",
  "executionTime": ["2026-01-14T12:42:21.928726Z", "2026-01-14T12:42:21.928726Z"]
}
```

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `id` | `string` | `string` | Direct extraction |
| `reportTime` | `string` | `string` | Direct pass-through (ISO 8601 instant) |
| `statusCode` | `string` | `CommandStatusCode` | Validate against `CommandStatusCodes` enum; fall back to `'PENDING'` if invalid (must always be present) |
| `percentCompletion` | `number \| undefined` | `number \| undefined` | Conditional extraction; range 0–100 |
| `executionTime` | `[string, string] \| undefined` | `TimeInterval \| undefined` | `parseValidTime()` |
| `message` | `string \| undefined` | `string \| undefined` | Conditional extraction |
| `links` | `array \| undefined` | `ResourceLink[] \| undefined` | Conditional extraction |

**Cross-references (NOT extracted):** `command@id` — present in raw JSON, not in `CommandStatus` interface.

**`statusCode` normalization:** Unlike `currentStatus` on Command (optional), `statusCode` on CommandStatus is **required** per the spec. If the value is missing or unrecognized, fall back to `'PENDING'` (the initial state) rather than undefined, because the interface type is non-optional `CommandStatusCode`.

**`executionTime` semantics vary by `statusCode`:**
- `SCHEDULED` → planned execution time
- `EXECUTING` → start time of execution
- `COMPLETED` / `FAILED` → actual execution time range

The parser does not interpret these semantics — it just parses the time interval.

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | Full CommandStatus | All fields from real OSH response (F38) |
| 2 | Minimal CommandStatus | Only `id`, `reportTime`, `statusCode` (required) |
| 3 | `statusCode` valid | `"COMPLETED"` → `'COMPLETED'` |
| 4 | `statusCode` invalid | Unknown string → `'PENDING'` fallback |
| 5 | `percentCompletion` present | Extracted as number |
| 6 | `executionTime` present | Parsed to `TimeInterval` |
| 7 | Non-object input | Throws Error |

---

## 5. Schema Response Parsers

### Context

Schema endpoints (`/datastreams/{id}/schema`, `/controlstreams/{id}/schema`) return a **wrapper object** containing a format identifier and a schema definition. The existing `parseSWEComponent()` function expects raw SWE Common components with `type` at the top level — it correctly rejects the wrapper.

Demo app finding Issue #17 (F-14) identified this gap and recommended deferring a full `parseSchemaResponse()` utility. The Phase 5 scope adds these parsers as new code without modifying existing library exports.

### 5.1 `parseDatastreamSchemaResponse()`

**Gap:** #7 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/schema-response.ts` (new file)  
**Input:** Raw JSON response from `/datastreams/{id}/schema`  
**Output:** `DatastreamSchemaResponse` (new interface)

#### Input Shape (OGC 23-002 schema endpoint)

The response shape varies by format. For `application/json`:

```json
{
  "obsFormat": "application/json",
  "resultSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "temperature",
        "type": "Quantity",
        "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
        "label": "Air Temperature",
        "uom": { "code": "Cel" }
      }
    ]
  }
}
```

For `application/swe+json` (SWE Common format):

```json
{
  "obsFormat": "application/swe+json",
  "recordSchema": {
    "type": "DataRecord",
    "fields": [ ... ]
  },
  "encoding": { "type": "JSONEncoding" }
}
```

#### New Interface

```typescript
export interface DatastreamSchemaResponse {
  obsFormat: string;
  resultSchema?: SWEComponent;
  recordSchema?: SWEComponent;
  encoding?: DataEncoding;
}
```

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `obsFormat` | `string` | `string` | Direct extraction; fall back to empty string |
| `resultSchema` | `object \| undefined` | `SWEComponent \| undefined` | Delegate to `parseSWEComponent()` if present |
| `recordSchema` | `object \| undefined` | `SWEComponent \| undefined` | Delegate to `parseSWEComponent()` if present |
| `encoding` | `object \| undefined` | `DataEncoding \| undefined` | Delegate to `parseEncoding()` if present |

**Schema delegation:** The `resultSchema` or `recordSchema` field contains a SWE Common component (typically `DataRecord`). The parser delegates to the existing `parseSWEComponent()` for full recursive parsing of the schema tree. This is the key value — it connects the schema response to the already-complete SWE Common parser layer.

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | JSON format response | `obsFormat` + `resultSchema` with DataRecord |
| 2 | SWE Common format response | `obsFormat` + `recordSchema` + `encoding` |
| 3 | Missing schema fields | Only `obsFormat` present |
| 4 | Nested DataRecord | Schema with multiple fields → full SWE parse tree |
| 5 | Non-object input | Throws Error |

---

### 5.2 `parseControlStreamSchemaResponse()`

**Gap:** #8 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/schema-response.ts` (same file as §5.1)  
**Input:** Raw JSON response from `/controlstreams/{id}/schema`  
**Output:** `ControlStreamSchemaResponse` (new interface)

#### Input Shape (OGC 23-002 schema endpoint)

```json
{
  "commandFormat": "application/json",
  "parametersSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "pan",
        "type": "Quantity",
        "definition": "http://sensorml.com/ont/swe/property/PanAngle",
        "label": "Pan Angle",
        "uom": { "code": "deg" }
      }
    ]
  }
}
```

#### New Interface

```typescript
export interface ControlStreamSchemaResponse {
  commandFormat: string;
  parametersSchema?: SWEComponent;
  encoding?: DataEncoding;
}
```

#### Field Transformations

| Field | Source Type | Target Type | Transformation |
|-------|------------|-------------|----------------|
| `commandFormat` | `string` | `string` | Direct extraction; fall back to empty string |
| `parametersSchema` | `object \| undefined` | `SWEComponent \| undefined` | Delegate to `parseSWEComponent()` if present |
| `encoding` | `object \| undefined` | `DataEncoding \| undefined` | Delegate to `parseEncoding()` if present |

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | JSON format response | `commandFormat` + `parametersSchema` with DataRecord |
| 2 | Missing parametersSchema | Only `commandFormat` present |
| 3 | Nested DataRecord | Full SWE parse tree verified |
| 4 | Non-object input | Throws Error |

---

## 6. Recursive Delegation Fix

**Gap:** #9 from Parsing Coverage Audit (counted as 1 gap, affects 2 files)  
**Issue:** #22 (referenced in code comments)

### Current Behavior

Both `parseComponentEntry()` functions (one in `physical-system.ts`, one in `aggregate-process.ts`) only recursively parse inline components matching their own type:

- `physical-system.ts`: Only parses `type === 'PhysicalSystem'`
- `aggregate-process.ts`: Only parses `type === 'AggregateProcess'`

All other inline component types (`SimpleProcess`, `PhysicalComponent`, and the cross-type cases) are returned as raw unparsed JSON via `return value as unknown as ComponentEntry`.

### Why This Matters

Real-world SensorML systems contain mixed process types. A PhysicalSystem weather station may contain:
- `SimpleProcess` temperature sensors
- `PhysicalComponent` wind vanes
- Nested `PhysicalSystem` sub-platforms

Only the last case is currently parsed. The first two pass through as raw JSON, breaking the type contract.

### Fix: Delegate to `parseSensorML30()`

`parseSensorML30()` in `parser.ts` already dispatches all 4 process types. The fix is to replace the type-specific recursive call with delegation to the main dispatcher.

#### physical-system.ts — Before

```typescript
// Recursive PhysicalSystem parsing
if (value.type === 'PhysicalSystem') {
  const parsed = parsePhysicalSystem(value);
  return { ...parsed, name: value.name as string } as ComponentEntry;
}

// Other inline process types and external links are passed through.
return value as unknown as ComponentEntry;
```

#### physical-system.ts — After

```typescript
// Delegate all inline process types to the main SensorML dispatcher
const knownTypes = ['PhysicalSystem', 'PhysicalComponent', 'SimpleProcess', 'AggregateProcess'];
if (typeof value.type === 'string' && knownTypes.includes(value.type)) {
  const parsed = parseSensorML30(value);
  return { ...parsed, name: value.name as string } as ComponentEntry;
}

// External links and unrecognized types are passed through
return value as unknown as ComponentEntry;
```

The same transformation applies to `aggregate-process.ts`.

#### Import Change

Both files will need to import `parseSensorML30` from `./parser`. This introduces a potential **circular dependency** because `parser.ts` imports from both `physical-system.ts` and `aggregate-process.ts`. The fix must verify that the circular reference resolves correctly at runtime. In the existing codebase, `parser.ts` already has these imports:

```typescript
import { parsePhysicalSystem, parsePhysicalComponent } from './physical-system';
import { parseAggregateProcess } from './aggregate-process';
import { parseSimpleProcess } from './simple-process';
```

Adding the reverse import (`import { parseSensorML30 } from './parser'` in both files) creates a cycle: `parser.ts → physical-system.ts → parser.ts`. TypeScript and Node.js ESM handle circular imports via live bindings — the function reference is resolved at call time, not import time. As long as `parseSensorML30` is not called during module initialization (it isn't — it's only called inside `parseComponentEntry()` which runs later), the cycle is safe.

**Verification:** Compile and run the existing test suite after the change. If any circular dependency issues arise, the alternative is to pass `parseSensorML30` as a callback parameter — but this should not be necessary.

#### Test Cases

| # | Test | Focus |
|---|------|-------|
| 1 | PhysicalSystem with SimpleProcess child | Child is parsed, not raw JSON |
| 2 | PhysicalSystem with PhysicalComponent child | Child is parsed |
| 3 | PhysicalSystem with AggregateProcess child | Child is parsed |
| 4 | PhysicalSystem with PhysicalSystem child | Still works (regression) |
| 5 | AggregateProcess with SimpleProcess child | Child is parsed |
| 6 | AggregateProcess with PhysicalSystem child | Child is parsed |
| 7 | AggregateProcess with PhysicalComponent child | Child is parsed |
| 8 | AggregateProcess with AggregateProcess child | Still works (regression) |
| 9 | External link component | Still passed through (not a process type) |
| 10 | Unknown type string | Passed through (tolerant extraction) |

---

## 7. Shared Utilities

### 7.1 `parseValidTime()` (Existing)

**Location:** `src/ogc-api/csapi/formats/geojson.ts` L274–324  
**Status:** Already implemented and tested. Handles null, array `[start, end]`, object `{ start, end }`, `"now"` sentinel, and invalid input.

All new parsers that handle time intervals (`parseDatastream`, `parseControlStream`, `parseCommand`, `parseCommandStatus`) should import and reuse this function. No duplication.

**Consideration:** `parseValidTime()` currently lives in `geojson.ts`. Since Part 2 parsers are not GeoJSON-related, this function may benefit from being moved to a shared module (e.g., `src/ogc-api/csapi/formats/time-utils.ts`) or re-exported. However, moving it would change the file structure and is not strictly necessary — importing from `geojson.ts` works fine. **Recommendation:** Import from `geojson.ts` now; refactor to shared module later if the pattern proliferates.

### 7.2 `parseTimeInstant()` (New — Optional)

Several Part 2 fields are single ISO 8601 instants (not intervals): `issueTime` on Command, `resultTime` and `phenomenonTime` on Observation, `reportTime` on CommandStatus. These are currently typed as `string` in the interfaces.

A `parseTimeInstant()` helper could validate the string format and return a normalized ISO 8601 string. However, since the interfaces type these as `string` (not `Date`), the parser should just pass them through. No new utility needed unless the interfaces change.

### 7.3 `normalizeStatusCode()` (New — Recommended)

Both `parseCommand()` and `parseCommandStatus()` need to validate status code strings against the `CommandStatusCodes` enum. A small shared helper avoids duplication:

```typescript
function normalizeStatusCode(value: unknown): CommandStatusCode | undefined {
  if (typeof value === 'string' && CommandStatusCodes.includes(value as CommandStatusCode)) {
    return value as CommandStatusCode;
  }
  return undefined;
}
```

### 7.4 `extractLinks()` (New — Recommended)

Every parser extracts a `links` field from the input. A small helper avoids repeating the pattern:

```typescript
function extractLinks(obj: Record<string, unknown>): ResourceLink[] {
  return Array.isArray(obj.links) ? (obj.links as ResourceLink[]) : [];
}
```

---

## 8. Integration Points

### 8.1 `parseCollectionResponse()` Pipeline

`parseCollectionResponse<T>()` in `response.ts` currently extracts items from the collection envelope but does **not** call any item-level parser. The integration question is: **where does item-level parsing get triggered?**

Two options:

**Option A: Parse inside `parseCollectionResponse()`**  
Add a parser callback parameter: `parseCollectionResponse<T>(body, itemParser?: (item: unknown) => T)`. If provided, map each item through the parser.

**Option B: Parse at the call site (QueryBuilder methods)**  
`parseCollectionResponse<T>()` remains unchanged. The QueryBuilder methods (e.g., `getDataStreams()`) call `parseCollectionResponse()` to get raw items, then map each item through the appropriate parser.

**Recommendation:** Option B. It keeps `parseCollectionResponse()` generic and avoids coupling the envelope parser to specific resource parsers. The QueryBuilder methods already know which resource type they're requesting and can import the right parser. This is consistent with how `extractCSAPIFeature()` is called — at the consumer level, not inside the envelope parser.

### 8.2 Schema Response Endpoints

Schema endpoints (`/datastreams/{id}/schema`, `/controlstreams/{id}/schema`) return a **single object**, not a collection. They do not go through `parseCollectionResponse()`. The schema response parsers are called directly by the QueryBuilder methods `getDataStreamSchema()` and `getControlStreamSchema()`.

### 8.3 Recursive Delegation

The fix in `parseComponentEntry()` integrates via the existing SensorML parser pipeline. No new integration points are needed — the fix is internal to the SensorML module.

---

## 9. Testing Strategy

### 9.1 Test File Organization

Following the pattern established by existing parser tests:

| Parser | Test File |
|--------|-----------|
| `parseProperty()` | `src/ogc-api/csapi/formats/property.spec.ts` |
| `parseDatastream()` | `src/ogc-api/csapi/formats/part2.spec.ts` |
| `parseObservation()` | `src/ogc-api/csapi/formats/part2.spec.ts` |
| `parseControlStream()` | `src/ogc-api/csapi/formats/part2.spec.ts` |
| `parseCommand()` | `src/ogc-api/csapi/formats/part2.spec.ts` |
| `parseCommandStatus()` | `src/ogc-api/csapi/formats/part2.spec.ts` |
| `parseDatastreamSchemaResponse()` | `src/ogc-api/csapi/formats/schema-response.spec.ts` |
| `parseControlStreamSchemaResponse()` | `src/ogc-api/csapi/formats/schema-response.spec.ts` |
| Recursive delegation fix | Tests in existing `physical-system.spec.ts` and `aggregate-process.spec.ts` |

### 9.2 Test Patterns

Following [Parser Testing vs Spec Validation](../../research/testing/review/notes-parser-testing-vs-spec-validation.md):

- **Parser tests verify client extraction, not server compliance.** The input is whatever the server sends; the test verifies we extract it correctly.
- **Fixture-based:** Each test uses a JSON fixture representing a real or spec-derived response.
- **Match existing patterns:** Use the same `describe` / `it` structure as SensorML parser tests (Phase 3.5 pattern).
- **No mocking:** Parser functions are pure transformations — no network, no state, no mocking needed.

### 9.3 Fixture Sources

| Resource | Real Server Data? | Fixture Source |
|----------|-------------------|----------------|
| Property | **No** — 0 items from both servers | Constructed from OGC 23-001 `DerivedProperty` schema |
| Datastream | Yes — OSH returns full datastreams | ST#7 response examples |
| Observation | Yes — OSH returns observations | ST#8 response examples |
| ControlStream | Yes — OSH returns control streams | ST#9 F30 response example |
| Command | Yes — OSH returns commands | ST#10 F31 response example |
| CommandStatus | Yes — OSH returns command statuses | ST#10 F38 response example |
| Schema Response | Yes — OSH returns schema wrappers | ST#7 schema observations |

### 9.4 Coverage Target

Per the [Contribution Goal](P5-contribution-goal-and-definition.md): **>80% code coverage** on new parser files.

Given that parser functions are pure transformations with well-defined inputs, achieving >90% coverage is realistic and expected. The primary uncovered paths would be defensive branches for extreme edge cases (e.g., `typeof json !== 'object'`).

---

## 10. Server Quirks Cross-Reference

Parser-relevant findings from the [Server Quirks Reference](../../implementation/server-quirks-reference.md):

| Finding | Summary | Parser Impact |
|---------|---------|---------------|
| F34 | OSH has no top-level `/commands` endpoint — only nested under `/controlstreams/{id}/commands` | No parser impact (URL-level concern), but means Command fixtures come from nested endpoints only |
| F38 | CommandStatus data shape: `command@id`, `reportTime`, `statusCode`, `executionTime` array | Directly informs `parseCommandStatus()` field list |
| F39 | Commands use `items` envelope with link-based pagination | Confirms `parseCollectionResponse()` handles the envelope; parsers only need item-level logic |
| F45 | Response envelope varies by server AND format — OSH uses `items` for default JSON, `features` for `?f=geojson` | Envelope handled by `parseCollectionResponse()`; Part 2 resources always use `items` |
| F49 | OSH SamplingFeatures lack `sampledFeature@link` | Validates tolerant extraction philosophy — never gate on missing fields |
| F85 | Deployment `validTime` absent from OSH, null from 52North | Validates `parseValidTime()` tolerant design; same function reused by new parsers |

---

## 11. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | **No Property test data** — both servers return 0 items | Certain | Medium | Build fixtures from OGC spec. Document as known limitation. Do an integration test once a server provides Property data. |
| 2 | **Circular import** from Gap #9 fix | Low | High | TypeScript ESM handles circular imports via live bindings. Verify with test suite. Fallback: pass dispatcher as callback. |
| 3 | **`observedProperties` shape variance** — objects vs strings | Medium | Low | Handle both shapes in `parseDatastream()`. Test both. |
| 4 | **Cross-reference fields evolve** — `@id` / `@link` fields may be added to interfaces later | Low | Low | Parsers currently ignore `@id` / `@link` fields. Adding them later is additive, not breaking. |
| 5 | **52North Part 2 differences** — 52North may serialize differently | Medium | Medium | Use OSH fixtures as primary, add 52North fixtures when available. Tolerant extraction handles most variance. |
| 6 | **Schema response format variance** — JSON vs SWE Common have different wrapper fields | Medium | Low | Handle both `resultSchema` and `recordSchema` in `parseDatastreamSchemaResponse()`. Test both formats. |
| 7 | **`CommandStatusCodes` enum drift** — spec may add new status codes | Low | Low | `normalizeStatusCode()` returns undefined for unrecognized values; interface accepts the union type. |

---

## Appendix A: Cross-Reference Field Inventory

All `@id` and `@link` fields observed in Part 2 responses, compiled from smoke tests:

| Field | Found On | Example Value |
|-------|----------|---------------|
| `system@id` | Datastream, ControlStream | `"0o0o"` |
| `system@link` | Datastream, ControlStream | `{ href, uid, type }` |
| `datastream@id` | Observation | `"0ocb"` |
| `foi@id` | Observation | Feature of Interest reference |
| `samplingFeature@id` | Observation | Alternative to `foi@id` |
| `controlstream@id` | Command | `"0o10"` |
| `command@id` | CommandStatus | `"0o1qr7kupc33cgmqj0"` |

**Current status:** None of these fields are in the TypeScript interfaces. The parsers ignore them during extraction. If interface expansion is desired in the future, it will be additive — no parser changes required, only additional field extraction.

---

## Appendix B: Complete `@id` Cross-Reference Chain

```
System ← system@id ← Datastream ← datastream@id ← Observation
System ← system@id ← ControlStream ← controlstream@id ← Command ← command@id ← CommandStatus
```

This chain represents the full resource navigation hierarchy. Each `@id` field links a child resource back to its parent. The parsers do not resolve these references — they are URL-navigable via the QueryBuilder methods.

---

## Appendix C: Time Field Type Summary

| Resource | Field | Spec Type | Interface Type | Parser Action |
|----------|-------|-----------|---------------|---------------|
| Datastream | `validTime` | `timePeriod` (array[2]) | `TimeInterval?` | `parseValidTime()` |
| Datastream | `phenomenonTime` | `timePeriod \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| Datastream | `resultTime` | `timePeriod \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| ControlStream | `validTime` | `timePeriod` (array[2]) | `TimeInterval?` | `parseValidTime()` |
| ControlStream | `issueTime` | `timePeriod \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| ControlStream | `executionTime` | `timePeriod \| null` | `TimeInterval \| null` | `parseValidTime()` or null |
| Command | `issueTime` | `date-time` (instant) | `string` | Pass-through |
| Command | `executionTime` | `timePeriod` (array[2]) | `TimeInterval?` | `parseValidTime()` |
| CommandStatus | `reportTime` | `date-time` (instant) | `string` | Pass-through |
| CommandStatus | `executionTime` | `timePeriod` (array[2]) | `TimeInterval?` | `parseValidTime()` |
| Observation | `phenomenonTime` | `date-time` (instant) | `string?` | Pass-through |
| Observation | `resultTime` | `date-time` (instant) | `string` | Pass-through |

Key distinction: **Instants** (`date-time`) stay as strings per the interface. **Periods** (`timePeriod` / array[2]) are parsed to `TimeInterval` via `parseValidTime()`. See [validTime coverage analysis](../../research/phase-5/validtime-coverage-analysis.md) for full rationale.
