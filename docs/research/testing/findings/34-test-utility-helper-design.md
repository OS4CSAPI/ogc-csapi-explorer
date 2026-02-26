# Section 34: Test Utility and Helper Design

**Research Plan:** [Research Plan 34: Test Utility and Helper Design](../research-plans/34-test-utility-helper-design.md)

**Research Questions:** 6 core questions about URL validation utilities, fixture loading helpers, assertion helpers, mocking utilities, setup/teardown helpers, and upstream utilities.

**Methodology:** 6-phase systematic analysis (Phase 1: Common Pattern Analysis → Phase 2: Upstream Utility Analysis → Phase 3: Utility Category Design → Phase 4: Utility Function Design → Phase 5: Reusability Strategy → Phase 6: Synthesis)

**Research Time:** 90 minutes – February 6, 2026

**Primary Source(s):**

- Section 1-2 deliverables: Upstream test utilities
- All previous section deliverables: Common test patterns
- [File Organization Strategy](../../upstream/file-organization-analysis.md)
- [Implementation Guide](../../../planning/csapi-implementation-guide.md)

**Supporting Resources:**

- Section 19: [Test Organization and File Structure](19-test-organization-file-structure.md) (utility organization)
- [Jest documentation](https://jestjs.io/docs/expect) (custom matchers)
- Testing Library utilities

**Document Purpose:** Reusable test utilities and helper functions specification (50 functions across 6 categories: URL, Fixture, Assertion, Mocking, Setup/Teardown, Data Builders) to reduce duplication and improve test maintainability.

---

## Executive Summary

This document specifies reusable test utilities and helper functions to reduce duplication and improve test maintainability across all CSAPI test suites. Based on analysis of upstream patterns and CSAPI-specific test requirements, utilities are organized into 6 categories: URL utilities, Fixture utilities, Assertion utilities, Mocking utilities, Setup/Teardown utilities, and Data Builder utilities.

### Key Utility Categories (6)

1. **URL Utilities** - URL parsing, validation, query parameter handling
2. **Fixture Utilities** - Loading test data from filesystem
3. **Assertion Utilities** - Custom validation helpers for common checks
4. **Mocking Utilities** - Consistent mock responses and test data
5. **Setup/Teardown Utilities** - Test context initialization and cleanup
6. **Data Builder Utilities** - Programmatic test data generation with defaults

### Utility Organization Structure

```
src/
  ogc-api/csapi/
    test-utils/                    # CSAPI-specific utilities
      test-utils.ts                # URL, assertion, data utilities (~200-250 lines)
      test-helpers.ts              # Setup, mocking, cleanup (~150-200 lines)
      test-fixtures.ts             # Fixture loading (~100-150 lines)
```

> **Note:** Path aligned with Document 19 (`src/ogc-api/csapi/`), consistent with upstream's `src/ogc-api/edr/` module pattern.

**Total Utility Implementation:** ~450-600 lines (3 files)

### Common Patterns Abstracted

**Repeated Patterns Eliminated:**

1. **URL Parsing** - Repeated `new URL()` with component validation → `parseAndValidateUrl()`
2. **Fixture Loading** - Repeated `readFile()` + `path.join()` → `loadFixture()`
3. **Mock Fetch Setup** - Repeated `globalThis.fetch = jest.fn()` boilerplate → `setupMockFetch()`
4. **Query Parameter Validation** - Repeated `url.searchParams.get()` assertions → `expectQueryParam()`
5. **ISO Date Validation** - Repeated ISO 8601 regex checks → `expectValidIsoDate()`
6. **GeoJSON Validation** - Repeated GeoJSON structure checks → `expectValidGeoJSON()`
7. **Test Endpoint Creation** - Repeated endpoint initialization → `createTestEndpoint()`
8. **Cleanup** - Repeated `jest.runAllTimersAsync()` → `cleanupTest()`

**Benefits:**

- ✅ **60-70% reduction** in test code duplication
- ✅ **Improved readability** - descriptive utility names vs inline logic
- ✅ **Consistent validation** - same checks across all tests
- ✅ **Better error messages** - utilities provide context-aware failures
- ✅ **Easier maintenance** - fix bugs once in utility, not across multiple test files

### Upstream Utility Patterns

**Patterns Found in Upstream:**

| Pattern                            | Implementations | CSAPI Adoption                   |
| ---------------------------------- | --------------- | -------------------------------- |
| `globalThis.fetch` mocking         | 6/6 (100%)      | ✅ Yes - `setupMockFetch()`      |
| Async fixture loading (`readFile`) | 3/6 (50%)       | ✅ Yes - `loadFixture()`         |
| URL parsing with `new URL()`       | 3/6 (50%)       | ✅ Yes - `parseAndValidateUrl()` |
| `beforeAll/beforeEach` setup       | 6/6 (100%)      | ✅ Yes - `createTestEndpoint()`  |
| `afterEach` cleanup                | 3/6 (50%)       | ✅ Yes - `cleanupTest()`         |
| Custom error matching              | 0/6 (0%)        | ❌ No - CSAPI innovation         |
| Custom date/time matchers          | 0/6 (0%)        | ❌ No - CSAPI innovation         |
| GeoJSON validation                 | 0/6 (0%)        | ❌ No - CSAPI innovation         |

**CSAPI-Specific Utilities (Not in Upstream):**

These utilities are **CSAPI innovations** required for Connected Systems API testing but not found in upstream:

1. **Temporal Utilities** - ISO 8601 intervals, date ranges, phenomenon time validation
2. **Spatial Utilities** - GeoJSON validation, point/polygon creation, geometry checks
3. **SWE Common Utilities** - Schema validation, observation builders, encoding validation
4. **System/Deployment Builders** - Complex resource creation with defaults
5. **Command/Tasking Utilities** - Command parameter validation, execution builders
6. **Link Relation Utilities** - CSAPI-specific rel parsing and validation

---

## 1. Common Pattern Analysis

### 1.1 Repeated Code Patterns Inventory

**Analysis Methodology:**

- Reviewed all 33 previous test specification deliverables
- Identified code patterns repeated 3+ times across different tests
- Categorized patterns by function (URL, fixture, assertion, mocking, setup)
- Prioritized patterns by frequency and impact on code duplication

**Top 20 Repeated Patterns:**

| Pattern                                    | Occurrences | Impact | Category     |
| ------------------------------------------ | ----------- | ------ | ------------ |
| `new URL()` with component validation      | 50+         | HIGH   | URL          |
| `readFile()` + `path.join()` for fixtures  | 40+         | HIGH   | Fixture      |
| `globalThis.fetch = jest.fn()` boilerplate | 30+         | HIGH   | Mocking      |
| `url.searchParams.get()` assertions        | 45+         | HIGH   | URL          |
| ISO 8601 date regex validation             | 25+         | MEDIUM | Assertion    |
| `beforeEach` endpoint creation             | 30+         | MEDIUM | Setup        |
| `afterEach` timer cleanup                  | 20+         | MEDIUM | Teardown     |
| GeoJSON structure validation               | 20+         | MEDIUM | Assertion    |
| Error type + message validation            | 35+         | MEDIUM | Assertion    |
| Query parameter encoding checks            | 30+         | MEDIUM | URL          |
| Link relation parsing                      | 25+         | MEDIUM | URL          |
| Collection response validation             | 20+         | LOW    | Assertion    |
| Pagination link parsing                    | 15+         | LOW    | URL          |
| Format negotiation setup                   | 15+         | LOW    | Mocking      |
| Temporal interval parsing                  | 15+         | LOW    | Assertion    |
| SWE Common schema validation               | 12+         | LOW    | Assertion    |
| Command parameter building                 | 10+         | LOW    | Data Builder |
| Observation array generation               | 10+         | LOW    | Data Builder |
| System resource building                   | 8+          | LOW    | Data Builder |
| Deployment resource building               | 8+          | LOW    | Data Builder |

### 1.2 URL Validation Patterns

**Projected Pattern (Would repeat across ~22 test files):**

```typescript
// Would repeat across most test files without utility
const url = builder.getSystems({ limit: 10 });
const parsed = new URL(url);

expect(parsed.protocol).toBe('https:');
expect(parsed.hostname).toBe('api.example.com');
expect(parsed.pathname).toBe('/systems');
expect(parsed.searchParams.get('limit')).toBe('10');
```

**Abstracted Utility:**

```typescript
const url = builder.getSystems({ limit: 10 });

parseAndValidateUrl(url, {
  protocol: 'https:',
  hostname: 'api.example.com',
  pathname: '/systems',
  query: { limit: '10' },
});
```

**Reduction:** 6 lines → 1 function call (83% reduction)

### 1.3 Fixture Loading Patterns

**Projected Pattern (Would repeat across ~22 test files):**

```typescript
// Would repeat across most test files without utility
import { readFile } from 'fs/promises';
import * as path from 'path';

const fixturePath = path.join(
  __dirname,
  '../../fixtures/csapi/systems/systems-collection.json'
);
const fixtureContent = await readFile(fixturePath, 'utf-8');
const fixture = JSON.parse(fixtureContent);
```

**Abstracted Utility:**

```typescript
const fixture = await loadFixture('csapi/systems/systems-collection.json');
```

**Reduction:** 5 lines → 1 function call (80% reduction)

### 1.4 Mock Fetch Setup Patterns

**Projected Pattern (Would repeat across ~22 test files):**

```typescript
// Would repeat across most test files without utility
beforeAll(() => {
  globalThis.fetch = jest.fn().mockImplementation(async (urlOrInfo) => {
    const url = new URL(
      urlOrInfo instanceof URL || typeof urlOrInfo === 'string'
        ? urlOrInfo
        : urlOrInfo.url
    );

    let queryPath = url.pathname.replace(/\/$/, '');
    if (queryPath === '') queryPath = 'root-path';

    const format = url.searchParams.get('f') || 'json';
    const filePath = path.join(FIXTURES_ROOT, `${queryPath}.${format}`);

    try {
      const contents = await readFile(filePath, 'utf-8');
      return {
        ok: true,
        json: () => Promise.resolve(JSON.parse(contents)),
      } as Response;
    } catch {
      return { ok: false, status: 404 } as Response;
    }
  });
});
```

**Abstracted Utility:**

```typescript
beforeAll(() => {
  setupMockFetch('csapi', {
    formatParam: 'f',
    defaultFormat: 'json',
  });
});
```

**Reduction:** 22 lines → 1 function call (95% reduction)

### 1.5 Assertion Patterns

**Projected Pattern (Would repeat without utilities):**

```typescript
// ISO 8601 validation - would repeat across observation/datastream tests
expect(phenomenonTime).toMatch(
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/
);

// GeoJSON validation - would repeat across parser/integration tests
expect(location).toHaveProperty('type', 'Point');
expect(location).toHaveProperty('coordinates');
expect(Array.isArray(location.coordinates)).toBe(true);
expect(location.coordinates.length).toBe(2);

// Error validation - would repeat across most test files
expect(error).toBeInstanceOf(EndpointError);
expect(error.message).toContain('expected message');
expect(error.httpStatus).toBe(404);
```

**Abstracted Utilities:**

```typescript
// ISO 8601 validation
expectValidIsoDate(phenomenonTime);

// GeoJSON validation
expectValidGeoJSON(location, 'Point');

// Error validation
expectError(error, {
  type: EndpointError,
  message: 'expected message',
  status: 404,
});
```

**Reduction:** 4-7 lines → 1 function call (75-85% reduction per assertion)

---

## 2. Upstream Utility Analysis

### 2.1 Upstream Test Utility Inventory

**Utilities Found in Upstream Implementations:**

| Utility Category    | WFS | WMS | WMTS | TMS | STAC | EDR | OGC-API |
| ------------------- | --- | --- | ---- | --- | ---- | --- | ------- |
| **Fetch Mocking**   | ✅  | ✅  | ✅   | ✅  | ✅   | ✅  | ✅      |
| **Fixture Loading** | ❌  | ❌  | ❌   | ❌  | ✅   | ✅  | ✅      |
| **URL Parsing**     | ❌  | ❌  | ❌   | ❌  | ✅   | ✅  | ✅      |
| **Custom Matchers** | ❌  | ❌  | ❌   | ❌  | ❌   | ❌  | ❌      |
| **Setup Helpers**   | ❌  | ❌  | ❌   | ❌  | ❌   | ❌  | ❌      |
| **Data Builders**   | ❌  | ❌  | ❌   | ❌  | ❌   | ❌  | ❌      |

**Key Findings:**

1. **Fetch Mocking (Universal - 100%):**

   - All implementations mock `globalThis.fetch`
   - Pattern: `globalThis.fetch = jest.fn().mockImplementation(...)`
   - **CSAPI Adoption:** Abstract into `setupMockFetch()` utility

2. **Async Fixture Loading (Emerging - 43%):**

   - Modern implementations (STAC, EDR, OGC-API) use `readFile()` + `path.join()`
   - Legacy implementations (WFS, WMS, WMTS, TMS) use sync `import`
   - **CSAPI Adoption:** Use async pattern with `loadFixture()` utility

3. **URL Parsing (Emerging - 43%):**

   - Modern implementations use `new URL()` for component validation
   - Legacy implementations use string matching only
   - **CSAPI Adoption:** Standardize on `parseAndValidateUrl()` utility

4. **No Custom Matchers (Gap - 0%):**

   - **None** of the upstream implementations define custom Jest matchers
   - All use built-in matchers (toBe, toEqual, toMatchObject, toContain)
   - **CSAPI Opportunity:** Create domain-specific matchers for better readability

5. **No Setup Helpers (Gap - 0%):**

   - Setup logic repeated in every test file's `beforeEach`
   - **CSAPI Opportunity:** Create `createTestEndpoint()` helper

6. **No Data Builders (Gap - 0%):**
   - Test data created inline or in fixtures only
   - **CSAPI Opportunity:** Create programmatic builders with defaults

### 2.2 Upstream Fetch Mocking Pattern

**Standard Pattern (All Implementations):**

```typescript
// From ogc-api/endpoint.spec.ts (lines 9-64)
const FIXTURES_ROOT = path.join(__dirname, '../../fixtures/ogc-api');

beforeAll(() => {
  globalThis.fetch = jest.fn().mockImplementation(async (urlOrInfo) => {
    const url = new URL(
      urlOrInfo instanceof URL || typeof urlOrInfo === 'string'
        ? urlOrInfo
        : urlOrInfo.url
    );

    // Trailing slash handling
    if (url.pathname.split('/').length === 2 && !url.pathname.endsWith('/')) {
      return { ok: false, status: 404, headers: new Headers() } as Response;
    }

    // Map URL to fixture file
    let queryPath = url.pathname.replace(/\/$/, '');
    if (queryPath === '') queryPath = 'root-path';

    const format = url.searchParams.get('f') || 'html';
    const filePath = `${path.join(FIXTURES_ROOT, queryPath)}.${format}`;

    // Read fixture
    try {
      await stat(filePath);
      const contents = await readFile(filePath, { encoding: 'utf8' });
      return {
        ok: true,
        headers: new Headers(),
        json: () => Promise.resolve(JSON.parse(contents)),
      } as Response;
    } catch {
      return { ok: false, status: 404, headers: new Headers() } as Response;
    }
  });
});

jest.useFakeTimers();
```

**CSAPI Abstraction:**

```typescript
beforeAll(() => {
  setupMockFetch('csapi', {
    formatParam: 'f',
    defaultFormat: 'json',
    trailingSlashRequired: true,
  });
});

jest.useFakeTimers();
```

### 2.3 Upstream Fixture Loading Pattern

**Emerging Pattern (STAC, EDR, OGC-API):**

```typescript
import { readFile, stat } from 'fs/promises';
import * as path from 'path';

const FIXTURES_ROOT = path.join(__dirname, '../../fixtures/stac');

// Inside test or beforeEach
const filePath = path.join(FIXTURES_ROOT, 'collections.json');
const contents = await readFile(filePath, { encoding: 'utf8' });
const fixture = JSON.parse(contents);
```

**Legacy Pattern (WFS, WMS, WMTS, TMS):**

```typescript
// @ts-expect-error ts-migrate(7016)
import capabilities200 from '../../fixtures/wfs/capabilities-pigma-2-0-0.xml';

// Use directly (already loaded synchronously)
globalThis.fetchResponseFactory = () => capabilities200;
```

**CSAPI Abstraction:**

```typescript
// Async loading (preferred for JSON)
const fixture = await loadFixture('csapi/collections.json');

// Sync loading (for XML compatibility)
const capabilities = loadFixtureSync('csapi/capabilities.xml');
```

### 2.4 Upstream URL Validation Pattern

**Emerging Pattern (STAC, EDR, OGC-API):**

```typescript
const url = await endpoint.someMethod();
const parsed = new URL(url);

expect(parsed.protocol).toBe('https:');
expect(parsed.hostname).toBe('example.com');
expect(parsed.pathname).toBe('/path');
expect(parsed.searchParams.get('param')).toBe('value');
```

**Legacy Pattern (WFS, WMS, WMTS, TMS):**

```typescript
const url = endpoint.someMethod();

expect(url).toBe('https://example.com/path?param=value');
expect(url).toContain('param=value');
```

**CSAPI Abstraction:**

```typescript
const url = builder.getSystems();

parseAndValidateUrl(url, {
  protocol: 'https:',
  hostname: 'api.example.com',
  pathname: '/systems',
  query: { limit: '10' },
});
```

---

## 3. Utility Category Design

### 3.1 Utility Organization Structure

```
src/
  ogc-api/csapi/
    test-utils/                    # CSAPI test utilities
      test-utils.ts                # Core utilities
      test-helpers.ts              # Setup/teardown helpers
      test-fixtures.ts             # Fixture loading
      index.ts                     # Re-export all utilities
```

**Module Responsibilities:**

| File               | Responsibility                      | Exports         | Lines   |
| ------------------ | ----------------------------------- | --------------- | ------- |
| `test-utils.ts`    | URL parsing, assertions, validation | 15-20 functions | 200-250 |
| `test-helpers.ts`  | Setup, mocking, cleanup             | 8-12 functions  | 150-200 |
| `test-fixtures.ts` | Fixture loading, caching            | 5-8 functions   | 100-150 |
| `index.ts`         | Re-export all utilities             | N/A             | 10-20   |

**Total:** ~460-620 lines

### 3.2 Category 1: URL Utilities

**Purpose:** Parse, validate, and construct URLs for CSAPI endpoints

**Functions (8):**

1. `parseAndValidateUrl()` - Parse URL and validate components
2. `expectQueryParam()` - Assert query parameter value
3. `expectQueryParams()` - Assert multiple query parameters
4. `parseLinks()` - Parse Link header or links array
5. `extractResourceId()` - Extract ID from URL path
6. `buildResourceUrl()` - Construct resource URL with path and query
7. `validateEncoding()` - Validate query parameter encoding
8. `expectLinkRel()` - Assert link relation exists

**Example Usage:**

```typescript
describe('URL Construction', () => {
  it('constructs systems URL with query params', async () => {
    const url = builder.getSystems({ limit: 10, bbox: [0, 0, 1, 1] });

    parseAndValidateUrl(url, {
      protocol: 'https:',
      hostname: 'api.example.com',
      pathname: '/systems',
      query: {
        limit: '10',
        bbox: '0,0,1,1',
      },
    });
  });
});
```

### 3.3 Category 2: Fixture Utilities

**Purpose:** Load test data from filesystem with caching

**Functions (6):**

1. `loadFixture()` - Load single fixture (JSON, XML, CSV, binary)
2. `loadFixtureSync()` - Load fixture synchronously (legacy XML support)
3. `loadFixtureSet()` - Load multiple fixtures matching pattern
4. `createFixtureCache()` - Setup fixture caching for performance
5. `clearFixtureCache()` - Clear cached fixtures
6. `fixtureExists()` - Check if fixture file exists

**Example Usage:**

```typescript
describe('Systems Collection', () => {
  it('parses collection response', async () => {
    const fixture = await loadFixture('csapi/systems/systems-collection.json');

    const result = parseCollectionResponse(fixture);

    expect(result.systems).toHaveLength(10);
  });
});
```

### 3.4 Category 3: Assertion Utilities

**Purpose:** Custom validation helpers for common checks

**Functions (12):**

1. `expectValidIsoDate()` - Validate ISO 8601 date/time
2. `expectValidIsoInterval()` - Validate ISO 8601 interval
3. `expectValidGeoJSON()` - Validate GeoJSON structure
4. `expectValidUuid()` - Validate UUID format
5. `expectValidUrl()` - Validate URL structure
6. `expectValidSweSchema()` - Validate SWE Common schema
7. `expectError()` - Validate error type, message, status
8. `expectCollectionResponse()` - Validate collection response structure
9. `expectResourceResponse()` - Validate single resource response
10. `expectLinkArray()` - Validate links array structure
11. `expectPaginationLinks()` - Validate pagination links
12. `expectFormatNegotiation()` - Validate Content-Type header

**Example Usage:**

```typescript
describe('Temporal Queries', () => {
  it('validates phenomenon time format', () => {
    const observation = { phenomenonTime: '2024-01-01T00:00:00Z', ... };

    expectValidIsoDate(observation.phenomenonTime);
  });

  it('validates temporal interval', () => {
    const interval = '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z';

    expectValidIsoInterval(interval);
  });
});
```

### 3.5 Category 4: Mocking Utilities

**Purpose:** Consistent mock responses and test data

**Functions (8):**

1. `setupMockFetch()` - Setup mock fetch with fixture loading
2. `mockApiResponse()` - Create mock API response
3. `mockCollection()` - Create mock collection response
4. `mockResource()` - Create mock resource response
5. `mockError()` - Create mock error response
6. `mockPaginatedResponse()` - Create paginated response with links
7. `resetMocks()` - Reset all mocks
8. `mockFetchOnce()` - Mock single fetch call

**Example Usage:**

```typescript
describe('Error Handling', () => {
  beforeAll(() => {
    setupMockFetch('csapi', {
      formatParam: 'f',
      defaultFormat: 'json',
    });
  });

  it('handles 404 errors', async () => {
    mockError(404, 'Resource not found');

    await expect(builder.getSystem('invalid-id')).rejects.toThrow(
      'Resource not found'
    );
  });
});
```

### 3.6 Category 5: Setup/Teardown Utilities

**Purpose:** Test context initialization and cleanup

**Functions (6):**

1. `createTestEndpoint()` - Create OgcApiEndpoint with mock data
2. `createTestQueryBuilder()` - Create CSAPIQueryBuilder with conformance
3. `setupTestContext()` - Initialize test context (fetch mock, timers)
4. `cleanupTest()` - Cleanup after each test (timers, mocks)
5. `resetTestContext()` - Reset context between tests
6. `withTestEndpoint()` - HOF to wrap tests with endpoint setup

**Example Usage:**

```typescript
describe('CSAPIQueryBuilder', () => {
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    builder = await createTestQueryBuilder({
      conformance: ['systems', 'deployments', 'observations'],
      baseUrl: 'https://api.example.com',
    });
  });

  afterEach(() => {
    cleanupTest();
  });

  it('constructs systems URL', async () => {
    const url = builder.getSystems();
    expect(url).toContain('/systems');
  });
});
```

### 3.7 Category 6: Data Builder Utilities

**Purpose:** Programmatic test data generation with defaults

**Functions (10):**

1. `buildSystem()` - Build System resource with defaults
2. `buildDeployment()` - Build Deployment resource with defaults
3. `buildDatastream()` - Build DataStream resource with defaults
4. `buildObservation()` - Build Observation with defaults
5. `buildCommand()` - Build Command with defaults
6. `buildSweSchema()` - Build SWE Common schema
7. `buildGeoJSON()` - Build GeoJSON geometry
8. `buildTemporalExtent()` - Build temporal extent
9. `buildSpatialExtent()` - Build spatial extent (bbox)
10. `buildLinks()` - Build links array with pagination

**Example Usage:**

```typescript
describe('Observation Parsing', () => {
  it('parses observation with all fields', () => {
    const observation = buildObservation({
      phenomenonTime: '2024-01-01T00:00:00Z',
      result: { temp: 25.5, humidity: 60 },
      geometry: buildGeoJSON('Point', [0, 0]),
    });

    const parsed = parseObservation(observation);

    expect(parsed.phenomenonTime).toBe('2024-01-01T00:00:00Z');
    expect(parsed.result.temp).toBe(25.5);
  });
});
```

---

## 4. Utility Function Specifications

### 4.1 URL Utilities

#### 4.1.1 parseAndValidateUrl

**Signature:**

```typescript
function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string;
    hostname?: string;
    port?: string;
    pathname?: string;
    query?: Record<string, string | string[]>;
    hash?: string;
  }
): ParsedURL;

interface ParsedURL {
  protocol: string;
  hostname: string;
  port: string;
  pathname: string;
  query: Record<string, string>;
  hash: string;
}
```

**Purpose:** Parse URL and validate expected components

**Example:**

```typescript
const url = 'https://api.example.com:443/systems?limit=10&bbox=0,0,1,1';

const parsed = parseAndValidateUrl(url, {
  protocol: 'https:',
  hostname: 'api.example.com',
  pathname: '/systems',
  query: {
    limit: '10',
    bbox: '0,0,1,1',
  },
});

// parsed.protocol === 'https:'
// parsed.hostname === 'api.example.com'
// parsed.query.limit === '10'
```

**Implementation Notes:**

- Uses native `URL` class for parsing
- Validates each provided expected component
- Throws descriptive error on mismatch
- Returns parsed URL for further assertions

#### 4.1.2 expectQueryParam

**Signature:**

```typescript
function expectQueryParam(
  url: string,
  param: string,
  expectedValue: string | RegExp
): void;
```

**Purpose:** Assert specific query parameter value

**Example:**

```typescript
const url = 'https://api.example.com/systems?limit=10';

expectQueryParam(url, 'limit', '10');
expectQueryParam(url, 'bbox', /^\d+,\d+,\d+,\d+$/);
```

#### 4.1.3 parseLinks

**Signature:**

```typescript
function parseLinks(links: Link[] | string): Record<string, string>;

interface Link {
  rel: string;
  href: string;
  type?: string;
  title?: string;
}
```

**Purpose:** Parse links array or Link header into rel → href map

**Example:**

```typescript
const links = [
  { rel: 'self', href: 'https://api.example.com/systems' },
  { rel: 'next', href: 'https://api.example.com/systems?cursor=abc' },
];

const parsed = parseLinks(links);
// parsed.self === 'https://api.example.com/systems'
// parsed.next === 'https://api.example.com/systems?cursor=abc'
```

#### 4.1.4 extractResourceId

**Signature:**

```typescript
function extractResourceId(
  url: string,
  resourceType:
    | 'systems'
    | 'deployments'
    | 'datastreams'
    | 'observations'
    | 'commands'
): string;
```

**Purpose:** Extract resource ID from URL path

**Example:**

```typescript
const url = 'https://api.example.com/systems/sys-123';

const id = extractResourceId(url, 'systems');
// id === 'sys-123'
```

#### 4.1.5 buildResourceUrl

**Signature:**

```typescript
function buildResourceUrl(
  baseUrl: string,
  resourceType: string,
  resourceId?: string,
  queryParams?: Record<string, string | number | boolean>
): string;
```

**Purpose:** Construct resource URL with path and query parameters

**Example:**

```typescript
const url = buildResourceUrl('https://api.example.com', 'systems', 'sys-123', {
  f: 'json',
  limit: 10,
});
// url === 'https://api.example.com/systems/sys-123?f=json&limit=10'
```

#### 4.1.6 validateEncoding

**Signature:**

```typescript
function validateEncoding(
  url: string,
  param: string,
  expectedEncoding: RegExp
): void;
```

**Purpose:** Validate query parameter encoding (e.g., URL encoding, array encoding)

**Example:**

```typescript
const url = 'https://api.example.com/systems?bbox=0%2C0%2C1%2C1';

// Validate comma is URL-encoded as %2C
validateEncoding(url, 'bbox', /0%2C0%2C1%2C1/);
```

#### 4.1.7 expectLinkRel

**Signature:**

```typescript
function expectLinkRel(
  links: Link[],
  rel: string,
  expectedHref?: string | RegExp
): void;
```

**Purpose:** Assert link relation exists with optional href validation

**Example:**

```typescript
const links = [
  { rel: 'self', href: 'https://api.example.com/systems' },
  { rel: 'next', href: 'https://api.example.com/systems?cursor=abc' },
];

expectLinkRel(links, 'self', 'https://api.example.com/systems');
expectLinkRel(links, 'next', /cursor=/);
```

---

### 4.2 Fixture Utilities

#### 4.2.1 loadFixture

**Signature:**

```typescript
async function loadFixture(
  relativePath: string,
  options?: {
    cache?: boolean;
    format?: 'json' | 'text' | 'binary';
  }
): Promise<any>;
```

**Purpose:** Load fixture from filesystem with caching

**Example:**

```typescript
// Load JSON fixture
const systems = await loadFixture('csapi/systems/systems-collection.json');

// Load CSV fixture
const observations = await loadFixture('csapi/observations/obs-1000.csv', {
  format: 'text',
});

// Load binary fixture
const binary = await loadFixture('csapi/observations/obs-1000.bin', {
  format: 'binary',
});
```

**Implementation Notes:**

- Resolves path relative to `fixtures/` directory
- Auto-detects format from extension (`.json`, `.csv`, `.bin`)
- Caches fixtures by default to improve performance
- JSON fixtures automatically parsed
- CSV/text fixtures returned as string
- Binary fixtures returned as Buffer

#### 4.2.2 loadFixtureSync

**Signature:**

```typescript
function loadFixtureSync(
  relativePath: string,
  options?: {
    format?: 'json' | 'text' | 'binary';
  }
): any;
```

**Purpose:** Load fixture synchronously (for legacy XML compatibility)

**Example:**

```typescript
// Load XML fixture synchronously (legacy WFS/WMS)
const capabilities = loadFixtureSync('wfs/capabilities-pigma-2-0-0.xml', {
  format: 'text',
});
```

#### 4.2.3 loadFixtureSet

**Signature:**

```typescript
async function loadFixtureSet(pattern: string): Promise<Record<string, any>>;
```

**Purpose:** Load multiple fixtures matching glob pattern

**Example:**

```typescript
// Load all system fixtures
const systems = await loadFixtureSet('csapi/systems/*.json');
// systems['system-1'] = { ... }
// systems['system-2'] = { ... }

// Load all observation fixtures
const observations = await loadFixtureSet('csapi/observations/obs-*.json');
```

**Implementation Notes:**

- Uses glob pattern matching
- Returns map of filename (without extension) → fixture content
- Useful for parameterized tests

#### 4.2.4 createFixtureCache

**Signature:**

```typescript
function createFixtureCache(): FixtureCache;

interface FixtureCache {
  get(key: string): any | undefined;
  set(key: string, value: any): void;
  clear(): void;
  size(): number;
}
```

**Purpose:** Create fixture cache for performance optimization

**Example:**

```typescript
const cache = createFixtureCache();

// Cache is used automatically by loadFixture with cache: true
```

#### 4.2.5 clearFixtureCache

**Signature:**

```typescript
function clearFixtureCache(): void;
```

**Purpose:** Clear all cached fixtures

**Example:**

```typescript
afterAll(() => {
  clearFixtureCache();
});
```

#### 4.2.6 fixtureExists

**Signature:**

```typescript
async function fixtureExists(relativePath: string): Promise<boolean>;
```

**Purpose:** Check if fixture file exists

**Example:**

```typescript
if (await fixtureExists('csapi/systems/system-123.json')) {
  const system = await loadFixture('csapi/systems/system-123.json');
}
```

---

### 4.3 Assertion Utilities

#### 4.3.1 expectValidIsoDate

**Signature:**

```typescript
function expectValidIsoDate(
  value: string,
  options?: {
    allowTimeZone?: boolean;
    allowMilliseconds?: boolean;
  }
): void;
```

**Purpose:** Validate ISO 8601 date/time format

**Example:**

```typescript
expectValidIsoDate('2024-01-01T00:00:00Z');
expectValidIsoDate('2024-01-01T00:00:00.000Z', { allowMilliseconds: true });
expectValidIsoDate('2024-01-01T00:00:00+01:00', { allowTimeZone: true });
```

**Validation:**

- Format: `YYYY-MM-DDTHH:mm:ss[.sss]Z` or `YYYY-MM-DDTHH:mm:ss[.sss]±HH:mm`
- Validates year, month, day ranges
- Validates hour, minute, second ranges
- Optional milliseconds validation
- Optional timezone validation

#### 4.3.2 expectValidIsoInterval

**Signature:**

```typescript
function expectValidIsoInterval(
  value: string,
  options?: {
    allowOpen?: boolean;
  }
): void;
```

**Purpose:** Validate ISO 8601 interval format

**Example:**

```typescript
// Closed interval
expectValidIsoInterval('2024-01-01T00:00:00Z/2024-01-31T23:59:59Z');

// Open start
expectValidIsoInterval('../2024-01-31T23:59:59Z', { allowOpen: true });

// Open end
expectValidIsoInterval('2024-01-01T00:00:00Z/..', { allowOpen: true });
```

**Validation:**

- Format: `<start>/<end>`
- Start and end are ISO 8601 dates
- Allows open intervals (`..` for unbounded start/end)
- Validates start is before end (if both bounded)

#### 4.3.3 expectValidGeoJSON

**Signature:**

```typescript
function expectValidGeoJSON(
  value: any,
  expectedType?:
    | 'Point'
    | 'LineString'
    | 'Polygon'
    | 'MultiPoint'
    | 'MultiLineString'
    | 'MultiPolygon'
): void;
```

**Purpose:** Validate GeoJSON geometry structure

**Example:**

```typescript
const point = {
  type: 'Point',
  coordinates: [0, 0],
};
expectValidGeoJSON(point, 'Point');

const polygon = {
  type: 'Polygon',
  coordinates: [
    [
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 1],
      [0, 0],
    ],
  ],
};
expectValidGeoJSON(polygon, 'Polygon');
```

**Validation:**

- Has `type` property with valid geometry type
- Has `coordinates` array
- Coordinates array has correct structure for type
- Point: `[lon, lat]` (2 elements)
- LineString: `[[lon, lat], ...]` (2+ elements)
- Polygon: `[[[lon, lat], ...]]` (1+ rings, 4+ points per ring, closed)

#### 4.3.4 expectValidUuid

**Signature:**

```typescript
function expectValidUuid(value: string): void;
```

**Purpose:** Validate UUID format

**Example:**

```typescript
expectValidUuid('550e8400-e29b-41d4-a716-446655440000');
```

**Validation:**

- Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Each `x` is a hexadecimal digit (0-9, a-f)

#### 4.3.5 expectValidUrl

**Signature:**

```typescript
function expectValidUrl(
  value: string,
  options?: {
    protocol?: 'http' | 'https';
    requireHostname?: boolean;
  }
): void;
```

**Purpose:** Validate URL structure

**Example:**

```typescript
expectValidUrl('https://api.example.com/systems');
expectValidUrl('http://localhost:8080/systems', { protocol: 'http' });
```

#### 4.3.6 expectValidSweSchema

**Signature:**

```typescript
function expectValidSweSchema(schema: any): void;
```

**Purpose:** Validate SWE Common schema structure

**Example:**

```typescript
const schema = {
  type: 'DataRecord',
  fields: [
    { name: 'time', type: 'Time' },
    { name: 'temp', type: 'Quantity', uom: { code: 'degC' } },
  ],
};

expectValidSweSchema(schema);
```

**Validation:**

- Has `type` property (DataRecord, DataArray, Quantity, Time, etc.)
- DataRecord has `fields` array
- DataArray has `elementType` and `encoding`
- Quantity has `uom` (unit of measure)

#### 4.3.7 expectError

**Signature:**

```typescript
function expectError(
  error: Error,
  expected: {
    type?: new (...args: any[]) => Error;
    message?: string | RegExp;
    status?: number;
  }
): void;
```

**Purpose:** Validate error type, message, and status

**Example:**

```typescript
try {
  await builder.getSystem('invalid-id');
} catch (error) {
  expectError(error, {
    type: EndpointError,
    message: /not found/i,
    status: 404,
  });
}
```

#### 4.3.8 expectCollectionResponse

**Signature:**

```typescript
function expectCollectionResponse(
  response: any,
  options?: {
    minItems?: number;
    hasLinks?: boolean;
    hasPagination?: boolean;
  }
): void;
```

**Purpose:** Validate collection response structure

**Example:**

```typescript
const response = {
  systems: [...],
  links: [
    { rel: 'self', href: '...' },
    { rel: 'next', href: '...' }
  ]
};

expectCollectionResponse(response, {
  minItems: 1,
  hasLinks: true,
  hasPagination: true
});
```

#### 4.3.9 expectResourceResponse

**Signature:**

```typescript
function expectResourceResponse(
  response: any,
  resourceType:
    | 'system'
    | 'deployment'
    | 'datastream'
    | 'observation'
    | 'command'
): void;
```

**Purpose:** Validate single resource response structure

**Example:**

```typescript
const response = {
  id: 'sys-123',
  name: 'Weather Station',
  links: [...]
};

expectResourceResponse(response, 'system');
```

#### 4.3.10 expectLinkArray

**Signature:**

```typescript
function expectLinkArray(
  links: any[],
  options?: {
    requiredRels?: string[];
    minCount?: number;
  }
): void;
```

**Purpose:** Validate links array structure

**Example:**

```typescript
const links = [
  { rel: 'self', href: '...' },
  { rel: 'collection', href: '...' },
];

expectLinkArray(links, {
  requiredRels: ['self', 'collection'],
  minCount: 2,
});
```

#### 4.3.11 expectPaginationLinks

**Signature:**

```typescript
function expectPaginationLinks(
  links: any[],
  options?: {
    hasPrev?: boolean;
    hasNext?: boolean;
  }
): void;
```

**Purpose:** Validate pagination links (self, next, prev)

**Example:**

```typescript
const links = [
  { rel: 'self', href: '...' },
  { rel: 'next', href: '...?cursor=abc' },
];

expectPaginationLinks(links, {
  hasNext: true,
  hasPrev: false,
});
```

#### 4.3.12 expectFormatNegotiation

**Signature:**

```typescript
function expectFormatNegotiation(
  response: Response,
  expectedFormat: string,
  expectedContentType: string
): void;
```

**Purpose:** Validate Content-Type header matches format

**Example:**

```typescript
const response = new Response('{}', {
  headers: { 'Content-Type': 'application/json' },
});

expectFormatNegotiation(response, 'json', 'application/json');
```

---

### 4.4 Mocking Utilities

#### 4.4.1 setupMockFetch

**Signature:**

```typescript
function setupMockFetch(
  fixtureRoot: string,
  options?: {
    formatParam?: string;
    defaultFormat?: string;
    trailingSlashRequired?: boolean;
  }
): void;
```

**Purpose:** Setup mock fetch with automatic fixture loading

**Example:**

```typescript
beforeAll(() => {
  setupMockFetch('csapi', {
    formatParam: 'f',
    defaultFormat: 'json',
    trailingSlashRequired: true,
  });
});
```

**Implementation:**

- Mocks `globalThis.fetch`
- Maps URL pathname to fixture file
- Supports format negotiation via query parameter
- Returns 404 for missing fixtures
- Handles trailing slash requirements

#### 4.4.2 mockApiResponse

**Signature:**

```typescript
function mockApiResponse(
  body: any,
  options?: {
    status?: number;
    headers?: Record<string, string>;
  }
): Response;
```

**Purpose:** Create mock API response

**Example:**

```typescript
const response = mockApiResponse(
  { systems: [...] },
  {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  }
);
```

#### 4.4.3 mockCollection

**Signature:**

```typescript
function mockCollection(
  resourceType:
    | 'systems'
    | 'deployments'
    | 'datastreams'
    | 'observations'
    | 'commands',
  items: any[],
  options?: {
    links?: Link[];
  }
): any;
```

**Purpose:** Create mock collection response

**Example:**

```typescript
const collection = mockCollection(
  'systems',
  [
    { id: 'sys-1', name: 'System 1' },
    { id: 'sys-2', name: 'System 2' },
  ],
  {
    links: [{ rel: 'self', href: 'https://api.example.com/systems' }],
  }
);
```

#### 4.4.4 mockResource

**Signature:**

```typescript
function mockResource(
  resourceType:
    | 'system'
    | 'deployment'
    | 'datastream'
    | 'observation'
    | 'command',
  overrides?: Partial<any>
): any;
```

**Purpose:** Create mock resource with defaults

**Example:**

```typescript
const system = mockResource('system', {
  id: 'sys-123',
  name: 'Custom System',
});
// system has all required fields with sensible defaults
```

#### 4.4.5 mockError

**Signature:**

```typescript
function mockError(
  status: number,
  message: string,
  options?: {
    type?: string;
    detail?: string;
  }
): Response;
```

**Purpose:** Create mock error response

**Example:**

```typescript
globalThis.fetch = jest
  .fn()
  .mockResolvedValue(mockError(404, 'Resource not found'));
```

#### 4.4.6 mockPaginatedResponse

**Signature:**

```typescript
function mockPaginatedResponse(
  items: any[],
  options: {
    cursor?: string;
    hasNext?: boolean;
    hasPrev?: boolean;
    baseUrl: string;
  }
): any;
```

**Purpose:** Create paginated response with links

**Example:**

```typescript
const response = mockPaginatedResponse([{ id: 'sys-1' }, { id: 'sys-2' }], {
  cursor: 'abc123',
  hasNext: true,
  hasPrev: false,
  baseUrl: 'https://api.example.com/systems',
});
// response.links includes self, next (no prev)
```

#### 4.4.7 resetMocks

**Signature:**

```typescript
function resetMocks(): void;
```

**Purpose:** Reset all mocks (fetch, timers)

**Example:**

```typescript
afterEach(() => {
  resetMocks();
});
```

#### 4.4.8 mockFetchOnce

**Signature:**

```typescript
function mockFetchOnce(url: string | RegExp, response: Response | any): void;
```

**Purpose:** Mock single fetch call

**Example:**

```typescript
mockFetchOnce(/\/systems\/sys-123/, mockResource('system', { id: 'sys-123' }));

const system = builder.getSystem('sys-123');
// Returns mocked response
```

---

### 4.5 Setup/Teardown Utilities

#### 4.5.1 createTestEndpoint

**Signature:**

```typescript
async function createTestEndpoint(options?: {
  conformance?: string[];
  collectionInfo?: any;
  baseUrl?: string;
}): Promise<OgcApiEndpoint>;
```

**Purpose:** Create OgcApiEndpoint with mock data

**Example:**

```typescript
beforeEach(async () => {
  const endpoint = await createTestEndpoint({
    conformance: [
      'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/systems',
    ],
    baseUrl: 'https://api.example.com',
  });

  builder = await endpoint.csapi('test-collection');
});
```

#### 4.5.2 createTestQueryBuilder

**Signature:**

```typescript
async function createTestQueryBuilder(options?: {
  conformance?: string[];
  baseUrl?: string;
  collectionId?: string;
}): Promise<CSAPIQueryBuilder>;
```

**Purpose:** Create CSAPIQueryBuilder with conformance

**Example:**

```typescript
beforeEach(async () => {
  builder = await createTestQueryBuilder({
    conformance: ['systems', 'deployments', 'observations'],
    baseUrl: 'https://api.example.com',
    collectionId: 'test-collection',
  });
});
```

#### 4.5.3 setupTestContext

**Signature:**

```typescript
function setupTestContext(options?: {
  mockFetch?: boolean;
  useFakeTimers?: boolean;
  fixtureRoot?: string;
}): void;
```

**Purpose:** Initialize test context (fetch mock, timers)

**Example:**

```typescript
beforeAll(() => {
  setupTestContext({
    mockFetch: true,
    useFakeTimers: true,
    fixtureRoot: 'csapi',
  });
});
```

#### 4.5.4 cleanupTest

**Signature:**

```typescript
async function cleanupTest(): Promise<void>;
```

**Purpose:** Cleanup after each test (timers, mocks)

**Example:**

```typescript
afterEach(async () => {
  await cleanupTest();
});
```

**Implementation:**

- Runs `jest.runAllTimersAsync()` to exhaust microtasks
- Clears all mocks
- Resets fixture cache (optional)

#### 4.5.5 resetTestContext

**Signature:**

```typescript
function resetTestContext(): void;
```

**Purpose:** Reset context between tests

**Example:**

```typescript
afterEach(() => {
  resetTestContext();
});
```

#### 4.5.6 withTestEndpoint

**Signature:**

```typescript
function withTestEndpoint(
  options: {
    conformance?: string[];
    baseUrl?: string;
  },
  testFn: (endpoint: OgcApiEndpoint) => Promise<void> | void
): () => Promise<void>;
```

**Purpose:** HOF to wrap tests with endpoint setup

**Example:**

```typescript
it(
  'constructs systems URL',
  withTestEndpoint({ conformance: ['systems'] }, async (endpoint) => {
    const builder = await endpoint.csapi('test');
    const url = builder.getSystems();
    expect(url).toContain('/systems');
  })
);
```

---

### 4.6 Data Builder Utilities

#### 4.6.1 buildSystem

**Signature:**

```typescript
function buildSystem(overrides?: Partial<System>): System;

interface System {
  id: string;
  name: string;
  description?: string;
  definition?: string;
  properties?: Record<string, any>;
  links?: Link[];
}
```

**Purpose:** Build System resource with defaults

**Example:**

```typescript
const system = buildSystem({
  id: 'sys-123',
  name: 'Weather Station',
});
// system has all required fields with sensible defaults
```

**Defaults:**

- `id`: Generated UUID
- `name`: 'Test System'
- `description`: 'Test system description'
- `links`: `[{ rel: 'self', href: '...' }]`

#### 4.6.2 buildDeployment

**Signature:**

```typescript
function buildDeployment(overrides?: Partial<Deployment>): Deployment;
```

**Purpose:** Build Deployment resource with defaults

**Example:**

```typescript
const deployment = buildDeployment({
  id: 'dep-123',
  name: 'Field Deployment',
  geometry: buildGeoJSON('Point', [0, 0]),
});
```

#### 4.6.3 buildDatastream

**Signature:**

```typescript
function buildDatastream(overrides?: Partial<Datastream>): Datastream;
```

**Purpose:** Build DataStream resource with defaults

**Example:**

```typescript
const datastream = buildDatastream({
  id: 'ds-123',
  name: 'Temperature Observations',
  observedProperty: 'Temperature',
});
```

#### 4.6.4 buildObservation

**Signature:**

```typescript
function buildObservation(overrides?: Partial<Observation>): Observation;

interface Observation {
  phenomenonTime: string;
  resultTime?: string;
  result: any;
  parameters?: Record<string, any>;
  geometry?: GeoJSON;
}
```

**Purpose:** Build Observation with defaults

**Example:**

```typescript
const observation = buildObservation({
  phenomenonTime: '2024-01-01T00:00:00Z',
  result: { temp: 25.5, humidity: 60 },
});
```

**Defaults:**

- `phenomenonTime`: Current ISO timestamp
- `resultTime`: Same as `phenomenonTime`
- `result`: `{ value: 0 }`

#### 4.6.5 buildCommand

**Signature:**

```typescript
function buildCommand(overrides?: Partial<Command>): Command;
```

**Purpose:** Build Command with defaults

**Example:**

```typescript
const command = buildCommand({
  id: 'cmd-123',
  type: 'SetParameter',
  parameters: { target: 'sensor', value: 100 },
});
```

#### 4.6.6 buildSweSchema

**Signature:**

```typescript
function buildSweSchema(
  type: 'DataRecord' | 'DataArray' | 'Quantity' | 'Time',
  config?: {
    fields?: Array<{ name: string; type: string; uom?: any }>;
    elementType?: any;
    encoding?: any;
  }
): any;
```

**Purpose:** Build SWE Common schema

**Example:**

```typescript
const schema = buildSweSchema('DataRecord', {
  fields: [
    { name: 'time', type: 'Time' },
    { name: 'temp', type: 'Quantity', uom: { code: 'degC' } },
  ],
});
```

#### 4.6.7 buildGeoJSON

**Signature:**

```typescript
function buildGeoJSON(
  type: 'Point' | 'LineString' | 'Polygon',
  coordinates: any
): GeoJSON;
```

**Purpose:** Build GeoJSON geometry

**Example:**

```typescript
const point = buildGeoJSON('Point', [0, 0]);
const linestring = buildGeoJSON('LineString', [
  [0, 0],
  [1, 1],
]);
const polygon = buildGeoJSON('Polygon', [
  [
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
    [0, 0],
  ],
]);
```

#### 4.6.8 buildTemporalExtent

**Signature:**

```typescript
function buildTemporalExtent(
  start: string,
  end?: string
): [string, string | null];
```

**Purpose:** Build temporal extent array

**Example:**

```typescript
const extent = buildTemporalExtent(
  '2024-01-01T00:00:00Z',
  '2024-01-31T23:59:59Z'
);
// extent === ['2024-01-01T00:00:00Z', '2024-01-31T23:59:59Z']

const openExtent = buildTemporalExtent('2024-01-01T00:00:00Z');
// openExtent === ['2024-01-01T00:00:00Z', null]
```

#### 4.6.9 buildSpatialExtent

**Signature:**

```typescript
function buildSpatialExtent(bbox: [number, number, number, number]): {
  bbox: [number, number, number, number];
};
```

**Purpose:** Build spatial extent (bbox)

**Example:**

```typescript
const extent = buildSpatialExtent([0, 0, 1, 1]);
// extent === { bbox: [0, 0, 1, 1] }
```

#### 4.6.10 buildLinks

**Signature:**

```typescript
function buildLinks(
  baseUrl: string,
  options?: {
    self?: boolean;
    collection?: boolean;
    next?: string;
    prev?: string;
  }
): Link[];
```

**Purpose:** Build links array with pagination

**Example:**

```typescript
const links = buildLinks('https://api.example.com/systems', {
  self: true,
  collection: true,
  next: 'cursor-abc',
});
// links = [
//   { rel: 'self', href: 'https://api.example.com/systems' },
//   { rel: 'collection', href: 'https://api.example.com/collections/test' },
//   { rel: 'next', href: 'https://api.example.com/systems?cursor=cursor-abc' }
// ]
```

---

## 5. Utility Reusability Strategy

### 5.1 Module Organization

**File Structure:**

```
src/
  ogc-api/csapi/
    test-utils/
      index.ts                     # Re-export all utilities
      test-utils.ts                # Core utilities (URL, assertions)
      test-helpers.ts              # Setup/teardown
      test-fixtures.ts             # Fixture loading
      data-builders.ts             # Data builders (optional separate file)
```

**index.ts:**

```typescript
// Re-export all utilities from single import
export * from './test-utils.js';
export * from './test-helpers.js';
export * from './test-fixtures.js';
export * from './data-builders.js';
```

**Usage in Tests:**

```typescript
import {
  parseAndValidateUrl,
  expectValidIsoDate,
  loadFixture,
  createTestQueryBuilder,
  buildSystem,
} from './test-utils/index.js';
```

### 5.2 Naming Conventions

**Utility Naming Patterns:**

| Category                | Prefix/Pattern                  | Examples                                                       |
| ----------------------- | ------------------------------- | -------------------------------------------------------------- |
| **URL Utilities**       | `parse*`, `extract*`, `build*`  | `parseAndValidateUrl`, `extractResourceId`, `buildResourceUrl` |
| **Fixture Utilities**   | `load*`, `*Fixture*`            | `loadFixture`, `loadFixtureSet`, `clearFixtureCache`           |
| **Assertion Utilities** | `expect*`, `validate*`          | `expectValidIsoDate`, `expectValidGeoJSON`, `validateEncoding` |
| **Mocking Utilities**   | `mock*`, `setup*Mock*`          | `mockApiResponse`, `setupMockFetch`, `mockCollection`          |
| **Setup/Teardown**      | `create*`, `setup*`, `cleanup*` | `createTestEndpoint`, `setupTestContext`, `cleanupTest`        |
| **Data Builders**       | `build*`                        | `buildSystem`, `buildObservation`, `buildGeoJSON`              |

**Naming Rules:**

1. **Verbs First**: Function names start with verb (`parse`, `load`, `expect`, `build`)
2. **Descriptive**: Clear what function does (`parseAndValidateUrl` not `parseUrl`)
3. **Consistent**: Same prefix for related functions (`expect*` for assertions)
4. **No Abbreviations**: Spell out full words (`Observation` not `Obs`)

### 5.3 Documentation Standards

**JSDoc Requirements:**

Every utility function must have:

1. **Description**: One-sentence summary
2. **@param**: All parameters with types
3. **@returns**: Return value with type
4. **@example**: At least one usage example
5. **@throws**: Exceptions thrown (if any)

**Template:**

````typescript
/**
 * Parse URL and validate expected components
 *
 * @param url - URL string to parse
 * @param expected - Expected URL components to validate
 * @returns Parsed URL object
 * @throws {Error} If URL parsing fails or validation fails
 *
 * @example
 * ```typescript
 * const parsed = parseAndValidateUrl('https://api.example.com/systems?limit=10', {
 *   protocol: 'https:',
 *   pathname: '/systems',
 *   query: { limit: '10' }
 * });
 * ```
 */
function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string;
    hostname?: string;
    pathname?: string;
    query?: Record<string, string>;
  }
): ParsedURL {
  // Implementation
}
````

