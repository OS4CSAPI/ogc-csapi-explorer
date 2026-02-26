# Worker Extensions Testing Strategy

> **🚫 OUT OF SCOPE (February 2026)**
>
> Worker extensions have been **removed from the CSAPI contribution scope entirely**. Analysis of the upstream codebase found that no JSON-based API (EDR, STAC, TMS, OGC API) uses the Web Worker infrastructure — only XML-based APIs (WMS, WFS, WMTS) offload parsing to workers for CPU-intensive XML DOM traversal. CSAPI operations use `response.json()` which does not benefit from worker offloading. All 9 proposed message types had zero upstream precedent. See ROADMAP v3.1 and Guide §8 for the full rationale.
>
> **Binary SWE parsing remains in scope** at the parser level (Phase 3 Task 3.13, Doc 10). Only worker offloading is excluded.
>
> This document is retained as reference material only — do not implement any worker message types or tests.

> **⚠️ Phase 2F Review Notice (February 2026)**
>
> This document was reviewed in [Phase 2F: Integration & Workflow Category Deep Dive](../review/phase-2f-integration-workflow-category.md). Three high-priority issues were identified:
>
> - **H1 — Scope Gating Required:** This testing strategy is **Phase 4 material**. Worker message handlers (`csapi-worker.ts`) must be implemented before these tests can be written. Do not implement before Phases 1-3 are complete. See ROADMAP.md Phase 4, Task 1.
> - **H2 — Performance Testing Out of Scope:** Performance threshold assertions (Section 7: `expect(duration).toBeLessThan(200)`) are **out of scope** for this contribution project, consistent with the project-wide scope decision (see Doc 33: "⚠️ PERFORMANCE TESTING IS NOT IN SCOPE ⚠️"). Upstream `ogc-client` has zero performance tests. Section 7 is retained as reference material only — do not implement any performance test assertions.
> - **H3 — `PARSE_SWE_BINARY` Worker Offloading Deferred:** PARSE_SWE_BINARY worker message type (15 scenarios, 180-200 lines) is deferred to Phase 4 along with the rest of this document. **Clarification:** This deferral applies only to the worker message type. Binary SWE parsing at the parser level (Doc 10, 96 tests) is IN SCOPE per the implementation guide §7 and Phase 2D assessment (M2/P4).
>
> Additional medium-priority notes: M3 (TRAVERSE_HIERARCHY needs explicit fetch mocking strategy), M4 (differentiate minimum viable ~200-300 lines from comprehensive ~2,310-2,860 lines), M5 (scope dependency on non-existent message handlers). See Phase 2F report for details.
>
> **Adjusted initial contribution scope:** ~200-300 test lines (minimum viable: 9 message types × 1-2 scenarios each, 4-6 hours) rather than 201 scenarios / 47-61 hours.

**Research Plan:** [Research Plan 16: Worker Extensions Testing Strategy](../research-plans/16-worker-extensions-testing.md)

**Research Questions:** 6 core questions about testing Worker message types in Jest, async parsing operations, fallback for non-worker environments, fixture requirements for heavy parsing, performance characteristics, and integration tests with parsers

**Methodology:** 5-phase systematic analysis (Phase 1: Worker Architecture Analysis with message type mapping → Phase 2: Upstream Worker Test Analysis of camptocamp/ogc-client patterns → Phase 3: Jest Worker Testing Patterns evaluation → Phase 4: Test Scenario Design for 201 scenarios across 9 message types → Phase 5: Synthesis into comprehensive testing strategy)

**Research Time:** 2.5 hours (February 6, 2026)

**Primary Source(s):**

- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Worker Extensions section)
- [ROADMAP](../../../planning/ROADMAP.md) (Phase 4: Task 1 - Worker Extensions)

**Supporting Resources:**

- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream test patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (Worker test patterns from ogc-client)
- Section 9: [SensorML Testing Requirements](09-sensorml-testing-requirements.md) (parser integration fixtures)
- Section 10: [SWE Common Testing Requirements](10-swe-common-testing-requirements.md) (parser integration fixtures)
- Section 11: [GeoJSON CSAPI Testing Requirements](11-geojson-csapi-testing-requirements.md) (parser integration fixtures)

**Document Purpose:** Defines comprehensive testing strategy for 9 Web Worker message types with Jest testing patterns, async message passing test templates, fallback behavior scenarios, performance testing approach, and integration patterns with format parsers

---

## Executive Summary

This document defines the testing strategy for the 9 Web Worker message types that extend the existing ogc-client worker infrastructure for CSAPI operations. The worker extension moves heavy parsing (SensorML, SWE Common), validation (observation/command schemas), and query operations (hierarchy traversal, spatial/temporal filtering) off the main thread to maintain responsive UIs.

### Key Findings

**Worker Architecture:**

- **Existing Pattern:** Request/response message passing via `sendTaskRequest()` and `addTaskHandler()`
- **Fallback Mechanism:** EventTarget-based fallback for non-worker environments (Node.js, older browsers)
- **Message Types:** 9 new CSAPI message types extending 4 existing (WMS, WFS, WMTS, updateFetchOptions)

**Testing Approach:**

- **Unit Tests:** 180-220 lines per message type (~1,800-2,000 lines total for 9 message types)
- **Integration Tests:** 200-300 lines for parser integration, 150-200 lines for fallback behavior (~350-500 lines total)
- **Fixture Requirements:** Leverage existing fixtures from Sections 9, 10, 11 (minimal new fixtures needed)

**Test Coverage Targets:**

- 100% message type coverage (all 9 types with scenarios)
- 100% parser integration coverage (SensorML, SWE Common, GeoJSON CSAPI)
- 100% fallback mechanism coverage (with/without worker)
- Error condition coverage (validation errors, parse errors, timeouts)

### 9 Worker Message Types to Test

| #         | Message Type              | Parser     | Operation                       | Complexity | Test Lines      |
| --------- | ------------------------- | ---------- | ------------------------------- | ---------- | --------------- |
| 1         | `PARSE_SENSORML_3`        | SensorML   | Parse hierarchical JSON         | Medium     | 180-200         |
| 2         | `PARSE_SWE_RESULT`        | SWE Common | Parse JSON/Text/Binary + schema | High       | 200-220         |
| 3         | `PARSE_SWE_BINARY`        | SWE Common | Decode Base64 binary block      | Medium     | 180-200         |
| 4         | `VALIDATE_OBSERVATIONS`   | SWE Common | Schema validation               | Medium     | 180-200         |
| 5         | `VALIDATE_COMMANDS`       | SWE Common | Schema validation               | Medium     | 180-200         |
| 6         | `PARSE_OBSERVATION_ARRAY` | SWE Common | Large array parsing             | Medium     | 180-200         |
| 7         | `TRAVERSE_HIERARCHY`      | CSAPI      | Recursive traversal             | Low        | 150-180         |
| 8         | `FILTER_SPATIAL`          | GeoJSON    | Bbox filtering                  | Low        | 150-180         |
| 9         | `FILTER_TEMPORAL`         | CSAPI      | Temporal filtering              | Low        | 150-180         |
| **Total** |                           |            |                                 |            | **1,510-1,760** |

---

## 1. Worker Architecture Overview

### 1.1 Existing Worker Infrastructure

The upstream ogc-client library provides a proven Web Worker pattern in `src/worker/`:

**Core Components:**

- **`worker.ts`**: Worker-side message handlers (runs in worker thread)
- **`utils.ts`**: Message passing utilities (`sendTaskRequest`, `addTaskHandler`)
- **`index.ts`**: Main-thread API with worker lifecycle management
- **`worker?worker&inline` Vite plugin**: Worker bundling

**Existing Message Types (4):**

1. `parseWmsCapabilities` - Parse WMS XML capabilities
2. `parseWfsCapabilities` - Parse WFS XML capabilities
3. `queryWfsFeatureTypeDetails` - Query WFS feature type details
4. `updateFetchOptions` - Update fetch configuration
5. `parseWmtsCapabilities` - Parse WMTS XML capabilities

**Architecture Pattern:**

```typescript
// Main thread (src/worker/index.ts)
export function parseWmsCapabilities(
  url: string
): Promise<WmsCapabilitiesInfo> {
  return sendTaskRequest('parseWmsCapabilities', getWorkerInstance(), { url });
}

// Worker thread (src/worker/worker.ts)
addTaskHandler('parseWmsCapabilities', globalThis, ({ url }: { url: string }) =>
  queryXmlDocument(url)
    .then((xmlDoc) => check(xmlDoc, url))
    .then((xmlDoc) => ({
      info: wmsCapabilities.readInfoFromCapabilities(xmlDoc),
      layers: wmsCapabilities.readLayersFromCapabilities(xmlDoc),
      // ... more parsing
    }))
);
```

### 1.2 Message Passing Protocol

**Request Structure (`WorkerRequest`):**

```typescript
{
  requestId: number,      // Unique ID for request/response matching
  taskName: string,       // Message type identifier
  params: Record<string, unknown>  // Task-specific parameters
}
```

