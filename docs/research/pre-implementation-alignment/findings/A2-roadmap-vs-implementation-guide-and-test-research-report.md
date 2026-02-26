# A2: ROADMAP vs Implementation Guide + Test Research — Alignment Report

**Date:** February 13, 2026  
**Research Plan:** [A2 Research Plan](../A2-research-plan-roadmap-vs-implementation-guide-and-test-research.md)  
**Scope:** Cross-reference ROADMAP v3.0 against both the Implementation Guide v7.0 and the test research corpus  
**Checks Executed:** 12 of 12  
**Status:** ✅ Complete

> **📝 Post-Audit Update (February 2026):** After this report was completed, ROADMAP was updated from v3.0 to v3.1 — removing worker extensions (Phase 4 Task 4.1) from scope. Key numbers changed: 34→33 tasks, 60-88→57-84 hours, 4,400-6,300→4,200-6,000 test lines. Check 8 (Scope Boundaries) has been updated to reflect this decision. Other checks retain their original v3.0 figures for audit integrity — the findings remain valid as the changes only reduce scope (no new gaps introduced).

> **✅ Resolution Update (February 2026):** All 17 actionable findings have been resolved across ROADMAP v3.2 and Guide v7.0. Prompt 1 applied 14 ROADMAP-only fixes (commit 35746ca). Prompt 2 applied 5 cross-document fixes: 13 "70-80"→"80" Guide replacements, estimate reconciliation (Guide aligned to ROADMAP's 57-84 hrs / 8-11 wks), test line range annotation (Doc 19 authoritative 4,040-5,340), and Guide Code Volume sub-category alignment with Doc 19. See Priority tables below for per-item status.

---

## Executive Summary

The ROADMAP v3.0 is **structurally well-aligned** with both the Implementation Guide and test research corpus. All 34 tasks map to documented Guide components, all 80 method names match, all phase dependencies are correct, and the testing cadence (34 checkpoints, "test immediately" on every task) enforces the incremental rhythm established by the test research.

The primary gaps are **maintenance lag** — the ROADMAP was not updated during the A1 alignment cycle, leaving several known corrections unapplied (test file count 17→22, `sortBy`/`sortOrder` absent, stale Phase 3 count). Additionally, the ROADMAP's Development Standards section is **incomplete relative to the Guide's §16**, missing the AP1-AP5 anti-pattern catalog, "meaningful vs trivial" testing standard, and `globalThis.fetch` mocking convention.

No Critical or High findings. The anti-pattern audit (Check 9) found **zero explicit AP violations** in any of the 34 "Test immediately" sections — only minor wording ambiguities in 6 tasks that could be misinterpreted without the AP catalog context.

| Severity     | Count  |
| ------------ | ------ |
| **Critical** | 0      |
| **High**     | 0      |
| **Medium**   | 7      |
| **Low**      | 12     |
| **Info**     | 15     |
| **Total**    | **34** |

---

## Findings Summary by Check

| Check | Part | Title                    | Findings | Severities |
| ----- | ---- | ------------------------ | -------- | ---------- |
| 1     | I    | Task-Component Mapping   | 3        | 1L, 2I     |
| 2     | I    | Estimate Consistency     | 4        | 2M, 1L, 1I |
| 3     | I    | Method Count Accuracy    | 3        | 1M, 1L, 1I |
| 4     | I    | File/Directory Structure | 4        | 2L, 2I     |
| 5     | I    | Phase Dependencies       | 3        | 3I         |
| 6     | II   | Test File Inventory      | 2        | 1M, 1I     |
| 7     | II   | Testing Cadence          | 4        | 1M, 1L, 2I |
| 8     | II   | Scope Boundaries         | 2        | 1L, 1I     |
| 9     | II   | Anti-Pattern Audit       | 3        | 2L, 1I     |
| 10    | II   | Coverage/Estimates       | 2        | 1L, 1I     |
| 11    | II   | Development Standards    | 3        | 2M, 1L     |
| 12    | III  | Phase Structure Feedback | 2        | 1L, 1I     |

---

## Part I: Backward Checks (ROADMAP ↔ Implementation Guide)

### Check 1: Task-Component Mapping

All 34 ROADMAP tasks map to documented Guide components. All Guide components have at least one ROADMAP task. No orphans or uncovered components.

| Phase   | Tasks    | All Mapped? |
| ------- | -------- | ----------- |
| Phase 1 | 1.1-1.4  | ✅          |
| Phase 2 | 2.1-2.9  | ✅          |
| Phase 3 | 3.1-3.17 | ✅          |
| Phase 4 | 4.1-4.4  | ✅          |

| ID      | Severity | Finding                                                                                                                                                                     | Recommended Resolution                                                                                |
| ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| A2-F1.1 | **Info** | ROADMAP executive summary (line 27) says Phase 3 has "15 tasks" — should be 17. Stale reference from v3.0 restructure.                                                      | Update ROADMAP line 27: "15 tasks" → "17 tasks"                                                       |
| A2-F1.2 | **Info** | Complete bidirectional mapping: 34 tasks ↔ 16+ Guide components. No orphans.                                                                                                | No action needed                                                                                      |
| A2-F1.3 | **Low**  | ROADMAP Task 3.1 says "Extend existing GeoJSON parser" without mentioning `formats/geojson.ts`. Guide file structure (line ~2058) lists this as a new file (~50-100 lines). | Clarify in ROADMAP whether Task 3.1 creates `formats/geojson.ts` or modifies an existing parser file. |

---

### Check 2: Estimate Consistency

| Metric            | ROADMAP  | Guide   | Delta   | Status                  |
| ----------------- | -------- | ------- | ------- | ----------------------- |
| Total hours       | 60-88    | 51-72   | +17-22% | ⚠️ High-end exceeds 20% |
| Calendar time     | 8-12 wks | 6-9 wks | +33%    | ⚠️ Exceeds              |
| Impl files        | 24       | 24      | 0%      | ✅ Match                |
| Test files        | 17       | 22      | -23%    | ❌ Exceeds              |
| Impl lines (low)  | 4,850    | 4,614   | +5%     | ✅ Within               |
| Impl lines (high) | 6,500    | 6,094   | +7%     | ✅ Within               |
| Test lines (low)  | 4,400    | 4,040   | +9%     | ✅ Within               |
| Test lines (high) | 6,300    | 5,340   | +18%    | ✅ Within               |

| ID      | Severity   | Finding                                                                                                                                                                                                                             | Recommended Resolution                                                                         |
| ------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| A2-F2.1 | **Medium** | Total hours discrepancy: ROADMAP 60-88 hrs vs Guide 51-72 hrs. High-end difference (88 vs 72 = 22.2%) exceeds 20% threshold. ROADMAP sums are internally consistent across 4 phases; Guide aggregate appears independently derived. | Reconcile to single range. If ROADMAP phase sums are more granular, update Guide §13 to match. |
| A2-F2.2 | **Medium** | Test file count: ROADMAP 17, Guide 22 (post-A1). Known A1 finding deferred to ROADMAP update. Authoritative count per Doc 19 is 22.                                                                                                 | Update ROADMAP summary table: 17→22 test files, total files 41→46.                             |
| A2-F2.3 | **Low**    | Calendar time: ROADMAP 8-12 wks vs Guide 6-9 wks. Different weekly hour assumptions (ROADMAP: 6-8 hrs/wk; Guide: unstated).                                                                                                         | Align calendar time. State weekly pace assumption in Guide.                                    |
| A2-F2.4 | **Info**   | Implementation file count (24) and implementation line estimates are within 20% and consistent.                                                                                                                                     | No action needed                                                                               |

---

### Check 3: Method Count Accuracy

All 80 method names verified across 9 resource types. Three-way match: ROADMAP task lists, Guide §6, Guide file structure.

| Resource Type     | ROADMAP | Guide  | Status |
| ----------------- | ------- | ------ | ------ |
| Systems           | 12      | 12     | ✅     |
| Deployments       | 8       | 8      | ✅     |
| Procedures        | 8       | 8      | ✅     |
| Sampling Features | 8       | 8      | ✅     |
| Properties        | 6       | 6      | ✅     |
| DataStreams       | 11      | 11     | ✅     |
| Observations      | 9       | 9      | ✅     |
| Control Streams   | 8       | 8      | ✅     |
| Commands          | 10      | 10     | ✅     |
| **TOTAL**         | **80**  | **80** | ✅     |

| ID      | Severity   | Finding                                                                                                                                                                         | Recommended Resolution                                   |
| ------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| A2-F3.1 | **Info**   | All 80 method names and per-resource counts match.                                                                                                                              | No action needed                                         |
| A2-F3.2 | **Low**    | Both documents use "70-80 public methods" in several locations; actual count is exactly 80.                                                                                     | Update "70-80" → "80" in both documents.                 |
| A2-F3.3 | **Medium** | `sortBy`/`sortOrder` query parameters restored post-A1 (commit `af11e85`) in Guide §6 "Complete Query Parameter Support." ROADMAP has zero mentions of `sortBy` or `sortOrder`. | Add `sortBy`/`sortOrder` to ROADMAP Phase 2 description. |

---

### Check 4: File/Directory Structure

All 24 implementation files match between ROADMAP and Guide (paths, hierarchy, flat core + `formats/` subdirectory).

| ID      | Severity | Finding                                                                                                                                                                       | Recommended Resolution                                                     |
| ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| A2-F4.1 | **Low**  | `formats/geojson.ts` in Guide but not explicitly in ROADMAP Task 3.1. (Duplicate of F1.3.)                                                                                    | See F1.3                                                                   |
| A2-F4.2 | **Low**  | ROADMAP doesn't specify fixture directory path (`fixtures/csapi/sample-server/`), URL-path-mirroring convention, or fixture count (~80-100). Guide §9 specifies all of these. | Add fixture directory reference to ROADMAP Phase 1 or conventions section. |
| A2-F4.3 | **Info** | Implementation file structure fully consistent between documents.                                                                                                             | No action needed                                                           |
| A2-F4.4 | **Info** | Guide Code Volume Summary sub-categories for test files differ from Doc 19's breakdown. Totals match (22=22).                                                                 | Align Guide sub-categories with Doc 19 during next Guide update.           |

---

### Check 5: Phase Dependencies

All inter-phase and intra-phase dependencies verified as correct. No circular dependencies. No A1 findings changed component relationships.

| ID      | Severity | Finding                                                                                                                     |
| ------- | -------- | --------------------------------------------------------------------------------------------------------------------------- |
| A2-F5.1 | **Info** | All inter-phase dependencies (1→2, 2→3, 1-3→4) correctly stated.                                                            |
| A2-F5.2 | **Info** | All intra-Phase 3 dependencies correctly ordered (SWE Common types before SensorML types; sub-parsers before main parsers). |
| A2-F5.3 | **Info** | No A1 updates introduced new dependencies or broken existing ordering.                                                      |

---

## Part II: Forward Checks (ROADMAP → Test Research)

### Check 6: Test File Inventory

| Source                 | Test Files | Test Lines  |
| ---------------------- | ---------- | ----------- |
| ROADMAP                | 17         | 4,400-6,300 |
| Doc 19 (authoritative) | 22         | 4,040-5,340 |
| Guide (post-A1)        | 22         | 4,040-5,340 |

The 5 missing files in the ROADMAP are: `url_builder-base.spec.ts`, `test-utils.ts`, `test-helpers.ts`, `test-fixtures.ts`, and 1 integration test file.

| ID      | Severity   | Finding                                                                                                                         | Recommended Resolution                                             |
| ------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| A2-F6.1 | **Medium** | ROADMAP states 17 test files; Doc 19 specifies 22. Guide updated during A1 but ROADMAP was not. Known A1 finding (C3-M1/C7-M2). | Update ROADMAP summary table: test files 17→22, total files 41→46. |
| A2-F6.2 | **Info**   | Guide Code Volume sub-categories differ from Doc 19's (see F4.4). Totals match.                                                 | Align Guide sub-categories with Doc 19.                            |

---

### Check 7: Testing Cadence

34 total test checkpoints (30 implementation tasks with "Test immediately" + 2 test-writing tasks + 1 validated-by-other-tests + 1 documentation validation). No task produces >800 LOC of implementation code without tests, with one borderline case.

| ID      | Severity   | Finding                                                                                                                                                                                                                   | Recommended Resolution                                                                 |
| ------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| A2-F7.1 | **Low**    | Task 1.1 at 4-5 hours exceeds 3-hour cadence maximum. However, estimate includes test writing — cadence is met if developer writes types incrementally with tests at the 3-hour mark.                                     | Add note that Task 1.1 should write types incrementally with mid-task test checkpoint. |
| A2-F7.2 | **Medium** | Task 3.5 (SensorML Types) estimates 800-1,200 lines. Upper bound exceeds 800 LOC threshold. These are passive type definitions (interfaces), not behavioral code — the 800 LOC rule was designed for implementation code. | Clarify threshold applies to behavioral code, or split Task 3.5 into sub-tasks.        |
| A2-F7.3 | **Info**   | All 34 tasks have test coverage: 30 "Test immediately" + 2 test-writing tasks + 1 validated by detector tests + 1 doc build validation.                                                                                   | No action needed                                                                       |
| A2-F7.4 | **Info**   | Phase 2 tasks follow strict incremental cadence — maximum gap is ~2.5-3 hours (Systems, 12 methods). All within limits.                                                                                                   | No action needed                                                                       |

---

### Check 8: Scope Boundary Alignment

**OUT OF SCOPE items from test research:**

| Item                                      | Source                             | In ROADMAP?                  | Status                                                                                                    |
| ----------------------------------------- | ---------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------- |
| Performance testing                       | Doc 33, Guide §9                   | ❌ Not in ROADMAP            | ✅ Correctly excluded                                                                                     |
| Real-world server testing                 | Doc 32 (AP2), Guide §9             | ❌ Not in ROADMAP            | ✅ Correctly excluded                                                                                     |
| Migration testing                         | Not defined                        | ❌ Not in ROADMAP            | ✅ Correctly excluded                                                                                     |
| Worker extensions (9 CSAPI message types) | Guide §8 (now marked OUT OF SCOPE) | ❌ Removed from ROADMAP v3.1 | ✅ Correctly removed — no upstream JSON API uses workers                                                  |
| `PARSE_SWE_BINARY` worker offloading      | Guide §8, Phase 2D                 | ❌ Removed from ROADMAP v3.1 | ✅ Removed — binary parsing remains in scope at parser level (Task 3.13), only worker offloading excluded |

**IN SCOPE items requiring ROADMAP coverage:**

| Item                              | Source           | In ROADMAP?                                   | Status     |
| --------------------------------- | ---------------- | --------------------------------------------- | ---------- |
| Binary SWE parsing (parser level) | Doc 10, Phase 2D | ✅ Task 3.13 ("Test Binary encoding")         | ✅ Covered |
| Error condition testing           | Doc 18           | ✅ Throughout Phase 2-3 test sections         | ✅ Covered |
| Pagination testing                | Doc 23           | ✅ Phase 2 tasks (cursor-based, offset-based) | ✅ Covered |
| Subresource navigation            | Doc 26           | ✅ Phase 2 tasks (association methods)        | ✅ Covered |
| Command lifecycle                 | Doc 31           | ✅ Task 2.9 (status, result, cancel)          | ✅ Covered |

| ID      | Severity | Finding                                                                                                                                                                                                                                                                                                                                                                       | Recommended Resolution                                                                                         |
| ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| A2-F8.1 | **Info** | Scope boundaries are clean. ROADMAP correctly excludes performance testing, real-world server testing, migration testing, and worker extensions (9 CSAPI message types removed in ROADMAP v3.1 — no upstream JSON API uses workers). Binary SWE parsing remains in scope at parser level (Task 3.13). All IN SCOPE items from test research have corresponding ROADMAP tasks. | No action needed                                                                                               |
| A2-F8.2 | **Low**  | ROADMAP does not include an explicit "Scope Exclusions" section. Guide §9 has "Test Scope Exclusions" listing performance testing and real-world server testing with rationale. A brief exclusions note in the ROADMAP would prevent scope creep during implementation.                                                                                                       | Add 3-5 line "Scope Exclusions" note to ROADMAP listing what is explicitly OUT OF SCOPE for this contribution. |

---

### Check 9: Anti-Pattern Compliance in Test Guidance

**Methodology:** Scanned all 34 "Test immediately" sections against AP1 (Testing Response Content), AP3 (Server Conformance Testing), AP4 (Asserting Data Shape), AP2 (Live Server Dependencies), and AP5 (Graceful Skipping).

**Overall Result:**

| Anti-Pattern | Explicit Violations | Ambiguous Wording       | Documents With Risk |
| ------------ | ------------------- | ----------------------- | ------------------- |
| AP1          | 0                   | 3 tasks (2.7, 3.1, 3.3) | 0                   |
| AP2          | 0                   | 0                       | 0                   |
| AP3          | 0                   | 2 tasks (3.1, 3.3)      | 0                   |
| AP4          | 0                   | 2 tasks (3.1, 3.3)      | 0                   |
| AP5          | 0                   | 0                       | 0                   |

**Per-Phase Assessment:**

- **Phase 1** (4 tasks): All clean. Test descriptions focus on type validation, helper functions, constructor validation, conformance detection — all client code. ✅
- **Phase 2** (9 tasks): 8 clean, 1 ambiguous. URL construction context makes all test descriptions inherently client-oriented ("Test getSystems with pagination, filtering, bbox" = URL construction). One ambiguous phrase in Task 2.7. ✅
- **Phase 3** (17 tasks): 15 clean, 2 ambiguous. Parser/type context is client-oriented ("Test parsing with spec example fixtures" = green flag). Two ambiguous phrases in Tasks 3.1 and 3.3 involving "validation rules." ✅
- **Phase 4** (3 tasks): All clean. Integration workflows, unit test completion, documentation — all client code. ✅

**Ambiguous Phrases Flagged:**

| Task | Phrase                                                                                              | Risk    | Context                                                                                                                                                                                                                                 |
| ---- | --------------------------------------------------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.7  | "Test result format handling"                                                                       | AP1     | Could mean testing fixture result content vs. client-side format parameter construction. In QueryBuilder context, this is URL construction with `f=` parameter.                                                                         |
| 3.1  | "Test validation rules"                                                                             | AP3/AP4 | Could mean testing data correctness vs. testing validator function behavior. Guide §7 Validator has explicit clarification ("Tests should verify validator correctly rejects invalid inputs, not that fixture data passes validation"). |
| 3.3  | "Test Part 1 validation rules" / "Test Part 2 validation rules" / "Test cross-reference validation" | AP3/AP4 | Same ambiguity as 3.1. "Cross-reference validation" could be interpreted as testing server data integrity rather than testing the client-side cross-reference validator function.                                                       |

| ID      | Severity | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                        | Recommended Resolution                                                                                                                                                   |
| ------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A2-F9.1 | **Low**  | Task 2.7 (Observations) "Test result format handling" is ambiguous — could lead a developer to test fixture result content (AP1) rather than URL construction with format parameters. In the QueryBuilder context this should test that `getObservations({ resultFormat: 'swe+json' })` constructs the correct URL.                                                                                                                            | Reword to "Test result format URL parameter construction" or "Test format query parameter encoding."                                                                     |
| A2-F9.2 | **Low**  | Tasks 3.1 and 3.3 "Test validation rules" / "Test cross-reference validation" are ambiguous — could lead to testing data correctness (AP3/AP4) rather than testing the validator function's accept/reject behavior. Guide §7 Validator already includes a clarification note ("Tests should verify that the validator correctly rejects invalid inputs, not that fixture data passes validation"). The ROADMAP should include similar framing. | Reword to "Test validator correctly rejects invalid input" and "Test cross-reference validator detects broken associations." Reference Guide §7 Validator clarification. |
| A2-F9.3 | **Info** | Anti-pattern audit: **zero explicit AP violations** across all 34 tasks. No AP2 (live server) references, no AP3 (OGC requirement IDs) structuring, no AP5 (graceful skipping) patterns. 28 of 34 tasks (82%) have fully unambiguous client-oriented test descriptions. The remaining 6 tasks have minor wording issues that would be correctly interpreted by a developer who has read the AP catalog.                                        | No action needed — overall test guidance is well-oriented.                                                                                                               |

---

### Check 10: Coverage Target and Estimate Alignment

**Coverage Targets:**

| Source                        | Target                                    | Status |
| ----------------------------- | ----------------------------------------- | ------ |
| ROADMAP Development Standards | >80% test coverage                        | ✅     |
| Guide §9 Testing Components   | >80% statement, >80% branch               | ✅     |
| Doc 20 (Test-to-Code Ratio)   | >80% mandatory floor, 85-95% aspirational | ✅     |

All three documents specify >80% as the mandatory floor. Doc 20 adds the aspirational 85-95% range which the other documents don't contradict. ✅ Aligned.

**Test Estimate Comparison:**

| Source                                | Test Lines   | Test Files | Ratio       |
| ------------------------------------- | ------------ | ---------- | ----------- |
| ROADMAP                               | 4,400-6,300  | 17         | 0.91-0.97:1 |
| Doc 19 (authoritative file inventory) | 4,040-5,340  | 22         | —           |
| Doc 20 (adjusted)                     | 4,150-5,850  | 22         | 0.86-0.90:1 |
| Guide §13 (aggregate)                 | ~4,500-6,000 | 22         | —           |

ROADMAP phase-by-phase sums: ~400-550 + ~800-1,000 + ~2,400-3,500 + ~800-1,250 = ~4,400-6,300 ✅ Internally consistent.

| ID       | Severity | Finding                                                                                                                                                                                                                                                                                                                           | Recommended Resolution                                                                                                                                                           |
| -------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-F10.1 | **Info** | Coverage target (>80%) consistently specified across ROADMAP, Guide §9, and Doc 20. Doc 20 adds aspirational 85-95% which ROADMAP doesn't mention but doesn't contradict.                                                                                                                                                         | No action needed                                                                                                                                                                 |
| A2-F10.2 | **Low**  | ROADMAP test line upper bound (6,300) exceeds Doc 20's adjusted upper bound (5,850) by 7.7% and Doc 19's upper bound (5,340) by 18%. The ROADMAP range is wider than the reconciled test research ranges, though the lower bounds overlap well (4,400 vs 4,040-4,150). This contributes to overall estimate drift alongside F2.1. | When reconciling estimates per F2.1, also narrow the ROADMAP test line range to align with Doc 20's adjusted 4,150-5,850 (or Doc 19's 4,040-5,340 if worker tests are excluded). |

