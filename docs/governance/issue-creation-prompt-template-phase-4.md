# Issue Creation Prompt Template — Phase 4

**Purpose:** Reusable template for creating uniform, scoped GitHub issues. Covers both ROADMAP implementation tasks and **finding-driven issues** discovered during smoke testing. Every issue produced from this template acts as an AI scope-containment boundary — it defines exactly what to build, what files to touch, what NOT to touch, and what to verify before closing.

**Usage:** Copy the appropriate template section below (ROADMAP task or finding-driven), fill in the placeholders (marked with `{{...}}`), and create the issue via the GitHub API or UI.

**Version:** 2.0
**Date:** February 19, 2026
**Supersedes:** `docs/governance/issue-creation-prompt-template.md` (v1.0)

---

## Before Creating an Issue

1. **Read the ROADMAP task** — `docs/planning/ROADMAP.md` contains the authoritative task definition _(skip for finding-driven issues)_
2. **Read the Guide section** — `docs/planning/csapi-implementation-guide.md` has detailed specifications for every component
3. **Read the relevant smoke test report** — `docs/implementation/live-server-smoke-test-post-phase-*.md` documents the finding that triggered this issue _(for finding-driven issues)_
4. **Read server quirks** — `docs/governance/known-server-quirks.md` for any issue touching HTTP requests, content negotiation, or CRUD operations
5. **Identify the exact files** — list every file created or modified, nothing more
6. **Identify the scope fence** — what files/concerns belong to adjacent issues, not this one
7. **Identify dependencies** — which issue(s) must be closed before this one can start
8. **Search existing issues** — confirm no duplicate issue already tracks this work

---

## Issue Template A: ROADMAP Task

Use this template when the issue maps to a planned ROADMAP task.

