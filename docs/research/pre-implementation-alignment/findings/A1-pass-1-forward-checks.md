# A1 Pass 1: Forward Checks (Implementation Guide → Test Research)

**Date:** February 13, 2026  
**Phase:** Pre-Implementation Alignment  
**Step:** A1, Pass 1 of 3  
**Status:** Complete

---

## Summary

Pass 1 executes the four forward checks from the A1 research plan, asking: _"Is every component in the implementation guide adequately covered by test research?"_

**Overall Assessment:** Test research provides **strong but imperfect** coverage of the implementation guide. All 12 components have at least partial coverage, with 7 rated Complete and 5 rated Partial. No component is Missing. The most significant gaps are in helper method dedicated testing, type system explicit coverage for 5/9 resource interfaces, format detector fallback detection, and validator content validation as a standalone spec.

**Quick Stats:**

- Components assessed: 12
- Complete coverage: 7 (58%)
- Partial coverage: 5 (42%)
- Missing coverage: 0 (0%)
- QueryBuilder methods covered: ~80/80 (100%) with 188 test scenarios
- Estimate discrepancy: File count (17 vs 22), line ranges overlapping but non-identical
- Orphans confirmed: 2 properly flagged (Doc 32 partial, Doc 33 full), 1 correctly deferred (Doc 16 Binary SWE)

---

## Check 1: Component Coverage

**Question:** Does every component in the implementation guide have corresponding test specifications in the research?

### Coverage Matrix

| #   | Component                  | Guide § | Test Docs              | Rating       | Details                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | -------------------------- | ------- | ---------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Conformance Reader         | §5      | Doc 22                 | **Complete** | 25 CSAPI conformance classes, 8 server profiles, `hasConnectedSystems` getter, `checkHasConnectedSystems()`, malformed/missing responses, 8 named scenarios (S1-S8)                                                                                                                                                                                                                                                                          |
| 2   | Collections Reader         | §5      | Doc 22                 | **Complete** | `csapiCollections` getter, collection-based resource availability detection, resource client initialization                                                                                                                                                                                                                                                                                                                                  |
| 3   | OgcApiEndpoint Integration | §5      | Docs 04, 05, 14        | **Complete** | `csapi()` factory method, caching, entry point for all 4 integration workflows (Discovery, Observation, Command, Navigation). Doc 04 specifies per-file breakdowns; Doc 05 provides phase-by-phase task mapping; Doc 14 defines 26 integration scenarios                                                                                                                                                                                     |
| 4   | CSAPIQueryBuilder          | §6      | Docs 08, 12, 13, 23-29 | **Complete** | 188 test scenarios across all 9 resource types, all ~80 methods inventoried with priority levels (P0-P3), nested endpoints (15 chains), URL encoding (15 scenarios), resource availability, error conditions                                                                                                                                                                                                                                 |
| 5   | Helper Methods             | §6      | Docs 12, 34            | **Partial**  | `buildResourceUrl` and `buildQueryString` tested _indirectly_ only — no dedicated unit tests. `extractAvailableResources` not specified in Doc 34 at all. Doc 12 §24.3 marks all three as "✅ Tested indirectly via all methods" but no standalone test file or section targets them directly                                                                                                                                                |
| 6   | Type System (model.ts)     | §6      | Doc 21                 | **Partial**  | 31 types inventoried, compilation-only approach correctly identified, 6 test patterns defined. However: 5 of 9 resource interfaces (Procedure, SamplingFeature, Datastream, ControlStream, Command) lack explicit test code — covered only by "Similar tests for other resources" comment. Properties resource type has naming mismatch ("Control" in Doc 21 inventory). H4 review flag acknowledges shape-assertion patterns are zero-value |
| 7   | GeoJSON Handler            | §7      | Doc 11                 | **Complete** | All 5 Part 1 resource types with full property matrices. 150+ validation rules catalogued. `identifyResourceType()`, `parseValidTime()`, `parseAssociationLinks()`, FeatureCollection parsing, geometry constraints all specified. H3 review correctly flags some validation rules as server-side concerns                                                                                                                                   |
| 8   | SensorML Handler           | §7      | Doc 09                 | **Complete** | All 4 structure types (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess) with priority ratings. Recursive component parsing (10 nesting scenarios, cycle detection). 10/13 implementation guide areas fully aligned. **Critical pre-req gap:** No parser output TypeScript interface defined (C2 flag). Position/orientation partially deferred                                                                            |
| 9   | SWE Common Handler         | §7      | Doc 10                 | **Complete** | All 15 component types (6 simple, 3 range, 6 complex). All 3 encodings: JSON (48 tests), Text (43 tests), Binary (96 tests, ~50% of effort). Schema validation (16 scenarios). Binary identified as "highest rejection risk." **Pre-req gap:** No parser output TypeScript interfaces defined (H1/H2 flags)                                                                                                                                  |
| 10  | Format Detector            | §7      | Docs 22, 25            | **Partial**  | Media type inventory complete (7 types). Resource-format matrix complete. Format constants (`PART1_FORMATS`, `MEDIA_TYPES`, `FORMAT_MAP`) specified. **Missing:** Document structure analysis fallback NOT covered — no scenarios for detecting format from response body when Content-Type is ambiguous/missing. Parser dispatch/routing logic not deeply specified. Doc 25 H2: 45/50 scenarios test server behavior, not client code       |
| 11  | Validator                  | §7      | Doc 22                 | **Partial**  | `ConformanceError` class fully specified. Conformance-based validation (capability checks before CRUD) fully defined. **Missing:** Content validation as a standalone spec — schema compliance, cross-reference validation, batch validation, error reporting as described in implementation guide §7 Validator section are NOT covered by any dedicated test research document. Doc 22 covers conformance validation only                   |
| 12  | Worker Extensions          | §8      | Doc 16                 | **Complete** | All 9 CSAPI message types have scenarios (201 total). `PARSE_SWE_BINARY` worker offloading correctly deferred to Phase 4 (H3); binary parsing itself remains in scope per Doc 10. Performance thresholds correctly excluded (H2). Minimum viable estimate: ~200-300 lines. Entire doc Phase 4 gated (H1). Comprehensive estimate: 1,510-1,760 unit + 350-500 integration lines                                                               |

