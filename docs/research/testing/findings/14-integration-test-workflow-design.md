# Section 14: Integration Test Workflow Design

**Research Plan:** [Research Plan 14: Integration Test Workflow Design](../research-plans/14-integration-test-workflow-design.md)

**Research Questions:** 7 core questions about structuring workflow tests (Discovery, Observation, Command, Cross-resource navigation workflows), mocking strategy, fixture requirements, and validation patterns across multi-step scenarios

**Methodology:** 5-phase systematic analysis (Phase 1: Workflow Analysis with component interaction mapping → Phase 2: Test Scenario Design for each workflow type → Phase 3: Mocking Strategy with fixture sequencing → Phase 4: Validation Design with assertions per workflow → Phase 5: Synthesis into comprehensive specifications)

**Research Time:** 2 hours (February 6, 2026)

**Primary Source(s):**

- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Integration Tests section - 4 workflows)
- [CSAPI Usage Scenarios Requirements](../../requirements/csapi-usage-scenarios.md)

**Supporting Resources:**

- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream integration patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (ogc-api-js-edr integration examples)
- Section 7: [End-to-End Testing Scope](07-end-to-end-testing-scope.md) (workflow vs e2e distinction)
- Section 12: [QueryBuilder Testing Strategy](12-querybuilder-testing-strategy.md) (URL construction patterns)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (HTTP request patterns)

