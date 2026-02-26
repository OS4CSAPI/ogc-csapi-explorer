# Issue #15 Findings Report — Add parseLocationHeader() utility for extracting resource IDs from 201 responses (F-12)

> **Date:** 2026-02-18
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#15](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/15) — "Add parseLocationHeader() utility for extracting resource IDs from 201 responses (F-12)"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/helpers.ts`)
> **Labels:** enhancement

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Analysis](#7-analysis)
8. [Recommendation](#8-recommendation)
9. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
10. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not propose behavioral modifications to the library without approval. All recommendations distinguish between **fact** (verified), **inference** (reasoned), and **proposal** (requires approval), per Section 3 of the constraints.

**Key constraint assessment for this issue:** Section 2.2 of the AI Operational Constraints states: _"Do not introduce new abstractions, layers, or dependencies without approval"_ and _"Preserve upstream structure, naming, and patterns unless explicitly instructed otherwise."_ Issue #15 proposes adding a **new public utility function** to `helpers.ts` and a **new export** from `src/index.ts`. While it does not modify any existing function or change any existing behavior, it expands the library's public API surface. This is a qualitatively different kind of change from a bug fix or a documentation improvement: it adds a new capability that upstream maintainers must review, accept responsibility for, and maintain indefinitely.

---

## 2. Executive Summary

**Issue #15 proposes adding a `parseLocationHeader()` utility function to `src/ogc-api/csapi/helpers.ts` for extracting resource type and ID from the `Location` header returned in HTTP 201 Created responses. After thorough review of the source code, 12 reference documents, and the finding's position in the priority framework, this report recommends DEFERRAL. The function is well-specified, small (~15 lines), and handles real edge cases, but it is the lowest-priority actionable finding (#10 of 11), the library is a URL builder rather than an HTTP response parser, the extraction is trivially self-implementable by consumers, there is no caller within the library itself, and adding it expands the public API surface with no corresponding reduction in existing consumer friction.**

| Aspect                           | Assessment                                                                                         |
| -------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Change type**                  | New public utility function + new barrel export                                                    |
| **Finding priority**             | **#10 of 11** in upstream-findings.md — Low severity, Low effort, "Should Address" category        |
| **Production behavior modified** | **None** — purely additive; no existing function is changed                                        |
| **Existing tests affected**      | **None** — no existing test needs modification                                                     |
| **Risk to library integrity**    | **Very low** — the function is self-contained with zero dependencies                               |
| **New abstraction introduced**   | **Yes** — new public function, new export from `src/index.ts`                                      |
| **Upstream pattern precedent**   | **None** — no upstream `ogc-client` handler includes response header parsing utilities             |
| **AI Constraints trigger**       | **Section 2.2 triggered** — introduces a new public function without approval; expands API surface |
| **Existing workaround**          | **Yes** — one-liner: `locationHeader.split('/').pop()`                                             |
| **Internal caller**              | **None** — the library has no code that would call this function                                   |

**Key findings from this review:**

1. **Fact:** F-12 is ranked **#10 out of 11** in the upstream-findings.md priority table — the lowest-priority actionable finding. Only F-5 (a pre-existing bug in `endpoint.ts` outside CSAPI scope) is ranked lower.

2. **Fact:** The upstream-findings.md itself describes F-12 as: _"Low priority — consumers can easily implement this themselves."_

3. **Fact:** The library-findings-gap-analysis.md describes the extraction as _"trivial"_ and provides the one-liner: `const id = locationHeader.split('/').pop();`

4. **Fact:** The library (`ogc-client`) is architecturally a **URL builder** — it constructs URLs and parses response envelopes, but does not make HTTP requests or parse HTTP headers. `parseLocationHeader()` operates on an HTTP response header, placing it outside the library's established architectural boundary.

5. **Fact:** There are **zero callers** within the library source that would use `parseLocationHeader()`. The function would exist solely for external consumers. By contrast, every existing function in `helpers.ts` (`formatDateTimeParameter()`, `validateLimit()`, `validateBbox()`, `scanCsapiLinks()`, `encodeResourceId()`, `isValidResourceType()`, `assertValidResourceType()`) is called internally by `CSAPIQueryBuilder` or its test suite.

6. **Fact:** Only **1 commit** (`e73cff8`) has ever modified library source (`src/`) during the entire demo app development lifecycle. All other accommodations — including the Location header parsing needed in the demo — were implemented as demo-layer workarounds. This establishes a strong precedent of extreme conservatism toward library modifications.

7. **Fact:** The demo app's bridge module already implements Location header parsing with a one-liner in `api.ts`, confirming the workaround is trivial.

8. **Fact:** Finding #8 in the [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md) documents this as _"Informational — useful pattern"_ and notes the server behavior, but does not identify this as a library deficiency.

9. **Inference:** While the proposed function is described as "complementary" to `encodeResourceId()`, the symmetry is imprecise. `encodeResourceId()` is called internally by `buildResourceUrl()` during URL construction — it is part of the library's core URL-building pipeline. `parseLocationHeader()` would have no internal caller and serves a fundamentally different purpose (response parsing vs. request construction).

10. **Inference:** Adding a new public function and barrel export increases the maintenance surface for upstream maintainers. Even a small, well-specified function creates a commitment: backward compatibility, documentation upkeep, potential for interaction with future changes, and review overhead for the upstream PR. In the context of a contribution that already spans 10,222 lines across 24 implementation files, minimizing non-essential additions strengthens the submission.

---

## 3. Issue Description

Issue #15 ([OS4CSAPI/ogc-csapi-explorer#15](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/15)) identifies that when resources are created via POST requests, OGC API servers return HTTP `201 Created` with an empty response body and a `Location` header containing the URL of the created resource:

```
HTTP/1.1 201 Created
Location: /sensorhub/api/systems/043g
Content-Length: 0
```

The issue proposes adding a `parseLocationHeader()` utility function with the following signature:

```typescript
export function parseLocationHeader(
  header: string | null
): { resourceType: string; id: string } | null;
```

The function would:

- Extract the last path segment as the resource ID
- Extract the second-to-last path segment as the resource type
- Handle edge cases: trailing slashes, query parameters, URI encoding, empty/null headers, absolute URLs
- Return `null` for empty, null, or unparseable input

The proposed placement is in `src/ogc-api/csapi/helpers.ts` alongside existing utilities, with export via `src/index.ts`.

### Edge Cases Documented in Issue

| Input                                  | Expected Output                                                     |
| -------------------------------------- | ------------------------------------------------------------------- |
| `/api/systems/043g`                    | `{ resourceType: 'systems', id: '043g' }`                           |
| `/api/systems/043g/`                   | `{ resourceType: 'systems', id: '043g' }` (trailing slash stripped) |
| `/api/systems/043g?f=json`             | `{ resourceType: 'systems', id: '043g' }` (query stripped)          |
| `https://example.com/api/systems/043g` | `{ resourceType: 'systems', id: '043g' }` (absolute URL handled)    |
| `''` or `null`                         | `null`                                                              |
| `/api`                                 | `null` (insufficient segments)                                      |

### Standards References in Issue

- **RFC 7231 §7.1.2** — The `Location` header field definition
- **OGC API Common Part 1** (OGC 19-072) — General HTTP semantics for OGC APIs
- **OGC Connected Systems API** (OGC 23-002r1) — CSAPI-specific resource creation patterns

---

## 4. Source Code Review

### 4.1 Target File: `src/ogc-api/csapi/helpers.ts` (223 lines)

The file contains 7 exported functions organized into 5 sections:

| Section                  | Function                    | Lines   | Internal Caller                                  |
| ------------------------ | --------------------------- | ------- | ------------------------------------------------ |
| Temporal Encoding        | `formatDateTimeParameter()` | 28–50   | `CSAPIQueryBuilder.buildQueryString()`           |
| Resource Type Validation | `isValidResourceType()`     | 61–63   | `assertValidResourceType()`, `CSAPIQueryBuilder` |
| Resource Type Validation | `assertValidResourceType()` | 71–78   | `CSAPIQueryBuilder` constructor                  |
| URL Encoding             | `encodeResourceId()`        | 97–99   | `CSAPIQueryBuilder.buildResourceUrl()`           |
| Link Scanning            | `scanCsapiLinks()`          | 123–166 | `CSAPIQueryBuilder` constructor                  |
| Parameter Validation     | `validateLimit()`           | 178–183 | `CSAPIQueryBuilder.buildQueryString()`           |
| Parameter Validation     | `validateBbox()`            | 196–218 | `CSAPIQueryBuilder.buildQueryString()`           |

**Observation:** Every function in `helpers.ts` is called by `CSAPIQueryBuilder` or its directly supporting code. The file serves as a utility module for the URL builder, not as a general-purpose consumer toolkit. Adding `parseLocationHeader()` would be the first function in this file with **zero internal callers**.

The file ends with a comment: `// (End of module — feature-level validators removed per Issue #52)` — indicating that content has been deliberately **removed** from this file in the past to maintain scope discipline. Adding a new function would go against this trajectory.

### 4.2 Proposed Complementary Function: `encodeResourceId()` (Line 97)

The issue describes `parseLocationHeader()` as "complementary" to `encodeResourceId()`:

```typescript
export function encodeResourceId(id: string): string {
  return encodeURIComponent(id);
}
```

The symmetry argument: `encodeResourceId()` encodes IDs for URL construction; `parseLocationHeader()` would decode IDs from URL paths (the reverse operation).

**Assessment:** The symmetry is conceptually appealing but architecturally imprecise:

- `encodeResourceId()` is a single-line wrapper around `encodeURIComponent` called internally by `buildResourceUrl()` during URL construction — it is part of the core pipeline.
- `parseLocationHeader()` would be a ~15-line function with URL parsing, query stripping, trailing slash handling, and segment extraction — a meaningfully more complex function with no internal caller.
- The "complementary" frame is **encode for outbound / decode for inbound**, but the library's architectural boundary is outbound (URL construction), not inbound (response parsing).

### 4.3 Public API Surface: `src/index.ts`

The CSAPI exports from `src/index.ts` currently include:

- `CSAPIQueryBuilder` (the URL builder class)
- `CSAPIResourceTypes`, `CSAPIResourceType` (resource type constants)
- 16+ type exports (query options, resource interfaces, format types)
- `extractCSAPIFeature`, `getCSAPIResourceType`, `isCSAPIFeature` (GeoJSON feature utilities)
- `parseCollectionResponse` (response envelope normalizer)
- `parseSWEComponent`, `validateAgainstSchema` (SWE Common utilities)

The issue proposes adding `parseLocationHeader` to this export list. This would be the first export of a standalone utility function from `helpers.ts` — all other `helpers.ts` functions are consumed internally and not individually exported from the barrel.

### 4.4 Test File: `src/ogc-api/csapi/helpers.spec.ts`

Tests exist for all current functions in `helpers.ts`. Adding `parseLocationHeader()` would require a corresponding test section (~20–30 lines covering the 6 edge cases documented in the issue). The test burden is small.

---

## 5. Reference Document Review

### 5.1 upstream-findings.md — Priority Ranking

F-12 appears in the priority table as:

| Priority | Finding                                  | Severity | Effort | Category       |
| -------- | ---------------------------------------- | -------- | ------ | -------------- |
| #10      | F-12 — No Location Header Parsing Helper | Low      | Low    | Should Address |

This is the **lowest-priority actionable finding**. Only F-5 (pre-existing bug in `endpoint.ts` line 74, outside CSAPI scope) is ranked lower at #11.

The finding description states: _"Consider a `parseLocationHeader(header: string): { resourceType: string, id: string }` utility. Low priority — consumers can easily implement this themselves."_

### 5.2 library-findings-gap-analysis.md — Actionability Assessment

F-12 in the gap analysis:

| Finding | Has GitHub Issue? | Actionable?            | Effort | Priority |
| ------- | ----------------- | ---------------------- | ------ | -------- |
| F-12    | Not yet           | Yes — utility function | Low    | 6 (Low)  |

The detailed breakdown states:

- _"The extraction is trivial:"_ followed by the one-liner `const id = locationHeader.split('/').pop();`
- _"However, a proper helper would: Handle trailing slashes, Handle query parameters, Extract both the resource type and ID, Handle edge cases (empty header, malformed URL)"_
- _"The demo app's bridge module in `api.ts` does its own Location header parsing with a one-liner."_
- _"Consider a `parseLocationHeader(...)` utility, but this is low priority since consumers can easily implement it themselves."_

### 5.3 e2e-write-operations-report.md — Finding #8 (Origin of F-12)

This is where the finding was first documented during live E2E testing:

> **Finding #8: Server Response Exposes Resource IDs via Location Header**
>
> - **Severity:** Informational — useful pattern
> - **Type:** Server behavior documentation
>
> On successful creation (201), the OSH SensorHub returns:
>
> - Empty response body (no JSON content)
> - `Location` header with the path to the created resource (e.g., `/systems/043g`)
> - Resource ID can be extracted from the last path segment
>
> This is standard OGC API behavior, but the library provides no helper for extracting IDs from Location headers. Consumers must implement this themselves.

**Note:** The finding is classified as _"Informational — useful pattern"_ and _"Server behavior documentation"_, not as a library deficiency or gap.

### 5.4 crud-smoke-test-findings.md — F-15 (Related 201 Response Issue)

F-15 documents a more critical related issue: the demo app crashing when parsing 201 responses with empty bodies. F-15 is rated **High severity** and was worked around in the demo layer.

Relevance to Issue #15: F-15's recommendation item 3 states: _"For 201 responses, extract the resource ID from the `Location` header (see also #15 — parseLocationHeader())"_. However, this cross-reference acknowledges that `parseLocationHeader()` is a complementary convenience, not a prerequisite for the F-15 fix.

### 5.5 library-source-changes-audit.md — Library Modification Precedent

The audit confirms: **exactly one commit** (`e73cff8`) modified library source during the entire demo app lifecycle. All other workarounds — including Location header parsing — were implemented in the demo layer (`demo/src/`).

The audit's workaround table does not include Location header parsing as a separate entry, suggesting the operation was trivially absorbed into existing response handling code.

### 5.6 contribution-goal-accuracy-assessment.md — Library Architecture

The assessment repeatedly characterizes the library as a "URL builder":

- _"The library is a **URL builder**, not an HTTP client — it does not perform fetch operations, manage authentication, or handle response deserialization end-to-end"_
- _"Content negotiation guidance exists via constants and the `f` query parameter, but HTTP-level `Accept` header management is outside the library's scope as a URL builder."_

This establishes a clear architectural boundary. `parseLocationHeader()` operates on an HTTP response header — a domain explicitly described as outside the library's scope.

### 5.7 library-integration-report.md — Bridge Architecture

The integration report documents how the demo uses the library and where workarounds were applied. Location header parsing is not discussed as a significant finding — it was incorporated into the demo's response handling without comment.

### 5.8 AI Operational Constraints — Section 2.2

> _"Do not introduce new abstractions, layers, or dependencies without approval."_ > _"Preserve upstream structure, naming, and patterns unless explicitly instructed otherwise."_ > _"Prefer minimal diffs over idealized rewrites."_

While `parseLocationHeader()` is a small addition, it is a **new public function** that crosses the library's architectural boundary (URL building → response parsing). The constraints favor minimal changes.

---

## 6. Risk Assessment

### 6.1 Technical Risk: Very Low

The proposed function is self-contained, stateless, and has zero dependencies:

- No imports required (pure string manipulation)
- No interaction with any existing function
- No modification to any existing behavior
- No side effects

If implemented correctly, the function cannot break anything. The risk of introducing a bug in the function itself is minimal given the well-defined edge cases.

### 6.2 Architectural Risk: Low but Non-Zero

The function crosses an established boundary:

- Every existing `helpers.ts` function serves the URL builder's construction pipeline
- `parseLocationHeader()` would serve the response parsing pipeline, which the library explicitly does not own
- This sets a precedent: future contributors might add more response parsing helpers (e.g., `parseErrorResponse()`, `extractPaginationLinks()`, `parseETag()`), gradually expanding the library beyond its URL builder scope

### 6.3 Contribution Risk: Low but Relevant

In the context of the upstream PR:

- The CSAPI contribution is already large (10,222 implementation lines, 11,548 test lines, 24 implementation files)
- Every additional function increases the review surface for upstream maintainers
- Upstream `ogc-client` has **no precedent** for response header parsing utilities in any handler (WMS, WFS, WMTS, TMS, EDR, STAC)
- The function would be unique across the entire library — no other handler offers anything similar

### 6.4 Risk Summary

| Risk Category         | Level    | Rationale                                                           |
| --------------------- | -------- | ------------------------------------------------------------------- |
| Technical correctness | Very Low | Self-contained, no side effects, well-defined behavior              |
| Regression potential  | None     | No existing code modified                                           |
| Architectural drift   | Low      | Crosses URL builder boundary, sets response parsing precedent       |
| Upstream acceptance   | Moderate | No precedent in any other handler; may prompt questions about scope |
| Maintenance burden    | Very Low | ~15 lines of code, well-tested, unlikely to require future changes  |

---

## 7. Analysis

### 7.1 Arguments FOR Implementation

1. **Small and well-specified:** ~15 lines of code with clear edge case handling based on RFC 7231 and OGC conventions.

2. **Handles real edge cases:** The proper implementation handles trailing slashes, query parameters, URI encoding, and absolute URLs — subtleties that a consumer's one-liner would miss.

3. **Architectural complement to `encodeResourceId()`:** `encode` for outbound URL construction, `parse/decode` for inbound response processing — a natural symmetry.

4. **Low implementation risk:** Zero dependencies, zero interaction with existing code, no behavior change to any existing function.

5. **Standards-backed:** RFC 7231 §7.1.2 defines the `Location` header. OGC API Common Part 1 (19-072) standardizes its use in resource creation responses. The function has a clear specification basis.

### 7.2 Arguments AGAINST Implementation

1. **Lowest priority actionable finding:** F-12 is #10 of 11 in the priority ranking. The upstream-findings.md, library-findings-gap-analysis.md, and e2e-write-operations-report.md all describe it as low priority.

2. **Trivially self-implementable:** The gap analysis provides the one-liner: `const id = locationHeader.split('/').pop()`. Any consumer sophisticated enough to perform HTTP POST operations can parse a URL path segment.

3. **No internal caller:** Every other function in `helpers.ts` is called by `CSAPIQueryBuilder`. This function would exist solely for external consumers, making it architecturally orphaned within the module.

4. **Crosses the library's architectural boundary:** The library is explicitly described as a "URL builder, not an HTTP client." It _constructs_ requests but does not _parse_ responses at the HTTP header level. `parseCollectionResponse()` parses response _bodies_ (JSON), which is different from parsing HTTP headers.

5. **No upstream precedent:** No other `ogc-client` handler (WMS, WFS, WMTS, TMS, EDR, STAC) includes response header parsing utilities. Adding one to CSAPI would make it architecturally unique across the library.

6. **Expands public API surface:** Adding a new export to `src/index.ts` increases the commitment upstream maintainers take on. Every public function is a backward-compatibility promise.

7. **Precedent concern:** If `parseLocationHeader()` is added, the same logic could justify `parseErrorResponse()`, `extractContentType()`, `parseETagHeader()`, and other response-parsing utilities. The boundary between "URL builder" and "HTTP utility library" would become ambiguous.

8. **Demo workaround was trivial:** The demo app's Location header parsing was absorbed into existing response handling code without requiring a separate function, helper, or module — confirming the consumer-side burden is minimal.

9. **Conservation precedent:** Only 1 commit has ever modified library source during demo development. All other accommodations were demo-layer workarounds. Adding a new function for a Low-priority finding (when higher-priority findings were deferred to documentation) breaks this conservative pattern.

### 7.3 The Symmetry Argument Examined

The issue's strongest argument is the `encodeResourceId()` / `parseLocationHeader()` symmetry. This deserves specific analysis:

| Dimension          | `encodeResourceId()`                     | `parseLocationHeader()`                  |
| ------------------ | ---------------------------------------- | ---------------------------------------- |
| Internal caller    | `buildResourceUrl()` (L224–245)          | None                                     |
| Architectural role | Core URL construction pipeline           | Response parsing (outside library scope) |
| Complexity         | 1 line (`encodeURIComponent`)            | ~15 lines (URL parsing, edge cases)      |
| Upstream precedent | URL encoding is standard in URL builders | No response parsing precedent            |
| Consumer need      | Invisible — called internally            | Consumer must know to call it            |

The symmetry is conceptual ("encode ↔ decode") but the architectural roles are asymmetric. `encodeResourceId()` is infrastructure for the library's core function; `parseLocationHeader()` would be a consumer convenience unrelated to URL building.

### 7.4 Comparison with Prior Findings Reports

| Finding                    | Priority | Recommendation        | Rationale                                                              |
| -------------------------- | -------- | --------------------- | ---------------------------------------------------------------------- |
| F-1 (wrong URL)            | #1       | Fix                   | URL construction bug — core library function                           |
| F-2 (missing methods)      | #2       | Fix                   | API completeness gap — core library function                           |
| F-10 (content-type map)    | #3       | Add helper            | Directly supports CRUD workflow — every consumer needs it              |
| F-11 (resource discovery)  | #5       | **Defer** (Issue #14) | Behavioral change to `assertResourceAvailable()` — too risky           |
| F-5 (pre-existing bug)     | #11      | **Defer** (Issue #10) | Outside CSAPI scope — pre-existing bug                                 |
| **F-12 (Location header)** | **#10**  | **?**                 | Convenience utility — no internal caller, trivially self-implementable |

Issue #14 (F-11, priority #5) was recommended for deferral because it would change the behavioral contract of `assertResourceAvailable()`. Issue #10 (F-5, priority #11) was also deferred. F-12 at priority #10 is lower priority than the deferred F-11 and only marginally higher than the deferred F-5.

---

## 8. Recommendation

### Primary Recommendation: DEFER

**Do not implement `parseLocationHeader()` as part of the upstream CSAPI contribution.**

**Rationale:**

1. F-12 is the lowest-priority actionable finding (#10 of 11) — lower than findings that were already recommended for deferral (F-11 at #5, deferred in Issue #14).

2. The function has no internal caller and crosses the library's established architectural boundary (URL builder → response parser).

3. The extraction is trivially self-implementable by any consumer performing HTTP POST operations.

4. No upstream `ogc-client` handler includes response header parsing utilities — adding one would make CSAPI architecturally unique.

5. The conservation precedent (1 library-source commit in the entire demo lifecycle) favors not introducing non-essential additions.

6. Every additional function in the upstream PR is a review surface increase and a backward-compatibility commitment for maintainers.

### If Implementation Is Desired Despite Deferral Recommendation

If the project lead determines that the function should be added regardless, the following guidance applies:

**Placement:** `src/ogc-api/csapi/helpers.ts`, after `encodeResourceId()` (maintaining the URL Encoding section theme).

**Signature:** Per the issue:

```typescript
export function parseLocationHeader(
  header: string | null
): { resourceType: string; id: string } | null;
```

**Edge cases:** Per the issue's table (trailing slashes, query params, URI encoding, absolute URLs, empty/null input, insufficient path segments).

**Export:** Add to `src/index.ts` CSAPI exports block.

**Tests:** Add 6+ test cases to `helpers.spec.ts` covering the documented edge cases.

**JSDoc:** Include `@see` references to RFC 7231 §7.1.2 and OGC API Common Part 1 (19-072), plus a note that this is a consumer convenience utility the library does not use internally.

**Risk:** Very low — the function is self-contained and cannot affect existing behavior.

### Alternative: Document the Pattern Instead

If the goal is to help consumers handle 201 responses, consider adding a JSDoc `@example` block to the Issue #6 content-type helper (when implemented) or to the `createSystem()` method, showing the one-liner extraction pattern:

```typescript
/**
 * @example
 * // After POST with the URL from createSystem():
 * const locationHeader = response.headers.get('Location');
 * const resourceId = locationHeader?.split('/').pop();
 */
```

This achieves discoverability without adding a new function or export.

---

## Appendix A: Authority Precedence Analysis

| Authority Level               | Source                                               | What It Says About F-12                                                                                                   |
| ----------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1. OGC Specs                  | RFC 7231 §7.1.2, OGC API Common Part 1, OGC 23-002r1 | `Location` header is standard on 201 Created. No guidance on client-side parsing utilities.                               |
| 2. AI Collaboration Agreement | Section 2.2                                          | _"Do not introduce new abstractions, layers, or dependencies without approval."_ A new public function requires approval. |
| 3. Issue Description          | Issue #15                                            | Proposes `parseLocationHeader()` in `helpers.ts` with export. Acknowledges "Low" priority.                                |
| 4. Existing Code Patterns     | `helpers.ts` functions                               | Every function has an internal caller. No response-parsing functions exist.                                               |
| 5. Conversation Context       | User emphasis on conservatism                        | _"I am very reluctant to make changes that could degrade the integrity of our CSAPI client library contribution work."_   |

**Conclusion:** Authorities 2, 4, and 5 all favor deferral. Authority 1 is neutral. Authority 3 supports implementation but self-identifies as low priority.

---

## Appendix B: Cross-Reference Matrix

| Reference Document                                                                                                                                             | Finding/Section                       | Relevance to Issue #15                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | F-12, Priority #10                    | Source finding — lowest priority actionable item                                                                                                       |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | F-12 detailed breakdown               | _"The extraction is trivial"_; provides one-liner; priority 6 (Low)                                                                                    |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | Finding #8                            | Origin of F-12 — classified as _"Informational"_                                                                                                       |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | F-15 recommendation item 3            | Cross-references Issue #15 as "complementary"                                                                                                          |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | Executive Summary, Workaround Table   | 1 library commit; Location parsing not listed as a separate workaround                                                                                 |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Library architecture characterization | _"URL builder, not an HTTP client"_ — establishes scope boundary                                                                                       |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | Findings #1–#16                       | Location header parsing not flagged as significant; absorbed into demo response handling                                                               |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | Lesson #1: Module Boundary Discipline | _"Every new module we add should be checked for transitive dependencies that reach outside the JSON/HTTP stack."_ Reinforces architectural discipline. |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | Section 2.2                           | _"Do not introduce new abstractions... without approval"_ — triggered by new function                                                                  |
| [csapi-implementation-guide.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/csapi-implementation-guide.md)                          | Library scope definition              | URL builder scope; response parsing is consumer responsibility                                                                                         |
| [ROADMAP.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/ROADMAP.md)                                                                | Phase scope                           | No phase includes response header parsing utilities                                                                                                    |

---

_This report was generated by analyzing Issue #15, 12 reference documents, the full source of `helpers.ts` (223 lines), and the `src/index.ts` export surface. No code changes were made. Recommendation: defer implementation; alternatively, document the one-liner pattern in JSDoc._
