# A3 Execution Prompt

**Use this prompt to execute the A3 research plan. Copy everything below the line.**

---

## Prompt

Execute research plan A3: **Contribution Goal ↔ Implementation Guide Alignment**.

The research plan is at: `docs/research/pre-implementation-alignment/A3-research-plan-contribution-goal-vs-implementation-guide.md`

Read the full research plan first, then execute all 8 checks systematically. Here is the execution guidance:

### Documents to cross-reference:

**Subject:** `docs/planning/contribution-goal-and-definition.md` (v1.0, 32 lines — the document being verified)

**Source of Truth:** `docs/planning/csapi-implementation-guide.md` (v7.0, ~4,491 lines — post-A1/A2 updates, authoritative)

**Context:**

- `docs/research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md` — A1 findings (29 resolved)
- `docs/research/pre-implementation-alignment/findings/A2-roadmap-vs-implementation-guide-and-test-research-report.md` — A2 findings (19 actionable, all resolved)
- `docs/planning/ROADMAP.md` (v3.2) — for three-way number cross-checks

### Important context:

The Implementation Guide (post-A1/A2) is the **definitive source of truth**. The Contribution Goal is a v1.0 summary written before test research review findings and before A1/A2 alignment resolved scope and number changes. Any discrepancy should be resolved by updating the Contribution Goal.

**Key changes since Contribution Goal v1.0:**

- Method count confirmed at exactly **80** (was "70-80" everywhere, now corrected in Guide + ROADMAP)
- Test files increased from **17 → 22** (A1/A2 finding, ROADMAP + Guide updated)
- Test lines narrowed to **4,040-5,340** (was "4,500-6,000" in Guide, now aligned with Doc 19 authoritative breakdown)
- Estimates reconciled to **57-84 hours / 8-11 weeks** (Guide aligned to ROADMAP in A2)
- Grand total now **8,654-11,434 lines** (was 9,114-12,094)
- Worker extensions (9 CSAPI message types) **removed from scope** — no upstream JSON API uses workers (ROADMAP v3.1)
- Total files now **46** (24 impl + 22 test, was 41)

### What to do:

**Part I — Contribution Goal vs Implementation Guide (Checks 1-7):**

1. **Check 1 (Goal Statement):** Read the Contribution Goal's two opening paragraphs. Verify each claim against Implementation Guide §3 (Purpose/Scope) and §4 (Architecture). Check whether "sensor networks", "observation data", "system control", "unified interface", "specification-complete", "critical ecosystem gap" are accurate. Check "real-time observation queries", "historical data analysis", "remote system control capabilities" — do these overstate what the code does?

2. **Check 2 (Core Integration):** Verify all 5 bullet points under "Core Integration":

   - "Single QueryBuilder class with 70-80 methods" — read §6, verify class count and method count (authoritative count is now **80**, not 70-80)
   - "9 CSAPI resource types (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands)" — verify all 9 names match exactly
   - "Factory method integration pattern following established library architecture (EDR pattern)" — read §5, verify pattern
   - "Resource validation in all methods with fail-fast error handling" — read §6 and §11
   - "Complete query parameter support (spatial, temporal, hierarchical, relationship-based, property-based filters)" — read §6 parameter sections, check if any category is missing or misnamed
   - "Both pagination modes (offset-based and cursor-based)" — verify in §6

3. **Check 3 (Format Support):** Verify all 4 bullet points under "Format Support":

   - "SensorML 3.0 parser" — read §7 SensorML section, verify "all system models" and "recursive component parsing"
   - "SWE Common 3.0 parser supporting all three encodings (JSON, Text/CSV, Binary)" — **note:** Binary SWE _parsing_ is in scope per Doc 10 and Phase 2D assessment (M2/P4). Worker offloading for SWE Binary (`PARSE_SWE_BINARY` message type from Doc 16) is **OUT OF SCOPE** — removed in ROADMAP v3.1 along with all 9 CSAPI worker message types. "All three encodings" is correct for parsing at the parser level.
   - "GeoJSON extensions" — verify against §7
   - "Format detection and content negotiation" — verify against §7, check whether "content negotiation" is accurately described