---

### Check 11: Development Standards Consistency

**Comparison Matrix: ROADMAP Dev Standards vs Guide §16**

| Standard                                   | ROADMAP                                      | Guide §16                                 | Gap?    |
| ------------------------------------------ | -------------------------------------------- | ----------------------------------------- | ------- |
| Write method signatures first              | ✅                                           | ✅                                        | —       |
| Write tests immediately (not batched)      | ✅                                           | ✅                                        | —       |
| Quantified cadence (max 2-3 hrs / 800 LOC) | ⚠️ In Key Success Factors, not Dev Standards | ✅ In Dev Standards with "31 checkpoints" | Minor   |
| 100% public API JSDoc                      | ✅                                           | ✅                                        | —       |
| >80% test coverage                         | ✅                                           | ✅                                        | —       |
| TypeScript strict mode                     | ✅                                           | ✅                                        | —       |
| No magic numbers/strings                   | ✅                                           | ✅                                        | —       |
| Three-tier type hierarchy                  | ✅                                           | ✅                                        | —       |
| Helper methods (no inheritance)            | ✅                                           | ✅                                        | —       |
| **"Meaningful vs trivial" test standard**  | ❌ Not present                               | ✅ With Doc 06 reference                  | **Gap** |
| **AP1-AP5 anti-pattern catalog**           | ❌ Not present                               | ✅ Full table + Phase 0 reference         | **Gap** |
| **`globalThis.fetch` mocking convention**  | ❌ Not present                               | ✅ In §9 with code example                | **Gap** |
| Validate against spec examples             | ✅                                           | ✅                                        | —       |
| Lint-clean code                            | ✅                                           | ✅                                        | —       |
| Documentation standards (8 items)          | ✅                                           | ✅                                        | —       |
| Research-Validated Standards (8 items)     | ✅                                           | ✅                                        | —       |