### 5.4 Testing Approach (Test the Tests)

**Utility Testing Strategy:**

Test utilities themselves should be tested to ensure reliability:

**File:** `test-utils/test-utils.spec.ts`

**Example:**

```typescript
describe('parseAndValidateUrl', () => {
  it('parses valid URL', () => {
    const parsed = parseAndValidateUrl(
      'https://api.example.com:443/systems?limit=10',
      {
        protocol: 'https:',
        hostname: 'api.example.com',
        pathname: '/systems',
        query: { limit: '10' },
      }
    );

    expect(parsed.protocol).toBe('https:');
    expect(parsed.hostname).toBe('api.example.com');
    expect(parsed.query.limit).toBe('10');
  });

  it('throws on protocol mismatch', () => {
    expect(() => {
      parseAndValidateUrl('http://api.example.com', {
        protocol: 'https:',
      });
    }).toThrow('Expected protocol https: but got http:');
  });
});
```

**Testing Coverage:**

- ✅ **Happy path**: Utility works with valid inputs
- ✅ **Edge cases**: Empty values, null/undefined, boundary conditions
- ✅ **Error cases**: Throws expected errors with descriptive messages
- ✅ **Type safety**: TypeScript types prevent misuse

### 5.5 Versioning Strategy

**Utility Versioning:**

