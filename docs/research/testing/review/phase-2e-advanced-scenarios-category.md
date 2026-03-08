# Phase 2E: Advanced Scenarios Category Deep Dive

**Review Date:** February 2026  
**Reviewer:** AI Review Agent  
**Phase:** 2E of multi-phase research document review  
**Category:** Advanced Testing Scenarios (12 documents)  
**Anti-Pattern Catalog:** [Phase 0: Lessons from Failed Attempt](phase-0-lessons-from-failed-attempt.md)

---

## 1. Phase Overview

### 1.1 Documents Reviewed

| #   | Document                                                                                                | Lines | Status      | Verdict                |
| --- | ------------------------------------------------------------------------------------------------------- | ----- | ----------- | ---------------------- |
| 18  | [error-condition-testing-strategy.md](../findings/18-error-condition-testing-strategy.md)               | 1,195 | ✅ Reviewed | ✅ Pass                |
| 23  | [pagination-testing.md](../findings/23-pagination-testing.md)                                           | 1,667 | ✅ Reviewed | ⚠️ Issues Found        |
| 24  | [query-parameter-combination-testing.md](../findings/24-query-parameter-combination-testing.md)         | 1,906 | ✅ Reviewed | ⚠️ Issues Found        |
| 25  | [format-negotiation-testing.md](../findings/25-format-negotiation-testing.md)                           | 1,460 | ✅ Reviewed | ⚠️ Issues Found        |
| 26  | [subresource-navigation-testing.md](../findings/26-subresource-navigation-testing.md)                   | 1,798 | ✅ Reviewed | ✅ Pass                |
| 27  | [schema-driven-validation-testing.md](../findings/27-schema-driven-validation-testing.md)               | 1,660 | ✅ Reviewed | ⚠️ Issues Found        |
| 28  | [temporal-query-testing.md](../findings/28-temporal-query-testing.md)                                   | 1,496 | ✅ Reviewed | ⚠️ Issues Found        |
| 29  | [spatial-query-testing.md](../findings/29-spatial-query-testing.md)                                     | 1,597 | ✅ Reviewed | ⚠️ Issues Found (mild) |
| 30  | [bulk-operations-testing.md](../findings/30-bulk-operations-testing.md)                                 | 1,723 | ✅ Reviewed | ⚠️ Issues Found        |
| 31  | [command-lifecycle-testing.md](../findings/31-command-lifecycle-testing.md)                             | 2,006 | ✅ Reviewed | ✅ Pass                |
| 32  | [real-world-server-compatibility-testing.md](../findings/32-real-world-server-compatibility-testing.md) | 2,061 | ✅ Reviewed | ❌ Critical Issues     |
| 33  | [performance-efficiency-testing.md](../findings/33-performance-efficiency-testing.md)                   | 2,020 | ✅ Reviewed | ⚠️ Issues (scope)      |

**Total Lines Reviewed:** 20,589

### 1.2 Review Focus

These 12 documents define advanced testing scenarios for error handling, pagination, query parameters, format negotiation, sub-resource navigation, schema validation, temporal/spatial queries, bulk operations, command lifecycle, server compatibility, and performance. The review evaluates:

1. **Client vs. Server Orientation** — Do tests verify client code behavior (URL construction, response parsing, error handling, type construction) or server spec-compliance?
2. **Anti-Pattern Cross-Reference** — Do documents avoid the 5 anti-patterns from Phase 0?
3. **Realistic Scope** — Are testing efforts proportionate to an initial contribution?
4. **Alignment with Upstream Patterns** — Do test patterns match the upstream `ogc-client` style (QueryBuilder + mocked fetch + parsed output assertions)?
5. **Practical Implementation Guidance** — Can a developer actually implement the recommended tests?
6. **No Scope Creep / Gold-Plating** — Are recommendations focused on initial contribution needs?

---

## 2. Review Methodology

### 2.1 Anti-Pattern Cross-Reference

Each document was checked against all 5 Phase 0 anti-patterns:

| ID  | Anti-Pattern                 | Description                                                   |
| --- | ---------------------------- | ------------------------------------------------------------- |
| AP1 | Testing Response Content     | Tests validate server responses rather than client code       |
| AP2 | Hybrid Fixture/Live          | Tests designed to run against live servers OR fixtures        |
| AP3 | OGC Requirement Traceability | Test structure mirrors spec requirements, not client code     |
| AP4 | Asserting Data Shape         | Tests check response structure without testing transformation |
| AP5 | Graceful Skipping            | Tests conditionally skip based on fixture content             |

### 2.2 Client Orientation Scoring

Each document was scored for client-orientation percentage based on the proportion of test patterns that genuinely test client code (URL building, response parsing, error handling, type construction) versus those that test server behavior (response content, HTTP status codes, data shape, spec compliance).