| ID       | Severity   | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                               | Recommended Resolution                                                                                                                                                                                                  |
| -------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-F11.1 | **Medium** | ROADMAP Development Standards lacks the AP1-AP5 anti-pattern catalog and the "meaningful vs trivial" testing standard, both present in Guide §16. Since the ROADMAP is the operational execution document, a developer following only the ROADMAP during implementation would not see these quality gates. The AP catalog is referenced in the Guide with a full 5-row table; the "meaningful vs trivial" standard includes a Doc 06 cross-reference. | Add to ROADMAP Development Standards: (1) AP1-AP5 anti-pattern catalog reference with brief summary table, and (2) "meaningful vs trivial" test standard with Doc 06 reference. Can be concise — a 10-15 line addition. |
| A2-F11.2 | **Medium** | ROADMAP makes no mention of the `globalThis.fetch` mocking convention anywhere in its 713 lines. Guide §9 specifies this explicitly with a code example and "Never use nock, msw" warning. This is the project's HTTP mocking standard — a developer following only the ROADMAP would not know which mocking approach to use.                                                                                                                         | Add `globalThis.fetch` mocking convention to ROADMAP Development Standards or a "Testing Conventions" subsection. A 3-5 line note referencing Guide §9 would suffice.                                                   |
| A2-F11.3 | **Low**    | ROADMAP has the cadence rule ("max 2-3 hrs between tests") in the Key Success Factors section (line ~636) but NOT in the Development Standards section. Guide §16 has it in Development Standards with "31 checkpoints" quantification. Minor structural inconsistency — a developer reading only the Dev Standards section would miss the cadence quantification.                                                                                    | Move cadence rule from Key Success Factors into Development Standards, or add a cross-reference.                                                                                                                        |