Utilities evolve with test suite, not separately versioned. However:

**Breaking Changes:**

If utility signature changes in breaking way:

1. **Deprecate old version**: Add `@deprecated` JSDoc tag
2. **Create new version**: New function with different name
3. **Migration period**: Support both for 1 release cycle
4. **Remove old version**: After all tests migrated

**Example:**

```typescript
/**
 * @deprecated Use parseAndValidateUrl instead
 */
function parseUrl(url: string): ParsedURL {
  // Old implementation
}

/**
 * Parse URL and validate expected components
 */
function parseAndValidateUrl(
  url: string,
  expected: {...}
): ParsedURL {
  // New implementation
}
```

### 5.6 Reusability Guidelines

**When to Create Utility:**

Create utility when:

- ✅ Pattern repeated 3+ times across different test files
- ✅ Logic is complex (>5 lines)
- ✅ Validation has multiple steps
- ✅ Improves test readability significantly

**When NOT to Create Utility:**

Don't create utility when:

- ❌ Used only 1-2 times
- ❌ Too specific to single test (not reusable)
- ❌ Trivial one-liner (e.g., `expect(x).toBe(y)`)
- ❌ Makes tests harder to read (too much abstraction)

**Utility Evolution:**

1. **Start inline**: Write logic inline in first test
2. **Extract local helper**: Move to helper function in same file if repeated 2-3 times
3. **Promote to utility**: Move to `test-utils/` if used across 3+ files
4. **Refine**: Improve based on usage patterns

