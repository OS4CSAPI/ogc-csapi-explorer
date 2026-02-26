# Research Plan A2: ROADMAP ↔ Implementation Guide + Test Research Alignment

**Date:** February 13, 2026  
**Phase:** Pre-Implementation Alignment  
**Step:** A2 (follows A1: Test Research ↔ Implementation Guide)  
**Status:** Not Started  
**Prerequisite:** A1 findings resolved — Implementation Guide and Test Research are authoritative

---

## Objective

Cross-reference the **ROADMAP** (v3.0, 713 lines, 4 phases, 34 tasks) against the **updated Implementation Guide** and **updated Test Research corpus** to verify that the ROADMAP accurately reflects the current state of both documents.

**Directionality:** This step is **primarily one-directional** — the Implementation Guide and Test Research (once reconciled from A1) are the stronger sources of truth. The ROADMAP is the document most likely to need updates. A small reverse check verifies whether the ROADMAP contains any phase-level sequencing or structural decisions that the other documents should acknowledge.

**Core Questions:**

- Does every ROADMAP task map to a real component in the Implementation Guide?
- Are the ROADMAP's estimates (time, lines, files) consistent with both source documents?
- Does the ROADMAP's testing model reflect what the test research established?
- Does the ROADMAP omit anything the other documents require, or include anything they've excluded?
- Are there ROADMAP-level decisions (phase structure, task ordering) that should be echoed back?

---

## Documents Under Review

### ROADMAP (the "execution plan" document)

**CSAPI Implementation Roadmap** (`docs/planning/ROADMAP.md`, v3.0, 713 lines)

Defines 4 phases, 34 tasks, 60-88 hours of development. Specifies task ordering, per-task estimates, deliverables, dependencies, and development standards. Extracted from (and cross-references) the Implementation Guide.

### Implementation Guide (authoritative "what to build" document — post-A1)

**CSAPI Implementation Guide** (`docs/planning/csapi-implementation-guide.md`, v7.0+, ~4,200+ lines)

After A1 resolution, this document incorporates test research feedback and is the canonical source for component specifications, method signatures, architectural patterns, and development standards.

### Test Research Corpus (authoritative "how to verify" documents — post-A1)

**38 findings documents + 13 review files** in `docs/research/testing/`

After A1 resolution, scope decisions, anti-pattern rules, fixture strategy, testing cadence, and estimate reconciliation are finalized. Key authoritative documents: Doc 19 (file inventory), Doc 20 (ratios), Doc 34 (test utilities), Phase 0 report (anti-patterns).

### Cross-Reference Map

| ROADMAP Section                       | Implementation Guide Section                             | Test Research Docs                                 |
| ------------------------------------- | -------------------------------------------------------- | -------------------------------------------------- |
| Phase 1: Core Structure (Tasks 1-4)   | §5 (Service Discovery), §6 (QueryBuilder stub), model.ts | Docs 04, 05, 21, 22                                |
| Phase 2: QueryBuilder (Tasks 1-9)     | §6 (QueryBuilder, ~70-80 methods, 9 resource types)      | Docs 08, 12, 13, 23-29                             |
| Phase 3: Format Handling (Tasks 1-17) | §7 (Format Handlers), SensorML/SWE/GeoJSON               | Docs 09, 10, 11, 25                                |
| Phase 4: Worker & Tests (Tasks 1-4)   | §8 (Worker), §9 (Testing), §16 (Standards)               | Docs 16, 17, 19, 20, 34                            |
| Roadmap Summary table                 | §13 (Timeline/Estimates)                                 | Doc 19 (file inventory), Doc 20 (ratios)           |
| Development Standards section         | §16 (Development Standards)                              | Phase 0 (anti-patterns), Doc 06 (meaningful tests) |
| Key Dependencies section              | §14 (Dependencies)                                       | —                                                  |

---

## Part I: Forward Checks (ROADMAP → Implementation Guide)

_"Does the ROADMAP accurately reflect what the Implementation Guide specifies?"_

