# A1 Execution Prompt — 3-Pass Structure

**This research plan is split into 3 passes to ensure full-depth cross-referencing.**  
**Execute one pass at a time. Each pass commits interim findings. Pass 3 assembles the final report.**

---

## Pass 1: Forward Checks (Checks 1-4)

**Copy everything in this section to execute Pass 1.**

### Prompt

Execute **Pass 1 of 3** for research plan A1: **Test Research ↔ Implementation Guide Bidirectional Alignment**.

The research plan is at: `docs/research/pre-implementation-alignment/A1-research-plan-test-research-vs-implementation-guide.md`

Read the full research plan first for context, then execute **only Checks 1-4** with full depth.

### Documents to read:

**Anchor:** `docs/planning/csapi-implementation-guide.md` (v7.0, ~4,200 lines)

**Test Research Corpus:** 38 findings documents in `docs/research/testing/findings/` (Docs 01-38 plus Doc 15 Part 2) and 13 review files in `docs/research/testing/review/` (Phase 0-4 reports, notes, verified conformance URIs)

### What to do (Checks 1-4 only):

1. **Check 1 (Component Coverage):** Read implementation guide §5-§8 (lines 301-2982) to extract all 12 components. For each component, read the corresponding test research document(s) listed in the research plan's cross-reference map. Rate each as Complete/Partial/Missing. Document gaps.

2. **Check 2 (Method-Level Coverage):** Read implementation guide §6 resource method sections (lines 1193-1715) to extract every QueryBuilder method signature across all 9 resource types. Cross-reference each method against Doc 12's method inventory (Sections 5-13). Identify any methods without test scenarios.

3. **Check 3 (Estimate Consistency):** Read implementation guide §9 and §13 for test estimates. Read Doc 19 executive summary for the authoritative file inventory. Read Doc 20 for test-to-code ratios. Read ROADMAP summary table. Reconcile all numbers into one table. Flag discrepancies >20%.

4. **Check 4 (Orphan Detection):** Scan each test research document's Document Purpose header. Verify the tested component exists in the implementation guide. Flag any test specs for non-existent components (expect Docs 32, 33 to be properly flagged already).

### Output for Pass 1:

Generate interim findings saved to `docs/research/pre-implementation-alignment/findings/A1-pass-1-forward-checks.md` with:

1. **Pass 1 Summary** — findings count by severity for Checks 1-4
2. **Check 1 Findings** — coverage matrix (Complete/Partial/Missing per component) with gap details
3. **Check 2 Findings** — method-by-method matrix showing which have test scenarios and which don't
4. **Check 3 Findings** — estimate reconciliation table with discrepancies flagged
5. **Check 4 Findings** — orphan list with disposition

Commit and push. Use commit message: `docs(alignment): A1 Pass 1 — Forward checks (1-4) interim findings`

**Stop after committing. Do not proceed to Pass 2 in this session.**

---

## Pass 2: Reverse Checks (Checks 5-8)

**Copy everything in this section to execute Pass 2. Run this AFTER Pass 1 is committed.**

### Prompt

Execute **Pass 2 of 3** for research plan A1: **Test Research ↔ Implementation Guide Bidirectional Alignment**.

The research plan is at: `docs/research/pre-implementation-alignment/A1-research-plan-test-research-vs-implementation-guide.md`

Read the Pass 1 interim findings first: `docs/research/pre-implementation-alignment/findings/A1-pass-1-forward-checks.md`

Then execute **only Checks 5-8** with full depth.

### Documents to read:

**Anchor:** `docs/planning/csapi-implementation-guide.md` (v7.0, ~4,200 lines)

**Review Reports:** Phase 0-4 reports in `docs/research/testing/review/` — these are the primary sources for reverse checks

**Key Test Research Docs for this pass:**

- Phase 0 report — client responsibilities (5), anti-patterns (AP1-AP5)
- Phase 1-4 reports — scope decisions, corrections
- Doc 08 — CSAPI spec test requirements
- Doc 15/15P2 — fixture strategy
- Doc 26 — 16 parent-child relationships
- Doc 28 — temporal query patterns
- Doc 29 — spatial query patterns
- Doc 31 — command state machine
- Doc 34 — test utilities, `parseAndValidateUrl` signature

### What to do (Checks 5-8 only):

5. **Check 5 (Scope Decisions):** Read Phase 0-4 review reports for every scope-altering finding. For each, check whether the implementation guide reflects it. Key decisions to check: performance testing OUT OF SCOPE, real-world server testing rejected, `PARSE_SWE_BINARY` worker offloading deferred (binary parsing itself is in scope per Doc 10/Phase 2D), worker extensions Phase 4 only, `_metadata` pattern rejected, enterprise review simplified, incremental testing cadence.

6. **Check 6 (Client Responsibility Model):** Read Phase 0 report for the 5 client responsibilities (Parse, Construct, Transform, Handle, Validate). Check whether implementation guide §3 or §4 states them. Scan implementation guide code examples in §6, §7, §11, §12 for any that test server behavior rather than client behavior.

