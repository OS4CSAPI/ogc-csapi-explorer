# Section 27: Schema-Driven Validation Testing Strategy

> ⚠️ **REVIEW NOTICE — HIGH (H10): Schema Evolution Tests Require Server Integration**
>
> **Phase 2E Review | Issues: H10, M5 | Anti-Patterns: AP1**
>
> This document is ~70% client-oriented. The observation/command validation test patterns (Sections 4-5) are well-designed IF schema validation is implemented as client-side pre-validation (`validateObservation()` with `options.validate = true`). However:
>
> - **Section 6.1** (Schema Evolution, 4 tests): Uses `client.createDataStream()`, `client.createObservation()`, `client.updateDataStream()` expecting 409 Conflict. The 409 response requires server state — this is inherently integration testing, not client unit testing.
> - **Section 10.2**: Explicitly describes server-side validation workflow ("Receive observation", "Fetch DataStream schema", "Return 400 Bad Request"). This is server compliance documentation.
>
> **What's usable:** Sections 4-5 (validation scenarios), Section 10.1 (client-side validation flow), SWE Common type analysis (Section 3), fixture design (Section 8).
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

**Research Plan:** [Research Plan 27: Schema-Driven Validation Testing](../research-plans/27-schema-driven-validation-testing.md)

**Research Questions:** 6 core questions about testing observation result validation against DataStream schema, command parameter validation against ControlStream schema, schema mismatch scenarios, schema parsing (SWE Common schemas), fixtures needed for schema validation scenarios, and error messages for schema violations

**Methodology:** 6-phase systematic analysis (Phase 1: Schema Specification Analysis of DataStream/ControlStream requirements → Phase 2: SWE Common Schema Analysis of 12+ component types → Phase 3: Upstream Schema Validation Analysis of existing patterns → Phase 4: Validation Scenario Design for 66 test scenarios → Phase 5: Fixture Design for valid/invalid observations and commands → Phase 6: Synthesis into comprehensive schema-driven validation testing strategy)

**Research Time:** ~3.5 hours (February 6, 2026)

**Primary Source(s):**

- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (schema requirements)
- [Part 2 Requirements](../../requirements/csapi-part2-requirements.md)
- [SWE Common 3.0 Specification](https://docs.ogc.org/is/24-014/24-014.html)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (schema validation specifications)

**Supporting Resources:**

- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream schema validation patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (validation patterns)
- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (schema definitions)
- Section 10: [SWE Common Testing Requirements](10-swe-common-testing-requirements.md) (schema component testing)
- Section 16: [Worker Extensions Testing](16-worker-extensions-testing.md) (VALIDATE_OBSERVATIONS, VALIDATE_COMMANDS)
- [JSON Schema standards](https://json-schema.org/specification.html)

**Document Purpose:** Defines comprehensive testing strategy for dual CSAPI Part 2 schema validation system (DataStream resultSchema for observations, ControlStream parametersSchema for commands) with 66 test scenarios covering SWE Common 3.0 component validation, type mismatches, missing/extra fields, constraint violations, schema evolution, and error messaging

---

## Executive Summary

This document defines comprehensive testing requirements for schema-driven validation in CSAPI Part 2, covering DataStream observation schema validation and ControlStream command schema validation. Schema validation is a unique CSAPI feature that ensures observations and commands conform to predefined SWE Common schemas before submission.

### Key Findings

**Dual Schema System:**

- **DataStream resultSchema** - Defines structure for observation results (SWE Common DataRecord or DataArray)
- **ControlStream parametersSchema** - Defines structure for command parameters (SWE Common DataRecord)
- Both use SWE Common 3.0 DataComponent structure with 12+ component types

**Schema Validation Points:**

- **Observation Creation (POST)** - result must match DataStream resultSchema
- **Observation Update (PUT/PATCH)** - result must match DataStream resultSchema
- **Command Creation (POST)** - parameters must match ControlStream parametersSchema
- **Command Update (PUT/PATCH)** - parameters must match ControlStream parametersSchema
- **Schema Evolution** - Schema changes rejected if observations/commands exist (409 Conflict)

**Testing Priorities:**

- **CRITICAL:** Type mismatch validation, missing required fields, constraint violations
- **HIGH:** Extra field handling, array length validation, nested structure validation
- **MEDIUM:** Error message validation, schema evolution scenarios
- **LOW:** Complex nesting (4+ levels), performance with large schemas

**Fixture Requirements:** ~60 fixtures

- Valid DataStream schemas: ~10 fixtures
- Valid ControlStream schemas: ~5 fixtures
- Valid observation results: ~15 fixtures
- Invalid observation results: ~15 fixtures (various error types)
- Valid command parameters: ~5 fixtures
- Invalid command parameters: ~10 fixtures

**Estimated Test Implementation:** 800-1,200 lines

- Observation validation tests: 400-600 lines (25 tests)
- Command validation tests: 250-400 lines (15 tests)
- Schema evolution tests: 100-150 lines (8 tests)
- Error message tests: 50-50 lines (4 tests)

**Key Testing Challenges:**

1. **SWE Common complexity** - 12+ component types with different validation rules
2. **Constraint enforcement** - allowedValues, allowedIntervals, significantFigures
3. **Nested structures** - DataRecord within DataRecord, DataArray of DataRecords
4. **Error message validation** - Detailed error messages with field names and types
5. **Schema immutability** - Cannot change schema with existing data

### Highest Rejection Risk

Schema validation is **HIGH RISK** because:

- **Most complex validation logic** - Must handle 12+ SWE Common types with different rules
- **User-facing errors** - Invalid observations/commands produce 400 errors with detailed messages
- **Schema evolution constraints** - 409 errors for schema changes with existing data
- **Format-specific schemas** - Different schemas for JSON, SWE CSV, SWE Binary encodings

**Mitigation:** Comprehensive test coverage with ~60 fixtures testing all component types, constraint types, and error scenarios.

---

## 1. DataStream Schema Structure

### 1.1 Schema Properties

**DataStream Schema (resultSchema):**

```json
{
  "type": "DataStream",
  "id": "ds-weather-001",
  "uniqueIdentifier": "urn:example:datastream:weather-001",
  "resultSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "time",
        "type": "Time",
        "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
        "referenceFrame": "http://www.opengis.net/def/trs/BIPM/0/UTC"
      },
      {
        "name": "temperature",
        "type": "Quantity",
        "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
        "uom": { "code": "Cel" },
        "constraint": {
          "interval": [-50, 100]
        }
      },
      {
        "name": "humidity",
        "type": "Quantity",
        "definition": "http://mmisw.org/ont/cf/parameter/relative_humidity",
        "uom": { "code": "%" },
        "constraint": {
          "interval": [0, 100]
        }
      }
    ]
  },
  "parametersSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "quality",
        "type": "Category",
        "definition": "http://www.opengis.net/def/property/OGC/0/DataQuality",
        "constraint": {
          "allowedTokens": ["good", "questionable", "bad"]
        }
      }
    ]
  }
}
```

**Key Properties:**

- **resultSchema** (required) - SWE Common DataComponent defining observation result structure
- **parametersSchema** (optional) - SWE Common DataComponent defining observation-specific parameters
- **Schema Types:** DataRecord (structured data) or DataArray (time series)

### 1.2 Observation Validation

**Valid Observation:**

```json
{
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": {
    "time": "2024-01-15T12:00:00Z",
    "temperature": 23.5,
    "humidity": 65.0
  },
  "parameters": {
    "quality": "good"
  }
}
```

**Validation Rules:**

1. **Type Matching** - result values must match field types (Quantity → number, Text → string, etc.)
2. **Required Fields** - All non-optional fields must be present
3. **Constraint Enforcement** - Values must satisfy constraints (intervals, allowedTokens)
4. **No Extra Fields** (strict mode) - Only fields defined in schema are allowed
5. **Nested Structure** - Nested DataRecords validated recursively

**Error Responses:**

- **400 Bad Request** - Invalid result structure incompatible with schema
- **409 Conflict** - Schema change attempted with existing observations

---

## 2. ControlStream Schema Structure

### 2.1 Schema Properties

**ControlStream Schema (parametersSchema):**

```json
{
  "type": "ControlStream",
  "id": "cs-heater-001",
  "uniqueIdentifier": "urn:example:controlstream:heater-001",
  "parametersSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "setpoint",
        "type": "Quantity",
        "definition": "http://www.opengis.net/def/property/OGC/0/Temperature",
        "uom": { "code": "Cel" },
        "constraint": {
          "interval": [10, 30]
        }
      },
      {
        "name": "mode",
        "type": "Category",
        "definition": "http://www.opengis.net/def/property/OGC/0/OperatingMode",
        "constraint": {
          "allowedTokens": ["heat", "cool", "auto", "off"]
        }
      },
      {
        "name": "enabled",
        "type": "Boolean",
        "definition": "http://www.opengis.net/def/property/OGC/0/PowerState"
      }
    ]
  },
  "resultSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "success",
        "type": "Boolean"
      },
      {
        "name": "message",
        "type": "Text"
      }
    ]
  }
}
```

**Key Properties:**

- **parametersSchema** (required) - SWE Common DataComponent defining command parameter structure
- **resultSchema** (optional) - SWE Common DataComponent defining command result structure (for feasibility/result endpoints)

### 2.2 Command Validation

**Valid Command:**

```json
{
  "issueTime": "2024-01-15T12:00:00Z",
  "executionTime": "2024-01-15T12:00:00Z",
  "parameters": {
    "setpoint": 22.0,
    "mode": "heat",
    "enabled": true
  }
}
```

**Validation Rules:**

1. **Type Matching** - parameters values must match field types
2. **Required Fields** - All non-optional fields must be present
3. **Constraint Enforcement** - Values must satisfy constraints
4. **Feasibility Constraints** - Command parameters must be feasible (equipment capabilities)

**Error Responses:**

- **400 Bad Request** - Invalid parameters structure incompatible with schema
- **409 Conflict** - Schema change attempted with existing commands

---

## 3. SWE Common Component Types

### 3.1 Simple Components

| Component Type | JSON Type | Validation Rules            | Constraint Types                       | Test Priority |
| -------------- | --------- | --------------------------- | -------------------------------------- | ------------- |
| **Quantity**   | number    | Numeric value, optional UOM | interval (min/max), significantFigures | **CRITICAL**  |
| **Count**      | integer   | Integer value               | interval, allowedValues                | HIGH          |
| **Boolean**    | boolean   | true or false               | None                                   | HIGH          |
| **Text**       | string    | String value                | allowedTokens, pattern (regex)         | HIGH          |
| **Time**       | string    | ISO 8601 datetime/interval  | interval (time range)                  | **CRITICAL**  |
| **Category**   | string    | String from codeSpace       | allowedTokens                          | MEDIUM        |

### 3.2 Range Components

| Component Type    | JSON Type        | Validation Rules         | Constraint Types | Test Priority |
| ----------------- | ---------------- | ------------------------ | ---------------- | ------------- |
| **QuantityRange** | [number, number] | Numeric range [min, max] | interval         | MEDIUM        |
| **CategoryRange** | [string, string] | Category range           | allowedTokens    | LOW           |
| **TimeRange**     | [string, string] | ISO 8601 time range      | interval         | MEDIUM        |

### 3.3 Complex Components

| Component Type   | JSON Type | Validation Rules                                               | Constraint Types           | Test Priority |
| ---------------- | --------- | -------------------------------------------------------------- | -------------------------- | ------------- |
| **DataRecord**   | object    | Named fields with types, unique field names                    | Per-field constraints      | **CRITICAL**  |
| **DataArray**    | array     | Array of values, elementType validation, optional elementCount | Per-element constraints    | **CRITICAL**  |
| **Vector**       | object    | Coordinates array, optional referenceFrame                     | Per-coordinate constraints | MEDIUM        |
| **Matrix**       | array     | 2D array, dimensions validation                                | Per-element constraints    | LOW           |
| **DataChoice**   | object    | One of multiple alternatives                                   | Per-option constraints     | MEDIUM        |
| **GeometryData** | object    | GeoJSON geometry                                               | geometry type validation   | MEDIUM        |

### 3.4 Constraint Types

**AllowedIntervals (Quantity, Count, Time):**

```json
{
  "constraint": {
    "interval": [-50, 100]
  }
}
```

**AllowedValues (Category, Text, Count):**

```json
{
  "constraint": {
    "allowedTokens": ["clear", "cloudy", "rainy", "snowy"]
  }
}
```

**Pattern (Text):**

```json
{
  "constraint": {
    "pattern": "^[A-Z]{3}-[0-9]{4}$"
  }
}
```

**SignificantFigures (Quantity):**

```json
{
  "constraint": {
    "significantFigures": 3
  }
}
```

---

## 4. Observation Validation Test Patterns

### 4.1 Type Mismatch Scenarios (8 tests)

**Priority:** **CRITICAL**

| Test ID     | Component Type | Valid Type        | Invalid Value       | Error Type | Expected Message                                                |
| ----------- | -------------- | ----------------- | ------------------- | ---------- | --------------------------------------------------------------- |
| OBS-VAL-001 | Quantity       | number            | "23.5" (string)     | Type error | "Invalid type for 'temperature': expected number, got string"   |
| OBS-VAL-002 | Count          | integer           | 23.5 (float)        | Type error | "Invalid type for 'count': expected integer, got number"        |
| OBS-VAL-003 | Boolean        | boolean           | "true" (string)     | Type error | "Invalid type for 'enabled': expected boolean, got string"      |
| OBS-VAL-004 | Text           | string            | 123 (number)        | Type error | "Invalid type for 'code': expected string, got number"          |
| OBS-VAL-005 | Time           | string (ISO 8601) | 1234567890 (number) | Type error | "Invalid type for 'time': expected ISO 8601 string, got number" |
| OBS-VAL-006 | Category       | string            | ["cloudy"] (array)  | Type error | "Invalid type for 'weather': expected string, got array"        |
| OBS-VAL-007 | DataArray      | array             | {} (object)         | Type error | "Invalid type for 'measurements': expected array, got object"   |
| OBS-VAL-008 | DataRecord     | object            | [] (array)          | Type error | "Invalid type for 'station': expected object, got array"        |

**Test Implementation (~120 lines, 8 tests):**

```typescript
describe('Observation Validation - Type Mismatch', () => {
  it('should reject Quantity field with string value', () => {
    const schema = loadSchemaFixture('datastream-weather.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        temperature: '23.5', // Invalid: string instead of number
        humidity: 65.0,
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'temperature',
      type: 'type',
      expectedType: 'number',
      actualType: 'string',
      message: "Invalid type for 'temperature': expected number, got string",
    });
  });

  // Similar tests for Count, Boolean, Text, Time, Category, DataArray, DataRecord...
});
```

### 4.2 Missing Required Field Scenarios (5 tests)

**Priority:** **CRITICAL**

| Test ID     | Field Type       | Missing Field        | Error Type    | Expected Message                                |
| ----------- | ---------------- | -------------------- | ------------- | ----------------------------------------------- |
| OBS-VAL-009 | Quantity         | temperature          | Missing error | "Missing required field 'temperature'"          |
| OBS-VAL-010 | Time             | time                 | Missing error | "Missing required field 'time'"                 |
| OBS-VAL-011 | DataRecord field | station.location.lat | Missing error | "Missing required field 'station.location.lat'" |
| OBS-VAL-012 | DataArray        | measurements         | Missing error | "Missing required field 'measurements'"         |
| OBS-VAL-013 | Entire result    | result               | Missing error | "Missing required field 'result'"               |

**Test Implementation (~75 lines, 5 tests):**

```typescript
describe('Observation Validation - Missing Required Fields', () => {
  it('should reject observation missing required Quantity field', () => {
    const schema = loadSchemaFixture('datastream-weather.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        // temperature missing
        humidity: 65.0,
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'temperature',
      type: 'missing',
      message: "Missing required field 'temperature'",
    });
  });

  // Similar tests for Time, nested fields, DataArray, entire result...
});
```

### 4.3 Extra Unexpected Field Scenarios (3 tests)

**Priority:** HIGH

| Test ID     | Extra Field              | Handling Mode | Expected Behavior | Expected Message                          |
| ----------- | ------------------------ | ------------- | ----------------- | ----------------------------------------- |
| OBS-VAL-014 | pressure (not in schema) | Strict        | Error             | "Unknown field 'pressure' not in schema"  |
| OBS-VAL-015 | pressure                 | Lenient       | Warning           | "Extra field 'pressure' ignored"          |
| OBS-VAL-016 | Multiple extra fields    | Strict        | Error with list   | "Unknown fields: 'pressure', 'windSpeed'" |

**Test Implementation (~45 lines, 3 tests):**

```typescript
describe('Observation Validation - Extra Fields', () => {
  it('should reject observation with extra field in strict mode', () => {
    const schema = loadSchemaFixture('datastream-weather.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        temperature: 23.5,
        humidity: 65.0,
        pressure: 1013.25, // Extra field not in schema
      },
    };

    const result = validateObservation(observation, schema, { strict: true });

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'pressure',
      type: 'extra',
      message: "Unknown field 'pressure' not in schema",
    });
  });

  it('should warn for extra field in lenient mode', () => {
    const schema = loadSchemaFixture('datastream-weather.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        temperature: 23.5,
        humidity: 65.0,
        pressure: 1013.25,
      },
    };

    const result = validateObservation(observation, schema, { strict: false });

    expect(result.valid).toBe(true);
    expect(result.warnings).toHaveLength(1);
    expect(result.warnings[0]).toMatchObject({
      field: 'pressure',
      type: 'extra',
      message: "Extra field 'pressure' ignored",
    });
  });

  // Test for multiple extra fields...
});
```

### 4.4 Constraint Violation Scenarios (12 tests)

**Priority:** **CRITICAL**

| Test ID     | Constraint Type              | Valid Range/Values           | Invalid Value        | Expected Message                                                                 |
| ----------- | ---------------------------- | ---------------------------- | -------------------- | -------------------------------------------------------------------------------- |
| OBS-VAL-017 | Quantity interval            | [-50, 100]                   | 150.0                | "Value 150.0 outside allowed interval [-50, 100] for 'temperature'"              |
| OBS-VAL-018 | Quantity interval            | [-50, 100]                   | -75.0                | "Value -75.0 outside allowed interval [-50, 100] for 'temperature'"              |
| OBS-VAL-019 | Count interval               | [0, 1000]                    | 1500                 | "Value 1500 outside allowed interval [0, 1000] for 'count'"                      |
| OBS-VAL-020 | Category allowedTokens       | ["clear", "cloudy", "rainy"] | "foggy"              | "Value 'foggy' not in allowed tokens ['clear', 'cloudy', 'rainy'] for 'weather'" |
| OBS-VAL-021 | Text pattern                 | ^[A-Z]{3}-[0-9]{4}$          | "AB-1234"            | "Value 'AB-1234' does not match pattern '^[A-Z]{3}-[0-9]{4}$' for 'code'"        |
| OBS-VAL-022 | Time interval                | [2024-01-01, 2024-12-31]     | 2025-01-01T00:00:00Z | "Time '2025-01-01T00:00:00Z' outside allowed interval for 'time'"                |
| OBS-VAL-023 | Quantity significantFigures  | 3                            | 23.456789            | "Value 23.456789 has more than 3 significant figures for 'temperature'"          |
| OBS-VAL-024 | QuantityRange interval       | [0, 100]                     | [110, 120]           | "Range [110, 120] outside allowed interval [0, 100] for 'temperatureRange'"      |
| OBS-VAL-025 | Count allowedValues          | [1, 2, 5, 10]                | 7                    | "Value 7 not in allowed values [1, 2, 5, 10] for 'sampleSize'"                   |
| OBS-VAL-026 | Multiple constraints         | interval + pattern           | 150.0 (out of range) | "Multiple constraint violations for 'value'"                                     |
| OBS-VAL-027 | Nested field constraint      | station.temp interval        | 150.0                | "Value 150.0 outside allowed interval for 'station.temperature'"                 |
| OBS-VAL-028 | DataArray element constraint | Element interval             | [23.5, 150.0, 24.1]  | "Element 1 value 150.0 outside allowed interval for 'measurements'"              |

**Test Implementation (~180 lines, 12 tests):**

```typescript
describe('Observation Validation - Constraint Violations', () => {
  it('should reject Quantity value outside allowed interval (above max)', () => {
    const schema = loadSchemaFixture('datastream-weather-constrained.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        temperature: 150.0, // Outside [-50, 100] interval
        humidity: 65.0,
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'temperature',
      type: 'constraint',
      constraintType: 'interval',
      expectedValue: '[-50, 100]',
      actualValue: 150.0,
      message:
        "Value 150.0 outside allowed interval [-50, 100] for 'temperature'",
    });
  });

  it('should reject Category value not in allowedTokens', () => {
    const schema = loadSchemaFixture('datastream-weather-category.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        weather: 'foggy', // Not in ["clear", "cloudy", "rainy"]
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'weather',
      type: 'constraint',
      constraintType: 'allowedTokens',
      expectedValue: ['clear', 'cloudy', 'rainy'],
      actualValue: 'foggy',
      message:
        "Value 'foggy' not in allowed tokens ['clear', 'cloudy', 'rainy'] for 'weather'",
    });
  });

  // Similar tests for interval (below min), Count interval, Text pattern, Time interval,
  // significantFigures, QuantityRange, Count allowedValues, multiple constraints,
  // nested field constraints, DataArray element constraints...
});
```

### 4.5 Nested Structure Scenarios (5 tests)

**Priority:** HIGH

| Test ID     | Nesting Type              | Depth    | Error Location      | Expected Behavior                                     |
| ----------- | ------------------------- | -------- | ------------------- | ----------------------------------------------------- |
| OBS-VAL-029 | DataRecord in DataRecord  | 2 levels | Nested field        | "Missing required field 'station.location.lat'"       |
| OBS-VAL-030 | DataRecord in DataRecord  | 3 levels | Deeply nested       | "Invalid type for 'station.location.coordinates.lat'" |
| OBS-VAL-031 | DataArray of DataRecords  | 1 level  | Array element       | "Element 2 missing required field 'temperature'"      |
| OBS-VAL-032 | DataRecord with DataArray | 2 levels | Array inside record | "station.measurements element 5 constraint violation" |
| OBS-VAL-033 | DataArray of DataArrays   | 2 levels | Nested array        | "measurements[3][2] value outside allowed interval"   |

**Test Implementation (~75 lines, 5 tests):**

```typescript
describe('Observation Validation - Nested Structures', () => {
  it('should validate nested DataRecord and report errors with full path', () => {
    const schema = loadSchemaFixture('datastream-nested-station.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        station: {
          id: 'WX-001',
          location: {
            // lat missing
            lon: -122.08,
          },
        },
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'station.location.lat',
      type: 'missing',
      message: "Missing required field 'station.location.lat'",
    });
  });

  it('should validate DataArray of DataRecords with element-level errors', () => {
    const schema = loadSchemaFixture('datastream-timeseries.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z/2024-01-15T12:10:00Z',
      resultTime: '2024-01-15T12:10:01Z',
      result: {
        measurements: [
          { time: '2024-01-15T12:00:00Z', temp: 23.5, humidity: 65.0 },
          { time: '2024-01-15T12:01:00Z', temp: 23.6, humidity: 64.8 },
          { time: '2024-01-15T12:02:00Z', humidity: 65.2 }, // temp missing
        ],
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'measurements[2].temp',
      type: 'missing',
      message: "Element 2 missing required field 'temp' in 'measurements'",
    });
  });

  // Similar tests for 3-level nesting, DataRecord with DataArray, DataArray of DataArrays...
});
```

### 4.6 DataArray Element Count Scenarios (3 tests)

**Priority:** HIGH

| Test ID     | Expected Count | Actual Count | Error Type     | Expected Message                                                        |
| ----------- | -------------- | ------------ | -------------- | ----------------------------------------------------------------------- |
| OBS-VAL-034 | 10             | 8            | Count mismatch | "Array 'measurements' length 8 does not match expected elementCount 10" |
| OBS-VAL-035 | 100            | 101          | Count mismatch | "Array 'measurements' length 101 exceeds expected elementCount 100"     |
| OBS-VAL-036 | 0              | 0            | Valid          | No error (empty array allowed)                                          |

**Test Implementation (~45 lines, 3 tests):**

```typescript
describe('Observation Validation - DataArray Element Count', () => {
  it('should reject DataArray with fewer elements than elementCount', () => {
    const schema = loadSchemaFixture('datastream-array-fixed-count.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        measurements: [23.5, 23.6, 23.4, 23.7, 23.3, 23.8, 23.2, 23.9], // 8 elements, expect 10
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatchObject({
      field: 'measurements',
      type: 'count',
      expectedCount: 10,
      actualCount: 8,
      message:
        "Array 'measurements' length 8 does not match expected elementCount 10",
    });
  });

  // Similar tests for more elements than expected, empty array...
});
```

### 4.7 Summary - Observation Validation Tests

**Total Tests:** 36 tests  
**Total Lines:** 540-660 lines

| Test Category           | Test Count | Lines | Priority     |
| ----------------------- | ---------- | ----- | ------------ |
| Type Mismatch           | 8          | 120   | **CRITICAL** |
| Missing Required Fields | 5          | 75    | **CRITICAL** |
| Extra Unexpected Fields | 3          | 45    | HIGH         |
| Constraint Violations   | 12         | 180   | **CRITICAL** |
| Nested Structures       | 5          | 75    | HIGH         |
| DataArray Element Count | 3          | 45    | HIGH         |

---

## 5. Command Validation Test Patterns

### 5.1 Type Mismatch Scenarios (5 tests)

**Priority:** **CRITICAL**

| Test ID     | Component Type      | Valid Type | Invalid Value   | Expected Message                                            |
| ----------- | ------------------- | ---------- | --------------- | ----------------------------------------------------------- |
| CMD-VAL-001 | Quantity (setpoint) | number     | "22.0" (string) | "Invalid type for 'setpoint': expected number, got string"  |
| CMD-VAL-002 | Category (mode)     | string     | 123 (number)    | "Invalid type for 'mode': expected string, got number"      |
| CMD-VAL-003 | Boolean (enabled)   | boolean    | "true" (string) | "Invalid type for 'enabled': expected boolean, got string"  |
| CMD-VAL-004 | Count (duration)    | integer    | 30.5 (float)    | "Invalid type for 'duration': expected integer, got number" |
| CMD-VAL-005 | DataRecord          | object     | [] (array)      | "Invalid type for 'settings': expected object, got array"   |

**Test Implementation (~75 lines, 5 tests)**

### 5.2 Missing Required Field Scenarios (3 tests)

**Priority:** **CRITICAL**

| Test ID     | Field Type        | Missing Field | Expected Message                      |
| ----------- | ----------------- | ------------- | ------------------------------------- |
| CMD-VAL-006 | Quantity          | setpoint      | "Missing required field 'setpoint'"   |
| CMD-VAL-007 | Category          | mode          | "Missing required field 'mode'"       |
| CMD-VAL-008 | Entire parameters | parameters    | "Missing required field 'parameters'" |

**Test Implementation (~45 lines, 3 tests)**

### 5.3 Constraint Violation Scenarios (8 tests)

**Priority:** **CRITICAL**

| Test ID     | Constraint Type         | Valid Range/Values              | Invalid Value | Expected Message                                                          |
| ----------- | ----------------------- | ------------------------------- | ------------- | ------------------------------------------------------------------------- |
| CMD-VAL-009 | Quantity interval       | [10, 30]                        | 35.0          | "Value 35.0 outside allowed interval [10, 30] for 'setpoint'"             |
| CMD-VAL-010 | Quantity interval       | [10, 30]                        | 5.0           | "Value 5.0 outside allowed interval [10, 30] for 'setpoint'"              |
| CMD-VAL-011 | Category allowedTokens  | ["heat", "cool", "auto", "off"] | "fan"         | "Value 'fan' not in allowed tokens for 'mode'"                            |
| CMD-VAL-012 | Count interval          | [0, 3600]                       | 5000          | "Value 5000 outside allowed interval [0, 3600] for 'duration'"            |
| CMD-VAL-013 | Feasibility constraint  | Device max temp 28°C            | 30.0          | "Value 30.0 exceeds device capability (max 28°C) for 'setpoint'"          |
| CMD-VAL-014 | Multiple constraints    | interval + feasibility          | 35.0          | "Multiple constraint violations for 'setpoint'"                           |
| CMD-VAL-015 | Nested field constraint | settings.temp                   | 50.0          | "Value 50.0 outside allowed interval for 'settings.temperature'"          |
| CMD-VAL-016 | Text pattern            | ^CMD-[0-9]{4}$                  | "CMD-ABC"     | "Value 'CMD-ABC' does not match pattern '^CMD-[0-9]{4}$' for 'commandId'" |

**Test Implementation (~120 lines, 8 tests)**

### 5.4 Nested Structure Scenarios (2 tests)

**Priority:** MEDIUM

| Test ID     | Nesting Type                | Error Location    | Expected Message                                                    |
| ----------- | --------------------------- | ----------------- | ------------------------------------------------------------------- |
| CMD-VAL-017 | DataRecord in DataRecord    | Nested field      | "Missing required field 'settings.advanced.pid.kp'"                 |
| CMD-VAL-018 | DataRecord with constraints | Nested constraint | "Value 1.5 outside allowed interval for 'settings.advanced.pid.kp'" |

**Test Implementation (~30 lines, 2 tests)**

### 5.5 Summary - Command Validation Tests

**Total Tests:** 18 tests  
**Total Lines:** 270-330 lines

| Test Category           | Test Count | Lines | Priority     |
| ----------------------- | ---------- | ----- | ------------ |
| Type Mismatch           | 5          | 75    | **CRITICAL** |
| Missing Required Fields | 3          | 45    | **CRITICAL** |
| Constraint Violations   | 8          | 120   | **CRITICAL** |
| Nested Structures       | 2          | 30    | MEDIUM       |

---

## 6. Schema Evolution Test Scenarios

> ⚠️ **REVIEW NOTICE (H10): Schema Evolution Tests Require Server State — Integration Testing**
>
> These 8 tests (Sections 6.1-6.2) use `client.createDataStream()`, `client.createObservation()`, then `client.updateDataStream()` expecting 409 Conflict. The 409 response depends on server state (whether the datastream has existing observations). This is inherently integration testing against a server, not client unit testing with mocked fetch. If schema evolution behavior needs client-side handling (e.g., catching 409 and presenting a user-friendly message), test the error handling path with a mocked 409 response — don't test whether the server produces 409.

### 6.1 Schema Change with Existing Data (4 tests)

**Priority:** **CRITICAL**

| Test ID     | Change Type             | Has Data         | Expected Result | Expected Status                                         |
| ----------- | ----------------------- | ---------------- | --------------- | ------------------------------------------------------- |
| SCH-EVO-001 | Modify resultSchema     | Has observations | 409 Conflict    | "Cannot modify schema when datastream has observations" |
| SCH-EVO-002 | Modify parametersSchema | Has commands     | 409 Conflict    | "Cannot modify schema when controlstream has commands"  |
| SCH-EVO-003 | Add optional field      | Has observations | 409 Conflict    | "Cannot modify schema when datastream has observations" |
| SCH-EVO-004 | Remove optional field   | Has observations | 409 Conflict    | "Cannot modify schema when datastream has observations" |

**Test Implementation (~60 lines, 4 tests):**

```typescript
describe('Schema Evolution - Changes with Existing Data', () => {
  it('should reject schema modification when observations exist', async () => {
    const client = new CSAPIClient(baseUrl);

    // Create DataStream
    const datastream = await client.createDataStream({
      uniqueIdentifier: 'urn:test:ds-001',
      resultSchema: {
        type: 'DataRecord',
        fields: [
          { name: 'temperature', type: 'Quantity', uom: { code: 'Cel' } },
        ],
      },
    });

    // Create observation
    await client.createObservation(datastream.id, {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: { temperature: 23.5 },
    });

    // Try to modify schema
    const modifiedSchema = {
      type: 'DataRecord',
      fields: [
        { name: 'temperature', type: 'Quantity', uom: { code: 'Cel' } },
        { name: 'humidity', type: 'Quantity', uom: { code: '%' } },
      ],
    };

    await expect(
      client.updateDataStream(datastream.id, { resultSchema: modifiedSchema })
    ).rejects.toThrow(
      /409.*Cannot modify schema when datastream has observations/
    );
  });

  // Similar tests for ControlStream, adding optional field, removing field...
});
```

### 6.2 Schema Change without Data (4 tests)

**Priority:** HIGH

| Test ID     | Change Type             | Has Data        | Expected Result | Expected Status |
| ----------- | ----------------------- | --------------- | --------------- | --------------- |
| SCH-EVO-005 | Modify resultSchema     | No observations | Success         | 200 OK          |
| SCH-EVO-006 | Modify parametersSchema | No commands     | Success         | 200 OK          |
| SCH-EVO-007 | Add optional field      | No observations | Success         | 200 OK          |
| SCH-EVO-008 | Remove optional field   | No observations | Success         | 200 OK          |

**Test Implementation (~60 lines, 4 tests)**

### 6.3 Summary - Schema Evolution Tests

**Total Tests:** 8 tests  
**Total Lines:** 120-150 lines

| Test Category              | Test Count | Lines | Priority     |
| -------------------------- | ---------- | ----- | ------------ |
| Changes with Existing Data | 4          | 60    | **CRITICAL** |
| Changes without Data       | 4          | 60    | HIGH         |

---

## 7. Error Message Validation Tests

### 7.1 Error Message Structure (4 tests)

**Priority:** HIGH

| Test ID     | Error Type           | Required Fields                                            | Expected Structure                                          |
| ----------- | -------------------- | ---------------------------------------------------------- | ----------------------------------------------------------- |
| ERR-MSG-001 | Type mismatch        | field, expectedType, actualType, message                   | Field name, expected type, actual type, descriptive message |
| ERR-MSG-002 | Missing field        | field, type, message                                       | Field name, "missing" type, descriptive message             |
| ERR-MSG-003 | Constraint violation | field, constraintType, expectedValue, actualValue, message | Constraint details                                          |
| ERR-MSG-004 | Multiple errors      | errors array                                               | All errors with individual structures                       |

**Test Implementation (~60 lines, 4 tests):**

```typescript
describe('Error Message Validation', () => {
  it('should provide detailed type mismatch error with expected and actual types', () => {
    const schema = loadSchemaFixture('datastream-weather.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        temperature: '23.5', // Invalid: string
        humidity: 65.0,
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors[0]).toMatchObject({
      field: 'temperature',
      type: 'type',
      expectedType: 'number',
      actualType: 'string',
      message: expect.stringContaining('expected number'),
    });
  });

  it('should provide constraint violation error with constraint details', () => {
    const schema = loadSchemaFixture('datastream-weather-constrained.json');
    const observation = {
      phenomenonTime: '2024-01-15T12:00:00Z',
      resultTime: '2024-01-15T12:00:01Z',
      result: {
        time: '2024-01-15T12:00:00Z',
        temperature: 150.0, // Outside [-50, 100]
        humidity: 65.0,
      },
    };

    const result = validateObservation(observation, schema);

    expect(result.valid).toBe(false);
    expect(result.errors[0]).toMatchObject({
      field: 'temperature',
      type: 'constraint',
      constraintType: 'interval',
      expectedValue: '[-50, 100]',
      actualValue: 150.0,
      message: expect.stringContaining('outside allowed interval'),
    });
  });

  // Similar tests for missing field, multiple errors...
});
```

### 7.2 Summary - Error Message Tests

**Total Tests:** 4 tests  
**Total Lines:** 60-80 lines

---

## 8. Fixture Requirements

### 8.1 DataStream Schema Fixtures (10 fixtures)

**Priority:** **CRITICAL**

| Fixture ID    | Description              | Component Types                                | Constraints             | Nesting  |
| ------------- | ------------------------ | ---------------------------------------------- | ----------------------- | -------- |
| DS-SCHEMA-001 | Simple weather           | Quantity (2), Time                             | interval                | None     |
| DS-SCHEMA-002 | Weather with category    | Quantity (2), Time, Category                   | interval, allowedTokens | None     |
| DS-SCHEMA-003 | Weather with parameters  | Quantity (2), Time + parametersSchema          | interval                | None     |
| DS-SCHEMA-004 | Nested station           | DataRecord (3 levels), Quantity (2)            | interval                | 3 levels |
| DS-SCHEMA-005 | Time series DataArray    | DataArray, Quantity                            | interval                | 1 level  |
| DS-SCHEMA-006 | Complex multi-type       | Quantity, Count, Boolean, Text, Time, Category | All types               | None     |
| DS-SCHEMA-007 | DataArray of DataRecords | DataArray, DataRecord, Quantity (2)            | interval                | 2 levels |
| DS-SCHEMA-008 | Text with pattern        | Text, Quantity                                 | pattern, interval       | None     |
| DS-SCHEMA-009 | Count with allowedValues | Count, Quantity                                | allowedValues, interval | None     |
| DS-SCHEMA-010 | SignificantFigures       | Quantity                                       | significantFigures      | None     |

### 8.2 ControlStream Schema Fixtures (5 fixtures)

**Priority:** HIGH

| Fixture ID    | Description         | Component Types                               | Constraints             | Nesting  |
| ------------- | ------------------- | --------------------------------------------- | ----------------------- | -------- |
| CS-SCHEMA-001 | Heater control      | Quantity (setpoint), Category (mode), Boolean | interval, allowedTokens | None     |
| CS-SCHEMA-002 | Motor control       | Quantity (speed), Count (duration), Boolean   | interval, interval      | None     |
| CS-SCHEMA-003 | Valve control       | Quantity (position), Category (state)         | interval, allowedTokens | None     |
| CS-SCHEMA-004 | Nested settings     | DataRecord (2 levels), Quantity (3)           | interval                | 2 levels |
| CS-SCHEMA-005 | Complex multi-param | Quantity, Count, Boolean, Text, Category      | All types               | None     |

### 8.3 Valid Observation Fixtures (15 fixtures)

**Priority:** **CRITICAL**

| Fixture ID    | Schema        | Description              | Result Structure           |
| ------------- | ------------- | ------------------------ | -------------------------- |
| OBS-VALID-001 | DS-SCHEMA-001 | Simple observation       | 3 fields                   |
| OBS-VALID-002 | DS-SCHEMA-002 | With category            | 4 fields                   |
| OBS-VALID-003 | DS-SCHEMA-003 | With parameters          | 3 fields + parameters      |
| OBS-VALID-004 | DS-SCHEMA-004 | Nested structure         | 3-level nesting            |
| OBS-VALID-005 | DS-SCHEMA-005 | DataArray (10 elements)  | Array of 10 Quantity       |
| OBS-VALID-006 | DS-SCHEMA-006 | All component types      | 6 different types          |
| OBS-VALID-007 | DS-SCHEMA-007 | DataArray of records (5) | Array of 5 DataRecords     |
| OBS-VALID-008 | DS-SCHEMA-001 | Edge value (min)         | Min constraint value       |
| OBS-VALID-009 | DS-SCHEMA-001 | Edge value (max)         | Max constraint value       |
| OBS-VALID-010 | DS-SCHEMA-008 | Valid pattern            | Matches regex pattern      |
| OBS-VALID-011 | DS-SCHEMA-009 | Allowed value            | In allowedValues list      |
| OBS-VALID-012 | DS-SCHEMA-010 | Valid sig figs           | 3 significant figures      |
| OBS-VALID-013 | DS-SCHEMA-005 | Large array (100)        | Array of 100 elements      |
| OBS-VALID-014 | DS-SCHEMA-005 | Empty array              | Array of 0 elements        |
| OBS-VALID-015 | DS-SCHEMA-003 | Optional field omitted   | Missing optional parameter |

### 8.4 Invalid Observation Fixtures (15 fixtures)

**Priority:** **CRITICAL**

| Fixture ID      | Schema        | Error Type             | Description                  |
| --------------- | ------------- | ---------------------- | ---------------------------- |
| OBS-INVALID-001 | DS-SCHEMA-001 | Type mismatch          | String instead of number     |
| OBS-INVALID-002 | DS-SCHEMA-001 | Missing field          | Required field absent        |
| OBS-INVALID-003 | DS-SCHEMA-001 | Extra field            | Unknown field present        |
| OBS-INVALID-004 | DS-SCHEMA-001 | Constraint (above max) | Value > max interval         |
| OBS-INVALID-005 | DS-SCHEMA-001 | Constraint (below min) | Value < min interval         |
| OBS-INVALID-006 | DS-SCHEMA-002 | Category not allowed   | Token not in allowedTokens   |
| OBS-INVALID-007 | DS-SCHEMA-008 | Pattern mismatch       | Doesn't match regex          |
| OBS-INVALID-008 | DS-SCHEMA-009 | Count not allowed      | Not in allowedValues         |
| OBS-INVALID-009 | DS-SCHEMA-010 | Sig figs exceeded      | Too many significant figures |
| OBS-INVALID-010 | DS-SCHEMA-004 | Nested missing field   | Deep nested field absent     |
| OBS-INVALID-011 | DS-SCHEMA-005 | Array count mismatch   | Length ≠ elementCount        |
| OBS-INVALID-012 | DS-SCHEMA-007 | Array element error    | Element missing field        |
| OBS-INVALID-013 | DS-SCHEMA-001 | Multiple errors        | Type + constraint errors     |
| OBS-INVALID-014 | DS-SCHEMA-006 | Wrong Boolean type     | String instead of boolean    |
| OBS-INVALID-015 | DS-SCHEMA-005 | Array type mismatch    | Object instead of array      |

### 8.5 Valid Command Fixtures (5 fixtures)

**Priority:** HIGH

| Fixture ID    | Schema        | Description     | Parameters Structure     |
| ------------- | ------------- | --------------- | ------------------------ |
| CMD-VALID-001 | CS-SCHEMA-001 | Heater command  | setpoint, mode, enabled  |
| CMD-VALID-002 | CS-SCHEMA-002 | Motor command   | speed, duration, enabled |
| CMD-VALID-003 | CS-SCHEMA-003 | Valve command   | position, state          |
| CMD-VALID-004 | CS-SCHEMA-004 | Nested settings | 2-level structure        |
| CMD-VALID-005 | CS-SCHEMA-005 | All types       | 5 parameter types        |

### 8.6 Invalid Command Fixtures (10 fixtures)

**Priority:** HIGH

| Fixture ID      | Schema        | Error Type            | Description               |
| --------------- | ------------- | --------------------- | ------------------------- |
| CMD-INVALID-001 | CS-SCHEMA-001 | Type mismatch         | String instead of number  |
| CMD-INVALID-002 | CS-SCHEMA-001 | Missing field         | Required parameter absent |
| CMD-INVALID-003 | CS-SCHEMA-001 | Constraint (above)    | Setpoint > max            |
| CMD-INVALID-004 | CS-SCHEMA-001 | Constraint (below)    | Setpoint < min            |
| CMD-INVALID-005 | CS-SCHEMA-001 | Mode not allowed      | Mode not in allowedTokens |
| CMD-INVALID-006 | CS-SCHEMA-002 | Duration out of range | Duration > max interval   |
| CMD-INVALID-007 | CS-SCHEMA-004 | Nested missing field  | Deep field absent         |
| CMD-INVALID-008 | CS-SCHEMA-004 | Nested constraint     | Deep field out of range   |
| CMD-INVALID-009 | CS-SCHEMA-001 | Multiple errors       | Type + constraint         |
| CMD-INVALID-010 | CS-SCHEMA-005 | Wrong type mix        | Multiple type errors      |

### 8.7 Fixture Summary

**Total Fixtures:** 60 fixtures

| Fixture Category      | Count | Priority     |
| --------------------- | ----- | ------------ |
| DataStream Schemas    | 10    | **CRITICAL** |
| ControlStream Schemas | 5     | HIGH         |
| Valid Observations    | 15    | **CRITICAL** |
| Invalid Observations  | 15    | **CRITICAL** |
| Valid Commands        | 5     | HIGH         |
| Invalid Commands      | 10    | HIGH         |

---

## 9. Implementation Estimates

### 9.1 Test Implementation Summary

| Test Category              | Test Count | Lines per Test | Total Lines | Priority     |
| -------------------------- | ---------- | -------------- | ----------- | ------------ |
| **Observation Validation** |
| Type Mismatch              | 8          | 15             | 120         | **CRITICAL** |
| Missing Required Fields    | 5          | 15             | 75          | **CRITICAL** |
| Extra Unexpected Fields    | 3          | 15             | 45          | HIGH         |
| Constraint Violations      | 12         | 15             | 180         | **CRITICAL** |
| Nested Structures          | 5          | 15             | 75          | HIGH         |
| DataArray Element Count    | 3          | 15             | 45          | HIGH         |
| **Subtotal**               | **36**     | **~15**        | **540**     |              |
| **Command Validation**     |
| Type Mismatch              | 5          | 15             | 75          | **CRITICAL** |
| Missing Required Fields    | 3          | 15             | 45          | **CRITICAL** |
| Constraint Violations      | 8          | 15             | 120         | **CRITICAL** |
| Nested Structures          | 2          | 15             | 30          | MEDIUM       |
| **Subtotal**               | **18**     | **~15**        | **270**     |              |
| **Schema Evolution**       |
| Changes with Data          | 4          | 15             | 60          | **CRITICAL** |
| Changes without Data       | 4          | 15             | 60          | HIGH         |
| **Subtotal**               | **8**      | **~15**        | **120**     |              |
| **Error Messages**         |
| Message Structure          | 4          | 15             | 60          | HIGH         |
| **Subtotal**               | **4**      | **~15**        | **60**      |              |
| **TOTAL**                  | **66**     | **~15**        | **990**     |              |

**Test File Organization:**

```
src/validation/
  observation-validation.spec.ts      (~540 lines, 36 tests)
  command-validation.spec.ts          (~270 lines, 18 tests)
  schema-evolution.spec.ts            (~120 lines, 8 tests)
  validation-error-messages.spec.ts   (~60 lines, 4 tests)

fixtures/validation/
  schemas/
    datastreams/                      (10 schema files)
    controlstreams/                   (5 schema files)
  observations/
    valid/                            (15 observation files)
    invalid/                          (15 observation files)
  commands/
    valid/                            (5 command files)
    invalid/                          (10 command files)
```

### 9.2 Implementation Effort Estimates

**Development Tasks:**

| Task                         | Estimated Lines       | Estimated Time  |
| ---------------------------- | --------------------- | --------------- |
| Schema validation utilities  | 200-300               | 4-6 hours       |
| Observation validation tests | 540-660               | 8-12 hours      |
| Command validation tests     | 270-330               | 4-6 hours       |
| Schema evolution tests       | 120-150               | 2-3 hours       |
| Error message tests          | 60-80                 | 1-2 hours       |
| Fixture creation             | 60 files              | 8-10 hours      |
| Documentation                | 50-100                | 1-2 hours       |
| **TOTAL**                    | **1,240-1,620 lines** | **28-41 hours** |

**Testing Priorities:**

1. **CRITICAL (Priority 1):** 46 tests, ~675 lines, 12-18 hours

   - Type mismatch validation (all component types)
   - Missing required field validation
   - Constraint violation validation
   - Schema evolution with existing data

2. **HIGH (Priority 2):** 16 tests, ~255 lines, 6-9 hours

   - Extra field handling
   - Nested structure validation
   - DataArray element count
   - Schema evolution without data
   - Error message structure

3. **MEDIUM (Priority 3):** 4 tests, ~60 lines, 1-2 hours
   - Complex nesting (3+ levels)
   - Advanced constraint scenarios

---

## 10. Validation Workflow

### 10.1 Client-Side Validation Flow

```typescript
class CSAPIClient {
  async createObservation(
    dataStreamId: string,
    observation: Observation,
    options?: { validate?: boolean; strict?: boolean }
  ): Promise<Observation> {
    const validate = options?.validate !== false; // Default: true
    const strict = options?.strict ?? true; // Default: strict mode

    if (validate) {
      // Fetch DataStream schema
      const dataStream = await this.getDataStream(dataStreamId);
      const schema = dataStream.resultSchema;

      // Validate observation result against schema
      const result = this.validateObservationResult(
        observation.result,
        schema,
        { strict }
      );

      if (!result.valid) {
        throw new ValidationError(
          'Observation validation failed',
          result.errors
        );
      }

      if (!strict && result.warnings.length > 0) {
        console.warn('Observation validation warnings:', result.warnings);
      }
    }

    // Submit observation
    const response = await this.post(
      `/datastreams/${dataStreamId}/observations`,
      observation
    );

    return response.data;
  }

  private validateObservationResult(
    result: any,
    schema: DataStreamSchema,
    options: { strict: boolean }
  ): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Validate against SWE Common schema
    if (schema.type === 'DataRecord') {
      this.validateDataRecord(result, schema, errors, warnings, options);
    } else if (schema.type === 'DataArray') {
      this.validateDataArray(result, schema, errors, warnings, options);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  private validateDataRecord(
    result: any,
    schema: DataRecord,
    errors: ValidationError[],
    warnings: ValidationWarning[],
    options: { strict: boolean }
  ): void {
    // Check type
    if (typeof result !== 'object' || Array.isArray(result)) {
      errors.push({
        field: schema.name || 'result',
        type: 'type',
        expectedType: 'object',
        actualType: Array.isArray(result) ? 'array' : typeof result,
        message: `Invalid type for '${
          schema.name || 'result'
        }': expected object, got ${typeof result}`,
      });
      return;
    }

    // Check required fields
    for (const field of schema.fields) {
      const value = result[field.name];

      if (value === undefined && !field.optional) {
        errors.push({
          field: field.name,
          type: 'missing',
          message: `Missing required field '${field.name}'`,
        });
        continue;
      }

      if (value !== undefined) {
        // Validate field type and constraints
        this.validateField(field, value, errors, warnings, options);
      }
    }

    // Check for extra fields (strict mode)
    if (options.strict) {
      const allowedFields = new Set(schema.fields.map((f) => f.name));
      for (const key of Object.keys(result)) {
        if (!allowedFields.has(key)) {
          errors.push({
            field: key,
            type: 'extra',
            message: `Unknown field '${key}' not in schema`,
          });
        }
      }
    } else {
      // Warn about extra fields (lenient mode)
      const allowedFields = new Set(schema.fields.map((f) => f.name));
      for (const key of Object.keys(result)) {
        if (!allowedFields.has(key)) {
          warnings.push({
            field: key,
            type: 'extra',
            message: `Extra field '${key}' ignored`,
          });
        }
      }
    }
  }

  private validateField(
    field: Field,
    value: any,
    errors: ValidationError[],
    warnings: ValidationWarning[],
    options: { strict: boolean }
  ): void {
    // Type validation
    switch (field.type) {
      case 'Quantity':
        if (typeof value !== 'number') {
          errors.push({
            field: field.name,
            type: 'type',
            expectedType: 'number',
            actualType: typeof value,
            message: `Invalid type for '${
              field.name
            }': expected number, got ${typeof value}`,
          });
          return;
        }
        break;

      case 'Count':
        if (!Number.isInteger(value)) {
          errors.push({
            field: field.name,
            type: 'type',
            expectedType: 'integer',
            actualType: typeof value,
            message: `Invalid type for '${
              field.name
            }': expected integer, got ${typeof value}`,
          });
          return;
        }
        break;

      case 'Boolean':
        if (typeof value !== 'boolean') {
          errors.push({
            field: field.name,
            type: 'type',
            expectedType: 'boolean',
            actualType: typeof value,
            message: `Invalid type for '${
              field.name
            }': expected boolean, got ${typeof value}`,
          });
          return;
        }
        break;

      case 'Text':
      case 'Category':
        if (typeof value !== 'string') {
          errors.push({
            field: field.name,
            type: 'type',
            expectedType: 'string',
            actualType: typeof value,
            message: `Invalid type for '${
              field.name
            }': expected string, got ${typeof value}`,
          });
          return;
        }
        break;

      case 'Time':
        if (typeof value !== 'string') {
          errors.push({
            field: field.name,
            type: 'type',
            expectedType: 'string (ISO 8601)',
            actualType: typeof value,
            message: `Invalid type for '${
              field.name
            }': expected ISO 8601 string, got ${typeof value}`,
          });
          return;
        }
        break;

      case 'DataRecord':
        if (typeof value !== 'object' || Array.isArray(value)) {
          errors.push({
            field: field.name,
            type: 'type',
            expectedType: 'object',
            actualType: Array.isArray(value) ? 'array' : typeof value,
            message: `Invalid type for '${
              field.name
            }': expected object, got ${typeof value}`,
          });
          return;
        }
        // Recursive validation
        this.validateDataRecord(value, field, errors, warnings, options);
        break;

      case 'DataArray':
        if (!Array.isArray(value)) {
          errors.push({
            field: field.name,
            type: 'type',
            expectedType: 'array',
            actualType: typeof value,
            message: `Invalid type for '${
              field.name
            }': expected array, got ${typeof value}`,
          });
          return;
        }
        // Validate array elements
        this.validateDataArray(value, field, errors, warnings, options);
        break;
    }

    // Constraint validation
    if (field.constraint) {
      this.validateConstraints(field, value, errors);
    }
  }

  private validateConstraints(
    field: Field,
    value: any,
    errors: ValidationError[]
  ): void {
    const constraint = field.constraint;

    // Interval constraint (Quantity, Count, Time)
    if (constraint.interval) {
      const [min, max] = constraint.interval;
      if (value < min || value > max) {
        errors.push({
          field: field.name,
          type: 'constraint',
          constraintType: 'interval',
          expectedValue: `[${min}, ${max}]`,
          actualValue: value,
          message: `Value ${value} outside allowed interval [${min}, ${max}] for '${field.name}'`,
        });
      }
    }

    // AllowedTokens constraint (Category, Text)
    if (constraint.allowedTokens) {
      if (!constraint.allowedTokens.includes(value)) {
        errors.push({
          field: field.name,
          type: 'constraint',
          constraintType: 'allowedTokens',
          expectedValue: constraint.allowedTokens,
          actualValue: value,
          message: `Value '${value}' not in allowed tokens [${constraint.allowedTokens.join(
            ', '
          )}] for '${field.name}'`,
        });
      }
    }

    // Pattern constraint (Text)
    if (constraint.pattern) {
      const regex = new RegExp(constraint.pattern);
      if (!regex.test(value)) {
        errors.push({
          field: field.name,
          type: 'constraint',
          constraintType: 'pattern',
          expectedValue: constraint.pattern,
          actualValue: value,
          message: `Value '${value}' does not match pattern '${constraint.pattern}' for '${field.name}'`,
        });
      }
    }

    // SignificantFigures constraint (Quantity)
    if (constraint.significantFigures) {
      const sigFigs = this.countSignificantFigures(value);
      if (sigFigs > constraint.significantFigures) {
        errors.push({
          field: field.name,
          type: 'constraint',
          constraintType: 'significantFigures',
          expectedValue: constraint.significantFigures,
          actualValue: sigFigs,
          message: `Value ${value} has more than ${constraint.significantFigures} significant figures for '${field.name}'`,
        });
      }
    }

    // AllowedValues constraint (Count)
    if (constraint.allowedValues) {
      if (!constraint.allowedValues.includes(value)) {
        errors.push({
          field: field.name,
          type: 'constraint',
          constraintType: 'allowedValues',
          expectedValue: constraint.allowedValues,
          actualValue: value,
          message: `Value ${value} not in allowed values [${constraint.allowedValues.join(
            ', '
          )}] for '${field.name}'`,
        });
      }
    }
  }

  private validateDataArray(
    result: any[],
    schema: DataArray,
    errors: ValidationError[],
    warnings: ValidationWarning[],
    options: { strict: boolean }
  ): void {
    // Check elementCount
    if (schema.elementCount && result.length !== schema.elementCount.value) {
      errors.push({
        field: schema.name || 'array',
        type: 'count',
        expectedCount: schema.elementCount.value,
        actualCount: result.length,
        message: `Array '${schema.name || 'array'}' length ${
          result.length
        } does not match expected elementCount ${schema.elementCount.value}`,
      });
    }

    // Validate each element
    for (let i = 0; i < result.length; i++) {
      const element = result[i];
      const elementField = {
        ...schema.elementType,
        name: `${schema.name || 'array'}[${i}]`,
      };

      this.validateField(elementField, element, errors, warnings, options);
    }
  }

  private countSignificantFigures(value: number): number {
    // Remove trailing zeros after decimal point
    const str = value.toString().replace(/\.?0+$/, '');
    // Remove decimal point
    const digits = str.replace('.', '').replace('-', '');
    return digits.length;
  }
}
```

### 10.2 Server-Side Validation (API Behavior)

> ⚠️ **REVIEW NOTICE (M5): Server-Side Validation Documentation — Not Client Behavior**
>
> This section explicitly describes server behavior: "Receive observation", "Fetch DataStream schema", "Validate result against resultSchema", "Return 400 Bad Request if validation fails." This is server compliance documentation, not client behavior testing. Useful as reference context for understanding the API contract, but should not be the basis for client test assertions. Client tests should verify: the client's `validateObservation()` function catches schema mismatches BEFORE sending the request.

**POST /datastreams/{id}/observations:**

1. **Receive observation** with result object
2. **Fetch DataStream schema** (resultSchema, parametersSchema)
3. **Validate result** against resultSchema
   - Type matching
   - Required fields present
   - Constraint enforcement
4. **Validate parameters** (if present) against parametersSchema
5. **Return 400 Bad Request** if validation fails with detailed error message
6. **Return 201 Created** if validation succeeds

**Example Error Response:**

```json
{
  "code": "InvalidParameterValue",
  "description": "Observation result does not match DataStream schema",
  "details": {
    "field": "temperature",
    "expectedType": "number",
    "actualType": "string",
    "expectedValue": "numeric value in range [-50, 100]",
    "actualValue": "twenty-three"
  }
}
```

---

## 11. References

### 11.1 Specifications

- **CSAPI Part 2 Specification:** OGC 23-002 (Connected Systems API - Part 2: Dynamic Data) — https://docs.ogc.org/is/23-002/23-002.html
- **SWE Common 3.0:** OGC 24-014 (Sensor Web Enablement Common Data Model 3.0)
- **JSON Schema Specification:** draft-07

### 11.2 Related Research

- **Section 8:** CSAPI Specification Test Requirements (validation rules)
- **Section 10:** SWE Common Testing Requirements (schema structure, component types)
- **Section 12:** QueryBuilder Testing Strategy (schema endpoints)
- **Section 16:** Worker Extensions Testing (VALIDATE_OBSERVATIONS, VALIDATE_COMMANDS)

### 11.3 Implementation References

- Part 2 Requirements: `csapi-part2-requirements.md` (DataStream/ControlStream schemas)
- Format Requirements: `csapi-format-requirements.md` (SWE Common validation)
- Usage Scenarios: `csapi-usage-scenarios.md` (validateObservationSchema convenience method)
- CRUD Operations: `csapi-crud-operations.md` (schema validation constraints)

---

## 12. Appendices

### Appendix A: Schema Validation Rules Matrix

| Rule ID | Component Type | Validation Check            | Error Type             | Priority     |
| ------- | -------------- | --------------------------- | ---------------------- | ------------ |
| VAL-001 | Quantity       | Value is numeric            | Type error             | **CRITICAL** |
| VAL-002 | Quantity       | Value within interval       | Constraint error       | **CRITICAL** |
| VAL-003 | Quantity       | SignificantFigures limit    | Constraint error       | MEDIUM       |
| VAL-004 | Count          | Value is integer            | Type error             | HIGH         |
| VAL-005 | Count          | Value within interval       | Constraint error       | HIGH         |
| VAL-006 | Count          | Value in allowedValues      | Constraint error       | MEDIUM       |
| VAL-007 | Boolean        | Value is boolean            | Type error             | HIGH         |
| VAL-008 | Text           | Value is string             | Type error             | HIGH         |
| VAL-009 | Text           | Value in allowedTokens      | Constraint error       | MEDIUM       |
| VAL-010 | Text           | Value matches pattern       | Constraint error       | MEDIUM       |
| VAL-011 | Time           | Value is ISO 8601 string    | Type error             | **CRITICAL** |
| VAL-012 | Time           | Value within time interval  | Constraint error       | MEDIUM       |
| VAL-013 | Category       | Value is string             | Type error             | MEDIUM       |
| VAL-014 | Category       | Value in allowedTokens      | Constraint error       | MEDIUM       |
| VAL-015 | DataRecord     | Value is object             | Type error             | **CRITICAL** |
| VAL-016 | DataRecord     | All required fields present | Missing error          | **CRITICAL** |
| VAL-017 | DataRecord     | No extra fields (strict)    | Extra error            | HIGH         |
| VAL-018 | DataArray      | Value is array              | Type error             | **CRITICAL** |
| VAL-019 | DataArray      | Length matches elementCount | Count error            | HIGH         |
| VAL-020 | DataArray      | Elements match elementType  | Type/constraint errors | **CRITICAL** |

### Appendix B: Error Message Templates

**Type Mismatch:**

```
"Invalid type for '{fieldName}': expected {expectedType}, got {actualType}"
```

**Missing Field:**

```
"Missing required field '{fieldName}'"
```

**Extra Field (Strict):**

```
"Unknown field '{fieldName}' not in schema"
```

**Extra Field (Lenient):**

```
"Extra field '{fieldName}' ignored"
```

**Constraint Violation (Interval):**

```
"Value {actualValue} outside allowed interval [{min}, {max}] for '{fieldName}'"
```

**Constraint Violation (AllowedTokens):**

```
"Value '{actualValue}' not in allowed tokens [{tokens}] for '{fieldName}'"
```

**Constraint Violation (Pattern):**

```
"Value '{actualValue}' does not match pattern '{pattern}' for '{fieldName}'"
```

**Constraint Violation (SignificantFigures):**

```
"Value {actualValue} has more than {maxFigures} significant figures for '{fieldName}'"
```

**Constraint Violation (AllowedValues):**

```
"Value {actualValue} not in allowed values [{values}] for '{fieldName}'"
```

**Array Count Mismatch:**

```
"Array '{arrayName}' length {actualLength} does not match expected elementCount {expectedCount}"
```

**Nested Field Error:**

```
"{errorType} at '{parentName}.{childName}.{fieldName}': {message}"
```

**Array Element Error:**

```
"Element {index} {errorType} in '{arrayName}': {message}"
```

**Schema Evolution Error:**

```
"Cannot modify schema when datastream has observations"
"Cannot modify schema when controlstream has commands"
```

---

**End of Document**
