# Section 17: Coverage Targets and Metrics Definition

**Research Plan:** [Research Plan 17: Coverage Targets and Metrics Definition](../research-plans/17-coverage-targets-metrics.md)

**Research Questions:** 7 core questions about overall coverage requirements, component-specific targets (QueryBuilder, parsers, types), branch vs statement coverage measurement, type definition coverage, meaningful coverage vs percentage coverage, high-threshold modules (95%+ vs 80%), and phase-based coverage tracking during incremental development

**Methodology:** 6-phase systematic analysis (Phase 1: Upstream Coverage Analysis of existing configurations → Phase 2: Industry Standards Research for TypeScript libraries → Phase 3: Component-Specific Target Definition with rationale matrix → Phase 4: Meaningful Coverage Metrics beyond percentages → Phase 5: Implementation Strategy for Jest configuration → Phase 6: Synthesis into comprehensive coverage specification)

**Research Time:** ~90 minutes (January 8, 2025)

**Primary Source(s):**

- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Coverage targets: >80%)
- [Jest Coverage Documentation](https://jestjs.io/docs/configuration#coveragethreshold)

**Supporting Resources:**

- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream coverage analysis)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (upstream coverage patterns)
- Section 3: [TypeScript Testing Standards](03-typescript-testing-standards.md) (industry standards)
- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (component coverage needs)
- Section 9: [SensorML Testing Requirements](09-sensorml-testing-requirements.md) (parser coverage needs)
- Section 10: [SWE Common Testing Requirements](10-swe-common-testing-requirements.md) (parser coverage needs)
- Section 11: [GeoJSON CSAPI Testing Requirements](11-geojson-csapi-testing-requirements.md) (parser coverage needs)
- Section 12: [QueryBuilder Testing Strategy](12-querybuilder-testing-strategy.md) (QueryBuilder coverage needs)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (resource coverage needs)
- Section 14: [Integration Test Workflow Design](14-integration-test-workflow-design.md) (integration coverage needs)
- Section 15: [Fixture Sourcing Organization](15-fixture-sourcing-organization.md) (fixture coverage needs)
- Section 16: [Worker Extensions Testing](16-worker-extensions-testing.md) (worker coverage needs)

**Document Purpose:** Defines specific coverage targets for each component type (85-95% statement, 80-95% branch) with meaningful quality metrics beyond percentages, Jest configuration specifications, and incremental tracking strategy aligned with ROADMAP phases

---

## Executive Summary

This research defines comprehensive coverage targets for the CSAPI test implementation, establishing both quantitative thresholds and qualitative metrics to ensure meaningful test coverage. Key findings:

- **Upstream State:** No coverage thresholds currently configured in `jest.config.cjs`
- **Official Requirement:** >80% statement, >80% branch, 100% public API coverage
- **Component-Specific Targets:** 85-95% statement, 80-95% branch based on component complexity
- **Meaningful Metrics:** Edge case coverage, error path testing, assertion quality prioritized over raw percentages
- **Implementation:** Jest configuration with per-component glob patterns and incremental tracking per ROADMAP phase

> **Note (Phase 4 Review):** The ROADMAP v3.0 authoritative minimum is **>80% statement, >80% branch**. The component-specific targets of 85-95% statement / 80-95% branch presented in this document are **aspirational stretch goals** based on component complexity analysis. During implementation, >80% is the mandatory floor; higher targets are encouraged but not required.

**Deliverable:** Ready-to-use Jest coverage configuration + quality metrics framework

---

## 1. Coverage Requirements Analysis

### 1.1 Official CSAPI Requirements

From [`csapi-implementation-guide.md`](../../../planning/csapi-implementation-guide.md):

> **Code coverage**: >80% statement coverage, >80% branch coverage, 100% public API coverage

**Key Requirements:**

- **Statement Coverage:** >80% minimum
- **Branch Coverage:** >80% minimum
- **Public API Coverage:** 100% (all exported functions, classes, types)
- **Total Test Lines:** ~4,500-6,000 lines expected

**Status:** These are MINIMUM thresholds; component-specific targets may exceed these.

### 1.2 Industry Standards

From [Section 3: TypeScript Testing Standards](./03-typescript-testing-standards.md):

**Industry Targets:**

- **Statement Coverage:** 85-95% target, 80% minimum
- **Branch Coverage:** 80-90% target, 75% minimum
- **Function Coverage:** 90-100% target, 85% minimum

**Mature Library Priorities:**

1. **Branch coverage** (80%+) prioritized over statement coverage
2. **Error path coverage** explicitly tested
3. **Edge case coverage** documented and measured
4. **Assertion quality** more important than test quantity

**Examples from Major Libraries:**

- **@octokit/rest.js:** Aims for 100% coverage in critical areas
- **axios:** 95%+ coverage with extensive edge case testing
- **TypeORM:** 80-90% coverage with focus on integration tests

### 1.3 Upstream Coverage State