**Response Structure (`WorkerResponse`):**

```typescript
{
  requestId: number,      // Matches request ID
  error?: Record<string, unknown>,     // Serialized error if failed
  response?: Record<string, unknown>   // Task result if succeeded
}
```

**Promise-Based API:**

- Main thread calls `sendTaskRequest()` which returns a Promise
- Worker receives message, executes handler, posts response
- Main thread resolves/rejects Promise based on response

### 1.3 Fallback Mechanism

**Non-Worker Environment Detection:**

```typescript
const useWorker = typeof WorkerGlobalScope !== 'undefined';
```

**Fallback Implementation:**

- Uses `EventTarget` (global fallbackEventTarget) for message passing
- Same handler code runs on main thread instead of worker thread
- Synchronous execution (blocks main thread but maintains API compatibility)
- Enabled via `enableFallbackWithoutWorker()` API

**Fallback Testing:**

- Existing test: `src/worker-fallback/worker-fallback.spec.ts`
- Tests WMS/WFS endpoint parsing with fallback enabled
- CSAPI worker extensions must follow same pattern

---

## 2. CSAPI Worker Message Types

### 2.1 Format Parsing Operations (3 Message Types)

#### 2.1.1 PARSE_SENSORML_3

**Purpose:** Parse SensorML 3.0 JSON documents with complex hierarchical component trees.

**Input Parameters:**

```typescript
{
  sensormlJson: unknown,        // Raw SensorML 3.0 JSON
  options?: {
    skipSWEParsing?: boolean,   // Skip SWE Common deep parsing
    maxDepth?: number           // Limit recursion depth (default: 50)
  }
}
```

**Output:**

```typescript
{
  system: PhysicalSystem | PhysicalComponent | SimpleProcess | AggregateProcess,
  metadata: {
    parseTime: number,          // Parsing duration (ms)
    componentCount: number,     // Total components parsed
    maxDepth: number           // Actual recursion depth reached
  }
}
```

**Error Conditions:**

- Invalid JSON structure
- Unknown system type
- Recursion depth exceeded
- Missing required SensorML properties
- SWE Common parsing errors (if enabled)

**Performance Characteristics:**

- Small documents (<10 components): <10ms
- Medium documents (10-50 components): 10-50ms
- Large documents (>50 components): >50ms

#### 2.1.2 PARSE_SWE_RESULT

**Purpose:** Parse SWE Common encoded observation results (JSON/Text/Binary) with schema validation.

**Input Parameters:**

```typescript
{
  encoding: 'json' | 'text' | 'binary',
  data: string | ArrayBuffer,        // Encoded data
  schema: DataStreamSchema,          // SWE Common DataArray/DataRecord schema
  options?: {
    validateConstraints?: boolean,   // Validate quality/constraint indicators
    decimalSeparator?: string,       // For text encoding (default: '.')
    tokenSeparator?: string,         // For text encoding (default: ',')
    blockSeparator?: string          // For text encoding (default: '\n')
  }
}
```

**Output:**

```typescript
{
  observations: Array<Record<string, unknown>>,
  metadata: {
    parseTime: number,
    observationCount: number,
    encoding: string,
    validationErrors: Array<{ index: number, field: string, error: string }>
  }
}
```

**Error Conditions:**