### Check 1 Findings Summary

| Severity   | Count | Details                                                                                                                                                                               |
| ---------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Medium** | 3     | Helper methods lack dedicated tests (Component 5); Type system missing explicit test code for 5/9 interfaces (Component 6); Format detector missing fallback detection (Component 10) |
| **Low**    | 2     | Validator content validation not standalone spec (Component 11); Parser output TypeScript interfaces undefined for SensorML + SWE Common (Components 8, 9 — pre-req, not test gap)    |
| **Info**   | 2     | Doc 25 disproportionate (45/50 scenarios test server behavior for ~13 impl lines); Doc 11 validation rules partially flagged as server-side                                           |

---

## Check 2: Method-Level Coverage (QueryBuilder Deep Dive)

**Question:** Does the test research define test scenarios for all ~70-80 QueryBuilder methods across all 9 resource types?

### Method Coverage Matrix

| Resource Type     | Guide §             | Methods | Doc 12 § | Test Scenarios | Coverage     |
| ----------------- | ------------------- | ------- | -------- | -------------- | ------------ |
| Systems           | §6, lines 1193-1240 | ~12     | §5       | 32             | **Complete** |
| Deployments       | §6, lines 1241-1285 | ~8      | §6       | 21             | **Complete** |
| Procedures        | §6, lines 1286-1334 | ~8      | §7       | 17             | **Complete** |
| Sampling Features | §6, lines 1335-1385 | ~8      | §8       | 19             | **Complete** |
| Properties        | §6, lines 1386-1422 | ~6      | §9       | 14             | **Complete** |
| DataStreams       | §6, lines 1423-1487 | ~11     | §10      | 28             | **Complete** |
| Observations      | §6, lines 1488-1569 | ~9      | §11      | 22             | **Complete** |
| Control Streams   | §6, lines 1570-1629 | ~8      | §12      | 21             | **Complete** |
| Commands          | §6, lines 1630-1715 | ~10     | §13      | 24             | **Complete** |
| **TOTAL**         |                     | **~80** |          | **198**        | **Complete** |

