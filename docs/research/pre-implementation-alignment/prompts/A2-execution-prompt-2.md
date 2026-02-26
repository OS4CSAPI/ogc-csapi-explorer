# A2 Execution Prompt — Prompt 2 of 2

**Checks covered:** 8-12 (Scope Boundaries, Anti-Pattern Audit, Coverage/Estimates, Development Standards, Reverse Check)  
**Prerequisite:** Prompt 1 interim findings at `docs/research/pre-implementation-alignment/findings/A2-prompt-1-interim-findings.md`  
**Split rationale:** These checks are qualitative/audit-oriented, require different source documents (Phase 0, Doc 06, Doc 20, Phase 2E), and the anti-pattern audit (Check 9) is the single most labor-intensive check.

---

## Prompt

Execute research plan A2 (Prompt 2 of 2): **ROADMAP scope/quality checks + reverse feedback + final report assembly.**

The research plan is at: `docs/research/pre-implementation-alignment/A2-research-plan-roadmap-vs-implementation-guide-and-test-research.md`

**Prompt 1 interim findings are at:** `docs/research/pre-implementation-alignment/findings/A2-prompt-1-interim-findings.md` — read this first to understand what Checks 1-7 found.

### Documents to read:

**Read first:**

- `docs/research/pre-implementation-alignment/findings/A2-prompt-1-interim-findings.md` — Prompt 1's findings for Checks 1-7
- `docs/research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md` (~465 lines) — A1 context

**Anchor document:**

- `docs/planning/ROADMAP.md` (v3.0, ~712 lines) — read in full. Focus on:
  - Every "Test immediately" section across all 34 tasks (for Check 9)
  - Phase 4 Task 1 worker extensions (for Check 8)
  - Development Standards section near end of document (for Check 11)
  - Summary table (for Check 10)

**Source of Truth #1 (for Checks 11-12):**

- `docs/planning/csapi-implementation-guide.md` — read these sections only:
  - §9 (Testing Strategy) — for Check 8 scope boundaries
  - §13 (Timeline & Estimates) — for Check 12 reverse check
  - §16 (Development Standards) — for Check 11

**Source of Truth #2 (test research documents for Checks 8-11):**

- `docs/research/testing/review/phase-0-lessons-from-failed-attempt.md` (~335 lines) — AP1-AP5 anti-pattern definitions for Check 9
- `docs/research/testing/review/phase-2e-advanced-scenarios-category.md` (~571 lines) — scope boundary decisions for Check 8
- `docs/research/testing/findings/20-test-to-code-ratio-validation.md` (~1,243 lines) — coverage targets for Check 10
- `docs/research/testing/findings/06-meaningful-vs-trivial-definition.md` (~2,320 lines) — testing standard for Check 11
- `docs/research/testing/findings/19-test-organization-file-structure.md` (~1,488 lines) — authoritative estimates for Check 10

### Important context:

- The Implementation Guide and Test Research are the **stronger sources of truth**. The ROADMAP is the document most likely to need updates.
- `sortBy`/`sortOrder` was brought back into scope (MEDIUM priority) after A1 — verify the ROADMAP doesn't still defer it.
- Check 9 (anti-pattern audit) is the most labor-intensive check. Read every "Test immediately" section in the ROADMAP and evaluate each against AP1 (testing response content), AP3 (server conformance), and AP4 (data shape assertions). Be specific about problematic language — quote it and recommend rewording.
- Binary SWE parsing (Doc 10) is IN SCOPE at the parser level. Only the `PARSE_SWE_BINARY` _worker message type_ (Doc 16) is deferred to Phase 4.

### What to do:

**Part II — ROADMAP vs Test Research (Checks 8-11):**

8. **Check 8 (Scope Boundaries):** Verify the ROADMAP does NOT include dedicated tasks for:

   - Performance testing (Doc 33 — fully out of scope)
   - Real-world server testing (Doc 32 — AP2, out of scope)
   - Migration testing (not defined anywhere)

   Verify the ROADMAP DOES include:

   - Binary SWE parsing at the parser level (Doc 10, in scope per Phase 2D assessment)
   - `PARSE_SWE_BINARY` worker message type in Phase 4 Task 1 (correctly deferred with all worker extensions)

   Check Implementation Guide §9 for the OUT OF SCOPE exclusions added during A1 (performance testing, real-world server testing). Verify consistency with ROADMAP.