**Current Configuration (`jest.config.cjs`):**

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  transform: { '^.+\\.(ts|xml)$': ['<rootDir>/jest.ts-transformer.cjs', {...}] },
  setupFilesAfterEnv: ['./test-setup.ts'],
  coveragePathIgnorePatterns: ['.(xml)$'],  // Only XML files excluded
  moduleNameMapper: { '^(..?/.+)\\.c?jsx?$': '$1' }
};
```

**Findings:**

- ❌ No `coverageThreshold` property configured
- ❌ No coverage scripts in `package.json`
- ✅ `coveragePathIgnorePatterns` excludes only XML files
- ✅ Jest 29.7.0 installed (built-in coverage support via V8)

**Implication:** Coverage enforcement must be added to enforce quality standards.

### 1.4 Upstream Coverage Analysis

From [Section 1: EDR Test Blueprint](./01-edr-test-blueprint.md):

**EDR Coverage Characteristics:**

- **Test-to-Code Ratio:** ~1:4.8 (298 test lines / 2,858 implementation lines)
- **Coverage:** Not explicitly measured, but comprehensive based on evidence:
  - All 8 EDR query methods tested
  - Error paths systematically tested
  - Edge cases (empty params, datetime variations, Z parameter) covered
- **Coverage Gaps:**
  - `url_builder.ts` has no direct unit tests (only integration tests)
  - Corridor/trajectory queries only have error tests (not happy path)

**Takeaway:** Even without explicit coverage metrics, comprehensive testing is achievable through systematic scenario coverage.

---

## 2. Component-Specific Coverage Targets

### 2.1 Target Matrix

Based on component complexity, criticality, and testing effort from Sections 8-16:

| Component Type                          | Statement | Branch | Function | Rationale                                                                           | Test Lines (Est.)     |
| --------------------------------------- | --------- | ------ | -------- | ----------------------------------------------------------------------------------- | --------------------- |
| **QueryBuilders (URL Builders)**        | 90-95%    | 85-90% | 95-100%  | Core functionality, many parameter combinations, high cyclomatic complexity         | ~1,880-2,256 lines    |
| **Parsers (SensorML, SWE)**             | 90-95%    | 85-95% | 100%     | Complex nested structures, many formats (JSON/Text/Binary), critical data integrity | ~2,200-3,300 lines    |
| **Endpoint (OgcApiEndpoint)**           | 90-95%    | 85-90% | 100%     | Central orchestration logic, many resource types, complex workflows                 | ~4,800 lines          |
| **Utilities (Validators, Type Guards)** | 85-95%    | 80-90% | 90-100%  | Reusable across components, tested in isolation + integration, simpler logic        | ~500-800 lines        |
| **Worker Extensions**                   | 85-90%    | 80-85% | 95-100%  | Async complexity, background processing, message passing, critical for performance  | ~2,310-2,860 lines    |
| **Error Classes**                       | 90-100%   | 80-90% | 100%     | Critical for debugging, error messages, stack traces; simple but important          | ~200-300 lines        |
| **Type Definitions**                    | N/A       | N/A    | N/A      | No runtime code; validated at compile time only                                     | 0 lines (compilation) |
| **Integration Tests**                   | N/A       | N/A    | N/A      | Measure workflow coverage, not line coverage                                        | ~1,200-1,500 lines    |

**Total Estimated Test Lines:** ~13,090-17,016 lines

> **⚠️ Estimate Discrepancy (H1 review fix):** This component-level total of ~13,090–17,016 lines is **~3× higher** than all other estimates in the research series and the Implementation Guide:
>
> - **Implementation Guide** (§1.1 above): ~4,500–6,000 lines
> - **Doc 19** (authoritative file inventory, 22 files): ~4,040–5,340 lines
> - **Doc 20** (module-level estimates): ~4,150–5,850 lines
>
> The inflation appears to result from component estimates being developed independently (Sections 8–16) without reconciliation against the file-level inventory. For example, Endpoint alone is estimated at ~4,800 lines — nearly the entire budget from Doc 19. **The authoritative estimate is Doc 19's 4,040–5,340 lines across 22 files.** The coverage _percentage targets_ in this matrix remain valid; only the line count estimates are inflated. When planning test implementation, use Doc 19's file inventory as the sizing reference.

### 2.2 Detailed Component Targets

#### QueryBuilders (URL Builders)

**Coverage Targets:**

- **Statement:** 90-95%
- **Branch:** 85-90%
- **Function:** 95-100%

**Justification:**

- 9 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands)
- Each resource has 5-10 query parameters (temporal, spatial, entity filtering)
- Parameter combination logic creates high cyclomatic complexity
- Pagination, sorting, filtering all need branch testing

**Test Scenarios (153 tests, 1,880-2,256 lines):**

- Systems: 18 tests (~150-200 lines)
- Deployments: 16 tests (~120-180 lines)
- Procedures: 16 tests (~120-180 lines)
- SamplingFeatures: 16 tests (~120-180 lines)
- Properties: 12 tests (~90-130 lines)
- DataStreams: 21 tests (~150-220 lines)
- Observations: 18 tests (~120-180 lines)
- ControlStreams: 16 tests (~120-180 lines)
- Commands: 20 tests (~150-220 lines)

**Coverage Quality Indicators:**

- ✅ All parameter combinations tested (valid + invalid)
- ✅ All temporal filter formats tested (ISO 8601 intervals)
- ✅ All spatial filter formats tested (bbox, point, polygon)
- ✅ URL encoding edge cases tested (special characters, spaces)
- ✅ Pagination edge cases tested (limit=0, offset > total)

#### Parsers (SensorML + SWE Common)

**Coverage Targets:**

- **Statement:** 90-95%
- **Branch:** 85-95%
- **Function:** 100%

**Justification:**

- **SensorML:** 4 structure types (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess)
- **SWE Common:** 3 encodings (JSON, Text, Binary) × many data types
- Complex nested structures (recursive parsing, 4-5 levels deep)
- Critical for data integrity (sensor metadata, observation data)
- High error handling complexity (malformed XML/JSON, missing fields)

**Test Scenarios:**

- **SensorML:** 46-57 tests, 500-800 lines

  - PhysicalSystem: 12-15 tests (~150-225 lines)
  - PhysicalComponent: 8-10 tests (~80-120 lines)
  - SimpleProcess: 5-6 tests (~50-72 lines)
  - AggregateProcess: 8-10 tests (~80-150 lines)
  - Error handling: 8-10 tests (~64-100 lines)
  - Recursive structures: 5-6 tests (~75-120 lines)

- **SWE Common:** 195 tests, 1,700-2,500 lines
  - JSON encoding: 48 tests (~589-811 lines)
  - Text encoding: 43 tests (~491-646 lines)
  - Binary encoding: 96 tests (~1,447-1,896 lines) - **50% of effort**
  - Schema validation: 8 tests (~96-120 lines)

**Coverage Quality Indicators:**

- ✅ All nesting levels tested (1-5 levels deep)
- ✅ All data types tested (integers, floats, booleans, text, time, category, choice)
- ✅ All encoding formats tested (JSON, Text, Binary with endianness variants)
- ✅ All error conditions tested (malformed data, missing fields, type mismatches)
- ✅ All namespace variations tested (gml, sml, swe prefixes)

#### Endpoint (OgcApiEndpoint + CSAPI Resources)

**Coverage Targets:**

- **Statement:** 90-95%
- **Branch:** 85-90%
- **Function:** 100%

**Justification:**

- Central orchestration for all CSAPI operations
- 9 resource types with CRUD operations
- Complex filtering logic (temporal, spatial, entity)
- GeoJSON + SWE Common + SensorML validation
- High cyclomatic complexity (many code paths)

**Test Scenarios (250+ tests, ~4,800 lines):**

- **CRITICAL Priority:** Systems, DataStreams, Observations (~2,500 lines)
- **HIGH Priority:** Deployments, SamplingFeatures, ControlStreams, Commands (~1,500 lines)
- **MEDIUM Priority:** Procedures, Properties, Subdeployments (~800 lines)

**Coverage Quality Indicators:**

- ✅ All resource types tested (9 resources)
- ✅ All CRUD operations tested (list, get, create, update, delete, patch)
- ✅ All query parameters tested per resource
- ✅ All format validations tested (GeoJSON, SWE, SensorML)
- ✅ All error scenarios tested (404, 400, 500)

#### Utilities (Validators, Type Guards, Helpers)

**Coverage Targets:**

- **Statement:** 85-95%
- **Branch:** 80-90%
- **Function:** 90-100%

**Justification:**

- Reusable across all components
- Simpler logic than parsers/builders
- High function coverage due to small, focused functions
- Tested in both isolation (unit) and integration

**Test Scenarios:**

- Validators: ~200-300 lines (ISO 8601, bbox, GeoJSON, SWE)
- Type guards: ~100-150 lines (isSystem, isDataStream, etc.)
- Helpers: ~200-350 lines (URL encoding, pagination, sorting)

**Coverage Quality Indicators:**

- ✅ All validation rules tested (valid + invalid inputs)
- ✅ All type guards tested (positive + negative cases)
- ✅ All helper functions tested (edge cases + typical use)
- ✅ All error messages validated (clear, actionable)

#### Worker Extensions

**Coverage Targets:**

- **Statement:** 85-90%
- **Branch:** 80-85%
- **Function:** 95-100%

**Justification:**

- Async complexity (promises, callbacks, message passing)
- Background processing (parsing, validation)
- Critical for performance (large datasets)
- Moderate cyclomatic complexity (less than parsers)

**Test Scenarios (201 tests, 2,310-2,860 lines):**

- **Unit Tests:** 139 tests (~1,650-1,980 lines)

  - Message handling: 12 tests (~180-240 lines)
  - Worker lifecycle: 12 tests (~180-240 lines)
  - Error propagation: 18 tests (~270-360 lines)
  - Parser integration: 30 tests (~450-600 lines)
  - Validator integration: 18 tests (~270-360 lines)
  - Message serialization: 24 tests (~300-360 lines)
  - Resource-specific: 25 tests (~300-400 lines)

- **Integration Tests:** 62 tests (~660-880 lines)
  - Workflow tests: 32 tests (~384-512 lines)
  - Performance tests: 12 tests (~120-160 lines)
  - Error scenarios: 18 tests (~156-208 lines)

**Coverage Quality Indicators:**

- ✅ All message types tested (parse, validate, transform)
- ✅ All lifecycle events tested (start, stop, error, complete)
- ✅ All error propagation paths tested (worker → main thread)
- ✅ All async edge cases tested (timeouts, cancellation, race conditions)
- ✅ Large dataset handling tested (10K+ observations)

#### Error Classes

**Coverage Targets:**

- **Statement:** 90-100%
- **Branch:** 80-90%
- **Function:** 100%

**Justification:**

- Simple logic but critical for debugging
- Error messages must be clear and actionable
- Stack traces must be preserved
- Few branches (mostly straightforward constructors)

**Test Scenarios (~200-300 lines):**

- All custom error classes instantiated
- All error messages validated
- All stack traces preserved
- All error codes/types validated

**Coverage Quality Indicators:**

- ✅ All error classes instantiated
- ✅ All error messages validated (clear, actionable)
- ✅ All stack traces preserved (`Error.captureStackTrace`)
- ✅ All error metadata validated (code, type, context)

### 2.3 Overall Project Target

**Recommended Overall Targets:**

- **Statement Coverage:** 88-92% (weighted average)
- **Branch Coverage:** 83-88% (weighted average)
- **Function Coverage:** 95-98% (weighted average)

**Rationale:**

- Exceeds official >80% requirement
- Aligns with industry standards (85-95% statement, 80-90% branch)
- Component-specific targets reflect complexity and criticality
- Focuses on branch coverage (more meaningful than statement)

---

## 3. Meaningful Coverage Metrics

### 3.1 Beyond Percentage Coverage

**Problem:** 100% code coverage ≠ Quality tests

**Example of "Trivial Coverage":**

```typescript
// BAD: 100% coverage, 0% meaningful testing
function add(a: number, b: number): number {
  return a + b;
}

