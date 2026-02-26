# Code Review Prompt Template — Phase 6

**Purpose:** Reusable prompt for triggering AI-generated code reviews during Phase 6 (Upstream Acceptance Refactoring). Adapts the Phase 5 review template to the specific quality concerns of module boundary decoupling, barrel file completeness, factory function correctness, and formatting compliance.

**Version:** 1.0  
**Date:** February 24, 2026  
**Supersedes:** Nothing — sibling to `code-review-prompt-template-phase-5.md` (Phase 5), `code-review-prompt-template-phase-3.md` (Phase 3), and `code-review-prompt-template.md` (Phase 2), which remain valid for any revisits to those phases.  
**Report destination:** `docs/implementation/phase-{X.Y}-code-review.md`

---

## Why a Separate Template?

Phase 6 code differs fundamentally from Phase 5 code:

| Dimension          | Phase 5 (Parser Completion)                                               | Phase 6 (Upstream Acceptance Refactoring)                                          |
| ------------------ | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Primary output     | Typed objects from raw JSON (6 parsers)                                   | Structural changes — barrel file, factory function, export reorganization          |
| Correctness check  | "Does the parser produce the right typed output?"                         | "Is the module boundary clean? Do all 12 verification gates pass?"                 |
| Test strategy      | Fixture-based input → typed output assertions                             | 2 factory tests + `git grep` boundary checks + full CI suite regression            |
| Pattern reference  | `parseDatastream()` gold standard                                         | `formats/index.ts` barrel, EDR factory blueprint, existing `package.json` exports  |
| Validation concern | Tolerant extraction, time fields, cross-references                        | Export completeness, import direction, tree-shaking, visibility changes            |
| Heatmap dimensions | Parser-specific (time handling, cross-ref exclusion, opaque pass-through) | Architecture-specific (boundary isolation, export coverage, formatting compliance) |
| Spec references    | OGC 23-002 Part 2                                                         | jahow's PR #136 review requirements                                                |
| Risk profile       | Runtime behavior correctness                                              | Build/bundle correctness, import resolution                                        |

The Phase 5 test checklists (resource parsers, schema parsers, recursive fix, integration wiring) do not apply. Phase 6 needs architecture-specific review dimensions.

---

## When to Use

Trigger this prompt after any of these Phase 6 milestones:

1. **Phase A is completed** (Commit 14 — Prettier + ESLint formatting)
2. **A Phase B task is completed** (e.g., barrel file created, factory function created, endpoint decoupled)
3. **Multiple Phase B tasks are completed** in a single session (batch review)
4. **Commit 15 is ready** (all Phase B tasks done — full architecture review)
5. **Phase C verification passes** (final gate review before push to upstream)
6. **Before pushing to `clean-pr`** (gate review for the complete Phase 6 contribution)

Do NOT trigger after trivial doc-only commits or non-code changes.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a code review of the work completed since the last review.

### Scope

**Phase:** {{Phase number, e.g., "6.1" or "6.2"}}
**Tasks completed:** {{List task numbers and titles, e.g., "Task 1: Apply Prettier, Task 2a: Fix ESLint source files, Task 2b: Fix ESLint test files, Task 3: Verify and commit"}}
**Commits to review:** {{List commit SHAs or say "all commits since {last review commit SHA}"}}
**Last review:** {{Reference the previous review doc, e.g., "docs/implementation/phase-5.4-code-review.md" or "none — first Phase 6 review"}}

### Review Instructions

1. **Review Lessons Learned** — read both documents before evaluating code:
   - `docs/governance/phase-3-lessons-learned.md` — Key checks still active in Phase 6:
     - Lesson 1: Does any new code introduce an architectural layer without upstream precedent?
     - Lesson 4: Are there parallel systems doing the same thing?
     - Lesson 10: Do type names collide with JS/TS built-ins?
   - `docs/governance/phase-2-lessons-learned.md` — General guardrails (Lessons 6-10 still active)

