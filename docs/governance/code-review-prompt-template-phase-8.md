# Code Review Prompt Template — Phase 8

**Purpose:** Reusable prompt for triggering AI-generated code reviews during Phase 8 (Pre-Merge API-Design Refinement). Adapts the Phase 7 review template skeleton to the specific quality concerns of API-surface naming, error-type contracts, type tightening, server-interop spec conformance, and structural exposure that define Phase 8's work.

**Version:** 1.0
**Date:** April 29, 2026
**Supersedes:** Nothing — sibling to [`code-review-prompt-template-phase-7.md`](code-review-prompt-template-phase-7.md) (Phase 7), [`code-review-prompt-template-phase-6.md`](code-review-prompt-template-phase-6.md) (Phase 6), [`code-review-prompt-template-phase-5.md`](code-review-prompt-template-phase-5.md) (Phase 5), [`code-review-prompt-template-phase-3.md`](code-review-prompt-template-phase-3.md) (Phase 3), and [`code-review-prompt-template.md`](code-review-prompt-template.md) (Phase 2), which remain valid for any revisits to those phases.
**Report destination:** `docs/implementation/phase-{X.Y}-code-review.md`
**Cadence:** Per-checkpoint (A / B / C / D / final) — runs at the end of each Phase 8 roadmap phase to confirm we haven't fucked anything up.

---

## Why a Separate Template?

Phase 8 code differs fundamentally from Phase 7 code:

| Dimension          | Phase 7 (Code Review Cleanup)                                                        | Phase 8 (Pre-Merge API-Design Refinement)                                                                        |
| ------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Primary output     | Quality fixes — type safety, DRY consolidation, security hardening, test cleanup     | API-design fixes — public-surface naming, error-type contract, type tightening, structural exposure              |
| Correctness check  | "Are the review findings properly resolved? Is behavior preserved?"                  | "Are the locked design decisions implemented exactly as specified? Is the public surface coherent?"              |
| Test strategy      | Per-issue unit/integration tests + full CI suite                                     | Per-task acceptance gates (verification commands from P8-ROADMAP) + URL parity + compile-time gates              |
| Pattern reference  | `build()` private helper, `parseBaseStream` extraction, `makeTestCollection` factory | `endpoint.csapi()` entry point, `EndpointError`-only error path, `CSAPICollectionRef` value-shaped factory       |
| Validation concern | Type narrowing correctness, URL encoding, scheme validation, deduplication           | Public API coherence, naming consistency (Datastream not DataStream), error contract uniformity, link fallback   |
| Heatmap dimensions | 20 issues across 6 phases (quick wins, parsers, type safety, DRY, security, tests)   | 10 tasks across 5 phases (A=docs/typing×4, B=API surface×2, C=server-interop×1, D=structural×1, E=delivery×2)    |
| Spec references    | Senior developer code review findings (16 docs), OGC 23-002 Part 2, OGC 23-001       | Phase 8 trio (P8-contribution-goal, P8-implementation-guide, P8-ROADMAP), OGC 23-002 §16.1 (`@link` form)        |
| Risk profile       | Behavioral correctness, backward compatibility, zero public API breakage             | **Intentional public API breakage** (rename, re-privatize) — coherence over compatibility, with locked decisions |
| Re-litigation      | Findings live in finding docs                                                        | **Locked decisions in P8 trio** — review confirms implementation matches; does not relitigate                    |

The Phase 7 issue-resolution focus, 16-finding traceability matrix, and category checklists (A1–F1) do not apply. Phase 8 needs **per-task acceptance-gate verification** plus **public-surface coherence** review dimensions.

---

## When to Use

Trigger this prompt at every Phase 8 **checkpoint**, mirroring the smoke-test cadence:

