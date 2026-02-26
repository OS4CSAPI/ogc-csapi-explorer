# Section 36: Test Quality Checklist and Review Process

**Research Plan:** [Research Plan 36: Test Quality Checklist and Review Process](../research-plans/36-test-quality-checklist-review-process.md)

**Research Questions:** 6 core questions about validating "meaningful" tests, defining "useful" tests, constituting "deep" testing, validating "end-to-end" tests, reviewing tests against checklist, and sign-off process.

**Methodology:** 6-phase systematic analysis (Phase 1: Quality Criteria Extraction → Phase 2: Checklist Item Design → Phase 3: Review Process Design → Phase 4: Component-Specific Criteria → Phase 5: Quality Metrics Design → Phase 6: Synthesis)

**Research Time:** 50 minutes – February 6, 2026

**Primary Source(s):**

- Section 6 deliverable: "Meaningful vs Trivial" guide
- Section 7 deliverable: E2E scope definition
- All previous section deliverables: Component-specific quality criteria
- [Lessons Learned Analysis](../../requirements/lessons-learned-analysis.md)

**Supporting Resources:**

- Section 17: [Coverage Targets and Metrics](17-coverage-targets-and-metrics.md) (coverage criteria)
- Section 18: [Error Condition Testing Strategy](18-error-condition-testing-strategy.md) (error test completeness)
- Section 35: [JSDoc Testing Documentation Standards](35-jsdoc-testing-documentation-standards.md) (documentation requirements)

**Document Purpose:** Comprehensive quality checklist (41 items across 6 categories) and 3-stage review process to validate tests meet "meaningful, useful, deep, end-to-end" criteria before completion, serving as the final quality gate.

---

## Executive Summary

This document provides a comprehensive quality checklist and review process for validating that CSAPI tests meet the "meaningful, useful, deep, end-to-end" criteria established in the lessons learned analysis. This checklist serves as the final quality gate before tests are considered complete.

### Key Quality Dimensions

**From Senior Developer Feedback:**

> "Tests were too trivial" - Previous iteration lacked meaningful validation

**Four Quality Dimensions:**

1. **Meaningful** - Tests real behavior with real scenarios (not mocks/stubs)
2. **Useful** - Catches real bugs, provides value, maintainable
3. **Deep** - Comprehensive coverage including edge cases, not just happy path
4. **End-to-End** - Complete workflows, cross-component integration

### Quality Philosophy

**Quality Over Quantity:**

- ❌ 1,000 trivial tests: High line count, low value
- ✅ 300 meaningful tests: Lower line count, high value

**Real Behavior Over Mocks:**

- ❌ Test that mocks return expected data
- ✅ Test that code correctly processes real spec examples

**Spec-Informed Client Behavior:**

- ❌ Test implementation details (private methods, internals)
- ❌ Test spec conformance (whether a server is spec-compliant)
- ✅ Test that client code behaves correctly (URLs, parsing, error handling)
- ✅ Use spec knowledge as input to understand what correct behavior looks like

### Checklist Overview

> **⚠️ Review Notice (H2 fix):** The original 41-item / 3-stage enterprise review process with invented roles (Self-Review → Peer Review → Tech Lead Sign-Off) has been simplified to align with upstream `camptocamp/ogc-client` conventions. Upstream uses standard GitHub PR review with no formal quality gate, no distinct reviewer roles, and no multi-stage sign-off. The checklist below retains the most valuable quality checks as a **single-stage self-review** the developer runs before submitting a PR.

| Quality Dimension | Key Checks                                              | Review Stage |
| ----------------- | ------------------------------------------------------- | ------------ |
| **Meaningful**    | Real fixtures, behavior assertions, complete validation | Self-review  |
| **Useful**        | Bug detection, clear failures, fast execution           | Self-review  |
| **Deep**          | Edge cases, error paths, branch coverage                | Self-review  |
| **Coverage**      | Statement >80%, Branch >80%, no flakiness               | Self-review  |

> **Note (Phase 4 Review):** The ROADMAP v3.0 authoritative minimum is **>80% statement, >80% branch**. The component-specific targets of 85-95% / 80-95% that appear throughout this document (D-5, QM-1, QM-2, coverage examples) are **aspirational stretch goals** from Doc 17's component complexity analysis, not mandatory requirements. The self-review checklist above uses the >80% ROADMAP minimum as the acceptance threshold.

### Review Process

**Single-Stage Self-Review:**

1. Developer completes the condensed checklist before PR submission
2. Standard GitHub PR review by maintainer (upstream convention)

**Typical Timeline:**

- Self-review checklist: 5–10 minutes per test file

---

## 1. Quality Criteria Extraction

### 1.1 "Meaningful" Test Criteria

**Source:** Lessons Learned Analysis, Section 12 (QueryBuilder Testing)

**Definition:**

> Meaningful tests validate REAL behavior with REAL scenarios, not just mocks returning expected data.

**Characteristics:**

| Meaningful Test                    | Trivial Test                    |
| ---------------------------------- | ------------------------------- |
| Uses real spec examples            | Uses made-up test data          |
| Validates complete URL structure   | Checks `.toContain('/systems')` |
| Parses query parameters as objects | Uses regex or string matching   |
| Tests with realistic data volumes  | Tests with minimal data         |
| Validates correct client behavior  | Checks method exists            |
| Asserts on behavior                | Asserts on structure only       |

**Example - URL Testing:**

```typescript
// ❌ TRIVIAL
it('returns systems URL', () => {
  const url = builder.getSystems();
  expect(url).toContain('/systems'); // Doesn't validate structure
});

// ✅ MEANINGFUL
it('constructs systems URL with pagination', () => {
  const url = builder.getSystems({ limit: 10, offset: 20 });

  const parsed = parseAndValidateUrl(url, {
    protocol: 'https:',
    host: 'api.example.com',
    pathname: '/systems',
    query: { limit: '10', offset: '20' },
  });

  // Validates protocol, host, path, and structured query params
});
```

**Meaningful Test Indicators:**

- ✅ Uses real spec examples (from OGC 23-001/23-002/23-003)
- ✅ Validates complete structures (not just `.toBeTruthy()`)
- ✅ Tests realistic scenarios (not contrived edge cases)
- ✅ Asserts on important behavior (not implementation details)
- ✅ Uses real fixtures from real servers (gnosis-earth, OpenSensorHub)
- ✅ Validates correct client behavior (informed by spec expectations)
- ✅ Tests integration points (how components work together)
- ✅ Validates error messages are clear and actionable

### 1.2 "Useful" Test Criteria

**Source:** Lessons Learned Analysis, Industry Standards

**Definition:**

> Useful tests catch REAL bugs and provide VALUE to maintainers.

**Characteristics:**

| Useful Test                   | Useless Test                       |
| ----------------------------- | ---------------------------------- |
| Catches bugs when code breaks | Always passes (even when broken)   |
| Clear failure messages        | Generic "expected true, got false" |
| Fast execution (< 100ms unit) | Slow execution (> 1s unit)         |
| Independent (can run alone)   | Depends on test order              |
| Tests public API              | Tests private internals            |
| Maintainable (clear intent)   | Brittle (breaks on refactors)      |

**Example - Bug Detection:**

```typescript
// ❌ USELESS - Always passes
it('builder has getSystems method', () => {
  expect(typeof builder.getSystems).toBe('function');
  // Passes even if getSystems() is broken
});

// ✅ USEFUL - Catches real bugs
it('constructs systems URL correctly', () => {
  const url = builder.getSystems({ limit: 10 });

  // This WILL fail if:
  // - Query parameter encoding is wrong
  // - Parameter name is wrong ('max' instead of 'limit')
  // - Base URL construction fails
  // - Optional parameters aren't handled

  expect(
    parseAndValidateUrl(url, {
      pathname: '/systems',
      query: { limit: '10' },
    })
  ).toBeDefined();
});
```

**Useful Test Indicators:**

- ✅ Intentionally break code → test fails (validated)
- ✅ Failure messages clearly indicate problem
- ✅ Runs in < 100ms (unit) or < 1s (integration)
- ✅ Can run in isolation (no hidden dependencies)
- ✅ Tests externally visible behavior
- ✅ Survives refactoring (tests interface, not implementation)
- ✅ Helps debug failures quickly

### 1.3 "Deep" Test Criteria

**Source:** Section 17 (Coverage Targets), Section 18 (Error Testing)

**Definition:**

> Deep tests cover happy path, edge cases, error conditions, and all code paths systematically.

**Coverage Dimensions:**

| Dimension              | Target            | Indicator                   |
| ---------------------- | ----------------- | --------------------------- |
| **Statement Coverage** | 85-95%            | All lines executed          |
| **Branch Coverage**    | 80-95%            | All if/else/switch paths    |
| **Edge Case Coverage** | 100% identified   | All edge cases tested       |
| **Error Coverage**     | 100% error types  | All error conditions tested |
| **Spec Coverage**      | 100% requirements | All spec sections validated |

**Example - Deep Coverage:**

```typescript
// ❌ SHALLOW - Only happy path
describe('getSystems', () => {
  it('returns systems URL', () => {
    const url = builder.getSystems({ limit: 10 });
    expect(url).toContain('limit=10');
  });
});

// ✅ DEEP - Covers all paths
describe('getSystems', () => {
  it('constructs URL with no parameters', () => {
    // Edge case: empty options
  });

  it('constructs URL with limit only', () => {
    // Happy path: common case
  });

  it('constructs URL with all parameters', () => {
    // Edge case: maximum parameters
  });

  it('handles zero limit', () => {
    // Edge case: boundary value
  });

  it('handles null parameters', () => {
    // Edge case: null handling
  });

  it('throws on invalid bbox', () => {
    // Error condition: validation failure
  });

  it('properly encodes special characters', () => {
    // Edge case: encoding
  });
});
```