---

## Part III: Reverse Check (ROADMAP → Implementation Guide + Test Research)

### Check 12: Phase Structure and Sequencing Feedback

**ROADMAP-specific structural decisions:**

| Decision                            | Where in ROADMAP           | Guide Acknowledgment?                                                                   |
| ----------------------------------- | -------------------------- | --------------------------------------------------------------------------------------- |
| 4-phase sequential model            | Throughout                 | ❌ Guide §13 "Estimated Scope" uses own 51-72 hr estimate without referencing 4 phases  |
| 34 total tasks as checkpoints       | Summary table              | ✅ Guide §16: "31 checkpoints" (slightly off — 34 tasks, 31 implementation checkpoints) |
| Phase 3 restructure from 7→17 tasks | v3.0 changelog             | ✅ Guide §16: "ROADMAP v3" referenced                                                   |
| Calendar time 8-12 weeks            | Summary                    | ❌ Guide §13: "6-9 weeks" (different, see F2.3)                                         |
| 60-88 hours total estimate          | Summary                    | ❌ Guide §13: "51-72 hours" (different, see F2.1)                                       |
| "Test immediately" as workflow rule | Every task + Dev Standards | ✅ Guide §16: "Write tests as you implement"                                            |

| ID       | Severity | Finding                                                                                                                                                                                                                                                                                                                               | Recommended Resolution                                                                                                           |
| -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| A2-F12.1 | **Low**  | Guide §13 "Estimated Scope" does not cross-reference the ROADMAP's more granular 4-phase breakdown or its 60-88 hour estimate. The Guide and ROADMAP present different numbers (51-72 vs 60-88) without stating which is authoritative. The ROADMAP provides the more granular derivation (sum-of-34-tasks). This overlaps with F2.1. | When reconciling estimates per F2.1, add a note in Guide §13 referencing the ROADMAP as the authoritative phase-level breakdown. |
| A2-F12.2 | **Info** | Guide §16 correctly cross-references ROADMAP v3.0: "incremental cadence from ROADMAP v3, 31 checkpoints." This demonstrates the ROADMAP's phase structure decisions have been acknowledged in the Guide's development standards. The test research (Doc 20) also references "ROADMAP phase-by-phase estimates" in §6.                 | No action needed                                                                                                                 |

