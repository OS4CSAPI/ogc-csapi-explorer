# Task Granularity Review

**Date:** February 24, 2026  
**Purpose:** Pre-implementation review of P6-ROADMAP task granularity to identify which tasks are safe for single-pass execution and which warrant splitting for risk reduction.  
**Input:** [P6-ROADMAP.md v1.0](../../planning/phase-6/P6-ROADMAP.md) (584 lines, 10 tasks, 3 phases)  
**Output:** 3 recommended splits (10 tasks → 13 execution units)

---

## Analysis Methodology

Each of the 10 original tasks was evaluated against four risk dimensions:

1. **File count** — More files = more surface area for mistakes
2. **Error pattern diversity** — Heterogeneous fixes are harder than homogeneous ones
3. **Reversibility** — Can a mistake be undone with `git reset`, or is it permanent?
4. **Logical seams** — Does the task contain a natural break point where a commit or pause would reduce risk?

Tasks were classified as "safe for one pass" or "recommend splitting." A subsequent challenge ("are you sure we shouldn't break them up any further?") prompted a second review pass, which identified one additional split.

---

## Initial Assessment: 8 Safe, 2 Recommend Splitting

### Tasks Safe for One Pass

**Task 1: Apply Prettier to 51 files** — Fully automated (`npx prettier --write`). Zero judgment calls. If Prettier introduces a regression, `git checkout -- .` reverts everything instantly. The 51-file count is irrelevant because every change is deterministic.

**Task 3: Verify and Commit (Commit 14)** — Pure verification (run commands, check output) followed by a single `git commit`. No code authoring. Linear checklist execution.

**Task 5: Create `factory.ts` + `factory.spec.ts`** — Two small files (~55 + ~30 lines) that form a single logical unit. The factory function and its tests are inseparable — creating one without the other leaves the codebase in an inconsistent state. Complete code sketches exist in the Implementation Guide §6.2–6.3.

**Task 6: Modify `endpoint.ts`** — Five surgical deletions (2 imports, 1 cache, 2 methods) and two `private` → `public` visibility changes. Each removal is independent, and `npx tsc --noEmit` after each deletion catches issues immediately. Net change: −63 lines. Every removal has an exact line reference in the Implementation Guide.

**Task 7: Modify `index.ts` + `endpoint.spec.ts`** — Two files, but the work is purely deletional: remove 183 lines of CSAPI exports from `index.ts`, remove 3 tests from `endpoint.spec.ts`. No new code. Deletion is the lowest-risk edit type — removing lines that are no longer referenced cannot introduce new bugs.

**Task 8: Modify `package.json`** — Two additions: a `"./csapi"` sub-path export block and `"sideEffects": false`. Both are JSON insertions with exact content specified in the Implementation Guide. The file is ~60 lines. Risk is near-zero.

**Task 9: Run CI Gates and Commit (Commit 15)** — Pure verification followed by a commit. Same pattern as Task 3.

### Tasks Recommended for Splitting

**Task 2: Fix 99 ESLint errors across 15 files → Split into 2a + 2b**

The 99 errors span two distinct file populations with different error patterns:

| Sub-task             | Files | Errors | Pattern                                                   |
| -------------------- | ----- | ------ | --------------------------------------------------------- |
| **2a: Source files** | 5     | 9      | Mix of `import type` conversions + unused import removals |
| **2b: Test files**   | 10    | 90     | Almost entirely unused import removals (bulk delete)      |

**Why split:** Source files require judgment (is the import used as a type annotation? → convert to `import type`. Is it truly unused? → remove entirely). Test files are mechanical bulk removal. Mixing them invites applying the wrong fix pattern to the wrong file. The split also provides a natural verification checkpoint — run `npx tsc --noEmit` after 2a to confirm source files still compile before touching tests.

**Task 4: Create barrel file `csapi/index.ts` → Split into 4a + 4b**

The barrel file requires tracing every CSAPI symbol currently in `src/index.ts` (lines 45–227) back to its source module, then writing ~190 lines of organized re-exports.

| Sub-task                            | Deliverable                                                                                          | Risk                                    |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **4a: Audit and build export list** | Complete inventory of every CSAPI public symbol, its source module, and whether it's a value or type | Zero code changes — pure research       |
| **4b: Write barrel file**           | `csapi/index.ts` with all re-exports, JSDoc sections, `.js` extensions                               | New file creation from the 4a inventory |

**Why split:** The barrel file is the most content-dense new file (~190 lines). Errors in mapping symbols to source modules cascade downstream — if a re-export points to the wrong path, TypeScript fails at compile time but the error message may point to the consumer, not the barrel. Separating the audit from the write ensures the mapping is verified before committing to code.

---

## Second Review: One Additional Split

