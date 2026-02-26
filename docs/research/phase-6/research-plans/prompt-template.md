# Prompt Template: Request Creation of a Research Plan

**Purpose:** Use this template to request the AI assistant to create a single research plan document that follows the standardized format. Copy, fill in the blanks, and submit as your prompt.

---

## How to Use

1. Copy the prompt below
2. Replace all `[PLACEHOLDER]` values with your specifics
3. Submit as your message to the AI assistant
4. The assistant will create the research plan in the correct location using the template

---

## The Prompt

```
Please create Research Plan [PLAN_NUMBER] for Phase 6.

**Title:** [PLAN_TITLE]

**Plan Type:** [Internal analysis / External research (industry) / External research (architecture) / External research (standards) / Design synthesis / Implementation synthesis / Mechanical analysis]

**Objective:** [2-3 sentences describing what this research will investigate and what concrete output it will produce]

**Sequencing:** This is Plan [N] of [TOTAL]. It depends on [PLAN_NUMBERS_OR_NONE] and blocks [PLAN_NUMBERS_OR_NONE].

**Boundary conditions that apply:**
- [List the specific constraints from the research strategy that scope this plan]
- [Include what is explicitly excluded from scope]

**What's open for exploration:**
- [List the genuine open questions this plan should investigate]

**Key research questions to answer:**
1. [Core question 1]
2. [Core question 2]
3. [Core question 3]
[Add more as needed — these become the Core Questions in Section 4]

**Sources to consult:**
- In workspace: [file paths]
- External: [URLs, documentation, repos, specs]
- Prior findings: [which earlier plan findings to build on]

**Methodology notes:** [Any specific phases, tasks, or approaches you want the plan to follow. Leave blank if the assistant should design the methodology.]

**Risks to address:**
- [Known risks or concerns about this research]

Use the research plan template at:
docs/research/phase-6/research-plans/research-plan-template.md

Place the completed plan at:
docs/research/phase-6/research-plans/[NN]-[slug].md

Commit and push to the phase-6 branch.
```

---

## Example: Filled-In Prompt

```
Please create Research Plan 01 for Phase 6.

**Title:** Upstream Build System and Entry Point Analysis

**Plan Type:** Internal analysis

**Objective:** Understand how ogc-client builds, bundles, and exposes its public API so we can add a ./csapi entry point correctly. Produce a complete build pipeline analysis with a proven package.json "exports" configuration for "./csapi".

**Sequencing:** This is Plan 1 of 8. It depends on None and blocks Plan 03 (Separate Entry Point Design Patterns).

**Boundary conditions that apply:**
- The entry point MUST be "./csapi" mapping to CSAPI module code only (constraint 2)
- Do not explore shared or merged entry point configurations (constraints 1, 3)

**What's open for exploration:**
- Whether the build system supports multiple entry points natively or needs config changes
- What barrel file structure to use for the CSAPI entry point
- How TypeScript declaration files should be generated for the sub-path

**Key research questions to answer:**
1. How does package.json "exports" map to dist output?
2. What does esbuild do with the find ./src -name "*.ts" command?
3. How does vite build (node and worker configs) handle entry points?
4. What changes to package.json "exports" are needed for "./csapi"?
5. Does tree-shaking work automatically or is the separate entry point strictly necessary?

**Sources to consult:**
- In workspace: package.json, vite.node-config.js, vite.worker-config.js, tsconfig.json
- External: esbuild docs, vite docs, Node.js package exports docs
- Prior findings: None (first plan)

**Methodology notes:** Build locally and inspect dist/ output as part of the analysis.

**Risks to address:**
- Build system may not support multiple entry points without config changes
- vite-plugin-dts may not generate declarations for sub-path exports

Use the research plan template at:
docs/research/phase-6/research-plans/research-plan-template.md

Place the completed plan at:
docs/research/phase-6/research-plans/01-build-system-entry-point-analysis.md

Commit and push to the phase-6 branch.
```

---

## Quick Reference: Phase 6 Plans

| #   | Title                                          | Type                     | Depends On     | Blocks |
| --- | ---------------------------------------------- | ------------------------ | -------------- | ------ |
| 01  | Upstream Build System and Entry Point Analysis | Internal analysis        | —              | 03     |
| 02  | EDR Integration Pattern Analysis               | Internal analysis        | —              | 06     |
| 03  | Separate Entry Point Design Patterns           | External (packaging)     | 01             | 06     |
| 04  | TypeScript Sub-Module API Design Patterns      | External (industry)      | —              | 06     |
| 05  | Module Decoupling Patterns in TypeScript       | External (architecture)  | —              | 06     |
| 06  | Endpoint Decoupling Architecture               | Design synthesis         | 02, 03, 04, 05 | 08     |
| 07  | Prettier and ESLint Configuration Analysis     | Mechanical               | —              | 08     |
| 08  | File-Level Changelist and Commit Strategy      | Implementation synthesis | 01–07          | —      |

---

## Tips for Best Results

1. **Be specific about boundary conditions.** The more explicit you are about what's in and out of scope, the more focused the plan will be.

2. **List your key questions.** Don't leave core questions for the assistant to guess — you know what you need answered.

3. **Reference prior findings.** If this plan builds on earlier research, say which findings to consult and what to extract from them.

4. **Mention methodology preferences.** If you want local testing, external documentation review, or code analysis, say so.

5. **One plan per prompt.** Create plans one at a time so you can review each before proceeding to the next.
