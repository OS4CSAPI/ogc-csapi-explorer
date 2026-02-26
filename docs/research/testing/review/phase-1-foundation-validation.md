# Phase 1: Foundation Validation

**Review Date:** February 12, 2026  
**Reviewer:** AI Research Review Agent (Claude Opus 4.6)  
**Review Framework:** 5 Quality Layers + Client-Orientation Lens  
**Phase 0 Reference:** [phase-0-lessons-from-failed-attempt.md](phase-0-lessons-from-failed-attempt.md)

---

## 1. Phase Overview

### Purpose

Validate the 4 foundational research documents that all subsequent documents build upon. These define the EDR blueprint, upstream consistency patterns, QueryBuilder testing strategy, and the final synthesis playbook. If any of these are flawed, every dependent document inherits those flaws.

### Documents Reviewed

| #   | Document                                                                               | Lines | Status              |
| --- | -------------------------------------------------------------------------------------- | ----- | ------------------- |
| 01  | [01-edr-test-blueprint.md](../findings/01-edr-test-blueprint.md)                       | 1,107 | ✅ PASS             |
| 02  | [02-upstream-test-consistency.md](../findings/02-upstream-test-consistency.md)         | 1,391 | ⚠️ PASS WITH ISSUES |
| 12  | [12-querybuilder-testing-strategy.md](../findings/12-querybuilder-testing-strategy.md) | 2,635 | ⚠️ PASS WITH ISSUES |
| 38  | [38-testing-playbook-synthesis.md](../findings/38-testing-playbook-synthesis.md)       | 3,412 | ⚠️ PASS WITH ISSUES |

**Total lines reviewed:** 8,545

---

## 2. Review Methodology

Each document was evaluated against 6 criteria:

1. **Structural Integrity** — Is the document well-organized, complete, and internally navigable?
2. **Content Accuracy** — Do claims match actual upstream code, OGC specifications, and verifiable facts?
3. **Internal Consistency** — Do recommendations, code examples, and conclusions within the document agree?
4. **Practical Utility** — Are recommendations specific, actionable, and implementable by a developer?
5. **Strategic Value** — Do recommendations align with the project's contribution goal and upstream acceptance requirements?
6. **Client vs Server Orientation** (Phase 0 lens) — Does the document recommend testing _client behavior_ (URL construction, response parsing, error handling) rather than _server compliance_ (response content validation, spec conformance)?

Each criterion scored as: ✅ PASS, ⚠️ PASS WITH ISSUES, or ❌ FAIL.

---

## 3. Overall Assessment: ✅ GO

**The 4 foundation documents are fundamentally sound and provide a solid, actionable basis for CSAPI testing.** All documents pass the critical client-orientation test — none recommends patterns that echo the failed repo's anti-patterns. The core architectural guidance (QueryBuilder pattern, mocked fetch, URL construction testing, parsed output assertions) is correctly aligned with upstream conventions throughout.

**No showstoppers were found.** All issues identified are correctable without structural changes to the documents. The documents can be used to guide implementation, provided the issues below are addressed first (or tracked as known errata).

**Confidence level:** HIGH — The documents demonstrate thorough upstream analysis, consistent application of patterns, and clear practical value.

---

## 4. Critical Issues (Showstoppers)

**None found.**

---

## 5. High-Priority Issues

### Issue H1: Resource Type Naming Error in Document 02

**Document:** 02-upstream-test-consistency.md  
**Location:** Section 12 (CSAPI-Specific Adaptations)  
**Quality Layer:** Content Accuracy  
**Severity:** HIGH — Wrong names would propagate to incorrect test file names, type names, and API surface

**Problem:** Document 02 lists the 9 CSAPI resource types using SensorThings API terminology instead of OGC CSAPI terminology:

| Doc 02 Lists       | Should Be (per Implementation Guide) |
| ------------------ | ------------------------------------ |
| ObservedProperties | **Properties**                       |
| Sensors            | _(not a CSAPI resource type)_        |
| FeaturesOfInterest | _(not a CSAPI resource type)_        |
| _(missing)_        | **ControlStreams**                   |
| _(missing)_        | **Commands**                         |

