# Findings Report: Issue #21 — Replace Manual URL Construction in MapViewPage with CSAPIQueryBuilder Methods

> **Date**: 2026-02-18
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#21](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/21)
> **Labels on source issue**: `enhancement`

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the manual URL construction in the demo app's `MapViewPage.vue` (bypassing the `CSAPIQueryBuilder`) indicates any bug, gap, or required change in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the builder methods referenced by the issue are verified to already exist in our library.

---

## Executive Summary

Issue #21 reports that `MapViewPage.vue` in the demo app (`ogc-csapi-explorer`) constructs 3 nested-resource API URLs by hand — e.g., `` `/datastreams/${id}/observations?limit=1` `` — instead of using the corresponding `CSAPIQueryBuilder` methods. The issue proposes replacing these manual constructions with builder method calls routed through `csapi-bridge.ts`, improving code quality in the demo app and exercising builder methods currently listed as "Not Demonstrated" in the [query parameter coverage audit](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-demonstration-coverage.md).

**This issue does not affect our CSAPI client library contribution.** The two builder methods referenced by the issue — `getDataStreamObservations()` (line 1348) and `getSystemSamplingFeatures()` (line 484) — already exist in `url_builder.ts`, are fully implemented, have complete JSDoc documentation, and pass all unit tests. The "gap" identified by Issue #21 is that the demo app's `MapViewPage.vue` doesn't _use_ these existing methods — it hardcodes URLs instead. That is a code quality concern in the demo app, not a defect or gap in the library.

**Recommendation: NO ACTION REQUIRED** in our CSAPI client library contribution. The issue is correctly scoped to the demo app (`ogc-csapi-explorer`). Every file identified for modification — `app/src/pages/MapViewPage.vue` and `app/src/csapi-bridge.ts` — is in the demo app repository, not in our library.

---

## Issue Description

### What the issue reports

Three locations in the demo app's `MapViewPage.vue` construct API URLs as raw strings instead of using the query builder:

| Manual URL | Location | Purpose |
|---|---|---|
| `` `/datastreams/${id}/observations?limit=1` `` | `MapViewPage.vue` ~L352 | Fetch latest observation for system location |
| `` `/systems/${sysId}/samplingFeatures?limit=100` `` | `MapViewPage.vue` ~L544 | Enrich sampling features with parent system data |
| `` `/datastreams/${id}/observations?limit=500` `` | `MapViewPage.vue` ~L670 | Load observation tracks for map layer |

### What the issue proposes

Replace each manual `fetch()` call with the corresponding builder method call:

| Manual URL | Builder Method |
|---|---|
| `/datastreams/{id}/observations?limit=1` | `getDataStreamObservations(id, { limit: 1 })` |
| `/systems/{sysId}/samplingFeatures?limit=100` | `getSystemSamplingFeatures(sysId, { limit: 100 })` |
| `/datastreams/{id}/observations?limit=500` | `getDataStreamObservations(id, { limit: 500 })` |

### Affected files (per the issue)

- `app/src/pages/MapViewPage.vue` — in the demo app
- `app/src/csapi-bridge.ts` — in the demo app

**Neither file is in our library repository.**

---

## Analysis

### The builder methods already exist and work correctly

Both methods referenced by Issue #21 are fully implemented in our library:

**`getDataStreamObservations()`** — `url_builder.ts` line 1348:

```typescript
getDataStreamObservations(id: string, options?: ObservationQueryOptions): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', id, 'observations', options);
}
```

Supports `phenomenonTime`, `resultTime` (including the special `latest` value), `cursor`, `limit`, and all standard query parameters via `ObservationQueryOptions`.

**`getSystemSamplingFeatures()`** — `url_builder.ts` line 484:

```typescript
getSystemSamplingFeatures(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', id, 'samplingFeatures', options);
}
```

Supports `limit`, `offset`, `bbox`, `datetime`, `q`, and all standard query parameters via `QueryOptions`.

Both methods have complete JSDoc documentation with `@example` blocks and `@see` links to the OGC spec. Both have corresponding unit tests in `url_builder.spec.ts`.

### This is a demo app code quality issue, not a library issue

