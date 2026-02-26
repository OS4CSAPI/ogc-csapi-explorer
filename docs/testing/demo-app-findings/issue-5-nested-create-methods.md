# Issue #5 Findings Report — `createDataStream()` URL Generation and Missing Nested Create Methods

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) — "Fix createDataStream() URL generation and add missing nested create methods"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/url_builder.ts`)
> **Findings consolidated from:** F-1, F-2 (upstream findings), F-83 (amendment)
> **Labels:** bug, enhancement

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
9. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (23-001r1 Part 1, 23-002r1 Part 2) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #5 describes. No refactoring is proposed. All recommendations are purely additive (new methods alongside existing ones) or documentation-only.

---

## 2. Executive Summary

**Issue #5 is correct. The proposed changes are warranted and low-risk.**

The issue identifies two genuine gaps in `CSAPIQueryBuilder`:

| Finding  | Description                                                                                                                         | Severity | Risk of Fix    |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------- | -------------- |
| **F-1**  | `createDataStream()` generates top-level `/datastreams` URL; spec-compliant servers reject with 405                                 | High     | Low (additive) |
| **F-2**  | Three nested create methods missing (`createDataStreamForSystem`, `createControlStreamForSystem`, `createSamplingFeatureForSystem`) | Medium   | Low (additive) |
| **F-83** | Two additional nested create methods missing (`createSubsystem`, `createSubdeployment`)                                             | Medium   | Low (additive) |

**Key finding:** All proposed changes are **purely additive** — new methods added alongside existing ones. No existing method signatures change. No existing tests break. No behavioral modifications to any current code path. This is the lowest-risk category of library change.

---

## 3. Issue Description

### F-1: `createDataStream()` generates wrong URL

**Current code** (`url_builder.ts` L1255–1258):

```typescript
createDataStream(): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams');
}
```

This produces: `POST /collections/iot/datastreams` (top-level collection endpoint).

**OGC 23-002r1 §7.2** requires datastreams to be created as nested sub-resources of a System:
`POST /systems/{systemId}/datastreams`

**Evidence from live E2E testing:** OSH SensorHub returns `405 Method Not Allowed: "Datastreams can only be created within a System resource"` when POST is sent to the top-level `/datastreams` endpoint.

### F-2: Missing nested create methods

The library already has the correct nested pattern for observations and commands:

| Method                                     | Pattern                               | Status            |
| ------------------------------------------ | ------------------------------------- | ----------------- |
| `createObservation(datastreamId)`          | `POST /datastreams/{id}/observations` | ✅ Exists (L1371) |
| `createCommand(controlStreamId)`           | `POST /controlStreams/{id}/commands`  | ✅ Exists (L1873) |
| `createDataStreamForSystem(systemId)`      | `POST /systems/{id}/datastreams`      | ❌ Missing        |
| `createControlStreamForSystem(systemId)`   | `POST /systems/{id}/controlstreams`   | ❌ Missing        |
| `createSamplingFeatureForSystem(systemId)` | `POST /systems/{id}/samplingFeatures` | ❌ Missing        |

The library also has corresponding **GET** methods that produce the exact same base URLs:

| GET Method (exists)                    | Missing POST counterpart             |
| -------------------------------------- | ------------------------------------ |
| `getSystemDataStreams(id)` (L442)      | `createDataStreamForSystem(id)`      |
| `getSystemControlStreams(id)` (L463)   | `createControlStreamForSystem(id)`   |
| `getSystemSamplingFeatures(id)` (L484) | `createSamplingFeatureForSystem(id)` |

### F-83: Additional missing nested methods (Issue #5 amendment)

| Missing Method                  | Pattern                                 | Spec Reference    |
| ------------------------------- | --------------------------------------- | ----------------- |
| `createSubsystem(parentId)`     | `POST /systems/{id}/subsystems`         | OGC 23-001r1 §7.2 |
| `createSubdeployment(parentId)` | `POST /deployments/{id}/subdeployments` | OGC 23-001r1 §9.2 |

The corresponding GET methods already exist:

- `getSystemSubsystems(id)` (L421) → `GET /systems/{id}/subsystems`
- `getDeploymentSubdeployments(id)` (L653) → `GET /deployments/{id}/subdeployments`

---

## 4. Source Code Review

### 4.1 The `buildResourceUrl()` method (L199–219)

```typescript
private buildResourceUrl(
  resourceType: string,
  id?: string,
  subPath?: string,
  options?: QueryOptions
): string {
  const topLevelUrl = this.resourceUrls_.get(resourceType);
  const resourceBase = topLevelUrl
    ? topLevelUrl.replace(/\/+$/, '')
    : `${this.baseUrl}/${resourceType}`;
  let url = resourceBase;
  if (id) url += `/${encodeResourceId(id)}`;
  if (subPath) url += `/${subPath}`;
  return url + this.buildQueryString(options);
}
```

This method already fully supports the nested URL pattern. Adding new methods requires zero changes to `buildResourceUrl()`. The proposed methods follow the exact same `this.buildResourceUrl(parentType, parentId, childType)` pattern already used by `createObservation()` and `createCommand()`.

### 4.2 Existing correct nested create pattern

```typescript
// L1371 — correct nested pattern for observations
createObservation(datastreamId: string): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', datastreamId, 'observations');
}

