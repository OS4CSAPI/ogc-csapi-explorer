# EDR Test Pattern Blueprint (PR #114 Analysis)

**Research Plan:** [docs/research/testing/research-plans/01-pr114-blueprint-analysis.md](../research-plans/01-pr114-blueprint-analysis.md)  
**Research Questions:** 71 detailed questions about test patterns, coverage, assertions, fixtures, and quality indicators  
**Methodology:** 4-phase analysis (PR overview → test file analysis → pattern extraction → synthesis)  
**Research Time:** 3.5 hours (February 5, 2026, 10:30 AM - 2:00 PM)

**Primary Source:** camptocamp/ogc-client PR #114 - OGC EDR URL Builder Support  
**PR Details:**

- Merged: August 29, 2025 by jahow
- Author: C-Loftus (cgs-earth)
- URL: https://github.com/camptocamp/ogc-client/pull/114

**Supporting Resources:**

- Local clone: camptocamp/ogc-client repository
- EDR test files: src/ogc-api/edr/\*.spec.ts, src/ogc-api/endpoint.spec.ts (EDR sections)
- EDR fixtures: fixtures/ogc-api/edr/
- OGC API - Environmental Data Retrieval specification
- PR review comments and feedback

**Document Purpose:** Extract complete testing blueprint from accepted upstream implementation to define what constitutes "meaningful" tests for CSAPI implementation

---

## Executive Summary

PR #114 added OGC Environmental Data Retrieval (EDR) API support to ogc-client through a composition-based architecture. The PR added **2,858 lines** (18 files changed) with **298 test lines** across 3 test files plus extensive integration tests in `endpoint.spec.ts`. The implementation follows the factory method + QueryBuilder pattern consistent with existing implementations (Features, Records, Tiles).

### Key Metrics

- **Implementation Lines:** 2,858 additions, 54 deletions
- **Test Lines:** ~600 lines of tests (3 unit test files + 1 integration file)
- **Test Files:** 4 files (3 new unit tests + modifications to existing endpoint.spec.ts)
- **Test Cases:** 16 unit tests + 13 integration scenarios = **29 total tests**
- **Fixtures:** 6 JSON fixture files (root, collections, collection details, conformance)
- **Test-to-Code Ratio:** ~1:4.8 (test lines / implementation lines)
- **Coverage:** Not explicitly stated in PR artifacts, but comprehensive URL builder coverage evident

### What Made These Tests Acceptable

1. **URL Validation Depth:** Tests validate complete URL structure including protocol, host, path, and query parameters
2. **Error Condition Coverage:** Comprehensive validation error tests (invalid params, unsupported queries, bbox validation)
3. **Type Safety:** Strong TypeScript typing with type-safe parameter interfaces
4. **Spec Compliance:** All methods documented with links to OGC EDR spec sections
5. **Real Fixtures:** Used realistic EDR collection responses (USACE reservoir data)
6. **Integration Coverage:** Tests showed end-to-end flows from endpoint detection to query building

---

## 1. Test File Inventory

### Unit Test Files (New)

| File                   | Location           | Lines | Tests | Purpose                                       |
| ---------------------- | ------------------ | ----- | ----- | --------------------------------------------- |
| `helpers.spec.ts`      | `src/ogc-api/edr/` | 39    | 5     | DateTime parameter serialization              |
| `model.spec.ts`        | `src/ogc-api/edr/` | 38    | 6     | Z-parameter (vertical level) serialization    |
| (url_builder implicit) | `src/ogc-api/edr/` | 0     | 0     | No direct unit tests - tested via integration |

### Integration Test Files (Modified)

| File               | Location       | Lines Added | Tests Added  | Purpose                                                                    |
| ------------------ | -------------- | ----------- | ------------ | -------------------------------------------------------------------------- |
| `endpoint.spec.ts` | `src/ogc-api/` | 298         | 13 scenarios | EDR endpoint detection, collection listing, query building, error handling |

### Implementation Files

| File                 | Location           | Lines   | Purpose                                          |
| -------------------- | ------------------ | ------- | ------------------------------------------------ |
| `url_builder.ts`     | `src/ogc-api/edr/` | 561     | Main QueryBuilder class with 8 EDR query methods |
| `model.ts`           | `src/ogc-api/edr/` | 125     | Type definitions for EDR-specific parameters     |
| `helpers.ts`         | `src/ogc-api/edr/` | 23      | DateTime serialization utility                   |
| `endpoint.ts`        | `src/ogc-api/`     | +41 -2  | Integration of EDR into OgcApiEndpoint           |
| `info.ts`            | `src/ogc-api/`     | +61 -45 | EDR conformance checking, collection parsing     |
| `model.ts` (ogc-api) | `src/ogc-api/`     | +46 -1  | EDR type definitions in OgcApiCollectionInfo     |
| `link-utils.ts`      | `src/ogc-api/`     | +9 -5   | Link resolution support for EDR collections      |