**Deep Test Indicators:**

- ✅ Happy path thoroughly tested
- ✅ Boundary values tested (0, 1, max, min)
- ✅ Edge cases documented and tested (empty, null, undefined)
- ✅ Error conditions systematically tested (invalid input, missing data)
- ✅ All code paths executed (branch coverage)
- ✅ Meets component-specific coverage targets (85-95%)
- ✅ Tests all parameter combinations (for small parameter sets)
- ✅ Validates error messages are clear
- ✅ Tests integration points between components

### 1.4 "End-to-End" Test Criteria

**Source:** Section 14 (Integration Testing), Section 5 (Roadmap Testing Integration)

**Definition:**

> End-to-end tests validate complete user workflows from endpoint detection through resource navigation to data retrieval.

**Workflow Characteristics:**

| E2E Workflow                   | Not E2E                   |
| ------------------------------ | ------------------------- |
| Multiple components integrated | Single component isolated |
| Real fixtures from spec        | Synthetic test data       |
| Navigation between resources   | Single resource access    |
| Complete user scenario         | Partial operation         |
| Round-trip validation          | One-way operation         |

**Example - E2E Workflow:**

```typescript
// ❌ NOT E2E - Single operation
it('retrieves system', async () => {
  const system = await endpoint.getSystem('sys-123');
  expect(system.id).toBe('sys-123');
});

// ✅ E2E - Complete workflow
it('completes observation query workflow end-to-end', async () => {
  // 1. Detect CSAPI endpoint
  const endpoint = new OgcApiEndpoint('https://api.example.com');
  expect(endpoint).toSupportCSAPI();

  // 2. Retrieve systems collection
  const systems = await endpoint.getFeatures('systems');
  expect(systems.features).toHaveLength(1);

  // 3. Navigate to specific system
  const system = systems.features[0];
  expect(system.id).toBe('weather-station-001');

  // 4. Retrieve system's datastreams
  const datastreams = await endpoint.getFeatures('datastreams', {
    system: system.id,
  });
  expect(datastreams.features).toHaveLength(3);

  // 5. Query observations for datastream
  const observations = await endpoint.getFeatures('observations', {
    datastream: datastreams.features[0].id,
    datetime: '2024-01-01T00:00:00Z/..',
  });
  expect(observations.features.length).toBeGreaterThan(0);

  // 6. Validate observation structure
  const obs = observations.features[0];
  expect(obs.properties.phenomenonTime).toBeDefined();
  expect(obs.properties.result).toBeDefined();
});
```

**E2E Test Indicators:**

- ✅ Tests complete user workflows (3+ operations)
- ✅ Uses real fixtures from spec examples
- ✅ Validates cross-component integration
- ✅ Tests resource navigation (via links)
- ✅ Validates round-trip scenarios (create → read → update → delete)
- ✅ Uses realistic data volumes (not minimal test data)

---

## 2. Comprehensive Test Quality Checklist

### 2.1 Meaningful Test Validation

**Purpose:** Ensure tests validate real behavior with real scenarios

| #   | Checklist Item                                                | Critical? | How to Validate                                                                           |
| --- | ------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------- |
| M-1 | Tests use real spec examples (from OGC 23-001/23-002/23-003)  | ✅ YES    | Review fixtures - must match spec examples                                                |
| M-2 | Tests validate complete structures (not just `.toBeTruthy()`) | ✅ YES    | Search for `toBeTruthy()` - must have follow-up assertions                                |
| M-3 | Tests use realistic scenarios (not contrived)                 | ❌ NO     | Review test names - should match real-world usage                                         |
| M-4 | Tests assert on behavior (not implementation details)         | ✅ YES    | Tests should not access private methods/properties                                        |
| M-5 | Tests use real fixtures from real servers                     | ❌ NO     | Check fixture sources (gnosis-earth, OpenSensorHub)                                       |
| M-6 | Tests validate correct client behavior (informed by spec)     | ✅ YES    | Verify tests assert on client outputs (URLs, parsed objects, errors) not spec conformance |
| M-7 | Tests validate integration points                             | ❌ NO     | Integration tests exist for cross-component scenarios                                     |
| M-8 | Error messages are clear and actionable                       | ❌ NO     | Error tests validate message content                                                      |

**M-1 Example:**

```typescript
// ✅ GOOD - Uses real spec example
const system = parseFixture(
  'fixtures/csapi/systems/system-weather-station.json'
);
// From OGC 23-001 Example 7.2.1

// ❌ BAD - Made-up test data
const system = { id: 'test-123', type: 'Feature' };
```

**M-2 Example:**

```typescript
// ❌ BAD - Only toBeTruthy
expect(builder.getSystems()).toBeTruthy();

// ✅ GOOD - Complete validation
const url = builder.getSystems({ limit: 10 });
const parsed = parseAndValidateUrl(url, {
  pathname: '/systems',
  query: { limit: '10' },
});
```

**M-4 Example:**

```typescript
// ❌ BAD - Tests internal implementation
expect(builder._buildQueryString({ limit: 10 })).toBe('limit=10');

// ✅ GOOD - Tests public behavior
const url = builder.getSystems({ limit: 10 });
expect(parseAndValidateUrl(url, { query: { limit: '10' } })).toBeDefined();
```

### 2.2 Useful Test Validation

**Purpose:** Ensure tests catch real bugs and provide value

| #   | Checklist Item                                            | Critical? | How to Validate                               |
| --- | --------------------------------------------------------- | --------- | --------------------------------------------- |
| U-1 | Tests catch real bugs (validated by intentional breakage) | ✅ YES    | Break code → test should fail                 |
| U-2 | Failure messages are clear and specific                   | ✅ YES    | Review error assertions - no generic messages |
| U-3 | Tests run quickly (< 100ms unit, < 1s integration)        | ❌ NO     | Run test suite - check timing in output       |
| U-4 | Tests are independent (can run in isolation)              | ✅ YES    | Run single test - should pass without others  |
| U-5 | Tests validate public API (not private internals)         | ❌ NO     | No tests of private methods/properties        |
| U-6 | Tests survive refactoring                                 | ❌ NO     | Refactor implementation - tests still pass    |
| U-7 | Tests help debug failures quickly                         | ❌ NO     | Failure messages indicate exact problem       |

**U-1 Example (Bug Detection Validation):**

```typescript
// Test: URL construction with limit parameter
it('constructs URL with limit', () => {
  const url = builder.getSystems({ limit: 10 });
  expect(
    parseAndValidateUrl(url, {
      query: { limit: '10' },
    })
  ).toBeDefined();
});

// Validation: Intentionally break the code
// Change: query: { limit: value }
// To:     query: { max: value }  // Wrong parameter name
// Result: Test MUST fail

// If test still passes after breaking code → test is useless
```

**U-2 Example:**

```typescript
// ❌ BAD - Generic message
expect(url).toBe('https://api.example.com/systems?limit=10');
// Failure: "expected 'https://api...' to equal 'https://api...'"

// ✅ GOOD - Specific message
expect(parsed.query.limit).toBe('10', 'Query parameter "limit" should be "10"');
// Failure: "Query parameter "limit" should be "10" but got "undefined""
```

**U-4 Example (Test Independence):**

```typescript
// ❌ BAD - Depends on previous test
describe('Systems', () => {
  let builder;

  it('creates builder', () => {
    builder = new CSAPIQueryBuilder(endpoint); // Sets shared state
  });

  it('builds URL', () => {
    const url = builder.getSystems(); // Depends on previous test
  });
});

// ✅ GOOD - Independent
describe('Systems', () => {
  it('builds URL', () => {
    const builder = new CSAPIQueryBuilder(endpoint); // Self-contained
    const url = builder.getSystems();
  });
});
```

### 2.3 Deep Test Validation

**Purpose:** Ensure comprehensive coverage including edge cases

| #   | Checklist Item                                           | Critical? | How to Validate                         |
| --- | -------------------------------------------------------- | --------- | --------------------------------------- |
| D-1 | Happy path thoroughly tested                             | ✅ YES    | All common scenarios have tests         |
| D-2 | Boundary values tested (0, 1, min, max)                  | ✅ YES    | Search for boundary test cases          |
| D-3 | Edge cases documented and tested                         | ✅ YES    | Edge cases listed and validated         |
| D-4 | Error conditions systematically tested                   | ✅ YES    | All error types from Section 18 tested  |
| D-5 | Meets coverage targets (85-95% statement, 80-95% branch) | ✅ YES    | Run coverage report - check thresholds  |
| D-6 | All code paths executed                                  | ❌ NO     | Coverage report shows all branches hit  |
| D-7 | Parameter combinations tested (for small sets)           | ❌ NO     | Common combinations have explicit tests |
| D-8 | Error messages validated                                 | ❌ NO     | Error tests check message content       |
| D-9 | Integration points tested                                | ❌ NO     | Cross-component scenarios validated     |

**D-2 Example (Boundary Values):**

```typescript
describe('pagination', () => {
  it('handles limit=0', () => {
    /* boundary */
  });
  it('handles limit=1', () => {
    /* boundary */
  });
  it('handles limit=10', () => {
    /* typical */
  });
  it('handles limit=1000', () => {
    /* max */
  });

  it('handles offset=0', () => {
    /* boundary */
  });
  it('handles offset > total', () => {
    /* edge case */
  });
});
```

**D-3 Example (Edge Cases Documented):**