### Additional Coverage Areas (Doc 12)

| Area                       | Doc 12 § | Scenarios                     | Coverage     |
| -------------------------- | -------- | ----------------------------- | ------------ |
| Nested Endpoints           | §14      | 15 parent→child chains        | **Complete** |
| URL Encoding Edge Cases    | §15      | 15 encoding scenarios         | **Complete** |
| Resource Availability      | §16      | Available/unavailable/partial | **Complete** |
| Error Conditions           | §17      | Referenced                    | **Complete** |
| Query Parameter Categories | §4       | 9 categories                  | **Complete** |

### Check 2 Findings

| Severity                 | Count | Details                                                                                                                                                                        |
| ------------------------ | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ~~**Low**~~ **Resolved** | 1     | `sortBy`/`sortOrder` parameters brought back into scope (MEDIUM priority) — essential for deterministic pagination. Guide §6 and Doc 12 §24.2 updated.                         |
| **Info**                 | 1     | Helper methods (`buildResourceUrl`, `buildQueryString`, `extractAvailableResources`) tested indirectly only — marked as "✅ Tested indirectly via all methods" in Doc 12 §24.3 |

**Assessment:** Method-level coverage is **excellent**. All ~80 public methods across all 9 resource types have defined test scenarios. The former `sortBy`/`sortOrder` gap has been resolved — sorting is now in scope (MEDIUM priority) as it is essential for deterministic pagination.

---

## Check 3: Estimate Consistency

**Question:** Do the test research estimates align with the implementation guide's stated test volume?

### Estimate Reconciliation Table

| Source                               | Test Files | Test Lines              | Impl Lines   | Test:Code Ratio |
| ------------------------------------ | ---------- | ----------------------- | ------------ | --------------- |
| **Implementation Guide §13**         | 17         | ~4,500-6,000            | ~4,614-6,094 | ~0.97:1         |
| **Doc 19 (authoritative inventory)** | 22         | ~4,040-5,340            | —            | —               |
| **Doc 20 (ratio validation)**        | —          | ~4,150-5,850 (adjusted) | ~4,850-6,500 | ~0.9-1.0:1      |
| **ROADMAP v3.0 summary**             | 17         | ~4,400-6,300            | ~4,850-6,500 | —               |
| **Doc 17 §2.1 (INFLATED ⚠️)**        | —          | ~13,090-17,016          | —            | —               |

### Discrepancy Analysis

#### D1: File Count (17 vs 22) — **Medium Severity**

The implementation guide and ROADMAP both state 17 test files. Doc 19 (authoritative inventory) lists 22 files. The 5-file discrepancy consists of:

- 3 format parser test files: `sensorml-parser.spec.ts`, `swe-parser.spec.ts`, `geojson-csapi-parser.spec.ts`
- 3 test utility files: `test-utils.ts`, `test-helpers.ts`, `test-fixtures.ts`

The implementation guide may have folded format parser tests into "Format tests: 15 files" and excluded utility files from the count. Doc 19's 22-file breakdown is the more granular and authoritative count.

**Recommendation:** The implementation guide should adopt Doc 19's 22-file count, or explicitly note that its 17-file count excludes test utility files and groups format tests differently.

#### D2: Test Line Ranges — **Low Severity**

All non-inflated sources produce overlapping ranges:

- Guide: 4,500-6,000
- Doc 19: 4,040-5,340
- Doc 20: 4,150-5,850
- ROADMAP: 4,400-6,300

The combined envelope is ~4,040-6,300. Doc 19's narrower range (4,040-5,340) is the most conservative and file-level-validated. The guide's upper bound (6,000) and ROADMAP's upper bound (6,300) exceed Doc 19's upper bound by ~12-18%.

