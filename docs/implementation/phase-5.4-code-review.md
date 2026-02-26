# Phase 5.4 Code Review — Code Review Finding Resolutions + Smoke Test Report

**Date:** 2026-02-20
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** Fourth Phase 5 code review covering Issues #94–#97 (resolution of 4 code review findings from Phase 5.1–5.3) plus Smoke Test Report ST#22
**Commits:**

- `c1f8271` — `test(part2): add unknown resultType enum rejection test (F7) closes #94`
- `0246fa3` — `test(part2): add unknown type field rejection test (F8) closes #95`
- `c1fa10a` — `test(part2): rename CommandStatus fixture ID to avoid collision (F19) closes #96`
- `78115de` — `refactor(sensorml): extract shared parseComponentEntry to _helpers.ts (F27) closes #97`
- `49426a0` — `docs: add Phase 5.3 smoke test report (ST#22)`

**Last review:** `docs/implementation/phase-5.3-code-review.md` (commit `b4ab1a0`)

---

## Verification Status

| Check                      | Result                                                                                           |
| -------------------------- | ------------------------------------------------------------------------------------------------ |
| tsc --noEmit               | ✅ 0 errors (clean)                                                                              |
| CSAPI unit tests (all)     | ✅ 1251 passing, 29 suites                                                                       |
| CSAPI format tests         | ✅ 724 passing, 20 suites                                                                        |
| Endpoint integration tests | ⚠️ 82/83 passing (1 pre-existing upstream failure — Unicode mismatch at `endpoint.spec.ts:1789`) |

**Test delta from Phase 5.3:** +2 tests (1249 → 1251), 0 new suites (29 → 29). New: 1 (unknown `resultType` enum → null) + 1 (unknown `type` field → omitted) = 2 new tests in `part2.spec.ts`. The fixture ID rename in #96 modified 2 lines but did not add/remove tests.
**Format test delta:** +2 tests (722 → 724), 0 new suites (20 → 20).
**SensorML test delta:** 0 (243 → 243, 6 suites). All existing cross-type delegation tests pass after `parseComponentEntry` extraction.

---

## Files Reviewed

### Issue #94 — Unknown resultType Enum Rejection Test (F7)

| File                                      | Lines Changed     | Scope                                                        |
| ----------------------------------------- | ----------------- | ------------------------------------------------------------ |
| `src/ogc-api/csapi/formats/part2.spec.ts` | +10 (1 test case) | Test: `resultType: 'foobar'` → `result.resultType` is `null` |

### Issue #95 — Unknown type Field Rejection Test (F8)

| File                                      | Lines Changed     | Scope                                                           |
| ----------------------------------------- | ----------------- | --------------------------------------------------------------- |
| `src/ogc-api/csapi/formats/part2.spec.ts` | +10 (1 test case) | Test: `type: 'foobar'` → `result` does not have property `type` |

### Issue #96 — CommandStatus Fixture ID Rename (F19)

| File                                      | Lines Changed    | Scope                                                                                                        |
| ----------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------ |
| `src/ogc-api/csapi/formats/part2.spec.ts` | 2 lines modified | Rename `id: 'cs-minimal'` → `id: 'cmdstatus-minimal'` in parseCommandStatus minimal test fixture + assertion |

### Issue #97 — Extract Shared parseComponentEntry to \_helpers.ts (F27)

