# Research Plan A1: Test Research ↔ Implementation Guide Bidirectional Alignment

**Date:** February 13, 2026  
**Phase:** Pre-Implementation Alignment  
**Step:** A1 of 5  
**Status:** Not Started

---

## Objective

Perform a **bidirectional** cross-reference between the 38-document test research corpus (plus 13 review files) and the CSAPI Implementation Guide (v7.0, 4,207 lines) to:

1. **Forward (Implementation Guide → Test Research):** Verify every implementation component has complete, consistent, and actionable test coverage — no gaps, no orphans, no contradictions.
2. **Reverse (Test Research → Implementation Guide):** Identify lessons learned, architectural insights, scope corrections, specification details, and structural decisions discovered during test research that should be propagated back into the implementation guide to make it the best possible version before coding begins.

**Core Questions:**

- Does the test research accurately and completely cover what the implementation guide specifies?
- Has the test research discovered anything — corrections, clarifications, refined patterns, scope decisions, deeper specification understanding — that the implementation guide should incorporate?

---

## Documents Under Review

### Implementation Guide (the "what to build" document)

**CSAPI Implementation Guide** (`docs/planning/csapi-implementation-guide.md`, v7.0, 4,207 lines, 68 sections)

Defines all 12 components, method signatures, type system, file structure, development standards, and usage scenarios.

### Test Research Corpus (the "how to verify" documents)

**38 findings documents + 13 review files** in `docs/research/testing/`

The corpus represents ~50,000+ lines of systematic analysis conducted after the implementation guide was written. During this analysis, the research surfaced corrections, refined understanding, scope decisions, and specification details that may not have been fed back into the implementation guide.

### Cross-Reference Map

| Implementation Guide Section                               | Primary Test Research Docs |
| ---------------------------------------------------------- | -------------------------- |
| §5: Service Discovery (Conformance, Collections, Endpoint) | Docs 04, 05, 22            |
| §6: QueryBuilder (all 9 resource types, 70-80 methods)     | Docs 08, 12, 13, 23-29     |
| §6: Resource Validation Strategy                           | Docs 12, 18, 34            |
| §6: Helper Methods                                         | Docs 12, 34                |
| §6: Navigation Patterns                                    | Docs 26                    |
| §6: Type System Architecture                               | Docs 21                    |
| §6: Query Parameters                                       | Docs 24, 28, 29            |
| §7: Format Handlers (GeoJSON, SensorML, SWE Common)        | Docs 09, 10, 11, 25        |
| §7: Format Detector, Validator                             | Docs 22, 25                |
| §8: Worker Components                                      | Doc 16                     |
| §9: Testing Components                                     | Docs 17, 19, 20            |
| §11: Developer Experience / Error Handling                 | Docs 06, 18                |
| §12: Usage Scenarios                                       | Docs 07, 14                |
| Cross-cutting: Fixtures                                    | Docs 15, 15P2              |
| Cross-cutting: Quality                                     | Docs 03, 06, 35, 36        |
| Cross-cutting: Playbook                                    | Doc 38                     |
| Cross-cutting: Anti-patterns                               | Phase 0 report             |

---

## Part I: Forward Checks (Implementation Guide → Test Research)

_"Is every component in the guide adequately covered by test research?"_

### Check 1: Component Coverage

**Question:** Does every component in the implementation guide have corresponding test specifications in the research?

**Procedure:**

1. Extract every distinct component from the implementation guide (12 components across §5-§8)
2. For each component, identify which test research document(s) cover it
3. Rate coverage: **Complete** (test scenarios defined for all public methods/behaviors), **Partial** (some methods/behaviors missing), **Missing** (no test coverage defined)
4. For partial/missing, document specifically what's missing

**Components to check (12):**

