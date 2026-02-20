# Issue #6 Findings Report — `CSAPI_CONTENT_TYPES` Helper Map for Resource-Type Content Negotiation

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#6](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) — "Add CSAPI_CONTENT_TYPES helper map for resource-type content negotiation"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/`)
> **Finding reference:** F-10 (upstream-findings.md), Finding #14 (library-integration-report.md), Finding #6 (e2e-write-operations-report.md)
> **Labels:** enhancement

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Discrepancy: `properties` Content-Type](#7-discrepancy-properties-content-type)
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

This report does not expand scope beyond what Issue #6 describes. No refactoring is proposed. All recommendations are purely additive (new constant + new helper function + new export) with zero modifications to existing code.

---

## 2. Executive Summary

**Issue #6 is correct. The proposed change is warranted and very low-risk.**

The issue identifies a genuine gap: the library provides no guidance on which `Content-Type` header consumers must use for POST/PUT write operations against CSAPI resources. Consumers must independently know the OGC spec's Part 1 vs Part 2 content-type split, which was confirmed to cause real failures during live E2E testing.

| Aspect | Assessment |
|--------|------------|
| **Finding** | F-10 — "No Content-Type Guidance from the Builder" |
| **Severity** | Medium (per upstream-findings.md and gap analysis) |
| **Implementation risk** | Very Low — purely additive |
| **Test risk** | Zero — no existing tests affected |
| **API surface risk** | Zero — no existing signatures change |
| **Change type** | New constant + new function + new export |
| **Files affected** | 1–2 new additions, 1 export update |
| **Existing code modified** | None |

**Key finding:** One discrepancy was identified between Issue #6 and the E2E test reports regarding the correct Content-Type for `properties` resources. Issue #6 specifies `application/json`, but the specification and E2E write operations report indicate `application/geo+json` is correct. See [Section 7](#7-discrepancy-properties-content-type) for analysis.

---

## 3. Issue Description

### F-10: No Content-Type Guidance from the Builder

The `CSAPIQueryBuilder` constructs URLs for all CRUD operations but provides no information about which `Content-Type` header is required for write requests (POST/PUT). The OGC Connected Systems API defines a clear split:

| Resource Category | Resource Types | Required Content-Type |
|-------------------|----------------|-----------------------|
| **Part 1** (OGC 23-001r1) | systems, deployments, procedures, samplingFeatures, properties | `application/geo+json` |
| **Part 2** (OGC 23-002r1) | datastreams, observations, controlStreams, commands | `application/json` |

### What Issue #6 proposes

1. A `CSAPI_CONTENT_TYPES` constant map: `Record<CSAPIResourceType, string>` mapping all 9 resource types to their correct Content-Type
2. A `getContentTypeForResource(resourceType: string): string` helper function with a safe default fallback
3. Export from `src/index.ts`

### Why this matters

During E2E testing against OSH SensorHub, sending a Part 1 resource (system) with `Content-Type: application/json` instead of `application/geo+json` caused the server to reject the request. The demo app had to implement its own inline content-type logic in the bridge module (`csapi-bridge.ts`) as a workaround:

```typescript
// Demo app workaround (csapi-bridge.ts)
export function getContentType(resourceType: string): string {
  const part1 = ['systems', 'deployments', 'procedures', 'samplingFeatures', 'properties'];
  return part1.includes(resourceType) ? 'application/geo+json' : 'application/json';
}
```

This is exactly the kind of boilerplate that every CSAPI consumer would need to write independently.

---

## 4. Source Code Review

### 4.1 Existing type infrastructure (`model.ts` L31–44)

The library already has the complete type foundation for this constant:

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

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];
```

The proposed `CSAPI_CONTENT_TYPES` constant typed as `Record<CSAPIResourceType, string>` would be both complete (covering all 9 types) and type-safe (TypeScript would enforce that every resource type has an entry).

### 4.2 Existing media type constants (`formats/constants.ts` L25–31)

The library already defines the two relevant media type constants:

```typescript
export const MEDIA_TYPE_GEOJSON = 'application/geo+json' as const;
export const MEDIA_TYPE_JSON = 'application/json' as const;
```

The proposed constant can reference these existing values rather than hardcoding strings, maintaining consistency with the established pattern.

### 4.3 Existing CSAPI format constant pattern (`formats/constants.ts` L69–80)

The file already follows a grouping pattern with `CSAPI_MEDIA_TYPES` — an array of all 7 media types with a derived union type. Adding `CSAPI_CONTENT_TYPES` as a resource-type-keyed map follows the same module's conventions.

### 4.4 No existing Content-Type logic in the builder

A search of `url_builder.ts` (2,034 lines, 82 methods) confirms zero references to Content-Type, `application/geo+json`, or `application/json`. The builder is exclusively concerned with URL construction. The proposed addition does not modify any builder method — it is a standalone constant and helper function.

### 4.5 Public API exports (`src/index.ts`)

The library currently exports `CSAPIResourceTypes` and `CSAPIResourceType` from `model.ts`, and `CSAPI_MEDIA_TYPES` from `formats/index.ts`. Adding `CSAPI_CONTENT_TYPES` and `getContentTypeForResource` to the public API follows the existing export pattern for CSAPI constants.

---

## 5. Reference Document Review

All 12 reference documents provided were reviewed. The following contain evidence directly relevant to Issue #6 / F-10:

### 5.1 Core evidence documents

| Document | Relevant Finding | Content-Type Relevance |
|----------|------------------|------------------------|
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) | F-10: Medium severity, Priority 6 ("Should Address"), type "Missing helper" | Proposes `CSAPI_CONTENT_TYPES: Record<CSAPIResourceType, string>` |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md) | F-10 mapped to Issue #6, severity Medium, implementation risk Low | Confirms actionability and low risk |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) | Finding #14: "No Content-Type guidance from the builder" (🟡 Low priority) | Bridge module implemented `getContentType()` as workaround |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md) | Finding #6: "Content-Type Mapping Needs Library Guidance" (Medium); Priority 2 recommendation | Provides full content-type map with `properties: 'application/geo+json'` |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md) | Finding #3: Content negotiation is critical; `application/geo+json` returns data from both servers | Confirms Part 1 = `geo+json` is the most interoperable choice |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | S-8: OSH rejects `Accept: application/geo+json` on POST; F-16 recommendation notes Content-Type guidance pairs with Issue #6 | Distinguishes Content-Type (request body format) from Accept (response format) |

### 5.2 Supporting context documents

| Document | Relevance to Issue #6 |
|----------|----------------------|
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | Authority precedence confirming specs take priority over issue text (relevant to `properties` discrepancy) |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/contribution-goal-accuracy-assessment.md) | Confirms library is "specification-scoped" with all 9 resource types; F-10 noted as known gap |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | Demo bypasses `OgcApiEndpoint` — CSAPI modules are self-contained utilities; content-type helper fits this model |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | Only one library source change (EndpointError isolation) was made during demo development; all other workarounds stayed in demo code — supports the case that content-type logic belongs in the library |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) | Established the pattern for additive, zero-behavior-change library improvements; the proposed constant follows the same philosophy |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | F-14 notes similar gap (no schema response parser); confirms pattern where library provides URL construction but lacks complementary metadata |

### 5.3 Consensus across documents

All reports independently agree that:
- The gap is real (F-10 confirmed across 6 documents)
- The fix is additive (no existing code modified)
- The risk is Low
- The priority is Medium (not blocking, but prevents real errors)
- The demo app had to implement its own workaround

---

## 6. Risk Assessment

### 6.1 What changes

| Component | Change | Risk |
|-----------|--------|------|
| New constant `CSAPI_CONTENT_TYPES` | ~15 lines in `formats/constants.ts` or `model.ts` | Zero — new code only |
| New function `getContentTypeForResource()` | ~5 lines helper function | Zero — new code only |
| `src/index.ts` | Add 2 exports | Zero — additive export |

### 6.2 What does NOT change

- No modifications to `CSAPIQueryBuilder` class or any of its 82 methods
- No modifications to `buildResourceUrl()`, `buildQueryString()`, or any private method
- No modifications to any existing constant, type, or interface
- No modifications to any test file
- No modifications to `model.ts` existing definitions
- No modifications to `formats/constants.ts` existing definitions
- All 298 `url_builder.spec.ts` tests remain exactly as they are

### 6.3 Risk comparison

| Risk category | Issue #5 (nested create methods) | Issue #6 (content-type constant) |
|---------------|----------------------------------|----------------------------------|
| New methods/functions | 5 new methods in `url_builder.ts` | 1 constant + 1 function (not in builder) |
| Modifies existing code | No | No |
| Touches builder internals | No (uses existing `buildResourceUrl`) | No (standalone constant/function) |
| Test impact | None (new tests only) | None (new tests only) |
| **Overall risk** | **Low** | **Very Low** |

Issue #6 is strictly lower-risk than Issue #5 because it doesn't even add methods to the `CSAPIQueryBuilder` class — it adds a standalone constant and helper function.

---

## 7. Discrepancy: `properties` Content-Type

### The discrepancy

Issue #6 specifies:
```typescript
properties: 'application/json',  // Issue #6 text
```

The E2E write operations report (Priority 2 recommendation) specifies:
```typescript
properties: 'application/geo+json',  // E2E report
```

### Resolution: `application/geo+json` is correct

Per AI Operational Constraints, **OGC specifications take precedence over issue descriptions**.

**Properties** are defined in **OGC 23-001r1 (Part 1)**, not Part 2:
- Part 1 (§11) defines the `Property` resource type
- Part 1 resources are encoded as GeoJSON Features
- Part 1 resource creation requires `Content-Type: application/geo+json`

The `CSAPIResourceTypes` array in `model.ts` groups `properties` alongside other Part 1 types (systems, deployments, samplingFeatures, procedures), not with Part 2 types. The E2E write operations report correctly categorizes all Part 1 types as `application/geo+json`.

**Recommendation:** When implementing Issue #6, use `properties: 'application/geo+json'` (the spec-correct value), not `properties: 'application/json'` (as written in the issue text).

The corrected constant:

```typescript
export const CSAPI_CONTENT_TYPES: Record<CSAPIResourceType, string> = {
  // Part 1 resources — GeoJSON Features (OGC 23-001r1)
  systems: MEDIA_TYPE_GEOJSON,         // 'application/geo+json'
  deployments: MEDIA_TYPE_GEOJSON,     // 'application/geo+json'
  procedures: MEDIA_TYPE_GEOJSON,      // 'application/geo+json'
  samplingFeatures: MEDIA_TYPE_GEOJSON, // 'application/geo+json'
  properties: MEDIA_TYPE_GEOJSON,      // 'application/geo+json' (Part 1, NOT Part 2)
  // Part 2 resources — plain JSON (OGC 23-002r1)
  datastreams: MEDIA_TYPE_JSON,        // 'application/json'
  observations: MEDIA_TYPE_JSON,       // 'application/json'
  controlStreams: MEDIA_TYPE_JSON,     // 'application/json'
  commands: MEDIA_TYPE_JSON,           // 'application/json'
} as const;
```

---

## 8. Recommendation

### 8.1 Verdict: Proceed with implementation

Issue #6 should be implemented. The change is:
- **Spec-justified** — OGC 23-001r1 and 23-002r1 define clear Content-Type requirements
- **Evidence-backed** — wrong Content-Type caused real server rejections during E2E testing
- **Purely additive** — zero modifications to existing code
- **Very low risk** — standalone constant and helper function
- **Type-safe** — leverages existing `CSAPIResourceType` union for compile-time completeness

### 8.2 Suggested placement

**Preferred:** `src/ogc-api/csapi/formats/constants.ts`

Rationale: This file already contains `MEDIA_TYPE_GEOJSON`, `MEDIA_TYPE_JSON`, `CSAPI_MEDIA_TYPES`, and follows the grouped constant pattern. The new `CSAPI_CONTENT_TYPES` can reference the existing media type constants directly rather than hardcoding strings, maintaining DRY consistency.

The helper function `getContentTypeForResource()` could live in the same file or in `helpers.ts` alongside other utility functions like `encodeResourceId()` and `formatDateTimeParameter()`.

### 8.3 Correction required

The implementation MUST use `properties: MEDIA_TYPE_GEOJSON` (not `MEDIA_TYPE_JSON` as Issue #6 states). See [Section 7](#7-discrepancy-properties-content-type).

### 8.4 What NOT to do

Per AI Operational Constraints:
- Do NOT add Content-Type logic inside any existing `CSAPIQueryBuilder` method
- Do NOT change any method return type to include content-type metadata (e.g., returning `{ url, contentType }` objects)
- Do NOT modify any existing test
- Do NOT refactor how the builder works

The constant and helper function stand alone. Consumers who want content-type guidance import them directly; consumers who don't need them are unaffected.

---

## Appendix A: Authority Precedence Analysis

| Level | Source | What it says about F-10 | Alignment |
|-------|--------|-------------------------|-----------|
| 1 | **OGC 23-001r1** | Part 1 resources are GeoJSON Features → `application/geo+json` | ✅ Supports Issue #6 |
| 1 | **OGC 23-002r1** | Part 2 resources are JSON → `application/json` | ✅ Supports Issue #6 |
| 2 | **AI Collaboration Agreement** | Spec takes precedence over issue text | ✅ Resolves `properties` discrepancy |
| 3 | **Issue #6 description** | Proposes `CSAPI_CONTENT_TYPES` + `getContentTypeForResource()` | ✅ Correct approach (with `properties` correction) |
| 4 | **Existing code** | `formats/constants.ts` has `MEDIA_TYPE_GEOJSON`, `MEDIA_TYPE_JSON`; `model.ts` has `CSAPIResourceType` | ✅ Full infrastructure exists |
| 5 | **Demo app** | Bridge module implemented identical workaround (`getContentType()`) | ✅ Proves the gap is real |

---

## Appendix B: Cross-Reference Matrix

This matrix maps Issue #6 / F-10 across all 12 reference documents reviewed:

| Document | Finding ID | Severity | Priority | Content-Type for `properties` | Notes |
|----------|-----------|----------|----------|-------------------------------|-------|
| upstream-findings.md | F-10 | Medium | 6 ("Should Address") | `application/geo+json` | Original finding |
| library-findings-gap-analysis.md | F-10 → Issue #6 | Medium | 3 (Medium) | Not specified | Confirms actionability |
| library-integration-report.md | Finding #14 | 🟡 Low | — | Not specified | Workaround in bridge module |
| e2e-write-operations-report.md | Finding #6 | Medium | Priority 2 | `application/geo+json` ✅ | Full map provided |
| e2e-cross-server-report.md | Finding #3 | HIGH | — | — | Confirms `geo+json` most interoperable |
| crud-smoke-test-findings.md | S-8, F-16 ref | — | — | — | Distinguishes Accept vs Content-Type |
| AI_OPERATIONAL_CONSTRAINTS.md | — | — | — | — | Authority precedence rules |
| contribution-goal-accuracy-assessment.md | — | — | — | — | F-10 noted as known gap |
| conformance-bypass-architecture-notes.md | — | — | — | — | CSAPI modules are self-contained |
| library-source-changes-audit.md | — | — | — | — | Only 1 library change during demo |
| endpoint-error-isolation-report.md | — | — | — | — | Pattern for additive improvements |
| schema-display-findings.md | F-14 (related) | Medium | — | — | Similar "missing helper" pattern |
| **Issue #6 text** | F-10 | — | — | `application/json` ❌ | **Incorrect for `properties`** |

---

## Change Log

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-02-17 | Initial report |