### 2.3 Scope Assessment

Test counts, fixture counts, estimated effort hours, and proposed file counts were evaluated against the baseline that this is an **initial contribution** to an existing library. Upstream `ogc-client` has approximately 15 test files totaling ~2,500 lines — proposed additions should be proportionate.

### 2.4 Cross-Document Consistency

Documents were checked for internal contradictions (e.g., error class philosophy) and alignment with the Implementation Guide architecture (CSAPIQueryBuilder, format parsers, conformance extensions).

---

## 3. Overall Assessment

### Verdict: ⚠️ CONDITIONAL GO — Significant corrections required

| Metric                         | Value                                                                 |
| ------------------------------ | --------------------------------------------------------------------- |
| Documents passing              | 3 of 12 (Docs 18, 26, 31)                                             |
| Documents with issues          | 8 of 12                                                               |
| Documents with critical issues | 1 of 12 (Doc 32)                                                      |
| Total issues identified        | 27                                                                    |
| Critical issues                | 2                                                                     |
| High-priority issues           | 10                                                                    |
| Medium-priority issues         | 11                                                                    |
| Low-priority issues            | 4                                                                     |
| Aggregate scope creep          | **~600+ tests, ~300-450h estimated effort** — wildly disproportionate |

### Client Orientation Summary

| Document                     | Client % | Primary Concern                                              |
| ---------------------------- | -------- | ------------------------------------------------------------ |
| 18 — Error Conditions        | ~85%     | Minor scope items                                            |
| 23 — Pagination              | ~40%     | `fetchJson()` asserts fixture content, not client behavior   |
| 24 — Query Parameters        | ~70%     | Server validation/precedence testing                         |
| 25 — Format Negotiation      | ~60%     | 45 scenarios test server HTTP behavior                       |
| 26 — Sub-Resource Navigation | ~90%     | Minor cosmetic issues only                                   |
| 27 — Schema Validation       | ~70%     | Schema evolution tests require server integration            |
| 28 — Temporal Queries        | ~55%     | Identifies client code but doesn't test it                   |
| 29 — Spatial Queries         | ~65%     | Milder — has some good client validation tests               |
| 30 — Bulk Operations         | ~40%     | Asserts fixture data directly; ignores client chunking logic |
| 31 — Command Lifecycle       | ~85%     | Properly mocked, client-oriented                             |
| 32 — Server Compatibility    | ~35%     | Fundamentally a server conformance test suite                |
| 33 — Performance             | ~90%     | Well-oriented but entirely out of scope                      |
| **Weighted Average**         | **~63%** | **~37% of test patterns are server-oriented**                |

---

## 4. Critical Issues (Must Fix — Showstoppers)

### C1: Doc 32 — Entire Document Built on Hybrid Fixture/Live Execution Model (AP2)

**Document:** [32-real-world-server-compatibility-testing.md](../findings/32-real-world-server-compatibility-testing.md)  
**Anti-Pattern:** AP2, AP5  
**Severity:** CRITICAL

**Problem:** The document's fundamental architecture is a hybrid fixture/live test execution model — the exact architecture the senior developer identified as the primary failure mode. Key evidence:

- Section 4.1: `checkServerAvailability()` gating with `console.warn('OSH server unavailable - skipping live tests')`
- Section 6.4: Separate jest projects for `*.offline.spec.ts` and `*.live.spec.ts`, with `npm run test:live` nightly scripts
- Lines 546-548: Hardcoded credentials (redacted — see env vars)
- Lines 744-755: Nightly CI/CD YAML for live server testing
- 5+ instances of AP5 (graceful skipping): `console.warn('OSH unavailable - skipping tests'); return;`, `console.warn('No datastreams for system - skipping'); return;`, etc.

**Impact:** This is the single most severe anti-pattern identified in the entire review. Doc 32's design mirrors the failed attempt's architecture: tests that run against live OpenSensorHub and 52°North servers, conditionally skip based on server availability, and validate server response content rather than client code.

**Resolution:** The document's client-oriented sections (~35% — conformance detection, graceful degradation) are valuable and should be extracted. The remaining ~65% (live server testing, response content assertions, availability gating) must be either removed or completely reframed as fixture-based client behavior tests.

---

### C2: Doc 23 — Test Templates Assert Fixture Content, Not Client Behavior (AP1)

**Document:** [23-pagination-testing.md](../findings/23-pagination-testing.md)  
**Anti-Pattern:** AP1, AP4, AP5  
**Severity:** CRITICAL

**Problem:** Sections 5.1-5.2 contain ~30 test scenarios using an undefined `fetchJson()` function that directly asserts server response fixture content. These tests would pass even if the client code did nothing — the hallmark of server testing.

Key instances:

- `const response = await fetchJson('/systems?limit=10&offset=0'); const nextLink = response.links?.find(...)` — asserts fixture has `next` link
- `expect(response.features).toEqual([])` — asserts fixture returns empty
- `expect(response.numberReturned).toBe(5)` — validates fixture metadata
- `if (response.numberMatched !== undefined) { expect(...) }` — conditional assertion on fixture content (AP5)
- Cursor pagination tests: `expect(page1Ids).not.toEqual(page2Ids)` — tests SERVER returns different items per page
- `fetchJson('/observations?limit=15000')` expects 400 — tests SERVER rejects invalid limit

**Mitigating factor:** The URL construction tests using `builder.*` + `parseAndValidateUrl()` (scattered in earlier sections) ARE properly client-oriented. The link parsing utility tests (`extractNextLink`, `extractCursor`, `isLastPage`) are genuinely useful.

**Resolution:** Test templates in Sections 5.1-5.2 must be rewritten as client-oriented tests: feed fixture through mocked fetch → call client pagination methods → assert client's parsed output (extracted links, page metadata, constructed next-page URLs). Remove undefined `fetchJson()` pattern entirely.

---

## 5. High-Priority Issues (Should Fix Before Implementation)

### H1: Doc 32 — Response Content Assertions Throughout (AP1, AP4)

**Document:** [32-real-world-server-compatibility-testing.md](../findings/32-real-world-server-compatibility-testing.md)

Tests throughout Section 5 assert live server response content rather than client transformation:

- `expect(systems.items.length).toBeGreaterThan(0)` — validates server returns items
- `expect(system.id).toMatch(/^[a-z0-9]+$/)` — validates server's ID format (Base32). Client shouldn't care about ID format
- `expect(ds).toHaveProperty('observedProperty')` — asserts server response has expected fields
- `expect(obs).toHaveProperty('phenomenonTime')` — asserts server data shape
- `expect(deployment.geometry.coordinates).toHaveLength(2)` with `expect(lon).toBeCloseTo(14.03, 0)` — asserts specific Baltic Sea coordinates from 52°North server

**Resolution:** These assertions must target client outputs: parsed objects, constructed URLs, set flags, thrown errors.

---

### H2: Doc 25 — 45 Test Scenarios Test Server HTTP Response Behavior (AP1)

**Document:** [25-format-negotiation-testing.md](../findings/25-format-negotiation-testing.md)

Section 4 (scenarios 1-45) is structured as HTTP request → expected HTTP response assertions (`GET /systems/sys123?f=json → Expected: 200 OK, Content-Type: application/json`). These test what the SERVER returns, not what the CLIENT constructs or parses. The client library only builds URLs with `f=` parameters and handles responses — whether the server returns 200 or 406 is server compliance testing.

Aggravating factors:

- Accept header scenarios (scenarios 21-25) explicitly note the client does NOT use Accept headers, yet 5 tests are designed for them
- Default format scenarios (scenarios 31-35) test what the server returns when no format is specified
- The entire FormatValidator/URL encoding section is only ~15% of the document but represents the actual client-testable surface

The document itself notes the client implements format selection in "~13 lines of code" — 50 test scenarios for 13 lines is extreme over-engineering.

**Resolution:** Trim to ~10-15 client-oriented tests: URL construction with `f=` parameter, URL encoding of `+` as `%2B`, format constant mapping. Remove server HTTP behavior scenarios.

---

### H3: Doc 24 — "Invalid Parameter" and "Precedence Conflict" Tests Test Server Behavior (AP1)

**Document:** [24-query-parameter-combination-testing.md](../findings/24-query-parameter-combination-testing.md)

Two categories of test scenarios in Section 4.2 test server behavior:

**Category A — "Wrong Parameter for Resource" (10 scenarios):**

- `GET /properties?bbox=-180,-90,180,90` → "Expected: 400 Bad Request or silently ignored" — testing whether SERVER validates parameter applicability

**Category C — "Precedence Conflicts" (10 scenarios):**

- `offset + cursor` → "Expected: cursor takes precedence, offset ignored" — testing SERVER's precedence resolution
- `datetime + phenomenonTime` → "Expected: phenomenonTime takes precedence" — SERVER behavior
- `f + Accept header` → "Expected: f parameter takes precedence" — SERVER behavior

The client's job is to build the URLs requested by the user and handle whatever response comes back. It should not implement server-side parameter validation or precedence rules.

**Resolution:** Remove server validation/precedence test scenarios. Retain the ~60 client-oriented URL construction tests using `builder.*`.

---

### H4: Doc 30 — Tests Assert Fixture Response Data Directly (AP1)

**Document:** [30-bulk-operations-testing.md](../findings/30-bulk-operations-testing.md)

Section 4.1-4.2 test patterns assert fixture response data:

- `expect(response.data.items).toHaveLength(10)` — verifies fixture content
- `expect(obs.id).toMatch(/^obs-/)` — validates fixture ID format
- `expect(obs.result).toBe(20 + i * 0.5)` — checks fixture contains expected values
- `expect(cmd.parameters.action).toBe('capture')` — validates fixture command content

**Resolution:** Tests should assert client transformation outputs: `BulkCreateResult<T>` construction from raw responses, auto-chunking behavior, fallback-to-sequential logic, progress callback invocations.

---

### H5: Doc 30 — No Tests for Actual Client Logic (AP4)

**Document:** [30-bulk-operations-testing.md](../findings/30-bulk-operations-testing.md)

The document defines substantial client-side code (auto-chunking, fallback-to-sequential, BulkCreateResult construction, progress callbacks) but the test scenarios in Section 4 don't test any of it. The structural gap is:

- Section 6 defines `autoChunk()`, `fallbackToSequential()`, `BulkCreateResult<T>` — real client code
- Section 4 tests fixture response data — not the client code from Section 6

**Resolution:** Add test scenarios that exercise the client-side auto-chunking and fallback logic. These are the actual testable client behaviors.

---

### H6: Doc 28 — Identifies Client Utilities But Doesn't Test Them (AP4)

**Document:** [28-temporal-query-testing.md](../findings/28-temporal-query-testing.md)

Section 7 defines 5 client utility functions (`parseInstant()`, `parseInterval()`, `parseDuration()`, `toUTC()`, `validateISO8601()`), but the test scenarios in Section 4 only test URL query parameter construction and `response.ok` assertions. No test exercises the temporal parsing/transformation functions.

**Resolution:** Test scenarios should target the utility functions: `parseInstant('2024-01-01T12:00:00Z')` → `Date`, `parseInterval('2024-01-01/..')` → `{start, end}`, `toUTC(localDate)` → expected ISO string.

---

### H7: Doc 23 — Cursor Pagination Tests Assert Server Behavior (AP1)

**Document:** [23-pagination-testing.md](../findings/23-pagination-testing.md)

Section 5.2: Multiple tests assert server pagination state:

- Loops through all pages testing SERVER produces no duplicates
- Tests that SERVER returns different items per page
- Tests SERVER's maximum limit enforcement

These are server conformance tests, not client tests.

**Resolution:** Client tests should verify: client correctly extracts cursor from response links, client constructs next-page URL with cursor parameter, client recognizes last page (no `next` link).

---

### H8: Doc 32 — Graceful Skipping Based on Server Availability (AP5)

**Document:** [32-real-world-server-compatibility-testing.md](../findings/32-real-world-server-compatibility-testing.md)

5+ instances of conditional test skipping based on live server availability:

- `console.warn('OSH server unavailable - skipping live tests'); return;`
- `console.warn('OSH unavailable - skipping tests'); return;`
- `console.warn('No datastreams for system - skipping'); return;`
- `console.warn('52N unavailable - skipping tests'); return;`
- `console.warn('Server unavailable - skipping test suite'); return;`

In client tests, fixtures are controlled — there's never a reason to skip because "the fixture is unavailable."

**Resolution:** All tests must use mocked fetch with deterministic fixtures. Remove all availability checks.

---

### H9: Doc 25 — Accept Header Tests for Feature Client Doesn't Use (AP1)

**Document:** [25-format-negotiation-testing.md](../findings/25-format-negotiation-testing.md)

Scenarios 21-25 test server behavior for Accept header negotiation, but the document itself notes (line 179) that the CSAPI client does NOT use Accept headers — it uses the `f=` query parameter exclusively. Testing server response to Accept headers tests a feature the client doesn't implement.

**Resolution:** Remove Accept header test scenarios entirely.

---

### H10: Doc 27 — Schema Evolution Tests Require Server Integration (AP1)

**Document:** [27-schema-driven-validation-testing.md](../findings/27-schema-driven-validation-testing.md)

Section 6.1: Schema evolution tests use `await client.createDataStream(...)`, `await client.updateDataStream(...)`, `await expect(client.updateDataStream(...)).rejects.toThrow(/409/)`. The 409 Conflict response requires server state — this is inherently integration testing against a server, not client unit testing.

**Resolution:** If schema validation is implemented as client-side pre-validation (`validateObservation()` with `options.validate = true`), test the validation function directly. The schema evolution 409 tests should either be removed or clearly labeled as hypothetical integration scenarios.

---

## 6. Medium-Priority Issues

### M1: Doc 24 — `ParameterValidationError` Contradicts Doc 18 Error Philosophy

**Document:** [24-query-parameter-combination-testing.md](../findings/24-query-parameter-combination-testing.md)

Section 5.1 proposes `class ParameterValidationError extends Error` with custom properties (`parameterName`, `parameterValue`, `validationRule`), used 12+ times throughout the document. Doc 18 explicitly states "Reuse existing `EndpointError` and native `Error` — no new error classes needed." This is a direct cross-document contradiction.