7. **Check 7 (Architectural Patterns):** Check implementation guide for: (a) `parseAndValidateUrl` signature — does it use `hostname` (correct) or `host`? (b) fixture directory — `fixtures/csapi/` (correct) or `fixtures/ogc-api/csapi/`? (c) test file count — 17 (original) or 22 (Doc 19)? (d) test utility structure from Doc 34? (e) any SensorThings API terminology? (f) QueryBuilder-not-standalone-clients warning?

8. **Check 8 (Specification Details):** Read Doc 08 (CSAPI spec test requirements), Doc 26 §1 (16 parent-child relationships), Doc 28 (temporal patterns), Doc 29 (spatial patterns), Doc 31 (command state machine). For each, check whether the implementation guide's corresponding section contains equivalent detail or could benefit from enrichment.

### Output for Pass 2:

Generate interim findings saved to `docs/research/pre-implementation-alignment/findings/A1-pass-2-reverse-checks.md` with:

1. **Pass 2 Summary** — findings count by severity for Checks 5-8
2. **Check 5 Findings** — scope decision propagation status table
3. **Check 6 Findings** — client responsibility audit with examples flagged
4. **Check 7 Findings** — architectural consistency checklist with line references
5. **Check 8 Findings** — specification enrichment opportunities table

Commit and push. Use commit message: `docs(alignment): A1 Pass 2 — Reverse checks (5-8) interim findings`

**Stop after committing. Do not proceed to Pass 3 in this session.**

---

## Pass 3: Bidirectional Checks + Final Report Assembly (Checks 9-12)

**Copy everything in this section to execute Pass 3. Run this AFTER Pass 2 is committed.**

### Prompt

Execute **Pass 3 of 3** for research plan A1: **Test Research ↔ Implementation Guide Bidirectional Alignment**.

The research plan is at: `docs/research/pre-implementation-alignment/A1-research-plan-test-research-vs-implementation-guide.md`

Read both interim findings first:

- `docs/research/pre-implementation-alignment/findings/A1-pass-1-forward-checks.md`
- `docs/research/pre-implementation-alignment/findings/A1-pass-2-reverse-checks.md`

Then execute **Checks 9-12** with full depth, and assemble the final consolidated report.

### Documents to read:

**Anchor:** `docs/planning/csapi-implementation-guide.md` (v7.0, ~4,200 lines) — focus on §9, §16

**Key Test Research Docs for this pass:**

- Phase 0 report — AP1-AP5 anti-pattern definitions
- Doc 06 — meaningful vs trivial test standard
- Doc 15 §5.2 — revised fixture structure
- Doc 15 Part 2 — no embedded metadata finding
- Doc 19 — authoritative file inventory
- Implementation guide §6, §7, §11, §12 — code examples to audit

### What to do (Checks 9-12, then consolidate):

9. **Check 9 (Convention Alignment):** Read implementation guide §16 (Development Standards). Cross-reference against test research conventions: `globalThis.fetch` mocking, `*.spec.ts` naming, three-tier imports, JSDoc, error handling. Then reverse: check whether §16 references the anti-pattern catalog, "meaningful vs trivial" standard, or incremental testing cadence.

10. **Check 10 (Anti-Pattern Compliance):** Read Phase 0's AP1-AP5 definitions. Scan implementation guide §6, §7, §11, §12 code examples for any that would produce anti-pattern violations if a developer followed them literally as test templates.

11. **Check 11 (Fixture Strategy):** Read implementation guide §9 fixture references. Compare against Doc 15 §5.2 (revised structure) and Doc 15 Part 2 (no embedded metadata). Check whether the implementation guide uses outdated fixture paths or patterns.

12. **Check 12 (Terminology):** Search implementation guide for: "integration test", "end-to-end", "e2e", "ObservedProperties", "Sensors", "FeaturesOfInterest", "SensorThings" — flag any incorrect usage. Verify the 9 CSAPI resource type names are used consistently.

### Final Report Assembly:

After completing Checks 9-12, consolidate ALL findings from Pass 1, Pass 2, and Pass 3 into the final report saved to `docs/research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md` with:

1. **Executive Summary** — overall alignment status, total finding count by severity across all 12 checks
2. **Part I Findings** — one subsection per check (1-4), each finding with severity (Critical/High/Medium/Low), description, specific line references, and recommended resolution (incorporate from Pass 1 interim)
3. **Part II Findings** — one subsection per check (5-12), each finding with severity, description, what the implementation guide currently says (with line reference), what the test research says (with document reference), and recommended update (incorporate from Pass 2 interim + new Pass 3 findings)
4. **Recommendations** — prioritized action list across all 12 checks
5. **Acceptance Criteria Checklist** — the 12 checkboxes from the research plan, marked pass/fail

Commit and push the final report. Use commit message: `docs(alignment): A1 report — Test Research ↔ Implementation Guide findings`

The Pass 1 and Pass 2 interim files may be kept for reference or deleted — they are superseded by the final report.
