# Prompt Template: Request Creation of a Findings Report

**Purpose:** Use this template to request the AI assistant to execute a research plan and produce its findings report. Copy, fill in the blanks, and submit as your prompt.

---

## How to Use

1. Copy the prompt below
2. Replace all `[PLACEHOLDER]` values with your specifics
3. Ensure the research plan has been created and reviewed before starting
4. Submit as your message to the AI assistant
5. The assistant will execute the research plan and create the findings report

---

## The Prompt

```
Please execute Research Plan [PLAN_NUMBER] and produce its findings report.

**Research Plan:** [PLAN_NUMBER] — [PLAN_TITLE]
**Plan Location:** docs/research/phase-6/research-plans/[NN]-[slug].md

**Prior findings to consult first:**
- [List findings reports from prerequisite plans that should be read before starting]
- [e.g., "Plan 02 findings: docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md"]

**Execution guidance:**
- [Any specific focus areas, known constraints, or methodology adjustments]
- [e.g., "Focus especially on Question 14 — the `scanCsapiLinks` placement"]
- [e.g., "The OpenSensorHub server is down, skip live server testing"]
- [Leave blank if the plan should be executed as-written]

**Scope reminder:**
- Answer all detailed questions in the plan with specific, evidenced answers
- Respect all boundary conditions from the plan's Section 3
- Apply the minimum-change test for any implementation recommendations
- Document what downstream plans should consume from these findings

Use the findings report template at:
docs/research/phase-6/findings/findings-report-template.md

Place the completed findings report at:
docs/research/phase-6/findings/[NN]-[slug].md

Commit and push to the phase-6 branch.
```

---

## Example: Filled-In Prompt

```
Please execute Research Plan 01 and produce its findings report.

**Research Plan:** 01 — Upstream Build System and Entry Point Analysis
**Plan Location:** docs/research/phase-6/research-plans/01-build-system-entry-point-analysis.md

**Prior findings to consult first:**
- None (Plan 01 has no dependencies)

**Execution guidance:**
- Run `npm run build` locally and inspect the `dist/` output as part of Phase 1
- Pay special attention to whether esbuild per-file output preserves CSAPI directory structure
- Check if `vite-plugin-dts` generates `.d.ts` files for CSAPI modules

**Scope reminder:**
- Answer all 42 detailed questions in the plan with specific, evidenced answers
- Respect all boundary conditions from the plan's Section 3
- Apply the minimum-change test for any implementation recommendations
- Document what Plans 03, 06, and 08 should consume from these findings

Use the findings report template at:
docs/research/phase-6/findings/findings-report-template.md

Place the completed findings report at:
docs/research/phase-6/findings/01-build-system-entry-point-analysis.md

Commit and push to the phase-6 branch.
```

---

## Example: Design Synthesis Plan (with prior findings)

```
Please execute Research Plan 06 and produce its findings report.

**Research Plan:** 06 — Endpoint Decoupling Architecture (Design Synthesis)
**Plan Location:** docs/research/phase-6/research-plans/06-endpoint-decoupling-architecture.md

**Prior findings to consult first:**
- Plan 02 findings: docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md
- Plan 03 findings: docs/research/phase-6/findings/03-separate-entry-point-design-patterns.md
- Plan 04 findings: docs/research/phase-6/findings/04-typescript-sub-module-api-design-patterns.md
- Plan 05 findings: docs/research/phase-6/findings/05-module-decoupling-patterns.md

**Execution guidance:**
- This is the critical design synthesis plan — every architectural decision is made here
- Start by reading all four prior findings reports completely before beginning Phase 1
- The Implementation Scope Gate is especially important for this plan
- For every design decision, apply the minimum-change test: does this change serve jahow's two bullet points, or does it add work he didn't request?
- If Plan 04 and Plan 05 recommendations conflict, resolve by evaluating both against boundary conditions + migration effort + developer ergonomics

**Scope reminder:**
- Answer all detailed questions with specific, evidenced answers
- Respect all boundary conditions from the plan's Section 3
- The Implementation Scope Gate assessment is REQUIRED for this plan
- Document exactly what Plan 08 should consume from these findings

Use the findings report template at:
docs/research/phase-6/findings/findings-report-template.md

Place the completed findings report at:
docs/research/phase-6/findings/06-endpoint-decoupling-architecture.md

Commit and push to the phase-6 branch.
```

---

## Quick Reference: Phase 6 Plans and Their Findings

| #   | Title                                          | Type                     | Depends On     | Prior Findings to Read     |
| --- | ---------------------------------------------- | ------------------------ | -------------- | -------------------------- |
| 01  | Upstream Build System and Entry Point Analysis | Internal analysis        | —              | None                       |
| 02  | EDR Integration Pattern Analysis               | Internal analysis        | —              | None                       |
| 03  | Separate Entry Point Design Patterns           | External (packaging)     | 01             | 01 findings                |
| 04  | TypeScript Sub-Module API Design Patterns      | External (industry)      | —              | None                       |
| 05  | Module Decoupling Patterns in TypeScript       | External (architecture)  | —              | None                       |
| 06  | Endpoint Decoupling Architecture               | Design synthesis         | 02, 03, 04, 05 | 02, 03, 04, 05 findings    |
| 07  | Prettier and ESLint Configuration Analysis     | Mechanical               | —              | None                       |
| 08  | File-Level Changelist and Commit Strategy      | Implementation synthesis | 01–07          | All prior findings (01–07) |

---

## Tips for Best Results

1. **Read the plan first.** Before submitting this prompt, read the research plan yourself to confirm it's still relevant and the questions still matter. If the plan needs updates, update it before requesting execution.

2. **Ensure prerequisites are met.** If the plan depends on earlier plans, their findings reports should exist before you start. The prompt includes prior findings for the assistant to consult.

3. **Provide execution guidance sparingly.** The research plan already specifies methodology. Only add guidance here if you have new information the plan doesn't account for (e.g., a server is down, a file has moved, a constraint has changed).

4. **One plan per prompt.** Execute plans one at a time so you can review findings before proceeding to dependent plans. This is especially important for Plan 06 (design synthesis) — review its output carefully before allowing Plan 08 to proceed.

5. **Review findings for scope creep.** After the assistant produces a findings report, review the Implementation Scope Gate Assessment section. If findings recommend work beyond jahow's two bullet points, flag it before it propagates to downstream plans.

6. **Plans with no dependencies can be parallelized.** Plans 01, 02, 04, 05, and 07 have no upstream dependencies. They can be executed in any order or in parallel sessions. Plans 03, 06, and 08 must wait for their dependencies.
