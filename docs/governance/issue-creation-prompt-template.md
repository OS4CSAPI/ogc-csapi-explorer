# Issue Creation Prompt Template

**Purpose:** Reusable template for creating uniform, scoped GitHub issues for each of the 33 ROADMAP implementation tasks. Every issue produced from this template acts as an AI scope-containment boundary — it defines exactly what to build, what files to touch, what NOT to touch, and what to verify before closing.

**Usage:** Copy the template below, fill in the placeholders (marked with `{{...}}`), and create the issue via the GitHub API or UI.

**Version:** 1.0  
**Date:** February 13, 2026

---

## Before Creating an Issue

1. **Read the ROADMAP task** — `docs/planning/ROADMAP.md` contains the authoritative task definition
2. **Read the Guide section** — `docs/planning/csapi-implementation-guide.md` has detailed specifications for every component
3. **Identify the exact files** — list every file created or modified, nothing more
4. **Identify the scope fence** — what files/concerns belong to adjacent issues, not this one
5. **Identify dependencies** — which issue(s) must be closed before this one can start

---

## Issue Template

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

> **⚠️ MANDATORY:** Before starting work on this issue, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](../AI_OPERATIONAL_CONSTRAINTS.md).
>
> **For Phase 3 issues:** Also review [`docs/governance/phase-3-lessons-learned.md`](../governance/phase-3-lessons-learned.md) — these are guardrails derived from real mistakes in Phase 3 (validator removal, upstream audit failures, real-world data divergence). Lessons 1-2 (audit upstream, Postel's Law) are especially critical.
>
> **For Phase 2 issues:** Also review [`docs/governance/phase-2-lessons-learned.md`](../governance/phase-2-lessons-learned.md) — test checklist (Lesson 1) and query options table (Lesson 2) are mandatory.

Key constraints for this task:

- **Precedence:** OGC specifications → AI Collaboration Agreement → This issue description → Existing code → Conversational context
- **No scope expansion:** Do not infer unstated requirements or add unrequested features
- **No refactoring:** Do not rename, restructure, or "improve" code outside this issue's scope
- **Minimal diffs:** Prefer the smallest change that satisfies the acceptance criteria
- **Ask when unclear:** If intent is ambiguous, stop and ask for clarification
- **Audit upstream first (Phase 3):** Before building any new architectural layer, verify that at least one upstream handler uses the same pattern (Lesson 1)

---

## References

Read these documents before starting implementation. They are ordered by priority.

### Primary References (must read)

| #   | Document                                              | Section/Lines             | What It Provides                      |
| --- | ----------------------------------------------------- | ------------------------- | ------------------------------------- |
| 1   | {{Guide section with code template or specification}} | {{Lines N-M}}             | {{What the implementer gets from it}} |
| 2   | {{Blueprint file to match}}                           | {{Full file / Lines N-M}} | {{What pattern to follow}}            |
| 3   | {{Blueprint test file}}                               | {{Full file / Lines N-M}} | {{What test pattern to follow}}       |

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

## Template Usage Notes

### Filling in the "Scope — What NOT to Touch" Section

This is the most important section for AI safety. For each issue, identify:

1. **The next task in the ROADMAP** — the implementer must not reach ahead
2. **Files owned by other tasks** — even if this task's code could benefit from touching them
3. **Refactoring opportunities** — the implementer must not "improve" adjacent code
4. **Export changes** — `index.ts` exports are usually owned by the integration task (Phase 1.4)

### Filling in the References Section

Every issue should reference at minimum:

1. **Implementation Guide** — the specific section (§5, §6, §7, etc.) that specifies this task's output
2. **An EDR or upstream blueprint** — the existing file that demonstrates the pattern to follow
3. **The OGC specification** — for `@see` links and field-level accuracy

Omit research references if the task is straightforward (e.g., barrel file creation). Include them when the task involves non-obvious design decisions.

### Issue Numbering Convention

Issues follow ROADMAP task order:

| Issue # | ROADMAP Task                                          |
| ------- | ----------------------------------------------------- |
| #1      | Phase 1, Task 1: Create Type System                   |
| #2      | Phase 1, Task 2: Create Helper Utilities              |
| #3      | Phase 1, Task 3: Create Stub QueryBuilder             |
| #4      | Phase 1, Task 4: Integrate with OgcApiEndpoint        |
| #5      | Phase 2, Task 1: Systems Methods                      |
| #6      | Phase 2, Task 2: Deployments Methods                  |
| #7      | Phase 2, Task 3: Procedures Methods                   |
| #8      | Phase 2, Task 4: Sampling Features Methods            |
| #9      | Phase 2, Task 5: Properties Methods                   |
| #10     | Phase 2, Task 6: DataStreams Methods                  |
| #11     | Phase 2, Task 7: Observations Methods                 |
| #12     | Phase 2, Task 8: Control Streams Methods              |
| #13     | Phase 2, Task 9: Commands Methods                     |
| #14     | Phase 3, Task 1: GeoJSON Handler Extensions           |
| #15     | Phase 3, Task 2: Format Detector Extensions           |
| #16     | Phase 3, Task 3: Validator Extensions                 |
| #17     | Phase 3, Task 4: SWE Common Types                     |
| #18     | Phase 3, Task 5: SensorML Types                       |
| #19     | Phase 3, Task 6: SensorML Simple Process Parser       |
| #20     | Phase 3, Task 7: SensorML Aggregate Process Parser    |
| #21     | Phase 3, Task 8: SensorML Physical System Parser      |
| #22     | Phase 3, Task 9: SensorML Main Parser                 |
| #23     | Phase 3, Task 10: SensorML Index                      |
| #24     | Phase 3, Task 11: SWE Common Simple Components Parser |
| #25     | Phase 3, Task 12: SWE Common DataRecord Parser        |
| #26     | Phase 3, Task 13: SWE Common DataArray Parser         |
| #27     | Phase 3, Task 14: SWE Common Main Parser              |
| #28     | Phase 3, Task 15: SWE Common Index                    |
| #29     | Phase 3, Task 16: Format Constants                    |
| #30     | Phase 3, Task 17: Format Index                        |
| #31     | Phase 4, Task 1: Integration Tests                    |
| #32     | Phase 4, Task 2: Unit Tests Completion                |
| #33     | Phase 4, Task 3: API Documentation                    |

### Labels

Apply these labels consistently:

| Label            | When to Use                                      |
| ---------------- | ------------------------------------------------ |
| `phase-1`        | Phase 1 tasks (issues #1-#4)                     |
| `phase-2`        | Phase 2 tasks (issues #5-#13)                    |
| `phase-3`        | Phase 3 tasks (issues #14-#30)                   |
| `phase-4`        | Phase 4 tasks (issues #31-#33)                   |
| `implementation` | All coding tasks                                 |
| `documentation`  | Tasks with significant documentation focus (#33) |
