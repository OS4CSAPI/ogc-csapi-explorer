# Issue #99 Findings Report — `?f=` Query Parameter for Format Negotiation

> **Date:** 2026-02-20
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99) — "URL builder should support ?f= query parameter for format negotiation (Accept header ignored by OSH)"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/url_builder.ts`, `src/ogc-api/csapi/model.ts`)
> **Discovered by:** [OS4CSAPI/ogc-csapi-explorer#27](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/27) — SensorML rendering for Procedures
> **Labels:** enhancement, interoperability

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Recommendation](#7-recommendation)
8. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
9. [Appendix B: Cross-Reference to Related Issues](#appendix-b-cross-reference-to-related-issues)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (OGC API — Common Part 1, §7.7–7.8) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #99 describes. Per §2.1 (do not infer unstated requirements), §2.2 (preserve existing patterns, prefer minimal diffs), and §2.3 (no refactoring for style), this report evaluates the existing implementation against the issue's claims before recommending any action.

---

## 2. Executive Summary

**Issue #99's core claim is factually incorrect. The `?f=` query parameter is already fully supported by our library. No code changes are needed.**

| Finding    | Description                                                                                    | Severity      | Recommendation                           |
| ---------- | ---------------------------------------------------------------------------------------------- | ------------- | ---------------------------------------- |
| **F-99.1** | `QueryOptions.f` already exists as a typed `MimeType` property                                 | INFORMATIONAL | **NO ACTION** — capability exists        |
| **F-99.2** | `buildQueryString()` correctly serializes `f` into `?f={value}`                                | INFORMATIONAL | **NO ACTION** — serialization works      |
| **F-99.3** | The real blocker is #100 (`assertResourceAvailable()` throwing), not a missing `?f=` parameter | INFORMATIONAL | **DEFER** to Issue #100 analysis         |
| **F-99.4** | Issue claims library "currently only facilitates the Accept header path"                       | INCORRECT     | Library already supports both mechanisms |

**Conclusion:** The library's URL builder already implements exactly what Issue #99 requests. The demo app's failure to use `?f=` stemmed from #100's `assertResourceAvailable()` guard throwing before the URL (including `?f=`) could be constructed. No changes to our CSAPI client library contribution are warranted.

---

## 3. Issue Description

Issue #99 reports that the URL builder (`CSAPIQueryBuilder`) "currently constructs detail URLs like `/procedures/{id}` and relies on the HTTP `Accept` header for content negotiation" and cannot append a `?f=` query parameter for servers like OpenSensorHub that ignore the `Accept` header and require query-parameter-based negotiation.

The issue proposes three solution options:

- **Option A:** Add `format` to `QueryOptions`
- **Option B:** Add a dedicated `.withFormat()` method
- **Option C:** Support both `Accept` header and `?f=` with automatic fallback

The issue was discovered during development of the CSAPI Explorer demo application (ogc-csapi-explorer#27), where `SensorMLDisplay.vue` needed to fetch SensorML representations of Procedures from OSH. The demo app implemented a workaround by scanning response `links[]` for alternate links containing `?f=sml3` and following them.

---

## 4. Source Code Review

### 4.1 `QueryOptions` Already Has `f?: MimeType`

The `QueryOptions` interface in `model.ts` (line 138) already defines the `f` parameter:

```typescript
export interface QueryOptions {
  limit?: number;
  offset?: number;
  cursor?: string;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  q?: string;
  id?: string | string[];
  uid?: string | string[];
  f?: MimeType; // ← ALREADY EXISTS
  crs?: CrsCode;
}
```

This is precisely what Issue #99 Option A proposes. It already exists.

### 4.2 `buildQueryString()` Correctly Serializes `f`

The `buildQueryString()` method in `url_builder.ts` (lines 280–310) iterates all `Object.entries(options)` and serializes non-null values. The `f` parameter hits the generic `else` branch:

```typescript
} else {
  params.append(key, String(value));  // f → ?f=sml3
}
```

This produces exactly the `?f=sml3` URL format that Issue #99 wants.

### 4.3 Per-ID Methods Accept `QueryOptions` Including `f`

Every per-ID method accepts `options?: QueryOptions`, which includes `f`. For example:

```typescript
getProcedure(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('procedures');
  return this.buildResourceUrl('procedures', id, undefined, options);
}
```

A consumer can already write:

```typescript
builder.getProcedure('040g', { f: 'sml3' });
// → /procedures/040g?f=sml3
```

### 4.4 The Real Blocker: `assertResourceAvailable()` (Issue #100)

The reason the demo app could not use this capability is that `assertResourceAvailable()` throws `EndpointError` before `buildResourceUrl()` is ever reached — if the resource type wasn't discovered as a top-level link during builder construction. This is Issue #100's scope, not Issue #99's.

On OSH, `procedures` IS discovered as a top-level link, so `getProcedure(id, { f: 'sml3' })` would actually work. The demo app's problem was a combination of factors:

1. For Part 2 resources (datastreams, controlStreams): #100 blocks the call entirely
2. For Part 1 resources (procedures): the demo app didn't try passing `{ f: 'sml3' }` — it went straight to the `Accept` header workaround

### 4.5 Verification: End-to-End Path

Tracing the code path for `builder.getProcedure('040g', { f: 'sml3' })`:

1. `assertResourceAvailable('procedures')` — passes (procedures is a top-level link on OSH)
2. `buildResourceUrl('procedures', '040g', undefined, { f: 'sml3' })` — constructs base URL
3. `buildQueryString({ f: 'sml3' })` — produces `?f=sml3`
4. **Result:** `https://45.55.99.236:8080/sensorhub/api/procedures/040g?f=sml3`

