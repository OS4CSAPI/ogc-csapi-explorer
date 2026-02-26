# Issue Creation Prompt Template — Phase 6

**Purpose:** Reusable template for creating uniform, scoped GitHub issues for Phase 6 (Upstream Acceptance Refactoring). Covers both ROADMAP implementation tasks and finding-driven issues discovered during verification. Every issue produced from this template acts as an AI scope-containment boundary — it defines exactly what to build, what files to touch, what NOT to touch, and what to verify before closing.

**Usage:** Copy the appropriate template section below (ROADMAP task or finding-driven), fill in the placeholders (marked with `{{...}}`), and create the issue via the GitHub API or UI.

**Version:** 4.0  
**Date:** February 24, 2026  
**Supersedes:** `docs/governance/issue-creation-prompt-template-phase-5.md` (v3.0)

---

## Before Creating an Issue

> **⚠️ Implementation branch:** `phase-6` — All Phase 6 work MUST be implemented on the `phase-6` branch. Do NOT implement on `main` or `clean-pr`.

1. **Read the ROADMAP task** — Identify the authoritative task definition:
   - **Phase 6 tasks:** [`docs/planning/phase-6/P6-ROADMAP.md`](../planning/phase-6/P6-ROADMAP.md) — 10 tasks (13 execution units) for module boundary refactoring
   - **Phase 1–5 tasks:** [`docs/planning/ROADMAP.md`](../planning/ROADMAP.md), [`docs/planning/phase-5/P5-ROADMAP.md`](../planning/phase-5/P5-ROADMAP.md) — prior phases (complete)
2. **Read the Guide section** — Identify the implementation specification:
   - **Phase 6:** [`docs/planning/phase-6/P6-implementation-guide.md`](../planning/phase-6/P6-implementation-guide.md) — barrel file, factory function, endpoint decoupling, package.json specs (991 lines, 14 sections)
   - **Phase 1–4:** [`docs/planning/csapi-implementation-guide.md`](../planning/csapi-implementation-guide.md) — full CSAPI architecture (4,715 lines)
   - **Phase 5:** [`docs/planning/phase-5/P5-parser-completion-implementation-guide.md`](../planning/phase-5/P5-parser-completion-implementation-guide.md) — parser specs (1,009 lines)
3. **Read the Contribution Goal** — Confirm the task is within scope:
   - **Phase 6:** [`docs/planning/phase-6/P6-contribution-goal-and-definition.md`](../planning/phase-6/P6-contribution-goal-and-definition.md) — 12 acceptance criteria, 2 commits, 7 files
4. **Read the Task Granularity Review** — Understand split rationale for execution units 2a/2b, 4a/4b, 10a/10b:
   - [`docs/research/phase-6/task-granularity-review.md`](../research/phase-6/task-granularity-review.md)
5. **Read server quirks** — [`docs/implementation/server-quirks-reference.md`](../implementation/server-quirks-reference.md) for any issue that might affect test behavior
6. **Identify the exact files** — list every file created or modified, nothing more
7. **Identify the scope fence** — what files/concerns belong to adjacent tasks, not this one
8. **Identify dependencies** — which task(s) must be completed before this one can start
9. **Search existing issues** — confirm no duplicate issue already tracks this work

---

## Issue Template A: ROADMAP Task

Use this template when the issue maps to a planned P6 ROADMAP task.