test('add function exists', () => {
  expect(add).toBeDefined();
  add(1, 2); // No assertion on result!
});
```

**Example of "Meaningful Coverage":**

```typescript
// GOOD: Tests behavior, edge cases, and error conditions
test('add calculates sum correctly', () => {
  expect(add(1, 2)).toBe(3);
  expect(add(-1, 1)).toBe(0);
  expect(add(0, 0)).toBe(0);
  expect(add(Number.MAX_VALUE, 1)).toBe(Number.MAX_VALUE + 1);
});
```

### 3.2 Coverage Quality Indicators

#### 3.2.1 Edge Case Coverage

**Definition:** Testing boundary conditions, extreme values, and unusual inputs

**Required Edge Cases per Component:**

**QueryBuilders:**

- ✅ Empty parameters (`{}`)
- ✅ Single parameter (`{limit: 10}`)
- ✅ All parameters combined
- ✅ Invalid parameter types (`{limit: "abc"}`)
- ✅ Boundary values (`{limit: 0}`, `{limit: -1}`, `{offset: Number.MAX_SAFE_INTEGER}`)
- ✅ Special characters in strings (`systemId: "sys/with/slashes"`)
- ✅ URL encoding edge cases (`name: "test & value"`)
- ✅ Temporal edge cases (open intervals: `../2024-01-31`, `2024-01-01/..`)

**Parsers:**

- ✅ Empty documents (`{}`, `""`)
- ✅ Minimal valid documents (only required fields)
- ✅ Maximal documents (all optional fields)
- ✅ Deeply nested structures (4-5 levels)
- ✅ Large arrays (100+ items)
- ✅ All data types (integers, floats, booleans, strings, dates)
- ✅ Malformed data (missing fields, wrong types, invalid values)
- ✅ Namespace variations (`gml:id` vs `id`, `sml:PhysicalSystem` vs `PhysicalSystem`)

**Endpoint:**

- ✅ Empty collections (`[]`)
- ✅ Single item collections (`[item]`)
- ✅ Large collections (1000+ items)
- ✅ Pagination edge cases (page 1, last page, page > total)
- ✅ Filtering edge cases (no matches, all matches)
- ✅ Sorting edge cases (single field, multiple fields, invalid field)

**Workers:**

- ✅ Empty messages (`{type: "parse", data: {}}`)
- ✅ Large messages (10K+ observations)
- ✅ Invalid messages (missing type, missing data)
- ✅ Timeout scenarios (slow parsing)
- ✅ Cancellation scenarios (abort mid-parse)
- ✅ Race conditions (multiple messages in parallel)

#### 3.2.2 Error Path Coverage

**Definition:** Testing all error conditions, exceptions, and failure modes

**Required Error Paths per Component:**

**QueryBuilders:**

- ✅ Invalid parameter types (TypeError)
- ✅ Invalid parameter values (RangeError)
- ✅ Invalid parameter combinations (ValidationError)

**Parsers:**

- ✅ Malformed JSON/XML (SyntaxError)
- ✅ Missing required fields (ValidationError)
- ✅ Invalid field types (TypeError)
- ✅ Invalid field values (RangeError)
- ✅ Schema validation failures (SchemaError)
- ✅ Namespace resolution failures (NamespaceError)

**Endpoint:**

- ✅ HTTP 404 Not Found (missing resource)
- ✅ HTTP 400 Bad Request (invalid parameters)
- ✅ HTTP 500 Internal Server Error (parsing failure)
- ✅ Network errors (timeout, connection refused)
- ✅ Validation errors (invalid GeoJSON, invalid SWE)

**Workers:**

- ✅ Message handling errors (unknown message type)
- ✅ Parsing errors (malformed data)
- ✅ Validation errors (invalid schema)
- ✅ Timeout errors (slow operations)
- ✅ Cancellation errors (aborted operations)
- ✅ Memory errors (large datasets)

**Error Path Coverage Metric:**

```
Error Path Coverage = (Error Paths Tested / Total Error Paths) × 100%
```

**Target:** 90-100% error path coverage (all error types tested)

#### 3.2.3 Assertion Quality

**Definition:** Tests must verify expected behavior, not just execution

**Quality Criteria:**

1. **Specific Assertions:** Use `.toBe()`, `.toEqual()`, `.toStrictEqual()` over `.toBeDefined()`

   ```typescript
   // BAD
   expect(result).toBeDefined();

   // GOOD
   expect(result).toEqual({ id: 'sys1', name: 'System 1' });
   ```

2. **Multiple Assertions:** Verify all aspects of result

   ```typescript
   // BAD
   expect(result).toBeDefined();

   // GOOD
   expect(result.id).toBe('sys1');
   expect(result.name).toBe('System 1');
   expect(result.type).toBe('PhysicalSystem');
   expect(result.properties).toHaveLength(3);
   ```

3. **Error Assertions:** Verify error type, message, and context

   ```typescript
   // BAD
   expect(() => parse(invalid)).toThrow();

   // GOOD
   expect(() => parse(invalid)).toThrow(ValidationError);
   expect(() => parse(invalid)).toThrow('Missing required field: id');
   ```

4. **State Verification:** Verify side effects, not just return values

   ```typescript
   // BAD
   client.createSystem(system);

   // GOOD
   await client.createSystem(system);
   expect(client.cache.has('sys1')).toBe(true);
   expect(client.cache.get('sys1')).toEqual(system);
   ```

**Assertion Quality Metric:**

```
Assertion Quality = (Specific Assertions / Total Assertions) × 100%
```

**Target:** 80-90% specific assertions (avoid `.toBeDefined()`, `.toBeTruthy()`)

#### 3.2.4 Client Code Coverage

> **⚠️ Review Notice (M2 fix — Phase 2C):** This section originally framed coverage as "Behavior Tests / Total Requirements" — measuring test coverage against OGC spec requirements rather than client code paths. This is AP3 (OGC Requirement Traceability): it organizes testing around spec sections instead of the code being contributed. Coverage should measure what client code functions and methods are exercised by tests, not what spec requirements have corresponding tests.

**Definition:** Tests cover the client code paths being contributed — URL builder methods, parser functions, error handlers, type converters.

**Coverage by client code area:**

**QueryBuilder methods:**

- ✅ All resource type methods covered (getSystems, getDeployments, etc.)
- ✅ Parameter encoding paths (pagination, bbox, datetime, filtering)
- ✅ Edge cases per method (empty params, boundary values, special characters)

**Parser functions:**

- ✅ Each parser's happy path (valid input → correct output)
- ✅ Each parser's error path (malformed input → appropriate error)
- ✅ Optional field handling (present vs absent)

**Endpoint methods:**

- ✅ Each public method exercised
- ✅ Error handling paths (network errors, 404, malformed responses)
- ✅ Conformance-dependent behavior (feature available vs not)

**Practical coverage metric:**

```
Client Code Coverage = (Tested functions & branches / Total functions & branches) × 100%
```

**Target:** Use Jest's built-in `--coverage` reporting (statement, branch, function coverage) rather than manually tracking spec requirements.

### 3.3 Coverage Quality Checklist

Use this checklist to evaluate test quality beyond raw percentages:

**Per Test Suite:**

- [ ] All edge cases documented and tested
- [ ] All error paths documented and tested
- [ ] All assertions are specific (not just `.toBeDefined()`)
- [ ] All public client methods have corresponding tests
- [ ] All tests have descriptive names (`it('should...')`)
- [ ] All tests are isolated (no shared state)
- [ ] All tests are deterministic (no flaky tests)
- [ ] All tests run quickly (<100ms per test)

**Per Component:**

- [ ] Coverage targets met (statement, branch, function)
- [ ] Edge case coverage ≥90%
- [ ] Error path coverage ≥90%
- [ ] Assertion quality ≥80%
- [ ] All public methods have tests

**Overall Project:**

- [ ] Overall coverage targets met (88-92% statement, 83-88% branch)
- [ ] No coverage regressions (coverage doesn't decrease)
- [ ] Coverage reports generated automatically (CI/CD)
- [ ] Coverage trends tracked over time

---

## 4. Jest Configuration Specification

> **⚠️ Review Notice (L2 fix — Phase 2C):** The configuration below is a **template for future use** — the CSAPI files it references (e.g., `./src/ogc-api/csapi/url_builder.ts`, `./src/ogc-api/csapi/parsers/*.ts`) do not exist yet. This configuration should be adapted and committed incrementally as implementation progresses through ROADMAP phases, not committed as-is before any CSAPI code exists.

### 4.1 Coverage Configuration

Add the following to `jest.config.cjs` (adapt paths as implementation progresses):

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.(ts|xml)$': [
      '<rootDir>/jest.ts-transformer.cjs',
      {
        /* ... */
      },
    ],
  },
  setupFilesAfterEnv: ['./test-setup.ts'],
  coveragePathIgnorePatterns: [
    '.(xml)$', // XML fixtures
    '.d.ts$', // Type definitions
    '/fixtures/', // Test fixtures
    '/examples/', // Example code
    'test-setup.ts', // Test setup
    'test-setup.node.ts', // Node test setup
  ],
  moduleNameMapper: {
    '^(..?/.+)\\.c?jsx?$': '$1',
  },

  // ===== NEW: Coverage Configuration =====
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.ts', // Re-exports only
  ],
  coverageReporters: [
    'text', // Console output
    'text-summary', // Summary for CI
    'html', // HTML report for local dev
    'json', // JSON for tooling
    'lcov', // LCOV for CI integration
  ],
  coverageDirectory: 'coverage',

  // Overall thresholds (enforced across all files)
  coverageThreshold: {
    global: {
      statements: 80, // Official minimum
      branches: 80, // Official minimum
      functions: 85, // Higher for small, focused functions
      lines: 80, // Matches statements
    },

    // Component-specific thresholds
    './src/ogc-api/csapi/url_builder.ts': {
      statements: 90,
      branches: 85,
      functions: 95,
      lines: 90,
    },
    './src/ogc-api/csapi/endpoint.ts': {
      statements: 90,
      branches: 85,
      functions: 100,
      lines: 90,
    },
    './src/ogc-api/csapi/parsers/*.ts': {
      statements: 90,
      branches: 85,
      functions: 100,
      lines: 90,
    },
    './src/ogc-api/csapi/validators/*.ts': {
      statements: 85,
      branches: 80,
      functions: 90,
      lines: 85,
    },
    './src/worker/*.ts': {
      statements: 85,
      branches: 80,
      functions: 95,
      lines: 85,
    },
    './src/shared/errors/*.ts': {
      statements: 90,
      branches: 80,
      functions: 100,
      lines: 90,
    },
  },
};
```

### 4.2 Coverage Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "test": "jest",
    "test:browser": "jest --config jest.config.cjs",
    "test:node": "jest --config jest.node.config.cjs",

    // NEW: Coverage scripts
    "test:coverage": "jest --coverage",
    "test:coverage:browser": "jest --config jest.config.cjs --coverage",
    "test:coverage:node": "jest --config jest.node.config.cjs --coverage",
    "coverage:report": "open coverage/lcov-report/index.html", // macOS
    "coverage:report:win": "start coverage/lcov-report/index.html" // Windows
  }
}
```