1. **Checkpoint A** — Tasks A1–A4 merged on `phase-8` (docs framing, `CSAPICollectionRef`, `ReadonlySet` guard, pagination JSDoc)
2. **Checkpoint B** — Tasks B1–B2 merged (`Datastream` rename across 13 methods, `EndpointError` standardization)
3. **Checkpoint C** — Task C1 merged (`@link` fallback per OGC 23-002 §16.1)
4. **Checkpoint D** — Task D1 merged (`endpoint.csapi()` + re-privatize + value-shaped factory)
5. **Final (post-E)** — Tasks E1–E2 merged (CI gate, squash + push, PR #136 refresh) — comprehensive review of the entire Phase 8 branch before tagging @jahow

Do NOT trigger after trivial doc-only commits outside the source tree, test-only changes that don't touch acceptance-gate behavior, or housekeeping commits.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing a Phase 8 checkpoint. Replace all `{{...}}` placeholders with actual values, including the **Checkpoint** field (A / B / C / D / final).

---

## Prompt

````
Please perform a comprehensive code review of the Phase 8 work at checkpoint **{{Checkpoint: A / B / C / D / final}}**.

### Scope

**Phase:** {{Phase number, e.g., "8.1" or "8.final"}}
**Checkpoint:** {{A — post Tasks A1–A4 / B — post Tasks B1–B2 / C — post Task C1 / D — post Task D1 / final — post Tasks E1–E2}}
**Tasks completed in this checkpoint:** {{List task IDs from P8-ROADMAP and the GitHub issue numbers, e.g., "A1 (#aaa), A2 (#bbb), A3 (#ccc), A4 (#167)"}}
**Commits to review:** {{List commit SHAs, or "all commits on phase-8 since {{previous-checkpoint-tag-or-commit}}"}}
**Last review:** {{Reference the previous review doc, e.g., "docs/implementation/phase-8.A-code-review.md" or "none — first Phase 8 review"}}

### Context

Phase 8 resolves **7 code-review findings** (017, 018, 019, 021, 022, 023, 024) and **2 server-interop bugs** (#166 `@link` fallback, #167 pagination contract) across **10 execution tasks** organized into **5 phases (A–E)**:

- **Phase A — Documentation & Typing (low risk, no behavior change):**
  - A1 (017): URL-builder framing in module/file/class JSDoc + README
  - A2 (022): Extract `CSAPICollectionRef` type from `OgcApiCollectionInfo`
  - A3 (023): Tighten `availableResources` to `ReadonlySet<CSAPIResourceType>`
  - A4 (#167): Pagination contract JSDoc on every list method
- **Phase B — API Surface (intentional public-API breakage):**
  - B1 (019): `DataStream` → `Datastream` rename across 13 public methods (URLs unchanged)
  - B2 (021): `EndpointError`-only error contract from validators
- **Phase C — Server Interop (parser change, additive):**
  - C1 (#166): `@link` object-form fallback in Part 2 cross-reference fields per OGC 23-002 §16.1
- **Phase D — Structural (coordinated multi-finding):**
  - D1 (018+024): `endpoint.csapi(collectionId)` public entry point + re-privatize `root` and `getCollectionDocument` + value-shaped standalone `createCSAPIBuilder` factory
- **Phase E — Delivery:**
  - E1: CI gate + patch generation
  - E2: Squash + push to `clean-pr` + PR #136 refresh

**All design decisions are LOCKED in the Phase 8 trio.** This review confirms the implementation matches the locked decisions; it does not relitigate them. If a review observation makes the reviewer want to revisit a locked decision, file a new P8-F finding with severity and ownership and surface it.

### Review Instructions

1. **Read the Phase 8 trio FIRST** — these documents lock the decisions this review checks against:
   - `docs/planning/phase-8/P8-contribution-goal-and-definition.md` (goal, scope, locked decisions §3)
   - `docs/planning/phase-8/P8-implementation-guide.md` (per-task execution detail)
   - `docs/planning/phase-8/P8-ROADMAP.md` (per-task acceptance gates — these are the verification commands this review runs)

2. **Review Lessons Learned** — read both governance documents:
   - `docs/governance/phase-3-lessons-learned.md` — Key checks still active:
     - Lesson 1: Does any new code introduce an architectural layer without upstream precedent?
     - Lesson 2: Postel's Law — never gate extraction on validation
     - Lesson 4: Are there parallel systems doing the same thing?
     - Lesson 10: Do type names collide with JS/TS built-ins?
   - `docs/governance/phase-2-lessons-learned.md` — General guardrails (Lessons 6-10 still active)

3. **Review the original Phase 8 finding documents** (7 docs + 2 issue threads):
   - `docs/code-review/017-*.md` → Task A1 (URL-builder framing)
   - `docs/code-review/022-*.md` → Task A2 (`CSAPICollectionRef`)
   - `docs/code-review/023-*.md` → Task A3 (`ReadonlySet` guard)
   - `docs/code-review/019-*.md` → Task B1 (`Datastream` rename)
   - `docs/code-review/021-*.md` → Task B2 (`EndpointError` standardization)
   - `docs/code-review/018-*.md` + `docs/code-review/024-*.md` → Task D1 (coordinated)
   - GitHub Issue #166 → Task C1 (`@link` fallback)
   - GitHub Issue #167 → Task A4 (pagination JSDoc)

4. **Run CI verification gates — the EXACT 5 upstream QA commands** (mirroring [`.github/workflows/qa.yml`](../../.github/workflows/qa.yml), which is identical to camptocamp's upstream QA workflow). These are the gates the upstream PR #136 will be measured against. Execute in this order and record results:
   - `npm run format:check` (C1 — Prettier formatting; **this is the one that bit us last time** — see [`docs/upstream-pr-preparation/03-lessons-learned-ci-formatting.md`](../upstream-pr-preparation/03-lessons-learned-ci-formatting.md))
   - `npm run typecheck` (C2 — TypeScript type check)
   - `npm run lint` (C3 — ESLint)
   - `npm run test:browser` (C4 — Jest browser tests)
   - `npm run test:node` (C5 — Jest Node tests)

   **Then verify the QA workflow itself ran green on the checkpoint HEAD commit:**
   - Open <https://github.com/OS4CSAPI/ogc-client-CSAPI_2/actions/workflows/qa.yml>
   - Confirm the most recent run on the `phase-8` branch (or, at Checkpoint final, on `clean-pr`) is green for the commit being reviewed
   - Record the run URL and conclusion in the report's CI Gates table
   - If the workflow has not yet been triggered for the HEAD commit, dispatch it manually via the **Run workflow** button (workflow_dispatch is enabled) and wait for completion before continuing the review

5. **Run per-task acceptance gates** — execute the verification commands defined in `P8-ROADMAP.md` for every task in the active checkpoint. Record exact command output. These are the **acceptance gates** — if any fail, the checkpoint is not done. (See Section "Per-Task Acceptance Gates" below for the canonical command list.)

6. **Read all changed files** — identify every file modified since the last review commit. For each file, note:
   - What changed (lines added/modified/removed)
   - Whether the change matches the locked decision in the Phase 8 trio (it must — this review confirms exact match, not creative interpretation)

7. **Verify Phase 8 diff stats** — run and record:
   ```bash
   git diff --stat phase-7..phase-8 -- src/
   ```
   {{Expected size depends on checkpoint:
     - Post-A: small — mostly JSDoc + 1 new type + 1 type tightening
     - Post-B: medium — 13 method renames + N validator throw replacements
     - Post-C: small — parser additions for @link fallback (additive only)
     - Post-D: small — 1 new method + 2 access modifier changes + 1 factory rewrite
     - Post-E: same as final pre-squash diff vs phase-7
   }}
   Significant deviation warrants investigation — Phase 8 is intentionally tight in scope.

8. **Reaffirm ALL prior findings** — if a previous Phase 8 review exists (e.g., reviewing post-B after post-A was reviewed), read it and check each finding:
   - For each RESOLVED finding: confirm it's still resolved, cite evidence
   - For each STILL OPEN finding: check if it was addressed, update status
   - For each UNCHANGED finding (not-our-code): reaffirm unchanged status

9. **Evaluate each Phase 8 task against its locked acceptance criteria:**

   #### Phase A — Documentation & Typing (CHECKPOINT A / final)

   **Task A1 (Finding 017) — URL-builder framing:**
   - [ ] `src/ogc-api/csapi/index.ts` — module docblock present with the 5-step worked example (instantiate `OgcApiEndpoint` → `await endpoint.csapi(collectionId)` → call URL builder method → fetch → parse)
   - [ ] `src/ogc-api/csapi/factory.ts` — `createCSAPIBuilder` JSDoc cross-references the module docblock and is unmistakably framed as a URL-builder factory
   - [ ] `src/ogc-api/csapi/url_builder.ts` — class-level JSDoc on `CSAPIQueryBuilder` reinforces the URL-builder framing (not "client", not "endpoint")
   - [ ] `README.md` — "Connected Systems — making a request" section present and consistent with the module docblock
   - [ ] No code changes — documentation only

   **Task A2 (Finding 022) — `CSAPICollectionRef` extraction:**
   - [ ] New named export `CSAPICollectionRef` defined in the appropriate types module
   - [ ] Type contains only the fields `CSAPIQueryBuilder` actually reads (NOT a re-export of `OgcApiCollectionInfo`)
   - [ ] `git grep -n "OgcApiCollectionInfo" -- src/ogc-api/csapi/url_builder.ts` returns 0 matches
   - [ ] `CSAPIQueryBuilder` constructor and `factory.ts` use the new type
   - [ ] Structural compatibility preserved — passing an `OgcApiCollectionInfo` value still compiles
   - [ ] No runtime behavior change

   **Task A3 (Finding 023) — `ReadonlySet<CSAPIResourceType>`:**
   - [ ] `availableResources` property type is `ReadonlySet<CSAPIResourceType>` (not `Set<CSAPIResourceType>`)
   - [ ] Mutation attempts (`builder.availableResources.add(...)`, `.delete(...)`, `.clear(...)`) are TypeScript compile errors
   - [ ] Internal construction in `factory.ts` still works (Set construction → ReadonlySet upcast)
   - [ ] Existing tests still pass

   **Task A4 (Issue #167) — Pagination JSDoc:**
   - [ ] Module/class-level docblock has a "Pagination" anchor section describing default page size, `next` link contract, server-default deferral
   - [ ] EVERY `get*` list method's JSDoc has an `@remarks` block (or equivalent) referencing the Pagination contract
   - [ ] Spot-check: `getSystems`, `getDatastreams` (post-B1 name), `getControlStreams`, `getCommands`, `getProcedures`, `getSamplingFeatures`, `getDeployments`, `getProperties`, `getObservations`
   - [ ] Cross-references are accurate (mention OGC 23-001 list-pattern + cs-go default discovery)

   #### Phase B — API Surface (CHECKPOINT B / final)

   **Task B1 (Finding 019) — `DataStream` → `Datastream` rename:**
   - [ ] All 13 affected public methods renamed (per P8-implementation-guide §B1):
     - `getDataStreams` → `getDatastreams`
     - `getDataStream` → `getDatastream`
     - `getDataStreamSchema` → `getDatastreamSchema`
     - `getSystemDataStreams` → `getSystemDatastreams`
     - `createDataStream` → `createDatastream`
     - `updateDataStream` → `updateDatastream`
     - `deleteDataStream` → `deleteDatastream`
     - `replaceDataStream` → `replaceDatastream`
     - (and remaining 5 per implementation guide)
   - [ ] `git grep -n "DataStream" -- 'src/ogc-api/csapi/'` returns **0 matches** (modulo `Datastream` — note case difference)
   - [ ] `git grep -n "DataStream" -- 'README.md' 'app/' 'docs/code-review/' 'docs/planning/phase-8/'` updated as appropriate
   - [ ] **URL parity:** for at least 3 spot-checked methods, the URL string produced is byte-identical to the pre-rename URL (URLs do not change; only method names change). Confirm in `url_builder.spec.ts`.
   - [ ] No `@deprecated` aliases retained — clean break per locked decision
   - [ ] `npm run typecheck && npx jest src/ogc-api/csapi/url_builder.spec.ts` both green
   - [ ] All call sites in tests, app/, and demos updated

   **Task B2 (Finding 021) — `EndpointError` standardization:**
   - [ ] `git grep -n "throw new Error\|throw new TypeError\|throw new RangeError" -- src/ogc-api/csapi/` returns **0 matches** (excluding test files where intentional)
   - [ ] All validators (`validateLimit`, `validateBbox`, `validateDatetime`, `parseProperty`, `assertResourceAvailable`, etc.) throw `EndpointError`
   - [ ] Error messages preserve callsite information (caller name, parameter name where applicable)
   - [ ] **No CSAPI-specific subclass introduced** — `EndpointError` only, per locked decision §3
   - [ ] Unit tests cover at least 3 validator paths each throwing `EndpointError` (not generic `Error`)
   - [ ] Existing error-message test assertions still pass (text content unchanged where possible)

   #### Phase C — Server Interop (CHECKPOINT C / final)

   **Task C1 (Issue #166) — `@link` object-form fallback:**
   - [ ] Cross-reference resolution helper updated to accept the `@link` object form per OGC 23-002 §16.1
   - [ ] Helper extracts the ID from the **last URL segment** of `@link.href`
   - [ ] Applied to all 5 cross-reference fields: `system`, `datastream`, `foi` (a.k.a. `samplingFeature`), `controlstream`, `command`
   - [ ] **`@id` precedence preserved** — when both `@id` and `@link` are present, `@id` wins (per locked decision)
   - [ ] Affected parsers updated: `parseDatastream`, `parseControlStream`, `parseObservation`, `parseCommand`, `parseCommandStatus`
   - [ ] Unit tests cover: `@id` only (existing behavior), `@link` only (new behavior), both present (`@id` wins), neither (existing error path)
   - [ ] Live cs-go fixture added to test suite OR live-server smoke test gates this (see post-C smoke test report)
   - [ ] Additive only — no existing parser behavior regresses

   #### Phase D — Structural (CHECKPOINT D / final)

   **Task D1 (Findings 018 + 024 coordinated) — `endpoint.csapi()` + re-privatize + value-shaped factory:**
   - [ ] New public method `OgcApiEndpoint.prototype.csapi(collectionId: string): Promise<CSAPIQueryBuilder>` exists
   - [ ] Method internally calls the value-shaped `createCSAPIBuilder` with the collection ref + resource URL map
   - [ ] **Re-privatization confirmed:** `endpoint.root` and `endpoint.getCollectionDocument(...)` are no longer publicly accessible (TypeScript `private` keyword or `#` private). Compile-time test: `endpoint.root` and `endpoint.getCollectionDocument('foo')` produce TS errors in a scratch script.
   - [ ] `git grep -n "isCollectionInfo" -- src/ogc-api/csapi/` returns **0 matches** (the upstream cast is gone)
   - [ ] **Standalone `createCSAPIBuilder` is value-shaped:** signature is `(collection: CSAPICollectionRef, resourceUrls: ReadonlyMap<CSAPIResourceType, string>): CSAPIQueryBuilder` — synchronous, no `await`, no `OgcApiEndpoint` parameter
   - [ ] A builder constructed via `endpoint.csapi(id)` and a builder constructed via standalone `createCSAPIBuilder(ref, urls)` from literal values produce **identical URL output** for at least 3 spot-checked methods
   - [ ] Error contract: `endpoint.csapi('non-csapi-collection')` throws `EndpointError` with message indicating CSAPI conformance is missing
   - [ ] Error contract: `endpoint.csapi('does-not-exist')` throws `EndpointError` wrapping the upstream lookup failure (per Task B2 + D1 contract)
   - [ ] All existing CSAPI integration tests updated to use `endpoint.csapi()` instead of `endpoint.root` + factory dance
   - [ ] No public re-export breakage — all previously-public CSAPI types still exported

   #### Phase E — Delivery (CHECKPOINT final)

   **Task E1 — CI gate + patch generation:**
   - [ ] CI on `phase-8` is green (all 4 C-gates + per-task acceptance gates)
   - [ ] `git diff phase-7..phase-8 -- src/` produces a clean patch with no extraneous changes
   - [ ] Patch line count is consistent with the cumulative locked scope (not bloated with refactor opportunities)

   **Task E2 — Squash + push + PR #136 refresh:**
   - [ ] Squashed commit on `clean-pr` has a descriptive subject + bullet body covering all 10 tasks
   - [ ] Force-push to `clean-pr` succeeded
   - [ ] PR #136 description updated with Phase 8 summary
   - [ ] @jahow tagged for re-review

10. **Cross-cutting quality checks** — apply to all changed files:

    - **Locked-decision fidelity:** Every change exactly matches the corresponding decision in P8-contribution-goal-and-definition.md §3 and P8-implementation-guide.md. No silent re-decisions, no creative additions.
    - **Public API coherence:** After Phase 8, every public CSAPI surface uses the same vocabulary (`Datastream` not `DataStream`, `EndpointError` not bare `Error`, `endpoint.csapi()` not `endpoint.root` + manual factory).
    - **Minimal diff principle:** Changes are limited to what each task requires — no opportunistic refactoring outside the trio's locked scope. Phase 8 is intentionally tight.
    - **JSDoc quality:** New types (`CSAPICollectionRef`), new methods (`endpoint.csapi`), and renamed methods retain or improve JSDoc completeness with `@param`, `@returns`, `@throws EndpointError`, `@example`, `@remarks` (pagination section), `@see` cross-refs as appropriate
    - **Error message clarity:** `EndpointError` messages from validators include validator name, parameter name, and the offending value where safe to log
    - **Test coverage:** Every behavioral change has corresponding test additions/updates. Documentation-only tasks (A1, A4) need no new tests but their JSDoc presence is still asserted.
    - **Import hygiene:** No circular imports; `import type` used for type-only references; `CSAPICollectionRef` exported from a stable barrel
    - **Consistency:** New code follows patterns already established in the repo (Phase 7's `build()` helper, error-handling conventions, etc.)
    - **Backward compatibility note:** Phase 8 INTENTIONALLY breaks public surface (B1 rename, D1 re-privatize). This is by design and locked. The review confirms breakage is **only** where locked, and ergonomic on-ramps (`endpoint.csapi()`) are present so the break is net-positive.

11. **Verify upstream-only findings are untouched** — confirm these are NOT modified (carry-forward from Phase 7):
    - Finding 001 (path traversal in `itemId`) — upstream-only
    - Finding 002 (query param injection via `encodeURI`) — upstream-only
    - Finding 005 (`http://` accepted without warning) — upstream-only
    - Finding 006 (full error object logged) — upstream-only

12. **Verify no Phase 7 fixes regressed** — Phase 7 closed 17 issues. Phase 8 must not regress any of them. Spot-check at least:
    - Issue #147 (`isSafeHref` URL-scheme guard) — `scanCsapiLinks` still rejects `javascript:` etc.
    - Issue #142 (`subPath` union-type encoding) — still type-safe and encoded
    - Issue #144 (SensorML field extraction) — no raw spread re-introduced
    - Issue #145 (`build()` helper / `assertResourceAvailable` removal) — Phase 8 B2 changes the throw type but does NOT re-introduce the paired pattern

13. **Classify every finding** using these severity labels:
    - **BUG** — incorrect behavior, wrong output, runtime error
    - **DESIGN** — architectural concern, coherence gap, locked-decision deviation
    - **GAP** — missing test, incomplete acceptance gate, JSDoc absence where required
    - **POSITIVE** — something done well that should be maintained
    - **INFORMATIONAL** — worth noting but no action needed
    - **CONSISTENCY** — follows or deviates from established patterns
    - **REGRESSION** — behavior that worked before Phase 8 but is now broken (including Phase 7 fixes)
    - **LOCKED-DECISION-DEVIATION** — implementation diverges from the P8 trio's locked decision; requires either revert-to-spec or a P8-F finding to formally re-open the decision

14. **Generate the CI verification matrix** — must mirror the upstream QA workflow exactly:

    | Gate | Command | Expected | Actual | Status |
    |------|---------|----------|--------|--------|
    | C1 | `npm run format:check` | exit 0 | {{result}} | ✅/❌ |
    | C2 | `npm run typecheck` | exit 0 | {{result}} | ✅/❌ |
    | C3 | `npm run lint` | exit 0 | {{result}} | ✅/❌ |
    | C4 | `npm run test:browser` | all pass | {{N}} pass, {{N}} fail | ✅/❌ |
    | C5 | `npm run test:node` | all pass | {{N}} pass, {{N}} fail | ✅/❌ |
    | QA workflow | `.github/workflows/qa.yml` run on HEAD commit | conclusion: success | {{run URL}} | ✅/❌ |

15. **Generate the per-task acceptance-gate matrix** (the canonical Phase 8 quality gate, drawn from `P8-ROADMAP.md`):

    | Task | Phase | Gate Command | Expected | Actual | Status |
    |------|-------|--------------|----------|--------|--------|
    | A1 | A | manual review of 4 surfaces | docs framing present | {{result}} | ✅/❌ |
    | A2 | A | `git grep "OgcApiCollectionInfo" -- src/ogc-api/csapi/url_builder.ts` | 0 matches | {{result}} | ✅/❌ |
    | A3 | A | scratch: `builder.availableResources.add(...)` | TS compile error | {{result}} | ✅/❌ |
    | A4 | A | manual JSDoc audit of 9 list methods | every method has @remarks pagination | {{result}} | ✅/❌ |
    | B1 | B | `git grep "DataStream" -- 'src/ogc-api/csapi/'` | 0 matches | {{result}} | ✅/❌ |
    | B1 | B | URL parity (3 spot checks) | byte-identical to pre-rename | {{result}} | ✅/❌ |
    | B2 | B | `git grep "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` | 0 matches | {{result}} | ✅/❌ |
    | B2 | B | 3 validators × `instanceof EndpointError` | all true | {{result}} | ✅/❌ |
    | C1 | C | parser unit tests for `@link` form | green | {{result}} | ✅/❌ |
    | C1 | C | `@id` precedence test | green | {{result}} | ✅/❌ |
    | D1 | D | `endpoint.csapi()` happy path × 4 servers (smoke test) | builds correct URLs | {{result}} | ✅/❌ |
    | D1 | D | `endpoint.root` access | TS compile error | {{result}} | ✅/❌ |
    | D1 | D | `git grep "isCollectionInfo" -- src/ogc-api/csapi/` | 0 matches | {{result}} | ✅/❌ |
    | D1 | D | standalone factory URL parity | matches `endpoint.csapi()` URLs | {{result}} | ✅/❌ |
    | E1 | E | `git diff phase-7..phase-8 -- src/` size | within expected band | {{result}} | ✅/❌ |
    | E2 | E | `clean-pr` HEAD has Phase 8 squash | yes | {{result}} | ✅/❌ |

    (Include only rows for tasks completed in or before the active checkpoint.)

16. **Generate the task resolution heatmap:**

    | Task | Finding(s)/Issue | Phase | File(s) | Resolution | Tests | Status |
    |------|------------------|-------|---------|------------|-------|--------|
    | A1 | 017 | A | csapi/index.ts, factory.ts, url_builder.ts, README.md | URL-builder framing docs | 0 | ✅/❌ |
    | A2 | 022 | A | csapi types module, url_builder.ts, factory.ts | `CSAPICollectionRef` extracted | {{N}} | ✅/❌ |
    | A3 | 023 | A | url_builder.ts | `ReadonlySet<CSAPIResourceType>` | {{N}} | ✅/❌ |
    | A4 | #167 | A | url_builder.ts | Pagination JSDoc on every list method | 0 | ✅/❌ |
    | B1 | 019 | B | url_builder.ts (+ tests, README, app) | 13 method renames | {{N}} | ✅/❌ |
    | B2 | 021 | B | url_builder.ts, validators across csapi/ | `EndpointError`-only | {{N}} | ✅/❌ |
    | C1 | #166 | C | csapi/formats/part2.ts (+ helpers) | `@link` fallback | {{N}} | ✅/❌ |
    | D1 | 018 + 024 | D | OgcApiEndpoint, csapi/factory.ts, url_builder.ts | `endpoint.csapi()` + re-private + value-shaped factory | {{N}} | ✅/❌ |
    | E1 | — | E | CI config / patch verification | green CI + clean diff | 0 | ✅/❌ |
    | E2 | — | E | clean-pr branch | squashed commit + PR refresh | 0 | ✅/❌ |

17. **Include a root cause analysis** if there are new defects — explain HOW and WHY each was introduced (especially any `LOCKED-DECISION-DEVIATION` finding)

18. **Write prioritized recommendations** in three tiers:
    - **Fix Now** (before advancing to the next checkpoint)
    - **Fix Before Push** (before the E2 squash to `clean-pr`)
    - **Defer** (low priority, no current impact — may become a Phase 9 candidate)

### Pattern References

When evaluating Phase 8 code, compare against these established patterns:

| Pattern | Reference | Used In |
|---------|-----------|---------|
| Public entry-point method on host class | `OgcApiEndpoint.prototype.csapi()` | D1 (018) |
| Value-shaped factory (no async, no host object) | `createCSAPIBuilder(ref, urls)` | D1 (024) |
| Value-shaped collection ref type | `CSAPICollectionRef` (subset of `OgcApiCollectionInfo`) | A2 (022) |
| Read-only public collection | `ReadonlySet<CSAPIResourceType>` | A3 (023) |
| Single-error-type contract | `EndpointError` from all validator paths | B2 (021) |
| Spec-conformant fallback parsing | `@link` object form per OGC 23-002 §16.1 | C1 (#166) |
| Naming consistency with spec | `Datastream` (matches OGC tag) | B1 (019) |
| Documented pagination contract | `@remarks` block on every list method | A4 (#167) |
| URL-builder framing in module docblock | 5-step worked example | A1 (017) |
| Carry-forward from Phase 7 | `build()` helper, `parseBaseStream`, `requireObject`, `isSafeHref` | unchanged in Phase 8 |

### Report Format

Generate the report as a markdown file and save it to:
`docs/implementation/phase-{{X.Y}}-code-review.md`

Suggested filename per checkpoint:
- Checkpoint A → `phase-8.A-code-review.md`
- Checkpoint B → `phase-8.B-code-review.md`
- Checkpoint C → `phase-8.C-code-review.md`
- Checkpoint D → `phase-8.D-code-review.md`
- Checkpoint final → `phase-8.final-code-review.md`

Use this exact structure:

```markdown
# Phase {{X.Y}} Code Review — {{Subtitle describing checkpoint scope}}

**Date:** {{YYYY-MM-DD}}
**Reviewer:** GitHub Copilot ({{model}})
**Checkpoint:** {{A / B / C / D / final}}
**Scope:** {{One-line description of what's being reviewed}}
**Phase 8 trio anchor:** [P8-contribution-goal](../planning/phase-8/P8-contribution-goal-and-definition.md), [P8-implementation-guide](../planning/phase-8/P8-implementation-guide.md), [P8-ROADMAP](../planning/phase-8/P8-ROADMAP.md)
**Commits:**
- `{sha}` — `{commit message}`
(list all Phase 8 commits in this checkpoint scope)

## Verification Status

### CI Gates (mirror of upstream `.github/workflows/qa.yml`)

| Check | Command | Result |
|-------|---------|--------|
| format:check (C1) | `npm run format:check` | ✅/❌ {{result}} |
| typecheck (C2) | `npm run typecheck` | ✅/❌ {{result}} |
| lint (C3) | `npm run lint` | ✅/❌ {{result}} |
| test:browser (C4) | `npm run test:browser` | ✅ {{N}} passing, {{N}} failing |
| test:node (C5) | `npm run test:node` | ✅ {{N}} passing, {{N}} failing |
| **QA workflow run** | <https://github.com/OS4CSAPI/ogc-client-CSAPI_2/actions/workflows/qa.yml> | ✅/❌ {{run URL}} |

### Per-Task Acceptance Gates

(See "Per-Task Acceptance Gate Matrix" section below)

### Diff Stats

```
git diff --stat {{previous-checkpoint-anchor}}..phase-8 -- src/
{{paste output}}
```

## Phase 8 Commit History (this checkpoint)

| Task | Commit | Issue/Finding | Description |
|------|--------|---------------|-------------|
| A1 | `{sha}` | 017 | URL-builder framing |
| A2 | `{sha}` | 022 | CSAPICollectionRef extraction |
| ... | ... | ... | ... |

## Files Reviewed

| File | Lines Changed | Tasks |
|------|--------------|-------|
| src/ogc-api/csapi/url_builder.ts | +{{N}} / -{{N}} | A3, A4, B1, B2 |
| src/ogc-api/csapi/index.ts | +{{N}} / -{{N}} | A1 |
| ... | ... | ... |

## Locked-Decision Fidelity

| Decision | P8 Trio Source | Implemented As | Match? |
|----------|----------------|----------------|--------|
| EndpointError-only error path (no CSAPIError subclass) | P8-goal §3 | {{describe}} | ✅/❌ |
| Datastream rename (no @deprecated aliases) | P8-goal §3 | {{describe}} | ✅/❌ |
| @id precedence over @link | P8-impl §C1 | {{describe}} | ✅/❌ |
| Value-shaped createCSAPIBuilder (no async, no endpoint param) | P8-impl §D1 | {{describe}} | ✅/❌ |
| Re-privatize root + getCollectionDocument | P8-impl §D1 | {{describe}} | ✅/❌ |

## Prior Findings Status

### [{{ID}}] {{STATUS}}: {{Title}}
{{For each finding from any previous Phase 8 review — resolved, still open, or unchanged.
 Also reaffirm Phase 7 fixes are not regressed.}}

## Phase {{X.Y}} Findings — New

### [P8-F{{N}}] {{SEVERITY}}: {{Title}}
{{Detailed finding with file references, code snippets, severity, and recommendation.
 Use LOCKED-DECISION-DEVIATION severity if implementation diverges from the trio.}}

## Per-Task Acceptance Gate Matrix

| Task | Phase | Gate Command | Expected | Actual | Status |
|------|-------|--------------|----------|--------|--------|
| ... | ... | ... | ... | ... | ... |

## Task Resolution Heatmap

| Task | Finding(s)/Issue | Phase | Resolution | Acceptance Gate Met | Tests | Status |
|------|------------------|-------|------------|---------------------|-------|--------|
| ... | ... | ... | ... | ... | ... | ... |

## CI Verification Matrix (mirrors upstream `.github/workflows/qa.yml`)

| Gate | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| C1 | `npm run format:check` | exit 0 | {{result}} | ✅/❌ |
| C2 | `npm run typecheck` | exit 0 | {{result}} | ✅/❌ |
| C3 | `npm run lint` | exit 0 | {{result}} | ✅/❌ |
| C4 | `npm run test:browser` | all pass | {{N}} pass | ✅/❌ |
| C5 | `npm run test:node` | all pass | {{N}} pass | ✅/❌ |
| QA workflow | <https://github.com/OS4CSAPI/ogc-client-CSAPI_2/actions/workflows/qa.yml> | conclusion: success | {{run URL}} | ✅/❌ |

## Phase 8 Finding Traceability

| Finding Doc / Issue | Task | Severity | Resolution Status | Evidence |
|---------------------|------|----------|-------------------|----------|
| 017-*.md | A1 | P3 | ✅/❌ | {{cite commit + surface}} |
| 022-*.md | A2 | P3 | ✅/❌ | {{cite commit + grep result}} |
| 023-*.md | A3 | P3 | ✅/❌ | {{cite commit + compile-error proof}} |
| 019-*.md | B1 | P2 | ✅/❌ | {{cite commit + grep result + URL parity}} |
| 021-*.md | B2 | P2 | ✅/❌ | {{cite commit + grep result + EndpointError tests}} |
| 018-*.md + 024-*.md | D1 | P2 | ✅/❌ | {{cite commit + endpoint.csapi() proof + re-private proof}} |
| Issue #166 | C1 | P2 | ✅/❌ | {{cite commit + parser tests + smoke test report}} |
| Issue #167 | A4 | P3 | ✅/❌ | {{cite commit + JSDoc audit}} |
| 001-upstream-p1-path-traversal | — | P1 | NOT IN SCOPE | Upstream-only |
| 002-upstream-p1-query-param-injection | — | P1 | NOT IN SCOPE | Upstream-only |
| 005-pending-p2-http-no-enforcement | — | P2 | NOT IN SCOPE | Upstream-only |
| 006-pending-p2-error-object-logged | — | P2 | NOT IN SCOPE | Upstream-only |

## Carry-Forward: Phase 7 Fixes Not Regressed

| Phase 7 Issue | Spot-Check | Result |
|---------------|------------|--------|
| #147 (isSafeHref scheme guard) | scanCsapiLinks still rejects javascript: etc. | ✅/❌ |
| #142 (subPath union encoding) | subPath still type-safe + encoded | ✅/❌ |
| #144 (SensorML field extraction) | no raw spread re-introduced | ✅/❌ |
| #145 (build() helper) | paired-pattern not re-introduced | ✅/❌ |

## Summary

| Category | Count | Details |
|----------|-------|---------|
| Tasks completed in this checkpoint | {{N}}/10 | {{list}} |
| Findings resolved | {{N}} | {{list}} |
| New review findings | {{N}} | {{summary}} |
| Locked-decision deviations | {{N}} | {{summary; ideally 0}} |
| Regressions | {{N}} | {{summary; ideally 0}} |
| Phase 7 fixes still intact | ✅ / ⚠️ | {{summary}} |

## Recommendations

### Fix Now (before advancing to the next checkpoint)
### Fix Before Push (before E2 squash to clean-pr)
### Defer (Low Priority — Phase 9 candidates)

## Root Cause Analysis
{{Only if new defects or LOCKED-DECISION-DEVIATION findings — explain how/why}}

## Overall Assessment
{{2–3 paragraph assessment covering:
  1. Whether all checkpoint tasks are properly resolved with locked-decision fidelity
  2. Whether Phase 8 introduced any regressions to Phase 7 fixes or upstream behavior
  3. Whether the code is ready to advance to the next checkpoint (or, at final, to E2 squash + PR #136 refresh)
  4. Public API coherence comparison: pre-Phase-8 vs post-Phase-8 surface}}
```

Then commit the report, push, and confirm the file is at the expected path.
````

---

## Post-Review Workflow

After the review report is generated:

1. **Review the recommendations** — decide which to fix now vs defer
2. **Create a GitHub issue** for any "Fix Now" items using [`docs/governance/issue-creation-prompt-template-phase-8.md`](issue-creation-prompt-template-phase-8.md) (NOT the v1.0 general template — Phase 8 issues use the Phase 8 variant)
3. **Complete the fix** before advancing to the next checkpoint
4. **The next code review will reaffirm** all findings from this review — nothing is forgotten
5. **At Checkpoint final:** the post-final code review is the final quality gate before E2 squash to `clean-pr` and PR #136 refresh

---

## Quality Gates (Non-Negotiable)

Every Phase 8 code review report MUST include:

- [ ] All 5 CI verification commands executed and results recorded (C1–C5) — these are the EXACT upstream `qa.yml` commands
- [ ] QA workflow run URL recorded with conclusion (must be `success` for the HEAD commit being reviewed)
- [ ] All per-task acceptance-gate commands from `P8-ROADMAP.md` executed and results recorded (for tasks in scope of the active checkpoint)
- [ ] Locked-Decision Fidelity table with one row per locked decision in P8 trio
- [ ] Diff stats recorded and compared against expected band for the checkpoint
- [ ] Every prior Phase 8 finding reaffirmed with current status (if previous P8 review exists)
- [ ] Each completed task evaluated against its category checklist
- [ ] New findings classified with severity labels (including LOCKED-DECISION-DEVIATION where applicable)
- [ ] CI verification matrix (4 gates)
- [ ] Per-task acceptance-gate matrix (rows for tasks in scope)
- [ ] Task resolution heatmap (10 rows for final checkpoint; subset for earlier checkpoints)
- [ ] Phase 8 finding traceability table (7 findings + 2 issues + 4 upstream-only)
- [ ] Carry-forward Phase 7 fix spot-check (4+ items)
- [ ] Prioritized recommendations in three tiers
- [ ] Overall assessment paragraph

---

## Naming Convention

Reports follow the same naming pattern as prior phases:

```
docs/implementation/phase-{major}.{checkpoint}-code-review.md
```

Where:

- **major** = `8`
- **checkpoint** = `A`, `B`, `C`, `D`, or `final`

Examples:

- `phase-8.A-code-review.md` (Phase 8, Checkpoint A — Tasks A1–A4)
- `phase-8.B-code-review.md` (Phase 8, Checkpoint B — Tasks B1–B2)
- `phase-8.C-code-review.md` (Phase 8, Checkpoint C — Task C1)
- `phase-8.D-code-review.md` (Phase 8, Checkpoint D — Task D1)
- `phase-8.final-code-review.md` (Phase 8, post-E — comprehensive)
- `phase-8.final-rev2-code-review.md` (Phase 8, post-final after fixes — re-review)

---

## Reference Documents

When performing a Phase 8 code review, the reviewer should have access to:

| Document                              | Location                                                                                            | Purpose                                                                               |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **P8 Contribution Goal & Definition** | `docs/planning/phase-8/P8-contribution-goal-and-definition.md`                                      | **Goal, scope, locked decisions §3** — primary anchor                                 |
| **P8 Implementation Guide**           | `docs/planning/phase-8/P8-implementation-guide.md`                                                  | **Per-task execution detail** — primary anchor                                        |
| **P8 ROADMAP**                        | `docs/planning/phase-8/P8-ROADMAP.md`                                                               | **Per-task acceptance gates** — verification commands this review runs                |
| Phase 8 Smoke Test Template           | `docs/governance/smoke-test-prompt-template-phase-8.md`                                             | Companion live-server validation template (run before this review at each checkpoint) |
| Phase 8 Issue Template                | `docs/governance/issue-creation-prompt-template-phase-8.md`                                         | Used to file any new "Fix Now" findings                                               |
| Code Review Finding Docs (7)          | `docs/code-review/017-*.md`, `018-*.md`, `019-*.md`, `021-*.md`, `022-*.md`, `023-*.md`, `024-*.md` | Original Phase 8 findings with severity, evidence, recommendations                    |
| Issues #166 #167                      | GitHub                                                                                              | cs-go integration findings driving Tasks C1 and A4                                    |
| Upstream Findings Report              | `docs/code-review/upstream-findings-report.md`                                                      | 4 findings excluded from Phase 8 (upstream-only)                                      |
| AI Operational Constraints            | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`                                                     | Behavioral boundaries — mandatory for all AI work                                     |
| Phase 3 Lessons Learned               | `docs/governance/phase-3-lessons-learned.md`                                                        | Lessons 1, 2, 4, 10 still active                                                      |
| Phase 2 Lessons Learned               | `docs/governance/phase-2-lessons-learned.md`                                                        | General guardrails — Lessons 6-10 still active                                        |
| CSAPI Implementation Guide            | `docs/planning/csapi-implementation-guide.md`                                                       | Overall CSAPI architecture and design decisions                                       |
| ROADMAP                               | `docs/planning/ROADMAP.md`                                                                          | Phase definitions and sequencing                                                      |

### Phase 8 Source Files (expected change set)

(Concrete file list emerges as tasks land. Below is the expected scope; the actual review records the real file list per checkpoint.)

| File                                                  | Likely Tasks       | Category                                       |
| ----------------------------------------------------- | ------------------ | ---------------------------------------------- |
| `src/ogc-api/csapi/index.ts`                          | A1                 | Module docblock                                |
| `src/ogc-api/csapi/factory.ts`                        | A1, D1             | Factory + framing JSDoc                        |
| `src/ogc-api/csapi/url_builder.ts`                    | A1, A3, A4, B1, B2 | URL builder (5 tasks touch this)               |
| `src/ogc-api/csapi/url_builder.spec.ts`               | A3, A4, B1, B2     | Tests (compile + behavior)                     |
| `src/ogc-api/csapi/types.ts` (or wherever types live) | A2                 | `CSAPICollectionRef`                           |
| `src/ogc-api/csapi/formats/part2.ts`                  | C1                 | `@link` fallback                               |
| `src/ogc-api/csapi/formats/part2.spec.ts`             | C1                 | Parser tests                                   |
| `src/ogc-api/endpoint.ts` (`OgcApiEndpoint`)          | D1                 | New `csapi()` method + re-private              |
| `src/ogc-api/endpoint.spec.ts`                        | D1                 | Tests                                          |
| `src/ogc-api/csapi/integration/*.spec.ts`             | B1, D1             | Updated call sites                             |
| `README.md`                                           | A1                 | "Connected Systems — making a request" section |
| `app/`                                                | B1                 | Demo updates for renamed methods               |

---

## Key Differences from Phase 7 Template

For reviewers familiar with the Phase 7 template, these are the substantive changes:

| Section                      | Phase 7                                                                                     | Phase 8                                                                                                                                     |
| ---------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Quality dimension categories | A1–F1 (quick wins, parser cleanup, type safety, url_builder batch, security, test fixtures) | A1–A4 / B1–B2 / C1 / D1 / E1–E2 (10 tasks across 5 phases per P8-ROADMAP)                                                                   |
| Cadence                      | Once at end of phase                                                                        | **Per-checkpoint** (A / B / C / D / final) — same cadence as the smoke test                                                                 |
| Verification gates           | 4 CI (C1–C4) + diff stats                                                                   | **5 CI (C1–C5) mirroring upstream `qa.yml` exactly** + QA workflow run check + per-task acceptance-gate matrix from P8-ROADMAP + diff stats |
| Traceability                 | 20-row issue resolution heatmap + 16-finding doc traceability                               | 10-row task resolution heatmap + 7-finding + 2-issue traceability + Phase 7 carry-forward spot-check                                        |
| Re-litigation                | Implicit                                                                                    | **Explicit non-relitigation policy** — P8 trio locks decisions; review confirms exact match                                                 |
| New severity label           | n/a                                                                                         | **LOCKED-DECISION-DEVIATION** — implementation diverges from P8 trio                                                                        |
| Pattern references           | `build()` helper, `parseBaseStream`, `requireObject`, `isSafeHref`, `makeTestCollection`    | `endpoint.csapi()`, value-shaped `createCSAPIBuilder`, `CSAPICollectionRef`, `EndpointError`-only                                           |
| Scope basis                  | 20 Phase 7 steps resolving 17 issues                                                        | 10 Phase 8 tasks resolving 7 findings + 2 issues                                                                                            |
| Review source                | Senior developer code review (16 finding documents)                                         | Phase 8 trio (3 docs) + 7 finding docs + Issues #166/#167                                                                                   |
| Issue-creation template      | `issue-creation-prompt-template-code-review.md`                                             | **`issue-creation-prompt-template-phase-8.md`** (Phase 8 variant)                                                                           |
| Backward-compatibility lens  | "Zero public API breakage"                                                                  | **"Intentional public API breakage where locked, ergonomic on-ramps elsewhere"**                                                            |
| Recommendation tiers         | "Fix Before Push" (before updating PR #136)                                                 | "Fix Now" (next checkpoint) / "Fix Before Push" (E2) / "Defer" (Phase 9)                                                                    |
