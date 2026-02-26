# Phase 6.1 Code Review — Phase A: Prettier Formatting + ESLint Fixes

**Date:** 2026-02-24
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** Phase A complete — Prettier formatting, ESLint `no-unused-vars` fixes, and Commit 14 verification
**Commits:**

- `944b0f9` — `style(csapi): apply prettier formatting and fix eslint errors`

## Verification Status

### CI Gates

| Check             | Result                                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------- |
| format:check (C1) | ❌ 605 files fail — **pre-existing** (full-repo `prettier --check .` has never passed; all CSAPI files pass individually) |
| typecheck (C2)    | ✅ 0 errors                                                                                                               |
| lint (C3)         | ✅ 0 errors, 0 warnings                                                                                                   |
| test:browser (C4) | ⚠️ 1,641 passing / 5 failed (2 suites) — **pre-existing** failures in `endpoint.spec.ts` and `http-utils.spec.ts`         |
| test:node (C5)    | ⚠️ 1,720 passing / 1 failed (1 suite) — **pre-existing** failure in `endpoint.spec.ts`                                    |

**C1 Note:** `npm run format:check` runs `prettier --check .` across the entire repo. The upstream codebase has never been fully Prettier-formatted — 605 files (all non-CSAPI) fail. This pre-dates Phase 6. CSAPI-scoped check (`npx prettier --check "src/ogc-api/csapi/**/*.ts"`) passes cleanly.

**C4/C5 Note:** The 2 failing test suites (`endpoint.spec.ts` string-encoding mismatch, `http-utils.spec.ts` esbuild worker timeout) are pre-existing on the `phase-6` branch before any Phase 6 code changes. Confirmed by running tests on the parent commit `7fdb7d0`. All 29 CSAPI test suites pass.

### Boundary Gates

These gates verify CSAPI module isolation. Phase A (formatting) does not modify module boundaries — these are baselines for Phase B tracking.