- Unsupported encoding type
- Schema mismatch (data structure doesn't match schema)
- Binary decoding errors (invalid Base64, wrong data type)
- Text parsing errors (incorrect separators, malformed values)
- Constraint violations (out-of-range values, invalid quality indicators)

**Performance Characteristics:**

- Small datasets (<100 observations): <20ms
- Medium datasets (100-1,000 observations): 20-100ms
- Large datasets (>1,000 observations): >100ms

#### 2.1.3 PARSE_SWE_BINARY

**Purpose:** Decode Base64-encoded binary SWE Common data blocks.

**Input Parameters:**

```typescript
{
  base64Data: string,                // Base64-encoded binary block
  dataTypes: Array<BinaryDataType>,  // Data type sequence
  blockSize: number,                 // Expected block size
  options?: {
    byteOrder?: 'littleEndian' | 'bigEndian',  // Default: littleEndian
    stringEncoding?: 'utf-8' | 'ascii'         // Default: utf-8
  }
}
```

**BinaryDataType Values:**

- Integer types: `signedByte`, `unsignedByte`, `signedShort`, `unsignedShort`, `signedInt`, `unsignedInt`, `signedLong`, `unsignedLong`
- Float types: `float16`, `float32`, `float64`, `float128`
- String type: `string-utf-8`

**Output:**

```typescript
{
  values: Array<number | string>,
  metadata: {
    parseTime: number,
    blockCount: number,
    totalBytes: number
  }
}
```

**Error Conditions:**

- Invalid Base64 encoding
- Block size mismatch
- Unknown data type
- Buffer underflow/overflow
- Invalid string encoding

**Performance Characteristics:**

- Small blocks (<1KB): <5ms
- Medium blocks (1KB-100KB): 5-50ms
- Large blocks (>100KB): >50ms

### 2.2 Validation Operations (2 Message Types)

#### 2.2.1 VALIDATE_OBSERVATIONS

**Purpose:** Validate observation arrays against DataStream schemas with constraint checking.

**Input Parameters:**

```typescript
{
  observations: Array<unknown>,
  schema: DataStreamSchema,          // SWE Common DataArray/DataRecord
  options?: {
    validateConstraints?: boolean,   // Check AllowedValues, AllowedTimes, etc.
    validateQuality?: boolean,       // Check quality indicators
    stopOnFirstError?: boolean       // Default: false (collect all errors)
  }
}
```

**Output:**

```typescript
{
  valid: boolean,
  errors: Array<{
    index: number,                   // Observation index
    field: string,                   // Field name
    type: 'missing' | 'type' | 'constraint' | 'quality',
    message: string
  }>,
  metadata: {
    validateTime: number,
    observationCount: number,
    errorCount: number
  }
}
```

**Error Conditions:**

- Schema not provided
- Invalid schema structure
- Observations not an array

**Validation Types:**

- **Structure validation:** Required fields present, correct types
- **Constraint validation:** Values within AllowedValues, AllowedTimes ranges
- **Quality validation:** Quality indicators valid (good, bad, estimate, etc.)

#### 2.2.2 VALIDATE_COMMANDS

**Purpose:** Validate command parameter objects against ControlStream schemas.

**Input Parameters:**

```typescript
{
  commands: Array<unknown>,
  schema: ControlStreamSchema,       // SWE Common DataRecord for parameters
  options?: {
    validateConstraints?: boolean,
    checkFeasibility?: boolean,      // Validate against feasibility constraints
    stopOnFirstError?: boolean
  }
}
```

**Output:**

```typescript
{
  valid: boolean,
  errors: Array<{
    index: number,
    parameter: string,
    type: 'missing' | 'type' | 'constraint' | 'feasibility',
    message: string
  }>,
  metadata: {
    validateTime: number,
    commandCount: number,
    errorCount: number
  }
}
```

**Error Conditions:**

- Schema not provided
- Invalid schema structure
- Commands not an array
- Feasibility check failures

### 2.3 Query Operations (4 Message Types)

#### 2.3.1 PARSE_OBSERVATION_ARRAY

**Purpose:** Parse and validate large observation arrays (thousands of observations).

**Input Parameters:**

```typescript
{
  observations: Array<unknown>,
  schema: DataStreamSchema,
  options?: {
    validateEach?: boolean,          // Validate each observation
    computeStats?: boolean,          // Compute min/max/avg for numeric fields
    batchSize?: number              // Process in batches (default: 1000)
  }
}
```

**Output:**

```typescript
{
  parsed: Array<Observation>,
  statistics?: Record<string, { min: number, max: number, avg: number }>,
  metadata: {
    parseTime: number,
    totalCount: number,
    validCount: number,
    invalidCount: number
  }
}
```

**Performance Characteristics:**

- Small arrays (<1,000): <50ms
- Medium arrays (1,000-10,000): 50-500ms
- Large arrays (>10,000): >500ms

#### 2.3.2 TRAVERSE_HIERARCHY

**Purpose:** Recursively traverse system/deployment hierarchies to build complete trees.

> **📝 Phase 2F M3 Note:** TRAVERSE_HIERARCHY is unique among the 9 message types because it initiates HTTP fetches via `fetchFunc` during traversal. Tests MUST inject a mock fetch function (e.g., `jest.fn()` returning fixture data) rather than relying on `globalThis.fetch`. See test scenario 10 (Fetch Integration) for the pattern. Without explicit mocking, these tests would require live or fixture-served HTTP — approaching AP2 territory.

**Input Parameters:**

```typescript
{
  rootId: string,                    // Starting system/deployment ID
  hierarchyType: 'system' | 'deployment',
  includeDescendants: boolean,       // Recursive traversal
  maxDepth?: number,                 // Limit recursion (default: 10)
  fetchFunc: string                  // Serialized fetch function name
}
```

**Output:**

```typescript
{
  root: System | Deployment,
  descendants: Array<System | Deployment>,
  tree: HierarchyTree,               // Nested structure
  metadata: {
    traversalTime: number,
    totalNodes: number,
    maxDepth: number,
    fetchCount: number
  }
}
```

**Error Conditions:**

- Root resource not found
- Max depth exceeded
- Circular reference detected
- Fetch failures

#### 2.3.3 FILTER_SPATIAL

**Purpose:** Filter GeoJSON FeatureCollections by bounding box with bbox intersection calculations.

**Input Parameters:**

```typescript
{
  features: GeoJSON.FeatureCollection,
  bbox: [number, number, number, number],  // [minLon, minLat, maxLon, maxLat]
  options?: {
    crs?: string,                    // Coordinate reference system
    partial?: boolean                // Include partially intersecting features
  }
}
```

**Output:**

```typescript
{
  filtered: GeoJSON.FeatureCollection,
  metadata: {
    filterTime: number,
    totalCount: number,
    filteredCount: number,
    rejectedCount: number
  }
}
```

**Error Conditions:**

- Invalid bbox format
- Invalid GeoJSON structure
- Geometry type not supported
- CRS mismatch

#### 2.3.4 FILTER_TEMPORAL

**Purpose:** Filter observation/command arrays by temporal intervals.

**Input Parameters:**

```typescript
{
  items: Array<Observation | Command>,
  interval: {
    start?: string | Date,           // ISO 8601 datetime
    end?: string | Date
  },
  timeField: 'phenomenonTime' | 'resultTime' | 'executionTime',
  options?: {
    inclusive?: boolean              // Include boundary values
  }
}
```

**Output:**

```typescript
{
  filtered: Array<Observation | Command>,
  metadata: {
    filterTime: number,
    totalCount: number,
    filteredCount: number,
    rejectedCount: number
  }
}
```

**Error Conditions:**

- Invalid interval format
- Time field missing
- Invalid datetime values

---

## 3. Test Scenarios by Message Type

### 3.1 PARSE_SENSORML_3 Test Scenarios

**Test File:** `src/worker/sensorml-worker.spec.ts` (~180-200 lines)

#### Unit Tests (15 scenarios)

**1. Parse PhysicalSystem (Simple)**

- **Input:** PhysicalSystem JSON with 3 components
- **Expected:** Parsed system object with components array
- **Assertions:** Type, ID, name, components length, metadata

**2. Parse PhysicalComponent (No Components)**

- **Input:** Leaf PhysicalComponent JSON
- **Expected:** Parsed component with no sub-components
- **Assertions:** Type, properties, no components array

**3. Parse SimpleProcess**

- **Input:** SimpleProcess JSON with inputs/outputs
- **Expected:** Parsed process with IO definitions
- **Assertions:** Type, inputs array, outputs array, method property

**4. Parse AggregateProcess**

- **Input:** AggregateProcess with multiple component processes
- **Expected:** Parsed aggregate with components
- **Assertions:** Components array length, component types

**5. Parse Deep Hierarchy (10 levels)**

- **Input:** PhysicalSystem with 10-level nested components
- **Expected:** Complete tree parsed
- **Assertions:** Max depth reached, total component count

**6. Parse with SWE Common Integration**

- **Input:** System with SWE DataRecord outputs
- **Expected:** Parsed with SWE data components
- **Assertions:** SWE components parsed, data types correct

**7. Skip SWE Parsing Option**

- **Input:** System with SWE components, `skipSWEParsing: true`
- **Expected:** SWE components as raw JSON
- **Assertions:** SWE not fully parsed, faster parse time

**8. Max Depth Limit Enforcement**

- **Input:** 60-level hierarchy, `maxDepth: 50`
- **Expected:** Error thrown at depth 50
- **Assertions:** Error message, partial tree returned

**9. Invalid JSON Structure**

- **Input:** Malformed JSON string
- **Expected:** Parse error
- **Assertions:** Error type, message contains "JSON"

**10. Unknown System Type**

- **Input:** JSON with `"type": "UnknownSystemType"`
- **Expected:** Error thrown
- **Assertions:** Error message mentions unknown type

**11. Missing Required Property (id)**

- **Input:** System JSON without `uid` property
- **Expected:** Validation error
- **Assertions:** Error mentions missing "uid"

**12. Empty Components Array**

- **Input:** PhysicalSystem with `"components": []`
- **Expected:** Valid parse, empty components
- **Assertions:** No error, components length = 0

**13. Parse Performance (Large Document)**

- **Input:** System with 100 components
- **Expected:** Parse completes
- **Assertions:** Parse time recorded, time < 200ms threshold

**14. Circular Reference Detection**

- **Input:** System referencing itself via component
- **Expected:** Error or max depth reached
- **Assertions:** Graceful handling, no infinite loop

**15. Parse Metadata Accuracy**

- **Input:** System with 25 components, 5 levels deep
- **Expected:** Accurate metadata
- **Assertions:** componentCount = 25, maxDepth = 5, parseTime > 0

#### Integration Tests (3 scenarios)

**16. Worker Message Passing**

- **Setup:** Send PARSE_SENSORML_3 request via `sendTaskRequest`
- **Expected:** Promise resolves with parsed system
- **Assertions:** Correct message format, response structure

**17. Fallback Mode**

- **Setup:** Enable fallback, parse same document
- **Expected:** Same result as worker mode
- **Assertions:** Results identical, no worker used

**18. Concurrent Parsing**

- **Setup:** Send 5 parse requests simultaneously
- **Expected:** All resolve with correct results
- **Assertions:** No request ID collision, all responses correct

### 3.2 PARSE_SWE_RESULT Test Scenarios

**Test File:** `src/worker/swe-result-worker.spec.ts` (~200-220 lines)

#### Unit Tests (20 scenarios)

**JSON Encoding (5 tests):**

1. **Parse JSON DataArray:** Input JSON array, schema with 3 fields → Parsed observations
2. **Parse JSON DataRecord:** Input JSON object, schema → Single observation
3. **Parse JSON with Arrays Option:** Input with `recordsAsArrays: true` → Array format
4. **JSON Special Values:** Input with `-Infinity`, `+Infinity`, `NaN` strings → Parsed correctly
5. **JSON Schema Mismatch:** Input doesn't match schema → Validation errors

**Text Encoding (5 tests):** 6. **Parse CSV Text:** Input CSV with default separators → Parsed observations 7. **Parse Custom Separators:** Input with custom token/block separators → Correct parsing 8. **Parse with Decimal Separator:** Input with comma decimal separator → Numbers correct 9. **Text Missing Values:** Input with empty tokens (`,,`) → Null values 10. **Text Malformed Row:** Input with wrong column count → Error with row number

**Binary Encoding (5 tests):** 11. **Parse Base64 Binary:** Input Base64 with float32 array → Decoded values 12. **Parse Mixed Data Types:** Input with int, float, string mix → All types correct 13. **Parse Little Endian:** Input with little endian byte order → Correct values 14. **Parse Big Endian:** Input with big endian → Correct values (byte swap) 15. **Binary Block Size Mismatch:** Input size doesn't match schema → Error

**Validation (3 tests):** 16. **Validate with Constraints:** Input with values outside AllowedValues → Errors reported 17. **Validate Quality Indicators:** Input with invalid quality codes → Validation errors 18. **Stop on First Error:** Input with multiple errors, `stopOnFirstError: true` → One error

**Performance (2 tests):** 19. **Parse Large JSON Dataset (5,000 observations):** → Parse time < 200ms 20. **Parse Large Binary Block (100KB):** → Parse time < 100ms

#### Integration Tests (3 scenarios)

**21. Worker Message Passing (All Encodings)**

- **Setup:** Send 3 requests (JSON, Text, Binary) via worker
- **Expected:** All resolve correctly
- **Assertions:** Encoding-specific results correct

**22. Fallback Mode Consistency**

- **Setup:** Parse same data with/without worker
- **Expected:** Identical results
- **Assertions:** Bit-for-bit identical output

**23. Schema Validation Integration**

- **Setup:** Parse with complex schema (nested DataRecords, AllowedValues)
- **Expected:** Full validation performed
- **Assertions:** Constraint violations caught

### 3.3 PARSE_SWE_BINARY Test Scenarios

**Test File:** `src/worker/swe-binary-worker.spec.ts` (~180-200 lines)

#### Unit Tests (12 scenarios)

**Integer Types (4 tests):**

1. **Decode SignedByte:** Base64 with signed bytes → Correct values
2. **Decode UnsignedShort:** Base64 with unsigned shorts → Correct values
3. **Decode SignedInt:** Base64 with signed ints → Correct values including negatives
4. **Decode UnsignedLong:** Base64 with large unsigned longs → Correct uint64 values

**Float Types (3 tests):** 5. **Decode Float32:** Base64 with IEEE 754 floats → Correct float values 6. **Decode Float64:** Base64 with doubles → Correct double values 7. **Decode Special Floats:** Base64 with -Infinity, +Infinity, NaN → Special values

**String Types (2 tests):** 8. **Decode UTF-8 String:** Base64 with variable-length UTF-8 → Correct strings 9. **Decode Fixed-Length String:** Base64 with fixed string length → Padded strings

**Byte Order (2 tests):** 10. **Little Endian (Default):** Multi-byte values → Correct little endian 11. **Big Endian:** Same values, big endian flag → Byte-swapped correct

**Error Cases (1 test):** 12. **Invalid Base64:** Malformed Base64 string → Error thrown

#### Integration Tests (3 scenarios)

**13. Worker Message Passing**

- **Setup:** Send binary decode request
- **Expected:** Promise resolves with decoded values
- **Assertions:** ArrayBuffer correctly decoded

**14. Large Block Performance**

- **Setup:** Send 500KB binary block
- **Expected:** Decode completes in <200ms
- **Assertions:** Performance threshold met

**15. Fallback Mode**

- **Setup:** Decode with fallback enabled
- **Expected:** Same results as worker
- **Assertions:** Results identical

### 3.4 VALIDATE_OBSERVATIONS Test Scenarios

**Test File:** `src/worker/validate-observations-worker.spec.ts` (~180-200 lines)

#### Unit Tests (12 scenarios)

**Structure Validation (4 tests):**

1. **Valid Observations:** Input matching schema → `valid: true`, no errors
2. **Missing Required Field:** Observation missing required field → Error with field name
3. **Wrong Field Type:** String where number expected → Type error
4. **Extra Fields Allowed:** Observation with extra fields → No error (lenient)

**Constraint Validation (4 tests):** 5. **AllowedValues Range:** Value outside AllowedValues → Constraint error 6. **AllowedTimes Interval:** Time outside interval → Temporal constraint error 7. **Numeric Range (min/max):** Value below min or above max → Range error 8. **Category AllowedTokens:** Invalid category token → Token error

**Quality Validation (2 tests):** 9. **Valid Quality Indicators:** Quality = "good" → No error 10. **Invalid Quality Code:** Quality = "unknown-code" → Quality error

**Options (2 tests):** 11. **Stop on First Error:** Multiple errors, stop flag → Only first error returned 12. **Skip Constraint Validation:** Constraints violated, validate flag off → No constraint errors

#### Integration Tests (3 scenarios)

**13. Large Array Validation**

- **Setup:** Validate 10,000 observations
- **Expected:** All validated
- **Assertions:** Performance acceptable (<500ms)

**14. Worker Message Passing**

- **Setup:** Send validation request via worker
- **Expected:** Response with validation results
- **Assertions:** Errors array correct

**15. Fallback Mode**

- **Setup:** Validate with fallback enabled
- **Expected:** Same validation results
- **Assertions:** Results identical

### 3.5 VALIDATE_COMMANDS Test Scenarios

**Test File:** `src/worker/validate-commands-worker.spec.ts` (~180-200 lines)

**Test Structure:** Similar to VALIDATE_OBSERVATIONS with 15 scenarios (12 unit + 3 integration)

**Differences:**

- Command-specific parameter types (setpoint, mode, enable/disable)
- Feasibility constraint checking (valid command ranges, equipment capabilities)
- Control stream schema validation

### 3.6 PARSE_OBSERVATION_ARRAY Test Scenarios

**Test File:** `src/worker/parse-observations-worker.spec.ts` (~180-200 lines)

#### Unit Tests (10 scenarios)

**Parsing (4 tests):**

1. **Small Array (<100):** Parse and validate → All parsed
2. **Medium Array (1,000):** Parse with validation → Correct count
3. **Large Array (10,000):** Parse without validation → Fast parsing
4. **Mixed Valid/Invalid:** Array with some invalid → Separate counts

**Batch Processing (2 tests):** 5. **Default Batch Size (1,000):** Large array → Processed in batches 6. **Custom Batch Size (500):** Same array → Different batch count

**Statistics (2 tests):** 7. **Compute Stats Option:** Numeric fields → Min/max/avg computed 8. **Stats Disabled:** Same data, stats off → No stats in result

**Error Handling (2 tests):** 9. **Schema Missing:** No schema provided → Error 10. **Non-Array Input:** Input is object not array → Type error

#### Integration Tests (5 scenarios)

**11. Worker Message Passing**

- **Setup:** Send large array via worker
- **Expected:** Parsed in worker thread
- **Assertions:** Main thread not blocked

**12. Concurrent Parsing**

- **Setup:** Parse 3 large arrays simultaneously
- **Expected:** All complete without interference
- **Assertions:** Correct results for each

**13. Performance Threshold (10,000 obs)**

- **Setup:** Parse 10,000 observations
- **Expected:** Complete in <500ms
- **Assertions:** Time threshold met

**14. Fallback Mode Performance**

- **Setup:** Parse large array with fallback
- **Expected:** Slower but correct
- **Assertions:** Results correct, time slower

**15. Memory Efficiency**

- **Setup:** Parse very large array (100,000 obs)
- **Expected:** No memory overflow
- **Assertions:** Process completes, memory usage reasonable

### 3.7 TRAVERSE_HIERARCHY Test Scenarios

**Test File:** `src/worker/traverse-hierarchy-worker.spec.ts` (~150-180 lines)

#### Unit Tests (8 scenarios)

**Basic Traversal (3 tests):**

1. **Single Node (No Descendants):** System with no children → Root only
2. **Flat Hierarchy (3 Children):** System with 3 direct children → All children found
3. **Deep Hierarchy (5 Levels):** System with 5-level tree → Complete tree built

**Options (3 tests):** 4. **Max Depth Limit:** 10-level tree, maxDepth=5 → Stops at level 5 5. **Include Descendants Flag:** Descendants disabled → Only root 6. **Deployment Hierarchy:** Deployment tree instead of systems → Works correctly

**Error Handling (2 tests):** 7. **Root Not Found:** Invalid root ID → Error 8. **Circular Reference:** System references ancestor → Detected, error

#### Integration Tests (4 scenarios)

**9. Worker Message Passing**

- **Setup:** Send traversal request
- **Expected:** Tree built in worker
- **Assertions:** Complete tree structure

**10. Fetch Integration**

- **Setup:** Traversal requires fetching descendant resources
- **Expected:** Fetch calls made, data integrated
- **Assertions:** Correct fetch count, data correct

**11. Performance (Large Hierarchy - 100 nodes)**

- **Setup:** Traverse 100-node system tree
- **Expected:** Complete in <200ms
- **Assertions:** All nodes traversed, time acceptable

**12. Fallback Mode**

- **Setup:** Traverse with fallback enabled
- **Expected:** Same tree structure
- **Assertions:** Results identical

### 3.8 FILTER_SPATIAL Test Scenarios

**Test File:** `src/worker/filter-spatial-worker.spec.ts` (~150-180 lines)

#### Unit Tests (10 scenarios)

**Geometry Types (4 tests):**

1. **Point Features:** Filter points by bbox → Correct inclusion/exclusion
2. **LineString Features:** Filter lines → Partially intersecting handled
3. **Polygon Features:** Filter polygons → Intersection detection correct
4. **Multi-Geometries:** Filter MultiPoint/MultiLineString → All geometries checked

**Bbox Variations (3 tests):** 5. **Global Bbox:** Bbox covering entire world → All features included 6. **Small Bbox:** Small region → Only nearby features 7. **Anti-Meridian Bbox:** Bbox crossing dateline → Correct wrapping logic

**Options (2 tests):** 8. **Partial Intersection:** Partial flag on → Partially intersecting included 9. **Partial Disabled:** Partial flag off → Only fully contained features

**Error Handling (1 test):** 10. **Invalid Bbox:** Malformed bbox array → Error

#### Integration Tests (3 scenarios)

**11. Large FeatureCollection (10,000 features)**

- **Setup:** Filter large collection
- **Expected:** Filtered quickly (<100ms)
- **Assertions:** Performance acceptable, correct count

**12. Worker Message Passing**

- **Setup:** Send filter request
- **Expected:** Filtered in worker
- **Assertions:** Correct filtered collection

**13. Fallback Mode**

- **Setup:** Filter with fallback enabled
- **Expected:** Same filtered results
- **Assertions:** Results identical

### 3.9 FILTER_TEMPORAL Test Scenarios

**Test File:** `src/worker/filter-temporal-worker.spec.ts` (~150-180 lines)

**Test Structure:** Similar to FILTER_SPATIAL with 13 scenarios (10 unit + 3 integration)

**Key Differences:**

- Temporal interval variations (open start, open end, closed interval)
- Time field options (phenomenonTime, resultTime, executionTime)
- Datetime format handling (ISO 8601 strings, Date objects)
- Inclusive/exclusive boundary handling

---

## 4. Jest Worker Testing Patterns

### 4.1 Worker Mocking Strategies

#### Strategy 1: Fallback Mode Testing (Recommended)

**Pattern:** Enable fallback mode to run worker code synchronously on main thread.

**Advantages:**

- No worker mocking needed
- Tests actual worker handler code
- Same code path as production fallback
- Simple test setup

**Implementation:**

```typescript
import { enableFallbackWithoutWorker } from '../worker/index.js';
import '../worker/worker.js'; // Load worker handlers

enableFallbackWithoutWorker();

describe('Worker fallback', () => {
  it('parses SensorML 3.0', async () => {
    const result = await parseSensorML3(sensormlJson);
    expect(result.system.type).toBe('PhysicalSystem');
  });
});
```

**When to Use:**

- Testing worker handler logic
- Integration tests where worker/fallback behavior identical
- CI environments where workers may not be available

#### Strategy 2: Worker Message Mocking

**Pattern:** Mock worker `postMessage`/`addEventListener` for unit testing message passing.

**Advantages:**

- Tests actual worker creation and message passing
- Can verify message structure
- Tests async Promise resolution

**Implementation:**

```typescript
// Mock Worker constructor
global.Worker = jest.fn().mockImplementation(() => ({
  postMessage: jest.fn((message) => {
    // Simulate async response
    setTimeout(() => {
      const response: WorkerResponse = {
        requestId: message.requestId,
        response: {
          /* mock result */
        },
      };
      messageListener({ data: response });
    }, 0);
  }),
  addEventListener: jest.fn((event, listener) => {
    if (event === 'message') {
      messageListener = listener;
    }
  }),
  removeEventListener: jest.fn(),
}));

let messageListener: (event: MessageEvent) => void;
```

**When to Use:**

- Testing worker lifecycle (creation, termination)
- Testing error handling in message passing
- Testing concurrent request handling

#### Strategy 3: Integration Testing with Real Worker

**Pattern:** Use real worker in Node.js environment (requires worker_threads polyfill).

**Advantages:**

- Tests actual production behavior
- Catches worker-specific issues
- True parallelism testing

**Disadvantages:**

- Requires Node.js worker_threads or JSDOM setup
- More complex test configuration
- Slower test execution

**When to Use:**

- Performance testing (actual parallelism)
- Worker-specific bug reproduction
- Final integration verification

### 4.2 Async Testing Patterns

**Promise-Based Tests:**

```typescript
it('resolves with parsed result', async () => {
  const result = await parseSensorML3(sensormlJson);
  expect(result).toHaveProperty('system');
});
```

**Error Handling Tests:**

```typescript
it('rejects with validation error', async () => {
  await expect(parseSensorML3(invalidJson)).rejects.toThrow(
    'Invalid SensorML structure'
  );
});
```

**Timeout Tests:**

```typescript
it('rejects if parsing takes too long', async () => {
  jest.setTimeout(1000); // 1 second timeout
  await expect(parseSensorML3(hugeSensorML)).rejects.toThrow('Timeout');
}, 1000);
```

**Concurrent Request Tests:**

```typescript
it('handles concurrent parse requests', async () => {
  const promises = [
    parseSensorML3(sensorml1),
    parseSensorML3(sensorml2),
    parseSensorML3(sensorml3),
  ];
  const results = await Promise.all(promises);
  expect(results).toHaveLength(3);
  expect(results[0].system.uid).not.toBe(results[1].system.uid);
});
```

### 4.3 Test Structure Template

```typescript
import { enableFallbackWithoutWorker } from '../worker/index.js';
import '../worker/worker.js';

// Mock cache to avoid persistence
jest.mock('../shared/cache', () => ({
  useCache: jest.fn((factory) => factory()),
}));

enableFallbackWithoutWorker();

describe('MESSAGE_TYPE', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Happy Path', () => {
    it('processes valid input', async () => {
      // Arrange
      const input = /* fixture */;

      // Act
      const result = await workerFunction(input);

      // Assert
      expect(result).toHaveProperty('expectedField');
    });
  });

  describe('Error Handling', () => {
    it('throws error on invalid input', async () => {
      // Arrange
      const invalidInput = /* bad fixture */;

      // Act & Assert
      await expect(workerFunction(invalidInput))
        .rejects.toThrow('Expected error message');
    });
  });

  describe('Performance', () => {
    it('completes within threshold', async () => {
      // Arrange
      const largeInput = /* large fixture */;
      const startTime = performance.now();

      // Act
      await workerFunction(largeInput);
      const duration = performance.now() - startTime;

      // Assert
      expect(duration).toBeLessThan(200); // 200ms threshold
    });
  });
});
```

---

## 5. Fixture Requirements

### 5.1 Leveraging Existing Fixtures

**SensorML Fixtures (Section 9):**

- PhysicalSystem: `fixtures/sensorml/physical-system-valid.json`
- PhysicalComponent: `fixtures/sensorml/physical-component-valid.json`
- SimpleProcess: `fixtures/sensorml/simple-process-valid.json`
- AggregateProcess: `fixtures/sensorml/aggregate-process-valid.json`
- Deep hierarchy: `fixtures/sensorml/physical-system-deep-hierarchy.json`

**SWE Common Fixtures (Section 10):**

- JSON DataArray: `fixtures/swe-common/json/dataarray-valid.json`
- Text encoding: `fixtures/swe-common/text/weather-data.csv`
- Binary encoding: `fixtures/swe-common/binary/float32-array.base64`
- DataStream schema: `fixtures/swe-common/json/datastream-schema-valid.json`

**GeoJSON CSAPI Fixtures (Section 11):**

- Systems FeatureCollection: `fixtures/geojson-csapi/systems-collection-valid.json`
- Deployments: `fixtures/geojson-csapi/deployments-collection-valid.json`
- SamplingFeatures: `fixtures/geojson-csapi/sampling-features-collection-valid.json`

### 5.2 New Fixtures Needed

**Worker-Specific Fixtures (10 new fixtures):**

| Fixture                             | Purpose                                  | Size            | Format          |
| ----------------------------------- | ---------------------------------------- | --------------- | --------------- |
| `large-observation-array.json`      | PARSE_OBSERVATION_ARRAY performance      | 10,000 obs      | JSON            |
| `large-system-hierarchy.json`       | TRAVERSE_HIERARCHY performance           | 100 nodes       | JSON            |
| `large-feature-collection.json`     | FILTER_SPATIAL performance               | 10,000 features | GeoJSON         |
| `binary-mixed-types.base64`         | PARSE_SWE_BINARY mixed data types        | 1KB             | Base64          |
| `observation-with-constraints.json` | VALIDATE_OBSERVATIONS constraint testing | 100 obs         | JSON            |
| `command-with-feasibility.json`     | VALIDATE_COMMANDS feasibility testing    | 50 commands     | JSON            |
| `swe-result-all-encodings/`         | PARSE_SWE_RESULT all 3 encodings         | ~5KB total      | JSON/CSV/Base64 |
| `temporal-observations.json`        | FILTER_TEMPORAL various time ranges      | 1,000 obs       | JSON            |
| `circular-reference-system.json`    | Error handling                           | Small           | JSON            |
| `anti-meridian-features.json`       | FILTER_SPATIAL dateline crossing         | 50 features     | GeoJSON         |

### 5.3 Fixture Loading Pattern

```typescript
import { promises as fs } from 'fs';
import path from 'path';

async function loadFixture<T>(relativePath: string): Promise<T> {
  const fixturePath = path.resolve(
    __dirname,
    '../../../fixtures',
    relativePath
  );
  const content = await fs.readFile(fixturePath, 'utf-8');
  return JSON.parse(content) as T;
}

// Usage
const sensorml = await loadFixture<SensorML>(
  'sensorml/physical-system-valid.json'
);
```

---

## 6. Integration Testing Patterns

### 6.1 Parser Integration Tests

**Purpose:** Verify worker message types integrate correctly with format parsers.

**Test File:** `src/worker/parser-integration.spec.ts` (~200-300 lines)

#### Test Scenarios (12 scenarios)

**SensorML Parser Integration (4 tests):**

1. **PARSE_SENSORML_3 → SensorML Parser:** Worker invokes parser correctly
2. **Parser Output Format:** Worker returns parsed system in expected format
3. **Parser Error Propagation:** Parser error surfaced in worker response
4. **Lazy Parsing Option:** skipSWEParsing option passed to parser

**SWE Common Parser Integration (5 tests):** 5. **PARSE_SWE_RESULT (JSON) → Parser:** JSON encoding parsed correctly 6. **PARSE_SWE_RESULT (Text) → Parser:** Text encoding with custom separators 7. **PARSE_SWE_RESULT (Binary) → Parser:** Binary decoding integrated 8. **PARSE_SWE_BINARY → Binary Decoder:** Direct binary decoding 9. **Schema Validation Integration:** Parser validates against schema

**GeoJSON Parser Integration (3 tests):** 10. **FILTER_SPATIAL → GeoJSON Parser:** Geometry intersection uses GeoJSON library 11. **CSAPI Property Extraction:** GeoJSON CSAPI properties preserved after filtering 12. **Feature Type Validation:** Only valid CSAPI feature types processed

**Test Pattern:**

```typescript
describe('Parser Integration', () => {
  it('PARSE_SENSORML_3 integrates with SensorML parser', async () => {
    // Arrange
    const sensormlJson = await loadFixture(
      'sensorml/physical-system-valid.json'
    );

    // Act - Call via worker
    const result = await parseSensorML3Worker({ sensormlJson });

    // Assert - Verify parser was invoked correctly
    expect(result.system).toHaveProperty('uid');
    expect(result.system.components).toBeInstanceOf(Array);

    // Act - Call parser directly
    const directResult = parseSensorML(sensormlJson);

    // Assert - Results should match
    expect(result.system).toEqual(directResult);
  });
});
```

### 6.2 Fallback Behavior Tests

**Purpose:** Verify fallback mechanism provides identical results to worker mode.

**Test File:** `src/worker-fallback/csapi-worker-fallback.spec.ts` (~150-200 lines)

#### Test Scenarios (9 scenarios)

**Fallback Equivalence (9 tests - one per message type):**

1. **PARSE_SENSORML_3 Fallback:** Same result with/without worker
2. **PARSE_SWE_RESULT Fallback:** Same parsed observations
3. **PARSE_SWE_BINARY Fallback:** Same decoded values
4. **VALIDATE_OBSERVATIONS Fallback:** Same validation errors
5. **VALIDATE_COMMANDS Fallback:** Same command validation
6. **PARSE_OBSERVATION_ARRAY Fallback:** Same parsed array
7. **TRAVERSE_HIERARCHY Fallback:** Same hierarchy tree
8. **FILTER_SPATIAL Fallback:** Same filtered features
9. **FILTER_TEMPORAL Fallback:** Same filtered observations

**Test Pattern:**

```typescript
describe('CSAPI Worker Fallback', () => {
  // Test with worker
  describe('With Worker', () => {
    it('parses SensorML 3.0', async () => {
      const result = await parseSensorML3(sensormlJson);
      expect(result.system.uid).toBe('system-123');
    });
  });

  // Test with fallback
  describe('Fallback Mode', () => {
    beforeAll(() => {
      enableFallbackWithoutWorker();
    });

    it('parses SensorML 3.0 with identical result', async () => {
      const result = await parseSensorML3(sensormlJson);
      expect(result.system.uid).toBe('system-123');
    });
  });
});
```

### 6.3 Concurrent Request Handling

> **📝 Phase 2F L1 Note:** Concurrent request handling is inherent to the upstream worker infrastructure (`sendTaskRequest`/`addTaskHandler`), not CSAPI-specific. Before implementing these tests, verify whether `src/worker/worker.spec.ts` already covers concurrent message handling. If upstream tests exist, CSAPI inherits that behavior and these tests add limited additional value.

**Purpose:** Verify worker handles multiple simultaneous requests correctly.

**Test File:** `src/worker/concurrent-requests.spec.ts` (~100-150 lines)

#### Test Scenarios (6 scenarios)

1. **Multiple Same Message Type:** 10 PARSE_SENSORML_3 requests simultaneously → All resolve correctly
2. **Mixed Message Types:** 3 different message types concurrently → Correct responses for each
3. **Request ID Uniqueness:** Verify no request ID collisions across concurrent requests
4. **Response Ordering:** Responses match requests (not FIFO necessarily but correct pairing)
5. **Error in One Request:** One request fails, others succeed → Independent execution
6. **Worker Termination During Requests:** Terminate worker mid-processing → Pending requests rejected

**Test Pattern:**

```typescript
it('handles 10 concurrent parse requests', async () => {
  // Arrange
  const sensormlDocs = await Promise.all([
    loadFixture('sensorml/system-1.json'),
    loadFixture('sensorml/system-2.json'),
    // ... 8 more
  ]);

  // Act - Send all requests simultaneously
  const promises = sensormlDocs.map((doc) =>
    parseSensorML3({ sensormlJson: doc })
  );
  const results = await Promise.all(promises);

  // Assert - All 10 resolved
  expect(results).toHaveLength(10);

  // Assert - Each has unique system ID
  const uids = results.map((r) => r.system.uid);
  const uniqueUids = new Set(uids);
  expect(uniqueUids.size).toBe(10);
});
```

---

## 7. Performance Testing

> **⚠️ OUT OF SCOPE — Performance testing is NOT in scope for this contribution project.**
> Upstream `ogc-client` has zero performance tests. This section is retained as **reference material only** for potential future use. Do not implement any performance test assertions. See [Doc 33](33-performance-efficiency-testing.md) for the full scope exclusion rationale. (Phase 2F H2 resolution)

### 7.1 Performance Thresholds

**Performance Test Goals:**

- Ensure worker operations complete within acceptable time limits
- Prevent main thread blocking
- Validate worker provides performance benefit over main thread

**Thresholds by Operation:**

| Operation                 | Input Size       | Threshold | Rationale                         |
| ------------------------- | ---------------- | --------- | --------------------------------- |
| PARSE_SENSORML_3          | <10 components   | <10ms     | Small documents should be instant |
|                           | 10-50 components | <50ms     | Medium documents acceptable delay |
|                           | >50 components   | <200ms    | Large documents tolerable delay   |
| PARSE_SWE_RESULT (JSON)   | <100 obs         | <20ms     | Small datasets near-instant       |
|                           | 100-1,000 obs    | <100ms    | Medium datasets acceptable        |
|                           | >1,000 obs       | <500ms    | Large datasets tolerable          |
| PARSE_SWE_RESULT (Binary) | <1KB             | <5ms      | Binary decoding very fast         |
|                           | 1KB-100KB        | <50ms     | Medium blocks acceptable          |
|                           | >100KB           | <200ms    | Large blocks tolerable            |
| VALIDATE_OBSERVATIONS     | <1,000 obs       | <50ms     | Validation should be fast         |
|                           | >1,000 obs       | <200ms    | Large validation tolerable        |
| PARSE_OBSERVATION_ARRAY   | <1,000 obs       | <50ms     | Parsing should be fast            |
|                           | 1,000-10,000 obs | <500ms    | Medium arrays tolerable           |
|                           | >10,000 obs      | <2000ms   | Very large arrays acceptable      |
| TRAVERSE_HIERARCHY        | <10 nodes        | <20ms     | Small trees instant               |
|                           | 10-100 nodes     | <200ms    | Medium trees acceptable           |
|                           | >100 nodes       | <1000ms   | Large trees tolerable             |
| FILTER_SPATIAL            | <1,000 features  | <50ms     | Filtering should be fast          |
|                           | >1,000 features  | <200ms    | Large collections tolerable       |
| FILTER_TEMPORAL           | <1,000 items     | <50ms     | Temporal filtering fast           |
|                           | >1,000 items     | <200ms    | Large arrays tolerable            |

### 7.2 Performance Test Pattern

**Test File:** `src/worker/performance.spec.ts` (~200-250 lines)

```typescript
describe('Worker Performance', () => {
  it('PARSE_SENSORML_3 completes within threshold (large doc)', async () => {
    // Arrange
    const largeSensorML = await loadFixture(
      'sensorml/system-100-components.json'
    );
    const startTime = performance.now();

    // Act
    const result = await parseSensorML3({ sensormlJson: largeSensorML });
    const duration = performance.now() - startTime;

    // Assert
    expect(result.system.components).toHaveLength(100);
    expect(duration).toBeLessThan(200); // 200ms threshold

    // Log for analysis
    console.log(`Parse time (100 components): ${duration.toFixed(2)}ms`);
  });

  it('Worker is faster than main thread for large operations', async () => {
    // Arrange
    const largeData = await loadFixture(
      'swe-common/large-observation-array.json'
    );

    // Act - Measure worker time
    const workerStart = performance.now();
    await parseObservationArray({
      observations: largeData,
      schema: mockSchema,
    });
    const workerDuration = performance.now() - workerStart;

    // Act - Measure main thread time (fallback)
    enableFallbackWithoutWorker();
    const mainStart = performance.now();
    await parseObservationArray({
      observations: largeData,
      schema: mockSchema,
    });
    const mainDuration = performance.now() - mainStart;

    // Assert - Worker should be faster (or at least not slower)
    console.log(
      `Worker: ${workerDuration.toFixed(2)}ms, Main: ${mainDuration.toFixed(
        2
      )}ms`
    );
    expect(workerDuration).toBeLessThanOrEqual(mainDuration * 1.1); // Within 10% of main thread
  });
});
```

### 7.3 Performance Monitoring

**Metadata Collection:**

- All worker operations return `metadata.parseTime` or equivalent timing
- Tests can assert on these values
- Performance regression detection via CI

**Example:**

```typescript
it('records accurate parse time in metadata', async () => {
  const result = await parseSensorML3({ sensormlJson });

  expect(result.metadata.parseTime).toBeGreaterThan(0);
  expect(result.metadata.parseTime).toBeLessThan(200);
  expect(typeof result.metadata.parseTime).toBe('number');
});
```

---

## 8. Error Handling Testing

### 8.1 Error Types to Test

**Worker-Specific Errors:**

1. **Message Format Errors:** Invalid request structure, missing requestId
2. **Unknown Message Type:** taskName not recognized by worker
3. **Serialization Errors:** Non-serializable data in params/response
4. **Worker Initialization Errors:** Worker fails to load
5. **Timeout Errors:** Operation exceeds max time limit

**Operation-Specific Errors:** 6. **Parse Errors:** Invalid JSON, XML, or binary data 7. **Validation Errors:** Schema mismatch, constraint violations 8. **Resource Errors:** Missing resource, fetch failures 9. **Logic Errors:** Circular references, max depth exceeded, buffer overflow

### 8.2 Error Handling Pattern

**Test File:** `src/worker/error-handling.spec.ts` (~150-200 lines)

```typescript
describe('Worker Error Handling', () => {
  describe('Message Format Errors', () => {
    it('rejects request with missing params', async () => {
      await expect(
        sendTaskRequest('PARSE_SENSORML_3', getWorkerInstance(), null)
      ).rejects.toThrow('params is required');
    });

    it('rejects request with invalid message type', async () => {
      await expect(
        sendTaskRequest('UNKNOWN_TYPE', getWorkerInstance(), {})
      ).rejects.toThrow('Unknown task type');
    });
  });

  describe('Parse Errors', () => {
    it('propagates JSON parse error from SensorML parser', async () => {
      const invalidJson = '{ invalid json }';

      await expect(
        parseSensorML3({ sensormlJson: invalidJson })
      ).rejects.toThrow('Invalid JSON');
    });

    it('includes error context in rejection', async () => {
      try {
        await parseSensorML3({ sensormlJson: invalidJson });
        fail('Should have thrown');
      } catch (error) {
        expect(error).toHaveProperty('message');
        expect(error).toHaveProperty('taskName', 'PARSE_SENSORML_3');
      }
    });
  });

  describe('Validation Errors', () => {
    it('returns validation errors in response (not rejection)', async () => {
      const invalidObs = [{ missingField: true }];

      const result = await validateObservations({
        observations: invalidObs,
        schema: mockSchema,
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].type).toBe('missing');
    });
  });
});
```

### 8.3 Error Serialization

**Challenge:** Error objects don't serialize across worker boundary.

**Solution:** Use `encodeError`/`decodeError` from `shared/errors.ts`

**Test Pattern:**

```typescript
it('serializes and deserializes custom errors', async () => {
  const customError = new ValidationError('Field "uid" is required', {
    field: 'uid',
    rule: 'required',
  });

  // Encode for worker message
  const encoded = encodeError(customError);
  expect(encoded).toHaveProperty('message');
  expect(encoded).toHaveProperty('field', 'uid');

  // Simulate worker response with error
  const response: WorkerResponse = {
    requestId: 123,
    error: encoded,
  };

  // Decode in main thread
  const decoded = decodeError(response.error);
  expect(decoded).toBeInstanceOf(ValidationError);
  expect(decoded.message).toBe('Field "uid" is required');
});
```

---

## 9. Test Organization

### 9.1 Directory Structure

```
src/
├── worker/
│   ├── worker.ts                          # Worker-side handlers
│   ├── utils.ts                           # Message passing utilities
│   ├── index.ts                           # Main-thread API
│   ├── worker.spec.ts                     # (Existing WMS/WFS/WMTS tests)
│   │
│   ├── csapi-worker.ts                    # NEW: CSAPI message handlers
│   ├── csapi-worker.spec.ts               # NEW: CSAPI message type tests
│   │
│   ├── sensorml-worker.spec.ts            # NEW: PARSE_SENSORML_3 tests (180-200 lines)
│   ├── swe-result-worker.spec.ts          # NEW: PARSE_SWE_RESULT tests (200-220 lines)
│   ├── swe-binary-worker.spec.ts          # NEW: PARSE_SWE_BINARY tests (180-200 lines)
│   ├── validate-observations-worker.spec.ts  # NEW: VALIDATE_OBSERVATIONS tests (180-200 lines)
│   ├── validate-commands-worker.spec.ts   # NEW: VALIDATE_COMMANDS tests (180-200 lines)
│   ├── parse-observations-worker.spec.ts  # NEW: PARSE_OBSERVATION_ARRAY tests (180-200 lines)
│   ├── traverse-hierarchy-worker.spec.ts  # NEW: TRAVERSE_HIERARCHY tests (150-180 lines)
│   ├── filter-spatial-worker.spec.ts      # NEW: FILTER_SPATIAL tests (150-180 lines)
│   ├── filter-temporal-worker.spec.ts     # NEW: FILTER_TEMPORAL tests (150-180 lines)
│   │
│   ├── parser-integration.spec.ts         # NEW: Parser integration tests (200-300 lines)
│   ├── concurrent-requests.spec.ts        # NEW: Concurrent request tests (100-150 lines)
│   ├── error-handling.spec.ts             # NEW: Error handling tests (150-200 lines)
│   └── performance.spec.ts                # NEW: Performance tests (200-250 lines)
│
├── worker-fallback/
│   ├── worker-fallback.spec.ts            # (Existing WMS/WFS fallback tests)
│   └── csapi-worker-fallback.spec.ts      # NEW: CSAPI fallback tests (150-200 lines)
│
└── [parsers have their own unit tests per Sections 9, 10, 11]
```

### 9.2 File Naming Conventions

**Pattern:** `<operation>-worker.spec.ts` for message type tests

**Examples:**

- `sensorml-worker.spec.ts` - PARSE_SENSORML_3 message type
- `swe-result-worker.spec.ts` - PARSE_SWE_RESULT message type
- `validate-observations-worker.spec.ts` - VALIDATE_OBSERVATIONS message type

**Shared Tests:**

- `parser-integration.spec.ts` - Parser integration across all message types
- `csapi-worker-fallback.spec.ts` - Fallback equivalence for all message types
- `concurrent-requests.spec.ts` - Concurrency testing
- `error-handling.spec.ts` - Error scenarios across message types
- `performance.spec.ts` - Performance benchmarks

### 9.3 Test Line Count Summary

| Test File                              | Scenarios | Lines           | Type         |
| -------------------------------------- | --------- | --------------- | ------------ |
| `sensorml-worker.spec.ts`              | 18        | 180-200         | Message Type |
| `swe-result-worker.spec.ts`            | 23        | 200-220         | Message Type |
| `swe-binary-worker.spec.ts`            | 15        | 180-200         | Message Type |
| `validate-observations-worker.spec.ts` | 15        | 180-200         | Message Type |
| `validate-commands-worker.spec.ts`     | 15        | 180-200         | Message Type |
| `parse-observations-worker.spec.ts`    | 15        | 180-200         | Message Type |
| `traverse-hierarchy-worker.spec.ts`    | 12        | 150-180         | Message Type |
| `filter-spatial-worker.spec.ts`        | 13        | 150-180         | Message Type |
| `filter-temporal-worker.spec.ts`       | 13        | 150-180         | Message Type |
| **Subtotal (Message Types)**           | **139**   | **1,510-1,760** |              |
| `parser-integration.spec.ts`           | 12        | 200-300         | Integration  |
| `csapi-worker-fallback.spec.ts`        | 9         | 150-200         | Integration  |
| `concurrent-requests.spec.ts`          | 6         | 100-150         | Integration  |
| `error-handling.spec.ts`               | ~15       | 150-200         | Integration  |
| `performance.spec.ts`                  | ~20       | 200-250         | Integration  |
| **Subtotal (Integration)**             | **62**    | **800-1,100**   |              |
| **GRAND TOTAL**                        | **201**   | **2,310-2,860** |              |

---

## 10. Implementation Estimates

### 10.1 Test Implementation Effort

**Per Message Type (9 types):**

- Test design: 30 minutes
- Test implementation: 2-3 hours
- Fixture preparation: 30 minutes
- Test debugging: 1 hour
- **Total per type:** 4-5 hours

**Total for 9 Message Types:** 36-45 hours

**Integration Tests:**

- Parser integration: 3-4 hours
- Fallback tests: 2-3 hours
- Concurrent requests: 1-2 hours
- Error handling: 2-3 hours
- Performance tests: 3-4 hours
- **Total integration:** 11-16 hours

**TOTAL TEST IMPLEMENTATION:** 47-61 hours (~6-8 days)

### 10.2 Worker Implementation Effort (Reference)

**Per Message Type:**

- Handler implementation: 1-2 hours
- Parser integration: 1 hour
- Error handling: 30 minutes
- **Total per type:** 2.5-3.5 hours

**Total for 9 Message Types:** 22.5-31.5 hours (~3-4 days)

**Total Worker Extensions (Implementation + Tests):** 69.5-92.5 hours (~9-12 days)

### 10.3 Critical Path Dependencies

**Implementation Order:**

1. **Phase 1:** Format parser workers (PARSE_SENSORML_3, PARSE_SWE_RESULT, PARSE_SWE_BINARY) - 12-15 hours
   - Depends on: SensorML parser (Section 9), SWE Common parser (Section 10)
2. **Phase 2:** Validation workers (VALIDATE_OBSERVATIONS, VALIDATE_COMMANDS) - 8-10 hours
   - Depends on: Phase 1 parsers
3. **Phase 3:** Query workers (PARSE*OBSERVATION_ARRAY, TRAVERSE_HIERARCHY, FILTER*\*) - 12-15 hours
   - Depends on: Phase 1 parsers, Phase 2 validators
4. **Phase 4:** Integration tests (parser, fallback, concurrent, error, performance) - 11-16 hours
   - Depends on: All Phase 1-3 workers implemented

---

## 11. Success Criteria

### 11.1 Functional Requirements ✅

- [ ] All 9 worker message types have test scenarios
- [ ] Each message type has 10-23 test scenarios (139 total across all types)
- [ ] All test scenarios include:
  - [ ] Happy path (valid input → correct output)
  - [ ] Error handling (invalid input → appropriate error)
  - [ ] Performance checks (large input → acceptable time)
- [ ] Integration tests verify:
  - [ ] Parser integration (worker calls parser correctly)
  - [ ] Fallback equivalence (with/without worker same result)
  - [ ] Concurrent handling (multiple requests don't interfere)
  - [ ] Error propagation (errors surfaced correctly)

### 11.2 Test Coverage Requirements ✅

- [ ] 100% message type coverage (all 9 types tested)
- [ ] 100% parser integration coverage (SensorML, SWE Common, GeoJSON CSAPI)
- [ ] 100% fallback mechanism coverage
- [ ] > 80% code coverage for worker utilities (utils.ts)
- [ ] All error conditions tested (9 error types)

### 11.3 Test Quality Requirements ✅

- [ ] Tests follow existing patterns (Section 1, 2 analysis)
- [ ] Async tests use async/await pattern
- [ ] Error tests use `rejects.toThrow()` matcher
- [ ] Performance tests include threshold assertions
- [ ] Fixtures reused from Sections 9, 10, 11 where possible
- [ ] New fixtures documented in Section 15
- [ ] Test files organized per Section 19 structure

### 11.4 Documentation Requirements ✅

- [ ] Each message type has JSDoc with:
  - [ ] Purpose description
  - [ ] Input parameter specification
  - [ ] Output format specification
  - [ ] Error conditions listed
  - [ ] Performance characteristics documented
- [ ] Test files have descriptive test names
- [ ] Integration tests have setup/teardown documented
- [ ] Performance thresholds justified in comments

---

## 12. Risk Assessment

### 12.1 Testing Challenges

**Risk 1: Worker Testing Complexity**

- **Description:** Testing Web Workers in Jest requires mocking or fallback mode
- **Impact:** Tests may not catch worker-specific issues (thread safety, serialization)
- **Mitigation:** Use fallback mode for logic testing, add worker-specific integration tests, use real worker in CI

**Risk 2: Async Race Conditions**

- **Description:** Concurrent request tests may have timing-dependent failures
- **Impact:** Flaky tests, false negatives
- **Mitigation:** Use deterministic async patterns, avoid setTimeout, use jest.runAllTimers()

**Risk 3: Performance Test Variability**

- **Description:** Performance thresholds may vary by machine, CI environment
- **Impact:** Tests fail on slower hardware
- **Mitigation:** Set generous thresholds (80th percentile), log times for analysis, skip performance tests in slow environments

**Risk 4: Fixture Maintenance**

- **Description:** Large fixtures (10,000 observations) may become outdated or bloated
- **Impact:** Test slowness, fixture repo size
- **Mitigation:** Generate large fixtures programmatically in tests, keep committed fixtures small

**Risk 5: Parser Integration Coupling**

- **Description:** Worker tests depend on parser implementations (Sections 9, 10, 11)
- **Impact:** Parser changes break worker tests
- **Mitigation:** Use parser unit tests as source of truth, worker tests focus on message passing, mock parsers where appropriate

### 12.2 Implementation Challenges

**Risk 6: Error Serialization Edge Cases**

- **Description:** Some error types may not serialize correctly across worker boundary
- **Impact:** Error information loss, unhelpful error messages
- **Mitigation:** Test error serialization explicitly, use `encodeError`/`decodeError`, document serializable error types

**Risk 7: Worker Lifecycle Management**

- **Description:** Worker creation/termination may have race conditions
- **Impact:** Memory leaks, resource exhaustion
- **Mitigation:** Test worker termination, implement worker pooling, monitor resource usage

**Risk 8: Fallback Performance Degradation**

- **Description:** Fallback mode runs on main thread, may block UI
- **Impact:** Poor UX in non-worker environments
- **Mitigation:** Document fallback limitations, recommend worker-enabled environments, test performance in both modes

---

## 13. Integration with Test Plan

### 13.1 Relationship to Other Sections

**Dependencies (Input from):**

- **Section 1:** Upstream test patterns (async, fixtures, error handling) → Applied to worker tests
- **Section 2:** Consistent test structure (describe blocks, mocking) → Worker test templates
- **Section 9:** SensorML parser tests → Parser integration tests reference these
- **Section 10:** SWE Common parser tests → PARSE_SWE_RESULT/PARSE_SWE_BINARY integration
- **Section 11:** GeoJSON parser tests → FILTER_SPATIAL integration

**Blocks (Output to):**

- **Section 19:** Test organization → Worker test files added to directory structure
- **ROADMAP Phase 4:** Worker implementation → Test scenarios guide implementation

### 13.2 Test Execution Strategy

**Unit Tests (per message type):**

- Run independently
- Fast execution (<1 second per test file)
- No external dependencies

**Integration Tests:**

- Run after unit tests
- May require parser implementations
- Slower execution (1-5 seconds per test file)

**Performance Tests:**

- Run separately (not in CI by default)
- Optional for local development
- Required before release

**Fallback Tests:**

- Run in both worker and fallback modes
- Verify equivalence
- Critical for Node.js compatibility

---

## 14. References

### 14.1 Implementation Documents

- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) - Worker Extensions section (lines 2929-3050)
- [ROADMAP](../../../planning/ROADMAP.md) - Phase 4: Worker Extensions and Tests (lines 535-600)

### 14.2 Testing Research

- [Section 1: EDR Test Blueprint](01-edr-test-blueprint.md) - Async testing patterns, fixture loading
- [Section 2: Upstream Test Consistency](02-upstream-test-consistency.md) - Jest patterns, mocking strategies
- [Section 9: SensorML Testing Requirements](09-sensorml-testing-requirements.md) - PARSE_SENSORML_3 parser integration
- [Section 10: SWE Common Testing Requirements](10-swe-common-testing-requirements.md) - PARSE_SWE_RESULT/PARSE_SWE_BINARY parser integration
- [Section 11: GeoJSON CSAPI Testing Requirements](11-geojson-csapi-testing-requirements.md) - FILTER_SPATIAL parser integration
- [Section 15: Fixture Sourcing and Organization](15-fixture-sourcing-organization.md) - Fixture requirements and organization

### 14.3 Specifications

- **OGC SensorML 3.0:** https://docs.ogc.org/is/23-000/23-000.html
- **OGC SWE Common 3.0:** https://docs.ogc.org/is/24-014/24-014.html
- **OGC API - Connected Systems Part 1:** https://docs.ogc.org/is/23-001/23-001.html
- **OGC API - Connected Systems Part 2:** https://docs.ogc.org/is/23-002/23-002.html

### 14.4 Testing Tools

- **Jest:** https://jestjs.io/ - Test framework
- **Jest Manual Mocks:** https://jestjs.io/docs/manual-mocks - Worker mocking patterns
- **Web Workers API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API - Worker specification

---

## 15. Next Steps

### 15.1 Immediate Actions

1. **Fixture Preparation** (Section 15 implementation):

   - Generate 10 new worker-specific fixtures
   - Validate fixtures against schemas
   - Commit fixtures to repository

2. **Test File Setup** (ROADMAP Phase 4):

   - Create 13 new test files per directory structure
   - Copy test template to each file
   - Import fixtures and utilities

3. **Message Type Implementation** (ROADMAP Phase 4, Task 1):

   - Implement 9 CSAPI message handlers in `worker/csapi-worker.ts`
   - Add handlers to `worker/worker.ts`
   - Export APIs in `worker/index.ts`

4. **Test Implementation** (ROADMAP Phase 4, Task 1):
   - Implement tests per message type (139 scenarios)
   - Implement integration tests (62 scenarios)
   - Run tests, debug failures

### 15.2 Validation Checklist

Before marking Section 16 complete:

- [ ] All 9 message types documented with test scenarios
- [ ] Test structure templates provided
- [ ] Fixture requirements specified
- [ ] Integration patterns defined
- [ ] Performance thresholds established
- [ ] Error handling strategies documented
- [ ] Implementation estimates calculated
- [ ] Success criteria defined
- [ ] Deliverable reviewed and approved

### 15.3 Post-Implementation

After ROADMAP Phase 4 completes:

- [ ] All tests passing (201 scenarios)
- [ ] Test coverage >80% achieved
- [ ] Performance thresholds validated
- [ ] Fallback equivalence verified
- [ ] CI integration configured
- [ ] Documentation updated with actual results

---

**Document Version:** 1.0  
**Last Updated:** February 6, 2026  
**Status:** Research Complete - Ready for Implementation