2. **Run verification gates** — execute and record results:

   **CI gates (always run):**
   - `npm run format:check` (C1)
   - `npm run typecheck` (C2)
   - `npm run lint` (C3)
   - `npm run test:browser` (C4 — record pass count, must include ALL prior tests + any new tests)
   - `npm run test:node` (C5)

   **Boundary gates (run for any Phase B or C review):**
   - `git grep "from.*csapi" src/ogc-api/endpoint.ts` → expect 0 matches (V1)
   - `git grep "csapi\|CSAPI" src/index.ts` → expect 0 matches (V2)
   - `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"` → expect 0 matches (V3)
   - `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` → expect 0 matches (V4)

3. **Read all changed files** — identify every file modified since the last review commit. For each file, note:
   - What changed (lines added/modified/removed)
   - Whether the change follows the established pattern for its component type (see Pattern References below)

4. **Reaffirm ALL prior findings** — read the previous review doc and check each open finding:
   - For each RESOLVED finding: confirm it's still resolved, cite evidence
   - For each STILL OPEN finding: check if it was addressed, update status
   - For each UNCHANGED finding (not-our-code): reaffirm unchanged status

5. **Evaluate new code against these quality dimensions:**

   - **Boundary isolation:** Does the change maintain clean module boundaries?
     - Zero CSAPI imports outside `src/ogc-api/csapi/`
     - Zero CSAPI exports in root `src/index.ts`
     - `import type` used for all type-only cross-module references
     - No runtime coupling from core to CSAPI

   - **Export completeness** (for barrel file reviews):

     **Category A — Barrel file (`csapi/index.ts`):**
     - [ ] Every CSAPI symbol previously in `src/index.ts` lines 45–227 is re-exported
     - [ ] Value exports use `export { ... }` — type exports use `export type { ... }`
     - [ ] All import paths use `.js` extensions
     - [ ] Sections follow `formats/index.ts` JSDoc divider pattern
     - [ ] Module-level JSDoc with `@example` showing import paths
     - [ ] `npx tsc --noEmit` passes — all re-exports resolve

   - **Factory correctness** (for factory function reviews):

     **Category B — Factory function (`csapi/factory.ts`):**
     - [ ] 4-step logic preserved: guard (`hasConnectedSystems`) → fetch collection → scan root links → construct builder
     - [ ] `import type OgcApiEndpoint` — type-only import, erased at compile
     - [ ] `import { EndpointError }` from `../../shared/errors.js` — runtime import for error throwing
     - [ ] No auto-caching — endpoint already caches internally
     - [ ] Complete JSDoc with `@param`, `@returns`, `@throws`, `@example`
     - [ ] Tests cover: successful builder creation + error on non-CSAPI endpoint

   - **Endpoint decoupling** (for `endpoint.ts` reviews):

     **Category C — Endpoint modification:**
     - [ ] All CSAPI imports removed (2 import statements)
     - [ ] `csapi()` method removed (~49 lines)
     - [ ] `extractRootResourceUrls()` removed (~14 lines)
     - [ ] CSAPI cache field removed
     - [ ] `root` visibility: `private` → `public` (1-word change, implementation unchanged)
     - [ ] `getCollectionDocument` visibility: `private` → `public` (1-word change, implementation unchanged)
     - [ ] `hasConnectedSystems` and `csapiCollections` unchanged (these stay on endpoint)
     - [ ] `git grep "from.*csapi" src/ogc-api/endpoint.ts` → 0 matches

   - **Root exports** (for `index.ts` reviews):

     **Category D — Root index modification:**
     - [ ] All CSAPI export lines removed (lines 45–227, ~183 lines)
     - [ ] Core exports (WFS, WMS, WMTS, TMS, STAC, etc.) completely intact
     - [ ] `git grep "csapi\|CSAPI" src/index.ts` → 0 matches

   - **Package configuration** (for `package.json` reviews):

     **Category E — Package.json modification:**
     - [ ] `"./csapi"` sub-path added with `types`, `import`, `browser`, `default` conditions
     - [ ] `"types"` condition listed first (TypeScript ecosystem convention)
     - [ ] Paths point to `dist/ogc-api/csapi/index.js` (correct compiled output path)
     - [ ] `"sideEffects": false` added at top level
     - [ ] Existing exports (`.`, `./worker`) unchanged

   - **Formatting compliance** (for Phase A reviews):

     **Category F — Prettier + ESLint:**
     - [ ] `npx prettier --check` passes for all CSAPI files
     - [ ] `npx eslint src/ogc-api/csapi/` passes with 0 errors
     - [ ] Zero logic changes — only whitespace and unused import removal
     - [ ] ESLint fixes use `import type` conversions (not underscore prefixing) for source files
     - [ ] ESLint fixes are pure import removal for test files

   - **Test migration** (for `endpoint.spec.ts` reviews):

     **Category G — Test file changes:**
     - [ ] 3 CSAPI tests removed from `endpoint.spec.ts` (`csapi()` method, caching, error)
     - [ ] 2 tests migrated to `factory.spec.ts` (builder creation + error case)
     - [ ] 1 test removed (caching — no longer applicable)
     - [ ] 3 tests preserved in `endpoint.spec.ts` (`hasConnectedSystems`, `csapiCollections`, no-support)
     - [ ] Same fixture URLs and mock fetch setup as existing tests

   - **JSDoc quality:** Params, returns, throws, examples where applicable
   - **Consistency:** Does new code follow patterns already established in the repo?

