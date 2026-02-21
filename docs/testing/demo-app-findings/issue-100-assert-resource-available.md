# Issue #100 Findings Report — `assertResourceAvailable()` Overly Strict for Per-ID Methods

> **Date:** 2026-02-20
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) — "assertResourceAvailable() is overly strict for per-ID methods — blocks valid URL construction for nested resources"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/url_builder.ts`)
> **Discovered by:** [OS4CSAPI/ogc-csapi-explorer#28](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/28) (DataStream schema), [OS4CSAPI/ogc-csapi-explorer#29](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/29) (ControlStream schema)
> **Labels:** bug, interoperability

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

1. **OGC specifications** (OGC 23-001 Part 1, OGC 23-002 Part 2) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #100 describes. Per §2.1 (do not infer unstated requirements), §2.2 (preserve existing patterns, prefer minimal diffs), and §2.3 (no refactoring for style), this report evaluates the existing implementation against the issue's claims before recommending any action.

---

## 2. Executive Summary

**Issue #100 identifies a genuine interoperability concern — the `assertResourceAvailable()` guard conflates "can I list/create resources at a collection endpoint?" with "can I construct a URL for a specific resource by ID?" However, the current behavior is an intentional, documented design choice with a provided workaround, and changing it would be a high-risk modification to a thoroughly tested API contract.**

| Finding | Description | Severity | Recommendation |
|---------|-------------|----------|----------------|
| **F-100.1** | Issue's core claim is **technically valid**: `assertResourceAvailable()` blocks 69 per-ID methods when the resource type wasn't discovered as a top-level link | VALID | **DEFER** — legitimate concern, but change is high-risk pre-contribution |
| **F-100.2** | The assertion behavior is **intentional and documented**: class JSDoc (L23–24) explicitly states "Attempting to build a URL for an unavailable resource throws an EndpointError" | DESIGN CHOICE | **NO ACTION NOW** — this is a documented API contract, not a bug |
| **F-100.3** | A **workaround already exists**: the constructor's `resourceUrls` parameter (L170) explicitly allows callers to register resource types for servers that don't advertise top-level links | MITIGATED | **NO ACTION** — escape hatch exists and is documented |
| **F-100.4** | `buildResourceUrl()` (L251–262) **already has graceful fallback logic** — it would construct valid URLs if the assertion were removed | CONFIRMED | Underlying URL construction is sound; the assertion is the only obstacle |
| **F-100.5** | Removing assertions from 69 methods would require updating **57+ dedicated assertion tests** and potentially re-validating the full 319-test URL builder suite | HIGH RISK | **DEFER** — invasive change best addressed post-contribution |

**Conclusion:** The behavior described in Issue #100 is real and affects interoperability with servers like OpenSensorHub that don't advertise Part 2 resources as top-level links. However, the behavior is intentional, documented, and has a provided workaround (`resourceUrls` constructor parameter). Changing it now — before the upstream contribution is submitted — would be an invasive modification to a thoroughly tested API contract (319 tests, 57+ assertion-specific tests). **Recommend deferring to a post-contribution enhancement**, when the change can be made with full test-suite validation and without risking the integrity of the current submission.

---

## 3. Issue Description

Issue #100 reports that every public method in `CSAPIQueryBuilder` calls `assertResourceAvailable()` before constructing the URL. For per-ID methods (e.g., `getDataStream(id)`, `getDataStreamSchema(id)`), this guard throws `EndpointError` if the resource type wasn't discovered as a top-level link during builder construction — even though the caller already has a valid resource ID and the URL pattern (`/{type}/{id}`) is deterministic.

The problem manifests on servers like OpenSensorHub (OSH) that advertise Part 2 resources (datastreams, observations, controlStreams, commands) only as nested paths under systems (e.g., `/systems/{id}/datastreams`), not as top-level collection endpoints (e.g., `/datastreams`).

**Example failure:**

```typescript
// Throws EndpointError even though /datastreams/03tbj7mvqg50/schema is a valid URL:
builder.getDataStreamSchema('03tbj7mvqg50')
// EndpointError: Collection 'csapi-explorer' does not support 'datastreams' resource.
//   Available resources: systems, deployments, procedures, samplingFeatures, properties
```

The issue proposes three options:
- **Option A:** Remove `assertResourceAvailable()` from 69 per-ID methods (69-line deletion)
- **Option B:** Replace with a `warnIfResourceNotDiscovered()` soft check (69-line substitution)
- **Option C:** Separate `assertCollectionAvailable()` for list/create methods vs no-op for per-ID methods

---

## 4. Source Code Review

### 4.1 `assertResourceAvailable()` Is an Intentional Design Contract

The class-level JSDoc (`url_builder.ts` L22–30) explicitly documents the throwing behavior as the intended API:

```typescript
/**
 * ## Resource Discovery
 *
 * Available resources are discovered automatically from the collection's link
 * relations. Attempting to build a URL for an unavailable resource throws an
 * {@link EndpointError}. Check `availableResources` to inspect what is available.
 *
 * ## Error Handling
 *
 * All URL-building methods throw {@link EndpointError} when the requested
 * resource type is not available on the collection.
 */