```typescript
/**
 * Edge Cases Tested:
 * - Empty bbox (no spatial filter)
 * - Null bbox (explicit no filter)
 * - Invalid bbox (minLon > maxLon) - should throw
 * - World bbox (-180, -90, 180, 90)
 * - Single-point bbox (minLon === maxLon)
 * - Antimeridian-crossing bbox (minLon > maxLon, valid case)
 */
describe('spatial filtering', () => {
  it('handles empty bbox', () => {
    /* ... */
  });
  it('handles null bbox', () => {
    /* ... */
  });
  // ... etc
});
```

**D-4 Example (Systematic Error Testing):**

```typescript
// From Section 18: Error Taxonomy
describe('error conditions', () => {
  // Validation errors
  it('throws on invalid bbox (minLon > maxLon)', () => {
    /* ... */
  });
  it('throws on invalid datetime (start > end)', () => {
    /* ... */
  });

  // Conformance errors
  it('throws if CSAPI not supported', () => {
    /* ... */
  });
  it('throws if resource type unavailable', () => {
    /* ... */
  });

  // Parse errors
  it('throws on malformed GeoJSON', () => {
    /* ... */
  });
  it('throws on invalid SensorML', () => {
    /* ... */
  });
});
```

### 2.4 End-to-End Test Validation

**Purpose:** Ensure complete user workflows are tested

| #     | Checklist Item                                | Critical? | How to Validate                         |
| ----- | --------------------------------------------- | --------- | --------------------------------------- |
| E2E-1 | Tests complete user workflows (3+ operations) | ✅ YES    | Workflow tests span multiple components |
| E2E-2 | Uses real fixtures from spec examples         | ✅ YES    | Fixtures match OGC spec examples        |
| E2E-3 | Validates cross-component integration         | ✅ YES    | Tests navigate between resources        |
| E2E-4 | Tests resource navigation (via links)         | ❌ NO     | Workflow follows HATEOAS links          |
| E2E-5 | Validates round-trip scenarios                | ❌ NO     | Create → Read → Update → Delete tested  |
| E2E-6 | Uses realistic data volumes                   | ❌ NO     | Not minimal test data (10+ resources)   |

**E2E-1 Example (Complete Workflow):**

```typescript
it('completes system-to-observations workflow', async () => {
  // 1. Endpoint detection
  const endpoint = new OgcApiEndpoint(API_URL);

  // 2. List systems
  const systems = await endpoint.getFeatures('systems');
  const system = systems.features[0];

  // 3. Get system's datastreams
  const datastreams = await endpoint.getFeatures('datastreams', {
    system: system.id,
  });
  const datastream = datastreams.features[0];

  // 4. Query observations
  const observations = await endpoint.getFeatures('observations', {
    datastream: datastream.id,
    datetime: '2024-01-01T00:00:00Z/..',
  });

  // 5. Validate observation data
  expect(observations.features.length).toBeGreaterThan(0);
  expect(observations.features[0].properties.result).toBeDefined();
});
```

**E2E-4 Example (Navigation via Links):**

```typescript
it('navigates via HATEOAS links', async () => {
  // 1. Get system
  const system = await endpoint.getFeature('systems', 'sys-123');

  // 2. Find datastreams link
  const datastreamLink = system.links.find((l) => l.rel === 'datastreams');
  expect(datastreamLink).toBeDefined();

  // 3. Navigate to datastreams
  const datastreams = await endpoint.getFeaturesByLink(datastreamLink.href);

  // 4. Validate navigation worked
  expect(datastreams.features.length).toBeGreaterThan(0);
});
```

### 2.5 Documentation Validation

**Purpose:** Ensure tests are documented per Section 35 standards

| #     | Checklist Item                                                  | Critical? | How to Validate                  |
| ----- | --------------------------------------------------------------- | --------- | -------------------------------- |
| DOC-1 | Test utilities have complete JSDoc (@param, @returns, @example) | ✅ YES    | All helper functions documented  |
| DOC-2 | Spec-validating tests have @specification tags                  | ❌ NO     | Search for tests linking to spec |
| DOC-3 | Fixture-using tests have @fixture references                    | ❌ NO     | Fixture usage documented         |
| DOC-4 | Complex scenarios have @scenario tags                           | ❌ NO     | Non-obvious tests explained      |
| DOC-5 | Coverage gaps documented                                        | ✅ YES    | Known limitations listed         |

**DOC-1 Example:**

```typescript
/**
 * Parses and validates URL structure against expected values.
 *
 * @param {string} url - URL to parse and validate
 * @param {object} expected - Expected URL components
 * @param {string} [expected.protocol] - Expected protocol (e.g., 'https:')
 * @param {string} [expected.host] - Expected host (e.g., 'api.example.com')
 * @param {string} [expected.pathname] - Expected pathname (e.g., '/systems')
 * @param {object} [expected.query] - Expected query parameters
 * @returns {ParsedURL} Parsed URL components
 * @throws {Error} If URL doesn't match expected structure
 *
 * @example
 * const parsed = parseAndValidateUrl(url, {
 *   pathname: '/systems',
 *   query: { limit: '10' }
 * });
 */
function parseAndValidateUrl(url, expected) {
  /* ... */
}
```

**DOC-2 Example:**

```typescript
/**
 * Validates system response includes all required properties per spec.
 *
 * @specification OGC 23-001 §7.2.1, Table 4
 */
it('includes required system properties', () => {
  /* ... */
});
```

### 2.6 Quality Metrics Validation

**Purpose:** Ensure measurable quality standards are met

| #    | Checklist Item                                  | Critical? | How to Validate                                 |
| ---- | ----------------------------------------------- | --------- | ----------------------------------------------- |
| QM-1 | Line coverage meets component target (85-95%)   | ✅ YES    | Run coverage report - check statement %         |
| QM-2 | Branch coverage meets component target (80-95%) | ✅ YES    | Run coverage report - check branch %            |
| QM-3 | Edge case coverage: All identified cases tested | ✅ YES    | Edge case list vs test cases                    |
| QM-4 | No test flakiness detected                      | ❌ NO     | Run tests multiple times if flakiness suspected |
| QM-5 | Test independence verified                      | ❌ NO     | Run tests in random order                       |
| QM-6 | Performance: Tests run within time limits       | ❌ NO     | Check test timing in output                     |

**QM-1/QM-2 Example (Coverage Report):**

```
npm run test:coverage

Coverage Summary:
------------------
Statements   : 92.5% (548/592)   ✅ Target: 85-95%
Branches     : 88.3% (234/265)   ✅ Target: 80-95%
Functions    : 95.2% (80/84)     ✅ Target: 90-100%
Lines        : 92.1% (532/578)   ✅ Target: 85-95%
```

**QM-4 Example (Flakiness Check):**

```bash
# Re-run tests a few times if flakiness is suspected
npm test -- --testNamePattern="QueryBuilder"
npm test -- --testNamePattern="QueryBuilder"
npm test -- --testNamePattern="QueryBuilder"
# If any run fails non-deterministically, investigate the flaky test
```

**QM-5 Example (Independence Check):**

```bash
# Run tests in random order
npm test -- --randomize

# Run single test in isolation
npm test -- --testNamePattern="specific test name"
```

---

## 3. Review Process Workflow

> **⚠️ Simplified Review Process (H2 fix):** The original 3-stage enterprise review (Self-Review → Peer Review → Tech Lead Sign-Off) with 41-item checklist, invented roles, mandatory 100-run flakiness checks, and elaborate markdown templates has been replaced with a single-stage self-review checklist. This aligns with upstream `camptocamp/ogc-client` conventions: standard GitHub PR review, no formal quality gates, no distinct reviewer roles.

### 3.1 Single-Stage Self-Review

**When:** Before PR submission  
**Duration:** 5–10 minutes per test file  
**Responsibility:** Developer who wrote tests

**Self-Review Checklist (10 items):**

```markdown
## Test Quality Self-Review

**Test File:** `csapi-querybuilder.spec.ts`

### Meaningful & Useful

- [ ] Tests use real fixtures (not invented data)
- [ ] Tests assert behavior, not implementation details
- [ ] Tests catch bugs when code is intentionally broken
- [ ] Failure messages are clear and actionable
- [ ] Tests run fast (<200ms each)

### Coverage & Depth

- [ ] Happy path, edge cases, and error conditions covered
- [ ] Statement coverage >80%, branch coverage >80%
- [ ] No flaky tests detected
- [ ] Tests are independent (pass in any order)

### Ready

- [ ] All tests pass locally before PR submission
```

**After self-review:** Submit PR for standard GitHub review by maintainer.

### 3.2 Remediation

If a PR reviewer identifies quality issues:

1. Developer addresses feedback in the PR
2. Re-runs self-review checklist
3. Updates PR — standard GitHub PR workflow

No escalation tiers, no separate sign-off stage.

---

## 4. Component-Specific Quality Criteria

### 4.1 QueryBuilder Tests

**Specific Criteria:**

| Criteria                | Requirement                                           | Validation                    |
| ----------------------- | ----------------------------------------------------- | ----------------------------- |
| **URL Structure**       | All URLs validated with parseAndValidateUrl()         | No string matching or regex   |
| **Query Parameters**    | All parameters tested individually and in combination | Parameter matrix coverage     |
| **Encoding**            | Special characters, spaces, unicode tested            | Edge case tests               |
| **Optional Parameters** | Omission validated (no empty query strings)           | Null/undefined handling       |
| **Error Conditions**    | Invalid bbox, temporal, conformance errors tested     | All validation errors covered |

**Quality Indicators:**

- ✅ No `.toContain()` or regex matching for URLs
- ✅ All resource methods tested (list, get, create, update, delete, patch)
- ✅ All query parameters tested per resource type
- ✅ Edge cases: empty, null, boundary values
- ✅ Error messages validated for clarity