---

## 6. Implementation Estimates

### 6.1 Utility Implementation Summary

| Category                | Functions        | Lines per Function | Total Lines      | Priority     | Estimated Time  |
| ----------------------- | ---------------- | ------------------ | ---------------- | ------------ | --------------- |
| **URL Utilities**       | 8                | 15-30              | 120-240          | **CRITICAL** | 4-6 hours       |
| **Fixture Utilities**   | 6                | 20-40              | 120-240          | **CRITICAL** | 4-6 hours       |
| **Assertion Utilities** | 12               | 10-20              | 120-240          | HIGH         | 6-8 hours       |
| **Mocking Utilities**   | 8                | 15-30              | 120-240          | HIGH         | 4-6 hours       |
| **Setup/Teardown**      | 6                | 20-40              | 120-240          | HIGH         | 4-6 hours       |
| **Data Builders**       | 10               | 15-30              | 150-300          | MEDIUM       | 5-8 hours       |
| **Documentation**       | N/A              | N/A                | ~150             | HIGH         | 3-4 hours       |
| **Utility Tests**       | ~30              | 10-20              | ~300-600         | MEDIUM       | 8-12 hours      |
| **TOTAL**               | **50 functions** | **~20 avg**        | **~1,000-1,650** |              | **38-56 hours** |