```

The method's own JSDoc (`url_builder.ts` L320–327) further documents the `resourceUrls` constructor parameter as the intended workaround:

```typescript
/**
 * Validates that a resource type is available on this collection.
 * @throws {EndpointError} If the resource type is not available.
 *
 * @see The constructor's `resourceUrls` parameter for a workaround when
 *   a resource type exists on the server but was not discovered via links.
 */
private assertResourceAvailable(resourceType: string): void {
  if (!this.availableResources.has(resourceType)) {
    throw new EndpointError(
      `Collection '${this.collection_.id}' does not support '${resourceType}' resource. ` +
        `Available resources: ${Array.from(this.availableResources).join(', ')}`
    );
  }
}
```

This is not accidental — the assertion, the error message, the JSDoc, and the workaround parameter were all designed together.

### 4.2 The `resourceUrls` Constructor Workaround Already Exists

The constructor (`url_builder.ts` L167–175) accepts `resourceUrls?: Map<string, string>` as an explicit escape hatch:

```typescript
constructor(
  private collection_: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,
  resourceUrls?: Map<string, string>
) {
  this.resourceUrls_ = resourceUrls ?? new Map();
  this.baseUrl = this.extractBaseUrl();
  this.availableResources = this.extractAvailableResources();
}
```

The constructor JSDoc (L150–165) documents this as the **recommended workaround**:

```typescript
/**
 * The `resourceUrls` parameter is the recommended workaround for such
 * servers: when provided, its keys are merged into `availableResources`,
 * and its values are used as endpoint base URLs.
 *
 * @example
 * // For servers that don't advertise CSAPI links, provide explicit resource URLs:
 * const resourceUrls = new Map(
 *   CSAPIResourceTypes.map(t => [t, `${baseUrl}/${t}`])
 * );
 * const builder = new CSAPIQueryBuilder(collection, resourceUrls);
 */