### Check 1: Task-to-Component Mapping

**Question:** Does every ROADMAP task correspond to a real, current component in the Implementation Guide? Are there Implementation Guide components with no ROADMAP task?

**Procedure:**

1. Extract every ROADMAP task (34 tasks across 4 phases) and identify the component it implements
2. For each task, verify the component exists in the Implementation Guide at the referenced section/lines
3. Check the reverse: extract all 12 Implementation Guide components and verify each has at least one ROADMAP task
4. Flag any mismatches: tasks for non-existent components, or components with no task

**Task inventory (34 tasks):**

| Phase     | Task                                    | Component                      | Impl Guide Section  |
| --------- | --------------------------------------- | ------------------------------ | ------------------- |
| 1.1       | Create Type System                      | model.ts                       | §6, lines 1960-2248 |
| 1.2       | Create Helper Utilities                 | helpers.ts                     | §6, lines 603-712   |
| 1.3       | Create Stub QueryBuilder                | url_builder.ts (stub)          | §6, lines 481-602   |
| 1.4       | Integrate with OgcApiEndpoint           | endpoint.ts, info.ts, index.ts | §5, lines 303-478   |
| 2.1-2.9   | QueryBuilder Methods (9 resource types) | url_builder.ts (full)          | §6, lines 1193-1715 |
| 3.1       | GeoJSON Handler Extensions              | GeoJSON handler                | §7, lines 2682-2710 |
| 3.2       | Format Detector Extensions              | Format detector                | §7, lines 2845-2874 |
| 3.3       | Validator Extensions                    | Validator                      | §7, lines 2875-2926 |
| 3.4       | SWE Common Types                        | swecommon/types.ts             | §7                  |
| 3.5       | SensorML Types                          | sensorml/types.ts              | §7                  |
| 3.6-3.9   | SensorML Parsers (4 tasks)              | sensorml/\*.ts                 | §7, lines 2711-2761 |
| 3.10      | SensorML Index                          | sensorml/index.ts              | §7                  |
| 3.11-3.14 | SWE Common Parsers (4 tasks)            | swecommon/\*.ts                | §7, lines 2762-2844 |
| 3.15      | SWE Common Index                        | swecommon/index.ts             | §7                  |
| 3.16      | Format Constants                        | formats/constants.ts           | §7                  |
| 3.17      | Format Index                            | formats/index.ts               | §7                  |
| 4.1       | Worker Extensions                       | worker/                        | §8, lines 2929-2982 |
| 4.2       | Integration Tests                       | test files                     | §9                  |
| 4.3       | Unit Tests Completion                   | test files                     | §9                  |
| 4.4       | API Documentation                       | TypeDoc, JSDoc                 | §16                 |

**Deliverable:** Mapping matrix showing each task's corresponding Implementation Guide component, with gaps flagged.

---

### Check 2: Estimate Consistency (ROADMAP ↔ Implementation Guide)

**Question:** Do the ROADMAP's time and line count estimates match the Implementation Guide's estimates?

**Procedure:**

1. Extract ROADMAP summary table estimates:
   - Total time: 60-88 hours
   - Implementation lines: ~4,850-6,500
   - Test lines: ~4,400-6,300
   - Implementation files: 24
   - Test files: 17
2. Extract corresponding estimates from Implementation Guide §13
3. Compare each number — flag discrepancies >20%
4. Check whether post-A1 updates changed any Implementation Guide estimates
5. Verify per-phase breakdowns sum to totals

**Key numbers to reconcile:**

| Metric      | ROADMAP      | Impl Guide §13 | Delta |
| ----------- | ------------ | -------------- | ----- |
| Total hours | 60-88        | ?              | ?     |
| Impl lines  | ~4,850-6,500 | ~4,614-6,094   | ?     |
| Test lines  | ~4,400-6,300 | ~4,500-6,000   | ?     |
| Impl files  | 24           | 24             | ?     |
| Test files  | 17           | 17             | ?     |

**Deliverable:** Estimate reconciliation table with identified discrepancies and recommended resolution.

