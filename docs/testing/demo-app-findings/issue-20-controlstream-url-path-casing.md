# Findings Report: Issue #20 — Fix `buildResourceUrl()` Fallback to Use Correct Lowercase URL Path for controlStreams (F-17)

> **Date**: 2026-02-18
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#20](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/20) > **Finding ID**: F-17 (from [crud-smoke-test-phase-2-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-phase-2-findings.md))
> **Labels on source issue**: `bug`

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the `buildResourceUrl()` camelCase fallback path for `controlStreams` (F-17) requires a fix in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the bug is verified in source code and corroborated by live server testing.

---

## Executive Summary

Issue #20 reports that `buildResourceUrl()` in `url_builder.ts` uses the internal resource type key `'controlStreams'` (camelCase) directly as a URL path segment in its fallback path, producing URLs like `/controlStreams/cs-001` instead of the OGC-specified `/controlstreams/cs-001` (all lowercase). Servers like OSH SensorHub that enforce the spec's lowercase path reject these URLs with `400 Bad Request`.

**This is a confirmed bug in our CSAPI client library contribution.** Unlike findings F-12 through F-16 — which involved HTTP request/response handling outside the library's scope — F-17 is squarely within the library's core responsibility: URL construction. The `CSAPIQueryBuilder` exists to produce correct OGC API URLs, and it produces incorrect URLs for all six top-level controlStream operations when the `resourceUrls_` map lacks a pre-populated entry for the `controlStreams` type.

The bug exhibits an internal inconsistency: the library's nested sub-path methods (e.g., `getSystemControlStreams()` at line 465) already use the correct lowercase `'controlstreams'`, while the six top-level controlStream methods pass the camelCase key that `buildResourceUrl()` uses verbatim in the URL path.

**Recommendation: FIX RECOMMENDED** — This is a genuine URL construction bug in the library's core functionality. The proposed Option A fix (a `RESOURCE_PATH_OVERRIDES` map in `buildResourceUrl()`) is a single-point, minimal-diff change that corrects all six affected methods at once without modifying `CSAPIResourceTypes`, `assertResourceAvailable()`, or any method signatures. The fix is the same class of correction as Issue #5 (F-1: `createDataStream()` URL generation), which was also recommended for fix. Unit test expectations that assert the current camelCase behaviour will need corresponding updates.

---

## Issue Description

### What the issue reports

The `buildResourceUrl()` method at lines 199–215 of `url_builder.ts` constructs fallback URLs by appending the internal resource type key directly to the base URL:

```typescript
const resourceBase = topLevelUrl
  ? topLevelUrl.replace(/\/+$/, '')
  : `${this.baseUrl}/${resourceType}`;
//                      ^^^^^^^^^^^^^^ uses camelCase key directly
```

When `resourceUrls_` has no entry for `'controlStreams'` (the common case — the constructor defaults to an empty Map), the fallback produces:

```
GET  /controlStreams/cs-001        ← camelCase — REJECTED by OSH (400)
PUT  /controlStreams/cs-001        ← camelCase — REJECTED by OSH (400)
DELETE /controlStreams/cs-001      ← camelCase — REJECTED by OSH (400)
```

The OGC Connected Systems API Part 2 spec uses `/controlstreams` (all lowercase) in all endpoint definitions and examples.

### Affected methods

| Method                       | Line | Produces                      | Should Produce                |
| ---------------------------- | ---- | ----------------------------- | ----------------------------- |
| `getControlStreams()`        | 1642 | `/controlStreams?...`         | `/controlstreams?...`         |
| `getControlStream(id)`       | 1664 | `/controlStreams/{id}`        | `/controlstreams/{id}`        |
| `createControlStream()`      | 1685 | `/controlStreams`             | `/controlstreams`             |
| `updateControlStream(id)`    | 1707 | `/controlStreams/{id}`        | `/controlstreams/{id}`        |
| `deleteControlStream(id)`    | 1727 | `/controlStreams/{id}`        | `/controlstreams/{id}`        |
| `getControlStreamSchema(id)` | 1753 | `/controlStreams/{id}/schema` | `/controlstreams/{id}/schema` |

