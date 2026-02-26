# Issue #110 Findings Report — No `@link` / `@id` Resolution Utilities for Cross-Resource Reference Following

> **Date:** 2026-02-21
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#110](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) — "No `@link` / `@id` resolution utilities for cross-resource reference following"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/`)
> **Discovered by:** [ogc-csapi-explorer `tryLinkFallback()` workaround](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52), [Gap Analysis Report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/csapi-link-property-gap-analysis.md) > **Labels:** enhancement

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Scope Boundary Analysis](#5-scope-boundary-analysis)
6. [Upstream Architectural Pattern Review](#6-upstream-architectural-pattern-review)
7. [Risk Assessment](#7-risk-assessment)
8. [Recommendation](#8-recommendation)
9. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
10. [Appendix B: Detailed Utility-by-Utility Assessment](#appendix-b-detailed-utility-by-utility-assessment)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (OGC 23-001/23-002) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report applies the following constraints with particular care:

- **§2.1 — Do not infer unstated requirements or expand scope.** The ROADMAP and Implementation Guide do not define `@link` resolution utilities as a deliverable. This report does not presume they should be added.
- **§2.2 — Do not introduce new abstractions, layers, or dependencies without approval.** The proposed utilities in Issue #110 would constitute a new architectural layer (fetch-level resolution on top of the existing URL builder and parser layers). This requires careful justification.
- **§2.2 — Preserve upstream structure, naming, and patterns.** Any change must align with how the upstream ogc-client library handles similar concerns.
- **§2.3 — Do not refactor for style, clarity, or "best practice" unless explicitly requested.** This report does not propose "improving" existing code.

---

## 2. Executive Summary

**Issue #110 identifies a real consumer pain point — the library parses `@link` data into typed fields (Issues #108/#109, resolved) and builds server-side navigation URLs (`CSAPIQueryBuilder`), but provides no utilities for resolving `@link` references by fetching the target resource. However, the proposed fix represents new functionality that falls outside the defined contribution scope and introduces significant architectural and risk concerns.**

**Recommendation: DO NOT IMPLEMENT at this time.** The issue should remain open as a documented enhancement for future consideration, but no code changes should be made to the CSAPI client library contribution.

| Finding     | Description                                                                                  | Severity               | Recommendation                                                                             |
| ----------- | -------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------ |
| **F-110.1** | No `@link` resolution utilities exist in the library                                         | **CONFIRMED GAP**      | Acknowledged — but not in contribution scope                                               |
| **F-110.2** | The gap is a **consumer convenience concern**, not a spec-conformance gap                    | **LOW**                | Library correctly parses and exposes `@link` data; resolution is consumer responsibility   |
| **F-110.3** | ROADMAP defines no task for `@link` resolution utilities                                     | **SCOPE BOUNDARY**     | Adding unplanned functionality violates §2.1                                               |
| **F-110.4** | Implementation Guide mentions "reference resolution" only for SensorML parser internals      | **NOT APPLICABLE**     | Not a standalone utility; different concern entirely                                       |
| **F-110.5** | The upstream library has no precedent for resolving inline `@link`-style property references | **ARCHITECTURAL RISK** | Existing `fetchLink()` operates on HATEOAS `links[]` arrays, not inline `@link` properties |
| **F-110.6** | Proposed `resolveResourceRef()` introduces `fetch()` calls into the CSAPI module             | **ARCHITECTURAL RISK** | CSAPI module currently has zero direct fetch calls; this would break the layering          |
| **F-110.7** | `resolveWithLinkFallback()` requires knowledge of both navigation URLs and `@link` refs      | **COMPLEXITY RISK**    | Couples URL builder concerns with parser output; increases surface area significantly      |
| **F-110.8** | `CSAPIResourceRef` type is already exported; consumers have everything needed                | **SUFFICIENT**         | Typed `@link` fields + exported type = consumers can build their own resolution            |
| **F-110.9** | The ogc-csapi-explorer workaround (`tryLinkFallback()`) is application-specific              | **CONTEXT**            | Different apps need different error handling, auth, caching — library shouldn't prescribe  |

**Bottom line:** Issues #108 and #109 delivered the foundational capability — `@link` data is parsed, typed, and accessible. The library's job is to **parse and expose** the data faithfully, which it now does. Resolution (fetching resources from `@link` hrefs) is inherently application-specific and belongs in consuming applications, not in a parsing/URL-building library.

---

## 3. Issue Description

Issue #110 requests four new utility functions for `@link` / `@id` cross-reference resolution:

| Proposed Utility            | Purpose                                          | Category            |
| --------------------------- | ------------------------------------------------ | ------------------- |
| `resolveResourceRef()`      | Fetch a resource from a `CSAPIResourceRef.href`  | **HTTP fetch**      |
| `parseResourceRefHref()`    | Extract resource type and ID from an href string | **URL parsing**     |
| `extractCrossReferences()`  | Collect all `@link`/`@id` fields from raw JSON   | **Data extraction** |
| `resolveWithLinkFallback()` | Try navigation endpoint, fall back to `@link`    | **Orchestration**   |

The issue was discovered by the [ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer) project, which had to implement a `tryLinkFallback()` function (~105 lines) because the library didn't expose `@link` data at all. That root cause has now been resolved by #108 (interfaces) and #109 (parser extraction).

---

## 4. Source Code Review

### 4.1 What the Library Provides Today (Post #108/#109)

| Layer                 | Component                                                                     | Status                | What It Does                                                                |
| --------------------- | ----------------------------------------------------------------------------- | --------------------- | --------------------------------------------------------------------------- |
| **Types**             | `CSAPIResourceRef` in `model.ts` L117–127                                     | Exported              | Typed interface for `@link` objects: `{ href, uid?, title?, rt? }`          |
| **Part 1 interfaces** | `systemKindLink`, `platformLink`, `deployedSystemsLink`, `sampledFeatureLink` | Complete              | Optional `CSAPIResourceRef` fields on System, Deployment, SamplingFeature   |
| **Part 1 parser**     | `extractCSAPIFeature()` in `geojson.ts`                                       | Complete              | Extracts all 4 `@link` fields into typed interface fields                   |
| **Part 2 parsers**    | `parseDatastream()`, `parseControlStream()`, etc. in `part2.ts`               | Complete (`@id` only) | Extracts all `@id` scalar cross-references (e.g., `system@id` → `systemId`) |
| **URL builder**       | `CSAPIQueryBuilder` in `url_builder.ts`                                       | Complete (68 methods) | Builds URLs for all server-side navigation endpoints                        |
| **HATEOAS scanner**   | `scanCsapiLinks()` in `helpers.ts`                                            | Complete              | Scans document-level HATEOAS `links[]` for resource type navigation         |

### 4.2 What the Library Does NOT Provide

| Missing Capability                      | Issue #110 Proposal         | Currently a Gap?                                    |
| --------------------------------------- | --------------------------- | --------------------------------------------------- |
| Fetch a resource from `@link.href`      | `resolveResourceRef()`      | Consumer responsibility — data is exposed           |
| Parse resource type/ID from href        | `parseResourceRefHref()`    | Consumer responsibility — href is a plain string    |
| Collect all `@link`/`@id` from raw JSON | `extractCrossReferences()`  | Partially redundant — typed parsers already do this |
| Navigation-then-fallback orchestration  | `resolveWithLinkFallback()` | Consumer responsibility — application-specific      |

### 4.3 Private Helpers — Already Present But Not Exported

Two private helper functions exist in `geojson.ts` (added in #109):

- **`isCSAPIResourceRef()`** — Type guard for `@link` objects
- **`parseResourceRef()`** — Parses raw `@link` object into `CSAPIResourceRef`

These are private to the parser module. The question of whether to export them is separate from the resolution utilities proposed in #110.

---

## 5. Scope Boundary Analysis

### 5.1 Contribution Goal (contribution-goal-and-definition.md)

The contribution scope defines:

> **Format Support:** "GeoJSON extensions recognizing all CSAPI-specific resource types **and properties**"

This is satisfied by #108 (interfaces) and #109 (parser extraction). The contribution goal says "recognizing" — parsing and exposing — not "resolving" or "fetching" referenced resources.

> **Core Integration:** "Single QueryBuilder class with 80 methods covering all 9 CSAPI resource types"

The `CSAPIQueryBuilder` provides URL construction for server-side navigation. The contribution goal does not mention `@link` resolution utilities, fallback orchestration, or fetch-level functionality.

### 5.2 ROADMAP

The ROADMAP (795 lines, 4 phases + Phase 5 parser completion) contains:

- **One mention of `@link`** — Phase 3 Task 1 (GeoJSON Handler Extensions): "Extract CSAPI-specific properties (uid, featureType, assetType, validTime, **@link associations**, etc.)." This is about **parsing**, which is now complete.
- **No task** for `@link` resolution utilities, link-following, `resolveResourceRef`, or fallback orchestration.
- **No phase** dedicated to or containing fetch-level cross-reference resolution.

### 5.3 Implementation Guide

The Implementation Guide (4,715 lines) mentions "reference resolution" once:

> "**Reference resolution**: External link dereferencing for procedures, datasheets, feature definitions"

This appears in the SensorML Handler section under "Parsing Capabilities" — it describes a future parser internal for dereferencing `xlink:href` in SensorML XML documents. It is not a standalone utility and addresses a different concern entirely (`xlink:href` in XML vs `@link` in JSON).

### 5.4 AI Operational Constraints Assessment

| Constraint                                         | Applies? | Analysis                                                                                                                |
| -------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------- |
| §2.1 — Do not infer unstated requirements          | **YES**  | No ROADMAP task, no Guide section, no contribution goal statement defines `@link` resolution utilities as a deliverable |
| §2.1 — Do not expand scope beyond issue            | **YES**  | Even if Issue #110 is accepted, the utilities themselves have never been part of the contribution scope                 |
| §2.2 — Do not introduce new abstractions or layers | **YES**  | The proposed utilities create a new "resolution layer" between parsing and consumption                                  |
| §2.2 — Do not introduce new dependencies           | **YES**  | `resolveResourceRef()` and `resolveWithLinkFallback()` introduce fetch calls into the CSAPI module                      |
| §2.2 — Preserve upstream patterns                  | **YES**  | The upstream library's CSAPI module contains zero fetch calls; adding them changes the module's character               |

---

## 6. Upstream Architectural Pattern Review

### 6.1 How the Upstream Library Handles Link Resolution

The upstream ogc-client library has a clear architectural pattern for link resolution:

| Module                          | Link Resolution Approach                                                                | Fetch Calls?               |
| ------------------------------- | --------------------------------------------------------------------------------------- | -------------------------- |
| **`src/ogc-api/link-utils.ts`** | `fetchLink()`, `fetchDocument()`, `getLinkUrl()` — operates on HATEOAS `links[]` arrays | Yes — uses `sharedFetch()` |
| **`src/stac/link-utils.ts`**    | `fetchLink()` — same pattern adapted for STAC                                           | Yes — uses `sharedFetch()` |
| **`src/ogc-api/endpoint.ts`**   | Orchestrates `fetchLink()` calls for document navigation                                | Yes — through link-utils   |
| **`src/ogc-api/csapi/`**        | `CSAPIQueryBuilder` builds URLs; parsers parse JSON; helpers scan links                 | **No fetch calls**         |

**Critical observation:** The CSAPI module (`src/ogc-api/csapi/`) is a **parse-and-build** module. It parses incoming JSON into typed objects and builds outgoing URL strings. It never fetches. The fetch calls happen at the `endpoint.ts` level (one tier up).

Adding `resolveResourceRef()` or `resolveWithLinkFallback()` to the CSAPI module would break this layering by introducing fetch-level responsibilities into a parse-and-build layer.

### 6.2 What `fetchLink()` Actually Does vs What #110 Proposes

| Aspect    | Upstream `fetchLink()`                                                  | Proposed `resolveResourceRef()`                                    |
| --------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Input     | OGC API document containing `links[]` array                             | `CSAPIResourceRef` object with `href` string                       |
| Link type | HATEOAS rel-typed links (`{ rel, href, type }`)                         | Inline `@link` property references (`{ href, uid?, title?, rt? }`) |
| Purpose   | Navigate between OGC API documents (conformance, collections, tilesets) | Resolve inline cross-references to fetch associated resources      |
| Location  | `src/ogc-api/link-utils.ts` (shared utility)                            | Proposed: `src/ogc-api/csapi/link-resolution.ts` (CSAPI-specific)  |
| Precedent | Used ~10 times in `endpoint.ts`                                         | No existing usage anywhere                                         |

The upstream `fetchLink()` operates on document-level HATEOAS navigation — a fundamentally different concern from resolving inline `@link` properties within parsed CSAPI resources.

---

## 7. Risk Assessment

### 7.1 Risks of Implementing

| Risk                              | Severity   | Description                                                                                               |
| --------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------- |
| **Scope expansion**               | **HIGH**   | Adds unplanned functionality not in ROADMAP, Guide, or contribution goal                                  |
| **Architectural layer violation** | **HIGH**   | Introduces fetch calls into the CSAPI parse-and-build module                                              |
| **Test surface explosion**        | **MEDIUM** | Each fetch-based utility needs network mocking, error handling, timeout testing                           |
| **API surface growth**            | **MEDIUM** | 4 new exported functions + new file = significant new public API to maintain                              |
| **Application-specific concerns** | **MEDIUM** | Error handling, auth headers, retry logic, caching — apps differ; library can't prescribe                 |
| **Premature abstraction**         | **MEDIUM** | Only one consumer (ogc-csapi-explorer) has encountered this; pattern isn't validated across multiple apps |
| **Contribution integrity**        | **HIGH**   | Adding unscoped work risks introducing defects into a well-tested, stable codebase                        |

### 7.2 Risks of NOT Implementing

| Risk                          | Severity | Description                                                                                                                                           |
| ----------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Consumer boilerplate**      | **LOW**  | Consumers write ~10–20 lines to fetch from a `CSAPIResourceRef.href` — trivial with typed data available                                              |
| **Discovery gap**             | **LOW**  | Without a library function, consumers must know to read `@link` fields — but `CSAPIResourceRef` type is exported and fields are documented with JSDoc |
| **No fallback orchestration** | **LOW**  | Consumers implement their own try-navigation-then-fallback — but this is application-specific by nature                                               |

### 7.3 What #108/#109 Already Solved

The root cause of the ogc-csapi-explorer's pain was that `@link` data was **invisible** — silently dropped during parsing, with no interface fields to hold it. That is now fully resolved:

1. **Before #108/#109:** Consumers had to bypass the library entirely, reading raw JSON to access `@link` data. The `tryLinkFallback()` workaround existed because the library threw away the data.

2. **After #108/#109:** Consumers get typed `CSAPIResourceRef` objects on every parsed Part 1 resource. A consumer resolving an `@link` reference is now trivial:

```typescript
// After #108/#109 — consumer code is straightforward
const system = extractCSAPIFeature(rawJson) as System;
if (system.properties.systemKindLink) {
  const procedureUrl = system.properties.systemKindLink.href;
  const response = await fetch(procedureUrl);
  const procedure = await response.json();
}
```

The 105-line `tryLinkFallback()` workaround was primarily needed because the library didn't expose `@link` data at all. With typed fields available, a consumer's resolution code is ~5 lines per `@link` field — straightforward and application-specific.

---

## 8. Recommendation

### Verdict: **DO NOT IMPLEMENT — Keep Issue Open as Future Enhancement**

Issue #110 identifies a real consumer convenience gap, but the proposed fix:

1. **Falls outside the defined contribution scope** — No ROADMAP task, no Implementation Guide section, no contribution goal statement covers `@link` resolution utilities.
2. **Violates architectural patterns** — The CSAPI module is a parse-and-build layer with zero fetch calls. Adding fetch-based resolution changes the module's character.
3. **Addresses a concern already mitigated** — Issues #108/#109 resolved the root cause (invisible `@link` data). Consumers now have typed, documented access to all `@link` fields.
4. **Carries high risk for the contribution** — Adding unplanned, untested functionality to a stable codebase risks introducing defects without corresponding contribution scope justification.
5. **Is inherently application-specific** — Different consumers need different auth, error handling, caching, and retry strategies. A one-size-fits-all library function would either be too generic (just wrapping `fetch`) or too opinionated (prescribing error handling).

### What the Library Should Provide (and Already Does)

| Responsibility              | Status                      | How                                                                       |
| --------------------------- | --------------------------- | ------------------------------------------------------------------------- |
| Parse `@link` from JSON     | **Done** (#109)             | `extractCSAPIFeature()` extracts all `@link` fields                       |
| Type `@link` data           | **Done** (#108)             | `CSAPIResourceRef` interface, fields on System/Deployment/SamplingFeature |
| Export types for consumers  | **Done** (#108)             | `CSAPIResourceRef` exported from `src/index.ts`                           |
| Build navigation URLs       | **Done** (original)         | `CSAPIQueryBuilder` with 68 methods                                       |
| Resolve `@link` by fetching | **Consumer responsibility** | Consumers fetch `ref.href` using their own HTTP infrastructure            |

### Recommended Actions

1. **Do not create a new file** (`link-resolution.ts` or similar) in the CSAPI module.
2. **Do not add fetch calls** to any CSAPI source file.
3. **Do not export** the private helpers `isCSAPIResourceRef()` / `parseResourceRef()` from `geojson.ts` — they are internal parser implementation details.
4. **Keep Issue #110 open** as a documented enhancement request for future consideration (post-contribution).
5. **Consider adding a JSDoc usage example** to `CSAPIResourceRef` showing how consumers can resolve references — this is informational, zero-risk, and helps consumers without expanding the API surface. _(Optional, low priority.)_

### If the Scope Were Expanded in the Future

If the project maintainer later decides to add `@link` resolution utilities, the following guidance would apply:

- **Location:** A new file in `src/ogc-api/csapi/` (e.g., `link-resolution.ts`), NOT in the parser or model files.
- **Pattern:** Follow `src/ogc-api/link-utils.ts` — use `sharedFetch()` from `src/shared/http-utils.ts`, not bare `fetch()`.
- **Scope:** Start with `parseResourceRefHref()` only (URL parsing, no fetch) — smallest possible addition. Defer fetch-based utilities until multiple consumers validate the need.
- **Risk mitigation:** Comprehensive unit tests with mocked fetch responses, covering network errors, relative URLs, 4xx/5xx responses, and malformed hrefs.

---

## Appendix A: Authority Precedence Analysis

| Level       | Source                              | What It Says About `@link` Resolution Utilities                                                             | Supports Implementation?                                                |
| ----------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 1 (highest) | OGC 23-001/23-002                   | Defines `@link` data format and semantics — says nothing about how clients should resolve references        | **NEUTRAL** — spec defines data, not client behavior                    |
| 2           | AI Collaboration Agreement          | §3: Human maintainer has final authority over scope. §5: Controlled evolution; no opportunistic improvement | **NO** — no approval for scope expansion                                |
| 3           | AI Operational Constraints          | §2.1: Do not infer unstated requirements. §2.2: Do not introduce new abstractions without approval          | **NO** — utilities are unstated requirements                            |
| 4           | ROADMAP                             | No task for `@link` resolution utilities. `@link` mentioned only for parsing (Phase 3 Task 1)               | **NO** — not in any phase                                               |
| 4           | Implementation Guide                | "Reference resolution" mentioned once — for SensorML `xlink:href` internal parsing                          | **NO** — different concern                                              |
| 4           | Contribution Goal                   | "GeoJSON extensions recognizing all CSAPI-specific resource types and properties"                           | **NO** — "recognizing" ≠ "resolving"; parsing is complete               |
| 4           | Existing code (`CSAPIQueryBuilder`) | Builds navigation URLs; does not fetch                                                                      | **NO** — establishes parse-and-build pattern                            |
| 4           | Existing code (`link-utils.ts`)     | `fetchLink()` exists for HATEOAS document links                                                             | **PARTIAL** — pattern exists in upstream, but for a different link type |
| 5           | Explorer workaround                 | `tryLinkFallback()` needed 105 lines pre-#108/#109                                                          | **MITIGATED** — root cause resolved; consumer code now trivial          |

**No authority level supports adding `@link` resolution utilities to the contribution scope.**

---

## Appendix B: Detailed Utility-by-Utility Assessment

### B.1 `resolveResourceRef()` — Fetch a Referenced Resource

**What it does:** Takes a `CSAPIResourceRef`, resolves the `href` against a base URL, fetches the target, returns parsed JSON.

**Assessment: DO NOT IMPLEMENT**

- Wraps `fetch()` with URL resolution — ~10 lines of code that every consumer can write trivially
- Introduces fetch calls into the CSAPI module (currently zero)
- Cannot handle application-specific concerns: authentication headers, retry logic, caching, timeout strategies
- The upstream `fetchLink()` in `link-utils.ts` operates on document-level HATEOAS links, not inline `@link` properties — no direct precedent

### B.2 `parseResourceRefHref()` — Extract Type and ID from href

**What it does:** Parses a URL path like `/api/procedures/abc123` into `{ resourceType: 'procedures', resourceId: 'abc123' }`.

**Assessment: LOWEST RISK but questionable value**

- Pure URL parsing — no fetch, no side effects
- Fragile: assumes URL path structure (`/type/id`) that may vary across servers
- Partial overlap with `CSAPIQueryBuilder`'s URL construction (reverse direction)
- Consumers rarely need "type + ID from URL" — they typically just need the full URL to fetch
- If ever added, should be the first/only utility (smallest possible scope expansion)

### B.3 `extractCrossReferences()` — Collect All `@link`/`@id` Fields

**What it does:** Iterates over raw JSON object properties, collects any key ending in `@link` or `@id`.

**Assessment: DO NOT IMPLEMENT — largely redundant**

- The typed parsers already extract known `@link`/`@id` fields into named interface properties
- Consumers access `system.properties.systemKindLink` — they don't need a generic scanner
- Operating on raw JSON bypasses the typed model, which undermines the purpose of the parser
- Only useful for discovering `@link` fields the library doesn't yet know about — an edge case better handled by extending the parser

### B.4 `resolveWithLinkFallback()` — Navigation-Then-Fallback Orchestration

**What it does:** Tries fetching from a navigation URL; if it fails, falls back to `@link` resolution.

**Assessment: DO NOT IMPLEMENT — application-specific orchestration**

- The highest-level utility — couples URL builder, parser output, and fetch logic
- Error handling strategy (what counts as "failure"? 400? 404? 500? timeout?) is application-specific
- Authentication, caching, and retry are consumer concerns
- Different apps may want different fallback strategies (show error, try alternate endpoint, use cached data)
- This is application workflow, not library infrastructure

---

## Linked References

- [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) — Mandatory behavioral rules (§2.1 scope, §2.2 architecture, §2.3 refactoring)
- [AI Collaboration Agreement](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_Collaboration_Agreement.md) — Governance framework (§3 authority, §5 drift prevention)
- [Contribution Goal and Definition](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/contribution-goal-and-definition.md) — Defines contribution scope ("recognizing all CSAPI-specific resource types and properties")
- [ROADMAP](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/ROADMAP.md) — Phase definitions — no task for `@link` resolution utilities
- [CSAPI Implementation Guide](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/csapi-implementation-guide.md) — 4,715-line specification — "reference resolution" mentioned only for SensorML internals
- [Issue #108 Findings Report](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-108-part1-geojson-link-properties.md) — Interface fields for `@link` properties (resolved)
- [Issue #109 Findings Report](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-109-extractcsapifeature-link-extraction.md) — Parser extraction of `@link` properties (resolved)
- [Issue #108](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/108) — Part 1 interfaces: `CSAPIResourceRef` type + `@link` fields (closed, resolved)
- [Issue #109](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/109) — Part 1 parser: `@link` extraction in `extractCSAPIFeature()` (closed, resolved)
- [Issue #103](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) — Part 2 parsers: `@id` cross-reference field extraction (closed, resolved)
- [Gap Analysis Report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/csapi-link-property-gap-analysis.md) — Full audit of `@link` gaps (upstream ogc-csapi-explorer)
- [ogc-csapi-explorer `tryLinkFallback()` workaround (ad06b52)](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52) — Explorer workaround that motivated Issues #108/#109/#110
- [src/ogc-api/link-utils.ts](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/src/ogc-api/link-utils.ts) — Upstream `fetchLink()` / `fetchDocument()` — HATEOAS link resolution pattern (distinct from `@link`)
- [src/shared/http-utils.ts](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/src/shared/http-utils.ts) — `sharedFetch()` — library's foundational fetch wrapper
- OGC 23-001 §8.3, §8.5, §8.9, §16 — Part 1 resource associations and JSON encoding for `@link` inline properties
- OGC 23-002 §16.1 — Part 2 JSON encoding for `@id` inline properties