**Resolution:** Use existing `EndpointError` or native `Error` per Doc 18's established philosophy.

---

### M2: Doc 25 — Format Precedence Rules Describe Server Behavior (AP1)

Sections 3.1-3.5: Format precedence rules ("Query parameter `f=sml` overrides Accept header", "Server returns default format") describe server-side behavior. The client doesn't implement precedence — it sends `f=` and accepts whatever comes back.

---

### M3: Doc 25 — `ResponseValidator` Tests Server Content-Type Correctness (AP1)

Section 6.2: `ResponseValidator` class verifies that the server correctly set Content-Type headers matching the requested format. This validates server behavior, not client transformation.

---

### M4: Doc 23 — Server Invalid Parameter Rejection Tests (AP1)

Section 5.1 "Invalid Parameters" block: Tests like `fetchJson('/systems?limit=0')` expecting 400 test whether the SERVER validates invalid limits. Only client-side validation (e.g., QueryBuilder rejects negative limit before sending) is appropriate.

---

### M5: Doc 27 — "Server-Side Validation" Section Documents Server Compliance (AP1)

Section 10.2 explicitly describes server behavior: "Receive observation", "Fetch DataStream schema", "Return 400 Bad Request if validation fails." This is server compliance documentation, not client behavior testing.

---

### M6: Doc 28 — `expect(response.ok).toBe(true)` Meaningless Against Fixtures (AP1)

Section 4.1: Tests assert `expect(response.ok).toBe(true)` against fixture-driven responses. This only confirms the mock returns `ok: true`, testing nothing. The `expect(response.requestUrl).toContain(...)` assertions in the same tests ARE client-oriented and should be retained.

---

### M7: Doc 29 — Same `expect(response.ok).toBe(true)` Pattern (AP1)

Section 4.1: Identical meaningless `response.ok` assertions as Doc 28. Table descriptions say "Returns resources in North America" — describing server filtering behavior.

---

### M8: Doc 30 — Performance Tests Measure Server Response Timing (AP1)

Section 4.5: `expect(elapsed).toBeLessThan(500)` and `expect(memUsed).toBeLessThan(100 * 1024 * 1024)` are integration performance tests against server responses, not client unit tests.

---

### M9: Doc 23 — Conditional Assertion Based on Fixture Content (AP5)

Section 5.1, Metadata Validation: `if (response.numberMatched !== undefined) { expect(...) }` — conditionally runs assertion based on fixture content. In client tests, you control the fixture — if you need `numberMatched`, put it in the fixture.

---

### M10: Doc 32 — Server ID Format and Coordinate Assertions (AP4)

Separate instances of asserting server data shape:

- `expect(system.id).toMatch(/^[a-z0-9]+$/)` — client shouldn't care about ID format
- `expect(lon).toBeCloseTo(14.03, 0)` — asserts specific coordinates from 52°North server's Baltic Sea buoy

---

### M11: Doc 24 — Mixed Client/Server Invalid Parameter Tests (AP1)

Section 4.2 Category B: ~50% are legitimate client validation (bbox minLon > maxLon, negative limit) but ~50% test server behavior (invalid format → 406, malformed URI → server rejection).

---

## 7. Low-Priority Issues

### L1: Doc 18 — SWE Common Binary Encoding _Error Test Scenarios_ May Be Speculative

23-25 binary encoding error tests (wrong endianness, insufficient buffer, invalid data type codes) are speculative — these specific error scenarios may need refinement once binary parsing is implemented. **Clarification:** Binary SWE parsing itself (Doc 10, 96 tests) is IN SCOPE per the implementation guide §7 and Phase 2D assessment (M2, P4: "sound and directly usable"). This L1 flag is about the _error test specificity_ in Doc 18 §4.2.3 only, not about binary parsing scope.

---

### L2: Doc 18 — Worker Extension Error Scenarios Premature

7 worker error scenarios (initialization failure, timeout, premature termination) reference infrastructure that doesn't exist yet.

---

### L3: Doc 23 — Metadata Validation Checks Fixture Invariants (AP4)

`expect(response.numberReturned).toBe(response.features.length)` — validates fixture self-consistency, not client behavior. `numberReturned === features.length` is a spec invariant the client doesn't need to enforce.

---

### L4: Doc 29 — Point BBox Test Compares Result Set Sizes (AP4)

`expect(responseWithBbox.features.length).toBeLessThanOrEqual(responseWithoutBbox.features.length)` — compares server filtering results rather than testing client code.

---

## 8. Scope Creep Assessment (Critical Cross-Cutting Concern)

### 8.1 Aggregate Scope Analysis

The combined scope proposed across all 12 documents is massively disproportionate to an initial contribution:

| Document                     | Tests    | Fixtures | Est. Hours    | Test Files |
| ---------------------------- | -------- | -------- | ------------- | ---------- |
| 18 — Error Conditions        | ~40      | ~25      | 15-22h        | 3          |
| 23 — Pagination              | 53       | 20       | 19-28h        | 5          |
| 24 — Query Parameters        | 120      | ~40      | 34-49h        | 5          |
| 25 — Format Negotiation      | 50       | 37       | 18-28h        | 5          |
| 26 — Sub-Resource Navigation | 60       | 50       | 40-52h        | 4          |
| 27 — Schema Validation       | 66       | 60       | 28-41h        | 4          |
| 28 — Temporal Queries        | 72       | 55       | 25-36h        | 4          |
| 29 — Spatial Queries         | 43       | 40       | 18-26h        | 3          |
| 30 — Bulk Operations         | 28       | 30       | 20-30h        | 3          |
| 31 — Command Lifecycle       | 42       | 35       | 20-28h        | 3          |
| 32 — Server Compatibility    | 56       | ~25      | 31-46h        | 5          |
| 33 — Performance             | 53       | 51       | 46-64h        | 5          |
| **TOTAL**                    | **~683** | **~468** | **~314-450h** | **~49**    |

For context, upstream `ogc-client` has approximately **15 test files** totaling **~2,500 lines**. These 12 documents alone propose **49 test files** with **~683 tests** requiring **~314-450 hours** (8-11 weeks of full-time work) — and this is only 12 of 38 research documents.

### 8.2 Specific Scope Concerns

| ID  | Document | Concern                                                                           | Severity |
| --- | -------- | --------------------------------------------------------------------------------- | -------- |
| S1  | Doc 24   | 120 test scenarios, 34-49h for parameter combinations alone                       | CRITICAL |
| S2  | Doc 32   | 56 tests, 31-46h for server compatibility infrastructure                          | HIGH     |
| S3  | Doc 33   | 53 tests, 46-64h for explicitly out-of-scope performance testing                  | HIGH     |
| S4  | Doc 25   | 50 tests for ~13 lines of format selection code                                   | HIGH     |
| S5  | Doc 28   | 72 tests, 25-36h for temporal query URL construction                              | HIGH     |
| S6  | Doc 27   | 66 tests, 60 fixtures, full validation implementation in test doc                 | HIGH     |
| S7  | Doc 26   | 60 tests, 40-52h — scope justified by 16 relationship types but still substantial | MEDIUM   |
| S8  | Doc 30   | 500+ lines of implementation code (auto-chunking, fallback) in test research doc  | MEDIUM   |

### 8.3 Implementation Code in Test Research Documents

Several documents embed substantial implementation code that belongs in design/planning documents, not test research:

- **Doc 28** Section 7-8: ISO 8601 parsing utilities, client API design with `DateTimeParameter` types
- **Doc 29** Section 8: Antimeridian handling workarounds with split-query strategy
- **Doc 30** Sections 6.3-6.4, 9.3: Auto-chunking strategy, fallback-to-sequential, retry with exponential backoff
- **Doc 27** Section 10.1: 375 lines of full client-side validation implementation
- **Doc 24** Section 5.1: `ParameterValidator` and `ParameterEncoder` classes (~260 lines)

This is scope confusion — implementation design is masquerading as testing research, inflating perceived testing complexity.

---

## 9. Positive Findings

### P1: Doc 26 — Strongest Document in Category (~90% Client-Oriented)

[26-subresource-navigation-testing.md](../findings/26-subresource-navigation-testing.md) is the model for how these documents should look. Nearly every test follows the pattern: call `builder.getXxx()` → `parseAndValidateUrl(url, { pathname, query })`. It stays firmly focused on URL construction, parameter encoding, input validation, and type-safety for 16 sub-resource relationship patterns. No AP2/AP3/AP5 issues. Reusable test helpers (`testNestedNavigation()`, `describe.each`) reduce boilerplate effectively.

### P2: Doc 31 — Excellent Command Lifecycle Testing (~85% Client-Oriented)

[31-command-lifecycle-testing.md](../findings/31-command-lifecycle-testing.md) correctly uses `mockServer.mockAsyncCommand()` to isolate client behavior: polling logic with exponential backoff, timeout handling, cancellation, state machine interpretation. No hybrid execution, no OGC requirement IDs, no conditional skipping. The command lifecycle genuinely requires complex client logic (async polling, state transitions), and the document focuses test design on that logic.

### P3: Doc 18 — Best Error Philosophy Alignment with Upstream

[18-error-condition-testing-strategy.md](../findings/18-error-condition-testing-strategy.md) correctly mirrors upstream's "minimal, targeted error handling" philosophy. Clean separation of Library vs. Server vs. Browser responsibility. Correct reuse of existing `EndpointError` — no new error classes. Clear "Library does NOT throw for" list prevents over-validation. Test examples in the appendix are genuinely client-oriented.

