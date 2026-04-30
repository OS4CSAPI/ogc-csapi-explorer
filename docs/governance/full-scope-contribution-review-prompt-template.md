# Full-Scope Contribution Review Prompt Template

**Purpose:** One-time-use prompt for a comprehensive review of the **entire CSAPI contribution** (Phases 1–7) before updating PR #136 for upstream submission to camptocamp/ogc-client. This is NOT a phase-specific review — it evaluates the contribution as a whole.

**Version:** 1.0
**Date:** March 7, 2026
**Complements:** Phase-specific review templates remain available for targeted reviews:

- `code-review-prompt-template.md` (Phase 2)
- `code-review-prompt-template-phase-3.md` (Phase 3)
- `code-review-prompt-template-phase-5.md` (Phase 5)
- `code-review-prompt-template-phase-6.md` (Phase 6)
- `code-review-prompt-template-phase-7.md` (Phase 7)
  **Report destination:** `docs/implementation/full-scope-contribution-review.md`

---

## When to Use

This template should be used **exactly once** — as the final gate review before porting Phase 7 changes to the `clean-pr` branch and pushing the updated PR #136 to camptocamp/ogc-client.

**Prerequisites before triggering:**

1. All Phase 7 issues are closed (Steps 1–20, Issues #98–#151)
2. `phase-7` branch passes all CI gates (`tsc`, `lint`, `test`, `prettier`)
3. Phase 7 review (`code-review-prompt-template-phase-7.md`) has been executed and all "Fix Now" items resolved
4. No open issues remain against the CSAPI contribution

---

## Why a Separate Template?

Phase-specific templates evaluate whether individual phase work is correct. This template evaluates whether the **complete contribution is ready for upstream submission**:

| Dimension            | Phase-Specific Reviews              | Full-Scope Review                                                       |
| -------------------- | ----------------------------------- | ----------------------------------------------------------------------- |
| Scope                | One phase at a time (20-50 files)   | Entire fork diff vs upstream (60 files, 125 commits)                    |
| Question answered    | "Is this phase's work correct?"     | "Is this contribution mergeable and professionally complete?"           |
| Audience             | Internal QA                         | Upstream maintainer (jahow)                                             |
| Success criteria     | Tests pass, code quality acceptable | PR #136 worth merging — clean diff, complete coverage, no debris        |
| Prior review history | None or 1-2 per phase               | ~30 prior code review reports across all phases                         |
| Risk concern         | Phase-specific regressions          | Cross-phase inconsistencies, accumulated technical debt, stale patterns |

---

## Contribution Summary

This review covers the **complete CSAPI implementation** contributed to camptocamp/ogc-client:

**What we built:**

- Connected Systems API (CSAPI) support implementing OGC API - Connected Systems Parts 1 & 2
- 9 resource types: Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands
- URL builder with 87 public methods for all CRUD/query operations
- SensorML 3.0 parser (Physical System, Simple Process, Aggregate Process)
- SWE Common 3.0 parser (DataRecord, DataArray, components, 3 encodings)
- GeoJSON extensions for CSAPI resource types
- Collection response with typed element parsing
- Schema response parsing (command/tasking schemas)
- Property definition parsing
- Conformance detection and factory method integration
- Barrel file with complete public API exports

**Integration footprint in upstream files:**

- `src/ogc-api/endpoint.ts` — factory method, conformance getters (~35 lines)
- `src/ogc-api/endpoint.spec.ts` — integration tests (~60 lines)
- `src/ogc-api/info.ts` — conformance checking (~12 lines)
- `src/index.ts` — root re-exports (~17 lines, now removed in Phase 6 — barrel-only export)

**Diff stats (origin/main → phase-7):**

- 60 source files changed
- ~4,691 lines added / ~2,297 lines removed
- 5 new files created, 55 existing files modified
- 4 upstream files touched (`endpoint.ts`, `endpoint.spec.ts`, `info.ts`, `index.ts`)
- 13 fixture files added (354 lines)

**Development history:**

- 7 phases (Phases 1–7)
- 125 commits on development branch
- ~30 code review reports in `docs/implementation/`
- ~20 smoke test reports

---

## How to Use

Copy the prompt below and paste it into the conversation. No placeholders — this is a one-shot full sweep.

---

## Prompt

````
Please perform a full-scope code review of the entire CSAPI contribution.

### Scope

This reviews the COMPLETE diff between `origin/main` (upstream camptocamp/ogc-client baseline) and `phase-7` (our latest development branch). This is the final gate review before updating PR #136.

### Context

Refer to:
- `docs/planning/contribution-goal-and-definition.md` — what the contribution is
- `docs/planning/csapi-implementation-guide.md` — complete architectural guide (v7.0)
- `docs/planning/ROADMAP.md` — phase definitions and task breakdown (v3.4)
- `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` — behavioral constraints
- `docs/governance/phase-3-lessons-learned.md` — critical lessons (Postel's Law, upstream audit, etc.)
- `docs/governance/phase-2-lessons-learned.md` — general guardrails

### Prior Review History

~30 prior code review reports exist in `docs/implementation/`. Key ones to reference:
- `phase-1-code-review.md` — Phase 1 foundational review
- `phase-2.9-code-review.md` — Phase 2 final review
- `phase-3.17-code-review.md` — Phase 3 final review
- `phase-5.6-code-review.md` — Phase 5 final review
- `phase-6.4-code-review.md` — Phase 6 final review
- `phase-6-architecture-verification.md` — Phase 6 architecture gate
- Phase 7 review (if exists) — `phase-7.X-code-review.md`
- `final-project-code-review.md` / `project-completion-report.md` — prior completion assessments

Read the most recent review from each phase to understand the current state of known findings.

### Review Instructions

Perform the review in this order. Each section is mandatory.

---

#### Part 1: CI Verification (Mandatory First Step)

Execute all gates and record results before reading any code:

| Gate | Command | Expected |
|------|---------|----------|
| C1 | `npx tsc --noEmit` | exit 0 |
| C2 | `npm run lint` | exit 0 |
| C3 | `npm test` | all tests pass (record count) |
| C4 | `npx prettier --check src/` | exit 0 |

Record exact results. If any gate fails, note it prominently.

---

#### Part 2: Diff Inventory

Generate and record the complete diff stats:

```bash
# Full contribution diff
git diff --stat origin/main..phase-7 -- src/

# New files only
git diff --name-status origin/main..phase-7 -- src/ | grep '^A'

# Modified upstream files
git diff --name-only origin/main..phase-7 -- src/ | grep -v csapi

# Fixture files
git diff --stat origin/main..phase-7 -- fixtures/
```

Expected:
- ~60 source files changed
- ~4,691 insertions / ~2,297 deletions
- 5 new files (factory.ts, factory.spec.ts, _parse-utils.ts, index.ts, _fixtures.ts)
- 4 upstream files modified (endpoint.ts, endpoint.spec.ts, info.ts, index.ts)
- 13 fixture files

Flag any unexpected files or significant deviation from expected counts.

---

#### Part 3: Module Boundary Audit

Verify the CSAPI module is properly isolated:

1. **Import direction check** — no file in `src/ogc-api/csapi/` should import from outside the `csapi/` directory EXCEPT:
   - `../../shared/` (shared utilities)
   - `../model.js` (OGC API collection types)
   - `../endpoint.js` (type-only imports if any)
   - Standard library / `geojson` package

2. **Export completeness** — verify `src/ogc-api/csapi/index.ts` exports everything consumers need:
   - [ ] `CSAPIQueryBuilder` class
   - [ ] All Part 1 resource types (System, Deployment, Procedure, SamplingFeature, Property)
   - [ ] All Part 2 resource types (Datastream, Observation, ControlStream, Command, CommandStatus)
   - [ ] Query option types
   - [ ] All parser functions
   - [ ] Factory function (`createCSAPIQueryBuilder`)
   - [ ] `parseCollectionResponse` and related response utilities

3. **No CSAPI imports outside module** — verify no file outside `src/ogc-api/csapi/` directly imports from a CSAPI sub-module (all access should go through the barrel `index.ts` or the factory):
   ```bash
   git grep "from.*csapi/" -- src/ | grep -v "src/ogc-api/csapi/" | grep -v "csapi/index"
   ```

4. **Upstream file minimality** — for each of the 4 upstream files we modified, verify our changes are minimal and well-contained:
   - `endpoint.ts` — only factory method + conformance getters
   - `endpoint.spec.ts` — only tests for the above
   - `info.ts` — only conformance checking function
   - `index.ts` — only re-exports (or removal of re-exports in Phase 6)

---

#### Part 4: Public API Surface Audit

Review what consumers of the library actually receive:

1. **Entry points** — how does a consumer access CSAPI functionality?
   - `endpoint.csapi(collectionId)` → returns `CSAPIQueryBuilder`
   - `endpoint.hasConnectedSystems` getter
   - `endpoint.csapiCollections` getter
   - Direct import from `@camptocamp/ogc-client` barrel exports

2. **CSAPIQueryBuilder public methods** — verify all 87 methods are present and correctly typed:
   - Systems: getSystems, getSystem, createSystem, updateSystem, deleteSystem, getSystemDeployments, getSystemProcedure, getSystemSamplingFeatures, getSystemDataStreams, getSystemControlStreams, getSystemHistory, getSystemHistoryEntry, getSystemMembers, getSystemMember, createSystemMember, getDeploymentSystems (deprecated)
   - Deployments: getDeployments, getDeployment, createDeployment, updateDeployment, deleteDeployment, getDeploymentSystems (deprecated), getDeploymentHistory, getDeploymentHistoryEntry, getDeploymentSubsystems
   - Procedures: getProcedures, getProcedure, createProcedure, updateProcedure, deleteProcedure, getProcedureHistory, getProcedureHistoryEntry, getProcedureImplementations
   - SamplingFeatures: getSamplingFeatures, getSamplingFeature, createSamplingFeature, updateSamplingFeature, deleteSamplingFeature, getSamplingFeatureMembership, getSamplingFeatureHistory, getSamplingFeatureHistoryEntry
   - Properties: getProperties, getProperty, createProperty, updateProperty, deleteProperty, getPropertyDefinition
   - DataStreams: getDataStreams, getDataStream, createDataStream, updateDataStream, deleteDataStream, getDataStreamSchema, getDataStreamObservations, getDataStreamObservation, createDataStreamObservation, updateDataStreamObservation, deleteDataStreamObservation
   - Observations: getObservations, getObservation, createObservation, updateObservation, deleteObservation, getObservationSchema, getObservationResult, getObservationResultSchema
   - ControlStreams: getControlStreams, getControlStream, createControlStream, updateControlStream, deleteControlStream, getControlStreamSchema, getControlStreamCommands, getControlStreamCommand, createControlStreamCommand, updateControlStreamCommand, deleteControlStreamCommand
   - Commands: getCommands, getCommand, createCommand, createCommands, updateCommand, deleteCommand, getCommandStatus, getCommandResult, checkCommandFeasibility, getCommandStatusHistory

3. **Type exports** — verify all public types are properly exported with JSDoc:
   - Resource types (System, Deployment, Procedure, etc.)
   - Query option types (QueryOptions, SystemQueryOptions, etc.)
   - Response types (CollectionResponse, etc.)
   - SensorML types (PhysicalSystem, SimpleProcess, AggregateProcess, etc.)
   - SWE Common types (DataRecord, DataArray, etc.)

4. **No internal leakage** — verify private helpers are NOT exported:
   - `build()`, `buildResourceUrl()`, `buildQueryString()`, `assertResourceAvailable()` — should be private
   - `requireObject()`, `parseBaseStream()` — should be private/non-exported
   - `isSafeHref()` — should be non-exported
   - `PADDING`, internal fixture helpers — should not be in barrel

---

#### Part 5: OGC Specification Conformance Spot-Check

This is NOT a full spec compliance audit. Spot-check key areas:

1. **Resource type coverage** — verify all 9 resource types from OGC 23-001 (Part 1) and OGC 23-002 (Part 2) have URL builder methods
2. **Query parameter support** — verify `limit`, `offset`, `bbox`, `datetime`, `phenomenonTime`, `resultTime`, `sortBy`, `sortOrder` are supported where specified
3. **Conformance class detection** — verify `info.ts` checks for correct CSAPI conformance URIs
4. **SensorML parsing** — verify Physical System, Simple Process, Aggregate Process parsers handle the fields specified in SensorML 3.0
5. **SWE Common parsing** — verify DataRecord, DataArray, component types, and encoding support match SWE Common 3.0

---

#### Part 6: Cross-Phase Consistency Audit

Check that patterns established early are still followed:

1. **Error handling** — is `EndpointError` used consistently across all phases?
2. **URL encoding** — does every method that builds URLs use the same encoding approach?
3. **Naming conventions** — do method names follow `get`/`create`/`update`/`delete` + resource name pattern consistently?
4. **JSDoc** — do all public methods have JSDoc with `@param`, `@returns`, `@throws`?
5. **Test structure** — do all test files follow the same `describe`/`it` nesting pattern?
6. **Type naming** — no collisions with JS/TS built-ins (Lesson 10 from Phase 3)?
7. **Import style** — `import type` used for type-only imports?
8. **Postel's Law** — parsers extract what they can rather than rejecting non-conformant data?

---

#### Part 7: Test Coverage Assessment

Evaluate the test suite comprehensiveness:

1. **Unit test inventory** — list every `.spec.ts` file, what it tests, approximate test count
2. **Integration test inventory** — list all integration spec files, what workflows they cover
3. **Coverage gaps** — identify any production code files without corresponding test files
4. **Edge case coverage** — do tests cover: null inputs, empty arrays, missing fields, malformed JSON, server errors, network failures?
5. **Fixture completeness** — are there fixtures for all resource types? List any missing fixture types
6. **Pre-existing test failures** — document any known failing tests and why they fail (are they pre-existing or introduced by us?)

---

#### Part 8: PR Readiness Assessment

Evaluate whether PR #136 is ready to update:

1. **Diff cleanliness** — is the diff between `origin/main` and our contribution clean? No debug code, no TODO comments, no leftover planning artifacts?
2. **Documentation debris** — verify no `docs/` files would be included in the PR (only `src/` and `fixtures/`)
3. **Commit message quality** — evaluate whether a single squashed commit message adequately describes the contribution
4. **jahow's review comments** — check PR #136 for any original review comments that haven't been addressed
5. **Breaking changes** — confirm zero breaking changes to existing public API
6. **Bundle size** — any concern about contribution size relative to existing library?

---

#### Part 9: Upstream-Only Findings Status

Verify the 4 upstream-only security findings are documented but NOT fixed in our branch (they require separate upstream PRs):

| Finding | Doc | Status Check |
|---------|-----|-------------|
| 001 — Path traversal in `itemId` | `docs/code-review/001-upstream-p1-path-traversal-item-id.md` | Verify we did NOT modify the affected upstream code |
| 002 — Query param injection via `encodeURI` | `docs/code-review/002-upstream-p1-query-param-injection.md` | Verify we did NOT modify the affected upstream code |
| 005 — `http://` accepted without warning | `docs/code-review/005-pending-p2-http-no-enforcement.md` | Verify we did NOT modify the affected upstream code |
| 006 — Full error object logged | `docs/code-review/006-pending-p2-error-object-logged.md` | Verify we did NOT modify the affected upstream code |

---

#### Part 10: Known Issues and Deferred Work

Document what is NOT included in this contribution and why:

1. **Issue #110** — `@link` / `@id` resolution utilities — deferred enhancement, separate PR
2. **Upstream security findings** (001, 002, 005, 006) — require upstream coordination
3. **Any pre-existing test failures** — document cause and whether they affect contribution quality
4. **Any "Fix Before Push" items from Phase 7 review** — verify they're resolved

---

### Report Format

Generate the report as a markdown file and save to:
`docs/implementation/full-scope-contribution-review.md`

Use this structure:

```markdown
# Full-Scope Contribution Review

**Date:** {{YYYY-MM-DD}}
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** Complete CSAPI contribution (Phases 1–7) — PR #136 readiness gate
**Diff:** origin/main → phase-7 (125 commits, 60 files, +4,691 / -2,297 lines)

## Executive Summary
{{3-5 paragraph overall assessment:
  1. Is the contribution complete and correct?
  2. Is the code quality professional and consistent?
  3. Is it ready for upstream submission?
  4. Key strengths and concerns
  5. Final recommendation: READY / NOT READY / READY WITH CONDITIONS}}

## Part 1: CI Verification

| Gate | Command | Expected | Actual | Status |
|------|---------|----------|--------|--------|
| C1 | `npx tsc --noEmit` | exit 0 | {{result}} | ✅/❌ |
| C2 | `npm run lint` | exit 0 | {{result}} | ✅/❌ |
| C3 | `npm test` | all pass | {{N}} pass, {{N}} fail | ✅/❌ |
| C4 | `npx prettier --check src/` | exit 0 | {{result}} | ✅/❌ |

## Part 2: Diff Inventory

### Source Files
```
{{git diff --stat output}}
```

### New Files Created
{{list with purpose}}

### Upstream Files Modified
{{list with change description and line count}}

### Fixture Files
{{list}}

## Part 3: Module Boundary Audit
{{Results of all 4 boundary checks}}

## Part 4: Public API Surface Audit
{{Method inventory, type exports, internal leakage check}}

## Part 5: OGC Specification Conformance
{{Spot-check results}}

## Part 6: Cross-Phase Consistency
{{Pattern consistency findings}}

## Part 7: Test Coverage Assessment

### Unit Test Inventory
| File | Tests | Coverage Area |
|------|-------|--------------|
| {{file}} | {{N}} | {{description}} |

### Integration Test Inventory
| File | Tests | Workflow |
|------|-------|---------|
| {{file}} | {{N}} | {{description}} |

### Coverage Gaps
{{Any production files without tests}}

### Pre-Existing Test Failures
{{Document known failures}}

## Part 8: PR Readiness Assessment
{{Diff cleanliness, documentation debris, commit message, review comments, breaking changes}}

## Part 9: Upstream-Only Findings
{{Status of 4 upstream-only findings}}

## Part 10: Known Issues and Deferred Work
{{What's NOT included and why}}

## Findings

### [F{{N}}] {{SEVERITY}}: {{Title}}
**File:** {{path}}
**Phase:** {{which phase introduced this}}
**Impact:** {{who/what is affected}}
**Evidence:** {{code snippet or grep result}}
**Recommendation:** {{what to do}}

## Cumulative Metrics

| Metric | Count |
|--------|-------|
| Source files (production) | {{N}} |
| Source files (test) | {{N}} |
| Total lines added | {{N}} |
| Total lines removed | {{N}} |
| Net lines | {{N}} |
| Public methods (CSAPIQueryBuilder) | 87 |
| Public type exports | {{N}} |
| Parser functions | {{N}} |
| Fixture files | {{N}} |
| Total test count | {{N}} |
| Commits (development) | 125 |
| Phases | 7 |
| Issues resolved | {{N}} |
| Code review reports | ~30 |
| Smoke test reports | ~20 |

## Recommendations

### Fix Now (before porting to clean-pr)
{{Critical items that must be resolved}}

### Fix Before Push (before updating PR #136)
{{Important items for PR quality}}

### Defer (post-merge or separate PR)
{{Low-priority items or out-of-scope work}}

## Final Verdict

**Recommendation:** {{READY / NOT READY / READY WITH CONDITIONS}}

{{Detailed justification with evidence from each part of the review}}
```

Then commit the report, push, and confirm the file is at the expected path.
````

---

## Quality Gates (Non-Negotiable)

Every full-scope contribution review MUST include:

- [ ] All CI verification commands executed and results recorded (C1–C4)
- [ ] Complete diff inventory with file counts matching expectations
- [ ] Module boundary audit (import direction, export completeness, no internal leakage)
- [ ] Public API surface audit (all 87 methods, all type exports)
- [ ] OGC spec conformance spot-check (9 resource types, query params, conformance URIs)
- [ ] Cross-phase consistency audit (error handling, naming, JSDoc, test structure)
- [ ] Test coverage assessment with gap analysis
- [ ] PR readiness assessment (diff cleanliness, no debug code, no docs in PR)
- [ ] Upstream-only findings confirmation (4 findings NOT in our diff)
- [ ] Known issues and deferred work documented
- [ ] Cumulative metrics table
- [ ] Prioritized recommendations in three tiers
- [ ] Final verdict: READY / NOT READY / READY WITH CONDITIONS

---

## Reference Documents

| Document                   | Location                                                 | Purpose                                     |
| -------------------------- | -------------------------------------------------------- | ------------------------------------------- |
| Contribution Goal          | `docs/planning/contribution-goal-and-definition.md`      | What the contribution is                    |
| Implementation Guide       | `docs/planning/csapi-implementation-guide.md`            | Complete architectural guide (v7.0)         |
| ROADMAP                    | `docs/planning/ROADMAP.md`                               | Phase definitions and task breakdown (v3.4) |
| P7 Cleanup Plan            | `docs/planning/phase-7/P7-code-review-cleanup-plan.md`   | Phase 7 execution plan                      |
| AI Constraints             | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`          | Behavioral boundaries                       |
| Phase 2 Lessons            | `docs/governance/phase-2-lessons-learned.md`             | General guardrails                          |
| Phase 3 Lessons            | `docs/governance/phase-3-lessons-learned.md`             | Parser-specific lessons                     |
| Code Review Findings (16)  | `docs/code-review/003-*.md` through `016-*.md`           | Senior dev review findings                  |
| Upstream Findings          | `docs/code-review/upstream-findings-report.md`           | 4 upstream-only findings                    |
| Phase 7 Review Template    | `docs/governance/code-review-prompt-template-phase-7.md` | Phase 7-specific review                     |
| Prior Review Reports (~30) | `docs/implementation/phase-*.md`                         | All prior phase reviews                     |
| Prior Smoke Tests (~20)    | `docs/implementation/live-server-smoke-test-*.md`        | All prior smoke tests                       |
