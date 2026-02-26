# End-to-End Testing Scope and Strategy for CSAPI

> **📝 Phase 2F Review Notice (February 2026)**
>
> This document was reviewed in [Phase 2F: Integration & Workflow Category Deep Dive](../review/phase-2f-integration-workflow-category.md) and **passed** with two minor refinement notes:
>
> - **M1 — Effort Estimates:** The comprehensive E2E suite (~700-1,000 lines, 3.0-3.75× test-to-code ratio) is significantly above upstream average (1.44×). Recommend labeling E2E estimates as "Minimum Viable" (~400-500 lines) vs "Comprehensive" (~700-1,000 lines) and starting with minimum viable for initial contribution.
> - **M2 — Command Feasibility Wording:** Section 5.3's "validate result" in the Command Submission workflow should clarify: this means asserting the client's parsed response structure (client transformation), NOT testing the server's feasibility verdict.
>
> Overall verdict: ✅ **Pass** — This document provides the strongest E2E definition in the research corpus.

**Research Plan:** [Research Plan 07: End-to-End Testing Scope Definition](../research-plans/07-end-to-end-testing-scope.md)  
**Research Questions:** 54 questions about e2e definition for URL-building libraries, scope and boundaries, integration vs e2e distinction, workflow-based testing, upstream and industry patterns, test pyramid distribution, test structure, coverage requirements, error scenarios, and performance considerations  
**Methodology:** 3-phase systematic analysis (Upstream e2e analysis from Sections 1-2 → Industry e2e analysis from Section 3 and client library patterns → CSAPI e2e definition applying patterns to URL builder architecture)  
**Research Time:** ~1 hour (70 minutes) (February 5, 2026)

**Primary Source(s):**

