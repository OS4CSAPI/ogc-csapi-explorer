# Section 18: Error Condition Testing Strategy

> ⚠️ **REVIEW NOTICE — LOW (L1, L2): Scope Items — Binary Error Test Specificity and Worker Errors**
>
> **Phase 2E Review | Issues: L1, L2 | Severity: LOW**
>
> This document is largely well-structured for client-side error testing. Two sections may need refinement:
>
> - **Section 4.2.3** (SWE Common Binary Encoding Errors, ~23-25 tests): These specific binary error test scenarios (endianness, buffer truncation, data type codes) may be speculative and need refinement once binary parsing is implemented. **Clarification:** Binary SWE parsing itself IS in scope per the implementation guide §7 and Phase 2D assessment (Doc 10, M2/P4: "sound and directly usable"). This L1 flag is about error test specificity only.
> - **Section 4.5** (Worker Extension Errors, ~7 tests): Worker error scenarios (initialization failure, timeout, premature termination) reference infrastructure that doesn't exist yet.
>
> **What's usable now:** Sections 4.1 (QueryBuilder errors), 4.2.1 (GeoJSON parser errors), 4.2.2 (SensorML parser errors), 4.3 (Resource method errors), 4.4 (Integration workflow errors), Section 5 (Error test pattern design).
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

**Research Plan:** [Research Plan 18: Error Condition Testing Strategy](../research-plans/18-error-condition-testing.md)

**Research Questions:** 7 core questions about error types to test (validation, network, parse, conformance), meaningful error messages, CSAPI spec-defined error conditions, resource validation errors, malformed data errors in parsers, missing/invalid query parameter errors, and consistent error test structure

**Methodology:** 6-phase systematic analysis (Phase 1: Error Taxonomy categorizing error types → Phase 2: Upstream Error Pattern Analysis of existing error handling → Phase 3: CSAPI Error Specification Analysis from OpenAPI schemas → Phase 4: Component-Specific Error Scenarios for QueryBuilder/parsers/resources/workflows → Phase 5: Error Test Pattern Design with consistent templates → Phase 6: Synthesis into comprehensive error testing strategy)

**Research Time:** 120 minutes (February 6, 2026)

**Primary Source(s):**

- [Error Handling Design Analysis](../../upstream/error-handling-analysis.md)
- [CSAPI Part 1 OpenAPI Specification](../../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) (error schemas)
- [CSAPI Part 2 OpenAPI Specification](../../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) (error schemas)

**Supporting Resources:**

- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream error test patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (error handling patterns)
- Section 12: [QueryBuilder Testing Strategy](12-querybuilder-testing-strategy.md) (validation error scenarios)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (resource error scenarios)
- Section 14: [Integration Test Workflow Design](14-integration-test-workflow-design.md) (workflow error scenarios)

**Document Purpose:** Establishes comprehensive error testing strategy covering 5 error categories (Validation, Network, Parse, Conformance, HTTP) with ~280-320 test scenarios, consistent test patterns, and minimal targeted error handling philosophy aligned with upstream patterns

---

## Executive Summary

This research establishes a comprehensive error testing strategy for the CSAPI client library, systematically categorizing all error types, defining test patterns, and ensuring meaningful error messages guide developers to correct usage. Key findings:

- **Error Philosophy:** Minimal, targeted error handling following upstream patterns (throw only when library can't proceed)
- **Error Taxonomy:** 5 primary error categories (Validation, Network, Parse, Conformance, HTTP)
- **Test Coverage:** ~280-320 error test scenarios across all components
- **Error Classes:** Reuse existing `EndpointError` and native `Error` (no new error classes needed)
- **Test Patterns:** Consistent assertion structure with clear error message validation

**Impact:** Ensures comprehensive error testing with ~20% of total test effort dedicated to error scenarios, providing clear diagnostics for developers.

---

## 1. Error Taxonomy

### 1.1 Error Categories

Based on upstream analysis, CSAPI errors fall into 5 primary categories:

| Category        | Description                                       | Responsibility           | Examples                                                                         |
| --------------- | ------------------------------------------------- | ------------------------ | -------------------------------------------------------------------------------- |
| **Validation**  | Client-side parameter validation before API calls | Library                  | Invalid bbox (minLon > maxLon), malformed ISO 8601 datetime, missing required ID |
| **Conformance** | Endpoint capabilities vs requested operations     | Library                  | Calling `getDataStreams()` when endpoint doesn't support Part 2 CSAPI            |
| **Network**     | HTTP connection failures, timeouts, CORS          | User/Browser (propagate) | DNS resolution failure, connection timeout, CORS policy violation                |
| **Parse**       | Response parsing failures                         | Library                  | Malformed GeoJSON, invalid SensorML XML, SWE Common schema violations            |
| **HTTP**        | Server-side errors via HTTP status codes          | Server (propagate)       | 404 Not Found, 400 Bad Request, 500 Internal Server Error                        |

### 1.2 Error Handling Philosophy

**From [Error Handling Design Analysis](../../upstream/error-handling-analysis.md):**

> ogc-client uses **minimal, targeted error handling**:
>
> 1. Throw errors for library-detectable problems
> 2. Let HTTP errors propagate naturally
> 3. Use specific error types for different categories
> 4. Validate only what's necessary for library correctness
> 5. Trust servers to validate their own requirements

**CSAPI follows this philosophy:**

✅ **Library throws when:**

- Endpoint doesn't support requested CSAPI feature (conformance check)
- Parameter values are logically invalid (e.g., minLon > maxLon, start > end)
- Required links are missing from collection/resource metadata
- Response parsing fails (malformed GeoJSON, invalid SensorML)

❌ **Library does NOT throw for:**

- Resource ID format validation (trust TypeScript types)
- Server-side constraint validation (limit ranges, field existence)
- Optional parameter validation beyond type checking
- HTTP status codes (let browser/user handle)

### 1.3 Error Taxonomy Matrix

| Error Type      | Subtype                     | Where Thrown | Error Class     | HTTP Status       | Test Priority        |
| --------------- | --------------------------- | ------------ | --------------- | ----------------- | -------------------- |
| **Validation**  | Invalid bbox                | QueryBuilder | Error           | N/A (client-side) | CRITICAL             |
| **Validation**  | Invalid temporal interval   | QueryBuilder | Error           | N/A (client-side) | CRITICAL             |
| **Validation**  | Missing required parameter  | QueryBuilder | Error           | N/A (client-side) | HIGH                 |
| **Conformance** | CSAPI not supported         | Endpoint     | EndpointError   | N/A (client-side) | CRITICAL             |
| **Conformance** | Resource type unavailable   | QueryBuilder | EndpointError   | N/A (client-side) | CRITICAL             |
| **Conformance** | Required link missing       | QueryBuilder | EndpointError   | N/A (client-side) | HIGH                 |
| **Parse**       | Malformed GeoJSON           | Parser       | Error           | N/A (parsing)     | HIGH                 |
| **Parse**       | Invalid SensorML            | Parser       | Error           | N/A (parsing)     | HIGH                 |
| **Parse**       | SWE Common schema violation | Parser       | Error           | N/A (parsing)     | HIGH                 |
| **Network**     | Connection timeout          | fetch        | Native Error    | 0                 | LOW (user handles)   |
| **Network**     | DNS resolution failure      | fetch        | Native Error    | 0                 | LOW (user handles)   |
| **Network**     | CORS violation              | fetch        | Native Error    | 0                 | MEDIUM (detectable)  |
| **HTTP**        | 404 Not Found               | Server       | N/A (propagate) | 404               | LOW (server handles) |
| **HTTP**        | 400 Bad Request             | Server       | N/A (propagate) | 400               | LOW (server handles) |
| **HTTP**        | 500 Internal Server Error   | Server       | N/A (propagate) | 500               | LOW (server handles) |

**Total Error Categories:** 15 error types  
**Test Priority Distribution:**

- CRITICAL: 4 error types (~40% of error tests)
- HIGH: 4 error types (~35% of error tests)
- MEDIUM: 1 error type (~10% of error tests)
- LOW: 6 error types (~15% of error tests)

---

## 2. Upstream Error Pattern Analysis

### 2.1 Error Classes in ogc-client

**From `src/shared/errors.ts`:**

```typescript
// Error Class 1: General endpoint/capability errors
export class EndpointError extends Error {
  constructor(
    message: string,
    public readonly httpStatus?: number,
    public readonly isCrossOriginRelated?: boolean
  ) {
    super(message);
    this.name = 'EndpointError';
  }
}

// Error Class 2: OWS XML exception reports (WMS/WFS only)
export class ServiceExceptionError extends Error {
  constructor(message: string, public readonly httpStatus: number) {
    super(message);
    this.name = 'ServiceExceptionError';
  }
}
```

**CSAPI Usage:** Reuse `EndpointError` for conformance and resource availability errors. Do NOT create custom CSAPI error classes.

### 2.2 Error Patterns from EDR Implementation

#### Pattern 1: Conformance Check at Entry Point

```typescript
// From endpoint.ts
public async edr(collection_id: string): Promise<EDRQueryBuilder> {
  if (!this.hasEnvironmentalDataRetrieval) {
    throw new EndpointError('Endpoint does not support EDR');
  }
  // ... proceed
}
```

**Test Pattern:**

```typescript
it('throws error when EDR not supported', async () => {
  await expect(endpoint.edr('test-collection')).rejects.toThrow(
    /Endpoint does not support EDR/
  );
});
```

#### Pattern 2: Validate Parameters at Use

```typescript
// From edr/url_builder.ts
buildPositionDownloadUrl(
  coords: WellKnownTextString,
  optional_params: optionalPositionParams = {}
): string {
  // Check query type support
  if (!this.supported_query_types.position) {
    throw new Error('Collection does not support position queries');
  }

  // Validate parameter names
  if (optional_params.parameter_name) {
    for (const parameter of optional_params.parameter_name) {
      if (!this.supported_parameters[parameter]) {
        throw new Error(
          `The following parameter name does not exist on this collection: '${parameter}'.`
        );
      }
    }
  }

  // Validate CRS
  if (optional_params.crs !== undefined) {
    if (!this.supported_crs.includes(optional_params.crs)) {
      throw new Error(
        `The following crs does not exist on this collection: '${optional_params.crs}'.`
      );
    }
  }

  return url.toString();
}
```

**Test Pattern:**

```typescript
describe('Parameter validation', () => {
  it('throws error when query type not supported', () => {
    expect(() => builder.buildPositionDownloadUrl('POINT(0 0)')).toThrow(
      /does not support position queries/
    );
  });

  it('throws error when parameter name invalid', () => {
    expect(() =>
      builder.buildAreaDownloadUrl('POLYGON(...)', {
        parameter_name: ['invalid_param'],
      })
    ).toThrow(/parameter name does not exist.*'invalid_param'/);
  });

  it('throws error when CRS not supported', () => {
    expect(() =>
      builder.buildAreaDownloadUrl('POLYGON(...)', {
        crs: 'EPSG:9999',
      })
    ).toThrow(/crs does not exist.*'EPSG:9999'/);
  });
});
```

#### Pattern 3: Assert Required Links

```typescript
// From shared/link-utils.ts
export function assertHasLinks(
  doc: OgcApiDocument,
  relType: string | string[]
) {
  if (!hasLinks(doc, relType)) {
    throw new EndpointError(`Could not find link with type: ${relType}`);
  }
}
```

**Test Pattern:**

```typescript
it('throws error when required link missing', () => {
  const doc = { links: [] };
  expect(() => assertHasLinks(doc, 'service-doc')).toThrow(
    /Could not find link with type: service-doc/
  );
});
```

#### Pattern 4: Warn Instead of Error (Optional Features)

```typescript
// From endpoint.ts
if (options?.outputFormat && !linkWithFormat) {
  console.warn(
    `[ogc-client] The following output format type was not found in the collection '${collectionId}': ${options.outputFormat}`
  );
  // Still add as query parameter (server may support it)
  url.searchParams.set('f', options.outputFormat);
}
```

**Test Pattern:**

```typescript
it('warns but continues when optional format not found', async () => {
  const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

  const url = builder.getSystems({ f: 'invalid-format' });

  expect(consoleSpy).toHaveBeenCalledWith(
    expect.stringContaining('output format type was not found')
  );
  expect(url).toContain('f=invalid-format'); // Still added to URL

  consoleSpy.mockRestore();
});
```

### 2.3 Error Message Guidelines

**From upstream analysis:**

✅ **GOOD Error Messages:**

- Clear and actionable
- Include context (collection ID, parameter name, etc.)
- Suggest resolution when possible

```typescript
// Good examples:
throw new EndpointError('Endpoint does not support Connected Systems API');
throw new EndpointError(`Collection not found: ${collectionId}`);
throw new Error(
  `The following parameter name does not exist on this collection: '${parameter}'.`
);
```

❌ **BAD Error Messages:**

- Too vague
- Too prescriptive
- No context

```typescript
// Bad examples:
throw new Error('Invalid input');
throw new Error('Operation failed');
throw new Error(
  'The systemId parameter must be a valid UUID matching RFC 4122'
);
```

---

## 3. CSAPI Error Specification Analysis

### 3.1 HTTP Error Responses from OpenAPI Specification

**From `ogcapi-connectedsystems-1.bundled.oas31.yaml`:**

```yaml
responses:
  '400':
    description: Bad request. Either the query parameters or the content body are invalid.
  '401':
    description: No authentication information was provided.
  '403':
    description: The user doesn't have the necessary permissions to access the resource.
  '404':
    description: No resource was found with the specified URL.
  '5XX':
    description: Unexpected server error. Only retry on 502 and 503.
```

**HTTP Status Code Matrix:**

| Status Code | Meaning               | When                             | Library Action             | Test Priority              |
| ----------- | --------------------- | -------------------------------- | -------------------------- | -------------------------- |
| **200**     | Success               | Valid request, resource found    | Parse response             | HIGH (happy path)          |
| **201**     | Created               | POST/PUT successful              | Return Location header     | HIGH (creation)            |
| **400**     | Bad Request           | Invalid query parameters or body | Propagate (server error)   | LOW (server validates)     |
| **401**     | Unauthorized          | Missing authentication           | Propagate (user handles)   | LOW (auth out of scope)    |
| **403**     | Forbidden             | Insufficient permissions         | Propagate (user handles)   | LOW (auth out of scope)    |
| **404**     | Not Found             | Resource doesn't exist           | Propagate (server error)   | MEDIUM (integration tests) |
| **500**     | Internal Server Error | Server failure                   | Propagate (server error)   | LOW (server issue)         |
| **502**     | Bad Gateway           | Upstream server error            | Propagate (retry possible) | LOW (infrastructure)       |
| **503**     | Service Unavailable   | Server overloaded                | Propagate (retry possible) | LOW (infrastructure)       |

**Testing Strategy:**

- **200/201**: Test extensively (success cases)
- **404**: Test in integration tests (resource not found scenarios)
- **400/401/403/500/502/503**: Low priority (server/infrastructure responsibility)

### 3.2 CSAPI Error Schemas

**From OpenAPI spec:**

The CSAPI specification does NOT define custom error response schemas (e.g., RFC 7807 Problem Details). Errors are communicated via:

1. **HTTP status codes** (standard semantics)
2. **HTTP reason phrases** (standard messages)
3. **Response body** (optional, server-specific)

**Implication:** Library should NOT attempt to parse error response bodies. Let HTTP status codes communicate errors naturally.

---

## 4. Component-Specific Error Scenarios

### 4.1 QueryBuilder (URL Builder) Error Scenarios

**From [Section 12: QueryBuilder Testing Strategy](./12-querybuilder-testing-strategy.md):**

| Error Condition                    | Test Scenario                                                                    | Expected Behavior                                                        | Test Count                                              | Priority |
| ---------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------- | -------- |
| **Resource unavailable**           | Call method when resource type not in conformance                                | Throw EndpointError: "Collection does not support '{resource}' resource" | 9 (1 per resource)                                      | CRITICAL |
| **Invalid bbox**                   | Pass bbox with minLon > maxLon or minLat > maxLat                                | Throw Error: "Invalid bbox: min must be < max"                           | 2                                                       | HIGH     |
| **Invalid temporal interval**      | Pass datetime with start > end                                                   | Throw Error: "Invalid datetime: start must be before end"                | 2                                                       | HIGH     |
| **Missing required ID**            | Omit required ID parameter (e.g., `getSystem()` with no ID)                      | TypeScript compile error (caught at compile time)                        | 0 (TS only)                                             | N/A      |
| **Null/undefined optional params** | Pass null or undefined for optional parameters                                   | Omit from URL (no error)                                                 | 9 (1 per resource)                                      | MEDIUM   |
| **Already encoded value**          | Pass double-encoded value (e.g., `%2520` for space)                              | Handle gracefully (no double-encoding)                                   | 3                                                       | LOW      |
| **Very long URL**                  | Construct URL with 100+ query parameters                                         | Handle gracefully (browser handles length limits)                        | 1                                                       | LOW      |
| **Part 2 method when Part 1 only** | Call Part 2 method (e.g., `getDataStreams()`) when endpoint only supports Part 1 | Throw EndpointError: "Endpoint does not support Part 2"                  | 4 (DataStreams, Observations, ControlStreams, Commands) | CRITICAL |

**Total QueryBuilder Error Tests:** ~30 tests

**Test Organization:** Include 3-4 error tests per resource type file (e.g., `url_builder-systems.spec.ts`).

### 4.2 Parser Error Scenarios

#### 4.2.1 GeoJSON Parser Errors

| Error Condition           | Test Scenario                                                         | Expected Error                                          | Test Count        | Priority |
| ------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- | ----------------- | -------- |
| **Malformed JSON**        | Parse invalid JSON string                                             | SyntaxError (from JSON.parse)                           | 1                 | HIGH     |
| **Missing type**          | Parse object without `type: "Feature"` or `type: "FeatureCollection"` | Error: "Invalid GeoJSON: missing type"                  | 2                 | HIGH     |
| **Invalid geometry type** | Parse geometry with unknown type (e.g., `type: "InvalidType"`)        | Error: "Invalid geometry type: InvalidType"             | 1                 | MEDIUM   |
| **Null geometry**         | Parse Feature with `geometry: null`                                   | Accept (valid GeoJSON, represents non-spatial features) | 1 (negative test) | MEDIUM   |
| **Missing properties**    | Parse Feature without `properties`                                    | Accept (valid GeoJSON, `properties` is optional)        | 1 (negative test) | LOW      |

**Total GeoJSON Error Tests:** ~5 tests

#### 4.2.2 SensorML Parser Errors

**From [Section 9: SensorML Testing Requirements](./09-sensorml-testing-requirements.md):**

| Error Condition                  | Test Scenario                                                                                | Expected Error                                    | Test Count          | Priority |
| -------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------- | -------- |
| **Malformed XML**                | Parse invalid XML string                                                                     | Error: "Invalid XML" (from XML parser)            | 1                   | HIGH     |
| **Missing required element**     | Parse PhysicalSystem without `<sml:identification>`                                          | Error: "Missing required element: identification" | 4 (1 per structure) | HIGH     |
| **Invalid namespace**            | Parse with wrong namespace (e.g., `<sml2:PhysicalSystem>` instead of `<sml:PhysicalSystem>`) | Error: "Invalid namespace"                        | 2                   | MEDIUM   |
| **Recursive structure too deep** | Parse with 10+ nested levels                                                                 | Error: "Maximum recursion depth exceeded"         | 1                   | MEDIUM   |
| **Empty document**               | Parse empty string or whitespace-only                                                        | Error: "Empty document"                           | 1                   | LOW      |

**Total SensorML Error Tests:** ~8-10 tests

#### 4.2.3 SWE Common Parser Errors

> ⚠️ **REVIEW NOTICE (L1): Binary Encoding Error Test Scenarios May Need Refinement**
>
> The Binary Encoding Errors subsection (~7 tests for buffer truncation, endianness, invalid data type codes) may be speculative in their specificity. These tests should be refined once binary SWE parsing implementation details are clearer. **Clarification:** Binary SWE Common parsing IS in scope per the implementation guide §7 and Phase 2D assessment (Doc 10, M2/P4). This L1 flag is about error test specificity, not about binary parsing scope.

**From [Section 10: SWE Common Testing Requirements](./10-swe-common-testing-requirements.md):**

| Error Condition              | Test Scenario                                       | Expected Error                    | Test Count                | Priority |
| ---------------------------- | --------------------------------------------------- | --------------------------------- | ------------------------- | -------- |
| **JSON Encoding Errors**     |                                                     |                                   |                           |          |
| - Malformed JSON             | Parse invalid JSON                                  | SyntaxError                       | 1                         | HIGH     |
| - Missing DataRecord fields  | Parse DataRecord without `name` or `definition`     | Error: "Missing required field"   | 3                         | HIGH     |
| - Invalid field type         | Parse with wrong type (number instead of string)    | Error: "Invalid field type"       | 2                         | MEDIUM   |
| **Text Encoding Errors**     |                                                     |                                   |                           |          |
| - Incorrect delimiter        | Parse CSV with wrong delimiter                      | Error: "Unexpected delimiter"     | 2                         | HIGH     |
| - Field count mismatch       | Parse row with wrong number of fields               | Error: "Field count mismatch"     | 2                         | HIGH     |
| - Invalid numeric value      | Parse non-numeric value in Quantity field           | Error: "Invalid numeric value"    | 2                         | MEDIUM   |
| **Binary Encoding Errors**   |                                                     |                                   |                           |          |
| - Insufficient data          | Parse truncated binary buffer                       | Error: "Unexpected end of buffer" | 3                         | HIGH     |
| - Wrong endianness           | Parse little-endian as big-endian                   | Silent error (wrong values)       | 2 (verify correct values) | HIGH     |
| - Invalid data type          | Parse with undefined data type code                 | Error: "Unknown data type"        | 2                         | MEDIUM   |
| **Schema Validation Errors** |                                                     |                                   |                           |          |
| - Schema mismatch            | Parse data with schema that doesn't match structure | Error: "Schema validation failed" | 3                         | HIGH     |
| - Missing schema             | Attempt to parse without schema                     | Error: "Schema required"          | 1                         | MEDIUM   |

**Total SWE Common Error Tests:** ~23-25 tests

### 4.3 Resource Method Error Scenarios

**From [Section 13: Resource Method Testing Patterns](./13-resource-method-testing-patterns.md):**

| Error Condition                    | Test Scenario                                         | Expected Behavior                            | Test Count              | Priority |
| ---------------------------------- | ----------------------------------------------------- | -------------------------------------------- | ----------------------- | -------- |
| **Resource unavailable**           | Call resource method when resource not in conformance | Throw EndpointError                          | 9 (1 per resource type) | CRITICAL |
| **Empty resource ID**              | Call `getSystem('')` with empty string                | Throw Error: "ID is required"                | 9                       | HIGH     |
| **Create without required fields** | Call `createSystem({})` with empty body               | Propagate 400 from server (server validates) | 0 (server-side)         | LOW      |
| **Update non-existent resource**   | Call `updateSystem('non-existent-id', {...})`         | Propagate 404 from server                    | 0 (integration test)    | MEDIUM   |
| **Delete non-existent resource**   | Call `deleteSystem('non-existent-id')`                | Propagate 404 from server                    | 0 (integration test)    | MEDIUM   |

**Total Resource Method Error Tests:** ~18 tests (2 per resource type × 9 resources)

### 4.4 Integration Workflow Error Scenarios

**From [Section 14: Integration Test Workflow Design](./14-integration-test-workflow-design.md):**

| Error Condition              | Test Scenario                                           | Expected Behavior                                     | Test Count | Priority |
| ---------------------------- | ------------------------------------------------------- | ----------------------------------------------------- | ---------- | -------- |
| **Missing collection**       | Initialize endpoint with non-existent collection        | Propagate 404 from server                             | 1          | HIGH     |
| **Network timeout**          | Simulate slow server (5s+ response time)                | Propagate timeout error                               | 1          | MEDIUM   |
| **CORS error**               | Call from browser without CORS headers                  | Detect CORS error (if possible)                       | 1          | MEDIUM   |
| **Partial workflow failure** | Create system → Create deployment (fails) → Rollback    | Verify first operation succeeds, second fails cleanly | 2          | HIGH     |
| **Invalid nested resource**  | Create system → Create datastream with invalid systemId | Propagate 400 from server                             | 1          | MEDIUM   |

**Total Integration Error Tests:** ~6 tests

### 4.5 Worker Extension Error Scenarios

> ⚠️ **REVIEW NOTICE (L2): Worker Infrastructure Does Not Exist Yet — Premature**
>
> All 7 worker error scenarios (initialization failure, parse error propagation, timeout, premature termination, serialization error) reference worker infrastructure that hasn't been built. These tests are premature for the initial contribution. Defer this entire section until worker support is implemented.

**From [Section 16: Worker Extensions Testing Strategy](./16-worker-extensions-testing-strategy.md):**

| Error Condition                   | Test Scenario                                  | Expected Behavior                           | Test Count       | Priority |
| --------------------------------- | ---------------------------------------------- | ------------------------------------------- | ---------------- | -------- |
| **Worker initialization failure** | Fail to create Worker (e.g., script not found) | Throw Error: "Worker initialization failed" | 1                | HIGH     |
| **Parse error in worker**         | Send malformed data to parser worker           | Propagate error from worker to main thread  | 3 (1 per parser) | HIGH     |
| **Worker timeout**                | Worker doesn't respond within timeout          | Throw Error: "Worker timeout"               | 1                | MEDIUM   |
| **Worker terminated prematurely** | Terminate worker mid-operation                 | Throw Error: "Worker terminated"            | 1                | MEDIUM   |
| **Message serialization error**   | Send non-serializable data to worker           | Throw Error: "Failed to serialize message"  | 1                | LOW      |

**Total Worker Error Tests:** ~7 tests

### 4.6 Error Test Count Summary

| Component                  | Error Test Count | % of Total Error Tests |
| -------------------------- | ---------------- | ---------------------- |
| QueryBuilder (URL Builder) | ~30              | 10%                    |
| GeoJSON Parser             | ~5               | 2%                     |
| SensorML Parser            | ~10              | 3%                     |
| SWE Common Parser          | ~25              | 8%                     |
| Resource Methods           | ~18              | 6%                     |
| Integration Workflows      | ~6               | 2%                     |
| Worker Extensions          | ~7               | 2%                     |
| **TOTAL**                  | **~100**         | **33%**                |

**Note:** These are EXPLICIT error tests. Additional error scenarios are tested implicitly in happy path tests (e.g., null/undefined parameter handling).

**Estimated Total Error Test Lines:** ~1,500-2,000 lines (15-20 lines per error test)

---

## 5. Error Test Pattern Design

### 5.1 Error Test Structure Template

**Pattern 1: Simple Error Assertion**

```typescript
describe('Error Conditions', () => {
  it('throws clear error when [condition]', () => {
    expect(() => {
      // Code that should throw
      builder.getResource('invalid-id');
    }).toThrow(/Expected error message pattern/);
  });
});
```

**Pattern 2: Async Error Assertion**

```typescript
describe('Error Conditions', () => {
  it('throws error when [condition]', async () => {
    await expect(builder.getResourceAsync('invalid-id')).rejects.toThrow(
      /Expected error message/
    );
  });
});
```

**Pattern 3: Error Class and Message Validation**

```typescript
describe('Error Conditions', () => {
  it('throws EndpointError with clear message', async () => {
    await expect(endpoint.csapi('test-collection')).rejects.toThrow(
      EndpointError
    );

    await expect(endpoint.csapi('test-collection')).rejects.toThrow(
      /Endpoint does not support.*CSAPI/
    );
  });
});
```

**Pattern 4: Error Message Context Validation**

```typescript
describe('Error Conditions', () => {
  it('includes context in error message', async () => {
    const collectionId = 'test-collection';

    await expect(builder.getObservations()).rejects.toThrow(
      new RegExp(`Collection does not support.*observations.*${collectionId}`)
    );
  });
});
```

**Pattern 5: Multiple Assertions on Error**

```typescript
describe('Error Conditions', () => {
  it('validates error properties', async () => {
    try {
      await builder.getResource('invalid');
      fail('Should have thrown error');
    } catch (error) {
      expect(error).toBeInstanceOf(EndpointError);
      expect(error.message).toMatch(/does not support/);
      expect(error.httpStatus).toBeUndefined(); // Client-side error
      expect(error.isCrossOriginRelated).toBe(false);
    }
  });
});
```

### 5.2 Error Assertion Helpers

**Helper 1: Assert Error Message Pattern**

```typescript
/**
 * Assert that a function throws an error matching a pattern
 */
function assertThrows(
  fn: () => void,
  errorPattern: string | RegExp,
  errorClass?: new (...args: any[]) => Error
) {
  expect(fn).toThrow(errorPattern);
  if (errorClass) {
    expect(fn).toThrow(errorClass);
  }
}

// Usage:
assertThrows(() => builder.getSystem(''), /ID.*required/, Error);
```

**Helper 2: Assert Async Error**

```typescript
/**
 * Assert that an async function rejects with an error matching a pattern
 */
async function assertRejects(
  promise: Promise<any>,
  errorPattern: string | RegExp,
  errorClass?: new (...args: any[]) => Error
) {
  await expect(promise).rejects.toThrow(errorPattern);
  if (errorClass) {
    await expect(promise).rejects.toThrow(errorClass);
  }
}

// Usage:
await assertRejects(
  builder.getObservations(),
  /Collection does not support.*observations/,
  EndpointError
);
```

**Helper 3: Parse and Validate Error Details**

```typescript
/**
 * Capture error and validate all properties
 */
async function captureError<T extends Error>(
  promise: Promise<any>
): Promise<T> {
  try {
    await promise;
    throw new Error('Expected promise to reject, but it resolved');
  } catch (error) {
    return error as T;
  }
}

// Usage:
const error = await captureError<EndpointError>(
  endpoint.csapi('non-csapi-collection')
);
expect(error).toBeInstanceOf(EndpointError);
expect(error.message).toMatch(/does not support.*CSAPI/);
expect(error.httpStatus).toBeUndefined();
expect(error.isCrossOriginRelated).toBe(false);
```

### 5.3 Error Message Validation Approach

**Validation Levels:**

1. **Level 1: Error Thrown (Basic)**

   ```typescript
   expect(() => fn()).toThrow();
   ```

   ✅ Verifies error is thrown  
   ❌ Doesn't verify error type or message

2. **Level 2: Error Pattern Match (Good)**

   ```typescript
   expect(() => fn()).toThrow(/pattern/);
   ```

   ✅ Verifies error message content  
   ❌ Doesn't verify error class

3. **Level 3: Error Class and Pattern (Better)**

   ```typescript
   expect(() => fn()).toThrow(EndpointError);
   expect(() => fn()).toThrow(/pattern/);
   ```

   ✅ Verifies error class AND message  
   ❌ Requires two assertions

4. **Level 4: Complete Error Validation (Best)**
   ```typescript
   try {
     fn();
     fail('Should have thrown');
   } catch (error) {
     expect(error).toBeInstanceOf(EndpointError);
     expect(error.message).toMatch(/pattern/);
     expect(error.httpStatus).toBeUndefined();
     expect(error.isCrossOriginRelated).toBe(false);
   }
   ```
   ✅ Verifies all error properties  
   ❌ More verbose

**Recommendation:** Use Level 3 for most tests (error class + message pattern). Use Level 4 for critical error paths.

### 5.4 Error Recovery Test Patterns

**Pattern: Graceful Degradation**

```typescript
describe('Error recovery', () => {
  it('continues operation after recoverable error', async () => {
    // First operation fails
    await expect(builder.getSystem('invalid')).rejects.toThrow();

    // Second operation succeeds
    const url = builder.getSystem('valid-id');
    expect(url).toBeDefined();
  });
});
```

**Pattern: Cascading Error Prevention**

```typescript
describe('Error isolation', () => {
  it('does not leak errors across operations', async () => {
    // Operation 1 fails
    await expect(builder.getObservations()).rejects.toThrow(
      /does not support observations/
    );

    // Operation 2 succeeds (different resource)
    const url = builder.getSystems();
    expect(url).toBeDefined();

    // Operation 3 fails again (same error)
    await expect(builder.getObservations()).rejects.toThrow();
  });
});
```

---

## 6. Error Test Organization

### 6.1 Error Test Placement

**Strategy:** Embed error tests within component test files (NOT separate error test files)

**Rationale:**

- Errors are specific to components
- Error tests provide context for happy path tests
- Easier to maintain (error tests co-located with related code)

**File Structure:**

```
src/ogc-api/csapi/
  url_builder-systems.spec.ts
    ├── describe('Systems - Happy Path', ...)
    ├── describe('Systems - Error Conditions', ...)
    │   ├── it('throws when resource unavailable', ...)
    │   ├── it('throws when ID is empty', ...)
    │   └── it('validates bbox coordinates', ...)
    └── describe('Systems - Edge Cases', ...)
```

### 6.2 Error Test Organization Pattern

**Per Component File:**

```typescript
describe('ComponentName', () => {
  // 1. Setup
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    // Common setup
  });

  // 2. Happy Path Tests (~70% of tests)
  describe('Happy Path', () => {
    it('test 1', ...);
    it('test 2', ...);
    // ...
  });

  // 3. Error Condition Tests (~20% of tests)
  describe('Error Conditions', () => {
    it('throws error when [condition 1]', ...);
    it('throws error when [condition 2]', ...);
    // ...
  });

  // 4. Edge Case Tests (~10% of tests)
  describe('Edge Cases', () => {
    it('handles empty collection', ...);
    it('handles null parameters', ...);
    // ...
  });
});
```

**Test Distribution:**

- Happy Path: ~70% of tests
- Error Conditions: ~20% of tests
- Edge Cases: ~10% of tests

### 6.3 Error Test Naming Conventions

**Pattern: `throws [error class] when [condition]`**

✅ **GOOD:**

```typescript
it('throws EndpointError when CSAPI not supported', ...);
it('throws Error when bbox coordinates invalid', ...);
it('throws EndpointError when resource unavailable', ...);
it('throws Error when temporal interval has start > end', ...);
```

❌ **BAD (too vague):**

```typescript
it('handles error', ...);
it('error test', ...);
it('throws', ...);
```

❌ **BAD (too prescriptive):**

```typescript
it('should throw an EndpointError with message "Endpoint does not support CSAPI" when calling csapi() on a non-CSAPI endpoint', ...);
```

**Pattern for negative tests (no error expected):**

```typescript
it('does NOT throw when [condition]', ...);
it('accepts null optional parameters without error', ...);
it('handles empty collection gracefully', ...);
```

---

## 7. Error Test Priorities

### 7.1 Priority Matrix

| Priority     | Error Type                                                                         | Test Count | % of Error Tests | Why                                            |
| ------------ | ---------------------------------------------------------------------------------- | ---------- | ---------------- | ---------------------------------------------- |
| **CRITICAL** | Conformance errors (CSAPI not supported, resource unavailable)                     | ~20        | 20%              | Block library usage if not detected            |
| **HIGH**     | Validation errors (invalid bbox, temporal interval), Parse errors (malformed data) | ~50        | 50%              | Common developer mistakes, data quality issues |
| **MEDIUM**   | Edge cases (null params, empty IDs), Integration errors (network timeout)          | ~20        | 20%              | Less common but still important                |
| **LOW**      | HTTP errors (404, 500), Infrastructure errors (DNS, CORS)                          | ~10        | 10%              | Server/browser responsibility                  |

### 7.2 Implementation Phases

**Phase 1: CRITICAL Error Tests (Week 1)**

- Conformance check errors (~20 tests)
- Resource unavailability errors (~10 tests)
- **Total:** ~30 tests, ~450-600 lines

**Phase 2: HIGH Priority Error Tests (Week 2)**

- Parameter validation errors (~25 tests)
- Parse errors (GeoJSON, SensorML, SWE) (~25 tests)
- **Total:** ~50 tests, ~750-1,000 lines

**Phase 3: MEDIUM/LOW Priority Error Tests (Week 3)**

- Edge case handling (~20 tests)
- Integration error scenarios (~10 tests)
- **Total:** ~30 tests, ~450-600 lines

**Total Error Test Implementation:** ~110 tests, ~1,650-2,200 lines

---

## 8. Error Test Fixtures

### 8.1 Conformance Fixtures for Error Testing

**Fixture 1: No CSAPI Support**

```json
// fixtures/ogc-api/conformance-no-csapi.json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson"
  ]
}
```

**Fixture 2: Part 1 Only (No Part 2)**

```json
// fixtures/ogc-api/conformance-part1-only.json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment"
  ]
}
```

**Fixture 3: Missing Required Links**

```json
// fixtures/ogc-api/collection-no-csapi-links.json
{
  "id": "test-collection",
  "title": "Test Collection",
  "links": [
    {
      "rel": "self",
      "href": "http://example.com/collections/test-collection"
    }
    // NO CSAPI resource links
  ]
}
```

### 8.2 Parser Error Fixtures

**Fixture 1: Malformed GeoJSON**

```json
// fixtures/ogc-api/malformed-geojson.json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [0] // Invalid: Point requires [lon, lat]
  },
  "properties": {}
}
```

**Fixture 2: Invalid SensorML**

```xml
<!-- fixtures/ogc-api/invalid-sensorml.xml -->
<sml:PhysicalSystem xmlns:sml="http://www.opengis.net/sensorml/2.0">
  <!-- Missing required <sml:identification> -->
  <sml:description>Invalid system</sml:description>
</sml:PhysicalSystem>
```

**Fixture 3: SWE Common Data Mismatch**

```json
// fixtures/ogc-api/swe-data-mismatch.json
{
  "type": "DataRecord",
  "fields": [
    { "name": "temperature", "type": "Quantity" },
    { "name": "humidity", "type": "Quantity" }
  ],
  "values": [25.3] // Error: 2 fields but only 1 value
}
```

---

## 9. Error Test Implementation Estimates

### 9.1 Test Line Estimates by Component

| Component                  | Error Tests | Lines per Test | Total Lines      | Time Estimate   |
| -------------------------- | ----------- | -------------- | ---------------- | --------------- |
| QueryBuilder (URL Builder) | 30          | 15-20          | 450-600          | 2-3 hours       |
| GeoJSON Parser             | 5           | 15-20          | 75-100           | 30 min          |
| SensorML Parser            | 10          | 15-20          | 150-200          | 1 hour          |
| SWE Common Parser          | 25          | 15-20          | 375-500          | 2 hours         |
| Resource Methods           | 18          | 15-20          | 270-360          | 1.5 hours       |
| Integration Workflows      | 6           | 20-25          | 120-150          | 1 hour          |
| Worker Extensions          | 7           | 15-20          | 105-140          | 1 hour          |
| **TOTAL**                  | **101**     | **~16 avg**    | **~1,545-2,050** | **~9-10 hours** |

### 9.2 Fixture Creation Estimates

| Fixture Type                   | Count  | Lines per Fixture | Total Lines  | Time Estimate  |
| ------------------------------ | ------ | ----------------- | ------------ | -------------- |
| Conformance (error scenarios)  | 3      | 10-20             | 30-60        | 30 min         |
| Collection (missing links)     | 2      | 15-25             | 30-50        | 30 min         |
| GeoJSON (malformed)            | 3      | 10-20             | 30-60        | 30 min         |
| SensorML (invalid)             | 4      | 20-40             | 80-160       | 1 hour         |
| SWE Common (schema violations) | 5      | 15-30             | 75-150       | 1 hour         |
| **TOTAL**                      | **17** | **~18 avg**       | **~245-480** | **~3.5 hours** |

### 9.3 Total Error Testing Implementation

**Total Error Test Code:**

- Error tests: ~1,545-2,050 lines
- Error fixtures: ~245-480 lines
- **TOTAL: ~1,790-2,530 lines**

**Total Time:**

- Error test implementation: ~9-10 hours
- Error fixture creation: ~3.5 hours
- **TOTAL: ~12.5-13.5 hours** (~2 developer-days)

**% of Total Testing Effort:**

- Total test lines (from all sections): ~13,000-17,000 lines
- Error test lines: ~1,790-2,530 lines
- **Error tests = ~13-15% of total testing effort**

---

## 10. Success Criteria

This error testing strategy is complete when:

✅ **Error Taxonomy:**

- [x] All error categories documented (Validation, Conformance, Network, Parse, HTTP)
- [x] Error responsibility clearly assigned (Library vs Server vs Browser)
- [x] Error handling philosophy documented (minimal, targeted)

✅ **Upstream Patterns:**

- [x] Upstream error patterns analyzed and documented
- [x] Upstream error classes identified (EndpointError, ServiceExceptionError)
- [x] Upstream error message guidelines extracted
- [x] Upstream test patterns documented (4 patterns identified)

✅ **CSAPI Specification:**

- [x] CSAPI error schemas analyzed (HTTP status codes, no custom schemas)
- [x] HTTP error responses documented (400, 401, 403, 404, 500, 502, 503)
- [x] Error handling strategy aligns with specification

✅ **Component Scenarios:**

- [x] QueryBuilder error scenarios defined (~30 tests)
- [x] Parser error scenarios defined (~40 tests)
- [x] Resource method error scenarios defined (~18 tests)
- [x] Integration error scenarios defined (~6 tests)
- [x] Worker error scenarios defined (~7 tests)
- [x] Total ~101 error tests estimated

✅ **Test Patterns:**

- [x] Error test structure templates defined (5 patterns)
- [x] Error assertion helpers documented (3 helpers)
- [x] Error message validation approach defined (4 levels)
- [x] Error recovery test patterns documented

✅ **Organization:**

- [x] Error test placement strategy defined (embed in component files)
- [x] Error test organization pattern documented (20% of tests)
- [x] Error test naming conventions established
- [x] Error test priorities defined (CRITICAL, HIGH, MEDIUM, LOW)

✅ **Implementation:**

- [x] Implementation phases defined (3 phases, ~12.5 hours total)
- [x] Test line estimates calculated (~1,545-2,050 lines)
- [x] Fixture requirements documented (17 fixtures, ~245-480 lines)
- [x] Success criteria documented

---

## 11. Validation Against Upstream Patterns

### 11.1 Alignment with Upstream Error Handling

| Upstream Pattern               | CSAPI Implementation                                           | Status     |
| ------------------------------ | -------------------------------------------------------------- | ---------- |
| **Minimal error handling**     | Throw only when library can't proceed                          | ✅ ALIGNED |
| **Reuse EndpointError**        | Use EndpointError for conformance/availability errors          | ✅ ALIGNED |
| **No custom error classes**    | No CSAPI-specific error classes                                | ✅ ALIGNED |
| **Clear error messages**       | Include context (collection ID, resource type, parameter name) | ✅ ALIGNED |
| **Validate at use**            | Check parameters in QueryBuilder methods                       | ✅ ALIGNED |
| **Trust server validation**    | Let HTTP errors propagate, don't validate server constraints   | ✅ ALIGNED |
| **Warn for optional features** | Use console.warn for optional format not found                 | ✅ ALIGNED |

### 11.2 Deviations from Upstream (None)

CSAPI error handling fully aligns with upstream patterns. No deviations.

### 11.3 Enhancements to Upstream

| Enhancement                      | Description                                                      | Justification                                                         |
| -------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Bbox validation**              | Validate minLon < maxLon, minLat < maxLat                        | Logical error detectable client-side, prevents wasted server requests |
| **Temporal interval validation** | Validate start < end for datetime intervals                      | Logical error detectable client-side, common developer mistake        |
| **Part 2 method validation**     | Throw error when Part 2 method called without Part 2 conformance | CSAPI-specific conformance check, prevents confusing server errors    |

**All enhancements follow upstream philosophy:** Validate only logical errors detectable client-side, trust server for constraints.

---

## 12. References

1. [Error Handling Design Analysis](../../upstream/error-handling-analysis.md) - Upstream error patterns
2. [Section 1: Upstream Blueprint Analysis](./01-edr-test-blueprint.md) - EDR error test patterns
3. [Section 2: Existing Upstream Test Pattern Survey](./02-upstream-test-consistency.md) - Error handling consistency
4. [Section 12: QueryBuilder Testing Strategy](./12-querybuilder-testing-strategy.md) - QueryBuilder error scenarios
5. [Section 13: Resource Method Testing Patterns](./13-resource-method-testing-patterns.md) - Resource method error scenarios
6. [Section 14: Integration Test Workflow Design](./14-integration-test-workflow-design.md) - Integration error scenarios
7. [Section 16: Worker Extensions Testing Strategy](./16-worker-extensions-testing-strategy.md) - Worker error scenarios
8. [Section 9: SensorML Testing Requirements](./09-sensorml-testing-requirements.md) - SensorML parser errors
9. [Section 10: SWE Common Testing Requirements](./10-swe-common-testing-requirements.md) - SWE Common parser errors
10. [CSAPI Part 1 OpenAPI Spec](../../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) - HTTP error responses
11. [CSAPI Part 2 OpenAPI Spec](../../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) - HTTP error responses

---

## 13. Appendix: Error Test Examples

### Example 1: Conformance Check Error

```typescript
// File: src/ogc-api/csapi/endpoint.spec.ts
describe('OgcApiEndpoint.csapi()', () => {
  describe('Error Conditions', () => {
    it('throws EndpointError when CSAPI not supported', async () => {
      const endpoint = new OgcApiEndpoint(
        'http://example.com',
        { conformance: conformanceNoCSAPI } // Fixture without CSAPI
      );

      await expect(endpoint.csapi('test-collection')).rejects.toThrow(
        EndpointError
      );

      await expect(endpoint.csapi('test-collection')).rejects.toThrow(
        /Endpoint does not support.*Connected Systems API/
      );
    });
  });
});
```

### Example 2: Parameter Validation Error

```typescript
// File: src/ogc-api/csapi/url_builder-systems.spec.ts
describe('Systems - Error Conditions', () => {
  it('throws Error when bbox has minLon > maxLon', () => {
    expect(() => {
      builder.getSystems({
        bbox: { minLon: 180, minLat: -90, maxLon: -180, maxLat: 90 },
      });
    }).toThrow(/Invalid bbox.*minLon.*maxLon/);
  });

  it('throws Error when temporal interval has start > end', () => {
    expect(() => {
      builder.getSystems({
        datetime: '2024-12-31T23:59:59Z/2024-01-01T00:00:00Z',
      });
    }).toThrow(/Invalid datetime.*start.*before.*end/);
  });
});
```

### Example 3: Parser Error

```typescript
// File: src/ogc-api/csapi/parsers/sensorml.spec.ts
describe('SensorML Parser - Error Conditions', () => {
  it('throws Error when XML is malformed', () => {
    const malformedXml = '<sml:PhysicalSystem><invalid>';

    expect(() => parseSensorML(malformedXml)).toThrow(/Invalid XML/);
  });

  it('throws Error when required element missing', () => {
    const invalidSystem = `
      <sml:PhysicalSystem xmlns:sml="http://www.opengis.net/sensorml/2.0">
        <sml:description>Missing identification</sml:description>
      </sml:PhysicalSystem>
    `;

    expect(() => parseSensorML(invalidSystem)).toThrow(
      /Missing required element.*identification/
    );
  });
});
```

### Example 4: Integration Error

```typescript
// File: src/ogc-api/csapi/integration.spec.ts
describe('CSAPI Integration - Error Scenarios', () => {
  it('handles missing collection gracefully', async () => {
    const endpoint = new OgcApiEndpoint('http://example.com');

    // Should propagate 404 from server
    await expect(
      endpoint.getCollectionInfo('non-existent-collection')
    ).rejects.toThrow();

    // Subsequent operations should still work
    const collections = await endpoint.getCollectionList();
    expect(collections).toBeDefined();
  });
});
```

---

**Document Status:** ✅ COMPLETE  
**Next Steps:**

1. Implement CRITICAL error tests (conformance, resource availability) - ~30 tests, ~450-600 lines
2. Implement HIGH priority error tests (validation, parsing) - ~50 tests, ~750-1,000 lines
3. Implement MEDIUM/LOW priority error tests - ~30 tests, ~450-600 lines
4. Create error test fixtures - 17 fixtures, ~245-480 lines
5. Review error messages for clarity and consistency