---

## Cross-Check Summary: Findings Overlapping with A1

| A2 Finding                      | A1 Finding                   | Status                                    |
| ------------------------------- | ---------------------------- | ----------------------------------------- |
| A2-F2.2 (test files 17→22)      | A1 C3-M1 / C7-M2             | ROADMAP still outdated                    |
| A2-F3.3 (sortBy not in ROADMAP) | A1 C2-L1 (resolved in Guide) | New ROADMAP gap (sortBy restored post-A1) |

Both are cases where A1 updated the Guide and/or test research but the ROADMAP was not in scope for A1.

---

## Acceptance Criteria Validation

### ROADMAP ↔ Implementation Guide (Part I)

- [x] All 34 ROADMAP tasks map to real Guide components (Check 1) — ✅ 34/34
- [x] Time and line estimates consistent within 20% (Check 2) — ⚠️ Hours high-end at 22%, test files at 23% — flagged as F2.1, F2.2
- [x] Method counts match per resource type (Check 3) — ✅ 80=80
- [x] File/directory structure consistent (Check 4) — ✅ 24 impl files match; fixtures gap noted
- [x] Phase dependencies verified as correct (Check 5) — ✅ All valid

### ROADMAP ↔ Test Research (Part II)

- [x] Test file inventory reconciled (Check 6) — ⚠️ 17 vs 22, flagged as F6.1
- [x] Testing cadence compliance verified (Check 7) — ✅ 34 checkpoints, 1 borderline LOC case
- [x] Scope boundaries consistent (Check 8) — ✅ No OUT OF SCOPE items in ROADMAP
- [x] Test guidance free of anti-pattern language (Check 9) — ✅ Zero explicit violations; 6 minor ambiguities
- [x] Coverage targets and estimates aligned (Check 10) — ✅ >80% consistent; ranges overlap
- [x] Development standards consistent (Check 11) — ⚠️ 3 gaps (AP catalog, meaningful/trivial, globalThis.fetch)