This is exactly the URL that Issue #99 says is needed.

---

## 5. Reference Document Review

### OGC API — Common Part 1 (19-072)

Issue #99 correctly references:

- **§7.7 (HTTP Content Negotiation):** Servers SHOULD support `Accept` headers
- **§7.8 (Parameter-based Negotiation):** Servers MAY support a `f` query parameter

Both mechanisms are valid per the spec. Our library supports both:

- `Accept` header: consumer's responsibility when making the HTTP request (library is a URL builder, not an HTTP client)
- `?f=` parameter: supported via `QueryOptions.f` since the `QueryOptions` interface was defined

### AI Operational Constraints

- **§2.1:** "Do not infer unstated requirements; do not expand scope." — The issue requests functionality that already exists. Implementing it again would be scope expansion.
- **§2.2:** "Preserve upstream structure/naming/patterns; prefer minimal diffs." — The existing implementation is correct. Changing it would introduce unnecessary diff.
- **§2.3:** "No refactoring for style/clarity/'best practice'." — No refactoring is warranted.

### Cross-Server Findings (from Issue #99)

| Server              | `Accept` Header Honored? | `?f=` Supported?   | Library handles `?f=`?   |
| ------------------- | ------------------------ | ------------------ | ------------------------ |
| OpenSensorHub (OSH) | ❌ No                    | ✅ Yes (`?f=sml3`) | ✅ Yes — `{ f: 'sml3' }` |
| 52North CSAPI Demo  | ⚠️ Partial               | ✅ Yes             | ✅ Yes — `{ f: '...' }`  |

---

## 6. Risk Assessment

### Risk of Making Changes

| Risk                       | Severity   | Description                                                                                                                                                                           |
| -------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Degradation of tested code | **HIGH**   | The `QueryOptions` interface and `buildQueryString()` are covered by existing unit tests (1,251 CSAPI tests, 319 URL builder tests). Any modifications risk breaking tested behavior. |
| Redundant implementation   | **MEDIUM** | Adding a new parameter (e.g., `format`) alongside the existing `f` would create two ways to do the same thing — a DRY violation and maintenance burden.                               |
| Precedence violation       | **MEDIUM** | Per AI Operational Constraints §2.2, adding new abstractions (Option B's `.withFormat()` method, Option C's automatic fallback) requires approval and has no upstream precedent.      |

### Risk of Doing Nothing

| Risk              | Severity | Description                                                                                                                                    |
| ----------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| None identifiable | **NONE** | The capability already exists. The demo app's workaround was unnecessary — `{ f: 'sml3' }` in `QueryOptions` would have worked for procedures. |

---

## 7. Recommendation

### **NO ACTION REQUIRED on our CSAPI client library**

The `?f=` query parameter support described in Issue #99 is already implemented:

- `QueryOptions.f?: MimeType` — typed parameter in the interface
- `buildQueryString()` — correctly serializes it to `?f={value}`
- All 84 public methods accept `QueryOptions` — `f` is available everywhere

**Issue #99 should be closed as "not planned" or relabeled as a documentation/demo concern**, because:

1. The library capability exists and is functional
2. The demo app's workaround was unnecessarily complex — passing `{ f: 'sml3' }` to `getProcedure()` would have worked
3. The actual blocker for Part 2 resources (datastreams, controlStreams) is Issue #100 (`assertResourceAvailable()`), not a missing `?f=` parameter

### If any action is taken, it should be limited to:

**Option: JSDoc Enhancement (zero runtime change)**

Add a `@example` showing `?f=` usage to a representative per-ID method's JSDoc. For example, in `getProcedure()`:

````typescript
/**
 * @example Request SensorML format via query parameter:
 * ```ts
 * const url = builder.getProcedure('040g', { f: 'sml3' });
 * // => "https://example.com/api/procedures/040g?f=sml3"
 * ```
 */
````

This would be documentation-only, zero runtime impact, and would make the existing capability more discoverable. However, per AI Operational Constraints §2.3, even this is not required and should only be pursued if a separate issue is created for it.

---

## Appendix A: Authority Precedence Analysis

| Authority Level                   | Source                                    | Ruling                                                                                   |
| --------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------- |
| **1. OGC Specification**          | OGC API Common §7.8 — `f` query parameter | Library already conforms via `QueryOptions.f`                                            |
| **2. AI Collaboration Agreement** | §2.2 — preserve structure, minimal diffs  | No changes warranted — existing code is correct                                          |
| **3. Issue Description**          | #99 — "URL builder should support ?f="    | Already supported; issue premise is incorrect                                            |
| **4. Existing Code**              | `model.ts` L138: `f?: MimeType`           | Implementation exists and is functional                                                  |
| **5. Conversation Context**       | Demo app's alternate-link workaround      | Workaround was unnecessary for procedures; #100 is the real blocker for Part 2 resources |

**Conclusion:** All authority levels confirm that the requested capability already exists. No action is required.

---

## Appendix B: Cross-Reference to Related Issues

| Issue                                                                                                                                                      | Repository         | Relationship                                                                                            | Status        |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------- | ------------- |
| [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99)                                                                                            | ogc-client-CSAPI_2 | **This issue** — requests `?f=` support that already exists                                             | Open          |
| [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100)                                                                                          | ogc-client-CSAPI_2 | **Related** — `assertResourceAvailable()` is the actual blocker for Part 2 per-ID methods               | Open          |
| [#27](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/27)                                                                                            | ogc-csapi-explorer | **Discovery source** — SensorML rendering for Procedures discovered the workaround need                 | Closed        |
| [#28](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/28)                                                                                            | ogc-csapi-explorer | **Adjacent** — `parseDatastreamSchemaResponse()` usage; blocked by #100 on OSH                          | Closed        |
| [#29](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/29)                                                                                            | ogc-csapi-explorer | **Adjacent** — ControlStream schema display; blocked by #100 on OSH                                     | Closed        |
| [Issue #16 findings](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-16-schema-jsdoc-parameter-confusion.md) | ogc-client-CSAPI_2 | **Related** — JSDoc conflates `f` with `obsFormat`/`cmdFormat`; existing findings report addresses this | Report exists |

### Linked Reference Documents

| Document                         | Location                                                                                                                                                | Relevance                                                                                           |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| AI Operational Constraints       | [docs/governance/AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | §2.1 (no scope expansion), §2.2 (preserve structure), §2.3 (no refactoring) — all support NO ACTION |
| OGC API Common Part 1            | OGC 19-072, §7.7–7.8                                                                                                                                    | Defines both `Accept` header and `f` query parameter negotiation mechanisms                         |
| OGC API Connected Systems Part 1 | OGC 23-001, §7.3                                                                                                                                        | Procedure resource representations                                                                  |
| QueryOptions interface           | `src/ogc-api/csapi/model.ts` L119–143                                                                                                                   | Contains `f?: MimeType` — the existing implementation                                               |
| URL builder                      | `src/ogc-api/csapi/url_builder.ts` L245–310                                                                                                             | `buildResourceUrl()` + `buildQueryString()` — correctly serializes `f`                              |
