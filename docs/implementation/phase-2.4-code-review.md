# Phase 2.4 Code Review — SamplingFeatures Methods + Convention 3 Fixes

**Date:** 2025-02-14  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Scope:** Issue #8 (SamplingFeatures methods), Issue #39 (Convention 3 link detection fixes)  
**Commits:**

- `851cf1d` — `fix(csapi): strip query params and normalize featuresOfInterest in Convention 3 link detection`
- `ba3ecc0` — `feat(csapi): add SamplingFeatures methods to CSAPIQueryBuilder (#8)`

---

## Verification Status

| Check                                                          | Result                                              |
| -------------------------------------------------------------- | --------------------------------------------------- |
| `tsc --noEmit`                                                 | ✅ Clean                                            |
| CSAPI unit tests (url_builder, model, helpers)                 | ✅ 178 passing, 3 suites                            |
| Endpoint integration tests                                     | ✅ 82/83 passing (1 pre-existing non-CSAPI failure) |
| `assertResourceAvailable('samplingFeatures')` in all 8 methods | ✅ Verified — 8 occurrences                         |
| All `toBe()` assertions (no `toContain`)                       | ✅ Verified for all new tests                       |
| Lessons Learned L1–L10 compliance                              | ✅ All applied                                      |

---

## Files Reviewed

### Issue #39: Convention 3 Link Detection Fixes

| File                                | Lines Changed | Description                                                |
| ----------------------------------- | ------------- | ---------------------------------------------------------- |
| `src/ogc-api/csapi/helpers.ts`      | ~4            | Query param stripping + `featuresOfInterest` normalization |
| `src/ogc-api/csapi/helpers.spec.ts` | +28 (4 tests) | Tests for both fixes                                       |

### Issue #8: SamplingFeatures Methods

| File                                    | Lines Changed      | Phase 2.4 Lines  |
| --------------------------------------- | ------------------ | ---------------- |
| `src/ogc-api/csapi/url_builder.ts`      | +172 (793 → 965)   | Lines 2, 796–965 |
| `src/ogc-api/csapi/url_builder.spec.ts` | +200 (1079 → 1279) | Lines 1084–1279  |