### Reverse (Part III)

- [x] ROADMAP-specific decisions documented for cross-reference (Check 12) — ✅ Guide §16 acknowledges ROADMAP v3; §13 estimate gap noted

---

## Recommended Resolutions (Prioritized)

### Priority 1: Fix Before Implementation (7 items)

| #   | Finding      | Action                                                                 | Target Document       | Status                                              |
| --- | ------------ | ---------------------------------------------------------------------- | --------------------- | --------------------------------------------------- |
| 1   | F2.2 / F6.1  | Update test file count 17→22, total files 41→46                        | ROADMAP summary table | ✅ Resolved (ROADMAP v3.2)                          |
| 2   | F3.3         | Add `sortBy`/`sortOrder` to Phase 2 descriptions                       | ROADMAP Phase 2       | ✅ Resolved (ROADMAP v3.2)                          |
| 3   | F11.1        | Add AP1-AP5 catalog reference + "meaningful vs trivial" standard       | ROADMAP Dev Standards | ✅ Resolved (ROADMAP v3.2)                          |
| 4   | F11.2        | Add `globalThis.fetch` mocking convention note                         | ROADMAP Dev Standards | ✅ Resolved (ROADMAP v3.2)                          |
| 5   | F2.1 / F12.1 | Reconcile total hours (60-88 vs 51-72); designate authoritative source | ROADMAP + Guide §13   | ✅ Resolved (Guide aligned to ROADMAP 57-84 hrs)    |
| 6   | F7.2         | Clarify 800 LOC threshold for type definitions (or split Task 3.5)     | ROADMAP Dev Standards | ✅ Resolved (ROADMAP v3.2 — note added to Task 3.5) |
| 7   | F1.1         | Fix Phase 3 task count in executive summary (15→17)                    | ROADMAP line 27       | ✅ Resolved (ROADMAP v3.2)                          |