**Not affected**: `getSystemControlStreams()` (line 465) and `getPropertyControlStreams()` (line 1164) — these already hardcode the correct lowercase `'controlstreams'` as a sub-path parameter.

### Internal inconsistency

The library already uses the correct lowercase path in its nested sub-path methods:

```typescript
// url_builder.ts:465 — CORRECT lowercase sub-path
getSystemControlStreams(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', id, 'controlstreams', options);
  //                                           ^^^^^^^^^^^^^^ lowercase ✓
}
```

But all top-level controlStream methods pass the camelCase key:

```typescript
// url_builder.ts:1642–1644 — passes camelCase key
getControlStreams(options?: ControlStreamQueryOptions): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', undefined, undefined, options);
  //                            ^^^^^^^^^^^^^^ camelCase — becomes URL path ✗
}
```

### Root cause

The `CSAPIResourceTypes` array in `model.ts` (lines 30–41) uses `'controlStreams'` (camelCase) as the canonical key. For 8 of the 9 resource types, the key equals the URL path segment. But `controlStreams` is the exception — the OGC spec path is `/controlstreams` (lowercase). The `samplingFeatures` type also has a camelCase key, but the OGC spec actually uses `/samplingFeatures` in its paths, so there is no mismatch for that type.

### Evidence from live testing

Tested against OSH SensorHub at `http://45.55.99.236:8080/sensorhub/api`:

```
GET /controlStreams/0410
→ 400 Bad Request
→ { "status": 400, "message": "Invalid resource name: 'controlStreams'" }

GET /controlstreams/0410
→ 200 OK (success)
```

### Demo app workaround

Applied in `demo/src/csapi-bridge.ts` at commit [`6f2d854`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/6f2d854). The bridge module maps `controlStreams` → `controlstreams` and injects the lowercase path into the builder's `resourceUrls` map during initialization, bypassing the fallback path.

---

## Analysis

### This IS the library's core responsibility

The `CSAPIQueryBuilder` exists for one purpose: to construct correct OGC API URLs. The library's five responsibilities per the [CSAPI Implementation Guide](../../planning/csapi-implementation-guide.md) are Parse, **Construct** (URLs), Transform, Handle, and Validate. Responsibility #2 — URL construction — is the affected area.

Unlike findings F-12 through F-16, which involved HTTP request/response handling that the library does not perform, F-17 is about the library producing URLs that do not conform to the OGC spec. This is the exact type of bug the library should fix.

### Precedent: Issue #5 (F-1) — same class of bug

Issue #5 identified that `createDataStream()` generates incorrect URLs (top-level `/datastreams` instead of nested `/systems/{id}/datastreams`). The [Issue #5 findings report](issue-5-nested-create-methods.md) recommended **"Proceed with fix"** because it's a URL generation bug in the library's core functionality. F-17 is the same class of defect — the library constructs URLs with wrong path segments.

### The `scanCsapiLinks` return value is not used for URL construction

The `scanCsapiLinks()` helper (lines 123–166 in `helpers.ts`) returns a `Map<string, string>` where keys are resource type names and values are hrefs from the link relations. However, `extractAvailableResources()` at line 180 only uses the **keys** (for the `availableResources` Set). The href values — which may contain the correct lowercase path — are discarded. The `resourceUrls_` map used by `buildResourceUrl()` is populated solely from the optional constructor parameter, not from link discovery.

This means that even when a server advertises `{ rel: 'ogc-cs:controlStreams', href: '/controlstreams' }` (with the correct lowercase href), `buildResourceUrl()` still falls back to the camelCase key because the href is never stored in `resourceUrls_`.

### Existing tests assert the buggy behaviour

The test suite's `makeCsBuilder()` at line 2015 of `url_builder.spec.ts` constructs a builder without a `resourceUrls` parameter:

```typescript
function makeCsBuilder() {
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
          rel: 'ogc-cs:controlStreams',
          type: '',
          title: '',
          href: '/controlstreams',
        },
      ],
    })
  );
}
```

The test expectations assert the camelCase URL:

```typescript
expect(url).toBe('https://example.com/collections/iot/controlStreams');
//                                                     ^^^^^^^^^^^^^^ asserts buggy camelCase
```

A fix would require updating these test expectations to assert the correct lowercase path.

### JSDoc documentation already shows the correct URLs

All six affected methods have JSDoc `@example` blocks that show the **correct lowercase** URLs:

```typescript
// Line 1637 — JSDoc example for getControlStreams():
// => "https://example.com/collections/iot/controlstreams?limit=10&systemId=sys-001"
//                                         ^^^^^^^^^^^^^^ lowercase in docs ✓
```

The fix would make the code's output match its own documentation.

---

## Risk Assessment

### Risk of fixing (LOW)

| Risk Factor                                            | Assessment                                                       |
| ------------------------------------------------------ | ---------------------------------------------------------------- |
| **Scope of change**                                    | 1 line changed + ~6 lines added (override map + helper function) |
| **Method signatures**                                  | No changes — all public API signatures remain identical          |
| **`CSAPIResourceTypes` / `assertResourceAvailable()`** | No changes — internal type keys preserved                        |
| **8 other resource types**                             | Unaffected — their keys already match their URL paths            |
| **`resourceUrls_` map path**                           | Unaffected — the fix only changes the fallback path              |
| **Nested sub-path methods**                            | Unaffected — they already use correct lowercase strings          |
| **Test updates required**                              | Yes — ~10 test expectations change from camelCase to lowercase   |
| **Breaking change?**                                   | No — the fix corrects output to match the spec                   |

### Risk of NOT fixing (MEDIUM-HIGH)

| Risk Factor                                    | Assessment                                                                                |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Every consumer without `resourceUrls_` map** | Gets broken controlStream URLs                                                            |
| **Strict servers (OSH)**                       | Reject all 6 controlStream operations with 400                                            |
| **Internal inconsistency persists**            | Sub-path methods produce correct lowercase; top-level methods produce incorrect camelCase |
| **Documentation mismatch persists**            | JSDoc examples show lowercase; code produces camelCase                                    |
| **Consumers must workaround**                  | Every consumer must independently discover and work around the casing bug                 |

---

## Assessment of Proposed Fix Options

### Option A: `RESOURCE_PATH_OVERRIDES` map (RECOMMENDED)

```typescript
/** Maps internal resource type keys to their OGC API URL path segments. */
const RESOURCE_PATH_OVERRIDES: Readonly<Record<string, string>> = {
  controlStreams: 'controlstreams',
};

function toUrlPathSegment(resourceType: string): string {
  return RESOURCE_PATH_OVERRIDES[resourceType] ?? resourceType;
}
```

Applied in `buildResourceUrl()`:

```diff
  const resourceBase = topLevelUrl
    ? topLevelUrl.replace(/\/+$/, '')
-   : `${this.baseUrl}/${resourceType}`;
+   : `${this.baseUrl}/${toUrlPathSegment(resourceType)}`;
```

**Advantages:**

- Single-point change — corrects all 6 affected methods at once
- No changes to `CSAPIResourceTypes`, `assertResourceAvailable()`, or any method signatures
- Extensible — if future resource types have similar mismatches, one map entry suffices
- Only affects the fallback path — `resourceUrls_` map entries are used as-is
- Consistent with §2.2: minimal diff, no new abstractions or layers

**Test updates:** ~10 expectations for top-level controlStream methods change from `controlStreams` to `controlstreams` in URL paths. All other tests are unaffected.

### Option B: Normalize in each method individually (NOT RECOMMENDED)

Would require updating 6 methods to pass a lowercase literal string. Introduces inconsistency where `assertResourceAvailable('controlStreams')` uses the camelCase key but `buildResourceUrl('controlstreams')` uses lowercase.