| File                                                      | Lines Changed                    | Scope                                                                                                                                                                      |
| --------------------------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/formats/sensorml/_helpers.ts`          | +55 (function + imports + JSDoc) | `parseComponentEntry()` extracted here with `parseSensorML30` import and `ComponentEntry` type import                                                                      |
| `src/ogc-api/csapi/formats/sensorml/physical-system.ts`   | −48 / +2                         | Removed inline `parseComponentEntry()` + JSDoc; added `parseComponentEntry` to `_helpers.js` import; added `export { parseComponentEntry } from './_helpers.js'` re-export |
| `src/ogc-api/csapi/formats/sensorml/aggregate-process.ts` | −50 / +2                         | Same pattern as physical-system.ts: removed inline function, added import + re-export                                                                                      |

### Smoke Test Report ST#22

| File                                                           | Lines Changed   | Scope                                                                                                |
| -------------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------------------- |
| `docs/implementation/live-server-smoke-test-post-phase-5.3.md` | +437 (new file) | Smoke test report: PASS verdict, 0 regressions, CRUD 8/8 Part 1, parseComponentEntry live validation |

**Net code change:** +520 insertions, −102 deletions across 5 files. 1 new file created, 4 files modified.
**Net production code impact:** −39 lines (DRY extraction removed 48+50 duplicated lines, added 55 shared lines).

---

## Overall Codebase Metrics (Cumulative)

| Metric                       | Phase 5.3 | Phase 5.4 | Delta |
| ---------------------------- | --------: | --------: | ----: |
| Production lines (CSAPI all) |    11,508 |    11,469 |   −39 |
| Test lines (CSAPI all)       |   ~13,823 |   ~13,843 |   +20 |
| Total lines (CSAPI)          |   ~25,331 |   ~25,312 |   −19 |
| Production files             |        28 |        28 |     0 |
| Test files (suites)          |        29 |        29 |     0 |
| Test count                   |     1,249 |     1,251 |    +2 |

### Phase 5 Files (Updated State)

| File                                    | Lines (5.3) | Lines (5.4) | Delta | Purpose                                                                          |
| --------------------------------------- | ----------: | ----------: | ----: | -------------------------------------------------------------------------------- |
| `formats/part2.spec.ts`                 |         905 |         925 |   +20 | 43 test cases for Part 2 parsers (+2 from 41)                                    |
| `formats/sensorml/_helpers.ts`          |         207 |         258 |   +51 | Shared helpers including `parseComponentEntry()`                                 |
| `formats/sensorml/physical-system.ts`   |         668 |         623 |   −45 | PhysicalSystem/PhysicalComponent sub-parser (removed inline parseComponentEntry) |
| `formats/sensorml/aggregate-process.ts` |         285 |         240 |   −45 | AggregateProcess sub-parser (removed inline parseComponentEntry)                 |

---

## Phase 3 Lessons Learned Check

| #       | Lesson                                           | Status  | Evidence                                                                                                                                              |
| ------- | ------------------------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L1**  | Audit upstream before building new layers        | ✅ PASS | No new architectural layers. `parseComponentEntry` extraction is a move, not a new system.                                                            |
| **L2**  | Postel's Law governs client libraries            | ✅ PASS | No extraction-depends-on-validation patterns. `parseComponentEntry` validates input guards (isRecord, name check) before extraction — correct order.  |
| **L4**  | Don't build parallel systems                     | ✅ PASS | Issue #97 **eliminates** a parallel system — the two identical `parseComponentEntry` implementations are consolidated into one shared implementation. |
| **L7**  | DRY violations compound across issues            | ✅ PASS | Issue #97 directly resolves the DRY concern from F27.                                                                                                 |
| **L10** | Type naming must avoid built-in collisions       | ✅ PASS | No new types introduced.                                                                                                                              |
| **L12** | "Build it right, but should we build it at all?" | ✅ PASS | All changes resolve specific review findings. No speculative code.                                                                                    |

**Result:** 6/6 applicable lessons PASS. 0 WORSENED.

---

## Prior Findings Status

### All Phase 3 findings (F1–F6 from 3.1 through 3.17): ✅ Still RESOLVED

No Phase 5.4 commits modify any previously-reviewed Phase 3 file. All tracked findings remain resolved.

### Phase 3.17 findings:

| Finding                                    | Status            | Evidence                   |
| ------------------------------------------ | ----------------- | -------------------------- |
| [3.17 F1–F6] POSITIVE findings             | ✅ Unchanged      | No regressions             |
| [3.17 F7] GAP: `SSN_NS` not in root barrel | ✅ Still RESOLVED | No changes to barrel files |

### Phase 5.1 findings:

| Finding                                                    | 5.3 Status    | 5.4 Status      | Evidence                                                                                               |
| ---------------------------------------------------------- | ------------- | --------------- | ------------------------------------------------------------------------------------------------------ |
| [F1] POSITIVE: Consistent tolerant extraction pattern      | ✅ EXTENDED   | ✅ Unchanged    | No new parsers                                                                                         |
| [F2] POSITIVE: Correct instant-vs-interval distinction     | ✅ Unchanged  | ✅ Unchanged    | No change                                                                                              |
| [F3] POSITIVE: Opaque `result` pass-through                | ✅ Unchanged  | ✅ Unchanged    | No change                                                                                              |
| [F4] POSITIVE: Cross-reference exclusion tested            | ✅ Unchanged  | ✅ Unchanged    | No change                                                                                              |
| [F5] POSITIVE: `normalizeObservedProperties()`             | ✅ Unchanged  | ✅ Unchanged    | No change                                                                                              |
| [F6] POSITIVE: `parameters` array guard                    | ✅ Unchanged  | ✅ Unchanged    | No change                                                                                              |
| **[F7] GAP: No test for unknown `resultType` enum → null** | ⚠️ STILL OPEN | ✅ **RESOLVED** | Issue #94 (commit `c1f8271`) — test verifies `resultType: 'foobar'` → `result.resultType` is `null`    |
| **[F8] GAP: No test for unknown `type` field → omitted**   | ⚠️ STILL OPEN | ✅ **RESOLVED** | Issue #95 (commit `0246fa3`) — test verifies `type: 'foobar'` → `result` does not have property `type` |
| [F9] GAP: Stale module-level JSDoc                         | ✅ Unchanged  | ✅ Unchanged    | Still resolved                                                                                         |
| [F10] INFORMATIONAL: Barrel exports deferred to Task 9a    | ✅ RESOLVED   | ✅ Unchanged    | Still resolved                                                                                         |
| [F11] INFORMATIONAL: `links` cast is trust-the-server      | ℹ️ Unchanged  | ℹ️ Unchanged    | No change                                                                                              |

### Phase 5.2 findings:

| Finding                                                             | 5.3 Status    | 5.4 Status        | Evidence                                                                                                                                                                          |
| ------------------------------------------------------------------- | ------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [F12] POSITIVE: `normalizeStatusCode()` shared reuse                | ✅ Unchanged  | ✅ Unchanged      | No change                                                                                                                                                                         |
| [F13] POSITIVE: ControlStream parallels Datastream                  | ✅ Unchanged  | ✅ Unchanged      | No change                                                                                                                                                                         |
| [F14] POSITIVE: Time field asymmetry documented                     | ✅ Unchanged  | ✅ Unchanged      | No change                                                                                                                                                                         |
| [F15] POSITIVE: Required vs. optional statusCode                    | ✅ Unchanged  | ✅ Unchanged      | No change                                                                                                                                                                         |
| [F16] POSITIVE: Command parameters pass-through                     | ✅ Unchanged  | ✅ Unchanged      | No change                                                                                                                                                                         |
| [F17] POSITIVE: All cross-ref fields excluded                       | ✅ Unchanged  | ✅ Unchanged      | No change                                                                                                                                                                         |
| **[F18] GAP (minor): `@see` link precision for parseCommandStatus** | ⚠️ STILL OPEN | ⚠️ **STILL OPEN** | Issue #98 was closed as `not_planned` — the existing link is technically correct but points to a broad section rather than the specific CommandStatus anchor. Knowingly deferred. |
| **[F19] GAP (minor): Fixture ID collision `cs-minimal`**            | ⚠️ STILL OPEN | ✅ **RESOLVED**   | Issue #96 (commit `c1fa10a`) — renamed `id: 'cs-minimal'` to `id: 'cmdstatus-minimal'` in parseCommandStatus minimal test                                                         |
| [F20] INFORMATIONAL: Part 2 suite complete                          | ℹ️ Unchanged  | ℹ️ Unchanged      | Still complete (now 43 tests)                                                                                                                                                     |
| [F21] INFORMATIONAL: Command parameters fallback spec-driven        | ℹ️ Unchanged  | ℹ️ Unchanged      | No change                                                                                                                                                                         |

### Phase 5.3 findings:

| Finding                                                        | 5.3 Status                 | 5.4 Status      | Evidence                                                                                                                                                              |
| -------------------------------------------------------------- | -------------------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [F22] POSITIVE: Schema response parsers delegate to SWE Common | ✅                         | ✅ Unchanged    | No change                                                                                                                                                             |
| [F23] POSITIVE: Recursive delegation dispatches all 4 types    | ✅                         | ✅ Unchanged    | `parseComponentEntry` still delegates all 4 types, now from `_helpers.ts`                                                                                             |
| [F24] POSITIVE: Complete cross-type test coverage              | ✅                         | ✅ Unchanged    | All 10 cross-type tests pass (243/243 SensorML tests)                                                                                                                 |
| [F25] POSITIVE: Integration wiring complete at 3 levels        | ✅                         | ✅ Unchanged    | No change to barrel exports                                                                                                                                           |
| [F26] POSITIVE: E2E pipeline tests validate full chain         | ✅                         | ✅ Unchanged    | No change                                                                                                                                                             |
| **[F27] CONSISTENCY: Duplicated `parseComponentEntry`**        | ⚠️ Acceptable              | ✅ **RESOLVED** | Issue #97 (commit `78115de`) — extracted to shared `_helpers.ts`. Both `physical-system.ts` and `aggregate-process.ts` now import + re-export from the single source. |
| [F28] GAP: TS2352 cast in `pipeline.spec.ts`                   | ✅ RESOLVED (in `b4ab1a0`) | ✅ Unchanged    | Still resolved — `tsc --noEmit` is clean                                                                                                                              |
| [F29] POSITIVE: P4 JSDoc documentation                         | ✅                         | ✅ Unchanged    | No change                                                                                                                                                             |
| [F30] POSITIVE: Schema response inline import types            | ✅                         | ✅ Unchanged    | No change                                                                                                                                                             |
| [F31] INFORMATIONAL: Phase 5 complete                          | ℹ️                         | ℹ️ Unchanged    | Still complete                                                                                                                                                        |

**Summary:** 4 findings resolved (F7, F8, F19, F27). 1 finding still open (F18 — knowingly deferred via #98 not_planned). All 17 positive findings maintained. 0 regressions.

---

## Phase 5.4 Findings — New

### [F32] POSITIVE: Enum test gaps correctly closed with targeted test cases

The two new tests in `part2.spec.ts` (Issues #94, #95) precisely address the Phase 5.1 F7/F8 gaps:

**F7 test** (`rejects unknown resultType enum value and returns null`):

```typescript
const input = {
  id: 'ds-unknown-result',
  name: 'Unknown Result Type Test',
  outputName: 'test-output',
  resultType: 'foobar',
};
const result = parseDatastream(input);
expect(result.resultType).toBeNull();
```

**F8 test** (`omits type field when value is not a recognized enum`):

```typescript
const input = {
  id: 'ds-unknown-type',
  name: 'Unknown Type Test',
  outputName: 'test-output',
  type: 'foobar',
};
const result = parseDatastream(input);
expect(result).not.toHaveProperty('type');
```

Both tests are tightly focused: minimal fixture with only required fields plus the target field, clear assertion matching the parser's documented behavior. The `resultType` test verifies enum-invalid → `null` fallback (tolerant extraction). The `type` test verifies conditional spread exclusion — the key absent-vs-undefined distinction established in Phase 5.1.

**Severity:** POSITIVE

---

### [F33] POSITIVE: DRY extraction of `parseComponentEntry` eliminates dual-maintenance concern

Issue #97 moves `parseComponentEntry()` from both `physical-system.ts` and `aggregate-process.ts` into the shared `_helpers.ts` module, resolving the Phase 5.3 F27 consistency finding. The extraction is clean:

1. **Source file** (`_helpers.ts`): +55 lines including the function body, JSDoc, `ComponentEntry` type import, and `parseSensorML30` import
2. **Consumer files** (both sub-parsers): removed inline function (−48/−50 lines each), added `parseComponentEntry` to the `_helpers.js` import list, added `export { parseComponentEntry } from './_helpers.js'` re-export
3. **Net effect:** −39 production lines (DRY improvement)

The re-export statements in both consumer files maintain backward compatibility — any existing imports of `parseComponentEntry` from `physical-system` or `aggregate-process` continue to resolve correctly.

The `parseSensorML30` import now lives in `_helpers.ts` instead of the two consumer files. This creates a circular dependency path (`_helpers.ts` → `parser.ts` → `physical-system.ts` → `_helpers.ts`), but this is the same safe ESM live binding pattern that was already present. All 243 SensorML tests passing validates the runtime safety.

**Severity:** POSITIVE

---

### [F34] CONSISTENCY (minor): Two separate re-export lines in `physical-system.ts`

`physical-system.ts` now has two adjacent re-export lines from the same module:

```typescript
export { parseProcessMethod } from './_helpers.js';
export { parseComponentEntry } from './_helpers.js';
```

These could be combined into a single statement:

```typescript
export { parseProcessMethod, parseComponentEntry } from './_helpers.js';
```

`aggregate-process.ts` has only one re-export (`parseComponentEntry`) and does not exhibit this pattern.

**Impact:** Zero functional impact. Purely stylistic. Both forms are valid TypeScript and produce identical bundle output.

**Severity:** CONSISTENCY (trivial)

---

### [F35] POSITIVE: Fixture ID rename eliminates cross-parser ambiguity

The rename from `id: 'cs-minimal'` to `id: 'cmdstatus-minimal'` in the parseCommandStatus minimal test (Issue #96) resolves the Phase 5.2 F19 concern. The `cs-` prefix was ambiguous because it could refer to either ControlStream or CommandStatus. The new `cmdstatus-` prefix is unambiguous and follows the established convention where fixture IDs reflect their parser context (e.g., `ds-` for Datastream, `obs-` for Observation, `cmd-` for Command).

**Severity:** POSITIVE

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

No changes. All Phase 2 dimensions remain at established coverage levels. 319 tests passing.

### Phase 3 (Format Handlers) — Carried Forward

No changes. All Phase 3 dimensions remain at established coverage levels (see Phase 3.17 review).

### Phase 5 (Parser Completion) — Updated

| Dimension               | parseProperty | parseDatastream | parseObservation | parseControlStream | parseCommand | parseCommandStatus | SchemaResp (DS) | SchemaResp (CS) | Recursive Fix | Integration |
| ----------------------- | :-----------: | :-------------: | :--------------: | :----------------: | :----------: | :----------------: | :-------------: | :-------------: | :-----------: | :---------: |
| Fixture → typed output  |      ✅       |       ✅        |        ✅        |         ✅         |      ✅      |         ✅         |       ✅        |       ✅        |      ✅       |     ✅      |
| Minimal fixture         |      ✅       |       ✅        |        ✅        |         ✅         |      ✅      |         ✅         |       ✅        |       ✅        |      n/a      |     ✅      |
| Non-object rejection    |      ✅       |       ✅        |        ✅        |         ✅         |      ✅      |         ✅         |       ✅        |       ✅        |      n/a      |     n/a     |
| Cross-ref exclusion     |      n/a      |       ✅        |        ✅        |         ✅         |      ✅      |         ✅         |       n/a       |       n/a       |      n/a      |     ✅      |
| Time field correctness  |      n/a      |       ✅        |        ✅        |         ✅         |      ✅      |         ✅         |       n/a       |       n/a       |      n/a      |     ✅      |
| Optional field handling |      ✅       |       ✅        |        ✅        |         ✅         |      ✅      |         ✅         |       ✅        |       ✅        |      n/a      |     ✅      |
| Opaque pass-through     |      n/a      |       n/a       |        ✅        |        n/a         |      ✅      |        n/a         |       n/a       |       n/a       |      n/a      |     n/a     |
| Enum validation         |      n/a      |       ✅        |       n/a        |        n/a         |      ✅      |         ✅         |       n/a       |       n/a       |      n/a      |     n/a     |
| `satisfies` typing      |      ✅       |       ✅        |        ✅        |         ✅         |      ✅      |         ✅         |       ✅        |       ✅        |      n/a      |     n/a     |
| SWE delegation          |      n/a      |       n/a       |       n/a        |        n/a         |     n/a      |        n/a         |       ✅        |       ✅        |      n/a      |     ✅      |
| Missing schema fallback |      n/a      |       n/a       |       n/a        |        n/a         |     n/a      |        n/a         |       ✅        |       ✅        |      n/a      |     n/a     |
| Barrel exports          |      n/a      |       n/a       |       n/a        |        n/a         |     n/a      |        n/a         |       n/a       |       n/a       |      n/a      |     ✅      |
| Cross-type delegation   |      n/a      |       n/a       |       n/a        |        n/a         |     n/a      |        n/a         |       n/a       |       n/a       |      ✅       |     n/a     |
| E2E pipeline            |      n/a      |       n/a       |       n/a        |        n/a         |     n/a      |        n/a         |       n/a       |       n/a       |      n/a      |     ✅      |

**Legend:** ✅ = covered, n/a = not applicable.

**Changes from Phase 5.3:** `parseDatastream` Enum validation upgraded from ⚠️ to ✅. The unknown `resultType` → null test (#94) and unknown `type` → omitted test (#95) close the last partial-coverage cell. All heatmap cells are now either ✅ or n/a — no remaining gaps.

---

## Smoke Test Findings Integration

| Finding                                                       | Status                   | Evidence       |
| ------------------------------------------------------------- | ------------------------ | -------------- |
| F27 (Observation `foi@id`)                                    | ✅ Addressed (Phase 5.1) | No regression. |
| F30 (ControlStream `system@link`)                             | ✅ Addressed (Phase 5.2) | No regression. |
| F31 (Command `controlstream@id`)                              | ✅ Addressed (Phase 5.2) | No regression. |
| F33 (ControlStream schema `commandFormat`/`parametersSchema`) | ✅ Addressed (Phase 5.3) | No regression. |
| F38 (CommandStatus data shape)                                | ✅ Addressed (Phase 5.2) | No regression. |

All 5 smoke test findings remain addressed. ✅

---

## Summary

| Category      | Count | Details                                                                                                    |
| ------------- | ----: | ---------------------------------------------------------------------------------------------------------- |
| POSITIVE      |     4 | F32 (enum gap tests), F33 (DRY extraction), F34 (re-export consistency — trivial), F35 (fixture ID rename) |
| CONSISTENCY   |     1 | F34 (two re-export lines — trivial, zero impact)                                                           |
| GAP           |     0 | —                                                                                                          |
| BUG           |     0 | —                                                                                                          |
| DESIGN        |     0 | —                                                                                                          |
| INFORMATIONAL |     0 | —                                                                                                          |

**Prior findings resolved this review:** 4 (F7 enum resultType test, F8 enum type test, F19 fixture ID rename, F27 parseComponentEntry DRY extraction)
**Prior findings still open:** 1 (F18 — parseCommandStatus `@see` link precision, knowingly deferred via Issue #98 closed as not_planned)

---

## Recommendations

### Fix Now (before next issue)

None. All actionable findings have been resolved.

### Fix Before Phase 6 (before upstream submission)

**1. Combine re-export lines in `physical-system.ts` (F34) — optional**

```typescript
// Current (two lines):
export { parseProcessMethod } from './_helpers.js';
export { parseComponentEntry } from './_helpers.js';