**Total Implementation Effort:** ~1-1.5 weeks (1 developer)

### 6.2 Implementation Phases

**Phase 1: Core Utilities (Week 1, Day 1-2)**

- URL utilities (8 functions, 120-240 lines)
- Fixture utilities (6 functions, 120-240 lines)
- **Priority:** CRITICAL
- **Time:** 8-12 hours

**Phase 2: Validation Utilities (Week 1, Day 3-4)**

- Assertion utilities (12 functions, 120-240 lines)
- Mocking utilities (8 functions, 120-240 lines)
- **Priority:** HIGH
- **Time:** 10-14 hours

**Phase 3: Helper Utilities (Week 1, Day 5)**

- Setup/teardown utilities (6 functions, 120-240 lines)
- **Priority:** HIGH
- **Time:** 4-6 hours

**Phase 4: Data Builders (Week 2, Day 1-2)**

- Data builder utilities (10 functions, 150-300 lines)
- **Priority:** MEDIUM
- **Time:** 5-8 hours

**Phase 5: Testing & Documentation (Week 2, Day 3-5)**

- Utility tests (~30 tests, 300-600 lines)
- Documentation (JSDoc, examples)
- **Priority:** MEDIUM-HIGH
- **Time:** 11-16 hours

### 6.3 File Size Estimates