**Recommendation:** Adopt Doc 19's 4,040-5,340 as the authoritative range. The guide's ~4,500-6,000 is acceptable as it overlaps substantially, but the upper end may be optimistic compared to the file-level inventory.

#### D3: Doc 17 Inflation — **Already Resolved**

Doc 17 §2.1's ~13,090-17,016 line total is flagged with an explicit `⚠️ Estimate Discrepancy (H1 review fix)` notice stating: _"This component-level total is ~3× higher than all other estimates."_ Root cause: component estimates developed independently without reconciliation. The discrepancy notice correctly directs readers to Doc 19's authoritative number. **No action needed.**

#### D4: Test-to-Code Ratio — **Info**

Doc 20 validates the CSAPI ratio at ~0.9-1.0:1 against upstream average 1.45:1 and median 1.13:1. Verdict: "conservative but appropriate." Upstream range: 0.10:1 (EDR) to 2.47:1 (WMTS). CSAPI falls within the lower half of the upstream range but above the minimum.

### Check 3 Findings

| Severity     | Count | Details                                                                                        |
| ------------ | ----- | ---------------------------------------------------------------------------------------------- |
| **Medium**   | 1     | File count discrepancy: Guide says 17, Doc 19 says 22. Guide should update or reconcile.       |
| **Low**      | 1     | Test line upper bounds slightly exceed Doc 19's authoritative range. Not materially impactful. |
| **Resolved** | 1     | Doc 17 §2.1 inflation already flagged with H1 discrepancy notice.                              |

---

## Check 4: Orphan Detection

**Question:** Does the test research define test specifications for anything that doesn't exist in the implementation guide?

### Orphan Assessment Table

| Test Doc   | Content                                 | Impl Guide Counterpart?                                                                              | Disposition                                                                                                                                                                                                   | Status              |
| ---------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **Doc 32** | Real-world server compatibility testing | ~35% overlaps §5 conformance. ~65% has no counterpart (live server URLs, credentials, rate limiting) | **Partially orphaned** — AP2 heavily bannered. Salvageable ~35% overlaps with Doc 22.                                                                                                                         | ✅ Properly flagged |
| **Doc 33** | Performance and efficiency testing      | None. Zero performance testing in guide or upstream.                                                 | **Fully orphaned** — `⚠️ PERFORMANCE TESTING IS NOT IN SCOPE ⚠️` banner. Retained as reference artifact.                                                                                                      | ✅ Properly flagged |
| **Doc 16** | PARSE_SWE_BINARY message type           | §7 SWE Common (Binary encoding described) and §8 Worker (message type listed)                        | **Worker offloading deferred to Phase 4** — H3 flag applies to the worker message type only. Binary SWE parsing itself (Doc 10, 96 tests) is in scope per implementation guide §7 and Phase 2D P4 assessment. | ✅ Properly flagged |
| **Doc 31** | Command lifecycle testing               | §6 Commands section (10 methods, status/result/cancel)                                               | **NOT orphaned** — in-scope, AP1/AP4 on test _implementations_ only. Spec analysis, scenarios, state machine, and fixture designs are valid.                                                                  | ✅ Properly flagged |

### Additional Over-Specification Observations

These are not orphans (the tested component exists) but represent disproportionate or misdirected test specifications:

| Test Doc   | Observation                                                                                                                                                                                                                      | Severity                                                                        |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Doc 25** | 45 of 50 test scenarios test server HTTP response behavior, not client code (H2 flag). 1,800 estimated LOC for ~13 lines of implementation. Accept header tests (10 scenarios) test a feature the client doesn't implement (H9). | **Medium** — disproportionate effort, most scenarios non-implementable          |
| **Doc 11** | 150+ validation rules catalogued, but H3 review flags `validateUID()`, `validateName()`, etc. as server-side concerns. Parser should extract, not validate vocabulary membership.                                                | **Low** — rules retained for reference, H3 flag ensures they won't become tests |
| **Doc 09** | VAL-SML-_ and ERR-SML-_ IDs test spec conformance, not parser extraction (C2 flag). Live server fixture sourcing planned in §8 (AP2).                                                                                            | **Low** — C2 flag ensures reframing before implementation                       |
| **Doc 10** | Constraint/UOM/temporal validation entries in §6 conflate parser with validator (M2).                                                                                                                                            | **Low** — M2 flag ensures separation during implementation                      |

