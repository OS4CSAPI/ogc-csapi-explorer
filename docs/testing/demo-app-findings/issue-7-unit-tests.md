# Issue #7 Findings Report — Unit Tests for Nested Create Methods and Content-Type Map

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#7](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/7) — "Write unit tests for new nested create methods and Content-Type map"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/url_builder.spec.ts`)
> **Dependencies:** Issue #5 (nested create methods), Issue #6 (Content-Type helper)
> **Labels:** enhancement, testing

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Discrepancy: `properties` Content-Type Classification](#7-discrepancy-properties-content-type-classification)
8. [Recommendation](#8-recommendation)
9. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
10. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (23-001r1 Part 1, 23-002r1 Part 2) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #7 describes. No production code modifications are proposed. All recommendations target test files only (`url_builder.spec.ts`).

---

## 2. Executive Summary

**Issue #7 is correct. The proposed tests are warranted and carry zero risk to library integrity.**

Issue #7 proposes writing unit tests for the changes described in Issue #5 (nested create methods) and Issue #6 (Content-Type helper map). This is the **lowest possible risk category** of library change: tests are purely additive, they do not modify production code, and they cannot affect runtime behavior.

| Aspect                        | Assessment                                                                                                                                                                                                                  |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Change type**               | Test-only — new `describe`/`it` blocks appended to existing test file                                                                                                                                                       |
| **Production code modified**  | None                                                                                                                                                                                                                        |
| **Existing tests affected**   | None — purely additive                                                                                                                                                                                                      |
| **Risk to library integrity** | **Zero**                                                                                                                                                                                                                    |
| **Estimated scope**           | ~50–60 new lines in `url_builder.spec.ts`, ~15 new test cases                                                                                                                                                               |
| **Dependency**                | Cannot be implemented until Issue #5 and Issue #6 are completed first                                                                                                                                                       |
| **Discrepancy found**         | Issue #7 misclassifies `properties` as Part 2 (`application/json`); correct classification is Part 1 (`application/geo+json`) per OGC 23-001r1 §11 — see [Section 7](#7-discrepancy-properties-content-type-classification) |

**Key finding:** Issue #7 inherits a `properties` Content-Type misclassification from its Issue #6 dependency. The Issue #6 findings report already identified and corrected this discrepancy. The test plan in Issue #7 must be adjusted to place `properties` under the Part 1 (`application/geo+json`) tests, not Part 2 (`application/json`).

---

## 3. Issue Description

### 3.1 Scope: Test Suite A — Nested Create Methods (Issue #5)

Issue #7 proposes ~9 tests for the 3 new nested create methods:

| Method Under Test                          | Test Categories                                                   | Expected URL Pattern             |
| ------------------------------------------ | ----------------------------------------------------------------- | -------------------------------- |
| `createDataStreamForSystem(systemId)`      | URL generation, special character encoding, resource availability | `/systems/{id}/datastreams`      |
| `createControlStreamForSystem(systemId)`   | URL generation, special character encoding, resource availability | `/systems/{id}/controlstreams`   |
| `createSamplingFeatureForSystem(systemId)` | URL generation, special character encoding, resource availability | `/systems/{id}/samplingFeatures` |

Each method gets 3 test cases:

1. **Basic URL generation** — Correct path with a simple system ID
2. **Special character encoding** — URN-style IDs (e.g., `urn:example:sys:001`) are properly encoded
3. **Resource availability assertion** — Throws `EndpointError` when systems resource is not available

### 3.2 Scope: Test Suite B — Content-Type Map (Issue #6)

Issue #7 proposes ~6 tests for the `CSAPI_CONTENT_TYPES` constant and `getContentTypeForResource()` helper:

| Test Category     | Description                                                                                                             |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Part 1 mapping    | All Part 1 resources (systems, deployments, procedures, samplingFeatures, **properties**) map to `application/geo+json` |
| Part 2 mapping    | All Part 2 resources (datastreams, observations, controlStreams, commands) map to `application/json`                    |
| Completeness      | All 9 `CSAPIResourceTypes` have an entry in `CSAPI_CONTENT_TYPES`                                                       |
| Helper function   | `getContentTypeForResource()` returns correct type for known resources                                                  |
| Fallback behavior | `getContentTypeForResource()` returns `application/json` for unknown resource types                                     |

### 3.3 Dependencies

Issue #7 **cannot** be implemented until both dependency issues are completed:

- **Issue #5** ([ogc-csapi-explorer#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5)) — Adds the nested create methods being tested
- **Issue #6** ([ogc-csapi-explorer#6](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6)) — Adds the `CSAPI_CONTENT_TYPES` constant and helper function being tested

Neither Issue #5 nor Issue #6 has been implemented yet. Only findings reports exist for both (committed as `24de2ac` and `f7fc7bd` respectively). Corresponding upstream GitHub issues have been created:

- [OS4CSAPI/ogc-client-CSAPI_2#57](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/57) — Nested create methods
- [OS4CSAPI/ogc-client-CSAPI_2#58](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/58) — Content-Type helper

---

## 4. Source Code Review

### 4.1 Existing test file (`url_builder.spec.ts`)

The test file contains **298 existing tests**, all passing. The file is well-structured with clear patterns:

- Tests are grouped by method under `describe()` blocks
- Each `describe()` block has its own `makeDsBuilder()` or similar factory function
- URL assertions use exact string matching via `expect(url).toBe(...)`
- Special character encoding tests use URN-style IDs
- Resource availability tests assert `EndpointError` throws

### 4.2 Existing test patterns for nested create methods

The `createObservation()` tests at L1724–1733 are the closest precedent for Issue #7's nested create method tests:

```typescript
describe('createObservation', () => {
  function makeDsBuilder() {
    return new CSAPIQueryBuilder(
      makeCollection({
        links: [
          {
            rel: 'self',
            type: '',
            title: '',
            href: 'https://example.com/collections/iot',
          },
          {
            rel: 'ogc-cs:datastreams',
            type: '',
            title: '',
            href: '/datastreams',
          },
        ],
      })
    );
  }

  it('returns correct URL for observation creation', () => {
    const url = makeDsBuilder().createObservation('ds-001');
    expect(url).toBe(
      'https://example.com/collections/iot/datastreams/ds-001/observations'
    );
  });

  it('encodes special characters in datastream ID', () => {
    const url = makeDsBuilder().createObservation('urn:example:ds:001');
    expect(url).toBe(
      'https://example.com/collections/iot/datastreams/urn%3Aexample%3Ads%3A001/observations'
    );
  });
});
```

The new tests for `createDataStreamForSystem()`, `createControlStreamForSystem()`, and `createSamplingFeatureForSystem()` would follow this exact pattern, substituting:

- Parent resource: `systems` (via `ogc-cs:systems` link rel)
- Child sub-path: `datastreams`, `controlstreams`, or `samplingFeatures`

### 4.3 Existing test pattern for `createDataStream()` (L1628–1631)

```typescript
it('createDataStream returns correct URL', () => {
  const url = makeDsBuilder().createDataStream();
  expect(url).toBe('https://example.com/collections/iot/datastreams');
});
```

This existing test remains untouched. New tests are appended in separate `describe()` blocks.

### 4.4 Content-Type test target

No tests currently exist for `CSAPI_CONTENT_TYPES` or `getContentTypeForResource()` because those artifacts do not yet exist (Issue #6 not implemented). The tests proposed by Issue #7 would be the first test coverage for these new exports.

The existing `CSAPIResourceTypes` array in `model.ts` (L31–41) lists all 9 resource types that the completeness test would iterate over:

```typescript
export const CSAPIResourceTypes = [
  'systems',
  'deployments',
  'samplingFeatures',
  'procedures',
  'properties',
  'datastreams',
  'observations',
  'controlStreams',
  'commands',
] as const;
```

### 4.5 Existing media type constants (`formats/constants.ts`)

The library already defines `MEDIA_TYPE_GEOJSON = 'application/geo+json'` (L25) and `MEDIA_TYPE_JSON = 'application/json'` (L31). Issue #6's `CSAPI_CONTENT_TYPES` map would reference these constants, and Issue #7's tests would validate the mapping.

---

## 5. Reference Document Review

All 12 linked reference documents from the ogc-csapi-explorer repository were reviewed. Key corroboration for Issue #7:

### 5.1 E2E Write Operations Report

- **14/15 core CRUD tests passed**; the 1 failure was `createDataStream()` → 405
- Finding #1: `createDataStream()` generates wrong URL — confirms the methods in Issue #5 are needed, and therefore the tests in Issue #7 are warranted
- Finding #6: Content-Type mapping needs library guidance — confirms Issue #6 is needed, and therefore the Content-Type tests in Issue #7 are warranted
- **Priority 2 recommendation** explicitly proposes the same `CSAPI_CONTENT_TYPES` map that Issue #7 would test, and lists `properties` under Part 1 (`application/geo+json`) — consistent with our correction

### 5.2 Library Source Changes Audit

- Confirms only **one commit** (`e73cff8`) has modified library source code during the entire demo app lifecycle
- All 317 tests in affected suites pass (298 in `url_builder.spec.ts` + 19 in `errors.spec.ts`)
- Validates that the test suite is clean and stable — safe to extend

### 5.3 Upstream Findings

- **F-1** (High severity, Priority 1): `createDataStream()` generates top-level URL — nested create methods needed
- **F-2** (Medium severity, Priority 1): Missing nested create methods — 3 methods need tests
- **F-10** (Medium severity, Priority 2): No Content-Type guidance — helper needs tests
- All three findings are addressed by Issues #5, #6, and #7 together

### 5.4 Library Findings Gap Analysis

- F-1 actionability: "Straightforward — change assertResourceAvailable target or add new method"
- F-2 actionability: "Straightforward — add 3 new methods following existing patterns"
- F-10 actionability: "Straightforward — add constant map + helper function"
- All rated as low implementation risk with high value

### 5.5 Library Integration Report

- Finding #12: CRUD URL symmetry confirmed working — validates the pattern Issue #7 tests would exercise
- Finding #13: Nested creation (observations/commands) works correctly — validates the pattern the new tests follow
- Finding #14: No Content-Type guidance from builder — directly supports the Content-Type tests

### 5.6 Contribution Goal Accuracy Assessment

- Validates library is "specification-scoped" with 82 methods covering all 9 resource types
- V-6 (CRUD URL symmetry) and V-7 (nested creation) verified working — test patterns are proven

### 5.7 Conformance Bypass Architecture Notes

- Demo bypasses `OgcApiEndpoint` and uses `CSAPIQueryBuilder` directly, which exposed the gaps that Issues #5/#6 address
- Tests for these fixes ensure the gaps remain covered after implementation

### 5.8 CRUD Smoke Test Findings

- F-15 (empty body crash on 201): Separate concern, not related to Issue #7
- F-16 (uid required for PUT): Separate concern, not related to Issue #7
- S-8 (OSH rejects geo+json Accept on POST): Confirms Content-Type handling is critical — supports testing the mapping

### 5.9 E2E Cross-Server Report

- 62/69 tests passing (90%) across OSH and 52North
- Content negotiation identified as critical — reinforces the need for Content-Type tests

### 5.10 EndpointError Isolation Report

- All 298 `url_builder.spec.ts` tests pass after the isolation refactor
- The test suite is stable and well-maintained — safe to extend with new tests
- `assertResourceAvailable()` throws `EndpointError` — the resource availability tests in Issue #7 would import from `shared/endpoint-error.ts` (new path post-refactor)

### 5.11 Schema Display Findings

- F-13 (JSDoc conflates `f` with `obsFormat`/`cmdFormat`): Separate concern from Issue #7
- F-14 (no schema response parser): Separate concern from Issue #7
- These are tracked independently and do not affect Issue #7's scope

### 5.12 AI Operational Constraints

- Authority precedence: Tests validate spec-compliant behavior — aligned with OGC spec authority
- No scope expansion: Issue #7 is purely about tests for Issues #5 and #6
- Minimal diffs: ~50–60 lines of test code appended to existing file
- No refactoring: Test infrastructure (`makeCollection`, `CSAPIQueryBuilder` import) already exists

---

## 6. Risk Assessment

### 6.1 What could go wrong?

| Risk                                          | Likelihood     | Impact          | Mitigation                                                                                                       |
| --------------------------------------------- | -------------- | --------------- | ---------------------------------------------------------------------------------------------------------------- |
| New tests break existing tests                | **None**       | N/A             | Tests are appended in new `describe()` blocks — no existing code touched                                         |
| New tests fail on first run                   | **Possible**   | None (expected) | Tests cannot pass until Issues #5 and #6 are implemented — this is by design                                     |
| Test assertions have wrong expected values    | **Very low**   | Low             | Assertions follow the exact URL patterns already validated by existing tests                                     |
| Import path errors                            | **Very low**   | Low             | Follow existing import patterns (`EndpointError` from `endpoint-error.ts`, `CSAPIQueryBuilder` already imported) |
| Tests accidentally modify production behavior | **Impossible** | N/A             | Tests are in `*.spec.ts` files — Jest only reads them, never ships them                                          |

### 6.2 Risk classification

**This is a ZERO RISK change to library integrity.**

Tests are the safest category of code change:

- They **do not** modify any production source file
- They **do not** change the public API surface
- They **do not** affect runtime behavior
- They **do not** add dependencies
- They **do not** change build output
- They are isolated in `*.spec.ts` files that are excluded from the library's published package

The only "risk" is that the tests won't pass until their dependency issues (#5 and #6) are implemented, which is expected and documented in Issue #7.

### 6.3 Integrity assessment

The library's integrity is **completely unaffected** by this change. Adding tests:

- Strengthens confidence in future implementations
- Documents expected behavior in executable form
- Provides regression protection
- Follows the existing 298-test pattern that has proven reliable

---

## 7. Discrepancy: `properties` Content-Type Classification

### The issue

Issue #7's test plan includes a section for Content-Type mapping tests that states:

> "Part 2 resources map to `application/json` — Test all 5: datastreams, observations, controlStreams, commands, **properties**"

This places `properties` under Part 2 with Content-Type `application/json`.

### The correction

**`properties` is a Part 1 resource and requires `application/geo+json`, not `application/json`.**

- **OGC 23-001r1 §11** defines the Properties resource type within Part 1 of the Connected Systems API
- The `CSAPIResourceTypes` array in `model.ts` lists `properties` alongside other Part 1 resources
- The E2E Write Operations Report's Priority 2 recommendation explicitly maps `properties: 'application/geo+json'`
- The Issue #6 findings report (committed as `f7fc7bd`) already identified and documented this exact discrepancy in its [Section 7: Discrepancy — `properties` Content-Type](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-6-content-type-helper.md#7-discrepancy-properties-content-type)

### Corrected test grouping

The Content-Type tests should use this classification:

| Category   | Resources                                                          | Expected Content-Type  |
| ---------- | ------------------------------------------------------------------ | ---------------------- |
| **Part 1** | systems, deployments, procedures, samplingFeatures, **properties** | `application/geo+json` |
| **Part 2** | datastreams, observations, controlStreams, commands                | `application/json`     |

This gives **5 Part 1 resources** and **4 Part 2 resources** (not 4 and 5 as Issue #7 states).

### Impact on test count

The total test count remains the same (~15 tests). Only the grouping within the Part 1 vs Part 2 test blocks needs adjustment. The `properties` assertion moves from the Part 2 block to the Part 1 block.

---

## 8. Recommendation

### Primary recommendation: **Proceed with Issue #7 after Issues #5 and #6 are implemented**

#### 8.1 Test Suite A: Nested Create Methods (~9 tests)

Add three new `describe()` blocks to `url_builder.spec.ts`, one per method:

```typescript
describe('createDataStreamForSystem', () => {
  // Factory function using systems link (ogc-cs:systems)
  it('returns correct URL for nested datastream creation', () => { ... });
  it('encodes special characters in system ID', () => { ... });
  it('throws EndpointError when systems resource is unavailable', () => { ... });
});

describe('createControlStreamForSystem', () => {
  it('returns correct URL for nested control stream creation', () => { ... });
  it('encodes special characters in system ID', () => { ... });
  it('throws EndpointError when systems resource is unavailable', () => { ... });
});

describe('createSamplingFeatureForSystem', () => {
  it('returns correct URL for nested sampling feature creation', () => { ... });
  it('encodes special characters in system ID', () => { ... });
  it('throws EndpointError when systems resource is unavailable', () => { ... });
});
```

Each test follows the exact pattern of the existing `createObservation()` tests (L1724–1733).

#### 8.2 Test Suite B: Content-Type Map (~6 tests)

Add a new `describe()` block for the Content-Type constant and helper:

```typescript
describe('CSAPI_CONTENT_TYPES', () => {
  it('maps Part 1 resources to application/geo+json', () => {
    // systems, deployments, procedures, samplingFeatures, properties
  });

  it('maps Part 2 resources to application/json', () => {
    // datastreams, observations, controlStreams, commands
  });

  it('has an entry for every CSAPIResourceType', () => {
    // Iterate CSAPIResourceTypes and verify each has a CSAPI_CONTENT_TYPES entry
  });
});

describe('getContentTypeForResource', () => {
  it('returns correct Content-Type for known resource types', () => { ... });
  it('returns application/json as fallback for unknown types', () => { ... });
  it('handles empty string input gracefully', () => { ... });
});
```

**Critical:** The Part 1 test must include `properties` (not the Part 2 test). See [Section 7](#7-discrepancy-properties-content-type-classification).

#### 8.3 Implementation order

1. **Wait** for Issue #5 (nested create methods) to be implemented
2. **Wait** for Issue #6 (Content-Type helper) to be implemented
3. Add Test Suite A (nested create methods) to `url_builder.spec.ts`
4. Add Test Suite B (Content-Type map) to `url_builder.spec.ts`
5. Run full test suite: `npx jest url_builder.spec.ts`
6. Verify all 298 existing tests + ~15 new tests pass

#### 8.4 What NOT to do

- **Do not** modify any existing test
- **Do not** modify any production source file
- **Do not** add tests before the dependency issues are implemented
- **Do not** place `properties` in the Part 2 test group

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source                     | Says About These Tests                                                    | Weight                    |
| --------------- | -------------------------- | ------------------------------------------------------------------------- | ------------------------- |
| 1 (Highest)     | OGC 23-001r1 §11           | `properties` is Part 1 (geo+json) — corrects Issue #7                     | Definitive                |
| 2               | OGC 23-002r1 §7.2          | Nested creation is spec-required — tests validate compliance              | Definitive                |
| 3               | AI Collaboration Agreement | Tests strengthen contribution quality                                     | Supportive                |
| 4               | Issue #7                   | Proposes test plan with correct scope but incorrect `properties` grouping | Scoping (with correction) |
| 5               | Existing test patterns     | `createObservation()` tests at L1724–1733 provide exact template          | Precedent                 |
| 6               | E2E test evidence          | 14/15 CRUD tests pass, Content-Type critical for POST                     | Evidence                  |

---

## Appendix B: Cross-Reference Matrix

| Document                                                                                                                                                       | Location           | Relevance to Issue #7                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------- |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | ogc-csapi-explorer | F-1, F-2, F-10 — the findings that Issues #5/#6 address and Issue #7 tests                   |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | ogc-csapi-explorer | Severity/priority ratings for F-1, F-2, F-10; actionability assessment                       |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | ogc-csapi-explorer | Live server evidence: 405 error on `createDataStream()`, Content-Type mapping recommendation |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | ogc-csapi-explorer | Cross-server validation confirms Content-Type criticality                                    |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | ogc-csapi-explorer | Findings #12 (CRUD symmetry), #13 (nested creation works), #14 (no Content-Type guidance)    |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | Validates library spec-scoped, confirms F-1 bug, V-6/V-7 positive                            |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | ogc-csapi-explorer | Confirms clean test suite (298 + 19 all passing), safe to extend                             |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Explains why direct `CSAPIQueryBuilder` testing exposed these gaps                           |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | ogc-csapi-explorer | S-8 confirms Content-Type handling is critical for write operations                          |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | ogc-csapi-explorer | 298 tests pass post-refactor; `EndpointError` import path confirmed                          |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | ogc-csapi-explorer | F-13/F-14 are separate concerns; no overlap with Issue #7                                    |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | ogc-client-CSAPI_2 | Authority precedence, no scope expansion, minimal diffs                                      |

---

## Conclusion

Issue #7 proposes the right tests, in the right place, following the right patterns. The changes are:

1. **Correct** — tests validate spec-compliant behavior documented across 12 reference documents
2. **Consistent** — follows the exact test patterns already established by the 298 existing tests
3. **Non-impacting** — zero production code changes; purely additive test-only modifications
4. **Zero-risk** — tests cannot degrade library integrity; they can only increase confidence
5. **Properly sequenced** — correctly identifies dependency on Issues #5 and #6

**One correction required:** Move `properties` from the Part 2 test group to Part 1 (see [Section 7](#7-discrepancy-properties-content-type-classification)). This is consistent with the correction already documented in the Issue #6 findings report.

The recommended approach is: implement Issues #5 and #6 first, then write the tests as described in Issue #7 with the `properties` classification correction applied.