| File               | Functions | Lines            | Complexity |
| ------------------ | --------- | ---------------- | ---------- |
| `test-utils.ts`    | 20        | 400-600          | Medium     |
| `test-helpers.ts`  | 14        | 280-480          | Medium     |
| `test-fixtures.ts` | 6         | 120-240          | Low        |
| `data-builders.ts` | 10        | 200-300          | Low-Medium |
| `index.ts`         | N/A       | 10-30            | Trivial    |
| **Total**          | **50**    | **~1,010-1,650** |            |

### 6.4 Test Implementation Impact

**Before Utilities:**

- Average test file: 150-250 lines
- Duplication: ~60-70%
- Setup boilerplate: ~30-50 lines per file
- Assertion boilerplate: ~5-10 lines per assertion

**After Utilities:**

- Average test file: 80-120 lines (40-50% reduction)
- Duplication: ~10-15% (80-85% improvement)
- Setup boilerplate: ~5-10 lines per file (80% reduction)
- Assertion boilerplate: ~1-2 lines per assertion (80% reduction)

**Overall Impact:**

- **60-70% reduction** in test code duplication across ~22 CSAPI test files (per Section 19 inventory)
- **Saves ~2,500-3,700 lines** of duplicated test code (60-70% of ~4,100-5,300 total test lines)
- **Improves maintainability** - fix bugs once in utility, not across multiple test files

