# Research Plan 08: File-Level Changelist and Commit Strategy

> **Plan 8 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                     |
| ---------------------- | --------------------------------------------------------- |
| **Status**             | Not Started                                               |
| **Plan Type**          | Implementation synthesis                                  |
| **Date Created**       | 2026-02-23                                                |
| **Last Updated**       | 2026-02-23                                                |
| **Estimated Time**     | 2–3 hours                                                 |
| **Actual Time**        | —                                                         |
| **Depends On**         | Plans 01, 02, 03, 04, 05, 06, 07 (all prior plans)        |
| **Blocks**             | None — this is the final plan; it unblocks implementation |
| **Strategy Reference** | [research-strategy.md § Plan 08](../research-strategy.md) |

---

## 1. Research Objective

Produce the exact, numbered file-level changelist and commit sequence needed to refactor CSAPI for upstream acceptance. The deliverable is a complete implementation blueprint that specifies: (a) every file to create, modify, move, or delete — with before/after paths and a summary of changes, (b) the ordered commit sequence with draft commit messages, (c) the rebase strategy from `phase-6` → `clean-pr` → upstream submission, (d) how each commit interacts with the 13-commit structure of existing PR #136, (e) Prettier/ESLint execution timing within the commit sequence, and (f) the final CI verification checklist.

This is the terminal research plan — the bridge between research and implementation. After this plan's findings are produced, no further research is needed. The findings document IS the implementation spec. A developer (human or AI) should be able to execute the changelist mechanically, producing a PR that passes all CI checks and satisfies all four of jahow's boundary conditions.

Every decision made in Plans 01–07 converges here. Plan 01 provides the `package.json` `"exports"` configuration. Plan 02 provides the EDR precedent for what patterns are acceptable. Plan 03 provides the barrel file and sub-path export mechanics. Plan 04 provides the consumer API shape. Plan 05 provides the coupling level. Plan 06 provides the complete architecture. Plan 07 provides the formatting/linting impact and execution order. Plan 08 translates all of these into an ordered list of file changes and commits.

---

## 2. Sequencing Rationale

### Why Plan 8?

This must be last because it synthesizes every prior plan's output into the implementation spec. It cannot be written until all architectural decisions (Plan 06), formatting strategies (Plan 07), and technical details (Plans 01–05) are finalized. Any unresolved decision from a prior plan would create an ambiguity in the changelist — and the changelist must have zero ambiguities. Every line in the spec must be actionable without further research.