4. **Check 4 (Number Accuracy):** Extract every number from the Contribution Goal and verify against Implementation Guide. **Use the post-A2 authoritative values** (the Guide and ROADMAP have been reconciled):

   - 70-80 methods → §6 (authoritative: **80**)
   - 9 resource types → §6
   - 1,750-2,400 lines of interfaces → model.ts estimate
   - > 80% test coverage → §9
   - 24 implementation files → §13/§14
   - ~4,614-6,094 implementation lines → §13
   - 17 test files → §13/§14 (authoritative: **22** — this is a known A1/A2 finding already resolved in Guide + ROADMAP)
   - ~4,500-6,000 test lines → §13 (authoritative: **4,040-5,340** — reconciled in A2)
     Also cross-reference against ROADMAP v3.2 summary table for three-way consistency.

5. **Check 5 (Quality Standards):** Verify all 5 quality standards bullets:

   - "three-tier type hierarchy" — verify in §6 type system section
   - ">80% test coverage with comprehensive unit, integration, and end-to-end tests" — **critical:** does "end-to-end tests" contradict AP2 (real-server testing rejected)? Should this say "integration tests" instead?
   - "JSDoc documentation for all public APIs" — verify in §16
   - "Compliance with OGC API - Connected Systems specifications (Parts 1 & 2)" — verify scope
   - "Zero-breaking-change integration" — verify backward compatibility requirements

6. **Check 6 (Omissions):** Read Implementation Guide table of contents/section headers. Identify major scope areas NOT mentioned in the Contribution Goal:

   - Worker Extensions (§8) — mentioned? **Note:** Worker extensions are now OUT OF SCOPE (ROADMAP v3.1). If the Contribution Goal doesn't mention them, that's correct. But verify the Contribution Goal doesn't _imply_ worker support.
   - Service Discovery extensions (§5 Conformance/Collections readers) — mentioned?
   - Helper utilities — mentioned?
   - Anti-pattern compliance — mentioned?
   - Navigation patterns (16 parent-child relationships) — mentioned?
     Categorize each omission as Acceptable (appropriate for a summary) or Needs Addition.

7. **Check 7 (Overclaims):** Scan for promises that exceed what the Implementation Guide delivers:
   - "specification-complete" — does the guide implement ALL conformance classes?
   - "real-time observation queries" — does the guide implement streaming/WebSocket, or only HTTP request/response?
   - "historical data analysis" — does the guide provide analysis tools, or only data retrieval?
   - "remote system control" — does the guide implement end-to-end control, or only URL building for command endpoints?

**Part II — Reverse Check (Check 8):**

8. **Check 8 (Value Proposition Feedback):** Read Implementation Guide §3 and §4. Check whether the guide contains any ecosystem positioning or value framing that the Contribution Goal should incorporate. This is a lightweight check — expected to produce minimal findings.

### Output format:

Generate a report saved to `docs/research/pre-implementation-alignment/findings/A3-contribution-goal-vs-implementation-guide-report.md` with:

1. **Executive Summary** — overall alignment status, total finding count by severity
2. **Part I Findings** — one subsection per check (1-7), each finding with severity (Critical/High/Medium/Low), the exact Contribution Goal text being checked, what the Implementation Guide says (with section/line reference), and recommended resolution
3. **Part II Findings** — Check 8 reverse feedback (expected to be brief)
4. **Recommendations** — prioritized action list, focusing on Contribution Goal text updates
5. **Acceptance Criteria Checklist** — the 8 checkboxes from the research plan, marked pass/fail

After generating the report, **also resolve all Critical, High, and Medium findings** by updating the Contribution Goal document directly. Then commit both the report and the updated Contribution Goal, and push. Use commit message format: `docs(alignment): A3 report + Contribution Goal updates — resolve alignment findings`