### P4: Doc 33 — Best Out-of-Scope Declaration

[33-performance-efficiency-testing.md](../findings/33-performance-efficiency-testing.md) opens with "⚠️ PERFORMANCE TESTING IS NOT IN SCOPE ⚠️" and provides clear rationale (upstream has zero performance tests). Despite the excellent scoping, the document still provides 2,000 lines of detailed implementation guidance for the out-of-scope work, which is where the "Issues" rating comes from (research effort directed at excluded scope).

### P5: Builder + ParseAndValidateUrl Pattern Across Multiple Documents

Multiple documents (Docs 23, 24, 26, 28, 29) correctly use the `builder.*` method → `parseAndValidateUrl()` pattern for URL construction testing. This is the upstream-aligned approach and represents the strongest test design pattern across the category.

### P6: No AP3 (OGC Requirement Traceability) Found in Any Document

None of the 12 documents structure tests around OGC requirement IDs (e.g., `/req/X/Y`). This is a significant improvement over the failed attempt, where every test file used requirement-ID-driven naming.

### P7: Doc 32's Client-Oriented Sections Are Valuable (When Extracted)

Despite Doc 32's critical issues, its conformance detection tests (~35% of content) are genuinely client-oriented: testing how the client parses conformance declarations, probes endpoints, and degrades gracefully when capabilities are missing. These sections should be preserved and potentially merged into Doc 22 (conformance testing).

---

## 10. Anti-Pattern Distribution

| Anti-Pattern               | Occurrences  | Documents Affected                      | Severity Range |
| -------------------------- | ------------ | --------------------------------------- | -------------- |
| AP1 (Response Content)     | 18 instances | 8 docs (23, 24, 25, 28, 29, 30, 32, 27) | CRITICAL — LOW |
| AP2 (Hybrid Fixture/Live)  | 2 instances  | 1 doc (32)                              | CRITICAL       |
| AP3 (OGC Requirement IDs)  | 0 instances  | None                                    | —              |
| AP4 (Asserting Data Shape) | 6 instances  | 5 docs (23, 28, 29, 30, 32)             | HIGH — LOW     |
| AP5 (Graceful Skipping)    | 7 instances  | 2 docs (23, 32)                         | HIGH — MEDIUM  |

**Key finding:** AP1 (Testing Response Content) is the dominant anti-pattern, appearing in 8 of 12 documents. This is the residual "server testing" orientation that the senior developer warned about. AP2 (Hybrid Fixture/Live) is concentrated in Doc 32, which is the most severely affected document.

---

## 11. Cross-Document Consistency Issues

### 11.1 Error Class Contradiction

Doc 24 proposes `ParameterValidationError` with custom properties. Doc 18 explicitly states "no new error classes — reuse `EndpointError` and native `Error`." Doc 18 was written as the error handling strategy and should take precedence.

### 11.2 Structural Gap: Test Scenarios Don't Test Identified Client Code

A recurring pattern across Docs 28, 29, and 30: the document's later sections carefully define client-side code (parsing utilities, validation functions, auto-chunking logic), but the test scenarios in Section 4 only test URL construction and fixture response content. The test scenarios fail to connect with the client code identified in the same document.

### 11.3 Implementation Code in Test Research

Multiple documents (24, 27, 28, 29, 30) embed substantial implementation code (~1,500+ lines total) that belongs in design/planning documents, not test research. This inflates the perceived testing complexity and blurs the boundary between "what to test" and "what to build."

---

## 12. Recommendations

### 12.1 Immediate Actions

1. **Doc 32: Reclassify or substantially rewrite.** The hybrid fixture/live model is the primary failure mode from Phase 0. Extract the client-oriented sections (conformance detection, graceful degradation, ~35%) into a supplement to Doc 22. The remaining server compatibility testing should be either removed or clearly labeled as out-of-scope server conformance research.

2. **Doc 23: Rewrite test templates in Sections 5.1-5.2.** Replace `fetchJson()` + response assertions with `builder.*` + `parseAndValidateUrl()` and client pagination method → parsed output assertions. Retain the link parsing utility tests.

3. **Doc 24: Remove `ParameterValidationError`.** Use `EndpointError` or native `Error` per Doc 18. Remove the 20 server validation/precedence test scenarios. Trim from 120 to ~30-40 client-oriented tests.

### 12.2 Before Implementation

4. **Docs 25, 28, 29: Remove `response.ok` and HTTP status assertions.** Keep URL construction tests. Trim Doc 25 from 50 to ~10-15 tests.

5. **Doc 30: Add tests for client logic (auto-chunking, fallback).** The current tests only assert fixture content. Move implementation code to a design document.

