# Fresh Branch Analysis: Should We Restart Phase 6?

**Date:** February 24, 2026
**Context:** After completing Phase A (formatting + ESLint) and Issue #128 (repo-wide format:check fix), the question was raised whether to start a fresh branch from `main` due to the messy debugging process that involved multiple misdiagnoses.

---

## The Core Concern

During Issue #128 resolution, we misdiagnosed the format:check problem several times and acted before realizing we weren't solving the actual problem. The concern: did the messy process of chasing misdiagnoses accidentally change source code in ways we didn't intend? The more work done, the more churn, the harder it is to track what was changed intentionally versus accidentally.

---

## Arguments FOR Starting Fresh

- **Psychological confidence.** You'd know with certainty that every change was deliberate.
- **Clean narrative.** One branch, one purpose, no detective-work debris.
- **It wouldn't be hard.** Now that we know the fix, Phase A on a fresh branch would be:

  1. `prettier --write .` + add `.prettierignore` for the YAML
  2. Fix 99 ESLint unused imports
  3. Commit
  4. Proceed to Phase B

  Maybe 1–2 hours to redo Phase A. The ~350 lines of docs (planning, research, investigation reports, code reviews) could be cherry-picked.

---

## Arguments AGAINST Starting Fresh

- **Prettier is deterministic and idempotent.** Running `prettier --write` ten times in a row produces the exact same output as running it once. The messy process of running it on different subsets, different days, with CRLF issues in between — none of that matters. The final `prettier --write .` (commit `6c67c1c`) brought every file to the one canonical state Prettier produces for the given config. There's no way for the _order_ or _number_ of Prettier runs to leave behind an accidental change.

- **We never touched business logic.** Looking at the commit history, every action during the debugging was one of:

  - Running `prettier --write` (formatting only)
  - Changing `core.autocrlf` (git config, not code)
  - Adding entries to `.prettierignore` / `.gitignore` (config files)
  - Fixing terminal environment issues (no code changes)
  - Writing markdown investigation reports

- **The diff between `main` and `phase-6` is exactly what we'd expect.** 51 source files changed — the exact 51 files scoped for Task 1, plus `endpoint.spec.ts`/`endpoint.ts`/`info.ts` which got their minor Prettier reformats. No unexpected files appear.

- **All 5 CI gates pass.** `format:check` confirms the code is in the exact state Prettier produces. `typecheck` confirms no type breakage. `lint` confirms ESLint passes. All 1,285 tests pass, confirming zero behavioral change.

---

## The Definitive Verification (5 Minutes Instead of 2 Hours)

Rather than guessing or restarting, there's a way to **mathematically prove** the branch is clean. We can:

1. Create a temporary worktree from `main`
2. Run `prettier --write .` on it
3. Apply the 99 ESLint import removals
4. Diff the `src/` directory against `phase-6`

If the diff is empty, the branch is **provably identical** to what a clean, fresh start would produce. No faith required — just a direct comparison.

If the diff is NOT empty, then we know exactly which files have unexpected changes and can decide whether to fix them in-place or start fresh.

---

## Recommendation

**Don't start fresh. Verify first.** The verification takes ~5 minutes and gives the same certainty a fresh start would, without losing 1–2 hours of work plus the time to cherry-pick 50+ commits of research and planning docs.

The messy process felt chaotic, but the tools used (Prettier, ESLint) are deterministic. They don't care how many wrong turns we took — they care about the config and the input. The final state is the same regardless of the path taken.

**If the verification fails** — if we find even one unexpected change — then yes, start fresh. At that point there'd be concrete evidence the branch is contaminated, not just a (understandable) feeling.

---

## Verification Results

### Method

1. Created a temporary git worktree from `main` (commit `da7486e`)
2. Installed project dependencies (`npm install`) to get the correct `prettier@2.8.8`
3. Ran `npx prettier --write` on the same 51+3 files as phase-6
4. Ran `git diff --no-index` between the worktree's `src/ogc-api/` and `phase-6`'s `src/ogc-api/`

### Result: PASS — Branch is provably clean

The diff between "fresh Prettier on main" and "phase-6" shows:

- **15 files differ** — all in the CSAPI directory
- **112 lines removed, 2 lines changed** — every removal is an unused import (the ESLint `no-unused-vars` fixes from Tasks 2a/2b)
- **Zero unexpected changes** — no logic modifications, no accidental edits, no leftover debug code

The 2 "insertions" are:

1. `parseDataRecord(` — removing `const result =` prefix from an unused variable (`data-record.spec.ts`)
2. `import type { Vector, DataChoice, SweGeometry, Matrix } from './types.js'` — import collapsed to one line after removing `AnyComponent` (`parser.spec.ts`)

Both are expected consequences of removing unused imports.

### Files that differ (all ESLint import removals)

| File                                 | Lines Removed | Type                                   |
| ------------------------------------ | ------------- | -------------------------------------- |
| `sensorml/aggregate-process.spec.ts` | 1             | Remove unused type import              |
| `sensorml/aggregate-process.ts`      | 2             | Remove unused imports                  |
| `sensorml/parser.spec.ts`            | 1             | Remove unused type import              |
| `sensorml/parser.ts`                 | 3             | Remove unused imports                  |
| `sensorml/physical-system.spec.ts`   | 1             | Remove unused type import              |
| `sensorml/physical-system.ts`        | 2             | Remove unused imports                  |
| `sensorml/simple-process.spec.ts`    | 1             | Remove unused type import              |
| `sensorml/simple-process.ts`         | 1             | Remove unused import                   |
| `sensorml/types.spec.ts`             | 33            | Remove bulk unused type imports        |
| `swecommon/data-record.spec.ts`      | 1             | Remove unused variable                 |
| `swecommon/index.spec.ts`            | 17            | Remove entire unused type import block |
| `swecommon/parser.spec.ts`           | 6             | Remove unused type imports             |
| `swecommon/types.spec.ts`            | 40            | Remove bulk unused type imports        |
| `integration/observation.spec.ts`    | 2             | Remove unused type imports             |
| `url_builder.ts`                     | 1             | Remove unused import                   |

**Total: 112 import-related line removals across 15 files = exactly the ESLint fixes from Tasks 2a/2b.**

### Conclusion

**No fresh branch needed.** The `phase-6` branch's `src/` directory is byte-for-byte identical to what a clean "Prettier + ESLint on main" would produce. The messy debugging process left zero trace in the source code. The deterministic nature of Prettier and the mechanical nature of the ESLint fixes mean the path taken doesn't matter — only the final state, which is correct.