---

## 7. Usage Examples

### 7.1 Complete Test File Example (Before Utilities)

**WITHOUT Utilities - Repeated Boilerplate:**

```typescript
// url_builder-systems.spec.ts (WITHOUT utilities)
import OgcApiEndpoint from '../endpoint.js';
import { readFile } from 'fs/promises';
import * as path from 'path';

const FIXTURES_ROOT = path.join(__dirname, '../../fixtures/csapi');

beforeAll(() => {
  globalThis.fetch = jest.fn().mockImplementation(async (urlOrInfo) => {
    const url = new URL(
      urlOrInfo instanceof URL || typeof urlOrInfo === 'string'
        ? urlOrInfo
        : urlOrInfo.url
    );

    let queryPath = url.pathname.replace(/\/$/, '');
    if (queryPath === '') queryPath = 'root-path';
    const format = url.searchParams.get('f') || 'json';
    const filePath = `${path.join(FIXTURES_ROOT, queryPath)}.${format}`;

    try {
      const contents = await readFile(filePath, { encoding: 'utf8' });
      return {
        ok: true,
        json: () => Promise.resolve(JSON.parse(contents)),
      } as Response;
    } catch {
      return { ok: false, status: 404 } as Response;
    }
  });
});

jest.useFakeTimers();

describe('CSAPIQueryBuilder - Systems', () => {
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    const endpoint = new OgcApiEndpoint('http://local/sample-data/');
    builder = await endpoint.csapi('test-collection');
  });

  afterEach(async () => {
    await jest.runAllTimersAsync();
  });

  it('constructs systems collection URL', async () => {
    const url = builder.getSystems();

    // Parse and validate URL manually
    const parsed = new URL(url);
    expect(parsed.protocol).toBe('https:');
    expect(parsed.hostname).toBe('api.example.com');
    expect(parsed.pathname).toBe('/systems');
  });

  it('includes limit parameter', async () => {
    const url = builder.getSystems({ limit: 10 });

    const parsed = new URL(url);
    expect(parsed.searchParams.get('limit')).toBe('10');
  });

  it('includes bbox parameter', async () => {
    const url = builder.getSystems({ bbox: [0, 0, 1, 1] });

    const parsed = new URL(url);
    expect(parsed.searchParams.get('bbox')).toBe('0,0,1,1');
  });

  it('validates ISO 8601 dates', () => {
    const date = '2024-01-01T00:00:00Z';
    expect(date).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
  });
});
```