```markdown
## Task

{{One-sentence summary of what this task produces. Example: "Implement all 12 Systems methods in `url_builder.ts` and add Systems method tests."}}

**ROADMAP Reference:** Phase {{1-4}}, Task {{number}} — {{ROADMAP task title}} (~{{X-Y}} hours, {{Low/Medium/High}} complexity)

---

## Files to Create or Modify

| File                       | Action              | Est. Lines | Purpose           |
| -------------------------- | ------------------- | ---------- | ----------------- |
| {{`path/to/file.ts`}}      | {{Create / Modify}} | {{~N-M}}   | {{Brief purpose}} |
| {{`path/to/file.spec.ts`}} | {{Create / Modify}} | {{~N-M}}   | {{Brief purpose}} |

## Blueprint Reference

{{Which existing file(s) in the repo demonstrate the pattern to follow. Always include the EDR equivalent if one exists. Example: "Follow the EDR pattern in `src/ogc-api/edr/model.ts` (126 lines)."}}

## Scope — What to Implement

{{Organized list of exactly what to build. Use sub-headers if the task has distinct sub-parts (e.g., interfaces, methods, parsers). Include method signatures, interface names, or component names — be specific enough that the implementer has no ambiguity.}}

### JSDoc Requirements

- Document {{what}} with {{what level of detail}}
- Add `@see` links to {{which spec sections}}
- Follow the JSDoc style in {{which blueprint file}}

### Testing Requirements

- Create/extend {{test file path}} (~{{N-M}} lines)
- {{Specific test scenarios to cover — list 3-6 concrete test cases}}
- Follow test patterns from {{which blueprint test file}}

## Scope — What NOT to Touch

{{This section is critical for AI scope containment. List every adjacent concern that does NOT belong in this issue. Reference the issue number that owns each concern.}}

- ❌ Do NOT {{action}} — that belongs to {{issue title / future issue}}
- ❌ Do NOT {{action}} — that belongs to {{issue title / future issue}}
- ❌ Do NOT modify files outside the "Files to Create or Modify" table above
- ❌ Do NOT refactor existing code unless required to complete this task

## Acceptance Criteria

- [ ] {{File}} exists with {{specific content — e.g., "all 9 resource interfaces"}}
- [ ] All new code has complete JSDoc documentation
- [ ] {{Test file}} exists with {{specific coverage — e.g., "tests for all 12 methods"}}
- [ ] Existing tests still pass (`npm test`)
- [ ] No lint errors
- [ ] {{Any task-specific criteria — e.g., "three-tier import hierarchy is correct"}}

## Dependencies

**Blocked by:** {{Issue #N — title, or "Nothing (first task)"}}
**Blocks:** {{Issue #N — title, or "Nothing (final task)"}}

---

## Operational Constraints

> **⚠️ MANDATORY:** Before starting work on this issue, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](AI_OPERATIONAL_CONSTRAINTS.md).
>
> **For all phases:** Review [`docs/governance/known-server-quirks.md`](known-server-quirks.md) if this issue involves HTTP requests, content negotiation, CRUD operations, or server interaction of any kind.
>
> **For Phase 4 issues:** Review the most recent smoke test report in `docs/implementation/` — it contains the current state of all findings and server behavior. Also review Phase 4 CRUD constraints below.
>
> **For Phase 3 issues:** Also review [`docs/governance/phase-3-lessons-learned.md`](phase-3-lessons-learned.md) — guardrails from real mistakes (validator removal, upstream audit failures, real-world data divergence). Lessons 1-2 (audit upstream, Postel's Law) are especially critical.
>
> **For Phase 2 issues:** Also review [`docs/governance/phase-2-lessons-learned.md`](phase-2-lessons-learned.md) — test checklist (Lesson 1) and query options table (Lesson 2) are mandatory.

Key constraints for this task:

- **Precedence:** OGC specifications → AI Collaboration Agreement → This issue description → Existing code → Conversational context
- **No scope expansion:** Do not infer unstated requirements or add unrequested features
- **No refactoring:** Do not rename, restructure, or "improve" code outside this issue's scope
- **Minimal diffs:** Prefer the smallest change that satisfies the acceptance criteria
- **Ask when unclear:** If intent is ambiguous, stop and ask for clarification
- **Audit upstream first (Phase 3+):** Before building any new architectural layer, verify that at least one upstream handler uses the same pattern (Lesson 1)

### Phase 4 CRUD Constraints

These constraints apply to any issue involving write operations (create/update/delete):

- **Content-Type matters:** Part 1 POST/PUT uses `application/geo+json`. Part 2 POST/PUT uses `application/json`. Getting this wrong returns 400/415.
- **Do NOT send Accept headers on POST:** OSH returns errors if Accept header is included on write requests.
- **PUT requires exact uid:** OSH rejects PUT if the `uid` in the body doesn't byte-for-byte match the server-stored value (P4-F2). Update methods must read the current uid before PUT, or preserve the original uid from creation.
- **Command POST may not return:** OSH holds the connection open for streaming status updates on command creation (P4-F1). Any command create implementation needs a timeout strategy.
- **ControlStreams path is lowercase:** Use `/controlstreams` — camelCase `/controlStreams` returns 400 on OSH.
- **Only delete what you create:** CRUD testing creates test data and deletes ONLY that data. Never delete pre-existing resources.

---

## References

Read these documents before starting implementation. They are ordered by priority.

### Primary References (must read)

| #   | Document                                              | Section/Lines             | What It Provides                      |
| --- | ----------------------------------------------------- | ------------------------- | ------------------------------------- |
| 1   | {{Guide section with code template or specification}} | {{Lines N-M}}             | {{What the implementer gets from it}} |
| 2   | {{Blueprint file to match}}                           | {{Full file / Lines N-M}} | {{What pattern to follow}}            |
| 3   | {{Blueprint test file}}                               | {{Full file / Lines N-M}} | {{What test pattern to follow}}       |

### Server Behavior References (for issues involving HTTP interaction)

| #   | Document                                                                                                                       | What It Provides                                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| 1   | [`docs/governance/known-server-quirks.md`](known-server-quirks.md)                                                             | All known server behaviors, content negotiation rules, and workarounds |
| 2   | Most recent `docs/implementation/live-server-smoke-test-post-phase-*.md`                                                       | Current state of all findings, server inventories, regression data     |
| 3   | [`docs/implementation/cross-server-interoperability-analysis.md`](../implementation/cross-server-interoperability-analysis.md) | Cross-server differences and interoperability patterns                 |

### Upstream Type/Import References (files this task imports from)

| #     | Document                    | What to Import              |
| ----- | --------------------------- | --------------------------- |
| {{N}} | {{`path/to/dependency.ts`}} | {{Specific exports needed}} |

### Research References (context, not required reading)

| #     | Document              | What It Provides                   |
| ----- | --------------------- | ---------------------------------- |
| {{N}} | {{Research doc path}} | {{Why a design decision was made}} |

### Specification References (for `@see` links and field accuracy)

| #     | Document                                                                                  | Use                            |
| ----- | ----------------------------------------------------------------------------------------- | ------------------------------ |
| {{N}} | [OGC API - Connected Systems Part 1 (23-001)](https://docs.ogc.org/is/23-001/23-001.html) | {{Which resource definitions}} |
| {{N}} | [OGC API - Connected Systems Part 2 (23-002)](https://docs.ogc.org/is/23-002/23-002.html) | {{Which resource definitions}} |

### Convention Quick Reference

| Rule                                               | Example                                              |
| -------------------------------------------------- | ---------------------------------------------------- |
| Use `.js` extension for relative imports           | `import { X } from './file.js'`                      |
| Use `import type` for interfaces/types             | `import type { Y } from './model.js'`                |
| Three-tier hierarchy: import from lower tiers only | shared → ogc-api → csapi                             |
| Named exports for types and utilities              | `export interface Z { ... }`                         |
| `as const` arrays for enum-like values             | `export const XTypes = [...] as const`               |
| HTTP mocking: `globalThis.fetch = jest.fn()`       | Never use nock, msw, or other libraries              |
| Meaningful tests only                              | Verify behavior, not that code runs without throwing |
```

