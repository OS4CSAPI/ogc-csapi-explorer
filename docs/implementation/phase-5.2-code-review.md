# Phase 5.2 Code Review — parseControlStream, parseCommand, normalizeStatusCode, parseCommandStatus

**Date:** 2026-02-19  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Scope:** Second Phase 5 code review covering Tasks 4–6 (3 resource parsers, 1 shared utility, 20 new test cases, 2 files modified)  
**Commits:**
- `acb5139` — `feat(csapi): add parseControlStream() with 7 test cases (P5 Task 4)` — Closes #82
- `4c6a5a0` — `feat(csapi): add normalizeStatusCode() + parseCommand() (P5 Task 5a)` — Closes #83
- `4c226b6` — `test(csapi): add parseCommand() + normalizeStatusCode() test cases (P5 Task 5b)` — Closes #84
- `d556f31` — `feat(csapi): add parseCommandStatus() + 7 tests (Phase 5, Task 6)` — Closes #85

**Last review:** `docs/implementation/phase-5.1-code-review.md` (commit `f172dd0`)

---

## Verification Status

| Check | Result |
|-------|--------|
| tsc --noEmit | ✅ Clean (zero errors) |
| CSAPI unit tests (all) | ✅ 1216 passing, 27 suites |
| CSAPI format tests | ✅ 694 passing, 19 suites |
| Endpoint integration tests | ⚠️ 82/83 passing (1 pre-existing upstream failure — Unicode mismatch at `endpoint.spec.ts:1789`) |

**Test delta from Phase 5.1:** +26 tests (1190 → 1216), +0 suites. New tests: 7 (parseControlStream) + 8 (parseCommand) + 4 (normalizeStatusCode) + 7 (parseCommandStatus) = 26 in `part2.spec.ts`.  
**Format test delta:** +26 tests (668 → 694), +0 suites.

---

## Files Reviewed

### Issue #82 — parseControlStream + 7 Tests (Task 4)

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/formats/part2.ts` | +91 (new function + JSDoc) | `parseControlStream()` — 12 ControlStream fields, 3 time intervals via `parseValidTime()`, `controlledProperties` via `normalizeObservedProperties()`, `async` default to `false` |
| `src/ogc-api/csapi/formats/part2.spec.ts` | +200 (new describe block) | 7 test cases: full (cross-ref excluded), minimal, 3 time fields with "now" sentinel, controlledProperties normalization, missing optionals, async boolean handling, non-object throw |

### Issue #83 — normalizeStatusCode + parseCommand (Task 5a)

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/formats/part2.ts` | +110 (2 functions + JSDoc) | `normalizeStatusCode()` — validates against 9 CommandStatusCodes; `parseCommand()` — 7 Command fields, issueTime string pass-through, executionTime via `parseValidTime()`, `currentStatus` via `normalizeStatusCode()`, `parameters` opaque pass-through |

### Issue #84 — parseCommand + normalizeStatusCode Tests (Task 5b)

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/formats/part2.spec.ts` | +262 (2 describe blocks) | 8 parseCommand tests: full (cross-ref excluded), minimal, valid/invalid currentStatus, executionTime present/absent, complex nested parameters, non-object throw. 4 normalizeStatusCode tests: all 9 valid codes, unrecognized strings, non-string input, undefined input |

### Issue #85 — parseCommandStatus + 7 Tests (Task 6)

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/formats/part2.ts` | +80 (new function + JSDoc) | `parseCommandStatus()` — 7 CommandStatus fields, `reportTime` string pass-through, `statusCode` required via `normalizeStatusCode() ?? 'PENDING'`, `executionTime` via `parseValidTime()`, `percentCompletion`/`message` conditional extraction |
| `src/ogc-api/csapi/formats/part2.spec.ts` | +170 (new describe block) | 7 test cases: full (cross-ref excluded), minimal, valid statusCode, PENDING fallback for invalid/absent, percentCompletion, executionTime, non-object throw |

### Module-level JSDoc updates (across all 4 commits)

Both `part2.ts` and `part2.spec.ts` had their module-level JSDoc headers updated incrementally to reflect newly added parsers. The Phase 5.1 finding F9 (stale JSDoc) is now **resolved** — the final state accurately lists all 5 parsers and the "Subsequent tasks" placeholder has been replaced with "All 5 Part 2 resource parsers are now in this file."

