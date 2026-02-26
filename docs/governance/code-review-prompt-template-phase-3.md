# Code Review Prompt Template — Phase 3

**Purpose:** Reusable prompt for triggering AI-generated code reviews during Phase 3 (Format Handling). Adapts the Phase 2 review template to the distinct quality concerns of parser/format handler code vs. URL-builder code.

**Version:** 1.0  
**Date:** February 14, 2026  
**Supersedes:** Nothing — sibling to `code-review-prompt-template.md` (Phase 2), which remains valid for any Phase 2 revisits.  
**Report destination:** `docs/implementation/phase-{X.Y}-code-review.md`

---

## Why a Separate Template?

Phase 3 code differs fundamentally from Phase 2 code:

| Dimension          | Phase 2 (URL Builder)                       | Phase 3 (Format Handlers)                                          |
| ------------------ | ------------------------------------------- | ------------------------------------------------------------------ |
| Primary output     | URL strings                                 | Typed objects from raw JSON/XML                                    |
| Correctness check  | "Is the URL right?"                         | "Does the parser produce the right typed output?"                  |
| Test strategy      | Exact `toBe()` URL assertions               | Fixture-based input → typed output assertions                      |
| Pattern reference  | Procedures/SamplingFeatures gold standard   | Varies per component (see below)                                   |
| Validation concern | `assertResourceAvailable()` on every method | Input validation before parsing (null, wrong type, missing fields) |
| Heatmap dimensions | Query parameter coverage                    | Parser behavior coverage                                           |
| Spec references    | OGC API Part 1/Part 2 endpoint sections     | SWE Common 3.0, SensorML 3.0, GeoJSON encoding rules               |

The Phase 2 test checklist (Lesson 1) would produce false positives if applied to parser code — every item would be "N/A" and real gaps would go undetected.

---

## When to Use

Trigger this prompt after any of these Phase 3 milestones:

1. **A format handler issue is completed** (e.g., Issue #14 GeoJSON Handler Extensions)
2. **A parser component is completed** (e.g., SWE Common Types, SensorML Simple Process Parser)
3. **A fix or cleanup issue for Phase 3 code is completed**
4. **Multiple related Phase 3 issues are completed** in a single session (batch review)
5. **Before starting Phase 4** (gate review for all of Phase 3)

Do NOT trigger after trivial doc-only commits or non-code changes.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a code review of the work completed since the last review.

### Scope

**Phase:** {{Phase number, e.g., "3.1"}}
**Issues completed:** {{List issue numbers and titles, e.g., "#14 — GeoJSON Handler Extensions"}}
**Commits to review:** {{List commit SHAs or say "all commits since {last review commit SHA}"}}
**Last review:** {{Reference the previous review doc, e.g., "docs/implementation/phase-2.9-code-review.md"}}

### Review Instructions

1. **Review Phase 3 Lessons Learned** — read `docs/governance/phase-3-lessons-learned.md` before evaluating code. Key checks:
   - Lesson 1: Does any new code introduce an architectural layer without upstream precedent?
   - Lesson 2: Does extraction depend on validation? (It must not.)
   - Lesson 4: Are there parallel systems doing the same thing?
   - Lesson 10: Do type names collide with JS/TS built-ins?
   - Lesson 12: Is the code technically correct but should not exist in a client library?

2. **Run verification gates** — execute all four and record results:
   - `npx tsc --noEmit` (must be clean)
   - `npx jest "src/ogc-api/csapi"` (record pass count — must include ALL prior tests + new tests)
   - `npx jest "src/ogc-api/endpoint.spec"` (record pass count, note pre-existing failures)
   - `npx jest "src/ogc-api/csapi/formats"` (record pass count for format-specific tests only)

3. **Read all changed files** — identify every file modified since the last review commit. For each file, note:
   - What changed (lines added/modified/removed)
   - Whether the change follows the established pattern for its component type (see Pattern References below)

4. **Reaffirm ALL prior findings** — read the previous review doc and check each open finding:
   - For each RESOLVED finding: confirm it's still resolved, cite evidence
   - For each STILL OPEN finding: check if it was addressed, update status
   - For each UNCHANGED finding (not-our-code): reaffirm unchanged status

5. **Evaluate new code against these quality dimensions:**

   - **Correctness:** Does the function produce the correct typed output from valid input? Does it handle the spec-defined variants (e.g., compact CURIE vs full URI, array vs object format)?

   - **Test thoroughness:** Apply the Phase 3 test checklist (see below — choose the appropriate category for the component being reviewed):

     **Category A — Utility/Extension modules** (geojson.ts, format-detector, constants):
     - [ ] Every public function tested with valid input producing expected output
     - [ ] Every public function tested with invalid/malformed input (returns error, undefined, or throws as documented)
     - [ ] Edge cases: null, undefined, empty string, wrong type
     - [ ] All spec-defined variants covered (e.g., both `sosa:Sensor` and `http://www.w3.org/ns/sosa/Sensor`)
     - [ ] If function returns a classification/type: all branches tested (every recognized type + unrecognized → null/false)
     - [ ] If function validates: valid input → no errors, each individual constraint violation → specific error message

     **Category B — Type definition modules** (swecommon/types.ts, sensorml/types.ts):
     - [ ] Type definitions compile without errors (`tsc --noEmit` gate)
     - [ ] Union types discriminate correctly (TypeScript narrowing test)
     - [ ] Interface compatibility: a well-formed object satisfies the interface
     - [ ] Required vs optional properties: object missing optionals still satisfies, object missing required does not
     - [ ] Cross-module type references resolve (e.g., SensorML type referencing SWE Common type)

     **Category C — Parser modules** (sensorml/*.ts, swecommon/*.ts parsers):
     - [ ] Valid fixture → correctly typed output with all properties mapped
     - [ ] Minimal valid fixture → output with optional fields absent/undefined
     - [ ] Malformed input → clear error (throws or returns error structure)
     - [ ] Missing required fields → specific error message identifying the field
     - [ ] Nested/recursive structures parsed correctly (if applicable)
     - [ ] Type discrimination: parser selects correct sub-parser based on input discriminator
     - [ ] Encoding handling: each supported encoding tested (JSON, Text, Binary — if applicable)
     - [ ] Round-trip fidelity: parsed output contains all semantically meaningful data from input

     **Category D — Validator extensions** (validator.ts):
     - [ ] Valid input passes validation (empty error array)
     - [ ] Each individual constraint violation produces a specific, identifiable error message
     - [ ] Multiple simultaneous violations all reported (not short-circuiting)
     - [ ] Cross-reference validation: broken links detected, valid links pass
     - [ ] Part 1 vs Part 2 validation rules applied to correct resource types

   - **Consistency:** Does new code follow the established pattern for its component type?

     | Component Type | Pattern Reference (Gold Standard) |
     |---------------|----------------------------------|
     | GeoJSON handler | `src/shared/mime-type.ts` (small utility module) |
     | Format detector | Existing format detector in `src/ogc-api/` |
     | Validator | Existing validation patterns in `src/ogc-api/` |
     | SWE Common types | `src/ogc-api/csapi/model.ts` (interface + const patterns) |
     | SensorML types | SWE Common types (once established) |
     | Parsers (all) | First parser completed becomes the reference for subsequent parsers |
     | Index/barrel files | `src/ogc-api/csapi/formats/index.ts` pattern |

   - **JSDoc quality:** Params, returns, throws, examples, @see spec links
   - **Spec compliance:** Do @see links point to correct spec sections?

     | Component | Expected Spec References |
     |-----------|------------------------|
     | GeoJSON handler | OGC API 23-001 (Part 1) GeoJSON encoding sections |
     | SWE Common | OGC SWE Common 3.0 (OGC 08-094r2) |
     | SensorML | OGC SensorML 3.0 (OGC 12-000r2) |
     | Validator | OGC API 23-001 / 23-002 required property tables |
     | Format detector | IANA media type registry + OGC media type conventions |

   - **Exports:** Are new types/functions exported from the appropriate barrel file (`formats/index.ts`, `src/index.ts`)?
   - **Input validation:** Does every public function guard against null/undefined/wrong-type input before processing?

6. **Classify every finding** using these severity labels:
   - **BUG** — incorrect behavior, wrong output, runtime error
   - **DESIGN** — architectural concern, DRY violation, type safety issue
   - **GAP** — missing test coverage, missing export, incomplete implementation
   - **POSITIVE** — something done well that should be maintained
   - **INFORMATIONAL** — worth noting but no action needed
   - **CONSISTENCY** — follows or deviates from established patterns

7. **Generate the test quality heatmap** — update the table showing coverage across ALL Phase 3 components (not just new ones), using these dimensions:

   **For utility/extension modules (Category A):**

   | Dimension | Description |
   |-----------|-------------|
   | Valid input → correct output | Happy path for each public function |
   | Invalid input → rejection | Malformed, null, undefined, wrong type |
   | All spec variants | Compact CURIE, full URI, array format, object format, etc. |
   | All classification branches | Every recognized type + unrecognized fallback |
   | Validation error specificity | Each constraint produces identifiable error message |
   | Edge cases | Empty strings, boundary values, mixed valid/invalid |

   **For parser modules (Category C):**

   | Dimension | Description |
   |-----------|-------------|
   | Fixture → typed output | Valid fixture produces correct typed result |
   | Minimal fixture | Only required fields populated |
   | Malformed input rejection | Clear error on bad input |
   | Missing required fields | Named field in error message |
   | Nested structures | Recursive/hierarchical parsing |
   | Type discrimination | Correct sub-parser selected |
   | Encoding variants | JSON, Text, Binary (if applicable) |
   | Error messages actionable | Error text identifies what went wrong and where |

8. **Include a root cause analysis** if there are new defects — explain HOW and WHY each issue was introduced, following the pattern from Phase 2.2 review

9. **Write prioritized recommendations** in three tiers:
   - **Fix Now** (before next coding issue)
   - **Fix Before Phase 4** (before integration testing begins)
   - **Defer** (low priority, no current impact)

10. **Check smoke test finding integration** — for each Phase 3 task, verify that relevant smoke test findings have been addressed:

   | Finding | Relevant Phase 3 Task | What to Check |
   |---------|----------------------|---------------|
   | F4 (validTime array format) | GeoJSON handler | `parseValidTime` handles `["ISO", "now"]` |
   | F33 (commandFormat vs observationFormat) | SWE Common parser | Both schema variants handled |
   | F34 (Commands fallback routing) | Validator/GeoJSON | Dual-path resolution documented/implemented |
   | F35 (Cancel rejected by OSH) | Validator | 400 on cancel handled gracefully |
   | F36 (id filter ignored on nested commands) | Validator | JSDoc documents limitation |
   | F37 (result 404 for fire-and-forget) | Validator | 404 on /result returns null, not throw |
   | F38 (command@id cross-reference) | GeoJSON/Validator | `command@id` in cross-reference registry |
   | F39 (commands use standard envelope) | GeoJSON/Parser | Single `parseCollectionResponse` handles all types |

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

| Check | Result |
|-------|--------|
| tsc --noEmit | ✅/❌ {{result}} |
| CSAPI unit tests (all) | ✅ {{N}} passing, {{N}} suites |
| CSAPI format tests | ✅ {{N}} passing, {{N}} suites |
| Endpoint integration tests | ✅ {{N}}/{{N}} passing |

## Files Reviewed

### {{Issue title}}

| File | Lines Changed | Scope |
|------|--------------|-------|
| ... | ... | ... |

## Overall Codebase Metrics (Cumulative)

| File | Lines | Purpose |
|------|-------|---------|
| ... | ... | ... |
| **Total** | **{{N}}** | **{{N}} tests** |

## Prior Findings Status

### [{{ID}}] {{STATUS}}: {{Title}}
{{For each finding from the previous review — resolved, still open, or unchanged}}

## Phase {{X.Y}} Findings — New

### [F{{N}}] {{SEVERITY}}: {{Title}}
{{Detailed finding with file references, code snippets, severity, and recommendation}}

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

| Dimension | Systems | Deployments | Procedures | SF | Properties | DataStreams | Observations | ControlStreams | Commands |
|-----------|---------|-------------|------------|----|------------|-------------|--------------|----------------|----------|
| {{Phase 2 dimensions — copy from last Phase 2 review, update only if regressions}} |

### Phase 3 (Format Handlers) — Current

| Dimension | GeoJSON | Format Detector | Validator | SWE Types | SML Types | {{Parser...}} |
|-----------|---------|-----------------|-----------|-----------|-----------|------|
| Valid input → output | ✅/❌ | ... | ... | ... | ... | ... |
| Invalid input → rejection | ✅/❌ | ... | ... | ... | ... | ... |
| All spec variants | ✅/❌ | ... | ... | ... | ... | ... |
| All branches/types | ✅/❌ | ... | ... | ... | ... | ... |
| Error specificity | ✅/❌ | ... | ... | ... | ... | ... |
| Edge cases | ✅/❌ | ... | ... | ... | ... | ... |

## Smoke Test Findings Integration

| Finding | Status | Evidence |
|---------|--------|----------|
| F4 (validTime) | ✅/❌/N/A | {{How it was addressed}} |
| F33-F39 | ... | ... |

## Summary

| Category | Count | Details |
|----------|-------|---------|
| ... | ... | ... |

## Recommendations

### Fix Now (before next issue)
### Fix Before Phase 4
### Defer (Low Priority)

## Root Cause Analysis
{{Only if new defects found — explain how/why they were introduced}}

## Overall Assessment
{{2-3 paragraph assessment of code quality, patterns, and trajectory}}
````

Then commit the report, push, and confirm the file is at the expected path.

```

---

## Post-Review Workflow

After the review report is generated:

1. **Read the recommendations** — decide which to fix now vs defer
2. **Create a GitHub issue** for any "Fix Now" items using `docs/governance/issue-creation-prompt-template.md`
3. **Complete the fix issue** before proceeding to the next Phase 3 task
4. **The next code review will reaffirm** all findings from this review — nothing is forgotten

---

## Quality Gates (Non-Negotiable)

Every Phase 3 code review report MUST include:

- [ ] All four verification commands executed and results recorded
- [ ] Every prior finding reaffirmed with current status
- [ ] New findings classified with severity labels
- [ ] Updated test quality heatmap (Phase 2 carried forward + Phase 3 current)
- [ ] Cumulative codebase metrics table (including Phase 2 files)
- [ ] Smoke test findings integration table
- [ ] Prioritized recommendations in three tiers
- [ ] Overall assessment paragraph

---

## Naming Convention

Reports follow the same naming pattern as Phase 2:

```

docs/implementation/phase-{major}.{minor}-code-review.md

```

Where:
- **Major** = project phase (3 for Phase 3)
- **Minor** = sequential review number within Phase 3 (1, 2, 3...)

Examples:
- `phase-3.1-code-review.md` (Phase 3, first review — GeoJSON handler)
- `phase-3.2-code-review.md` (Phase 3, second review — Format detector + Validator)
- `phase-3.3-code-review.md` (Phase 3, third review — SWE Common types + SensorML types)

---

## Reference Documents

When performing a Phase 3 code review, the reviewer should have access to:

| Document | Location | Purpose |
|----------|----------|---------|
| Phase 3 Lessons Learned | `docs/governance/phase-3-lessons-learned.md` | Phase 3 guardrails: upstream audit, Postel's Law, type naming, content negotiation, layered architecture |
| Phase 2 Lessons Learned | `docs/governance/phase-2-lessons-learned.md` | General guardrails — Lessons 6-10 still active in Phase 3 |
| Phase 2 Review Template | `docs/governance/code-review-prompt-template.md` | Reference for Phase 2 heatmap dimensions |
| Previous Review | `docs/implementation/phase-{prev}-code-review.md` | Prior findings to reaffirm |
| Implementation Guide | `docs/planning/csapi-implementation-guide.md` | Spec compliance, Phase 3 component specs (§7) |
| ROADMAP | `docs/planning/ROADMAP.md` | Phase 3 task definitions, acceptance criteria |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |
| Smoke Test Report (Phase 2.8) | `docs/implementation/live-server-smoke-test-post-phase-2.8.md` | F33 finding (schema variants) |
| Smoke Test Report (Phase 2.9) | `docs/implementation/live-server-smoke-test-post-phase-2.9.md` | F34-F39 findings |
| OGC SWE Common 3.0 Spec | `docs/research/standards/` (if available) | SWE Common type/parser reference |
| OGC SensorML 3.0 Spec | `docs/research/standards/` (if available) | SensorML parser reference |
| OGC API Connected Systems | `docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml` | GeoJSON encoding, featureType vocabularies |
```
