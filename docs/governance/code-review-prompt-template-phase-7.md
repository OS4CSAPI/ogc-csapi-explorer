# Code Review Prompt Template — Phase 7

**Purpose:** Reusable prompt for triggering AI-generated code reviews during Phase 7 (Code Review Cleanup). Adapts the Phase 6 review template skeleton to the specific quality concerns of type safety, DRY refactoring, security hardening, and test fixture centralization that define Phase 7's work.

**Version:** 1.0
**Date:** March 7, 2026
**Supersedes:** Nothing — sibling to `code-review-prompt-template-phase-6.md` (Phase 6), `code-review-prompt-template-phase-5.md` (Phase 5), `code-review-prompt-template-phase-3.md` (Phase 3), and `code-review-prompt-template.md` (Phase 2), which remain valid for any revisits to those phases.
**Report destination:** `docs/implementation/phase-{X.Y}-code-review.md`

---

## Why a Separate Template?

Phase 7 code differs fundamentally from Phase 6 code:

| Dimension          | Phase 6 (Upstream Acceptance Refactoring)                                          | Phase 7 (Code Review Cleanup)                                                          |
| ------------------ | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Primary output     | Structural changes — barrel file, factory function, export reorganization          | Quality fixes — type safety, DRY consolidation, security hardening, test cleanup       |
| Correctness check  | "Is the module boundary clean? Do all 12 verification gates pass?"                 | "Are the review findings properly resolved? Is behavior preserved?"                    |
| Test strategy      | 2 factory tests + `git grep` boundary checks + full CI suite regression            | Per-issue unit/integration tests + full CI suite regression                            |
| Pattern reference  | `formats/index.ts` barrel, EDR factory blueprint, existing `package.json` exports  | `build()` private helper, `parseBaseStream` extraction, `makeTestCollection` factory   |
| Validation concern | Export completeness, import direction, tree-shaking, visibility changes            | Type narrowing correctness, URL encoding, scheme validation, deduplication             |
| Heatmap dimensions | Architecture-specific (boundary isolation, export coverage, formatting compliance) | Issue-specific (20 issues across 6 phases: quick wins, parsers, type safety, DRY, security, tests) |
| Spec references    | jahow's PR #136 review requirements                                                | Senior developer code review findings (16 docs), OGC 23-002 Part 2, OGC 23-001        |
| Risk profile       | Build/bundle correctness, import resolution                                        | Behavioral correctness, backward compatibility, zero public API breakage               |

The Phase 6 boundary gates (V1–V4), export completeness audit, and task-specific checklists (Categories A–G) do not apply. Phase 7 needs issue-resolution and code-quality review dimensions.

---

## When to Use

Trigger this prompt after any of these Phase 7 milestones:

1. **A full Phase (A–F) is completed** — e.g., all Phase D `url_builder.ts` steps done
2. **All 20 steps are completed** — comprehensive review of the entire Phase 7 branch
3. **Before porting to `clean-pr`** — final gate review ensuring everything is correct
4. **After porting to `clean-pr`** — validation that the patch applied cleanly

Do NOT trigger after trivial doc-only commits or non-code changes.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a comprehensive code review of the Phase 7 work.

### Scope

**Phase:** {{Phase number, e.g., "7.1" or "7.final"}}
**Steps completed:** {{List step numbers and issue numbers, e.g., "Steps 1–20 (Issues #98, #148, #149, #146, #140, #154, #155, #143, #144, #142, #139, #156, #157, #102, #158, #159, #160, #150, #147, #151)"}}
**Commits to review:** {{List commit SHAs or say "all 20 commits on phase-7 since phase-6"}}
**Last review:** {{Reference the previous review doc, e.g., "docs/implementation/phase-6.X-code-review.md" or "none — first Phase 7 review"}}

### Context