**Net code change:** +281 production lines (part2.ts: 232 → 511, delta = +279, plus 2 import line changes), +638 test lines (part2.spec.ts: 384 → 1022, delta = +638). Test-to-production ratio for new code: 2.27:1.

---

## Overall Codebase Metrics (Cumulative)

| Metric | Phase 5.1 | Phase 5.2 | Delta |
|--------|----------:|----------:|------:|
| Production lines (CSAPI formats) | 11,816 | 12,095 | +279 |
| Test lines (CSAPI formats) | 14,089 | 14,727 | +638 |
| Total lines | 25,905 | 26,822 | +917 |
| Production files | 26 | 26 | 0 |
| Test files (suites) | 27 | 27 | 0 |
| Test count | 1,190 | 1,216 | +26 |
| Test-to-production ratio | 1.19:1 | 1.22:1 | +0.03 |

### Phase 5 Files (Updated)

| File | Lines | Purpose |
|------|-------|---------|
| `formats/property.ts` | 60 | `parseProperty()` — Part 1 DerivedProperty parser |
| `formats/property.spec.ts` | 130 | 6 test cases for parseProperty |
| `formats/part2.ts` | 511 | `parseDatastream()`, `parseObservation()`, `parseControlStream()`, `normalizeStatusCode()`, `parseCommand()`, `parseCommandStatus()` — all Part 2 parsers |
| `formats/part2.spec.ts` | 1,022 | 41 test cases for Part 2 parsers + normalizeStatusCode utility |
| **Total** | **1,723** | **47 tests** |

---

## Phase 3 Lessons Learned Check