---

## Issue Template B: Finding-Driven Issue

Use this template when the issue is triggered by a smoke test finding, demo app finding, or server behavior discovery — NOT a planned ROADMAP task.

```markdown
## Task

{{One-sentence summary. Example: "Handle OSH PUT uid strictness — update methods must preserve server-assigned uid exactly."}}

**Finding Reference:** {{P4-F2}} from [Smoke Test #19](../implementation/live-server-smoke-test-post-phase-4.1.md)
**Severity:** {{Critical / Moderate / Low / Informational}}
**Category:** {{Code bug / Server limitation / Interoperability concern / Design gap}}
**Ownership:** {{Ours / Upstream / Shared}}

---

## Problem Statement

{{What was observed during testing. Include the HTTP request, response, and why it's a problem. Be specific — copy evidence from the smoke test report.}}

**Evidence:**
```

{{Paste the relevant HTTP request/response or error from the smoke test}}

```

**Impact:** {{What breaks or degrades if this isn't fixed. Which library methods are affected?}}

## Files to Create or Modify

| File | Action | Est. Lines | Purpose |
|------|--------|-----------|---------|
| {{`path/to/file.ts`}} | {{Create / Modify}} | {{~N-M}} | {{Brief purpose}} |
| {{`path/to/file.spec.ts`}} | {{Create / Modify}} | {{~N-M}} | {{Brief purpose}} |

## Proposed Fix

{{Describe the approach. For design decisions, present 2-3 options with tradeoffs. Example:}}

**Option A:** {{Description}} — {{Tradeoff}}
**Option B:** {{Description}} — {{Tradeoff}}
**Recommended:** {{Which option and why}}

## Scope — What NOT to Touch

- ❌ Do NOT {{action}} — that belongs to {{issue title / future issue}}
- ❌ Do NOT modify files outside the "Files to Create or Modify" table above
- ❌ Do NOT refactor existing code unless required to complete this task
- ❌ Do NOT add server-specific hardcoded branches (e.g., "if server is 52N then...") — fixes must generalize

## Acceptance Criteria

- [ ] {{Specific fix implemented}}
- [ ] {{Test case covering the scenario that exposed the finding}}
- [ ] Existing tests still pass (`npm test`)
- [ ] No lint errors
- [ ] {{Smoke test verification step — e.g., "PUT with preserved uid returns 204 on OSH"}}

## Dependencies

**Blocked by:** {{Issue #N — title, or "Nothing"}}
**Blocks:** {{Issue #N — title, or "Nothing"}}

---

## Operational Constraints

> **⚠️ MANDATORY:** Before starting work on this issue, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](AI_OPERATIONAL_CONSTRAINTS.md) and [`docs/governance/known-server-quirks.md`](known-server-quirks.md).

Key constraints:
- **Precedence:** OGC specifications → AI Collaboration Agreement → This issue description → Existing code → Conversational context
- **No scope expansion:** Fix the finding, nothing more
- **No server-specific branches:** Fixes must be general-purpose, not "if OSH" / "if 52N"
- **Minimal diffs:** Prefer the smallest change that satisfies the acceptance criteria
- **Verify against live server:** The acceptance criteria should include a live-server verification step where applicable

---

## References

| # | Document | What It Provides |
|---|----------|------------------|
| 1 | {{Smoke test report where finding was discovered}} | Evidence and context |
| 2 | [`docs/governance/known-server-quirks.md`](known-server-quirks.md) | Server behavior patterns |
| 3 | {{Source file containing the affected code}} | Code to modify |
| 4 | {{Spec reference if applicable}} | Spec-correct behavior |
```

---

## Template Usage Notes

### Choosing Template A vs Template B