### 4.3 Coverage Enforcement

**Local Development:**

```bash
# Run tests with coverage (no threshold enforcement by default)
npm run test:coverage

# View HTML report
npm run coverage:report      # macOS/Linux
npm run coverage:report:win  # Windows
```

**CI/CD (Enforce Thresholds):**

```bash
# Run tests with coverage and enforce thresholds (fails if below targets)
npm run test:coverage -- --coverageThreshold

# Or set in CI configuration
CI=true npm run test:coverage
```

### 4.4 Incremental Thresholds (Per ROADMAP Phase)

**Problem:** Cannot achieve 90% coverage immediately; need incremental targets

**Solution:** Phase-based coverage ratcheting

**Phase 4 (Current - Testing Infrastructure):**

- Global: 50% statement, 50% branch (baseline)
- Critical components: 70% statement, 65% branch
- Goal: Establish coverage infrastructure and baseline

**Phase 5 (CSAPI Implementation):**

- Global: 70% statement, 70% branch
- Critical components (Systems, DataStreams, Observations): 85% statement, 80% branch
- Goal: High coverage for core resources

**Phase 6 (Advanced Features):**

- Global: 80% statement, 80% branch (meets official requirement)
- All components: 85%+ statement, 80%+ branch
- Goal: Meet official coverage targets