**Total production code:** 176 new lines (Issue #39: 4, Issue #8: 172)  
**Total test code:** 228 new lines (Issue #39: 28, Issue #8: 200)  
**Test-to-code ratio:** 1.30:1 (good — more test code than production code)

---

## Overall Codebase Metrics (Cumulative)

| File                  | Lines    | Purpose                                                   |
| --------------------- | -------- | --------------------------------------------------------- |
| `model.ts`            | 582      | Type definitions, constants, 9 resource interfaces        |
| `model.spec.ts`       | 383      | 27 type compatibility + constant validation tests         |
| `helpers.ts`          | 213      | 7 utility functions (encoding, validation, link scanning) |
| `helpers.spec.ts`     | 273      | 38 helper function tests                                  |
| `url_builder.ts`      | 965      | CSAPIQueryBuilder — 36 public methods + 4 private helpers |
| `url_builder.spec.ts` | 1279     | 113 url_builder tests in 33 describe blocks               |
| **Total**             | **3695** | **178 tests**                                             |

---

## Prior Findings Status

### [P2-F1] RESOLVED: Dead `encodeArrayParameter` function

Fixed in Issue #38. No change.

### [P2-F2] RESOLVED: DRY violation in link-scanning logic

Fixed in Issue #38. No change.

### [P2-F3] RESOLVED: Strict-mode type safety in `buildResourceUrl`

Fixed in Issue #38. No change.

---

### [P2-F4] STILL OPEN: Weak datetime test for `getDeployments`

**File:** `src/ogc-api/csapi/url_builder.spec.ts` line 751  
**Status:** Unchanged. Still uses `toContain('datetime=')` instead of an exact `toBe()`. Now the _only_ `toContain` assertion in the entire url_builder spec (verified via grep — 1 occurrence at line 751). The contrast with the SamplingFeatures datetime test (line ~1127, exact `toBe()`) makes this more conspicuous.

### [P2-F5] STILL OPEN: Missing `parent` and `recursive` tests for `getDeployments`

**Status:** Unchanged. `DeploymentQueryOptions` supports `parent`, `systemId`, and `recursive`, but only `systemId` is tested.

### [P2-F6] STILL OPEN: Missing pagination test for `getDeploymentSubdeployments`

**Status:** Unchanged. Only tests no-options and `recursive=true`.

### [P2-F7] STILL OPEN: No test for cursor-based pagination

**Status:** Unchanged across all 4 resource types. `QueryOptions.cursor` has zero test coverage. This finding now applies to Systems, Deployments, Procedures, and SamplingFeatures.

### [P2-F8] FURTHER RESOLVED: No test for `offset` with actual value

**Status:** Now resolved for **Procedures** (line 920) and **SamplingFeatures** (line 1106). Still open for Systems and Deployments.

### [P1-F4] STILL OPEN: Missing exports from `index.ts` — GROWING

**Status:** The gap has grown. Current `index.ts` (lines 44–68) exports:

- ✅ `CSAPIQueryBuilder` (default export)
- ✅ `CSAPIResourceType`, `CommandStatusCode`, `SystemTypeUri` (union types)
- ✅ `TimeInterval`, `ResourceLink`
- ✅ `CSAPIQueryOptions` (alias for `QueryOptions`), `SystemQueryOptions`, `DeploymentQueryOptions`
- ✅ `DatastreamQueryOptions`, `ObservationQueryOptions`, `ControlStreamQueryOptions`, `CommandQueryOptions`
- ✅ All 9 resource interfaces + `CommandStatus`

**Still missing:**

- ❌ `CSAPIResourceTypes` (const array — needed for runtime iteration/validation)
- ❌ `CommandStatusCodes` (const array — needed for runtime validation)
- ❌ `SystemTypeUris` (const array — needed for runtime validation)
- ❌ `ProcedureQueryOptions` (type alias — consumers of `getProcedures` need this)
- ❌ `SamplingFeatureQueryOptions` (type alias — new in Phase 2.4)
- ❌ `PropertyQueryOptions` (type alias — needed for Phase 2.5)
- ❌ `FeatureCollection<T>`, `ItemCollection<T>` (generic collection wrappers)
- ❌ 10 collection type aliases (`SystemCollection`, `DeploymentCollection`, etc.)

The query options gap is now 3 missing vs 6 present. Any consumer using `getProcedures()` or `getSamplingFeatures()` in TypeScript strict mode will need to import the query options type — and they can't get it from the public API.

### [P1-F6] STILL OPEN: Hardcoded temporal parameter keys

**File:** `src/ogc-api/csapi/url_builder.ts` line 175  
**Status:** Unchanged. Still a chain of `||` comparisons. Will become more relevant in Phase 2 Part 2 (Issues #10–#13).

---

## Phase 2.4 Findings — New

### [F1] POSITIVE: SamplingFeatures tests are the most thorough yet

The 22 SamplingFeatures tests represent a clear progression in test quality:

| Quality metric             | Systems (P2.1)                 | Deployments (P2.2)  | Procedures (P2.3) | SamplingFeatures (P2.4) |
| -------------------------- | ------------------------------ | ------------------- | ----------------- | ----------------------- |
| Collection query tests     | 16                             | 4                   | 8                 | 10                      |
| Assertion style            | All `toBe`                     | Mixed (`toContain`) | All `toBe`        | All `toBe`              |
| `offset` test              | ❌                             | ❌                  | ✅                | ✅                      |
| `f` (format) test          | ❌                             | ❌                  | ✅                | ✅                      |
| `bbox` test                | ✅                             | ✅ (combined)       | — (unsupported)   | ✅ (standalone)         |
| `datetime` exact assertion | ✅ (single Date)               | ❌ (`toContain`)    | — (unsupported)   | ✅ (interval, exact)    |
| Resource validation        | Scattered                      | 1 of 8 checked      | 8 of 8 checked    | 8 of 8 checked          |
| Association pagination     | ❌ (subsystems yes, others no) | ❌                  | ✅                | ✅                      |

SamplingFeatures is the first resource type with standalone `bbox` and exact interval `datetime` tests alongside `offset`, `f`, and full validation coverage. The Lesson 1 checklist continues to produce measurably better test suites with each iteration.

---

### [F2] POSITIVE: Convention 3 link detection is now robust

Issue #39 addressed two latent bugs in `scanCsapiLinks()`:

**Fix 1 — Query parameter stripping (line 137 of helpers.ts):**

```typescript
// Before: href.replace(/\/+$/, '').split('/').pop()
// After:  href.split('?')[0].replace(/\/+$/, '').split('/').pop()
```

Servers like 52North append `?f=application/json` to items links. Without stripping, the segment `procedures?f=application/json` doesn't match any known resource type.

**Fix 2 — `featuresOfInterest` normalization (line 139 of helpers.ts):**

```typescript
const normalized =
  segment === 'featuresOfInterest' ? 'samplingFeatures' : segment;
```

52North uses the SOSA term `featuresOfInterest` while the spec uses `samplingFeatures`. This inline normalization handles the discrepancy at the discovery layer.

Both fixes have dedicated test coverage (4 tests at end of helpers.spec.ts). The original href is preserved in the map value — only the key is normalized. This is the correct design: the caller can still use the original href for requests.

---

### [F3] JSDoc documents `uid` as supported but type system doesn't include it

**Files:** `src/ogc-api/csapi/url_builder.ts` lines 801 and 632

Both `getSamplingFeatures` and `getProcedures` JSDoc state:

```
*   Sampling features support: `id`, `uid`, `q`, `bbox`, `datetime`, `limit`, `offset`, `f`.
*   Procedures support: `id`, `uid`, `q`, `limit`, `offset`, `f`.
```

But `uid` is not a field in `QueryOptions`, and both `SamplingFeatureQueryOptions` and `ProcedureQueryOptions` are plain type aliases to `QueryOptions`. A consumer reading the JSDoc would expect to pass `{ uid: 'urn:example:sf:001' }` — which TypeScript would reject in strict mode.

This was already noted in Issue #8's resolution comment. The JSDoc accurately reflects the OGC spec, but it doesn't reflect what the TypeScript type allows. Two possible resolutions:

1. Add `uid?: string` to `QueryOptions` (it applies to most resource types per spec)
2. Add `uid?: string` to each resource-specific query options type

**Severity:** Low — informational accuracy. The JSDoc serves as a contract reference for when `uid` support is added. No incorrect behavior.

---

### [F4] POSITIVE: Spec links correctly differentiated

All SamplingFeature methods correctly point to the right spec sections:

| Method                           | `@see` target                                    |
| -------------------------------- | ------------------------------------------------ |
| `getSamplingFeatures`            | `23-001/23-001.html#_sampling_feature_resources` |
| `getSamplingFeature`             | `23-001/23-001.html#_sampling_feature_resources` |
| `createSamplingFeature`          | `23-001/23-001.html#_sampling_feature_resources` |
| `updateSamplingFeature`          | `23-001/23-001.html#_sampling_feature_resources` |
| `deleteSamplingFeature`          | `23-001/23-001.html#_sampling_feature_resources` |
| `getSamplingFeatureSystems`      | `23-001/23-001.html#_sampling_feature_resources` |
| `getSamplingFeatureObservations` | `23-002/23-002.html#_observation_resources`      |
| `getSamplingFeatureHistory`      | `23-001/23-001.html#_sampling_feature_history`   |

`getSamplingFeatureObservations` correctly references Part 2 spec (`23-002`) since observations are a Part 2 resource — matching the pattern established by `getSystemDataStreams`, `getSystemControlStreams`, and `getProcedureDataStreams`. `getSamplingFeatureHistory` correctly uses the `_sampling_feature_history` anchor.

---

### [F5] POSITIVE: Correct method set — no sub-resource nesting

Like Procedures, SamplingFeatures are leaf resources in the CSAPI spec. The method set is exactly right:

- **CRUD:** get list, get single, create, update, delete (5 methods)
- **Associations:** systems observing at the feature, observations collected at the feature (2 methods)
- **History:** version history (1 method)

No missing methods. No extraneous methods. The choice of `observations` (Part 2 cross-reference) over `datastreams` as the second association is correct per spec — sampling features link to observations, not directly to datastreams.

---

### [F6] POSITIVE: SamplingFeatures datetime test uses exact interval assertion

**File:** `src/ogc-api/csapi/url_builder.spec.ts` line ~1127

```typescript
it('returns correct URL with datetime parameter', () => {
  const url = makeSfBuilder().getSamplingFeatures({
    datetime: {
      start: new Date('2024-01-01T00:00:00Z'),
      end: new Date('2024-12-31T23:59:59Z'),
    },
  });
  expect(url).toBe(
    'https://example.com/collections/iot/samplingFeatures?datetime=2024-01-01T00%3A00%3A00.000Z%2F2024-12-31T23%3A59%3A59.000Z'
  );
});
```

This is the most thorough datetime test in the spec:

- Uses interval form (start/end) — not just a single Date
- Uses exact `toBe()` — the full encoded ISO 8601 interval string
- Validates that the `/` separator between start and end is properly encoded as `%2F`

Contrast with Systems (line ~320, single Date with `toBe`) and Deployments (line 751, interval with `toContain`). The SamplingFeatures test proves the interval serialization and encoding are both correct.

---

### [F7] CONSISTENCY: `makeSfBuilder` follows established factory pattern

The `makeSfBuilder()` factory function is repeated identically in 6 of 7 SamplingFeature describe blocks. The 7th (resource validation) uses a different collection to test the error case.

This matches `makeProcBuilder()` (6 repeats), `makeDepBuilder()` (6 repeats), and `makeIotBuilder()` (14 repeats for Systems). The self-contained pattern is deliberate and consistent.

---

### [F8] INFORMATIONAL: Test count asymmetry across resource types

Current test distribution in `url_builder.spec.ts` (113 tests in 33 describe blocks):

| Section                 | describe blocks | Tests  | Notes                                           |
| ----------------------- | --------------- | ------ | ----------------------------------------------- |
| Constructor & discovery | 1               | 8      | Shared infrastructure                           |
| Resource validation     | 1               | 4      | Shared                                          |
| Top-level URLs          | 1               | 7      | Shared                                          |
| **Systems**             | **14**          | **38** | Oldest — most tests but missing offset/f/cursor |
| **Deployments**         | **6**           | **16** | Weakest — has all P2-F4/F5/F6 findings          |
| **Procedures**          | **6**           | **20** | First Lesson 1 compliant resource               |
| **SamplingFeatures**    | **7**           | **22** | Most thorough — all checklist items             |
| **Infra total**         | 3               | 19     |                                                 |
| **Resource total**      | 33              | 96     |                                                 |

Systems has the most tests (38) but the most gaps (no offset, no f, no cursor, scattered validation). This paradox exists because Systems was the first resource implemented before the test checklist was created. Test count alone is not a quality indicator — checklist compliance is.

---

## Test Quality Heatmap

This table shows which quality dimensions are covered for each resource type's collection query tests:

| Dimension                         | Systems        | Deployments      | Procedures | SamplingFeatures |
| --------------------------------- | -------------- | ---------------- | ---------- | ---------------- |
| No options (base URL)             | ✅             | ✅               | ✅         | ✅               |
| `limit`                           | ✅             | ✅ (combined)    | ✅         | ✅               |
| `offset` (standalone)             | ❌             | ❌               | ✅         | ✅               |
| `q`                               | ✅             | ❌               | ✅         | ✅               |
| `id` (single)                     | ❌             | ❌               | ✅         | ✅               |
| `id` (array)                      | ✅             | ❌               | ✅         | ✅               |
| `bbox`                            | ✅             | ✅ (combined)    | N/A        | ✅               |
| `datetime` (exact)                | ✅ (single)    | ❌ (`toContain`) | N/A        | ✅ (interval)    |
| `f` (format)                      | ❌             | ❌               | ✅         | ✅               |
| `cursor`                          | ❌             | ❌               | ❌         | ❌               |
| Multiple options                  | ✅             | ❌               | ✅         | ✅               |
| Type-specific params              | ✅ (6/6)       | ✅ (1/3)         | N/A        | N/A              |
| Resource validation (all methods) | ❌ (scattered) | ❌ (1 of 8)      | ✅ (8/8)   | ✅ (8/8)         |
| Association pagination            | Partial        | ❌               | ✅         | ✅               |

**Checklist compliance score:**

- Systems: 7/13 (54%)
- Deployments: 4/13 (31%)
- Procedures: 10/12 (83%) — 2 N/A (bbox, datetime)
- SamplingFeatures: 12/13 (92%)

---

## Summary

| Category                            | Count | Items                                                                                                                     |
| ----------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------- |
| Phase 2.2 findings resolved         | **3** | P2-F1, P2-F2, P2-F3 (no change from P2.3 review)                                                                          |
| Phase 2.2 findings further resolved | **1** | P2-F8 (offset — now fixed for Procedures AND SamplingFeatures)                                                            |
| Phase 2.2 findings still open       | **4** | P2-F4 (weak datetime), P2-F5 (parent/recursive), P2-F6 (pagination), P2-F7 (cursor)                                       |
| Phase 1 findings still open         | **2** | P1-F4 (exports — growing), P1-F6 (temporal keys)                                                                          |
| New — positive findings             | **5** | F1 (quality progression), F2 (Convention 3 robust), F4 (spec links), F5 (correct method set), F6 (datetime interval test) |
| New — informational                 | **2** | F3 (uid JSDoc vs type), F8 (test count asymmetry)                                                                         |
| New — consistency note              | **1** | F7 (factory pattern — by design)                                                                                          |
| **New bugs or design issues**       | **0** | —                                                                                                                         |

---

## Recommendations

### Fix Before Next Phase 2 Issue

1. **[P2-F4–F7] Backfill Deployment test gaps** — These have been open since the Phase 2.2 review (two phases ago). The SamplingFeatures tests now provide the gold standard. Estimated ~8 tests to add:

   - Strengthen `getDeployments` datetime to exact `toBe()` assertion
   - Add `getDeployments({ parent: 'dep-parent-001' })` test
   - Add `getDeployments({ recursive: true })` test
   - Add `getDeployments({ q: 'field' })` test
   - Add `getDeployments({ offset: 20 })` test
   - Add `getDeployments({ f: 'application/json' })` test
   - Add `getDeploymentSubdeployments` pagination+filtering test
   - Expand Deployment resource validation to cover all 8 methods

2. **[P2-F7] Add cursor test** — A single test for any one resource type would suffice to verify `buildQueryString` handles it correctly (since cursor flows through the generic parameter serialization path).

### Fix Before Phase 3

3. **[P1-F4] Add missing exports** — Growing to 16+ unexported types/constants. Blocking for any downstream consumer.
4. **[P1-F6] Extract temporal keys to a Set** — Before Part 2 resource methods.
5. **[F3] Add `uid` to query options types** — Create dedicated issue.

---

## Root Cause Analysis — Continued Zero Defects

Phase 2.4 is the second consecutive phase with zero new defects or design issues. The compound reasons:

### The Issue #39 effect

By fixing the Convention 3 bugs _before_ implementing SamplingFeatures methods (same session, earlier commit), we ensured the link discovery layer handles real-world server responses. The interoperability analysis that drove Issue #39 was itself a product of Lesson 8 (multi-server testing). The causal chain: Lesson 8 → 52North smoke test → interoperability analysis → Issue #39 → clean SamplingFeatures implementation.

### The checklist effect

The Lesson 1 test checklist has now been applied to two consecutive resource types (Procedures, SamplingFeatures) with zero defects each. The checklist items are:

1. Collection query with exact `toBe()` URL assertion
2. Every applicable query option tested individually
3. Single resource retrieval with exact URL
4. CRUD operations with exact URLs
5. Each nested/association method tested with and without options
6. Nested method with pagination + filtering
7. Resource validation failure — all methods in resource type throw
8. Temporal parameter with exact `toBe()` assertion

The heatmap above shows SamplingFeatures at 92% compliance (only `cursor` missing — which is a cross-cutting issue, not a SamplingFeatures gap). Procedures is at 83%. Both are materially above Systems (54%) and Deployments (31%), which were implemented before the checklist existed.

### The pattern maturity effect

By Phase 2.4, the code pattern for adding a new resource type is fully stabilized:

1. Add methods to `url_builder.ts` (copy-adapt from previous resource, change resource string and methods)
2. Add tests to `url_builder.spec.ts` (copy-adapt from best previous resource, apply full checklist)
3. Verify all 3 gates: `tsc --noEmit`, CSAPI tests, endpoint tests
4. Verify with grep that all `assertResourceAvailable` calls use correct string (Lesson 4)

This pattern will carry forward to Issues #9–#13. The remaining risk is test gaps in Systems and Deployments, which continue to age without correction.

---

## Overall Assessment

**Phase 2.4 is clean.** The 8 SamplingFeatures methods and 22 tests follow established patterns correctly. The Convention 3 fixes (Issue #39) improve interoperability. JSDoc is accurate (modulo the `uid` vs type system discrepancy). Spec links are correct. No new bugs.

The 6 still-open findings from prior reviews (P2-F4–F7, P1-F4, P1-F6) are becoming technical debt. P2-F4–F7 are 2 phases old, and P1-F4/P1-F6 have been open since Phase 1. The recommendation to backfill before the next resource type issue is now stronger — each new resource type that passes with a clean checklist makes the Deployments test gap more visible.

**The CSAPI module now has:**

- **36 public methods** across 4 resource types
- **178 tests** across 3 suites (27 model + 38 helpers + 113 url_builder)
- **3,695 lines** of production + test code
- **0 `toContain` assertions** in new code (only 1 remains, from Phase 2.2)
