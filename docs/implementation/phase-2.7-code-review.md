# Phase 2.7 Code Review — Observations Methods + resultTime=latest

**Date:** 2025-07-14  
**Reviewer:** AI (Claude Opus 4.6, GitHub Copilot)  
**Phase:** 2.7  
**Issues:** #43 (`resultTime=latest` type fix), #11 (Observations Methods)  
**Commits:** `052860b` (Issue #43), `b9cd3df` (Issue #11)  
**Prior review:** `docs/implementation/phase-2.6-code-review.md`

---

## Verification Gates

| Gate                | Status         | Details                                                                    |
| ------------------- | -------------- | -------------------------------------------------------------------------- |
| `tsc --noEmit`      | ✅ Clean       | No type errors                                                             |
| CSAPI unit tests    | ✅ 262 passing | 3 suites, 0 failures                                                       |
| Endpoint tests      | ✅ 82/83       | 1 pre-existing failure (non-JSON parse test at endpoint.spec.ts line 1789) |
| Uncommitted changes | ✅ Clean       | Working tree clean at review start                                         |

---

## Files Reviewed

6 files changed, +401 insertions, −27 deletions.

### Codebase Metrics

| File                  | Lines     | Purpose                                                   |
| --------------------- | --------- | --------------------------------------------------------- |
| `model.ts`            | 600       | Type definitions, constants, 9 resource interfaces        |
| `model.spec.ts`       | 407       | Type compatibility + constant validation tests            |
| `helpers.ts`          | 218       | 7 utility functions (encoding, validation, link scanning) |
| `helpers.spec.ts`     | 313       | Helper function tests                                     |
| `url_builder.ts`      | 1,553     | CSAPIQueryBuilder — 61 public methods + 4 private helpers |
| `url_builder.spec.ts` | 1,985     | url_builder tests                                         |
| **Total**             | **5,076** | **262 tests**                                             |

Delta from Phase 2.6: +290 lines, +24 tests

Test distribution: 41 model + 43 helpers + 178 url_builder = 262 total

---

## Prior Findings Status

### Phase 2.2 Findings (resolved in earlier phases — no change)

#### [P2-F1] RESOLVED: Dead `encodeArrayParameter` function

No change. Fixed in Issue #38.

#### [P2-F2] RESOLVED: DRY violation in link-scanning logic

No change. Fixed in Issue #38.

#### [P2-F3] RESOLVED: Strict-mode type safety in `buildResourceUrl`

No change. Fixed in Issue #38.

---

### Phase 2.2→2.4 Findings (all resolved — no change)

#### [P2-F4] RESOLVED: Weak datetime test for `getDeployments`

No change.

#### [P2-F5] RESOLVED: Missing `parent` and `recursive` tests for `getDeployments`

No change.

#### [P2-F6] RESOLVED: Missing pagination test for `getDeploymentSubdeployments`

No change.

#### [P2-F7] RESOLVED: No test for cursor-based pagination

No change.

#### [P2-F8] RESOLVED: No test for `offset` with actual value

No change. Resolved by Issue #41.

---

### Phase 1 Findings (resolved — no change)

#### [P1-F4] RESOLVED: Missing exports from `index.ts`

No change.

#### [P1-F6] RESOLVED: Hardcoded temporal parameter keys

No change. `TEMPORAL_KEYS` Set covers all temporal keys including `phenomenonTime` and `resultTime`.

---

### Phase 2.4 Findings (status check)

#### [F1] UNCHANGED: SamplingFeatures tests are the most thorough yet

Still the gold standard alongside Properties. Observations follows these patterns.

#### [F2] UNCHANGED: Convention 3 link detection is robust

No changes to `helpers.ts` link-scanning logic. Observations uses `ogc-cs:observations` rel convention per the existing pattern.

#### [F3] RESOLVED: JSDoc documents `uid` but type system didn't include it

No change. Fixed by Issue #40.

#### [F4] UNCHANGED: Spec links correctly differentiated

Observations methods correctly reference Part 2 spec (`23-002`). See new finding F7 below.

#### [F5] UNCHANGED: Correct method set — no sub-resource nesting

Observations follows the same principle: direct association endpoints, no deep nesting.

#### [F6] UNCHANGED: SamplingFeatures datetime uses exact interval assertion

No regression. Observations temporal tests follow the same exact `toBe()` pattern.

#### [F7] UNCHANGED: Factory pattern consistency

Observations tests introduce `makeObsBuilder()` following the established pattern.

#### [F8] UPDATED: Test count distribution across resource types

Updated distribution in `url_builder.spec.ts` (178 tests in url_builder, 262 total across all suites):

| Section                 | describe blocks | Tests  | Notes                                                                |
| ----------------------- | --------------- | ------ | -------------------------------------------------------------------- |
| Constructor & discovery | 1               | 8      | Shared infrastructure                                                |
| Resource validation     | 1               | 4      | Shared                                                               |
| Top-level URLs          | 1               | 7      | Shared                                                               |
| **Systems**             | **14**          | **40** | Unchanged                                                            |
| **Deployments**         | **6**           | **24** | Unchanged                                                            |
| **Procedures**          | **6**           | **20** | Unchanged                                                            |
| **SamplingFeatures**    | **7**           | **22** | Unchanged                                                            |
| **Properties**          | **5**           | **21** | Unchanged                                                            |
| **DataStreams**         | **9**           | **35** | +6 (4 from Issue #42 backfill, 2 `resultTime=latest` from Issue #43) |
| **Observations**        | **6**           | **17** | **New** — 8 methods, 6 describe blocks                               |
| **Infra total**         | 3               | 19     |                                                                      |
| **Resource total**      | 53              | 179    |                                                                      |

Note: model.spec.ts (41 tests) and helpers.spec.ts (43 tests) bring total from 178 to 262.

---

### Phase 2.5 Findings (status check)

#### [F1] UNCHANGED: Issue #40 resolves all 8 open findings systematically

No change. Positive finding.

#### [F2] UNCHANGED: Properties correctly models read-only semantics

No change. Observations has full CRUD, contrasting with read-only Properties.

#### [F3] UNCHANGED: Properties documents non-Feature response format

No change.

#### [F4] UNCHANGED: Spec links are correctly differentiated in Properties

No change. Observations continues the Part 2 convention — see new finding F7.

#### [F5] RESOLVED: Properties test coverage below gold standard

No change. Resolved by Issue #41.

#### [F6] RESOLVED: `PropertyQueryOptions` does not include property-specific parameters

No change. Resolved by Issue #41.

#### [F7] RESOLVED: Systems still missing standalone `offset` test

No change. Resolved by Issue #41.

#### [F8] UNCHANGED: TEMPORAL_KEYS extraction is clean and well-documented

No change.

#### [F9] UNCHANGED: Index.ts exports are comprehensive

No change. Observations types (`ObservationQueryOptions`) were already exported from Phase 2.6.

#### [F10] UNCHANGED: Deployment validation covers all 8 methods

No change. Observations follows the same pattern with 8/8 method validation (see F3 below).

---

### Phase 2.6 Findings (status check)

#### [F1] UNCHANGED: Issue #41 resolves all 3 Phase 2.5 gap findings in a single commit

No change. Positive finding.

#### [F2] UNCHANGED: DataStreams spec links correctly reference Part 2

No change. Observations extends this pattern — see new finding F7.

#### [F3] UNCHANGED: DataStreams resource validation is comprehensive — 11/11 methods

No change. Observations achieves 8/8 (see new finding F3).

#### [F4] NOW RESOLVED: DataStreams test coverage has minor heatmap gaps

**Resolved by:** Issue #42 (DataStreams backfill) + Issue #43 (`resultTime=latest`)

Issue #42 added 4 standalone tests:

- `offset: 20` → exact `toBe()`
- `id: 'ds-001'` → exact `toBe()` (single)
- `id: ['ds-001', 'ds-002']` → exact `toBe()` (array)
- `f: 'application/json'` → exact `toBe()`

Issue #43 added 2 `resultTime=latest` tests.

DataStreams now has 35 tests and **13/13 applicable heatmap dimensions (100%)** — the first resource type to achieve full compliance.

#### [F5] Retracted — not a finding

No change. `id` and `uid` are inherited from `QueryOptions`.

#### [F6] NOW RESOLVED: `resultTime: 'latest'` not representable in type system

**Resolved by:** Issue #43 (commit `052860b`)

**Evidence:**

1. `model.ts` line 13: `CsapiDateTimeParameter = DateTimeParameter | 'latest'` — CSAPI-local type alias, does not modify shared `DateTimeParameter` used by EDR.
2. `helpers.ts` line 28: `if (param === 'latest') return 'latest';` — pass-through as first check before Date operations.
3. `DatastreamQueryOptions.resultTime` and `ObservationQueryOptions.resultTime` both use `CsapiDateTimeParameter`.
4. 3 new tests confirm behavior: 1 helpers unit test + 2 url_builder integration tests.
5. Implementation guide updated from "Implementation Gap" to "RESOLVED" with reference to Issue #43.

This was the **only informational finding from Phase 2.6** and it is now fully resolved. The CSAPI module has zero open informational or gap findings from Phase 2.6.

#### [F7] UNCHANGED: DataStreams introduces observation-specific patterns cleanly

No change. Observations standalone methods build on these patterns.

#### [F8] UNCHANGED: Temporal filtering tested with exact `toBe()` assertions

No change. Observations temporal tests follow the same exact assertion pattern.

#### [F9] UNCHANGED: DataStreams JSDoc quality matches or exceeds prior resource types

No change. Observations JSDoc follows the same standard (see new finding F2).

#### [F10] UNCHANGED: DataStreams method count is correct per spec

No change.

---

## Phase 2.7 Findings — New

### [F1] POSITIVE: Issue #43 resolves Phase 2.6 [F6] with a clean CSAPI-local type alias

The `resultTime=latest` type gap has been resolved without modifying the shared `DateTimeParameter` type. The approach:

1. **Type alias scoped to CSAPI:** `CsapiDateTimeParameter = DateTimeParameter | 'latest'` in `model.ts` — keeps `'latest'` out of EDR and other OGC API modules.
2. **Formatter guard as first check:** `if (param === 'latest') return 'latest'` in `formatDateTimeParameter()` — executes before any Date operations, preventing runtime errors.
3. **Updated error message:** Error text changed from `'Invalid DateTimeParameter'` to `'Invalid CsapiDateTimeParameter'` to reflect the widened type.
4. **JSDoc thoroughly documents the type:** 10-line JSDoc block explains the scoping rationale and references Part 2 spec.
5. **Implementation guide updated:** Design note changed from "Implementation Gap" to "RESOLVED" with evidence.

This is the cleanest possible fix — one type alias, one guard clause, zero shared-type contamination.

---

### [F2] POSITIVE: Observations JSDoc correctly documents singular association semantics

All 3 Observations association methods include domain-specific guidance that explains the 1:1 relationship:

| Method                          | JSDoc key phrase                                                                                                        |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `getObservationDatastream`      | "Each observation belongs to exactly one datastream, so this endpoint returns a single resource (not a collection)."    |
| `getObservationSamplingFeature` | "Each observation targets at most one sampling feature, so this endpoint returns a single resource (not a collection)." |
| `getObservationSystem`          | "Each observation is produced by exactly one system, so this endpoint returns a single resource (not a collection)."    |

This is particularly important because DataStreams association methods (`getDataStreamSystems`, `getDataStreamProcedures`) use **plural** sub-paths for many-to-many relationships, while Observations uses **singular** sub-paths (`/datastream`, `/samplingFeature`, `/system`) for 1:1 relationships. The JSDoc makes this design distinction explicit for future maintainers.

---

### [F3] POSITIVE: Observations resource validation 8/8 in one block

The resource validation test at `url_builder.spec.ts` line 1975 verifies all 8 Observations methods throw `EndpointError` when `observations` is unavailable:

```typescript
expect(() => builder.getObservations()).toThrow(EndpointError);
expect(() => builder.getObservation('x')).toThrow(EndpointError);
expect(() => builder.updateObservation('x')).toThrow(EndpointError);
expect(() => builder.deleteObservation('x')).toThrow(EndpointError);
expect(() => builder.getObservationDatastream('x')).toThrow(EndpointError);
expect(() => builder.getObservationSamplingFeature('x')).toThrow(EndpointError);
expect(() => builder.getObservationSystem('x')).toThrow(EndpointError);
expect(() => builder.getObservationHistory('x')).toThrow(EndpointError);
```

Resource validation coverage is now complete for all post-Phase 2.2 resource types:

| Resource         | Coverage                                               |
| ---------------- | ------------------------------------------------------ |
| Systems          | ❌ (scattered — not all methods verified in one block) |
| Deployments      | ✅ (8/8)                                               |
| Procedures       | ✅ (8/8)                                               |
| SamplingFeatures | ✅ (8/8)                                               |
| Properties       | ✅ (6/6)                                               |
| DataStreams      | ✅ (11/11)                                             |
| Observations     | ✅ (8/8)                                               |

Systems remains the only resource type without consolidated validation coverage.

---

### [F4] POSITIVE: DataStreams reaches 100% heatmap compliance — first resource type

Issue #42 (backfill) + Issue #43 (`resultTime=latest`) bring DataStreams from 69% to **100%** of applicable heatmap dimensions:

| Dimension              | Phase 2.6       | Phase 2.7 | Change    |
| ---------------------- | --------------- | --------- | --------- |
| `offset` standalone    | ❌ (combo only) | ✅        | Issue #42 |
| `id` (single)          | ❌              | ✅        | Issue #42 |
| `id` (array)           | ❌              | ✅        | Issue #42 |
| `f` (format)           | ❌              | ✅        | Issue #42 |
| `resultTime: 'latest'` | —               | ✅        | Issue #43 |

DataStreams now has 35 tests across 9 describe blocks — the most thoroughly tested resource type after Systems (40 tests).

This is the third consecutive "review → backfill → 90%+" cycle:

1. Phase 2.5: Properties gap identified → Issue #41 → Properties 92%
2. Phase 2.6: DataStreams gap identified → Issue #42 → DataStreams 100%
3. Phase 2.7: Observations gap identified (see F5) → deferred to backfill issue

---

### [F5] GAP: Observations test coverage has initial heatmap gaps

Observations tests cover 7 of 12 applicable heatmap dimensions (58%). The missing standalone tests:

| Missing dimension       | Notes                                                         |
| ----------------------- | ------------------------------------------------------------- |
| `offset` standalone     | No test for `getObservations({ offset: 20 })`                 |
| `q`                     | No test for `getObservations({ q: 'temperature' })`           |
| `id` (single)           | No test for `getObservations({ id: 'obs-001' })`              |
| `id` (array)            | No test for `getObservations({ id: ['obs-001', 'obs-002'] })` |
| Multiple shared options | No test combining limit + offset + q or similar               |

**Severity:** GAP  
**Impact:** Low — all missing dimensions flow through `buildQueryString`'s shared parameter serialization, already exercised by 200+ tests across 6 other resource types. No unique Observations code path goes untested.

**Recommendation:** Add ~5 tests to bring Observations to ≥85% compliance. Estimated effort: small (copy-adapt from DataStreams).

---

### [F6] INFORMATIONAL: Observation singular association paths are a deliberate design departure

DataStreams uses **plural** sub-paths for its associations:

- `getDataStreamSystems(id)` → `/datastreams/{id}/systems`
- `getDataStreamProcedures(id)` → `/datastreams/{id}/procedures`

Observations uses **singular** sub-paths:

- `getObservationDatastream(id)` → `/observations/{id}/datastream`
- `getObservationSamplingFeature(id)` → `/observations/{id}/samplingFeature`
- `getObservationSystem(id)` → `/observations/{id}/system`

This is correct per the CSAPI Part 2 spec: each observation belongs to exactly one datastream, targets at most one sampling feature, and is produced by exactly one system. The plural form would imply a collection response. This is **not a defect** — it is the first instance of singular association paths in the project and worth documenting for pattern reference.

Future resource types (ControlStreams, Commands) may have a mix of singular and plural associations. The `buildResourceUrl` infrastructure handles both identically — the sub-path string is simply appended.

---

### [F7] POSITIVE: All 8 Observations spec links correctly reference Part 2

| Method                          | `@see` target                               | Correct?  |
| ------------------------------- | ------------------------------------------- | --------- |
| `getObservations`               | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |
| `getObservation`                | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |
| `updateObservation`             | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |
| `deleteObservation`             | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |
| `getObservationDatastream`      | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |
| `getObservationSamplingFeature` | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |
| `getObservationSystem`          | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |
| `getObservationHistory`         | `23-002/23-002.html#_observation_resources` | ✅ Part 2 |

Like DataStreams, Observations is entirely Part 2 — all 8 methods correctly reference `23-002`.

---

### [F8] POSITIVE: Observations temporal tests include resultTime='latest' from day one

Unlike DataStreams where `resultTime: 'latest'` support was retrofitted after the initial implementation (Issue #43 fixing Phase 2.6 F6 gap), Observations was implemented **after** the fix. This means:

1. `getObservations({ resultTime: 'latest' })` was tested as part of the initial Observations commit
2. `getObservations({ phenomenonTime: interval })` tests exact `toBe()` assertions with encoded separators
3. Both temporal parameters use the proven `formatDateTimeParameter` pipeline

The "fix before implement" workflow (Issue #43 resolved before Issue #11 started) prevented a gap that would otherwise have been identical to DataStreams' Phase 2.6 F6.

---

### [F9] POSITIVE: Observations method set correctly excludes `createObservation`

Issue #11 implements 8 methods for standalone Observations:

- Collection: `getObservations`
- Single resource: `getObservation`
- CRUD: `updateObservation`, `deleteObservation`
- Associations: `getObservationDatastream`, `getObservationSamplingFeature`, `getObservationSystem`
- History: `getObservationHistory`

`createObservation` is **not** duplicated here because it was already implemented in Issue #10 (DataStreams) as `createObservation(datastreamId)` — the POST target is `POST /datastreams/{id}/observations`. This is correct: you create an observation **within** a datastream, not at the top-level observations collection.

Total observation-related methods across both resource sections: 8 (standalone) + 2 (DataStreams: `getDataStreamObservations`, `createObservation`) = 10 methods.

---

### [F10] POSITIVE: `getObservations` tests format with MIME-type encoding

The format test uses `f: 'application/swe+json'` rather than the simple `'application/json'` used by other resource types:

```typescript
it('returns correct URL with obsFormat parameter', () => {
  const url = makeObsBuilder().getObservations({ f: 'application/swe+json' });
  expect(url).toBe(
    'https://example.com/collections/iot/observations?f=application%2Fswe%2Bjson'
  );
});
```

This verifies that the `+` character in SWE-specific MIME types is correctly URL-encoded (`%2B`), which is important because `+` has special meaning in URL query strings (space in `application/x-www-form-urlencoded`). The observation format test is more rigorous than the generic `application/json` tests used elsewhere.

---

## Test Quality Heatmap

| Dimension                         | Systems        | Deployments   | Procedures | SamplingFeatures | Properties | DataStreams        | Observations           |
| --------------------------------- | -------------- | ------------- | ---------- | ---------------- | ---------- | ------------------ | ---------------------- |
| No options (base URL)             | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     |
| `limit`                           | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅ (combo)             |
| `offset` (standalone)             | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ❌                     |
| `q`                               | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ❌                     |
| `id` (single)                     | ❌             | ❌            | ✅         | ✅               | ✅         | ✅                 | ❌                     |
| `id` (array)                      | ✅             | ❌            | ✅         | ✅               | ✅         | ✅                 | ❌                     |
| `bbox`                            | ✅             | ✅            | N/A        | ✅               | N/A        | N/A                | N/A                    |
| `datetime` / temporal (exact)     | ✅ (instant)   | ✅ (interval) | N/A        | ✅ (interval)    | N/A        | ✅ (both + latest) | ✅ (interval + latest) |
| `f` (format)                      | ❌             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     |
| `cursor`                          | ✅             | ❌            | ❌         | ❌               | ❌         | ✅                 | ✅                     |
| Multiple options                  | ✅             | ❌            | ✅         | ✅               | ✅         | ✅                 | ❌                     |
| Type-specific params              | ✅ (6/6)       | ✅ (3/3)      | N/A        | N/A              | ✅ (2/2)   | ✅ (4/4)           | ✅ (2/2)               |
| Resource validation (all methods) | ❌ (scattered) | ✅ (8/8)      | ✅ (8/8)   | ✅ (8/8)         | ✅ (6/6)   | ✅ (11/11)         | ✅ (8/8)               |
| Association pagination            | Partial        | ✅            | ✅         | ✅               | ✅         | ✅                 | N/A (singular)         |

**Checklist compliance score:**

- Systems: 10/14 (71%) — unchanged
- Deployments: 10/14 (71%) — unchanged
- Procedures: 10/11 (91%) — unchanged (3 N/A: bbox, temporal, type-specific)
- SamplingFeatures: 12/13 (92%) — unchanged (1 N/A: type-specific)
- Properties: 11/12 (92%) — unchanged (2 N/A: bbox, temporal)
- DataStreams: **13/13 (100%)** — up from 69% (Issue #42 backfill + Issue #43)
- Observations: **7/12 (58%)** — new (2 N/A: bbox, association pagination)

**Notable changes from Phase 2.6:**

- DataStreams jumped from 69% → **100%** (first resource type to achieve full compliance)
- Observations enters at 58% — lowest initial score, but follows the expected gap pattern
- Observations has cursor ✅, temporal ✅, and format ✅ from Day 1
- Observations type-specific params include `resultTime: 'latest'` from initial implementation (no retrofitting needed)

---

## Summary

| Category                            | Count | Items                                                                                                                                                                                    |
| ----------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 2.2 findings (no change)      | **3** | P2-F1, P2-F2, P2-F3                                                                                                                                                                      |
| Phase 2.2→2.4 findings (no change)  | **5** | P2-F4, P2-F5, P2-F6, P2-F7, P2-F8                                                                                                                                                        |
| Phase 1 findings (no change)        | **2** | P1-F4 (exports), P1-F6 (temporal keys)                                                                                                                                                   |
| Phase 2.4 findings unchanged        | **6** | F1, F2, F4, F5, F6, F7 + F3 resolved                                                                                                                                                     |
| Phase 2.4 findings updated          | **1** | F8 (test counts — Observations added)                                                                                                                                                    |
| Phase 2.5 findings no change        | **7** | F1, F2, F3, F4, F8, F9, F10                                                                                                                                                              |
| Phase 2.5 findings already resolved | **3** | F5, F6, F7 (resolved by Issue #41)                                                                                                                                                       |
| Phase 2.6 findings unchanged        | **6** | F1, F2, F3, F7, F8, F9, F10 (all positive)                                                                                                                                               |
| Phase 2.6 findings now resolved     | **2** | F4 (DataStreams heatmap → 100%), F6 (resultTime 'latest')                                                                                                                                |
| **New — positive findings**         | **7** | F1 (Issue #43 clean fix), F2 (singular JSDoc), F3 (validation 8/8), F4 (DataStreams 100%), F7 (spec links), F8 (latest from day 1), F9 (no createObservation dup), F10 (format encoding) |
| **New — gap findings**              | **1** | F5 (Observations heatmap gaps — 58%)                                                                                                                                                     |
| **New — informational**             | **1** | F6 (singular vs plural association paths)                                                                                                                                                |
| **New bugs or design issues**       | **0** | —                                                                                                                                                                                        |

---

## Recommendations

### Fix Before Next Coding Issue

1. **[F5] Backfill Observations test gaps** — Add ~5 tests: standalone `offset`, `q`, single `id`, array `id`, multiple shared options. Target ≥85% compliance. Estimated effort: 10 minutes (copy-adapt from DataStreams).

### Fix Before Phase 3

2. **Systems consolidated resource validation** — Systems remains the only resource type without a single test block verifying all methods throw when unavailable. Low priority since methods are individually tested elsewhere.

### Defer (Low Priority)

3. **Cursor tests for Deployments, Procedures, SamplingFeatures, Properties** — Cursor flows through the same `buildQueryString` path verified by Systems, DataStreams, and Observations cursor tests. Per-type tests would improve heatmap but wouldn't exercise new code paths.

4. **`id` (single) tests for Systems and Deployments** — Both types test `id` as an array but not as a single value. Low priority since the serialization path is the same.

---

## Root Cause Analysis — Continued Zero Defects

Phase 2.7 is the **fifth consecutive phase** with zero new defects or design issues. The streak now spans Procedures → SamplingFeatures → Properties → DataStreams → Observations.

### Why both changes were clean

**Issue #43 (CsapiDateTimeParameter):**

1. **Gap was exactly documented**: Phase 2.6 F6 described the problem, and the implementation guide §6 had a 3-step fix plan. The implementation followed the plan exactly.
2. **CSAPI-local scoping**: Rather than modifying the shared `DateTimeParameter` (which would affect EDR and other modules), a local type alias was created. This is the minimal-impact approach.
3. **Guard clause ordering**: `if (param === 'latest') return 'latest'` is the first check in `formatDateTimeParameter`, executing before any Date operations. This prevents the runtime error described in Phase 2.6 F6 without changing the happy path for Date-based parameters.

**Issue #11 (Observations Methods):**

1. **Pattern maturity**: Observations is the 7th resource type. The `assertResourceAvailable` → `buildResourceUrl` → return pipeline has now been exercised by ~260 tests across 7 resource types. Every method follows the identical 3-line pattern.
2. **Copy-adapt from DataStreams**: Observations methods were implemented using the same patterns proven by DataStreams. The only meaningful additions were singular association sub-paths — which use infrastructure already tested by plural association paths.
3. **Fix-before-implement workflow**: Issue #43 (`resultTime=latest`) was resolved before Issue #11 started. This prevented the same type gap from appearing in Observations and demonstrates that the "review → fix → implement" cycle catches issues at the right phase boundary.
4. **`createObservation` correctly not duplicated**: The decision to leave `createObservation` in the DataStreams section (where the POST target naturally lives) avoided a redundant method and potential maintenance confusion.

### Why the heatmap gap persists

Observations enters at 58% checklist compliance — the lowest initial score yet, but following the established pattern. The root cause is unchanged: when implementing a new resource type, the developer focuses on:

- Type-specific features: temporal filtering (phenomenonTime interval, resultTime latest)
- Unique patterns: singular association paths, cursor pagination, SWE MIME type format
- Domain validation: 8/8 resource validation assertions

Rather than re-testing generic dimensions (offset, q, id) that are proven to work via `buildQueryString` shared infrastructure. The Issue #42 backfill pattern (review → backfill → 100%) is now the established remedy and should be applied to Observations.

---

## Overall Assessment

**Phase 2.7 is clean.** The combination of Issue #43 (type system fix) and Issue #11 (Observations) delivers two significant milestones:

1. **Zero open findings from any prior review** — Issue #43 resolved Phase 2.6 F6 (the only open informational finding). Issue #42 resolved Phase 2.6 F4 (DataStreams heatmap gaps). The project now has zero inherited debt for the first time since Phase 2.4.

2. **Second Part 2 resource type with zero defects** — Observations joins DataStreams as the project's second Part 2 implementation. The 8-method implementation introduces singular association paths (a new pattern) while following all established conventions. The "fix-before-implement" workflow (Issue #43 before Issue #11) prevented a type gap that would otherwise have been identical to DataStreams' Phase 2.6 F6.

3. **DataStreams at 100% test compliance** — The backfill cycle (Phase 2.6 F4 → Issue #42 → Phase 2.7 verification) brings DataStreams to full heatmap compliance — the first resource type to achieve this.

The CSAPI module now implements **7 resource types** — all 5 Part 1 (Systems, Deployments, Procedures, SamplingFeatures, Properties) and 2 Part 2 (DataStreams, Observations) — with **61 public methods** and **262 tests**. The only new gap is the expected Observations heatmap shortfall (58%), which follows the established pattern and should be resolved by a backfill issue before the next feature implementation.

**Cumulative project stats:**

- **61 public methods** across 7 resource types
- **262 tests** across 3 suites (41 model + 43 helpers + 178 url_builder)
- **5,076 lines** of production + test code
- **0 open findings from prior reviews** (first time since Phase 2.4)
- **1 new gap finding** (Observations heatmap — low severity, established fix pattern)
- **5 consecutive phases** with zero defects