| #   | Component                                | Impl Guide Section  | Expected Test Docs     |
| --- | ---------------------------------------- | ------------------- | ---------------------- |
| 1   | Conformance Reader (extensions)          | §5, lines 303-330   | Doc 22                 |
| 2   | Collections Reader (extensions)          | §5, lines 331-352   | Doc 22                 |
| 3   | OgcApiEndpoint Integration               | §5, lines 353-478   | Docs 04, 05, 14        |
| 4   | CSAPIQueryBuilder (all 9 resource types) | §6, lines 481-1715  | Docs 08, 12, 13, 23-29 |
| 5   | Helper Methods                           | §6, lines 603-712   | Docs 12, 34            |
| 6   | Type System (model.ts)                   | §6, lines 1960-2248 | Doc 21                 |
| 7   | GeoJSON Handler (extensions)             | §7, lines 2682-2710 | Doc 11                 |
| 8   | SensorML Handler (new parser)            | §7, lines 2711-2761 | Doc 09                 |
| 9   | SWE Common Handler (new parser)          | §7, lines 2762-2844 | Doc 10                 |
| 10  | Format Detector (extensions)             | §7, lines 2845-2874 | Docs 22, 25            |
| 11  | Validator (extensions)                   | §7, lines 2875-2926 | Doc 22                 |
| 12  | Worker Extensions                        | §8, lines 2929-2982 | Doc 16                 |

**Deliverable:** Coverage matrix showing Complete/Partial/Missing per component with gap details.

---

### Check 2: Method-Level Coverage (QueryBuilder Deep Dive)

**Question:** Does the test research define test scenarios for all ~70-80 QueryBuilder methods across all 9 resource types?

**Procedure:**

1. Extract every method signature from the implementation guide §6 (Systems through Commands, lines 1193-1715)
2. Cross-reference against Doc 12 (QueryBuilder Testing Strategy) method inventory
3. Cross-reference against Docs 23-29 (parameter-specific strategies) for parameter coverage
4. Identify any methods with no defined test scenarios

**Resource types to check (9):**

| Resource Type     | Impl Guide Section  | Methods | Test Doc   |
| ----------------- | ------------------- | ------- | ---------- |
| Systems           | §6, lines 1193-1240 | ~12     | Doc 12 §5  |
| Deployments       | §6, lines 1241-1285 | ~8      | Doc 12 §6  |
| Procedures        | §6, lines 1286-1334 | ~8      | Doc 12 §7  |
| Sampling Features | §6, lines 1335-1385 | ~8      | Doc 12 §8  |
| Properties        | §6, lines 1386-1422 | ~6      | Doc 12 §9  |
| DataStreams       | §6, lines 1423-1487 | ~11     | Doc 12 §10 |
| Observations      | §6, lines 1488-1569 | ~9      | Doc 12 §11 |
| Control Streams   | §6, lines 1570-1629 | ~8      | Doc 12 §12 |
| Commands          | §6, lines 1630-1715 | ~10     | Doc 12 §13 |

**Deliverable:** Method-by-method matrix showing which have test scenarios defined and which don't.

---

### Check 3: Estimate Consistency

**Question:** Do the test research estimates align with the implementation guide's stated test volume?

**Procedure:**

1. Extract implementation guide test estimates (§9, §13):
   - Total test lines: ~4,500-6,000
   - Total test files: 17
2. Extract Doc 19 (authoritative file inventory) estimates:
   - Total test lines: ~4,040-5,340 across 22 files
3. Extract Doc 20 (test-to-code ratio) estimates
4. Compare all three sources for consistency
5. Identify any significant discrepancies (>20% variance)

**Key numbers to reconcile:**

| Source                         | Test Files | Test Lines     | Impl Lines   |
| ------------------------------ | ---------- | -------------- | ------------ |
| Implementation Guide §13       | 17         | ~4,500-6,000   | ~4,614-6,094 |
| Doc 19 (file inventory)        | 22         | ~4,040-5,340   | —            |
| Doc 20 (ratio validation)      | —          | —              | —            |
| ROADMAP v3.0 summary           | 17         | ~4,400-6,300   | ~4,850-6,500 |
| Doc 17 §2.1 (component matrix) | —          | ~13,090-17,016 | —            |

Note: Doc 17's inflated estimates were already flagged (H1 review fix with discrepancy note). Verify that this is the only source of inflation.

**Deliverable:** Estimate reconciliation table with authoritative numbers identified.

---

### Check 4: Orphan Detection (Test Research → Implementation Guide)

**Question:** Does the test research define test specifications for anything that doesn't exist in the implementation guide?

**Procedure:**