### Fixture Files

| File                            | Location                                            | Size            | Purpose                                    |
| ------------------------------- | --------------------------------------------------- | --------------- | ------------------------------------------ |
| `sample-data-hub.json`          | `fixtures/ogc-api/edr/`                             | 80 lines        | EDR root document                          |
| `conformance.json`              | `fixtures/ogc-api/edr/sample-data-hub/`             | 22 lines        | Conformance classes including EDR core     |
| `collections.json`              | `fixtures/ogc-api/edr/sample-data-hub/`             | 715 lines       | 2 collections (ADWR sites + reservoir-api) |
| `reservoir-api.json` (2 copies) | `fixtures/ogc-api/edr/sample-data-hub/`             | 194 + 574 lines | Detailed EDR collection with data_queries  |
| `reservoir-api.json`            | `fixtures/ogc-api/edr/sample-data-hub/collections/` | 574 lines       | Full collection document                   |

---

## 2. Test Structure Patterns

### Helper Function Tests (`helpers.spec.ts`)

```typescript
describe('DateTimeParameterToEDRString', () => {
  const toDate = (str: string) => new Date(str);

  it('serializes a plain Date', () => {
    const result = DateTimeParameterToEDRString(toDate('2025-01-01T00:00:00Z'));
    expect(result).toBe('2025-01-01T00:00:00.000Z');
  });

  it('serializes with only start', () => {
    const result = DateTimeParameterToEDRString({
      start: toDate('2025-01-01T00:00:00Z'),
    });
    expect(result).toBe('2025-01-01T00:00:00.000Z/..');
  });

  it('serializes with start and end', () => {
    const result = DateTimeParameterToEDRString({
      start: toDate('2025-01-01T00:00:00Z'),
      end: toDate('2025-12-31T23:59:59Z'),
    });
    expect(result).toBe('2025-01-01T00:00:00.000Z/2025-12-31T23:59:59.000Z');
  });

  it('throws if passed an invalid object', () => {
    expect(() =>
      DateTimeParameterToEDRString({} as DateTimeParameter)
    ).toThrow();
  });
});
```

**Pattern:** Pure function tests with clear input/output validation

### Model Tests (`model.spec.ts`)

```typescript
describe('zParameterToString', () => {
  test('single level', () => {
    const z: ZParameter = { type: 'single', level: 850 };
    expect(zParameterToString(z)).toBe('850');
  });

  test('interval (min/max)', () => {
    const z: ZParameter = { type: 'interval', minLevel: 100, maxLevel: 550 };
    expect(zParameterToString(z)).toBe('100/550');
  });

  test('list of levels', () => {
    const z: ZParameter = { type: 'list', levels: [10, 80, 200] };
    expect(zParameterToString(z)).toBe('10,80,200');
  });

  test('repeating interval', () => {
    const z: ZParameter = {
      type: 'repeating',
      repeat: 20,
      minLevel: 100,
      step: 50,
    };
    expect(zParameterToString(z)).toBe('R20/100/50');
  });
});
```

**Pattern:** Type-safe discriminated union testing with explicit types

### Integration Tests (`endpoint.spec.ts`)

```typescript
describe('OgcApiEndpoint with EDR', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(() => {
    endpoint = new OgcApiEndpoint('http://local/edr/sample-data-hub');
  });

  it('supports EDR', async () => {
    await expect(endpoint.hasEnvironmentalDataRetrieval).resolves.toBe(true);
  });

  it('can list all the EDR collections', async () => {
    await expect(endpoint.edrCollections).resolves.toEqual(['reservoir-api']);
  });

  it('can produce a EDR query builder', async () => {
    const builder = await endpoint.edr('reservoir-api');
    expect(builder).toBeTruthy();
    expect(builder.supported_queries).toEqual(
      new Set(['area', 'locations', 'cube'])
    );
  });

  it('can produce EDR area queries with/without optional parameters', async () => {
    const builder = await endpoint.edr('reservoir-api');

    const url1 = builder.buildAreaDownloadUrl(
      'POLYGON((-1.0 50.0, -1.0 51.0, 0.0 51.0, 0.0 50.0, -1.0 50.0))'
    );
    expect(url1).toEqual(
      'https://dummy.edr.app/collections/reservoir-api/area?coords=...'
    );

    const url2 = builder.buildAreaDownloadUrl('POLYGON(...)', {
      parameter_name: ['Water Temperature'],
      z: { type: 'single', level: 1 },
    });
    expect(url2).toContain('parameter-name=Water+Temperature');
    expect(url2).toContain('z=1');
  });

  it('throws with invalid parameters', async () => {
    const builder = await endpoint.edr('reservoir-api');
    expect(() =>
      builder.buildAreaDownloadUrl('POLYGON(...)', {
        parameter_name: ['BadParameterName'],
      })
    ).toThrow();
  });
});
```