**Example Quality Test:**

```typescript
describe('getSystems with spatial filtering', () => {
  it('constructs URL with world bbox', () => {
    const url = builder.getSystems({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
    });

    const parsed = parseAndValidateUrl(url, {
      pathname: '/systems',
      query: { bbox: '-180,-90,180,90' },
    });

    // Validate bbox encoding format
    expect(parsed.query.bbox).toMatch(
      /^-?\d+(\.\d+)?,-?\d+(\.\d+)?,-?\d+(\.\d+)?,-?\d+(\.\d+)?$/
    );
  });

  it('throws on invalid bbox (minLon > maxLon)', () => {
    expect(() =>
      builder.getSystems({
        bbox: { minLon: 180, minLat: -90, maxLon: -180, maxLat: 90 },
      })
    ).toThrow('Invalid bbox: minLon must be <= maxLon');
  });
});
```

### 4.2 Parser Tests (SensorML, SWE Common)

**Specific Criteria:**

| Criteria              | Requirement                                                     | Validation                |
| --------------------- | --------------------------------------------------------------- | ------------------------- |
| **Structure Parsing** | All structure types tested (PhysicalSystem, Component, Process) | Complete type coverage    |
| **Nesting**           | Tested up to 5 levels deep                                      | Deep hierarchy fixtures   |
| **Encoding**          | All 3 encodings tested (JSON, Text, Binary)                     | Format-specific tests     |
| **Error Handling**    | Malformed XML/JSON, missing fields, type mismatches             | Comprehensive error tests |
| **Schema Validation** | Namespace variations, optional elements                         | Schema compliance         |

**Quality Indicators:**

- ✅ All structure types tested (4 SensorML types, 8 SWE types)
- ✅ Nesting levels: 1, 2, 3, 5 levels tested
- ✅ Binary encoding: Endianness (big, little), data types tested
- ✅ Error conditions: ~15-20 error scenarios per parser
- ✅ Real fixtures from OpenSensorHub examples

**Example Quality Test:**

```typescript
describe('PhysicalSystem parsing', () => {
  it('parses simple physical system', () => {
    const xml = loadFixture('fixtures/sensorml/physical-system-simple.xml');
    const parsed = parseSensorML(xml);

    // Validate all required properties
    expect(parsed.id).toBe('sensor-sf-001');
    expect(parsed.type).toBe('PhysicalSystem');
    expect(parsed.identification).toHaveLength(1);
    expect(parsed.classification).toHaveLength(1);
    expect(parsed.capabilities).toHaveLength(1);
    expect(parsed.components).toHaveLength(2);

    // Validate component structure
    const component = parsed.components[0];
    expect(component.id).toBe('thermometer-001');
    expect(component.type).toBe('PhysicalComponent');
  });

  it('parses 5-level nested hierarchy', () => {
    const xml = loadFixture('fixtures/sensorml/physical-system-5-levels.xml');
    const parsed = parseSensorML(xml);

    // Validate depth
    let depth = 0;
    let current = parsed;
    while (current.components && current.components.length > 0) {
      depth++;
      current = current.components[0];
    }
    expect(depth).toBe(5);
  });

  it('throws on malformed XML', () => {
    const xml = '<PhysicalSystem><unclosed>';
    expect(() => parseSensorML(xml)).toThrow('Malformed XML');
  });
});
```

### 4.3 Integration Tests

**Specific Criteria:**

| Criteria                  | Requirement                  | Validation                        |
| ------------------------- | ---------------------------- | --------------------------------- |
| **Workflow Completeness** | 3+ operations per workflow   | Multi-step scenarios              |
| **Resource Navigation**   | HATEOAS link following       | Link-based navigation             |
| **Cross-Component**       | 2+ components integrated     | Endpoint + QueryBuilder + Parser  |
| **Real Fixtures**         | Spec examples used           | OGC 23-001/23-002/23-003 fixtures |
| **Data Validation**       | Complete response validation | Not just existence checks         |

**Quality Indicators:**

- ✅ Workflows span 3-6 operations
- ✅ Resource navigation via links
- ✅ Integration of Endpoint + QueryBuilder + Parsers
- ✅ Real fixtures (300+ lines each)
- ✅ Complete validation (not shallow checks)

**Example Quality Test:**

```typescript
describe('System-to-Observation workflow', () => {
  it('completes end-to-end workflow with real fixtures', async () => {
    // Setup: Mock API with real fixtures
    setupMockAPI({
      '/': loadFixture('fixtures/csapi/root.json'),
      '/systems': loadFixture('fixtures/csapi/systems/collection.json'),
      '/systems/weather-station-001': loadFixture(
        'fixtures/csapi/systems/system-weather-station.json'
      ),
      '/datastreams?system=weather-station-001': loadFixture(
        'fixtures/csapi/datastreams/collection-by-system.json'
      ),
      '/observations?datastream=ds-temp-001': loadFixture(
        'fixtures/csapi/observations/collection-temp.json'
      ),
    });

    // 1. Detect CSAPI endpoint
    const endpoint = new OgcApiEndpoint('https://api.example.com');
    expect(endpoint).toSupportCSAPI();

    // 2. Query systems
    const systems = await endpoint.getFeatures('systems');
    expect(systems.features).toHaveLength(1);
    const system = systems.features[0];
    expect(system.id).toBe('weather-station-001');

    // 3. Navigate to datastreams
    const datastreams = await endpoint.getFeatures('datastreams', {
      system: system.id,
    });
    expect(datastreams.features).toHaveLength(3);
    const datastream = datastreams.features[0];
    expect(datastream.id).toBe('ds-temp-001');

    // 4. Query observations
    const observations = await endpoint.getFeatures('observations', {
      datastream: datastream.id,
      datetime: '2024-01-01T00:00:00Z/..',
    });
    expect(observations.features.length).toBeGreaterThan(0);

    // 5. Validate observation structure
    const obs = observations.features[0];
    expect(obs.properties.phenomenonTime).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(obs.properties.result).toEqual(
      expect.objectContaining({
        measure: expect.any(Number),
        uom: expect.any(String),
      })
    );
  });
});
```

### 4.4 Utility/Helper Tests

**Specific Criteria:**

| Criteria              | Requirement                                 | Validation                     |
| --------------------- | ------------------------------------------- | ------------------------------ |
| **Function Coverage** | 100% of exported functions                  | All utilities tested           |
| **Edge Cases**        | null, undefined, empty, boundary values     | Comprehensive edge case tests  |
| **Error Conditions**  | Invalid input handling                      | Error tests for all validators |
| **Documentation**     | Complete JSDoc (@param, @returns, @example) | All functions documented       |
| **Type Safety**       | TypeScript type validation                  | Type tests or runtime checks   |

**Quality Indicators:**

- ✅ All utilities tested (validators, type guards, helpers)
- ✅ Edge cases: null, undefined, empty string, empty array, empty object
- ✅ Boundary values: 0, 1, -1, max, min
- ✅ Error messages validated
- ✅ Complete JSDoc with examples

**Example Quality Test:**

```typescript
describe('parseAndValidateUrl', () => {
  it('parses valid URL', () => {
    const parsed = parseAndValidateUrl(
      'https://api.example.com/systems?limit=10',
      {
        pathname: '/systems',
        query: { limit: '10' },
      }
    );
    expect(parsed.protocol).toBe('https:');
    expect(parsed.host).toBe('api.example.com');
  });

  it('handles URL without query parameters', () => {
    const parsed = parseAndValidateUrl('https://api.example.com/systems', {
      pathname: '/systems',
      query: {},
    });
    expect(Object.keys(parsed.query)).toHaveLength(0);
  });

  it('throws on protocol mismatch', () => {
    expect(() =>
      parseAndValidateUrl('http://api.example.com/systems', {
        protocol: 'https:',
      })
    ).toThrow('Expected protocol "https:" but got "http:"');
  });

  it('throws on invalid URL', () => {
    expect(() => parseAndValidateUrl('not a url', {})).toThrow('Invalid URL');
  });

  // Edge cases
  it('handles empty string URL', () => {
    expect(() => parseAndValidateUrl('', {})).toThrow('URL cannot be empty');
  });

  it('handles null URL', () => {
    expect(() => parseAndValidateUrl(null as any, {})).toThrow(
      'URL must be a string'
    );
  });
});
```

---

## 5. Quality Metrics Dashboard

### 5.1 Coverage Metrics

**Component-Specific Targets (from Section 17):**

| Component              | Statement | Branch | Function | Edge Cases | Error Tests |
| ---------------------- | --------- | ------ | -------- | ---------- | ----------- |
| **QueryBuilder**       | 85-90%    | 80-85% | 95-100%  | 100%       | 80-90%      |
| **Parsers (SensorML)** | 90-95%    | 85-95% | 100%     | 90-100%    | 100%        |
| **Parsers (SWE)**      | 90-95%    | 85-95% | 100%     | 90-100%    | 100%        |
| **Endpoint**           | 90-95%    | 85-90% | 100%     | 80-90%     | 90-100%     |
| **Utilities**          | 85-95%    | 80-90% | 90-100%  | 100%       | 100%        |
| **Worker**             | 85-90%    | 80-85% | 95-100%  | 70-80%     | 80-90%      |
| **Integration**        | N/A       | N/A    | N/A      | N/A        | N/A         |

**How to Validate:**

```bash
# Run coverage report
npm run test:coverage

# Check component-specific coverage
npm run test:coverage -- --collectCoverageFrom="src/ogc-api/csapi/querybuilder.ts"

# View detailed HTML report
open coverage/lcov-report/index.html
```

### 5.2 Reliability Metrics