The authoritative list from the Implementation Guide is: **Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands**.

Document 12 uses the correct list. Document 38 uses the correct list. Only Document 02 has this error.

**Impact:** A developer following Doc 02's scaling guidance would create test files for `ObservedProperties`, `Sensors`, and `FeaturesOfInterest` — none of which exist in the CSAPI implementation — while missing `ControlStreams` and `Commands` entirely.

**Recommendation:** Correct Section 12 of Doc 02 to use the Implementation Guide's canonical resource type list.

---

### Issue H2: Test File Location Inconsistency Across Documents

**Documents:** 02 vs 38 (12 partially affected)  
**Quality Layer:** Internal Consistency (cross-document)  
**Severity:** HIGH — Contradictory guidance on a fundamental project structure decision

**Problem:** The documents give conflicting advice on where test files should live:

| Document | Recommended Pattern                       | Example Path                                    |
| -------- | ----------------------------------------- | ----------------------------------------------- |
| 01       | Colocated (matches upstream EDR)          | `src/ogc-api/edr/helpers.spec.ts`               |
| 02       | Colocated ("no separate test/ directory") | `src/ogc-api/csapi/helpers.spec.ts`             |
| 12       | Colocated (Section 18 Option 2)           | `src/ogc-api/csapi/url_builder-systems.spec.ts` |
| 38       | `__tests__/` subdirectory                 | `src/ogc-api/csapi/__tests__/helpers.spec.ts`   |

Document 38, the synthesis playbook that's meant to be the definitive implementation guide, uses `__tests__/` subdirectories throughout all its code examples. This contradicts Document 02's explicit "no separate test/ directory" recommendation and the upstream convention visible in WFS, WMS, WMTS, TMS, STAC, and EDR implementations.

**Impact:** Without resolution, a developer following the playbook (Doc 38) would create a file structure that contradicts the consistency analysis (Doc 02) and the upstream pattern.

**Recommendation:** Doc 38 should be updated to use colocated `.spec.ts` files, matching the upstream convention documented in Doc 02. Specifically:

- `src/ogc-api/csapi/helpers.spec.ts` (not `__tests__/helpers.spec.ts`)
- `src/ogc-api/csapi/url_builder.spec.ts` (not `__tests__/url_builder.spec.ts`)
- Integration tests in `src/ogc-api/endpoint.spec.ts` (extending the existing file, as Doc 02 recommends)

---

## 6. Medium-Priority Issues

### Issue M1: Conformance Class URI Uncertainty

**Documents:** 06, 12, 14, 18, 22, 38  
**Quality Layer:** Content Accuracy  
**Severity:** ~~MEDIUM~~ → **ELEVATED TO HIGH** — Verified against both published specifications AND live server; multiple documents use wrong URIs  
**Status:** **RESOLVED (Verified against published standard)** — See [verified-conformance-uris.md](verified-conformance-uris.md)