**Phase 7 (Optional Features):**

- Global: 88% statement, 83% branch
- All components: 90%+ statement, 85%+ branch
- Goal: Exceed official targets, approach industry best practices

**Implementation:** Update `coverageThreshold` in `jest.config.cjs` after each phase

---

## 5. Incremental Tracking Strategy

### 5.1 Coverage Tracking Workflow

**Step 1: Establish Baseline (Phase 4)**

```bash
# Run initial coverage
npm run test:coverage

# Save baseline report
mkdir -p docs/research/testing/coverage-reports
cp coverage/coverage-summary.json docs/research/testing/coverage-reports/baseline-phase4.json
```

**Step 2: Track Progress (Each PR)**

```bash
# Run coverage before changes
npm run test:coverage
cp coverage/coverage-summary.json coverage-before.json

# Make changes, write tests
# ...

# Run coverage after changes
npm run test:coverage
cp coverage/coverage-summary.json coverage-after.json

# Compare (manual or with tool)
diff coverage-before.json coverage-after.json
```

**Step 3: Prevent Regressions (CI/CD)**

```yaml
# .github/workflows/test.yml (example)
- name: Run tests with coverage
  run: npm run test:coverage

- name: Check coverage thresholds
  run: npm run test:coverage -- --coverageThreshold

- name: Upload coverage to Codecov (optional)
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

### 5.2 Coverage Regression Prevention

**Goal:** Coverage should never decrease (ratcheting effect)

**Strategy 1: Git Hook (Pre-Commit)**

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run coverage
npm run test:coverage --silent

# Extract current coverage
CURRENT=$(grep -oP '"statements":\s*\{\s*"pct":\s*\K[0-9.]+' coverage/coverage-summary.json | head -1)

# Extract baseline coverage
BASELINE=$(grep -oP '"statements":\s*\{\s*"pct":\s*\K[0-9.]+' docs/research/testing/coverage-reports/baseline-phase4.json | head -1)

# Compare
if (( $(echo "$CURRENT < $BASELINE" | bc -l) )); then
  echo "❌ Coverage regression detected: $CURRENT% < $BASELINE%"
  exit 1
fi

echo "✅ Coverage maintained: $CURRENT% >= $BASELINE%"
```