6. **Establish scope budget.** All 12 documents combined propose ~683 tests / ~450h. A realistic initial contribution should target ~80-120 tests in ~4-6 test files, focusing on the client behaviors that matter most.

### 12.3 Nice-to-Fix

7. **Docs 28, 29, 30: Bridge the structural gap.** Add test scenarios for the client utility functions defined in the same documents (temporal parsing, spatial validation, bulk chunking).

8. **Doc 33: Reduce detail for out-of-scope work.** 2,000 lines for explicitly excluded functionality is wasted research effort. A 200-line "Future Performance Testing Considerations" section would suffice.

### 12.4 Assessment

**Status: Conditional Go.** The 3 passing documents (18, 26, 31) demonstrate that well-oriented advanced scenario testing is achievable. The 8 documents with issues all have recoverable problems — primarily residual server-testing orientation and scope creep — rather than fundamental architectural misalignment. Doc 32 is the exception and requires the most significant rework.

The aggregate scope creep (~683 tests, ~450h) is the category-level concern that must be addressed before implementation begins. A scope budget should be established as part of implementation planning.

---

## 13. Issue Resolution Tracker

| ID  | Severity | Doc | Description                                                                                     | Status      |
| --- | -------- | --- | ----------------------------------------------------------------------------------------------- | ----------- |
| C1  | CRITICAL | 32  | Hybrid fixture/live execution model (AP2)                                                       | ✅ Resolved |
| C2  | CRITICAL | 23  | Test templates assert fixture content via `fetchJson()` (AP1)                                   | ✅ Resolved |
| H1  | HIGH     | 32  | Response content assertions throughout (AP1, AP4)                                               | ✅ Resolved |
| H2  | HIGH     | 25  | 45 scenarios test server HTTP response behavior (AP1)                                           | ✅ Resolved |
| H3  | HIGH     | 24  | Server validation/precedence testing (AP1)                                                      | ✅ Resolved |
| H4  | HIGH     | 30  | Tests assert fixture response data directly (AP1)                                               | ✅ Resolved |
| H5  | HIGH     | 30  | No tests for actual client logic — chunking, fallback (AP4)                                     | ✅ Resolved |
| H6  | HIGH     | 28  | Identifies client utilities but doesn't test them (AP4)                                         | ✅ Resolved |
| H7  | HIGH     | 23  | Cursor pagination tests assert server behavior (AP1)                                            | ✅ Resolved |
| H8  | HIGH     | 32  | Graceful skipping on server availability — 5+ instances (AP5)                                   | ✅ Resolved |
| H9  | HIGH     | 25  | Accept header tests for unused feature (AP1)                                                    | ✅ Resolved |
| H10 | HIGH     | 27  | Schema evolution tests require server integration (AP1)                                         | ✅ Resolved |
| M1  | MEDIUM   | 24  | `ParameterValidationError` contradicts Doc 18 (cross-doc)                                       | ✅ Resolved |
| M2  | MEDIUM   | 25  | Format precedence rules describe server behavior (AP1)                                          | ✅ Resolved |
| M3  | MEDIUM   | 25  | `ResponseValidator` tests server Content-Type (AP1)                                             | ✅ Resolved |
| M4  | MEDIUM   | 23  | Server invalid parameter rejection tests (AP1)                                                  | ✅ Resolved |
| M5  | MEDIUM   | 27  | "Server-Side Validation" section documents server compliance                                    | ✅ Resolved |
| M6  | MEDIUM   | 28  | `response.ok` assertions meaningless against fixtures (AP1)                                     | ✅ Resolved |
| M7  | MEDIUM   | 29  | Same `response.ok` pattern as Doc 28 (AP1)                                                      | ✅ Resolved |
| M8  | MEDIUM   | 30  | Performance tests measure server response timing (AP1)                                          | ✅ Resolved |
| M9  | MEDIUM   | 23  | Conditional assertion on fixture content (AP5)                                                  | ✅ Resolved |
| M10 | MEDIUM   | 32  | Server ID format and coordinate assertions (AP4)                                                | ✅ Resolved |
| M11 | MEDIUM   | 24  | Mixed client/server invalid parameter tests (AP1)                                               | ✅ Resolved |
| L1  | LOW      | 18  | SWE binary encoding error test scenarios may be speculative (binary parsing itself is in scope) | ✅ Resolved |
| L2  | LOW      | 18  | Worker extension errors — premature                                                             | ✅ Resolved |
| L3  | LOW      | 23  | Metadata validation checks fixture invariants (AP4)                                             | ✅ Resolved |
| L4  | LOW      | 29  | Point bbox test compares result set sizes (AP4)                                                 | ✅ Resolved |

**Summary:** 2 Critical, 10 High, 11 Medium, 4 Low — **27 total issues**
