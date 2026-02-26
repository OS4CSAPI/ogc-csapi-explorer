# Phase 6: Upstream Acceptance Refactoring — Roadmap

**Version:** 1.1  
**Date:** February 24, 2026  
**Status:** Ready for Execution  
**Scope:** Module boundary refactoring only — zero CSAPI business logic changes

---

## Executive Summary

This roadmap covers the execution of **Phase 6: Upstream Acceptance Refactoring** — decoupling the CSAPI module from the core ogc-client library to satisfy upstream maintainer jahow's two acceptance requirements from [PR #136](https://github.com/camptocamp/ogc-client/pull/136). The work is organized into **3 sequential phases (10 tasks, 13 execution units)** spanning an estimated **6–10 hours of development time** (1 week calendar time).

> **Full Context**
>
> This roadmap is the execution plan derived from the [P6 Implementation Guide](P6-implementation-guide.md) (990 lines, 14 sections), which contains complete file-level specifications, code sketches, and commit messages. The [P6 Contribution Goal and Definition](P6-contribution-goal-and-definition.md) defines the acceptance criteria and scope boundaries. Zero open design questions remain — see [Design Decision Resolution Report](../../research/phase-6/design-decision-resolution-report.md).
>
> **Refer to the [P6 Implementation Guide](P6-implementation-guide.md) for complete per-file specifications, code sketches, and exact commit messages.**

**Roadmap Overview:**

- **Phase A: Formatting and ESLint (2–3 hours)** — Automated Prettier + manual ESLint fixes across 51 files (Commit 14)
- **Phase B: Architecture Refactoring (3–5 hours)** — 3 files created, 4 files modified, module boundary decoupled (Commit 15)
- **Phase C: Verification and Delivery (1–2 hours)** — 12 verification gates, litmus test, rebase to clean-pr, push

**What this covers:**

- Remove ~183 lines of CSAPI exports from `src/index.ts`
- Create barrel file `csapi/index.ts` (~190 lines) as new entry point
- Create factory function `csapi/factory.ts` (~55 lines) replacing `endpoint.csapi()`
- Create factory tests `csapi/factory.spec.ts` (~30 lines)
- Remove 2 CSAPI imports + 1 cache + 2 methods from `endpoint.ts` (~65 lines removed)
- Add `"./csapi"` sub-path export and `"sideEffects": false` to `package.json`
- Migrate 2 endpoint tests to factory.spec.ts, remove 1 obsolete caching test
- Apply Prettier formatting to 51 files (~3,023 insertion lines)
- Fix 99 ESLint `no-unused-vars` errors across 15 files

**Estimated volume:**

- ~280 lines of new code (barrel file + factory + factory tests)
- ~275 lines removed (endpoint method + root exports + migrated tests)
- ~3,023 lines of automated Prettier formatting changes
- Net architecture diff: ~+5 lines (excluding formatting)

**What this does NOT cover:** CSAPI business logic, URL builder methods, format parsers, model types, SensorML/SWE Common parsers, integration tests, or any work outside the module boundary refactoring. The CSAPI implementation is complete from Phases 1–5 (1,282 tests, 29 suites, 0 tsc errors). Phase 6 changes zero CSAPI behavior.

**Key Facts:**