```markdown
## Task

{{One-sentence summary of what this task produces. Example: "Apply Prettier formatting to all 51 CSAPI files" or "Create barrel file `csapi/index.ts` with all public CSAPI re-exports."}}

**ROADMAP Reference:** Phase 6, Task {{number/subtask}} — {{ROADMAP task title}} (~{{X-Y}} hours, {{Low/Medium}} complexity)
**Implementation Branch:** `phase-6`

---

## Files to Create or Modify

| File                       | Action              | Est. Lines | Purpose           |
| -------------------------- | ------------------- | ---------- | ----------------- |
| {{`path/to/file.ts`}}      | {{Create / Modify}} | {{~N-M}}   | {{Brief purpose}} |
| {{`path/to/file.spec.ts`}} | {{Create / Modify}} | {{~N-M}}   | {{Brief purpose}} |

## Blueprint Reference

{{Which existing file(s) in the repo demonstrate the pattern to follow. For Phase 6:

- Barrel file → `src/ogc-api/csapi/formats/index.ts` (sectioned JSDoc divider pattern)
- Factory function → `endpoint.csapi()` method logic (guard → fetch → scan → construct) and EDR `endpoint.edr()` pattern
- `package.json` exports → existing `"."` and `"./worker"` export conditions
- ESLint fixes → `import type` conversion pattern in existing CSAPI source files
  }}

## Scope — What to Implement

{{Organized list of exactly what to build. Use sub-headers if the task has distinct sub-parts. Include method signatures, file paths, or line references — be specific enough that the implementer has no ambiguity.}}

### JSDoc Requirements

- Document {{what}} with {{what level of detail}}
- Add `@see` links to {{which spec sections or implementation guide sections}}
- Follow the JSDoc style in {{which blueprint file}}

### Testing Requirements

- {{Specific testing action — e.g., "Run `npx tsc --noEmit` after modifications" or "Create `factory.spec.ts` with 2 tests"}}
- Follow test patterns from {{which blueprint test file}}

## Scope — What NOT to Touch

{{This section is critical for AI scope containment. List every adjacent concern that does NOT belong in this issue. Reference the task number that owns each concern.}}

- ❌ Do NOT {{action}} — that belongs to Task {{N}}
- ❌ Do NOT {{action}} — that belongs to Task {{N}}
- ❌ Do NOT modify files outside the "Files to Create or Modify" table above
- ❌ Do NOT refactor existing code unless required to complete this task
- ❌ Do NOT change any CSAPI business logic (types, builders, parsers, tests)

## Acceptance Criteria

- [ ] {{Specific deliverable — e.g., "All 51 files pass `npx prettier --check`"}}
- [ ] All new code has complete JSDoc documentation (where applicable)
- [ ] {{Test verification — e.g., "`npx tsc --noEmit` passes" or "Both factory tests pass"}}
- [ ] Existing tests still pass (`npm run test:browser`)
- [ ] No lint errors (`npm run lint`)
- [ ] All created or modified files pass `npx prettier --check`
- [ ] {{Any task-specific criteria — e.g., "`git grep 'csapi' src/index.ts` returns 0 matches"}}

## Dependencies

**Blocked by:** {{Task N — title, or "Nothing (first task)"}}
**Blocks:** {{Task N — title, or "Nothing (final task)"}}

---

## Operational Constraints

> **⚠️ MANDATORY:** Before starting work on this issue, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](AI_OPERATIONAL_CONSTRAINTS.md).
>
> **For Phase 6 issues:** Review the [P6 Implementation Guide](../planning/phase-6/P6-implementation-guide.md) for the specific file's complete specification, code sketches, and line references. Review Phase 6 constraints below.
>
> **For all phases:** Review [`docs/implementation/server-quirks-reference.md`](../implementation/server-quirks-reference.md) if this issue involves test execution or HTTP-related code.
>
> **For Phase 3 issues:** Also review [`docs/governance/phase-3-lessons-learned.md`](phase-3-lessons-learned.md)
>
> **For Phase 2 issues:** Also review [`docs/governance/phase-2-lessons-learned.md`](phase-2-lessons-learned.md)

Key constraints for this task:

- **Precedence:** OGC specifications → AI Collaboration Agreement → This issue description → Existing code → Conversational context
- **No scope expansion:** Do not infer unstated requirements or add unrequested features
- **No refactoring:** Do not rename, restructure, or "improve" code outside this issue's scope
- **Minimal diffs:** Prefer the smallest change that satisfies the acceptance criteria
- **Ask when unclear:** If intent is ambiguous, stop and ask for clarification
- **Zero business logic changes:** Phase 6 touches the integration boundary only — not types, builders, parsers, or test assertions

### Phase 6 Architectural Constraints

These constraints apply to all Phase 6 issues:

- **Format First ordering:** Prettier (Task 1) must complete before ESLint (Tasks 2a/2b). Both must complete before architecture changes (Tasks 4–8). Line numbers in the Implementation Guide are based on the formatted state.
- **`.js` extensions on all imports:** All local `import` and `export` statements in new files must use `.js` extensions (TypeScript ESM convention). Example: `import { X } from './factory.js'`.
- **`import type` for type-only imports:** All imports of interfaces/types must use `import type`. Example: `import type OgcApiEndpoint from '../endpoint.js'`. These are erased at compile time, creating zero runtime coupling.
- **Prettier-compliant from inception:** All new files must conform to upstream Prettier config (single quotes, semicolons, 80-char printWidth, 2-space indent, trailing commas ES5-style, LF line endings).
- **Barrel file is the CSAPI public API:** `csapi/index.ts` defines what consumers can import. Every re-export must trace to a real symbol in a real source module.
- **Factory function replaces `endpoint.csapi()`:** The 4-step logic (guard → fetch → scan → construct) must be preserved exactly. No auto-caching (endpoint already caches root and collection docs internally).
- **`hasConnectedSystems` and `csapiCollections` stay on endpoint:** These have zero CSAPI imports. They use `info.ts` functions. They follow the EDR pattern that jahow approved.
- **`root` and `getCollectionDocument` visibility change:** `private` → `public` is a 1-word change. The methods are unchanged in implementation.
- **No new dependencies:** Zero new npm packages, build tools, or configuration.

### Phase 6 Task-Specific Scope Boundaries

- Tasks 1/2a/2b/3 (Phase A) must NOT modify any code logic — formatting and import removal only
- Task 4a must NOT write any code — pure research/audit only
- Task 4b must NOT modify any existing files — creates `csapi/index.ts` only
- Task 5 must NOT modify `endpoint.ts` — creates `factory.ts` and `factory.spec.ts` only
- Task 6 must NOT modify `index.ts` or `endpoint.spec.ts` — modifies `endpoint.ts` only
- Task 7 must NOT modify `endpoint.ts` or `factory.ts` — modifies `index.ts` and `endpoint.spec.ts` only
- Task 8 must NOT modify any TypeScript files — modifies `package.json` only
- Task 9 must NOT modify code files — verification and commit only
- Task 10a must NOT push to any remote — verification only
- Task 10b must NOT modify code files — git operations only

---

## References

Read these documents before starting implementation. They are ordered by priority.

### Primary References (must read)

| #   | Document                                              | Section/Lines             | What It Provides                      |
| --- | ----------------------------------------------------- | ------------------------- | ------------------------------------- |
| 1   | {{Guide section with code template or specification}} | {{Lines N-M}}             | {{What the implementer gets from it}} |
| 2   | {{Blueprint file to match}}                           | {{Full file / Lines N-M}} | {{What pattern to follow}}            |

### Phase 6 Primary References

For Phase 6 tasks, include these in the Primary References table:

| #   | Document                                                                                      | What It Provides                                                                |
| --- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 1   | [P6 Implementation Guide](../planning/phase-6/P6-implementation-guide.md) §{{N}}              | Complete file specification, code sketch, line references for the specific task |
| 2   | [P6 ROADMAP](../planning/phase-6/P6-ROADMAP.md) Task {{N}}                                    | Task definition, deliverables, dependencies, estimated time                     |
| 3   | [P6 Contribution Goal](../planning/phase-6/P6-contribution-goal-and-definition.md)            | Acceptance criteria (12 gates), scope boundaries, consumer API migration        |
| 4   | [Task Granularity Review](../research/phase-6/task-granularity-review.md)                     | Split rationale for execution units 2a/2b, 4a/4b, 10a/10b                       |
| 5   | [Design Decision Resolution Report](../research/phase-6/design-decision-resolution-report.md) | All 10 design forks resolved — zero open questions                              |

### Research References (context, not required reading)

| #     | Document                        | What It Provides                   |
| ----- | ------------------------------- | ---------------------------------- |
| {{N}} | {{Research plan findings path}} | {{Why a design decision was made}} |

All Phase 6 research findings: [`docs/research/phase-6/findings/`](../research/phase-6/findings/)

### Convention Quick Reference

| Rule                                               | Example                                                           |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| Use `.js` extension for relative imports           | `import { X } from './file.js'`                                   |
| Use `import type` for interfaces/types             | `import type { Y } from './model.js'`                             |
| Three-tier hierarchy: import from lower tiers only | shared → ogc-api → csapi                                          |
| Named exports for types and utilities              | `export interface Z { ... }`                                      |
| Barrel file sections use JSDoc dividers            | `// ─────── Section Name ───────` pattern from `formats/index.ts` |
| Prettier-compliant from inception                  | Single quotes, semicolons, 80-char width, 2-space indent          |
| HTTP mocking: `globalThis.fetch = jest.fn()`       | Never use nock, msw, or other libraries                           |
| Meaningful tests only                              | Verify behavior, not that code runs without throwing              |
```

---

## Issue Template B: Finding-Driven Issue

Use this template when the issue is triggered by a verification failure, code review finding, or boundary violation discovered during Phase 6 execution — NOT a planned ROADMAP task.

```markdown
## Task