// L1873 — correct nested pattern for commands
createCommand(controlStreamId: string): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
}
```

### 4.3 Existing correct nested GET pattern

```typescript
// L442 — nested GET (the POST counterpart is missing)
getSystemDataStreams(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', id, 'datastreams', options);
}
```

### 4.4 Current `createDataStream()` (L1255)

```typescript
createDataStream(): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams');
}
```

This method produces the top-level collection URL. Whether this should be deprecated, documented, or removed is a design decision discussed in §7.

### 4.5 Test file (`url_builder.spec.ts`)

298 existing tests, all passing. The current test for `createDataStream()` (L1628–1631) asserts the top-level URL:

```typescript
it('createDataStream returns correct URL', () => {
  const url = makeDsBuilder().createDataStream();
  expect(url).toBe('https://example.com/collections/iot/datastreams');
});
```

New tests would be needed for the new methods but would not affect existing tests.

---

## 5. Reference Document Review

All 12 linked reference documents from the ogc-csapi-explorer repository were reviewed. Key corroboration:

### 5.1 Library Findings Gap Analysis

- **F-1** rated **High severity**, **Priority 1** (highest), **Low implementation risk**
- **F-2** rated **Medium severity**, **Priority 1**, **Low implementation risk**
- Notes the API inconsistency: GET nested methods exist but POST nested methods do not
- Actionability: "Straightforward — add 3 new methods following existing patterns"

### 5.2 E2E Write Operations Report

- **14/15 core CRUD tests passed**; the 1 failure was `createDataStream()` → 405
- Server explicitly returned: `"Datastreams can only be created within a System resource"`
- Test used `getSystemDataStreams(systemId)` as the POST target URL as a workaround — confirmed working
- Key verdict: "The library generates correct URLs for all CRUD operations. Every failure was caused by [...] Missing library methods"

### 5.3 Library Integration Report (Finding #12, #13)

- Finding #12: "Create/Update/Delete Methods Are Symmetric with Get Methods" — ✅ confirmed working
- Finding #13: "Nested Creation Methods Work Correctly" — ✅ `createObservation(datastreamId)` and `createCommand(controlStreamId)` produce correct URLs
- The asymmetry (nested GET exists but nested POST doesn't) is the gap being addressed

### 5.4 Cross-Server Interoperability Report

- OSH SensorHub: Full CRUD cycle passes for systems, procedures, deployments
- 52North: Read-only (401 on POST)
- The nested create gap was confirmed across both servers

### 5.5 Library Source Changes Audit

- Only **one commit** (`e73cff8`) has modified library source (`src/`) during the entire demo app lifecycle
- That commit was the `EndpointError` isolation refactor — purely structural, zero behavioral change
- All other workarounds implemented exclusively in `demo/` or `docs/`
- This confirms the library source is clean and suitable for additional targeted changes

### 5.6 Contribution Goal Accuracy Assessment

- Validates that the library is "specification-scoped" with 82 methods covering all 9 CSAPI resource types
- F-1 confirmed as a genuine bug: "the createDataStream() method generates a top-level URL that spec-compliant servers reject"
- V-6 (CRUD URL symmetry) and V-7 (nested creation for observations/commands) verified working

### 5.7 Conformance Bypass Architecture Notes

- The demo app bypasses `OgcApiEndpoint` and uses `CSAPIQueryBuilder` directly
- This bypass is what exposed the F-1/F-2 gaps — a consumer using `OgcApiEndpoint` would never reach the point of discovering these issues due to conformance gating
- Validates that the library's internal modules are being genuinely exercised

### 5.8 AI Operational Constraints

- Authority precedence: OGC spec says nested creation is required → library should support it
- No scope expansion: Issue #5 is tightly scoped to 5 new methods + potential deprecation of 1 existing method
- Minimal diffs: Each new method is 3–4 lines following an existing pattern
- No refactoring: Internal architecture unchanged; `buildResourceUrl()` not modified

---

## 6. Risk Assessment

### 6.1 What could go wrong?

| Risk                                              | Likelihood           | Mitigation                                                                                                                                                                    |
| ------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New methods break existing tests                  | **None**             | Purely additive — no existing code changes                                                                                                                                    |
| New methods produce wrong URLs                    | **Very low**         | Follow exact same `buildResourceUrl()` pattern as `createObservation()`/`createCommand()`                                                                                     |
| Deprecating `createDataStream()` breaks consumers | **None if Option B** | Option B (non-breaking) adds new method alongside existing one                                                                                                                |
| Naming convention mismatch                        | **Low**              | `createDataStreamForSystem(systemId)` follows the issue's proposed naming; alternative `createSystemDataStream(systemId)` follows existing `getSystemDataStreams(id)` pattern |

### 6.2 Risk classification

**This is a LOW RISK, HIGH VALUE change.**

- **Low risk** because:

  - All changes are purely additive (new methods)
  - The internal machinery (`buildResourceUrl`) already fully supports the pattern
  - Two existing methods (`createObservation`, `createCommand`) prove the pattern works
  - Five existing GET methods (`getSystemDataStreams`, `getSystemControlStreams`, `getSystemSamplingFeatures`, `getSystemSubsystems`, `getDeploymentSubdeployments`) produce the exact same base URLs
  - 298 existing tests remain untouched

- **High value** because:
  - F-1 prevents datastream creation against spec-compliant servers (confirmed 405 error)
  - The workaround (repurposing a GET method URL for POST) is fragile and semantically incorrect
  - The API inconsistency (GET nested methods exist but POST nested methods don't) confuses consumers

### 6.3 Integrity assessment

The library's integrity is not at risk from this change. The change:

- Does **not** modify `buildResourceUrl()`
- Does **not** modify any existing method signature or behavior
- Does **not** change the test suite
- Does **not** add new dependencies
- Does **not** change the public API surface (it extends it)
- Does **not** require changes to `model.ts`, `helpers.ts`, or any format parser

---

## 7. Recommendation

### Primary recommendation: **Proceed with Issue #5 using Option B (non-breaking additive approach)**

#### 7.1 Add 5 new methods

```typescript
// F-2: Nested create methods for system child resources
createDataStreamForSystem(systemId: string): string
createControlStreamForSystem(systemId: string): string
createSamplingFeatureForSystem(systemId: string): string