**Pattern:** Full integration flow testing with realistic fixtures

---

## 3. Assertion Depth Analysis

### ❌ TRIVIAL (Not Used in PR #114)

```typescript
// NOT FOUND - PR #114 did not use these trivial patterns
expect(url).toContain('/area');
expect(url).toBeDefined();
expect(builder).toBeTruthy(); // Only used as first check, always followed by deeper assertions
```

### ✅ MEANINGFUL (Used in PR #114)

```typescript
// 1. Exact URL string matching
expect(url).toEqual(
  'https://dummy.edr.app/collections/reservoir-api/area?coords=POLYGON%28%28-1.0+50.0...'
);

// 2. URL component validation
expect(url).toContain('parameter-name=Water+Temperature');
expect(url).toContain('z=1');
expect(url).toContain('&'); // Proper query string formatting

// 3. Type-safe object matching
expect(builder.supported_queries).toEqual(
  new Set(['area', 'locations', 'cube'])
);

expect(Object.keys(builder.supported_parameters)).toEqual([
  'Elevation',
  'Water Temperature',
  'Air Temperature',
]);

// 4. Error condition testing
expect(() =>
  builder.buildCubeDownloadUrl({ minX: 0, minY: 10, maxX: -10, maxY: 12 })
).toThrow('minX must be less than or equal to maxX');

expect(() =>
  builder.buildAreaDownloadUrl('POLYGON(...)', { crs: 'BadCRS' })
).toThrow("The following crs does not exist on this collection: 'BadCRS'.");

// 5. Serialization validation
expect(zParameterToString({ type: 'single', level: 850 })).toBe('850');
expect(DateTimeParameterToEDRString(new Date('2025-01-01'))).toBe(
  '2025-01-01T00:00:00.000Z'
);
```

**Key Difference:** PR #114 tests validate **exact outputs**, **complete structures**, and **meaningful error messages** rather than just checking presence.

---

## 4. Fixture Strategy

### Directory Structure

```
fixtures/ogc-api/
  edr/
    sample-data-hub.json              # Root EDR endpoint
    sample-data-hub/
      conformance.json                # EDR conformance
      collections.json                # Collections list (2 collections)
      reservoir-api.json              # Duplicate (194 lines, simpler)
      collections/
        reservoir-api.json            # Full collection (574 lines)
```

### Fixture Quality

**Real Spec Examples:** ✅ Yes

- Based on USACE (US Army Corps of Engineers) Access2Water API
- Contains realistic parameter names: "Elevation", "Water Temperature", "Inflow", "Outflow"
- Proper EDR data_queries structure with 4 query types (items, locations, cube, area)
- Complete parameter_names with units and observed properties

**Fixture Variations:**

| Variation             | File                           | Purpose                                       |
| --------------------- | ------------------------------ | --------------------------------------------- |
| Minimal EDR endpoint  | sample-data-hub.json           | Root with basic EDR conformance link          |
| Full EDR collection   | reservoir-api.json (574 lines) | Complete `data_queries` and `parameter_names` |
| Simplified collection | reservoir-api.json (194 lines) | Same structure, fewer parameters (3 vs 22)    |
| Non-EDR collection    | ADWR_GWSI_Sites                | Feature collection without EDR support        |

### Fixture Usage Pattern

```typescript
// Setup in beforeAll - mock fetch to read local fixtures
beforeAll(() => {
  globalThis.fetch = jest.fn().mockImplementation(async (urlOrInfo) => {
    const url = new URL(urlOrInfo);
    const queryPath = url.pathname.replace(/\/$/, '');
    const format = url.searchParams.get('f') || 'html';
    const filePath = `${path.join(FIXTURES_ROOT, queryPath)}.${format}`;
    const contents = await readFile(filePath, { encoding: 'utf8' });
    return {
      ok: true,
      json: () => Promise.resolve(JSON.parse(contents)),
    } as Response;
  });
});

// Tests then use real URLs that resolve to fixtures
endpoint = new OgcApiEndpoint('http://local/edr/sample-data-hub');
```