1. Scan each test research document's scope/purpose statement
2. Verify the tested component exists in the implementation guide
3. Check for test specifications that reference non-existent methods, types, or behaviors
4. Check for test research that goes beyond the implementation guide's scope (e.g., performance testing already flagged as out-of-scope)

**Known orphans to verify are properly flagged:**

| Test Doc | Potential Orphan                        | Expected Status                                                                               |
| -------- | --------------------------------------- | --------------------------------------------------------------------------------------------- |
| Doc 32   | Real-world server compatibility testing | Flagged AP2, heavily bannered                                                                 |
| Doc 33   | Performance testing                     | Flagged OUT OF SCOPE                                                                          |
| Doc 16   | `PARSE_SWE_BINARY` worker offloading    | Worker message type deferred to Phase 4 (binary parsing itself in scope per Doc 10, Phase 2D) |
| Doc 31   | Command lifecycle (Part 2 scope)        | Phase 4 material, bannered                                                                    |

**Deliverable:** Orphan list with disposition (properly flagged vs needs action).

---

## Part II: Reverse Checks (Test Research → Implementation Guide)

_"Has the test research discovered anything the implementation guide should incorporate?"_

### Check 5: Scope Decisions Not Yet Reflected

**Question:** Did the test research make scope decisions that the implementation guide should formally incorporate?

**Procedure:**

1. Scan all review reports (Phase 0-4) for scope-altering findings
2. Verify each scope decision is reflected in the implementation guide's §3 (Purpose and Scope) and §9 (Testing)
3. Flag any scope decisions that exist only in test research documents

**Known scope decisions to verify propagation:**

| Scope Decision                                | Source              | Expected in Impl Guide?                         |
| --------------------------------------------- | ------------------- | ----------------------------------------------- |
| Performance testing OUT OF SCOPE              | Doc 33, Phase 2E    | §9 or §3                                        |
| Real-world server testing rejected (AP2)      | Doc 32, Phase 2E    | §16                                             |
| `PARSE_SWE_BINARY` worker offloading deferred | Doc 16, Phase 2F H3 | §8 Worker (not §7 — binary parsing is in scope) |
| Worker extensions = Phase 4 only              | Doc 16, Phase 2F H1 | §8                                              |
| `_metadata` fixture pattern = hallucinated    | Doc 15P2            | §9 fixture guidance                             |
| Enterprise review process simplified          | Doc 36, Phase 2C H2 | §16 or §9                                       |
| Incremental testing cadence (max 2-3 hrs)     | Doc 05, ROADMAP v3  | §16                                             |

**Deliverable:** List of scope decisions with propagation status (Already reflected / Needs update / Not applicable).

---

### Check 6: Client Responsibility Model

**Question:** Does the implementation guide clearly articulate the 5 client responsibilities identified during test research, and do its examples consistently demonstrate them?

**Procedure:**

1. Extract the 5 client responsibilities from Phase 0 (Parse, Construct, Transform, Handle, Validate)
2. Check whether the implementation guide's §3 or §4 explicitly states these responsibilities
3. Scan implementation guide code examples (§6 QueryBuilder, §7 Format Handlers, §11 Developer Experience, §12 Usage Scenarios) for violations — examples that test server behavior rather than client behavior
4. Cross-reference against AP1-AP5 anti-pattern definitions

**Deliverable:** Client responsibility audit with examples flagged if non-compliant.

---

### Check 7: Architectural Patterns Refined by Test Research

**Question:** Did the test research refine or correct any architectural patterns that the implementation guide should update?

**Procedure:**

1. Check `parseAndValidateUrl()` signature — does the implementation guide use `hostname` (correct, per Doc 34) or `host` (incorrect, fixed in Phase 4)?
2. Check fixture directory structure — does the implementation guide reference `fixtures/ogc-api/csapi/` (old) or `fixtures/csapi/` with URL-path-mirroring (revised per Doc 15)?
3. Check test file inventory — does the implementation guide say 17 files (original) or 22 files (Doc 19 authoritative)?
4. Check test utility structure — does the implementation guide's §9 reference the test-utils design from Doc 34?
5. Check resource type naming — scan for any SensorThings API terminology (`ObservedProperties`, `Sensors`, `FeaturesOfInterest`) vs correct CSAPI names (Phase 1 H1 fix)
6. Check whether the QueryBuilder-not-standalone-clients pattern warning exists (Phase 0 lesson)