{{One-sentence summary. Example: "Fix barrel file missing re-export for CSAPIQueryBuilder type."}}

**Finding Reference:** {{Code review finding ID or verification gate failure}} from [{{Source document}}]({{link}})
**Severity:** {{Critical / Moderate / Low / Informational}}
**Category:** {{Boundary violation / Export gap / Type error / Test regression / Formatting issue}}
**Implementation Branch:** `phase-6`

---

## Problem Statement

{{What was observed during verification. Include the command run, actual output, and expected output. Be specific — paste evidence.}}

**Evidence:**
```

{{Paste the verification command and its output}}

```

**Impact:** {{What breaks or degrades if this isn't fixed. Which acceptance criteria are affected?}}

## Files to Create or Modify

| File | Action | Est. Lines | Purpose |
|------|--------|-----------|---------|
| {{`path/to/file.ts`}} | {{Create / Modify}} | {{~N-M}} | {{Brief purpose}} |

## Proposed Fix

{{Describe the approach. For ambiguous cases, present options with tradeoffs.}}

**Option A:** {{Description}} — {{Tradeoff}}
**Option B:** {{Description}} — {{Tradeoff}}
**Recommended:** {{Which option and why}}

## Scope — What NOT to Touch

- ❌ Do NOT {{action}} — that belongs to Task {{N}}
- ❌ Do NOT modify files outside the "Files to Create or Modify" table above
- ❌ Do NOT refactor existing code unless required to complete this task
- ❌ Do NOT change any CSAPI business logic

## Acceptance Criteria

- [ ] {{Specific fix implemented}}
- [ ] {{Verification gate that previously failed now passes}}
- [ ] Existing tests still pass (`npm run test:browser`)
- [ ] No lint errors (`npm run lint`)
- [ ] All created or modified files pass `npx prettier --check`

## Dependencies

**Blocked by:** {{Task N — title, or "Nothing"}}
**Blocks:** {{Task N — title, or "Nothing"}}

---

## Operational Constraints

> **⚠️ MANDATORY:** Before starting work on this issue, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](AI_OPERATIONAL_CONSTRAINTS.md) and the [P6 Implementation Guide](../planning/phase-6/P6-implementation-guide.md).

Key constraints:
- **Precedence:** OGC specifications → AI Collaboration Agreement → This issue description → Existing code → Conversational context
- **No scope expansion:** Fix the finding, nothing more
- **Minimal diffs:** Prefer the smallest change that satisfies the acceptance criteria
- **Zero business logic changes:** Phase 6 touches the integration boundary only
- **Verify against the 12 gates:** The acceptance criteria should reference specific verification gates from the [Contribution Goal](../planning/phase-6/P6-contribution-goal-and-definition.md)

---

## References

| # | Document | What It Provides |
|---|----------|------------------|
| 1 | {{Source document where finding was discovered}} | Evidence and context |
| 2 | [P6 Implementation Guide](../planning/phase-6/P6-implementation-guide.md) §{{N}} | Specification for the affected file |
| 3 | [P6 Contribution Goal](../planning/phase-6/P6-contribution-goal-and-definition.md) | 12 verification gates |
| 4 | {{Source file containing the affected code}} | Code to modify |
```

---

## Template Usage Notes

### Choosing Template A vs Template B

| Trigger                      | Template | Examples                                           |
| ---------------------------- | -------- | -------------------------------------------------- |
| Planned ROADMAP task         | **A**    | "Apply Prettier to 51 files", "Create barrel file" |
| Verification gate failure    | **B**    | "Barrel file missing export for CSAPIQueryBuilder" |
| Code review finding          | **B**    | "Factory function missing EndpointError import"    |
| TypeScript compilation error | **B**    | "Type mismatch in factory return type"             |
| Boundary violation           | **B**    | "endpoint.ts still imports from csapi/"            |

### Filling in the "Scope — What NOT to Touch" Section

This is the most important section for AI safety. For each issue, identify:

1. **Adjacent tasks** — the implementer must not reach into other task scopes
2. **Files owned by other tasks** — even if this task's code could benefit from touching them
3. **Refactoring opportunities** — the implementer must not "improve" adjacent code
4. **Business logic** — Phase 6 changes zero CSAPI behavior

**Phase 6 specific scope boundaries:**

- Phase A tasks (1, 2a, 2b, 3) must NOT touch any code logic — formatting/imports only
- Task 4b must NOT modify `index.ts` — only creates the barrel file
- Task 5 must NOT modify `endpoint.ts` — only creates factory files
- Task 6 must NOT modify `index.ts`, `endpoint.spec.ts`, or `package.json`
- Task 7 must NOT modify `endpoint.ts` or `factory.ts`
- Task 8 must NOT modify any TypeScript file
- Phase C tasks must NOT modify code files

### Issue Numbering

Issues are numbered sequentially as created. The original ROADMAP mapping (#1–#33) is historical context only.

**Current state (as of February 24, 2026):**

- Issues #1–#33: Original ROADMAP tasks (Phases 1–4)
- Issues #34–#77: Finding-driven fixes, smoke test follow-ups
- Issues #78+: Phase 5 parser completion tasks
- Issues #{{N}}+: Phase 6 refactoring tasks

New issues get the next available number.

### Labels

Apply these labels consistently:

| Label            | When to Use                                  |
| ---------------- | -------------------------------------------- |
| `phase-6`        | All Phase 6 tasks                            |
| `implementation` | All coding tasks                             |
| `documentation`  | Tasks with significant documentation focus   |
| `formatting`     | Phase A tasks (Prettier, ESLint)             |
| `architecture`   | Phase B tasks (barrel, factory, decoupling)  |
| `verification`   | Phase C tasks (gates, litmus test, rebase)   |
| `bug`            | Finding-driven issues where code needs a fix |

---

## Changes from v3.0

| Aspect               | v3.0 (Phase 5)                                                                | v4.0 (Phase 6)                                                                                                      |
| -------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Phase coverage       | Phases 1–5                                                                    | Phases 1–6                                                                                                          |
| Task scope           | Parser completion (9 tasks, 14 units)                                         | Module boundary refactoring (10 tasks, 13 units)                                                                    |
| Constraint focus     | Parser-specific (tolerant extraction, parseValidTime reuse, cross-references) | Architecture-specific (Format First ordering, `.js` extensions, `import type`, barrel exports, zero business logic) |
| Scope boundaries     | Per-parser isolation (don't touch other parsers)                              | Per-file isolation (each task owns specific files)                                                                  |
| Primary references   | P5 Implementation Guide, Parsing Coverage Audit                               | P6 Implementation Guide, Task Granularity Review, Design Decision Resolution Report                                 |
| Blueprint references | `extractCSAPIFeature()`, SensorML sub-parsers                                 | `formats/index.ts` barrel, EDR `endpoint.edr()` factory, existing `package.json` exports                            |
| Testing requirements | 8+ test cases per parser, fixture-based                                       | Minimal (2 factory tests, `tsc --noEmit` per task, full suite at commit boundaries)                                 |
| Finding categories   | Code bug, server limitation, parser gap                                       | Boundary violation, export gap, type error, test regression                                                         |
| Labels               | 12 labels (incl. `parser`)                                                    | 7 labels (incl. `formatting`, `architecture`, `verification`)                                                       |
| Template B triggers  | Smoke test findings                                                           | Verification gate failures, code review findings                                                                    |