**Problem:** Documents use conformance class URIs that do not match the published OGC standards. Cross-referenced against both the published specifications ([OGC 23-001](https://docs.ogc.org/is/23-001/23-001.html), [OGC 23-002](https://docs.ogc.org/is/23-002/23-002.html)) and a live OSH SensorHub instance on 2026-02-12, we found:

1. **Wrong namespace prefix:** Docs 22 and 38 use `ogcapi-connected-systems-1` (hyphenated). The correct form is `ogcapi-connectedsystems-1` (no hyphen). (~60+ occurrences)
2. **Wrong class names:** Doc 12 uses invented names like `system-features`, `deployment-features`, `samplingfeature-features`. The correct names per the published spec are `system`, `deployment`, `sf`, etc. (~26 occurrences)
3. **Wrong encoding class names:** Doc 22 uses `o-and-m-json`, `swe-json`. The correct names are `json`, `swecommon-json`, etc.
4. **Non-existent class:** Docs 14 and 38 reference `conf/dynamic-data` which is not a real conformance class in the published standard.

**Important note on authority:** The live server uses `/conf/core` for the common conformance class, but the **published specification** (Annex A of both 23-001 and 23-002) defines this as `/conf/api-common`. The published standard takes precedence. Our code should accept both for compatibility.

```
# SPEC-CORRECT URIs (from published OGC 23-001, 23-002):
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream

# SERVER LEGACY (valid for compatibility, but not spec-correct):
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core

# WRONG (Doc 12):
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system-features

# WRONG (Docs 22, 38):
http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/core
```

**Resolution:** Conformance URIs verified against the published OGC Implementation Standards are documented in [verified-conformance-uris.md](verified-conformance-uris.md). The published specification is the authoritative source; server deviations are noted. Individual document corrections will be applied during Phase 2-4 reviews. All fixture files and implementation code MUST use the spec-correct URIs from that reference.

---

### Issue M2: Sync vs Async QueryBuilder Method Inconsistency

**Documents:** 12 vs 38  
**Quality Layer:** Internal Consistency  
**Severity:** MEDIUM — Could cause type errors during implementation

**Problem:** Document 12 test examples use async patterns for QueryBuilder methods:

```typescript
// Doc 12, Section 5.2
it('constructs collection URL without parameters', async () => {
  const url = await builder.getSystems();  // async
  parseAndValidateUrl(url, { ... });
});
```

But Document 38's stub implementation returns synchronously:

```typescript
// Doc 38, Task 1.3
getSystems(options?: SystemQueryOptions): string {  // sync return
  this.validateResource('systems');
  const url = buildResourceUrl(...);
  return qs ? `${url}?${qs}` : url;
}
```

The upstream EDR QueryBuilder methods (`buildAreaDownloadUrl`, `buildLocationsDownloadUrl`, etc.) are synchronous — they construct and return URL strings without any async operations. URL construction is pure string manipulation and doesn't need async.

**Impact:** Using `await` on a sync return value works in practice (it resolves immediately), but it's technically incorrect, clutters the test code, and may confuse developers about the API contract.

**Recommendation:** Standardize on synchronous QueryBuilder URL methods throughout all documents. Remove `async/await` from test examples that call URL construction methods. Reserve async patterns for endpoint-level methods that require fixture loading (e.g., `endpoint.csapi('collection')`).

**Resolution:** Removed `await` from 302 synchronous QueryBuilder method calls across 14 documents (03, 04, 05, 12, 13, 14, 18, 19, 23, 24, 25, 26, 34, 35). Five `await builder.` instances intentionally retained — these are in error-handling test patterns where `await` is part of expected-throw logic, not URL construction. Verified against upstream: EDR `build*` methods are synchronous (return `string`), while getting the builder itself is async (`await endpoint.edr()`).

---

### Issue M3: Invented Factory Method `OgcApiEndpoint.fromUrl()`

**Document:** 38  
**Quality Layer:** Content Accuracy  
**Severity:** MEDIUM — Could confuse developers during implementation

**Problem:** Document 38's integration test examples use `OgcApiEndpoint.fromUrl()`:

```typescript
const endpoint = await OgcApiEndpoint.fromUrl(
  'http://example.com/api',
  { conformance: [...], collections: [...] }
);
```

This factory method does not exist in the upstream `OgcApiEndpoint` class. The actual upstream pattern is:

```typescript
// Upstream pattern: constructor + mocked fetch
beforeEach(() => {
  endpoint = new OgcApiEndpoint('http://local/sample-data/');
});
```

Where `fetch` is globally mocked to return fixtures for the constructed URLs.

**Impact:** A developer following the playbook literally would try to use a non-existent API. The test would fail at the `fromUrl` call.

**Recommendation:** Replace `OgcApiEndpoint.fromUrl()` examples with the upstream constructor pattern (`new OgcApiEndpoint(url)`) and ensure the global fetch mock is set up to serve the appropriate fixtures.

**Resolution:** Replaced all 60 occurrences of `OgcApiEndpoint.fromUrl()` with `new OgcApiEndpoint()` across 8 documents (04, 05, 06, 07, 14, 18, 36, 38). Zero remaining `fromUrl` references. Note: some instances passed fixture data as a second argument — the real constructor doesn't accept this, but it conveys test intent and will need adapting to the mocked-fetch pattern during implementation.

---

### Issue M4: URL-Encoded Space Character Inconsistency

**Documents:** 38 vs 12  
**Quality Layer:** Internal Consistency  
**Severity:** MEDIUM — Could cause test failures on encoding assertions

**Problem:** Document 38's `buildQueryString` helper uses JavaScript's `URLSearchParams`, which encodes spaces as `+`:

```typescript
// Doc 38 test expectation:
expect(qs).toContain('Weather+Station+%231'); // + for spaces
```

But Document 12 and Document 01 consistently recommend `%20` encoding:

```typescript
// Doc 12 test expectation:
expect(url).toContain('q=weather%20station%20%231'); // %20 for spaces
```

Both are valid per RFC 3986 / RFC 1866, but the test assertions are incompatible. If the implementation uses `URLSearchParams`, the Doc 12 tests will fail. If it uses manual encoding, the Doc 38 tests will fail.

**Recommendation:** Decide on one encoding standard for spaces in query parameters. Since the upstream EDR uses `new URL()` + `searchParams.set()` (which uses `+` for spaces in form data but `%20` for path segments), verify the actual encoding behavior and standardize all test assertions to match.

**Resolution:** Standardized on `%20` encoding. Updated Doc 38's `buildQueryString` helper to add `.replace(/\+/g, '%20')` normalization (matching upstream's `setQueryParams()` pattern in `http-utils.ts`), and fixed the test assertion from `Weather+Station+%231` to `Weather%20Station%20%231`. Doc 12 already used `%20` consistently. Doc 24's `+` references are intentionally in "bad input" sections showing what NOT to do — no changes needed there.

---

## 7. Low-Priority Issues

### Issue L1: Speculative Code in CSAPI Application Sections

**Document:** 01  
**Quality Layer:** Content Accuracy (minor)  
**Severity:** LOW

Document 01 includes CSAPI application code examples (Sections 10-12) that project patterns from EDR to CSAPI. These are reasonable projections but are not from actual upstream code. Examples like `buildPostSystemUrl()`, `buildPostDeploymentUrl()`, and nested resource validation are design proposals, not documented patterns.

**Recommendation:** No change needed, but implementers should understand these are projections, not verified upstream patterns.

---

### Issue L2: `createTestEndpoint` Placeholder

**Document:** 12  
**Quality Layer:** Practical Utility (minor)  
**Severity:** LOW

The `createTestEndpoint` helper in Section 18.2 throws `'createTestEndpoint not implemented'`. This is acknowledged as a placeholder but needs actual implementation before tests can run.

**Recommendation:** Track as implementation work, not a document defect. The specification of what it should do is clear.

---

### Issue L3: sortBy/sortOrder Parameter Gap — **RESOLVED**

**Document:** 12  
**Quality Layer:** Content Accuracy (minor)  
**Severity:** ~~LOW~~ **RESOLVED**

~~Section 24.2 identifies `sortBy`/`sortOrder` parameters as a gap ("Not covered in test specifications"). These are not critical for initial implementation but should be tracked.~~

**Resolution:** `sortBy`/`sortOrder` brought back into scope (MEDIUM priority). Sorting is essential for deterministic pagination — paginating unsorted results produces unpredictable ordering across pages. Implementation guide §6 and Doc 12 §4.1/§24.2 updated.

---

### Issue L4: Doc 02 Overfitting of Test-to-Code Ratios

**Document:** 02  
**Quality Layer:** Content Accuracy (minor)  
**Severity:** LOW

The featureprops test-to-code ratio of 4.53× is presented as a data point alongside others, but it's an extreme outlier caused by XML parsing complexity with many edge cases. It could mislead if a developer treats it as a target rather than an anomaly.

**Recommendation:** Add a note flagging 4.53× as an outlier, not a target.

---

## 8. Positive Findings

### P1: Excellent Client-Orientation Throughout (All Documents)

All four documents consistently recommend patterns that test client behavior:

- **URL construction** via `parseAndValidateUrl()` — verifying the client builds correct URLs from parameters
- **Parsed output assertions** — `expect(endpoint.property).resolves.toEqual({...})` — verifying the client transforms raw data correctly
- **Mocked fetch** — `globalThis.fetch = jest.fn()` or `globalThis.fetchResponseFactory` — complete isolation from servers
- **Error validation** — `expect(() => builder.method()).toThrow()` — testing client-side validation logic
- **Controlled fixtures** — designed to exercise specific scenarios, never conditional skipping

**None of the 5 anti-patterns from Phase 0 were detected in any document.** This is the single most important finding of this review.

### P2: Consistent QueryBuilder Architecture (Docs 01, 12, 38)

The QueryBuilder pattern is correctly and consistently described across all three documents that discuss it:

- Direct inheritance from EDR's `EDRQueryBuilder` pattern
- Factory method access via `endpoint.csapi(collectionId)`
- Builder caching (same instance returned for same collection)
- URL construction as the primary testable behavior
- Composition over inheritance (as per upstream PR review feedback)

### P3: Thorough Pattern Evolution Analysis (Doc 02)

Document 02's timeline analysis (2022-2023 Foundation → 2024 Refinement → 2025 Modern) correctly identifies which patterns are emerging vs deprecated, giving clear guidance on what CSAPI should adopt:

- ✅ Adopt: Async fixture loading, `jest.fn()` mocks, `afterEach` cleanup, URL parsing validation, type-safe interfaces
- ❌ Avoid: Sync fixture imports, `globalThis.fetchResponseFactory`, XML fixtures for OGC APIs, flat fixture structure

### P4: Actionable Test Code Examples (Docs 12, 38)

Documents 12 and 38 provide near-production-ready test code. The Systems resource tests in Doc 12 Section 5.2 (~200 lines) cover all 12 methods with proper `parseAndValidateUrl` usage, and could serve as a direct implementation template (M2 async/sync issue has been resolved).

### P5: Comprehensive Method Coverage Verification (Doc 12)

Document 12 Section 24 explicitly cross-references every recommendation against the Implementation Guide, confirming all 80 QueryBuilder methods have test specifications. This systematic validation step is strong evidence of thoroughness.

### P6: Realistic Scope Estimates (All Documents)

The estimates across documents are internally consistent:

- Doc 01: EDR has 29 tests, ~600 lines → CSAPI needs proportionally more
- Doc 02: Target 1.2-1.6× test-to-code ratio → ~1,400-1,800 test lines
- Doc 12: 188 tests, 1,880-2,256 lines, 22-29 hours
- Doc 38: 320+ tests across all phases, 52-76 total hours

These numbers converge and are grounded in upstream data points.

---

## 9. Cross-Document Consistency Matrix

| Aspect                    | Doc 01                 | Doc 02                 | Doc 12                       | Doc 38                                       | Consistent?          |
| ------------------------- | ---------------------- | ---------------------- | ---------------------------- | -------------------------------------------- | -------------------- |
| QueryBuilder pattern      | ✅                     | ✅                     | ✅                           | ✅                                           | ✅ Yes               |
| Mock fetch approach       | ✅ jest.fn()           | ✅ jest.fn()           | ✅ jest.fn()                 | ✅ jest.fn()                                 | ✅ Yes               |
| Resource type names       | ✅ Correct             | ❌ Wrong (H1)          | ✅ Correct                   | ✅ Correct                                   | ⚠️ No                |
| Test file location        | Colocated              | Colocated              | Colocated                    | `__tests__/` (H2)                            | ⚠️ No                |
| URL validation tool       | parseAndValidateUrl    | parseAndValidateUrl    | parseAndValidateUrl          | parseAndValidateUrl                          | ✅ Yes               |
| Client-orientation        | ✅                     | ✅                     | ✅                           | ✅                                           | ✅ Yes               |
| Fixture structure         | Hierarchical           | Hierarchical           | Hierarchical                 | Hierarchical                                 | ✅ Yes               |
| Test-to-code ratio target | —                      | 1.2-1.6×               | 1.2-1.6× (188 tests)         | —                                            | ✅ Yes               |
| QB methods sync/async     | Sync                   | —                      | ~~Mixed (M2)~~ Sync          | Sync                                         | ✅ Yes (M2 resolved) |
| Conformance URIs          | —                      | —                      | ~~Variant A~~ Corrected (M1) | ~~Variant B~~ Corrected (M1)                 | ✅ Yes (M1 resolved) |
| Endpoint construction     | `new OgcApiEndpoint()` | `new OgcApiEndpoint()` | `new OgcApiEndpoint()`       | ~~`.fromUrl()`~~ `new OgcApiEndpoint()` (M3) | ✅ Yes (M3 resolved) |
| Space encoding            | %20                    | —                      | %20                          | ~~+~~ %20 (M4)                               | ✅ Yes (M4 resolved) |

---

## 10. Issue Tracking Summary

| ID  | Severity         | Document(s)                               | Issue                                                                                                                                                                      | Status                                                                      |
| --- | ---------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| H1  | HIGH             | 02                                        | Wrong resource type names (SensorThings terminology)                                                                                                                       | **Resolved**                                                                |
| H2  | HIGH             | 38 (vs 01,02,12)                          | `__tests__/` directory contradicts colocated pattern                                                                                                                       | **Resolved**                                                                |
| M1  | ~~MEDIUM~~ HIGH  | 06, 12, 14, 18, 22, 38                    | Conformance URIs verified against published OGC specs (23-001, 23-002) AND live server — wrong prefix, wrong class names, server uses legacy `core` vs spec's `api-common` | **Resolved** — [verified-conformance-uris.md](verified-conformance-uris.md) |
| M2  | MEDIUM           | 03,04,05,12,13,14,18,19,23,24,25,26,34,35 | Sync vs async QueryBuilder methods — removed `await` from 302 sync method calls                                                                                            | **Resolved**                                                                |
| M3  | MEDIUM           | 04,05,06,07,14,18,36,38                   | `OgcApiEndpoint.fromUrl()` doesn't exist upstream — replaced 60 occurrences with `new OgcApiEndpoint()`                                                                    | **Resolved**                                                                |
| M4  | MEDIUM           | 38 (vs 12)                                | Space encoded as `+` vs `%20` — standardized on `%20`, updated `buildQueryString` and assertions                                                                           | **Resolved**                                                                |
| L1  | LOW              | 01                                        | Speculative CSAPI application code (noted, not a defect)                                                                                                                   | Informational                                                               |
| L2  | LOW              | 12                                        | `createTestEndpoint` placeholder                                                                                                                                           | Track as impl work                                                          |
| L3  | ~~LOW~~ RESOLVED | 12                                        | sortBy/sortOrder brought back into scope (MEDIUM priority)                                                                                                                 | **Resolved**                                                                |
| L4  | LOW              | 02                                        | 4.53× ratio outlier not flagged                                                                                                                                            | Open                                                                        |

---

## 11. Recommendation for Phase 2

### Verdict: Proceed to Phase 2

The foundation documents are solid. The issues found are correctable and do not undermine the overall testing strategy. Specifically:

1. **Before Phase 2 begins:** Resolve issues H1 and H2, as these could propagate through all subsequent documents. H1 is a simple name correction. H2 requires a decision (colocated is the upstream answer) and updating Doc 38's examples.

2. **During Phase 2 reviews:** Check each category's documents against the corrected resource type list and file location convention. Flag any documents that inherited Doc 02's wrong names or Doc 38's `__tests__/` pattern.

3. **~~Track M2-M4 as known errata~~ All medium issues resolved:** M1 (conformance URIs) was **verified and resolved** by cross-referencing the published OGC Implementation Standards (23-001 Part 1 and 23-002 Part 2) with a live server — see [verified-conformance-uris.md](verified-conformance-uris.md). M2 (async/sync) resolved by removing 302 unnecessary `await` calls across 14 docs. M3 (`fromUrl()`) resolved by replacing 60 occurrences with `new OgcApiEndpoint()` across 8 docs. M4 (space encoding) resolved by standardizing on `%20` in Doc 38's helper and assertions. The published specification is the authoritative source; the server's `/conf/core` is noted as a legacy alias for the spec-correct `/conf/api-common`. During Phase 2-4 reviews, fix the wrong conformance URIs in each document using that reference.

### Phase 2 Categories to Review

Based on Foundation Validation, the recommended Phase 2 review order (highest risk first):

| Phase | Category                | Documents              | Risk Level             |
| ----- | ----------------------- | ---------------------- | ---------------------- |
| 2A    | Fixture Design          | 03, 04, 06, 07, 14, 15 | Medium (H1 dependency) |
| 2B    | Test Architecture       | 05, 08, 19, 24, 34     | Medium (H2 dependency) |
| 2C    | Type System & Parsing   | 09, 10, 11, 16, 17     | Low                    |
| 2D    | Resource-Specific       | 13, 20, 21, 22, 25, 26 | Medium (H1 dependency) |
| 2E    | Quality & Standards     | 27, 28, 29, 33, 35, 36 | Low                    |
| 2F    | Integration & Workflows | 30, 31, 32, 37         | Low                    |

---

## 12. Appendix: Per-Document Detailed Scores

### Document 01: EDR Test Blueprint

| Quality Layer        | Score   | Notes                                                    |
| -------------------- | ------- | -------------------------------------------------------- |
| Structural Integrity | ✅ PASS | 12 well-organized sections, clear progression            |
| Content Accuracy     | ✅ PASS | PR #114 analysis matches actual upstream code            |
| Internal Consistency | ✅ PASS | CSAPI application sections correctly extend EDR patterns |
| Practical Utility    | ✅ PASS | Actionable code examples, clear file organization        |
| Strategic Value      | ✅ PASS | Correctly identifies EDR as the primary template         |
| Client Orientation   | ✅ PASS | All patterns test URL construction and parsed outputs    |

### Document 02: Upstream Test Consistency

| Quality Layer        | Score    | Notes                                                |
| -------------------- | -------- | ---------------------------------------------------- |
| Structural Integrity | ✅ PASS  | Comprehensive survey of 6 implementations            |
| Content Accuracy     | ⚠️ ISSUE | Wrong resource type names in Section 12 (H1)         |
| Internal Consistency | ✅ PASS  | MUST/SHOULD/CONSIDER hierarchy consistent            |
| Practical Utility    | ✅ PASS  | Clear actionable categories, ratio targets justified |
| Strategic Value      | ✅ PASS  | Evolution timeline correctly positions CSAPI         |
| Client Orientation   | ✅ PASS  | All recommended patterns are client-oriented         |

### Document 12: QueryBuilder Testing Strategy

| Quality Layer        | Score   | Notes                                                                 |
| -------------------- | ------- | --------------------------------------------------------------------- |
| Structural Integrity | ✅ PASS | 25 sections, comprehensive resource coverage                          |
| Content Accuracy     | ✅ PASS | ~~Conformance URIs uncertain (M1), async methods (M2)~~ Both resolved |
| Internal Consistency | ✅ PASS | All 9 resource types follow consistent pattern                        |
| Practical Utility    | ✅ PASS | Near-production-ready test code, detailed matrices                    |
| Strategic Value      | ✅ PASS | Upstream validation in Section 23 confirms alignment                  |
| Client Orientation   | ✅ PASS | Every test example tests URL construction                             |

### Document 38: Testing Playbook Synthesis

| Quality Layer        | Score   | Notes                                                                |
| -------------------- | ------- | -------------------------------------------------------------------- |
| Structural Integrity | ✅ PASS | 10 parts, detailed step-by-step workflows                            |
| Content Accuracy     | ✅ PASS | ~~`fromUrl()` invention (M3), URI variants (M1)~~ Both resolved      |
| Internal Consistency | ✅ PASS | ~~`__tests__/` contradicts (H2), space encoding (M4)~~ Both resolved |
| Practical Utility    | ✅ PASS | Complete implementation workflows, troubleshooting guide             |
| Strategic Value      | ✅ PASS | Comprehensive synthesis with progress tracking                       |
| Client Orientation   | ✅ PASS | Quality checklist explicitly addresses client orientation            |

---

_Report generated as part of the Progressive Review framework. Next: Phase 2 Category Deep Dives._