**Strategy 2: CI/CD Check**

```yaml
# .github/workflows/test.yml
- name: Run coverage
  run: npm run test:coverage

- name: Check for coverage regression
  run: |
    CURRENT=$(jq '.total.statements.pct' coverage/coverage-summary.json)
    BASELINE=$(jq '.total.statements.pct' docs/research/testing/coverage-reports/baseline-phase4.json)
    if (( $(echo "$CURRENT < $BASELINE" | bc -l) )); then
      echo "❌ Coverage regression detected"
      exit 1
    fi
```

**Strategy 3: Coverage Badge (README.md)**

```markdown
<!-- README.md -->

![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
```

### 5.3 Coverage Monitoring

**Recommended Tools:**

1. **Codecov** (Free for open source)

   - Automatic coverage reports on PRs
   - Coverage trends over time
   - Coverage diffs (before/after)
   - GitHub integration

2. **Coveralls** (Free for open source)

   - Similar to Codecov
   - Slightly different UI

3. **SonarCloud** (Free for open source)
   - Coverage + code quality metrics
   - Security scanning
   - Technical debt tracking

**Setup Example (Codecov):**

```yaml
# .github/workflows/test.yml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
    flags: unittests
    name: codecov-ogc-client-csapi
```

---

## 6. Success Criteria