9. **Check 9 (Anti-Pattern Audit):** This is the most important check. Read every "Test immediately" section across all 34 ROADMAP tasks. For each task's test guidance, check whether the language could lead a developer to write:

   - **AP1 violations** — testing response content (e.g., "verify the response contains...", "check that the server returns...")
   - **AP3 violations** — server conformance testing (e.g., "verify conformance to OGC spec...", "test that the endpoint supports...")
   - **AP4 violations** — asserting data shape without testing transformation (e.g., "verify the response structure...", "check the response has fields...")

   For each flagged instance: quote the problematic text, identify which anti-pattern it risks, and recommend specific rewording that focuses on client behavior (URL construction, response parsing, error handling).

   Produce a per-task audit table.

10. **Check 10 (Coverage and Estimates):**

    - Verify ROADMAP's >80% coverage target matches Doc 20's reconciled target (>80% mandatory floor, 85-95% aspirational)
    - Sum ROADMAP per-phase test line estimates: Phase 1 (~400-550), Phase 2 (~800-1,000), Phase 3 (~2,400-3,500), Phase 4 (~800-1,250) = ~4,400-6,300 total
    - Compare against Doc 19's authoritative ~4,040-5,340
    - Flag if ranges don't overlap or if ROADMAP upper bound seems optimistic
    - Produce a reconciliation table

11. **Check 11 (Development Standards):** Compare the ROADMAP's Development Standards section (~70 lines near end of document) against Implementation Guide §16. Check whether the ROADMAP references each of these conventions (all should be present after A1 updates to §16):

    - AP1-AP5 anti-pattern catalog with Phase 0 report link
    - "Meaningful vs trivial" test standard (Doc 06)
    - `globalThis.fetch` mocking convention
    - Three-tier imports (`import type` / named / default)
    - Incremental testing cadence (max 2-3 hrs, max 800 LOC between checkpoints)

    Flag any standards present in the Implementation Guide §16 but missing from the ROADMAP, or vice versa. Produce a comparison matrix.

**Part III — Reverse Check (Check 12):**

12. **Check 12 (Phase Structure Feedback):** Identify ROADMAP-specific structural decisions that the Implementation Guide or test research should cross-reference:

    - 4-phase sequential model with explicit dependencies
    - Phase 3 restructure from 7 tasks to 17 (v3.0 change)
    - 34 total tasks as granular test checkpoints
    - Calendar time estimates (8-12 weeks at 6-8 hrs/week)
    - "Test immediately after each subtask" as a workflow rule

    For each, check whether Implementation Guide §13 (Timeline) or §9 (Testing) references it. This check should be lightweight — flag genuine gaps only.

### Output format:

Generate the **final A2 report** at `docs/research/pre-implementation-alignment/findings/A2-roadmap-vs-implementation-guide-and-test-research-report.md` by:

1. **Merging** Prompt 1's interim findings (Checks 1-7) with Prompt 2's findings (Checks 8-12) into a single coherent report
2. **Delete** the interim file (`A2-prompt-1-interim-findings.md`) after merging — it should not persist

**Final report structure:**

1. **Executive Summary** — overall alignment status, total finding count by severity across all 12 checks, comparison to A1 (expected: fewer Critical/High findings since A1 already resolved guide/test-research alignment)
2. **Part I Findings (Checks 1-5)** — one subsection per check, each finding with severity, description, ROADMAP line reference, Implementation Guide section reference, recommended resolution
3. **Part II Findings (Checks 6-11)** — one subsection per check, each finding with severity, description, ROADMAP reference, test research document reference, recommended resolution
4. **Part III Findings (Check 12)** — reverse feedback items
5. **Recommendations** — prioritized action list (Critical → High → Medium → Low), grouped by target document (ROADMAP updates vs Implementation Guide updates vs test research updates)
6. **Acceptance Criteria Checklist** — the 12 acceptance criteria from the research plan, each marked ✅ Pass or ❌ Fail with a one-line justification

**Commit and push** the final report (with interim file deleted). Use commit message: `docs(alignment): A2 report — ROADMAP vs Implementation Guide + Test Research findings`