**Flakiness Detection:**

| Metric                | Target                    | How to Measure             |
| --------------------- | ------------------------- | -------------------------- |
| **Zero flakiness**    | 100 runs, 0 failures      | Run test suite 100 times   |
| **Test independence** | 100% pass in random order | `npm test -- --randomize`  |
| **Isolation**         | 100% pass when run alone  | Run each test individually |

**How to Validate:**

```bash
# Flakiness check (100 runs)
for i in {1..100}; do
  npm test -- --testPathPattern="querybuilder"
  if [ $? -ne 0 ]; then
    echo "FLAKY TEST on iteration $i"
    exit 1
  fi
done

# Random order check
npm test -- --randomize --runInBand

# Isolation check
npm test -- --testNamePattern="specific test" --runInBand
```

### 5.3 Maintainability Metrics

**Documentation Completeness:**

| Metric                    | Target       | How to Measure                     |
| ------------------------- | ------------ | ---------------------------------- |
| **Utilities documented**  | 100%         | All functions have JSDoc           |
| **Spec links**            | 60% of tests | @specification tag usage           |
| **Fixture references**    | 40% of tests | @fixture tag usage                 |
| **Edge cases documented** | 100%         | Edge case lists in describe blocks |

**How to Validate:**

```bash
# Check JSDoc coverage
npm run docs:coverage  # (if configured)

# Search for @specification tags
grep -r "@specification" tests/ | wc -l

# Search for @fixture tags
grep -r "@fixture" tests/ | wc -l

# Verify edge case documentation
grep -r "Edge Cases" tests/ | wc -l
```

### 5.4 Performance Metrics

**Execution Time Targets:**

| Test Type             | Target          | How to Measure     |
| --------------------- | --------------- | ------------------ |
| **Unit tests**        | < 100ms average | Jest timing output |
| **Integration tests** | < 1s average    | Jest timing output |
| **Full suite**        | < 30s total     | Total test time    |

**How to Validate:**

```bash
# Run tests with timing
npm test -- --verbose

# Example output:
# ✓ QueryBuilder › getSystems (45ms)
# ✓ QueryBuilder › getSystem (32ms)
# ✓ SensorML › parsePhysicalSystem (123ms)
# ✓ Integration › system-to-observations (856ms)

# Full suite timing:
# Test Suites: 15 passed, 15 total
# Tests:       324 passed, 324 total
# Time:        28.456s  ✅ < 30s target
```

### 5.5 Bug Detection Validation

**Intentional Breakage Tests:**

| Component        | Bug Types                                      | Tests Should Fail      |
| ---------------- | ---------------------------------------------- | ---------------------- |
| **QueryBuilder** | Wrong param name, missing encoding, wrong path | 100% of affected tests |
| **Parsers**      | Wrong field extraction, missing validation     | 100% of affected tests |
| **Utilities**    | Wrong validation logic, incorrect encoding     | 100% of affected tests |

**How to Validate:**

```bash
# Example: Break QueryBuilder
# Change: query: { limit: value }
# To:     query: { max: value }

npm test -- --testPathPattern="querybuilder"

# Expected: All limit-related tests should FAIL
# If tests still pass → tests are not meaningful
```

### 5.6 Metrics Dashboard Example

```
================== CSAPI Test Quality Dashboard ==================

Coverage Metrics:
-----------------
Component              Statement  Branch  Function  Edge   Error
QueryBuilder           88.2%      84.5%   97.3%     100%   85%
SensorML Parser        92.8%      89.1%   100%      95%    100%
SWE Common Parser      94.3%      91.7%   100%      100%   100%
Endpoint               91.5%      87.2%   100%      88%    95%
Utilities              89.7%      85.3%   95.5%     100%   100%
Worker Extensions      87.4%      82.8%   98.2%     75%    88%
------------------------------------------------------------------
OVERALL                91.2%      87.6%   98.5%     93%    94%
TARGET                 85-95%     80-95%  90-100%   90%+   90%+
STATUS                 ✅         ✅      ✅        ✅     ✅

Reliability Metrics:
-------------------
Flakiness (100 runs):              0 failures  ✅
Random order:                      324/324 pass ✅
Test isolation:                    324/324 pass ✅

Maintainability Metrics:
-----------------------
Utilities documented:              48/48 (100%)  ✅
@specification tags:               195/324 (60%) ✅
@fixture tags:                     132/324 (41%) ✅
Edge cases documented:             28/28 (100%)  ✅

Performance Metrics:
-------------------
Unit test avg:                     52ms    ✅ < 100ms
Integration test avg:              723ms   ✅ < 1s
Full suite time:                   27.8s   ✅ < 30s

Bug Detection:
-------------
Intentional breakage validation:   PASSED  ✅
- QueryBuilder: 5/5 bug types detected
- SensorML Parser: 4/4 bug types detected
- SWE Parser: 6/6 bug types detected
- Utilities: 3/3 bug types detected

OVERALL QUALITY:                   ✅ EXCELLENT
ALL METRICS WITHIN TARGET RANGES

Sign-off recommendation:           ✅ APPROVED
==================================================================
```

---

## 6. Checklist Usage Guidelines

### 6.1 When to Use Checklist

**Use checklist for:**

- ✅ Every new test file before PR submission
- ✅ Major test refactoring (>50 lines changed)
- ✅ Adding new component tests
- ✅ PR review process
- ✅ Final sign-off before merge

**Don't need full checklist for:**

- ❌ Fixing typos in tests
- ❌ Updating fixture paths
- ❌ Renaming test descriptions
- ❌ Small test adjustments (<10 lines)

### 6.2 Progressive Checklist Application

**During Development:**

- Run meaningful/useful checks continuously
- Validate as you write tests
- Don't wait until PR submission

**Before PR Submission:**

- Complete full self-review checklist
- Document any N/A items
- Fix all critical issues

**During PR Review:**

- Peer reviewer validates deep/E2E items
- Spot-checks meaningful/useful items
- Validates coverage metrics

**Before Merge:**

- Tech lead validates all metrics
- Final sign-off on overall quality
- Approves merge

### 6.3 Checklist Customization

**Component-Specific Adjustments:**

**QueryBuilder Tests:**

- Add: URL structure validation requirement
- Add: Query parameter encoding checks
- Skip: E2E tests (unit-level only)

**Parser Tests:**

- Add: Schema validation requirements
- Add: Nesting depth requirements
- Add: Encoding format requirements
- Skip: Integration tests (parser-focused)

**Integration Tests:**

- Add: Workflow completeness requirements
- Add: Resource navigation requirements
- Skip: Unit-level metrics (statement coverage N/A)

**Utility Tests:**

- Add: 100% function coverage requirement
- Add: Complete JSDoc requirement
- Skip: E2E tests (utility-focused)

### 6.4 Checklist Exceptions

**Valid Exceptions:**

**E2E-4 (Resource Navigation):**

- N/A for unit-level tests (QueryBuilder, Utilities)
- Required for integration tests only

**M-5 (Real Server Fixtures):**

- N/A for URL building tests (no data retrieval)
- Required for parser tests and integration tests

**D-9 (Integration Points):**

- N/A for isolated unit tests
- Required for integration tests and endpoint tests

**How to Document Exceptions:**

```markdown
## Checklist Exceptions

**Component:** CSAPIQueryBuilder (unit tests)

**E2E-4: Resource Navigation**

- Status: N/A
- Reason: Unit-level tests don't test navigation
- Alternative: Integration tests cover navigation

**M-5: Real Server Fixtures**

- Status: N/A
- Reason: URL building doesn't retrieve data
- Alternative: Integration tests use real fixtures
```

---

## 7. Common Quality Issues and Solutions

> **Cross-reference:** For the foundational definition of meaningful vs trivial tests, including the complete taxonomy of 7 trivial indicators and 7 meaningful characteristics, see [Section 06: Meaningful vs Trivial Definition](06-meaningful-vs-trivial-definition.md). The examples below show how to apply those principles as quick-fix patterns during code review.

### 7.1 Trivial Tests Anti-Patterns

**Issue 1: toBeTruthy() Without Further Validation**

```typescript
// ❌ PROBLEM
it('returns URL', () => {
  const url = builder.getSystems();
  expect(url).toBeTruthy(); // Always passes if method exists
});

// ✅ SOLUTION
it('returns URL', () => {
  const url = builder.getSystems();
  const parsed = parseAndValidateUrl(url, {
    pathname: '/systems',
    query: {},
  });
  // Validates structure, not just existence
});
```

**Issue 2: String Containment Checks**

```typescript
// ❌ PROBLEM
it('includes limit parameter', () => {
  const url = builder.getSystems({ limit: 10 });
  expect(url).toContain('limit=10'); // Brittle, doesn't validate structure
});

// ✅ SOLUTION
it('includes limit parameter', () => {
  const url = builder.getSystems({ limit: 10 });
  const parsed = parseAndValidateUrl(url, {
    query: { limit: '10' },
  });
  // Validates as structured data
});
```

**Issue 3: Checking Method Existence**

```typescript
// ❌ PROBLEM
it('has getSystems method', () => {
  expect(typeof builder.getSystems).toBe('function');
  // Doesn't test behavior
});

// ✅ SOLUTION
// Remove this test entirely - TypeScript ensures method exists
// Focus on testing behavior instead
it('constructs correct systems URL', () => {
  const url = builder.getSystems();
  // Test actual behavior
});
```

### 7.2 Incomplete Coverage Issues

**Issue 1: Missing Edge Cases**