**Key Strategy:** Mock `fetch` at global level to serve fixtures, allowing tests to use real URLs

---

## 5. Coverage Analysis

### Statement, Branch, Function Coverage

**No explicit coverage reports in PR artifacts**, but evidence suggests comprehensive coverage:

1. **All 8 EDR query methods have corresponding test scenarios:**

   - ✅ area
   - ✅ cube
   - ✅ locations
   - ✅ position (via error tests)
   - ✅ radius (via error tests)
   - ✅ trajectory (via error tests)
   - ✅ corridor (via error tests)
   - ✅ instances (via `buildInstancesDownloadUrl()` - returns link)

2. **Error paths systematically tested:**

   - Invalid parameter names (7 methods tested)
   - Invalid CRS (7 methods tested)
   - Invalid bbox (cube query)
   - Unsupported query types (all methods check `supported_query_types`)

3. **Edge cases covered:**
   - Empty optional parameters (all methods)
   - Single vs multiple parameters
   - With/without Z parameter
   - With/without datetime
   - Datetime variations (single date, start only, end only, start+end)
   - Z parameter variations (single, interval, list, repeating)

### Coverage Gaps (Inferred)

1. **url_builder.ts** has no direct unit tests - only integration tests
2. **Corridor and trajectory queries** only have error condition tests, not success cases
3. **Instances query** only returns a static link - minimal test coverage
4. **CRS validation** tests could be more comprehensive (only tests invalid CRS, not all valid ones)

---

## 6. QueryBuilder Test Patterns

### Composition Over Inheritance

```typescript
// OgcApiEndpoint uses composition to access EDR
class OgcApiEndpoint {
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();

  public async edr(collection_id: string): Promise<EDRQueryBuilder> {
    if (cache.has(collection_id)) {
      return cache.get(collection_id); // Caching pattern
    }
    const collection = await this.getCollectionInfo(collection_id);
    const result = new EDRQueryBuilder(collection);
    cache.set(collection_id, result);
    return result;
  }
}
```

**Pattern:** Factory method returns cached query builder instances

### URL Construction Method Testing

```typescript
// General pattern for all 8 query methods
buildAreaDownloadUrl(coords: string, params: optionalAreaParams = {}): string {
  // 1. Check if collection supports this query
  if (!this.supported_query_types.area) {
    throw new Error('Collection does not support area queries');
  }

  // 2. Build base URL from collection data_queries
  const url = new URL(this.collection.data_queries?.area?.link.href);

  // 3. Set required parameters
  url.searchParams.set('coords', coords);

  // 4. Set optional parameters with validation
  if (params.parameter_name) {
    for (const param of params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(`...does not exist...: '${param}'`);
      }
    }
    url.searchParams.set('parameter-name', params.parameter_name.join(','));
  }

  if (params.crs !== undefined) {
    if (!this.supported_crs.includes(params.crs)) {
      throw new Error(`...crs does not exist...: '${params.crs}'`);
    }
    url.searchParams.set('crs', params.crs);
  }

  // 5. Return string URL
  return url.toString();
}
```

**Testing Approach:**

- Test with no optional params (minimal URL)
- Test with each optional param individually
- Test with multiple optional params
- Test validation errors (invalid param, invalid CRS)
- Validate exact URL output including encoding

### Factory Method Testing

```typescript
it('can produce a EDR query builder', async () => {
  const builder = await endpoint.edr('reservoir-api');

  // 1. Check builder was created
  expect(builder).toBeTruthy();

  // 2. Validate builder exposes correct query types
  expect(builder.supported_queries).toEqual(
    new Set(['area', 'locations', 'cube'])
  );

  // 3. Validate builder exposes correct parameters
  expect(Object.keys(builder.supported_parameters)).toEqual([
    'Elevation',
    'Water Temperature',
    'Air Temperature',
  ]);
});
```

### Caching Testing

```typescript
it('caches properly', async () => {
  const spy = jest.spyOn(endpoint, 'getCollectionInfo');

  const builder1 = await endpoint.edr('reservoir-api');
  const builder2 = await endpoint.edr('reservoir-api');

  expect(builder1).toBe(builder2); // Same object is returned
  expect(spy).toHaveBeenCalledTimes(1); // Only called once
});
```

**Pattern:** Verify that repeated calls return the same instance and don't re-fetch collection info

---

## 7. Integration Test Patterns

### What Qualifies as "Integration"

Based on `endpoint.spec.ts` additions:

1. **Endpoint Detection → Query Building Flow:**

   ```typescript
   // Not just unit testing EDRQueryBuilder, but the full flow:
   endpoint = new OgcApiEndpoint('http://local/edr/sample-data-hub');
   const hasEDR = await endpoint.hasEnvironmentalDataRetrieval; // Parse conformance
   const collections = await endpoint.edrCollections; // Parse collections
   const builder = await endpoint.edr('reservoir-api'); // Get collection info + create builder
   const url = builder.buildAreaDownloadUrl(...); // Build query URL
   ```

2. **Multi-Component Interaction:**

   - OgcApiEndpoint (endpoint detection)
   - Info parsers (conformance, collections)
   - Link utilities (resolve data_queries links)
   - EDRQueryBuilder (query construction)

3. **Fixture-Driven Workflows:**
   - Tests use complete fixture chain (root → conformance → collections → collection details)
   - No mocking of internal components - only `fetch` is mocked

### Integration Test Structure

```typescript
describe('OgcApiEndpoint with EDR', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(() => {
    endpoint = new OgcApiEndpoint('http://local/edr/sample-data-hub');
  });

  describe('#info', () => {
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
      expect(builder.supported_queries).toEqual(
        new Set(['area', 'locations', 'cube'])
      );
    });
  });
});
```

**Key Difference from Unit Tests:** Integration tests go through the public API of OgcApiEndpoint, not directly instantiating EDRQueryBuilder

---

## 8. Test Utilities and Helpers

### Mock Fetch Setup

```typescript
// Global fetch mock for all tests
beforeAll(() => {
  globalThis.fetch = jest.fn().mockImplementation(async (urlOrInfo) => {
    const url = new URL(
      urlOrInfo instanceof URL || typeof urlOrInfo === 'string'
        ? urlOrInfo
        : urlOrInfo.url
    );

    // Handle trailing slash requirement
    if (url.pathname.split('/').length === 2 && !url.pathname.endsWith('/')) {
      return { ok: false, status: 404 } as Response;
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
        json: () => Promise.resolve(JSON.parse(contents)),
      } as Response;
    } catch (e) {
      return { ok: false, status: 404 } as Response;
    }
  });
});
```

### Helper Functions

**DateTimeParameterToEDRString (tested in helpers.spec.ts):**

```typescript
export function DateTimeParameterToEDRString(param: DateTimeParameter): string {
  const format = (d: Date) => d.toISOString();

  if (param instanceof Date) {
    return format(param);
  }

  if ('start' in param && 'end' in param) {
    return `${format(param.start)}/${format(param.end)}`;
  }

  if ('start' in param) {
    return `${format(param.start)}/..`;
  }

  if ('end' in param) {
    return `../${format(param.end)}`;
  }

  throw new Error('Invalid DateTimeParameter');
}
```

**zParameterToString (tested in model.spec.ts):**

```typescript
export function zParameterToString(z: ZParameter): string {
  switch (z.type) {
    case 'single':
      return `${z.level}`;
    case 'interval':
      return `${z.minLevel}/${z.maxLevel}`;
    case 'list':
      return z.levels.join(',');
    case 'repeating':
      return `R${z.repeat}/${z.minLevel}/${z.step}`;
  }
}
```

**Pattern:** Small, pure utility functions with dedicated unit tests

---

## 9. Quality Indicators

### What Makes Tests "Good" and Acceptable

Based on PR #114 acceptance:

1. **✅ Type Safety:**

   - Strong TypeScript typing throughout
   - Type-safe optional parameter interfaces (`optionalAreaParams`, etc.)
   - Discriminated unions (`ZParameter` with `type` field)
   - No `any` types

2. **✅ Comprehensive Error Handling:**

   - Tests for all validation paths
   - Meaningful error messages: `"The following parameter name does not exist..."`
   - Validation before URL construction

3. **✅ Spec Compliance:**

   - Every method documented with `@see` links to OGC EDR spec
   - Parameter descriptions match spec terminology
   - Proper encoding of special characters (URL encoding tested)

4. **✅ Real-World Fixtures:**

   - Based on actual USACE API
   - Realistic parameter names and units
   - Complete EDR data structures

5. **✅ Integration Testing:**

   - End-to-end flows tested
   - No mocking of internal components
   - Caching behavior verified

6. **✅ Consistency with Existing Code:**
   - Same patterns as Features, Tiles, Styles implementations
   - Reuses shared utilities (DateTimeParameter type)
   - Follows existing test structure in endpoint.spec.ts

### What Patterns Indicate "Trivial" Tests (Not Found in PR #114)

❌ **Not used:**

- Simple `toContain()` checks without context
- `toBeDefined()` / `toBeTruthy()` without follow-up
- No validation of outputs
- Testing implementation details instead of behavior
- Mocking internal classes

