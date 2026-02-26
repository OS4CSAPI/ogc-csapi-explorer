# Section 30: Bulk Operations Testing Strategy

> ⚠️ **REVIEW NOTICE — HIGH (H4, H5): Tests Assert Fixture Response Data, Not Client Logic**
>
> **Phase 2E Review | Issues: H4, H5, M8 | Anti-Patterns: AP1, AP4**
>
> This document is ~40% client-oriented. It defines substantial client-side code in Section 6 (auto-chunking, fallback-to-sequential, `BulkCreateResult<T>` construction, progress callbacks) but the test scenarios in Section 4 don't test any of it. Instead, Section 4 asserts fixture response data: `response.data.items`, `obs.id`, `obs.result`, `cmd.parameters.action`. These would pass even if the client did no transformation.
>
> **What's usable:** Client library design (Section 6) — auto-chunking, fallback-to-sequential, `BulkCreateResult<T>`, progress callbacks. Error handling strategy (Section 2.3, 3, 9). Specification analysis (Sections 1-2).
>
> **What must be rewritten:** Section 4 test scenarios must be reframed to test the client code from Section 6: feed fixture through mocked `globalThis.fetch` → call `createObservationsBulk()` → assert client outputs (`BulkCreateResult.created`, `.failed`, `.partial`, `onProgress` callback invocations, auto-chunking splits).
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

**Research Plan:** [Research Plan 30: Bulk Operations Testing Strategy](../research-plans/30-bulk-operations-testing.md)

**Research Questions:** 6 core questions about bulk observation creation, bulk command creation, request size limits, partial success/failure, error handling, and fixtures.

**Methodology:** 6-phase systematic analysis (Phase 1: Bulk Operation Specification Analysis → Phase 2: Error Handling Analysis → Phase 3: Upstream Bulk Testing Analysis → Phase 4: Test Scenario Design → Phase 5: Fixture Design → Phase 6: Synthesis)

**Research Time:** 90 minutes (1.5 hours) – February 6, 2026

**Primary Source(s):**

- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html)
- [Part 2 Requirements](../../requirements/csapi-part2-requirements.md)
- [CRUD Operations Requirements](../../requirements/csapi-crud-operations.md)
- [Implementation Guide](../../../planning/csapi-implementation-guide.md)

**Supporting Resources:**

- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (individual operations)
- Section 18: [Error Condition Testing Strategy](18-error-condition-testing-strategy.md) (error patterns)
- Section 27: [Schema-Driven Validation Testing](27-schema-driven-validation-testing.md) (bulk item validation)
- Section 33: Performance Testing (bulk performance)

**Document Purpose:** Testing strategy for bulk observation and command creation operations with transaction semantics, partial success/failure handling, and performance considerations for high-volume data ingestion.

---

## Executive Summary

This document defines comprehensive testing requirements for CSAPI bulk operations, specifically bulk observation and command creation. Bulk operations enable efficient high-volume data ingestion by allowing clients to POST arrays of items in a single request instead of making individual requests for each item.

### Key Findings

**Bulk Operation Endpoints (2 total):**

- **Observations:** `POST /datastreams/{id}/observations` (accepts array)
- **Commands:** `POST /controlstreams/{id}/commands` (accepts array)

**Request Structure:**

- Request body: JSON array of observation/command objects
- Each item validated against datastream/controlstream schema
- No explicit size limit in spec (implementation-dependent, typical max 10,000 items)

**Response Structure:**

- **Success:** 201 Created with array of created resource IDs or full resources
- **Partial failure:** Custom response with `created` and `failed` arrays
- **Complete failure:** 400 Bad Request with validation errors

**Transaction Semantics:**
CSAPI specification does **NOT** explicitly define transaction semantics. Based on OpenSensorHub implementation analysis:

- **Partial success is likely:** Valid items created, invalid items rejected
- **Best-effort processing:** Server attempts to create all items, reports failures
- **NOT all-or-nothing:** Entire request doesn't fail if some items are invalid

**Testing Priorities:**

- **CRITICAL:** All-valid bulk operations (observations, commands), schema validation for each item, size limits
- **HIGH:** Mixed valid/invalid items (partial success), error reporting structure, batch size performance
- **MEDIUM:** Empty array handling, single-item array, very large batches (1000+ items)

**Fixture Requirements:** ~30 fixtures

- Bulk request fixtures: ~12 fixtures (various sizes, valid/invalid mixes)
- Bulk response fixtures: ~10 fixtures (success, partial failure, complete failure)
- Performance test fixtures: ~8 fixtures (100, 500, 1000, 5000 items)

**Estimated Test Implementation:** 450-600 lines

- Bulk observations tests: 150-200 lines (8-10 tests)
- Bulk commands tests: 100-150 lines (6-8 tests)
- Mixed valid/invalid tests: 80-120 lines (4-6 tests)
- Size limit tests: 60-80 lines (3-4 tests)
- Performance tests: 60-80 lines (3-4 tests)

**Key Testing Challenges:**

1. **Undefined transaction semantics** - Spec doesn't mandate all-or-nothing vs partial success
2. **Implementation variance** - Different servers may handle failures differently
3. **Performance testing** - Need to test with realistic high-volume data (100-10,000 items)
4. **Schema validation** - Each item must be validated against datastream/controlstream schema
5. **Error reporting** - Need clear structure for reporting which items failed

### Highest Rejection Risk

Bulk operations testing is **MEDIUM-HIGH RISK** because:

- **Spec ambiguity** - Transaction semantics not explicitly defined in CSAPI Part 2
- **Implementation variance** - OpenSensorHub supports bulk, but other servers may not
- **Performance sensitivity** - Large batches can timeout or exceed memory limits
- **Schema complexity** - Each item must conform to schema (inherited from Section 27)

**Mitigation:** Test multiple batch sizes (10, 50, 100, 500, 1000), document fallback to sequential operations, test both all-valid and mixed valid/invalid scenarios.

---

## 1. Bulk Operation Specification

### 1.1 Bulk Operation Endpoints

| Endpoint                         | Method | Request Body                 | Response                             | Purpose                   |
| -------------------------------- | ------ | ---------------------------- | ------------------------------------ | ------------------------- |
| `/datastreams/{id}/observations` | POST   | Array of Observation objects | 201 Created (array of IDs/resources) | Bulk observation creation |
| `/controlstreams/{id}/commands`  | POST   | Array of Command objects     | 201 Created (array of IDs/resources) | Bulk command creation     |

**Key Characteristics:**

- **Array input:** Request body is JSON array (not single object)
- **Schema validation:** Each item validated against parent datastream/controlstream schema
- **Atomic validation:** Server validates all items before attempting creation
- **Partial success:** Valid items may be created even if some fail (implementation-dependent)

### 1.2 Bulk Observation Creation

**Endpoint:** `POST /datastreams/{datastreamId}/observations`

**Request Format:**

```http
POST /datastreams/ds-temp-123/observations HTTP/1.1
Content-Type: application/json

[
  {
    "phenomenonTime": "2024-01-01T00:00:00Z",
    "resultTime": "2024-01-01T00:00:01Z",
    "result": 23.5
  },
  {
    "phenomenonTime": "2024-01-01T01:00:00Z",
    "resultTime": "2024-01-01T01:00:01Z",
    "result": 24.1
  },
  {
    "phenomenonTime": "2024-01-01T02:00:00Z",
    "resultTime": "2024-01-01T02:00:01Z",
    "result": 24.8
  }
]
```

**Success Response (201 Created):**

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /datastreams/ds-temp-123/observations

