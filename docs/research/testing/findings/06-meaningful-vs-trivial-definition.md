# Meaningful vs Trivial Test Quality Guide

**Research Plan:** [Research Plan 06: Meaningful vs Trivial Definition](../research-plans/06-meaningful-vs-trivial-definition.md)  
**Research Questions:** 56 questions about test quality dimensions, assertion depth criteria, fixture quality standards, coverage depth standards, test organization patterns, and objective quality checklist validation  
**Methodology:** 3-phase systematic analysis (Previous iteration analysis of lessons learned and gap analysis → Pattern synthesis from Sections 1-4 deliverables → Concrete examples creation with side-by-side comparisons)  
**Research Time:** ~2 hours (February 5, 2026)

**Primary Source(s):**

- Lessons Learned Analysis (previous iteration feedback on test quality issues)
- Gap Analysis (specific feedback from senior developer on trivial tests)
- EDR Blueprint PR #114 (meaningful assertion patterns from upstream)

**Supporting Resources:**

- Section 1: Upstream Blueprint Analysis (PR #114 quality patterns)
- Section 2: Upstream Test Consistency (mature pattern examples across 6 implementations)
- Section 3: TypeScript Testing Standards (industry quality benchmarks)
- Section 4: Implementation Guide Testing Requirements (architectural context)

**Document Purpose:** Define objective, measurable criteria to distinguish meaningful tests (deep validation, edge cases, error handling, real fixtures) from trivial tests (superficial assertions, happy-path-only, synthetic mocks) with concrete side-by-side examples and actionable quality checklist for CSAPI test writing and review.

---

## Executive Summary

Previous CSAPI implementation was rejected for having tests that were "**not meaningful, useful, deep, or end-to-end**." This guide defines concrete, objective criteria for test quality based on:

1. **Specific feedback** from previous iteration (lessons learned)
2. **Proven patterns** from accepted upstream PRs (EDR PR #114)
3. **Industry standards** for TypeScript client library testing

### Core Rejection Reasons

From lessons learned analysis, previous tests were insufficient because they:

1. **Checked method existence, not behavior** - Tests verified functions existed but didn't validate output
2. **Lacked real spec examples** - Used synthetic, trivial mocks instead of actual OGC CSAPI spec examples
3. **Didn't validate complete URL structures** - Used substring matching (`toContain`) instead of complete validation
4. **Edge cases not thoroughly tested** - Only happy paths, missing null/undefined/empty/error conditions
5. **High line count, low value per test** - Many trivial tests inflated LOC without adding meaningful coverage

### Objective Quality Checklist

✅ **A meaningful test:**

- [ ] Validates **complete structure** (full URL, not substring)
- [ ] Tests **multiple scenarios** (happy path + edge cases + errors)
- [ ] Uses **real spec examples** as fixtures (not synthetic mocks)
- [ ] Validates **exact outputs** with deep assertions (parseUrl, exact equality)
- [ ] Tests **parameter combinations** (not just single values)
- [ ] Validates **encoding** (special characters, spaces, reserved chars)
- [ ] Tests **error messages** (not just that error was thrown)
- [ ] Has **clear intent** from test name (what behavior is tested)
- [ ] Tests **behavior**, not implementation details

❌ **A trivial test:**

- [ ] Only checks substring existence (`toContain('systems')`)
- [ ] Only checks truthiness (`toBeTruthy()`, `toBeDefined()`)
- [ ] Only checks type (`typeof === 'function'`, `typeof === 'string'`)
- [ ] Only tests happy path (no edge cases, no errors)
- [ ] Uses generic error checking (`toThrow()` without message validation)
- [ ] Tests one parameter value (no variations)
- [ ] Has vague test name ("should work", "should return value")

---

## 1. Definitions

### Meaningful

**Definition:** A test that validates **actual behavior** with **complete validation** of outputs, **real data**, and **comprehensive scenarios** (happy path + edge cases + errors).

**Objective Characteristics:**

1. **Complete validation** - Checks full structure, not just existence (URL path + query + encoding)
2. **Deep assertions** - Validates nested properties, array contents, object structure
3. **Real data** - Uses actual OGC CSAPI spec examples, not synthetic mocks
4. **Multiple scenarios** - Happy path + edge cases (null, empty, large) + error cases
5. **Specific errors** - Validates error types and messages, not just that error occurred
6. **Encoding verification** - Tests special characters, spaces, reserved characters
7. **Self-documenting** - Test name clearly states what is being validated

**Example:**

```typescript
// ✅ MEANINGFUL: Validates complete URL structure with parseUrl
it('should build Systems URL with bbox and datetime parameters', () => {
  const url = builder.getSystems({
    bbox: [-180, -90, 180, 90],
    datetime: '2024-01-01T00:00:00Z/..',
  });

  const parsed = new URL(url);
  expect(parsed.pathname).toBe('/collections/sensors/items');
  expect(parsed.searchParams.get('bbox')).toBe('-180,-90,180,90');
  expect(parsed.searchParams.get('datetime')).toBe('2024-01-01T00:00:00Z/..');
});
```

### Useful

**Definition:** A test that provides **value** to developers by catching real bugs, enabling confident refactoring, and documenting expected behavior.

**Useful to:**

1. **Developers** - Catches bugs during development (regression detection)
2. **Maintainers** - Documents expected behavior (self-documenting tests)
3. **Future contributors** - Shows how to use the API (usage examples)
4. **Code reviewers** - Validates implementation correctness

**Objective Measures:**

1. **Bug detection** - Would this test catch a real bug? (e.g., parameter encoding regression)
2. **Refactoring safety** - Can I refactor with confidence this test will catch issues?
3. **Documentation value** - Does this test show how to use the API?
4. **Specificity** - Does failure clearly indicate what broke?

**Example:**

```typescript
// ✅ USEFUL: Catches parameter encoding bugs
it('should properly encode special characters in System ID', () => {
  const url = builder.getSystem('sys-123/special?chars&more');
  expect(url).toContain('sys-123%2Fspecial%3Fchars%26more');
});

// This test is useful because:
// 1. Catches encoding regressions (if encoding breaks, test fails)
// 2. Documents expected encoding behavior (future contributors see how it works)
// 3. Specific failure (if fails, clearly encoding is broken)
// 4. Enables refactoring (can change URL builder implementation safely)
```

### Deep

**Definition:** A test that validates **multiple layers** of structure, **comprehensive parameter combinations**, and **all edge cases** rather than surface-level checks.

**Depth Dimensions:**

1. **Assertion depth** - Validates nested properties, not just top-level
2. **Case coverage depth** - Tests minimal, typical, maximal, edge, error cases (5 scenarios)
3. **Parameter combination depth** - Tests multiple parameters together, not just single values
4. **Error handling depth** - Tests all error types with message validation
5. **Encoding depth** - Tests simple + complex + reserved + Unicode characters

**Depth by Component Type:**

| Component            | Shallow (Trivial)                  | Deep (Meaningful)                                                                 |
| -------------------- | ---------------------------------- | --------------------------------------------------------------------------------- |
| **URL Construction** | `toContain('systems')`             | `parseUrl(url).pathname === '/collections/sensors/items'`                         |
| **Query Parameters** | `toContain('limit=10')`            | `parseUrl(url).query === {limit: '10', bbox: '...', datetime: '...'}`             |
| **Format Parsing**   | `result.type === 'PhysicalSystem'` | Validate type + components[0].name + components[0].position + nested capabilities |
| **Error Handling**   | `toThrow()`                        | `toThrow(EndpointError)` + `error.message.toMatch(/resource not available/)`      |
| **Type Validation**  | Type compiles                      | Runtime validation + all union cases + constraint validation                      |

**Example:**

```typescript
// ❌ SHALLOW: Only checks top-level property
it('should parse SensorML PhysicalSystem', () => {
  const result = parser.parse(fixture);
  expect(result.type).toBe('PhysicalSystem');
});

// ✅ DEEP: Validates nested structure with multiple levels
it('should parse SensorML PhysicalSystem with complete component hierarchy', () => {
  const result = parser.parse(physicalSystemFixture);

  expect(result.type).toBe('PhysicalSystem');
  expect(result.identification.identifier).toBe(
    'urn:x-noaa:def:system:noaa::station-NDBC-41001'
  );
  expect(result.components).toHaveLength(3);
  expect(result.components[0].name).toBe('wind_sensor');
  expect(result.components[0].type).toBe('PhysicalComponent');
  expect(result.components[0].position.coordinates).toEqual([
    25.9, -89.67, -999,
  ]);
  expect(result.components[0].capabilities).toHaveProperty('MeasurementRange');
  expect(result.components[0].capabilities.MeasurementRange.min).toBe(0);
  expect(result.components[0].capabilities.MeasurementRange.max).toBe(100);
});
```

### End-to-End

**Definition:** For a **URL-building library** (not a data-fetching library), "end-to-end" means testing **complete workflows** involving **multiple methods/components** working together, not comprehensive integration tests with actual HTTP calls.

**E2E Scope for CSAPI Client:**

- **IN SCOPE:** Multi-component URL building workflows (endpoint detection → collection listing → query builder creation → URL construction)
- **IN SCOPE:** Cross-resource navigation (System → DataStreams → Observations)
- **IN SCOPE:** Format parameter flows (query with format → validate format support → build URL with format param)
- **OUT OF SCOPE:** Actual HTTP requests (library doesn't fetch data)
- **OUT OF SCOPE:** Response parsing (users handle responses)
- **OUT OF SCOPE:** Server validation (trust server to validate)

**E2E vs Integration vs Unit:**

| Test Type       | Scope                                   | Example                                                                             |
| --------------- | --------------------------------------- | ----------------------------------------------------------------------------------- |
| **Unit**        | Single function in isolation            | `buildQueryString({ limit: 10 })` returns `?limit=10`                               |
| **Integration** | Multiple functions, single component    | `builder.getSystems()` uses helpers + URL class + param encoding                    |
| **End-to-End**  | Multiple components, realistic workflow | `endpoint.csapi('systems') → builder.getSystems() → builder.getSystemDataStreams()` |

**What makes e2e test meaningful vs trivial:**

❌ **Trivial e2e:**

```typescript
// Only tests one method in isolation (not actually end-to-end)
it('should work end-to-end', async () => {
  const endpoint = new OgcApiEndpoint('http://test/csapi/');
  const builder = await endpoint.csapi('systems');
  const url = builder.getSystems();
  expect(url).toBeDefined();
});
```

✅ **Meaningful e2e:**

```typescript
// Tests complete workflow: detection → collection → query → navigation
it('should support complete workflow from endpoint detection to cross-resource query', async () => {
  // 1. Endpoint detection
  const endpoint = new OgcApiEndpoint('http://test/csapi/');
  expect(await endpoint.hasConnectedSystems).toBe(true);

  // 2. Collection listing
  const collections = await endpoint.csapiCollections;
  expect(collections).toContainEqual(
    expect.objectContaining({ id: 'systems' })
  );

  // 3. Query builder creation
  const builder = await endpoint.csapi('systems');
  expect(builder.availableResources).toContain('systems');
  expect(builder.availableResources).toContain('datastreams');

  // 4. URL construction
  const systemsUrl = builder.getSystems({ limit: 10 });
  expect(new URL(systemsUrl).searchParams.get('limit')).toBe('10');

  // 5. Cross-resource navigation
  const datastreamsUrl = builder.getSystemDataStreams('sys-123');
  expect(new URL(datastreamsUrl).pathname).toContain(
    '/systems/items/sys-123/datastreams'
  );
});
```

### Trivial

**Definition:** A test that checks **superficial properties** (existence, type, truthiness) without validating **actual behavior**, uses **synthetic data**, and covers only **happy paths** without edge cases or errors.

**Trivial Indicators:**

1. **Superficial assertions** - `toContain`, `toBeTruthy`, `toBeDefined`, `typeof`
2. **Single scenario** - Only happy path, no edge cases
3. **No error testing** - Doesn't test what happens when things go wrong
4. **Vague test names** - "should work", "should return value"
5. **Synthetic fixtures** - Not from real spec examples
6. **No encoding tests** - Doesn't test special characters
7. **Implementation-focused** - Tests how it works, not what it does

**Anti-Pattern Examples:**

```typescript
// ❌ TRIVIAL: Only checks method exists
it('should have getSystems method', () => {
  expect(typeof builder.getSystems).toBe('function');
});

// ❌ TRIVIAL: Only checks return type
it('should return string', () => {
  expect(typeof builder.getSystems()).toBe('string');
});

// ❌ TRIVIAL: Only checks substring
it('should contain systems', () => {
  const url = builder.getSystems();
  expect(url).toContain('systems');
});

// ❌ TRIVIAL: Only checks truthiness
it('should return a value', () => {
  expect(builder.getSystems()).toBeTruthy();
});

// ❌ TRIVIAL: Generic error check
it('should throw error', () => {
  expect(() => builder.getSystem()).toThrow();
});
```

---

## 2. Meaningful Test Characteristics

### Assertion Depth Criteria

**Standard:** Use `new URL()` parsing for complete validation, not substring matching.

```typescript
// ❌ TRIVIAL: Substring matching
expect(url).toContain('systems');
expect(url).toContain('limit=10');

// ✅ MEANINGFUL: Complete URL validation
const parsed = new URL(url);
expect(parsed.protocol).toBe('https:');
expect(parsed.host).toBe('api.example.com');
expect(parsed.pathname).toBe('/collections/sensors/items');
expect(parsed.searchParams.get('limit')).toBe('10');
expect(parsed.searchParams.get('bbox')).toBe('-180,-90,180,90');
```

**Pattern from EDR PR #114:**

```typescript
// PR #114 used exact URL string matching
expect(url).toEqual(
  'https://dummy.edr.app/collections/reservoir-api/area?coords=POLYGON%28%28-1.0+50.0...'
);

// And component validation
expect(url).toContain('parameter-name=Water+Temperature');
expect(url).toContain('z=1');
```

### Edge Case Coverage Criteria

**Standard:** Test 5 scenario types for each method: minimal, typical, maximal, edge, error.

| Scenario Type | Description             | Example (getSystems)                                                             |
| ------------- | ----------------------- | -------------------------------------------------------------------------------- |
| **Minimal**   | No optional parameters  | `getSystems()` with no options                                                   |
| **Typical**   | Common use case         | `getSystems({ limit: 10, offset: 0 })`                                           |
| **Maximal**   | All optional parameters | `getSystems({ limit: 100, bbox: [...], datetime: '...', systemType: 'sensor' })` |
| **Edge**      | Boundary conditions     | Empty string, null, undefined, very large values, empty arrays                   |
| **Error**     | Invalid inputs          | Invalid bbox, unsupported systemType, negative limit                             |

**Example:**

```typescript
describe('getSystems', () => {
  it('builds minimal URL with no parameters', () => {
    const url = builder.getSystems();
    expect(new URL(url).search).toBe('');
  });

  it('builds typical URL with pagination', () => {
    const url = builder.getSystems({ limit: 10, offset: 20 });
    const parsed = new URL(url);
    expect(parsed.searchParams.get('limit')).toBe('10');
    expect(parsed.searchParams.get('offset')).toBe('20');
  });

  it('builds maximal URL with all parameters', () => {
    const url = builder.getSystems({
      limit: 100,
      bbox: [-180, -90, 180, 90],
      datetime: '2024-01-01T00:00:00Z/..',
      systemType: 'sensor',
    });
    const parsed = new URL(url);
    expect(parsed.searchParams.get('limit')).toBe('100');
    expect(parsed.searchParams.get('bbox')).toBe('-180,-90,180,90');
    expect(parsed.searchParams.get('datetime')).toBe('2024-01-01T00:00:00Z/..');
    expect(parsed.searchParams.get('systemType')).toBe('sensor');
  });

  it('handles edge case: undefined parameters', () => {
    const url = builder.getSystems({ limit: undefined, offset: undefined });
    expect(new URL(url).search).toBe(''); // No query params added
  });

  it('throws error for invalid bbox', () => {
    expect(() => builder.getSystems({ bbox: [1, 2, 3] })).toThrow(
      'bbox must have 4 values'
    );
  });
});
```

### Error Handling Criteria

**Standard:** Test error type + error message, not just that error was thrown.

```typescript
// ❌ TRIVIAL: Generic error check
expect(() => fn()).toThrow();

// ✅ MEANINGFUL: Specific error type + message validation
expect(() => fn()).toThrow(EndpointError);
expect(() => {
  try {
    fn();
  } catch (e) {
    expect(e.message).toMatch(/resource not available in collection/);
    throw e;
  }
}).toThrow();

// ✅ BETTER: Use Jest matcher for both
expect(() => fn()).toThrow(
  expect.objectContaining({
    name: 'EndpointError',
    message: expect.stringMatching(/resource not available/),
  })
);
```

**Pattern from EDR PR #114:**

```typescript
// EDR tests validated exact error messages
expect(() =>
  builder.buildAreaDownloadUrl('POLYGON(...)', { crs: 'BadCRS' })
).toThrow("The following crs does not exist on this collection: 'BadCRS'.");

expect(() =>
  builder.buildCubeDownloadUrl({ minX: 0, minY: 10, maxX: -10, maxY: 12 })
).toThrow('minX must be less than or equal to maxX');
```

### Fixture Quality Criteria

**Standard:** Use **real OGC CSAPI spec examples**, not synthetic mocks.

✅ **Real Spec Examples:**

- Example Systems from OGC CSAPI Part 1 spec (weather stations, sensor networks)
- Example Observations from OGC CSAPI Part 2 spec (temperature readings, wind measurements)
- Example SensorML from OGC SensorML 2.0 spec (physical systems, simple processes)
- Example SWE Common from OGC SWE Common 2.0 spec (DataRecord, DataArray)

❌ **Synthetic Mocks (Trivial):**

```typescript
// ❌ TRIVIAL: Made-up fixture
const mockSystem = {
  id: '123',
  name: 'test',
  type: 'system',
};
```

✅ **Real Fixture (Meaningful):**

```typescript
// ✅ MEANINGFUL: From OGC CSAPI spec
const weatherStationSystem = {
  id: 'urn:x-noaa:def:system:noaa::station-NDBC-41001',
  type: 'Feature',
  geometry: {
    type: 'Point',
    coordinates: [-89.67, 25.9, 0],
  },
  properties: {
    featureType: 'sosa:System',
    name: 'NOAA NDBC Station 41001',
    description: 'National Buoy 41001 - 150 NM East of Cape HATTERAS',
    systemKind: 'sosa:Platform',
    assetType: 'Mooring',
    uniqueIdentifier: 'urn:x-noaa:def:system:noaa::station-NDBC-41001',
  },
};
```

**Fixture Provenance:**

- Document where fixtures came from (OGC CSAPI spec section X.Y.Z)
- Include spec URL in comment
- Update fixtures when spec changes
- Use realistic values (not 'test', '123', 'foo')

### Test Organization Criteria

**Standard:** Hierarchical describe/it structure with clear grouping by feature.

```typescript
// ✅ MEANINGFUL: Clear hierarchical structure
describe('CSAPIQueryBuilder', () => {
  describe('constructor', () => {
    it('extracts available resources from collection info', () => { ... });
    it('throws when collection lacks systems resource', () => { ... });
  });

  describe('Systems methods', () => {
    describe('getSystems', () => {
      it('builds URL with no parameters', () => { ... });
      it('builds URL with pagination', () => { ... });
      it('builds URL with spatial filter', () => { ... });
      it('throws when systems resource unavailable', () => { ... });
    });

    describe('getSystem', () => {
      it('builds URL for single system', () => { ... });
      it('encodes special characters in ID', () => { ... });
    });
  });

  describe('DataStreams methods', () => { ... });
});
```

---

## 3. Trivial Test Anti-Patterns

### Superficial Assertions (Most Common Issue)

**Anti-Pattern:** Only checking substring existence or truthiness.

```typescript
// ❌ TRIVIAL: Substring check doesn't validate structure
it('should build systems URL', () => {
  const url = builder.getSystems();
  expect(url).toContain('systems');
});
// Problem: Passes even if URL is malformed, has wrong path, missing protocol

// ❌ TRIVIAL: Truthiness check doesn't validate content
it('should return a result', () => {
  const result = parser.parse(fixture);
  expect(result).toBeTruthy();
});
// Problem: Passes even if result is wrong type, has wrong properties

// ❌ TRIVIAL: Type check doesn't validate behavior
it('should return string', () => {
  expect(typeof builder.getSystems()).toBe('string');
});
// Problem: Passes even if string is empty, malformed, wrong URL
```

### Happy-Path-Only Coverage

**Anti-Pattern:** Only testing the success case, ignoring errors and edge cases.

```typescript
// ❌ TRIVIAL: Only happy path
describe('getSystems', () => {
  it('should build URL', () => {
    const url = builder.getSystems({ limit: 10 });
    expect(url).toContain('limit=10');
  });
});

// Missing: What if limit is 0? Negative? Undefined? String instead of number?
// Missing: What if systems resource unavailable?
// Missing: What if bbox is invalid?
// Missing: What if datetime is malformed?
```

### Synthetic Fixtures Without Edge Cases

**Anti-Pattern:** Creating minimal, made-up fixtures that don't represent real data.

```typescript
// ❌ TRIVIAL: Synthetic, minimal fixture
const mockCollection = {
  id: 'test',
  title: 'Test Collection',
};

// Problems:
// 1. Not from real spec - might not match actual structure
// 2. Missing properties - doesn't test handling of complete objects
// 3. No edge cases - doesn't test nullable/optional properties
// 4. No realistic values - doesn't catch real bugs
```

### Vague Test Intent

**Anti-Pattern:** Test names that don't describe what is being validated.

```typescript
// ❌ TRIVIAL: Vague names
it('should work', () => { ... });
it('should return value', () => { ... });
it('test getSystems', () => { ... });
it('builder methods', () => { ... });

// ✅ MEANINGFUL: Specific names
it('should build systems URL with bbox parameter encoded correctly', () => { ... });
it('should throw EndpointError when systems resource unavailable', () => { ... });
it('should parse SensorML PhysicalSystem with nested component hierarchy', () => { ... });
```

### Missing Error Conditions

**Anti-Pattern:** Not testing what happens when things go wrong.

```typescript
// ❌ TRIVIAL: Only tests success
describe('getSystem', () => {
  it('should get single system', () => {
    const url = builder.getSystem('sys-123');
    expect(url).toContain('sys-123');
  });
});

// Missing error tests:
// - What if ID is null?
// - What if ID contains special characters?
// - What if systems resource unavailable?
// - What if ID is empty string?
// - What if ID is extremely long?
```

### Incomplete Validation

**Anti-Pattern:** Only checking part of the structure, not the whole output.

```typescript
// ❌ TRIVIAL: Partial validation
it('should parse SensorML', () => {
  const result = parser.parse(fixture);
  expect(result.type).toBe('PhysicalSystem');
  // Only checks type, doesn't validate components, position, capabilities, etc.
});

// ✅ MEANINGFUL: Complete validation
it('should parse SensorML PhysicalSystem with all properties', () => {
  const result = parser.parse(fixture);
  expect(result.type).toBe('PhysicalSystem');
  expect(result.identification).toBeDefined();
  expect(result.classification).toBeDefined();
  expect(result.validTime).toBeDefined();
  expect(result.capabilities).toBeDefined();
  expect(result.components).toHaveLength(3);
  expect(result.position.coordinates).toEqual([x, y, z]);
});
```

---

## 4. Side-by-Side Examples: URL Construction

### Example 1: Basic Collection Query

❌ **TRIVIAL:**

```typescript
it('should build systems URL', () => {
  const url = builder.getSystems();
  expect(url).toContain('systems');
});
```

**Why trivial:**

- Only checks substring existence
- Doesn't validate protocol, host, path structure
- Would pass even if URL was "http://wrong.com/bad/systems/wrong"
- Doesn't test that query string is empty
- Low value: wouldn't catch most bugs

✅ **MEANINGFUL:**

```typescript
it('should build systems collection URL with correct structure', () => {
  const url = builder.getSystems();
  const parsed = new URL(url, 'http://localhost'); // Ensure parseable
  expect(parsed.pathname).toBe('/collections/sensors/items');
  expect(parsed.search).toBe(''); // No query parameters when none provided
});
```

**Why meaningful:**

- Validates complete URL structure
- Uses URL parsing for robust validation
- Tests specific behavior (no query params when not provided)
- High value: would catch path bugs, query param leaks
- Self-documenting: clearly states expected behavior

---

### Example 2: Query Parameters

❌ **TRIVIAL:**

```typescript
it('should add limit parameter', () => {
  const url = builder.getSystems({ limit: 10 });
  expect(url).toContain('limit=10');
});
```

**Why trivial:**

- Only checks substring presence
- Doesn't validate other parameters weren't added
- Doesn't validate encoding
- Doesn't test parameter position in query string
- Would pass even if URL had extra unwanted parameters

✅ **MEANINGFUL:**

```typescript
it('should build systems URL with pagination parameters only', () => {
  const url = builder.getSystems({ limit: 10, offset: 20 });
  const parsed = new URL(url, 'http://localhost');

  // Validate only expected parameters present
  expect(parsed.searchParams.get('limit')).toBe('10');
  expect(parsed.searchParams.get('offset')).toBe('20');
  expect(Array.from(parsed.searchParams.keys())).toEqual(['limit', 'offset']);

  // Validate path unchanged
  expect(parsed.pathname).toBe('/collections/sensors/items');
});
```

**Why meaningful:**

- Validates exact parameter set (no extras)
- Uses URL parsing for reliable validation
- Tests parameter values as strings (how they appear in URL)
- Validates path is correct
- Would catch bugs where unexpected parameters added

---

### Example 3: Parameter Encoding

❌ **TRIVIAL:**

```typescript
it('should handle special characters', () => {
  const url = builder.getSystem('sys-123');
  expect(url).toContain('sys-123');
});
```

**Why trivial:**

- Doesn't actually test special characters (none in 'sys-123')
- Doesn't validate encoding
- Would pass even if special chars weren't encoded
- Title says "special characters" but doesn't test them

✅ **MEANINGFUL:**

```typescript
it('should properly encode special characters in system ID', () => {
  const url = builder.getSystem('sys-123/special?chars&more');

  // Validate URL-encoded format
  expect(url).toContain('sys-123%2Fspecial%3Fchars%26more');

  // Validate when parsed, ID is correct
  const parsed = new URL(url, 'http://localhost');
  const pathSegments = parsed.pathname.split('/');
  expect(decodeURIComponent(pathSegments[pathSegments.length - 1])).toBe(
    'sys-123/special?chars&more'
  );
});
```

**Why meaningful:**

- Actually tests special characters (/, ?, &)
- Validates encoding is correct (%2F, %3F, %26)
- Tests round-trip (encode then decode)
- Would catch encoding bugs
- Documents expected encoding behavior

---

### Example 4: Complex Query Parameters (Spatial)

❌ **TRIVIAL:**

```typescript
it('should add bbox parameter', () => {
  const url = builder.getSystems({ bbox: [-180, -90, 180, 90] });
  expect(url).toContain('bbox');
});
```

**Why trivial:**

- Only checks parameter name exists
- Doesn't validate bbox values
- Doesn't validate bbox format (comma-separated)
- Doesn't test invalid bbox handling

✅ **MEANINGFUL:**

```typescript
describe('spatial filtering with bbox', () => {
  it('should build systems URL with bbox parameter in correct format', () => {
    const url = builder.getSystems({ bbox: [-180, -90, 180, 90] });
    const parsed = new URL(url, 'http://localhost');

    // Validate bbox format: minX,minY,maxX,maxY (no spaces)
    expect(parsed.searchParams.get('bbox')).toBe('-180,-90,180,90');
  });

  it('should throw error for invalid bbox with wrong number of values', () => {
    expect(() => builder.getSystems({ bbox: [1, 2, 3] })).toThrow(
      'bbox must have 4 values: [minX, minY, maxX, maxY]'
    );
  });

  it('should throw error for invalid bbox with minX > maxX', () => {
    expect(() => builder.getSystems({ bbox: [10, -90, -10, 90] })).toThrow(
      'bbox minX must be less than or equal to maxX'
    );
  });

  it('should handle bbox with fractional coordinates', () => {
    const url = builder.getSystems({ bbox: [-180.5, -90.25, 180.75, 90.5] });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('bbox')).toBe('-180.5,-90.25,180.75,90.5');
  });
});
```

**Why meaningful:**

- Tests format (comma-separated, no spaces)
- Tests validation (wrong count, invalid range)
- Tests edge cases (fractional coordinates)
- Would catch bbox formatting bugs
- Documents bbox validation rules

---

### Example 5: Temporal Parameters

❌ **TRIVIAL:**

```typescript
it('should add datetime parameter', () => {
  const url = builder.getSystems({ datetime: '2024-01-01' });
  expect(url).toContain('datetime');
});
```

**Why trivial:**

- Only checks parameter exists
- Doesn't validate datetime format
- Doesn't test interval format
- Doesn't test open-ended intervals

✅ **MEANINGFUL:**

```typescript
describe('temporal filtering with datetime', () => {
  it('should build systems URL with instant datetime', () => {
    const url = builder.getSystems({ datetime: '2024-01-01T00:00:00Z' });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('datetime')).toBe('2024-01-01T00:00:00Z');
  });

  it('should build systems URL with datetime interval', () => {
    const url = builder.getSystems({
      datetime: '2024-01-01T00:00:00Z/2024-12-31T23:59:59Z',
    });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('datetime')).toBe(
      '2024-01-01T00:00:00Z/2024-12-31T23:59:59Z'
    );
  });

  it('should build systems URL with open-ended datetime interval (start only)', () => {
    const url = builder.getSystems({ datetime: '2024-01-01T00:00:00Z/..' });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('datetime')).toBe('2024-01-01T00:00:00Z/..');
  });

  it('should build systems URL with open-ended datetime interval (end only)', () => {
    const url = builder.getSystems({ datetime: '../2024-12-31T23:59:59Z' });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('datetime')).toBe('../2024-12-31T23:59:59Z');
  });

  it('should properly encode datetime with special characters', () => {
    // ISO 8601 allows T and Z which need encoding in URLs
    const url = builder.getSystems({ datetime: '2024-01-01T00:00:00Z' });
    expect(url).toContain('2024-01-01T00%3A00%3A00Z'); // : encoded as %3A
  });
});
```

**Why meaningful:**

- Tests all datetime formats (instant, interval, open-ended)
- Tests encoding of special characters (: encoded as %3A)
- Documents OGC datetime parameter format
- Would catch datetime formatting bugs
- Comprehensive coverage of all variations

---

## 5. Side-by-Side Examples: Query Parameters

### Example 6: Parameter Combinations

❌ **TRIVIAL:**

```typescript
it('should handle multiple parameters', () => {
  const url = builder.getSystems({ limit: 10, bbox: [-180, -90, 180, 90] });
  expect(url).toContain('limit');
  expect(url).toContain('bbox');
});
```

**Why trivial:**

- Only checks parameters exist
- Doesn't validate values
- Doesn't check parameter order or encoding
- Doesn't test parameter interactions

✅ **MEANINGFUL:**

```typescript
it('should build systems URL with combined spatial and pagination parameters', () => {
  const url = builder.getSystems({
    limit: 10,
    offset: 20,
    bbox: [-180, -90, 180, 90],
    datetime: '2024-01-01T00:00:00Z/..',
    systemType: 'sensor',
  });

  const parsed = new URL(url, 'http://localhost');

  // Validate all parameters present with correct values
  expect(parsed.searchParams.get('limit')).toBe('10');
  expect(parsed.searchParams.get('offset')).toBe('20');
  expect(parsed.searchParams.get('bbox')).toBe('-180,-90,180,90');
  expect(parsed.searchParams.get('datetime')).toBe('2024-01-01T00:00:00Z/..');
  expect(parsed.searchParams.get('systemType')).toBe('sensor');

  // Validate no extra parameters
  expect(Array.from(parsed.searchParams.keys())).toEqual([
    'limit',
    'offset',
    'bbox',
    'datetime',
    'systemType',
  ]);
});
```

**Why meaningful:**

- Tests complete parameter set
- Validates all values are correct
- Checks no unexpected parameters added
- Tests realistic usage scenario
- Would catch parameter interaction bugs

---

### Example 7: Optional Parameters

❌ **TRIVIAL:**

```typescript
it('should work without optional parameters', () => {
  const url = builder.getSystems();
  expect(url).toBeDefined();
});
```

**Why trivial:**

- Only checks URL exists
- Doesn't validate query string is empty
- Doesn't validate URL structure
- Too vague ("work" is not specific)

✅ **MEANINGFUL:**

```typescript
it('should build systems URL with no query parameters when options omitted', () => {
  const url = builder.getSystems();
  const parsed = new URL(url, 'http://localhost');

  expect(parsed.pathname).toBe('/collections/sensors/items');
  expect(parsed.search).toBe(''); // No ? in URL
  expect(Array.from(parsed.searchParams.keys())).toEqual([]);
});

it('should build systems URL with only provided parameters', () => {
  const url = builder.getSystems({ limit: 10 }); // Only limit, no other params
  const parsed = new URL(url, 'http://localhost');

  expect(parsed.searchParams.get('limit')).toBe('10');
  expect(Array.from(parsed.searchParams.keys())).toEqual(['limit']);
});

it('should ignore undefined optional parameters', () => {
  const url = builder.getSystems({
    limit: 10,
    offset: undefined, // Explicitly undefined
    bbox: undefined,
  });
  const parsed = new URL(url, 'http://localhost');

  expect(parsed.searchParams.get('limit')).toBe('10');
  expect(parsed.searchParams.has('offset')).toBe(false);
  expect(parsed.searchParams.has('bbox')).toBe(false);
  expect(Array.from(parsed.searchParams.keys())).toEqual(['limit']);
});
```

**Why meaningful:**

- Tests no parameters scenario
- Tests partial parameters scenario
- Tests undefined handling
- Validates query string structure
- Would catch parameter leaking bugs

---

### Example 8: Array Parameters

❌ **TRIVIAL:**

```typescript
it('should handle array parameters', () => {
  const url = builder.getObservations({
    observedProperty: ['temperature', 'humidity'],
  });
  expect(url).toContain('observedProperty');
});
```

**Why trivial:**

- Doesn't validate array serialization format
- Doesn't test empty array
- Doesn't test single-item array
- Doesn't validate values

✅ **MEANINGFUL:**

```typescript
describe('array parameter serialization', () => {
  it('should serialize array parameter as comma-separated values', () => {
    const url = builder.getObservations({
      observedProperty: ['temperature', 'humidity', 'pressure'],
    });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('observedProperty')).toBe(
      'temperature,humidity,pressure'
    );
  });

  it('should handle single-item array', () => {
    const url = builder.getObservations({ observedProperty: ['temperature'] });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('observedProperty')).toBe('temperature');
  });

  it('should handle empty array by omitting parameter', () => {
    const url = builder.getObservations({ observedProperty: [] });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.has('observedProperty')).toBe(false);
  });

  it('should encode special characters in array values', () => {
    const url = builder.getObservations({
      observedProperty: ['water/level', 'air quality'],
    });
    const parsed = new URL(url, 'http://localhost');
    expect(parsed.searchParams.get('observedProperty')).toBe(
      'water%2Flevel,air%20quality'
    );
  });
});
```

**Why meaningful:**

- Tests array serialization format
- Tests edge cases (single item, empty array)
- Tests encoding within array values
- Documents array parameter format
- Would catch array serialization bugs

---

## 6. Side-by-Side Examples: Format Parsing

### Example 9: SensorML Parsing

❌ **TRIVIAL:**

```typescript
it('should parse SensorML', () => {
  const result = parser.parse(sensorMLFixture);
  expect(result).toBeTruthy();
});
```

**Why trivial:**

- Only checks result exists
- Doesn't validate structure
- Doesn't check any properties
- Would pass even if result is wrong type

✅ **MEANINGFUL:**

```typescript
it('should parse SensorML PhysicalSystem with complete structure', () => {
  const result = parser.parse(physicalSystemFixture);

  // Validate type discrimination
  expect(result.type).toBe('PhysicalSystem');

  // Validate identification
  expect(result.identification.identifier).toBe(
    'urn:x-noaa:def:system:noaa::station-NDBC-41001'
  );
  expect(result.identification.label).toBe('NOAA NDBC Station 41001');

  // Validate classification
  expect(result.classification.classifiers).toHaveLength(2);
  expect(result.classification.classifiers[0].name).toBe('System Type');
  expect(result.classification.classifiers[0].value).toBe('Weather Station');

  // Validate position
  expect(result.position.coordinates).toEqual([-89.67, 25.9, 0]);
  expect(result.position.referenceFrame).toBe(
    'http://www.opengis.net/def/crs/EPSG/0/4326'
  );

  // Validate components
  expect(result.components).toHaveLength(3);
  expect(result.components[0].name).toBe('wind_sensor');
  expect(result.components[0].type).toBe('PhysicalComponent');

  // Validate nested capabilities
  expect(result.components[0].capabilities).toHaveProperty('MeasurementRange');
  expect(result.components[0].capabilities.MeasurementRange.min).toBe(0);
  expect(result.components[0].capabilities.MeasurementRange.max).toBe(100);
  expect(result.components[0].capabilities.MeasurementRange.uom.code).toBe(
    'm/s'
  );
});
```

**Why meaningful:**

- Validates complete nested structure (4+ levels deep)
- Tests type discrimination
- Validates all major sections (identification, classification, position, components, capabilities)
- Tests nested properties and arrays
- Would catch parsing bugs at any level
- Documents expected SensorML structure

---

### Example 10: SWE Common DataRecord Parsing

❌ **TRIVIAL:**

```typescript
it('should parse DataRecord', () => {
  const result = parser.parse(dataRecordFixture);
  expect(result.type).toBe('DataRecord');
});
```

**Why trivial:**

- Only checks top-level type
- Doesn't validate fields
- Doesn't check field types or values
- Doesn't test nested records

✅ **MEANINGFUL:**

```typescript
describe('SWE Common DataRecord parsing', () => {
  it('should parse DataRecord with all field types', () => {
    const result = parser.parse(dataRecordFixture);

    expect(result.type).toBe('DataRecord');
    expect(result.fields).toHaveLength(4);

    // Validate Quantity field
    expect(result.fields[0].name).toBe('temperature');
    expect(result.fields[0].type).toBe('Quantity');
    expect(result.fields[0].definition).toBe(
      'http://www.qudt.org/qudt/owl/1.0.0/quantity/Instances.html#Temperature'
    );
    expect(result.fields[0].uom.code).toBe('Cel');
    expect(result.fields[0].constraint.interval).toEqual([-40, 60]);

    // Validate Time field
    expect(result.fields[1].name).toBe('time');
    expect(result.fields[1].type).toBe('Time');
    expect(result.fields[1].uom.href).toBe(
      'http://www.opengis.net/def/uom/ISO-8601/0/Gregorian'
    );

    // Validate Boolean field
    expect(result.fields[2].name).toBe('quality_flag');
    expect(result.fields[2].type).toBe('Boolean');

    // Validate Text field
    expect(result.fields[3].name).toBe('station_id');
    expect(result.fields[3].type).toBe('Text');
    expect(result.fields[3].constraint.pattern).toBe('[A-Z]{4}[0-9]{4}');
  });

  it('should parse nested DataRecord', () => {
    const result = parser.parse(nestedDataRecordFixture);

    expect(result.type).toBe('DataRecord');
    expect(result.fields[0].type).toBe('DataRecord'); // Nested record
    expect(result.fields[0].fields).toHaveLength(2);
    expect(result.fields[0].fields[0].name).toBe('latitude');
    expect(result.fields[0].fields[1].name).toBe('longitude');
  });

  it('should parse DataRecord with optional fields omitted', () => {
    const minimalFixture = {
      type: 'DataRecord',
      fields: [{ name: 'value', type: 'Quantity', uom: { code: 'm' } }],
    };

    const result = parser.parse(minimalFixture);
    expect(result.fields[0]).not.toHaveProperty('definition');
    expect(result.fields[0]).not.toHaveProperty('constraint');
  });
});
```

**Why meaningful:**

- Tests all SWE Common field types
- Validates complete field structure (name, type, definition, uom, constraint)
- Tests nested DataRecord
- Tests optional field handling
- Documents SWE Common field types
- Would catch field parsing bugs

---

### Example 11: GeoJSON Extension Parsing

❌ **TRIVIAL:**

```typescript
it('should parse CSAPI GeoJSON', () => {
  const result = parser.parse(geoJSONFixture);
  expect(result.type).toBe('Feature');
});
```

**Why trivial:**

- Only checks standard GeoJSON type
- Doesn't validate CSAPI extensions
- Doesn't check featureType property
- Doesn't validate CSAPI-specific properties

✅ **MEANINGFUL:**

```typescript
describe('CSAPI GeoJSON extension parsing', () => {
  it('should parse System feature with CSAPI properties', () => {
    const result = parser.parse(systemGeoJSONFixture);

    // Validate standard GeoJSON
    expect(result.type).toBe('Feature');
    expect(result.geometry.type).toBe('Point');
    expect(result.geometry.coordinates).toEqual([-89.67, 25.9, 0]);

    // Validate CSAPI featureType
    expect(result.properties.featureType).toBe('sosa:System');

    // Validate CSAPI-specific properties
    expect(result.properties.uniqueIdentifier).toBe(
      'urn:x-noaa:def:system:noaa::station-NDBC-41001'
    );
    expect(result.properties.systemKind).toBe('sosa:Platform');
    expect(result.properties.assetType).toBe('Mooring');

    // Validate uniqueIdentifier is URI format
    expect(result.properties.uniqueIdentifier).toMatch(/^urn:/);
  });

  it('should parse Observation feature with result property', () => {
    const result = parser.parse(observationGeoJSONFixture);

    expect(result.properties.featureType).toBe('sosa:Observation');
    expect(result.properties.resultTime).toBe('2024-01-15T12:00:00Z');
    expect(result.properties.phenomenonTime).toBe('2024-01-15T12:00:00Z');
    expect(result.properties.result).toBe(21.5);
    expect(result.properties.observedProperty).toBe(
      'http://www.qudt.org/qudt/owl/1.0.0/quantity/Instances.html#Temperature'
    );
  });

  it('should throw error for invalid uniqueIdentifier format', () => {
    const invalidFixture = {
      ...systemGeoJSONFixture,
      properties: {
        ...systemGeoJSONFixture.properties,
        uniqueIdentifier: 'not-a-uri', // Invalid: not URI format
      },
    };

    expect(() => parser.parse(invalidFixture)).toThrow(
      'uniqueIdentifier must be URI format'
    );
  });
});
```

**Why meaningful:**

- Tests standard GeoJSON + CSAPI extensions
- Validates all CSAPI-specific properties
- Tests URI format validation
- Tests different feature types (System, Observation)
- Documents CSAPI GeoJSON extensions
- Would catch extension parsing bugs

---

## 7. Side-by-Side Examples: Error Handling

### Example 12: Resource Validation Errors

❌ **TRIVIAL:**

```typescript
it('should throw error when invalid', () => {
  expect(() => builder.getSystem()).toThrow();
});
```

**Why trivial:**

- Doesn't specify what triggers error
- Doesn't validate error type
- Doesn't check error message
- Unclear what "invalid" means

✅ **MEANINGFUL:**

```typescript
describe('resource availability validation', () => {
  it('should throw EndpointError when systems resource unavailable in collection', () => {
    const minimalEndpoint = new OgcApiEndpoint('http://test/minimal/');
    const builder = await minimalEndpoint.csapi('minimal-collection');

    expect(() => builder.getSystem('sys-123')).toThrow(EndpointError);

    expect(() => builder.getSystem('sys-123')).toThrow(
      /systems resource not available in collection/
    );
  });

  it('should throw EndpointError with collection ID in message', () => {
    const builder = await endpoint.csapi('partial-collection');

    try {
      builder.getSystemDataStreams('sys-123');
      fail('Should have thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(EndpointError);
      expect(error.message).toContain('datastreams');
      expect(error.message).toContain('partial-collection');
    }
  });

  it('should list available resources in error message', () => {
    const builder = await endpoint.csapi('partial-collection');

    expect(() => builder.getSystemDataStreams('sys-123')).toThrow(
      /Available resources: systems, deployments, procedures/
    );
  });
});
```

**Why meaningful:**

- Tests specific error trigger (resource unavailable)
- Validates error type (EndpointError)
- Checks error message content (helpful debug info)
- Tests error message includes relevant data (collection ID, available resources)
- Would catch error handling bugs
- Documents expected error behavior

---

### Example 13: Parameter Validation Errors

❌ **TRIVIAL:**

```typescript
it('should validate parameters', () => {
  expect(() => builder.getSystems({ limit: -1 })).toThrow();
});
```

**Why trivial:**

- Doesn't specify validation rule
- Generic error check
- Doesn't test error message
- Missing other validation cases

✅ **MEANINGFUL:**

```typescript
describe('parameter validation', () => {
  it('should throw error for negative limit', () => {
    expect(() => builder.getSystems({ limit: -1 })).toThrow(
      'limit must be a positive integer'
    );
  });

  it('should throw error for limit of zero', () => {
    expect(() => builder.getSystems({ limit: 0 })).toThrow(
      'limit must be at least 1'
    );
  });

  it('should throw error for non-integer limit', () => {
    expect(() => builder.getSystems({ limit: 10.5 })).toThrow(
      'limit must be an integer'
    );
  });

  it('should throw error for bbox with wrong number of values', () => {
    expect(() => builder.getSystems({ bbox: [1, 2, 3] })).toThrow(
      'bbox must have exactly 4 values: [minX, minY, maxX, maxY]'
    );
  });

  it('should throw error for bbox with minX > maxX', () => {
    expect(() => builder.getSystems({ bbox: [10, -90, -10, 90] })).toThrow(
      'bbox: minX (10) must be less than or equal to maxX (-10)'
    );
  });

  it('should throw error for bbox with minY > maxY', () => {
    expect(() => builder.getSystems({ bbox: [-180, 50, 180, -50] })).toThrow(
      'bbox: minY (50) must be less than or equal to maxY (-50)'
    );
  });

  it('should throw error for invalid systemType', () => {
    expect(() => builder.getSystems({ systemType: 'invalid' })).toThrow(
      'systemType must be one of: sensor, platform, procedure'
    );
  });
});
```

**Why meaningful:**

- Tests all validation rules
- Validates specific error messages
- Tests boundary conditions
- Documents all validation constraints
- Would catch validation bugs
- Self-documenting (shows all valid/invalid cases)

---

### Example 14: Format Parsing Errors

❌ **TRIVIAL:**

```typescript
it('should handle invalid format', () => {
  expect(() => parser.parse(invalidFixture)).toThrow();
});
```

**Why trivial:**

- Doesn't specify what makes it invalid
- Generic error check
- Doesn't test error message
- Unclear what "invalid" means

✅ **MEANINGFUL:**

```typescript
describe('SensorML parsing error handling', () => {
  it('should throw error for missing required type field', () => {
    const invalidFixture = { ...validFixture };
    delete invalidFixture.type;

    expect(() => parser.parse(invalidFixture)).toThrow(
      'SensorML document must have "type" field'
    );
  });

  it('should throw error for unsupported type', () => {
    const invalidFixture = {
      ...validFixture,
      type: 'UnsupportedType',
    };

    expect(() => parser.parse(invalidFixture)).toThrow(
      'Unsupported SensorML type: UnsupportedType. Supported types: PhysicalSystem, SimpleProcess, AggregateProcess'
    );
  });

  it('should throw error for malformed position coordinates', () => {
    const invalidFixture = {
      ...physicalSystemFixture,
      position: {
        coordinates: [1, 2], // Missing Z coordinate
      },
    };

    expect(() => parser.parse(invalidFixture)).toThrow(
      'PhysicalSystem position must have [X, Y, Z] coordinates'
    );
  });

  it('should throw error for invalid component reference', () => {
    const invalidFixture = {
      ...aggregateProcessFixture,
      connections: [
        { source: 'component1.output', target: 'component2.input' },
      ],
      components: [
        { name: 'component1' },
        // Missing component2!
      ],
    };

    expect(() => parser.parse(invalidFixture)).toThrow(
      'Connection references non-existent component: component2'
    );
  });
});
```

**Why meaningful:**

- Tests specific error conditions
- Validates error messages describe the problem
- Tests different error types (missing, invalid, malformed)
- Documents all error cases
- Would catch error handling bugs
- Helps users understand what went wrong

---

## 8. Side-by-Side Examples: Type Validation

### Example 15: Interface Testing

❌ **TRIVIAL:**

```typescript
// Only compile-time type checking (TypeScript assumes correctness)
it('compiles with correct types', () => {
  const options: SystemQueryOptions = {
    limit: 10,
    offset: 20,
  };
  // No runtime validation
});
```

**Why trivial:**

- Only tests compilation
- No runtime validation
- Doesn't test constraints
- Doesn't test optional properties

✅ **MEANINGFUL:**

```typescript
describe('SystemQueryOptions interface', () => {
  it('accepts valid options object with required types', () => {
    const options: SystemQueryOptions = {
      limit: 10,
      offset: 20,
      bbox: [-180, -90, 180, 90],
      datetime: '2024-01-01T00:00:00Z/..',
      systemType: 'sensor',
    };

    // Runtime validation
    expect(typeof options.limit).toBe('number');
    expect(typeof options.offset).toBe('number');
    expect(Array.isArray(options.bbox)).toBe(true);
    expect(options.bbox).toHaveLength(4);
    expect(typeof options.datetime).toBe('string');
    expect(['sensor', 'platform', 'procedure']).toContain(options.systemType);
  });

  it('accepts partial options with only limit', () => {
    const options: SystemQueryOptions = { limit: 10 };
    expect(options).toEqual({ limit: 10 });
  });

  it('rejects options with wrong types at runtime', () => {
    const invalidOptions = {
      limit: '10', // Should be number
      offset: 'abc', // Should be number
    };

    expect(() => validateQueryOptions(invalidOptions)).toThrow(
      'limit must be a number'
    );
  });
});
```

**Why meaningful:**

- Tests compile-time + runtime validation
- Tests all properties
- Tests partial options
- Tests type validation at runtime
- Documents interface constraints
- Would catch type coercion bugs

---

### Example 16: Union Type Testing

❌ **TRIVIAL:**

```typescript
it('accepts union types', () => {
  const param: DateTimeParameter = '2024-01-01';
  expect(param).toBeDefined();
});
```

**Why trivial:**

- Only tests one variant
- Only compile-time check
- Doesn't test all union cases
- Doesn't test discriminated union logic

✅ **MEANINGFUL:**

```typescript
describe('DateTimeParameter union type', () => {
  it('accepts instant as string', () => {
    const instant: DateTimeParameter = '2024-01-01T00:00:00Z';
    const result = serializeDateTimeParameter(instant);
    expect(result).toBe('2024-01-01T00:00:00Z');
  });

  it('accepts instant as Date object', () => {
    const instant: DateTimeParameter = new Date('2024-01-01T00:00:00Z');
    const result = serializeDateTimeParameter(instant);
    expect(result).toBe('2024-01-01T00:00:00.000Z');
  });

  it('accepts interval with start and end', () => {
    const interval: DateTimeParameter = {
      start: new Date('2024-01-01'),
      end: new Date('2024-12-31'),
    };
    const result = serializeDateTimeParameter(interval);
    expect(result).toMatch(/2024-01-01.*\/2024-12-31/);
  });

  it('accepts interval with only start (open-ended)', () => {
    const interval: DateTimeParameter = {
      start: new Date('2024-01-01'),
    };
    const result = serializeDateTimeParameter(interval);
    expect(result).toMatch(/2024-01-01.*\/..\Z/);
  });

  it('accepts interval with only end (open-ended)', () => {
    const interval: DateTimeParameter = {
      end: new Date('2024-12-31'),
    };
    const result = serializeDateTimeParameter(interval);
    expect(result).toMatch(/^\.\.\/2024-12-31/);
  });

  it('throws error for invalid interval object (neither start nor end)', () => {
    const invalid = {} as DateTimeParameter;
    expect(() => serializeDateTimeParameter(invalid)).toThrow(
      'DateTimeParameter interval must have start or end'
    );
  });
});
```

**Why meaningful:**

- Tests ALL union variants (string, Date, interval objects)
- Tests discriminated union logic
- Tests edge cases (open-ended intervals)
- Tests error cases (invalid union variant)
- Documents all accepted formats
- Would catch union discrimination bugs

---

## 9. Side-by-Side Examples: Integration Tests

### Example 17: Multi-Component Workflow

❌ **TRIVIAL:**

```typescript
it('should work end-to-end', async () => {
  const endpoint = new OgcApiEndpoint('http://test/csapi/');
  const builder = await endpoint.csapi('systems');
  const url = builder.getSystems();
  expect(url).toBeDefined();
});
```

**Why trivial:**

- Only calls methods, doesn't validate
- Doesn't test actual workflow
- Only checks existence
- Not actually end-to-end (just 3 method calls)

✅ **MEANINGFUL:**

```typescript
describe('complete workflow: endpoint detection to cross-resource query', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(async () => {
    endpoint = new OgcApiEndpoint('http://test/csapi/sample-data/');
  });

  it('supports full discovery → collection → query → navigation workflow', async () => {
    // 1. Endpoint detection
    expect(await endpoint.hasConnectedSystems).toBe(true);

    // 2. Conformance validation
    const conformance = await endpoint.info().conformsTo;
    expect(conformance).toContain(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common'
    );
    expect(conformance).toContain(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream'
    );

    // 3. Collection listing
    const collections = await endpoint.csapiCollections;
    expect(collections.length).toBeGreaterThan(0);
    expect(collections).toContainEqual(
      expect.objectContaining({
        id: 'systems',
        conformsTo: expect.arrayContaining([
          'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/create-replace-delete',
        ]),
      })
    );

    // 4. Query builder creation with caching
    const builder1 = await endpoint.csapi('systems');
    const builder2 = await endpoint.csapi('systems');
    expect(builder1).toBe(builder2); // Same instance (cached)

    // 5. Resource availability check
    expect(builder1.availableResources).toContain('systems');
    expect(builder1.availableResources).toContain('datastreams');
    expect(builder1.availableResources).toContain('observations');

    // 6. Systems query with filters
    const systemsUrl = builder1.getSystems({
      bbox: [-180, -90, 180, 90],
      datetime: '2024-01-01T00:00:00Z/..',
      limit: 10,
    });
    const systemsParsed = new URL(systemsUrl);
    expect(systemsParsed.pathname).toBe('/collections/systems/items');
    expect(systemsParsed.searchParams.get('bbox')).toBe('-180,-90,180,90');

    // 7. Cross-resource navigation (Systems → DataStreams)
    const datastreamsUrl = builder1.getSystemDataStreams('sys-123', {
      limit: 5,
    });
    const datastreamsParsed = new URL(datastreamsUrl);
    expect(datastreamsParsed.pathname).toContain(
      '/systems/items/sys-123/datastreams'
    );
    expect(datastreamsParsed.searchParams.get('limit')).toBe('5');

    // 8. Cross-resource navigation (DataStreams → Observations)
    const observationsUrl = builder1.getDataStreamObservations('ds-456', {
      phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
    });
    const observationsParsed = new URL(observationsUrl);
    expect(observationsParsed.pathname).toContain(
      '/datastreams/items/ds-456/observations'
    );
    expect(observationsParsed.searchParams.get('phenomenonTime')).toMatch(
      /2024-01-01.*\/2024-01-31/
    );
  });

  it('handles errors gracefully in workflow', async () => {
    // 1. Non-CSAPI endpoint
    const nonCSAPIEndpoint = new OgcApiEndpoint('http://test/features-only/');
    expect(await nonCSAPIEndpoint.hasConnectedSystems).toBe(false);
    await expect(nonCSAPIEndpoint.csapi('systems')).rejects.toThrow(
      'Endpoint does not support OGC API - Connected Systems'
    );

    // 2. Unsupported collection
    await expect(endpoint.csapi('non-existent-collection')).rejects.toThrow(
      /Collection.*not found/
    );

    // 3. Unavailable resource
    const minimalBuilder = await endpoint.csapi('minimal-collection'); // Only has 'systems', no 'datastreams'
    expect(() => minimalBuilder.getSystemDataStreams('sys-123')).toThrow(
      /datastreams resource not available/
    );
  });
});
```

**Why meaningful:**

- Tests complete realistic workflow (8 steps)
- Validates each step completely
- Tests caching behavior
- Tests cross-resource navigation
- Tests error handling throughout workflow
- Documents expected usage patterns
- Would catch integration bugs
- Self-documenting (shows how to use API)

---

## 10. Coverage Depth Standards

### Statement Coverage

**Target:** 85-90% (industry standard)

**What to cover:**

- All public methods
- All code paths (if/else, switch, ternary)
- All error handling paths
- All validation logic

**What is acceptable to NOT cover:**

- Defensive programming checks that should never happen
- Type guards that TypeScript already prevents
- Logger calls (unless testing logging logic)

### Branch Coverage

**Target:** 80-85% (prioritize over statement)

**Why it matters:** Branch coverage ensures all logical paths are tested (if/else, switch, early returns).

**Example:**

```typescript
// Function has 3 branches
function buildUrl(id?: string) {
  if (!id) {
    return '/collection/items'; // Branch 1
  }
  if (id.includes('/')) {
    return `/collection/items/${encodeURIComponent(id)}`; // Branch 2
  }
  return `/collection/items/${id}`; // Branch 3
}

// Meaningful tests cover all 3 branches
it('returns collection URL when no ID', () => { ... }); // Branch 1
it('encodes ID with special chars', () => { ... }); // Branch 2
it('returns item URL with simple ID', () => { ... }); // Branch 3
```

### Edge Case Coverage

**Required edge cases for CSAPI:**

| Parameter Type | Edge Cases to Test                                                      |
| -------------- | ----------------------------------------------------------------------- |
| **Strings**    | Empty string, very long string, special chars, Unicode, null, undefined |
| **Numbers**    | 0, negative, fractional, very large, very small, null, undefined        |
| **Arrays**     | Empty array, single item, many items, null, undefined                   |
| **Objects**    | Empty object, partial properties, all properties, null, undefined       |
| **Booleans**   | true, false, null, undefined                                            |
| **Dates**      | Past, present, future, invalid format, null, undefined                  |

### Error Condition Coverage

**Required error tests:**

- All validation errors (with specific messages)
- Resource unavailable errors
- Collection not found errors
- Invalid format errors
- Malformed data errors
- Encoding errors
- Network errors (if applicable)

---

## 11. Fixture Quality Standards

### Real Spec Examples (REQUIRED)

✅ **Use actual OGC CSAPI spec examples:**

**Systems (from OGC CSAPI Part 1):**

```json
{
  "id": "urn:x-noaa:def:system:noaa::station-NDBC-41001",
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-89.67, 25.9, 0]
  },
  "properties": {
    "featureType": "sosa:System",
    "name": "NOAA NDBC Station 41001",
    "description": "National Buoy 41001 - 150 NM East of Cape HATTERAS",
    "systemKind": "sosa:Platform",
    "assetType": "Mooring",
    "uniqueIdentifier": "urn:x-noaa:def:system:noaa::station-NDBC-41001",
    "validTime": {
      "begin": "2005-01-01T00:00:00Z",
      "end": null
    }
  }
}
```

**SensorML PhysicalSystem (from OGC SensorML 2.0 spec):**

```json
{
  "type": "PhysicalSystem",
  "identification": {
    "identifier": "urn:x-noaa:def:system:noaa::station-NDBC-41001",
    "label": "NOAA NDBC Station 41001"
  },
  "classification": {
    "classifiers": [
      { "name": "System Type", "value": "Weather Station" },
      { "name": "Intended Application", "value": "Marine Weather Monitoring" }
    ]
  },
  "position": {
    "coordinates": [-89.67, 25.9, 0],
    "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4326"
  },
  "components": [
    {
      "name": "wind_sensor",
      "type": "PhysicalComponent",
      "description": "Anemometer for wind speed and direction",
      "position": { "coordinates": [-89.67, 25.9, 3] },
      "capabilities": {
        "MeasurementRange": {
          "min": 0,
          "max": 100,
          "uom": { "code": "m/s" }
        }
      }
    }
  ]
}
```

### Fixture Variations Required

**Standard:** 5 fixture types per component

1. **Minimal** - Only required properties
2. **Typical** - Common use case with typical properties
3. **Maximal** - All properties populated
4. **Edge** - Boundary values, empty arrays, null where allowed
5. **Invalid** - For error testing (wrong types, missing required, malformed)

### Fixture Provenance Documentation

**Required in fixture files:**

```typescript
/**
 * Fixture: NOAA NDBC Weather Station System
 * Source: OGC API - Connected Systems Part 1 Specification
 * Section: 7.2.1 System Resource Example
 * URL: https://docs.ogc.org/is/23-001/23-001.html#systems-resource
 *
 * Description: Real-world example of a weather station system deployed
 * as a mooring buoy off Cape Hatteras, North Carolina.
 *
 * Last Updated: 2024-01-15 (synced with spec version 0.0.3)
 */
export const noaaNDBCStation41001 = { ... };
```

### Fixture Maintenance

**Process:**

1. Review OGC CSAPI spec for updated examples when spec changes
2. Update fixtures to match new spec version
3. Add fixtures for new resource types as spec evolves
4. Tag fixtures with spec version they match
5. Create test for each fixture to ensure it parses correctly

---

## 12. Test Organization Standards

### Describe/It Structure

**Standard:** Hierarchical grouping by component → feature → scenario

```typescript
describe('CSAPIQueryBuilder', () => {
  // Component level

  describe('constructor', () => {
    // Feature level

    it('extracts available resources from collection info', () => {
      // Scenario level - specific behavior
    });

    it('throws EndpointError when collection lacks conformance', () => {
      // Scenario level - specific error case
    });
  });

  describe('Systems methods', () => {
    // Feature group level

    describe('getSystems', () => {
      // Method level

      describe('with pagination parameters', () => {
        // Parameter group level

        it('builds URL with limit only', () => { ... });
        it('builds URL with limit and offset', () => { ... });
        it('throws error for negative limit', () => { ... });
      });

      describe('with spatial parameters', () => {
        it('builds URL with bbox', () => { ... });
        it('validates bbox has 4 values', () => { ... });
      });
    });
  });
});
```

### Test Naming Standards

**Pattern:** `should [action] [condition/context]`

✅ **Good names (specific, clear):**

- `should build systems URL with bbox parameter correctly encoded`
- `should throw EndpointError when systems resource unavailable`
- `should parse SensorML PhysicalSystem with nested components`
- `should serialize datetime interval with open end (start only)`

❌ **Bad names (vague, unclear):**

- `should work`
- `should return value`
- `test getSystems`
- `getSystems method`

### Setup/Teardown Standards

**beforeEach:** Use for test-specific setup that most tests need

```typescript
describe('CSAPIQueryBuilder', () => {
  let endpoint: OgcApiEndpoint;
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    endpoint = new OgcApiEndpoint('http://test/csapi/');
    builder = await endpoint.csapi('systems');
  });

  // All tests can use endpoint and builder
});
```

**beforeAll:** Use for expensive setup shared by all tests (fixture loading)

```typescript
describe('OgcApiEndpoint with CSAPI fixtures', () => {
  beforeAll(() => {
    // Mock fetch once for all tests
    globalThis.fetch = jest.fn().mockImplementation(/* ... */);
  });

  afterAll(() => {
    // Clean up
    jest.restoreAllMocks();
  });
});
```

---

## 13. Objective Quality Checklist

Use this checklist to evaluate any test for meaningfulness:

### Assertion Quality

- [ ] Uses complete structure validation (parseUrl, object shape), not substring matching
- [ ] Validates nested properties (at least 2 levels deep for complex objects)
- [ ] Checks exact values, not just existence or truthiness
- [ ] Validates encoding (special characters, spaces, reserved characters)

### Scenario Coverage

- [ ] Tests happy path (typical use case)
- [ ] Tests edge cases (null, undefined, empty, boundary values)
- [ ] Tests error conditions (with specific error types and messages)
- [ ] Tests parameter combinations (not just single values)
- [ ] Tests optional vs required parameters

### Fixture Quality

- [ ] Uses real OGC CSAPI spec examples
- [ ] Fixture provenance documented (spec section, URL)
- [ ] Multiple fixture variations (minimal, typical, maximal, edge, invalid)
- [ ] Realistic values (not 'test', '123', 'foo')

### Test Organization

- [ ] Clear hierarchical describe/it structure
- [ ] Specific test names describing behavior
- [ ] Logical grouping by feature/method
- [ ] Setup/teardown used appropriately

### Documentation Value

- [ ] Test is self-documenting (name + code clearly show expected behavior)
- [ ] Shows how to use API correctly
- [ ] Failure would clearly indicate what broke
- [ ] Useful for future contributors

### Bug Detection

- [ ] Would catch real bugs (not just type errors)
- [ ] Would catch regressions (if behavior changes)
- [ ] Tests behavior, not implementation details
- [ ] Enables safe refactoring

---

## 14. Application to CSAPI

### QueryBuilder Method Testing Standards

**Pattern:** Complete URL validation + parameter combinations + error handling

```typescript
describe('[ResourceType] methods', () => {
  describe('get[ResourceType]s', () => {
    // Minimal case
    it('builds URL with no parameters', () => {
      const url = builder.get[ResourceType]s();
      const parsed = new URL(url);
      expect(parsed.pathname).toBe('/collections/[resourceType]/items');
      expect(parsed.search).toBe('');
    });

    // Parameter testing
    it('builds URL with pagination', () => { ... });
    it('builds URL with spatial filter', () => { ... });
    it('builds URL with temporal filter', () => { ... });
    it('builds URL with all parameters combined', () => { ... });

    // Encoding testing
    it('encodes special characters in parameters', () => { ... });

    // Error testing
    it('throws when resource unavailable', () => { ... });
    it('validates parameter constraints', () => { ... });
  });

  describe('get[ResourceType]', () => {
    it('builds URL for single item', () => { ... });
    it('encodes special characters in ID', () => { ... });
    it('throws when resource unavailable', () => { ... });
  });

  describe('[ResourceType] navigation methods', () => {
    it('builds URL for subresource', () => { ... });
    // ... navigation tests
  });
});
```

### Format Parser Testing Standards

**Pattern:** Complete structure validation + all types + error handling

```typescript
describe('[Format] parser', () => {
  describe('type discrimination', () => {
    it('identifies [Type1]', () => { ... });
    it('identifies [Type2]', () => { ... });
    it('throws for unsupported type', () => { ... });
  });

  describe('[Type1] parsing', () => {
    it('parses complete [Type1] with all properties', () => {
      const result = parser.parse(type1Fixture);
      expect(result.type).toBe('[Type1]');
      expect(result.property1).toBeDefined();
      expect(result.nestedProperty.subProperty).toBe(...);
      // Validate 3-4 levels deep
    });

    it('parses [Type1] with optional properties omitted', () => { ... });
    it('handles nested [Type1]', () => { ... });
  });

  describe('error handling', () => {
    it('throws for missing required field', () => { ... });
    it('throws for invalid type value', () => { ... });
    it('throws for malformed structure', () => { ... });
  });
});
```

### Resource Method Testing Standards

**Pattern:** CRUD operations + validation + encoding

```typescript
describe('[Resource] CRUD methods', () => {
  describe('create[Resource]', () => {
    it('builds POST URL with no query parameters', () => {
      const url = builder.create[Resource]({ ... });
      const parsed = new URL(url);
      expect(parsed.pathname).toBe('/collections/[resource]/items');
      expect(parsed.search).toBe('');
    });
  });

  describe('update[Resource]', () => {
    it('builds PUT URL for specific item', () => { ... });
    it('encodes special characters in ID', () => { ... });
  });

  describe('delete[Resource]', () => {
    it('builds DELETE URL for specific item', () => { ... });
  });
});
```

### Integration Test Standards

**Pattern:** Multi-step workflow + caching + error handling

```typescript
describe('CSAPI integration workflow', () => {
  it('supports endpoint detection → collection → query → navigation', async () => {
    // 1. Detect CSAPI support
    expect(await endpoint.hasConnectedSystems).toBe(true);

    // 2. List collections
    const collections = await endpoint.csapiCollections;
    expect(collections.length).toBeGreaterThan(0);

    // 3. Create builder with caching
    const builder1 = await endpoint.csapi('systems');
    const builder2 = await endpoint.csapi('systems');
    expect(builder1).toBe(builder2); // Cached

    // 4. Query with filters
    const url = builder1.getSystems({ ... });
    // Validate URL

    // 5. Navigate to subresources
    const subUrl = builder1.getSystemDataStreams('sys-123');
    // Validate URL
  });

  it('handles errors throughout workflow', async () => {
    // Test error at each step
  });
});
```

### Type System Testing Standards

**Pattern:** Compilation + runtime + all variants

```typescript
describe('[Type] interface', () => {
  it('accepts valid object with all properties', () => {
    const obj: [Type] = { ... };
    // Runtime validation
    expect(obj).toHaveProperty('requiredProp');
  });

  it('accepts partial object with required only', () => { ... });

  it('rejects invalid types at runtime', () => {
    expect(() => validate[Type]({ wrongType: true }))
      .toThrow('...');
  });
});

describe('[UnionType] discriminated union', () => {
  it('handles variant 1', () => { ... });
  it('handles variant 2', () => { ... });
  it('throws for invalid variant', () => { ... });
});
```

---

## 15. Review Criteria

### How to Review Tests Against This Guide

**Red Flags (Request Improvements):**

1. **Superficial assertions:**

   - `expect(url).toContain('systems')` → Request: Use parseUrl
   - `expect(result).toBeTruthy()` → Request: Validate structure
   - `expect(typeof x).toBe('string')` → Request: Validate content

2. **Missing edge cases:**

   - Only one test per method → Request: Add edge cases + errors
   - No error tests → Request: Add error condition tests
   - No encoding tests → Request: Add special character tests

3. **Vague test names:**

   - "should work" → Request: Specific behavior description
   - "test method" → Request: Describe what is being validated

4. **Synthetic fixtures:**

   - `{ id: '123', name: 'test' }` → Request: Use real spec examples

5. **Single scenario only:**
   - Only happy path → Request: Add edge cases and error cases

**Green Flags (Approve):**

1. **Complete validation:**

   - Uses `new URL()` parsing
   - Validates all parameters
   - Checks nested properties

2. **Comprehensive scenarios:**

   - Happy path + edge cases + errors
   - Parameter combinations tested
   - Encoding validated

3. **Real fixtures:**

   - From OGC CSAPI spec
   - Documented provenance
   - Multiple variations

4. **Clear intent:**

   - Specific test names
   - Self-documenting
   - Hierarchical organization

5. **High value:**
   - Would catch real bugs
   - Enables refactoring
   - Documents expected behavior

### When to Request Test Improvements

**Triggers for requesting improvements:**

1. Test only checks existence/truthiness
2. Test has vague name
3. No edge case tests for a method
4. No error condition tests
5. Fixtures are synthetic
6. Only string matching (toContain), no parsing
7. Test is implementation-focused (tests how, not what)

**How to request:**

```
This test is a good start, but it's a bit superficial. Could you:
1. Use `new URL()` to validate the complete URL structure instead of `toContain`
2. Add tests for edge cases (null, undefined, special characters)
3. Add error condition tests (what happens when resource unavailable?)
4. Use a real spec example fixture instead of synthetic data

Example of what I'm looking for:
[provide side-by-side example from this guide]
```

---

## Summary

### Key Takeaways

**From Lessons Learned:**

- Previous tests were rejected for being "not meaningful, useful, deep, or end-to-end"
- Specific issues: only checked method existence, lacked real spec examples, didn't validate complete URL structures, edge cases not tested
- High line count but low value per test

**Objective Quality Criteria:**

- **Meaningful** = Complete validation + real data + comprehensive scenarios
- **Useful** = Catches real bugs + enables refactoring + documents behavior
- **Deep** = Multiple assertion levels + 5 scenario types + all parameters tested
- **End-to-End** = Multi-component workflows (for URL-building library)
- **Trivial** = Superficial assertions + happy-path-only + synthetic fixtures

**Proven Patterns (from EDR PR #114):**

- Complete URL validation with `new URL()` parsing
- Exact string matching for specific outputs
- Parameter encoding validation
- Error type + message validation
- Real spec examples as fixtures
- Discriminated union testing
- Comprehensive integration tests

**Industry Standards (from TypeScript ecosystem):**

- 85-90% statement coverage
- 80-85% branch coverage
- Test-to-code ratio 1.0-2.0×
- Jest/Vitest with colocated tests
- Mock HTTP calls, never make real requests
- Self-documenting test names

### Application to CSAPI

✅ **Use these patterns for all CSAPI tests:**

1. **URL Construction:** Use `new URL()` for complete validation
2. **Query Parameters:** Validate exact parameter set with parseUrl
3. **Encoding:** Test special characters, spaces, reserved chars
4. **Format Parsing:** Validate 3-4 levels deep, all properties
5. **Error Handling:** Test error type + message for all error conditions
6. **Fixtures:** Use real OGC CSAPI spec examples with provenance
7. **Coverage:** Test 5 scenarios per method (minimal, typical, maximal, edge, error)
8. **Integration:** Test multi-step workflows with caching and error handling

❌ **Avoid these anti-patterns:**

1. Substring matching (`toContain`) without complete validation
2. Truthiness checks (`toBeTruthy`, `toBeDefined`) as sole assertion
3. Type checks (`typeof`) without content validation
4. Happy-path-only tests (no edge cases, no errors)
5. Synthetic fixtures (not from spec)
6. Vague test names ("should work", "test method")
7. Single scenario per method (need comprehensive coverage)

**Objective Checklist:** Use the checklist in Section 13 to evaluate every test before committing.