### PR Review Feedback Patterns

**From review comments:**

1. **Composition over inheritance requested:** jahow suggested using composition (`edr()` method) instead of inheritance, which C-Loftus implemented

2. **Type safety emphasized:** Reviewer caught type errors in imports and requested fixes

3. **Code organization:** Suggested using existing `shared` folder instead of new `ogc-common`

4. **Caching pattern:** Reviewer requested caching mechanism similar to other builders

5. **Parameter structure:** Suggested using interface-based optional parameters instead of many positional parameters

**What this tells us:** Upstream values architecture consistency, type safety, and following established patterns

---

## 10. CSAPI Application

### How EDR Patterns Apply to CSAPI

**Direct Applicability:**

1. **✅ QueryBuilder Pattern:** CSAPI needs QueryBuilder classes for Systems, Deployments, Observations, etc. - same pattern as EDRQueryBuilder

2. **✅ Factory Method:** `csapi(collection_id)` factory method that returns collection-specific builder

3. **✅ Optional Parameter Interfaces:** CSAPI resource methods will need similar optional parameter objects

4. **✅ Type-Safe Parameter Modeling:** CSAPI temporal filters, spatial filters can use discriminated unions like `ZParameter`

5. **✅ Validation Before Construction:** Check resource availability, validate parameters before building URLs

6. **✅ Integration Test Structure:** Same pattern of endpoint → collection info → builder → URL construction

**Where CSAPI Differs:**

1. **More Resource Types:** EDR has 1 builder class; CSAPI needs 9 (Systems, Deployments, Procedures, etc.)

2. **Resource References:** CSAPI has nested resources (Systems contain Deployments); EDR collections are flat

3. **CRUD Operations:** CSAPI needs POST/PUT/PATCH/DELETE; EDR only has data retrieval (GET)

4. **Temporal Complexity:** CSAPI temporal filters more complex (phenomenonTime, resultTime, validTime all have different semantics)

### Adaptations Needed for CSAPI

1. **Multi-Builder Architecture:**

   ```typescript
   // Instead of one EDRQueryBuilder, CSAPI needs:
   const systemsBuilder = await endpoint.csapi('systems');
   const deploymentsBuilder = await endpoint.csapi('deployments');
   // etc.
   ```

2. **CRUD Method Pattern:**

   ```typescript
   // EDR only has buildXxxDownloadUrl()
   // CSAPI needs:
   buildGetSystemsUrl(params);
   buildGetSystemUrl(id, params);
   buildPostSystemUrl(body);
   buildPutSystemUrl(id, body);
   buildPatchSystemUrl(id, body);
   buildDeleteSystemUrl(id);
   ```

3. **Resource Reference Validation:**

   ```typescript
   // CSAPI needs to validate related resources
   buildPostDeploymentUrl(systemId, deploymentBody) {
     // Validate systemId exists
     // Validate deployment references valid system
   }
   ```

4. **Nested Resource Queries:**
   ```typescript
   // CSAPI needs nested patterns
   system.getDataStreams(); // Get all DataStreams for a System
   system.getDeployments(); // Get all Deployments for a System
   ```

### Actionable Recommendations for CSAPI Testing

1. **Test File Organization:**

   ```
   src/ogc-api/csapi/
     helpers.spec.ts          # Temporal filter serialization
     model.spec.ts            # Type definitions (like ZParameter)
     systems-builder.spec.ts  # SystemsQueryBuilder unit tests
     // ... one per resource type

   src/ogc-api/
     endpoint.spec.ts         # Integration tests (modify existing)
   ```

2. **Fixture Strategy:**

   ```
   fixtures/ogc-api/csapi/
     sample-csapi-endpoint.json       # Root
     sample-csapi-endpoint/
       conformance.json               # CSAPI conformance
       collections.json               # All 9 resource collections
       collections/
         systems.json                 # Systems collection
         deployments.json             # Deployments collection
         // ... one per resource type
   ```

3. **Test Prioritization:**

   - **HIGH:** Systems QueryBuilder (simplest, foundation)
   - **HIGH:** Integration tests (endpoint detection → builder creation)
   - **MEDIUM:** Deployments, DataStreams QueryBuilders (temporal complexity)
   - **MEDIUM:** Nested resource queries
   - **LOW:** Remaining 6 resource types (follow established pattern)

4. **Assertion Depth:**
   - Use PR #114's exact URL matching pattern
   - Validate complete query parameter encoding
   - Test all error paths (invalid references, missing required fields)
   - Verify type-safe parameter handling