```typescript
// ❌ PROBLEM - Only happy path
describe('pagination', () => {
  it('handles limit parameter', () => {
    const url = builder.getSystems({ limit: 10 });
    // ...
  });
});

// ✅ SOLUTION - Complete edge case coverage
describe('pagination', () => {
  it('handles no pagination parameters', () => {
    /* empty */
  });
  it('handles limit only', () => {
    /* limit */
  });
  it('handles limit and offset', () => {
    /* both */
  });
  it('handles zero limit', () => {
    /* boundary */
  });
  it('handles large limit (1000)', () => {
    /* boundary */
  });
  it('handles null limit', () => {
    /* edge case */
  });
  it('throws on negative limit', () => {
    /* error */
  });
});
```

**Issue 2: Missing Error Tests**

```typescript
// ❌ PROBLEM - No error testing
describe('bbox filtering', () => {
  it('constructs URL with bbox', () => {
    const url = builder.getSystems({ bbox: {...} });
    // Only tests happy path
  });
});

// ✅ SOLUTION - Comprehensive error testing
describe('bbox filtering', () => {
  it('constructs URL with valid bbox', () => { /* happy path */ });

  // Error conditions
  it('throws when minLon > maxLon', () => { /* error */ });
  it('throws when minLat > maxLat', () => { /* error */ });
  it('throws when coordinates out of range', () => { /* error */ });
  it('throws with invalid bbox format', () => { /* error */ });
});
```

### 7.3 Flaky Test Issues

**Issue 1: Test Order Dependencies**

```typescript
// ❌ PROBLEM - Tests depend on execution order
describe('endpoint', () => {
  let endpoint;

  it('creates endpoint', async () => {
    endpoint = new OgcApiEndpoint(API_URL);
  });

  it('queries systems', async () => {
    const systems = await endpoint.getFeatures('systems');
    // Depends on previous test setting 'endpoint'
  });
});

// ✅ SOLUTION - Independent tests
describe('endpoint', () => {
  it('creates endpoint and queries systems', async () => {
    const endpoint = new OgcApiEndpoint(API_URL);
    const systems = await endpoint.getFeatures('systems');
    // Self-contained
  });

  // Or use beforeEach
  let endpoint;
  beforeEach(async () => {
    endpoint = new OgcApiEndpoint(API_URL);
  });

  it('queries systems', async () => {
    const systems = await endpoint.getFeatures('systems');
    // Independent (beforeEach runs every time)
  });
});
```

**Issue 2: Shared Mutable State**

```typescript
// ❌ PROBLEM - Shared state between tests
describe('builder', () => {
  const options = { limit: 10 }; // Shared object

  it('test 1', () => {
    options.offset = 20; // Mutates shared state
    const url = builder.getSystems(options);
  });

  it('test 2', () => {
    const url = builder.getSystems(options);
    // Unexpected: options now has offset from test 1
  });
});

// ✅ SOLUTION - Isolated state
describe('builder', () => {
  it('test 1', () => {
    const options = { limit: 10, offset: 20 }; // Local state
    const url = builder.getSystems(options);
  });

  it('test 2', () => {
    const options = { limit: 10 }; // Separate local state
    const url = builder.getSystems(options);
  });
});
```

### 7.4 Poor Documentation Issues

**Issue 1: Missing JSDoc on Utilities**

```typescript
// ❌ PROBLEM - No documentation
function parseAndValidateUrl(url, expected) {
  // ...
}

// ✅ SOLUTION - Complete JSDoc
/**
 * Parses and validates URL structure against expected values.
 *
 * @param {string} url - URL to parse and validate
 * @param {object} expected - Expected URL components
 * @returns {ParsedURL} Parsed URL components
 * @throws {Error} If URL doesn't match expected structure
 *
 * @example
 * const parsed = parseAndValidateUrl(url, {
 *   pathname: '/systems',
 *   query: { limit: '10' }
 * });
 */
function parseAndValidateUrl(url, expected) {
  // ...
}
```

**Issue 2: Testing Spec Compliance Instead of Client Behavior**

```typescript
// ❌ PROBLEM - Tests spec conformance, not client behavior
it('validates system response conforms to OGC 23-001 §7.2.1', () => {
  // Tests whether the response is spec-compliant (server concern)
});

// ✅ SOLUTION - Test client behavior, use spec as context
it('parses system properties from response', () => {
  // Spec tells us what properties to expect; we test that our parser extracts them
  const result = parseSystem(fixture);
  expect(result.id).toBe('weather-station-001');
  expect(result.name).toBe('Weather Station Alpha');
});
```

### 7.5 Performance Issues

**Issue 1: Slow Tests**

```typescript
// ❌ PROBLEM - Unnecessary async delays
it('constructs URL', async () => {
  await new Promise((resolve) => setTimeout(resolve, 100)); // Why?
  const url = builder.getSystems();
  expect(url).toBeDefined();
});

// ✅ SOLUTION - Remove unnecessary delays
it('constructs URL', () => {
  const url = builder.getSystems(); // Synchronous, fast
  expect(url).toBeDefined();
});
```

**Issue 2: Excessive Fixture Loading**

```typescript
// ❌ PROBLEM - Load fixtures in every test
describe('parsing', () => {
  it('test 1', () => {
    const fixture = loadFixture('large-file.json'); // 1MB file
    // ...
  });

  it('test 2', () => {
    const fixture = loadFixture('large-file.json'); // Load again
    // ...
  });
});

// ✅ SOLUTION - Load fixtures once
describe('parsing', () => {
  let fixture;

  beforeAll(() => {
    fixture = loadFixture('large-file.json'); // Load once
  });

  it('test 1', () => {
    // Use cached fixture
  });

  it('test 2', () => {
    // Use cached fixture
  });
});
```

---

## 8. Implementation Estimates

### 8.1 Time to Complete Checklist

**Per Test File:**

| Activity           | Duration       | Notes                        |
| ------------------ | -------------- | ---------------------------- |
| **Self-Review**    | 15-30 min      | Initial checklist completion |
| **Fixes**          | 10-60 min      | Depends on issues found      |
| **Peer Review**    | 10-20 min      | Reviewer validation          |
| **Final Sign-Off** | 5-10 min       | Tech lead approval           |
| **TOTAL**          | **40-120 min** | **Per test file**            |

**Full Test Suite (80 files):**

| Activity            | Duration         | Notes                |
| ------------------- | ---------------- | -------------------- |
| **Self-Reviews**    | 20-40 hours      | 80 files × 15-30 min |
| **Fixes**           | 13-80 hours      | 80 files × 10-60 min |
| **Peer Reviews**    | 13-27 hours      | 80 files × 10-20 min |
| **Final Sign-Offs** | 7-13 hours       | 80 files × 5-10 min  |
| **TOTAL**           | **53-160 hours** | **Entire project**   |

**Expected Range:**

- **Optimistic:** ~53 hours (minimal fixes needed, efficient reviews)
- **Realistic:** ~80-100 hours (some fixes, typical review cycles)
- **Pessimistic:** ~160 hours (many fixes, multiple review rounds)

### 8.2 Effort by Component Type

| Component Type   | Files  | Self-Review   | Fixes         | Peer Review   | Sign-Off       | Total            |
| ---------------- | ------ | ------------- | ------------- | ------------- | -------------- | ---------------- |
| **QueryBuilder** | 10     | 3-5 hrs       | 2-10 hrs      | 2-3 hrs       | 1-2 hrs        | **8-20 hrs**     |
| **Parsers**      | 15     | 6-8 hrs       | 3-15 hrs      | 3-5 hrs       | 1-3 hrs        | **13-31 hrs**    |
| **Integration**  | 20     | 7-10 hrs      | 3-20 hrs      | 3-7 hrs       | 2-3 hrs        | **15-40 hrs**    |
| **Utilities**    | 15     | 4-8 hrs       | 2-15 hrs      | 3-5 hrs       | 1-3 hrs        | **10-31 hrs**    |
| **Worker**       | 5      | 2-3 hrs       | 1-5 hrs       | 1-2 hrs       | 0.5-1 hr       | **4.5-11 hrs**   |
| **Other**        | 15     | 3-6 hrs       | 2-15 hrs      | 2-5 hrs       | 1-2 hrs        | **8-28 hrs**     |
| **TOTAL**        | **80** | **25-40 hrs** | **13-80 hrs** | **14-27 hrs** | **6.5-14 hrs** | **58.5-161 hrs** |

### 8.3 Return on Investment

**Time Investment:**

- Self-review: ~25-40 hours
- Peer review: ~14-27 hours
- Final sign-off: ~7-14 hours
- **Total:** ~46-81 hours

**Value Delivered:**

- ✅ Prevents "too trivial" feedback (avoided previous iteration rejection)
- ✅ Catches bugs before PR submission (saves review cycles)
- ✅ Ensures spec compliance (traceability validated)
- ✅ Maintains test quality over time (checklist as living standard)
- ✅ Facilitates faster PR reviews (reviewer confidence)
- ✅ Reduces maintenance burden (meaningful tests easier to maintain)

**Cost-Benefit Analysis:**

| Scenario          | Without Checklist             | With Checklist              | Savings                       |
| ----------------- | ----------------------------- | --------------------------- | ----------------------------- |
| **PR Rejections** | 2-3 major revisions           | 0-1 minor revisions         | ~80-120 hours saved           |
| **Bug Detection** | Bugs found in production      | Bugs found in tests         | ~20-40 hours saved            |
| **Review Cycles** | 3-5 review rounds             | 1-2 review rounds           | ~30-50 hours saved            |
| **Maintenance**   | Brittle tests, frequent fixes | Robust tests, minimal fixes | ~50-100 hours saved over year |
| **TOTAL SAVINGS** | N/A                           | **~180-310 hours**          | **ROI: 3.8x - 5.4x**          |

