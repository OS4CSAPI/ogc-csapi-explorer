# A2 Execution Prompt — Prompt 1 of 2

**Checks covered:** 1-5 (ROADMAP vs Implementation Guide) + 6-7 (Test File Inventory + Cadence)  
**Split rationale:** These 7 checks are structural/mechanical comparisons clustered around the ROADMAP, Implementation Guide, and Doc 19. Prompt 2 handles the qualitative/audit checks (8-12) with different source documents.

---

## Prompt

Execute research plan A2 (Prompt 1 of 2): **ROADMAP ↔ Implementation Guide structural alignment + test inventory/cadence checks.**

The research plan is at: `docs/research/pre-implementation-alignment/A2-research-plan-roadmap-vs-implementation-guide-and-test-research.md`

Read the full research plan first to understand the complete scope, then execute **Checks 1-7 only** in this prompt.

### Documents to read:

**Read first:**

- `docs/research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md` (~465 lines) — understand what A1 already resolved so you don't re-flag resolved items

**Anchor document:**

- `docs/planning/ROADMAP.md` (v3.0, ~712 lines) — read in full. Extract all 34 tasks, all estimates, all "Test immediately" sections, all file paths.

**Source of Truth #1:**

- `docs/planning/csapi-implementation-guide.md` (~4,488 lines) — read these sections:
  - §5 (Service Discovery & Integration, lines ~303-478) — for Check 1
  - §6 (QueryBuilder, lines ~481-2000) — for Checks 1, 3 (method inventory at lines ~1193-1715)
  - §7 (Format Handlers, lines ~2248-2926) — for Check 1
  - §8 (Worker Extensions, lines ~2929-2982) — for Check 1
  - §13 (Timeline & Estimates) — for Check 2
  - §14 (File Inventory) — for Check 4

**Source of Truth #2 (for Checks 6-7):**

- `docs/research/testing/findings/19-test-organization-file-structure.md` (~1,488 lines) — authoritative test file inventory

### Important context:

- The Implementation Guide and Test Research are the **stronger sources of truth** after A1 resolution. The ROADMAP is the document most likely to need updates.
- The Implementation Guide is now ~4,488 lines (post-A1), up from the ~4,200 stated in the research plan. This is expected — A1 added ~288 lines of enrichments.
- The ROADMAP is 712 lines (plan says 713 — negligible).
- `sortBy`/`sortOrder` was brought back into scope (MEDIUM priority) after A1 — if the ROADMAP still shows it as deferred, flag it.

### What to do:

**Part I — ROADMAP vs Implementation Guide (Checks 1-5):**

1. **Check 1 (Task-Component Mapping):** Read the ROADMAP task list (all 34 tasks across 4 phases). For each task, verify the component it references exists in the Implementation Guide at the stated section. Then reverse: read Implementation Guide §5-§8 to extract all major components and verify each has at least one ROADMAP task. Flag orphan tasks (ROADMAP task for non-existent component) or uncovered components (guide component with no ROADMAP task). Produce a mapping matrix.

2. **Check 2 (Estimate Consistency):** Read the ROADMAP summary table (near end of document, line ~610+). Read Implementation Guide §13 for its estimates. Compare: total hours, implementation lines, test lines, implementation files, test files. Flag discrepancies >20%. Check whether any A1 findings changed estimates (A1 added ~288 lines to the guide but didn't change the estimate tables). Produce a reconciliation table.

3. **Check 3 (Method Count Accuracy):** Sum the method counts listed in ROADMAP Phase 2 tasks (Systems: 12, Deployments: 8, Procedures: 8, Sampling Features: 8, Properties: 6, DataStreams: 11, Observations: 9, Control Streams: 8, Commands: 10 = 80 total). For each resource type, go to the corresponding section in Implementation Guide §6 (lines ~1193-1715) and count the actual methods listed. Compare per-resource-type counts. Check that method names match. Produce a per-resource reconciliation table.

4. **Check 4 (File/Directory Structure):** Extract every file path mentioned or implied by ROADMAP tasks (model.ts, helpers.ts, url*builder.ts, endpoint.ts, info.ts, index.ts, formats/sensorml/*.ts, formats/swecommon/\_.ts, formats/constants.ts, formats/index.ts, test files). Compare against Implementation Guide §14 file inventory. Pay special attention to:

   - Fixture directory: should be `fixtures/csapi/sample-server/` with URL-path-mirroring convention (per A1 Prompt 3 C7-M1 update)
   - `formats/` subdirectory structure consistency
   - Any files in one document but not the other

5. **Check 5 (Phase Dependencies):** Verify the stated inter-phase dependencies (Phase 1→2, Phase 2→3, Phases 1-3→4). Check intra-phase dependencies within Phase 3 (SWE Common types before SensorML parsers that consume them). Check whether any A1 updates changed component relationships that affect phasing.

**Part II — ROADMAP vs Test Research (Checks 6-7 only):**

6. **Check 6 (Test File Inventory):** Compare ROADMAP's stated test file count (17 files) against Doc 19's authoritative inventory (22 files). List the 5 files present in Doc 19 but not in the ROADMAP (or vice versa). Check whether this discrepancy was flagged in A1 — it was (A1 Pass 1 Check 3, D1: "File Count (17 vs 22) — Medium Severity"). Verify whether the ROADMAP was updated during A1 (it likely was NOT — A1 focused on the guide and test research, not the ROADMAP). Flag for resolution.

7. **Check 7 (Testing Cadence):** For each of the 34 ROADMAP tasks, identify:
   - (a) Estimated implementation lines for that task
   - (b) Estimated hours for that task
   - (c) Whether the task has a "Test immediately" section
     Verify: no single task produces >800 implementation lines without tests, no task exceeds ~3 hours without a test checkpoint. Count total test checkpoints (should be ~34, one per task). Produce a cadence compliance matrix.

### Output format:

Save **interim findings** to `docs/research/pre-implementation-alignment/findings/A2-prompt-1-interim-findings.md` with:

1. **Summary** — checks completed, finding count by severity
2. **Check 1 Findings** — mapping matrix + orphan/uncovered flags
3. **Check 2 Findings** — estimate reconciliation table + discrepancies
4. **Check 3 Findings** — per-resource method count reconciliation
5. **Check 4 Findings** — file inventory comparison
6. **Check 5 Findings** — dependency validation
7. **Check 6 Findings** — test file inventory comparison
8. **Check 7 Findings** — cadence compliance matrix

Each finding should have: severity (Critical/High/Medium/Low/Info), description, specific ROADMAP line reference, corresponding source document reference, and recommended resolution.

**Do NOT commit yet** — Prompt 2 will merge interim findings into the final report, then commit.