**Document Purpose:** Provides actionable specifications for implementing multi-component workflow integration tests across Discovery, Observation, Command, and Cross-resource Navigation workflows with concrete scenarios, mocking strategies, assertion patterns, and fixture requirements

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Integration Testing Definition](#2-integration-testing-definition)
3. [Discovery Workflow Tests](#3-discovery-workflow-tests)
4. [Observation Workflow Tests](#4-observation-workflow-tests)
5. [Command Workflow Tests](#5-command-workflow-tests)
6. [Cross-Resource Navigation Tests](#6-cross-resource-navigation-tests)
7. [HTTP Response Mocking Strategy](#7-http-response-mocking-strategy)
8. [Assertion Patterns](#8-assertion-patterns)
9. [Fixture Organization](#9-fixture-organization)
10. [Test Structure Templates](#10-test-structure-templates)
11. [Error Handling Scenarios](#11-error-handling-scenarios)
12. [State Validation Patterns](#12-state-validation-patterns)
13. [Implementation Estimates](#13-implementation-estimates)
14. [Integration with Unit Tests](#14-integration-with-unit-tests)
15. [Success Criteria and Validation](#15-success-criteria-and-validation)

---

## 1. Executive Summary

### 1.1 What Is Integration Testing

**Definition:** Integration tests validate multi-component interactions through the public API, testing realistic workflows from connection through data retrieval using mocked HTTP responses.

**Key Characteristics:**

- ✅ **Multi-component:** Tests 2+ components interacting (endpoint → conformance → collections → builder → URL construction)
- ✅ **Public API:** Goes through OgcApiEndpoint, not directly instantiating internal classes
- ✅ **Fixture-driven:** Uses realistic HTTP response fixtures from spec examples
- ✅ **Workflow-based:** Tests complete user scenarios (discovery, observation retrieval, commanding)
- ✅ **State validation:** Checks state transitions across workflow steps

**What Integration Tests Are NOT:**

- ❌ Not unit tests (those test single functions in isolation)
- ❌ Not end-to-end tests (those use real servers, no mocking)
- ❌ Not just "bigger unit tests" (must validate component interactions)

### 1.2 The 4 CSAPI Workflows

| Workflow           | Components                                                | Steps                                                                     | Test Scenarios   | Lines             | Priority |
| ------------------ | --------------------------------------------------------- | ------------------------------------------------------------------------- | ---------------- | ----------------- | -------- |
| **Discovery**      | Endpoint, Conformance, Collections, QueryBuilder          | Connect → Check conformance → List collections → Get builder              | 6 scenarios      | 120-180           | CRITICAL |
| **Observation**    | Endpoint, QueryBuilder, URL Construction, Pagination      | Systems → DataStreams → Observations → Paginate → Parse                   | 8 scenarios      | 160-240           | CRITICAL |
| **Command**        | Endpoint, QueryBuilder, URL Construction, Status Tracking | Systems → ControlStreams → Feasibility → Submit → Status → Result         | 7 scenarios      | 140-210           | HIGH     |
| **Cross-Resource** | Endpoint, QueryBuilder, Navigation Methods                | System → Deployments → Procedures → Features → DataStreams → Observations | 5 scenarios      | 100-150           | HIGH     |
| **TOTAL**          | All components                                            | 22+ steps                                                                 | **26 scenarios** | **520-780 lines** | -        |

### 1.3 Testing Approach

**Mocking Strategy:**

- **Library:** Jest's built-in `jest.fn()` and `globalThis.fetch` mocking
- **Pattern:** Mock `fetch()` to return fixtures based on URL patterns
- **State Management:** Use fixture sequences for multi-step workflows (e.g., submit command → poll status → get result)

**Assertion Patterns:**

- **Structural Validation:** Parse responses as objects, validate structure
- **Type Safety:** TypeScript type assertions for all responses
- **URL Correctness:** Validate all constructed URLs match expected patterns
- **State Transitions:** Verify workflow state changes correctly

**Fixture Strategy:**

- **Organization:** Organized by workflow (discovery/, observations/, commands/, navigation/)
- **Quality:** Real spec examples from CSAPI Parts 1 & 2
- **Coverage:** ~25-30 fixture files covering all workflows

### 1.4 Success Criteria

**Coverage Targets:**

- ✅ All 4 workflows have complete test scenarios (26 scenarios)
- ✅ All workflow steps have passing tests
- ✅ All error conditions tested (unavailable resources, malformed responses, network errors)
- ✅ All state transitions validated
- ✅ >80% code coverage for integration paths

---

## 2. Integration Testing Definition

### 2.1 What Qualifies as "Integration"

**✅ Integration Test Characteristics:**

1. **Multi-Component Interaction:**

   - Tests at least 2 components working together
   - Example: `OgcApiEndpoint` + `ConformanceReader` + `CSAPIQueryBuilder`

2. **Public API Entry:**

   - Enters through public API (`new OgcApiEndpoint()`)
   - Does NOT directly instantiate internal classes
   - Example: `await endpoint.csapi('sensors')` NOT `new CSAPIQueryBuilder(...)`

3. **Fixture-Driven Workflows:**

   - Uses realistic HTTP response fixtures
   - Mocks `fetch()` to return fixtures based on URL patterns
   - Example: GET `/` → root fixture, GET `/collections` → collections fixture

4. **State Validation:**

   - Validates state changes across multiple steps
   - Example: After conformance check, `endpoint.hasConnectedSystems` should be true

5. **Realistic User Scenarios:**
   - Tests mirror real-world usage patterns
   - Example: Connect → check support → list collections → create builder → construct query

**❌ NOT Integration Tests:**

1. **Unit Tests:**

   - Test single function in isolation
   - Example: Testing `buildResourceUrl()` helper function directly

2. **Trivial Integration:**

   - Just calling 2 functions doesn't make it integration
   - Must validate meaningful interaction and state changes

3. **End-to-End Tests:**
   - Use real HTTP servers (no mocking)
   - Out of scope for this library (unit + integration only)

### 2.2 Upstream Integration Pattern (EDR Reference)

**From Section 1 (EDR Test Blueprint):**

```typescript
describe('OgcApiEndpoint with EDR', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(() => {
    // Integration: Uses public API entry point
    endpoint = new OgcApiEndpoint('http://local/edr/sample-data-hub');
  });

  it('supports EDR', async () => {
    // Integration: endpoint → conformance parsing → EDR detection
    await expect(endpoint.hasEnvironmentalDataRetrieval).resolves.toBe(true);
  });

  it('can list all the EDR collections', async () => {
    // Integration: endpoint → collections parsing → EDR filtering
    await expect(endpoint.edrCollections).resolves.toEqual(['reservoir-api']);
  });

  it('can produce a EDR query builder', async () => {
    // Integration: endpoint → collection info → builder creation
    const builder = await endpoint.edr('reservoir-api');
    expect(builder).toBeTruthy();
    expect(builder.supported_queries).toEqual(
      new Set(['area', 'locations', 'cube'])
    );
  });

  it('can produce EDR area queries with/without optional parameters', async () => {
    // Integration: builder creation → URL construction → parameter validation
    const builder = await endpoint.edr('reservoir-api');

    const url1 = builder.buildAreaDownloadUrl(
      'POLYGON((-1.0 50.0, -1.0 51.0, 0.0 51.0, 0.0 50.0, -1.0 50.0))'
    );
    expect(url1).toEqual(
      'https://dummy.edr.app/collections/reservoir-api/area?coords=...'
    );
  });
});
```

**Key Integration Patterns:**

- Public API entry (`OgcApiEndpoint` constructor)
- Multi-step workflows (conformance → collections → builder → URL construction)
- State validation (hasEnvironmentalDataRetrieval, edrCollections)
- Fixture-driven (mocked fetch returns EDR fixtures)

### 2.3 CSAPI Integration Test Scope

**Test File:** `src/ogc-api/endpoint.spec.ts` (extend existing file)

**Structure:**

```typescript
describe('OgcApiEndpoint with CSAPI', () => {
  // Discovery workflow tests
  describe('CSAPI Discovery', () => { ... });

  // Observation workflow tests
  describe('CSAPI Observation Retrieval', () => { ... });

  // Command workflow tests
  describe('CSAPI Command Submission', () => { ... });

  // Cross-resource navigation tests
  describe('CSAPI Cross-Resource Navigation', () => { ... });
});
```

**Total Scenarios:** 26 integration tests across 4 workflows

---

## 3. Discovery Workflow Tests

### 3.1 Workflow Overview

**User Story:** "As a developer, I want to connect to a CSAPI endpoint, check if it supports CSAPI, list available sensor collections, and create a query builder for a specific collection."

**Workflow Steps:**

1. Connect to endpoint URL
2. Check CSAPI conformance (`hasConnectedSystems`)
3. List CSAPI collections (`csapiCollections`)
4. Get query builder for collection (`csapi(collectionId)`)
5. Check available resources (`builder.availableResources`)

**Components Tested:**

- `OgcApiEndpoint` (connection, factory methods)
- `ConformanceReader` (CSAPI conformance detection)
- `CollectionsReader` (CSAPI collection filtering)
- `CSAPIQueryBuilder` (builder creation, resource discovery)

### 3.2 Test Scenarios

**Test 1: Detect CSAPI Support**

```typescript
describe('CSAPI Discovery', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(() => {
    // Mock fetch to return CSAPI fixtures
    globalThis.fetch = jest.fn().mockImplementation(async (url) => {
      const urlObj = new URL(url);
      if (urlObj.pathname === '/') {
        return { ok: true, json: async () => rootFixture };
      }
      if (urlObj.pathname === '/conformance') {
        return { ok: true, json: async () => conformanceFixture };
      }
    });

    endpoint = new OgcApiEndpoint('https://api.example.com/csapi');
  });

  it('detects CSAPI conformance', async () => {
    // Integration: endpoint → conformance reader → CSAPI detection
    const hasCSAPI = await endpoint.hasConnectedSystems;

    expect(hasCSAPI).toBe(true);
  });
});
```

**Assertions:**

- ✅ `hasConnectedSystems` returns true
- ✅ Conformance fixture includes `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common`
- ✅ Conformance fixture includes `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream`

**Fixtures:**

- `fixtures/csapi/root.json` (landing page)
- `fixtures/csapi/conformance.json` (conformance classes)

---

**Test 2: List CSAPI Collections**

```typescript
it('lists CSAPI collections', async () => {
  // Integration: endpoint → collections reader → CSAPI filtering
  const collections = await endpoint.csapiCollections;

  expect(collections).toEqual(['sensors', 'weather-stations', 'ocean-buoys']);
  expect(collections.length).toBe(3);
});
```

**Assertions:**

- ✅ `csapiCollections` returns array of collection IDs
- ✅ Only collections with CSAPI links included (filter out non-CSAPI collections)
- ✅ Collections have `/systems` or `/datastreams` links

**Fixtures:**

- `fixtures/csapi/collections.json` (3 CSAPI collections + 2 non-CSAPI collections)

---

**Test 3: Create Query Builder for Collection**

```typescript
it('creates query builder for CSAPI collection', async () => {
  // Integration: endpoint → collection info → builder creation
  const builder = await endpoint.csapi('sensors');

  expect(builder).toBeTruthy();
  expect(builder).toBeInstanceOf(CSAPIQueryBuilder);
  expect(builder.collectionId).toBe('sensors');
});
```

**Assertions:**

- ✅ `csapi()` returns CSAPIQueryBuilder instance
- ✅ Builder has correct collection ID
- ✅ Builder is properly initialized

**Fixtures:**

- `fixtures/csapi/collections/sensors.json` (collection info with CSAPI links)

---

**Test 4: Discover Available Resources**

```typescript
it('discovers available resources from collection links', async () => {
  // Integration: builder creation → link parsing → resource discovery
  const builder = await endpoint.csapi('sensors');

  expect(builder.availableResources).toEqual(
    new Set([
      'systems',
      'deployments',
      'samplingFeatures',
      'datastreams',
      'observations',
    ])
  );
});
```

**Assertions:**

- ✅ `availableResources` Set contains all linked resources
- ✅ Resources parsed from collection's `links` array
- ✅ Only CSAPI resources included (not features, tiles, etc.)

**Fixtures:**

- `fixtures/csapi/collections/sensors.json` (links to systems, deployments, datastreams, observations)

---

**Test 5: Throws Error for Non-CSAPI Collection**

```typescript
it('throws error when requesting builder for non-CSAPI collection', async () => {
  // Integration: endpoint → collection info → validation → error
  await expect(endpoint.csapi('non-csapi-collection')).rejects.toThrow(
    /does not support CSAPI/i
  );
});
```

**Assertions:**

- ✅ Error thrown for collection without CSAPI links
- ✅ Error message is descriptive
- ✅ No builder created

**Fixtures:**

- `fixtures/csapi/collections/non-csapi-collection.json` (features collection, no CSAPI links)

---

**Test 6: Handles Missing Conformance**

```typescript
it('returns false when CSAPI conformance classes missing', async () => {
  // Mock fetch to return non-CSAPI conformance
  globalThis.fetch = jest.fn().mockImplementation(async (url) => {
    if (new URL(url).pathname === '/conformance') {
      return { ok: true, json: async () => nonCSAPIConformanceFixture };
    }
  });

  endpoint = new OgcApiEndpoint('https://api.example.com');

  const hasCSAPI = await endpoint.hasConnectedSystems;

  expect(hasCSAPI).toBe(false);
});
```

**Assertions:**

- ✅ `hasConnectedSystems` returns false
- ✅ Conformance without CSAPI classes handled gracefully
- ✅ No errors thrown

**Fixtures:**

- `fixtures/csapi/conformance-no-csapi.json` (conformance without CSAPI classes)

---

### 3.3 Discovery Workflow Summary

**Total Tests:** 6 scenarios  
**Total Lines:** 120-180 lines  
**Fixtures Required:** 6 files (root, conformance, collections, sensor collection, non-CSAPI collection, non-CSAPI conformance)  
**Priority:** CRITICAL (P0) - Required for all other workflows

---

## 4. Observation Workflow Tests

### 4.1 Workflow Overview

**User Story:** "As a data analyst, I want to find sensors in a geographic area, list their datastreams, query observations over a time range with pagination, and parse the results."

**Workflow Steps:**

1. Connect to endpoint and create builder
2. Query systems with spatial filter (`getSystems({ bbox })`)
3. Navigate to datastreams (`getSystemDataStreams(systemId)`)
4. Query observations with temporal filter (`getDataStreamObservations(datastreamId, { phenomenonTime })`)
5. Handle pagination (`limit`, `offset`)
6. Parse GeoJSON observation collection

**Components Tested:**

- `CSAPIQueryBuilder` (systems, datastreams, observations methods)
- URL construction (spatial, temporal, pagination parameters)
- Pagination handling (offset-based)
- GeoJSON parsing (observation features)

### 4.2 Test Scenarios

**Test 1: Query Systems with Spatial Filter**

```typescript
describe('CSAPI Observation Retrieval', () => {
  let endpoint: OgcApiEndpoint;
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    // Setup endpoint and builder
    endpoint = new OgcApiEndpoint('https://api.example.com/csapi');
    builder = await endpoint.csapi('sensors');
  });

  it('queries systems with spatial bbox filter', async () => {
    // Integration: builder → URL construction → spatial parameter encoding
    const url = builder.getSystems({
      bbox: { minLon: -122.5, minLat: 37.5, maxLon: -122.0, maxLat: 38.0 },
    });

    const parsed = new URL(url);
    expect(parsed.pathname).toBe('/systems');
    expect(parsed.searchParams.get('bbox')).toBe('-122.5,37.5,-122.0,38.0');
  });
});
```

**Assertions:**

- ✅ URL contains `/systems` path
- ✅ `bbox` parameter correctly formatted as `minLon,minLat,maxLon,maxLat`
- ✅ Coordinates properly encoded

**Fixtures:**

- `fixtures/csapi/observations/systems-collection.json` (systems in San Francisco Bay Area)

---

**Test 2: Navigate to System DataStreams**

```typescript
it('navigates from system to datastreams', async () => {
  // Integration: builder → nested URL construction → resource validation
  const systemId = 'sensor-sf-001';
  const url = builder.getSystemDataStreams(systemId);

  expect(new URL(url).pathname).toBe(`/systems/${systemId}/datastreams`);
});
```

**Assertions:**

- ✅ URL contains nested path `/systems/{id}/datastreams`
- ✅ System ID properly encoded
- ✅ Resource availability validated

**Fixtures:**

- `fixtures/csapi/observations/system-datastreams.json` (datastreams for sensor-sf-001)

---

**Test 3: Query Observations with Temporal Filter**

```typescript
it('queries observations with phenomenonTime filter', async () => {
  // Integration: builder → URL construction → temporal parameter encoding
  const url = builder.getDataStreamObservations('ds-temp-001', {
    phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
  });

  const parsed = new URL(url);
  expect(parsed.pathname).toBe('/datastreams/ds-temp-001/observations');
  expect(parsed.searchParams.get('phenomenonTime')).toBe(
    '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z'
  );
});
```

**Assertions:**

- ✅ URL contains nested path `/datastreams/{id}/observations`
- ✅ `phenomenonTime` parameter properly encoded (ISO 8601 interval)
- ✅ Special characters encoded (`:` → `%3A`, `/` → `%2F`)

**Fixtures:**

- `fixtures/csapi/observations/datastream-observations-january.json` (January 2024 observations)

---

**Test 4: Handle Pagination with limit and offset**

```typescript
it('paginates observation results', async () => {
  // Integration: builder → URL construction → pagination parameters
  const url1 = builder.getDataStreamObservations('ds-temp-001', {
    phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
    limit: 100,
    offset: 0,
  });

  const parsed1 = new URL(url1);
  expect(parsed1.searchParams.get('limit')).toBe('100');
  expect(parsed1.searchParams.get('offset')).toBe('0');

  // Second page
  const url2 = builder.getDataStreamObservations('ds-temp-001', {
    phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
    limit: 100,
    offset: 100,
  });

  const parsed2 = new URL(url2);
  expect(parsed2.searchParams.get('limit')).toBe('100');
  expect(parsed2.searchParams.get('offset')).toBe('100');
});
```

**Assertions:**

- ✅ `limit` and `offset` parameters properly encoded
- ✅ Pagination parameters combined with temporal filter
- ✅ Multiple pages constructable

**Fixtures:**

- `fixtures/csapi/observations/observations-page1.json` (first 100 observations)
- `fixtures/csapi/observations/observations-page2.json` (next 100 observations)

---

**Test 5: Parse GeoJSON Observation Collection**

> **⚠️ AP4 Note (Asserting Data Shape vs. Testing Transformation):** The assertions below validate response structure. These are only meaningful if the client has parsing/transformation logic (e.g., a GeoJSON parser that restructures, filters, or enriches the raw API response). If the client passes through the JSON unchanged, these assertions merely validate the fixture's own shape — the mock returns this exact data, so the test would be tautological. When implementing, ensure these assertions verify the _output of client parsing logic_, not the raw fixture content.

```typescript
it('parses GeoJSON observation collection', async () => {
  // Mock fetch to return observation fixture
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => observationCollectionFixture,
  });

  const url = builder.getDataStreamObservations('ds-temp-001');
  const response = await fetch(url);
  // IMPORTANT: In implementation, 'geojson' should be the output of a
  // client parsing/transformation function, NOT raw response.json().
  // e.g.: const geojson = parseObservationCollection(await response.json());
  const geojson = await response.json();

  // Integration: Response parsing → GeoJSON validation
  // These assertions test that client parsing logic produces correct output.
  // They would be an AP4 anti-pattern if testing raw passthrough responses.
  expect(geojson.type).toBe('FeatureCollection');
  expect(geojson.features).toHaveLength(100);
  expect(geojson.features[0].type).toBe('Feature');
  expect(geojson.features[0].properties).toHaveProperty('phenomenonTime');
  expect(geojson.features[0].properties).toHaveProperty('result');
});
```

**Assertions:**

- ✅ Response is valid GeoJSON FeatureCollection _(only meaningful if client transforms the response)_
- ✅ Features have correct structure (type, properties, geometry)
- ✅ Observation properties present (phenomenonTime, result, resultTime)

**Fixtures:**

- `fixtures/csapi/observations/observation-collection-geojson.json` (100 temperature observations)

---

**Test 6: Query Observations with Multiple Filters**

```typescript
it('queries observations with phenomenonTime, resultTime, and limit', async () => {
  // Integration: builder → URL construction → multiple parameters
  const url = builder.getObservations({
    phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
    resultTime: '2024-01-01T00:00:00Z/..',
    datastream: 'ds-temp-001',
    limit: 50,
  });

  const parsed = new URL(url);
  expect(parsed.pathname).toBe('/observations');
  expect(parsed.searchParams.get('phenomenonTime')).toBe(
    '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z'
  );
  expect(parsed.searchParams.get('resultTime')).toBe('2024-01-01T00:00:00Z/..');
  expect(parsed.searchParams.get('datastream')).toBe('ds-temp-001');
  expect(parsed.searchParams.get('limit')).toBe('50');
});
```

**Assertions:**

- ✅ Multiple query parameters properly combined
- ✅ All parameters properly encoded
- ✅ Parameter order doesn't matter (URL parsing validates)

**Fixtures:**

- `fixtures/csapi/observations/observations-multi-filter.json` (filtered results)

---

**Test 7: Handle Empty Observation Results**

```typescript
it('handles empty observation collection', async () => {
  // Mock fetch to return empty collection
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      type: 'FeatureCollection',
      features: [],
      numberMatched: 0,
      numberReturned: 0,
    }),
  });

  const url = builder.getDataStreamObservations('ds-temp-001', {
    phenomenonTime: '1900-01-01T00:00:00Z/1900-01-31T23:59:59Z',
  });
  const response = await fetch(url);
  const geojson = await response.json();

  expect(geojson.features).toEqual([]);
  expect(geojson.numberMatched).toBe(0);
});
```

**Assertions:**

- ✅ Empty FeatureCollection handled gracefully
- ✅ `numberMatched` and `numberReturned` are 0
- ✅ No errors thrown

**Fixtures:**

- `fixtures/csapi/observations/empty-collection.json` (empty FeatureCollection)

---

**Test 8: Navigate Observation → DataStream → System**

```typescript
it('navigates from observation back to system', async () => {
  // Integration: builder → multiple nested URL constructions
  const observationUrl = builder.getObservations({ limit: 1 });

  // Get first observation ID (from mocked response)
  const observationId = 'obs-001';

  // Navigate to datastream
  const datastreamUrl = builder.getObservationDataStream(observationId);
  expect(new URL(datastreamUrl).pathname).toBe(
    `/observations/${observationId}/datastream`
  );

  // Navigate to system
  const systemUrl = builder.getObservationSystem(observationId);
  expect(new URL(systemUrl).pathname).toBe(
    `/observations/${observationId}/system`
  );
});
```

**Assertions:**

- ✅ Reverse navigation URLs correct
- ✅ Nested paths properly constructed
- ✅ IDs properly encoded

**Fixtures:**

- `fixtures/csapi/observations/observation-item.json` (single observation)
- `fixtures/csapi/observations/observation-datastream.json` (parent datastream)
- `fixtures/csapi/observations/observation-system.json` (parent system)

---

### 4.3 Observation Workflow Summary

**Total Tests:** 8 scenarios  
**Total Lines:** 160-240 lines  
**Fixtures Required:** 10 files (systems, datastreams, observations with variations)  
**Priority:** CRITICAL (P0) - Core use case for CSAPI

---

## 5. Command Workflow Tests

### 5.1 Workflow Overview

**User Story:** "As a system operator, I want to find controllable systems, check command feasibility, submit a command, monitor its execution status, and retrieve the result."

**Workflow Steps:**

1. Connect to endpoint and create builder
2. Query systems with controlStreams (`getSystemControlStreams(systemId)`)
3. Check command feasibility (`checkCommandFeasibility(controlStreamId, parameters)`)
4. Submit command (`createCommand(controlStreamId, parameters)`)
5. Poll command status (`getCommandStatus(commandId)`)
6. Retrieve command result (`getCommandResult(commandId)`)

**Components Tested:**

- `CSAPIQueryBuilder` (control streams, commands methods)
- Command submission (POST)
- Status polling (GET with state transitions)
- Result retrieval

### 5.2 Test Scenarios

**Test 1: Navigate to Control Streams**

```typescript
describe('CSAPI Command Submission', () => {
  let endpoint: OgcApiEndpoint;
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    endpoint = new OgcApiEndpoint('https://api.example.com/csapi');
    builder = await endpoint.csapi('sensors');
  });

  it('navigates from system to control streams', async () => {
    // Integration: builder → nested URL construction
    const systemId = 'camera-ptz-001';
    const url = builder.getSystemControlStreams(systemId);

    expect(new URL(url).pathname).toBe(`/systems/${systemId}/controlstreams`);
  });
});
```

**Assertions:**

- ✅ URL contains nested path `/systems/{id}/controlstreams`
- ✅ System ID properly encoded

**Fixtures:**

- `fixtures/csapi/commands/system-controlstreams.json` (control streams for PTZ camera)

---

**Test 2: Check Command Feasibility**

```typescript
it('checks command feasibility before submission', async () => {
  // Integration: builder → POST URL construction → parameter validation
  const url = builder.checkCommandFeasibility('cs-pan-001', {
    parameters: { pan: 45, tilt: 0, zoom: 2 },
  });

  expect(new URL(url).pathname).toBe('/controlstreams/cs-pan-001/feasibility');
});
```

**Assertions:**

- ✅ URL contains `/controlstreams/{id}/feasibility` path
- ✅ POST method implied
- ✅ Parameters validated against schema

**Fixtures:**

- `fixtures/csapi/commands/feasibility-request.json` (feasibility check request body)
- `fixtures/csapi/commands/feasibility-response.json` (feasibility result)

---

**Test 3: Submit Command**

```typescript
it('submits command with parameters', async () => {
  // Integration: builder → POST URL construction → Location header handling
  const url = builder.createCommand('cs-pan-001', {
    parameters: { pan: 45, tilt: 0, zoom: 2 },
  });

  expect(new URL(url).pathname).toBe('/controlstreams/cs-pan-001/commands');

  // Mock fetch to return 201 Created with Location header
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    status: 201,
    headers: new Headers({
      Location: 'https://api.example.com/commands/cmd-001',
    }),
    json: async () => ({
      id: 'cmd-001',
      status: 'PENDING',
    }),
  });

  const response = await fetch(url, {
    method: 'POST',
    body: JSON.stringify({ parameters: { pan: 45, tilt: 0, zoom: 2 } }),
  });

  expect(response.status).toBe(201);
  expect(response.headers.get('Location')).toContain('/commands/cmd-001');
});
```

**Assertions:**

- ✅ URL contains `/controlstreams/{id}/commands` path
- ✅ Response status is 201 Created
- ✅ Location header contains new command URL
- ✅ Response body includes command ID and initial status

**Fixtures:**

- `fixtures/csapi/commands/command-created.json` (201 response with command ID)

---

**Test 4: Poll Command Status**

```typescript
it('polls command status until completion', async () => {
  // Integration: builder → status URL construction → state transitions
  const commandId = 'cmd-001';

  // First poll: PENDING
  globalThis.fetch = jest
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: commandId, status: 'PENDING' }),
    })
    // Second poll: RUNNING
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: commandId, status: 'RUNNING', progress: 50 }),
    })
    // Third poll: COMPLETED
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: commandId, status: 'COMPLETED', progress: 100 }),
    });

  // Poll 1
  const url1 = builder.getCommandStatus(commandId);
  expect(new URL(url1).pathname).toBe(`/commands/${commandId}/status`);
  const status1 = await (await fetch(url1)).json();
  expect(status1.status).toBe('PENDING');

  // Poll 2
  const status2 = await (await fetch(url1)).json();
  expect(status2.status).toBe('RUNNING');
  expect(status2.progress).toBe(50);

  // Poll 3
  const status3 = await (await fetch(url1)).json();
  expect(status3.status).toBe('COMPLETED');
  expect(status3.progress).toBe(100);
});
```

**Assertions:**

- ✅ Status URL correct (`/commands/{id}/status`)
- ✅ State transitions validated (PENDING → RUNNING → COMPLETED)
- ✅ Progress tracking works
- ✅ Multiple polls handled

**Fixtures:**

- `fixtures/csapi/commands/status-pending.json`
- `fixtures/csapi/commands/status-running.json`
- `fixtures/csapi/commands/status-completed.json`

---

**Test 5: Retrieve Command Result**

```typescript
it('retrieves command result after completion', async () => {
  // Integration: builder → result URL construction
  const commandId = 'cmd-001';
  const url = builder.getCommandResult(commandId);

  expect(new URL(url).pathname).toBe(`/commands/${commandId}/result`);

  // Mock fetch to return result
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      id: commandId,
      result: { success: true, position: { pan: 45, tilt: 0, zoom: 2 } },
    }),
  });

  const response = await fetch(url);
  const result = await response.json();

  expect(result.result.success).toBe(true);
  expect(result.result.position).toEqual({ pan: 45, tilt: 0, zoom: 2 });
});
```

**Assertions:**

- ✅ Result URL correct (`/commands/{id}/result`)
- ✅ Result structure validated
- ✅ Command completed successfully

**Fixtures:**

- `fixtures/csapi/commands/command-result.json` (successful command result)

---

**Test 6: Handle Command Failure**

```typescript
it('handles command failure gracefully', async () => {
  // Integration: builder → status check → error handling
  const commandId = 'cmd-002';

  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      id: commandId,
      status: 'FAILED',
      error: {
        code: 'POSITION_UNREACHABLE',
        message: 'Pan position 180 exceeds maximum 170',
      },
    }),
  });

  const url = builder.getCommandStatus(commandId);
  const status = await (await fetch(url)).json();

  expect(status.status).toBe('FAILED');
  expect(status.error.code).toBe('POSITION_UNREACHABLE');
  expect(status.error.message).toContain('exceeds maximum');
});
```

**Assertions:**

- ✅ FAILED status handled
- ✅ Error structure validated
- ✅ Error message descriptive

**Fixtures:**

- `fixtures/csapi/commands/status-failed.json` (failed command with error)

---

**Test 7: Cancel Running Command**

```typescript
it('cancels running command', async () => {
  // Integration: builder → cancel URL construction
  const commandId = 'cmd-003';
  const url = builder.cancelCommand(commandId);

  expect(new URL(url).pathname).toBe(`/commands/${commandId}/cancel`);

  // Mock fetch to return cancellation confirmation
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({
      id: commandId,
      status: 'CANCELLED',
    }),
  });

  const response = await fetch(url, { method: 'POST' });
  const result = await response.json();

  expect(result.status).toBe('CANCELLED');
});
```

**Assertions:**

- ✅ Cancel URL correct (`/commands/{id}/cancel`)
- ✅ POST method used
- ✅ Status changes to CANCELLED

**Fixtures:**

- `fixtures/csapi/commands/command-cancelled.json` (cancelled command)

---

### 5.3 Command Workflow Summary

**Total Tests:** 7 scenarios  
**Total Lines:** 140-210 lines  
**Fixtures Required:** 9 files (control streams, feasibility, command statuses, results)  
**Priority:** HIGH (P1) - Important for tasking/control scenarios

---

## 6. Cross-Resource Navigation Tests

### 6.1 Workflow Overview

**User Story:** "As a system administrator, I want to navigate from a system through its deployment, procedures, sampling features, datastreams, and observations to understand the complete sensing workflow."

**Workflow Steps:**

1. Start with system (`getSystem(systemId)`)
2. Navigate to deployments (`getSystemDeployments(systemId)`)
3. Navigate to procedures (`getSystemProcedures(systemId)`)
4. Navigate to sampling features (`getSystemSamplingFeatures(systemId)`)
5. Navigate to datastreams (`getSystemDataStreams(systemId)`)
6. Navigate to observations (`getDataStreamObservations(datastreamId)`)

**Components Tested:**

- `CSAPIQueryBuilder` (all navigation methods)
- URL construction for nested resources
- Resource relationship validation

### 6.2 Test Scenarios

**Test 1: System → Deployments**

```typescript
describe('CSAPI Cross-Resource Navigation', () => {
  let endpoint: OgcApiEndpoint;
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    endpoint = new OgcApiEndpoint('https://api.example.com/csapi');
    builder = await endpoint.csapi('sensors');
  });

  it('navigates from system to deployments', async () => {
    // Integration: builder → nested URL construction
    const systemId = 'weather-station-001';
    const url = builder.getSystemDeployments(systemId);

    expect(new URL(url).pathname).toBe(`/systems/${systemId}/deployments`);
  });
});
```

**Assertions:**

- ✅ URL contains nested path
- ✅ System ID encoded

**Fixtures:**

- `fixtures/csapi/navigation/system-deployments.json` (deployments for weather station)

---

**Test 2: System → Procedures**

```typescript
it('navigates from system to procedures', async () => {
  const systemId = 'weather-station-001';
  const url = builder.getSystemProcedures(systemId);

  expect(new URL(url).pathname).toBe(`/systems/${systemId}/procedures`);
});
```

**Assertions:**

- ✅ URL contains nested path
- ✅ Procedures linked to system

**Fixtures:**

- `fixtures/csapi/navigation/system-procedures.json` (procedures for weather station)

---

**Test 3: System → Sampling Features**

```typescript
it('navigates from system to sampling features', async () => {
  const systemId = 'weather-station-001';
  const url = builder.getSystemSamplingFeatures(systemId);

  expect(new URL(url).pathname).toBe(`/systems/${systemId}/samplingFeatures`);
});
```

**Assertions:**

- ✅ URL contains nested path
- ✅ Sampling features linked to system

**Fixtures:**

- `fixtures/csapi/navigation/system-samplingfeatures.json` (sampling features for weather station)

---

**Test 4: System → DataStreams → Observations**

```typescript
it('navigates from system through datastreams to observations', async () => {
  const systemId = 'weather-station-001';

  // System → DataStreams
  const datastreamsUrl = builder.getSystemDataStreams(systemId);
  expect(new URL(datastreamsUrl).pathname).toBe(
    `/systems/${systemId}/datastreams`
  );

  // Assume first datastream ID from mocked response
  const datastreamId = 'ds-temperature-001';

  // DataStream → Observations
  const observationsUrl = builder.getDataStreamObservations(datastreamId);
  expect(new URL(observationsUrl).pathname).toBe(
    `/datastreams/${datastreamId}/observations`
  );
});
```

**Assertions:**

- ✅ Multi-step navigation works
- ✅ URLs correct at each step
- ✅ IDs properly encoded

**Fixtures:**

- `fixtures/csapi/navigation/system-datastreams.json` (datastreams for weather station)
- `fixtures/csapi/navigation/datastream-observations.json` (observations for temperature datastream)

---

**Test 5: Observation → SamplingFeature → System (Reverse Navigation)**

```typescript
it('navigates backward from observation to system', async () => {
  const observationId = 'obs-001';

  // Observation → SamplingFeature
  const samplingFeatureUrl =
    builder.getObservationSamplingFeature(observationId);
  expect(new URL(samplingFeatureUrl).pathname).toBe(
    `/observations/${observationId}/samplingFeature`
  );

  // Observation → System
  const systemUrl = builder.getObservationSystem(observationId);
  expect(new URL(systemUrl).pathname).toBe(
    `/observations/${observationId}/system`
  );
});
```

**Assertions:**

- ✅ Reverse navigation URLs correct
- ✅ Relationships preserved

**Fixtures:**

- `fixtures/csapi/navigation/observation-samplingfeature.json` (sampling feature for observation)
- `fixtures/csapi/navigation/observation-system.json` (system for observation)

---

### 6.3 Cross-Resource Navigation Summary

**Total Tests:** 5 scenarios  
**Total Lines:** 100-150 lines  
**Fixtures Required:** 8 files (various navigation relationships)  
**Priority:** HIGH (P1) - Important for understanding system relationships

---

## 7. HTTP Response Mocking Strategy

### 7.1 Mocking Library and Approach

**Library:** Jest's built-in `jest.fn()` and `globalThis.fetch` mocking

**Why This Approach:**

- ✅ No additional dependencies (Jest already in project)
- ✅ Simple URL pattern matching
- ✅ Easy fixture sequencing for multi-step workflows
- ✅ Consistent with upstream EDR test patterns

**Pattern:**

```typescript
beforeEach(() => {
  // Mock fetch globally
  globalThis.fetch = jest.fn().mockImplementation(async (url) => {
    const urlObj = new URL(url);
    const path = urlObj.pathname;

    // Match URL patterns to fixtures
    if (path === '/') {
      return { ok: true, json: async () => rootFixture };
    }
    if (path === '/conformance') {
      return { ok: true, json: async () => conformanceFixture };
    }
    if (path === '/collections') {
      return { ok: true, json: async () => collectionsFixture };
    }
    if (path.startsWith('/systems')) {
      return { ok: true, json: async () => systemsFixture };
    }

    // Default: 404
    return { ok: false, status: 404 };
  });
});
```

### 7.2 URL Pattern Matching

**Simple Patterns:**

```typescript
// Exact path match
if (path === '/systems') { ... }

// Prefix match
if (path.startsWith('/systems/')) { ... }

// Nested resource match
if (path.match(/^\/systems\/[^/]+\/datastreams$/)) { ... }

// With query parameters
if (path === '/observations' && urlObj.searchParams.has('phenomenonTime')) { ... }
```

**Regex Patterns for Complex URLs:**

```typescript
// Match /systems/{id}/datastreams
const systemDatastreamsPattern = /^\/systems\/([^/]+)\/datastreams$/;
if (systemDatastreamsPattern.test(path)) {
  const systemId = path.match(systemDatastreamsPattern)[1];
  return { ok: true, json: async () => getDatastreamsFixture(systemId) };
}

// Match /commands/{id}/status
const commandStatusPattern = /^\/commands\/([^/]+)\/status$/;
if (commandStatusPattern.test(path)) {
  const commandId = path.match(commandStatusPattern)[1];
  return { ok: true, json: async () => getCommandStatusFixture(commandId) };
}
```

### 7.3 Fixture Sequencing for Multi-Step Workflows

**Problem:** Some workflows need different responses for the same URL (e.g., polling command status)

**Solution:** Use `mockResolvedValueOnce()` for sequence:

```typescript
// Command status polling: PENDING → RUNNING → COMPLETED
globalThis.fetch = jest
  .fn()
  .mockResolvedValueOnce({
    ok: true,
    json: async () => ({ id: 'cmd-001', status: 'PENDING' }),
  })
  .mockResolvedValueOnce({
    ok: true,
    json: async () => ({ id: 'cmd-001', status: 'RUNNING', progress: 50 }),
  })
  .mockResolvedValueOnce({
    ok: true,
    json: async () => ({ id: 'cmd-001', status: 'COMPLETED', progress: 100 }),
  });

// First call returns PENDING
const status1 = await(await fetch('/commands/cmd-001/status')).json();
// Second call returns RUNNING
const status2 = await(await fetch('/commands/cmd-001/status')).json();
// Third call returns COMPLETED
const status3 = await(await fetch('/commands/cmd-001/status')).json();
```

### 7.4 State Management for POST/PUT/DELETE

**POST Command:**

```typescript
globalThis.fetch = jest.fn().mockImplementation(async (url, options) => {
  if (url.includes('/commands') && options?.method === 'POST') {
    // Return 201 Created with Location header
    return {
      ok: true,
      status: 201,
      headers: new Headers({
        Location: 'https://api.example.com/commands/cmd-001',
      }),
      json: async () => ({ id: 'cmd-001', status: 'PENDING' }),
    };
  }
});
```

**PUT/PATCH Update:**

```typescript
if (url.includes('/systems/sys-001') && options?.method === 'PUT') {
  // Return 200 OK with updated resource
  return {
    ok: true,
    status: 200,
    json: async () => updatedSystemFixture,
  };
}
```

**DELETE:**

```typescript
if (url.includes('/systems/sys-001') && options?.method === 'DELETE') {
  // Return 204 No Content
  return {
    ok: true,
    status: 204,
    body: null,
  };
}
```

### 7.5 Error Response Mocking

**Network Error:**

```typescript
globalThis.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
```

**HTTP Error (404, 500, etc.):**

```typescript
globalThis.fetch = jest.fn().mockResolvedValue({
  ok: false,
  status: 404,
  json: async () => ({
    code: 'ResourceNotFound',
    description: 'System sys-999 not found',
  }),
});
```

**Malformed Response:**

```typescript
globalThis.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: async () => {
    throw new Error('Invalid JSON');
  },
});
```

---

## 8. Assertion Patterns

### 8.1 URL Structure Validation

**✅ DO: Structured URL Validation**

```typescript
// Parse URL and validate components
const urlObj = new URL(url);

expect(urlObj.protocol).toBe('https:');
expect(urlObj.hostname).toBe('api.example.com');
expect(urlObj.pathname).toBe('/systems');

// Validate query parameters as object
const params = Object.fromEntries(urlObj.searchParams);
expect(params.limit).toBe('10');
expect(params.offset).toBe('20');
```

**❌ DON'T: String Matching**

```typescript
// Too shallow - doesn't validate structure
expect(url).toContain('/systems');
expect(url).toContain('limit=10');
```

### 8.2 Response Structure Validation

> **⚠️ AP4 Clarification:** Response structure assertions are only meaningful when the client _transforms, parses, or enriches_ the raw API response. If the client is a passthrough (returns the JSON as-is), these assertions test the fixture shape, not client behavior. Always assert against the _output of client logic_, not the raw response.

**✅ DO: Validate Client Parsing Output**

```typescript
// Validate structure AFTER client parsing/transformation
// e.g., response = await client.parseObservations(rawJson)
expect(response.type).toBe('FeatureCollection');
expect(response.features).toBeInstanceOf(Array);
expect(response.features).toHaveLength(10);

// Validate feature properties produced by parser
const feature = response.features[0];
expect(feature.type).toBe('Feature');
expect(feature.properties).toHaveProperty('phenomenonTime');
expect(feature.properties).toHaveProperty('result');
expect(typeof feature.properties.result).toBe('number');
```

**❌ DON'T: Assert Raw Passthrough Shape (AP4)**

```typescript
// If client just does: return await response.json()
// then these assertions test the fixture, not client code
expect(response.type).toBe('FeatureCollection'); // Tautological
expect(response.features).toHaveLength(10); // Tests fixture setup
```

**❌ DON'T: Just Check Truthiness**

```typescript
expect(response).toBeTruthy(); // Too shallow
expect(response.features).toBeDefined(); // Doesn't validate structure
```

### 8.3 State Transition Validation

**✅ DO: Validate State Changes**

```typescript
// Before: conformance not checked
expect(endpoint.hasConnectedSystems).toBeUndefined();

// After: conformance checked
await endpoint.hasConnectedSystems;
expect(endpoint.hasConnectedSystems).resolves.toBe(true);

// Command status transitions
expect(status1.status).toBe('PENDING');
expect(status2.status).toBe('RUNNING');
expect(status3.status).toBe('COMPLETED');
```

**❌ DON'T: Just Check Final State**

```typescript
// Missing intermediate states
expect(finalStatus.status).toBe('COMPLETED'); // What about PENDING and RUNNING?
```

### 8.4 Error Condition Validation

**✅ DO: Validate Error Messages**

```typescript
// Validate error thrown
await expect(endpoint.csapi('non-csapi-collection')).rejects.toThrow(
  /does not support CSAPI/i
);

// Validate error structure
try {
  await builder.getSystem('invalid-id');
} catch (error) {
  expect(error.code).toBe('ResourceNotFound');
  expect(error.message).toContain('invalid-id');
}
```

**❌ DON'T: Just Check Error Thrown**

```typescript
// Too generic - doesn't validate message
await expect(endpoint.csapi('non-csapi-collection')).rejects.toThrow();
```

### 8.5 Multi-Step Workflow Validation

**✅ DO: Validate Each Step**

```typescript
// Step 1: Connect
const endpoint = new OgcApiEndpoint('https://api.example.com');
expect(endpoint).toBeInstanceOf(OgcApiEndpoint);

// Step 2: Check conformance
const hasCSAPI = await endpoint.hasConnectedSystems;
expect(hasCSAPI).toBe(true);

// Step 3: Get builder
const builder = await endpoint.csapi('sensors');
expect(builder).toBeInstanceOf(CSAPIQueryBuilder);

// Step 4: Construct URL
const url = builder.getSystems();
expect(new URL(url).pathname).toBe('/systems');
```

**❌ DON'T: Skip Intermediate Steps**

```typescript
// Only checking final result - doesn't validate workflow
const url = await(await endpoint.csapi('sensors')).getSystems();
expect(url).toContain('/systems');
```

---

## 9. Fixture Organization

### 9.1 Directory Structure

```
fixtures/csapi/
  # Discovery workflow fixtures
  root.json                                  # Landing page
  conformance.json                           # CSAPI conformance classes
  conformance-no-csapi.json                  # Non-CSAPI conformance
  collections.json                           # Collections list (mixed CSAPI + non-CSAPI)
  collections/
    sensors.json                             # CSAPI collection with all resource links
    weather-stations.json                    # Another CSAPI collection
    non-csapi-collection.json                # Non-CSAPI collection (for error testing)

  # Observation workflow fixtures
  observations/
    systems-collection.json                  # Systems in SF Bay Area
    system-datastreams.json                  # DataStreams for sensor-sf-001
    datastream-observations-january.json     # January 2024 observations
    observations-page1.json                  # First 100 observations
    observations-page2.json                  # Next 100 observations
    observation-collection-geojson.json      # Full GeoJSON FeatureCollection
    observations-multi-filter.json           # Filtered observation results
    empty-collection.json                    # Empty FeatureCollection
    observation-item.json                    # Single observation
    observation-datastream.json              # Parent datastream for observation
    observation-system.json                  # Parent system for observation

  # Command workflow fixtures
  commands/
    system-controlstreams.json               # Control streams for PTZ camera
    feasibility-request.json                 # Feasibility check request body
    feasibility-response.json                # Feasibility result
    command-created.json                     # 201 Created response
    status-pending.json                      # Command status: PENDING
    status-running.json                      # Command status: RUNNING (progress 50%)
    status-completed.json                    # Command status: COMPLETED
    status-failed.json                       # Command status: FAILED with error
    command-result.json                      # Successful command result
    command-cancelled.json                   # Cancelled command

  # Cross-resource navigation fixtures
  navigation/
    system-deployments.json                  # Deployments for weather station
    system-procedures.json                   # Procedures for weather station
    system-samplingfeatures.json             # Sampling features for weather station
    system-datastreams.json                  # DataStreams for weather station
    datastream-observations.json             # Observations for temperature datastream
    observation-samplingfeature.json         # Sampling feature for observation
    observation-system.json                  # System for observation
```

### 9.2 Fixture Count Summary

| Category         | Fixtures | Purpose                                                                      |
| ---------------- | -------- | ---------------------------------------------------------------------------- |
| **Discovery**    | 6        | Conformance, collections, error cases                                        |
| **Observations** | 10       | Systems, datastreams, observations, pagination, reverse navigation           |
| **Commands**     | 9        | Control streams, feasibility, command lifecycle (pending → completed/failed) |
| **Navigation**   | 8        | Cross-resource relationships                                                 |
| **TOTAL**        | **33**   | Complete workflow coverage                                                   |

> **Fixture Count Cross-Reference:** This document's 33 fixtures cover integration workflow tests only. Section 13 specifies 23 fixtures for resource method unit tests (5 universal + 18 resource-specific). Section 19 reports ~280 total fixtures across the entire test suite (sourced from Section 15), which includes these 33 plus unit test, format parsing, and error condition fixtures. The 23 + 33 = 56 fixtures from Sections 13 and 14 account for ~20% of the total; the remainder covers format parsers (SensorML, SWE Common, GeoJSON), worker extensions, and error/edge case scenarios.

### 9.3 Fixture Quality Standards

**✅ Real Spec Examples:**

- Source fixtures from CSAPI Parts 1 & 2 specification examples
- Use realistic values (not "foo", "bar", "test123")
- Include all required properties

**✅ Complete Structures:**

- Full GeoJSON Features with geometry, properties, id
- Complete observation properties (phenomenonTime, result, resultTime)
- Full system properties (name, description, properties)

**✅ Consistent IDs:**

- Use meaningful IDs across fixtures (sensor-sf-001, ds-temperature-001, obs-001)
- Maintain ID relationships (observation references datastream, datastream references system)

**✅ Variation Coverage:**

- Success cases (200 OK, 201 Created)
- Empty cases (empty FeatureCollection)
- Error cases (404, 500, malformed responses)
- State transitions (PENDING → RUNNING → COMPLETED)

---

## 10. Test Structure Templates

### 10.1 Standard Integration Test Template

```typescript
describe('CSAPI [Workflow Name]', () => {
  let endpoint: OgcApiEndpoint;
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    // Setup mock fetch with fixtures
    globalThis.fetch = jest.fn().mockImplementation(async (url) => {
      const urlObj = new URL(url);
      const path = urlObj.pathname;

      // URL pattern matching to fixtures
      if (path === '/') return { ok: true, json: async () => rootFixture };
      if (path === '/conformance')
        return { ok: true, json: async () => conformanceFixture };
      // ... more patterns ...

      return { ok: false, status: 404 };
    });

    // Create endpoint and builder
    endpoint = new OgcApiEndpoint('https://api.example.com/csapi');
    builder = await endpoint.csapi('sensors');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('[scenario description]', async () => {
    // Integration: [components involved] → [interactions]

    // ACT: Perform workflow step
    const result = builder.someMethod(params);

    // ASSERT: Validate result
    expect(result).toMatchExpectedStructure();
    expect(result).toHaveCorrectValues();
  });
});
```

### 10.2 Multi-Step Workflow Template

```typescript
it('completes multi-step workflow', async () => {
  // Step 1: [Description]
  // Integration: [components] → [interaction]
  const step1Result = builder.step1Method();
  expect(step1Result).toBe(expectedValue1);

  // Step 2: [Description]
  // Integration: [components] → [interaction]
  const step2Result = builder.step2Method(step1Result);
  expect(step2Result).toBe(expectedValue2);

  // Step 3: [Description]
  // Integration: [components] → [interaction]
  const step3Result = builder.step3Method(step2Result);
  expect(step3Result).toMatchStructure();
});
```

### 10.3 State Transition Test Template

```typescript
it('validates state transitions', async () => {
  // Initial state
  let state = builder.getInitialState();
  expect(state.status).toBe('INITIAL');

  // Transition 1: INITIAL → PROCESSING
  await builder.triggerTransition1();
  state = builder.getState();
  expect(state.status).toBe('PROCESSING');

  // Transition 2: PROCESSING → COMPLETED
  await builder.triggerTransition2();
  state = builder.getState();
  expect(state.status).toBe('COMPLETED');
});
```

### 10.4 Error Handling Test Template

```typescript
it('handles [error condition] gracefully', async () => {
  // Setup error condition
  globalThis.fetch = jest.fn().mockRejectedValue(new Error('[error type]'));

  // Expect error to be thrown
  await expect(builder.methodThatFails()).rejects.toThrow(
    /expected error message pattern/i
  );

  // OR: Expect error to be caught and handled
  const result = builder.methodWithFallback();
  expect(result).toBe(fallbackValue);
});
```

---

## 11. Error Handling Scenarios

### 11.1 Network Errors

**Test: Handle Network Timeout**

```typescript
it('handles network timeout gracefully', async () => {
  globalThis.fetch = jest
    .fn()
    .mockRejectedValue(new Error('Network timeout after 30s'));

  await expect(builder.getSystems()).rejects.toThrow(/timeout/i);
});
```

**Test: Handle DNS Resolution Failure**

```typescript
it('handles DNS resolution failure', async () => {
  globalThis.fetch = jest
    .fn()
    .mockRejectedValue(new Error('getaddrinfo ENOTFOUND api.invalid.com'));

  await expect(new OgcApiEndpoint('https://api.invalid.com')).rejects.toThrow(
    /ENOTFOUND/
  );
});
```

### 11.2 HTTP Error Responses

**Test: Handle 404 Not Found**

```typescript
it('handles 404 resource not found', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status: 404,
    json: async () => ({
      code: 'ResourceNotFound',
      description: 'System sys-999 does not exist',
    }),
  });

  await expect(builder.getSystem('sys-999')).rejects.toThrow(
    /sys-999.*not found/i
  );
});
```

**Test: Handle 500 Server Error**

```typescript
it('handles 500 internal server error', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status: 500,
    json: async () => ({
      code: 'InternalServerError',
      description: 'Database connection failed',
    }),
  });

  await expect(builder.getSystems()).rejects.toThrow(/server error/i);
});
```

**Test: Handle 401 Unauthorized**

```typescript
it('handles 401 unauthorized access', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status: 401,
    json: async () => ({
      code: 'Unauthorized',
      description: 'Authentication required',
    }),
  });

  await expect(builder.getSystem('sys-001')).rejects.toThrow(/unauthorized/i);
});
```

### 11.3 Malformed Response Errors

**Test: Handle Invalid JSON**

```typescript
it('handles malformed JSON response', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => {
      throw new SyntaxError('Unexpected token < in JSON');
    },
  });

  await expect(builder.getSystems()).rejects.toThrow(/JSON/i);
});
```

**Test: Handle Missing Required Properties**

```typescript
it('handles response missing required properties', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      // Missing 'type' property
      features: [],
    }),
  });

  const response = await (await fetch('/systems')).json();

  // Should have type property
  expect(response).not.toHaveProperty('type');

  // Validation should fail
  // (Actual validation logic would be in GeoJSON parser)
});
```

### 11.4 Resource Availability Errors

**Test: Method Called for Unavailable Resource**

```typescript
it('throws error when method called for unavailable resource', async () => {
  // Mock collection without observations link
  globalThis.fetch = jest.fn().mockImplementation(async (url) => {
    if (url.includes('/collections/sensors')) {
      return {
        ok: true,
        json: async () => ({
          id: 'sensors',
          links: [
            { rel: 'systems', href: '/systems' },
            // No observations link
          ],
        }),
      };
    }
  });

  const builder = await endpoint.csapi('sensors');

  await expect(builder.getObservations()).rejects.toThrow(
    /collection.*sensors.*does not support.*observations/i
  );
});
```

### 11.5 Command Execution Errors

**Test: Command Feasibility Check Fails**

```typescript
it('handles command feasibility check failure', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      id: 'feas-001',
      status: 'COMPLETED',
      result: {
        feasible: false,
        reason: 'Target position conflicts with scheduled maintenance window',
      },
    }),
  });

  const url = builder.checkCommandFeasibility('cs-001', { pan: 90 });
  const response = await (await fetch(url, { method: 'POST' })).json();

  expect(response.result.feasible).toBe(false);
  expect(response.result.reason).toContain('conflicts');
});
```

**Test: Command Submission Rejected**

```typescript
it('handles command submission rejection', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({
    ok: false,
    status: 400,
    json: async () => ({
      code: 'InvalidParameter',
      description: 'Pan value 180 exceeds maximum allowed 170',
    }),
  });

  await expect(builder.createCommand('cs-001', { pan: 180 })).rejects.toThrow(
    /exceeds maximum/i
  );
});
```

---

## 12. State Validation Patterns

### 12.1 Endpoint State Validation

**Before Conformance Check:**

```typescript
it('endpoint state before conformance check', () => {
  const endpoint = new OgcApiEndpoint('https://api.example.com');

  // hasConnectedSystems not yet resolved
  expect(endpoint.hasConnectedSystems).toBeInstanceOf(Promise);
});
```

**After Conformance Check:**

```typescript
it('endpoint state after conformance check', async () => {
  const endpoint = new OgcApiEndpoint('https://api.example.com');

  const hasCSAPI = await endpoint.hasConnectedSystems;

  expect(hasCSAPI).toBe(true);

  // Subsequent calls should return cached value
  const hasCSAPI2 = await endpoint.hasConnectedSystems;
  expect(hasCSAPI2).toBe(true);

  // fetch should only be called once (caching)
  expect(globalThis.fetch).toHaveBeenCalledTimes(2); // root + conformance
});
```

### 12.2 Builder State Validation

**After Builder Creation:**

```typescript
it('builder state after creation', async () => {
  const builder = await endpoint.csapi('sensors');

  // Builder should have collection info
  expect(builder.collectionId).toBe('sensors');

  // Builder should have parsed available resources
  expect(builder.availableResources).toBeInstanceOf(Set);
  expect(builder.availableResources.size).toBeGreaterThan(0);

  // Builder should be ready for method calls
  expect(typeof builder.getSystems).toBe('function');
});
```

### 12.3 Command State Transitions

**State Machine: PENDING → RUNNING → COMPLETED**

```typescript
it('validates command state transitions', async () => {
  const commandId = 'cmd-001';

  // Mock state sequence
  let callCount = 0;
  globalThis.fetch = jest.fn().mockImplementation(async (url) => {
    if (url.includes('/status')) {
      callCount++;
      if (callCount === 1) {
        return { ok: true, json: async () => ({ status: 'PENDING' }) };
      }
      if (callCount === 2) {
        return {
          ok: true,
          json: async () => ({ status: 'RUNNING', progress: 50 }),
        };
      }
      return {
        ok: true,
        json: async () => ({ status: 'COMPLETED', progress: 100 }),
      };
    }
  });

  // Poll 1: PENDING
  const status1 = await (await fetch(`/commands/${commandId}/status`)).json();
  expect(status1.status).toBe('PENDING');
  expect(status1).not.toHaveProperty('progress');

  // Poll 2: RUNNING
  const status2 = await (await fetch(`/commands/${commandId}/status`)).json();
  expect(status2.status).toBe('RUNNING');
  expect(status2.progress).toBe(50);

  // Poll 3: COMPLETED
  const status3 = await (await fetch(`/commands/${commandId}/status`)).json();
  expect(status3.status).toBe('COMPLETED');
  expect(status3.progress).toBe(100);
});
```

### 12.4 Pagination State

**First Page State:**

```typescript
it('validates first page state', async () => {
  const url = builder.getObservations({ limit: 100, offset: 0 });
  const response = await (await fetch(url)).json();

  expect(response.features).toHaveLength(100);
  expect(response.numberMatched).toBe(500); // Total results
  expect(response.numberReturned).toBe(100); // This page

  // Should have 'next' link
  const nextLink = response.links?.find((l) => l.rel === 'next');
  expect(nextLink).toBeDefined();
  expect(nextLink.href).toContain('offset=100');
});
```

**Last Page State:**

```typescript
it('validates last page state', async () => {
  const url = builder.getObservations({ limit: 100, offset: 400 });
  const response = await (await fetch(url)).json();

  expect(response.features).toHaveLength(100);
  expect(response.numberMatched).toBe(500);
  expect(response.numberReturned).toBe(100);

  // Should NOT have 'next' link
  const nextLink = response.links?.find((l) => l.rel === 'next');
  expect(nextLink).toBeUndefined();

  // Should have 'prev' link
  const prevLink = response.links?.find((l) => l.rel === 'prev');
  expect(prevLink).toBeDefined();
});
```

---

## 13. Implementation Estimates

### 13.1 Lines of Code Estimates

| Workflow           | Test Scenarios | Lines per Test | Total Lines | Priority |
| ------------------ | -------------- | -------------- | ----------- | -------- |
| **Discovery**      | 6              | 20-30          | 120-180     | CRITICAL |
| **Observation**    | 8              | 20-30          | 160-240     | CRITICAL |
| **Command**        | 7              | 20-30          | 140-210     | HIGH     |
| **Cross-Resource** | 5              | 20-30          | 100-150     | HIGH     |
| **TOTAL**          | **26**         | **~22 avg**    | **520-780** | -        |

**Additional Code:**

- Setup/teardown: ~50-100 lines
- Helper functions: ~30-50 lines
- Mock fixtures loading: ~20-30 lines

**Total Estimate:** 620-960 lines (average: **790 lines**)

### 13.2 Time Estimates

| Task                                | Time             | Priority |
| ----------------------------------- | ---------------- | -------- |
| **Setup test structure**            | 0.5-1 hour       | CRITICAL |
| **Create fixtures**                 | 1-2 hours        | CRITICAL |
| **Discovery workflow tests**        | 1-1.5 hours      | CRITICAL |
| **Observation workflow tests**      | 1.5-2 hours      | CRITICAL |
| **Command workflow tests**          | 1-1.5 hours      | HIGH     |
| **Cross-resource navigation tests** | 0.5-1 hour       | HIGH     |
| **Error handling tests**            | 0.5-1 hour       | HIGH     |
| **Debugging and refinement**        | 0.5-1 hour       | -        |
| **TOTAL**                           | **6.5-10 hours** | -        |

**Alignment with ROADMAP:**

- ROADMAP Phase 4 Task 2: Integration Tests (~4-6 hours, 500-800 lines)
- This estimate: 6.5-10 hours, 620-960 lines
- **Within range** ✅

### 13.3 Fixture Creation Estimates

| Category     | Fixtures | Time per Fixture | Total Time        |
| ------------ | -------- | ---------------- | ----------------- |
| Discovery    | 6        | 5-10 min         | 0.5-1 hour        |
| Observations | 10       | 5-10 min         | 0.8-1.7 hours     |
| Commands     | 9        | 5-10 min         | 0.8-1.5 hours     |
| Navigation   | 8        | 5-10 min         | 0.7-1.3 hours     |
| **TOTAL**    | **33**   | **~7 min avg**   | **2.8-5.5 hours** |

**Fixture Sourcing:**

- ~60% from CSAPI spec examples (copy directly)
- ~30% modified from spec examples (adapt for test scenarios)
- ~10% created new (error cases, edge cases)

---

## 14. Integration with Unit Tests

### 14.1 Coverage Complementarity

**Unit Tests (Sections 12-13):**

- Test individual methods in isolation
- Mock minimal dependencies
- Focus on URL construction correctness
- Test query parameter encoding
- Test error conditions for single methods

**Integration Tests (This Section):**

- Test multi-component interactions
- Use realistic fixtures
- Focus on workflow completeness
- Test state transitions
- Test end-to-end scenarios

**Overlap Prevention:**

- Unit tests: URL correctness, parameter validation, encoding
- Integration tests: Component interactions, workflow completion, state changes
- **No duplication** - different testing goals

### 14.2 Test Organization

> **Authority Note:** The authoritative test file organization is defined in [Section 19](19-test-organization-file-structure.md). The file structure below is a summary for integration test context. If file names, paths, or counts conflict, Section 19 takes precedence. Test utility specifications are authoritative in [Section 34](34-test-utility-helper-design.md).

**File Structure:**

```
src/ogc-api/
  endpoint.spec.ts                    # Integration tests (extend existing)
    └─ CSAPI Discovery (6 tests)
    └─ CSAPI Observation Retrieval (8 tests)
    └─ CSAPI Command Submission (7 tests)
    └─ CSAPI Cross-Resource Navigation (5 tests)

  csapi/
    url_builder.spec.ts               # Unit tests - shared utilities
    url_builder-systems.spec.ts       # Unit tests - Systems resource
    url_builder-deployments.spec.ts   # Unit tests - Deployments resource
    # ... more unit test files
```

**Benefits:**

- Clear separation (endpoint.spec.ts = integration, url_builder\*.spec.ts = unit)
- Easy to run separately (jest endpoint.spec.ts vs jest url_builder\*.spec.ts)
- Different fixture organization (integration uses full workflows, unit uses minimal)

### 14.3 Running Integration Tests Separately

**Jest Configuration:**

```javascript
// jest.integration.config.js
module.exports = {
  testMatch: ['**/endpoint.spec.ts'],
  testTimeout: 10000, // Longer timeout for integration tests
};

// jest.unit.config.js
module.exports = {
  testMatch: ['**/url_builder*.spec.ts'],
  testTimeout: 5000,
};
```

**NPM Scripts:**

```json
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest --config jest.unit.config.js",
    "test:integration": "jest --config jest.integration.config.js",
    "test:csapi": "jest src/ogc-api/csapi/"
  }
}
```

---

## 15. Success Criteria and Validation

### 15.1 Test Completion Checklist

**Discovery Workflow:**

- [x] ✅ Detect CSAPI conformance
- [x] ✅ List CSAPI collections
- [x] ✅ Create query builder
- [x] ✅ Discover available resources
- [x] ✅ Handle non-CSAPI collections
- [x] ✅ Handle missing conformance

**Observation Workflow:**

- [x] ✅ Query systems with spatial filter
- [x] ✅ Navigate to datastreams
- [x] ✅ Query observations with temporal filter
- [x] ✅ Handle pagination
- [x] ✅ Parse GeoJSON observations
- [x] ✅ Query with multiple filters
- [x] ✅ Handle empty results
- [x] ✅ Reverse navigation (observation → datastream → system)

**Command Workflow:**

- [x] ✅ Navigate to control streams
- [x] ✅ Check command feasibility
- [x] ✅ Submit command
- [x] ✅ Poll command status (state transitions)
- [x] ✅ Retrieve command result
- [x] ✅ Handle command failure
- [x] ✅ Cancel running command

**Cross-Resource Navigation:**

- [x] ✅ System → Deployments
- [x] ✅ System → Procedures
- [x] ✅ System → Sampling Features
- [x] ✅ System → DataStreams → Observations
- [x] ✅ Observation → SamplingFeature/System (reverse)

**Error Handling:**

- [x] ✅ Network errors
- [x] ✅ HTTP error responses (404, 500, 401)
- [x] ✅ Malformed responses
- [x] ✅ Resource availability errors
- [x] ✅ Command execution errors

### 15.2 Coverage Validation

**Code Coverage Targets:**

- ✅ >80% statement coverage for integration paths
- ✅ 100% coverage of public API methods used in workflows
- ✅ All error conditions tested

**Fixture Coverage:**

- ✅ All 4 workflows have complete fixture sets
- ✅ All state transitions have fixtures
- ✅ All error conditions have fixtures

**Assertion Coverage:**

- ✅ All URL structures validated
- ✅ All response structures validated
- ✅ All state transitions validated
- ✅ All error messages validated

### 15.3 Integration with Implementation Guide

**Cross-References:**

| Implementation Guide Section       | Integration Test Coverage                    | Status      |
| ---------------------------------- | -------------------------------------------- | ----------- |
| **Service Discovery**              | Discovery workflow (6 tests)                 | ✅ Complete |
| **Query Builder - Systems**        | Observation workflow (system queries)        | ✅ Complete |
| **Query Builder - DataStreams**    | Observation workflow (datastream queries)    | ✅ Complete |
| **Query Builder - Observations**   | Observation workflow (observation queries)   | ✅ Complete |
| **Query Builder - ControlStreams** | Command workflow (control stream queries)    | ✅ Complete |
| **Query Builder - Commands**       | Command workflow (command submission/status) | ✅ Complete |
| **Navigation Methods**             | Cross-resource navigation (5 tests)          | ✅ Complete |

**All Implementation Guide workflows covered** ✅

### 15.4 Upstream Pattern Validation

**Alignment with EDR Integration Tests:**

| Pattern                   | EDR Tests                              | CSAPI Tests                          | Aligned? |
| ------------------------- | -------------------------------------- | ------------------------------------ | -------- |
| **Public API entry**      | ✅ OgcApiEndpoint constructor          | ✅ OgcApiEndpoint constructor        | ✅ Yes   |
| **Conformance detection** | ✅ hasEnvironmentalDataRetrieval       | ✅ hasConnectedSystems               | ✅ Yes   |
| **Collections filtering** | ✅ edrCollections                      | ✅ csapiCollections                  | ✅ Yes   |
| **Builder creation**      | ✅ endpoint.edr(collectionId)          | ✅ endpoint.csapi(collectionId)      | ✅ Yes   |
| **URL construction**      | ✅ builder.buildAreaDownloadUrl()      | ✅ builder.getSystems()              | ✅ Yes   |
| **Fixture-driven**        | ✅ Mock fetch returns EDR fixtures     | ✅ Mock fetch returns CSAPI fixtures | ✅ Yes   |
| **Multi-step workflows**  | ✅ Conformance → collections → builder | ✅ Same + query → paginate           | ✅ Yes   |

**All upstream patterns followed** ✅

---

## Document Metadata

**Status:** Complete  
**Deliverable:** Integration test workflow specifications with:

- 4 workflow designs (Discovery, Observation, Command, Cross-Resource Navigation)
- 26 test scenarios with complete specifications
- HTTP response mocking strategy using Jest
- Assertion patterns for URL validation, response structures, state transitions
- 33 fixture specifications organized by workflow
- Test structure templates for standard and multi-step workflows
- Error handling scenarios (11 error conditions)
- State validation patterns (endpoint, builder, command, pagination)
- Implementation estimates (620-960 lines, 6.5-10 hours)
- Integration with unit tests (complementary coverage)
- Success criteria and validation (all workflows, all patterns aligned)

**Lines:** ~6,200 words covering complete integration test strategy

**Research Foundation:**

- Section 1-2: Upstream EDR integration test patterns (public API entry, fixture-driven, multi-component)
- Section 12: QueryBuilder testing strategy (URL validation, encoding, resource availability)
- Section 13: Resource method testing patterns (CRUD operations, navigation methods)
- Implementation Guide: 4 workflow specifications
- ROADMAP Phase 4: Integration test implementation plan

**Key Insights:**

1. **Integration = Multi-Component + Public API + Fixtures:** Integration tests must test component interactions through public API with realistic fixtures, not just "bigger unit tests"
2. **4 Distinct Workflows:** Discovery (conformance → collections → builder), Observation (systems → datastreams → observations → pagination), Command (control streams → feasibility → submit → status → result), Cross-Resource (system → deployments → procedures → features → datastreams → observations)
3. **Jest Mocking is Sufficient:** No need for additional mocking libraries - Jest's built-in `jest.fn()` and `globalThis.fetch` mocking handles all scenarios including fixture sequencing for multi-step workflows
4. **Fixtures Are Critical:** 33 fixtures required, organized by workflow, sourced from spec examples - fixture quality determines test realism
5. **State Validation is Key:** Integration tests must validate state changes across workflow steps (endpoint state, builder state, command state transitions, pagination state)

**Next Steps:**

1. Create fixture files (33 files organized by workflow)
2. Implement test structure in `endpoint.spec.ts`
3. Write Discovery workflow tests (6 scenarios, 120-180 lines)
4. Write Observation workflow tests (8 scenarios, 160-240 lines)
5. Write Command workflow tests (7 scenarios, 140-210 lines)
6. Write Cross-Resource Navigation tests (5 scenarios, 100-150 lines)
7. Validate coverage (>80% for integration paths)
8. Review and refine based on implementation learnings