6. **Classify every finding** using these severity labels:
   - **BUG** — incorrect behavior, wrong output, runtime error, boundary violation
   - **DESIGN** — architectural concern, DRY violation, type safety issue
   - **GAP** — missing export, missing test, incomplete migration
   - **POSITIVE** — something done well that should be maintained
   - **INFORMATIONAL** — worth noting but no action needed
   - **CONSISTENCY** — follows or deviates from established patterns

7. **Generate the architecture verification matrix** — update the table showing boundary compliance:

   | Gate | Command | Expected | Actual | Status |
   |------|---------|----------|--------|--------|
   | V1 | `git grep "from.*csapi" src/ogc-api/endpoint.ts` | 0 matches | {{N}} | ✅/❌ |
   | V2 | `git grep "csapi\|CSAPI" src/index.ts` | 0 matches | {{N}} | ✅/❌ |
   | V3 | `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"` | 0 matches | {{N}} | ✅/❌ |
   | V4 | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` | 0 matches | {{N}} | ✅/❌ |
   | C1 | `npm run format:check` | exit 0 | {{result}} | ✅/❌ |
   | C2 | `npm run typecheck` | exit 0 | {{result}} | ✅/❌ |
   | C3 | `npm run lint` | exit 0 | {{result}} | ✅/❌ |
   | C4 | `npm run test:browser` | all pass | {{N}} pass | ✅/❌ |
   | C5 | `npm run test:node` | all pass | {{N}} pass | ✅/❌ |

8. **Generate the task completion heatmap** — update the table showing Phase 6 progress:

   | Dimension | Task 1 | Task 2a | Task 2b | Task 3 | Task 4a | Task 4b | Task 5 | Task 6 | Task 7 | Task 8 | Task 9 | Task 10a | Task 10b |
   |-----------|--------|---------|---------|--------|---------|---------|--------|--------|--------|--------|--------|----------|----------|
   | Deliverable complete | ✅/❌/— | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
   | Formatting compliant | ✅/❌/— | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
   | Boundary clean | —/✅/❌ | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
   | Tests pass | ✅/❌/— | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
   | Committed | ✅/❌ | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

9. **Include a root cause analysis** if there are new defects — explain HOW and WHY each issue was introduced

10. **Write prioritized recommendations** in three tiers:
    - **Fix Now** (before next coding task)
    - **Fix Before Push** (before pushing to `clean-pr` / upstream)
    - **Defer** (low priority, no current impact)

### Report Format

Generate the report as a markdown file and save it to:
`docs/implementation/phase-{{X.Y}}-code-review.md`

Use this exact structure (matching prior reviews):

```markdown
# Phase {{X.Y}} Code Review — {{Subtitle describing scope}}