The issue is labeled `enhancement` and its scope is entirely within the demo app:
- The code producing hardcoded URLs is in `MapViewPage.vue` (demo app)
- The proposed fix adds helpers in `csapi-bridge.ts` (demo app)
- The library's builder methods are already complete and correct

The [query parameter coverage audit](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-demonstration-coverage.md) lists these methods as "Not Demonstrated" — meaning the demo app doesn't exercise them, not that they don't work. The distinction between "Not Demonstrated" (demo app coverage gap) and "Missing" (library gap) is critical.

### The issue is Priority 1 in the demo app's own roadmap

The [query parameter coverage recommendations](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-coverage-recommendations.md) classify this as "Recommendation 1 — Priority 1 (Highest)" for the demo app's own improvement plan. This priority ranking reflects its importance to the demo app's quality, not to the library.

### No library source changes are proposed or needed

The issue does not propose any changes to:
- `url_builder.ts` — the builder methods are already correct
- `model.ts` — the type definitions are already correct
- `helpers.ts` — no helper changes needed
- `url_builder.spec.ts` — no test changes needed
- Any other file in `src/ogc-api/csapi/`

### Conservation record consistency

This follows the established pattern from Issues #18, #19, and the majority of prior findings: the issue is about consumer-layer code (the demo app), not the library. The library provides the correct tools; the consumer chose not to use them in one component.

---

## Recommendation

**NO ACTION REQUIRED** in our CSAPI client library contribution.

### Justification

1. **The builder methods already exist.** `getDataStreamObservations()` and `getSystemSamplingFeatures()` are fully implemented, documented, and tested in our library. There is no missing method, no bug, and no gap.

2. **The issue targets the demo app exclusively.** Every file identified for modification (`MapViewPage.vue`, `csapi-bridge.ts`) is in the `ogc-csapi-explorer` repository, not in our `ogc-client-CSAPI_2` library.

3. **"Not Demonstrated" ≠ "Not Working".** The coverage audit's "Not Demonstrated" label means the demo app doesn't exercise these methods — it does not indicate a library defect. The methods produce correct URLs as verified by unit tests.

4. **No library changes are proposed.** The issue itself does not request or suggest any changes to the library source code.

5. **Making changes would introduce risk with zero benefit.** The library code is correct. Touching it in response to a demo app code quality issue would violate §2.2 of the AI Operational Constraints ("Prefer minimal diffs over idealized rewrites") and §2.1 ("Do not expand scope beyond the issue description").

---

## Cross-References

| Document | Relevance |
|---|---|
| [AI Operational Constraints §2.1, §2.2](../../governance/AI_OPERATIONAL_CONSTRAINTS.md) | No scope expansion; minimal diffs; do not infer unstated requirements |
| [query-parameter-demonstration-coverage.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-demonstration-coverage.md) | Primary source: lists `getDataStreamObservations()` and `getSystemSamplingFeatures()` as "Not Demonstrated" in demo app |
| [query-parameter-coverage-recommendations.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-coverage-recommendations.md) | Recommendation 1 (Priority 1) IS Issue #21 — demo app improvement plan |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) | Establishes the pattern of replacing manual URLs with builder calls (for CRUD components; MapViewPage was not part of that integration) |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Confirms builder methods work correctly; assesses library contribution goal accuracy |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) | Finding #7 mentions `getObservationsForDatastream()` as missing — but `getDataStreamObservations()` exists (different name) |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md) | Finding #7 confirms cross-server context; builder methods are functional |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md) | Documents F-2 (missing nested create methods) — separate issue from #21 |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | Explains demo architecture bypassing `OgcApiEndpoint` — context for why MapViewPage uses direct builder |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | Phase 1 findings context (F-15, F-16) — unrelated to Issue #21 |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md) | Write operation context — unrelated to Issue #21 |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) | EndpointError refactor context — unrelated to Issue #21 |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | Confirms one library source change (e73cff8); no changes related to these methods |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | Schema method findings — unrelated to Issue #21 |
| [url_builder.ts](../../src/ogc-api/csapi/url_builder.ts) | `getDataStreamObservations()` at L1348; `getSystemSamplingFeatures()` at L484 — both fully implemented |