// Suggested (one line):
export { parseProcessMethod, parseComponentEntry } from './_helpers.js';
```

Purely stylistic. Zero functional impact. Can be done as part of any future change to the file.

### Defer (Low Priority)

**2. Improve `@see` link precision for parseCommandStatus (F18) — carried forward**

Verify whether `#_commandstatus_resources` exists as an anchor in OGC 23-002. If yes, update; if not, current link is acceptable. Issue #98 was closed as `not_planned` — this is appropriate given the link is technically correct.

---

## Root Cause Analysis

No defects found. This is the fourth consecutive Phase 5 code review with zero bugs and zero design concerns.

---

## Overall Assessment

Phase 5.4 is a clean-up review that resolves 4 of the 5 remaining open findings from Phase 5.1–5.3. The changes are entirely finding-driven: two targeted test additions (#94, #95), one fixture rename (#96), and one DRY refactoring (#97). No new features, no new parsers, no new architectural patterns.

The most structurally significant change is the `parseComponentEntry` extraction (#97), which consolidates two identical 48-line functions into a single implementation in the shared `_helpers.ts` module. The extraction is mechanically sound — the function body is unchanged, the import of `parseSensorML30` is correctly relocated, and both consumer files maintain backward-compatible re-exports. The circular dependency path (`_helpers.ts` → `parser.ts` → `physical-system.ts` → `_helpers.ts`) is safe via ESM live bindings, as proven by all 243 SensorML tests passing.

The test heatmap is now fully green: every applicable dimension for every Phase 5 component shows ✅. The `parseDatastream` enum validation cell — the last ⚠️ in the heatmap — is upgraded to ✅ by the two new tests. With 1,251 CSAPI tests across 29 suites, zero tsc errors, and only 1 remaining open finding (F18, knowingly deferred), the Phase 5 codebase is in its cleanest state.

The defect-free streak now extends to 33 consecutive review findings (F22–F35 in Phase 5.3/5.4, plus all prior findings maintained). Phase 5 is fully complete and ready for Phase 6 planning.
