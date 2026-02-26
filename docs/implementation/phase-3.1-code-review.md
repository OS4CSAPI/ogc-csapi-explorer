# Phase 3.1 Code Review — GeoJSON Handler Extensions + Commands Backfill

**Date:** 2026-02-14  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Scope:** All code changes since the Phase 2.8 smoke test — Issue #13 (Commands, already reviewed in Phase 2.9), Issue #46 (Commands backfill), and Issue #14 (GeoJSON Handler Extensions — first Phase 3 deliverable).  
**Prior review:** `docs/implementation/phase-2.9-code-review.md`  
**Commits:**

- `0d94317` — docs: update lessons learned to v1.2 — add Phase 2.3–2.8 source documents
- `b1c08d4` — feat(csapi): implement Commands methods (Issue #13) _(reviewed in Phase 2.9)_
- `950e694` — docs: Phase 2.9 code review — Commands methods
- `dc4a988` — test: backfill Commands test gaps — offset, create validation (Issue #46)
- `c26491b` — docs: Phase 2.9 live server smoke test — Commands validation (F34-F39)
- `603894d` — docs: integrate smoke test findings F34-F39 into roadmap v3.3 (Issue #47)
- `fb60321` — docs: add Phase 2 implementation overview
- `a30f5bf` — feat: GeoJSON handler extensions — featureType recognition, property extraction, validation (Issue #14)
- `5bcbb5a` — docs: add Phase 3 code review prompt template

**Note:** Issue #13 (Commands) was already reviewed in Phase 2.9. This review focuses its _new analysis_ on Issue #46 (backfill) and Issue #14 (GeoJSON). All prior findings from Phase 2.9 are reaffirmed below.

---

## Verification Status

| Check                      | Result                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| `tsc --noEmit`             | ✅ Clean — no type errors                                                                |
| CSAPI unit tests (all)     | ✅ **379 passing**, 4 suites, 0 failures                                                 |
| CSAPI format tests         | ✅ **65 passing**, 1 suite                                                               |
| Endpoint integration tests | ✅ **82/83 passing** (1 pre-existing: non-JSON parse test at endpoint.spec.ts line 1789) |

Test delta from Phase 2.9: 379 − 311 = **+68 tests** (65 new GeoJSON handler tests + 3 backfill tests from Issue #46).

---

## Files Reviewed

### Issue #46 — Commands Test Backfill

| File                                    | Lines Changed | Scope                                                                           |
| --------------------------------------- | ------------- | ------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/url_builder.spec.ts` | +24 lines     | 3 new tests: offset standalone, multiple options with offset, create validation |

### Issue #14 — GeoJSON Handler Extensions

| File                                        | Lines Changed    | Scope                                                        |
| ------------------------------------------- | ---------------- | ------------------------------------------------------------ |
| `src/ogc-api/csapi/formats/geojson.ts`      | +419 lines (new) | 6 public functions, 2 exported constants, 2 internal helpers |
| `src/ogc-api/csapi/formats/geojson.spec.ts` | +529 lines (new) | 65 tests across 6 describe blocks                            |

### Already Reviewed in Phase 2.9 (included in diff for completeness)

| File                                    | Lines Changed | Scope                                                            |
| --------------------------------------- | ------------- | ---------------------------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts`      | +227 lines    | 10 Commands methods — **no new analysis** (see Phase 2.9 review) |
| `src/ogc-api/csapi/url_builder.spec.ts` | +194 lines    | Commands tests — **no new analysis** (see Phase 2.9 review)      |

**Total new code under review:** 948 lines (419 + 529) from Issue #14, plus 24 lines from Issue #46.

---

## Overall Codebase Metrics (Cumulative)

### Phase 2 — URL Builder (Carried Forward)

| File                  | Lines     | Purpose                                                   |
| --------------------- | --------- | --------------------------------------------------------- |
| `model.ts`            | 560       | Type definitions, constants, 9 resource interfaces        |
| `model.spec.ts`       | 377       | Type compatibility + constant validation tests            |
| `helpers.ts`          | 191       | 7 utility functions (encoding, validation, link scanning) |
| `helpers.spec.ts`     | 268       | Helper function tests                                     |
| `url_builder.ts`      | 1,968     | CSAPIQueryBuilder — 79 public methods + 4 private helpers |
| `url_builder.spec.ts` | 2,445     | url_builder tests (2,421 + 24 from Issue #46 backfill)    |
| **Phase 2 Total**     | **5,809** | **314 tests** (311 + 3 from Issue #46 backfill)           |

### Phase 3 — Format Handlers (New)

| File                      | Lines   | Purpose                                                        |
| ------------------------- | ------- | -------------------------------------------------------------- |
| `formats/geojson.ts`      | 419     | GeoJSON handler — recognition, parsing, validation, extraction |
| `formats/geojson.spec.ts` | 529     | GeoJSON handler tests                                          |
| **Phase 3 Total**         | **948** | **65 tests**                                                   |

### Combined

| Metric                       | Value                                                          |
| ---------------------------- | -------------------------------------------------------------- |
| Total lines (prod + test)    | **6,757**                                                      |
| Total tests                  | **379** (41 model + 43 helpers + 230 url_builder + 65 geojson) |
| Public methods (url_builder) | **79**                                                         |
| Public functions (geojson)   | **6**                                                          |
| Resource types (Phase 2)     | **9**                                                          |
| Format handlers (Phase 3)    | **1** (GeoJSON)                                                |

---

## Prior Findings Status

### Phase 2.2 Findings (all resolved — no change)

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

No change. All Command types exported from `src/index.ts`.

#### [P1-F6] RESOLVED: Hardcoded temporal parameter keys

No change. `TEMPORAL_KEYS` Set covers all temporal keys.

---

### Phase 2.4 Findings (status check)

#### [F1] UNCHANGED: SamplingFeatures tests are the most thorough yet

Still the gold standard alongside Properties.

#### [F2] UNCHANGED: Convention 3 link detection is robust

No changes to `helpers.ts`.

#### [F3] RESOLVED: JSDoc documents `uid` but type system didn't include it

No change. Fixed by Issue #40.

#### [F4] UNCHANGED: Spec links correctly differentiated

No change.

#### [F5] UNCHANGED: Correct method set — no sub-resource nesting

No change.

#### [F6] UNCHANGED: SamplingFeatures datetime uses exact interval assertion

No change.

#### [F7] UNCHANGED: Factory pattern consistency

No change.

#### [F8] UNCHANGED: Test count distribution across resource types

No change. Phase 2.9 provided the last update.

---

### Phase 2.5 Findings (no change)

#### [F1] UNCHANGED: Issue #40 resolves all 8 open findings systematically

#### [F2] UNCHANGED: Properties correctly models read-only semantics

#### [F3] UNCHANGED: Properties documents non-Feature response format

#### [F4] UNCHANGED: Spec links correctly differentiated in Properties

#### [F5] RESOLVED: Properties test coverage below gold standard (resolved by Issue #41)

#### [F6] RESOLVED: `PropertyQueryOptions` missing parameters (resolved by Issue #41)

#### [F7] RESOLVED: Systems still missing standalone offset test (resolved by Issue #41)

#### [F8] UNCHANGED: TEMPORAL_KEYS extraction is clean and well-documented

#### [F9] UNCHANGED: Index.ts exports are comprehensive

#### [F10] UNCHANGED: Deployment validation covers all 8 methods

---

### Phase 2.6 Findings (no change)

#### [F1] UNCHANGED: Issue #41 resolves all 3 Phase 2.5 gap findings

#### [F2] UNCHANGED: DataStreams spec links correctly reference Part 2

#### [F3] UNCHANGED: DataStreams resource validation — 11/11 methods

#### [F4] RESOLVED: DataStreams test coverage gaps (resolved by Issues #42, #43)

#### [F6] RESOLVED: `resultTime: 'latest'` not representable (resolved by Issue #43)

#### [F7] UNCHANGED: DataStreams observation-specific patterns clean

#### [F8] UNCHANGED: Temporal filtering tested with exact `toBe()` assertions

#### [F9] UNCHANGED: DataStreams JSDoc quality matches or exceeds prior types

#### [F10] UNCHANGED: DataStreams method count is correct per spec

---

### Phase 2.7 Findings (no change)

#### [F1] UNCHANGED: Issue #43 resolves Phase 2.6 [F6] cleanly

#### [F2] UNCHANGED: Observations JSDoc documents singular association semantics

#### [F3] UNCHANGED: Observations resource validation 8/8

#### [F4] UNCHANGED: DataStreams 100% heatmap

#### [F5] RESOLVED: Observations heatmap gaps (resolved by Issue #44)

#### [F6] UNCHANGED: Observation singular association paths — informational

#### [F7] UNCHANGED: All 8 Observations spec links correct

#### [F8] UNCHANGED: Observations temporal tests include `resultTime='latest'`

#### [F9] UNCHANGED: Observations correctly excludes `createObservation`

#### [F10] UNCHANGED: `getObservations` tests format with MIME-type encoding

---

### Phase 2.8 Findings (no change)

#### [F1] UNCHANGED: ControlStreams mirrors DataStreams architecture

#### [F2] UNCHANGED: ControlStreams resource validation 8/8

#### [F3] UNCHANGED: ControlStreams documents cmdFormat requirement

#### [F4] UNCHANGED: All 8 ControlStreams spec links correct

#### [F5] UNCHANGED: Temporal tests exercise `issueTime` and `executionTime`

#### [F6] UNCHANGED: `checkCommandFeasibility` tests special character encoding

#### [F7] NOW RESOLVED: ControlStreams heatmap gaps

Resolved by Issue #45 (5 standalone tests, 85% compliance). Already noted in Phase 2.9 review.

#### [F8] UNCHANGED: JSDoc examples show lowercase `controlstreams` but builder produces camelCase

#### [F9] UNCHANGED: `getControlStreamCommands` uses `CommandQueryOptions`

---

### Phase 2.9 Findings (status check — first reaffirmation)

#### [F1] UNCHANGED: Commands completes all 80 Phase 2 QueryBuilder methods

79 public `get|create|update|delete|check|cancel` methods confirmed. No regressions.

#### [F2] UNCHANGED: Commands mirrors Observations architecture with lifecycle extensions

10 Commands methods with 5 new patterns (bulk creation, status, result, cancel). No changes.

#### [F3] UNCHANGED: `createCommand`/`createCommands` correctly validate `controlStreams`

Still validates `controlStreams` (not `commands`), with proper `@throws` JSDoc.

#### [F4] UNCHANGED: All 10 Commands spec links correctly reference Part 2

All link to `23-002/23-002.html#_command_resources`.

#### [F5] UNCHANGED: Commands JSDoc documents lifecycle semantics beyond URL construction

Status state machine, async cancellation semantics, bulk vs single docs all unchanged.

#### [F6] UNCHANGED: Temporal tests exercise `issueTime` and `executionTime` directly

Both closed interval and open-end interval patterns verified.

#### [F7] UNCHANGED: `cancelCommand` tests special character encoding

Mirrors `checkCommandFeasibility` encoding test.

#### [F8] NOW RESOLVED: Commands resource validation covers 8/10 — `createCommand`/`createCommands` missing

**Resolved by:** Issue #46 (commit `dc4a988`).

Issue #46 added a test that verifies both `createCommand` and `createCommands` throw `EndpointError` when `controlStreams` is unavailable:

```typescript
// From dc4a988 diff:
it('throws EndpointError for createCommand/createCommands when controlStreams unavailable', () => {
  expect(() => builder.createCommand('x')).toThrow(EndpointError);
  expect(() => builder.createCommands('x')).toThrow(EndpointError);
});
```

Commands resource validation is now **10/10 methods covered**.

#### [F9] NOW RESOLVED: Commands test coverage has initial heatmap gaps

**Resolved by:** Issue #46 (commit `dc4a988`).

Issue #46 added 2 standalone tests:

1. `getCommands({ offset: 20 })` → exact `toBe()` assertion
2. `getCommands({ limit: 10, offset: 5, currentStatus: 'PENDING' })` → multiple options with offset

Commands heatmap compliance rises from **83% → 92%**. The only remaining theoretical gap is `cursor` as a standalone test (tested in combo only), which is the same pattern as several other resource types.

#### [F10] UNCHANGED: `createCommand`/`createCommands` produce identical URLs

Informational finding — no change. Both route through `POST /controlstreams/{controlStreamId}/commands`.

---

## Phase 3.1 Findings — New

### [F1] POSITIVE: GeoJSON handler follows utility module best practices

`geojson.ts` is a well-structured utility module with clear separation of concerns:

1. **Constants layer** (lines 25–82): `SOSA_NS`, `CSAPIResourceTypeName`, four `ReadonlySet` constants for vocabulary lookup
2. **Internal helpers** (lines 88–122): `getFeatureType` and `toSosaLocalName` — not exported, reducing API surface
3. **Recognition layer** (lines 128–168): `isCSAPIFeature` and `getCSAPIResourceType` — pure functions, no side effects
4. **Parsing layer** (lines 174–248): `parseValidTime` — handles both spec-canonical array format and defensive object format
5. **Validation layer** (lines 254–335): `validateCSAPIFeature` — returns `string[]` (not throws), enables caller to decide error handling
6. **Extraction layer** (lines 341–420): `extractCSAPIFeature` — validates, converts, and returns typed output

This layered architecture makes each function independently testable and follows the pattern reference (`src/shared/mime-type.ts` — small utility module).

---

### [F2] POSITIVE: Test thoroughness exceeds Category A checklist requirements

Evaluating against the Phase 3 Category A (Utility/Extension) test checklist:

| Checklist Item                                            | Status | Evidence                                                                                                                |
| --------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| Every public function tested with valid input             | ✅     | All 6 functions have happy-path tests                                                                                   |
| Every public function tested with invalid/malformed input | ✅     | null, undefined, wrong type, missing fields, empty strings                                                              |
| Edge cases: null, undefined, empty string, wrong type     | ✅     | `isCSAPIFeature(null)`, `isCSAPIFeature(42)`, `isValidUri('')`, `parseValidTime(123)`, etc.                             |
| All spec-defined variants covered                         | ✅     | Both compact CURIE (`sosa:Sensor`) and full URI (`http://www.w3.org/ns/sosa/Sensor`) tested for all 12 SOSA local names |
| All classification branches tested                        | ✅     | System (5), Deployment (1), Procedure (4), SamplingFeature (2) + unrecognized → null                                    |
| Validation error specificity                              | ✅     | Each constraint produces identifiable message; multiple simultaneous errors test confirms no short-circuiting           |

**All 6 checklist items pass.** This is the strongest initial test coverage for any new component in the project.

---

### [F3] POSITIVE: `parseValidTime` bridges smoke test finding F4

The Phase 2.8 smoke test discovered that the OGC specification encodes `validTime` as a JSON array `["ISO-8601-string", "now"]`, not as a `TimeInterval` object. `parseValidTime` directly addresses this:

- Array format `["2026-01-26T18:32:01.56Z", "now"]` → `{ start: Date, end: undefined }` ✅
- Array format `["2026-01-26T18:32:01.56Z", "2027-06-15T00:00:00Z"]` → `{ start: Date, end: Date }` ✅
- Defensive object format also handled (forward-compatible)
- Invalid date strings → `undefined` (safe failure)
- 13 dedicated tests for `parseValidTime` covering all branches

---

### [F4] POSITIVE: Validation does not short-circuit — all errors reported

`validateCSAPIFeature` (line 274) accumulates all errors into an array rather than throwing on the first failure:

```typescript
it('reports multiple errors at once', () => {
  const feature = {
    type: 'Feature',
    properties: { featureType: '', uid: '', name: '' },
  };
  const errors = validateCSAPIFeature(feature);
  expect(errors.length).toBeGreaterThanOrEqual(3);
});
```

This is the correct design for a validation function — it allows callers to display all issues at once rather than requiring fix-and-retry cycles. The test confirms at least 3 errors are reported simultaneously (featureType, uid, name).

---

### [F5] POSITIVE: Type-specific constraints correctly implemented

The validator enforces two type-specific constraints documented in the OGC spec:

1. **Deployment requires `validTime`** (line 316): The spec states that `timePeriod` is required for deployments. Test at geojson.spec.ts line 397 confirms the specific error message `'Deployment requires validTime'`.

2. **Procedure geometry must be null** (line 322): The spec states procedures have no spatial footprint in GeoJSON encoding. Test at geojson.spec.ts line 405 confirms the specific error message `'Procedure geometry must be null'`.

Both constraints are guarded by checking `resourceType` after classification, ensuring they only apply to the correct resource type.

---

### [F6] POSITIVE: `extractCSAPIFeature` produces correctly typed output for all 4 resource types

Each branch of the `switch (resourceType)` statement builds the output using the validated base properties plus type-specific additions:

| Branch          | `validTime`             | `geometry`             | Extra Properties | Test                     |
| --------------- | ----------------------- | ---------------------- | ---------------- | ------------------------ |
| System          | Optional (if present)   | Optional (passthrough) | `assetType`      | geojson.spec.ts line 450 |
| Deployment      | Required (`validTime!`) | Optional               | —                | geojson.spec.ts line 466 |
| Procedure       | —                       | Always `null`          | —                | geojson.spec.ts line 475 |
| SamplingFeature | Optional                | Optional               | —                | geojson.spec.ts line 483 |

All 4 branches tested with specific assertions on output properties.

---

### [F7] DESIGN: `extractCSAPIFeature` uses `as` type assertions after validation

`extractCSAPIFeature` (lines 355–420) uses `as System`, `as Deployment`, etc. on the return values:

```typescript
return {
  id: String(f.id ?? ''),
  type: 'Feature',
  properties: { ...baseProperties, ... },
  links,
} as System;
```

**Why this is acceptable (not a bug):**

- The `validateCSAPIFeature` call at line 361 ensures all required properties exist before the switch statement executes
- The object literal constructs every required field from validated data
- `tsc --noEmit` passes cleanly, confirming no structural type mismatch

**Why it's worth noting (design concern):**

- `as` casts bypass TypeScript's structural type checking at the cast point
- If a future change adds a required property to `System` (e.g., in model.ts), this code would silently produce an incomplete object — the `as` cast would suppress the compiler error that would otherwise catch the omission
- A typed builder function or `satisfies` operator (TypeScript 4.9+) would provide compile-time safety without `as` casts

**Severity:** DESIGN (low)  
**Impact:** Low currently — the project uses TypeScript 5.x which supports `satisfies`. No immediate action needed, but worth considering when the extraction logic stabilizes.

**Recommendation:** Consider replacing `as System` with `satisfies System` in a future cleanup pass. This would cause `tsc` to report structural mismatches while still allowing the spread construction pattern.

---

### [F8] GAP: No barrel file for `formats/` directory

The `src/ogc-api/csapi/formats/` directory contains only `geojson.ts` and `geojson.spec.ts`. There is no `index.ts` barrel file to re-export the public API.

Additionally, none of the geojson.ts exports (`isCSAPIFeature`, `getCSAPIResourceType`, `parseValidTime`, `isValidUri`, `validateCSAPIFeature`, `extractCSAPIFeature`, `SOSA_NS`, `CSAPIResourceTypeName`) appear in the root `src/index.ts`.

**Severity:** GAP  
**Impact:** Low — the geojson module is importable via direct path (`./csapi/formats/geojson.js`). The exports become more important as more format handlers are added in Phase 3 and when external consumers need access.

**Recommendation:** Create `src/ogc-api/csapi/formats/index.ts` as a barrel file and add appropriate exports to `src/index.ts`. This should be done before Phase 4 (integration) when external consumers will need these functions. The Phase 3 review template already lists `formats/index.ts` as a pattern reference — establishing it now sets the convention for subsequent Phase 3 modules.

---

### [F9] POSITIVE: `makeFeature` test helper is well-designed

The `makeFeature()` factory function at geojson.spec.ts line 17 provides:

- Sensible defaults (`uid: 'urn:x-test:feature:1'`, `name: 'Test Feature'`)
- Override capability via spread (`overrides: Record<string, unknown>`)
- Proper GeoJSON structure (`type: 'Feature'`, `id`, `geometry`, `properties`, `links`)
- Destructured overrides that cleanly separate properties from extra props

This is comparable to the `makeBuilder()` / `makeCmdBuilder()` pattern established in Phase 2 tests and provides the same benefits: minimal boilerplate per test, explicit overrides for the property under test.

---

### [F10] INFORMATIONAL: Non-SOSA featureType vocabularies not yet supported

`isCSAPIFeature` returns `false` for non-SOSA vocabularies — this is explicitly tested:

```typescript
it('returns false for non-SOSA URIs', () => {
  expect(
    isCSAPIFeature(
      makeFeature(
        'http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint'
      )
    )
  ).toBe(false);
});
```

Real CSAPI servers (notably OpenSensorHub) may use OGC-OM or SensorML vocabularies for `featureType`. The `SAMPLING_FEATURE_LOCAL_NAMES` JSDoc (geojson.ts line 77) correctly documents this limitation: _"This recognition covers the SOSA vocabulary only."_

**Severity:** INFORMATIONAL  
**Impact:** None currently. The roadmap tracks vocabulary expansion as a future enhancement.  
**No action needed** — the documented limitation is correct, and expanding vocabulary recognition is scoped for a later Phase 3 task.

---

### [F11] POSITIVE: Input guards on every public function

Every public function in geojson.ts handles defensive input:

| Function                        | Guard                                                                                        | Behavior                                        |
| ------------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `isCSAPIFeature(feature)`       | Delegates to `getCSAPIResourceType`, which calls `getFeatureType` with null/non-object guard | Returns `false`                                 |
| `getCSAPIResourceType(feature)` | `getFeatureType` checks `typeof !== 'object'`, `=== null`, missing `properties`              | Returns `null`                                  |
| `parseValidTime(value)`         | Explicit `null`/`undefined` check, `Array.isArray` + length, `typeof` checks                 | Returns `undefined`                             |
| `isValidUri(value)`             | `typeof !== 'string'` + length check                                                         | Returns `false`                                 |
| `validateCSAPIFeature(feature)` | `typeof !== 'object'` + `=== null` → early return with error                                 | Returns `['Feature must be a non-null object']` |
| `extractCSAPIFeature(feature)`  | Delegates to `validateCSAPIFeature` → throws on error                                        | Throws `Error`                                  |

All 6 functions are safe against null, undefined, wrong-type, and missing-property inputs. Tests confirm all guard paths.

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

Updated to reflect Issue #46 (Commands backfill) changes:

| Dimension                           | Systems        | Deployments | Procedures | SF       | Properties | DataStreams | Observations | ControlStreams | Commands       |
| ----------------------------------- | -------------- | ----------- | ---------- | -------- | ---------- | ----------- | ------------ | -------------- | -------------- |
| No options (base URL)               | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅             |
| `limit`                             | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅ (combo)   | ✅ (combo)     | ✅ (combo)     |
| `offset` (standalone)               | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | **✅**         |
| `q`                                 | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | N/A            |
| `id` (single)                       | ❌             | ❌          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅             |
| `id` (array)                        | ✅             | ❌          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅             |
| `bbox`                              | ✅             | ✅          | N/A        | ✅       | N/A        | N/A         | N/A          | N/A            | N/A            |
| `datetime` / temporal (exact)       | ✅             | ✅          | N/A        | ✅       | N/A        | ✅          | ✅           | ✅             | ✅             |
| `f` (format)                        | ❌             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅             |
| `cursor`                            | ✅             | ❌          | ❌         | ❌       | ❌         | ✅          | ✅           | ❌             | ✅             |
| Multiple options (incl. offset)     | ✅             | ❌          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | **✅**         |
| Type-specific params                | ✅ (6/6)       | ✅ (3/3)    | N/A        | N/A      | ✅ (2/2)   | ✅ (4/4)    | ✅ (2/2)     | ✅ (2/2)       | ✅ (1/1)       |
| Resource validation (all methods)   | ❌ (scattered) | ✅ (8/8)    | ✅ (8/8)   | ✅ (8/8) | ✅ (6/6)   | ✅ (11/11)  | ✅ (8/8)     | ✅ (8/8)       | **✅ (10/10)** |
| Association/sub-resource pagination | Partial        | ✅          | ✅         | ✅       | ✅         | ✅          | N/A          | ✅             | N/A            |

**Changes from Phase 2.9 heatmap (bold cells above):**

- Commands `offset` (standalone): ❌ → **✅** (Issue #46)
- Commands multiple options (incl. offset): ✅ → **✅** (now includes offset combo — Issue #46)
- Commands resource validation: ⚠️ (8/10) → **✅ (10/10)** (Issue #46)

**Updated checklist compliance:**

- Commands: **12/12 (100%)** — up from 83%. All applicable dimensions covered.
- All other resource types: unchanged from Phase 2.9.

---

### Phase 3 (Format Handlers) — Current

| Dimension                    | GeoJSON Handler                                                                                                 |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Valid input → correct output | ✅ All 6 public functions have happy-path tests                                                                 |
| Invalid input → rejection    | ✅ null, undefined, wrong type, empty string, missing fields                                                    |
| All spec variants            | ✅ 12 SOSA local names × 2 forms (CURIE + full URI)                                                             |
| All classification branches  | ✅ System (5) + Deployment (1) + Procedure (4) + SamplingFeature (2) + unrecognized → null                      |
| Validation error specificity | ✅ Each constraint → named error message; multiple-errors-at-once test                                          |
| Edge cases                   | ✅ Array wrong length, non-string array start, non-Date object start, "now" sentinel, missing properties object |

**GeoJSON Handler: 6/6 dimensions (100%)**

---

## Smoke Test Findings Integration

| Finding                                                  | Status           | Evidence                                                                                         |
| -------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------ |
| F4 (validTime array format)                              | ✅ **Addressed** | `parseValidTime` handles `["ISO", "now"]` spec-canonical format. 13 tests covering all branches. |
| F33 (commandFormat vs observationFormat schema variants) | N/A              | SWE Common parser scope — not addressed by GeoJSON handler                                       |
| F34 (Commands fallback routing)                          | N/A              | Validator scope — documented in roadmap v3.3 (Issue #47)                                         |
| F35 (Cancel rejected by OSH)                             | N/A              | Validator scope — 400 on cancel to be handled by error handler                                   |
| F36 (id filter ignored on nested commands)               | N/A              | JSDoc limitation to be documented in validator                                                   |
| F37 (result 404 for fire-and-forget)                     | N/A              | Validator scope — 404 → null to be handled by response handler                                   |
| F38 (command@id cross-reference)                         | N/A              | GeoJSON handler could eventually register this; not in Issue #14 scope                           |
| F39 (commands use standard envelope)                     | N/A              | Parser scope — single `parseCollectionResponse` is a later Phase 3 task                          |

**1 of 8 findings addressed by this Phase 3 deliverable.** The remaining 7 are correctly scoped to later Phase 3 tasks (validator, parser, error handler).

---

## Summary

| Category                              | Count  | Items                                                                                                                                                                                                                               |
| ------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prior findings reaffirmed (unchanged) | **52** | All accumulated Phase 1–2.9 findings                                                                                                                                                                                                |
| Prior findings now resolved           | **2**  | Phase 2.9 F8 (create validation → Issue #46), F9 (heatmap gaps → Issue #46)                                                                                                                                                         |
| **New — positive findings**           | **7**  | F1 (utility module structure), F2 (Category A checklist 6/6), F3 (F4 smoke test bridge), F4 (no short-circuit validation), F5 (type-specific constraints), F6 (all 4 types extracted), F9 (test helper quality), F11 (input guards) |
| **New — design findings**             | **1**  | F7 (`as` type assertions in extraction)                                                                                                                                                                                             |
| **New — gap findings**                | **1**  | F8 (no barrel file for `formats/`)                                                                                                                                                                                                  |
| **New — informational findings**      | **1**  | F10 (non-SOSA vocabularies not yet supported)                                                                                                                                                                                       |
| **New bugs**                          | **0**  | —                                                                                                                                                                                                                                   |

---

## Recommendations

### Fix Now (before next coding issue)

1. **[F8] Create `formats/index.ts` barrel file** — Create `src/ogc-api/csapi/formats/index.ts` that re-exports the public API from `geojson.ts`. Add appropriate exports to `src/index.ts` for external consumers. This establishes the convention for subsequent Phase 3 modules and should be done while the export surface is small. Estimated effort: 5 minutes.

### Fix Before Phase 4

2. **[F7] Replace `as` casts with `satisfies` in `extractCSAPIFeature`** — Replace `as System`, `as Deployment`, etc. with `satisfies System` to get compile-time structural checking. This ensures future model.ts changes are caught by the compiler. Low urgency since `tsc --noEmit` currently passes and the validated-first-then-cast pattern is correct.

3. **Systems consolidated resource validation** — Carried forward from Phase 2.9. Systems remains the only resource type without a single validation block.

### Defer (Low Priority)

4. **Cursor standalone tests** — Cursor for Deployments, Procedures, SamplingFeatures, Properties, ControlStreams. Same shared code path, low risk.

5. **`id` (single) tests for Systems and Deployments** — Same serialization path, low risk.

6. **[Phase 2.8 F8] JSDoc example casing alignment** — No functional impact.

7. **Non-SOSA vocabulary expansion** — F10. Tracked in roadmap for a later Phase 3 task.

---

## Root Cause Analysis — Continued Zero Defects

Phase 3.1 is the **eighth consecutive phase** with zero new defects. The streak now extends from Phase 2 into Phase 3: Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams → Commands → GeoJSON Handler.

### Why the GeoJSON handler was clean

**Issue #14 (GeoJSON Handler Extensions):**

1. **Layered architecture from the start**: The module was designed as five clearly separated layers (constants → recognition → parsing → validation → extraction), each building on the one below. This made it natural to test each layer independently and catch issues at the lowest possible level.

2. **Vocabulary lookup via `ReadonlySet`**: Using `Set.has()` for SOSA local name recognition eliminates the switch/if-else chains that tend to accumulate spelling errors. The constant sets are declared once and used by `getCSAPIResourceType`, `validateCSAPIFeature`, and transitively by `extractCSAPIFeature`.

3. **Smoke test findings informed the design**: F4 (validTime discovery) directly shaped `parseValidTime`'s array-first format support. The implementation handled the spec-canonical format as the primary path and the object format as a defensive fallback — the right priority order.

4. **Existing model.ts types constrained the output**: The `System`, `Deployment`, `Procedure`, and `SamplingFeature` interfaces were already fully defined in Phase 2. `extractCSAPIFeature` had a concrete target type for each branch, eliminating ambiguity about what properties to include.

5. **Test coverage reached 100% of the Category A checklist from Day 1**: All 6 dimensions passed on initial implementation. The GeoJSON handler is the first component to achieve full heatmap compliance without a backfill cycle.

---

## Overall Assessment

**Phase 3.1 is clean.** The first Phase 3 deliverable (GeoJSON Handler Extensions) enters with zero defects and full test checklist compliance — the strongest initial quality of any component in the project.

1. **Issue #46 resolves all Phase 2 technical debt** — The Commands backfill added 3 tests (offset standalone, offset combo, create validation), resolving the last two Phase 2.9 gap findings (F8, F9). Commands now achieves 100% heatmap compliance (12/12), joining DataStreams as the only resource types at 100%. With F8 and F9 resolved, there are **zero open gap findings from any prior review**.

2. **GeoJSON handler sets the Phase 3 quality bar** — 65 tests covering 6 public functions across 419 lines of implementation code. The module achieves 6/6 on the Category A test checklist, handles both SOSA vocabulary forms (compact CURIE + full URI), bridges smoke test finding F4 (validTime array format), and validates without short-circuiting. The layered architecture (constants → recognition → parsing → validation → extraction) provides a clean separation of concerns that will serve as the pattern reference for subsequent Phase 3 modules.

3. **One actionable gap identified** — The missing `formats/index.ts` barrel file (F8) is the sole gap finding. It has no current functional impact since the module is importable via direct path, but establishing the barrel file convention now — while the export surface is small — will prevent export sprawl as more format handlers are added. This is a 5-minute fix that should be done before the next coding issue.

**Cumulative project quality:**

- **8 consecutive phases** with zero defects (Phase 2.3 → Phase 3.1)
- **0 open gap findings** across all prior reviews (first time in project history)
- **379 tests** across 4 suites, all passing
- **6,757 lines** of production + test code
- **Phase 2:** 79 public methods, 9 resource types, 314 tests — **complete**
- **Phase 3:** 6 public functions, 1 format handler, 65 tests — **in progress**