| # | Lesson | Status | Evidence |
|---|--------|--------|----------|
| **L1** | Audit upstream before building new layers | ✅ PASS | No new layers. All 3 parsers + 1 utility follow existing tolerant extraction pattern from `extractCSAPIFeature()`. `normalizeStatusCode()` is a minimal helper, not a new architectural layer. |
| **L2** | Postel's Law governs client libraries | ✅ PASS | Every parser defaults missing required strings to `''`, omits absent optional fields via conditional spread, and never throws on malformed *data* — only on non-object input type. `parseCommandStatus()` falls back to `'PENDING'` for missing/invalid `statusCode` rather than throwing. |
| **L4** | Don't build parallel systems | ✅ PASS | `parseControlStream()` correctly reuses `normalizeObservedProperties()` from `parseDatastream()` for the analogous `controlledProperties` field. `normalizeStatusCode()` is shared between `parseCommand()` and `parseCommandStatus()` — no duplication. |
| **L7** | DRY violations compound across issues | ✅ PASS | No logic duplication. `normalizeStatusCode()` was designed in Task 5a and reused in Task 6. `normalizeObservedProperties()` was designed in Task 2a and reused in Task 4. |
| **L10** | Type naming must avoid built-in collisions | ✅ PASS | No new types introduced. Parsers return existing interfaces from `model.ts`. `normalizeStatusCode` name is clear and domain-specific. |
| **L12** | "Build it right, but should we build it at all?" | ✅ PASS | All 3 parsers + 1 utility fill specific gaps (#4, #5, #6) from the Parsing Coverage Audit. This completes all Part 2 resource parsers — no scope expansion. |

**Result:** 6/6 applicable lessons PASS. 0 WORSENED.

---

## Prior Findings Status

### All Phase 3 findings (F1–F6 from 3.1 through 3.17): ✅ Still RESOLVED

No Phase 5.2 commits modify any previously-reviewed Phase 3 file. All 14 tracked findings remain resolved.

### Phase 3.17 findings:

| Finding | Status | Evidence |
|---------|--------|----------|
| [3.17 F1–F6] POSITIVE findings | ✅ Unchanged | No regressions |
| **[3.17 F7] GAP: `SSN_NS` not in root barrel** | ⏳ **STILL OPEN** | `src/index.ts` still does not re-export `SSN_NS`. Deferred to Task 9a (#90). |

### Phase 5.1 findings:

| Finding | 5.1 Status | 5.2 Status | Evidence |
|---------|-----------|-----------|----------|
| [F1] POSITIVE: Consistent tolerant extraction pattern | ✅ | ✅ **MAINTAINED** | 3 new parsers follow the identical pattern: input guard → cast → extract → conditional spread → `satisfies` return |
| [F2] POSITIVE: Correct instant-vs-interval distinction | ✅ | ✅ **EXTENDED** | `parseCommand()` adds a new variant — `issueTime` is instant (string), `executionTime` is interval (`parseValidTime()`). `parseCommandStatus()` mirrors this with `reportTime` (string) vs `executionTime` (interval). Both are documented in JSDoc. |
| [F3] POSITIVE: Opaque `result` pass-through | ✅ | ✅ Unchanged | Only applicable to `parseObservation()` — no change |
| [F4] POSITIVE: Cross-reference exclusion tested | ✅ | ✅ **EXTENDED** | New cross-refs tested: `system@id`/`system@link` (ControlStream test 1), `controlstream@id` (Command test 1), `command@id` (CommandStatus test 1) |
| [F5] POSITIVE: `normalizeObservedProperties()` | ✅ | ✅ **REUSED** | Now also handles `controlledProperties` in `parseControlStream()`, confirming the helper generalizes correctly |
| [F6] POSITIVE: `parameters` array guard | ✅ | ✅ **REPLICATED** | `parseCommand()` has the same `!Array.isArray(parametersValue)` guard for its `parameters` field (part2.ts line 360) |
| **[F7] GAP: No test for unknown `resultType` enum → null** | ⚠️ | ⚠️ **STILL OPEN** | No change — `parseDatastream` test gap. Low priority. |
| **[F8] GAP: No test for unknown `type` field → omitted** | ⚠️ | ⚠️ **STILL OPEN** | No change — `parseDatastream` test gap. Low priority. |
| **[F9] GAP: Stale module-level JSDoc** | ⚠️ | ✅ **RESOLVED** | Both files now accurately list all parsers. `part2.ts` L5–11 lists all 5 parsers + Task labels. `part2.spec.ts` L19–21 reads "This file houses tests for all Part 2 resource parsers and shared utilities." — no stale "Subsequent tasks" text. |
| [F10] INFORMATIONAL: Barrel exports deferred to Task 9a | ℹ️ | ℹ️ **Unchanged** | Still deferred. Correct per ROADMAP. |
| [F11] INFORMATIONAL: `links` cast is trust-the-server | ℹ️ | ℹ️ **UNCHANGED** | Same pattern in all 3 new parsers — consistent. |

**Summary:** 1 finding resolved (F9 stale JSDoc). 2 findings still open (F7, F8 — low priority `parseDatastream` enum test gaps). 6 positive findings maintained or extended. 2 informational findings unchanged. 1 Phase 3.17 finding still open (SSN_NS barrel).

---

## Phase 5.2 Findings — New

### [F12] POSITIVE: `normalizeStatusCode()` shared utility reuse pattern

`normalizeStatusCode()` was designed in Task 5a specifically for dual use:
- `parseCommand()`: `normalizeStatusCode(obj.currentStatus)` → optional, falls back to `undefined`
- `parseCommandStatus()`: `normalizeStatusCode(obj.statusCode) ?? 'PENDING'` → required, falls back to `'PENDING'`

This demonstrates excellent forward planning — the utility was implemented once with a clean `string → CommandStatusCode | undefined` contract, and each caller applies its own fallback semantic. The JSDoc explicitly documents this dual-use pattern.

The test coverage for `normalizeStatusCode()` is exhaustive: all 9 valid codes, unrecognized strings, non-string input, and `undefined` input — 4 tests covering all branches.

**Severity:** POSITIVE

---

### [F13] POSITIVE: `parseControlStream()` correctly parallels `parseDatastream()` with no duplication

`parseControlStream()` is structurally parallel to `parseDatastream()` (same `baseStream` schema) but correctly differs in:
- `controlledProperties` instead of `observedProperties` (both use `normalizeObservedProperties()`)
- `inputName` instead of `outputName`
- `issueTime`/`executionTime` instead of `phenomenonTime`/`resultTime`
- `async` field with `false` default (not present on Datastream)
- No `resultType` or `type` enum fields

The structural parallelism makes the code predictable, while the differences are spec-correct. No logic is duplicated — the shared helper `normalizeObservedProperties()` is reused.

**Severity:** POSITIVE

---

### [F14] POSITIVE: Correct time field asymmetry documented and tested across all 3 new parsers

The 3 new parsers all handle the instant-vs-interval time distinction correctly:

| Parser | Instant (string pass-through) | Interval (`parseValidTime()`) |
|--------|-------------------------------|------------------------------|
| parseControlStream | — | `validTime`, `issueTime`, `executionTime` |
| parseCommand | `issueTime` | `executionTime` |
| parseCommandStatus | `reportTime` | `executionTime` |

Each instant field is tested with `typeof result.field === 'string'` assertions. Each interval field is tested with `result.field?.start` → `Date` object assertions. The JSDoc for `parseCommand()` and `parseCommandStatus()` explicitly documents the asymmetry:

> "`issueTime` is a single ISO 8601 instant string... `executionTime` is a time interval array parsed via `parseValidTime()`"

**Severity:** POSITIVE

---

### [F15] POSITIVE: Required vs. optional `statusCode` semantic correctly distinguished

The most nuanced design decision in this review: `parseCommand()` treats `currentStatus` as **optional** (`normalizeStatusCode() → undefined` if invalid, conditional spread omits it), while `parseCommandStatus()` treats `statusCode` as **required** (`normalizeStatusCode() ?? 'PENDING'` — always present in output).

This matches the `model.ts` interface contracts:
- `Command.currentStatus?: CommandStatusCode` — optional
- `CommandStatus.statusCode: CommandStatusCode` — required (non-optional)

Test 4 in `parseCommandStatus` ("falls back to PENDING when statusCode is invalid or absent") explicitly verifies both the invalid case (`'UNKNOWN_STATUS'` → `'PENDING'`) and the absent case (no `statusCode` key → `'PENDING'`), with `not.toBeUndefined()` assertions confirming the required semantic.

**Severity:** POSITIVE

---

### [F16] POSITIVE: `parseCommand()` parameters pass-through with array guard

Like `parseObservation()` (F6 from Phase 5.1), `parseCommand()` includes a `!Array.isArray(parametersValue)` guard when extracting `parameters`. However, `parseCommand()` has an additional design choice: it falls back to `{}` (empty object) rather than omitting the field, because `Command.parameters: Record<string, unknown>` is **required** on the interface, whereas `Observation.parameters` is optional.

Test 7 ("passes through complex nested parameters exactly") verifies deep equality with a multi-level nested object.

**Severity:** POSITIVE

---

### [F17] POSITIVE: All cross-reference fields excluded with explicit tests

Every new parser excludes its relevant cross-reference fields, and every test suite's first test case asserts this:

| Parser | Cross-ref excluded | Test assertion |
|--------|-------------------|----------------|
| parseControlStream | `system@id`, `system@link` | `not.toHaveProperty('system@id')`, `not.toHaveProperty('system@link')` |
| parseCommand | `controlstream@id` | `not.toHaveProperty('controlstream@id')` |
| parseCommandStatus | `command@id` | `not.toHaveProperty('command@id')` |

Combined with Phase 5.1's cross-ref tests for `parseDatastream` and `parseObservation`, all 5 Part 2 parsers now have complete cross-reference exclusion coverage.

**Severity:** POSITIVE

---

### [F18] GAP (minor): `parseCommandStatus()` JSDoc `@see` link references `#_command_resources` instead of `#_commandstatus_resources`

The JSDoc for `parseCommandStatus()` (part2.ts line 461) links to:
```
@see https://docs.ogc.org/is/23-002/23-002.html#_command_resources
```

While CommandStatus is documented under the Command resources section in OGC 23-002, a more precise link would be `#_commandstatus_resources` if such an anchor exists in the spec. Note that the `CommandStatus` interface in `model.ts` (line 558) uses the same `#_command_resources` link, so this is at least consistent with the model's convention.

**Impact:** Very low. The link lands on the correct page/section. A reviewer familiar with the spec can navigate from Command resources to CommandStatus.

**Severity:** GAP (minor)

---

### [F19] GAP (minor): `parseCommandStatus` minimal fixture ID `'cs-minimal'` collides with `parseControlStream` minimal fixture ID

Both `parseControlStream` test 2 ("handles a minimal ControlStream with only required fields") and `parseCommandStatus` test 2 ("handles a minimal CommandStatus with only required fields") use `id: 'cs-minimal'` as the fixture ID. While test isolation means there is zero runtime impact, it creates a minor readability ambiguity when scanning test output — both tests would produce output containing `'cs-minimal'`.

This stems from `cs-` being a natural prefix for both "ControlStream" and "CommandStatus."

**Impact:** Zero — tests are independent. Purely a naming style concern.

**Severity:** GAP (minor)

---

### [F20] INFORMATIONAL: Part 2 parser suite now complete

All 5 Part 2 resource parsers are implemented and fully tested:

| Parser | Task | Issue | Tests | Commit |
|--------|------|-------|-------|--------|
| `parseDatastream()` | 2a/2b | #79/#80 | 8 | `a8c01a5`/`8be9399` |
| `parseObservation()` | 3 | #81 | 7 | `954a1e6` |
| `parseControlStream()` | 4 | #82 | 7 | `acb5139` |
| `parseCommand()` | 5a/5b | #83/#84 | 8 | `4c6a5a0`/`4c226b6` |
| `parseCommandStatus()` | 6 | #85 | 7 | `d556f31` |
| `normalizeStatusCode()` | 5a/5b | #83/#84 | 4 | `4c6a5a0`/`4c226b6` |

Total: 6 functions, 41 test cases. The remaining Phase 5 work (Tasks 7–9) consists of schema response parsers, the recursive delegation fix, and integration wiring — none of which add new Part 2 resource parsers.

**Severity:** INFORMATIONAL

---

### [F21] INFORMATIONAL: `parseCommand()` parameters fallback to `{}` is spec-driven

`parseCommand()` falls back to an empty object `{}` when `parameters` is missing/invalid, unlike `parseObservation()` which omits `parameters` entirely. This is correct because:
- `Command.parameters: Record<string, unknown>` — **required**, non-optional
- `Observation.parameters?: Record<string, unknown>` — **optional**

The empty-object fallback ensures the return type always satisfies the interface contract without throwing. This is worth documenting because it's a subtle but deliberate difference.

**Severity:** INFORMATIONAL

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

No changes. All Phase 2 dimensions remain at established coverage levels.

### Phase 3 (Format Handlers) — Carried Forward

No changes. All Phase 3 dimensions remain at established coverage levels (see Phase 3.17 review).

### Phase 5 (Parser Completion) — Current

| Dimension | parseProperty | parseDatastream | parseObservation | parseControlStream | parseCommand | parseCommandStatus | SchemaResp (DS) | SchemaResp (CS) | Recursive Fix | Integration |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Fixture → typed output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Minimal fixture | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Non-object rejection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Cross-ref exclusion | n/a | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Time field correctness | n/a | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Optional field handling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| Opaque pass-through | n/a | n/a | ✅ | n/a | ✅ | n/a | — | — | — | — |
| Enum validation | n/a | ⚠️ | n/a | n/a | ✅ | ✅ | — | — | — | — |
| `satisfies` typing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — | — | — |

**Legend:** ✅ = covered, ⚠️ = partially covered (absent value tested but invalid value not tested — phase 5.1 F7/F8), n/a = not applicable, — = not yet implemented.

**Changes from Phase 5.1:** 4 columns filled (parseControlStream, parseCommand, parseCommandStatus, plus normalizeStatusCode embedded in Enum validation rows). `parseCommand` Opaque pass-through = ✅ because `parameters` is treated as opaque `Record<string, unknown>` with deep equality test. `parseCommand` and `parseCommandStatus` Enum validation = ✅ because `normalizeStatusCode()` is tested independently with all 9 valid codes, invalid strings, and non-string input — complete branch coverage.

---

## Smoke Test Findings Integration

| Finding | Status | Evidence |
|---------|--------|----------|
| F27 (Observation `foi@id`) | ✅ **Addressed** (Phase 5.1) | `parseObservation()` excludes `foi@id` — test assertion `not.toHaveProperty('foi@id')`. No regression. |
| F30 (ControlStream `system@link`) | ✅ **Addressed** | `parseControlStream()` excludes both `system@id` and `system@link`. Test 1 asserts `not.toHaveProperty('system@id')` and `not.toHaveProperty('system@link')`. Fixture derived from OSH ST#9 F30 data. Commit `acb5139`. |
| F31 (Command `controlstream@id`) | ✅ **Addressed** | `parseCommand()` excludes `controlstream@id`. Test 1 asserts `not.toHaveProperty('controlstream@id')`. Fixture derived from OSH ST#10 F31 data. Commit `4c6a5a0`. |
| F33 (ControlStream schema variants) | — **Not yet** | Task 7b (#87) — `parseControlStreamSchemaResponse` not yet implemented |
| F38 (CommandStatus data shape) | ✅ **Addressed** | `parseCommandStatus()` extracts all fields from F38 fixture shape: `command@id` excluded, `reportTime` as string, `statusCode` normalized via `normalizeStatusCode()`. Test fixture explicitly derived from OSH ST#10 F38 data. Commit `d556f31`. |

---

## Summary

| Category | Count | Details |
|----------|------:|---------|
| POSITIVE | 6 | F12 (normalizeStatusCode reuse), F13 (ControlStream parallel), F14 (time asymmetry), F15 (required vs optional statusCode), F16 (parameters array guard), F17 (cross-ref exclusion complete) |
| GAP (minor) | 2 | F18 (@see link precision), F19 (fixture ID collision) |
| INFORMATIONAL | 2 | F20 (Part 2 suite complete), F21 (parameters fallback spec-driven) |
| BUG | 0 | — |
| DESIGN | 0 | — |

**Prior findings:** 14 from Phase 3 remain resolved. 1 from Phase 3.17 still open (SSN_NS barrel). 1 from Phase 5.1 resolved (F9 stale JSDoc). 2 from Phase 5.1 still open (F7/F8 enum rejection tests).

---

## Recommendations

### Fix Now (before next issue)

None — no blocking issues. All findings are minor or positive.

### Fix Before Phase 6 (before upstream submission)

**1. Add enum rejection tests for `resultType` and `type` (Phase 5.1 F7/F8) — carried forward**

Add 2 test cases to `parseDatastream` in `part2.spec.ts`:
- `resultType: 'foobar'` → `result.resultType` is `null`
- `type: 'foobar'` → `result` does not have property `type`

These are quick additions (~10 lines each) and would bring enum validation coverage for `parseDatastream` from ⚠️ to ✅.

**2. Export `SSN_NS` from root barrel (carried from Phase 3.17 F7)**

Single-line addition to `src/index.ts`. Can be batched with the Task 9a barrel update.

**3. Rename `parseCommandStatus` minimal fixture ID to avoid collision (F19)**

Change `id: 'cs-minimal'` in the parseCommandStatus minimal test to `id: 'cmdstatus-minimal'` to distinguish from the parseControlStream minimal fixture. Trivial 1-line fix.

### Defer (Low Priority)

**4. Improve `@see` link precision for parseCommandStatus (F18)**

Verify whether `#_commandstatus_resources` is a valid anchor in OGC 23-002. If it is, update both `parseCommandStatus()` JSDoc and `model.ts` `CommandStatus` interface to use the more precise anchor. If not, the current `#_command_resources` link is acceptable.

---

## Root Cause Analysis

No defects found. The two minor gaps are trivial naming/documentation issues:

- **F18 (@see link):** The JSDoc `@see` link was copied from the `Command` interface section, which points to `#_command_resources`. Since CommandStatus is indeed documented *within* the Command resources section of OGC 23-002, this is technically correct — just not maximally precise.
- **F19 (fixture ID collision):** The prefix `cs-` was independently chosen for both ControlStream and CommandStatus fixtures because it's a natural abbreviation for both. The collision was not caught because the two parsers were implemented in separate issues (Tasks 4 and 6) with different contexts.

---

## Overall Assessment

Phase 5.2 delivers three high-quality resource parsers and one shared utility that complete the entire Part 2 parser suite. The code quality matches the excellent standard set in Phase 5.1 — zero bugs, zero design concerns, and a continued 100% adherence to the established tolerant extraction pattern.

The most significant technical achievement in this review is the `normalizeStatusCode()` shared utility pattern. Designing it once with a clean `string → typed union | undefined` contract enabled two callers (`parseCommand` and `parseCommandStatus`) to apply different fallback semantics (optional → `undefined` vs. required → `'PENDING'`) without any code duplication. This is a textbook demonstration of the Single Responsibility Principle applied to enum validation.

The time field asymmetry handling continues to impress across the three new parsers. `parseControlStream` uses intervals for all three time fields (like Datastream), while `parseCommand` and `parseCommandStatus` each mix instants and intervals — and each correctly documents and tests the distinction. Test coverage is thorough: 26 new tests with explicit type assertions (`typeof === 'string'` for instants, `?.start` → `Date` for intervals).

With 41 tests across 6 functions in `part2.ts`, the Part 2 parser suite is now complete and well-covered. The remaining Phase 5 work (Tasks 7–9: schema response parsers, recursive fix, integration wiring) builds on this foundation without modifying it. The defect-free streak continues through 26 consecutive review phases.