Phase 7 resolves **17 issues** (11 code-review findings + 6 pre-existing bugs) across **20 execution passes** (3 parent issues were split into 2–3 sub-issues each for safe single-pass execution). One additional issue (#111) was auto-resolved by #160. This work was driven by a senior developer's code review of the `clean-pr` draft PR (#136).

**Issue splits:**
- #141 → #154 + #155 (parseCollectionResponse: core impl + integration test call sites)
- #100 → #156 + #157 (assertResourceAvailable removal: 33 methods + 39 methods)
- #145 → #158 + #159 + #160 (build() wrapper: 33 + 25 + 29 methods)

**All changes are within `src/ogc-api/csapi/` except #154 which touches `formats/response.ts` (shared file).**

### Review Instructions

1. **Review Lessons Learned** — read both documents before evaluating code:
   - `docs/governance/phase-3-lessons-learned.md` — Key checks still active:
     - Lesson 1: Does any new code introduce an architectural layer without upstream precedent?
     - Lesson 2: Postel's Law — never gate extraction on validation
     - Lesson 4: Are there parallel systems doing the same thing?
     - Lesson 10: Do type names collide with JS/TS built-ins?
   - `docs/governance/phase-2-lessons-learned.md` — General guardrails (Lessons 6-10 still active)

2. **Review Phase 7 Plan** — understand scope, dependency order, and issue inventory:
   - `docs/planning/phase-7/P7-code-review-cleanup-plan.md` (v1.3)
   - `docs/planning/phase-7/P7-scope-split-assessment.md`

3. **Review the original code review findings** (16 finding documents):
   - `docs/code-review/003-pending-p1-unchecked-generic-cast-response.md` → #141
   - `docs/code-review/004-pending-p2-subpath-no-encoding.md` → #142
   - `docs/code-review/007-pending-p2-properties-null-cast.md` → #143
   - `docs/code-review/008-pending-p2-raw-json-spread-into-typed-result.md` → #144
   - `docs/code-review/009-pending-p2-assert-resource-paired-pattern.md` → #145
   - `docs/code-review/010-pending-p2-datastream-controlstream-base-duplication.md` → #146
   - `docs/code-review/011-pending-p3-server-href-scheme-validation.md` → #147
   - `docs/code-review/012-pending-p3-redundant-casts-after-isrecord.md` → #148
   - `docs/code-review/013-pending-p3-null-guard-duplicated-5x.md` → #149
   - `docs/code-review/014-pending-p3-create-command-duplicate.md` → #150
   - `docs/code-review/016-pending-p3-integration-test-fixture-duplication.md` → #151
   - `docs/code-review/015-duplicate-p3-get-command-status-inconsistent.md` → #111
   - `docs/code-review/upstream-findings-report.md` (4 upstream-only findings — NOT in scope)

4. **Run CI verification gates** — execute and record results:

   - `npx tsc --noEmit` (C1 — type check)
   - `npm run lint` (C2 — ESLint)
   - `npm test` (C3 — full test suite)
   - `npx prettier --check src/` (C4 — formatting)

5. **Read all changed files** — identify every file modified since the last review commit. For each file, note:
   - What changed (lines added/modified/removed)
   - Whether the change follows the established pattern for its component type (see Pattern References below)

6. **Verify Phase 7 diff stats** — run and record:

   ```bash
   git diff --stat phase-6..phase-7 -- src/
   ```

   Expected: 27 files changed, ~1,166 insertions, ~797 deletions. Significant deviation warrants investigation.

7. **Reaffirm ALL prior findings** — if a previous Phase 7 review exists, read it and check each finding:
   - For each RESOLVED finding: confirm it's still resolved, cite evidence
   - For each STILL OPEN finding: check if it was addressed, update status
   - For each UNCHANGED finding (not-our-code): reaffirm unchanged status

8. **Evaluate each Phase 7 issue resolution against its quality dimension:**

   #### Phase A — Zero-Risk Quick Wins

   **Category A1 — Documentation (#98):**
   - [ ] `@see` link in `parseCommandStatus` points to correct OGC 23-002 clause
   - [ ] No code changes — documentation only

   **Category A2 — Redundant Casts (#148):**
   - [ ] All `as Record<string, unknown>` casts after `isRecord()` / `isLinkReference()` removed
   - [ ] TypeScript narrowing still holds — `tsc --noEmit` clean
   - [ ] Zero behavioral change

   #### Phase B — Parser Cleanup (part2.ts)

   **Category B1 — requireObject helper (#149):**
   - [ ] Private `requireObject(json, callerName)` helper extracts null-guard + cast
   - [ ] 5 inline null-guard blocks replaced with `requireObject()` calls
   - [ ] Identical runtime behavior — same error messages

   **Category B2 — parseBaseStream helper (#146):**
   - [ ] Private `parseBaseStream(callerName, json)` extracts 7 shared fields: `id`, `name`, `description`, `validTime`, `formats`, `systemId`, `links`
   - [ ] `parseDatastream()` and `parseControlStream()` spread base + add only resource-specific fields
   - [ ] Uses `requireObject()` from #149

   **Category B3 — paramsSchema fallback (#140):**
   - [ ] `parseControlStreamSchemaResponse()` accepts `paramsSchema` in addition to `commandSchema`
   - [ ] Handles older OSH servers that use the alternative field name
   - [ ] Additive only — no existing behavior changed

   #### Phase C — Type Safety Fixes

   **Category C1 — parseItem callback (#154 + #155):**
   - [ ] `parseCollectionResponse<T>()` accepts optional `parseItem?: (raw: unknown) => T` callback
   - [ ] When provided, each element in `features`/`items` array is mapped through callback
   - [ ] When omitted, backward-compatible behavior preserved (raw cast)
   - [ ] All ~35–40 integration test call sites updated with appropriate parser callbacks
   - [ ] Unit tests cover: with callback, without callback, malformed elements

   **Category C2 — extractCSAPIFeature null guard (#143):**
   - [ ] `feature.properties` checked for null/type before casting to `Record<string, unknown>`
   - [ ] Defensive guard — GeoJSON spec allows `properties: null`
   - [ ] Unit test covers null properties case

   **Category C3 — SensorML raw JSON spread (#144):**
   - [ ] `...json` spread replaced with explicit field extraction in all 3 SensorML parsers
   - [ ] `physical-system.ts`, `simple-process.ts`, `aggregate-process.ts` all updated
   - [ ] No raw server fields leak into typed output objects
   - [ ] Unit tests verify only declared fields present

   #### Phase D — url_builder.ts Batch (The Big One)

   **Category D1 — subPath union types (#142):**
   - [ ] `subPath` parameter constrained to string literal union type (not `string`)
   - [ ] Runtime allowlist prevents unrecognized paths
   - [ ] `encodeURIComponent()` or equivalent encoding applied

   **Category D2 — getDeploymentSystems deprecation (#139):**
   - [ ] `getDeploymentSystems()` marked `@deprecated` with migration guidance
   - [ ] `deployedSystems` is an inline GeoJSON property, not a sub-resource endpoint (OGC 23-001 Table 43)

   **Category D3 — assertResourceAvailable removal (#156 + #157):**
   - [ ] `assertResourceAvailable()` removed from 72 per-ID methods (33 + 39)
   - [ ] Per-ID methods no longer throw when the collection doesn't advertise the resource type link
   - [ ] Collection-level listing methods still have the guard (via `build()`)
   - [ ] Tests updated — per-ID methods accept any collection

   **Category D4 — Nested parent IDs (#102):**
   - [ ] Command/observation CRUD methods accept optional parent ID parameters
   - [ ] Nested URLs constructable: e.g., `/controlstreams/{csId}/commands/{cmdId}`
   - [ ] Backward-compatible — new params are optional
   - [ ] Unit tests cover nested and flat paths

   **Category D5 — build() helper (#158 + #159 + #160):**
   - [ ] Private `build(resourceType, id?, subPath?, options?)` method created
   - [ ] Fuses `assertResourceAvailable()` with `buildResourceUrl()` for collection-level methods
   - [ ] Per-ID methods use `build()` WITHOUT the assert guard (conditional based on whether `id` is present)
   - [ ] All 87 public methods rewritten to delegate through `build()`
   - [ ] Zero direct `assertResourceAvailable()` or `buildResourceUrl()` calls in any public method
   - [ ] #111 auto-resolved — `getCommandStatus()` no longer uses manual `buildQueryString()` concatenation

   **Category D6 — createCommands delegation (#150):**
   - [ ] `createCommands()` body replaced with `return this.createCommand(controlStreamId)`
   - [ ] Single-line delegation — no duplicated logic

   #### Phase E — Security Hardening

   **Category E1 — URL scheme validation (#147):**
   - [ ] `isSafeHref()` function validates `href` values in `scanCsapiLinks()`
   - [ ] Only `http:` and `https:` absolute URLs accepted — relative paths pass through
   - [ ] `javascript:`, `data:`, `vbscript:`, `ftp:`, `//evil.com` all rejected
   - [ ] Applied at all 3 storage points in `scanCsapiLinks()`
   - [ ] Unit tests cover all rejection and acceptance cases

   #### Phase F — Test-Only Cleanup

   **Category F1 — Shared fixture factory (#151):**
   - [ ] `_fixtures.ts` created with `PADDING` constant, `ALL_CSAPI_LINKS` array, `makeTestCollection()` factory
   - [ ] 4 spec files import from `_fixtures.ts` instead of declaring local factories
   - [ ] 10 padding fields no longer duplicated across 4 files
   - [ ] Each spec's local factory delegates to `makeTestCollection()` with domain-specific overrides
   - [ ] Zero production code impact — test-only change

9. **Cross-cutting quality checks** — apply to all changed files:

   - **Backward compatibility:** Zero public API signature changes unless explicitly required by the issue (#102 adds optional params — backward-compatible; #139 deprecates but doesn't remove)
   - **Minimal diff principle:** Changes are limited to what each issue requires — no opportunistic refactoring
   - **JSDoc quality:** New helpers (`build()`, `parseBaseStream`, `requireObject`, `isSafeHref`, `makeTestCollection`) have complete JSDoc with `@param`, `@returns`, `@throws`, `@internal` as appropriate
   - **Error message clarity:** Error messages in `build()` and `assertResourceAvailable()` clearly identify the collection and missing resource type
   - **Test coverage:** Every behavioral change has corresponding test additions/updates
   - **Import hygiene:** No circular imports; `import type` used for type-only references
   - **Consistency:** New code follows patterns already established in the repo

10. **Verify upstream-only findings are untouched** — confirm these are NOT modified:
    - Finding 001 (path traversal in `itemId`) — upstream-only
    - Finding 002 (query param injection via `encodeURI`) — upstream-only
    - Finding 005 (`http://` accepted without warning) — upstream-only
    - Finding 006 (full error object logged) — upstream-only

11. **Check for known pre-existing test failures** — Phase 7 did NOT introduce these:
    - 3 pre-existing failures in `command.spec.ts` and `observation.spec.ts` error scenario tests
    - These relate to `isSafeHref()` rejecting relative-path-only link fixtures that lack `http:`/`https:` schemes
    - Verify they existed before Phase 7 by comparing against `phase-6` baseline

12. **Classify every finding** using these severity labels:
    - **BUG** — incorrect behavior, wrong output, runtime error
    - **DESIGN** — architectural concern, DRY violation, type safety issue
    - **GAP** — missing test, incomplete resolution, acceptance criteria not fully met
    - **POSITIVE** — something done well that should be maintained
    - **INFORMATIONAL** — worth noting but no action needed
    - **CONSISTENCY** — follows or deviates from established patterns
    - **REGRESSION** — behavior that worked before Phase 7 but is now broken

13. **Generate the CI verification matrix:**

    | Gate | Command | Expected | Actual | Status |
    |------|---------|----------|--------|--------|
    | C1 | `npx tsc --noEmit` | exit 0 | {{result}} | ✅/❌ |
    | C2 | `npm run lint` | exit 0 | {{result}} | ✅/❌ |
    | C3 | `npm test` | all pass | {{N}} pass, {{N}} fail | ✅/❌ |
    | C4 | `npx prettier --check src/` | exit 0 | {{result}} | ✅/❌ |

14. **Generate the issue resolution heatmap:**

    | Step | Issue | Phase | File(s) | Resolution | Tests Added | Status |
    |------|-------|-------|---------|------------|-------------|--------|
    | 1 | #98 | A | part2.ts | @see link updated | 0 | ✅/❌ |
    | 2 | #148 | A | parser.ts, data-array.ts | 27 casts removed | 0 | ✅/❌ |
    | 3 | #149 | B | part2.ts | requireObject helper | {{N}} | ✅/❌ |
    | 4 | #146 | B | part2.ts | parseBaseStream helper | {{N}} | ✅/❌ |
    | 5 | #140 | B | part2.ts | paramsSchema fallback | {{N}} | ✅/❌ |
    | 6 | #154 | C | response.ts | parseItem callback | {{N}} | ✅/❌ |
    | 7 | #155 | C | integration/*.spec.ts | Call sites updated | 0 | ✅/❌ |
    | 8 | #143 | C | geojson.ts | Null properties guard | {{N}} | ✅/❌ |
    | 9 | #144 | C | sensorml/*.ts | Explicit field extraction | {{N}} | ✅/❌ |
    | 10 | #142 | D | url_builder.ts | subPath union types | {{N}} | ✅/❌ |
    | 11 | #139 | D | url_builder.ts | Deprecate getDeploymentSystems | {{N}} | ✅/❌ |
    | 12 | #156 | D | url_builder.ts | Remove asserts (33 methods) | {{N}} | ✅/❌ |
    | 13 | #157 | D | url_builder.ts | Remove asserts (39 methods) | {{N}} | ✅/❌ |
    | 14 | #102 | D | url_builder.ts | Nested parent IDs | {{N}} | ✅/❌ |
    | 15 | #158 | D | url_builder.ts | build() + 33 methods | {{N}} | ✅/❌ |
    | 16 | #159 | D | url_builder.ts | build() + 25 methods | 0 | ✅/❌ |
    | 17 | #160 | D | url_builder.ts | build() + 29 methods (+#111) | {{N}} | ✅/❌ |
    | 18 | #150 | D | url_builder.ts | createCommands delegation | 0 | ✅/❌ |
    | 19 | #147 | E | helpers.ts | isSafeHref URL scheme guard | {{N}} | ✅/❌ |
    | 20 | #151 | F | integration/*.ts | Shared fixture factory | 0 | ✅/❌ |

15. **Include a root cause analysis** if there are new defects — explain HOW and WHY each issue was introduced

16. **Write prioritized recommendations** in three tiers:
    - **Fix Now** (before porting to `clean-pr`)
    - **Fix Before Push** (before updating PR #136)
    - **Defer** (low priority, no current impact)

### Pattern References

When evaluating Phase 7 code, compare against these established patterns:

| Pattern | Reference | Used In |
|---------|-----------|---------|
| Private helper extraction | `parseBaseStream()` in part2.ts | B2 (#146) |
| Null-guard helper | `requireObject()` in part2.ts | B1 (#149) |
| DRY wrapper delegation | `build()` in url_builder.ts | D5 (#158–#160) |
| Conditional guard in wrapper | `build()` omits assert when `id` is provided | D3/D5 |
| Defense-in-depth URL validation | `isSafeHref()` in helpers.ts | E1 (#147) |
| Test fixture centralization | `_fixtures.ts` with PADDING + factory | F1 (#151) |
| Deprecation annotation | `@deprecated` tag with migration guidance | D2 (#139) |
| Union type constraint | `CsapiSubPath` literal union for subPath | D1 (#142) |

### Report Format

Generate the report as a markdown file and save it to:
`docs/implementation/phase-{{X.Y}}-code-review.md`

Use this exact structure:

```markdown
# Phase {{X.Y}} Code Review — {{Subtitle describing scope}}

**Date:** {{YYYY-MM-DD}}
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** {{One-line description of what's being reviewed}}
**Commits:**
- `{sha}` — `{commit message}`
(list all 20 Phase 7 commits)

## Verification Status

### CI Gates

| Check | Result |
|-------|--------|
| tsc --noEmit (C1) | ✅/❌ {{result}} |
| lint (C2) | ✅/❌ {{result}} |
| test (C3) | ✅ {{N}} passing, {{N}} failing |
| prettier (C4) | ✅/❌ {{result}} |

### Diff Stats

```
git diff --stat phase-6..phase-7 -- src/
{{paste output}}
```

## Phase 7 Commit History

| Step | Commit | Issue(s) | Description |
|------|--------|----------|-------------|
| 1 | `ac889a9` | #98 | @see link precision |
| 2 | `7858a76` | #148 | 27 redundant casts removed |
| ... | ... | ... | ... |
| 20 | `85686ed` | #151 | Shared fixture factory |

## Files Reviewed

| File | Lines Changed | Issues |
|------|--------------|--------|
| src/ogc-api/csapi/url_builder.ts | +{{N}} / -{{N}} | #142, #139, #156, #157, #102, #158, #159, #160, #150 |
| ... | ... | ... |

## Overall Codebase Metrics (Cumulative)

| Category | Files | Lines Added | Lines Removed | Net | Tests Added |
|----------|-------|-------------|---------------|-----|-------------|
| Phase 7 (Code Review Cleanup) | 27 | ~1,166 | ~797 | +369 | {{N}} |
| **Total CSAPI** | **{{N}}** | — | — | **{{N}}** | **{{N}}** |

## Prior Findings Status

### [{{ID}}] {{STATUS}}: {{Title}}
{{For each finding from any previous Phase 7 review — resolved, still open, or unchanged}}

## Phase {{X.Y}} Findings — New

### [F{{N}}] {{SEVERITY}}: {{Title}}
{{Detailed finding with file references, code snippets, severity, and recommendation}}

## Issue Resolution Heatmap

| Step | Issue | Phase | Resolution | Acceptance Criteria Met | Tests | Status |
|------|-------|-------|------------|------------------------|-------|--------|
| 1 | #98 | A | @see link updated | ✅/❌ | 0 | ✅/❌ |
| ... | ... | ... | ... | ... | ... | ... |

## CI Verification Matrix

| Gate | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| C1 | `npx tsc --noEmit` | exit 0 | {{result}} | ✅/❌ |
| C2 | `npm run lint` | exit 0 | {{result}} | ✅/❌ |
| C3 | `npm test` | all pass | {{N}} pass | ✅/❌ |
| C4 | `npx prettier --check src/` | exit 0 | {{result}} | ✅/❌ |

## Code Review Finding Traceability

| Finding Doc | Issue | Severity | Resolution Status | Evidence |
|-------------|-------|----------|-------------------|----------|
| 003-pending-p1-unchecked-generic-cast-response | #141 (#154+#155) | P1 | ✅/❌ | {{cite commit + test}} |
| 004-pending-p2-subpath-no-encoding | #142 | P2 | ✅/❌ | {{cite commit + test}} |
| 007-pending-p2-properties-null-cast | #143 | P2 | ✅/❌ | {{cite commit + test}} |
| 008-pending-p2-raw-json-spread-into-typed-result | #144 | P2 | ✅/❌ | {{cite commit + test}} |
| 009-pending-p2-assert-resource-paired-pattern | #145 (#158+#159+#160) | P2 | ✅/❌ | {{cite commit + test}} |
| 010-pending-p2-datastream-controlstream-base-duplication | #146 | P2 | ✅/❌ | {{cite commit + test}} |
| 011-pending-p3-server-href-scheme-validation | #147 | P3 | ✅/❌ | {{cite commit + test}} |
| 012-pending-p3-redundant-casts-after-isrecord | #148 | P3 | ✅/❌ | {{cite commit + test}} |
| 013-pending-p3-null-guard-duplicated-5x | #149 | P3 | ✅/❌ | {{cite commit + test}} |
| 014-pending-p3-create-command-duplicate | #150 | P3 | ✅/❌ | {{cite commit + test}} |
| 015-duplicate-p3-get-command-status-inconsistent | #111 | P3 | ✅/❌ | {{cite commit}} |
| 016-pending-p3-integration-test-fixture-duplication | #151 | P3 | ✅/❌ | {{cite commit}} |
| 001-upstream-p1-path-traversal (upstream-only) | — | P1 | NOT IN SCOPE | Upstream-only |
| 002-upstream-p1-query-param-injection (upstream-only) | — | P1 | NOT IN SCOPE | Upstream-only |
| 005-pending-p2-http-no-enforcement (upstream-only) | — | P2 | NOT IN SCOPE | Upstream-only |
| 006-pending-p2-error-object-logged (upstream-only) | — | P2 | NOT IN SCOPE | Upstream-only |

## Summary

| Category | Count | Details |
|----------|-------|---------|
| Issues resolved | {{N}}/17 | {{list}} |
| Auto-resolved | {{N}} | #111 via #160 |
| New findings | {{N}} | {{summary}} |
| Regressions | {{N}} | {{summary}} |
| Pre-existing failures | {{N}} | {{summary}} |

## Recommendations

### Fix Now (before porting to clean-pr)
### Fix Before Push (before updating PR #136)
### Defer (Low Priority)

## Root Cause Analysis
{{Only if new defects found — explain how/why they were introduced}}

## Overall Assessment
{{2-3 paragraph assessment covering:
  1. Whether all 17 issues are properly resolved with evidence
  2. Whether Phase 7 introduced any regressions or new issues
  3. Whether the code is ready to port to clean-pr for PR #136 update
  4. Quality comparison: pre-Phase-7 vs post-Phase-7 codebase}}
```

Then commit the report, push, and confirm the file is at the expected path.
````

---

## Post-Review Workflow

After the review report is generated:

1. **Review the recommendations** — decide which to fix now vs defer
2. **Create a GitHub issue** for any "Fix Now" items using `docs/governance/issue-creation-prompt-template-code-review.md`
3. **Complete the fix** before porting to `clean-pr`
4. **The next code review will reaffirm** all findings from this review — nothing is forgotten

---

## Quality Gates (Non-Negotiable)

Every Phase 7 code review report MUST include:

- [ ] All CI verification commands executed and results recorded (C1–C4)
- [ ] Diff stats recorded and compared against expected
- [ ] Every prior finding reaffirmed with current status (if previous P7 review exists)
- [ ] Each of the 20 issue resolutions evaluated against its category checklist
- [ ] New findings classified with severity labels
- [ ] CI verification matrix (4 gates)
- [ ] Issue resolution heatmap (20 rows)
- [ ] Code review finding traceability table (16 findings — 12 ours + 4 upstream)
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
- **Major** = project phase (7 for Phase 7)
- **Minor** = sequential review number within Phase 7 (1, 2, 3...)

Examples:
- `phase-7.1-code-review.md` (Phase 7, first review — partial, e.g., Phase A+B only)
- `phase-7.2-code-review.md` (Phase 7, second review — comprehensive, all 20 steps)
- `phase-7.3-code-review.md` (Phase 7, third review — post-fix re-review)

---

## Reference Documents

When performing a Phase 7 code review, the reviewer should have access to:

| Document | Location | Purpose |
|----------|----------|---------|
| P7 Cleanup Plan | `docs/planning/phase-7/P7-code-review-cleanup-plan.md` | 20-step execution plan, dependency graph, issue inventory |
| P7 Scope Split Assessment | `docs/planning/phase-7/P7-scope-split-assessment.md` | Rationale for splitting #141, #100, #145 |
| Code Review Finding Docs (16) | `docs/code-review/003-*.md` through `016-*.md` | Original senior dev findings with severity, evidence, recommendations |
| Upstream Findings Report | `docs/code-review/upstream-findings-report.md` | 4 findings excluded from Phase 7 (upstream-only) |
| Deferred Enhancement | `docs/code-review/110-deferred-enhancement-link-resolution-utilities.md` | #110 — deferred, not in Phase 7 scope |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries — mandatory for all AI work |
| Phase 3 Lessons Learned | `docs/governance/phase-3-lessons-learned.md` | Lessons 1, 2, 4, 10 still active |
| Phase 2 Lessons Learned | `docs/governance/phase-2-lessons-learned.md` | General guardrails — Lessons 6-10 still active |
| CSAPI Implementation Guide | `docs/planning/csapi-implementation-guide.md` | Overall CSAPI architecture and design decisions |
| ROADMAP | `docs/planning/ROADMAP.md` | Phase definitions and sequencing |

### Phase 7 Source Files (27 files changed)

| File | Primary Issues | Category |
|------|---------------|----------|
| `src/ogc-api/csapi/url_builder.ts` | #142, #139, #156, #157, #102, #158, #159, #160, #150 | URL building (9 issues) |
| `src/ogc-api/csapi/url_builder.spec.ts` | (tests for above) | Tests |
| `src/ogc-api/csapi/formats/part2.ts` | #98, #149, #146, #140 | Parser helpers (4 issues) |
| `src/ogc-api/csapi/formats/response.ts` | #154 | Collection response parsing |
| `src/ogc-api/csapi/formats/response.spec.ts` | #154 | Tests |
| `src/ogc-api/csapi/formats/schema-response.ts` | #140 | Schema response parsing |
| `src/ogc-api/csapi/formats/schema-response.spec.ts` | #140 | Tests |
| `src/ogc-api/csapi/formats/geojson.ts` | #143 | GeoJSON extraction |
| `src/ogc-api/csapi/formats/geojson.spec.ts` | #143 | Tests |
| `src/ogc-api/csapi/formats/sensorml/physical-system.ts` | #144 | SensorML parser |
| `src/ogc-api/csapi/formats/sensorml/physical-system.spec.ts` | #144 | Tests |
| `src/ogc-api/csapi/formats/sensorml/simple-process.ts` | #144 | SensorML parser |
| `src/ogc-api/csapi/formats/sensorml/simple-process.spec.ts` | #144 | Tests |
| `src/ogc-api/csapi/formats/sensorml/aggregate-process.ts` | #144 | SensorML parser |
| `src/ogc-api/csapi/formats/sensorml/aggregate-process.spec.ts` | #144 | Tests |
| `src/ogc-api/csapi/formats/swecommon/parser.ts` | #148 | SWE Common parser |
| `src/ogc-api/csapi/formats/swecommon/data-array.ts` | #148 | SWE Common data array |
| `src/ogc-api/csapi/helpers.ts` | #147 | Link scanning helpers |
| `src/ogc-api/csapi/helpers.spec.ts` | #147 | Tests |
| `src/ogc-api/csapi/command-routing.ts` | #142 | Command routing |
| `src/ogc-api/csapi/command-routing.spec.ts` | #142 | Tests |
| `src/ogc-api/csapi/integration/_fixtures.ts` | #151 (new file) | Shared test fixtures |
| `src/ogc-api/csapi/integration/discovery.spec.ts` | #151, #155 | Integration tests |
| `src/ogc-api/csapi/integration/observation.spec.ts` | #151, #155 | Integration tests |
| `src/ogc-api/csapi/integration/command.spec.ts` | #151, #155 | Integration tests |
| `src/ogc-api/csapi/integration/navigation.spec.ts` | #151, #155 | Integration tests |
| `src/ogc-api/csapi/integration/pipeline.spec.ts` | #155 | Integration tests |

---

## Key Differences from Phase 6 Template

For reviewers familiar with the Phase 6 template, these are the substantive changes:

| Section | Phase 6 | Phase 7 |
|---------|---------|---------|
| Quality dimension categories | A–G (barrel, factory, endpoint, root exports, package.json, formatting, test migration) | A1–F1 (quick wins, parser cleanup, type safety, url_builder batch, security, test fixtures) |
| Verification gates | 5 CI (C1–C5) + 4 boundary (V1–V4) = 9 total | 4 CI (C1–C4) + diff stats = 5 total |
| Traceability | Task completion heatmap | Issue resolution heatmap + finding doc traceability matrix |
| Pattern references | `formats/index.ts` barrel, EDR factory, `package.json` exports | `build()` helper, `parseBaseStream`, `requireObject`, `isSafeHref`, `makeTestCollection` |
| Scope basis | 13 Phase 6 tasks | 20 Phase 7 steps resolving 17 issues across 6 phases |
| Review source | jahow's PR #136 review requirements | Senior developer code review (16 finding documents) |
| Boundary checks | 4 `git grep` boundary gates (V1–V4) | Not applicable — Phase 7 didn't change module boundaries |
| Export audit | 6-section barrel completeness table | Not applicable — no barrel changes |
| Recommendation tiers | "Fix Before Push" (to upstream) | "Fix Before Push" (before updating PR #136) |