---

## Recommendation

**FIX RECOMMENDED** — Apply Option A (`RESOURCE_PATH_OVERRIDES` map in `buildResourceUrl()`).

### Justification

1. **This is a URL construction bug in the library's core functionality.** The `CSAPIQueryBuilder` exists to produce correct OGC API URLs. Producing `/controlStreams` instead of `/controlstreams` is a spec-conformance defect.

2. **The fix is minimal and targeted.** One line changed in `buildResourceUrl()`, plus ~6 lines for the static override map. No method signatures change. No new abstractions, layers, or dependencies. Consistent with §2.2.

3. **Precedent supports the fix.** Issue #5 (F-1) — the same class of bug (URL generation) — was [recommended for fix](issue-5-nested-create-methods.md). The library has an established pattern of correcting URL construction bugs.

4. **The internal inconsistency should not persist.** The sub-path methods already use correct lowercase paths. The top-level methods should produce matching URLs.

5. **The fix makes code match its own documentation.** All six affected methods' JSDoc examples already show the correct lowercase URLs. The fix aligns output with documentation.

6. **Not fixing transfers the bug to every consumer.** Without the fix, every consumer of `CSAPIQueryBuilder` must independently discover that controlStream URLs are wrong and apply their own workaround, as the demo app did.

### Implementation notes

- The fix should be implemented as a separate, well-scoped commit
- All 298+ existing tests should pass after the fix (with ~10 expectation updates for controlStream URL casing)
- The `RESOURCE_PATH_OVERRIDES` map and `toUrlPathSegment()` function should be module-private (not exported)
- No changes to `CSAPIResourceTypes`, `model.ts`, or any public API signatures

---

## Cross-References

| Document                                                                                                                                                       | Relevance                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [AI Operational Constraints §2.2](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)                                                                              | Minimal diffs preferred; no new abstractions without approval — Option A is compliant             |
| [CSAPI Implementation Guide](../../planning/csapi-implementation-guide.md)                                                                                     | Responsibility #2 (Construct URLs) — the affected core responsibility                             |
| [Issue #5 report (F-1/F-2)](issue-5-nested-create-methods.md)                                                                                                  | Same class of bug (URL generation); recommended to fix                                            |
| [crud-smoke-test-phase-2-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-phase-2-findings.md)           | F-17 original finding: severity High, demo workaround at commit `6f2d854`                         |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | Confirms F-17 workaround is in demo layer; library source NOT modified                            |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Confirms `CSAPIResourceTypes` includes `controlStreams`; F-1 reference (same class)               |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | V-7 shows camelCase builder output; F-2 shows expected lowercase paths                            |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | F-2 shows lowercase `/controlstreams` as expected server path                                     |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | Finding #13: builder outputs camelCase `/controlStreams/` in URLs                                 |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | Explains discovery fallback — why consumers hit `buildResourceUrl()` directly                     |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | §7 shows lowercase `/controlstreams` as correct URL path                                          |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | Phase 1 findings context (F-15, F-16)                                                             |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | Cross-server testing context                                                                      |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | EndpointError refactor context                                                                    |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | F-13: related `getControlStreamSchema()` parameter name issue                                     |
| [OGC 23-002 Connected Systems API Part 2](https://docs.ogc.org/is/23-002/23-002.html#_controlstream_resources)                                                 | Spec uses `/controlstreams` (lowercase)                                                           |
| [url_builder.ts](../../src/ogc-api/csapi/url_builder.ts)                                                                                                       | `buildResourceUrl()` fallback at L210; affected methods at L1642–1755                             |
| [model.ts](../../src/ogc-api/csapi/model.ts)                                                                                                                   | `CSAPIResourceTypes` with `'controlStreams'` key at L38                                           |
| [helpers.ts](../../src/ogc-api/csapi/helpers.ts)                                                                                                               | `scanCsapiLinks()` at L123 — returns hrefs but they're discarded by `extractAvailableResources()` |