This plan is also uniquely positioned: it must account for the _existing_ 13-commit structure on the `clean-pr` branch (PR #136). The refactoring changes don't start from scratch — they modify, amend, or extend an existing commit history. The commit strategy must decide whether to squash the refactoring into those existing commits, add new commits on top, or restructure the entire history. This decision has implications for PR review, `git blame`, and jahow's ability to see what changed.

### Dependency Chain

- **Builds on:**
  - **Plan 01** (Build System): Provides `package.json` `"exports"` configuration for `"./csapi"`, build script modifications (if any), `vite-plugin-dts` configuration, esbuild per-file output verification. Plan 08 needs the exact `package.json` diff.
  - **Plan 02** (EDR Pattern): Provides the boundary where EDR's approach diverges from CSAPI's. Plan 08 needs to know whether any EDR-related code changes are required (e.g., should EDR also get its own entry point? Or is the current integration acceptable?).
  - **Plan 03** (Entry Point Design): Provides barrel file structure, `package.json` `"exports"` field format, TypeScript declaration mapping. Plan 08 needs the exact barrel file path and re-export pattern.
  - **Plan 04** (Industry API Patterns): Provides the recommended consumer API shape. Plan 08 needs to know whether a new factory file is required, or whether the `CSAPIQueryBuilder` constructor is the public API.
  - **Plan 05** (Decoupling Patterns): Provides the coupling level and type-sharing strategy. Plan 08 needs to know whether adapter types or interface files must be created.
  - **Plan 06** (Decoupling Architecture): The primary input. Provides the complete architecture: consumer API signatures, `hasConnectedSystems` placement, `csapiCollections` placement, `scanCsapiLinks` resolution, barrel file design, test migration plan, and before/after code for every integration point. Plan 08 translates Plan 06's architecture into an ordered changelist.
  - **Plan 07** (Prettier/ESLint): Provides formatting impact scope (file count, line count), ESLint error inventory, and execution order recommendation. Plan 08 incorporates formatting into the commit sequence.
- **Feeds into:**
  - **Implementation** — this plan's deliverable IS the implementation spec. No further research follows.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **No CSAPI in root exports (Constraint 1):** The changelist must include the removal of all ~152 CSAPI symbols (184 lines) from `src/index.ts` (lines 46–211). After the changelist is applied, `git grep "csapi\|CSAPI\|connected.systems\|ConnectedSystems" src/index.ts` must return zero matches (excluding comments).
2. **Separate entry point (Constraint 2):** The changelist must include creation of `src/ogc-api/csapi/index.ts` (barrel file) and the addition of `"./csapi"` to `package.json` `"exports"`. After the changelist is applied, `import { CSAPIQueryBuilder } from '@camptocamp/ogc-client/csapi'` must resolve correctly.
3. **No outward imports (Constraint 3):** The changelist must include the removal of the two CSAPI imports in `endpoint.ts` (lines 52–53: `import CSAPIQueryBuilder from './csapi/url_builder.js'` and `import { scanCsapiLinks } from './csapi/helpers.js'`). After the changelist is applied, `git grep "from.*csapi" src/ogc-api/endpoint.ts` must return zero matches.
4. **One-way dependency (Constraint 4):** After the changelist is applied, removing the entire `src/ogc-api/csapi/` directory must leave core fully functional — `npm run typecheck`, `npm run test:browser`, and `npm run test:node` must all pass (with CSAPI tests naturally failing/absent).
5. **CI compliance (Constraint 5):** Every commit in the final sequence must individually pass all 5 CI checks: `npm run format:check`, `npm run typecheck`, `npm run lint`, `npm run test:browser`, `npm run test:node`. If this is impractical for intermediate commits, the plan must document which commits are allowed to be squashed.
6. **PR #136 compatibility:** The changelist must be applicable to the `clean-pr` branch, which has 13 commits above `upstream/main` (`53a6449`). The strategy must define how refactoring changes integrate with those 13 commits — amend, rebase, or extend.

### Implementation Scope Gate

> **Research broadly, implement minimally.**
>
> This plan translates research findings into the concrete changelist. Every file operation in the changelist must pass the **minimum-change test:**
>
> **"Does this file change directly serve jahow's two requirements (CSAPI out of root index.ts, non-CSAPI code stops importing CSAPI), or are we adding work he didn't request?"**
>
> The changelist must contain ONLY:
>
> - Changes required to satisfy jahow's two bullet points
> - Changes that are direct consequences of those requirements (e.g., moving a method because its imports violate the constraints)
> - Changes required to pass CI (formatting, linting)
>
> The changelist must NOT contain:
>
> - "While we're at it" improvements (refactoring code that isn't affected by the boundary conditions)
> - New abstractions or patterns inspired by research but not required by the constraints
> - Changes to modules outside our scope (EDR, other upstream code)
> - Documentation files beyond what's needed for the PR
>
> See: [Scope Alignment Review Notes](scope-alignment-review-notes.md)

### Excluded From Scope

- **Architectural decision-making:** All architectural decisions are made in Plans 01–06. Plan 08 does not revisit them — it translates them into file operations. If a decision is ambiguous, this plan flags it as an open question for Plan 06 rather than resolving it.
- **Formatting rule analysis:** Covered in Plan 07. Plan 08 consumes Plan 07's output (which files are affected, what changes are needed, what execution order is recommended) without re-analyzing the rules.
- **Code implementation:** Plan 08 specifies _what_ to change, not the exact code. It says "remove lines 52–53 from `endpoint.ts`" or "create barrel file with these exports" — it does not draft complete source files. (Plan 06's before/after code snippets are referenced, not duplicated.)
- **PR description drafting:** While noting that the PR description may need updating, the actual prose is out of scope.
- **Upstream communication strategy:** How to present the changes to jahow, what to say in PR comments, etc. — out of scope.

### What Remains Open

- **Rebase strategy:** Should we amend existing commits (modifying commits 11, 12, 13 which touch `endpoint.ts`, `index.ts`, and `endpoint.spec.ts`), add new commits on top of the 13, or do a full interactive rebase restructuring? Each has tradeoffs for review clarity, `git blame`, and merge conflict risk.
- **Commit granularity:** Is the refactoring one commit ("refactor: decouple CSAPI from endpoint")? Two commits ("refactor: architecture" + "style: formatting")? Three or more (barrel file, endpoint changes, index.ts changes, test migration, formatting)? The right granularity depends on Plan 07's formatting impact scope.
- **Formatting timing within commits:** Plan 07 recommends an execution order. Plan 08 must decide whether to follow it as-is or adapt it to the commit structure.
- **Squash vs preserve history:** For the final PR submission, should all refactoring commits be squashed into the existing 13 commits (cleaner history, but harder to review) or kept as additional commits (easier to review, but longer history)?
- **CSAPI fixture file handling:** Do the 4 CSAPI fixture files in `fixtures/ogc-api/csapi/` stay where they are, move, or get duplicated? (They support both `endpoint.spec.ts` tests and potential new CSAPI-specific tests.)
- **`shared/mime-type.ts` handling:** The 4 CSAPI-specific MIME type functions were added to a shared module. Do they stay (they're in `shared/`, not `csapi/`, so constraint 3 doesn't apply) or move?
- **`info.ts` changes:** The `checkHasConnectedSystems` function and `parseCollections` additions — do they stay as-is (they have no CSAPI imports), or are there Plan 06 changes?

---

## 4. Research Questions

### Core Questions

1. What is the complete, numbered file-level changelist — every file to create, modify, move, or delete — with enough specificity that a developer can execute it mechanically?
2. What is the correct commit sequence, and how does each commit relate to the existing 13-commit PR #136 structure?
3. Does each individual commit in the sequence pass all 5 CI checks, or must certain commits be squashed?
4. What is the rebase strategy from `phase-6` research branch → `clean-pr` implementation branch → upstream submission?
5. What is the final verification checklist that confirms all boundary conditions are satisfied before pushing?

### Detailed Questions

#### Complete File Inventory (8 questions)

1. What is the complete list of files to **create** as part of the refactoring? For each, specify: path, purpose, which Plan's findings define its contents, and approximate line count. Known candidates: `src/ogc-api/csapi/index.ts` (barrel file), potentially a factory file (if Plan 04/06 recommend one).
2. What is the complete list of files to **modify** as part of the refactoring? For each, specify: path, nature of modification (lines added/removed/changed), which Plan's findings define the changes. Known candidates: `src/ogc-api/endpoint.ts` (remove CSAPI imports, field, methods), `src/index.ts` (remove ~184 lines of CSAPI exports), `package.json` (add `"./csapi"` export), `src/ogc-api/endpoint.spec.ts` (migrate/rewrite 3 of 6 CSAPI tests).
3. What is the complete list of files to **move** as part of the refactoring? Are any files relocating? (Likely none — CSAPI files stay in `src/ogc-api/csapi/`, but this must be confirmed.)
4. What is the complete list of files to **delete** as part of the refactoring? (Likely none — all 56 CSAPI files remain. But confirm no files become orphaned.)
5. Are there any build configuration files that need modification? Known candidates: `package.json` (`"exports"` field), potentially `vite.node-config.js` (if the node build needs a second entry), `vite.worker-config.js` (if DTS generation needs adjustment). Plan 01's findings determine this.
6. Are there any test configuration files that need modification? Known candidates: `jest.config.cjs`, `jest.node.config.cjs`. Currently no CSAPI-specific test configuration exists — does the refactoring require any? (e.g., test path patterns, module name mapping for the barrel file.)
7. Do any CSAPI fixture files (`fixtures/ogc-api/csapi/sample-data-hub*`) need to be moved, duplicated, or modified? (Currently used by `endpoint.spec.ts` CSAPI tests. If tests migrate to CSAPI's test suite, do fixtures stay shared or get duplicated?)
8. Does the `.gitignore` change in commit 13 (`3061c68`) need any modification as part of the refactoring?

#### Changelist Per Modified File (8 questions)

9. For `src/ogc-api/endpoint.ts` (896 lines): What are the exact changes? Known removals: line 52 (`import CSAPIQueryBuilder`), line 53 (`import { scanCsapiLinks }`), lines 68–69 (cache field), lines 391–411 (`csapi()` method), lines 432–437 (`extractRootResourceUrls()`). Known additions: any new public methods (e.g., `getCollectionDocument()` if Plan 06 decides it must become public). What is the net line change?
10. For `src/index.ts` (252 lines): What are the exact changes? Lines 46–211 (~184 lines of CSAPI exports) must be removed. What remains after removal? Are there import statements that become unused? What is the final line count?
11. For `src/ogc-api/endpoint.spec.ts` (2888 lines): Which of the 6 CSAPI tests (lines 2836–2888) stay, move, or are rewritten? Plan 06's test migration plan specifies this. For tests that stay (e.g., `hasConnectedSystems`, `csapiCollections`), do they need modification? For tests that move, what is the destination file?
12. For `package.json`: What is the exact `"exports"` field after modification? Plan 01/03 provide the `"./csapi"` configuration. Are there any other `package.json` changes (e.g., `"files"` field, `"typesVersions"`, scripts)?
13. For `src/ogc-api/csapi/index.ts` (new barrel file): What is the complete list of re-exports? Plan 06 designs this — how many value exports, how many type exports? What is the approximate line count? Does it follow the `formats/index.ts` pattern (sectioned with JSDoc and comment dividers)?
14. For `src/ogc-api/info.ts` (309 lines): Do `checkHasConnectedSystems` (line 112) and the `parseCollections` additions (lines 255, 265, 303) stay unmodified? Plan 06 verifies these have no CSAPI imports — if confirmed, no changes needed. But document this explicitly.
15. For `src/shared/mime-type.ts` and `src/shared/mime-type.spec.ts`: Do the 4 CSAPI-specific MIME type functions stay? They're in `shared/`, not `csapi/`, so constraint 3 doesn't apply. But are they only used by CSAPI code? If so, should they move to `csapi/` for conceptual clarity?
16. If Plan 04/06 recommend a factory function/file: What is the path, signature, and approximate line count? Does it go in `csapi/factory.ts` or is it added to `csapi/url_builder.ts`?

#### Commit Sequence Design (7 questions)

17. How many commits should the refactoring consist of? Options: (a) a single "refactor: decouple CSAPI" commit, (b) two commits (architecture + formatting), (c) three or more granular commits. What are the tradeoffs of each for review clarity and CI compliance?
18. Should the refactoring commits be added on top of the existing 13 commits, or should they be squashed into the existing commits via interactive rebase? Specifically: commit 11 (`integrate CSAPI into endpoint`), commit 12 (`export CSAPI types from index`), and commit 13 (`.gitignore`) are the ones that would need amendment. What are the tradeoffs?
19. If commits are amended via interactive rebase, what is the exact sequence of `git rebase -i` operations? Which commits are `edit`ed, which are `pick`ed?
20. If commits are added on top, what are the commit messages? Draft the complete commit message for each, following the existing `feat(csapi):` / `test(csapi):` / `chore:` convention. Include the body text explaining the boundary condition compliance.
21. Does the commit sequence ensure that each intermediate commit passes all 5 CI checks? If not, which commits must be squashed together? For example: removing CSAPI from `index.ts` in one commit and creating the barrel file in a later commit would cause an intermediate state where CSAPI exports are unavailable — tests would fail.
22. What commit ordering minimizes merge conflicts? For example: creating the barrel file first (no conflicts), then modifying `endpoint.ts` (may conflict with commit 11), then modifying `index.ts` (may conflict with commit 12).
23. Should formatting (Plan 07's Prettier changes) be a separate commit or interleaved? If Plan 07 found that formatting affects many files with many line changes, a dedicated formatting commit keeps logic diffs clean. If formatting changes are minimal, interleaving is simpler.

#### Rebase Strategy (6 questions)

24. What is the current state of the `clean-pr` branch relative to `upstream/main`? Is it 13 commits ahead? Are there any upstream commits that need to be incorporated?
25. What is the rebase path: `phase-6` → `clean-pr` → upstream? Or can we go directly from implementation on `clean-pr`? (The `phase-6` branch is for research only — no code changes. Implementation happens on `clean-pr`.)
26. If we use `git rebase -i` on `clean-pr`, what is the risk of conflicts? The refactoring primarily modifies commits 11 (`endpoint.ts`), 12 (`index.ts`), and potentially 13 (`.gitignore`). Commits 1–10 (pure CSAPI additions) should be conflict-free.
27. After rebasing, should we force-push to `clean-pr`, or create a new branch? Force-pushing rewrites history on the open Draft PR #136. Is this acceptable for a draft PR?
28. Should we update the PR from "Draft" to "Ready for Review" as part of this changelist, or keep it as draft?
29. Does the rebase need to incorporate any new upstream commits? Check whether `upstream/main` has advanced past the base commit (`53a6449 — Merge pull request #132 fix-bbox`).

#### Verification and CI Compliance (7 questions)

30. What is the complete pre-push verification checklist? List every command that must pass, in order, with expected output.
31. What `git grep` commands verify all boundary conditions? Draft the exact commands and expected results:
    - `git grep "from.*csapi" src/ogc-api/endpoint.ts` → 0 matches
    - `git grep "from.*csapi" src/index.ts` → 0 matches (CSAPI re-exports removed)
    - `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"` → 0 matches (no outward imports)
    - What other `git grep` patterns are needed?
32. After the refactoring, what does `npm run typecheck` verify? Does `tsc --noEmit` check the barrel file's re-exports? Does it verify that the types are consistent?
33. After the refactoring, what does `npm run test:browser` verify? Which tests exercise the refactored code path? How many tests exist total, and how many are CSAPI-related?
34. After the refactoring, what does `npm run test:node` verify? Same questions as Q33 but for the Node.js environment.
35. What is Plan 06's "litmus test" applied concretely? The test is: "removing `src/ogc-api/csapi/` entirely leaves core functional." Draft the exact commands to verify this:
    - Temporarily rename/remove `src/ogc-api/csapi/`
    - Run `npm run typecheck` — must pass
    - Run non-CSAPI tests — must pass
    - Restore `src/ogc-api/csapi/`
36. Should the litmus test be automated as a CI step, or is it a one-time manual verification?

#### PR and Documentation Updates (4 questions)

37. Does the PR description for PR #136 need updating? Currently it describes CSAPI as integrated into the endpoint. After refactoring, the description must reflect the decoupled architecture with the separate entry point.
38. Do any README files need updating? The `app/README.md` or `examples/README.md` may reference `endpoint.csapi()` — do they need modification?
39. Should a MIGRATION.md or BREAKING-CHANGES.md be created documenting the new import path (`@camptocamp/ogc-client/csapi`)? Or is this premature since CSAPI was never in a released version?
40. Do the `app/examples/edr.ts` or other examples reference CSAPI in a way that needs updating?

**Total: 40 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                       | Path                                                                                  | What to Extract                                                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Endpoint CSAPI integration   | `src/ogc-api/endpoint.ts` (lines 2, 52–53, 68–69, 220–241, 312–337, 391–411, 432–437) | Every CSAPI touchpoint: 2 imports, 1 cache field, 3 getters/methods, 1 private helper. Exact line numbers for the changelist. |
| Root CSAPI exports           | `src/index.ts` (lines 46–211)                                                         | All ~152 CSAPI symbols (184 lines) that must be removed and relocated to the barrel file                                      |
| Endpoint CSAPI tests         | `src/ogc-api/endpoint.spec.ts` (lines 2836–2888)                                      | 6 test cases in 2 describe blocks. Must classify each: stays, moves, or rewrites.                                             |
| Info.ts CSAPI additions      | `src/ogc-api/info.ts` (lines 112–121, 255, 265, 303)                                  | `checkHasConnectedSystems()` and `parseCollections` additions — verify no CSAPI imports                                       |
| Shared MIME type additions   | `src/shared/mime-type.ts` (CSAPI additions)                                           | 4 CSAPI-specific functions — determine if they stay in shared or move                                                         |
| Shared MIME type tests       | `src/shared/mime-type.spec.ts` (CSAPI additions)                                      | Tests for CSAPI MIME types — stay or move?                                                                                    |
| Package.json                 | `package.json`                                                                        | Current `"exports"` field (`"."` only), scripts, `"files"` field                                                              |
| Existing barrel file pattern | `src/ogc-api/csapi/formats/index.ts` (344 lines)                                      | Re-export pattern: JSDoc sections, comment dividers, value vs type export grouping                                            |
| CSAPI module full inventory  | `src/ogc-api/csapi/` (56 files)                                                       | 27 source, 24 unit test, 5 integration test — all must remain after refactoring                                               |
| CSAPI fixtures               | `fixtures/ogc-api/csapi/sample-data-hub*` (4 files)                                   | JSON fixtures for endpoint CSAPI tests — fixture handling strategy                                                            |
| Vite node config             | `vite.node-config.js`                                                                 | Node build entry point (`src-node/index.ts` → `dist/dist-node.js`) — may need `./csapi` considerations                        |
| Vite worker config           | `vite.worker-config.js`                                                               | Worker build + DTS generation — `vite-plugin-dts` scope for `.d.ts` files                                                     |
| CI workflow                  | `.github/workflows/qa.yml`                                                            | 5-step sequential CI: format:check, typecheck, lint, test:browser, test:node                                                  |
| Jest browser config          | `jest.config.cjs`                                                                     | Test environment, transform, module name mapping — verify CSAPI test compatibility                                            |
| Jest node config             | `jest.node.config.cjs`                                                                | Node test config — verify CSAPI test compatibility                                                                            |
| TypeScript config            | `tsconfig.json`                                                                       | Include paths, declaration generation — verify barrel file is in scope                                                        |
| Clean-PR commit log          | `git log --oneline clean-fork/clean-pr`                                               | 13-commit structure: commits 1–10 (pure CSAPI), 11 (endpoint integration), 12 (index exports), 13 (.gitignore)                |

### External Sources

| Source                        | URL/Reference                                                                                                                                                         | What to Extract                                                                                             |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| GitHub PR #136                | `https://github.com/camptocamp/ogc-client/pull/136`                                                                                                                   | Current PR description, review comments from jahow, draft status, any CI check results from previous pushes |
| GitHub Issue #118             | `https://github.com/camptocamp/ogc-client/issues/118`                                                                                                                 | jahow's original feature request, referenced EDR precedent (PR #114), constraints on CSAPI integration      |
| Upstream CI workflow          | `https://github.com/camptocamp/ogc-client/blob/master/.github/workflows/qa.yml`                                                                                       | Verify our local `qa.yml` matches upstream — check for any recent changes                                   |
| Git interactive rebase docs   | `https://git-scm.com/docs/git-rebase`                                                                                                                                 | `git rebase -i` mechanics for amending historical commits                                                   |
| Conventional Commits          | `https://www.conventionalcommits.org/en/v1.0.0/`                                                                                                                      | Commit message format: `feat(csapi):`, `refactor(csapi):`, `chore:` — match existing convention             |
| GitHub Draft PR documentation | `https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests` | Force-push behavior on draft PRs, review implications                                                       |

### Prior Research Findings (All Plans)

| Finding          | Path                                                                          | What to Use                                                                                                                                                                                                                                                                 |
| ---------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plan 01 findings | `docs/research/phase-6/findings/01-build-system-entry-point-analysis.md`      | `package.json` `"exports"` configuration for `"./csapi"`, build script changes (if any), esbuild per-file output confirmation, DTS generation scope                                                                                                                         |
| Plan 02 findings | `docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md`       | EDR pattern comparison — what changes are acceptable, what EDR did that CSAPI must not, whether EDR also needs refactoring                                                                                                                                                  |
| Plan 03 findings | `docs/research/phase-6/findings/03-separate-entry-point-design-patterns.md`   | Barrel file structure, `package.json` exports format, TypeScript declaration file path mapping, consumer usage pattern                                                                                                                                                      |
| Plan 04 findings | `docs/research/phase-6/findings/04-sub-module-api-design-patterns.md`         | Recommended consumer API shape — does the changelist need a new factory file, or is the CSAPIQueryBuilder constructor the API?                                                                                                                                              |
| Plan 05 findings | `docs/research/phase-6/findings/05-module-decoupling-patterns.md`             | Coupling level — does the changelist need adapter types or interface files? Type import strategy (`import type` from core).                                                                                                                                                 |
| Plan 06 findings | `docs/research/phase-6/findings/06-endpoint-decoupling-architecture.md`       | **Primary input.** Complete architecture: consumer API, `hasConnectedSystems` placement, `csapiCollections` placement, `scanCsapiLinks` resolution, barrel file contents, test migration plan, before/after code for every integration point, boundary verification matrix. |
| Plan 07 findings | `docs/research/phase-6/findings/07-prettier-eslint-configuration-analysis.md` | Formatting impact scope (files/lines changed), ESLint error inventory, execution order recommendation (format-first/refactor-first/atomic), file-by-file impact matrix.                                                                                                     |

---

## 6. Research Methodology

### Phase 1: Consolidate Prior Findings Into File Operations (~35 minutes)

**Objective:** Extract the concrete file-level implications from each prior plan's findings, resolving any gaps or ambiguities.

**Tasks:**

1. From Plan 01: Extract the exact `package.json` `"exports"` diff. Confirm whether `vite.node-config.js`, `vite.worker-config.js`, or `tsconfig.json` require changes.
2. From Plan 02: Confirm whether any EDR-related files require changes as part of this refactoring. (Expected: no — EDR pattern is acceptable at its scale.)
3. From Plan 03: Extract the barrel file path (`src/ogc-api/csapi/index.ts`), re-export pattern, and sub-path export format for `package.json`.
4. From Plan 04/05: Confirm whether new files are required (factory file, adapter file, interface file). Extract the consumer API implications — does `CSAPIQueryBuilder` constructor change? Are new types needed?
5. From Plan 06: Extract the complete integration point resolution table — for every function/property/type that was straddling the boundary, record the decision (stays, moves, removed, refactored) and the corresponding file operation.
6. From Plan 06: Extract the test migration plan — which of the 6 tests stay, move, or rewrite. Determine the destination file for moved tests.
7. From Plan 07: Extract the formatting impact scope (file count, line count), ESLint error inventory, and execution order recommendation.
8. Identify any gaps — findings that are ambiguous or that multiple plans resolved differently. Flag these as issues to resolve before proceeding.

**Output:** File operations ledger — a table mapping each prior finding to a specific file create/modify/move/delete operation.

### Phase 2: Build the Complete File-Level Changelist (~40 minutes)

**Objective:** Produce the numbered changelist with every file operation, organized by category (create, modify, delete).

**Tasks:**

1. **Files to create:** List each new file with: path, purpose, approximate line count, which plan defines its contents. Include the barrel file and any factory/adapter files from Plan 06.
2. **Files to modify:** List each modified file with: path, lines to remove, lines to add, net change, which plan defines the modification. Include `endpoint.ts`, `index.ts`, `endpoint.spec.ts`, `package.json`, and any build configs from Plan 01.
3. **Files to move:** Inventory any files that relocate. (Expected: none — but confirm for MIME type functions if Plan 06 recommends moving them.)
4. **Files to delete:** Inventory any files removed. (Expected: none.)
5. **File dependencies:** For each file in the changelist, note which other files in the changelist it depends on (e.g., the barrel file must exist before `index.ts` removes the CSAPI exports, or tests will break).
6. Cross-reference the changelist against the 67-file diff of PR #136. Which of the 67 files are touched by the refactoring? (Expected: 5–8 of the 67.)
7. Verify completeness: is there any file affected by the refactoring that is NOT in the changelist? Mentally walk through each boundary condition and verify the changelist satisfies it.

**Output:** Numbered file-level changelist with full metadata.

### Phase 3: Design the Commit Sequence (~35 minutes)

**Objective:** Determine the optimal commit sequence, commit messages, and rebase strategy.

**Tasks:**

1. Evaluate three commit structure options:
   - **Option A (Amend):** Interactive rebase of `clean-pr`, amending commits 11, 12, and 13 to include the refactoring changes. The result is a 13-commit history that looks like CSAPI was never integrated into the endpoint. Pro: Clean history, as if the architecture was right from the start. Con: Force-push required, harder to review the refactoring diff in isolation.
   - **Option B (Append):** Add 1–3 new commits on top of the 13 existing commits. Pro: Refactoring changes are clearly visible as separate commits, easy to review. Con: Longer history, the "integrate into endpoint" commit (11) is followed by an "undo integration" commit.
   - **Option C (Squash entire PR):** Squash all commits into a single commit. Pro: Simplest history. Con: Loses the granular CSAPI build-up story (commits 1–10).
2. For the selected option, draft the exact commit messages following the existing `feat(csapi):` / `refactor(csapi):` / `chore:` convention.
3. Verify each interim commit against CI compliance: does each commit individually pass `format:check`, `typecheck`, `lint`, `test:browser`, `test:node`? If not, identify commits that must be combined.
4. Determine the formatting commit placement: is formatting a separate commit, or included in the architectural commit(s)?
5. Draft the rebase commands: the exact `git` command sequence from current state to final state. Include handling of merge conflicts if predictable.
6. Determine force-push strategy: is `git push --force-with-lease` acceptable for the draft PR? What precautions are needed?

**Output:** Commit sequence specification with messages, CI compliance analysis, and rebase strategy.

### Phase 4: Build the Verification Checklist (~20 minutes)

**Objective:** Produce the final gate checklist that must pass before pushing.

**Tasks:**

1. Draft boundary condition verification commands (4 `git grep` patterns from Strategy § Boundary Conditions).
2. Draft CI verification commands (5 `npm run` commands matching `qa.yml`).
3. Draft the litmus test procedure (remove `csapi/`, verify core compiles and tests pass, restore `csapi/`).
4. Draft the diff review procedure: commands to generate the total diff against `upstream/main` for human review before pushing.
5. Draft a "point of no return" checklist: what must be true before force-pushing to `clean-pr` (all local verification passes, current `clean-pr` state is backed up via tag or branch, etc.).

**Output:** Complete verification checklist with exact commands and expected outputs.

### Phase 5: Synthesis and Final Documentation (~30 minutes)

**Objective:** Consolidate all phase outputs into the deliverable implementation spec.

**Tasks:**

1. Synthesize the file-level changelist, commit sequence, rebase strategy, and verification checklist into a single coherent document.
2. Verify all 40 research questions are answered with specific, actionable answers.
3. Validate the changelist against all boundary conditions — walk through each constraint and verify the changelist satisfies it.
4. Produce a quick-reference summary: the changelist as a simple numbered list with one-line descriptions (for use as a working checklist during implementation).
5. Produce the rebase runbook: the exact git command sequence from start to finish.
6. Produce the CI verification runbook: the exact command sequence for pre-push verification.
7. Review for completeness: is there anything a developer would need to look up or decide when executing this spec? If so, resolve it or document it as a known gap.
8. Write the deliverable document.

**Output:** Completed implementation spec at `docs/research/phase-6/findings/08-file-level-changelist-and-commit-strategy.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 40 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] Every finding from Plans 01–07 is accounted for — no prior finding is ignored or contradicted
- [ ] The file-level changelist is complete: every file to create, modify, move, or delete is listed with metadata
- [ ] The file changelist covers all 4 boundary conditions — each constraint is traceable to specific file operations
- [ ] The commit sequence is specified with draft commit messages and CI compliance analysis
- [ ] Each commit in the sequence is verified against CI compliance (passes or must be squashed)
- [ ] The rebase strategy is specified with exact git commands
- [ ] The verification checklist includes all boundary condition checks, CI commands, and the litmus test
- [ ] The `git grep` patterns for each boundary condition are drafted with expected (zero-match) results
- [ ] The changelist accounts for formatting (Plan 07's output) and places it correctly in the commit sequence
- [ ] No file affected by the refactoring is missing from the changelist (completeness verified by walking through constraints)
- [ ] A developer can execute the spec mechanically — zero ambiguities, zero decisions left to make
- [ ] **Implementation scope gate applied:** Every file operation passes the minimum-change test — no changes beyond what jahow's requirements demand
- [ ] Deliverable document is complete and follows the findings report template
- [ ] The deliverable document IS the implementation spec — it bridges research and action

---

## 8. Deliverable

**Title:** File-Level Changelist and Commit Strategy: Complete Implementation Specification for CSAPI Upstream Refactoring

**Location:** `docs/research/phase-6/findings/08-file-level-changelist-and-commit-strategy.md`

**Required Sections:**

1. Executive Summary — total scope (files created, modified, deleted), commit count, rebase approach, verification gate count
2. Prior Findings Consolidation — what each Plan (01–07) contributed to the changelist, any gaps resolved
3. File-Level Changelist — numbered, categorized (create/modify/move/delete), with full metadata per file:
   - Path (before/after if moved)
   - Operation (create/modify/delete)
   - Lines added/removed/net
   - Which Plan defines the change
   - Brief summary of the change
   - Dependencies on other changelist items
4. Changelist Per Modified File — detailed breakdown for each modified file: what lines are removed, what lines are added, what the file looks like after
5. Commit Sequence Specification — ordered commits with: number, message (title + body), files affected, CI compliance (pass/fail per check)
6. Rebase Strategy and Git Command Runbook — exact sequence of git commands from current state to final state
7. Formatting Integration — how Plan 07's findings are incorporated into the commit sequence
8. Verification Checklist — pre-push gates:
   a. Boundary condition `git grep` commands (4)
   b. CI verification `npm run` commands (5)
   c. Litmus test procedure (remove csapi/, verify core, restore)
   d. Diff review procedure
   e. Point-of-no-return checklist
9. PR Update Notes — what changes to PR #136 description, labels, and status
10. Quick-Reference Implementation Checklist — the whole changelist as a printable numbered list
11. Known Risks and Rollback Plan — what could go wrong during implementation and how to recover
12. Open Questions — anything unresolved (ideally: nothing)

---

## 9. Risks and Mitigation

| Risk                                                                                                                                                                                                           | Impact                                                                                  | Mitigation                                                                                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A prior plan's finding is ambiguous, creating an unclear file operation in the changelist                                                                                                                      | Developer encounters ambiguity during implementation, must stop and re-research         | Phase 1 explicitly identifies gaps in prior findings. Any ambiguity is flagged and resolved (or escalated to the appropriate plan for re-investigation) before proceeding to Phase 2.                                                               |
| Commit sequence has a CI-failing intermediate state (e.g., barrel file doesn't exist yet but index.ts already removed CSAPI exports)                                                                           | CI rejects the PR, or individual commits can't be cherry-picked                         | Phase 3 explicitly verifies each commit against CI compliance. Commits that create failing intermediate states are merged/squashed. The commit dependency graph from Phase 2 identifies ordering constraints.                                       |
| Interactive rebase introduces merge conflicts when amending commits 11 or 12                                                                                                                                   | Rebase fails, requiring manual conflict resolution that may introduce bugs              | Phase 3 assesses conflict risk for each rebase option. If the amend strategy has high conflict risk, the append strategy is chosen instead. The git command runbook includes conflict resolution hints for predictable conflicts.                   |
| Force-pushing to `clean-pr` loses work if the local branch is out of sync                                                                                                                                      | PR branch diverges from local, causing confusion or data loss                           | The verification checklist includes a "backup" step: tag the current `clean-pr` state before force-pushing (`git tag pre-refactor-backup`).                                                                                                         |
| The changelist misses a file, and the omission isn't caught until CI runs                                                                                                                                      | CI failure on push, requiring a fix commit that clutters the history                    | Phase 2 includes a completeness verification: walk through every boundary condition and verify the changelist satisfies it. Phase 4's litmus test catches missing changes before push.                                                              |
| Plan 07's formatting changes interact with Plan 06's architectural changes in unexpected ways (e.g., Prettier changes lines that the refactoring also changes, causing merge conflicts in the commit sequence) | Commit sequence becomes tangled, formatting and architecture can't be cleanly separated | Phase 3's formatting integration step explicitly addresses this: either formatting is applied in a separate commit before or after architecture (avoiding overlap), or commits are atomic (each commit includes formatting for its affected files). |
| Upstream (`camptocamp/ogc-client` main branch) advances past our base commit (`53a6449`) between now and push time                                                                                             | Rebase against upstream introduces new conflicts                                        | Phase 3's rebase strategy includes a step to check for upstream advancement and rebase against the latest `upstream/main` if needed. The 13 CSAPI commits (1–10 are pure additions, minimal conflict risk) should rebase cleanly.                   |
| The 13-commit history is deemed too long by jahow — he may request squashing                                                                                                                                   | All commit sequence work is wasted if the reviewer wants fewer commits                  | Phase 3 evaluates all three options (amend, append, squash). A fallback squash plan is documented regardless of the selected strategy, so a quick pivot is possible.                                                                                |

---

## 10. Research Status Checklist

- [ ] Phase 1: Consolidate Prior Findings Into File Operations — Not Started
- [ ] Phase 2: Build the Complete File-Level Changelist — Not Started
- [ ] Phase 3: Design the Commit Sequence — Not Started
- [ ] Phase 4: Build the Verification Checklist — Not Started
- [ ] Phase 5: Synthesis and Final Documentation — Not Started
- [ ] Deliverable document created
- [ ] Implementation can begin — all research is complete

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