```

This means a demo app (or any caller) can pass `resourceUrls` containing the Part 2 types, and the assertions will pass.

### 4.3 `buildResourceUrl()` Graceful Fallback Already Works

The underlying `buildResourceUrl()` method (`url_builder.ts` L251–262) already handles missing resource URLs gracefully:

```typescript
private buildResourceUrl(
  resourceType: string, id?: string, subPath?: string, options?: QueryOptions
): string {
  const topLevelUrl = this.resourceUrls_.get(resourceType);
  const resourceBase = topLevelUrl
    ? topLevelUrl.replace(/\/+$/, '')
    : `${this.baseUrl}/${toUrlPathSegment(resourceType)}`;
  let url = resourceBase;
  if (id) url += `/${encodeResourceId(id)}`;
  if (subPath) url += `/${subPath}`;
  return url + this.buildQueryString(options);
}
```

If the assertion were removed, `buildResourceUrl()` would fall back to `${baseUrl}/${resourceType}` — producing a valid URL like `/datastreams/03tbj7mvqg50/schema`. The fallback path is already implemented and sound.

### 4.4 Resource Discovery: Three Link Conventions

`scanCsapiLinks()` in `helpers.ts` (L115–162) discovers resources from three OGC link conventions:

1. `ogc-cs:` prefixed rels (e.g., `rel: "ogc-cs:systems"`)
2. Plain rels matching `CSAPIResourceTypes` (e.g., `rel: "systems"`)
3. `rel: "items"` where the href path ends with a known resource type

This correctly finds top-level resources. The issue is that Part 2 resources on servers like OSH are only exposed as **nested** links under system entries — not as top-level collection links. The discovery mechanism was designed for top-level resources, which is correct for collection-level operations but overly restrictive for per-ID access.

### 4.5 Scope of Impact: 84 Call Sites, 69 Per-ID

| Category | Count | Assertion Appropriate? |
|----------|-------|------------------------|
| Collection/List methods (no `id`) | 15 | **Yes** — listing requires a valid collection endpoint |
| Per-ID methods (have `id`) | 69 | **Debatable** — URL is deterministic from type + ID |
| **Total** | **84** | |

By resource type:

| Resource Type | Collection | Per-ID | Total |
|---------------|-----------|--------|-------|
| `systems` | 2 | 14 | 16 |
| `deployments` | 2 | 7 | 9 |
| `procedures` | 2 | 6 | 8 |
| `samplingFeatures` | 2 | 6 | 8 |
| `properties` | 1 | 5 | 6 |
| `datastreams` | 2 | 9 | 11 |
| `observations` | 1 | 7 | 8 |
| `controlStreams` | 2 | 8 | 10 |
| `commands` | 1 | 7 | 8 |
| **Totals** | **15** | **69** | **84** |

The Part 2 resources (`datastreams`, `observations`, `controlStreams`, `commands`) are most impacted — **31 of the 69** per-ID methods — because these types are commonly only available as nested paths under systems.

### 4.6 Test Coverage: Comprehensive Assertion Tests

The URL builder test suite (`url_builder.spec.ts`) has **dedicated assertion test infrastructure**:

1. **Core "Resource validation" block** (~L148–176) — 4 tests verifying `EndpointError` throw/message/type behavior
2. **7 per-resource-type validation blocks** — each with a multi-assertion `it()` testing that EVERY method for that resource type throws when unavailable:
   - Deployment (8 assertions), Procedure (8), SamplingFeature (8), Property (6), DataStream (11), Observation (8), ControlStream (8), Command (8+)
3. **Dedicated error message format tests** (~L2929–2966) — 4 tests verifying error includes collection ID, resource type, and available resources list
4. **Individual method-level throw tests** scattered across method describe blocks

**Estimated 57+ test assertions** explicitly verify the assertion-throwing behavior. Removing assertions from 69 methods would require updating or removing all of these tests.

---

## 5. Reference Document Review

### OGC API — Connected Systems Part 2 (OGC 23-002)

Issue #100 correctly references the OGC spec:

> The spec defines that Part 2 resources are accessible **both** as:
> - **Nested paths**: `/systems/{id}/datastreams` (always available)
> - **Top-level paths**: `/datastreams` (optional — server decides)

This is accurate. The spec does NOT require top-level Part 2 collection endpoints. A server that only exposes Part 2 resources as nested paths under systems is fully compliant. The implication: a client should be able to construct per-ID URLs for Part 2 resources regardless of whether the top-level collection was discovered.

### Cross-Server Findings (from Issue #100)

| Server | Top-level `/datastreams`? | `/datastreams/{id}` works? | `/datastreams/{id}/schema` works? |
|--------|---------------------------|----------------------------|-----------------------------------|
| OpenSensorHub (OSH) | ❌ No (nested only) | ✅ Yes | ✅ Yes |
| 52North CSAPI Demo | ✅ Yes | ✅ Yes | ✅ Yes |

OSH does serve Part 2 resources by ID at well-known paths — it simply doesn't advertise them as top-level links.

### AI Operational Constraints

- **§2.1:** "Do not infer unstated requirements; do not expand scope." — The issue requests removing/softening assertions on 69 methods. This is the defined scope.
- **§2.2:** "Preserve upstream structure/naming/patterns; prefer minimal diffs." — The current assertion pattern IS the established architecture. All 84 methods follow it uniformly. Removing it from 69 methods while keeping it on 15 creates a **non-uniform pattern** that departs from the original design.
- **§2.3:** "No refactoring for style/clarity/'best practice'." — Changing assertion behavior is not a style change; it's a behavioral change to the public API contract.

**Key tension:** §2.2's "prefer minimal diffs" favors not making the change. But the OGC spec (authority level 1) arguably supports the change because the spec doesn't require top-level collection endpoints for per-ID access.

---

## 6. Risk Assessment

### Risk of Making Changes Now

| Risk | Severity | Description |
|------|----------|-------------|
| **Test suite regression** | **HIGH** | 57+ assertion-specific tests must be updated or removed. Even with mechanical changes, the risk of introducing subtle test gaps is significant. The URL builder suite (319 tests) is the most comprehensive in the CSAPI library. |
| **API contract change** | **HIGH** | The throw-on-unavailable behavior is documented in class-level JSDoc as the API contract. Consumers may rely on catching `EndpointError` to detect unsupported resources. Silently succeeding changes the contract. |
| **Non-uniform assertion pattern** | **MEDIUM** | Keeping assertions on 15 list/create methods but removing from 69 per-ID methods creates an inconsistency that must be documented. Future contributors may not understand why the distinction exists. |
| **Upstream contribution risk** | **HIGH** | The CSAPI library is pending upstream submission to `camptocamp/ogc-client`. The current implementation is internally consistent and thoroughly tested. Introducing a behavioral change at this stage risks complicating the upstream review — reviewers expect a coherent design, not one that was partially relaxed late in development. |
| **Pre-contribution scope creep** | **MEDIUM** | Making this change now moves the library from "well-tested, internally consistent design" to "design modified to accommodate a specific server's behavior." This is better positioned as a follow-up enhancement. |

### Risk of Doing Nothing

| Risk | Severity | Description |
|------|----------|-------------|
| **Interoperability gap for Part 2 nested resources** | **MEDIUM** | Callers must use the `resourceUrls` workaround or try/catch to handle servers that only expose Part 2 resources as nested paths. This is a known limitation, not a defect. |
| **Demo app complexity** | **LOW** | The demo app uses try/catch fallbacks. This is functional and documented. |
| **Post-contribution work required** | **LOW** | The change can be made after upstream acceptance with full test-suite support. |

---

## 7. Recommendation

### **DEFER — Valid Enhancement, Wrong Timing**

Issue #100 identifies a **genuine interoperability concern** that is consistent with the OGC specification. The analysis confirms:

1. The issue's core claim is **technically valid** — `assertResourceAvailable()` blocks per-ID URL construction for resource types only available as nested paths
2. `buildResourceUrl()` **already has the correct fallback logic** and would produce valid URLs if the assertion were removed
3. The OGC spec **does not require** top-level Part 2 collection endpoints

However, this report recommends **deferring the change** for the following reasons:

1. **The behavior is intentional and documented** — class JSDoc, method JSDoc, and constructor JSDoc all describe this as the designed API contract
2. **A workaround already exists** — the `resourceUrls` constructor parameter is the engineered escape hatch for exactly this scenario
3. **The change is invasive** — 69 production line deletions + 57+ test assertion updates across the most comprehensively tested module in the library
4. **Pre-contribution risk** — the CSAPI library is pending upstream submission with a consistent, thoroughly tested design; modifying that design now introduces unnecessary risk
5. **The fix is better positioned post-contribution** — once upstream, the change can be proposed as an enhancement with full CI/CD validation and upstream reviewer input

### If the change IS made in the future:

**Option A (from Issue #100) is the correct approach:** Simply remove `assertResourceAvailable()` from the 69 per-ID methods. This is mechanically simple (69 one-line deletions) and `buildResourceUrl()` already handles the fallback. Option B (warn) would add console noise in normal operation. Option C (separate methods) is over-engineering for a guard that should simply be removed from per-ID paths.

The test updates would involve:
- Removing or inverting 57+ `toThrow(EndpointError)` assertions for per-ID methods in the 7 per-resource-type validation blocks
- Verifying that the 4 core assertion tests still pass for collection/list methods
- Adding new positive tests confirming per-ID methods succeed without the resource being in `availableResources`

### Immediate Action: None

No code changes are recommended at this time. The `resourceUrls` constructor parameter provides adequate mitigation for callers encountering this behavior. The demo app's try/catch pattern is functional. The library's internal consistency should be preserved for the upstream contribution.

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source | Ruling |
|-----------------|--------|--------|
| **1. OGC Specification** | OGC 23-002 — Part 2 resources accessible both as nested and top-level paths; top-level not required | **Supports** the change — spec allows per-ID access without top-level discovery |
| **2. AI Collaboration Agreement** | §2.2 — preserve structure, prefer minimal diffs | **Opposes** the change now — current pattern is the established architecture |
| **3. Issue Description** | #100 — remove/soften assertion for 69 per-ID methods | Defines scope; does not mandate timing |
| **4. Existing Code** | `assertResourceAvailable()` — documented, intentional, tested on all 84 methods | **Opposes** the change now — behavior is the API contract |
| **5. Conversation Context** | User prioritizes protecting CSAPI contribution integrity | **Strongly opposes** the change now |

**Conclusion:** Authority levels 1 and 3 support the change in principle. Authority levels 2, 4, and 5 oppose making it now. The balance favors **deferring** to post-contribution.

---

## Appendix B: Cross-Reference to Related Issues

| Issue | Repository | Relationship | Status |
|-------|------------|-------------|--------|
| [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) | ogc-client-CSAPI_2 | **This issue** — `assertResourceAvailable()` overly strict for per-ID methods | Open |
| [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99) | ogc-client-CSAPI_2 | **Related** — `?f=` support (already exists; Issue #99 closed as not_planned) | Closed |
| [#28](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/28) | ogc-csapi-explorer | **Discovery source** — DataStream schema display blocked by this assertion | Closed |
| [#29](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/29) | ogc-csapi-explorer | **Discovery source** — ControlStream schema display blocked by this assertion | Closed |
| [#27](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/27) | ogc-csapi-explorer | **Adjacent** — SensorML rendering; discovered `?f=` need that led to #99 | Closed |
| [Issue #99 findings](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-99-format-query-parameter.md) | ogc-client-CSAPI_2 | **Predecessor** — established that #100 is the real blocker, not missing `?f=` support | Report exists |

### Linked Reference Documents

| Document | Location | Relevance |
|----------|----------|-----------|
| AI Operational Constraints | [docs/governance/AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | §2.1 (no scope expansion), §2.2 (preserve structure/minimal diffs) — supports deferring |
| OGC API Connected Systems Part 1 | OGC 23-001, §7.2–7.3 | Part 1 resource endpoints (systems, deployments, procedures, samplingFeatures, properties) |
| OGC API Connected Systems Part 2 | OGC 23-002, §7.1–7.4 | Part 2 resource endpoints (datastreams, observations, controlStreams, commands) — top-level optional |
| `assertResourceAvailable()` | `src/ogc-api/csapi/url_builder.ts` L320–327 | The guard method under review |
| `buildResourceUrl()` | `src/ogc-api/csapi/url_builder.ts` L251–262 | Already has graceful fallback; would work without assertion |
| `resourceUrls` constructor param | `src/ogc-api/csapi/url_builder.ts` L150–175 | Existing workaround for servers that don't advertise links |
| `scanCsapiLinks()` | `src/ogc-api/csapi/helpers.ts` L115–162 | Resource discovery from collection links |
| Issue #99 findings report | `docs/testing/demo-app-findings/issue-99-format-query-parameter.md` | Identified #100 as the real blocker |