### 6.1 Phase 4 (Current Phase)

**Coverage Infrastructure:**

- [x] Jest coverage configuration added to `jest.config.cjs`
- [x] Coverage scripts added to `package.json`
- [ ] Baseline coverage report generated and saved
- [ ] Coverage regression prevention implemented (git hook or CI)

**Baseline Targets (Phase 4):**

- [ ] Global: 50% statement, 50% branch
- [ ] Critical components: 70% statement, 65% branch

### 6.2 Phase 5 (CSAPI Implementation)

**Coverage Targets:**

- [ ] Global: 70% statement, 70% branch
- [ ] Systems: 85% statement, 80% branch
- [ ] DataStreams: 85% statement, 80% branch
- [ ] Observations: 85% statement, 80% branch

**Quality Metrics:**

- [ ] Edge case coverage ≥85%
- [ ] Error path coverage ≥85%
- [ ] Assertion quality ≥75%

### 6.3 Phase 6 (Advanced Features)

**Coverage Targets:**

- [ ] Global: 80% statement, 80% branch (official requirement met)
- [ ] All components: 85%+ statement, 80%+ branch

**Quality Metrics:**

- [ ] Edge case coverage ≥90%
- [ ] Error path coverage ≥90%
- [ ] Assertion quality ≥80%
- [ ] All public methods have tests

### 6.4 Phase 7 (Optional Features)

**Coverage Targets:**

- [ ] Global: 88% statement, 83% branch
- [ ] All components: 90%+ statement, 85%+ branch

**Quality Metrics:**

- [ ] All quality metrics ≥90%
- [ ] Zero coverage regressions
- [ ] Coverage trends tracked (Codecov/Coveralls)

---

## 7. Implementation Checklist

### 7.1 Immediate Actions (Phase 4)

- [ ] Add coverage configuration to `jest.config.cjs` (Section 4.1)
- [ ] Add coverage scripts to `package.json` (Section 4.2)
- [ ] Run `npm run test:coverage` to generate baseline report
- [ ] Save baseline report to `docs/research/testing/coverage-reports/baseline-phase4.json`
- [ ] Add `.gitignore` entry for `coverage/` directory (keep reports out of Git)
- [ ] Implement coverage regression prevention (git hook or CI check)

### 7.2 Per Test Implementation

**Before Writing Tests:**

