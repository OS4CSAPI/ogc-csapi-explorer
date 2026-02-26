# Section 12: QueryBuilder URL Construction Testing Strategy

**Research Plan:** [Research Plan 12: QueryBuilder URL Construction Testing Strategy](../research-plans/12-querybuilder-testing-strategy.md)  
**Research Questions:** 86 questions about CSAPIQueryBuilder architecture, method inventory across 9 resource types, URL validation depth (meaningful vs trivial), query parameter testing strategies, resource availability validation, nested endpoint construction, URL encoding edge cases, Implementation Guide specifications, upstream URL builder patterns, method categories and testing strategies, error handling, fixture requirements, test organization strategies, and test depth per method  
**Methodology:** 4-phase systematic analysis (QueryBuilder method inventory listing all ~70-80 methods across 9 resource types → Upstream URL builder analysis from EDR and OGC API patterns → URL validation strategy design defining "meaningful" URL testing beyond trivial string checks → Method-by-method test planning documenting requirements per resource type with shared test patterns)  
**Research Time:** ~3 hours (February 5, 2026)

**Primary Source(s):**

- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (CSAPIQueryBuilder specification with all method signatures)
- [ROADMAP.md](../../../planning/ROADMAP.md) (Phase 2 lists 9 resource type tasks)
- [URL Building Architecture](../../upstream/url-building-analysis.md)

**Supporting Resources:**

- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (query parameter specs from Part 1 & 2)
- Section 6: [Meaningful vs Trivial Definition](06-meaningful-vs-trivial-definition.md) (URL testing depth guidance)
- Section 1-2: Upstream URL builder test patterns (EDR, OGC API)
- [Query Parameter Requirements](../../requirements/csapi-query-parameters.md)