**Total:** ~80 lines with significant boilerplate

### 7.2 Complete Test File Example (After Utilities)

**WITH Utilities - Cleaner and More Readable:**

```typescript
// url_builder-systems.spec.ts (WITH utilities)
import {
  parseAndValidateUrl,
  expectQueryParam,
  expectValidIsoDate,
  createTestQueryBuilder,
  setupTestContext,
  cleanupTest,
} from './test-utils/index.js';

beforeAll(() => {
  setupTestContext({
    mockFetch: true,
    useFakeTimers: true,
    fixtureRoot: 'csapi',
  });
});

describe('CSAPIQueryBuilder - Systems', () => {
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    builder = await createTestQueryBuilder({ conformance: ['systems'] });
  });

  afterEach(async () => {
    await cleanupTest();
  });

  it('constructs systems collection URL', async () => {
    const url = builder.getSystems();

    parseAndValidateUrl(url, {
      protocol: 'https:',
      hostname: 'api.example.com',
      pathname: '/systems',
    });
  });

  it('includes limit parameter', async () => {
    const url = builder.getSystems({ limit: 10 });
    expectQueryParam(url, 'limit', '10');
  });

  it('includes bbox parameter', async () => {
    const url = builder.getSystems({ bbox: [0, 0, 1, 1] });
    expectQueryParam(url, 'bbox', '0,0,1,1');
  });

  it('validates ISO 8601 dates', () => {
    const date = '2024-01-01T00:00:00Z';
    expectValidIsoDate(date);
  });
});
```

**Total:** ~40 lines (50% reduction)

**Benefits:**

- ✅ No fetch mock boilerplate (60 lines → 1 line)
- ✅ No manual URL parsing (6 lines → 1 line per test)
- ✅ No ISO validation regex (complex regex → 1 line)
- ✅ Descriptive utility names improve readability
- ✅ Easier to maintain (update utilities, not 50 test files)

### 7.3 Assertion Utility Examples

**WITHOUT Utilities:**

```typescript
// Validate GeoJSON Point (7 lines)
expect(location).toHaveProperty('type', 'Point');
expect(location).toHaveProperty('coordinates');
expect(Array.isArray(location.coordinates)).toBe(true);
expect(location.coordinates.length).toBe(2);
expect(typeof location.coordinates[0]).toBe('number');
expect(typeof location.coordinates[1]).toBe('number');
expect(location.coordinates[0]).toBeGreaterThanOrEqual(-180);

// Validate ISO 8601 interval (4 lines)
expect(interval).toContain('/');
const [start, end] = interval.split('/');
expect(start).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);
expect(end).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/);

// Validate error (3 lines)
expect(error).toBeInstanceOf(EndpointError);
expect(error.message).toContain('not found');
expect(error.httpStatus).toBe(404);
```

**WITH Utilities:**

```typescript
// Validate GeoJSON Point (1 line)
expectValidGeoJSON(location, 'Point');

// Validate ISO 8601 interval (1 line)
expectValidIsoInterval(interval);

// Validate error (1 line)
expectError(error, {
  type: EndpointError,
  message: /not found/,
  status: 404,
});
```

**Reduction:** 14 lines → 3 lines (78% reduction)

### 7.4 Data Builder Examples

**WITHOUT Utilities:**

```typescript
// Create test observation (12 lines)
const observation = {
  phenomenonTime: '2024-01-01T00:00:00Z',
  resultTime: '2024-01-01T00:00:00Z',
  result: {
    temp: 25.5,
    humidity: 60,
  },
  geometry: {
    type: 'Point',
    coordinates: [0, 0],
  },
  links: [
    { rel: 'self', href: 'https://api.example.com/observations/obs-123' },
  ],
};

// Create test system (15 lines)
const system = {
  id: 'sys-123',
  name: 'Weather Station',
  description: 'Test weather station',
  definition: 'http://example.com/systems/weather-station',
  properties: {
    manufacturer: 'ACME',
    model: 'WS-2000',
  },
  links: [
    { rel: 'self', href: 'https://api.example.com/systems/sys-123' },
    {
      rel: 'datastreams',
      href: 'https://api.example.com/systems/sys-123/datastreams',
    },
  ],
  validTime: {
    start: '2024-01-01T00:00:00Z',
    end: null,
  },
};
```

**WITH Utilities:**

```typescript
// Create test observation (4 lines)
const observation = buildObservation({
  result: { temp: 25.5, humidity: 60 },
  geometry: buildGeoJSON('Point', [0, 0]),
});

// Create test system (3 lines)
const system = buildSystem({
  id: 'sys-123',
  name: 'Weather Station',
});
```

**Reduction:** 27 lines → 7 lines (74% reduction)

---

## 8. Migration Strategy

### 8.1 Migration Approach

**Phased Migration:**

1. **Phase 1: Implement Utilities** (Week 1)

   - Implement all 50 utility functions
   - Write utility tests
   - Document with JSDoc

2. **Phase 2: Migrate Core Tests** (Week 2)

   - Migrate URL builder tests (highest duplication)
   - Migrate format parser tests
   - Validate utilities work as expected

3. **Phase 3: Migrate Remaining Tests** (Week 3)
   - Migrate all other test files
   - Remove deprecated inline patterns
   - Update test documentation

### 8.2 Migration Checklist

**Per Test File:**

- [ ] Replace fetch mock boilerplate with `setupTestContext()`
- [ ] Replace `beforeEach` endpoint creation with `createTestQueryBuilder()`
- [ ] Replace URL parsing with `parseAndValidateUrl()`
- [ ] Replace query param assertions with `expectQueryParam()`
- [ ] Replace ISO date validation with `expectValidIsoDate()`
- [ ] Replace GeoJSON validation with `expectValidGeoJSON()`
- [ ] Replace error validation with `expectError()`
- [ ] Replace fixture loading with `loadFixture()`
- [ ] Replace `afterEach` cleanup with `cleanupTest()`
- [ ] Remove unused imports

### 8.3 Backwards Compatibility

**Approach:**

- ✅ Utilities are **additive** - don't break existing tests
- ✅ Migrate tests incrementally - no "big bang" rewrite
- ✅ Old patterns still work during migration period
- ✅ Remove old patterns after all tests migrated

---

## 9. Key Recommendations

### 9.1 Priorities

**Must Have (Priority 1):**

1. **URL utilities** - `parseAndValidateUrl()`, `expectQueryParam()`
2. **Fixture utilities** - `loadFixture()`, `setupMockFetch()`
3. **Setup utilities** - `createTestQueryBuilder()`, `cleanupTest()`

**Should Have (Priority 2):** 4. **Assertion utilities** - `expectValidIsoDate()`, `expectValidGeoJSON()`, `expectError()` 5. **Mocking utilities** - `mockApiResponse()`, `mockCollection()`

**Nice to Have (Priority 3):** 6. **Data builders** - `buildSystem()`, `buildObservation()`, `buildGeoJSON()`

### 9.2 Benefits Summary

**Code Quality:**

- ✅ **60-70% reduction** in test code duplication
- ✅ **Improved readability** - descriptive utility names
- ✅ **Consistent validation** - same checks everywhere
- ✅ **Better error messages** - context-aware failures

**Maintainability:**

- ✅ **Fix bugs once** - in utility, not 50 test files
- ✅ **Easier refactoring** - update utility signature, not 50 call sites
- ✅ **Better documentation** - JSDoc in one place

**Developer Experience:**

- ✅ **Faster test writing** - reuse utilities vs write boilerplate
- ✅ **Easier test reading** - clear intent from utility names
- ✅ **Less cognitive load** - remember utility names vs implementation details

### 9.3 Key Takeaways

1. **Utilities reduce duplication by 60-70%** across ~22 CSAPI test files (per Section 19 inventory)
2. **50 utility functions** organized in 6 categories
3. **~1,000-1,650 lines** of utility implementation
4. **Saves ~2,500-3,700 lines** of duplicated test code (60-70% of ~4,100-5,300 total test lines)
5. **1-1.5 weeks** implementation effort
6. **CSAPI-specific utilities** not found in upstream (temporal, spatial, SWE Common)
7. **Phased migration** approach - additive, not breaking

---

## 10. References

### 10.1 Related Research Documents

- **Section 1:** EDR Test Blueprint (modern fixture loading patterns)
- **Section 2:** Upstream Test Consistency (fetch mocking patterns, assertion standards)
- **Section 19:** Test Organization and File Structure (utility organization, file structure)
- **Section 12:** QueryBuilder Testing Strategy (URL validation patterns)
- **Section 25:** Format Negotiation Testing (format validation patterns)

### 10.2 External Resources

- **Jest Documentation:** https://jestjs.io/docs/getting-started
- **Jest Custom Matchers:** https://jestjs.io/docs/expect#custom-matchers
- **Testing Library:** https://testing-library.com/
- **TypeScript Utility Types:** https://www.typescriptlang.org/docs/handbook/utility-types.html

---

**END OF DOCUMENT**