- [ ] Review component-specific coverage targets (Section 2.2)
- [ ] Review coverage quality indicators (Section 3.2)
- [ ] Review coverage quality checklist (Section 3.3)

**During Test Implementation:**

- [ ] Write tests for each public method and code path
- [ ] Add edge case tests (boundary conditions)
- [ ] Add error path tests (all error types)
- [ ] Use specific assertions (avoid `.toBeDefined()`)
- [ ] Verify test isolation (no shared state)

**After Test Implementation:**

- [ ] Run `npm run test:coverage` to verify coverage
- [ ] Review coverage report (HTML or console)
- [ ] Verify coverage targets met for component
- [ ] Verify coverage quality indicators met
- [ ] Commit tests + coverage report update

### 7.3 Per ROADMAP Phase

**Phase End Checklist:**

- [ ] Run full coverage report (`npm run test:coverage`)
- [ ] Verify phase coverage targets met (Section 5.1)
- [ ] Update `coverageThreshold` in `jest.config.cjs` for next phase
- [ ] Save phase coverage report to `docs/research/testing/coverage-reports/phase-X.json`
- [ ] Update coverage badge in README.md (if applicable)
- [ ] Document any coverage gaps or exceptions

---

## 8. Appendix: Coverage Calculation Examples

### 8.1 Statement Coverage

**Code:**

```typescript
function divide(a: number, b: number): number {
  if (b === 0) {
    throw new Error('Division by zero');
  }
  return a / b;
}
```

**Test (50% statement coverage):**

```typescript
test('divide calculates quotient', () => {
  expect(divide(10, 2)).toBe(5);
});
// Covers: line 4 (return statement)
// Does NOT cover: lines 2-3 (if statement + throw)
// Statement Coverage: 1/2 = 50%
```

**Test (100% statement coverage):**

```typescript
test('divide calculates quotient', () => {
  expect(divide(10, 2)).toBe(5);
});

test('divide throws on division by zero', () => {
  expect(() => divide(10, 0)).toThrow('Division by zero');
});
// Covers: all 4 lines
// Statement Coverage: 4/4 = 100%
```

### 8.2 Branch Coverage

**Code:**

```typescript
function getStatus(value: number): string {
  if (value > 0) {
    return 'positive';
  } else if (value < 0) {
    return 'negative';
  } else {
    return 'zero';
  }
}
```

**Test (33% branch coverage):**

```typescript
test('getStatus returns positive', () => {
  expect(getStatus(5)).toBe('positive');
});
// Covers: 1 branch (value > 0)
// Does NOT cover: value < 0, value === 0
// Branch Coverage: 1/3 = 33%
```

**Test (100% branch coverage):**

```typescript
test('getStatus returns positive', () => {
  expect(getStatus(5)).toBe('positive');
});

test('getStatus returns negative', () => {
  expect(getStatus(-5)).toBe('negative');
});

test('getStatus returns zero', () => {
  expect(getStatus(0)).toBe('zero');
});
// Covers: all 3 branches
// Branch Coverage: 3/3 = 100%
```

### 8.3 Function Coverage

**Code:**

```typescript
function add(a: number, b: number): number {
  return a + b;
}

function subtract(a: number, b: number): number {
  return a - b;
}

function multiply(a: number, b: number): number {
  return a * b;
}
```

**Test (33% function coverage):**

```typescript
test('add calculates sum', () => {
  expect(add(1, 2)).toBe(3);
});
// Covers: 1 function (add)
// Does NOT cover: subtract, multiply
// Function Coverage: 1/3 = 33%
```

**Test (100% function coverage):**

```typescript
test('add calculates sum', () => {
  expect(add(1, 2)).toBe(3);
});

test('subtract calculates difference', () => {
  expect(subtract(5, 3)).toBe(2);
});

test('multiply calculates product', () => {
  expect(multiply(2, 3)).toBe(6);
});
// Covers: all 3 functions
// Function Coverage: 3/3 = 100%
```

---

## 9. References

1. [Section 1: EDR Test Blueprint](./01-edr-test-blueprint.md) - Upstream coverage analysis
2. [Section 3: TypeScript Testing Standards](./03-typescript-testing-standards.md) - Industry coverage standards
3. [Section 8: CSAPI Specification Test Requirements](./08-csapi-specification-test-requirements.md) - Endpoint test lines
4. [Section 9: SensorML Testing Requirements](./09-sensorml-testing-requirements.md) - SensorML test lines
5. [Section 10: SWE Common Testing Requirements](./10-swe-common-testing-requirements.md) - SWE Common test lines
6. [Section 12: QueryBuilder Testing Strategy](./12-querybuilder-testing-strategy.md) - URL Builder test lines
7. [Section 16: Worker Extensions Testing Strategy](./16-worker-extensions-testing.md) - Worker test lines
8. [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) - Official coverage requirements
9. [Jest Coverage Configuration](https://jestjs.io/docs/configuration#coveragethreshold-object) - Jest docs

---

**Document Status:** ✅ COMPLETE  
**Next Steps:**

1. Implement Jest coverage configuration (Section 4)
2. Establish baseline coverage (Section 5)
3. Begin Phase 4 test implementation with coverage tracking