---

## 11. Scaling Patterns for CSAPI's Broader Scope

### Challenge: 9 Resource Types vs 1 EDR Builder

**EDR:** 1 `EDRQueryBuilder` class with 8 query methods  
**CSAPI:** Needs 9 builder classes × 6 CRUD operations = 54 URL builder methods

### Scaling Strategy

**Option 1: Separate Builder per Resource Type** (Recommended)

```typescript
class SystemsQueryBuilder extends CSAPIQueryBuilder {
  // Inherits base CRUD methods
  // Adds Systems-specific methods
  buildGetSystemsUrl(params: GetSystemsParams): string {}
  buildGetSystemUrl(id: string): string {}
  buildPostSystemUrl(body: SystemBody): string {}
  // ...
}

class DeploymentsQueryBuilder extends CSAPIQueryBuilder {
  // Inherits base CRUD methods
  // Adds Deployments-specific methods (validTime filter)
}
```

**Testing Pattern:**

- Base class unit tests for common CRUD logic
- Per-resource tests for resource-specific parameters
- ~15-20 tests per resource type (12 base + resource-specific)

**Option 2: Single Parameterized Builder** (Not Recommended)

```typescript
class CSAPIQueryBuilder {
  buildGetUrl(resourceType: 'systems' | 'deployments' | ..., params) { }
  buildPostUrl(resourceType, body) { }
}
```

**Problem:** Loses type safety, harder to maintain

### Pattern Reusability

**From EDR to CSAPI:**

1. **URL Construction Pattern:** ✅ Reusable

   ```typescript
   const url = new URL(baseUrl);
   url.searchParams.set(key, value);
   return url.toString();
   ```

2. **Parameter Validation Pattern:** ✅ Reusable

   ```typescript
   if (!this.supportedParameters[param]) {
     throw new Error(`Parameter ${param} not supported`);
   }
   ```

3. **Optional Parameters Interface:** ✅ Reusable

   ```typescript
   type OptionalSystemsParams = {
     systemType?: string;
     parent?: string;
     limit?: number;
     offset?: number;
   };
   ```

4. **Factory Method + Caching:** ✅ Reusable

   ```typescript
   async csapi(resourceType: string): Promise<CSAPIQueryBuilder> {
     if (cache.has(resourceType)) return cache.get(resourceType);
     // ...
   }
   ```

5. **Integration Test Structure:** ✅ Reusable
   ```typescript
   describe('OgcApiEndpoint with CSAPI', () => {
     it('can produce a Systems query builder', async () => {
       const builder = await endpoint.csapi('systems');
       expect(builder.supportedOperations).toContain('GET');
     });
   });
   ```

---

## 12. Code Examples

### Example 1: Type-Safe Optional Parameters

```typescript
// EDR Pattern
export type optionalAreaParams = {
  parameter_name?: string[];
  z?: ZParameter;
  datetime?: DateTimeParameter;
  crs?: string;
  f?: string;
};

buildAreaDownloadUrl(
  coords: WellKnownTextString,
  optional_params: optionalAreaParams = {}
): string {
  const url = new URL(this.collection.data_queries?.area?.link.href);
  url.searchParams.set('coords', coords);

  if (optional_params.z !== undefined)
    url.searchParams.set('z', zParameterToString(optional_params.z));

  if (optional_params.datetime !== undefined)
    url.searchParams.set(
      'datetime',
      DateTimeParameterToEDRString(optional_params.datetime)
    );

  return url.toString();
}

// CSAPI Application
export type GetSystemsParams = {
  systemType?: string;  // vocabulary term
  parent?: string;      // URI reference
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
};

buildGetSystemsUrl(params: GetSystemsParams = {}): string {
  const url = new URL(`${this.baseUrl}/collections/systems/items`);

  if (params.systemType !== undefined)
    url.searchParams.set('systemType', params.systemType);

  if (params.parent !== undefined)
    url.searchParams.set('parent', params.parent);

  if (params.limit !== undefined)
    url.searchParams.set('limit', params.limit.toString());

  return url.toString();
}
```

### Example 2: Discriminated Union for Parameter Types