{
  "items": [
    {"id": "obs-001", "phenomenonTime": "2024-01-01T00:00:00Z", "result": 23.5},
    {"id": "obs-002", "phenomenonTime": "2024-01-01T01:00:00Z", "result": 24.1},
    {"id": "obs-003", "phenomenonTime": "2024-01-01T02:00:00Z", "result": 24.8}
  ]
}
```

**Alternative Success Response (IDs only):**

```json
{
  "created": 3,
  "ids": ["obs-001", "obs-002", "obs-003"]
}
```

**Observation Properties:**

- `phenomenonTime` (required): ISO 8601 timestamp when observation was made
- `resultTime` (optional): ISO 8601 timestamp when result became available
- `result` (required): Observation value, structure defined by datastream schema
- `resultQuality` (optional): Quality indicators (accuracy, precision)
- `parameters` (optional): Additional metadata
- `featureOfInterest` (optional): Link to observed feature

### 1.3 Bulk Command Creation

**Endpoint:** `POST /controlstreams/{controlStreamId}/commands`

**Request Format:**

```http
POST /controlstreams/cs-camera-456/commands HTTP/1.1
Content-Type: application/json

[
  {
    "issueTime": "2024-01-01T00:00:00Z",
    "executionTime": "2024-01-01T00:00:05Z",
    "parameters": {"action": "capture", "resolution": "1920x1080"}
  },
  {
    "issueTime": "2024-01-01T00:00:10Z",
    "executionTime": "2024-01-01T00:00:15Z",
    "parameters": {"action": "capture", "resolution": "3840x2160"}
  }
]
```

**Success Response (201 Created):**

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /controlstreams/cs-camera-456/commands

{
  "items": [
    {"id": "cmd-001", "issueTime": "2024-01-01T00:00:00Z", "parameters": {...}},
    {"id": "cmd-002", "issueTime": "2024-01-01T00:00:10Z", "parameters": {...}}
  ]
}
```

**Command Properties:**

- `issueTime` (optional): ISO 8601 timestamp when command issued (defaults to now)
- `executionTime` (optional): ISO 8601 timestamp when command should execute
- `parameters` (required): Command parameters, structure defined by controlstream schema
- `sender` (optional): Entity issuing command
- `featureOfInterest` (optional): Target feature

### 1.4 Request Size Limits

**No Explicit Limit in Specification:**
CSAPI Part 2 does not define maximum number of items in bulk request.

**Implementation Limits (OpenSensorHub):**

- **Recommended batch size:** 100-1,000 items per request
- **Maximum supported:** 10,000 items per request
- **Practical limits:** HTTP payload size (typically 1-10 MB), server memory, timeout

**Client Library Strategy:**

- Accept any batch size from user
- Automatically chunk large batches into smaller requests (e.g., 1,000 items each)
- Add small delays (100ms) between batches to avoid overloading server
- Provide progress callback for large batches

---

## 2. Transaction Semantics

### 2.1 Transaction Semantics Ambiguity

**CSAPI Specification Position:**
CSAPI Part 2 specification does **NOT** explicitly define transaction semantics for bulk operations. Three possible approaches:

**Option 1: All-or-Nothing (Atomic)**

- If ANY item fails validation → entire request rejected (400 Bad Request)
- No items created
- Client must fix all errors and retry entire batch
- **Pros:** Maintains consistency, simplifies error handling
- **Cons:** Inefficient if only 1 item invalid out of 1,000

**Option 2: Partial Success (Best-Effort)**

- Server validates all items
- Valid items are created
- Invalid items reported in response
- **Pros:** Efficient for large batches, some progress even with errors
- **Cons:** Complex error handling, client must track partial success

**Option 3: Sequential Processing**

- Server processes items one-by-one
- Stops at first failure
- Returns created items + error for first failure
- **Pros:** Predictable, easy to retry from failure point
- **Cons:** Inefficient, defeats purpose of bulk operation

### 2.2 OpenSensorHub Implementation

Based on OpenSensorHub analysis, the likely implementation is **Partial Success (Best-Effort)**:

**Partial Success Response:**

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/json

{
  "created": ["obs-001", "obs-003", "obs-004"],
  "failed": [
    {
      "index": 1,
      "error": "Schema validation failed: result must be numeric, got 'invalid'"
    },
    {
      "index": 4,
      "error": "Missing required property: phenomenonTime"
    }
  ]
}
```

**Alternative: Mixed Status in Array:**

```json
{
  "items": [
    { "id": "obs-001", "status": "created" },
    { "index": 1, "status": "failed", "error": "Schema validation failed" },
    { "id": "obs-003", "status": "created" },
    { "id": "obs-004", "status": "created" },
    { "index": 4, "status": "failed", "error": "Missing required property" }
  ]
}
```

### 2.3 Client Library Error Handling Strategy

**Client must handle three scenarios:**

**Scenario 1: Complete Success (201 Created)**

- All items created successfully
- Response contains array of created resources or IDs

**Scenario 2: Partial Success (207 Multi-Status or custom)**

- Some items created, some failed
- Client must:
  - Extract successfully created IDs
  - Identify failed items by index or error message
  - Optionally retry failed items

**Scenario 3: Complete Failure (400 Bad Request)**

- No items created
- Response contains validation errors for all items
- Client must fix errors and retry entire batch

**Recommended Client API:**

```typescript
interface BulkCreateResult<T> {
  created: T[]; // Successfully created items
  failed: BulkError[]; // Failed items with details
  partial: boolean; // true if some items failed
}

interface BulkError {
  index: number; // Index in original array
  item: any; // Original item data
  error: string; // Error message
  statusCode?: number; // HTTP status if available
}
```

---

## 3. Error Handling and Validation

### 3.1 Item-Level Validation

**Each Item Validated Independently:**

- Validated against parent datastream/controlstream schema
- Same validation rules as single-item POST
- Schema validation errors reported per-item

**Common Validation Errors:**

- **Schema mismatch:** Result doesn't match datastream schema
- **Missing required property:** `phenomenonTime`, `result` (observations), `parameters` (commands)
- **Invalid timestamp format:** Non-ISO 8601 timestamps
- **Invalid result type:** String when schema expects number
- **Invalid parameters:** Command parameters don't match schema

### 3.2 Error Response Structure

**Option 1: 400 Bad Request (All Items Invalid)**

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "code": "ValidationError",
  "description": "Bulk operation validation failed",
  "errors": [
    {
      "index": 0,
      "property": "result",
      "message": "Expected number, got string"
    },
    {
      "index": 2,
      "property": "phenomenonTime",
      "message": "Required property missing"
    }
  ]
}
```

**Option 2: 207 Multi-Status (Partial Success)**

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/json

{
  "created": 8,
  "failed": 2,
  "items": [
    {"id": "obs-001", "status": "created"},
    {"index": 1, "status": "failed", "error": "Schema validation failed"},
    // ... more items
  ]
}
```

**Option 3: 201 Created with Failed Items in Body**

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "created": ["obs-001", "obs-002", "obs-004"],
  "failed": [
    {"index": 1, "error": "Invalid result type"},
    {"index": 3, "error": "Missing phenomenonTime"}
  ]
}
```

### 3.3 Schema Validation Errors

**Example: DataStream Schema**

```json
{
  "type": "DataRecord",
  "fields": [
    {
      "name": "phenomenonTime",
      "type": "Time",
      "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime"
    },
    {
      "name": "result",
      "type": "Quantity",
      "definition": "http://example.org/temp",
      "uom": { "code": "Cel" }
    }
  ]
}
```

**Invalid Observation (Wrong Type):**

```json
{
  "phenomenonTime": "2024-01-01T00:00:00Z",
  "result": "twenty-three" // ❌ Should be number
}
```

**Error Response:**

```json
{
  "index": 2,
  "property": "result",
  "message": "Expected Quantity (number), got String",
  "schema": "http://example.org/temp"
}
```

---

## 4. Bulk Operation Test Scenarios