### Priority 2: Incorporate Before Implementation (7 items)

| #   | Finding     | Action                                                                                 | Target Document        | Status                                                  |
| --- | ----------- | -------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------- |
| 8   | F9.1        | Reword Task 2.7 "Test result format handling" → "Test format query parameter encoding" | ROADMAP Task 2.7       | ✅ Resolved (ROADMAP v3.2)                              |
| 9   | F9.2        | Reword Tasks 3.1/3.3 "Test validation rules" → "Test validator rejects invalid input"  | ROADMAP Tasks 3.1, 3.3 | ✅ Resolved (ROADMAP v3.2)                              |
| 10  | F1.3 / F4.1 | Clarify Task 3.1 creates `formats/geojson.ts`                                          | ROADMAP Task 3.1       | ✅ Resolved (ROADMAP v3.2)                              |
| 11  | F4.2        | Add fixture directory reference (`fixtures/csapi/sample-server/`)                      | ROADMAP                | ✅ Resolved (ROADMAP v3.2)                              |
| 12  | F8.2        | Add brief "Scope Exclusions" note                                                      | ROADMAP                | ✅ Resolved (ROADMAP v3.2)                              |
| 13  | F2.3        | Align calendar time estimates; state weekly pace assumption                            | ROADMAP + Guide        | ✅ Resolved (Guide aligned to 8-11 wks at 6-8 hrs/week) |
| 14  | F3.2        | Update "70-80" → "80" methods                                                          | ROADMAP + Guide        | ✅ Resolved (ROADMAP v3.2 + Guide 13 locations)         |