```typescript
// EDR Pattern
export type ZParameter =
  | { type: 'single'; level: number }
  | { type: 'interval'; minLevel: number; maxLevel: number }
  | { type: 'list'; levels: number[] }
  | { type: 'repeating'; repeat: number; minLevel: number; step: number };

export function zParameterToString(z: ZParameter): string {
  switch (z.type) {
    case 'single':
      return `${z.level}`;
    case 'interval':
      return `${z.minLevel}/${z.maxLevel}`;
    case 'list':
      return z.levels.join(',');
    case 'repeating':
      return `R${z.repeat}/${z.minLevel}/${z.step}`;
  }
}

// CSAPI Application
export type TemporalFilter =
  | { type: 'instant'; time: Date }
  | { type: 'interval'; start: Date; end: Date }
  | { type: 'open-start'; end: Date }
  | { type: 'open-end'; start: Date };

export function temporalFilterToString(filter: TemporalFilter): string {
  const format = (d: Date) => d.toISOString();
  switch (filter.type) {
    case 'instant':
      return format(filter.time);
    case 'interval':
      return `${format(filter.start)}/${format(filter.end)}`;
    case 'open-start':
      return `../${format(filter.end)}`;
    case 'open-end':
      return `${format(filter.start)}/..`;
  }
}
```

### Example 3: Validation Pattern

```typescript
// EDR Pattern
if (optional_params.parameter_name) {
  for (const param of optional_params.parameter_name) {
    if (!this.supported_parameters[param]) {
      throw new Error(
        `The following parameter name does not exist on this collection: '${param}'.`
      );
    }
  }
  url.searchParams.set(
    'parameter-name',
    optional_params.parameter_name.join(',')
  );
}

// CSAPI Application
if (params.systemType) {
  if (!this.supportedSystemTypes.includes(params.systemType)) {
    throw new Error(
      `Invalid systemType: '${
        params.systemType
      }'. Supported: ${this.supportedSystemTypes.join(', ')}`
    );
  }
  url.searchParams.set('systemType', params.systemType);
}
```

### Example 4: Integration Test Pattern

```typescript
// EDR Pattern
describe('OgcApiEndpoint with EDR', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(() => {
    endpoint = new OgcApiEndpoint('http://local/edr/sample-data-hub');
  });

  it('can produce a EDR query builder', async () => {
    const builder = await endpoint.edr('reservoir-api');
    expect(builder).toBeTruthy();
    expect(builder.supported_queries).toEqual(
      new Set(['area', 'locations', 'cube'])
    );
  });
});

// CSAPI Application
describe('OgcApiEndpoint with CSAPI', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(() => {
    endpoint = new OgcApiEndpoint('http://local/csapi/sample-endpoint');
  });

  it('can produce a Systems query builder', async () => {
    const builder = await endpoint.csapi('systems');
    expect(builder).toBeTruthy();
    expect(builder.supportedOperations).toEqual([
      'GET',
      'POST',
      'PUT',
      'PATCH',
      'DELETE',
    ]);
    expect(builder.resourceType).toBe('systems');
  });

  it('can build Systems GET collection URL', async () => {
    const builder = await endpoint.csapi('systems');
    const url = builder.buildGetSystemsUrl({ systemType: 'sensor', limit: 10 });
    expect(url).toContain('/collections/systems/items');
    expect(url).toContain('systemType=sensor');
    expect(url).toContain('limit=10');
  });
});
```

### Example 5: Error Test Pattern

```typescript
// EDR Pattern
it('throws an error with invalid bbox for cube query', async () => {
  const builder = await endpoint.edr('reservoir-api');
  expect(() =>
    builder.buildCubeDownloadUrl({
      minX: 0,
      minY: 10,
      maxX: -10, // Invalid: maxX < minX
      maxY: 12,
    })
  ).toThrow('minX must be less than or equal to maxX');
});

// CSAPI Application
it('throws error with invalid systemType', async () => {
  const builder = await endpoint.csapi('systems');
  expect(() =>
    builder.buildGetSystemsUrl({ systemType: 'invalid-type' })
  ).toThrow("Invalid systemType: 'invalid-type'");
});

it('throws error with invalid parent reference', async () => {
  const builder = await endpoint.csapi('systems');
  expect(() => builder.buildGetSystemsUrl({ parent: 'not-a-uri' })).toThrow(
    'parent must be a valid URI'
  );
});
```

---

## Summary

PR #114 provides a **comprehensive blueprint** for CSAPI testing with:

- ✅ Clear test organization (unit tests for utilities, integration tests for flows)
- ✅ Type-safe parameter handling with discriminated unions
- ✅ Validation-before-construction pattern
- ✅ Real-world fixtures from actual APIs
- ✅ Exact URL matching in assertions
- ✅ Comprehensive error condition coverage
- ✅ Factory method + caching pattern
- ✅ Composition over inheritance

**Key Takeaway:** CSAPI should follow the same patterns but scale to 9 resource types with CRUD operations, using inheritance from a base `CSAPIQueryBuilder` class to share common logic while allowing resource-specific extensions.