When challenged with "are you sure we shouldn't break them up any further?", a second pass was performed. The remaining 6 safe tasks were re-examined. One additional split was identified:

**Task 10: Boundary verification, litmus test, and rebase → Split into 10a + 10b**

| Sub-task                            | Actions                                                                  | Reversibility                                               |
| ----------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------- |
| **10a: Verification + litmus test** | Run V1–V4 boundary checks, litmus test (mv/compile/restore), diff review | Fully reversible — read-only checks + temp rename           |
| **10b: Rebase + push to upstream**  | Cherry-pick to `clean-pr`, force-push to upstream fork, update PR #136   | **Irreversible** — changes remote state visible to reviewer |

**Why split:** Everything in 10a is local and reversible. Everything in 10b modifies remote branches that the upstream maintainer (jahow) can see. If verification reveals an issue, the natural response is "go fix it" — which is easier if you haven't already pushed. The split creates a gate: only cross to 10b when 10a confirms everything is green.

### Tasks Confirmed Safe After Second Review

**Task 1** — Automated, deterministic.  
**Task 3** — Verification + commit, no code authoring.  
**Task 5** — Two small files, single logical unit, complete code sketches.  
**Task 6** — Surgical deletions with immediate type-check validation.  
**Task 7** — Pure deletion in two files.  
**Task 8** — Two JSON additions to an existing file.  
**Task 9** — Verification + commit.

None of these contain a risk boundary that a split would mitigate. Adding splits to any of them would increase coordination overhead without reducing error probability.

---

## Why Two-Way Splits Are Sufficient (No Three-Way Needed)

A final challenge asked whether Task 2 or Task 4 should be split into three rather than two sub-tasks. The answer is no, for the following reasons:

### Task 2 (ESLint fixes)

The 90 errors in 2b sound volumetrically large, but they are mechanical, repetitive patterns (remove unused imports). Each fix is independent and localized — no fix affects another. Splitting test files into two batches (2b + 2c) would add a commit boundary in the middle of identical work with no risk reduction. The danger in 2b isn't volume — it's that test files differ from source files in error patterns. That risk is already captured by the 2a/2b split.

### Task 4 (barrel file)

The entire deliverable is one small file (~15–20 export lines per section, ~190 total). 4a (audit what to export) is pure research with zero code changes. 4b (write the file) is writing the audited lines. A third split would mean something like "4a: audit, 4b: write half the exports, 4c: write the other half" — that's artificially granular for a file shorter than most config files.

### Principle

The splits are calibrated to **risk boundaries**, not volume:

- **Task 2** splits at the **source/test boundary** (different error patterns, different validation)
- **Task 4** splits at the **research/write boundary** (no code vs. new code)
- **Task 10** splits at the **verify/deliver boundary** (reversible vs. irreversible)

Adding a third split to any of these would increase coordination overhead without meaningfully reducing the chance of error.

---

## Final Execution Unit Plan

| #   | Unit                                                 | Est. Time | Complexity | Split From |
| --- | ---------------------------------------------------- | --------- | ---------- | ---------- |
| 1   | Task 1: Apply Prettier to 51 files                   | ~0.5h     | Low        | —          |
| 2a  | Task 2a: Fix 9 ESLint errors in 5 source files       | ~0.5h     | Low        | Task 2     |
| 2b  | Task 2b: Fix 90 ESLint errors in 10 test files       | ~0.5–1h   | Low        | Task 2     |
| 3   | Task 3: Verify formatting + lint, commit (Commit 14) | ~0.5h     | Low        | —          |
| 4a  | Task 4a: Audit and build CSAPI export inventory      | ~0.5h     | Medium     | Task 4     |
| 4b  | Task 4b: Write barrel file `csapi/index.ts`          | ~0.5–1h   | Medium     | Task 4     |
| 5   | Task 5: Create `factory.ts` + `factory.spec.ts`      | ~1–1.5h   | Medium     | —          |
| 6   | Task 6: Modify `endpoint.ts`                         | ~0.5–1h   | Medium     | —          |
| 7   | Task 7: Modify `index.ts` + `endpoint.spec.ts`       | ~0.5h     | Low        | —          |
| 8   | Task 8: Modify `package.json`                        | ~0.25h    | Low        | —          |
| 9   | Task 9: Run all CI gates, commit (Commit 15)         | ~0.5–1h   | Low        | —          |
| 10a | Task 10a: Boundary verification + litmus test        | ~0.5–1h   | Medium     | Task 10    |
| 10b | Task 10b: Rebase to clean-pr + push to upstream      | ~0.5h     | Medium     | Task 10    |

**Total: 10 tasks → 13 execution units, ~6–10 hours estimated**

**Execution order:** 1 → 2a → 2b → 3 → 4a → 4b → 5 → 6 → 7 → 8 → 9 → 10a → 10b
