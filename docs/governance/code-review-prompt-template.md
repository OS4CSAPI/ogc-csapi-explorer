# Code Review Prompt Template

**Purpose:** Reusable prompt for triggering AI-generated code reviews after coding progress. Produces a standardized report placed in `docs/implementation/` following the format established by Phase 1 through Phase 2.4 reviews.

**Version:** 1.0  
**Date:** February 14, 2026  
**Report destination:** `docs/implementation/phase-{X.Y}-code-review.md`

---

## When to Use

Trigger this prompt after any of these milestones:

1. **A resource type issue is completed** (e.g., Issue #9 Properties methods)
2. **A fix or cleanup issue is completed** (e.g., Issue #40 code review findings)
3. **Multiple related issues are completed** in a single session (batch review)
4. **Before starting Part 2 resources** (gate review)

Do NOT trigger after trivial doc-only commits or non-code changes.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a code review of the work completed since the last review.

### Scope

**Phase:** {{Phase number, e.g., "2.5"}}
**Issues completed:** {{List issue numbers and titles, e.g., "#9 — Properties Methods, #41 — DataStreams stub"}}
**Commits to review:** {{List commit SHAs or say "all commits since {last review commit SHA}"}}
**Last review:** {{Reference the previous review doc, e.g., "docs/implementation/phase-2.4-code-review.md"}}

### Review Instructions

1. **Run verification gates first** — execute all three and record results:
   - `npx tsc --noEmit` (must be clean)
   - `npx jest "src/ogc-api/csapi"` (record pass count)
   - `npx jest "src/ogc-api/endpoint.spec"` (record pass count, note pre-existing failures)

2. **Read all changed files** — identify every file modified since the last review commit. For each file, note:
   - What changed (lines added/modified/removed)
   - Whether the change follows established patterns

3. **Reaffirm ALL prior findings** — read the previous review doc and check each open finding:
   - For each RESOLVED finding: confirm it's still resolved, cite evidence
   - For each STILL OPEN finding: check if it was addressed, update status
   - For each UNCHANGED finding (not-our-code): reaffirm unchanged status

4. **Evaluate new code against these quality dimensions:**
   - **Correctness:** Do methods do what JSDoc says? Are URLs constructed correctly?
   - **Test thoroughness:** Apply the Lesson 1 checklist from `docs/governance/phase-2-lessons-learned.md`:
     - [ ] Collection query with exact `toBe()` URL assertion
     - [ ] Every applicable query option tested individually
     - [ ] Single resource retrieval with exact URL
     - [ ] CRUD operations with exact URLs
     - [ ] Each nested/association method tested with and without options
     - [ ] At least one nested method with pagination + filtering
     - [ ] Resource validation failure — all methods in resource type throw
     - [ ] Temporal parameter with exact `toBe()` assertion (if applicable)
   - **Consistency:** Does new code follow the patterns set by Procedures/SamplingFeatures (the gold standard)?
   - **JSDoc quality:** Params, returns, throws, examples, @see spec links
   - **Spec compliance:** Do spec links point to correct Part 1/Part 2 sections?
   - **Exports:** Are new types/constants exported from `src/index.ts`?
   - **Resource validation:** Does every public method call `assertResourceAvailable()` with the correct string?

5. **Classify every finding** using these severity labels:
   - **BUG** — incorrect behavior, wrong output, runtime error
   - **DESIGN** — architectural concern, DRY violation, type safety issue
   - **GAP** — missing test coverage, missing export, incomplete implementation
   - **POSITIVE** — something done well that should be maintained
   - **INFORMATIONAL** — worth noting but no action needed
   - **CONSISTENCY** — follows or deviates from established patterns

6. **Generate the test quality heatmap** — update the table showing coverage across ALL resource types (not just new ones), using these dimensions:
   - No options (base URL), limit, offset (standalone), q, id (single), id (array)
   - bbox, datetime (exact), f (format), cursor, multiple options
   - Type-specific params, resource validation (all methods), association pagination

7. **Include a root cause analysis** if there are new defects — explain HOW and WHY each issue was introduced, following the pattern from Phase 2.2 review

8. **Write prioritized recommendations** in three tiers:
   - **Fix Now** (before next coding issue)
   - **Fix Before Phase 3** (before response parsing work begins)
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

| Check | Result |
|-------|--------|
| tsc --noEmit | ✅/❌ {{result}} |
| CSAPI unit tests | ✅ {{N}} passing, {{N}} suites |
| Endpoint integration tests | ✅ {{N}}/{{N}} passing |
| {{Additional verification checks specific to this review}} | ✅/❌ |

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

| Dimension | Systems | Deployments | Procedures | SamplingFeatures | {{New resources...}} |
|-----------|---------|-------------|------------|------------------|-----|
| ... | ✅/❌ | ... | ... | ... | ... |

Checklist compliance score:
- Systems: {{N}}/{{N}} ({{%}})
- ...

## Summary

| Category | Count | Details |
|----------|-------|---------|
| ... | ... | ... |

## Recommendations

### Fix Now (before next issue)
### Fix Before Phase 3
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
3. **Complete the fix issue** before proceeding to the next resource type
4. **The next code review will reaffirm** all findings from this review — nothing is forgotten

---

## Quality Gates (Non-Negotiable)

Every code review report MUST include:

- [ ] All three verification commands executed and results recorded
- [ ] Every prior finding reaffirmed with current status
- [ ] New findings classified with severity labels
- [ ] Updated test quality heatmap (all resource types, not just new ones)
- [ ] Cumulative codebase metrics table
- [ ] Prioritized recommendations in three tiers
- [ ] Overall assessment paragraph

---

## Naming Convention

Reports follow this naming pattern:

```

docs/implementation/phase-{major}.{minor}-code-review.md

```

Where:
- **Major** = project phase (1, 2, 3, 4)
- **Minor** = sequential review number within that phase (1, 2, 3...)

Examples:
- `phase-1-code-review.md` (Phase 1, only review)
- `phase-2.2-code-review.md` (Phase 2, second review)
- `phase-2.5-code-review.md` (Phase 2, fifth review)

---

## Reference Documents

When performing a code review, the reviewer should have access to:

| Document | Location | Purpose |
|----------|----------|---------|
| Lessons Learned | `docs/governance/phase-2-lessons-learned.md` | Test checklist, query options table, guardrails |
| Previous Review | `docs/implementation/phase-{prev}-code-review.md` | Prior findings to reaffirm |
| Implementation Guide | `docs/planning/csapi-implementation-guide.md` | Spec compliance reference |
| ROADMAP | `docs/planning/ROADMAP.md` | Phase/issue context |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |
```