**Recommendation:** **PROCEED** - High ROI justifies time investment

---

## 9. Examples of Checklist Application

### 9.1 QueryBuilder Test Review

**File:** `csapi-querybuilder.spec.ts`  
**Lines:** 1,200  
**Tests:** 85

**Self-Review Checklist:**

```markdown
### Meaningful Tests (8 items)

- [x] M-1: Uses real spec examples
  - Validation: Reviewed 10 random tests, all use spec-compliant data
- [x] M-2: Complete structure validation
  - Validation: All 85 tests use parseAndValidateUrl(), no toBeTruthy() only
- [x] M-3: Realistic scenarios
  - Validation: Test names match real-world usage (e.g., "query systems with bbox and datetime")
- [x] M-4: Behavior not implementation
  - Validation: No tests of private methods, all test public API
- [ ] M-5: Real server fixtures
  - Status: N/A - URL building doesn't retrieve data
- [x] M-6: Client behavior validation
  - Validation: 85/85 tests assert on client outputs (URLs, parsed params, error messages)
- [ ] M-7: Integration points
  - Status: N/A - Unit-level tests
- [x] M-8: Clear error messages
  - Validation: All 12 error tests validate message content

### Useful Tests (7 items)

- [x] U-1: Bug detection validated
  - Validation: Broke code (changed 'limit' to 'max'), 8 tests failed ✅
- [x] U-2: Clear failure messages
  - Validation: Error assertions include descriptive messages
- [x] U-3: Fast execution
  - Validation: Average test time 42ms ✅ < 100ms
- [x] U-4: Test independence
  - Validation: Ran tests in random order, all passed ✅
- [x] U-5: Public API only
  - Validation: No tests access private methods/properties
- [x] U-6: Survives refactoring
  - Validation: Refactored internal URL building, tests still passed ✅
- [x] U-7: Debug-friendly
  - Validation: Failure messages clearly indicate problem

### Documentation (5 items)

- [x] DOC-1: Utilities documented
  - Validation: parseAndValidateUrl has complete JSDoc
- [x] DOC-2: @specification tags
  - Validation: 52/85 tests (61%) ✅ Target 60%
- [x] DOC-3: @fixture references
  - Validation: 0 tests (N/A - no fixtures used in URL building)
- [ ] DOC-4: @scenario tags
  - Status: N/A - Tests straightforward, not complex scenarios
- [x] DOC-5: Coverage gaps documented
  - Validation: README lists known gaps (antimeridian bbox, 1000+ param performance)

### Quality Metrics

- Statement coverage: 88.2% ✅ (target 85-90%)
- Branch coverage: 84.5% ✅ (target 80-85%)
- Function coverage: 97.3% ✅ (target 95-100%)
- Edge cases: 15/15 tested ✅
- Error tests: 12/14 error types ✅ (2 deferred to integration)

**Issues Found:** NONE

**Ready for Peer Review:** ✅ YES
```

**Peer Review Validation:**

```markdown
### Deep Test Validation (9 items)

- [x] D-1: Happy path thoroughly tested
  - Spot-checked: getSystems, getSystem, getDataStreams all have happy path
- [x] D-2: Boundary values tested
  - Found: limit=0, limit=1, limit=1000 all tested
- [x] D-3: Edge cases documented
  - Found: 15 edge cases listed in describe block comments
- [x] D-4: Error conditions systematically tested
  - Found: 12/14 error types tested (2 deferred appropriately)
- [x] D-5: Coverage targets met
  - Validated: 88.2%/84.5%/97.3% all within targets
- [x] D-6: All code paths executed
  - Coverage report: All branches hit
- [x] D-7: Parameter combinations tested
  - Found: bbox, datetime, limit, offset tested individually and in key combinations
- [x] D-8: Error messages validated
  - Spot-checked: 5 error tests all validate message content
- [ ] D-9: Integration points tested
  - Status: N/A - Unit tests

**Issues Found:** NONE

**Recommendation:** ✅ APPROVE
```

**Final Sign-Off:**

```markdown
### Quality Metrics (6 items)

- [x] QM-1: Statement coverage 88.2% (target 85-90%) ✅
- [x] QM-2: Branch coverage 84.5% (target 80-85%) ✅
- [x] QM-3: Edge cases 15/15 (100%) ✅
- [x] QM-4: No flakiness (ran 100 times, 0 failures) ✅
- [x] QM-5: Test independence (random order passed) ✅
- [x] QM-6: Performance (avg 42ms < 100ms) ✅

**Overall Quality:** ✅ EXCELLENT

**Decision:** ✅ APPROVED FOR MERGE
```

### 9.2 SensorML Parser Test Review

**File:** `sensorml-parser.spec.ts`  
**Lines:** 800  
**Tests:** 46

**Self-Review Checklist:**

```markdown
### Meaningful Tests (8 items)

- [x] M-1: Uses real spec examples
  - Validation: All fixtures from OpenSensorHub examples
- [x] M-2: Complete structure validation
  - Validation: No toBeTruthy() only - all tests validate complete structures
- [x] M-3: Realistic scenarios
  - Validation: Tests match real sensor configurations
- [x] M-4: Behavior not implementation
  - Validation: Tests public parsing API, not internal XML traversal
- [x] M-5: Real server fixtures
  - Validation: 46/46 tests use OpenSensorHub fixtures
- [x] M-6: Client behavior validation
  - Validation: 46/46 tests assert on parser outputs (parsed objects, property values)
- [ ] M-7: Integration points
  - Status: N/A - Parser-focused unit tests
- [x] M-8: Clear error messages
  - Validation: All 10 error tests validate message content

### Useful Tests (7 items)

- [x] U-1: Bug detection validated
  - Validation: Broke field extraction (id → identification), 6 tests failed ✅
- [x] U-2: Clear failure messages
  - Validation: Error assertions specify expected vs actual
- [x] U-3: Fast execution
  - Validation: Average test time 87ms ✅ < 100ms (parser tests acceptable)
- [x] U-4: Test independence
  - Validation: Ran in random order, all passed ✅
- [x] U-5: Public API only
  - Validation: No tests of internal parser state
- [x] U-6: Survives refactoring
  - Validation: Refactored XML parsing library, tests still passed ✅
- [x] U-7: Debug-friendly
  - Validation: Failures show XML snippet + expected structure

### Documentation (5 items)

- [x] DOC-1: Utilities documented
  - Validation: parseSensorML, loadFixture have complete JSDoc
- [x] DOC-2: @specification tags
  - Validation: 28/46 tests (61%) ✅ Target 60%
- [x] DOC-3: @fixture references
  - Validation: 46/46 tests (100%) - all reference fixtures
- [x] DOC-4: @scenario tags
  - Validation: 3 complex scenarios documented (deep nesting, circular refs, missing refs)
- [x] DOC-5: Coverage gaps documented
  - Validation: README lists gaps (AggregateProcess edge cases, 6+ level nesting)

### Quality Metrics

- Statement coverage: 92.8% ✅ (target 90-95%)
- Branch coverage: 89.1% ✅ (target 85-95%)
- Function coverage: 100% ✅ (target 100%)
- Edge cases: 12/12 tested ✅
- Error tests: 10/10 error types ✅

**Issues Found:** NONE

**Ready for Peer Review:** ✅ YES
```

**Peer Review Validation:**

```markdown
### Deep Test Validation (9 items)

- [x] D-1: Happy path thoroughly tested
  - All 4 structure types (PhysicalSystem, Component, SimpleProcess, AggregateProcess) tested
- [x] D-2: Boundary values tested
  - Found: 0 components, 1 component, 10 components, deeply nested (5 levels)
- [x] D-3: Edge cases documented
  - Found: 12 edge cases listed and tested (circular refs, missing refs, deep nesting, etc.)
- [x] D-4: Error conditions systematically tested
  - Found: All 10 parser error types tested
- [x] D-5: Coverage targets met
  - Validated: 92.8%/89.1%/100% all within targets
- [x] D-6: All code paths executed
  - Coverage report: All branches hit
- [x] D-7: Parameter combinations tested
  - Found: Tested various XML namespace combinations, optional elements
- [x] D-8: Error messages validated
  - All 10 error tests validate message content
- [ ] D-9: Integration points tested
  - Status: N/A - Parser-focused

**Issues Found:** NONE

**Recommendation:** ✅ APPROVE
```

### 9.3 Integration Test Review

**File:** `system-to-observations.integration.spec.ts`  
**Lines:** 350  
**Tests:** 8

**Self-Review Checklist:**