| Gate | Command                                                                    | Expected (Phase B) | Actual (Phase A baseline) | Status     |
| ---- | -------------------------------------------------------------------------- | ------------------ | ------------------------- | ---------- |
| V1   | `git grep "from.*csapi" src/ogc-api/endpoint.ts`                           | 0                  | 2                         | ⏳ Phase B |
| V2   | `git grep "csapi\|CSAPI" src/index.ts`                                     | 0                  | 8                         | ⏳ Phase B |
| V3   | `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"`          | 0                  | 2                         | ⏳ Phase B |
| V4   | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` | 0                  | 2                         | ⏳ Phase B |

## Files Reviewed

### Task 1: Apply Prettier Formatting (49 files)

All 49 files in Commit 14 received `npx prettier --write` formatting at 80-char `printWidth`. The formatting changes are mechanical:

- Multi-line arrow functions collapsed to single lines where within width
- Object literals expanded to one-property-per-line
- Import statements reformatted (multi-line where exceeding width)
- Trailing commas added per Prettier defaults
- String quotes normalized

**Top contributor to diff volume:** `url_builder.spec.ts` (+2,221 lines Δ, ~73% of total diff) — inline link objects expanded from compact single-line to multi-line at `printWidth: 80`.

### Task 2a: Fix ESLint Source Files (5 files, 9 errors)

| File                            | Imports Removed                                   | Reason                                              |
| ------------------------------- | ------------------------------------------------- | --------------------------------------------------- |
| `url_builder.ts`                | `CSAPIResourceTypes`                              | Used only in JSDoc `@see` — not a runtime reference |
| `sensorml/aggregate-process.ts` | `ComponentEntry`, `parseIOComponentChoice`        | Unused imports                                      |
| `sensorml/parser.ts`            | `Position`, `parseIOComponentChoice`, `parseMode` | Unused imports (kept `parseModes` plural)           |
| `sensorml/physical-system.ts`   | `ComponentEntry`, `parseIOComponentChoice`        | Unused imports                                      |
| `sensorml/simple-process.ts`    | `parseIOComponentChoice`                          | Unused import                                       |

### Task 2b: Fix ESLint Test Files (10 files, 90 errors)

| File                                 | Errors Fixed | Fix Type                                                    |
| ------------------------------------ | ------------ | ----------------------------------------------------------- |
| `sensorml/aggregate-process.spec.ts` | 1            | Removed `import type { AggregateProcess }`                  |
| `sensorml/parser.spec.ts`            | 1            | Removed `import type { SensorMLProcess }`                   |
| `sensorml/physical-system.spec.ts`   | 2            | Removed `import type { PhysicalSystem, PhysicalComponent }` |
| `sensorml/simple-process.spec.ts`    | 1            | Removed `import type { SimpleProcess }`                     |
| `sensorml/types.spec.ts`             | 32           | Removed 32 unused type imports; kept 19 used types          |
| `swecommon/types.spec.ts`            | 27           | Removed 27 unused type imports; kept 16 used types          |
| `swecommon/index.spec.ts`            | 14           | Removed entire unused `import type` block (14 types)        |
| `swecommon/parser.spec.ts`           | 1            | Removed `AnyComponent` from type import                     |
| `swecommon/data-record.spec.ts`      | 1            | Removed unused `const result =` assignment                  |
| `integration/observation.spec.ts`    | 2            | Removed 2 unused `import type` lines                        |

**Audit verification:** All removals confirmed correct via subagent audit — no removed types are referenced in file bodies; all kept types are actively used.

### Task 3: Verify and Commit

Commit 14 recorded as `944b0f9` on `phase-6` branch with the prescribed commit message format.

| File                            | Lines Δ                     | Change Type         |
| ------------------------------- | --------------------------- | ------------------- |
| `src/ogc-api/csapi/` (48 files) | +3,012/−1,140               | Formatting + ESLint |
| `src/ogc-api/endpoint.ts`       | +2/−6                       | Formatting only     |
| **Total**                       | **49 files, +3,020/−1,148** |                     |

## Overall Codebase Metrics (Cumulative)

| Category                             | Files                        | Lines                                    | Tests     |
| ------------------------------------ | ---------------------------- | ---------------------------------------- | --------- |
| Phase 1–4 (URL Builder, Integration) | ~15                          | ~10,200                                  | ~643      |
| Phase 5 (Parsers)                    | ~41                          | ~15,800                                  | ~642      |
| Phase 6.1 (Formatting — no new code) | 0 new                        | +1,874 (formatting)                      | 0 new     |
| **Total CSAPI**                      | **56** (27 source + 29 test) | **27,919** (11,864 source + 16,055 test) | **1,285** |

**Line growth from Phase 5.6:** +1,874 lines (all formatting expansion, zero logic). Test:source ratio improved from 1.21 to 1.35 due to test file expansion from Prettier's multi-line object formatting.

## Prior Findings Status

### Phase 5.1 Findings

| ID  | Type                                              | Status                  |
| --- | ------------------------------------------------- | ----------------------- |
| F1  | POSITIVE: Consistent tolerant extraction pattern  | ✅ Unchanged            |
| F2  | POSITIVE: Correct instant-vs-interval distinction | ✅ Unchanged            |
| F3  | POSITIVE: Opaque `result` pass-through            | ✅ Unchanged            |
| F4  | POSITIVE: Cross-reference extraction tested       | ✅ Unchanged            |
| F5  | POSITIVE: `normalizeObservedProperties()`         | ✅ Unchanged            |
| F6  | POSITIVE: `parameters` array guard                | ✅ Unchanged            |
| F7  | GAP: No test for unknown `resultType` enum → null | ✅ RESOLVED (Phase 5.4) |
| F8  | GAP: No test for unknown `type` field → omitted   | ✅ RESOLVED (Phase 5.4) |
| F9  | GAP: Stale module-level JSDoc                     | ✅ RESOLVED (Phase 5.3) |
| F10 | INFORMATIONAL: Barrel exports deferred to Task 9a | ✅ RESOLVED (Phase 5.3) |
| F11 | INFORMATIONAL: `links` cast is trust-the-server   | ℹ️ Unchanged            |

### Phase 5.2 Findings

| ID      | Type                                                          | Status                                                                                              |
| ------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| F12     | POSITIVE: `normalizeStatusCode()` shared reuse                | ✅ Unchanged                                                                                        |
| F13     | POSITIVE: ControlStream parallels Datastream                  | ✅ Unchanged                                                                                        |
| F14     | POSITIVE: Time field asymmetry documented                     | ✅ Unchanged                                                                                        |
| F15     | POSITIVE: Required vs. optional statusCode                    | ✅ Unchanged                                                                                        |
| F16     | POSITIVE: Command parameters pass-through                     | ✅ Unchanged                                                                                        |
| F17     | POSITIVE: Cross-ref @id extraction                            | ✅ Unchanged                                                                                        |
| **F18** | **GAP (minor): `@see` link precision for parseCommandStatus** | ⚠️ **STILL OPEN** — deferred; Issue #98 closed `not_planned`. Existing link is technically correct. |
| F19     | GAP: Fixture ID collision `cs-minimal`                        | ✅ RESOLVED (#108)                                                                                  |
| F20     | INFORMATIONAL: Part 2 suite complete                          | ℹ️ Unchanged                                                                                        |
| F21     | INFORMATIONAL: Command parameters fallback spec-driven        | ℹ️ Unchanged                                                                                        |

### Phase 5.3 Findings

| ID  | Type                                                     | Status             |
| --- | -------------------------------------------------------- | ------------------ |
| F22 | POSITIVE: Schema response parsers delegate to SWE Common | ✅ Unchanged       |
| F23 | POSITIVE: Recursive delegation dispatches all 4 types    | ✅ Unchanged       |
| F24 | POSITIVE: Complete cross-type test coverage              | ✅ Unchanged       |
| F25 | POSITIVE: Integration wiring complete at 3 levels        | ✅ Unchanged       |
| F26 | POSITIVE: E2E pipeline tests validate full chain         | ✅ Unchanged       |
| F27 | CONSISTENCY: Duplicated `parseComponentEntry`            | ✅ RESOLVED (#109) |
| F28 | GAP: TS2352 cast in `pipeline.spec.ts`                   | ✅ RESOLVED (#110) |
| F29 | POSITIVE: P4 JSDoc documentation                         | ✅ Unchanged       |
| F30 | POSITIVE: Schema response inline import types            | ✅ Unchanged       |
| F31 | INFORMATIONAL: Phase 5 complete                          | ℹ️ Unchanged       |

### Phase 5.4 Findings

| ID  | Type                                             | Status             |
| --- | ------------------------------------------------ | ------------------ |
| F32 | POSITIVE: Enum test gaps correctly closed        | ✅ Unchanged       |
| F33 | POSITIVE: DRY extraction of parseComponentEntry  | ✅ Unchanged       |
| F34 | CONSISTENCY: Two separate re-export lines        | ✅ RESOLVED (#111) |
| F35 | POSITIVE: Fixture ID rename eliminates ambiguity | ✅ Unchanged       |

### Phase 5.5 Findings

| ID      | Type                                                             | Status                                                            |
| ------- | ---------------------------------------------------------------- | ----------------------------------------------------------------- |
| F36     | POSITIVE: Callback injection breaks circular imports             | ✅ Unchanged                                                      |
| F37     | POSITIVE: Cross-reference @id extraction                         | ✅ Unchanged                                                      |
| F38     | POSITIVE: PARAM_NAME_MAP                                         | ✅ Unchanged                                                      |
| F39     | POSITIVE: Missing query option fields                            | ✅ Unchanged                                                      |
| F40     | POSITIVE: Nested method option types narrowed                    | ✅ Unchanged                                                      |
| F41     | POSITIVE: CSAPIResourceRef type                                  | ✅ Unchanged                                                      |
| F42     | POSITIVE: @link extraction with robust array handling            | ✅ Extended (#114)                                                |
| F43     | POSITIVE: ControlStream navigation methods                       | ✅ Unchanged                                                      |
| F44     | POSITIVE: Correct deferral of out-of-scope issues                | ✅ Unchanged                                                      |
| **F45** | **DESIGN (minor): `getCommandStatus` uses string concatenation** | ⚠️ **STILL OPEN** — functionally correct, minor pattern deviation |
| F46     | CONSISTENCY: `getControlStreamProcedures` uses `QueryOptions`    | ✅ RESOLVED (#112)                                                |
| F47     | GAP: No combined-option test for `getCommandStatus`              | ✅ RESOLVED (#113)                                                |

### Phase 5.6 Findings

| ID  | Type                                                         | Status       |
| --- | ------------------------------------------------------------ | ------------ |
| F48 | POSITIVE: `type` → `rt` normalization follows Postel's Law   | ✅ Unchanged |
| F49 | POSITIVE: Review-finding-to-fix pipeline closes loop cleanly | ✅ Unchanged |
| F50 | POSITIVE: `rt` precedence test prevents future regression    | ✅ Unchanged |

## Phase 6.1 Findings — New

### [F51] POSITIVE: Zero-logic formatting correctly separated from architecture changes

**Severity:** POSITIVE
**Evidence:** Commit 14 (`944b0f9`) contains exclusively formatting and unused-import removal. `git show 944b0f9 -- src/ogc-api/endpoint.ts` confirms only whitespace consolidation (multi-line arrow → single-line, multi-line string → single-line). No behavioral changes, no new code paths, no modified control flow. This follows the "Format First" commit strategy from Plan 07 and upstream precedent of 5+ formatting-only commits.

### [F52] POSITIVE: ESLint audit methodology — subagent-verified removals

**Severity:** POSITIVE
**Evidence:** All 99 ESLint `no-unused-vars` fixes were verified by a dedicated subagent audit that:

1. Read the full contents of all 10 test files with import removals
2. Confirmed no removed types appear in file bodies (type annotations, `as` casts, generics)
3. Confirmed all kept types are actively used with specific line references
4. Verified the `data-record.spec.ts` `const result =` removal was correct (result never referenced after the call)

This dual-verification approach (automated ESLint + manual audit) provides high confidence in correctness.

### [F53] INFORMATIONAL: Commit message inaccuracy — "51 files" and "4 fixture JSON"

**Severity:** INFORMATIONAL
**Details:** The Commit 14 message states "51 files changed (46 CSAPI source/test + 4 fixture JSON + endpoint.ts)" but `git show --stat` reports 49 files, all within `src/`. Zero fixture files (`fixtures/ogc-api/csapi/**/*.json`) were modified because they already passed Prettier formatting. The "51 files" and "4 fixture JSON" claims are inaccurate.
**Impact:** No behavioral impact — purely a commit message documentation issue. The committed code is correct.
**Recommendation:** Note for future commits. Not worth amending as it would change the commit hash.

### [F54] BUG: `git checkout HEAD~1 -- .` during review caused working tree reversion

**Severity:** BUG (process, not code)
**Details:** During the Task 3 verification, a `git checkout HEAD~1 -- .` command was run to test whether `npm run format:check` was pre-existing. This command overwrote the working tree AND staged the old (pre-commit) file versions. The subsequent `git status --short` appeared clean because both index and working tree matched (both at HEAD~1 state). This was detected during the code review when `npm run lint` reported 99 errors.
**Resolution:** Fixed immediately with `git checkout HEAD -- .` which restored all files to match Commit 14. The commit itself (`944b0f9`) was never affected — only the working tree/index were temporarily wrong.
**Root Cause:** Using `git checkout <ref> -- .` as an investigation tool is destructive to the working tree and index. For future investigations, use `git stash` + `git checkout <ref>` (detached HEAD) or `git show <ref>:<file>` for individual file inspection.
**Lesson:** Never use `git checkout <commit> -- .` to inspect prior states. Use `git stash`/`git switch --detach` or read-only commands like `git show`.

### [F55] INFORMATIONAL: Pre-existing CI gate failures (C1, C4, C5)

**Severity:** INFORMATIONAL
**Details:** Three CI gates fail on the `phase-6` branch, all pre-existing:

- **C1** (`format:check`): 605 non-CSAPI files fail Prettier — the upstream repo was never fully formatted
- **C4** (`test:browser`): 5 tests in 2 suites fail — `endpoint.spec.ts` (string encoding mismatch) and `http-utils.spec.ts` (esbuild worker timeout)
- **C5** (`test:node`): 1 test in `endpoint.spec.ts` fails (same string encoding issue)

These failures exist on the parent commit `7fdb7d0` before any Phase 6 work. They are not caused by or affected by Phase 6 changes. The GitHub Actions QA workflow is currently disabled for `phase-6` branch (commented out in `qa.yml`).
**Impact:** If the QA workflow were enabled on `phase-6`, it would fail on C1 and C4/C5 due to these pre-existing issues. The upstream repo's `main` branch likely has the same C1 failure.

### [F56] POSITIVE: Lesson 1 compliance — no new architectural layers

**Severity:** POSITIVE
**Evidence:** Phase A introduces zero new abstractions, patterns, or architectural layers. All changes are mechanical formatting (Prettier) and automated lint fixes (unused import removal). This directly follows Lesson 1 ("Audit Upstream Before Building New Layers") — Phase A builds nothing new.

### [F57] POSITIVE: Lesson 4 compliance — no parallel systems

**Severity:** POSITIVE
**Evidence:** No new functions, types, or modules introduced. No potential for parallel systems. Lesson 4 ("Don't Build Parallel Systems") is trivially satisfied.

## Architecture Verification Matrix

| Gate | Command                                          | Expected    | Actual                             | Status          |
| ---- | ------------------------------------------------ | ----------- | ---------------------------------- | --------------- |
| V1   | `git grep "from.*csapi" src/ogc-api/endpoint.ts` | 0 (Phase B) | 2                                  | ⏳ Phase B      |
| V2   | `git grep "csapi\|CSAPI" src/index.ts`           | 0 (Phase B) | 8                                  | ⏳ Phase B      |
| V3   | Cross-module CSAPI imports                       | 0 (Phase B) | 2                                  | ⏳ Phase B      |
| V4   | Non-index CSAPI imports                          | 0 (Phase B) | 2                                  | ⏳ Phase B      |
| C1   | `npm run format:check`                           | exit 0      | exit 1 (pre-existing)              | ⚠️ Pre-existing |
| C2   | `npm run typecheck`                              | exit 0      | exit 0                             | ✅              |
| C3   | `npm run lint`                                   | exit 0      | exit 0                             | ✅              |
| C4   | `npm run test:browser`                           | all pass    | 1,641 pass / 5 fail (pre-existing) | ⚠️ Pre-existing |
| C5   | `npm run test:node`                              | all pass    | 1,720 pass / 1 fail (pre-existing) | ⚠️ Pre-existing |

## Task Completion Heatmap

| Dimension            | Task 1 | Task 2a | Task 2b | Task 3 | Task 4a | Task 4b | Task 5 | Task 6 | Task 7 | Task 8 | Task 9 | Task 10a | Task 10b |
| -------------------- | ------ | ------- | ------- | ------ | ------- | ------- | ------ | ------ | ------ | ------ | ------ | -------- | -------- |
| Deliverable complete | ✅     | ✅      | ✅      | ✅     | —       | —       | —      | —      | —      | —      | —      | —        | —        |
| Formatting compliant | ✅     | ✅      | ✅      | ✅     | —       | —       | —      | —      | —      | —      | —      | —        | —        |
| Boundary clean       | —      | —       | —       | —      | —       | —       | —      | —      | —      | —      | —      | —        | —        |
| Tests pass           | ✅     | ✅      | ✅      | ✅     | —       | —       | —      | —      | —      | —      | —      | —        | —        |
| Committed            | ✅     | ✅      | ✅      | ✅     | —       | —       | —      | —      | —      | —      | —      | —        | —        |

Phase A (Tasks 1–3) is fully complete. All 4 tasks delivered, formatted, tested, and committed as Commit 14.

## Summary

| Category                     | Count | Details                                          |
| ---------------------------- | ----- | ------------------------------------------------ |
| Files reviewed               | 49    | All files in Commit 14                           |
| New findings                 | 7     | F51–F57                                          |
| POSITIVE findings            | 4     | F51, F52, F56, F57                               |
| BUG findings                 | 1     | F54 (process — working tree reversion, resolved) |
| INFORMATIONAL findings       | 2     | F53, F55                                         |
| Still-open prior findings    | 2     | F18, F45 (both minor, both deferred)             |
| Total findings (all reviews) | 57    | 45 POSITIVE, 7 resolved, 2 open, 3 INFORMATIONAL |

## Recommendations

### Fix Now (before next task)

None. All code is correct. The working tree reversion (F54) was already resolved.

### Fix Before Push (before upstream)

1. **Investigate C1 (`format:check`)** — Determine whether upstream `main` also fails `npm run format:check`. If yes, this is not our problem. If no, we need to understand why `phase-6` has 605 files failing. (Likely answer: the `.prettierrc.json` or Prettier version differs, or upstream has a `.prettierignore` that excludes certain files.)
2. **Investigate C4/C5 pre-existing test failures** — The `endpoint.spec.ts` string-encoding test and `http-utils.spec.ts` worker timeout should be understood before the PR. Determine if they also fail on upstream `main`.

### Defer (Low Priority)

1. **F53 commit message inaccuracy** — Not worth amending. Note for future commit messages.
2. **F18 `@see` link precision** — Deferred since Phase 5.2. Existing link is technically correct.
3. **F45 string concatenation pattern** — Deferred since Phase 5.5. Functionally correct.

## Root Cause Analysis

### F54: Working Tree Reversion

**What happened:** During Task 3 verification, `git checkout HEAD~1 -- .` was run to test whether `npm run format:check` failures were pre-existing. This command:

1. Read all files from the parent commit (pre-formatting state)
2. Wrote them to the index (staging area)
3. Wrote them to the working tree

**Why it wasn't caught sooner:** `git status --short` showed clean because both the index and working tree were at the same (wrong) state. The divergence was only between HEAD and the index — which `git status` shows as "Changes to be committed" (long form) but not in `--short` format without changes to unstaged files.

**How it was detected:** The code review's `npm run lint` gate caught 99 ESLint errors that should have been fixed.

**Resolution:** `git checkout HEAD -- .` restored the correct state. The commit itself was never corrupted.

**Prevention:** Use read-only inspection commands (`git show <ref>:<path>`, `git diff <ref1>..<ref2>`) instead of destructive checkout commands. If a full-tree comparison is needed, use `git stash` + `git switch --detach <ref>` + `git switch -` + `git stash pop`.

## Overall Assessment

Phase A is complete and correct. Commit 14 (`944b0f9`) packages all Prettier formatting and ESLint `no-unused-vars` fixes into a single formatting-only commit with zero logic changes, exactly as designed in the Phase 6 roadmap.

The code quality is high. All 99 ESLint errors were correctly resolved — 9 in source files (unused import removal) and 90 in test files (unused type import removal + 1 unused variable). Each removal was verified by both automated tools (ESLint, tsc) and manual audit (subagent file-body scanning). The separation of formatting from logic changes follows upstream precedent and makes the subsequent Commit 15 (architecture) diff reviewable.

The one process issue (F54 — accidental working tree reversion) was caught by this code review's verification gates, demonstrating the value of the systematic gate-checking approach. The working tree is now correctly restored to match Commit 14.

Phase A is ready to serve as the base for Phase B architecture tasks (Tasks 4a–9). The boundary gates (V1–V4) establish the baseline — they currently show CSAPI coupling that Phase B will eliminate. The next review (Phase 6.2) will track these gates moving toward zero.
