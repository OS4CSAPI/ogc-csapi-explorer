# Findings Report: Issue #22 — Add Relationship-Based Filter: systemId Dropdown on Datastreams List

> **Date**: 2026-02-18
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#22](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/22) > **Labels on source issue**: `enhancement`

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the demo app's lack of relationship-based query filter usage indicates any bug, gap, or required change in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the `DatastreamQueryOptions.systemId` parameter, the `getDataStreams()` method, and the `buildQueryString()` serialization logic are all verified to already exist and work correctly.

---

## Executive Summary

Issue #22 proposes adding a "Filter by System" dropdown to the demo app's `ResourceList.vue` component that would pass `systemId` as a query filter when listing datastreams. The issue notes that the demo app never exercises any of the five relationship-based query filter parameters (`systemId`, `procedureId`, `foiId`, `observedPropertyId`, `controlledPropertyId`), even though the library fully supports them.

**This issue does not affect our CSAPI client library contribution.** The library already provides:

1. **`DatastreamQueryOptions.systemId`** (model.ts line 203) — typed as `string`, documented with JSDoc
2. **`getDataStreams(options?: DatastreamQueryOptions)`** (url_builder.ts line 1212) — accepts the options including `systemId`
3. **`buildQueryString()`** (url_builder.ts line 234) — correctly serializes `systemId` into the URL query string
4. **Unit tests** confirming `systemId` serialization (url_builder.spec.ts lines 1535–1537, 1563–1564)

Every file the issue proposes modifying — `ResourceList.vue` and `csapi-bridge.ts` — is in the demo app repository (`ogc-csapi-explorer`), not in our library.

**Recommendation: NO ACTION REQUIRED** in our CSAPI client library contribution.

---

## Issue Description

### What the issue reports

The demo app's `ResourceList.vue` component never passes relationship-based query filters when listing resources. From the issue:

| Parameter              | Status                        |
| ---------------------- | ----------------------------- |
| `systemId`             | Never passed as a list filter |
| `procedureId`          | Never passed as a list filter |
| `foiId`                | Never passed as a list filter |
| `observedPropertyId`   | Never passed as a list filter |
| `controlledPropertyId` | Never passed as a list filter |

The issue is classified as **Priority 2** from the [Query Parameter Coverage Recommendations](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-coverage-recommendations.md).

### What the issue proposes

Add a PrimeVue `Select` dropdown to the datastreams list page that:

1. Fetches available systems on mount using the existing `getSystems()` builder method
2. Displays system name + ID as dropdown options
3. Passes `systemId` into `DatastreamQueryOptions` on selection to re-fetch filtered datastreams
4. Removes the filter on clear to return the full unfiltered list

### Affected files (per the issue)

- `app/src/components/ResourceList.vue` — in the demo app
- `app/src/csapi-bridge.ts` — in the demo app

**Neither file is in our library repository.**

---

## Analysis

### The library already fully supports relationship-based query filters

All five relationship-based filter parameters are defined in our `model.ts` interfaces:

| Parameter              | Interface                   | Line          |
| ---------------------- | --------------------------- | ------------- |
| `systemId`             | `DatastreamQueryOptions`    | model.ts L203 |
| `systemId`             | `DeploymentQueryOptions`    | model.ts L169 |
| `systemId`             | `ControlStreamQueryOptions` | model.ts L229 |
| `observedPropertyId`   | `DatastreamQueryOptions`    | model.ts L205 |
| `controlledPropertyId` | `ControlStreamQueryOptions` | model.ts L231 |

The `buildQueryString()` method at url_builder.ts line 234 handles all of these correctly — it iterates over option entries, skips `undefined`/`null` values, and serializes each parameter using `URLSearchParams.append()`.

### Unit tests confirm correct serialization

Three dedicated `systemId` tests exist in url_builder.spec.ts:

```
Line 768-770:  getDeployments({ systemId: 'sys-001' })  → ?systemId=sys-001
Line 1535-1537: getDataStreams({ systemId: 'sys-001' })  → ?systemId=sys-001
Line 1563-1564: getDataStreams({ limit: 10, offset: 5, systemId: 'sys-001' }) → ?limit=10&offset=5&systemId=sys-001
Line 2031-2033: getControlStreams({ systemId: 'sys-001' }) → ?systemId=sys-001
```

All tests pass. The library correctly serializes `systemId` as a URL query parameter.

### The issue's code example contains inaccuracies (not library defects)

The issue shows:

```typescript
interface DataStreamQueryOptions {
  systemId?: string[]; // Filter datastreams by parent system ID(s)
}
builder.getDataStreams({ systemId: ['sys123'] }).buildUrl();
```

Two inaccuracies relative to our actual API:

1. **Type**: Our `systemId` is typed as `string`, not `string[]`. A single system ID string is the correct type per our implementation.
2. **Return value**: `getDataStreams()` returns a `string` directly — there is no `.buildUrl()` chain.

These are notation errors in the issue description, not indications of a library defect. The actual library API for this use case is:

```typescript
const url = builder.getDataStreams({ systemId: 'sys-001' });
// => "https://example.com/collections/iot/datastreams?systemId=sys-001"
```

### This is a demo app demonstration coverage gap, not a library gap

The distinction between "Not Demonstrated" and "Not Working" is critical:

- **"Not Demonstrated"** means the demo app's UI does not exercise the capability — this is a demo app coverage gap
- **"Not Working"** would mean the library fails to produce correct URLs — this is NOT the case

The [contribution-goal-accuracy-assessment](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) explicitly **verifies** that all 10 `QueryOptions` interfaces are correctly implemented, listing `systemId` among the verified parameters.

### No library changes are proposed or needed

The issue does not propose any changes to:

- `url_builder.ts` — `getDataStreams()` already accepts `systemId` via `DatastreamQueryOptions`
- `model.ts` — `DatastreamQueryOptions.systemId` is already defined and typed
- `url_builder.spec.ts` — `systemId` serialization is already tested
- Any other file in `src/ogc-api/csapi/`

---

## Recommendation

**NO ACTION REQUIRED** in our CSAPI client library contribution.

### Justification

1. **The query filter parameters already exist.** `DatastreamQueryOptions.systemId`, `observedPropertyId`, `ControlStreamQueryOptions.controlledPropertyId`, and all other relationship-based filter parameters are defined in model.ts and correctly serialized by `buildQueryString()`.

2. **The builder method already accepts these filters.** `getDataStreams(options?: DatastreamQueryOptions)` at url_builder.ts line 1212 passes options through to `buildQueryString()`, which produces the correct `?systemId=...` query string.

3. **Unit tests confirm correctness.** url_builder.spec.ts lines 1535–1537 and 1563–1564 test `systemId` serialization in `getDataStreams()` and verify the expected output.

4. **The issue targets the demo app exclusively.** Every file identified for modification (`ResourceList.vue`, `csapi-bridge.ts`) is in the `ogc-csapi-explorer` repository, not in our `ogc-client-CSAPI_2` library.

5. **All 13 reference documents confirm no library gap.** No reference document identifies any bug, defect, or missing capability in the library's relationship-based filter support. Documents #12 (query-parameter-demonstration-coverage.md) and #13 (query-parameter-coverage-recommendations.md) explicitly confirm the library supports these filters — the demo app simply doesn't use them.

6. **Making library changes would introduce risk with zero benefit.** The library code is correct and tested. Modifying it in response to a demo app UI enhancement would violate §2.2 of the AI Operational Constraints ("Prefer minimal diffs over idealized rewrites") and §2.1 ("Do not expand scope beyond the issue description").

---

## Cross-References

| Document                                                                                                                                                             | Relevance                                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| [AI Operational Constraints §2.1, §2.2](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)                                                                              | No scope expansion; minimal diffs; do not infer unstated requirements                                                                   |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md)       | Explicitly verifies all 10 QueryOptions interfaces including `systemId` as correct                                                      |
| [query-parameter-demonstration-coverage.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-demonstration-coverage.md)     | Lists relationship-based filters as "Not Demonstrated" — confirms library support exists but demo doesn't exercise it                   |
| [query-parameter-coverage-recommendations.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/query-parameter-coverage-recommendations.md) | Recommendation 2 (Priority 2) IS Issue #22 — proposes demo app changes only                                                             |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                             | Finding #7 confirms `buildQueryString()` serializes parameters correctly; demo passes limited options                                   |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                           | No finding addresses relationship-based filter serialization as broken                                                                  |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                       | Exhaustive gap analysis found no issue with relationship-based filter support                                                           |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md)       | Explains demo architecture; unrelated to query parameter filtering                                                                      |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                                 | F-15, F-16 findings about CRUD payloads; unrelated to query filters                                                                     |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                                   | Query parameter tests cover `limit`, `offset`, `q`; relationship filters not tested but not flagged as broken                           |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                           | Write operation findings; unrelated to query filter serialization                                                                       |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)                   | EndpointError refactor; unrelated to query parameters                                                                                   |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                         | Confirms no library source was changed for query filter reasons                                                                         |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                                   | Schema endpoint findings; unrelated to query filters                                                                                    |
| [url_builder.ts](../../src/ogc-api/csapi/url_builder.ts)                                                                                                             | `getDataStreams()` at L1212 accepts `DatastreamQueryOptions` including `systemId`; `buildQueryString()` at L234 serializes it correctly |
| [model.ts](../../src/ogc-api/csapi/model.ts)                                                                                                                         | `DatastreamQueryOptions.systemId` at L203; `ControlStreamQueryOptions.systemId` at L229; `DeploymentQueryOptions.systemId` at L169      |
| [url_builder.spec.ts](../../src/ogc-api/csapi/url_builder.spec.ts)                                                                                                   | `systemId` serialization tests at L768–770, L1535–1537, L1563–1564, L2031–2033                                                          |