```markdown
### Meaningful Tests (8 items)

- [x] M-1: Uses real spec examples
  - Validation: All fixtures from OGC 23-001/23-002 examples
- [x] M-2: Complete structure validation
  - Validation: All responses validated completely (not just existence)
- [x] M-3: Realistic scenarios
  - Validation: Tests match real user workflows (discover → query → navigate)
- [x] M-4: Behavior not implementation
  - Validation: Tests external API behavior, not internal details
- [x] M-5: Real server fixtures
  - Validation: 8/8 tests use spec example fixtures
- [x] M-6: Client behavior validation
  - Validation: 8/8 tests assert on end-to-end client workflow outputs
- [x] M-7: Integration points
  - Validation: Tests integrate Endpoint + QueryBuilder + Parsers
- [x] M-8: Clear error messages
  - Validation: Workflow errors indicate which step failed

### Useful Tests (7 items)

- [x] U-1: Bug detection validated
  - Validation: Broke navigation link following, workflow test failed ✅
- [x] U-2: Clear failure messages
  - Validation: Failures show workflow step that failed
- [x] U-3: Fast execution
  - Validation: Average test time 723ms ✅ < 1s
- [x] U-4: Test independence
  - Validation: Each workflow test self-contained
- [x] U-5: Public API only
  - Validation: Tests user-facing API only
- [x] U-6: Survives refactoring
  - Validation: Internal refactoring doesn't break workflow tests ✅
- [x] U-7: Debug-friendly
  - Validation: Step-by-step workflow clearly shows failure point

### End-to-End Validation (6 items)

- [x] E2E-1: Complete workflows (3+ operations)
  - Validation: All 8 workflows span 4-6 operations
- [x] E2E-2: Real spec fixtures
  - Validation: All fixtures match OGC spec examples
- [x] E2E-3: Cross-component integration
  - Validation: Tests integrate 3+ components per workflow
- [x] E2E-4: Resource navigation
  - Validation: 5/8 workflows navigate via HATEOAS links
- [ ] E2E-5: Round-trip scenarios
  - Status: Deferred to Phase 5 (POST/PUT/PATCH implementation)
- [x] E2E-6: Realistic data volumes
  - Validation: Fixtures contain 10-100 resources (not minimal test data)

### Documentation (5 items)

- [x] DOC-1: Utilities documented
  - Validation: setupMockAPI has complete JSDoc
- [x] DOC-2: @specification tags
  - Validation: 8/8 tests (100%) ✅
- [x] DOC-3: @fixture references
  - Validation: 8/8 tests (100%) ✅
- [x] DOC-4: @scenario tags
  - Validation: All 8 workflows have @scenario tags
- [x] DOC-5: Coverage gaps documented
  - Validation: README lists gaps (round-trip deferred, error workflows limited)

**Issues Found:** NONE

**Ready for Peer Review:** ✅ YES
```

**Peer Review + Final Sign-Off:**

```markdown
### E2E Quality Validation

- [x] Workflows complete and realistic
- [x] Real fixtures used throughout
- [x] Cross-component integration validated
- [x] Navigation patterns correct
- [x] Data volumes realistic

**Overall Quality:** ✅ EXCELLENT

**Decision:** ✅ APPROVED FOR MERGE
```

---

## 10. Key Recommendations

### 10.1 Priorities

**MUST (Critical for Quality):**

1. ✅ Complete self-review checklist before every PR
2. ✅ Validate bug detection (U-1) - intentionally break code
3. ✅ Meet coverage targets (QM-1, QM-2) - 85-95% statement, 80-95% branch
4. ✅ Ensure test independence (U-4, QM-5) - run in random order
5. ✅ Document utilities completely (DOC-1) - all helpers have JSDoc

**SHOULD (Highly Recommended):**

1. 🟡 Link tests to spec (DOC-2) - @specification tags for 60%+ tests
2. 🟡 Test all edge cases (D-3) - document and test all identified cases
3. 🟡 Validate error messages (D-8) - check error content, not just throws
4. 🟡 Use real fixtures (M-5) - spec examples, not made-up data
5. 🟡 Complete peer review (Stage 2) - don't skip validation

**MAY (Optional but Valuable):**

1. 🟢 Add @scenario tags (DOC-4) - for complex workflows
2. 🟢 Test parameter combinations (D-7) - for small parameter sets
3. 🟢 Run flakiness check (QM-4) - 100 runs before major releases
4. 🟢 Profile test performance (QM-6) - optimize slow tests
5. 🟢 Document coverage gaps (DOC-5) - maintain list of known limitations

### 10.2 Balancing Quality vs Speed

**During Initial Development:**

- Focus on meaningful tests (M-1 through M-4)
- Ensure bug detection (U-1) validated
- Defer documentation until PR time

**Before PR Submission:**

- Complete self-review checklist
- Add @specification tags (DOC-2)
- Document edge cases (D-3)
- Run coverage report

**During PR Review:**

- Peer reviewer validates deep coverage
- Validate E2E workflows (if applicable)
- Spot-check meaningful/useful items

**Before Merge:**

- Tech lead validates metrics
- Final sign-off on quality
- Merge approved PR

**Time Allocation:**

- Development: 60-70% of time
- Self-review: 15-20% of time
- Peer review: 10-15% of time
- Sign-off: 5% of time

### 10.3 Common Pitfalls to Avoid

**Pitfall 1: Checkbox Mentality**

- ❌ Checking boxes without actually validating
- ✅ Genuinely validate each item, document evidence

**Pitfall 2: Skipping Bug Detection Validation**

- ❌ Assuming tests catch bugs without validation
- ✅ Intentionally break code, verify tests fail

**Pitfall 3: Over-Documenting**

- ❌ Adding JSDoc to every test case
- ✅ Document only where it adds value (utilities, complex scenarios)

**Pitfall 4: Under-Testing Edge Cases**

- ❌ Only testing happy path
- ✅ Systematically test boundaries, edge cases, errors

**Pitfall 5: Ignoring Test Independence**

- ❌ Tests pass individually but fail in suite
- ✅ Run tests in random order, verify independence

### 10.4 Migration Strategy (Applying to Existing Tests)

**Phase 1: Assess Current State**

1. Run checklist against existing tests
2. Identify gaps and issues
3. Prioritize fixes by criticality

**Phase 2: Fix Critical Issues**

1. Fix M-1, M-2, M-4 (meaningful tests)
2. Fix U-1, U-4 (bug detection, independence)
3. Fix QM-1, QM-2 (coverage targets)

**Phase 3: Improve Quality**

1. Add @specification tags (DOC-2)
2. Document edge cases (D-3)
3. Validate error messages (D-8)

**Phase 4: Polish**

1. Add @fixture references (DOC-3)
2. Document utilities (DOC-1)
3. Run flakiness check (QM-4)

**Time Estimate:**

- Phase 1: 5-10 hours (assessment)
- Phase 2: 20-40 hours (critical fixes)
- Phase 3: 10-20 hours (quality improvements)
- Phase 4: 5-10 hours (polish)
- **Total:** 40-80 hours

---

## 11. Summary

### 11.1 Quality Dimensions

**Four Quality Dimensions (from Senior Feedback):**

1. **Meaningful** - Tests real behavior with real scenarios

   - Use real spec examples
   - Validate complete structures
   - Test realistic scenarios
   - Assert on behavior, not implementation

2. **Useful** - Catches real bugs, provides value

   - Intentionally break code → tests fail
   - Clear failure messages
   - Fast execution (< 100ms unit, < 1s integration)
   - Independent (no test order dependencies)

3. **Deep** - Comprehensive coverage including edge cases

   - Happy path + boundary values + edge cases + errors
   - 85-95% statement, 80-95% branch coverage
   - All code paths executed
   - All client behaviors verified (informed by spec expectations)

4. **End-to-End** - Complete workflows, cross-component integration
   - 3+ operations per workflow
   - Real fixtures from spec examples
   - Resource navigation via HATEOAS links
   - Cross-component integration validated

### 11.2 Checklist Summary

**41 Total Checklist Items:**

- Meaningful: 8 items (4 critical)
- Useful: 7 items (3 critical)
- Deep: 9 items (5 critical)
- End-to-End: 6 items (3 critical)
- Documentation: 5 items (2 critical)
- Quality Metrics: 6 items (4 critical)

**21 Critical Items** must pass for test completion

### 11.3 Review Process Summary

**3-Stage Review:**

1. **Self-Review** (15-30 min) - Developer completes checklist
2. **Peer Review** (10-20 min) - Team member validates
3. **Final Sign-Off** (5-10 min) - Tech lead approves

**Total Time:** 30-60 minutes per test file

### 11.4 Component-Specific Criteria

| Component        | Key Quality Indicators                                       |
| ---------------- | ------------------------------------------------------------ |
| **QueryBuilder** | parseAndValidateUrl() for all URLs, no string matching       |
| **Parsers**      | All structure types tested, 1-5 level nesting, all encodings |
| **Integration**  | 3+ operation workflows, real fixtures, cross-component       |
| **Utilities**    | 100% function coverage, complete JSDoc, all edge cases       |

### 11.5 What This Unblocks

✅ **Test Implementation** - Clear quality standards guide test writing  
✅ **PR Reviews** - Checklist provides objective review criteria  
✅ **Test Sign-Off** - Clear gate for test completion  
✅ **Quality Assurance** - Prevents "too trivial" feedback  
✅ **Maintainability** - Meaningful tests easier to maintain over time

---

## 12. References

### 12.1 Related Research Sections

- **Section 12:** QueryBuilder Testing Strategy (meaningful URL testing)
- **Section 17:** Coverage Targets and Metrics (coverage thresholds)
- **Section 18:** Error Condition Testing Strategy (error test completeness)
- **Section 19:** Test Organization and File Structure (test file patterns)
- **Section 34:** Test Utility and Helper Design (utility patterns)
- **Section 35:** JSDoc Testing Documentation Standards (documentation requirements)

### 12.2 External References

- **Lessons Learned Analysis:** [docs/research/requirements/lessons-learned-analysis.md](../../requirements/lessons-learned-analysis.md)
- **CSAPI Implementation Guide:** [docs/planning/csapi-implementation-guide.md](../../planning/csapi-implementation-guide.md)

### 12.3 Specifications

- **OGC 23-001:** Connected Systems API - Part 1: Feature Resources
- **OGC 23-002:** Connected Systems API - Part 2: Observation Data
- **OGC 23-003:** Connected Systems API - Part 3: Command & Control

### 12.4 Tools and Frameworks

- **Jest:** Testing framework (coverage, matchers, mocking)
- **Node.js URL API:** URL parsing and validation
- **TypeScript:** Type checking and validation

---

**Document Status:** ✅ COMPLETE  
**Review Status:** Ready for peer review  
**Next Steps:** Apply checklist to test implementation