| Trigger                        | Template | Examples                                                |
| ------------------------------ | -------- | ------------------------------------------------------- |
| Planned ROADMAP task           | **A**    | "Implement SamplingFeatures CRUD methods"               |
| Smoke test finding (P4-F*, F*) | **B**    | "Fix PUT uid handling (P4-F2)"                          |
| Demo app finding               | **B**    | "Handle command POST streaming response"                |
| Bug report from testing        | **B**    | "classifyFeature returns wrong type for 52N procedures" |
| Refactoring / tech debt        | **A**    | "Extract shared pagination logic"                       |

### Filling in the "Scope — What NOT to Touch" Section

This is the most important section for AI safety. For each issue, identify:

1. **Adjacent issues** — the implementer must not reach into other issue scopes
2. **Files owned by other tasks** — even if this task's code could benefit from touching them
3. **Refactoring opportunities** — the implementer must not "improve" adjacent code
4. **Export changes** — `index.ts` exports are usually owned by integration tasks
5. **Server-specific workarounds** — fixes must generalize; no hardcoded server detection

### Filling in the References Section

**For ROADMAP tasks (Template A),** reference at minimum:

1. **Implementation Guide** — the specific section (§5, §6, §7, etc.)
2. **A blueprint file** — the existing file that demonstrates the pattern to follow
3. **The OGC specification** — for `@see` links and field-level accuracy

**For finding-driven issues (Template B),** reference at minimum:

1. **The smoke test report** — where the finding was discovered and what evidence was gathered
2. **Server quirks doc** — for understanding server behavior context
3. **The affected source file** — so the implementer knows where to look

Omit research references if the task is straightforward.

### Issue Numbering

Issues are numbered sequentially as created. The original ROADMAP mapping (#1–#33) is historical context only — it does not constrain future issue numbers.

**Current state (as of February 19, 2026):**

- Issues #1–#33: Original ROADMAP tasks (Phases 1–4)
- Issues #34+: Finding-driven fixes, smoke test follow-ups, interoperability improvements
- Latest issues: #76 (SSN namespace), #77 (validTime optional)

New issues get the next available number. There is no requirement to map issue numbers to ROADMAP tasks.

### Finding ID Cross-Reference

Findings from smoke tests use these numbering series:

| Series      | Phase     | Range  | Example                               |
| ----------- | --------- | ------ | ------------------------------------- |
| F-series    | Phase 2–3 | F1–F90 | F84 (52N procedure misclassification) |
| P4-F-series | Phase 4   | P4-F1+ | P4-F2 (PUT uid strictness)            |

When creating an issue for a finding, include the finding ID in the issue title and body. Example: `"Fix PUT uid strictness (P4-F2)"`.

### Labels

Apply these labels consistently:

| Label               | When to Use                                                              |
| ------------------- | ------------------------------------------------------------------------ |
| `phase-1`           | Phase 1 tasks                                                            |
| `phase-2`           | Phase 2 tasks                                                            |
| `phase-3`           | Phase 3 tasks                                                            |
| `phase-4`           | Phase 4 tasks (including finding-driven fixes discovered during Phase 4) |
| `implementation`    | All coding tasks                                                         |
| `documentation`     | Tasks with significant documentation focus                               |
| `bug`               | Finding-driven issues where our code needs a fix                         |
| `server-limitation` | Issues documenting upstream server behavior (won't be fixed client-side) |
| `interoperability`  | Issues about cross-server compatibility                                  |
| `smoke-test`        | Issues discovered during smoke testing                                   |

---

## Changes from v1.0

| Aspect                        | v1.0                 | v2.0                                                                   |
| ----------------------------- | -------------------- | ---------------------------------------------------------------------- |
| Issue types                   | ROADMAP tasks only   | ROADMAP tasks + finding-driven issues                                  |
| Templates                     | 1 template           | 2 templates (A: ROADMAP, B: finding-driven)                            |
| Server quirks reference       | Not included         | Required reading for HTTP-related issues                               |
| Smoke test reference          | Not included         | Required reading for finding-driven issues                             |
| Phase 4 CRUD constraints      | Not included         | Full section with uid, Content-Type, streaming rules                   |
| Issue numbering               | Fixed #1–#33 mapping | Sequential, no ROADMAP constraint                                      |
| Labels                        | 6 labels             | 10 labels (added bug, server-limitation, interoperability, smoke-test) |
| Finding ID guidance           | None                 | Cross-reference table for F-series and P4-F-series                     |
| "No server-specific branches" | Not mentioned        | Explicit constraint in both templates                                  |
| Operational Constraints       | Phase 2–3 lessons    | Phase 2–4 lessons + CRUD constraints                                   |