// F-83: Nested create methods for hierarchical resources
createSubsystem(parentId: string): string
createSubdeployment(parentId: string): string
```

Each method is 3–4 lines following the exact pattern of `createObservation()`.

#### 7.2 Do NOT modify `createDataStream()` at this time

The existing `createDataStream()` method should be preserved as-is for now:

- It correctly produces the top-level `/datastreams` collection URL
- Some servers may support top-level datastream creation (the spec's language is not universally interpreted as prohibiting it)
- Changing its signature would be a breaking change
- A `@deprecated` JSDoc annotation could be added in a follow-up, after confirming wide spec interpretation

#### 7.3 Add corresponding unit tests

New tests for each new method, following the existing test structure. Approximately 10–15 new test cases (basic URL generation, special character encoding, resource availability assertion).

#### 7.4 Implementation order

1. Add the 5 new methods to `url_builder.ts`
2. Add unit tests to `url_builder.spec.ts`
3. Verify all 298 existing tests still pass
4. Optionally add `@deprecated` JSDoc to `createDataStream()` pointing to `createDataStreamForSystem()`

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source                     | Says About Nested Creation                                         | Weight     |
| --------------- | -------------------------- | ------------------------------------------------------------------ | ---------- |
| 1 (Highest)     | OGC 23-002r1 §7.2          | "Datastreams are created as sub-resources of Systems"              | Definitive |
| 2               | AI Collaboration Agreement | Spec is primary authority                                          | Confirms   |
| 3               | Issue #5                   | Proposes additive methods + optional deprecation                   | Scoping    |
| 4               | Existing code              | `createObservation()`/`createCommand()` already use nested pattern | Precedent  |
| 5               | Demo app testing           | 405 error from OSH confirms spec interpretation                    | Evidence   |

All authority levels align: nested creation is the correct pattern, and the library should support it.

---

## Appendix B: Cross-Reference Matrix

| Document                                 | Location           | Relevance to Issue #5                                        |
| ---------------------------------------- | ------------------ | ------------------------------------------------------------ |
| upstream-findings.md                     | ogc-csapi-explorer | F-1/F-2 consolidated findings with priority ranking          |
| library-findings-gap-analysis.md         | ogc-csapi-explorer | Detailed F-1/F-2 breakdown, severity ratings, code examples  |
| e2e-write-operations-report.md           | ogc-csapi-explorer | Live server evidence: 405 error, 14/15 tests pass            |
| e2e-cross-server-report.md               | ogc-csapi-explorer | Cross-server validation: OSH full CRUD, 52N read-only        |
| library-integration-report.md            | ogc-csapi-explorer | Findings #12 (CRUD symmetry) and #13 (nested creation works) |
| contribution-goal-accuracy-assessment.md | ogc-csapi-explorer | Validates F-1 bug, confirms spec-scoped library              |
| library-source-changes-audit.md          | ogc-csapi-explorer | Confirms clean library source, only 1 prior commit           |
| conformance-bypass-architecture-notes.md | ogc-csapi-explorer | Explains why bypass exposed these gaps                       |
| crud-smoke-test-findings.md              | ogc-csapi-explorer | F-15/F-16 additional findings (separate from Issue #5)       |
| endpoint-error-isolation-report.md       | ogc-csapi-explorer | EndpointError refactor context (e73cff8)                     |
| schema-display-findings.md               | ogc-csapi-explorer | F-13/F-14 schema findings (separate from Issue #5)           |
| AI_OPERATIONAL_CONSTRAINTS.md            | ogc-client-CSAPI_2 | Authority precedence, no scope expansion, minimal diffs      |

---

## Conclusion

Issue #5 is well-documented, well-evidenced, and proposes changes that are:

1. **Correct** — aligned with OGC 23-002r1 spec requirements
2. **Consistent** — follows the exact pattern already used by `createObservation()` and `createCommand()`
3. **Non-breaking** — purely additive new methods, no existing behavior modified
4. **Low-risk** — relies on `buildResourceUrl()` which already handles the nested pattern
5. **Well-tested** — proven via E2E testing against live servers (OSH SensorHub 405 error confirms the gap)

The recommended approach is Option B: add the 5 new methods alongside existing ones without modifying `createDataStream()`. This preserves library integrity while addressing the specification compliance gap.