**Deliverable:** Architectural consistency checklist with specific line references for any needed updates.

---

### Check 8: Specification Details Discovered During Test Research

**Question:** Did the test research uncover specification details (from OGC 23-001, 23-002, 23-003) that would improve the implementation guide's accuracy or completeness?

**Procedure:**

1. Scan Doc 08 (CSAPI Specification Test Requirements) for specification details not in the implementation guide
2. Scan Docs 09, 10 (SensorML, SWE Common) for parser requirements that should inform §7 Format Handlers
3. Check Doc 26 (Sub-Resource Navigation) for relationship details (16 parent-child patterns, 3 relationship types) vs implementation guide's navigation section
4. Check Doc 28 (Temporal Query Testing) for ISO 8601 interval patterns vs implementation guide's temporal parameter specs
5. Check Doc 29 (Spatial Query Testing) for bbox/geometry patterns vs implementation guide's spatial parameter specs
6. Check Doc 31 (Command Lifecycle) for state machine details vs implementation guide's Command methods section

**Deliverable:** Specification enrichment opportunities table — details the implementation guide could absorb from test research to be more precise.

---

### Check 9: Convention and Standards Alignment (Bidirectional)

**Question:** Do the test research's recommended patterns align with the implementation guide's development standards, AND has the test research established conventions that the implementation guide should adopt?

**Procedure:**

**Forward (Implementation Guide → Test Research):**

1. Extract implementation guide §16 (Development Standards) conventions
2. Cross-reference against test research patterns:
   - Mocking convention: `globalThis.fetch` (Docs 01, 02, 03, Phase 0 AP2)
   - File naming: `*.spec.ts` (Doc 19)
   - Import patterns: three-tier hierarchy (Docs 21, implementation guide §6)
   - JSDoc requirements: (Implementation guide §16, Doc 35)
   - Error handling patterns: (Implementation guide §11, Doc 18)
3. Identify any cases where test research recommends a pattern that contradicts the implementation guide

**Reverse (Test Research → Implementation Guide):** 4. Check whether the implementation guide's §16 includes the anti-pattern catalog (AP1-AP5) or references it 5. Check whether the implementation guide references the "meaningful vs trivial" testing standard (Doc 06) as a development standard 6. Check whether the implementation guide's code examples inadvertently demonstrate any anti-patterns 7. Check whether the implementation guide's §9 Testing section incorporates the incremental testing cadence (31 checkpoints, max 2-3 hrs between tests, never >800 lines without tests) 8. Verify the implementation guide's coverage targets match the reconciled numbers (>80% mandatory floor, 85-95% aspirational)

**Deliverable:** Bidirectional convention alignment checklist (Aligned/Misaligned/Missing per convention, with direction of needed update).

---

### Check 10: Anti-Pattern Compliance (Bidirectional)

**Question:** Are all flagged anti-pattern violations (AP1-AP5 from Phase 0) properly accounted for in both the test research AND the implementation guide? Does the implementation guide itself avoid demonstrating anti-patterns?

**Procedure:**

1. Extract the 5 anti-patterns from Phase 0 report:
   - AP1: Testing Response Content (asserting fixture data values)
   - AP2: Live Server Dependencies (real HTTP in tests)
   - AP3: Server Conformance Testing (testing spec compliance vs client behavior)
   - AP4: Asserting Data Shape (testing structure rather than behavior)
   - AP5: Over-Engineered Test Infrastructure (custom frameworks)
2. Verify the implementation guide's development standards address each
3. Scan implementation guide code examples (§6, §7, §11, §12) for any examples that would produce AP1/AP3/AP4 tests if followed literally
4. Verify the test research's review notices cover all at-risk documents (16/16 confirmed in Phase 4)
5. Check whether the anti-pattern catalog should be referenced/summarized in the implementation guide's §16

**Deliverable:** Anti-pattern cross-reference matrix with implementation guide example audit.

---

### Check 11: Fixture Strategy Alignment (Bidirectional)