---

### Check 3: Method Count and Method-Task Alignment

**Question:** Does the ROADMAP's claim of "70-80 methods across 9 resource types" match the Implementation Guide's actual method inventory? Does each ROADMAP Phase 2 task list the correct number of methods?

**Procedure:**

1. Sum all methods listed in ROADMAP Phase 2 tasks (Systems: 12, Deployments: 8, etc.)
2. Sum all methods listed in the Implementation Guide §6 resource type sections
3. Compare totals — flag if they differ
4. Check each resource type individually for method count accuracy
5. Verify method names in ROADMAP match the Implementation Guide's method signatures

**Per-resource-type check:**

| Resource Type     | ROADMAP Methods Count | Impl Guide Methods Count | Match? |
| ----------------- | --------------------- | ------------------------ | ------ |
| Systems           | 12                    | ?                        | ?      |
| Deployments       | 8                     | ?                        | ?      |
| Procedures        | 8                     | ?                        | ?      |
| Sampling Features | 8                     | ?                        | ?      |
| Properties        | 6                     | ?                        | ?      |
| DataStreams       | 11                    | ?                        | ?      |
| Observations      | 9                     | ?                        | ?      |
| Control Streams   | 8                     | ?                        | ?      |
| Commands          | 10                    | ?                        | ?      |
| **TOTAL**         | **80**                | ?                        | ?      |

**Deliverable:** Method-count reconciliation and per-method name check.

---

### Check 4: File and Directory Structure Accuracy

**Question:** Does the ROADMAP's implied file/directory structure match the Implementation Guide's §14 file inventory?

**Procedure:**

1. Extract every file path mentioned or implied in ROADMAP tasks
2. Extract the Implementation Guide's §14 file inventory
3. Compare — flag any files the ROADMAP assumes but the guide doesn't define, or vice versa
4. Pay special attention to fixture directory (`fixtures/csapi/` vs `fixtures/ogc-api/csapi/`)
5. Verify the `formats/` subdirectory structure (sensorml/, swecommon/) is consistent

**Deliverable:** File inventory comparison table.

---

### Check 5: Phase Dependency Accuracy

**Question:** Are the ROADMAP's stated phase dependencies still correct and complete?

**Procedure:**

1. Extract stated dependencies: Phase 1 → Phase 2, Phase 2 → Phase 3, Phases 1-3 → Phase 4
2. Verify each by checking what actual components each phase's tasks consume from prior phases
3. Check for intra-phase dependencies not stated (e.g., Phase 3 Task 4 SWE Types before Task 5 SensorML Types)
4. Verify no circular dependencies exist
5. Check whether any A1 findings changed component relationships that affect phasing

**Deliverable:** Dependency validation table with any missing or incorrect dependencies.

---

## Part II: Forward Checks (ROADMAP → Test Research)

_"Does the ROADMAP's testing model match what the test research established?"_

### Check 6: Test File Inventory Alignment

**Question:** Does the ROADMAP's test file count (17 files) match the authoritative file inventory from Doc 19 (22 files)?

**Procedure:**

1. Extract ROADMAP's implied test file inventory from task descriptions (each "Test immediately" section)
2. Extract Doc 19's authoritative file inventory
3. Compare — identify files present in one but not the other
4. Check whether the discrepancy (17 vs 22) was resolved during A1
5. If not resolved, determine which number is correct and flag for update

**Known discrepancy context:** This was flagged in the A1 research plan (Check 7c). If A1 resolved it, verify the ROADMAP was updated. If not, flag it here.

**Deliverable:** Test file inventory comparison with resolution recommendation.

---

### Check 7: Testing Cadence Compliance

**Question:** Does the ROADMAP's task structure enforce the testing cadence established by the test research (31 checkpoints, max 2-3 hours between tests, never >800 lines without tests)?

**Procedure:**

