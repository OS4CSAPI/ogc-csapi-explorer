# Code Review Prompt Template — Phase 5

**Purpose:** Reusable prompt for triggering AI-generated code reviews during Phase 5 (Parser Completion). Adapts the Phase 3 review template to the specific quality concerns of Part 2 resource parsers, schema response parsers, and the recursive delegation fix.

**Version:** 1.0  
**Date:** February 19, 2026  
**Supersedes:** Nothing — sibling to `code-review-prompt-template-phase-3.md` (Phase 3) and `code-review-prompt-template.md` (Phase 2), which remain valid for any revisits to those phases.  
**Report destination:** `docs/implementation/phase-{X.Y}-code-review.md`

---

## Why a Separate Template?

Phase 5 code differs from Phase 3 code in key ways, even though both produce parsers:

| Dimension           | Phase 3 (Format Handlers)                                       | Phase 5 (Parser Completion)                                                                 |
| ------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Primary output      | Typed objects from raw JSON/XML (SWE Common, SensorML, GeoJSON) | Typed objects from Part 2 JSON (Observation, Command, etc.)                                 |
| Correctness check   | "Does the parser produce the right typed output?"               | Same + "Are instant vs interval time fields handled correctly?"                             |
| Test strategy       | Fixture-based input → typed output assertions                   | Same, but with cross-reference exclusion and opaque pass-through assertions                 |
| Pattern reference   | First parser completed becomes the reference                    | `parseDatastream()` is the explicit gold standard; `parseProperty()` for non-Part-2         |
| Validation concern  | Input validation before parsing                                 | Same + tolerant extraction (Postel's Law) — never gate on missing fields                    |
| Heatmap dimensions  | Parser behavior coverage (generic)                              | Resource-specific: time handling, cross-ref exclusion, result pass-through, enum validation |
| Spec references     | SWE Common 3.0, SensorML 3.0, GeoJSON encoding rules            | OGC API Connected Systems Part 2 (23-002)                                                   |
| Smoke test findings | F4, F33–F39                                                     | F27, F30, F31, F33, F38 (Part 2 data shape findings)                                        |

The Phase 3 test checklist Category C (Parser modules) is partially applicable but misses Phase 5-specific concerns like instant-vs-interval time distinction, opaque `result` pass-through, and cross-reference field exclusion.

---

## When to Use

Trigger this prompt after any of these Phase 5 milestones:

1. **A parser task is completed** (e.g., Issue #81 — parseObservation + Tests)
2. **Multiple related parser tasks are completed** in a single session (batch review)
3. **A schema response parser is completed** (Tasks 7a/7b)
4. **The recursive delegation fix is completed** (Task 8)
5. **Integration wiring is completed** (Task 9)
6. **Before Phase 6 or upstream submission** (gate review for all of Phase 5)

Do NOT trigger after trivial doc-only commits or non-code changes.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a code review of the work completed since the last review.

### Scope

**Phase:** {{Phase number, e.g., "5.1"}}
**Issues completed:** {{List issue numbers and titles, e.g., "#81 — parseObservation + Tests"}}
**Commits to review:** {{List commit SHAs or say "all commits since {last review commit SHA}"}}
**Last review:** {{Reference the previous review doc, e.g., "docs/implementation/phase-3.17-code-review.md" or "none — first Phase 5 review"}}

### Review Instructions

1. **Review Lessons Learned** — read both documents before evaluating code:
   - `docs/governance/phase-3-lessons-learned.md` — Key checks still active in Phase 5:
     - Lesson 1: Does any new code introduce an architectural layer without upstream precedent?
     - Lesson 2: Does extraction depend on validation? (It must not.)
     - Lesson 4: Are there parallel systems doing the same thing?
     - Lesson 10: Do type names collide with JS/TS built-ins?
     - Lesson 12: Is the code technically correct but should not exist in a client library?
   - `docs/governance/phase-2-lessons-learned.md` — General guardrails (Lessons 6-10 still active)

2. **Run verification gates** — execute all four and record results:
   - `npx tsc --noEmit` (note pre-existing `@types/node` errors — 4 expected)
   - `npx jest "src/ogc-api/csapi"` (record pass count — must include ALL prior tests + new tests)
   - `npx jest "src/ogc-api/csapi/formats"` (record pass count for format-specific tests only)
   - `npx jest "src/ogc-api/endpoint.spec"` (record pass count, note pre-existing failures)

3. **Read all changed files** — identify every file modified since the last review commit. For each file, note:
   - What changed (lines added/modified/removed)
   - Whether the change follows the established pattern for its component type (see Pattern References below)

4. **Reaffirm ALL prior findings** — read the previous review doc and check each open finding:
   - For each RESOLVED finding: confirm it's still resolved, cite evidence
   - For each STILL OPEN finding: check if it was addressed, update status
   - For each UNCHANGED finding (not-our-code): reaffirm unchanged status

5. **Evaluate new code against these quality dimensions:**

   - **Correctness:** Does the function produce the correct typed output from valid input?

   - **Test thoroughness:** Apply the Phase 5 test checklist (choose the appropriate category):

     **Category A — Resource parsers** (parseProperty, parseDatastream, parseObservation, parseControlStream, parseCommand, parseCommandStatus):
     - [ ] Valid fixture → correctly typed output with all properties mapped
     - [ ] Minimal valid fixture → output with optional fields absent/undefined (not empty string)
     - [ ] Non-object input → throws Error with function-specific message
     - [ ] Cross-reference fields excluded from output (`system@id`, `datastream@id`, `foi@id`, `controlstream@id`, `command@id`, etc.)
     - [ ] Time fields handled correctly:
       - For interval parsers (Datastream, ControlStream): `parseValidTime()` called, returns `TimeInterval`
       - For instant parsers (Observation, CommandStatus): plain string pass-through, `parseValidTime()` NOT called
     - [ ] Optional fields use conditional spread (absent in output, not `undefined` key)
     - [ ] `satisfies` typing on return statement
     - [ ] Opaque fields passed through without interpretation (`result` in Observation, `parameters` in Observation)
     - [ ] Enum fields validated against known values (e.g., `resultType`, `statusCode`)

     **Category B — Schema response parsers** (parseDatastreamSchemaResponse, parseControlStreamSchemaResponse):
     - [ ] Delegates to existing SWE Common parser (`parseSWEComponent()`)
     - [ ] Extracts envelope fields (`encoding`, `obsFormat`/`commandFormat`, etc.)
     - [ ] Falls back gracefully when SWE schema is absent
     - [ ] Non-object input → throws Error

     **Category C — Recursive delegation fix** (physical-system.ts, aggregate-process.ts):
     - [ ] `parseSensorML30()` called for nested subsystems/components
     - [ ] No circular import at runtime (test suite proves this)
     - [ ] Existing tests still pass (regression check)
     - [ ] New test cases cover nested structures

     **Category D — Integration wiring** (response.ts, index.ts):
     - [ ] New parsers wired into `parseCollectionResponse()` pipeline
     - [ ] Barrel exports updated for all new public functions
     - [ ] End-to-end test: raw JSON fixture → pipeline → typed output

   - **Consistency:** Does new code follow the established pattern for its component type?

     | Component Type | Pattern Reference (Gold Standard) |
     |---------------|----------------------------------|
     | Part 2 resource parsers | `parseDatastream()` in `part2.ts` — input guard, cast, extract, conditional spread, `satisfies` return |
     | Non-Part-2 resource parsers | `parseProperty()` in `property.ts` — flat JSON, no time fields |
     | Schema response parsers | To be established by Task 7a — envelope + SWE delegation |
     | Recursive delegation | Existing `parseSensorML30()` call patterns in `parser.ts` |
     | Shared helpers | `normalizeObservedProperties()` in `part2.ts`, `normalizeStatusCode()` (Task 5a) |
     | Test files | `part2.spec.ts` — sibling `describe` blocks per parser, inline fixtures, fixture source documented |
     | Index/barrel files | `src/ogc-api/csapi/formats/index.ts` pattern |

   - **JSDoc quality:** Params, returns, throws, examples, @see spec links
   - **Spec compliance:** Do @see links point to correct OGC 23-002 sections?

     | Component | Expected Spec References |
     |-----------|------------------------|
     | parseProperty | OGC 23-001 (Part 1) — DerivedProperty resources |
     | parseDatastream | OGC 23-002 (Part 2) — Datastream resources |
     | parseObservation | OGC 23-002 (Part 2) — Observation resources |
     | parseControlStream | OGC 23-002 (Part 2) — ControlStream resources |
     | parseCommand | OGC 23-002 (Part 2) — Command resources |
     | parseCommandStatus | OGC 23-002 (Part 2) — CommandStatus resources |
     | Schema response parsers | OGC 23-002 (Part 2) + SWE Common 3.0 |

   - **Exports:** Are new types/functions exported from the appropriate barrel file (`formats/index.ts`, `src/index.ts`)?
   - **Input validation:** Does every public function guard against null/undefined/wrong-type input before processing?

6. **Classify every finding** using these severity labels:
   - **BUG** — incorrect behavior, wrong output, runtime error
   - **DESIGN** — architectural concern, DRY violation, type safety issue
   - **GAP** — missing test coverage, missing export, incomplete implementation
   - **POSITIVE** — something done well that should be maintained
   - **INFORMATIONAL** — worth noting but no action needed
   - **CONSISTENCY** — follows or deviates from established patterns

7. **Generate the test quality heatmap** — update the table showing coverage across ALL Phase 5 components (not just new ones), using these dimensions:

   **For resource parsers (Category A):**

   | Dimension | Description |
   |-----------|-------------|
   | Fixture → typed output | Valid fixture produces correct typed result with all fields |
   | Minimal fixture | Only required fields populated; optionals absent |
   | Non-object rejection | Throws on null, number, string input |
   | Cross-ref exclusion | `@id` / `@link` fields not in output |
   | Time field correctness | Intervals use `parseValidTime()` → `TimeInterval`; instants are plain strings |
   | Optional field handling | Conditional spread — key absent, not `undefined` value |
   | Opaque pass-through | `result`, `parameters` passed without interpretation |
   | Enum validation | Known values accepted; unknown → null/fallback |
   | `satisfies` typing | Return statement uses `satisfies` for type safety |

   **For schema response parsers (Category B):**

   | Dimension | Description |
   |-----------|-------------|
   | Envelope extraction | Metadata fields (encoding, format) correctly extracted |
   | SWE delegation | `parseSWEComponent()` called and result included |
   | Missing schema fallback | Graceful handling when SWE schema is absent |
   | Non-object rejection | Throws on invalid input |

   **For integration wiring (Category D):**

   | Dimension | Description |
   |-----------|-------------|
   | Pipeline routing | Correct parser selected for each resource type |
   | Barrel exports | All new functions exported from index files |
   | End-to-end test | Raw JSON → pipeline → typed output verified |

8. **Include a root cause analysis** if there are new defects — explain HOW and WHY each issue was introduced, following the pattern from Phase 2.2 review

9. **Write prioritized recommendations** in three tiers:
   - **Fix Now** (before next coding issue)
   - **Fix Before Phase 6** (before upstream submission)
   - **Defer** (low priority, no current impact)

10. **Check smoke test finding integration** — for each Phase 5 task, verify that relevant smoke test findings have been addressed:

   | Finding | Relevant Phase 5 Task | What to Check |
   |---------|----------------------|---------------|
   | F27 (Observation `foi@id` abbreviated notation) | Task 3: parseObservation | `foi@id` excluded from output; parser handles shape tolerantly |
   | F30 (ControlStream `system@link` cross-reference) | Task 4: parseControlStream | `system@link` excluded from output; fields extracted correctly |
   | F31 (Command `controlstream@id` data shape) | Tasks 5a/5b: parseCommand | `controlstream@id` excluded from output; all fields mapped |
   | F33 (ControlStream schema `commandFormat`/`parametersSchema`) | Task 7b: parseControlStreamSchemaResponse | Both field names handled as schema source |
   | F38 (CommandStatus `command@id`, `reportTime`, `statusCode`) | Task 6: parseCommandStatus | All fields extracted; `statusCode` normalized via `normalizeStatusCode()` |

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
| tsc --noEmit | ✅/❌ {{result}} (note: 4 pre-existing @types/node errors expected) |
| CSAPI unit tests (all) | ✅ {{N}} passing, {{N}} suites |
| CSAPI format tests | ✅ {{N}} passing, {{N}} suites |
| Endpoint integration tests | ✅ {{N}}/{{N}} passing (note pre-existing WMTS/WFS timeouts) |

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

### Phase 3 (Format Handlers) — Carried Forward

| Dimension | GeoJSON | SWE Types | SML Types | Parsers |
|-----------|---------|-----------|-----------|---------|
| {{Phase 3 dimensions — copy from last Phase 3 review, update only if regressions}} |

### Phase 5 (Parser Completion) — Current

| Dimension | parseProperty | parseDatastream | parseObservation | parseControlStream | parseCommand | parseCommandStatus | SchemaResp (DS) | SchemaResp (CS) | Recursive Fix | Integration |
|-----------|--------------|-----------------|------------------|--------------------|--------------|-------------------|-----------------|-----------------|--------------|-------------|
| Fixture → typed output | ✅/❌/— | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Minimal fixture | ✅/❌/— | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Non-object rejection | ✅/❌/— | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Cross-ref exclusion | —/✅/❌ | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Time field correctness | — | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | ... | ... | ... | ... |
| Optional field handling | ✅/❌/— | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Opaque pass-through | — | — | ✅/❌ | — | — | — | ... | ... | ... | ... |
| Enum validation | — | ✅/❌ | — | — | — | ✅/❌ | ... | ... | ... | ... |
| `satisfies` typing | ✅/❌ | ... | ... | ... | ... | ... | ... | ... | ... | ... |

## Smoke Test Findings Integration

| Finding | Status | Evidence |
|---------|--------|----------|
| F27 (Observation `foi@id`) | ✅/❌/N/A | {{How it was addressed}} |
| F30 (ControlStream `system@link`) | ✅/❌/N/A | ... |
| F31 (Command `controlstream@id`) | ✅/❌/N/A | ... |
| F33 (ControlStream schema variants) | ✅/❌/N/A | ... |
| F38 (CommandStatus data shape) | ✅/❌/N/A | ... |

## Summary

| Category | Count | Details |
|----------|-------|---------|
| ... | ... | ... |

## Recommendations

### Fix Now (before next issue)
### Fix Before Phase 6 (before upstream submission)
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
3. **Complete the fix issue** before proceeding to the next Phase 5 task
4. **The next code review will reaffirm** all findings from this review — nothing is forgotten

---

## Quality Gates (Non-Negotiable)

Every Phase 5 code review report MUST include:

- [ ] All four verification commands executed and results recorded
- [ ] Every prior finding reaffirmed with current status
- [ ] New findings classified with severity labels
- [ ] Updated test quality heatmap (Phase 2 + Phase 3 carried forward + Phase 5 current)
- [ ] Cumulative codebase metrics table (including Phase 2 and Phase 3 files)
- [ ] Smoke test findings integration table (F27, F30, F31, F33, F38)
- [ ] Prioritized recommendations in three tiers
- [ ] Overall assessment paragraph

---

## Naming Convention

Reports follow the same naming pattern as prior phases:

```

docs/implementation/phase-{major}.{minor}-code-review.md

```

Where:
- **Major** = project phase (5 for Phase 5)
- **Minor** = sequential review number within Phase 5 (1, 2, 3...)

Examples:
- `phase-5.1-code-review.md` (Phase 5, first review — parseProperty + parseDatastream + parseObservation)
- `phase-5.2-code-review.md` (Phase 5, second review — parseControlStream + parseCommand)
- `phase-5.3-code-review.md` (Phase 5, third review — parseCommandStatus + schema response parsers)
- `phase-5.4-code-review.md` (Phase 5, fourth review — recursive fix + integration wiring)

---

## Reference Documents

When performing a Phase 5 code review, the reviewer should have access to:

| Document | Location | Purpose |
|----------|----------|---------|
| P5 ROADMAP | `docs/planning/phase-5/P5-ROADMAP.md` | Task definitions, dependencies, acceptance criteria |
| P5 Implementation Guide | `docs/planning/phase-5/P5-parser-completion-implementation-guide.md` | Field transformations, input shapes, test cases per parser |
| P5 Contribution Goal | `docs/planning/phase-5/P5-contribution-goal-and-definition.md` | Scope boundary — what is/isn't in Phase 5 |
| Parsing Coverage Audit | `docs/research/phase-5/parsing-coverage-audit.md` | Source of truth for the 9 parser gaps being addressed |
| P5 Findings Coverage Analysis | `docs/implementation/p5-findings-coverage-analysis.md` | Which smoke test findings are addressed by which P5 tasks |
| Phase 3 Lessons Learned | `docs/governance/phase-3-lessons-learned.md` | Phase 3 guardrails still active: upstream audit, Postel's Law, type naming |
| Phase 2 Lessons Learned | `docs/governance/phase-2-lessons-learned.md` | General guardrails — Lessons 6-10 still active |
| Phase 3 Review Template | `docs/governance/code-review-prompt-template-phase-3.md` | Predecessor template — Category C parser checklist is a subset of Phase 5's |
| Previous Review | `docs/implementation/phase-{prev}-code-review.md` | Prior findings to reaffirm |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |
| Smoke Test Report (Phase 4.1) | `docs/implementation/live-server-smoke-test-post-phase-4.1.md` | F27, F30, F31, F33, F38 findings (Phase 5 targets) |
| validTime Coverage Analysis | `docs/research/phase-5/validtime-coverage-analysis.md` | Which resource types use intervals vs instants |
| OGC API Connected Systems Part 1 | OGC 23-001 | Part 1 resource definitions (Property) |
| OGC API Connected Systems Part 2 | OGC 23-002 | Part 2 resource definitions (Datastream, Observation, ControlStream, Command, CommandStatus) |
| OGC SWE Common 3.0 | OGC 08-094r2 | SWE Common types used by schema response parsers |

---

## Key Differences from Phase 3 Template

For reviewers familiar with the Phase 3 template, these are the substantive changes:

| Section | Phase 3 | Phase 5 |
|---------|---------|---------|
| Test checklist categories | A (Utility), B (Types), C (Parsers), D (Validators) | A (Resource parsers), B (Schema response parsers), C (Recursive fix), D (Integration) |
| Pattern reference gold standard | "First parser completed" (generic) | `parseDatastream()` explicit; `parseProperty()` for non-Part-2 |
| Heatmap dimensions | Generic parser dimensions | Resource-specific: time handling, cross-ref exclusion, opaque pass-through, enum validation, `satisfies` typing |
| Smoke test findings | F4, F33–F39 | F27, F30, F31, F33, F38 |
| Spec references | SWE Common 3.0, SensorML 3.0, GeoJSON encoding | OGC 23-002 Part 2 (primary), OGC 23-001 Part 1 (Property only) |
| Recommendation tiers | "Fix Before Phase 4" | "Fix Before Phase 6" |
| Pre-existing test issues | Not documented | 4 `@types/node` tsc errors, 72 WMTS/WFS timeout failures |
```