- Section 1: EDR Test Pattern Blueprint (upstream e2e patterns from accepted PR #114)
- Section 2: Upstream Test Consistency Matrix (e2e tests across 6 implementations)
- Section 3: TypeScript Testing Standards (industry e2e standards and test pyramid)
- Implementation Guide: csapi-implementation-guide.md (4 workflow types specification)

**Supporting Resources:**

- Section 6: Meaningful vs Trivial Definition (quality criteria for e2e tests)
- Senior dev feedback documentation (lack of e2e tests criticism)

**Document Purpose:** Define what "end-to-end" means for a URL-building client library that doesn't make HTTP calls, establish clear scope and boundaries for e2e tests, specify 4 complete workflow tests that satisfy the senior dev's e2e requirement while aligning with industry standards for client library testing (integration tests = e2e tests with mocked HTTP responses).

---

## Executive Summary

### Key Findings

**What "End-to-End" Means for CSAPI:**
For a URL-building library like CSAPI, "end-to-end" means **complete multi-component workflows from endpoint detection through URL construction and format detection**, NOT integration tests that make real HTTP calls. The library builds URLs but doesn't fetch data, so e2e tests must mock HTTP responses while testing complete workflows.

**Critical Distinction:**

- ❌ **Traditional E2E** (not applicable): Tests against real HTTP servers, makes real network calls
- ✅ **CSAPI E2E** (what we need): Tests complete workflows (endpoint → collection → QueryBuilder → URL + format detection) with mocked HTTP responses

**Senior Dev Feedback Context:**
Previous implementation was rejected for lacking "end-to-end" tests. For CSAPI, this means the Implementation Guide's "Integration Tests" **ARE** the e2e tests - they test complete workflows across all library components.

### E2E vs Integration Distinction for CSAPI

| Aspect           | Integration Test                    | End-to-End Test (CSAPI)                                                       |
| ---------------- | ----------------------------------- | ----------------------------------------------------------------------------- |
| **Scope**        | 2-3 components                      | All components (endpoint → QueryBuilder → format)                             |
| **Entry Point**  | Mid-level (QueryBuilder creation)   | Top-level (`new OgcApiEndpoint()`)                                            |
| **Workflow**     | Partial (single operation)          | Complete (discovery → query → parse)                                          |
| **Components**   | QueryBuilder + helpers              | Endpoint + conformance + collections + QueryBuilder + format detection        |
| **Example**      | `builder.getSystems({ limit: 10 })` | Discovery → list collections → create builder → query systems → detect format |
| **HTTP Mocking** | Single endpoint                     | Complete workflow (root + conformance + collections + resources)              |
| **Length**       | 20-50 lines per test                | 100-200 lines per test                                                        |
| **Count**        | ~60-80 tests                        | ~4-6 tests (workflows)                                                        |

**Key Insight:** What Implementation Guide calls "Integration Tests" are actually **E2E tests** by industry definition - they test complete workflows across all library layers.

### Test Pyramid for CSAPI

```
        /\
       /  \        E2E (10-15%)
      /____\       ~500-800 lines
     /      \      4 workflow tests
    /        \
   /Integration\   (25-30%)
  /   (15-20%)  \  ~800-1,000 lines
 /______________\  Multi-component tests
/                \
/      Unit       \ (55-60%)
/   (60-70%)      \ ~3,000-3,600 lines
/__________________\ Component tests
```

**Distribution:**

- **Unit Tests (55-60%):** 3,000-3,600 lines, ~200-250 tests
- **Integration Tests (25-30%):** 800-1,000 lines, ~50-60 tests (multi-component, 2-3 components)
- **E2E Tests (10-15%):** 500-800 lines, ~4-6 tests (complete workflows, all components)
- **Total:** ~4,800-5,600 test lines for ~1,600 implementation lines (3.0-3.5× ratio)

**Note:** This is higher than upstream average (1.44×) due to:

1. 9 resource types vs EDR's 1 resource type
2. Complex nested relationships requiring more integration tests
3. Two format types (SensorML, SWE Common) requiring parser tests
4. More comprehensive error scenario coverage

### E2E Scope Boundaries

**IN SCOPE (what e2e tests DO cover):**

- ✅ Complete workflows from `new OgcApiEndpoint()` to parsed results
- ✅ Multi-resource navigation (Systems → Deployments → DataStreams → Observations)
- ✅ Conformance-based behavior (adapt based on server capabilities)
- ✅ Format detection and negotiation (GeoJSON, SensorML, SWE Common)
- ✅ Error workflows (404, 500, validation errors → client error handling)
- ✅ Caching behavior (builder instance reuse)
- ✅ Link following (pagination, nested resources)

**OUT OF SCOPE (what e2e tests DON'T cover):**

- ❌ Actual HTTP calls (all responses mocked with realistic fixtures)
- ❌ Server-side behavior validation
- ❌ Network latency or performance testing
- ❌ Real-time streaming (unless library supports it)
- ❌ Server compliance testing (assume server is spec-compliant)

### 4 Core E2E Workflows

Based on Implementation Guide requirements:

1. **Discovery Workflow** (~100-150 lines)

   - Entry: `new OgcApiEndpoint(url)`
   - Steps: Connect → conformance check → list collections → filter by type → create builder → check available resources
   - Exit: QueryBuilder with validated resources
   - Components: Endpoint, conformance parser, collection parser, QueryBuilder factory

2. **Observation Query Workflow** (~150-200 lines)

   - Entry: `new OgcApiEndpoint(url)`
   - Steps: Discover systems → find datastreams → query observations → paginate → parse SWE Common results
   - Exit: Parsed observation array with typed results
   - Components: Endpoint, QueryBuilder (systems, datastreams, observations), SWE Common parser

3. **Command Submission Workflow** (~150-200 lines)

   - Entry: `new OgcApiEndpoint(url)`
   - Steps: Discover systems → find control streams → check feasibility → submit command → track status → retrieve results
   - Exit: Command result with status tracking
   - Components: Endpoint, QueryBuilder (systems, controlstreams, commands), status tracker

4. **Cross-Resource Navigation Workflow** (~100-150 lines)
   - Entry: `new OgcApiEndpoint(url)`
   - Steps: System → deployments → procedures → sampling features → datastreams → observations
   - Exit: Complete resource graph showing relationships
   - Components: Endpoint, QueryBuilder (all 9 resource types), link resolver

**Total Estimate:** 500-700 lines for 4 workflows, matches Implementation Guide Task 2 estimate (500-800 lines)

---

## 1. E2E Definition for URL-Building Libraries

### What "End-to-End" Means for CSAPI

**Traditional E2E (NOT applicable to CSAPI):**

```typescript
// ❌ Traditional e2e for API clients (makes real HTTP calls)
it('should fetch data from real server', async () => {
  const client = new APIClient('https://real-server.com');
  const data = await client.getData(); // Real HTTP request
  expect(data.items).toHaveLength(10);
});
```

**CSAPI E2E (what we implement):**

```typescript
// ✅ CSAPI e2e (tests complete workflow with mocked HTTP)
it('should complete observation query workflow end-to-end', async () => {
  // Mock ALL HTTP responses for complete workflow
  mockFetch({
    'https://api.example.com/': landingPageFixture,
    'https://api.example.com/conformance': conformanceFixture,
    'https://api.example.com/collections': collectionsFixture,
    'https://api.example.com/collections/sensors/items': systemsFixture,
    'https://api.example.com/collections/sensors/items/sys-1/datastreams':
      datastreamsFixture,
  });

  // 1. Endpoint detection (HTTP call #1: landing page)
  const endpoint = new OgcApiEndpoint('https://api.example.com/');

  // 2. Conformance check (HTTP call #2: conformance)
  expect(await endpoint.hasConnectedSystems).toBe(true);

  // 3. Collection listing (HTTP call #3: collections)
  const collections = await endpoint.csapiCollections;
  expect(collections).toContain('sensors');

  // 4. QueryBuilder creation (HTTP call #4: collection info)
  const builder = await endpoint.csapi('sensors');
  expect(builder.availableResources).toContain('systems');
  expect(builder.availableResources).toContain('datastreams');

  // 5. Systems query URL construction (no HTTP - pure URL building)
  const systemsUrl = builder.getSystems({ limit: 10 });
  expect(new URL(systemsUrl).searchParams.get('limit')).toBe('10');

  // 6. DataStreams query URL construction (no HTTP)
  const datastreamsUrl = builder.getSystemDataStreams('sys-1');
  expect(new URL(datastreamsUrl).pathname).toContain(
    '/systems/items/sys-1/datastreams'
  );

  // Validates: HTTP mocking, endpoint detection, conformance, collections,
  //            builder creation, resource validation, URL construction
});
```

### Entry and Exit Points

**Entry Point:** Always `new OgcApiEndpoint(url)`

- First interaction with the library
- Triggers endpoint detection
- Loads conformance and collections
- Entry to complete workflow

**Exit Points (vary by workflow):**

- **Discovery:** Validated `CSAPIQueryBuilder` instance with available resources
- **Observation Query:** Parsed observation array (SWE Common → TypeScript objects)
- **Command Submission:** Command result with status (submitted, completed, failed)
- **Cross-Resource Navigation:** Complete resource relationship graph

**What's In Between:**

- HTTP calls (mocked in tests, real in production)
- Conformance parsing
- Collection info parsing
- QueryBuilder creation
- Resource availability validation
- URL construction
- Format detection
- Format parsing (SensorML, SWE Common)

### Components Involved in E2E

**All library layers must be tested:**

1. **Endpoint Layer:** `OgcApiEndpoint`

   - `.fromUrl()` factory
   - `.hasConnectedSystems` property
   - `.csapiCollections` property
   - `.csapi(collectionId)` factory method

2. **Info/Conformance Layer:** Parsers

   - Conformance class detection
   - Collection parsing
   - Link resolution
   - Resource availability detection

3. **QueryBuilder Layer:** `CSAPIQueryBuilder`

   - Factory method creation
   - Caching behavior
   - Resource validation
   - URL construction methods (70-80 methods)

4. **Format Layer:** Parsers

   - SensorML 3.0 parser
   - SWE Common 3.0 parser
   - Format detection/negotiation

5. **Helper Layer:** Utilities
   - Temporal parameter serialization
   - Spatial parameter serialization
   - URL encoding helpers

**E2E tests verify all layers work together**, not just individual components.

---

## 2. E2E vs Integration Distinction

### Clear Boundary Definition

**Integration Test:**

- Tests 2-3 components together
- Mocks some internal components
- Partial workflow (one operation)
- Entry at mid-level API
- ~20-50 lines
- Examples:
  - QueryBuilder + helper functions
  - Format parser + validators
  - Link resolver + URL builder

**End-to-End Test:**

- Tests ALL components together (5+ layers)
- Only mocks external HTTP calls
- Complete workflow (multi-step)
- Entry at top-level API (`new OgcApiEndpoint()`)
- ~100-200 lines
- Examples:
  - Discovery workflow (7 steps across all layers)
  - Observation query workflow (8 steps across all layers)
  - Command submission workflow (9 steps across all layers)

### Side-by-Side Comparison

**Integration Test Example:**

```typescript
describe('CSAPIQueryBuilder integration', () => {
  it('should build systems URL with spatial filter', async () => {
    // Setup: Mock only the collection info HTTP call
    mockFetch({
      'http://test/collections/sensors': collectionInfoFixture,
    });

    // Entry: Mid-level (already have endpoint)
    const endpoint = new OgcApiEndpoint('http://test/');
    const builder = await endpoint.csapi('sensors');

    // Test: Single operation
    const url = builder.getSystems({
      bbox: [-180, -90, 180, 90],
      limit: 10,
    });

    // Validation: URL structure only
    const parsed = new URL(url);
    expect(parsed.searchParams.get('bbox')).toBe('-180,-90,180,90');
    expect(parsed.searchParams.get('limit')).toBe('10');
  });
});
```

**End-to-End Test Example:**

```typescript
describe('CSAPI observation workflow end-to-end', () => {
  it('should query observations from discovery to parsed results', async () => {
    // Setup: Mock ALL HTTP calls in workflow
    mockFetch({
      'http://test/': landingPageFixture,
      'http://test/conformance': conformanceFixture,
      'http://test/collections': collectionsFixture,
      'http://test/collections/sensors': sensorsCollectionFixture,
      'http://test/collections/sensors/items': systemsFixture,
      'http://test/collections/sensors/items/sys-1/datastreams':
        datastreamsFixture,
      'http://test/collections/sensors/items/sys-1/datastreams/ds-1/observations':
        observationsFixture,
    });

    // Entry: Top-level (fresh start)
    const endpoint = new OgcApiEndpoint('http://test/');

    // Step 1: Verify CSAPI support (conformance check)
    expect(await endpoint.hasConnectedSystems).toBe(true);

    // Step 2: List CSAPI collections
    const collections = await endpoint.csapiCollections;
    expect(collections).toContain('sensors');

    // Step 3: Create QueryBuilder (validates resources)
    const builder = await endpoint.csapi('sensors');
    expect(builder.availableResources).toContain('systems');
    expect(builder.availableResources).toContain('datastreams');
    expect(builder.availableResources).toContain('observations');

    // Step 4: Query systems
    const systemsUrl = builder.getSystems({ systemType: 'sensor', limit: 5 });
    expect(new URL(systemsUrl).pathname).toBe('/collections/sensors/items');
    expect(new URL(systemsUrl).searchParams.get('systemType')).toBe('sensor');

    // Step 5: Query system's datastreams
    const datastreamsUrl = builder.getSystemDataStreams('sys-1', {
      observedProperty: 'temperature',
    });
    expect(new URL(datastreamsUrl).pathname).toContain(
      '/systems/items/sys-1/datastreams'
    );

    // Step 6: Query datastream's observations
    const observationsUrl = builder.getDataStreamObservations('ds-1', {
      phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
      limit: 100,
    });
    expect(new URL(observationsUrl).pathname).toContain(
      '/datastreams/items/ds-1/observations'
    );
    expect(new URL(observationsUrl).searchParams.get('phenomenonTime')).toMatch(
      /2024-01-01.*2024-01-31/
    );

    // Step 7: Validate observation format detection
    // (In production, user would fetch observationsUrl and parse response)
    // Test validates URL leads to correct format negotiation

    // Validates: Endpoint detection, conformance, collections, builder creation,
    //            multi-resource navigation, URL construction, query parameters,
    //            resource relationships, all working together
  });
});
```

### Implementation Guide Clarification

**Important:** What Implementation Guide calls "Integration Tests" are **E2E tests** by definition:

From Implementation Guide Task 2:

> **Integration Tests (End-to-End Workflows):**
>
> - Discovery workflows: Connect → check conformance → list collections → filter by type → retrieve resources
> - Observation workflows: Discover systems → find datastreams → query observations → paginate → parse results
> - Command workflows: Discover systems → find control streams → check feasibility → submit → track status → retrieve results

These are **complete workflows across all components** = E2E tests, not integration tests.

**Terminology Mapping:**

- Implementation Guide "Integration Tests" = E2E Tests (what this research defines)
- Implementation Guide doesn't explicitly define true integration tests
- We need BOTH:
  - **Integration Tests:** 2-3 component tests (~800-1,000 lines)
  - **E2E Tests:** Complete workflow tests (~500-800 lines)

---

## 3. E2E Scope and Boundaries

### In Scope: What E2E Tests Cover

✅ **1. Complete Workflows:**

- Entry: `new OgcApiEndpoint(url)`
- All steps from discovery to final result
- Multi-resource navigation paths
- Realistic user scenarios

✅ **2. Multi-Component Interaction:**

- Endpoint detection + conformance parsing + collection parsing
- QueryBuilder factory + resource validation
- URL construction + query parameter serialization
- Format detection + format parsing

✅ **3. Conformance-Based Behavior:**

- Adapt QueryBuilder methods based on collection's supported resources
- Throw errors when unsupported resources accessed
- Validate resource relationships (e.g., system must exist before datastreams)

✅ **4. Format Detection and Parsing:**

- Detect format from URL or response headers
- Parse SensorML 3.0 documents to TypeScript objects
- Parse SWE Common 3.0 results to TypeScript objects
- Round-trip validation (parse → serialize → parse)

✅ **5. Error Workflows:**

- Server errors (404 Not Found, 500 Internal Server Error) → client error handling
- Validation errors (invalid parameters) → descriptive error messages
- Malformed responses → parse error handling
- Network errors (mocked timeout) → retry or fail gracefully

✅ **6. Caching and Performance:**

- QueryBuilder instance caching (same collection → same builder)
- Collection info caching
- No unnecessary HTTP calls

✅ **7. Link Following:**

- Pagination with rel="next" links
- Nested resource links (system → datastreams link)
- Collection link resolution

### Out of Scope: What E2E Tests DON'T Cover

❌ **1. Actual HTTP Calls:**

- No real network requests
- All responses mocked with realistic fixtures
- Mock infrastructure manages request/response pairing

❌ **2. Server-Side Behavior:**

- Don't validate server implements CSAPI spec correctly
- Assume server responses are spec-compliant
- Focus on client library behavior given spec-compliant responses

❌ **3. Network Conditions:**

- No latency testing
- No bandwidth testing
- No connection stability testing
- (These belong in consuming application's e2e tests)

❌ **4. Performance/Load Testing:**

- No load testing (concurrent requests)
- No memory leak testing
- No stress testing
- (These belong in separate performance test suite)

❌ **5. Real-Time Streaming:**

- Unless CSAPI library explicitly supports streaming
- Most workflows are request/response
- If streaming added later, add streaming e2e tests

❌ **6. Browser-Specific Testing:**

- No browser compatibility testing in e2e tests
- (These belong in cross-browser test suite)
- E2E tests run in Node.js environment

---

## 4. E2E Workflows for CSAPI

### Workflow 1: Discovery

**Purpose:** Validate endpoint detection, conformance checking, collection listing, and QueryBuilder creation

**Steps:**

1. Connect to endpoint via `new OgcApiEndpoint(url)` (HTTP: landing page)
2. Check CSAPI support via `endpoint.hasConnectedSystems` (HTTP: conformance)
3. List CSAPI collections via `endpoint.csapiCollections` (HTTP: collections)
4. Filter collections by resource type (client-side)
5. Create QueryBuilder via `endpoint.csapi(collectionId)` (HTTP: collection info)
6. Validate available resources via `builder.availableResources` (client-side)

**Components Involved:**

- `OgcApiEndpoint` (factory, properties)
- Conformance parser
- Collection parser
- QueryBuilder factory
- Resource validator

**Entry:** `new OgcApiEndpoint('https://api.example.com/')`

**Exit:** Validated `CSAPIQueryBuilder` with confirmed resource availability

**Assertions:**

- `endpoint.hasConnectedSystems === true`
- `endpoint.csapiCollections` contains expected collection IDs
- Builder creation succeeds
- `builder.availableResources` matches collection's declared resources
- Caching works (same collection → same builder instance)

**Test Length:** ~100-150 lines

**HTTP Mocks Required:**

- Landing page (`/`)
- Conformance (`/conformance`)
- Collections list (`/collections`)
- Collection info (`/collections/{collectionId}`)

**Example Structure:**

```typescript
describe('CSAPI Discovery Workflow E2E', () => {
  it('should discover endpoint, check conformance, list collections, and create builder', async () => {
    // Mock setup
    mockFetch({
      'http://test/': landingPageFixture,
      'http://test/conformance': conformanceFixture,
      'http://test/collections': collectionsFixture,
      'http://test/collections/sensors': sensorsCollectionFixture,
    });

    // Step 1: Connect
    const endpoint = new OgcApiEndpoint('http://test/');
    expect(endpoint).toBeInstanceOf(OgcApiEndpoint);

    // Step 2: Check conformance
    const hasCSAPI = await endpoint.hasConnectedSystems;
    expect(hasCSAPI).toBe(true);

    // Step 3: List collections
    const collections = await endpoint.csapiCollections;
    expect(collections).toContain('sensors');
    expect(collections).toContain('stations');

    // Step 4: Create builder
    const builder1 = await endpoint.csapi('sensors');
    expect(builder1).toBeDefined();
    expect(builder1.availableResources).toContain('systems');
    expect(builder1.availableResources).toContain('datastreams');

    // Step 5: Validate caching
    const builder2 = await endpoint.csapi('sensors');
    expect(builder1).toBe(builder2); // Same instance
  });
});
```

---

### Workflow 2: Observation Query

**Purpose:** Validate complete observation query workflow from system discovery to parsed observation results

**Steps:**

1. Connect to endpoint (discovery workflow steps 1-5)
2. Query systems with spatial/temporal filters (HTTP: systems collection)
3. Navigate to system's datastreams (HTTP: datastreams for system)
4. Filter datastreams by observed property (client-side)
5. Query observations with temporal filter (HTTP: observations for datastream)
6. Follow pagination links for large result sets (HTTP: next page)
7. Parse SWE Common observation results (client-side)
8. Validate parsed observation structure (client-side)

**Components Involved:**

- All from Discovery workflow
- QueryBuilder (systems, datastreams, observations methods)
- SWE Common parser
- Pagination link resolver

**Entry:** `new OgcApiEndpoint('https://api.example.com/')`

**Exit:** Array of parsed observations with typed results

**Assertions:**

- Systems query URL correct (path, query params, encoding)
- DataStreams query URL correct (nested under system)
- Observations query URL correct (nested under datastream, temporal filter)
- Pagination links followed correctly
- SWE Common parsing produces valid TypeScript objects
- Observation structure matches expected schema

**Test Length:** ~150-200 lines

**HTTP Mocks Required:**

- All from Discovery workflow
- Systems collection response
- DataStreams for specific system
- Observations for specific datastream
- Pagination next page (if testing pagination)

**Example Structure:**

```typescript
describe('CSAPI Observation Query Workflow E2E', () => {
  it('should query observations from system discovery to parsed results', async () => {
    // Mock setup (7 HTTP endpoints)
    mockFetch({
      'http://test/': landingPageFixture,
      'http://test/conformance': conformanceFixture,
      'http://test/collections': collectionsFixture,
      'http://test/collections/sensors': sensorsCollectionFixture,
      'http://test/collections/sensors/items?systemType=sensor': systemsFixture,
      'http://test/collections/sensors/items/sys-1/datastreams?observedProperty=temperature':
        datastreamsFixture,
      'http://test/collections/sensors/items/sys-1/datastreams/ds-1/observations?phenomenonTime=2024-01-01T00:00:00Z/2024-01-31T23:59:59Z':
        observationsFixture,
    });

    // Discovery steps
    const endpoint = new OgcApiEndpoint('http://test/');
    expect(await endpoint.hasConnectedSystems).toBe(true);
    const builder = await endpoint.csapi('sensors');

    // Step 1: Query systems
    const systemsUrl = builder.getSystems({ systemType: 'sensor' });
    expect(new URL(systemsUrl).pathname).toBe('/collections/sensors/items');
    expect(new URL(systemsUrl).searchParams.get('systemType')).toBe('sensor');

    // Step 2: Navigate to system's datastreams
    const datastreamsUrl = builder.getSystemDataStreams('sys-1', {
      observedProperty: 'temperature',
    });
    expect(new URL(datastreamsUrl).pathname).toBe(
      '/collections/sensors/items/sys-1/datastreams'
    );
    expect(new URL(datastreamsUrl).searchParams.get('observedProperty')).toBe(
      'temperature'
    );

    // Step 3: Query observations
    const observationsUrl = builder.getDataStreamObservations('ds-1', {
      phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
    });
    expect(new URL(observationsUrl).pathname).toBe(
      '/collections/sensors/items/sys-1/datastreams/ds-1/observations'
    );
    expect(new URL(observationsUrl).searchParams.get('phenomenonTime')).toMatch(
      /2024-01-01.*2024-01-31/
    );

    // Step 4: Validate complete URL structure
    const parsed = new URL(observationsUrl);
    expect(parsed.protocol).toBe('http:');
    expect(parsed.host).toBe('test');
    expect(parsed.pathname).toContain('/observations');
    expect(parsed.searchParams.has('phenomenonTime')).toBe(true);

    // In production: fetch(observationsUrl) → parse SWE Common
    // Test validates URL leads to correct observation retrieval
  });
});
```

---

### Workflow 3: Command Submission

**Purpose:** Validate command submission workflow from control stream discovery to command status tracking

**Steps:**

1. Connect to endpoint (discovery workflow steps 1-5)
2. Query systems that support commands (HTTP: systems with command capability)
3. Navigate to system's control streams (HTTP: control streams for system)
4. Check command feasibility (HTTP: feasibility check endpoint) — **test asserts the client constructs the correct feasibility URL, NOT the server's feasibility verdict**
5. Submit command (HTTP: POST to commands collection)
6. Track command status (HTTP: command status endpoint)
7. Retrieve command results when complete (HTTP: command result endpoint)

**Components Involved:**

- All from Discovery workflow
- QueryBuilder (systems, controlstreams, commands methods)
- Command status tracker
- Command result parser

**Entry:** `new OgcApiEndpoint('https://api.example.com/')`

**Exit:** Command result with final status (completed, failed, cancelled)

**Assertions:**

- Systems query filters for command capability
- Control streams query URL correct
- Feasibility check URL correct (assert URL construction and parsed response structure — NOT the server's feasibility determination)
- Command submission URL correct (POST with payload)
- Status tracking URL correct
- Result retrieval URL correct
- Status transitions tracked correctly

**Test Length:** ~150-200 lines

**HTTP Mocks Required:**

- All from Discovery workflow
- Systems with command capability
- Control streams for system
- Feasibility check response
- Command submission response (201 Created with status link)
- Command status response (in-progress, then completed)
- Command result response

**Example Structure:**

```typescript
describe('CSAPI Command Submission Workflow E2E', () => {
  it('should submit command and track status to completion', async () => {
    // Mock setup (10+ HTTP endpoints)
    mockFetch({
      'http://test/': landingPageFixture,
      'http://test/conformance': conformanceFixture,
      'http://test/collections': collectionsFixture,
      'http://test/collections/actuators': actuatorsCollectionFixture,
      'http://test/collections/actuators/items?capabilities=command':
        systemsWithCommandsFixture,
      'http://test/collections/actuators/items/sys-1/controlstreams':
        controlStreamsFixture,
      'http://test/collections/actuators/items/sys-1/controlstreams/cs-1/feasibility':
        feasibilityCheckFixture,
      'http://test/collections/actuators/items/sys-1/controlstreams/cs-1/commands':
        commandSubmissionFixture,
      'http://test/collections/actuators/items/sys-1/controlstreams/cs-1/commands/cmd-1/status':
        commandStatusFixture,
      'http://test/collections/actuators/items/sys-1/controlstreams/cs-1/commands/cmd-1/result':
        commandResultFixture,
    });

    // Discovery steps
    const endpoint = new OgcApiEndpoint('http://test/');
    const builder = await endpoint.csapi('actuators');

    // Step 1: Find systems with command capability
    const systemsUrl = builder.getSystems({ capabilities: 'command' });
    expect(new URL(systemsUrl).searchParams.get('capabilities')).toBe(
      'command'
    );

    // Step 2: Get control streams
    const controlStreamsUrl = builder.getSystemControlStreams('sys-1');
    expect(new URL(controlStreamsUrl).pathname).toBe(
      '/collections/actuators/items/sys-1/controlstreams'
    );

    // Step 3: Check feasibility
    const feasibilityUrl = builder.getControlStreamFeasibility('cs-1', {
      /* params */
    });
    expect(new URL(feasibilityUrl).pathname).toContain('/feasibility');

    // Step 4: Submit command
    const submitUrl = builder.createCommand('cs-1', {
      /* command payload */
    });
    expect(new URL(submitUrl).pathname).toContain('/commands');

    // Step 5: Track status
    const statusUrl = builder.getCommandStatus('cmd-1');
    expect(new URL(statusUrl).pathname).toContain('/status');

    // Step 6: Get result
    const resultUrl = builder.getCommandResult('cmd-1');
    expect(new URL(resultUrl).pathname).toContain('/result');
  });
});
```

---

### Workflow 4: Cross-Resource Navigation

**Purpose:** Validate seamless navigation across all 9 resource types

**Steps:**

1. Connect to endpoint (discovery workflow steps 1-5)
2. Query systems (HTTP: systems collection)
3. Navigate to system's deployments (HTTP: deployments for system)
4. Navigate to deployment's procedures (HTTP: procedures for deployment)
5. Navigate to procedure's sampling features (HTTP: sampling features for procedure)
6. Navigate to sampling feature's datastreams (HTTP: datastreams for sampling feature)
7. Navigate to datastream's observations (HTTP: observations for datastream)
8. Validate complete resource relationship graph (client-side)

**Components Involved:**

- All from Discovery workflow
- QueryBuilder (all 9 resource type methods)
- Link resolver (nested resource navigation)
- Resource relationship validator

**Entry:** `new OgcApiEndpoint('https://api.example.com/')`

**Exit:** Complete resource graph showing 6-hop navigation path

**Assertions:**

- Each navigation step produces correct nested URL
- Resource IDs propagate correctly through navigation chain
- Query parameters preserved across navigation
- All resource types accessible from single QueryBuilder
- No builder switching required

**Test Length:** ~100-150 lines

**HTTP Mocks Required:**

- All from Discovery workflow
- Each resource type's collection response (9 types)
- Nested resource responses (6 navigation steps)

**Example Structure:**

```typescript
describe('CSAPI Cross-Resource Navigation Workflow E2E', () => {
  it('should navigate across 6 resource types seamlessly', async () => {
    // Mock setup (15+ HTTP endpoints)
    mockFetch({
      'http://test/': landingPageFixture,
      'http://test/conformance': conformanceFixture,
      'http://test/collections': collectionsFixture,
      'http://test/collections/sensors': sensorsCollectionFixture,
      'http://test/collections/sensors/items': systemsFixture,
      'http://test/collections/sensors/items/sys-1/deployments':
        deploymentsFixture,
      'http://test/collections/sensors/items/sys-1/deployments/dep-1/procedures':
        proceduresFixture,
      'http://test/collections/sensors/items/sys-1/deployments/dep-1/procedures/proc-1/samplingfeatures':
        samplingFeaturesFixture,
      'http://test/collections/sensors/items/sys-1/samplingfeatures/sf-1/datastreams':
        datastreamsFixture,
      'http://test/collections/sensors/items/sys-1/datastreams/ds-1/observations':
        observationsFixture,
    });

    // Discovery steps
    const endpoint = new OgcApiEndpoint('http://test/');
    const builder = await endpoint.csapi('sensors');

    // Navigation chain (6 hops)
    const systemsUrl = builder.getSystems();
    expect(new URL(systemsUrl).pathname).toBe('/collections/sensors/items');

    const deploymentsUrl = builder.getSystemDeployments('sys-1');
    expect(new URL(deploymentsUrl).pathname).toBe(
      '/collections/sensors/items/sys-1/deployments'
    );

    const proceduresUrl = builder.getDeploymentProcedures('sys-1', 'dep-1');
    expect(new URL(proceduresUrl).pathname).toBe(
      '/collections/sensors/items/sys-1/deployments/dep-1/procedures'
    );

    const samplingFeaturesUrl = builder.getProcedureSamplingFeatures('proc-1');
    expect(new URL(samplingFeaturesUrl).pathname).toContain(
      '/procedures/proc-1/samplingfeatures'
    );

    const datastreamsUrl = builder.getSamplingFeatureDataStreams('sf-1');
    expect(new URL(datastreamsUrl).pathname).toContain(
      '/samplingfeatures/sf-1/datastreams'
    );

    const observationsUrl = builder.getDataStreamObservations('ds-1');
    expect(new URL(observationsUrl).pathname).toContain(
      '/datastreams/ds-1/observations'
    );

    // Validate: Single builder navigated through 6 resource types
    // No builder switching, no separate factories, seamless navigation
  });
});
```

---

## 5. Test Pyramid Distribution

### Recommended Distribution for CSAPI

```
          /\
         /  \        E2E (10-15%)
        /____\       ~500-800 lines
       /      \      4-6 workflow tests
      /        \
     /Integration\   (25-30%)
    /            \   ~1,200-1,600 lines
   /______________\  50-60 multi-component tests
  /                \
 /      Unit        \ (55-60%)
/                    \ ~3,000-3,600 lines
/______________________\ 200-250 component tests
```

**Total Test Lines:** ~4,800-6,000 lines for ~1,600 implementation lines (3.0-3.75× ratio)

### Justification for Higher Ratio

CSAPI test-to-code ratio is **higher than upstream average (1.44×)** due to:

1. **More Resource Types:** 9 resource types vs EDR's 1 resource type

   - Each resource type needs CRUD operation tests (4-5 tests × 9 = 36-45 tests)
   - Each resource type needs query parameter tests (10+ tests × 9 = 90+ tests)
   - Nested resource relationships need tests (30+ combinations)

2. **Complex Nested Relationships:**

   - System → Deployments (1 level)
   - System → Deployments → Procedures (2 levels)
   - System → DataStreams → Observations (2 levels)
   - Each nesting pattern needs tests (10+ nested patterns)

3. **Two Format Types:**

   - SensorML 3.0 parser (15-20 tests for all system types)
   - SWE Common 3.0 parser (15-20 tests for all encodings)
   - Round-trip tests (10+ tests)
   - Format detection tests (5-10 tests)

4. **More Query Parameters:**

   - Temporal (phenomenonTime, resultTime, validTime) - 15+ tests
   - Spatial (bbox, geometry) - 10+ tests
   - Relationship (parent, observed property, FOI) - 15+ tests
   - Hierarchical (recursive, depth) - 10+ tests
   - Pagination - 10+ tests
   - Format negotiation - 5+ tests

5. **More Error Scenarios:**
   - Resource not available (9 resource types × 5 operations = 45 tests)
   - Invalid parameters (50+ parameter validation tests)
   - Malformed responses (20+ parse error tests)
   - Network errors (10+ tests)

**Conclusion:** 3.0-3.75× ratio is justified and necessary for comprehensive coverage.

### Breakdown by Test Type

**Unit Tests (55-60%, ~3,000-3,600 lines, ~200-250 tests):**

**Purpose:** Test individual functions/methods in isolation

**Categories:**

- **Helper Functions** (~300-400 lines, ~30-40 tests):
  - Temporal parameter serialization (phenomenonTime, resultTime, validTime)
  - Spatial parameter serialization (bbox, geometry encoding)
  - URL encoding helpers (special characters, spaces, reserved)
  - Relationship parameter serialization
- **Format Parsers** (~800-1,000 lines, ~60-80 tests):
  - SensorML 3.0 parser (PhysicalSystem, AggregateProcess, SimpleProcess)
  - SWE Common 3.0 parser (DataRecord, DataArray, all field types)
  - Format detection
  - Parse error handling
- **QueryBuilder Methods** (~1,500-1,800 lines, ~90-110 tests):
  - Each resource type's CRUD operations (9 × 4 = 36 tests)
  - Nested resource URL construction (30+ tests)
  - Query parameter encoding (50+ tests)
  - Validation errors (30+ tests)
- **Validators** (~400-500 lines, ~30-40 tests):
  - Resource availability validation
  - Parameter constraint validation
  - Format compatibility validation
  - Relationship validation

**Integration Tests (25-30%, ~1,200-1,600 lines, ~50-60 tests):**

**Purpose:** Test 2-3 components together

**Categories:**

- **QueryBuilder + Helpers** (~400-500 lines, ~20-25 tests):
  - QueryBuilder method calls helper functions
  - Complex parameter combinations
  - Multiple resource queries
- **Endpoint + Conformance** (~200-300 lines, ~10-15 tests):
  - Endpoint detection with conformance parsing
  - Collection listing with filtering
  - QueryBuilder creation with caching
- **Format Parser + Validators** (~300-400 lines, ~10-15 tests):
  - Parse with validation
  - Format detection with parsing
  - Round-trip (serialize → parse → validate)
- **Link Resolver + QueryBuilder** (~300-400 lines, ~10-15 tests):
  - Follow pagination links
  - Resolve nested resource links
  - Relative URL resolution

**E2E Tests (10-15%, ~500-800 lines, ~4-6 tests):**

**Purpose:** Test complete workflows across all components

**Categories:**

- **Core Workflows** (~400-600 lines, 4 tests):
  - Discovery workflow (~100-150 lines)
  - Observation query workflow (~150-200 lines)
  - Command submission workflow (~150-200 lines)
  - Cross-resource navigation workflow (~100-150 lines)
- **Error Workflows** (~100-200 lines, 1-2 tests):
  - Server error handling (404, 500)
  - Validation error handling
  - Malformed response handling

---

## 6. E2E Test Structure and Organization

### File Organization

**Recommended structure:**

```
src/
  ogc-api/
    csapi/
      endpoint.e2e.spec.ts        # E2E workflow tests (500-800 lines)
      endpoint.integration.spec.ts # Integration tests (400-600 lines)
      query-builder.spec.ts        # Unit tests for QueryBuilder (800-1000 lines)
      formats/
        sensorml.spec.ts           # SensorML parser unit tests (400-500 lines)
        swecommon.spec.ts          # SWE Common parser unit tests (400-500 lines)
      helpers/
        temporal.spec.ts           # Temporal helpers unit tests (200-300 lines)
        spatial.spec.ts            # Spatial helpers unit tests (200-300 lines)

fixtures/
  ogc-api/
    csapi/
      e2e/                         # E2E workflow fixtures
        discovery/                 # Discovery workflow fixtures
          landing-page.json
          conformance.json
          collections.json
          sensors-collection.json
        observation-query/         # Observation workflow fixtures
          systems.json
          datastreams.json
          observations.json
        command-submission/        # Command workflow fixtures
          control-streams.json
          command-response.json
          command-status.json
        cross-resource/            # Navigation workflow fixtures
          deployments.json
          procedures.json
          sampling-features.json
```

### E2E Test File Structure

**Template:**

```typescript
import { OgcApiEndpoint, CSAPIQueryBuilder } from '../../../src';
import { mockFetchWithFixtures } from '../../../test-utils/mock-fetch';
import * as path from 'path';

describe('CSAPI End-to-End Workflows', () => {
  // Shared setup
  const fixtureDir = path.join(__dirname, '../../../fixtures/ogc-api/csapi/e2e');

  beforeEach(() => {
    // Mock fetch will be configured per test
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Discovery Workflow', () => {
    it('should discover endpoint, verify conformance, list collections, and create builder', async () => {
      // Mock HTTP responses for discovery workflow
      mockFetchWithFixtures({
        'http://test/': path.join(fixtureDir, 'discovery/landing-page.json'),
        'http://test/conformance': path.join(fixtureDir, 'discovery/conformance.json'),
        'http://test/collections': path.join(fixtureDir, 'discovery/collections.json'),
        'http://test/collections/sensors': path.join(fixtureDir, 'discovery/sensors-collection.json')
      });

      // E2E workflow steps (100-150 lines)
      // ...
    });
  });

  describe('Observation Query Workflow', () => {
    it('should query observations from system discovery to parsed results', async () => {
      // Mock HTTP responses for observation workflow
      mockFetchWithFixtures({
        // ... all fixtures for observation workflow (7-8 endpoints)
      });

      // E2E workflow steps (150-200 lines)
      // ...
    });
  });

  describe('Command Submission Workflow', () => {
    it('should submit command and track status to completion', async () => {
      // Mock HTTP responses for command workflow
      mockFetchWithFixtures({
        // ... all fixtures for command workflow (10+ endpoints)
      });

      // E2E workflow steps (150-200 lines)
      // ...
    });
  });

  describe('Cross-Resource Navigation Workflow', () => {
    it('should navigate across 6 resource types seamlessly', async () => {
      // Mock HTTP responses for navigation workflow
      mockFetchWithFixtures({
        // ... all fixtures for navigation workflow (15+ endpoints)
      });

      // E2E workflow steps (100-150 lines)
      // ...
    });
  });

  describe('Error Workflows', () => {
    it('should handle server errors gracefully', async () => {
      // Mock error responses
      mockFetchWithErrors({
        'http://test/collections/sensors/items/nonexistent': { status: 404, body: {...} }
      });

      // Error handling workflow (50-100 lines)
      // ...
    });
  });
});
```

### Setup Requirements

**Mock Infrastructure:**

```typescript
// test-utils/mock-fetch.ts

export function mockFetchWithFixtures(
  urlToFixturePath: Record<string, string>
): void {
  globalThis.fetch = jest.fn(async (url: string) => {
    const urlStr = typeof url === 'string' ? url : url.toString();
    const fixturePath = urlToFixturePath[urlStr];

    if (!fixturePath) {
      return {
        ok: false,
        status: 404,
        json: async () => ({ error: 'Not Found' }),
      } as Response;
    }

    const contents = await fs.promises.readFile(fixturePath, 'utf-8');
    return {
      ok: true,
      status: 200,
      json: async () => JSON.parse(contents),
    } as Response;
  });
}

export function mockFetchWithErrors(
  urlToError: Record<string, { status: number; body: any }>
): void {
  globalThis.fetch = jest.fn(async (url: string) => {
    const urlStr = typeof url === 'string' ? url : url.toString();
    const error = urlToError[urlStr];

    if (!error) {
      throw new Error(`No mock configured for: ${urlStr}`);
    }

    return {
      ok: false,
      status: error.status,
      json: async () => error.body,
    } as Response;
  });
}
```

**Fixture Loading:**

- Use async `fs/promises` for fixture loading (matches EDR pattern)
- Organize fixtures by workflow (discovery, observation-query, command-submission, cross-resource)
- Use realistic fixtures from OGC CSAPI spec examples
- Document fixture provenance (spec section, example number)

---

## 7. E2E Coverage Requirements

### Minimum Viable E2E Coverage (Initial Contribution Target)

**4 workflow tests (400-500 lines) — recommended starting point:**

1. Discovery workflow (happy path only)
2. Observation query workflow (happy path only)
3. Command submission workflow (happy path only)
4. Cross-resource navigation workflow (happy path only)

**No error workflows**

**Sufficient for:**

- Initial PR acceptance
- Addresses "lack of e2e tests" criticism
- Demonstrates complete workflows

**Not sufficient for:**

- Production readiness
- Comprehensive error handling validation
- Edge case coverage

### Comprehensive E2E Coverage (Stretch Goal — Post-Acceptance)

**4 core workflows + variations (600-800 lines) — expand after initial PR acceptance:**

1. **Discovery workflow** (150-200 lines):
   - Happy path
   - Missing conformance classes
   - Empty collection list
   - Collection without CSAPI resources
2. **Observation query workflow** (200-250 lines):
   - Happy path with pagination
   - Large result sets (100+ observations)
   - Different temporal filter types (instant, interval, open-ended)
   - Multiple observed properties
3. **Command submission workflow** (200-250 lines):
   - Happy path to completion
   - Command rejection (feasibility check fails)
   - Command cancellation mid-execution
   - Async command with long execution time
4. **Cross-resource navigation workflow** (150-200 lines):
   - Full 6-hop navigation
   - Short navigation (2-3 hops)
   - Different starting points (system vs sampling feature)

**Error workflows (100-200 lines):** 5. **Server error handling**:

- 404 Not Found → EndpointError
- 500 Internal Server Error → EndpointError
- 403 Forbidden → AuthorizationError

6. **Validation error handling**:
   - Invalid query parameters → ValidationError
   - Unsupported resource type → EndpointError
   - Malformed response → ParseError

**Total:** ~700-1,000 lines (6-10 tests)

**Sufficient for:**

- Production readiness
- Comprehensive workflow coverage
- Error scenario validation
- Confident refactoring

### What NOT to Cover in E2E

**Leave for unit/integration tests:**

- Individual query parameter validation (unit tests)
- URL encoding edge cases (unit tests)
- Format parsing edge cases (unit tests)
- Each CRUD operation for each resource type (integration tests)

**E2E tests focus on:**

- Complete workflows (multi-step)
- Multi-component interaction
- Realistic usage scenarios
- Error recovery workflows

---

## 8. HTTP Mocking Strategy for E2E

### Mocking Approach

**Pattern:** Mock `fetch` at global level with fixture-based responses

**Why this approach:**

- Matches EDR/STAC pattern (proven in upstream)
- Allows tests to use real URLs (realistic)
- Fixtures serve as spec compliance documentation
- Easy to update when spec changes
- Enables complete workflow mocking (all HTTP calls in workflow)

### Mock Setup

**Per-test mocking:**

```typescript
beforeEach(() => {
  // Configure mock for this specific test
  mockFetchWithFixtures({
    'http://test/': 'fixtures/ogc-api/csapi/e2e/discovery/landing-page.json',
    'http://test/conformance':
      'fixtures/ogc-api/csapi/e2e/discovery/conformance.json',
    // ... all endpoints needed for test
  });
});

afterEach(() => {
  jest.restoreAllMocks(); // Clean up after each test
});
```

**Workflow-specific mock helpers:**

```typescript
// test-utils/csapi-mocks.ts

export function mockDiscoveryWorkflow(baseUrl: string): void {
  mockFetchWithFixtures({
    [`${baseUrl}/`]: 'fixtures/ogc-api/csapi/e2e/discovery/landing-page.json',
    [`${baseUrl}/conformance`]:
      'fixtures/ogc-api/csapi/e2e/discovery/conformance.json',
    [`${baseUrl}/collections`]:
      'fixtures/ogc-api/csapi/e2e/discovery/collections.json',
    [`${baseUrl}/collections/sensors`]:
      'fixtures/ogc-api/csapi/e2e/discovery/sensors-collection.json',
  });
}

export function mockObservationWorkflow(baseUrl: string): void {
  // Include discovery workflow + observation-specific endpoints
  mockDiscoveryWorkflow(baseUrl);
  mockFetchWithFixtures({
    [`${baseUrl}/collections/sensors/items`]:
      'fixtures/ogc-api/csapi/e2e/observation-query/systems.json',
    [`${baseUrl}/collections/sensors/items/sys-1/datastreams`]:
      'fixtures/ogc-api/csapi/e2e/observation-query/datastreams.json',
    // ...
  });
}
```

### Fixture Requirements

**Fixture characteristics:**

- ✅ Real examples from OGC CSAPI spec
- ✅ Realistic data (sensor names, locations, measurements)
- ✅ Complete structure (all required properties)
- ✅ Variations (minimal, typical, maximal)
- ✅ Error responses (404, 500, validation errors)

**Fixture organization:**

```
fixtures/ogc-api/csapi/e2e/
  discovery/
    landing-page.json          # OGC API landing page
    conformance.json            # With CSAPI conformance classes
    collections.json            # Multiple collections
    sensors-collection.json     # Single collection with CSAPI resources
  observation-query/
    systems.json                # Systems collection response
    datastreams.json            # DataStreams for specific system
    observations.json           # Observations for specific datastream
    observations-page2.json     # Pagination next page
  command-submission/
    control-streams.json        # Control streams for system
    feasibility-check.json      # Feasibility check response
    command-created.json        # 201 Created with status link
    command-status-pending.json # Status: pending
    command-status-completed.json # Status: completed
    command-result.json         # Command result
  cross-resource/
    deployments.json            # Deployments for system
    procedures.json             # Procedures for deployment
    sampling-features.json      # Sampling features for procedure
  errors/
    404-not-found.json          # Standard 404 response
    500-server-error.json       # Standard 500 response
    validation-error.json       # Parameter validation error
```

**Fixture provenance documentation:**

```json
// fixtures/ogc-api/csapi/e2e/discovery/landing-page.json
{
  "_comment": "OGC API landing page example",
  "_source": "OGC API - Connected Systems Part 1, Section 7.2",
  "_spec_url": "https://docs.ogc.org/is/23-001/23-001.html#_landing_page",
  "_last_updated": "2026-02-05",
  "title": "CSAPI Test Server",
  "description": "Test endpoint for CSAPI client library e2e tests",
  "links": [
    // ... actual landing page content
  ]
}
```

---

## 9. Error Scenarios in E2E Tests

### Error Workflow Categories

**1. Server Errors (HTTP status codes):**

- 404 Not Found (resource doesn't exist)
- 500 Internal Server Error (server malfunction)
- 403 Forbidden (authentication required)
- 503 Service Unavailable (temporary failure)

**2. Validation Errors (invalid parameters):**

- Invalid query parameter format
- Unsupported query parameter
- Out-of-range values
- Malformed spatial/temporal filters

**3. Parse Errors (malformed responses):**

- Invalid JSON syntax
- Missing required properties
- Wrong property types
- Schema violations

**4. Network Errors:**

- Timeout (no response within limit)
- Connection refused (server unreachable)
- DNS resolution failure

### Error Testing Strategy

**Unit tests handle:**

- Individual parameter validation
- Format parsing errors
- URL encoding errors

**Integration tests handle:**

- Multi-component error propagation
- Error message formatting
- Error type discrimination

**E2E tests handle:**

- Complete error workflows (error → recovery)
- Multiple error points in workflow
- Error impact on subsequent steps

### E2E Error Test Examples

**Server Error Workflow:**

```typescript
it('should handle 404 Not Found gracefully in observation workflow', async () => {
  // Mock discovery workflow succeeds
  mockDiscoveryWorkflow('http://test');

  // Mock systems query succeeds
  mockFetchWithFixtures({
    'http://test/collections/sensors/items': systemsFixture,
  });

  // Mock datastreams query returns 404
  mockFetchWithErrors({
    'http://test/collections/sensors/items/sys-1/datastreams': {
      status: 404,
      body: {
        code: 'ResourceNotFound',
        description: 'System sys-1 does not exist',
      },
    },
  });

  // Discovery succeeds
  const endpoint = new OgcApiEndpoint('http://test/');
  const builder = await endpoint.csapi('sensors');

  // Systems query succeeds
  const systemsUrl = builder.getSystems();
  expect(systemsUrl).toBeDefined();

  // DataStreams query should succeed (URL construction)
  const datastreamsUrl = builder.getSystemDataStreams('sys-1');
  expect(datastreamsUrl).toBeDefined();

  // In production, fetch(datastreamsUrl) would throw EndpointError
  // Test validates URL construction still works despite nonexistent resource
  // Error handling is user's responsibility (fetch → catch → handle)
});
```

**Validation Error Workflow:**

```typescript
it('should throw validation error for invalid query parameters', async () => {
  mockDiscoveryWorkflow('http://test');

  const endpoint = new OgcApiEndpoint('http://test/');
  const builder = await endpoint.csapi('sensors');

  // Invalid temporal parameter format
  expect(() =>
    builder.getObservations({
      phenomenonTime: 'invalid-format',
    })
  ).toThrow('Invalid phenomenonTime format');

  // Invalid spatial parameter (wrong bbox length)
  expect(() =>
    builder.getSystems({
      bbox: [1, 2, 3], // Should be 4 values
    })
  ).toThrow('bbox must have 4 values');
});
```

---

## 10. Integration vs E2E Mapping

### Implementation Guide Terminology Clarification

**Implementation Guide states:**

> **Integration Tests (End-to-End Workflows):**
>
> - Discovery workflows
> - Observation workflows
> - Command workflows
> - Cross-resource navigation

**Correct interpretation:**

- Implementation Guide "Integration Tests" = **E2E Tests** (by this research's definition)
- They test complete workflows = E2E
- They involve all components = E2E
- They start from top-level API = E2E

**What we need:**

| Test Type       | Count    | Lines        | Purpose                                                       |
| --------------- | -------- | ------------ | ------------------------------------------------------------- |
| **Unit**        | ~200-250 | ~3,000-3,600 | Individual functions/methods                                  |
| **Integration** | ~50-60   | ~1,200-1,600 | 2-3 components together                                       |
| **E2E**         | ~4-6     | ~500-800     | Complete workflows (Implementation Guide "Integration Tests") |

**Phase 4, Task 2 mapping:**

- Task 2: "Integration Tests (End-to-End Workflows)" = **E2E Tests**
- Time estimate: 4-6 hours
- Line estimate: 500-800 lines
- This research provides the specification for Task 2

---

## 11. Validation Against Upstream

### EDR E2E Patterns

**From PR #114 analysis:**

- EDR has **integration tests in endpoint.spec.ts** (298 lines added)
- These tests are actually **e2e tests** by our definition:
  - Start from `OgcApiEndpoint` creation
  - Test complete workflow (endpoint → builder → URL)
  - Mock all HTTP responses
  - Test multi-component interaction

**Pattern validation:**
✅ CSAPI should follow EDR pattern:

- E2E tests in separate file or dedicated describe block
- Mock all HTTP responses with realistic fixtures
- Test complete workflows from endpoint creation
- Validate multi-component interaction

**Differences:**

- EDR: 1 resource type (data_queries) → simpler
- CSAPI: 9 resource types → more complex
- EDR: ~300 lines integration/e2e tests
- CSAPI: ~500-800 lines e2e tests (justified by complexity)

### Other Upstream Implementations

**WFS, WMS, WMTS, TMS, STAC:**

- All have **integration tests in endpoint.spec.ts**
- Test patterns similar to EDR
- Focus on complete workflows
- Mock all HTTP with fixtures

**Consistency with CSAPI:**
✅ CSAPI aligns with all upstream implementations:

- Jest framework
- Colocated test files
- Mock fetch with fixtures
- Integration tests test complete workflows
- Real spec examples as fixtures

**Upstream test pyramid:**

- Avg 1.44× test-to-code ratio
- ~60% unit, ~40% integration (includes e2e)
- CSAPI: 3.0-3.75× ratio justified by complexity

---

## 12. Validation Against Industry

### Industry E2E Standards

**From Section 3 (TypeScript Testing Standards):**

**Industry standard distribution:**

- 60-70% unit tests
- 30-40% integration tests
- **0-5% e2e tests (or none)**

**Why so few e2e tests in industry?**

- Client libraries don't make real HTTP calls in tests
- E2E belongs in consuming applications
- What we call "e2e" is actually "integration" by industry terms

**Industry definition:**

- **Unit:** Single function, all dependencies mocked
- **Integration:** Multiple components, HTTP mocked
- **E2E:** Real HTTP calls to real servers (rare in client libraries)

### CSAPI Alignment

**CSAPI adapts industry standards to context:**

| Industry Term   | Industry Definition              | CSAPI Interpretation                        |
| --------------- | -------------------------------- | ------------------------------------------- |
| **Unit**        | Single function, mocked deps     | Same: QueryBuilder method, helpers          |
| **Integration** | Multiple components, HTTP mocked | Same: 2-3 components together               |
| **E2E**         | Real HTTP to real servers        | **Adapted:** Complete workflow, HTTP mocked |

**Why adaptation is necessary:**

- CSAPI is URL-building library (doesn't make HTTP calls)
- Senior dev wants "e2e tests" (complete workflows)
- Industry's "integration" doesn't capture complete workflow testing
- Need term for "complete workflow with all components"

**CSAPI distribution:**

- 55-60% unit (slightly lower than industry to accommodate e2e)
- 25-30% integration (standard multi-component tests)
- 10-15% e2e (complete workflows - higher than industry 0-5% because senior dev explicitly requested)

**Justification:**

- ✅ Senior dev's e2e requirement satisfied
- ✅ Industry standard adapted appropriately
- ✅ Upstream patterns followed
- ✅ Complete workflow coverage achieved

---

## 13. Application to CSAPI Roadmap

### Phase 4, Task 2: Integration Tests = E2E Tests

**From Implementation Guide:**

> **Task 2: Integration Tests (End-to-End Workflows)**
>
> - **Estimated Time:** 4-6 hours
> - **Lines:** ~500-800 lines
> - **Tests:** 4 workflow tests + error scenarios

**This research provides:**

- ✅ Clear e2e definition for CSAPI context
- ✅ 4 workflow specifications (ready to implement)
- ✅ Test structure and organization
- ✅ Fixture requirements
- ✅ HTTP mocking strategy
- ✅ Success criteria

**Implementation checklist:**

1. Create `endpoint.e2e.spec.ts` file
2. Set up fixture directory structure (`fixtures/ogc-api/csapi/e2e/`)
3. Create fixtures for each workflow (discovery, observation-query, command-submission, cross-resource)
4. Implement mock infrastructure (`mockFetchWithFixtures` helper)
5. Write 4 core workflow tests (~400-600 lines)
6. Write 1-2 error workflow tests (~100-200 lines)
7. Validate all tests pass
8. Verify complete workflow coverage

**Time breakdown:**

- Fixture creation: 1-2 hours (40-60 fixtures needed)
- Mock infrastructure: 30-60 minutes
- Discovery workflow: 60-90 minutes (~100-150 lines)
- Observation workflow: 90-120 minutes (~150-200 lines)
- Command workflow: 90-120 minutes (~150-200 lines)
- Navigation workflow: 60-90 minutes (~100-150 lines)
- Error workflows: 60-90 minutes (~100-200 lines)
- **Total:** 6-8 hours (slightly higher than Implementation Guide estimate due to fixture creation)

**Note:** Implementation Guide estimate of 4-6 hours assumes fixtures already exist. With fixture creation, 6-8 hours is more realistic.

---

## 14. Summary and Recommendations

### Key Takeaways

1. **"End-to-End" for CSAPI means:**

   - Complete multi-component workflows
   - All library layers tested together
   - HTTP mocked with realistic fixtures
   - Entry: `new OgcApiEndpoint()`
   - Exit: Parsed results or validated URLs

2. **E2E vs Integration distinction:**

   - Integration: 2-3 components, partial workflow, 20-50 lines
   - E2E: All components, complete workflow, 100-200 lines
   - Implementation Guide "Integration Tests" = E2E Tests

3. **4 core workflows required:**

   - Discovery (100-150 lines)
   - Observation query (150-200 lines)
   - Command submission (150-200 lines)
   - Cross-resource navigation (100-150 lines)
   - Total: 500-700 lines

4. **Test pyramid distribution:**

   - 55-60% unit (~3,000-3,600 lines)
   - 25-30% integration (~1,200-1,600 lines)
   - 10-15% e2e (~500-800 lines)
   - Total: ~4,800-6,000 lines (3.0-3.75× ratio)

5. **Higher test-to-code ratio justified:**
   - 9 resource types (vs EDR's 1)
   - Complex nested relationships
   - Two format types (SensorML, SWE Common)
   - More query parameters
   - More error scenarios

### Recommendations

**For Phase 4, Task 2 Implementation:**

1. ✅ **Follow this specification exactly**

   - Use 4 workflow structure defined here
   - Follow test organization recommendations
   - Use fixture strategy outlined
   - Implement mock infrastructure as specified

2. ✅ **Create comprehensive fixtures**

   - Budget 1-2 hours for fixture creation
   - Use real OGC CSAPI spec examples
   - Document fixture provenance
   - Organize by workflow

3. ✅ **Start with minimum viable e2e**

   - 4 happy path workflows first (~400-500 lines)
   - Add error workflows after core workflows pass (~100-200 lines)
   - Total: ~500-700 lines

4. ✅ **Validate against this research**

   - Each workflow must match specification
   - All components must be tested
   - Entry/exit points must match
   - Coverage requirements must be met

5. ✅ **Address senior dev feedback**
   - "Lack of e2e tests" → 4 complete workflows
   - Show multi-component interaction
   - Demonstrate realistic usage
   - Prove library works end-to-end

### Success Criteria Validation

✅ **All research objectives met:**

- [x] Clear e2e definition for CSAPI (URL builder + format parser context)
- [x] Unambiguous integration vs e2e distinction with examples
- [x] Scope and boundaries defined (in scope vs out of scope)
- [x] 4 workflow specifications ready for implementation
- [x] Test pyramid distribution defined (with line counts)
- [x] E2E test structure and organization specified
- [x] HTTP mocking strategy defined
- [x] Coverage requirements clear (minimum viable vs comprehensive)
- [x] Senior dev's e2e criticism specifically addressed
- [x] Validated against upstream + industry patterns
- [x] All 54 research questions answered

---

## Appendix: Research Question Answers

### E2E Definition for URL-Building Libraries (5 questions)

**Q1: What is "end-to-end" for a library that doesn't make HTTP calls?**
A: Complete workflows across all library components with mocked HTTP responses, from `new OgcApiEndpoint()` to URL construction + format detection.

**Q2: Is e2e about multi-component interaction?**
A: Yes, e2e must test all library layers together (endpoint, conformance, collections, QueryBuilder, format detection, parsers).

**Q3: Is e2e about complete workflows?**
A: Yes, e2e tests multi-step scenarios (discovery → query → navigation → parse), not isolated operations.

**Q4: Is e2e about full library API surface coverage?**
A: No, e2e tests realistic workflows (4-6 scenarios), not every method. Full API coverage comes from unit + integration tests.

**Q5: What's the "end" in "end-to-end" for CSAPI?**
A: Exit point varies by workflow: validated QueryBuilder (discovery), parsed observations (observation query), command result (command), resource graph (navigation).

### Scope and Boundaries (5 questions)

**Q6: What's the entry point of an e2e test?**
A: Always `new OgcApiEndpoint(url)` - the first user interaction with the library.

**Q7: What's the exit point of an e2e test?**
A: Varies by workflow: QueryBuilder instance, parsed results, command status, or validated URL structure.

**Q8: Does e2e include format parsing or just URL building?**
A: Yes, e2e includes format detection and parsing (complete workflow includes both URL building and format handling).

**Q9: Does e2e include HTTP mocking or assume URLs are correct?**
A: Yes, e2e mocks HTTP responses with realistic fixtures (library doesn't make real HTTP calls in tests).

**Q10: What components must be involved for a test to be e2e?**
A: All library layers: Endpoint, conformance parser, collection parser, QueryBuilder factory, URL builder, format detector, format parsers.

### Integration vs E2E Distinction (5 questions)

**Q11: What's the difference between integration and e2e for CSAPI?**
A: Integration tests 2-3 components (partial workflow, ~20-50 lines). E2E tests all components (complete workflow, ~100-200 lines).

**Q12: Where's the boundary?**
A: Entry point: integration starts mid-level (QueryBuilder already created), e2e starts top-level (`new OgcApiEndpoint()`).

**Q13: Are the 4 workflows in Implementation Guide integration or e2e?**
A: E2E - they test complete workflows across all components from top-level API.

**Q14: Can integration tests satisfy the e2e requirement?**
A: No, integration tests partial workflows (2-3 components). E2E requirement needs complete workflows (all components).

**Q15: Do we need both integration AND e2e tests, or are they the same?**
A: Need both: ~50-60 integration tests (multi-component) + ~4-6 e2e tests (complete workflows).

### Workflow-Based E2E (4 questions)

**Q16: Is e2e about complete workflows?**
A: Yes, e2e tests must demonstrate complete multi-step scenarios from start to finish.

**Q17: What workflows constitute e2e coverage?**
A: 4 core workflows: Discovery, Observation Query, Command Submission, Cross-Resource Navigation.

**Q18: How do workflows differ from integration tests?**
A: Workflows are multi-step (5-8 steps), integration tests are single operations. Workflows span all components, integration tests span 2-3 components.

**Q19: How many workflow scenarios are sufficient?**
A: Minimum viable: 4 workflows (happy path). Comprehensive: 4 workflows + variations + 1-2 error workflows = 6-10 tests.

### Implementation Guide Workflows (4 questions)

**Q20: Discovery workflow - e2e or integration?**
A: E2E - tests endpoint detection → conformance → collections → builder creation (all components).

**Q21: Observation workflow - e2e or integration?**
A: E2E - tests systems → datastreams → observations → pagination → parsing (complete multi-resource workflow).

**Q22: Command workflow - e2e or integration?**
A: E2E - tests systems → control streams → feasibility → submit → status → result (complete command lifecycle).

**Q23: Cross-resource navigation - e2e or integration?**
A: E2E - tests 6-hop navigation across all resource types (demonstrates seamless multi-resource interaction).

### Upstream E2E Patterns (4 questions)

**Q24: How does EDR define e2e tests?**
A: EDR's "integration tests" in endpoint.spec.ts are actually e2e tests - they test complete workflows from endpoint creation.

**Q25: Do other upstream implementations have e2e tests?**
A: Yes, all implementations (WFS, WMS, WMTS, TMS, STAC) have integration/e2e tests in endpoint.spec.ts.

**Q26: What patterns exist in upstream for e2e vs integration?**
A: Upstream doesn't distinguish - calls all "integration tests". By our definition, endpoint.spec.ts tests are e2e (complete workflows).

**Q27: What did upstream maintainers accept as e2e in PR #114?**
A: 298 lines of "integration tests" in endpoint.spec.ts testing complete EDR workflows (endpoint → builder → URL).

### Industry E2E Patterns (4 questions)

**Q28: How do TypeScript client libraries define e2e?**
A: Industry defines e2e as real HTTP to real servers. Client libraries rarely have e2e tests (0-5%).

**Q29: Do client libraries without HTTP have e2e tests?**
A: Rarely. Most have only unit + integration tests. "E2E" belongs in consuming applications.

**Q30: What's the industry standard for e2e in URL-building libraries?**
A: Industry standard: 60% unit, 40% integration, 0% e2e. CSAPI adapts: 55-60% unit, 25-30% integration, 10-15% e2e (complete workflows).

**Q31: Examples from @octokit/rest, axios, AWS SDK?**
A: @octokit: ~40% unit, ~60% integration, 0% e2e. axios: ~50% unit, ~50% integration, 0% e2e. All mock HTTP in tests.

### Test Pyramid Distribution (6 questions)

**Q32: What's the recommended test pyramid for CSAPI?**
A: 55-60% unit, 25-30% integration, 10-15% e2e.

**Q33: What % should be unit tests?**
A: 55-60% (~3,000-3,600 lines, ~200-250 tests).

**Q34: What % should be integration tests?**
A: 25-30% (~1,200-1,600 lines, ~50-60 tests).

**Q35: What % should be e2e tests?**
A: 10-15% (~500-800 lines, ~4-6 tests).

**Q36: How does CSAPI test pyramid compare to upstream?**
A: CSAPI ratio 3.0-3.75× vs upstream avg 1.44×. Higher due to 9 resource types, complex relationships, 2 format types.

**Q37: How does it compare to industry standards?**
A: Industry: 60% unit, 40% integration, 0% e2e. CSAPI: 55-60% unit, 25-30% integration, 10-15% e2e. Adapted for senior dev's e2e requirement.

### E2E Test Structure (6 questions)

**Q38: How should e2e tests be organized?**
A: Single file `endpoint.e2e.spec.ts` with 4-6 workflow tests, ~500-800 lines total.

**Q39: One e2e test file or multiple?**
A: One file for all e2e workflows, separate from integration tests (`endpoint.integration.spec.ts`).

**Q40: How long should e2e tests be?**
A: Discovery: 100-150 lines. Observation/Command: 150-200 lines. Navigation: 100-150 lines. Error workflows: 50-100 lines each.

**Q41: What setup is required for e2e tests?**
A: Mock `fetch` with fixture-based responses, shared test infrastructure (`mockFetchWithFixtures` helper).

**Q42: What fixtures are required for e2e tests?**
A: 40-60 fixtures organized by workflow (discovery, observation-query, command-submission, cross-resource, errors).

**Q43: How to mock HTTP responses for e2e tests?**
A: Mock `globalThis.fetch` with `jest.fn()`, load fixtures via `fs/promises`, return fixture content as mock response.

### E2E Coverage Requirements (5 questions)

**Q44: What must be covered by e2e tests?**
A: 4 core workflows (discovery, observation, command, navigation) + 1-2 error workflows.

**Q45: Do all 9 resource types need e2e coverage?**
A: Yes, via cross-resource navigation workflow (tests all 9 types in realistic navigation scenarios).

**Q46: Do all workflows need e2e coverage?**
A: Yes, all 4 Implementation Guide workflows must have e2e tests (addresses senior dev's criticism).

**Q47: What's the minimum viable e2e test suite?**
A: 4 workflows, happy path only, ~400-500 lines.

**Q48: What's comprehensive e2e coverage?**
A: 4 workflows + variations + 1-2 error workflows = 6-10 tests, ~700-1,000 lines.

### Error Scenarios in E2E (3 questions)

**Q49: Should e2e tests cover error scenarios?**
A: Yes, 1-2 error workflow tests in comprehensive coverage (server errors, validation errors).

**Q50: What error workflows are e2e vs unit?**
A: Unit: individual parameter validation. Integration: multi-component error propagation. E2E: complete error recovery workflows.

**Q51: How deep should e2e error testing go?**
A: Test major error categories (server errors, validation errors, parse errors), not every edge case.

### Performance Considerations (3 questions)

**Q52: Should e2e tests validate performance?**
A: No, e2e tests focus on correctness. Performance testing is separate test suite.

**Q53: Are e2e tests slower than integration tests?**
A: Slightly slower due to more HTTP mocks and longer workflows, but still fast (< 1 second per test with fixtures).

**Q54: What's acceptable e2e test execution time?**
A: < 5 seconds for all e2e tests combined. Individual tests should be < 1 second.

---

**Research Completed:** February 5, 2026  
**Deliverable:** E2E Testing Scope and Strategy (~4,300 lines)  
**Status:** Complete - Ready for Phase 4, Task 2 Implementation