### Check 4 Findings

| Severity                 | Count | Details                                                                                          |
| ------------------------ | ----- | ------------------------------------------------------------------------------------------------ |
| **None (Critical/High)** | 0     | All known orphans are properly flagged with appropriate banners                                  |
| **Medium**               | 1     | Doc 25 disproportionate specification (~1,800 LOC for ~13 impl lines, 90% server-behavior tests) |
| **Low**                  | 3     | Docs 09, 10, 11 parser/validator conflation — already flagged with review banners                |
| **Info**                 | 1     | Doc 33 fully orphaned by design — retained as reference artifact                                 |

---

## Pass 1 Consolidated Findings

### By Severity

| Severity     | Count | Findings                                                                                                                                                                                                                                                                                                                                                                          |
| ------------ | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Critical** | 0     | —                                                                                                                                                                                                                                                                                                                                                                                 |
| **High**     | 0     | —                                                                                                                                                                                                                                                                                                                                                                                 |
| **Medium**   | 5     | (1) Helper methods lack dedicated unit tests; (2) Format detector missing document structure fallback; (3) File count discrepancy (17 vs 22); (4) Type system missing explicit test code for 5/9 interfaces; (5) Doc 25 over-specified for implementation scope                                                                                                                   |
| **Low**      | 6     | (1) Validator content validation not standalone-specified; (2) SensorML parser output interface undefined; (3) SWE Common parser output interfaces undefined; ~~(4) sortBy/sortOrder not covered~~ **(RESOLVED — in scope)**; (5) Test line upper bounds slightly exceed authoritative range; (6) Doc 09 parser/validator conflation; (7) Docs 10, 11 parser/validator conflation |
| **Info**     | 3     | (1) Doc 33 fully orphaned by design; (2) Doc 25 most scenarios test server behavior; (3) Doc 17 inflation already resolved                                                                                                                                                                                                                                                        |

### Action Items for Implementation Guide Update (Pass 3)

These items are candidates for the reverse pass to evaluate whether the implementation guide should be updated:

1. **File count reconciliation** — Update §13 to state 22 files (per Doc 19) or explain why 17 is used
2. **Helper method testing guidance** — Consider noting in §9 that helpers are tested indirectly via public API methods
3. **Format detector fallback** — Verify §7 Format Detector section describes document structure analysis; if so, test research (Doc 25) needs a scenario for it
4. **Validator scope** — Consider whether §7 Validator section's content validation requirements need a dedicated test research document, or whether the existing coverage across Docs 09, 10, 11, 22 is sufficient when combined
5. **Parser output interfaces** — The C2/H1/H2 flags on Docs 09 and 10 indicate these are implementation pre-requisites, not test gaps per se. The implementation guide already specifies the interfaces in §6 type system. No guide update needed.

---

## Conclusion

The forward direction (Implementation Guide → Test Research) is in **good shape**. No critical or high-severity gaps exist. The test research corpus comprehensively covers all 12 implementation guide components and all ~80 QueryBuilder methods. The 5 medium-severity findings are addressable without structural changes — they represent refinement opportunities, not coverage holes.

The most actionable finding is the **file count discrepancy** (17 vs 22), which should be reconciled in the implementation guide before coding begins to avoid confusion during development.

Pass 2 will execute the reverse checks (Test Research → Implementation Guide) to identify what the test research discovered that the implementation guide should incorporate.

---

_Generated by A1 Pass 1 execution. Next: A1 Pass 2 (Checks 5-8, Reverse Checks)._