### Priority 3: Nice-to-Have (3 items)

| #   | Finding     | Action                                                                     | Target Document  | Status                                           |
| --- | ----------- | -------------------------------------------------------------------------- | ---------------- | ------------------------------------------------ |
| 15  | F7.1        | Add note that Task 1.1 should write types incrementally with mid-task test | ROADMAP Task 1.1 | ✅ Resolved (ROADMAP v3.2)                       |
| 16  | F11.3       | Move cadence quantification into Dev Standards section                     | ROADMAP          | ✅ Resolved (ROADMAP v3.2)                       |
| 17  | F4.4 / F6.2 | Align Guide Code Volume sub-categories with Doc 19                         | Guide            | ✅ Resolved (Guide test table aligned to Doc 19) |

---

## Overall Assessment

**Verdict: ✅ GO — ROADMAP is structurally sound and implementation-ready**

The ROADMAP v3.0 demonstrates strong alignment with both the Implementation Guide and test research corpus. The 4-phase structure, 34-task granularity, incremental testing cadence, and dependency ordering are all validated. The anti-pattern audit confirms that test guidance across all 34 tasks is appropriately client-oriented with no explicit violations.

The 7 Priority 1 items are primarily maintenance updates (test file count, sortBy, stale count) and Dev Standards completeness (AP catalog, meaningful/trivial, globalThis.fetch). None represent architectural misalignment. Applying these updates before implementation will ensure the ROADMAP functions as a self-contained execution guide without requiring constant cross-referencing to the Implementation Guide or test research.