### 4.1 All-Valid Bulk Observations Tests (8 tests)

> ⚠️ **REVIEW NOTICE (H4): Tests Assert Fixture Response Data Directly**
>
> These tests assert fixture content: `response.data.items.forEach((obs, i) => { expect(obs.id).toMatch(/^obs-/); expect(obs.result).toBe(20 + i * 0.5); })`. This validates the fixture returns expected data — not that the client transformed it correctly. Tests should instead verify `BulkCreateResult<T>` construction from raw responses, that `created[]` contains correctly typed objects, and that `totalItems` reflects the input count.
>
> The `response.ok` / `response.status` assertions also test the mock, not the client. See Section 6 for the actual client code these tests should exercise.

**Priority:** **CRITICAL**

| Test ID      | Scenario                 | Batch Size | Expected Behavior                              | Lines |
| ------------ | ------------------------ | ---------- | ---------------------------------------------- | ----- |
| BULK-OBS-001 | Small batch (10 items)   | 10         | 201 Created, 10 IDs returned                   | 20    |
| BULK-OBS-002 | Medium batch (100 items) | 100        | 201 Created, 100 IDs returned                  | 20    |
| BULK-OBS-003 | Large batch (1000 items) | 1000       | 201 Created, 1000 IDs returned                 | 25    |
| BULK-OBS-004 | Single item array        | 1          | 201 Created, 1 ID returned                     | 15    |
| BULK-OBS-005 | Empty array              | 0          | 400 Bad Request or 201 with 0 items            | 15    |
| BULK-OBS-006 | Varied result types      | 10         | All observations match schema                  | 20    |
| BULK-OBS-007 | With optional properties | 10         | All properties preserved (resultTime, quality) | 20    |
| BULK-OBS-008 | Sequential timestamps    | 100        | Observations ordered by phenomenonTime         | 20    |

**Test Implementation (~150-200 lines, 8 tests):**