**Date:** {{YYYY-MM-DD}}
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** {{One-line description of what's being reviewed}}
**Commits:**
- `{sha}` — `{commit message}`

## Verification Status

### CI Gates

| Check | Result |
|-------|--------|
| format:check (C1) | ✅/❌ {{result}} |
| typecheck (C2) | ✅/❌ {{result}} |
| lint (C3) | ✅/❌ {{result}} |
| test:browser (C4) | ✅ {{N}} passing, {{N}} suites |
| test:node (C5) | ✅ {{N}} passing |

### Boundary Gates

| Gate | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| V1 | `git grep "from.*csapi" src/ogc-api/endpoint.ts` | 0 | {{N}} | ✅/❌ |
| V2 | `git grep "csapi\|CSAPI" src/index.ts` | 0 | {{N}} | ✅/❌ |
| V3 | Cross-module CSAPI imports | 0 | {{N}} | ✅/❌ |
| V4 | Non-index CSAPI imports | 0 | {{N}} | ✅/❌ |

## Files Reviewed

### {{Task title}}

| File | Lines Changed | Scope |
|------|--------------|-------|
| ... | ... | ... |

## Overall Codebase Metrics (Cumulative)

| Category | Files | Lines | Tests |
|----------|-------|-------|-------|
| Phase 1–4 (URL Builder, Integration) | {{N}} | {{N}} | {{N}} |
| Phase 5 (Parsers) | {{N}} | {{N}} | {{N}} |
| Phase 6 (Boundary Refactoring) | {{N}} | {{N}} | {{N}} |
| **Total CSAPI** | **{{N}}** | **{{N}}** | **{{N}}** |

## Prior Findings Status

### [{{ID}}] {{STATUS}}: {{Title}}
{{For each finding from the previous review — resolved, still open, or unchanged}}

## Phase {{X.Y}} Findings — New

### [F{{N}}] {{SEVERITY}}: {{Title}}
{{Detailed finding with file references, code snippets, severity, and recommendation}}

## Architecture Verification Matrix

| Gate | Expected | Actual | Status |
|------|----------|--------|--------|
| V1–V4, C1–C5 | ... | ... | ✅/❌ |

## Task Completion Heatmap

| Dimension | Task 1 | Task 2a | ... | Task 10b |
|-----------|--------|---------|-----|----------|
| ... | ... | ... | ... | ... |

## Export Completeness Audit (if barrel file reviewed)

| Section | Symbols Expected | Symbols Found | Match? |
|---------|-----------------|---------------|--------|
| Factory | 1 | {{N}} | ✅/❌ |
| Query Builder | {{N}} | {{N}} | ✅/❌ |
| Model Values | {{N}} | {{N}} | ✅/❌ |
| Model Types | {{N}} | {{N}} | ✅/❌ |
| Format Values | {{N}} | {{N}} | ✅/❌ |
| Format Types | {{N}} | {{N}} | ✅/❌ |

## Summary

| Category | Count | Details |
|----------|-------|---------|
| ... | ... | ... |

## Recommendations

### Fix Now (before next task)
### Fix Before Push (before upstream)
### Defer (Low Priority)

## Root Cause Analysis
{{Only if new defects found — explain how/why they were introduced}}

## Overall Assessment
{{2-3 paragraph assessment of code quality, boundary isolation, and readiness for upstream review}}
````

Then commit the report, push, and confirm the file is at the expected path.

```

---

## Post-Review Workflow

After the review report is generated:

1. **Review the recommendations** — decide which to fix now vs defer
2. **Create a GitHub issue** for any "Fix Now" items using `docs/governance/issue-creation-prompt-template-phase-6.md`
3. **Complete the fix** before proceeding to the next Phase 6 task
4. **The next code review will reaffirm** all findings from this review — nothing is forgotten

---

## Quality Gates (Non-Negotiable)

Every Phase 6 code review report MUST include:

- [ ] All CI verification commands executed and results recorded (C1–C5)
- [ ] Boundary verification commands executed and results recorded (V1–V4) — for Phase B/C reviews
- [ ] Every prior finding reaffirmed with current status
- [ ] New findings classified with severity labels
- [ ] Architecture verification matrix (all 9 gates)
- [ ] Task completion heatmap
- [ ] Export completeness audit (if barrel file is in scope)
- [ ] Cumulative codebase metrics table
- [ ] Prioritized recommendations in three tiers
- [ ] Overall assessment paragraph

---

## Naming Convention

Reports follow the same naming pattern as prior phases:

```

docs/implementation/phase-{major}.{minor}-code-review.md

```

Where:
- **Major** = project phase (6 for Phase 6)
- **Minor** = sequential review number within Phase 6 (1, 2, 3...)

Examples:
- `phase-6.1-code-review.md` (Phase 6, first review — Phase A: Prettier + ESLint + Commit 14)
- `phase-6.2-code-review.md` (Phase 6, second review — Phase B partial: barrel + factory)
- `phase-6.3-code-review.md` (Phase 6, third review — Phase B complete: all architecture + Commit 15)
- `phase-6.4-code-review.md` (Phase 6, fourth review — Phase C: verification + delivery)

---

## Reference Documents

When performing a Phase 6 code review, the reviewer should have access to:

| Document | Location | Purpose |
|----------|----------|---------|
| P6 ROADMAP | `docs/planning/phase-6/P6-ROADMAP.md` | Task definitions, dependencies, execution order (13 units) |
| P6 Implementation Guide | `docs/planning/phase-6/P6-implementation-guide.md` | Complete file specifications, code sketches, line references (991 lines) |
| P6 Contribution Goal | `docs/planning/phase-6/P6-contribution-goal-and-definition.md` | 12 acceptance criteria, scope boundaries, consumer API migration |
| Task Granularity Review | `docs/research/phase-6/task-granularity-review.md` | Split rationale for 2a/2b, 4a/4b, 10a/10b |
| Design Decision Resolution Report | `docs/research/phase-6/design-decision-resolution-report.md` | All 10 design forks resolved |
| Testing Research Assessment | `docs/research/phase-6/testing-research-assessment.md` | Testing strategy validation |
| Phase 3 Lessons Learned | `docs/governance/phase-3-lessons-learned.md` | Guardrails still active: upstream audit, Postel's Law, type naming |
| Phase 2 Lessons Learned | `docs/governance/phase-2-lessons-learned.md` | General guardrails — Lessons 6-10 still active |
| Previous Review | `docs/implementation/phase-{prev}-code-review.md` | Prior findings to reaffirm |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |

### Phase 6 Research Foundation (for context on design decisions)

| Plan | Title | Key Decision |
|------|-------|-------------|
| 01 | Build System & Entry Point Analysis | No build config changes needed |
| 02 | EDR Integration Pattern Analysis | EDR is accepted precedent for endpoint getters |
| 03 | Separate Entry Point Design Patterns | 4-condition exports + barrel + `sideEffects: false` |
| 04 | Sub-Module API Design Patterns | Async factory function pattern |
| 05 | Module Decoupling Patterns | Level 3.5 coupling (`import type` + `Pick<>`) |
| 06 | Endpoint Decoupling Architecture | Factory signature, barrel contents, test migration |
| 07 | Prettier & ESLint Configuration Analysis | Format First strategy, 51 files, 99 errors |
| 08 | File-Level Changelist & Commit Strategy | 2 commits, 7 files, 12 gates |

All findings: [`docs/research/phase-6/findings/`](../research/phase-6/findings/)

---

## Key Differences from Phase 5 Template

For reviewers familiar with the Phase 5 template, these are the substantive changes:

| Section | Phase 5 | Phase 6 |
|---------|---------|---------|
| Test checklist categories | A (Resource parsers), B (Schema parsers), C (Recursive fix), D (Integration) | A (Barrel file), B (Factory), C (Endpoint decoupling), D (Root exports), E (Package.json), F (Formatting), G (Test migration) |
| Pattern reference gold standard | `parseDatastream()` for parsers, `parseProperty()` for non-Part-2 | `formats/index.ts` for barrel, EDR `endpoint.edr()` for factory, existing `package.json` for exports |
| Verification gates | 4 CI commands + pre-existing error notes | 5 CI gates (C1–C5) + 4 boundary gates (V1–V4) = 9 total |
| Heatmap | Parser dimensions (time handling, cross-ref, opaque pass-through) | Task completion tracking (deliverable, formatting, boundary, tests, committed) |
| Smoke test findings | F27, F30, F31, F33, F38 | N/A — Phase 6 has no parser work |
| Spec references | OGC 23-002 Part 2 | jahow's PR #136 review requirements |
| Recommendation tiers | "Fix Before Phase 6" | "Fix Before Push" (to upstream) |
| Export audit | Not applicable | Export completeness table (6 barrel sections) |
| Boundary matrix | Not applicable | 4 `git grep` boundary verification gates |
```
