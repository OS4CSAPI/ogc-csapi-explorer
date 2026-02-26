# A2 Execution Prompt

**Use this prompt to execute the A2 research plan. Copy everything below the line.**

---

## Prompt

Execute research plan A2: **ROADMAP ↔ Implementation Guide + Test Research Alignment**.

The research plan is at: `docs/research/pre-implementation-alignment/A2-research-plan-roadmap-vs-implementation-guide-and-test-research.md`

Read the full research plan first, then execute all 12 checks systematically. Here is the execution guidance:

### Documents to cross-reference:

**Anchor:** `docs/planning/ROADMAP.md` (v3.0, ~713 lines)

**Source of Truth #1:** `docs/planning/csapi-implementation-guide.md` (v7.0+, ~4,200+ lines — post-A1 updates)

**Source of Truth #2:** Test research corpus — 38 findings documents in `docs/research/testing/findings/` and 13 review files in `docs/research/testing/review/`

**A1 Report:** `docs/research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md` — read this first to understand what was already resolved

### Important context:

The Implementation Guide and Test Research are the **stronger sources of truth** after A1 resolution. This step primarily checks the ROADMAP against them and updates the ROADMAP where needed. The reverse direction (Check 12) is lightweight — only flagging ROADMAP-specific structural decisions the other documents should acknowledge.

### What to do:

**Part I — ROADMAP vs Implementation Guide (Checks 1-5):**

1. **Check 1 (Task-Component Mapping):** Read the ROADMAP task list (all 34 tasks across 4 phases). For each task, verify the component it references exists in the Implementation Guide at the stated section and line numbers. Then reverse: read Implementation Guide §5-§8 to extract all 12 components and verify each has at least one ROADMAP task. Flag orphan tasks or uncovered components.

2. **Check 2 (Estimate Consistency):** Read the ROADMAP summary table (line ~635). Read Implementation Guide §13 for its estimates. Compare total hours, implementation lines, test lines, implementation files, test files. Flag discrepancies >20%. Check whether A1 findings changed any estimates.

3. **Check 3 (Method Count Accuracy):** Sum the method counts listed in ROADMAP Phase 2 tasks (Systems: 12, Deployments: 8, Procedures: 8, Sampling Features: 8, Properties: 6, DataStreams: 11, Observations: 9, Control Streams: 8, Commands: 10 = 80 total). Verify each count against Implementation Guide §6 resource type sections (lines 1193-1715). Check method names match.

4. **Check 4 (File/Directory Structure):** Extract every file path implied by ROADMAP tasks (model.ts, helpers.ts, url*builder.ts, endpoint.ts, info.ts, index.ts, formats/sensorml/*.ts, formats/swecommon/\_.ts, formats/constants.ts, formats/index.ts). Compare against Implementation Guide §14 file inventory. Check fixture directory path is `fixtures/csapi/` not `fixtures/ogc-api/csapi/`.

5. **Check 5 (Phase Dependencies):** Verify stated dependencies (Phase 1→2→3→4). Check intra-phase dependencies (Phase 3: SWE Common types before SensorML types). Check whether any A1 updates changed component relationships.

**Part II — ROADMAP vs Test Research (Checks 6-11):**

6. **Check 6 (Test File Inventory):** Compare ROADMAP's 17 test files against Doc 19's 22-file authoritative inventory. If A1 resolved this discrepancy, verify the ROADMAP was updated. List any files present in one inventory but not the other.

7. **Check 7 (Testing Cadence):** For each of the 34 ROADMAP tasks, calculate: (a) max implementation lines before tests, (b) max hours before tests. Verify no task exceeds 800 lines without tests or 3 hours without tests. Count total test checkpoints.

8. **Check 8 (Scope Boundaries):** Verify the ROADMAP does NOT include dedicated tasks for: performance testing, real-world server testing, migration testing. Check ROADMAP Phase 4 Task 1 for `PARSE_SWE_BINARY` — this worker message type is correctly deferred along with the rest of Doc 16 (Phase 4). Binary SWE parsing at the parser level (Doc 10) is in scope.

9. **Check 9 (Anti-Pattern Audit):** Read every "Test immediately" section across all 34 ROADMAP tasks. For each, check whether the test descriptions could lead to AP1 (testing response content), AP3 (server conformance testing), or AP4 (asserting data shape) violations. Flag problematic language and recommend rewording.

10. **Check 10 (Coverage and Estimates):** Verify ROADMAP's >80% coverage target matches test research (>80% mandatory, 85-95% aspirational). Sum per-phase test line estimates (Phase 1: ~400-550, Phase 2: ~800-1,000, Phase 3: ~2,400-3,500, Phase 4: ~800-1,250 = ~4,400-6,300 total). Compare against Doc 19's authoritative ~4,040-5,340.

11. **Check 11 (Development Standards):** Compare ROADMAP's Development Standards section (near end of document, ~70 lines) against Implementation Guide §16. Check whether the ROADMAP references: AP1-AP5 anti-pattern catalog, "meaningful vs trivial" standard, `globalThis.fetch` mocking, three-tier imports, 31-checkpoint cadence. Flag any standards present in one document but not the other.

**Part III — Reverse Check (Check 12):**

12. **Check 12 (Phase Structure Feedback):** Identify ROADMAP-specific decisions: 4-phase model, Phase 3 restructure (7→17 tasks), 34 total checkpoints, calendar time estimates. For each, check whether Implementation Guide §13 or test research documents reference it. Flag gaps. This check should be lightweight — most structure is already derived from the Implementation Guide.

### Output format:

Generate a report saved to `docs/research/pre-implementation-alignment/findings/A2-roadmap-vs-implementation-guide-and-test-research-report.md` with:

1. **Executive Summary** — overall alignment status, total finding count by severity
2. **Part I Findings** — one subsection per check (1-5), each finding with severity (Critical/High/Medium/Low), description, specific line references in the ROADMAP, corresponding section in the Implementation Guide, and recommended resolution
3. **Part II Findings** — one subsection per check (6-11), each finding with severity, description, ROADMAP reference, test research document reference, and recommended resolution
4. **Part III Findings** — Check 12 reverse feedback (expected to be brief)
5. **Recommendations** — prioritized action list
6. **Acceptance Criteria Checklist** — the 12 checkboxes from the research plan, marked pass/fail

Commit the report and push when complete. Use commit message format: `docs(alignment): A2 report — ROADMAP vs Implementation Guide + Test Research findings`