```typescript
describe('Bulk Observation Creation - All Valid', () => {
  it('creates small batch (10 observations)', async () => {
    const observations = Array.from({ length: 10 }, (_, i) => ({
      phenomenonTime: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`,
      result: 20 + i * 0.5,
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(10);
    response.data.items.forEach((obs, i) => {
      expect(obs.id).toMatch(/^obs-/);
      expect(obs.result).toBe(20 + i * 0.5);
    });
  });

  it('creates medium batch (100 observations)', async () => {
    const observations = Array.from({ length: 100 }, (_, i) => ({
      phenomenonTime: `2024-01-01T${String(Math.floor(i / 60)).padStart(
        2,
        '0'
      )}:${String(i % 60).padStart(2, '0')}:00Z`,
      result: 20 + Math.random() * 10,
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(100);
  });

  it('creates large batch (1000 observations)', async () => {
    const observations = Array.from({ length: 1000 }, (_, i) => ({
      phenomenonTime: new Date(Date.UTC(2024, 0, 1, 0, i)).toISOString(),
      result: 20 + Math.sin(i * 0.1) * 5, // Sinusoidal pattern
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(1000);
    // Verify batch was chunked if necessary
  });

  it('creates single-item array', async () => {
    const observations = [
      {
        phenomenonTime: '2024-01-01T00:00:00Z',
        result: 23.5,
      },
    ];

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(1);
    expect(response.data.items[0].result).toBe(23.5);
  });

  it('handles empty array', async () => {
    const observations = [];

    // May return 400 Bad Request or 201 with 0 items (implementation-dependent)
    try {
      const response = await client.observations.createBulk(
        'ds-temp-123',
        observations
      );
      expect([201, 400]).toContain(response.status);
      if (response.status === 201) {
        expect(response.data.items).toHaveLength(0);
      }
    } catch (error) {
      expect(error.status).toBe(400);
    }
  });

  it('preserves varied result types', async () => {
    // Datastream schema: { temp: Quantity, humidity: Quantity }
    const observations = Array.from({ length: 10 }, (_, i) => ({
      phenomenonTime: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`,
      result: {
        temp: 20 + i * 0.5,
        humidity: 60 + i * 2,
      },
    }));

    const response = await client.observations.createBulk(
      'ds-multi-123',
      observations
    );

    expect(response.ok).toBe(true);
    response.data.items.forEach((obs, i) => {
      expect(obs.result.temp).toBeCloseTo(20 + i * 0.5);
      expect(obs.result.humidity).toBeCloseTo(60 + i * 2);
    });
  });

  it('preserves optional properties', async () => {
    const observations = Array.from({ length: 10 }, (_, i) => ({
      phenomenonTime: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`,
      resultTime: `2024-01-01T${String(i).padStart(2, '0')}:00:05Z`,
      result: 20 + i * 0.5,
      resultQuality: {
        accuracy: 0.1,
        precision: 0.05,
      },
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    response.data.items.forEach((obs, i) => {
      expect(obs.resultTime).toBe(
        `2024-01-01T${String(i).padStart(2, '0')}:00:05Z`
      );
      expect(obs.resultQuality.accuracy).toBe(0.1);
    });
  });

  it('handles sequential timestamps', async () => {
    const observations = Array.from({ length: 100 }, (_, i) => ({
      phenomenonTime: new Date(Date.UTC(2024, 0, 1, 0, i)).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    // Verify observations are ordered by phenomenonTime
    const times = response.data.items.map((obs) =>
      new Date(obs.phenomenonTime).getTime()
    );
    for (let i = 1; i < times.length; i++) {
      expect(times[i]).toBeGreaterThanOrEqual(times[i - 1]);
    }
  });
});
```

### 4.2 All-Valid Bulk Commands Tests (6 tests)

> ⚠️ **REVIEW NOTICE (H4): Same Fixture Content Assertion Pattern**
>
> Same issue as Section 4.1: tests assert `response.data.items`, `cmd.parameters.action`, `cmd.parameters.resolution` — all fixture content. Client tests should verify: `BulkCreateResult<Command>` construction, `.created[]` contains correctly typed command objects, `.totalItems` matches input.

**Priority:** HIGH

| Test ID      | Scenario                   | Batch Size | Expected Behavior             | Lines |
| ------------ | -------------------------- | ---------- | ----------------------------- | ----- |
| BULK-CMD-001 | Small batch (10 commands)  | 10         | 201 Created, 10 IDs returned  | 20    |
| BULK-CMD-002 | Medium batch (50 commands) | 50         | 201 Created, 50 IDs returned  | 20    |
| BULK-CMD-003 | Single command array       | 1          | 201 Created, 1 ID returned    | 15    |
| BULK-CMD-004 | Varied parameters          | 10         | All commands match schema     | 20    |
| BULK-CMD-005 | With executionTime         | 10         | All executionTimes preserved  | 20    |
| BULK-CMD-006 | Sequential issueTimes      | 50         | Commands ordered by issueTime | 20    |

**Test Implementation (~100-150 lines, 6 tests):**

```typescript
describe('Bulk Command Creation - All Valid', () => {
  it('creates small batch (10 commands)', async () => {
    const commands = Array.from({ length: 10 }, (_, i) => ({
      issueTime: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`,
      parameters: {
        action: 'capture',
        resolution: i % 2 === 0 ? '1920x1080' : '3840x2160',
      },
    }));

    const response = await client.commands.createBulk(
      'cs-camera-456',
      commands
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(10);
    response.data.items.forEach((cmd, i) => {
      expect(cmd.id).toMatch(/^cmd-/);
      expect(cmd.parameters.action).toBe('capture');
    });
  });

  it('creates medium batch (50 commands)', async () => {
    const commands = Array.from({ length: 50 }, (_, i) => ({
      issueTime: new Date(Date.UTC(2024, 0, 1, 0, i)).toISOString(),
      parameters: { sequence: i, action: 'capture' },
    }));

    const response = await client.commands.createBulk(
      'cs-camera-456',
      commands
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(50);
  });

  it('creates single command array', async () => {
    const commands = [
      {
        issueTime: '2024-01-01T00:00:00Z',
        parameters: { action: 'capture', resolution: '1920x1080' },
      },
    ];

    const response = await client.commands.createBulk(
      'cs-camera-456',
      commands
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(1);
  });

  it('preserves varied parameters', async () => {
    const commands = Array.from({ length: 10 }, (_, i) => ({
      issueTime: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`,
      parameters: {
        action: i % 3 === 0 ? 'capture' : i % 3 === 1 ? 'pan' : 'zoom',
        value: i * 10,
      },
    }));

    const response = await client.commands.createBulk(
      'cs-camera-456',
      commands
    );

    expect(response.ok).toBe(true);
    response.data.items.forEach((cmd, i) => {
      expect(cmd.parameters.value).toBe(i * 10);
    });
  });

  it('preserves executionTime', async () => {
    const commands = Array.from({ length: 10 }, (_, i) => ({
      issueTime: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`,
      executionTime: `2024-01-01T${String(i).padStart(2, '0')}:00:30Z`,
      parameters: { action: 'capture' },
    }));

    const response = await client.commands.createBulk(
      'cs-camera-456',
      commands
    );

    expect(response.ok).toBe(true);
    response.data.items.forEach((cmd, i) => {
      expect(cmd.executionTime).toBe(
        `2024-01-01T${String(i).padStart(2, '0')}:00:30Z`
      );
    });
  });

  it('handles sequential issueTimes', async () => {
    const commands = Array.from({ length: 50 }, (_, i) => ({
      issueTime: new Date(Date.UTC(2024, 0, 1, 0, i)).toISOString(),
      parameters: { sequence: i },
    }));

    const response = await client.commands.createBulk(
      'cs-camera-456',
      commands
    );

    expect(response.ok).toBe(true);
    // Verify commands are ordered by issueTime
    const times = response.data.items.map((cmd) =>
      new Date(cmd.issueTime).getTime()
    );
    for (let i = 1; i < times.length; i++) {
      expect(times[i]).toBeGreaterThanOrEqual(times[i - 1]);
    }
  });
});
```

### 4.3 Mixed Valid/Invalid Items Tests (6 tests)

**Priority:** HIGH

| Test ID      | Scenario                | Valid Items | Invalid Items       | Expected Behavior                           | Lines |
| ------------ | ----------------------- | ----------- | ------------------- | ------------------------------------------- | ----- |
| BULK-MIX-001 | Single invalid in batch | 9           | 1                   | 207 Multi-Status or 201 with failed array   | 25    |
| BULK-MIX-002 | Multiple invalid        | 7           | 3                   | Partial success, 3 errors reported          | 25    |
| BULK-MIX-003 | All invalid             | 0           | 10                  | 400 Bad Request, all errors reported        | 20    |
| BULK-MIX-004 | Invalid at start        | 8           | 2 (index 0,1)       | Partial success, errors at specific indices | 25    |
| BULK-MIX-005 | Invalid at end          | 8           | 2 (index 8,9)       | Partial success, errors at specific indices | 25    |
| BULK-MIX-006 | Scattered invalid       | 6           | 4 (indices 1,3,5,7) | Partial success, scattered errors           | 25    |

**Test Implementation (~80-120 lines, 6 tests):**

```typescript
describe('Bulk Operations - Mixed Valid/Invalid', () => {
  it('handles single invalid item in batch', async () => {
    const observations = [
      { phenomenonTime: '2024-01-01T00:00:00Z', result: 20.0 },
      { phenomenonTime: '2024-01-01T01:00:00Z', result: 21.0 },
      { phenomenonTime: '2024-01-01T02:00:00Z', result: 22.0 },
      { phenomenonTime: '2024-01-01T03:00:00Z', result: 'invalid' }, // ❌ Wrong type
      { phenomenonTime: '2024-01-01T04:00:00Z', result: 24.0 },
    ];

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    // May return 207 Multi-Status or 201 with failed array
    expect([201, 207]).toContain(response.status);
    expect(response.data.created).toHaveLength(4);
    expect(response.data.failed).toHaveLength(1);
    expect(response.data.failed[0].index).toBe(3);
    expect(response.data.failed[0].error).toMatch(/type|numeric|number/i);
  });

  it('handles multiple invalid items', async () => {
    const observations = [
      { phenomenonTime: '2024-01-01T00:00:00Z', result: 20.0 },
      { phenomenonTime: '2024-01-01T01:00:00Z', result: 'bad' }, // ❌
      { phenomenonTime: '2024-01-01T02:00:00Z', result: 22.0 },
      { phenomenonTime: 'invalid-time', result: 23.0 }, // ❌
      { phenomenonTime: '2024-01-01T04:00:00Z', result: 24.0 },
      { result: 25.0 }, // ❌ Missing phenomenonTime
    ];

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect([201, 207]).toContain(response.status);
    expect(response.data.created).toHaveLength(3);
    expect(response.data.failed).toHaveLength(3);

    const failedIndices = response.data.failed.map((f) => f.index);
    expect(failedIndices).toContain(1);
    expect(failedIndices).toContain(3);
    expect(failedIndices).toContain(5);
  });

  it('handles all invalid items', async () => {
    const observations = [
      { phenomenonTime: '2024-01-01T00:00:00Z', result: 'bad' },
      { phenomenonTime: 'invalid', result: 21.0 },
      { result: 22.0 }, // Missing phenomenonTime
    ];

    await expect(
      client.observations.createBulk('ds-temp-123', observations)
    ).rejects.toThrow(/400.*validation/i);
  });

  it('handles invalid items at start', async () => {
    const observations = [
      { phenomenonTime: 'invalid', result: 20.0 }, // ❌
      { result: 21.0 }, // ❌
      { phenomenonTime: '2024-01-01T02:00:00Z', result: 22.0 },
      { phenomenonTime: '2024-01-01T03:00:00Z', result: 23.0 },
    ];

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.data.created).toHaveLength(2);
    expect(response.data.failed).toHaveLength(2);
    expect(response.data.failed[0].index).toBe(0);
    expect(response.data.failed[1].index).toBe(1);
  });

  it('handles invalid items at end', async () => {
    const observations = [
      { phenomenonTime: '2024-01-01T00:00:00Z', result: 20.0 },
      { phenomenonTime: '2024-01-01T01:00:00Z', result: 21.0 },
      { phenomenonTime: '2024-01-01T02:00:00Z', result: 'bad' }, // ❌
      { result: 23.0 }, // ❌
    ];

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.data.created).toHaveLength(2);
    expect(response.data.failed).toHaveLength(2);
    expect(response.data.failed[0].index).toBe(2);
    expect(response.data.failed[1].index).toBe(3);
  });

  it('handles scattered invalid items', async () => {
    const observations = Array.from({ length: 10 }, (_, i) => ({
      phenomenonTime:
        i % 2 === 0
          ? `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`
          : 'invalid',
      result: i % 2 === 0 ? 20.0 + i : 'bad',
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.data.created).toHaveLength(5); // Indices 0, 2, 4, 6, 8
    expect(response.data.failed).toHaveLength(5); // Indices 1, 3, 5, 7, 9
  });
});
```

### 4.4 Size Limit Tests (4 tests)

**Priority:** MEDIUM

| Test ID       | Scenario                    | Batch Size | Expected Behavior                    | Lines |
| ------------- | --------------------------- | ---------- | ------------------------------------ | ----- |
| BULK-SIZE-001 | At recommended limit (1000) | 1000       | 201 Created, all items processed     | 20    |
| BULK-SIZE-002 | Above recommended (2000)    | 2000       | 201 Created, may be chunked          | 20    |
| BULK-SIZE-003 | Very large (10000)          | 10000      | 201 Created or 413 Payload Too Large | 20    |
| BULK-SIZE-004 | Exceeds HTTP limit (50000)  | 50000      | 413 Payload Too Large or timeout     | 15    |

**Test Implementation (~60-80 lines, 4 tests):**

```typescript
describe('Bulk Operations - Size Limits', () => {
  it('handles batch at recommended limit (1000 items)', async () => {
    const observations = Array.from({ length: 1000 }, (_, i) => ({
      phenomenonTime: new Date(Date.UTC(2024, 0, 1, 0, i)).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(1000);
  });

  it('handles batch above recommended limit (2000 items)', async () => {
    const observations = Array.from({ length: 2000 }, (_, i) => ({
      phenomenonTime: new Date(Date.UTC(2024, 0, 1, 0, i)).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );

    expect(response.ok).toBe(true);
    expect(response.status).toBe(201);
    expect(response.data.items).toHaveLength(2000);
    // Client may have chunked this into 2x 1000-item requests
  });

  it('handles very large batch (10000 items)', async () => {
    const observations = Array.from({ length: 10000 }, (_, i) => ({
      phenomenonTime: new Date(
        Date.UTC(2024, 0, 1, 0, Math.floor(i / 60), i % 60)
      ).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    try {
      const response = await client.observations.createBulk(
        'ds-temp-123',
        observations
      );
      expect(response.ok).toBe(true);
      expect(response.data.items).toHaveLength(10000);
    } catch (error) {
      // May fail with 413 Payload Too Large or timeout
      expect([413, 408, 504]).toContain(error.status);
    }
  });

  it('rejects batch exceeding HTTP limit (50000 items)', async () => {
    const observations = Array.from({ length: 50000 }, (_, i) => ({
      phenomenonTime: new Date(
        Date.UTC(
          2024,
          0,
          Math.floor(i / 1440) + 1,
          Math.floor((i % 1440) / 60),
          i % 60
        )
      ).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    // Should fail with 413 or timeout, or client should auto-chunk
    await expect(
      client.observations.createBulk('ds-temp-123', observations)
    ).rejects.toThrow();
  });
});
```

### 4.5 Performance Tests (4 tests)

> ⚠️ **REVIEW NOTICE (M8): Performance Tests Measure Server Response Timing**
>
> `expect(elapsed).toBeLessThan(500)` and `expect(memUsed).toBeLessThan(100 * 1024 * 1024)` are integration performance tests against server responses, not client unit tests. In a mocked-fetch test, timing measures the mock's latency (near-zero), not real performance. If client-side performance matters (e.g., auto-chunking overhead, memory allocation for 5000-item arrays), those should be tested separately with benchmarks, not as unit test assertions.

**Priority:** MEDIUM

| Test ID       | Scenario            | Batch Size | Expected Performance  | Lines |
| ------------- | ------------------- | ---------- | --------------------- | ----- |
| BULK-PERF-001 | Small batch timing  | 100        | < 500ms               | 20    |
| BULK-PERF-002 | Medium batch timing | 500        | < 2000ms              | 20    |
| BULK-PERF-003 | Large batch timing  | 1000       | < 5000ms              | 20    |
| BULK-PERF-004 | Memory usage        | 5000       | < 100MB client memory | 20    |

**Test Implementation (~60-80 lines, 4 tests):**

```typescript
describe('Bulk Operations - Performance', () => {
  it('processes small batch (100 items) quickly', async () => {
    const observations = Array.from({ length: 100 }, (_, i) => ({
      phenomenonTime: new Date(Date.UTC(2024, 0, 1, 0, i)).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    const start = Date.now();
    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );
    const elapsed = Date.now() - start;

    expect(response.ok).toBe(true);
    expect(elapsed).toBeLessThan(500); // < 500ms
  });

  it('processes medium batch (500 items) acceptably', async () => {
    const observations = Array.from({ length: 500 }, (_, i) => ({
      phenomenonTime: new Date(
        Date.UTC(2024, 0, 1, 0, Math.floor(i / 60), i % 60)
      ).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    const start = Date.now();
    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );
    const elapsed = Date.now() - start;

    expect(response.ok).toBe(true);
    expect(elapsed).toBeLessThan(2000); // < 2s
  });

  it('processes large batch (1000 items) within timeout', async () => {
    const observations = Array.from({ length: 1000 }, (_, i) => ({
      phenomenonTime: new Date(
        Date.UTC(2024, 0, 1, 0, Math.floor(i / 60), i % 60)
      ).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    const start = Date.now();
    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );
    const elapsed = Date.now() - start;

    expect(response.ok).toBe(true);
    expect(elapsed).toBeLessThan(5000); // < 5s
  });

  it('maintains reasonable memory usage for large batch', async () => {
    const observations = Array.from({ length: 5000 }, (_, i) => ({
      phenomenonTime: new Date(
        Date.UTC(
          2024,
          0,
          1,
          Math.floor(i / 1440),
          Math.floor((i % 1440) / 60),
          i % 60
        )
      ).toISOString(),
      result: 20 + Math.random() * 10,
    }));

    const memBefore = process.memoryUsage().heapUsed;
    const response = await client.observations.createBulk(
      'ds-temp-123',
      observations
    );
    const memAfter = process.memoryUsage().heapUsed;
    const memUsed = memAfter - memBefore;

    expect(response.ok).toBe(true);
    expect(memUsed).toBeLessThan(100 * 1024 * 1024); // < 100MB
  });
});
```

### 4.6 Test Scenario Summary

**Total Tests:** 28 tests  
**Total Lines:** 450-600 lines

| Test Category          | Test Count | Lines   | Priority     |
| ---------------------- | ---------- | ------- | ------------ |
| All-Valid Observations | 8          | 150-200 | **CRITICAL** |
| All-Valid Commands     | 6          | 100-150 | HIGH         |
| Mixed Valid/Invalid    | 6          | 80-120  | HIGH         |
| Size Limits            | 4          | 60-80   | MEDIUM       |
| Performance            | 4          | 60-80   | MEDIUM       |

---

## 5. Fixture Requirements

### 5.1 Bulk Request Fixtures (12 fixtures)

| Fixture ID                      | Type         | Size | Description                                    | Use Case                    |
| ------------------------------- | ------------ | ---- | ---------------------------------------------- | --------------------------- |
| **Valid Observation Batches**   |
| BULK-REQ-001                    | Observations | 10   | Small batch, all valid                         | Basic bulk creation         |
| BULK-REQ-002                    | Observations | 100  | Medium batch, all valid                        | Typical use case            |
| BULK-REQ-003                    | Observations | 1000 | Large batch, all valid                         | Performance testing         |
| BULK-REQ-004                    | Observations | 1    | Single-item array                              | Edge case                   |
| **Valid Command Batches**       |
| BULK-REQ-005                    | Commands     | 10   | Small batch, all valid                         | Basic bulk creation         |
| BULK-REQ-006                    | Commands     | 50   | Medium batch, all valid                        | Typical use case            |
| **Mixed Valid/Invalid Batches** |
| BULK-REQ-007                    | Observations | 10   | 9 valid, 1 invalid (index 3)                   | Single validation error     |
| BULK-REQ-008                    | Observations | 10   | 7 valid, 3 invalid (indices 1,3,5)             | Multiple validation errors  |
| BULK-REQ-009                    | Observations | 10   | All invalid                                    | Complete validation failure |
| **Edge Cases**                  |
| BULK-REQ-010                    | Observations | 0    | Empty array                                    | Boundary test               |
| BULK-REQ-011                    | Observations | 10   | With optional properties (resultTime, quality) | Full property set           |
| BULK-REQ-012                    | Commands     | 10   | With executionTime                             | Scheduled commands          |

### 5.2 Bulk Response Fixtures (10 fixtures)

| Fixture ID                    | Scenario               | Status Code | Description                            | Structure                                           |
| ----------------------------- | ---------------------- | ----------- | -------------------------------------- | --------------------------------------------------- |
| **Success Responses**         |
| BULK-RESP-001                 | All created            | 201         | 10 observations created                | Array of full Observation objects                   |
| BULK-RESP-002                 | All created (IDs only) | 201         | 100 observations created, IDs returned | `{ created: 100, ids: [...] }`                      |
| BULK-RESP-003                 | Commands created       | 201         | 10 commands created                    | Array of full Command objects                       |
| **Partial Success Responses** |
| BULK-RESP-004                 | Partial success        | 207         | 9 created, 1 failed                    | `{ created: [...], failed: [{index, error}] }`      |
| BULK-RESP-005                 | Multiple failures      | 207         | 7 created, 3 failed                    | `{ created: [...], failed: [{...}, {...}, {...}] }` |
| BULK-RESP-006                 | Mostly failures        | 207         | 2 created, 8 failed                    | More failures than successes                        |
| **Failure Responses**         |
| BULK-RESP-007                 | All invalid            | 400         | All 10 items failed validation         | `{ errors: [{index, property, message}, ...] }`     |
| BULK-RESP-008                 | Schema mismatch        | 400         | Result doesn't match schema            | Detailed schema validation error                    |
| BULK-RESP-009                 | Payload too large      | 413         | Exceeded size limit                    | Standard HTTP error                                 |
| BULK-RESP-010                 | Timeout                | 504         | Request timed out                      | Gateway timeout                                     |

### 5.3 Performance Test Fixtures (8 fixtures)

| Fixture ID    | Size  | Purpose           | Description                     |
| ------------- | ----- | ----------------- | ------------------------------- |
| BULK-PERF-001 | 100   | Baseline          | Small batch for baseline timing |
| BULK-PERF-002 | 500   | Standard          | Typical batch size              |
| BULK-PERF-003 | 1000  | Recommended max   | Recommended batch limit         |
| BULK-PERF-004 | 2000  | Above recommended | Testing chunking behavior       |
| BULK-PERF-005 | 5000  | Large batch       | Stress testing                  |
| BULK-PERF-006 | 10000 | Maximum           | At server limit                 |
| BULK-PERF-007 | 100   | Complex schema    | Multi-field observations        |
| BULK-PERF-008 | 1000  | Sequential times  | Time-series pattern             |

### 5.4 Fixture Summary

**Total Fixtures:** 30 fixtures

| Fixture Category          | Count | Priority     |
| ------------------------- | ----- | ------------ |
| Bulk Request Fixtures     | 12    | **CRITICAL** |
| Bulk Response Fixtures    | 10    | **CRITICAL** |
| Performance Test Fixtures | 8     | MEDIUM       |

---

## 6. Client Library Design

> ✅ **REVIEW NOTICE: Strongest Section — This Is What Tests Should Exercise**
>
> Section 6 defines the actual client code: `BulkCreateResult<T>` type construction, `BulkCreateOptions` with `chunkSize`/`delayBetweenChunks`/`continueOnError`/`onProgress`, auto-chunking strategy (Section 6.3), and fallback-to-sequential (Section 6.4). These are genuine client behaviors that can be tested with mocked fetch: feed bulk response fixture → call `createObservationsBulk()` → assert `BulkCreateResult` fields, verify `onProgress` was called N times, verify requests were chunked into expected sizes. Section 4's tests should be rewritten to target this code.

### 6.1 Bulk Operation Methods

```typescript
interface BulkCreateResult<T> {
  created: T[];           // Successfully created items
  failed: BulkError[];    // Failed items with details
  partial: boolean;       // true if some items failed
  totalItems: number;     // Original batch size
}

interface BulkError {
  index: number;          // Index in original array
  item: any;              // Original item data
  error: string;          // Error message
  property?: string;      // Property that failed validation
  statusCode?: number;    // HTTP status if available
}

// Observations
async createObservationsBulk(
  datastreamId: string,
  observations: ObservationInput[],
  options?: BulkCreateOptions
): Promise<BulkCreateResult<Observation>>

// Commands
async createCommandsBulk(
  controlStreamId: string,
  commands: CommandInput[],
  options?: BulkCreateOptions
): Promise<BulkCreateResult<Command>>
```

### 6.2 Bulk Create Options

```typescript
interface BulkCreateOptions {
  chunkSize?: number; // Items per request (default: 1000)
  delayBetweenChunks?: number; // Milliseconds between chunks (default: 100)
  continueOnError?: boolean; // Continue if a chunk fails (default: true)
  onProgress?: (progress: BulkProgress) => void; // Progress callback
}

interface BulkProgress {
  processed: number; // Items processed so far
  total: number; // Total items to process
  created: number; // Successfully created
  failed: number; // Failed items
  percentage: number; // Progress percentage
}
```

### 6.3 Auto-Chunking Strategy

```typescript
async createObservationsBulk(
  datastreamId: string,
  observations: ObservationInput[],
  options: BulkCreateOptions = {}
): Promise<BulkCreateResult<Observation>> {
  const {
    chunkSize = 1000,
    delayBetweenChunks = 100,
    continueOnError = true,
    onProgress
  } = options;

  const allCreated: Observation[] = [];
  const allFailed: BulkError[] = [];

  // Chunk observations
  const chunks = chunk(observations, chunkSize);

  for (let i = 0; i < chunks.length; i++) {
    const currentChunk = chunks[i];
    const chunkStartIndex = i * chunkSize;

    try {
      const response = await this.http.post(
        `/datastreams/${datastreamId}/observations`,
        currentChunk
      );

      // Handle success or partial success
      if (response.data.items) {
        allCreated.push(...response.data.items);
      }

      if (response.data.failed) {
        // Adjust indices to original array
        const adjustedFailed = response.data.failed.map(f => ({
          ...f,
          index: chunkStartIndex + f.index
        }));
        allFailed.push(...adjustedFailed);
      }

      // Report progress
      if (onProgress) {
        onProgress({
          processed: (i + 1) * chunkSize,
          total: observations.length,
          created: allCreated.length,
          failed: allFailed.length,
          percentage: ((i + 1) / chunks.length) * 100
        });
      }

      // Delay between chunks (except last)
      if (i < chunks.length - 1 && delayBetweenChunks > 0) {
        await delay(delayBetweenChunks);
      }

    } catch (error) {
      if (continueOnError) {
        // Mark entire chunk as failed
        currentChunk.forEach((item, j) => {
          allFailed.push({
            index: chunkStartIndex + j,
            item,
            error: error.message,
            statusCode: error.status
          });
        });
      } else {
        throw error;
      }
    }
  }

  return {
    created: allCreated,
    failed: allFailed,
    partial: allFailed.length > 0,
    totalItems: observations.length
  };
}
```

### 6.4 Fallback to Sequential Strategy

```typescript
async createObservationsWithFallback(
  datastreamId: string,
  observations: ObservationInput[]
): Promise<BulkCreateResult<Observation>> {
  try {
    // Try bulk first
    return await this.createObservationsBulk(datastreamId, observations);
  } catch (error) {
    if (error.status === 400 && error.message.match(/bulk.*not.*supported/i)) {
      // Server doesn't support bulk - fall back to sequential
      console.warn('Bulk operations not supported, falling back to sequential');
      return await this.createObservationsSequential(datastreamId, observations);
    }
    throw error;
  }
}

private async createObservationsSequential(
  datastreamId: string,
  observations: ObservationInput[]
): Promise<BulkCreateResult<Observation>> {
  const created: Observation[] = [];
  const failed: BulkError[] = [];

  for (let i = 0; i < observations.length; i++) {
    try {
      const response = await this.http.post(
        `/datastreams/${datastreamId}/observations`,
        observations[i]
      );
      created.push(response.data);
    } catch (error) {
      failed.push({
        index: i,
        item: observations[i],
        error: error.message,
        statusCode: error.status
      });
    }
  }

  return {
    created,
    failed,
    partial: failed.length > 0,
    totalItems: observations.length
  };
}
```

---

## 7. Implementation Estimates

### 7.1 Test Implementation Summary

| Test Category          | Test Count | Lines per Test | Total Lines | Priority     |
| ---------------------- | ---------- | -------------- | ----------- | ------------ |
| All-Valid Observations | 8          | 19-25          | 150-200     | **CRITICAL** |
| All-Valid Commands     | 6          | 17-25          | 100-150     | HIGH         |
| Mixed Valid/Invalid    | 6          | 13-20          | 80-120      | HIGH         |
| Size Limits            | 4          | 15-20          | 60-80       | MEDIUM       |
| Performance            | 4          | 15-20          | 60-80       | MEDIUM       |
| **TOTAL**              | **28**     | **~18 avg**    | **450-600** |              |

**Test File Organization:**

```
src/ogc-api/bulk/
  observations-bulk-valid.spec.ts         (~150-200 lines, 8 tests)
  commands-bulk-valid.spec.ts             (~100-150 lines, 6 tests)
  bulk-mixed-valid-invalid.spec.ts        (~80-120 lines, 6 tests)
  bulk-size-limits.spec.ts                (~60-80 lines, 4 tests)
  bulk-performance.spec.ts                (~60-80 lines, 4 tests)

fixtures/bulk/
  requests/                               (12 fixture files)
  responses/                              (10 fixture files)
  performance/                            (8 fixture files)
```

### 7.2 Implementation Effort Estimates

**Development Tasks:**

| Task                         | Estimated Lines   | Estimated Time  |
| ---------------------------- | ----------------- | --------------- |
| All-valid observations tests | 150-200           | 3-4 hours       |
| All-valid commands tests     | 100-150           | 2-3 hours       |
| Mixed valid/invalid tests    | 80-120            | 2-3 hours       |
| Size limit tests             | 60-80             | 1-2 hours       |
| Performance tests            | 60-80             | 1-2 hours       |
| Fixture creation             | 30 files          | 3-4 hours       |
| Documentation                | 50-100            | 1-2 hours       |
| **TOTAL**                    | **450-600 lines** | **13-20 hours** |

**Testing Priorities:**

1. **CRITICAL (Priority 1):** 8 tests, ~150-200 lines, 3-4 hours

   - All-valid observation bulk creation (basic functionality)

2. **HIGH (Priority 2):** 12 tests, ~180-270 lines, 4-6 hours

   - All-valid command bulk creation
   - Mixed valid/invalid items (partial success handling)

3. **MEDIUM (Priority 3):** 8 tests, ~120-160 lines, 2-4 hours
   - Size limit handling
   - Performance testing

---

## 8. Performance Considerations

### 8.1 Recommended Batch Sizes

| Operation         | Recommended Batch Size | Maximum | Rationale                                 |
| ----------------- | ---------------------- | ------- | ----------------------------------------- |
| POST Observations | 100-1,000              | 10,000  | Balance latency vs throughput             |
| POST Commands     | 50-500                 | 5,000   | Commands typically lower volume           |
| GET Observations  | 100-1,000              | 10,000  | Large result sets benefit from pagination |

**Factors Affecting Batch Size:**

- **Network latency:** Larger batches reduce round trips
- **Server memory:** Very large batches may exceed memory limits
- **Timeout limits:** Processing time increases linearly with batch size
- **Error handling:** Smaller batches make it easier to identify and retry failures

### 8.2 Performance Benchmarks (OpenSensorHub)

| Batch Size   | Expected Latency | Throughput         | Notes                     |
| ------------ | ---------------- | ------------------ | ------------------------- |
| 10 items     | 50-200ms         | 50-200 items/sec   | High latency overhead     |
| 100 items    | 100-500ms        | 200-1000 items/sec | Optimal for small batches |
| 1,000 items  | 500-2000ms       | 500-2000 items/sec | Recommended max           |
| 10,000 items | 5-20 seconds     | 500-2000 items/sec | Risk of timeout           |

**Performance Tips:**

1. **Use chunking:** Break large batches into 1,000-item chunks
2. **Add delays:** 100ms delay between chunks prevents server overload
3. **Monitor progress:** Use progress callbacks for user feedback
4. **Handle timeouts:** Implement retry logic for timeout errors
5. **Parallelize carefully:** Avoid parallel bulk requests to same endpoint

### 8.3 Memory Usage

**Client-Side Memory:**

- **Observation:** ~100-500 bytes per item (depends on result complexity)
- **Command:** ~50-200 bytes per item (depends on parameters)
- **1,000 observations:** ~100-500 KB
- **10,000 observations:** ~1-5 MB

**Server-Side Memory:**

- **Parsing:** 2-3x request size (JSON parsing overhead)
- **Validation:** Additional 1-2x for schema validation
- **Database insertion:** Batched inserts reduce memory footprint

**Memory Optimization:**

- Stream large requests (if supported)
- Use SWE Common Text/Binary encodings (more compact than JSON)
- Chunk requests to limit memory usage

---

## 9. Error Handling Best Practices

### 9.1 Error Categories

**1. Request Validation Errors (400 Bad Request)**

- Empty array
- Wrong content type (not application/json)
- Malformed JSON

**2. Item Validation Errors (400 or 207)**

- Schema mismatch
- Missing required properties
- Invalid timestamp format
- Invalid result type

**3. Resource Errors (404 Not Found)**

- Datastream/controlstream does not exist
- Referenced feature of interest not found

**4. Server Errors (500 Internal Server Error)**

- Database insertion failure
- Schema parsing failure

**5. Resource Limits (413 Payload Too Large, 504 Gateway Timeout)**

- Batch size exceeds limit
- Request takes too long to process

### 9.2 Client Error Handling Strategy

```typescript
try {
  const result = await client.observations.createBulk(
    datastreamId,
    observations
  );

  if (result.partial) {
    console.warn(
      `Partial success: ${result.created.length} created, ${result.failed.length} failed`
    );

    // Log failures
    result.failed.forEach((failure) => {
      console.error(`Item ${failure.index} failed: ${failure.error}`);
    });

    // Optionally retry failures
    const retryItems = result.failed.map((f) => f.item);
    await client.observations.createBulk(datastreamId, retryItems);
  }
} catch (error) {
  if (error.status === 400) {
    console.error('Validation error:', error.message);
    // Fix validation errors and retry
  } else if (error.status === 413) {
    console.error('Batch too large, reducing size');
    // Reduce batch size and retry
  } else if (error.status === 504) {
    console.error('Request timeout, reducing batch size');
    // Reduce batch size and retry
  } else {
    throw error; // Unexpected error
  }
}
```

### 9.3 Retry Strategy

```typescript
async function createWithRetry<T>(
  createFn: () => Promise<BulkCreateResult<T>>,
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<BulkCreateResult<T>> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await createFn();
    } catch (error) {
      lastError = error;

      if (error.status === 413 || error.status === 504) {
        // Reduce batch size and retry
        console.warn(`Attempt ${attempt + 1} failed, reducing batch size`);
        await delay(retryDelay * (attempt + 1));
      } else if (error.status >= 500) {
        // Server error, retry
        console.warn(
          `Attempt ${attempt + 1} failed with server error, retrying`
        );
        await delay(retryDelay * (attempt + 1));
      } else {
        // Client error, don't retry
        throw error;
      }
    }
  }

  throw lastError;
}
```

---

## 10. Schema Validation Integration

### 10.1 Schema-Driven Validation (from Section 27)

**Each Item Validated Against Schema:**

- Datastream schema defines expected observation structure
- ControlStream schema defines expected command structure
- Client pre-validates items before sending (optional)
- Server validates all items atomically

**Example DataStream Schema:**

```json
{
  "type": "DataRecord",
  "fields": [
    {
      "name": "phenomenonTime",
      "type": "Time",
      "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime"
    },
    {
      "name": "result",
      "type": "DataRecord",
      "fields": [
        {
          "name": "temp",
          "type": "Quantity",
          "uom": { "code": "Cel" }
        },
        {
          "name": "humidity",
          "type": "Quantity",
          "uom": { "code": "%" }
        }
      ]
    }
  ]
}
```

**Valid Observation:**

```json
{
  "phenomenonTime": "2024-01-01T00:00:00Z",
  "result": {
    "temp": 23.5,
    "humidity": 60.5
  }
}
```

**Invalid Observation (Missing Field):**

```json
{
  "phenomenonTime": "2024-01-01T00:00:00Z",
  "result": {
    "temp": 23.5
    // ❌ Missing humidity
  }
}
```

### 10.2 Client-Side Pre-Validation

```typescript
import Ajv from 'ajv';

async function validateObservations(
  observations: ObservationInput[],
  schema: DataStreamSchema
): Promise<ValidationResult> {
  const ajv = new Ajv();
  const jsonSchema = convertSWEtoJSONSchema(schema);
  const validate = ajv.compile(jsonSchema);

  const errors: ValidationError[] = [];

  observations.forEach((obs, index) => {
    if (!validate(obs)) {
      errors.push({
        index,
        item: obs,
        errors: validate.errors,
      });
    }
  });

  return {
    valid: errors.length === 0,
    errors,
  };
}

// Usage
const result = await validateObservations(observations, datastreamSchema);
if (!result.valid) {
  console.error('Pre-validation failed:', result.errors);
  // Fix errors or filter out invalid items before sending
}
```

---

## 11. References

### 11.1 Specifications

- **OGC API - Connected Systems Part 2:** OGC 23-002 (bulk observation/command creation)
- **OpenSensorHub Implementation:** Bulk observation insert patterns
- **SWE Common Data Model 3.0:** Schema validation for observations/commands

### 11.2 Related Research

- **Section 13:** Resource Method Testing Patterns (individual operations)
- **Section 18:** Error Condition Testing (error handling patterns)
- **Section 27:** Schema-Driven Validation Testing (item validation)
- **Section 33:** Performance Testing (bulk performance benchmarks) - **BLOCKED**

### 11.3 Implementation References

- Part 2 Requirements: `csapi-part2-requirements.md` (bulk endpoints)
- CRUD Operations: `csapi-crud-operations.md` (batch operations patterns)
- OpenSensorHub Analysis: `csapi-opensensorhub-analysis.md` (bulk insert patterns, batch sizes)

---

## 12. Appendices

### Appendix A: Bulk Request Examples

**Small Batch (10 Observations):**

```json
[
  { "phenomenonTime": "2024-01-01T00:00:00Z", "result": 20.0 },
  { "phenomenonTime": "2024-01-01T01:00:00Z", "result": 20.5 },
  { "phenomenonTime": "2024-01-01T02:00:00Z", "result": 21.0 },
  { "phenomenonTime": "2024-01-01T03:00:00Z", "result": 21.5 },
  { "phenomenonTime": "2024-01-01T04:00:00Z", "result": 22.0 },
  { "phenomenonTime": "2024-01-01T05:00:00Z", "result": 22.5 },
  { "phenomenonTime": "2024-01-01T06:00:00Z", "result": 23.0 },
  { "phenomenonTime": "2024-01-01T07:00:00Z", "result": 23.5 },
  { "phenomenonTime": "2024-01-01T08:00:00Z", "result": 24.0 },
  { "phenomenonTime": "2024-01-01T09:00:00Z", "result": 24.5 }
]
```

**Multi-Field Observations:**

```json
[
  {
    "phenomenonTime": "2024-01-01T00:00:00Z",
    "result": {
      "temp": 23.5,
      "humidity": 60.5,
      "pressure": 1013.25
    }
  },
  {
    "phenomenonTime": "2024-01-01T01:00:00Z",
    "result": {
      "temp": 23.8,
      "humidity": 61.2,
      "pressure": 1013.1
    }
  }
]
```

**Commands with Execution Time:**

```json
[
  {
    "issueTime": "2024-01-01T00:00:00Z",
    "executionTime": "2024-01-01T00:00:05Z",
    "parameters": { "action": "capture", "resolution": "1920x1080" }
  },
  {
    "issueTime": "2024-01-01T00:00:10Z",
    "executionTime": "2024-01-01T00:00:15Z",
    "parameters": { "action": "capture", "resolution": "3840x2160" }
  }
]
```

### Appendix B: Bulk Response Examples

**Complete Success:**

```json
{
  "created": 10,
  "items": [
    {"id": "obs-001", "phenomenonTime": "2024-01-01T00:00:00Z", "result": 20.0},
    {"id": "obs-002", "phenomenonTime": "2024-01-01T01:00:00Z", "result": 20.5},
    ...
  ]
}
```

**Partial Success (207 Multi-Status):**

```json
{
  "created": 8,
  "failed": 2,
  "items": [
    {"id": "obs-001", "status": "created"},
    {"index": 1, "status": "failed", "error": "Schema validation failed: result must be numeric"},
    {"id": "obs-003", "status": "created"},
    ...
  ]
}
```

**Complete Failure (400 Bad Request):**

```json
{
  "code": "ValidationError",
  "description": "Bulk operation validation failed",
  "errors": [
    {
      "index": 0,
      "property": "result",
      "message": "Expected number, got string",
      "value": "invalid"
    },
    {
      "index": 2,
      "property": "phenomenonTime",
      "message": "Required property missing"
    },
    {
      "index": 5,
      "property": "result",
      "message": "Expected DataRecord, got Quantity"
    }
  ]
}
```

### Appendix C: Transaction Semantics Comparison

| Approach            | All Items Valid | Some Items Invalid                | All Items Invalid  | Client Complexity              | Server Complexity           |
| ------------------- | --------------- | --------------------------------- | ------------------ | ------------------------------ | --------------------------- |
| **All-or-Nothing**  | Create all      | Reject all (400)                  | Reject all (400)   | Simple (retry entire batch)    | Simple (single transaction) |
| **Partial Success** | Create all      | Create valid, report failed (207) | Reject all (400)   | Moderate (track partial state) | Complex (per-item handling) |
| **Sequential**      | Create all      | Stop at first failure             | Fail on first item | Simple (retry from failure)    | Simple but slow             |

**CSAPI Likely Approach:** **Partial Success** (based on OpenSensorHub implementation)

### Appendix D: Batch Size Guidelines

**General Recommendations:**

- **Start small:** Begin with 100-item batches, increase if performance is acceptable
- **Monitor latency:** If latency > 2 seconds, reduce batch size
- **Monitor errors:** If many items fail, smaller batches make it easier to debug
- **Consider network:** Slow connections benefit from larger batches (fewer round trips)
- **Consider data rate:** High-frequency sensors (1 Hz+) benefit from larger batches

**By Use Case:**

- **Real-time ingestion:** 10-100 items (low latency)
- **Batch historical data:** 1,000-10,000 items (high throughput)
- **Interactive testing:** 5-10 items (easy to debug)
- **Automated workflows:** 500-1,000 items (balance efficiency and reliability)

---

**End of Document**