1. Extract the ROADMAP's testing rhythm (every task has "Test immediately" guidance)
2. Calculate the maximum gap between test checkpoints per phase:
   - Phase 1: 4 tasks × ~3-4 hrs each → test every task
   - Phase 2: 9 tasks × ~2-3 hrs each → test after each resource type
   - Phase 3: 17 tasks × ~1-3 hrs each → test after each component
   - Phase 4: 4 tasks → test after each
3. Verify no single task produces >800 lines without tests
4. Cross-reference against the ROADMAP v3.0 changelog (Phase 3 restructure was specifically to fix this)
5. Count total test checkpoints (should be ~34, one per task)

**Deliverable:** Cadence compliance matrix showing max lines before tests and max hours before tests per task.

---

### Check 8: Scope Boundary Alignment

**Question:** Does the ROADMAP include tasks for anything the test research marked OUT OF SCOPE, or omit anything the test research says is IN SCOPE?

**Procedure:**

1. Extract OUT OF SCOPE items from test research:
   - Performance testing (Doc 33)
   - Real-world server testing (Doc 32, AP2)
   - `PARSE_SWE_BINARY` worker offloading deferred to Phase 4 (binary parsing itself is in scope per Doc 10/Phase 2D)
   - Migration testing (not defined)
2. Verify the ROADMAP does NOT include dedicated tasks for these
3. Extract IN SCOPE items from test research that require implementation work and verify the ROADMAP covers them
4. Check the ROADMAP's Worker Extensions task (Phase 4, Task 1) — it lists `PARSE_SWE_BINARY` as a message type, which is correctly deferred with the rest of Doc 16 (Phase 4). Binary SWE parsing at the parser level (Doc 10) is in scope.

**Deliverable:** Scope boundary checklist (IN SCOPE covered / OUT OF SCOPE excluded / Contradictions flagged).

---

### Check 9: Anti-Pattern Compliance in Test Guidance

**Question:** Does the ROADMAP's test guidance (per-task "Test immediately" sections) avoid recommending patterns that would produce anti-pattern violations (AP1-AP5)?

**Procedure:**

1. Scan every "Test immediately" section in the ROADMAP (34 tasks)
2. Check each for language that could produce:
   - AP1: Testing Response Content — e.g., "Test that response contains expected data"
   - AP3: Server Conformance Testing — e.g., "Test that the endpoint returns proper conformance"
   - AP4: Asserting Data Shape — e.g., "Test that the response has the correct structure"
3. Flag any test descriptions that would lead a developer to write anti-pattern tests
4. Recommend rewording where needed

**Deliverable:** Per-task anti-pattern audit of test guidance.

---

### Check 10: Coverage Target and Estimate Alignment

**Question:** Do the ROADMAP's coverage targets and test estimates match the reconciled numbers from the test research?

**Procedure:**

1. Extract ROADMAP coverage target: >80%
2. Extract test research reconciled targets (Doc 20): >80% mandatory floor, 85-95% aspirational
3. Verify alignment
4. Extract ROADMAP per-phase test line estimates and sum them
5. Compare against Doc 19's authoritative total
6. Check whether the ROADMAP's estimate ranges overlap with Doc 19's ranges

**Key estimates to reconcile:**

| Source               | Test Lines       | Test Files |
| -------------------- | ---------------- | ---------- |
| ROADMAP Phase 1      | ~400-550         | ?          |
| ROADMAP Phase 2      | ~800-1,000       | ?          |
| ROADMAP Phase 3      | ~2,400-3,500     | ?          |
| ROADMAP Phase 4      | ~800-1,250       | ?          |
| **ROADMAP Total**    | **~4,400-6,300** | **17**     |
| Doc 19 Authoritative | ~4,040-5,340     | 22         |

**Deliverable:** Estimate reconciliation with recommended authoritative numbers.

---

### Check 11: Development Standards Consistency

**Question:** Does the ROADMAP's Development Standards section match the Implementation Guide's §16, and does it incorporate test research conventions?

**Procedure:**