**Question:** Does the fixture strategy align between both documents, and should the implementation guide incorporate the refined fixture guidance from the test research?

**Procedure:**

**Forward:**

1. Extract implementation guide's fixture references (§9)
2. Cross-reference against Doc 15 §5.2 (revised fixture structure under `fixtures/csapi/`)
3. Verify the implementation guide doesn't reference the old `fixtures/ogc-api/csapi/` structure

**Reverse:** 4. Check whether the implementation guide should incorporate Doc 15 Part 2's key finding: embedded fixture metadata is hallucinated content — use descriptive filenames + git history instead 5. Check whether the fixture count (~280 fixtures) should be noted in §9 6. Check whether the fixture sourcing strategy (OGC spec examples, real server responses from gnosis-earth/OpenSensorHub) should be documented in the implementation guide 7. Verify the URL-path-mirroring convention is explained or cross-referenced

**Deliverable:** Fixture alignment summary with update recommendations.

---

### Check 12: Terminology Consistency

**Question:** Does the implementation guide use terms consistently with how the test research has defined them?

**Procedure:**

1. Check 10 key terms identified in Phase 4 Check 1:
   - meaningful test, trivial test, fixture, unit test, integration test, end-to-end test, edge case, deep testing, client-oriented, server-oriented
2. Verify the implementation guide's usage of "integration test" vs "end-to-end test" aligns with the working definition established in Phase 4 H6 (integration = multi-component with mocked HTTP; end-to-end = real servers, out of scope)
3. Check for any SensorThings API terminology in the implementation guide (Phase 1 H1 catch)
4. Verify the 9 resource type names are consistently CSAPI-correct throughout

**Deliverable:** Terminology consistency checklist.

---

## Execution Strategy

**Read order:**

_Forward pass (Implementation Guide → Test Research):_

1. Implementation guide §5-§8 (the components) — extract what needs testing
2. Implementation guide §9 (testing section) — extract stated test expectations
3. Implementation guide §13-§16 (estimates, standards) — extract constraints
4. Test research docs in component order (Docs 22, 12, 08-11, 16, etc.) — verify coverage
5. Doc 19 (file inventory) — verify structure alignment
6. Doc 34 (test utilities) — verify helper alignment

_Reverse pass (Test Research → Implementation Guide):_ 7. Phase 0 report — extract anti-patterns, client responsibilities, architectural lessons 8. Phase 1-4 reports — extract all corrections and scope decisions 9. Docs 15/15P2 — extract fixture structure refinements 10. Doc 06 — extract meaningful/trivial definitions 11. Docs 08, 26, 28, 29, 31 — extract specification details 12. Re-read implementation guide §3, §9, §11, §16 — identify where reverse findings should land

**Estimated effort:** 4-5 hours (increased from 3-4 to accommodate reverse checks)

**Output:** Alignment report with severity-rated findings (Critical/High/Medium/Low), organized into two sections:

- **Part I findings:** Test research gaps/issues relative to implementation guide
- **Part II findings:** Implementation guide improvements informed by test research

---

## Acceptance Criteria

The cross-reference is complete when:

**Forward (Implementation Guide → Test Research):**

- [ ] All 12 implementation components have verified test coverage (Check 1)
- [ ] All ~70-80 QueryBuilder methods have verified test scenarios (Check 2)
- [ ] Test estimates are reconciled to one authoritative number (Check 3)
- [ ] All orphan test specs are accounted for (Check 4)

**Reverse (Test Research → Implementation Guide):**

- [ ] All scope decisions verified as propagated or flagged (Check 5)
- [ ] Client responsibility model verified in implementation guide (Check 6)
- [ ] Architectural patterns verified as current (Check 7)
- [ ] Specification enrichment opportunities documented (Check 8)

**Bidirectional:**

- [ ] All conventions aligned in both directions (Check 9)
- [ ] All anti-patterns accounted for in both documents (Check 10)
- [ ] Fixture strategy aligned in both documents (Check 11)
- [ ] Terminology consistent across both documents (Check 12)

**Final:**

- [ ] Report generated with severity-rated findings
- [ ] All Critical and High findings resolved
- [ ] Implementation guide updated where warranted