- All design decisions resolved through 8 research plans (285 questions, ~8,000 lines of findings)
- Zero open questions — every fork collapsed to a single choice (see [Resolution Report](../../research/phase-6/design-decision-resolution-report.md))
- Commit 14 (formatting) is fully automated except for 99 manual ESLint import removals
- Commit 15 (architecture) has complete code sketches in the [Implementation Guide §6–7](P6-implementation-guide.md#6-new-file-specifications)
- `url_builder.spec.ts` accounts for ~55% of the Prettier formatting diff (2,221 of 4,059 lines)
- Consumer API change: `endpoint.csapi(id)` → `createCSAPIBuilder(endpoint, id)`
- Branching: implement on `phase-6`, rebase code commits to `clean-pr`, push to upstream fork

**Execution unit summary:**

| #   | Unit                                                 | Est. Time | Complexity |
| --- | ---------------------------------------------------- | --------- | ---------- |
| 1   | Task 1: Apply Prettier to 51 files                   | ~0.5h     | Low        |
| 2a  | Task 2a: Fix 9 ESLint errors in 5 source files       | ~0.5h     | Low        |
| 2b  | Task 2b: Fix 90 ESLint errors in 10 test files       | ~0.5–1h   | Low        |
| 3   | Task 3: Verify formatting + lint, commit (Commit 14) | ~0.5h     | Low        |
| 4a  | Task 4a: Audit and build CSAPI export inventory      | ~0.5h     | Medium     |
| 4b  | Task 4b: Write barrel file `csapi/index.ts`          | ~0.5–1h   | Medium     |
| 5   | Task 5: Create `factory.ts` + `factory.spec.ts`      | ~1–1.5h   | Medium     |
| 6   | Task 6: Modify `endpoint.ts`                         | ~0.5–1h   | Medium     |
| 7   | Task 7: Modify `index.ts` + `endpoint.spec.ts`       | ~0.5h     | Low        |
| 8   | Task 8: Modify `package.json`                        | ~0.25h    | Low        |
| 9   | Task 9: Run all CI gates, commit (Commit 15)         | ~0.5–1h   | Low        |
| 10a | Task 10a: Boundary verification + litmus test        | ~0.5–1h   | Medium     |
| 10b | Task 10b: Rebase to clean-pr + push to upstream      | ~0.5h     | Medium     |

**Total: 10 tasks, 13 execution units, ~6–10 hours**

**Execution order:** 1 → 2a → 2b → 3 → 4a → 4b → 5 → 6 → 7 → 8 → 9 → 10a → 10b

> **Task splits rationale:** Three tasks were split at natural risk boundaries — see [Task Granularity Review](../../research/phase-6/task-granularity-review.md) for full analysis. Splits are calibrated to risk boundaries (source/test, research/write, verify/deliver), not volume.

**Dependencies:**

- Phase A → Phase B (Prettier must precede architecture changes — line numbers shift after formatting)
- Phase B → Phase C (code must be complete before verification and rebase)
- Within Phase B: Task 4 → Tasks 5–8 (barrel file defines what's exported; other files reference it)

**Success Factors:**

- Apply Prettier FIRST — line numbers in the implementation guide are based on formatted code
- Write new files Prettier-compliant from inception (single quotes, semicolons, 80-char width)
- Use `.js` extensions on all local imports/re-exports (TypeScript ESM convention)
- Run `npm run typecheck` after each file modification in Phase B — catch issues immediately
- Verify all 12 gates before pushing — no partial passes

---

## Task Ordering Rationale

Tasks are ordered by **dependency chain** and **commit boundary alignment**:

1. **Format first (Tasks 1–3, Commit 14).** The ~3,023-line Prettier diff MUST be separated from the ~5-line net architecture diff. A reviewer can skip Commit 14 entirely and focus on Commit 15. Upstream has 5+ formatting-only commit precedents. More critically, line numbers in the file specifications are based on the formatted state — applying formatting after architecture changes would invalidate all line references.

2. **Barrel file first in architecture (Task 4).** The barrel file `csapi/index.ts` defines the complete CSAPI public API surface. It must exist before `index.ts` can be modified (to remove the old exports) and before `package.json` can reference it (as the `"./csapi"` entry point). All other architecture tasks reference symbols that the barrel file re-exports.

3. **Factory + tests together (Task 5).** The factory function and its tests are a single logical unit — `factory.ts` is the replacement for the `endpoint.csapi()` method being removed in Task 6. Creating both before modifying endpoint ensures the replacement exists before the removal.

4. **Endpoint before index (Tasks 6–7).** Removing CSAPI imports from `endpoint.ts` must happen while the barrel file already exists. Removing CSAPI exports from `index.ts` immediately after. Test migration in `endpoint.spec.ts` happens simultaneously — the 3 tests referencing the removed `csapi()` method must be removed/migrated in the same logical step.

5. **Package.json last in architecture (Task 8).** The `"./csapi"` sub-path export references `dist/ogc-api/csapi/index.js` — the compiled barrel file. Adding it last ensures the source file it references (`csapi/index.ts`) already exists and passes type checking.

6. **Verification and delivery last (Tasks 9–10).** All code changes must be stable and committed before running the 12-gate verification plan, litmus test, and rebasing to `clean-pr`.

---

## Phase A: Formatting and ESLint (Commit 14)

**Estimated Time:** 2–3 hours  
**Goal:** Pass upstream CI formatting and linting gates with zero logic changes.

### Task 1: Apply Prettier Formatting

**Estimated Time:** ~0.5 hours  
**Complexity:** Low (fully automated)

- Run Prettier on all CSAPI source files (20 files):
  ```bash
  npx prettier --write "src/ogc-api/csapi/**/*.ts"
  ```
- Run Prettier on all CSAPI fixture JSON files (4 files):
  ```bash
  npx prettier --write "fixtures/ogc-api/csapi/**/*.json"
  ```
- Run Prettier on endpoint.ts (1 file, 8-line formatting diff):
  ```bash
  npx prettier --write "src/ogc-api/endpoint.ts"
  ```
- **Total:** 51 files formatted
- **Volume note:** `url_builder.spec.ts` accounts for ~55% of the formatting diff (2,221 of 4,059 lines) due to inline link object expansion at 80-char `printWidth`
- **Deliverable:** All 51 files Prettier-compliant

### Task 2a: Fix ESLint Errors in Source Files

**Estimated Time:** ~0.5 hours  
**Complexity:** Low  
**Split rationale:** Source files require judgment (`import type` conversions vs. removals); test files are mechanical bulk removal. Split at the source/test risk boundary. See [Task Granularity Review](../../research/phase-6/task-granularity-review.md).

9 errors across 5 source files — **all `@typescript-eslint/no-unused-vars`**.

**Fix approach:** Remove unused imports entirely, or convert `import { X }` to `import type { X }` where the import is used only as a type annotation. Do NOT prefix with `_` unless it is a function parameter (not an import).

| File                                    | Errors | Fix Pattern                        |
| --------------------------------------- | ------ | ---------------------------------- |
| `url_builder.ts`                        | 1      | Remove unused import               |
| `formats/sensorml/aggregate-process.ts` | 2      | Remove or convert to `import type` |
| `formats/sensorml/parser.ts`            | 2      | Remove or convert to `import type` |
| `formats/sensorml/physical-system.ts`   | 3      | Remove or convert to `import type` |
| `formats/sensorml/simple-process.ts`    | 1      | Remove unused import               |

- **Verification:** `npx tsc --noEmit` after all 5 files — confirm source still compiles
- **Deliverable:** 9 ESLint errors resolved in source files

### Task 2b: Fix ESLint Errors in Test Files

**Estimated Time:** ~0.5–1 hours  
**Complexity:** Low (mechanical bulk removal)

90 errors across 10 test files — **all `@typescript-eslint/no-unused-vars`**, almost entirely unused import removals.

| File                                         | Errors | Fix Pattern           |
| -------------------------------------------- | ------ | --------------------- |
| `formats/sensorml/aggregate-process.spec.ts` | 1      | Remove unused import  |
| `formats/sensorml/parser.spec.ts`            | 1      | Remove unused import  |
| `formats/sensorml/physical-system.spec.ts`   | 2      | Remove unused imports |
| `formats/sensorml/simple-process.spec.ts`    | 1      | Remove unused import  |
| `formats/sensorml/types.spec.ts`             | **32** | Remove unused imports |
| `formats/swecommon/data-record.spec.ts`      | **14** | Remove unused imports |
| `formats/swecommon/index.spec.ts`            | 1      | Remove unused import  |
| `formats/swecommon/parser.spec.ts`           | 1      | Remove unused import  |
| `formats/swecommon/types.spec.ts`            | **27** | Remove unused imports |
| `integration/observation.spec.ts`            | 3      | Remove unused imports |

- **Ordering:** Prettier first (Task 1), source ESLint second (Task 2a), test ESLint third (Task 2b). They do not conflict — upstream ESLint enforces no formatting rules.
- **Deliverable:** All 90 test-file ESLint errors resolved. Combined with 2a: all 99 errors fixed.

### Task 3: Verify and Commit (Commit 14)

**Estimated Time:** ~0.5 hours  
**Complexity:** Low

- Verify Prettier passes:
  ```bash
  npx prettier --check "src/ogc-api/csapi/**/*.ts" \
    "fixtures/ogc-api/csapi/**/*.json" "src/ogc-api/endpoint.ts"
  ```
- Verify ESLint passes:
  ```bash
  npx eslint src/ogc-api/csapi/
  ```
- Run full test suite to confirm zero regressions:
  ```bash
  npm run test:browser
  ```
- Stage and commit:
  ```bash
  git add -A
  git commit -m "style(csapi): apply prettier formatting and fix eslint errors"
  ```
- **Deliverable:** Commit 14 on `phase-6` branch — formatting only, zero logic changes
- **See:** [Implementation Guide §4.4](P6-implementation-guide.md#44-commit-message) for full commit message

**Phase A Deliverables:**

- 51 files Prettier-formatted
- 99 ESLint errors fixed across 15 files
- All tests still passing (zero regressions)
- Commit 14 recorded

---

## Phase B: Architecture Refactoring (Commit 15)

**Estimated Time:** 3–5 hours  
**Goal:** Decouple CSAPI from core — 3 files created, 4 files modified, 12 acceptance criteria satisfied.

### Task 4a: Audit and Build CSAPI Export Inventory

**Estimated Time:** ~0.5 hours  
**Complexity:** Medium  
**Split rationale:** Separates research (mapping symbols to sources) from code authoring (writing the barrel file). Errors in mapping cascade downstream. Split at the research/write risk boundary. See [Task Granularity Review](../../research/phase-6/task-granularity-review.md).

**Spec:** [Implementation Guide §6.1](P6-implementation-guide.md#61-barrel-file-csapiindexts)

- Trace every CSAPI symbol currently exported from `src/index.ts` lines 45–227 back to its source module in `csapi/`
- Build a complete inventory organized by the 6 barrel sections:
  1. Factory function from `./factory.js`
  2. Query builder from `./url_builder.js`
  3. Model values (enums/constants) from `./model.js`
  4. Model types from `./model.js`
  5. Format handler values from `./formats/index.js`
  6. Format handler types from `./formats/index.js`
- Classify each symbol as value (`export { ... }`) or type (`export type { ... }`)
- Verify every symbol has a traceable source — no guesses
- **Deliverable:** Complete symbol-to-source mapping ready for barrel file authoring. Zero code changes.

### Task 4b: Write Barrel File `csapi/index.ts`

**Estimated Time:** ~0.5–1 hours  
**Complexity:** Medium  
**File:** `src/ogc-api/csapi/index.ts` (new, ~190 lines)

- Create `src/ogc-api/csapi/index.ts` using the inventory from Task 4a
- Re-export all CSAPI public symbols across the 6 organized sections
- Use `export { ... }` for values, `export type { ... }` for types
- All paths use `.js` extensions
- Follow `formats/index.ts` (344 lines) sectioned JSDoc divider pattern
- **JSDoc:** Module-level documentation with `@example` showing import paths
- **Verification:** `npx tsc --noEmit` — barrel compiles without errors
- **Deliverable:** Barrel file compiles, all CSAPI public symbols accessible via single import path

### Task 5: Create Factory Function and Tests

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium  
**Files:** `src/ogc-api/csapi/factory.ts` (new, ~55 lines), `src/ogc-api/csapi/factory.spec.ts` (new, ~30 lines)  
**Spec:** [Implementation Guide §6.2–6.3](P6-implementation-guide.md#62-factory-function-csapifactoryts)

**factory.ts:**

- Implement `createCSAPIBuilder(endpoint, collectionId)` async factory function
- 4-step logic: guard (`hasConnectedSystems`) → fetch collection doc → scan root links → construct `CSAPIQueryBuilder`
- `import type OgcApiEndpoint` + `import type OgcApiCollectionInfo` — type-only imports, erased at compile, zero runtime coupling
- `import { EndpointError }` from `../../shared/errors.js` — for error throwing
- `import CSAPIQueryBuilder` + `import { scanCsapiLinks }` — CSAPI-internal imports
- No auto-caching (endpoint already caches `root` and collection documents internally)
- **JSDoc:** Complete function documentation with `@param`, `@returns`, `@throws`, `@example`

**factory.spec.ts:**

- 2 tests migrated and rewritten from `endpoint.spec.ts`:
  1. Creates a builder for a CSAPI-capable endpoint → calls `createCSAPIBuilder(endpoint, 'iot-sensors')`, verifies `availableResources` is populated
  2. Throws on non-CSAPI endpoint → expects `EndpointError`
- Uses same fixture URL as existing endpoint tests: `http://local/csapi/sample-data-hub`
- **Not migrated:** The `caches the CSAPI query builder` test — factory has no auto-caching, this behavior no longer exists
- **Testing research basis:** Factory test pattern follows EDR blueprint precedent ([Testing Plan 01](../../research/testing/findings/01-edr-test-blueprint.md), lines ~437–475). Quality bar per [Testing Plan 06](../../research/testing/findings/06-meaningful-vs-trivial-definition.md) and [Testing Plan 36](../../research/testing/findings/36-test-quality-checklist-review-process.md). See [Testing Strategy](#testing-strategy) section.

- **Verification:** `npx tsc --noEmit` + `npm run test:browser -- --testPathPattern factory`
- **Deliverable:** Factory function compiles, both tests pass

### Task 6: Modify `endpoint.ts`

**Estimated Time:** ~0.5–1 hours  
**Complexity:** Medium  
**File:** `src/ogc-api/endpoint.ts` (896 → ~833 lines, −63 net)  
**Spec:** [Implementation Guide §7.1](P6-implementation-guide.md#71-srcogc-apiendpointts)

**Removals:**

- Line 52: `import CSAPIQueryBuilder from './csapi/url_builder.js'`
- Line 53: `import { scanCsapiLinks } from './csapi/helpers.js'`
- Lines 70–71: `private collection_id_to_csapi_builder_: Map<...>`
- ~Lines 363–411: `csapi()` method + JSDoc (~49 lines)
- ~Lines 424–437: `extractRootResourceUrls()` + JSDoc (~14 lines)

**Changes:**

- `private get root()` → `public get root()` (1-word change)
- `private getCollectionDocument(` → `public getCollectionDocument(` (1-word change)
- Update `hasConnectedSystems` JSDoc: `@see` reference changed to point to new import path

**What stays (confirmed safe — zero CSAPI imports):**

- `hasConnectedSystems` getter — uses `info.ts` functions with conformance URI strings
- `csapiCollections` getter — filters collections by link relations

- **Verification:** `npx tsc --noEmit` + `git grep "from.*csapi" src/ogc-api/endpoint.ts` → 0 matches
- **Deliverable:** Endpoint has zero CSAPI imports, compiles cleanly

### Task 7: Modify `index.ts` and `endpoint.spec.ts`

**Estimated Time:** ~0.5 hours  
**Complexity:** Low  
**Files:** `src/index.ts` (252 → ~69 lines, −183), `src/ogc-api/endpoint.spec.ts` (2,888 → ~2,858 lines, −30)  
**Spec:** [Implementation Guide §7.2–7.3](P6-implementation-guide.md#72-srcindexts)

**`src/index.ts`:**

- Remove all CSAPI export lines (lines 45–227)
- Lines 1–44 (core exports) and lines 228+ (TMS, STAC, cache, worker) are unchanged
- **Verification:** `git grep "csapi\|CSAPI" src/index.ts` → 0 matches

**`src/ogc-api/endpoint.spec.ts`:**

- Remove 3 tests from the CSAPI block:
  - `can produce a CSAPI query builder` → migrated to `factory.spec.ts`
  - `caches the CSAPI query builder` → removed (no auto-caching)
  - `throws an error when calling csapi()` → migrated to `factory.spec.ts`
- 3 tests remain in endpoint.spec.ts:

  - `detects Connected Systems support` (tests `hasConnectedSystems`)
  - `can list all CSAPI collections` (tests `csapiCollections`)
  - `reports no Connected Systems support` (non-CSAPI endpoint)

- **Deliverable:** Root exports clean, test suite updated

### Task 8: Modify `package.json`

**Estimated Time:** ~0.25 hours  
**Complexity:** Low  
**File:** `package.json` (+8 lines)  
**Spec:** [Implementation Guide §7.4](P6-implementation-guide.md#74-packagejson)

**Change 1: Add `"./csapi"` sub-path to `"exports"`:**

```json
"./csapi": {
  "types": "./dist/ogc-api/csapi/index.d.ts",
  "import": "./dist/ogc-api/csapi/index.js",
  "browser": "./dist/ogc-api/csapi/index.js",
  "default": "./dist/ogc-api/csapi/index.js"
}
```

- Condition ordering: `"types"` first (ecosystem convention, required by TypeScript)
- Paths mirror esbuild per-file output: `src/ogc-api/csapi/index.ts` → `dist/ogc-api/csapi/index.js`

**Change 2: Add `"sideEffects": false`:**

- Add at top level of `package.json` (after `"type": "module"`)
- Enables bundler tree-shaking through barrel files
- Fallback if worker-fallback breaks: `"sideEffects": ["./dist/index.js", "./dist/worker-fallback/index.js"]`

- **Deliverable:** Package exports configured, tree-shaking enabled

### Task 9: Run CI Gates and Commit (Commit 15)

**Estimated Time:** ~0.5–1 hours  
**Complexity:** Low

Run all 5 CI verification commands:

```bash
npm run format:check    # C1
npm run typecheck        # C2
npm run lint             # C3
npm run test:browser     # C4
npm run test:node        # C5
```

If all pass, stage and commit:

```bash
git add -A
git commit -m "refactor(csapi): decouple from endpoint with separate entry point"
```

- **See:** [Implementation Guide §5.4](P6-implementation-guide.md#54-commit-message) for full commit message
- **Deliverable:** Commit 15 on `phase-6` branch — architecture refactoring complete

**Phase B Deliverables:**

- 3 new files: `csapi/index.ts`, `csapi/factory.ts`, `csapi/factory.spec.ts`
- 4 modified files: `endpoint.ts`, `index.ts`, `endpoint.spec.ts`, `package.json`
- Zero CSAPI imports outside `csapi/`
- Zero CSAPI exports in root `index.ts`
- All tests passing
- Commit 15 recorded

---

## Phase C: Verification and Delivery

**Estimated Time:** 1–2 hours  
**Goal:** Verify all 12 acceptance criteria, pass litmus test, rebase to contribution-ready branch.

### Task 10a: Boundary Verification and Litmus Test

**Estimated Time:** ~0.5–1 hours  
**Complexity:** Medium  
**Split rationale:** Verification is fully local and reversible; rebase/push modifies remote state visible to the upstream reviewer. Split at the verify/deliver risk boundary — only cross to 10b when 10a confirms everything is green. See [Task Granularity Review](../../research/phase-6/task-granularity-review.md).

**Step 1: Boundary Verification (V1–V4)**

| #   | Command                                                                    | Expected  |
| --- | -------------------------------------------------------------------------- | --------- |
| V1  | `git grep "from.*csapi" src/ogc-api/endpoint.ts`                           | 0 matches |
| V2  | `git grep "csapi\|CSAPI" src/index.ts`                                     | 0 matches |
| V3  | `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"`          | 0 matches |
| V4  | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` | 0 matches |

**Step 2: Litmus Test (A4)**

```bash
# Temporarily remove CSAPI to verify core independence
mv src/ogc-api/csapi src/ogc-api/_csapi_backup
# Core should compile without CSAPI (endpoint.ts has 0 csapi imports)
# Non-CSAPI tests should pass
mv src/ogc-api/_csapi_backup src/ogc-api/csapi
```

**Step 3: Diff Review**

```bash
# Architecture-only diff (Commit 15 — what jahow reviews)
git diff --stat HEAD~1..HEAD
# Total diff (both commits)
git diff --stat HEAD~2..HEAD
```

**Step 4: Push to phase-6**

```bash
git push origin phase-6
```

- **Gate:** All 12 verification gates must pass before proceeding to Task 10b
- **Deliverable:** All V1–V4 boundary checks pass, litmus test passes, diff reviewed, phase-6 branch pushed

### Task 10b: Rebase to clean-pr and Push to Upstream

**Estimated Time:** ~0.5 hours  
**Complexity:** Medium  
**Prerequisite:** Task 10a passes all verification gates

**Step 1: Rebase to clean-pr**

```bash
# Create safety tag
git checkout clean-pr
git tag pre-refactor-backup HEAD

# Cherry-pick implementation commits (NOT research docs)
git cherry-pick <commit-14-hash> <commit-15-hash>

# Verify
git log --oneline upstream/main..clean-pr  # Should show 15 commits

# Push to upstream fork
git push --force-with-lease clean-fork clean-pr
```

**Step 2: Update PR #136**

- Update PR description to document new consumer API
- Note the `"./csapi"` sub-path in the description
- Respond to jahow's review thread confirming requirements met

- **Deliverable:** `pre-refactor-backup` tag created, `clean-pr` updated with 15 commits, upstream fork pushed, PR #136 description updated

**Phase C Deliverables:**

- All 12 verification gates passed (V1–V4 + C1–C5 + A4 litmus + B1–B3 behavioral)
- `pre-refactor-backup` tag created on old `clean-pr` HEAD
- `clean-pr` branch updated with 15 commits (13 existing + 2 new)
- Upstream fork pushed
- PR #136 description updated

---

## Verification Gate Summary

All 12 gates from the [P6 Contribution Goal](P6-contribution-goal-and-definition.md#acceptance-criteria):

| #   | Category     | Gate                                  | Verification Command                                          |
| --- | ------------ | ------------------------------------- | ------------------------------------------------------------- |
| A1  | Architecture | Zero CSAPI in `index.ts`              | `git grep "csapi\|CSAPI" src/index.ts` → 0                    |
| A2  | Architecture | `"./csapi"` sub-path in exports       | Inspect `package.json`                                        |
| A3  | Architecture | Zero outward CSAPI imports            | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/"` → 0 |
| A4  | Architecture | Core compiles without CSAPI           | Litmus test (mv/compile/restore)                              |
| C1  | CI           | Prettier passes                       | `npm run format:check` → exit 0                               |
| C2  | CI           | TypeScript compiles                   | `npm run typecheck` → exit 0                                  |
| C3  | CI           | ESLint passes                         | `npm run lint` → exit 0                                       |
| C4  | CI           | Browser tests pass                    | `npm run test:browser` → all pass                             |
| C5  | CI           | Node tests pass                       | `npm run test:node` → all pass                                |
| B1  | Behavioral   | `hasConnectedSystems` works           | Existing test passes                                          |
| B2  | Behavioral   | `csapiCollections` works              | Existing test passes                                          |
| B3  | Behavioral   | All non-CSAPI functionality unchanged | Full test suite passes                                        |

---

## Testing Strategy

Phase 6 creates **exactly 2 new tests** in 1 new file, migrates 2 tests, and removes 1 obsolete test. The testing surface is minimal compared to Phases 1–5 (~6,000 lines of new test code). No new testing research is required — all Phase 6 testing decisions are covered by the existing [38-plan testing research arc](../../research/testing/findings/).

### Research Traceability

| Testing Decision                                          | Research Source                                                                                                                                                                                                      | What It Covers                                                                       |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Factory test pattern (create builder + verify properties) | [Plan 01: EDR Blueprint](../../research/testing/findings/01-edr-test-blueprint.md), lines ~437–475                                                                                                                   | Direct analog: `endpoint.edr('collection-id')` → assert builder, validate properties |
| Error case test (non-CSAPI throws `EndpointError`)        | [Plan 14: Integration Test Workflow](../../research/testing/findings/14-integration-test-workflow-design.md), Test 5                                                                                                 | "Throws Error for Non-CSAPI Collection" — exact pattern                              |
| Test file location (`factory.spec.ts` colocated)          | [Plan 19: Test Organization](../../research/testing/findings/19-test-organization-file-structure.md)                                                                                                                 | Colocated `.spec.ts` next to implementation, flat directory                          |
| Fixture reuse (same mock fetch as endpoint tests)         | [Plan 15: Fixture Sourcing](../../research/testing/findings/15-fixture-sourcing-organization.md)                                                                                                                     | Fixtures shared across test files via `setupMockFetch()`                             |
| Quality bar (meaningful assertions, not trivial)          | [Plan 06: Meaningful vs Trivial](../../research/testing/findings/06-meaningful-vs-trivial-definition.md) + [Plan 36: Quality Checklist](../../research/testing/findings/36-test-quality-checklist-review-process.md) | Complete validation, behavior assertions, specific error messages                    |
| Endpoint mocking pattern                                  | [Plan 34: Test Utility Helpers](../../research/testing/findings/34-test-utility-helper-design.md)                                                                                                                    | `setupMockFetch()`, `createTestEndpoint()` patterns                                  |
| Removing obsolete caching test                            | [Plan 37: Test Maintenance](../../research/testing/findings/37-test-maintenance-evolution-strategy.md)                                                                                                               | "Remove tests when the feature they test has been removed"                           |
| `hasConnectedSystems` stays tested on endpoint            | [Plan 22: Conformance Testing](../../research/testing/findings/22-conformance-capability-testing.md)                                                                                                                 | 8+ server profiles with fixture JSON for conformance detection                       |

### Testing Embedded at Task Level

Per [Testing Playbook §2](../../research/testing/findings/38-testing-playbook-synthesis.md) and the lesson learned from ROADMAP v1.0 (testing deferred too late), all Phase 6 testing is embedded within individual tasks:

| Task              | Testing Action                                                  | When                       |
| ----------------- | --------------------------------------------------------------- | -------------------------- |
| Task 3 (Phase A)  | Run full test suite after formatting — confirm zero regressions | End of Commit 14           |
| Task 5 (Phase B)  | Create `factory.spec.ts` with 2 tests — run immediately         | With factory creation      |
| Task 6 (Phase B)  | Run `npx tsc --noEmit` after endpoint changes                   | With endpoint modification |
| Task 7 (Phase B)  | Remove 3 tests from `endpoint.spec.ts`                          | With test migration        |
| Task 9 (Phase B)  | Run full CI suite (C4 + C5) — all 1,282+ tests pass             | End of Commit 15           |
| Task 10 (Phase C) | Litmus test, boundary verification, regression confirmation     | Final verification         |

No testing is deferred to a later phase or batched at the end.

---

## Deliverables Summary

| Category                       | Files                                                             | Lines Changed                        |
| ------------------------------ | ----------------------------------------------------------------- | ------------------------------------ |
| Commit 14: Prettier formatting | 51 files                                                          | ~3,023 insertions (automated)        |
| Commit 14: ESLint fixes        | 15 files                                                          | ~99 import removals (manual)         |
| Commit 15: New files           | 3 (`index.ts`, `factory.ts`, `factory.spec.ts`)                   | ~275 lines added                     |
| Commit 15: Modified files      | 4 (`endpoint.ts`, `index.ts`, `endpoint.spec.ts`, `package.json`) | ~278 lines removed, ~10 added        |
| **Net architecture change**    | **7 files**                                                       | **~+5 lines (excluding formatting)** |

**Quality Targets:**

- All 12 verification gates passing
- Zero CSAPI imports outside `csapi/` directory
- Zero CSAPI exports in root `index.ts`
- Factory function has 2 tests (builder creation + error case)
- 3 endpoint CSAPI tests preserved, 2 migrated, 1 removed
- All new files Prettier-compliant from inception
- JSDoc on barrel file module, factory function, and updated endpoint methods

---

## Scope Exclusions

The following are explicitly NOT in Phase 6 scope (all decisions documented in the [Design Decision Resolution Report](../../research/phase-6/design-decision-resolution-report.md)):

| Item                                              | Why Excluded                                                    |
| ------------------------------------------------- | --------------------------------------------------------------- |
| ESLint `import/no-restricted-paths` boundary rule | Enforcement tooling — jahow didn't ask for it                   |
| Custom boundary integration test                  | `git grep` verification suffices                                |
| TypeScript Project References                     | Heavyweight for one sub-module; 0/6 surveyed libraries use this |
| `typesVersions` fallback                          | 5/6 libraries skip it; only needed for TypeScript <4.7          |
| Move CSAPI MIME functions from `shared/`          | Constraint 3 does not apply to `shared/` utilities              |
| Generalized link scanner utility                  | Problem self-resolves with factory pattern                      |
| Any CSAPI business logic changes                  | Zero changes — types, builders, parsers all preserved           |
| Performance testing                               | No upstream precedent                                           |
| Worker extensions                                 | No upstream JSON API uses workers                               |

---

## Risk Register

| #   | Risk                                                  | Likelihood | Impact | Mitigation                                                                       | Rollback                                           |
| --- | ----------------------------------------------------- | ---------- | ------ | -------------------------------------------------------------------------------- | -------------------------------------------------- |
| 1   | Line numbers shift after Prettier                     | Certain    | Low    | Format FIRST (Commit 14), base architecture on formatted code                    | N/A — ordering prevents this                       |
| 2   | TypeScript fails after removing CSAPI from `index.ts` | Low        | High   | Create barrel file in SAME commit as removal                                     | `git reset --hard HEAD~1`                          |
| 3   | Factory tests use incorrect fixtures                  | Low        | Low    | Use same fixture URLs as existing endpoint tests                                 | Fix fixture paths                                  |
| 4   | Force-push overwrites remote clean-pr                 | Low        | High   | `pre-refactor-backup` tag + `--force-with-lease`                                 | `git push clean-fork pre-refactor-backup:clean-pr` |
| 5   | Prettier reformats new files                          | Low        | Low    | Write new files Prettier-compliant from start                                    | `npx prettier --write <file>`                      |
| 6   | `"sideEffects": false` breaks worker-fallback         | Low        | Medium | Tests catch immediately; switch to array form                                    | `"sideEffects": ["./dist/index.js"]`               |
| 7   | ESLint fixes accidentally change behavior             | Near-zero  | High   | All fixes are `no-unused-vars` — removing unused imports has zero runtime effect | Review each removal                                |
| 8   | Cherry-pick conflicts during rebase                   | Low        | Medium | Commits 14–15 touch files not modified in commits 1–13                           | `git cherry-pick --abort`, resolve manually        |

---

## Research Foundation

Phase 6 is backed by an 8-plan research arc. Every design choice is traced to systematic research.

| Plan | Title                                    | Questions | Key Output                                          |
| ---- | ---------------------------------------- | --------- | --------------------------------------------------- |
| 01   | Build System & Entry Point Analysis      | 31        | No build config changes needed                      |
| 02   | EDR Integration Pattern Analysis         | 35        | EDR is accepted precedent for endpoint getters      |
| 03   | Separate Entry Point Design Patterns     | 35        | 4-condition exports + barrel + `sideEffects: false` |
| 04   | Sub-Module API Design Patterns           | 38        | Async factory function pattern                      |
| 05   | Module Decoupling Patterns               | 37        | Level 3.5 coupling (`import type` + `Pick<>`)       |
| 06   | Endpoint Decoupling Architecture         | 42        | Factory signature, barrel contents, test migration  |
| 07   | Prettier & ESLint Configuration Analysis | 27        | Format First strategy, 51 files, 99 errors          |
| 08   | File-Level Changelist & Commit Strategy  | 40        | 2 commits, 7 files, 12 gates                        |

**Total: 285 questions answered, ~8,000 lines of findings.**

All findings: [`docs/research/phase-6/findings/`](../../research/phase-6/findings/)

**Related documents:**

- [P6 Implementation Guide](P6-implementation-guide.md) — Complete per-file specifications and code sketches
- [P6 Contribution Goal and Definition](P6-contribution-goal-and-definition.md) — Acceptance criteria and scope boundaries
- [Design Decision Resolution Report](../../research/phase-6/design-decision-resolution-report.md) — All 10 design forks resolved
- [Deferred Issues Scope Assessment](../../research/phase-6/deferred-issues-scope-assessment.md) — 5 deferred issues, all remain deferred
- [Implementation Readiness Recommendation](../../research/phase-6/implementation-readiness-recommendation.md) — Rationale for proceeding

---

## Version History

**Version 1.1 (February 24, 2026):**

- Split Task 2 into 2a (5 source files, 9 errors) + 2b (10 test files, 90 errors) — source/test risk boundary
- Split Task 4 into 4a (audit export inventory) + 4b (write barrel file) — research/write risk boundary
- Split Task 10 into 10a (verification + litmus) + 10b (rebase + push) — verify/deliver risk boundary
- Updated execution unit summary table (10 tasks → 13 execution units)
- Added explicit execution order and split rationale links
- See [Task Granularity Review](../../research/phase-6/task-granularity-review.md) for full analysis

**Version 1.0 (February 24, 2026):**

- Initial Phase 6 roadmap covering module boundary refactoring
- 3 phases, 10 tasks, 12 execution units
- Derived from [P6 Contribution Goal](P6-contribution-goal-and-definition.md), [P6 Implementation Guide](P6-implementation-guide.md), and 8 research plans (285 questions)
- All design decisions resolved — zero open questions