1. Compare ROADMAP "Development Standards" section (lines ~647-697) against Implementation Guide §16
2. Identify any standards in one but not the other
3. Check whether the ROADMAP references:
   - Anti-pattern catalog (AP1-AP5)
   - "Meaningful vs trivial" test standard (Doc 06)
   - `globalThis.fetch` mocking convention
   - Three-tier imports
   - Incremental testing cadence (31 checkpoints)
4. Check whether the ROADMAP's "Research-Validated Standards" list is still accurate after A1 updates

**Deliverable:** Standards comparison matrix.

---

## Part III: Reverse Check (ROADMAP → Implementation Guide + Test Research)

_"Are there ROADMAP-level decisions that the other documents should acknowledge?"_

### Check 12: Phase Structure and Sequencing Feedback

**Question:** Does the ROADMAP contain phase-level structural decisions that should be reflected in the Implementation Guide or test research?

**Procedure:**

1. Identify ROADMAP-specific structural decisions:
   - 4-phase sequential model with explicit dependencies
   - Phase 3 restructure from 7 tasks to 17 (v3.0 change)
   - 34 total tasks as granular checkpoints
   - Calendar time estimates (8-12 weeks at 6-8 hrs/week)
   - "Test immediately after each subtask" as a workflow requirement
2. For each, check whether the Implementation Guide's §13 (Timeline) or §9 (Testing) references it
3. Check whether the test research's cadence documents (Doc 05, Roadmap references) are consistent
4. This is a lightweight check — the ROADMAP is derived from the Implementation Guide, so most structure should already align. Flag only genuine gaps.

**Deliverable:** Reverse feedback list (items the Implementation Guide or test research should cross-reference from the ROADMAP).

---

## Execution Strategy

**Read order:**

1. ROADMAP in full (~713 lines) — extract all tasks, estimates, dependencies, standards
2. Implementation Guide §5-§8 (~2,700 lines) — verify task-component mapping
3. Implementation Guide §13 (Estimates) — reconcile numbers
4. Implementation Guide §14 (File Inventory) — verify file structure
5. Implementation Guide §16 (Development Standards) — compare standards
6. Doc 19 (File Inventory) — authoritative test file count and estimates
7. Doc 20 (Test-to-Code Ratios) — coverage targets
8. Doc 34 (Test Utilities) — test infrastructure alignment
9. Phase 0 report — anti-pattern definitions for test guidance audit
10. Phase 2E notes — scope boundary decisions (Docs 32, 33, binary SWE)
11. ROADMAP v3.0 changelog — verify Phase 3 restructure rationale consistency

**Estimated effort:** 2-3 hours (shorter than A1 — less bidirectional, ROADMAP is smaller, and many A1 findings will pre-resolve overlap areas)

**Output:** Alignment report with severity-rated findings (Critical/High/Medium/Low):

- **Part I findings:** ROADMAP vs Implementation Guide discrepancies
- **Part II findings:** ROADMAP vs Test Research discrepancies
- **Part III findings:** Reverse feedback items (expected to be minimal)

---

## Acceptance Criteria

The cross-reference is complete when:

**ROADMAP ↔ Implementation Guide:**

- [ ] All 34 ROADMAP tasks map to real Implementation Guide components (Check 1)
- [ ] Time and line estimates consistent within 20% (Check 2)
- [ ] Method counts match per resource type (Check 3)
- [ ] File/directory structure consistent (Check 4)
- [ ] Phase dependencies verified as correct (Check 5)

**ROADMAP ↔ Test Research:**

- [ ] Test file inventory reconciled (Check 6)
- [ ] Testing cadence compliance verified (Check 7)
- [ ] Scope boundaries consistent — no OUT OF SCOPE items in ROADMAP (Check 8)
- [ ] Test guidance free of anti-pattern language (Check 9)
- [ ] Coverage targets and estimates aligned (Check 10)
- [ ] Development standards consistent across all three documents (Check 11)

**Reverse:**

- [ ] ROADMAP-specific decisions documented for cross-reference (Check 12)

**Final:**

- [ ] Report generated with severity-rated findings
- [ ] All Critical and High findings resolved
- [ ] ROADMAP updated where warranted