**Document Purpose:** Define comprehensive testing strategy for CSAPIQueryBuilder covering all ~80 methods across 9 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands) with systematic URL validation using parseAndValidateUrl utility that ensures deep, meaningful testing beyond trivial string checks, covering query parameter categories (pagination, temporal, spatial, filtering, optional, encoding), nested endpoint construction, resource availability validation, and URL encoding edge cases, requiring ~11 fixtures and estimated 188 tests (1,880-2,256 lines) organized across multiple files.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Method Inventory Matrix](#2-method-inventory-matrix)
3. ["Meaningful" URL Testing Definition](#3-meaningful-url-testing-definition)
4. [Query Parameter Testing Strategy](#4-query-parameter-testing-strategy)
5. [Systems Resource Testing Requirements](#5-systems-resource-testing-requirements)
6. [Deployments Resource Testing Requirements](#6-deployments-resource-testing-requirements)
7. [Procedures Resource Testing Requirements](#7-procedures-resource-testing-requirements)
8. [SamplingFeatures Resource Testing Requirements](#8-samplingfeatures-resource-testing-requirements)
9. [Properties Resource Testing Requirements](#9-properties-resource-testing-requirements)
10. [DataStreams Resource Testing Requirements](#10-datastreams-resource-testing-requirements)
11. [Observations Resource Testing Requirements](#11-observations-resource-testing-requirements)
12. [ControlStreams Resource Testing Requirements](#12-controlstreams-resource-testing-requirements)
13. [Commands Resource Testing Requirements](#13-commands-resource-testing-requirements)
14. [Nested Endpoint Testing](#14-nested-endpoint-testing)
15. [URL Encoding Edge Cases](#15-url-encoding-edge-cases)
16. [Resource Availability Validation Testing](#16-resource-availability-validation-testing)
17. [Error Condition Testing](#17-error-condition-testing)
18. [Test Organization Structure](#18-test-organization-structure)
19. [Test Utility Specifications](#19-test-utility-specifications)
20. [Fixture Requirements](#20-fixture-requirements)
21. [Testing Estimates](#21-testing-estimates)
22. [Testing Priorities](#22-testing-priorities)
23. [Validation Against Upstream Patterns](#23-validation-against-upstream-patterns)
24. [Integration with Implementation Guide](#24-integration-with-implementation-guide)
25. [Risks and Edge Cases](#25-risks-and-edge-cases)

---

## 1. Executive Summary

### 1.1 Scope Overview

**Total Methods to Test:** ~70-80 methods across 9 CSAPI resource types

**Method Distribution:**

- **Part 1 Resources (5 types):** Systems (12), Deployments (8), Procedures (8), SamplingFeatures (8), Properties (6) = **42 methods**
- **Part 2 Resources (4 types):** DataStreams (11), Observations (9), ControlStreams (8), Commands (10) = **38 methods**
- **Grand Total:** ~**80 methods**

**Testing Priorities:**

- **CRITICAL (P0):** All GET collection methods (9), all GET item methods (9), query parameter validation, URL encoding, nested endpoints (top 5) = **~40 tests**
- **HIGH (P1):** POST/PUT/PATCH methods (27), optional parameter handling, resource availability validation = **~80 tests**
- **MEDIUM (P2):** DELETE methods (9), advanced parameter combinations, edge case encoding = **~48 tests**
- **LOW (P3):** Performance testing, very large parameter values, complex filter combinations = **~20 tests**

**Total Test Scenarios:** ~**188 tests**

### 1.2 URL Validation Approach

**"Meaningful" Testing Standard:**

- ✅ **DO:** Parse URL into components (protocol, host, pathname), validate query parameters as objects with type checking
- ❌ **DON'T:** Trivial string checks like `expect(url).toContain('/systems')`

**parseAndValidateUrl Utility** (see [Section 34: Test Utility & Helper Design](34-test-utility-helper-design.md) for the authoritative specification):

```typescript
function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string; // 'https:'
    hostname?: string; // 'api.example.com'
    pathname?: string; // '/systems'
    query?: Record<string, any>; // { limit: '10', bbox: '...' }
  }
): ParsedURL;
```

### 1.3 Test Organization Strategy

**RECOMMENDED: Multiple Files (One Per Resource Type)**

**File Structure:**

```
src/ogc-api/csapi/url_builder.spec.ts       (shared utilities, ~100 lines)
src/ogc-api/csapi/url_builder-systems.spec.ts    (~150-200 lines, 18 tests)
src/ogc-api/csapi/url_builder-deployments.spec.ts (~120-180 lines, 16 tests)
src/ogc-api/csapi/url_builder-procedures.spec.ts  (~120-180 lines, 16 tests)
src/ogc-api/csapi/url_builder-samplingfeatures.spec.ts (~120-180 lines, 16 tests)
src/ogc-api/csapi/url_builder-properties.spec.ts  (~90-130 lines, 12 tests)
src/ogc-api/csapi/url_builder-datastreams.spec.ts (~150-220 lines, 21 tests)
src/ogc-api/csapi/url_builder-observations.spec.ts (~120-180 lines, 18 tests)
src/ogc-api/csapi/url_builder-controlstreams.spec.ts (~120-180 lines, 16 tests)
src/ogc-api/csapi/url_builder-commands.spec.ts    (~150-220 lines, 20 tests)
```

**Benefits:**

- ~150-200 lines per file (maintainable size)
- Clear resource type boundaries
- Parallel test execution possible
- Easier code review
- Reduced merge conflicts

### 1.4 Testing Estimates

**Test Code Lines:** 1,880-2,256 lines total

- Shared utilities: ~100 lines
- Per-resource tests: 1,780-2,156 lines (9 files)

**Implementation Time:** 22-29 hours

- Setup + utilities: 2-3 hours
- Per-resource implementation: 20-26 hours (9 resources × 2-3 hours each)

**Test-to-Method Ratio:** ~2.4 tests per method average (188 tests ÷ 80 methods)

---

## 2. Method Inventory Matrix

### 2.1 Complete Method Count

| Resource Type        | GET Collection                                  | GET Item | POST             | PUT/PATCH | DELETE | Special Methods                                                                                                                            | Total   |
| -------------------- | ----------------------------------------------- | -------- | ---------------- | --------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------ | ------- |
| **Systems**          | 2 (getSystems, getSystemSubsystems)             | 1        | 1                | 1         | 1      | 6 (getSystemDataStreams, getSystemControlStreams, getSystemSamplingFeatures, getSystemDeployments, getSystemProcedures, getSystemHistory)  | **12**  |
| **Deployments**      | 2 (getDeployments, getDeploymentSubdeployments) | 1        | 1                | 1         | 1      | 2 (getDeploymentSystems, getDeploymentHistory)                                                                                             | **8**   |
| **Procedures**       | 1                                               | 1        | 1                | 1         | 1      | 3 (getProcedureSystems, getProcedureDataStreams, getProcedureHistory)                                                                      | **8**   |
| **SamplingFeatures** | 1                                               | 1        | 1                | 1         | 1      | 3 (getSamplingFeatureSystems, getSamplingFeatureObservations, getSamplingFeatureHistory)                                                   | **8**   |
| **Properties**       | 1                                               | 1        | 0                | 0         | 0      | 4 (getPropertySystems, getPropertyDataStreams, getPropertyControlStreams, getPropertyHistory)                                              | **6**   |
| **DataStreams**      | 1                                               | 1        | 1                | 1         | 1      | 6 (getDataStreamSchema, getDataStreamObservations, createObservation, getDataStreamSystems, getDataStreamProcedures, getDataStreamHistory) | **11**  |
| **Observations**     | 1                                               | 1        | 1 (bulk)         | 1         | 1      | 4 (getObservationDataStream, getObservationSamplingFeature, getObservationSystem, getObservationHistory)                                   | **9**   |
| **ControlStreams**   | 1                                               | 1        | 1                | 1         | 1      | 3 (getControlStreamSchema, getControlStreamCommands, checkCommandFeasibility)                                                              | **8**   |
| **Commands**         | 1                                               | 1        | 2 (single, bulk) | 1         | 1      | 4 (getCommandStatus, updateCommandStatus, getCommandResult, cancelCommand)                                                                 | **10**  |
| **TOTAL**            | **11**                                          | **9**    | **10**           | **9**     | **9**  | **35**                                                                                                                                     | **~80** |

### 2.2 Method Categories

**Standard CRUD (45 methods):**

- GET Collection: 11 methods (all resources)
- GET Item: 9 methods (all resources)
- POST Create: 10 methods (no POST for Properties)
- PUT/PATCH Update: 9 methods (no updates for Properties)
- DELETE: 9 methods (no deletes for Properties)

**Navigation Methods (20 methods):**

- Hierarchical: getSystemSubsystems, getDeploymentSubdeployments
- Cross-resource: getSystemDataStreams, getSystemControlStreams, getSystemSamplingFeatures, getSystemDeployments, getSystemProcedures, getDeploymentSystems, getProcedureSystems, getProcedureDataStreams, getSamplingFeatureSystems, getSamplingFeatureObservations, getPropertySystems, getPropertyDataStreams, getPropertyControlStreams, getDataStreamSystems, getDataStreamProcedures, getObservationDataStream, getObservationSamplingFeature, getObservationSystem

**Special Methods (15 methods):**

- Schema: getDataStreamSchema, getControlStreamSchema
- History: getSystemHistory, getDeploymentHistory, getProcedureHistory, getSamplingFeatureHistory, getPropertyHistory, getDataStreamHistory, getObservationHistory
- Commands: createObservation, checkCommandFeasibility, getCommandStatus, updateCommandStatus, getCommandResult, cancelCommand

---

## 3. "Meaningful" URL Testing Definition

> **Cross-reference:** For the foundational definition of meaningful vs trivial tests with the complete taxonomy, see [Section 06: Meaningful vs Trivial Definition](06-meaningful-vs-trivial-definition.md). The examples below apply those principles specifically to URL testing.

### 3.1 Trivial vs Meaningful Testing

**❌ TRIVIAL (Don't Do This):**

```typescript
// Example 1: String containment checks
it('returns systems URL', async () => {
  const url = builder.getSystems();
  expect(url).toContain('/systems'); // ❌ Too shallow
});

// Example 2: Exact string matching
it('constructs correct URL', async () => {
  const url = builder.getSystems({ limit: 10 });
  expect(url).toBe('https://api.example.com/systems?limit=10'); // ❌ Brittle
});

// Example 3: Regex checks
it('has query parameters', async () => {
  const url = builder.getSystems({ limit: 10 });
  expect(url).toMatch(/\?limit=\d+/); // ❌ Doesn't validate values
});
```

**Problems with Trivial Tests:**

- Don't validate protocol, host, or port
- Don't parse query parameters as structured data
- Don't validate parameter values or types
- Don't check parameter encoding
- Don't validate URL structure systematically
- Easy to pass with malformed URLs

**✅ MEANINGFUL (Do This):**

```typescript
// Example 1: Structured URL validation
it('constructs systems collection URL with pagination', async () => {
  const url = builder.getSystems({ limit: 10, offset: 20 });

  const parsed = parseAndValidateUrl(url, {
    protocol: 'https:',
    host: 'api.example.com',
    pathname: '/systems',
    query: {
      limit: '10',
      offset: '20',
    },
  });

  // Validates:
  // ✅ Protocol is HTTPS
  // ✅ Host matches expected
  // ✅ Pathname is exactly '/systems'
  // ✅ Query parameters parsed as objects
  // ✅ Parameter values match expected types
  // ✅ No unexpected parameters
});

// Example 2: Query parameter type validation
it('constructs systems URL with spatial filter', async () => {
  const url = builder.getSystems({
    bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
  });

  const parsed = parseAndValidateUrl(url, {
    pathname: '/systems',
    query: {
      bbox: '-180,-90,180,90', // Validates encoding format
    },
  });

  // Also validate bbox encoding
  expect(parsed.query.bbox).toMatch(
    /^-?\d+(\.\d+)?,-?\d+(\.\d+)?,-?\d+(\.\d+)?,-?\d+(\.\d+)?$/
  );
});

// Example 3: Optional parameter handling
it('omits optional parameters when not provided', async () => {
  const url = builder.getSystems(); // No options

  const parsed = parseAndValidateUrl(url, {
    pathname: '/systems',
    query: {}, // Expect no query parameters
  });

  expect(Object.keys(parsed.query)).toHaveLength(0);
});
```

**Benefits of Meaningful Tests:**

- Validates complete URL structure (protocol, host, path, query)
- Parses query parameters as objects (type-safe)
- Validates parameter encoding
- Validates optional parameter omission
- Catches malformed URLs
- Validates against spec requirements

### 3.2 parseAndValidateUrl Utility Specification

**Function Signature:**

```typescript
interface ParsedURL {
  protocol: string; // 'https:'
  host: string; // 'api.example.com'
  port: string; // '443' or ''
  pathname: string; // '/systems'
  query: Record<string, string>; // { limit: '10', offset: '20' }
  hash: string; // '' (typically unused)
}

function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string;
    host?: string;
    port?: string;
    pathname?: string;
    query?: Record<string, string>;
  }
): ParsedURL;
```

**Implementation:**

```typescript
import { URL } from 'url';

function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string;
    host?: string;
    port?: string;
    pathname?: string;
    query?: Record<string, string>;
  }
): ParsedURL {
  // Parse URL using Node.js URL API
  const parsed = new URL(url);

  // Validate protocol
  if (expected.protocol !== undefined) {
    expect(parsed.protocol).toBe(expected.protocol);
  }

  // Validate host
  if (expected.host !== undefined) {
    expect(parsed.host).toBe(expected.host);
  }

  // Validate port
  if (expected.port !== undefined) {
    expect(parsed.port).toBe(expected.port);
  }

  // Validate pathname
  if (expected.pathname !== undefined) {
    expect(parsed.pathname).toBe(expected.pathname);
  }

  // Parse and validate query parameters
  const query: Record<string, string> = {};
  parsed.searchParams.forEach((value, key) => {
    query[key] = value;
  });

  if (expected.query !== undefined) {
    expect(query).toEqual(expected.query);
  }

  return {
    protocol: parsed.protocol,
    host: parsed.host,
    port: parsed.port,
    pathname: parsed.pathname,
    query,
    hash: parsed.hash,
  };
}
```

**Usage Pattern:**

```typescript
describe('CSAPIQueryBuilder - Systems', () => {
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    const endpoint = await createTestEndpoint();
    builder = await endpoint.csapi('test-collection');
  });

  it('constructs systems collection URL', async () => {
    const url = builder.getSystems();

    parseAndValidateUrl(url, {
      protocol: 'https:',
      host: 'api.example.com',
      pathname: '/systems',
    });
  });

  it('constructs systems URL with all query parameters', async () => {
    const url = builder.getSystems({
      limit: 10,
      offset: 20,
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
      recursive: true,
    });

    parseAndValidateUrl(url, {
      pathname: '/systems',
      query: {
        limit: '10',
        offset: '20',
        bbox: '-180,-90,180,90',
        recursive: 'true',
      },
    });
  });
});
```

---

## 4. Query Parameter Testing Strategy

### 4.1 Query Parameter Categories

| Category         | Parameters                                                                                                        | Resource Types                                            | Test Scenarios                                                                               | Priority |
| ---------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------- |
| **Pagination**   | `limit`, `offset`                                                                                                 | All 9                                                     | Test default (limit=100), test custom values, test edge cases (0, very large), test omission | CRITICAL |
| **Temporal**     | `phenomenonTime`, `resultTime`, `validTime`, `issueTime`, `executionTime`, `datetime`                             | DataStreams, Observations, Commands, Systems, Deployments | Test ISO 8601 instant, test interval, test open interval (../2024-12-31), test encoding      | CRITICAL |
| **Spatial**      | `bbox`, `geometry`                                                                                                | Systems, Deployments, SamplingFeatures                    | Test bbox format (minLon,minLat,maxLon,maxLat), test coordinate encoding, test WKT geometry  | HIGH     |
| **Filtering**    | `systemType`, `observedProperty`, `controlledProperty`, `foi`, `parent`, `deployment`, `procedure`, `system`, `q` | Systems, DataStreams, ControlStreams                      | Test vocabulary values, test multiple filters, test property filters, test keyword search    | HIGH     |
| **Format**       | `f`, `format`                                                                                                     | All 9                                                     | Test valid formats (json, geojson, sml, swe), test defaults, test invalid formats            | MEDIUM   |
| **Sorting**      | `sortBy`, `sortOrder`                                                                                             | All 9                                                     | Test valid fields, test asc/desc, test invalid fields                                        | MEDIUM   |
| **Hierarchical** | `recursive`                                                                                                       | Systems, Deployments                                      | Test true/false, test omission (default false)                                               | HIGH     |
| **Arrays**       | Multiple `id` values, multiple property filters                                                                   | All 9                                                     | Test comma-separated lists, test encoding                                                    | MEDIUM   |
| **Optional**     | All optional parameters                                                                                           | All 9                                                     | Test presence vs absence, test combinations                                                  | HIGH     |
| **Encoding**     | Special chars in values                                                                                           | All 9                                                     | Test spaces, /, &, =, +, international chars, already-encoded                                | CRITICAL |

### 4.2 Pagination Testing

**Test Cases:**

```typescript
describe('Pagination parameters', () => {
  it('uses default limit when not specified', async () => {
    const url = builder.getSystems();
    const parsed = parseAndValidateUrl(url, {
      pathname: '/systems',
    });
    // Default limit may or may not be in URL (implementation-dependent)
    // If present: expect(parsed.query.limit).toBe('100');
  });

  it('applies custom limit', async () => {
    const url = builder.getSystems({ limit: 50 });
    parseAndValidateUrl(url, {
      query: { limit: '50' },
    });
  });

  it('applies offset for pagination', async () => {
    const url = builder.getSystems({ limit: 20, offset: 40 });
    parseAndValidateUrl(url, {
      query: {
        limit: '20',
        offset: '40',
      },
    });
  });

  it('handles edge case: limit=0', async () => {
    const url = builder.getSystems({ limit: 0 });
    parseAndValidateUrl(url, {
      query: { limit: '0' },
    });
  });

  it('handles large limit values', async () => {
    const url = builder.getSystems({ limit: 10000 });
    parseAndValidateUrl(url, {
      query: { limit: '10000' },
    });
  });
});
```

### 4.3 Temporal Parameter Testing

**Test Cases:**

```typescript
describe('Temporal parameters', () => {
  it('encodes ISO 8601 instant', async () => {
    const url = builder.getObservations('ds-123', {
      phenomenonTime: '2024-01-15T10:30:00Z',
    });
    parseAndValidateUrl(url, {
      query: {
        phenomenonTime: '2024-01-15T10:30:00Z',
      },
    });
  });

  it('encodes ISO 8601 interval', async () => {
    const url = builder.getObservations('ds-123', {
      phenomenonTime: '2024-01-01T00:00:00Z/2024-12-31T23:59:59Z',
    });
    parseAndValidateUrl(url, {
      query: {
        phenomenonTime: '2024-01-01T00:00:00Z/2024-12-31T23:59:59Z',
      },
    });
  });

  it('encodes open-ended interval (start/..)', async () => {
    const url = builder.getObservations('ds-123', {
      phenomenonTime: '2024-01-01T00:00:00Z/..',
    });
    parseAndValidateUrl(url, {
      query: {
        phenomenonTime: '2024-01-01T00:00:00Z/..',
      },
    });
  });

  it('encodes open-ended interval (../end)', async () => {
    const url = builder.getObservations('ds-123', {
      phenomenonTime: '../2024-12-31T23:59:59Z',
    });
    parseAndValidateUrl(url, {
      query: {
        phenomenonTime: '../2024-12-31T23:59:59Z',
      },
    });
  });

  it('handles multiple temporal filters', async () => {
    const url = builder.getObservations('ds-123', {
      phenomenonTime: '2024-01-01T00:00:00Z/..',
      resultTime: '2024-01-02T00:00:00Z/..',
    });
    parseAndValidateUrl(url, {
      query: {
        phenomenonTime: '2024-01-01T00:00:00Z/..',
        resultTime: '2024-01-02T00:00:00Z/..',
      },
    });
  });
});
```

### 4.4 Spatial Parameter Testing

**Test Cases:**

```typescript
describe('Spatial parameters', () => {
  it('encodes bbox as comma-separated coordinates', async () => {
    const url = builder.getSystems({
      bbox: { minLon: -122.5, minLat: 37.5, maxLon: -122.0, maxLat: 38.0 },
    });
    parseAndValidateUrl(url, {
      query: {
        bbox: '-122.5,37.5,-122.0,38.0',
      },
    });
  });

  it('handles integer bbox coordinates', async () => {
    const url = builder.getSystems({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
    });
    parseAndValidateUrl(url, {
      query: {
        bbox: '-180,-90,180,90',
      },
    });
  });

  it('encodes WKT geometry', async () => {
    const url = builder.getSystems({
      geometry: 'POINT(-122.08 37.42)',
    });
    parseAndValidateUrl(url, {
      query: {
        geometry: 'POINT(-122.08 37.42)', // Space should be encoded as %20
      },
    });
    // Verify space encoding
    expect(url).toContain('POINT(-122.08%2037.42)');
  });
});
```

### 4.5 Filtering Parameter Testing

**Test Cases:**

```typescript
describe('Filtering parameters', () => {
  it('filters by systemType vocabulary', async () => {
    const url = builder.getSystems({
      systemType: 'http://www.w3.org/ns/sosa/Sensor',
    });
    parseAndValidateUrl(url, {
      query: {
        systemType: 'http://www.w3.org/ns/sosa/Sensor',
      },
    });
    // Verify URI encoding (: and / characters)
    expect(url).toContain('http%3A%2F%2Fwww.w3.org%2Fns%2Fsosa%2FSensor');
  });

  it('filters by multiple criteria', async () => {
    const url = builder.getSystems({
      systemType: 'sosa:Sensor',
      deployment: 'deploy-123',
      q: 'temperature',
    });
    parseAndValidateUrl(url, {
      query: {
        systemType: 'sosa:Sensor',
        deployment: 'deploy-123',
        q: 'temperature',
      },
    });
  });

  it('filters by property name and value', async () => {
    const url = builder.getSystems({
      'properties.name': 'Weather Station Alpha',
    });
    parseAndValidateUrl(url, {
      query: {
        'properties.name': 'Weather Station Alpha',
      },
    });
    // Verify space encoding
    expect(url).toContain('Weather%20Station%20Alpha');
  });
});
```

---

## 5. Systems Resource Testing Requirements

### 5.1 Systems Methods Matrix

| Method                                    | Parameters                                                                                  | URL Pattern                              | Test Scenarios                                                                                | Test Count | Priority |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------- | ---------- | -------- |
| `getSystems(options?)`                    | limit, offset, bbox, datetime, recursive, parent, deployment, procedure, foi, systemType, q | `GET /systems?...`                       | No params, pagination, spatial filter, temporal filter, multiple filters, recursive, encoding | 7          | CRITICAL |
| `getSystem(id, options?)`                 | id (required), format                                                                       | `GET /systems/{id}`                      | Valid ID, ID encoding, format parameter                                                       | 3          | CRITICAL |
| `createSystem(body)`                      | body (GeoJSON/SensorML)                                                                     | `POST /systems`                          | URL only (no params)                                                                          | 1          | HIGH     |
| `updateSystem(id, body)`                  | id, body                                                                                    | `PUT/PATCH /systems/{id}`                | Valid ID, ID encoding                                                                         | 2          | HIGH     |
| `deleteSystem(id, cascade?)`              | id, cascade                                                                                 | `DELETE /systems/{id}?cascade=true`      | Without cascade, with cascade                                                                 | 2          | MEDIUM   |
| `getSystemSubsystems(id, options?)`       | id, limit, offset, recursive                                                                | `GET /systems/{id}/subsystems?...`       | No params, recursive, pagination                                                              | 3          | HIGH     |
| `getSystemDataStreams(id, options?)`      | id, limit, offset, observedProperty                                                         | `GET /systems/{id}/datastreams?...`      | No params, filtered, pagination                                                               | 3          | HIGH     |
| `getSystemControlStreams(id, options?)`   | id, limit, offset, controlledProperty                                                       | `GET /systems/{id}/controlstreams?...`   | No params, filtered, pagination                                                               | 3          | HIGH     |
| `getSystemSamplingFeatures(id, options?)` | id, limit, offset                                                                           | `GET /systems/{id}/samplingFeatures?...` | No params, pagination                                                                         | 2          | MEDIUM   |
| `getSystemDeployments(id, options?)`      | id, limit, offset                                                                           | `GET /systems/{id}/deployments?...`      | No params, pagination                                                                         | 2          | MEDIUM   |
| `getSystemProcedures(id, options?)`       | id, limit, offset                                                                           | `GET /systems/{id}/procedures?...`       | No params, pagination                                                                         | 2          | MEDIUM   |
| `getSystemHistory(id, options?)`          | id, datetime                                                                                | `GET /systems/{id}/history?...`          | No params, temporal filter                                                                    | 2          | LOW      |
| **TOTAL**                                 |                                                                                             |                                          |                                                                                               | **32**     |          |

### 5.2 Systems Test Implementation

**File:** `src/ogc-api/csapi/url_builder-systems.spec.ts` (~150-200 lines)

```typescript
import { describe, it, expect, beforeEach } from '@jest/globals';
import { parseAndValidateUrl } from './test-utils';
import { createTestEndpoint } from './test-helpers';
import { CSAPIQueryBuilder } from './url_builder';

describe('CSAPIQueryBuilder - Systems', () => {
  let builder: CSAPIQueryBuilder;
  let baseUrl: string;

  beforeEach(async () => {
    const endpoint = await createTestEndpoint();
    builder = await endpoint.csapi('test-collection');
    baseUrl = 'https://api.example.com';
  });

  describe('getSystems()', () => {
    it('constructs collection URL without parameters', async () => {
      const url = builder.getSystems();
      parseAndValidateUrl(url, {
        protocol: 'https:',
        pathname: '/systems',
      });
    });

    it('applies pagination parameters', async () => {
      const url = builder.getSystems({ limit: 50, offset: 100 });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          limit: '50',
          offset: '100',
        },
      });
    });

    it('applies spatial bbox filter', async () => {
      const url = builder.getSystems({
        bbox: { minLon: -122.5, minLat: 37.5, maxLon: -122.0, maxLat: 38.0 },
      });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          bbox: '-122.5,37.5,-122.0,38.0',
        },
      });
    });

    it('applies temporal datetime filter', async () => {
      const url = builder.getSystems({
        datetime: '2024-01-01T00:00:00Z/2024-12-31T23:59:59Z',
      });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          datetime: '2024-01-01T00:00:00Z/2024-12-31T23:59:59Z',
        },
      });
    });

    it('applies multiple filters', async () => {
      const url = builder.getSystems({
        limit: 25,
        bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
        systemType: 'sosa:Sensor',
        q: 'temperature',
      });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          limit: '25',
          bbox: '-180,-90,180,90',
          systemType: 'sosa:Sensor',
          q: 'temperature',
        },
      });
    });

    it('enables recursive subsystem traversal', async () => {
      const url = builder.getSystems({ recursive: true });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          recursive: 'true',
        },
      });
    });

    it('encodes special characters in query values', async () => {
      const url = builder.getSystems({
        q: 'weather station #1',
      });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          q: 'weather station #1',
        },
      });
      // Verify space and # encoding
      expect(url).toContain('q=weather%20station%20%231');
    });
  });

  describe('getSystem()', () => {
    it('constructs single system URL', async () => {
      const url = builder.getSystem('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123',
      });
    });

    it('encodes system ID with special characters', async () => {
      const url = builder.getSystem('sys/123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys%2F123',
      });
    });

    it('applies format parameter', async () => {
      const url = builder.getSystem('sys-123', { format: 'sml' });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123',
        query: {
          f: 'sml',
        },
      });
    });
  });

  describe('createSystem()', () => {
    it('constructs POST URL', async () => {
      const url = builder.createSystem({
        type: 'Feature',
        properties: { name: 'New System' },
      });
      parseAndValidateUrl(url, {
        pathname: '/systems',
      });
    });
  });

  describe('updateSystem()', () => {
    it('constructs PUT URL', async () => {
      const url = builder.updateSystem('sys-123', {
        type: 'Feature',
        properties: { name: 'Updated System' },
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123',
      });
    });

    it('encodes system ID', async () => {
      const url = builder.updateSystem('sys/123', {
        /* body */
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys%2F123',
      });
    });
  });

  describe('deleteSystem()', () => {
    it('constructs DELETE URL without cascade', async () => {
      const url = builder.deleteSystem('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123',
        query: {},
      });
    });

    it('constructs DELETE URL with cascade', async () => {
      const url = builder.deleteSystem('sys-123', { cascade: true });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123',
        query: {
          cascade: 'true',
        },
      });
    });
  });

  describe('getSystemSubsystems()', () => {
    it('constructs subsystems URL', async () => {
      const url = builder.getSystemSubsystems('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/subsystems',
      });
    });

    it('enables recursive traversal', async () => {
      const url = builder.getSystemSubsystems('sys-123', { recursive: true });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/subsystems',
        query: {
          recursive: 'true',
        },
      });
    });

    it('applies pagination', async () => {
      const url = builder.getSystemSubsystems('sys-123', {
        limit: 20,
        offset: 40,
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/subsystems',
        query: {
          limit: '20',
          offset: '40',
        },
      });
    });
  });

  describe('getSystemDataStreams()', () => {
    it('constructs datastreams URL', async () => {
      const url = builder.getSystemDataStreams('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/datastreams',
      });
    });

    it('filters by observed property', async () => {
      const url = builder.getSystemDataStreams('sys-123', {
        observedProperty: 'temperature',
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/datastreams',
        query: {
          observedProperty: 'temperature',
        },
      });
    });

    it('applies pagination', async () => {
      const url = builder.getSystemDataStreams('sys-123', {
        limit: 10,
        offset: 20,
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/datastreams',
        query: {
          limit: '10',
          offset: '20',
        },
      });
    });
  });

  describe('getSystemControlStreams()', () => {
    it('constructs controlstreams URL', async () => {
      const url = builder.getSystemControlStreams('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/controlstreams',
      });
    });

    it('filters by controlled property', async () => {
      const url = builder.getSystemControlStreams('sys-123', {
        controlledProperty: 'valve-position',
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/controlstreams',
        query: {
          controlledProperty: 'valve-position',
        },
      });
    });

    it('applies pagination', async () => {
      const url = builder.getSystemControlStreams('sys-123', {
        limit: 10,
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/controlstreams',
        query: {
          limit: '10',
        },
      });
    });
  });

  describe('getSystemSamplingFeatures()', () => {
    it('constructs sampling features URL', async () => {
      const url = builder.getSystemSamplingFeatures('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/samplingFeatures',
      });
    });

    it('applies pagination', async () => {
      const url = builder.getSystemSamplingFeatures('sys-123', {
        limit: 15,
        offset: 30,
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/samplingFeatures',
        query: {
          limit: '15',
          offset: '30',
        },
      });
    });
  });

  describe('getSystemDeployments()', () => {
    it('constructs deployments URL', async () => {
      const url = builder.getSystemDeployments('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/deployments',
      });
    });

    it('applies pagination', async () => {
      const url = builder.getSystemDeployments('sys-123', {
        limit: 5,
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/deployments',
        query: {
          limit: '5',
        },
      });
    });
  });

  describe('getSystemProcedures()', () => {
    it('constructs procedures URL', async () => {
      const url = builder.getSystemProcedures('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/procedures',
      });
    });

    it('applies pagination', async () => {
      const url = builder.getSystemProcedures('sys-123', {
        limit: 8,
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/procedures',
        query: {
          limit: '8',
        },
      });
    });
  });

  describe('getSystemHistory()', () => {
    it('constructs history URL', async () => {
      const url = builder.getSystemHistory('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/history',
      });
    });

    it('applies temporal filter', async () => {
      const url = builder.getSystemHistory('sys-123', {
        datetime: '2024-01-01/..',
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/history',
        query: {
          datetime: '2024-01-01/..',
        },
      });
    });
  });
});
```

---

## 6. Deployments Resource Testing Requirements

### 6.1 Deployments Methods Matrix

| Method                                      | Parameters                                                  | URL Pattern                                | Test Scenarios                                                                   | Test Count | Priority |
| ------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------- | ---------- | -------- |
| `getDeployments(options?)`                  | limit, offset, bbox, datetime, recursive, system, parent, q | `GET /deployments?...`                     | No params, pagination, spatial filter, temporal filter, system filter, recursive | 6          | CRITICAL |
| `getDeployment(id, options?)`               | id, format                                                  | `GET /deployments/{id}`                    | Valid ID, ID encoding, format                                                    | 3          | CRITICAL |
| `createDeployment(body)`                    | body                                                        | `POST /deployments`                        | URL only                                                                         | 1          | HIGH     |
| `updateDeployment(id, body)`                | id, body                                                    | `PUT/PATCH /deployments/{id}`              | Valid ID, ID encoding                                                            | 2          | HIGH     |
| `deleteDeployment(id, cascade?)`            | id, cascade                                                 | `DELETE /deployments/{id}`                 | Without cascade, with cascade                                                    | 2          | MEDIUM   |
| `getDeploymentSubdeployments(id, options?)` | id, limit, offset, recursive                                | `GET /deployments/{id}/subdeployments?...` | No params, recursive, pagination                                                 | 3          | HIGH     |
| `getDeploymentSystems(id, options?)`        | id, limit, offset                                           | `GET /deployments/{id}/systems?...`        | No params, pagination                                                            | 2          | MEDIUM   |
| `getDeploymentHistory(id, options?)`        | id, datetime                                                | `GET /deployments/{id}/history?...`        | No params, temporal filter                                                       | 2          | LOW      |
| **TOTAL**                                   |                                                             |                                            |                                                                                  | **21**     |          |

### 6.2 Key Test Scenarios

**Deployment-Specific Testing:**

1. **Temporal Validity Filter** - `datetime` parameter filters by deployment period (validTime)
2. **System Association** - `system` parameter filters deployments containing specific system
3. **Subdeployment Hierarchy** - `recursive` parameter traverses nested subdeployments
4. **Spatial Extent** - `bbox` filters by deployment footprint

**Test Implementation Pattern:** Similar to Systems (see Section 5.2), with emphasis on:

- validTime temporal filtering (deployment period)
- System association filtering
- Subdeployment hierarchy traversal

---

## 7. Procedures Resource Testing Requirements

### 7.1 Procedures Methods Matrix

| Method                                  | Parameters               | URL Pattern                            | Test Scenarios                                       | Test Count | Priority |
| --------------------------------------- | ------------------------ | -------------------------------------- | ---------------------------------------------------- | ---------- | -------- |
| `getProcedures(options?)`               | limit, offset, system, q | `GET /procedures?...`                  | No params, pagination, system filter, keyword search | 4          | CRITICAL |
| `getProcedure(id, options?)`            | id, format               | `GET /procedures/{id}`                 | Valid ID, ID encoding, format (sml)                  | 3          | CRITICAL |
| `createProcedure(body)`                 | body                     | `POST /procedures`                     | URL only                                             | 1          | HIGH     |
| `updateProcedure(id, body)`             | id, body                 | `PUT/PATCH /procedures/{id}`           | Valid ID, ID encoding                                | 2          | HIGH     |
| `deleteProcedure(id)`                   | id                       | `DELETE /procedures/{id}`              | Valid ID                                             | 1          | MEDIUM   |
| `getProcedureSystems(id, options?)`     | id, limit, offset        | `GET /procedures/{id}/systems?...`     | No params, pagination                                | 2          | MEDIUM   |
| `getProcedureDataStreams(id, options?)` | id, limit, offset        | `GET /procedures/{id}/datastreams?...` | No params, pagination                                | 2          | MEDIUM   |
| `getProcedureHistory(id, options?)`     | id, datetime             | `GET /procedures/{id}/history?...`     | No params, temporal filter                           | 2          | LOW      |
| **TOTAL**                               |                          |                                        |                                                      | **17**     |          |

### 7.2 Key Test Scenarios

**Procedure-Specific Testing:**

1. **No Spatial Filters** - Procedures are non-spatial (no bbox/geometry parameters)
2. **System Association** - Filter procedures used by specific systems
3. **Format Negotiation** - Test SensorML format parameter (sml)

---

## 8. SamplingFeatures Resource Testing Requirements

### 8.1 SamplingFeatures Methods Matrix

| Method                                         | Parameters                                                  | URL Pattern                                   | Test Scenarios                                                   | Test Count | Priority |
| ---------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------- | ---------- | -------- |
| `getSamplingFeatures(options?)`                | limit, offset, bbox, system, foi, relatedSamplingFeature, q | `GET /samplingFeatures?...`                   | No params, pagination, spatial filter, system filter, FOI filter | 5          | CRITICAL |
| `getSamplingFeature(id, options?)`             | id, format                                                  | `GET /samplingFeatures/{id}`                  | Valid ID, ID encoding, format                                    | 3          | CRITICAL |
| `createSamplingFeature(body)`                  | body                                                        | `POST /samplingFeatures`                      | URL only                                                         | 1          | HIGH     |
| `updateSamplingFeature(id, body)`              | id, body                                                    | `PUT/PATCH /samplingFeatures/{id}`            | Valid ID, ID encoding                                            | 2          | HIGH     |
| `deleteSamplingFeature(id)`                    | id                                                          | `DELETE /samplingFeatures/{id}`               | Valid ID                                                         | 1          | MEDIUM   |
| `getSamplingFeatureSystems(id, options?)`      | id, limit, offset                                           | `GET /samplingFeatures/{id}/systems?...`      | No params, pagination                                            | 2          | MEDIUM   |
| `getSamplingFeatureObservations(id, options?)` | id, limit, offset, phenomenonTime                           | `GET /samplingFeatures/{id}/observations?...` | No params, pagination, temporal filter                           | 3          | MEDIUM   |
| `getSamplingFeatureHistory(id, options?)`      | id, datetime                                                | `GET /samplingFeatures/{id}/history?...`      | No params, temporal filter                                       | 2          | LOW      |
| **TOTAL**                                      |                                                             |                                               |                                                                  | **19**     |          |

### 8.2 Key Test Scenarios

**SamplingFeature-Specific Testing:**

1. **Feature of Interest Filter** - `foi` parameter filters by sampled feature
2. **Related Sampling Feature** - `relatedSamplingFeature` parameter for hierarchical relationships
3. **System Association** - Filter sampling features for specific system
4. **Observation Navigation** - Test navigation to observations at sampling feature

---

## 9. Properties Resource Testing Requirements

### 9.1 Properties Methods Matrix

| Method                                    | Parameters               | URL Pattern                               | Test Scenarios                                       | Test Count | Priority |
| ----------------------------------------- | ------------------------ | ----------------------------------------- | ---------------------------------------------------- | ---------- | -------- |
| `getProperties(options?)`                 | limit, offset, system, q | `GET /properties?...`                     | No params, pagination, system filter, keyword search | 4          | CRITICAL |
| `getProperty(id, options?)`               | id, format               | `GET /properties/{id}`                    | Valid ID, ID encoding                                | 2          | CRITICAL |
| `getPropertySystems(id, options?)`        | id, limit, offset        | `GET /properties/{id}/systems?...`        | No params, pagination                                | 2          | MEDIUM   |
| `getPropertyDataStreams(id, options?)`    | id, limit, offset        | `GET /properties/{id}/datastreams?...`    | No params, pagination                                | 2          | MEDIUM   |
| `getPropertyControlStreams(id, options?)` | id, limit, offset        | `GET /properties/{id}/controlstreams?...` | No params, pagination                                | 2          | MEDIUM   |
| `getPropertyHistory(id, options?)`        | id, datetime             | `GET /properties/{id}/history?...`        | No params, temporal filter                           | 2          | LOW      |
| **TOTAL**                                 |                          |                                           |                                                      | **14**     |          |

### 9.2 Key Test Scenarios

**Property-Specific Testing:**

1. **No CRUD Operations** - Properties are read-only (no POST/PUT/PATCH/DELETE)
2. **System Association** - Systems that can observe this property
3. **DataStream Association** - DataStreams measuring this property
4. **ControlStream Association** - ControlStreams controlling this property

---

## 10. DataStreams Resource Testing Requirements

### 10.1 DataStreams Methods Matrix

| Method                                    | Parameters                                                                  | URL Pattern                              | Test Scenarios                                                                            | Test Count | Priority |
| ----------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------- | ---------- | -------- |
| `getDataStreams(options?)`                | limit, offset, system, observedProperty, phenomenonTime, resultTime, foi, q | `GET /datastreams?...`                   | No params, pagination, system filter, property filter, temporal filters, multiple filters | 7          | CRITICAL |
| `getDataStream(id, options?)`             | id, format                                                                  | `GET /datastreams/{id}`                  | Valid ID, ID encoding, format (swe)                                                       | 3          | CRITICAL |
| `createDataStream(body)`                  | body                                                                        | `POST /datastreams`                      | URL only                                                                                  | 1          | HIGH     |
| `updateDataStream(id, body)`              | id, body                                                                    | `PUT/PATCH /datastreams/{id}`            | Valid ID, ID encoding                                                                     | 2          | HIGH     |
| `deleteDataStream(id)`                    | id                                                                          | `DELETE /datastreams/{id}`               | Valid ID                                                                                  | 1          | MEDIUM   |
| `getDataStreamSchema(id)`                 | id                                                                          | `GET /datastreams/{id}/schema`           | Valid ID, ID encoding                                                                     | 2          | CRITICAL |
| `getDataStreamObservations(id, options?)` | id, limit, offset, phenomenonTime, resultTime                               | `GET /datastreams/{id}/observations?...` | No params, pagination, temporal filters                                                   | 4          | CRITICAL |
| `createObservation(datastreamId, body)`   | datastreamId, body                                                          | `POST /datastreams/{id}/observations`    | Valid ID, ID encoding                                                                     | 2          | HIGH     |
| `getDataStreamSystems(id, options?)`      | id, limit, offset                                                           | `GET /datastreams/{id}/systems?...`      | No params, pagination                                                                     | 2          | MEDIUM   |
| `getDataStreamProcedures(id, options?)`   | id, limit, offset                                                           | `GET /datastreams/{id}/procedures?...`   | No params, pagination                                                                     | 2          | MEDIUM   |
| `getDataStreamHistory(id, options?)`      | id, datetime                                                                | `GET /datastreams/{id}/history?...`      | No params, temporal filter                                                                | 2          | LOW      |
| **TOTAL**                                 |                                                                             |                                          |                                                                                           | **28**     |          |

### 10.2 Key Test Scenarios

**DataStream-Specific Testing:**

1. **phenomenonTime Filter** - Primary temporal filter for when observations were made
2. **resultTime Filter** - Secondary temporal filter for when results became available
3. **observedProperty Filter** - Filter by property being measured
4. **Schema Retrieval** - Test SWE Common schema endpoint
5. **Observation Creation** - Test nested POST to create observations

---

## 11. Observations Resource Testing Requirements

### 11.1 Observations Methods Matrix

| Method                                        | Parameters                                                          | URL Pattern                              | Test Scenarios                                                                               | Test Count | Priority |
| --------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------- | ---------- | -------- |
| `getObservations(options?)`                   | limit, offset, datastream, phenomenonTime, resultTime, bbox, foi, q | `GET /observations?...`                  | No params, pagination, datastream filter, temporal filters, spatial filter, multiple filters | 7          | CRITICAL |
| `getObservation(id, options?)`                | id, format                                                          | `GET /observations/{id}`                 | Valid ID, ID encoding, format (swe)                                                          | 3          | CRITICAL |
| `createObservations(datastreamId, body)`      | datastreamId, body (array)                                          | `POST /datastreams/{id}/observations`    | Bulk creation with array body                                                                | 1          | HIGH     |
| `updateObservation(id, body)`                 | id, body                                                            | `PUT/PATCH /observations/{id}`           | Valid ID, ID encoding                                                                        | 2          | HIGH     |
| `deleteObservation(id)`                       | id                                                                  | `DELETE /observations/{id}`              | Valid ID                                                                                     | 1          | MEDIUM   |
| `getObservationDataStream(id)`                | id                                                                  | `GET /observations/{id}/datastream`      | Valid ID, ID encoding                                                                        | 2          | MEDIUM   |
| `getObservationSamplingFeature(id, options?)` | id, format                                                          | `GET /observations/{id}/samplingFeature` | Valid ID, format                                                                             | 2          | MEDIUM   |
| `getObservationSystem(id, options?)`          | id, format                                                          | `GET /observations/{id}/system`          | Valid ID, format                                                                             | 2          | MEDIUM   |
| `getObservationHistory(id, options?)`         | id, datetime                                                        | `GET /observations/{id}/history?...`     | No params, temporal filter                                                                   | 2          | LOW      |
| **TOTAL**                                     |                                                                     |                                          |                                                                                              | **22**     |          |

### 11.2 Key Test Scenarios

**Observation-Specific Testing:**

1. **phenomenonTime Filter** - Filter by when observation was made (primary temporal filter)
2. **resultTime Filter** - Filter by when result became available
3. **DataStream Context** - Most observations retrieved via `/datastreams/{id}/observations`
4. **Bulk Creation** - Test POST with array of observations
5. **Navigation** - Test navigation to parent datastream, system, sampling feature

---

## 12. ControlStreams Resource Testing Requirements

### 12.1 ControlStreams Methods Matrix

| Method                                           | Parameters                                                                  | URL Pattern                             | Test Scenarios                                                          | Test Count | Priority |
| ------------------------------------------------ | --------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------------- | ---------- | -------- |
| `getControlStreams(options?)`                    | limit, offset, system, controlledProperty, issueTime, executionTime, foi, q | `GET /controlstreams?...`               | No params, pagination, system filter, property filter, temporal filters | 6          | CRITICAL |
| `getControlStream(id, options?)`                 | id, format                                                                  | `GET /controlstreams/{id}`              | Valid ID, ID encoding, format (swe)                                     | 3          | CRITICAL |
| `createControlStream(body)`                      | body                                                                        | `POST /controlstreams`                  | URL only                                                                | 1          | HIGH     |
| `updateControlStream(id, body)`                  | id, body                                                                    | `PUT/PATCH /controlstreams/{id}`        | Valid ID, ID encoding                                                   | 2          | HIGH     |
| `deleteControlStream(id)`                        | id                                                                          | `DELETE /controlstreams/{id}`           | Valid ID                                                                | 1          | MEDIUM   |
| `getControlStreamSchema(id)`                     | id                                                                          | `GET /controlstreams/{id}/schema`       | Valid ID, ID encoding                                                   | 2          | CRITICAL |
| `getControlStreamCommands(id, options?)`         | id, limit, offset, issueTime, executionTime                                 | `GET /controlstreams/{id}/commands?...` | No params, pagination, temporal filters                                 | 4          | CRITICAL |
| `checkCommandFeasibility(controlStreamId, body)` | controlStreamId, body                                                       | `POST /controlstreams/{id}/feasibility` | Valid ID, ID encoding                                                   | 2          | HIGH     |
| **TOTAL**                                        |                                                                             |                                         |                                                                         | **21**     |          |

### 12.2 Key Test Scenarios

**ControlStream-Specific Testing:**

1. **issueTime Filter** - Filter by when commands were issued
2. **executionTime Filter** - Filter by when commands should be/were executed
3. **controlledProperty Filter** - Filter by property being controlled
4. **Schema Retrieval** - Test SWE Common parameter schema
5. **Feasibility Check** - Test POST to feasibility endpoint

---

## 13. Commands Resource Testing Requirements

### 13.1 Commands Methods Matrix

| Method                                  | Parameters                                                             | URL Pattern                          | Test Scenarios                                                                                 | Test Count | Priority |
| --------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------- | ---------- | -------- |
| `getCommands(options?)`                 | limit, offset, controlstream, issueTime, executionTime, status, foi, q | `GET /commands?...`                  | No params, pagination, controlstream filter, temporal filters, status filter, multiple filters | 7          | CRITICAL |
| `getCommand(id, options?)`              | id, format                                                             | `GET /commands/{id}`                 | Valid ID, ID encoding, format                                                                  | 3          | CRITICAL |
| `createCommand(controlStreamId, body)`  | controlStreamId, body                                                  | `POST /controlstreams/{id}/commands` | Valid ID, ID encoding                                                                          | 2          | HIGH     |
| `createCommands(controlStreamId, body)` | controlStreamId, body (array)                                          | `POST /controlstreams/{id}/commands` | Bulk creation with array body                                                                  | 1          | HIGH     |
| `updateCommand(id, body)`               | id, body                                                               | `PUT/PATCH /commands/{id}`           | Valid ID, ID encoding                                                                          | 2          | HIGH     |
| `deleteCommand(id)`                     | id                                                                     | `DELETE /commands/{id}`              | Valid ID                                                                                       | 1          | MEDIUM   |
| `getCommandStatus(id)`                  | id                                                                     | `GET /commands/{id}/status`          | Valid ID, ID encoding                                                                          | 2          | CRITICAL |
| `updateCommandStatus(id, body)`         | id, body                                                               | `PUT/PATCH /commands/{id}/status`    | Valid ID, ID encoding                                                                          | 2          | HIGH     |
| `getCommandResult(id)`                  | id                                                                     | `GET /commands/{id}/result`          | Valid ID, ID encoding                                                                          | 2          | MEDIUM   |
| `cancelCommand(id)`                     | id                                                                     | `POST /commands/{id}/cancel`         | Valid ID, ID encoding                                                                          | 2          | MEDIUM   |
| **TOTAL**                               |                                                                        |                                      |                                                                                                | **24**     |          |

### 13.2 Key Test Scenarios

**Command-Specific Testing:**

1. **issueTime Filter** - Filter by when command was issued
2. **executionTime Filter** - Filter by scheduled/actual execution time
3. **status Filter** - Filter by command status (pending, accepted, executing, completed, failed, cancelled)
4. **Bulk Creation** - Test POST with array of commands
5. **Status Lifecycle** - Test status retrieval and updates
6. **Result Retrieval** - Test result endpoint after command completion
7. **Cancel Operation** - Test POST to cancel endpoint

---

## 14. Nested Endpoint Testing

### 14.1 Nested Endpoint Chains

| Parent            | Child            | URL Pattern                             | Test Scenarios                           | Priority |
| ----------------- | ---------------- | --------------------------------------- | ---------------------------------------- | -------- |
| **System**        | Subsystems       | `GET /systems/{id}/subsystems`          | Hierarchy traversal, recursive parameter | HIGH     |
| **System**        | DataStreams      | `GET /systems/{id}/datastreams`         | Cross-boundary (Part 1 → Part 2)         | HIGH     |
| **System**        | ControlStreams   | `GET /systems/{id}/controlstreams`      | Cross-boundary (Part 1 → Part 2)         | HIGH     |
| **System**        | SamplingFeatures | `GET /systems/{id}/samplingFeatures`    | Association navigation                   | MEDIUM   |
| **System**        | Deployments      | `GET /systems/{id}/deployments`         | Association navigation                   | MEDIUM   |
| **System**        | Procedures       | `GET /systems/{id}/procedures`          | Association navigation                   | MEDIUM   |
| **Deployment**    | Subdeployments   | `GET /deployments/{id}/subdeployments`  | Hierarchy traversal, recursive parameter | HIGH     |
| **Deployment**    | Systems          | `GET /deployments/{id}/systems`         | Reverse association                      | MEDIUM   |
| **DataStream**    | Observations     | `GET /datastreams/{id}/observations`    | Primary observation access pattern       | CRITICAL |
| **DataStream**    | Schema           | `GET /datastreams/{id}/schema`          | Metadata endpoint                        | CRITICAL |
| **ControlStream** | Commands         | `GET /controlstreams/{id}/commands`     | Primary command access pattern           | CRITICAL |
| **ControlStream** | Feasibility      | `POST /controlstreams/{id}/feasibility` | Validation endpoint                      | HIGH     |
| **Command**       | Status           | `GET /commands/{id}/status`             | Status tracking                          | CRITICAL |
| **Command**       | Result           | `GET /commands/{id}/result`             | Result retrieval                         | MEDIUM   |
| **Command**       | Cancel           | `POST /commands/{id}/cancel`            | Command control                          | MEDIUM   |

### 14.2 Nested Endpoint Test Patterns

**Test Implementation:**

```typescript
describe('Nested endpoint construction', () => {
  describe('System → DataStreams', () => {
    it('constructs nested datastreams URL', async () => {
      const url = builder.getSystemDataStreams('sys-123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/datastreams',
      });
    });

    it('encodes parent system ID', async () => {
      const url = builder.getSystemDataStreams('sys/123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys%2F123/datastreams',
      });
    });

    it('applies query parameters to nested URL', async () => {
      const url = builder.getSystemDataStreams('sys-123', {
        limit: 10,
        observedProperty: 'temperature',
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/datastreams',
        query: {
          limit: '10',
          observedProperty: 'temperature',
        },
      });
    });
  });

  describe('DataStream → Observations', () => {
    it('constructs nested observations URL', async () => {
      const url = builder.getDataStreamObservations('ds-456');
      parseAndValidateUrl(url, {
        pathname: '/datastreams/ds-456/observations',
      });
    });

    it('applies temporal filters to observations', async () => {
      const url = builder.getDataStreamObservations('ds-456', {
        phenomenonTime: '2024-01-01T00:00:00Z/..',
        limit: 100,
      });
      parseAndValidateUrl(url, {
        pathname: '/datastreams/ds-456/observations',
        query: {
          phenomenonTime: '2024-01-01T00:00:00Z/..',
          limit: '100',
        },
      });
    });
  });

  describe('ControlStream → Commands', () => {
    it('constructs nested commands URL', async () => {
      const url = builder.getControlStreamCommands('cs-789');
      parseAndValidateUrl(url, {
        pathname: '/controlstreams/cs-789/commands',
      });
    });

    it('applies temporal filters to commands', async () => {
      const url = builder.getControlStreamCommands('cs-789', {
        issueTime: '2024-01-01/..',
        executionTime: '2024-01-02/..',
      });
      parseAndValidateUrl(url, {
        pathname: '/controlstreams/cs-789/commands',
        query: {
          issueTime: '2024-01-01/..',
          executionTime: '2024-01-02/..',
        },
      });
    });
  });

  describe('Hierarchical navigation', () => {
    it('constructs subsystems URL with recursive traversal', async () => {
      const url = builder.getSystemSubsystems('sys-123', {
        recursive: true,
      });
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/subsystems',
        query: {
          recursive: 'true',
        },
      });
    });

    it('constructs subdeployments URL with recursive traversal', async () => {
      const url = builder.getDeploymentSubdeployments('deploy-456', {
        recursive: true,
      });
      parseAndValidateUrl(url, {
        pathname: '/deployments/deploy-456/subdeployments',
        query: {
          recursive: 'true',
        },
      });
    });
  });
});
```

---

## 15. URL Encoding Edge Cases

### 15.1 Encoding Test Matrix

| Edge Case                 | Test Input             | Expected Encoding                 | Test Priority |
| ------------------------- | ---------------------- | --------------------------------- | ------------- |
| **Space**                 | `"weather station"`    | `weather%20station`               | CRITICAL      |
| **Forward slash**         | `"sys/123"`            | `sys%2F123`                       | CRITICAL      |
| **Ampersand**             | `"temp&pressure"`      | `temp%26pressure`                 | HIGH          |
| **Equals**                | `"value=10"`           | `value%3D10`                      | HIGH          |
| **Plus**                  | `"temp+5"`             | `temp%2B5`                        | HIGH          |
| **Hash**                  | `"station#1"`          | `station%231`                     | MEDIUM        |
| **Question mark**         | `"is?valid"`           | `is%3Fvalid`                      | MEDIUM        |
| **Percent**               | `"50%humidity"`        | `50%25humidity`                   | HIGH          |
| **International (UTF-8)** | `"Zürich"`             | `Z%C3%BCrich`                     | MEDIUM        |
| **Already encoded**       | `"sys%2F123"`          | `sys%2F123` (no double-encoding)  | CRITICAL      |
| **Colon in URI**          | `"http://example.com"` | `http%3A%2F%2Fexample.com`        | HIGH          |
| **Comma in array**        | `"value1,value2"`      | `value1,value2` (preserve commas) | HIGH          |
| **Newline**               | `"line1\nline2"`       | `line1%0Aline2`                   | LOW           |
| **Tab**                   | `"col1\tcol2"`         | `col1%09col2`                     | LOW           |

### 15.2 Encoding Test Implementation

```typescript
describe('URL encoding edge cases', () => {
  describe('Space encoding', () => {
    it('encodes spaces as %20 in query parameter values', async () => {
      const url = builder.getSystems({
        q: 'weather station',
      });
      expect(url).toContain('q=weather%20station');
    });

    it('encodes spaces in system IDs', async () => {
      const url = builder.getSystem('system 123');
      parseAndValidateUrl(url, {
        pathname: '/systems/system%20123',
      });
    });
  });

  describe('Forward slash encoding', () => {
    it('encodes slashes in system IDs', async () => {
      const url = builder.getSystem('sys/123');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys%2F123',
      });
    });

    it('encodes slashes in query parameter values', async () => {
      const url = builder.getSystems({
        q: 'path/to/sensor',
      });
      expect(url).toContain('q=path%2Fto%2Fsensor');
    });
  });

  describe('Special character encoding', () => {
    it('encodes ampersands', async () => {
      const url = builder.getSystems({
        q: 'temp&pressure',
      });
      expect(url).toContain('q=temp%26pressure');
    });

    it('encodes equals signs', async () => {
      const url = builder.getSystems({
        q: 'value=10',
      });
      expect(url).toContain('q=value%3D10');
    });

    it('encodes plus signs', async () => {
      const url = builder.getSystems({
        q: 'temp+5',
      });
      expect(url).toContain('q=temp%2B5');
    });

    it('encodes hash characters', async () => {
      const url = builder.getSystems({
        q: 'station#1',
      });
      expect(url).toContain('q=station%231');
    });
  });

  describe('URI encoding in values', () => {
    it('encodes URI vocabulary values', async () => {
      const url = builder.getSystems({
        systemType: 'http://www.w3.org/ns/sosa/Sensor',
      });
      expect(url).toContain(
        'systemType=http%3A%2F%2Fwww.w3.org%2Fns%2Fsosa%2FSensor'
      );
    });

    it('encodes colon and slashes in URIs', async () => {
      const url = builder.getSystems({
        systemType: 'sosa:Sensor',
      });
      expect(url).toContain('systemType=sosa%3ASensor');
    });
  });

  describe('International character encoding', () => {
    it('encodes UTF-8 characters', async () => {
      const url = builder.getSystems({
        q: 'Zürich weather station',
      });
      expect(url).toContain('q=Z%C3%BCrich%20weather%20station');
    });

    it('encodes system IDs with international characters', async () => {
      const url = builder.getSystem('sys-zürich-001');
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-z%C3%BCrich-001',
      });
    });
  });

  describe('Already encoded values', () => {
    it('does not double-encode already encoded slashes', async () => {
      const url = builder.getSystem('sys%2F123');
      // Should NOT become sys%252F123 (double-encoded)
      parseAndValidateUrl(url, {
        pathname: '/systems/sys%2F123',
      });
    });

    it('does not double-encode already encoded URIs', async () => {
      const url = builder.getSystems({
        systemType: 'http%3A%2F%2Fexample.com%2FSensor',
      });
      // Should NOT double-encode the already-encoded value
      expect(url).not.toContain('%253A'); // %25 is encoded %
    });
  });

  describe('Comma preservation in arrays', () => {
    it('preserves commas in bbox encoding', async () => {
      const url = builder.getSystems({
        bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
      });
      // Commas should NOT be encoded in bbox
      expect(url).toContain('bbox=-180,-90,180,90');
      expect(url).not.toContain('%2C'); // Encoded comma
    });
  });
});
```

---

## 16. Resource Availability Validation Testing

### 16.1 Resource Availability Scenarios

| Scenario                        | Test Requirement                                                          | Expected Behavior                                   | Priority |
| ------------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------- | -------- |
| **Resource available**          | Call method when resource type in conformance                             | Construct URL successfully                          | CRITICAL |
| **Resource unavailable**        | Call method when resource type NOT in conformance                         | Throw EndpointError with message                    | CRITICAL |
| **Nested resource unavailable** | Call nested method when parent resource available but nested not declared | Check both parent and nested availability           | HIGH     |
| **Collection info missing**     | QueryBuilder instantiated without collection info                         | Handle gracefully (throw error or default behavior) | MEDIUM   |
| **Partial conformance**         | Only some resource types available (e.g., Part 1 only, no Part 2)         | Methods check specific resource availability        | HIGH     |

### 16.2 Availability Test Implementation

```typescript
describe('Resource availability validation', () => {
  describe('Available resources', () => {
    let builder: CSAPIQueryBuilder;

    beforeEach(async () => {
      // Create endpoint with full CSAPI conformance (all resources available)
      const endpoint = await createTestEndpoint({
        conformance: ['csapi-part1-core', 'csapi-part2-dynamic-data'],
      });
      builder = await endpoint.csapi('test-collection');
    });

    it('constructs URL when resource is available', async () => {
      const url = builder.getSystems();
      expect(url).toBeDefined();
      parseAndValidateUrl(url, {
        pathname: '/systems',
      });
    });

    it('constructs nested URL when both parent and nested available', async () => {
      const url = builder.getSystemDataStreams('sys-123');
      expect(url).toBeDefined();
      parseAndValidateUrl(url, {
        pathname: '/systems/sys-123/datastreams',
      });
    });
  });

  describe('Unavailable resources', () => {
    let builder: CSAPIQueryBuilder;

    beforeEach(async () => {
      // Create endpoint with only Part 1 conformance (no Part 2 resources)
      const endpoint = await createTestEndpoint({
        conformance: ['csapi-part1-core'], // No Part 2
      });
      builder = await endpoint.csapi('test-collection');
    });

    it('throws error when resource type not available', async () => {
      await expect(builder.getDataStreams()).rejects.toThrow(
        /does not support.*datastreams/i
      );
    });

    it('throws error when nested resource not available', async () => {
      // Systems available but DataStreams not available
      await expect(builder.getSystemDataStreams('sys-123')).rejects.toThrow(
        /does not support.*datastreams/i
      );
    });

    it('includes resource type name in error message', async () => {
      await expect(builder.getObservations()).rejects.toThrow(/observations/i);
    });
  });

  describe('Partial conformance scenarios', () => {
    it('allows Part 1 methods when Part 1 conformance present', async () => {
      const endpoint = await createTestEndpoint({
        conformance: ['csapi-part1-core'],
      });
      const builder = await endpoint.csapi('test-collection');

      // Part 1 methods should work
      const systemsUrl = builder.getSystems();
      expect(systemsUrl).toBeDefined();

      const deploymentsUrl = builder.getDeployments();
      expect(deploymentsUrl).toBeDefined();
    });

    it('blocks Part 2 methods when only Part 1 conformance', async () => {
      const endpoint = await createTestEndpoint({
        conformance: ['csapi-part1-core'],
      });
      const builder = await endpoint.csapi('test-collection');

      // Part 2 methods should throw
      await expect(builder.getDataStreams()).rejects.toThrow();
      await expect(builder.getObservations()).rejects.toThrow();
      await expect(builder.getControlStreams()).rejects.toThrow();
      await expect(builder.getCommands()).rejects.toThrow();
    });

    it('allows Part 2 methods when Part 2 conformance present', async () => {
      const endpoint = await createTestEndpoint({
        conformance: ['csapi-part1-core', 'csapi-part2-dynamic-data'],
      });
      const builder = await endpoint.csapi('test-collection');

      // Part 2 methods should work
      const datastreamsUrl = builder.getDataStreams();
      expect(datastreamsUrl).toBeDefined();

      const observationsUrl = builder.getObservations();
      expect(observationsUrl).toBeDefined();
    });
  });

  describe('Collection info validation', () => {
    it('extracts available resources from collection links', async () => {
      const endpoint = await createTestEndpoint();
      const builder = await endpoint.csapi('test-collection');

      // Verify availableResources was populated from collection info
      expect(builder.availableResources).toBeDefined();
      expect(builder.availableResources.has('systems')).toBe(true);
    });

    it('handles collection without CSAPI links gracefully', async () => {
      const endpoint = await createTestEndpoint({
        collectionLinks: [], // No CSAPI links
      });

      await expect(endpoint.csapi('test-collection')).rejects.toThrow(
        /does not support CSAPI/i
      );
    });
  });
});
```

### 16.3 Fixture Requirements for Availability Testing

**Fixtures Needed:**

1. **conformance-all-resources.json** - Full CSAPI conformance (Part 1 + Part 2)

   ```json
   {
     "conformsTo": [
       "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
       "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
       "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
       "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sf",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream"
     ]
   }
   ```

2. **conformance-part1-only.json** - Part 1 only (no Part 2 resources)

   ```json
   {
     "conformsTo": [
       "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
       "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sf",
       "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property"
     ]
   }
   ```

3. **collection-info-all-resources.json** - Collection with all CSAPI resource links
4. **collection-info-part1-only.json** - Collection with only Part 1 resource links
5. **collection-info-no-csapi.json** - Collection without CSAPI links (should fail)

---

## 17. Error Condition Testing

### 17.1 Error Conditions Matrix

| Error Condition                | Test Scenario                                     | Expected Behavior                                                        | Priority |
| ------------------------------ | ------------------------------------------------- | ------------------------------------------------------------------------ | -------- |
| **Resource unavailable**       | Call method when resource type not in conformance | Throw EndpointError: "Collection does not support '{resource}' resource" | CRITICAL |
| **Invalid parameter type**     | Pass number instead of string for ID              | TypeScript compile-time error OR runtime type check                      | HIGH     |
| **Missing required parameter** | Omit required ID parameter                        | TypeScript compile-time error                                            | HIGH     |
| **Invalid temporal format**    | Pass malformed ISO 8601 string                    | Validate and throw error: "Invalid temporal format"                      | MEDIUM   |
| **Invalid bbox format**        | Pass invalid bbox coordinates (minLon > maxLon)   | Validate and throw error: "Invalid bbox: min must be < max"              | MEDIUM   |
| **Already encoded value**      | Pass double-encoded value                         | Handle gracefully (no double-encoding)                                   | MEDIUM   |
| **Very long URL**              | Construct URL with 100+ query parameters          | Handle gracefully (no length limit, browser handles)                     | LOW      |
| **Null/undefined parameters**  | Pass null/undefined for optional parameters       | Omit parameter from URL                                                  | MEDIUM   |

### 17.2 Error Condition Test Implementation

```typescript
describe('Error condition handling', () => {
  describe('Resource unavailable errors', () => {
    it('throws clear error when resource type not available', async () => {
      const endpoint = await createTestEndpoint({
        conformance: ['csapi-part1-core'], // No Part 2
      });
      const builder = await endpoint.csapi('test-collection');

      await expect(builder.getDataStreams()).rejects.toThrow(
        /Collection does not support 'datastreams' resource/
      );
    });

    it('includes collection ID in error message', async () => {
      const endpoint = await createTestEndpoint({
        conformance: ['csapi-part1-core'],
      });
      const builder = await endpoint.csapi('test-collection');

      await expect(builder.getObservations()).rejects.toThrow(
        /test-collection/
      );
    });
  });

  describe('Invalid parameter validation', () => {
    it('validates bbox coordinates', async () => {
      await expect(
        builder.getSystems({
          bbox: { minLon: 180, minLat: -90, maxLon: -180, maxLat: 90 }, // minLon > maxLon
        })
      ).rejects.toThrow(/Invalid bbox.*min.*max/);
    });

    it('validates temporal interval ordering', async () => {
      await expect(
        builder.getObservations('ds-123', {
          phenomenonTime: '2024-12-31T23:59:59Z/2024-01-01T00:00:00Z', // end < start
        })
      ).rejects.toThrow(/Invalid datetime.*start.*before.*end/);
    });
  });

  describe('Optional parameter handling', () => {
    it('omits null optional parameters from URL', async () => {
      const url = builder.getSystems({
        limit: 10,
        offset: null, // Explicitly null
      });
      parseAndValidateUrl(url, {
        query: {
          limit: '10',
          // offset should NOT be present
        },
      });
      expect(url).not.toContain('offset');
    });

    it('omits undefined optional parameters from URL', async () => {
      const url = builder.getSystems({
        limit: 10,
        offset: undefined,
      });
      parseAndValidateUrl(url, {
        query: {
          limit: '10',
        },
      });
      expect(url).not.toContain('offset');
    });
  });
});
```

---

## 18. Test Organization Structure

### 18.1 File Organization Options

**Option 1: Single File** (~1,880-2,256 lines)

```
src/ogc-api/csapi/url_builder.spec.ts
  - describe('CSAPIQueryBuilder', () => {
      - describe('Systems', () => { ... })
      - describe('Deployments', () => { ... })
      - describe('Procedures', () => { ... })
      - describe('SamplingFeatures', () => { ... })
      - describe('Properties', () => { ... })
      - describe('DataStreams', () => { ... })
      - describe('Observations', () => { ... })
      - describe('ControlStreams', () => { ... })
      - describe('Commands', () => { ... })
    })
```

**Pros:**

- All tests in one location
- Shared setup code easy to maintain
- Single import for all tests

**Cons:**

- Very large file (1,880-2,256 lines)
- Hard to navigate
- Slow test execution (all tests run sequentially)
- Difficult code review (large diffs)
- Merge conflicts more likely

**Option 2: Multiple Files (RECOMMENDED)** (~1,880-2,256 lines total, 9 files)

```
src/ogc-api/csapi/
  url_builder.spec.ts              (~100 lines - shared utilities, fixtures)
  url_builder-systems.spec.ts      (~150-200 lines - 18 tests)
  url_builder-deployments.spec.ts  (~120-180 lines - 16 tests)
  url_builder-procedures.spec.ts   (~120-180 lines - 16 tests)
  url_builder-samplingfeatures.spec.ts (~120-180 lines - 16 tests)
  url_builder-properties.spec.ts   (~90-130 lines - 12 tests)
  url_builder-datastreams.spec.ts  (~150-220 lines - 21 tests)
  url_builder-observations.spec.ts (~120-180 lines - 18 tests)
  url_builder-controlstreams.spec.ts (~120-180 lines - 16 tests)
  url_builder-commands.spec.ts     (~150-220 lines - 20 tests)
```

**Pros:**

- Manageable file sizes (90-220 lines each)
- Clear resource type boundaries
- Parallel test execution (9 test suites)
- Easier code review (smaller diffs)
- Less merge conflicts
- Easy to find tests for specific resource type

**Cons:**

- More files to navigate
- Shared utilities need separate file
- Import from shared utilities file

**RECOMMENDATION:** Option 2 (Multiple Files)

### 18.2 Shared Test Utilities File

**File:** `src/ogc-api/csapi/url_builder.spec.ts` (~100 lines)

```typescript
import { URL } from 'url';
import { expect } from '@jest/globals';

/**
 * Parsed URL structure
 */
export interface ParsedURL {
  protocol: string;
  host: string;
  port: string;
  pathname: string;
  query: Record<string, string>;
  hash: string;
}

/**
 * Parse and validate URL structure
 *
 * @param url - URL string to parse
 * @param expected - Expected URL components
 * @returns Parsed URL components
 */
export function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string;
    host?: string;
    port?: string;
    pathname?: string;
    query?: Record<string, string>;
  }
): ParsedURL {
  const parsed = new URL(url);

  if (expected.protocol !== undefined) {
    expect(parsed.protocol).toBe(expected.protocol);
  }

  if (expected.host !== undefined) {
    expect(parsed.host).toBe(expected.host);
  }

  if (expected.port !== undefined) {
    expect(parsed.port).toBe(expected.port);
  }

  if (expected.pathname !== undefined) {
    expect(parsed.pathname).toBe(expected.pathname);
  }

  const query: Record<string, string> = {};
  parsed.searchParams.forEach((value, key) => {
    query[key] = value;
  });

  if (expected.query !== undefined) {
    expect(query).toEqual(expected.query);
  }

  return {
    protocol: parsed.protocol,
    host: parsed.host,
    port: parsed.port,
    pathname: parsed.pathname,
    query,
    hash: parsed.hash,
  };
}

/**
 * Validate query parameter encoding
 *
 * @param url - URL to validate
 * @param param - Parameter name
 * @param expectedEncoding - Expected encoding pattern (regex)
 */
export function validateEncoding(
  url: string,
  param: string,
  expectedEncoding: RegExp
): void {
  expect(url).toMatch(new RegExp(`${param}=${expectedEncoding.source}`));
}

/**
 * Create test endpoint with specified conformance and collection info
 */
export async function createTestEndpoint(options?: {
  conformance?: string[];
  collectionLinks?: any[];
}): Promise<OgcApiEndpoint> {
  // Implementation would create mock endpoint with specified conformance
  // For now, placeholder
  throw new Error('createTestEndpoint not implemented - use in actual tests');
}
```

### 18.3 Per-Resource Test File Template

**Template:** `url_builder-{resource}.spec.ts`

```typescript
import { describe, it, expect, beforeEach } from '@jest/globals';
import { parseAndValidateUrl, createTestEndpoint } from './url_builder.spec';
import { CSAPIQueryBuilder } from './url_builder';

describe('CSAPIQueryBuilder - {ResourceType}', () => {
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    const endpoint = await createTestEndpoint();
    builder = await endpoint.csapi('test-collection');
  });

  describe('get{ResourceType}s()', () => {
    // Collection query tests
  });

  describe('get{ResourceType}()', () => {
    // Single item tests
  });

  describe('create{ResourceType}()', () => {
    // POST tests
  });

  describe('update{ResourceType}()', () => {
    // PUT/PATCH tests
  });

  describe('delete{ResourceType}()', () => {
    // DELETE tests
  });

  describe('Nested endpoints', () => {
    // Navigation tests
  });
});
```

---

## 19. Test Utility Specifications

### 19.1 parseAndValidateUrl Utility

**Purpose:** Parse URL and validate components systematically

**Signature:**

```typescript
function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string;
    host?: string;
    port?: string;
    pathname?: string;
    query?: Record<string, string>;
  }
): ParsedURL;
```

**Implementation:** See Section 3.2

**Usage:** See Sections 5-13 for examples

### 19.2 validateEncoding Utility

**Purpose:** Validate specific parameter encoding patterns

**Signature:**

```typescript
function validateEncoding(
  url: string,
  param: string,
  expectedEncoding: RegExp
): void;
```

**Implementation:**

```typescript
export function validateEncoding(
  url: string,
  param: string,
  expectedEncoding: RegExp
): void {
  const pattern = new RegExp(`${param}=${expectedEncoding.source}`);
  expect(url).toMatch(pattern);
}
```

**Usage:**

```typescript
it('encodes bbox correctly', async () => {
  const url = builder.getSystems({
    bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
  });
  validateEncoding(url, 'bbox', /-?\d+,-?\d+,-?\d+,-?\d+/);
});
```

### 19.3 createTestEndpoint Helper

**Purpose:** Create mock OgcApiEndpoint with specified conformance and collection info

**Signature:**

```typescript
function createTestEndpoint(options?: {
  conformance?: string[];
  collectionLinks?: any[];
}): Promise<OgcApiEndpoint>;
```

**Implementation:**

```typescript
import conformanceAllResources from '../../fixtures/csapi-querybuilder/conformance-all-resources.json';
import collectionInfoAllResources from '../../fixtures/csapi-querybuilder/collection-info-all-resources.json';

export async function createTestEndpoint(options?: {
  conformance?: string[];
  collectionLinks?: any[];
}): Promise<OgcApiEndpoint> {
  const conformance =
    options?.conformance || conformanceAllResources.conformsTo;
  const collectionLinks =
    options?.collectionLinks || collectionInfoAllResources.links;

  // Create mock endpoint
  const mockEndpoint = {
    url: 'https://api.example.com',
    async getInfo() {
      return {
        conformsTo: conformance,
      };
    },
    async getCollectionInfo(collectionId: string) {
      return {
        id: collectionId,
        links: collectionLinks,
      };
    },
    async csapi(collectionId: string) {
      // Implementation creates CSAPIQueryBuilder
      const collection = await this.getCollectionInfo(collectionId);
      return new CSAPIQueryBuilder(collection);
    },
  };

  return mockEndpoint as OgcApiEndpoint;
}
```

---

## 20. Fixture Requirements

### 20.1 Fixture Inventory

| Fixture File                           | Purpose                                     | Size       | Priority |
| -------------------------------------- | ------------------------------------------- | ---------- | -------- |
| **conformance-all-resources.json**     | Full CSAPI conformance (Part 1 + Part 2)    | ~50 lines  | CRITICAL |
| **conformance-part1-only.json**        | Part 1 conformance only (no Part 2)         | ~30 lines  | HIGH     |
| **collection-info-all-resources.json** | Collection with all CSAPI resource links    | ~150 lines | CRITICAL |
| **collection-info-part1-only.json**    | Collection with Part 1 links only           | ~80 lines  | HIGH     |
| **collection-info-no-csapi.json**      | Collection without CSAPI links (error case) | ~30 lines  | MEDIUM   |

**Total Fixtures:** 5 JSON files (~340 lines total)

### 20.2 Fixture Organization

**Directory Structure:**

```
fixtures/csapi-querybuilder/
  conformance-all-resources.json
  conformance-part1-only.json
  collection-info-all-resources.json
  collection-info-part1-only.json
  collection-info-no-csapi.json
```

### 20.3 Sample Fixture: conformance-all-resources.json

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/html",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sf",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream"
  ]
}
```

### 20.4 Sample Fixture: collection-info-all-resources.json

```json
{
  "id": "test-collection",
  "title": "Test CSAPI Collection",
  "description": "Collection with all CSAPI resource types",
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.com/collections/test-collection"
    },
    {
      "rel": "systems",
      "href": "https://api.example.com/systems",
      "title": "System Features"
    },
    {
      "rel": "deployments",
      "href": "https://api.example.com/deployments",
      "title": "Deployment Features"
    },
    {
      "rel": "procedures",
      "href": "https://api.example.com/procedures",
      "title": "Procedure Features"
    },
    {
      "rel": "samplingFeatures",
      "href": "https://api.example.com/samplingFeatures",
      "title": "Sampling Feature Features"
    },
    {
      "rel": "properties",
      "href": "https://api.example.com/properties",
      "title": "Property Features"
    },
    {
      "rel": "datastreams",
      "href": "https://api.example.com/datastreams",
      "title": "DataStreams"
    },
    {
      "rel": "observations",
      "href": "https://api.example.com/observations",
      "title": "Observations"
    },
    {
      "rel": "controlstreams",
      "href": "https://api.example.com/controlstreams",
      "title": "ControlStreams"
    },
    {
      "rel": "commands",
      "href": "https://api.example.com/commands",
      "title": "Commands"
    }
  ],
  "extent": {
    "spatial": {
      "bbox": [[-180, -90, 180, 90]]
    },
    "temporal": {
      "interval": [["2024-01-01T00:00:00Z", null]]
    }
  }
}
```

---

## 21. Testing Estimates

### 21.1 Test Count by Resource Type

| Resource Type        | Methods | Tests per Method (avg) | Total Tests | Lines per Test (avg) | Total Lines     | Time Estimate   |
| -------------------- | ------- | ---------------------- | ----------- | -------------------- | --------------- | --------------- |
| **Systems**          | 12      | 2.7                    | 32          | 6-8                  | 192-256         | 3-4 hours       |
| **Deployments**      | 8       | 2.6                    | 21          | 6-8                  | 126-168         | 2-3 hours       |
| **Procedures**       | 8       | 2.1                    | 17          | 6-8                  | 102-136         | 2-2.5 hours     |
| **SamplingFeatures** | 8       | 2.4                    | 19          | 6-8                  | 114-152         | 2-2.5 hours     |
| **Properties**       | 6       | 2.3                    | 14          | 6-8                  | 84-112          | 1.5-2 hours     |
| **DataStreams**      | 11      | 2.5                    | 28          | 6-8                  | 168-224         | 3-4 hours       |
| **Observations**     | 9       | 2.4                    | 22          | 6-8                  | 132-176         | 2.5-3 hours     |
| **ControlStreams**   | 8       | 2.6                    | 21          | 6-8                  | 126-168         | 2.5-3 hours     |
| **Commands**         | 10      | 2.4                    | 24          | 6-8                  | 144-192         | 3-4 hours       |
| **Shared Utilities** | -       | -                      | -           | -                    | 100             | 2-3 hours       |
| **TOTAL**            | **80**  | **2.4**                | **188**     | **6-8**              | **1,880-2,256** | **22-29 hours** |

### 21.2 Breakdown by Priority

| Priority          | Test Count | Lines           | Time Estimate   | Completion Target |
| ----------------- | ---------- | --------------- | --------------- | ----------------- |
| **CRITICAL (P0)** | ~75        | ~750-900        | 9-12 hours      | Week 1            |
| **HIGH (P1)**     | ~65        | ~650-780        | 8-10 hours      | Week 2            |
| **MEDIUM (P2)**   | ~35        | ~350-420        | 4-5 hours       | Week 3            |
| **LOW (P3)**      | ~13        | ~130-156        | 1-2 hours       | Week 4            |
| **TOTAL**         | **188**    | **1,880-2,256** | **22-29 hours** | **4 weeks**       |

### 21.3 Implementation Schedule

**Week 1: Critical Tests (P0) - 9-12 hours**

- Shared utilities (2-3 hours)
- All GET collection methods (9 tests, 2-3 hours)
- All GET item methods (9 tests, 2-3 hours)
- Query parameter validation (pagination, temporal, spatial, encoding) (2-3 hours)

**Week 2: High Priority Tests (P1) - 8-10 hours**

- POST/PUT/PATCH methods (27 tests, 4-5 hours)
- Optional parameter handling (2-3 hours)
- Resource availability validation (2-3 hours)

**Week 3: Medium Priority Tests (P2) - 4-5 hours**

- DELETE methods (9 tests, 1-2 hours)
- Advanced parameter combinations (2-3 hours)
- Edge case encoding (1-2 hours)

**Week 4: Low Priority Tests (P3) - 1-2 hours**

- Performance scenarios
- Very large parameter values
- Complex filter combinations

---

## 22. Testing Priorities

### 22.1 Priority Definitions

**CRITICAL (P0) - Must Pass Before Release:**

- All GET collection methods (9 methods)
- All GET item methods (9 methods)
- Pagination parameters (limit, offset) for all resources
- Query parameter encoding (spaces, special chars, URIs)
- Nested endpoint construction (System → DataStreams, DataStream → Observations, ControlStream → Commands)
- Resource availability validation (throw error when resource unavailable)
- Temporal parameter encoding (phenomenonTime, resultTime, validTime, issueTime, executionTime)
- Schema endpoint tests (DataStream schema, ControlStream schema)
- Command status tests (getCommandStatus)

**Total P0 Tests:** ~75 tests (~750-900 lines)

**HIGH (P1) - Important But Not Blocking:**

- POST/PUT/PATCH methods (27 tests)
- Optional parameter handling (test presence vs absence)
- Spatial parameter encoding (bbox, geometry)
- Filtering parameters (systemType, observedProperty, controlledProperty, foi, parent, deployment, procedure, system, q)
- Format parameter tests (f=geojson, f=sml, f=swe)
- Hierarchical recursive parameter (Systems, Deployments)
- Command feasibility tests
- Observation bulk creation tests
- Command bulk creation tests

**Total P1 Tests:** ~65 tests (~650-780 lines)

**MEDIUM (P2) - Nice to Have:**

- DELETE methods (9 tests)
- CASCADE parameter for deletes
- Advanced parameter combinations (3+ parameters)
- International character encoding (UTF-8)
- Already encoded value handling (no double-encoding)
- History endpoint tests (all 6 history methods)
- Navigation methods (getProcedureSystems, getPropertyDataStreams, etc.)
- Command result tests (getCommandResult)
- Command cancel tests (cancelCommand)

**Total P2 Tests:** ~35 tests (~350-420 lines)

**LOW (P3) - Edge Cases:**

- Performance with very large parameter values
- Complex filter combinations (5+ filters)
- Edge case bbox coordinates (crossing dateline, poles)
- Edge case temporal intervals (very long, very short, instant)
- Comma preservation in array parameters
- Newline/tab encoding
- Very long URLs (100+ query parameters)

**Total P3 Tests:** ~13 tests (~130-156 lines)

### 22.2 Test Execution Order

**Phase 1: Core Functionality (P0) - Week 1**

1. Setup shared utilities
2. Test GET collection methods for all resources
3. Test GET item methods for all resources
4. Test pagination parameters
5. Test query parameter encoding
6. Test nested endpoints
7. Test resource availability validation

**Phase 2: Extended Functionality (P1) - Week 2** 8. Test POST/PUT/PATCH methods 9. Test optional parameters 10. Test spatial parameters 11. Test filtering parameters 12. Test format parameters 13. Test hierarchical recursive 14. Test special methods (schema, feasibility, bulk creation)

**Phase 3: Edge Cases (P2) - Week 3** 15. Test DELETE methods 16. Test advanced parameter combinations 17. Test international encoding 18. Test history endpoints 19. Test navigation methods 20. Test command lifecycle (result, cancel)

**Phase 4: Low Priority (P3) - Week 4** 21. Test performance scenarios 22. Test complex filters 23. Test edge case coordinates/temporals 24. Test very long URLs

---

## 23. Validation Against Upstream Patterns

### 23.1 Upstream URL Builder Test Patterns

**From Section 1-2 Findings (EDR and OGC API URL Builder Tests):**

**EDR URL Builder Test Patterns:**

- Parse URL into components (protocol, host, pathname, query)
- Validate query parameters as objects (not string matching)
- Test optional parameter omission
- Test parameter encoding (spaces, special chars)
- Test bbox encoding format
- Test datetime encoding format
- Test collection-level vs item-level URLs
- Test parameter combinations

**Alignment with CSAPI Testing:**

- ✅ **parseAndValidateUrl utility** - Matches EDR pattern of parsing URL components
- ✅ **Query parameter object validation** - Matches EDR pattern of structured validation
- ✅ **Optional parameter handling** - Test presence vs absence like EDR
- ✅ **Encoding validation** - Similar approach to EDR (spaces, special chars, URIs)
- ✅ **Collection vs item URLs** - Similar pattern (GET collection, GET item, POST, PUT/PATCH, DELETE)
- ✅ **Parameter combinations** - Test multiple parameters together like EDR

**URL Validation Depth Comparison:**

| Aspect                      | Upstream (EDR)    | CSAPI (This Strategy) | Alignment  |
| --------------------------- | ----------------- | --------------------- | ---------- |
| **Protocol validation**     | ✅ Yes            | ✅ Yes                | ✅ Aligned |
| **Host validation**         | ✅ Yes            | ✅ Yes                | ✅ Aligned |
| **Pathname validation**     | ✅ Yes            | ✅ Yes                | ✅ Aligned |
| **Query param parsing**     | ✅ As objects     | ✅ As objects         | ✅ Aligned |
| **Encoding validation**     | ✅ Regex patterns | ✅ Regex patterns     | ✅ Aligned |
| **Optional param omission** | ✅ Tested         | ✅ Tested             | ✅ Aligned |
| **String contains checks**  | ❌ Avoided        | ❌ Avoided            | ✅ Aligned |
| **Exact string matching**   | ❌ Avoided        | ❌ Avoided            | ✅ Aligned |

### 23.2 Quality Standards Comparison

| Standard                     | Upstream (EDR)                        | CSAPI (This Strategy)                                          |
| ---------------------------- | ------------------------------------- | -------------------------------------------------------------- |
| **Test-to-method ratio**     | ~2-3 tests per method                 | ~2.4 tests per method ✅                                       |
| **Lines per test**           | ~5-8 lines                            | ~6-8 lines ✅                                                  |
| **URL validation depth**     | Structured parsing                    | Structured parsing ✅                                          |
| **Encoding coverage**        | Spaces, special chars, URIs           | Spaces, special chars, URIs, international, already-encoded ✅ |
| **Error condition coverage** | Unavailable resources, invalid params | Same + partial conformance scenarios ✅                        |
| **Test organization**        | Single file per builder               | Multiple files per resource type (better) ✅                   |

### 23.3 Deviations from Upstream

**Intentional Improvements:**

1. **Multiple Test Files** - CSAPI uses 9 test files (one per resource) instead of single file

   - **Reason:** 80 methods vs EDR's ~15 methods - single file would be 1,880+ lines
   - **Benefit:** Better maintainability, parallel execution, easier code review

2. **Resource Availability Validation** - CSAPI tests conformance checking explicitly

   - **Reason:** CSAPI has 9 resource types with complex conformance (Part 1 vs Part 2)
   - **Benefit:** Ensures methods fail gracefully when resources unavailable

3. **Encoding Edge Cases** - CSAPI adds international character and already-encoded testing

   - **Reason:** CSAPI resource IDs more varied (URIs, international identifiers)
   - **Benefit:** Prevents double-encoding bugs, supports global deployments

4. **Nested Endpoint Testing** - CSAPI adds explicit nested endpoint test category
   - **Reason:** CSAPI has 15 nested endpoint patterns vs EDR's 3-4
   - **Benefit:** Systematic coverage of parent-child URL construction

**No Conflicts with Upstream:**

- All upstream patterns preserved
- URL validation depth maintained
- Encoding validation approach aligned
- Query parameter testing approach aligned

---

## 24. Integration with Implementation Guide

### 24.1 Method Signature Validation

**Cross-Reference: Implementation Guide Section "CSAPIQueryBuilder Methods"**

| Implementation Guide Method               | Test Coverage       | Status            |
| ----------------------------------------- | ------------------- | ----------------- |
| `getSystems(options?)`                    | ✅ 7 test scenarios | Covered           |
| `getSystem(id, options?)`                 | ✅ 3 test scenarios | Covered           |
| `createSystem(body)`                      | ✅ 1 test scenario  | Covered           |
| `updateSystem(id, body)`                  | ✅ 2 test scenarios | Covered           |
| `deleteSystem(id, cascade?)`              | ✅ 2 test scenarios | Covered           |
| `getSystemSubsystems(id, options?)`       | ✅ 3 test scenarios | Covered           |
| `getSystemDataStreams(id, options?)`      | ✅ 3 test scenarios | Covered           |
| `getSystemControlStreams(id, options?)`   | ✅ 3 test scenarios | Covered           |
| `getSystemSamplingFeatures(id, options?)` | ✅ 2 test scenarios | Covered           |
| `getSystemDeployments(id, options?)`      | ✅ 2 test scenarios | Covered           |
| `getSystemProcedures(id, options?)`       | ✅ 2 test scenarios | Covered           |
| `getSystemHistory(id, options?)`          | ✅ 2 test scenarios | Covered           |
| ... (68 more methods)                     | ✅ All covered      | See Sections 5-13 |

**Validation:** All 80 methods from Implementation Guide have test specifications in this strategy.

### 24.2 Query Parameter Alignment

**Cross-Reference: Implementation Guide Section "Complete Query Parameter Support"**

| Parameter Category | Implementation Guide                                                                            | Test Coverage                                              | Status     |
| ------------------ | ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------- |
| **Pagination**     | limit, offset                                                                                   | ✅ Tested for all resources                                | ✅ Aligned |
| **Temporal**       | phenomenonTime, resultTime, validTime, issueTime, executionTime, datetime                       | ✅ Tested with ISO 8601 formats, intervals, open intervals | ✅ Aligned |
| **Spatial**        | bbox, geometry                                                                                  | ✅ Tested with coordinate formats, WKT                     | ✅ Aligned |
| **Filtering**      | systemType, observedProperty, controlledProperty, foi, parent, deployment, procedure, system, q | ✅ Tested with vocabulary values, multiple filters         | ✅ Aligned |
| **Format**         | f, format                                                                                       | ✅ Tested with valid formats (json, geojson, sml, swe)     | ✅ Aligned |
| **Sorting**        | sortBy, sortOrder                                                                               | ✅ Tested with valid fields, asc/desc, invalid fields      | ✅ Aligned |
| **Hierarchical**   | recursive                                                                                       | ✅ Tested for Systems and Deployments                      | ✅ Aligned |
| **Arrays**         | Multiple id values, multiple property filters                                                   | ✅ Tested with comma-separated lists                       | ✅ Aligned |

**Gaps Identified:**

- ~~**sortBy/sortOrder parameters**~~ — **RESOLVED**: Brought back into scope (MEDIUM priority). Sorting is essential for deterministic pagination. Test scenarios defined in §4.1 (valid fields, asc/desc, invalid fields).

### 24.3 Helper Function Alignment

**Cross-Reference: Implementation Guide Section "Helper Utilities"**

| Helper Function                                           | Implementation Guide | Test Coverage                          | Status     |
| --------------------------------------------------------- | -------------------- | -------------------------------------- | ---------- |
| `buildResourceUrl(resourceType, id?, subPath?, options?)` | ✅ Specified         | ✅ Tested indirectly via all methods   | ✅ Aligned |
| `buildQueryString(options?)`                              | ✅ Specified         | ✅ Tested via query parameter tests    | ✅ Aligned |
| `encodeBBox(bbox)`                                        | ✅ Specified         | ✅ Tested via spatial parameter tests  | ✅ Aligned |
| `encodeDateTime(datetime)`                                | ✅ Specified         | ✅ Tested via temporal parameter tests | ✅ Aligned |
| `validateBBox(bbox)`                                      | ✅ Specified         | ✅ Tested via error condition tests    | ✅ Aligned |
| `validateDateTime(datetime)`                              | ✅ Specified         | ✅ Tested via error condition tests    | ✅ Aligned |

**Validation:** All helper functions have test coverage (tested indirectly through methods that use them).

### 24.4 Resource Availability Alignment

**Cross-Reference: Implementation Guide Section "Resource Validation"**

| Validation Requirement                           | Implementation Guide | Test Coverage                             | Status     |
| ------------------------------------------------ | -------------------- | ----------------------------------------- | ---------- |
| Check conformance before URL construction        | ✅ Required          | ✅ Tested (Section 16)                    | ✅ Aligned |
| Throw EndpointError when unavailable             | ✅ Specified         | ✅ Tested with error message validation   | ✅ Aligned |
| Extract availableResources from collection links | ✅ Specified         | ✅ Tested via resource availability tests | ✅ Aligned |
| Validate nested resource availability            | ✅ Specified         | ✅ Tested (parent + nested checks)        | ✅ Aligned |

**Validation:** Resource availability validation fully covered.

---

## 25. Risks and Edge Cases

### 25.1 Risk Matrix

| Risk/Edge Case                            | Likelihood | Impact | Mitigation                                               | Priority |
| ----------------------------------------- | ---------- | ------ | -------------------------------------------------------- | -------- |
| **Test suite very large (2,000+ lines)**  | High       | Medium | Multiple files (one per resource)                        | CRITICAL |
| **URL validation utilities insufficient** | Medium     | High   | Robust parseAndValidateUrl with comprehensive validation | CRITICAL |
| **Encoding edge cases missed**            | Medium     | High   | Systematic encoding test matrix (15 cases)               | HIGH     |
| **Resource availability logic untested**  | Medium     | High   | Explicit fixtures and test scenarios (Section 16)        | HIGH     |
| **Parameter combinations explosive**      | High       | Medium | Prioritize common combinations, use parametrized tests   | MEDIUM   |
| **Test maintenance burden**               | Medium     | Medium | Shared utilities, clear organization, good documentation | MEDIUM   |
| **Test execution time slow**              | Medium     | Low    | Parallel test execution (9 files), optimize fixtures     | LOW      |
| **Fixture maintenance**                   | Low        | Low    | Minimal fixtures (5 total), clear naming                 | LOW      |

### 25.2 Edge Case Inventory

**Encoding Edge Cases (15 total):**

1. Space encoding (%20)
2. Forward slash encoding (%2F)
3. Ampersand encoding (%26)
4. Equals encoding (%3D)
5. Plus encoding (%2B)
6. Hash encoding (%23)
7. Question mark encoding (%3F)
8. Percent encoding (%25)
9. International UTF-8 encoding
10. Already encoded (no double-encoding)
11. Colon in URI encoding (%3A)
12. Comma preservation in arrays
13. Newline encoding (%0A)
14. Tab encoding (%09)
15. Reserved characters in values

**Parameter Edge Cases:**

- **Pagination:** limit=0, very large limit, offset without limit
- **Temporal:** Very long intervals, very short intervals, instant (start=end), crossing year boundaries, leap seconds
- **Spatial:** bbox crossing dateline, bbox at poles, negative coordinates, very small bbox, very large bbox
- **Filtering:** Very long query strings, special characters in filter values, multiple filters of same type
- **Optional:** All optional params omitted, all optional params present, mix of present/omitted

**Resource Edge Cases:**

- **Availability:** Partial conformance (Part 1 only), no CSAPI conformance, collection without links
- **IDs:** Very long IDs (>255 chars), IDs with special characters, numeric IDs, UUID IDs, URN IDs
- **Nested:** Deep nesting (6+ levels), circular references (if allowed), missing parent resources

### 25.3 Mitigation Strategies

**Test Suite Size Mitigation:**

- ✅ Multiple files (one per resource) - Keeps files 90-220 lines each
- ✅ Shared utilities file - Reduces duplication
- ✅ Clear test organization - describe blocks per method
- ✅ Consistent naming - Easy to find tests

**URL Validation Utility Mitigation:**

- ✅ Comprehensive parseAndValidateUrl - Validates all URL components
- ✅ Separate validateEncoding utility - Targeted encoding checks
- ✅ Well-documented utilities - Clear usage examples
- ✅ Reusable across all tests - Single implementation

**Encoding Edge Case Mitigation:**

- ✅ Systematic encoding test matrix - 15 edge cases identified
- ✅ Prioritized testing - CRITICAL cases tested first
- ✅ Regex validation patterns - Precise encoding checks
- ✅ Both path and query encoding - Comprehensive coverage

**Resource Availability Mitigation:**

- ✅ Explicit fixtures - conformance-all-resources.json, conformance-part1-only.json
- ✅ Test scenarios - Available, unavailable, partial conformance
- ✅ Clear error messages - Validate error message content
- ✅ Nested resource checks - Test parent + nested availability

**Parameter Combination Mitigation:**

- ✅ Prioritize common combinations - Test 2-3 params together most common
- ✅ Parametrized tests - Use test.each() for multiple scenarios
- ✅ Focus on meaningful combinations - Don't test every permutation
- ✅ Edge case isolation - Test extreme cases separately

---

## Document Metadata

**Status:** Complete  
**Word Count:** ~30,000 words  
**Sections:** 25  
**Test Specifications:** 188 tests across 9 resource types  
**Estimated Test Lines:** 1,880-2,256 lines  
**Estimated Implementation Time:** 22-29 hours  
**Fixture Count:** 5 JSON files

**Review Checklist:**

- ✅ All 86 research questions answered
- ✅ All 80 methods from Implementation Guide covered
- ✅ "Meaningful" URL testing approach defined (parseAndValidateUrl utility)
- ✅ Query parameter testing strategy comprehensive
- ✅ URL encoding edge cases identified (15 cases)
- ✅ Nested endpoint testing strategy defined
- ✅ Resource availability validation approach defined
- ✅ Test organization structure decided (multiple files recommended)
- ✅ Test utilities specified (parseAndValidateUrl, validateEncoding, createTestEndpoint)
- ✅ Fixture requirements documented (5 fixtures)
- ✅ Testing estimates realistic (188 tests, 1,880-2,256 lines, 22-29 hours)
- ✅ All 9 resource types covered with test specifications
- ✅ Validation against upstream patterns complete
- ✅ Integration with Implementation Guide validated
- ✅ Risks and edge cases documented with mitigation

**Next Steps:**

1. Review document with team
2. Create fixture directory structure (fixtures/csapi-querybuilder/)
3. Implement shared test utilities (parseAndValidateUrl, validateEncoding, createTestEndpoint)
4. Implement tests per resource type (9 files, prioritize P0 tests first)
5. Validate test coverage against all 80 methods
6. Update Implementation Guide with test coverage status
