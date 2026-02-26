# A1 Final Report: Test Research ↔ Implementation Guide Bidirectional Alignment

**Date:** February 13, 2026  
**Phase:** Pre-Implementation Alignment  
**Step:** A1 of 5  
**Status:** Complete

---

## Executive Summary

This report consolidates all findings from the A1 bidirectional alignment analysis across 12 checks executed in 3 passes:

- **Pass 1 (Forward):** Checks 1-4 — Implementation Guide → Test Research
- **Pass 2 (Reverse):** Checks 5-8 — Test Research → Implementation Guide
- **Pass 3 (Bidirectional):** Checks 9-12 — Convention, Anti-Pattern, Fixture, Terminology alignment

### Overall Alignment Status

The implementation guide and test research corpus are **structurally well-aligned** — every implementation component has test coverage, and all ~80 QueryBuilder methods have defined scenarios. However, the guide (v7.0, Feb 5) pre-dates the test research review phases (Feb 12-13) by 7 days. This creates a **propagation gap** where ~90% of review-phase scope decisions, corrections, and specification details have not been reflected back into the guide.

### Finding Totals Across All 12 Checks

| Severity        | Count | Distribution                                                           |
| --------------- | ----- | ---------------------------------------------------------------------- |
| **Critical**    | 0     | —                                                                      |
| **High**        | 1     | Check 10 (§12 scenario examples use explicit `fetch()` with live URLs) |
| **Medium**      | 21    | Checks 1(3), 3(1), 4(1), 5(4), 6(1), 7(3), 8(5), 9(1), 10(1), 12(1)    |
| **Low**         | 24    | Checks 1(2), 2(1), 3(1), 5(9), 6(1), 7(3), 8(3), 9(3), 10(1), 12(0)    |
| **Info**        | 5     | Checks 1(3), 3(1), 11(1)                                               |
| **Clean / N/A** | 12    | Checks 5(4), 7(4), 11(3), 12(1)                                        |

**No Critical findings.** One High finding (§12 AP2 risk). 21 Medium findings are primarily propagation gaps — the guide needs updates to absorb test research decisions, not structural redesign.

---

## Part I: Forward Check Findings (Implementation Guide → Test Research)

_"Is every component in the guide adequately covered by test research?"_

### Check 1: Component Coverage

| #   | Component                  | Guide § | Test Docs              | Rating       | Gap Details                                                                                                                                                  |
| --- | -------------------------- | ------- | ---------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Conformance Reader         | §5      | Doc 22                 | **Complete** | 25 conformance classes, 8 server profiles, 8 scenarios                                                                                                       |
| 2   | Collections Reader         | §5      | Doc 22                 | **Complete** | `csapiCollections` getter, resource availability detection                                                                                                   |
| 3   | OgcApiEndpoint Integration | §5      | Docs 04, 05, 14        | **Complete** | `csapi()` factory, 4 integration workflows, 26 scenarios                                                                                                     |
| 4   | CSAPIQueryBuilder          | §6      | Docs 08, 12, 13, 23-29 | **Complete** | 188 scenarios across 9 resource types, all ~80 methods                                                                                                       |
| 5   | Helper Methods             | §6      | Docs 12, 34            | **Partial**  | `buildResourceUrl`, `buildQueryString` tested indirectly only; `extractAvailableResources` not in Doc 34                                                     |
| 6   | Type System (model.ts)     | §6      | Doc 21                 | **Partial**  | 5/9 resource interfaces lack explicit test code; naming mismatch ("Control" in Doc 21)                                                                       |
| 7   | GeoJSON Handler            | §7      | Doc 11                 | **Complete** | 5 Part 1 resource types, 150+ validation rules, H3 server-side flag                                                                                          |
| 8   | SensorML Handler           | §7      | Doc 09                 | **Complete** | 4 structure types, recursive parsing, 10/13 areas aligned. Pre-req gap: no parser output interface (C2)                                                      |
| 9   | SWE Common Handler         | §7      | Doc 10                 | **Complete** | 15 component types, 3 encodings, 96 binary tests. Pre-req gaps: no parser output interfaces (H1/H2)                                                          |
| 10  | Format Detector            | §7      | Docs 22, 25            | **Partial**  | Document structure analysis fallback NOT covered; Doc 25 H2: 45/50 scenarios test server behavior                                                            |
| 11  | Validator                  | §7      | Doc 22                 | **Partial**  | Conformance validation covered; content validation (schema compliance, batch validation) NOT standalone-specified                                            |
| 12  | Worker Extensions          | §8      | Doc 16                 | **Complete** | 9 message types, 201 scenarios. `PARSE_SWE_BINARY` worker offloading deferred to Phase 4 (binary parsing itself remains in scope per Doc 10). Phase 4 gated. |

**Check 1 Findings:**

| ID    | Severity   | Finding                                                                                                                                                                                                | Resolution                                                                         |
| ----- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| C1-M1 | **Medium** | Helper methods lack dedicated unit tests — tested only indirectly via public API methods (Component 5)                                                                                                 | Acceptable if helpers remain private. Add dedicated tests if helpers are extracted |
| C1-M2 | **Medium** | Type system missing explicit test code for 5/9 resource interfaces: Procedure, SamplingFeature, Datastream, ControlStream, Command (Component 6)                                                       | Add explicit shape-validation tests for all 9 interfaces during implementation     |
| C1-M3 | **Medium** | Format detector missing document structure analysis fallback — no test scenarios for detecting format from response body when Content-Type is ambiguous/missing (Component 10)                         | Add fallback detection scenarios to Doc 25                                         |
| C1-L1 | **Low**    | Validator content validation not standalone-specified — schema compliance, cross-reference validation, batch validation described in guide §7 but not covered by any dedicated test doc (Component 11) | Existing coverage across Docs 09, 10, 11, 22 may suffice when combined             |
| C1-L2 | **Low**    | Parser output TypeScript interfaces undefined for SensorML + SWE Common (Components 8, 9 — C2/H1/H2 pre-req flags)                                                                                     | Implementation pre-requisite, not test gap. Guide §6 type system specifies these   |
| C1-I1 | **Info**   | Doc 25 disproportionate: 45/50 scenarios test server HTTP response behavior for ~13 lines of implementation code                                                                                       | Covered by H2 review banner                                                        |
| C1-I2 | **Info**   | Docs 09, 10, 11 parser/validator conflation flagged with C2/M2/H3 review banners                                                                                                                       | Ensured reframing before implementation                                            |

---

### Check 2: Method-Level Coverage (QueryBuilder Deep Dive)

| Resource Type     | Methods | Scenarios | Coverage     |
| ----------------- | ------- | --------- | ------------ |
| Systems           | ~12     | 32        | **Complete** |
| Deployments       | ~8      | 21        | **Complete** |
| Procedures        | ~8      | 17        | **Complete** |
| Sampling Features | ~8      | 19        | **Complete** |
| Properties        | ~6      | 14        | **Complete** |
| DataStreams       | ~11     | 28        | **Complete** |
| Observations      | ~9      | 22        | **Complete** |
| Control Streams   | ~8      | 21        | **Complete** |
| Commands          | ~10     | 24        | **Complete** |
| **TOTAL**         | **~80** | **198**   | **Complete** |

Additional: Nested endpoints (15 chains), URL encoding (15 scenarios), resource availability, error conditions — all complete.

**Check 2 Findings:**

| ID    | Severity                 | Finding                                                                                                                                                                |
| ----- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C2-L1 | ~~**Low**~~ **Resolved** | `sortBy`/`sortOrder` parameters brought back into scope (MEDIUM priority) — sorting is essential for deterministic pagination. Guide §6 and Doc 12 §4.1/§24.2 updated. |
| C2-I1 | **Info**                 | Helper methods tested indirectly only (Doc 12 §24.3)                                                                                                                   |

---

### Check 3: Estimate Consistency

| Source                    | Test Files | Test Lines   |
| ------------------------- | ---------- | ------------ |
| Implementation Guide §13  | 17         | ~4,500-6,000 |
| Doc 19 (authoritative)    | 22         | ~4,040-5,340 |
| Doc 20 (ratio validation) | —          | ~4,150-5,850 |
| ROADMAP v3.0              | 17         | ~4,400-6,300 |

**Check 3 Findings:**

| ID    | Severity     | Finding                                                                                                                                  | Resolution                                  |
| ----- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| C3-M1 | **Medium**   | File count discrepancy: guide says 17 (line 4000), Doc 19 says 22. 5-file difference = 3 format parser test files + 3 test utility files | Update guide §13 to 22 files per Doc 19     |
| C3-L1 | **Low**      | Test line upper bounds slightly exceed Doc 19's authoritative range (guide: 6,000 vs Doc 19: 5,340). Not materially impactful.           | Adopt Doc 19's 4,040-5,340 as authoritative |
| C3-R1 | **Resolved** | Doc 17 §2.1 inflation (~13,090-17,016) already flagged with H1 discrepancy notice                                                        | No action needed                            |

---

### Check 4: Orphan Detection

| Test Doc | Content                                 | Disposition                                                                                                                                          |
| -------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Doc 32   | Real-world server compatibility testing | **Partially orphaned** — AP2 bannered. ~35% overlaps Doc 22                                                                                          |
| Doc 33   | Performance and efficiency testing      | **Fully orphaned** — OUT OF SCOPE banner. Retained as reference                                                                                      |
| Doc 16   | `PARSE_SWE_BINARY` message type         | **Worker offloading deferred to Phase 4** — H3 flag applies to worker message type only; binary SWE parsing itself is in scope (Doc 10, Phase 2D P4) |
| Doc 31   | Command lifecycle testing               | **NOT orphaned** — in-scope, AP1/AP4 on test implementations only                                                                                    |

**Check 4 Findings:**

| ID    | Severity   | Finding                                                                                                         |
| ----- | ---------- | --------------------------------------------------------------------------------------------------------------- |
| C4-M1 | **Medium** | Doc 25 over-specified: ~1,800 LOC for ~13 implementation lines; 90% scenarios test server behavior (H2 flagged) |
| C4-L1 | **Low**    | Docs 09, 10, 11 parser/validator conflation — already flagged with review banners                               |
| C4-I1 | **Info**   | Doc 33 fully orphaned by design — retained as reference artifact                                                |

---

## Part II: Reverse and Bidirectional Check Findings (Checks 5-12)

_"Has the test research discovered anything the implementation guide should incorporate?"_

### Check 5: Scope Decisions Not Yet Reflected

21 scope decisions were checked for propagation from test research to implementation guide.

| ID    | Scope Decision                                          | Source                  | Propagated?                                                                                                                       | Severity                                |
| ----- | ------------------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| C5-M1 | Performance testing OUT OF SCOPE                        | Phase 2F H2, Phase 3 H1 | **No** — §9/§16 don't note exclusion                                                                                              | **Medium**                              |
| C5-M2 | Real-world server testing rejected (AP2)                | Phase 2E C1             | **No** — no test scope exclusions in guide                                                                                        | **Medium**                              |
| C5-M3 | `PARSE_SWE_BINARY` worker offloading deferred (Phase 4) | Phase 2F H3             | **Correctly not reflected** — §7 SWE Common correctly treats binary parsing as in-scope; only the worker message type is deferred | **Low** (downgraded — guide is correct) |
| C5-M4 | `OgcApiEndpoint.fromUrl()` doesn't exist                | Phase 1 M3              | **No** — still used in §11 (line 3089)                                                                                            | **Medium**                              |
| C5-L1 | Worker extensions = Phase 4 only                        | Phase 2F H1             | **No** — §8 has no phasing constraint                                                                                             | **Low**                                 |
| C5-L2 | Enterprise review process simplified                    | Phase 2C H2             | **No** — §16 doesn't reference cadence                                                                                            | **Low**                                 |
| C5-L3 | Incremental testing cadence (max 2-3 hrs)               | Phase 2F P2             | **No** — §16 says only "write tests as you implement"                                                                             | **Low**                                 |
| C5-L4 | Doc 08 reclassified to spec reference                   | Phase 2D C1             | **No** — §4 doesn't mention reclassification                                                                                      | **Low**                                 |
| C5-L5 | Fixture count: ~280 → ~80-100                           | Phase 2A H1             | **No** — §9 doesn't specify counts                                                                                                | **Low**                                 |
| C5-L6 | Aggregate scope creep flagged (~683 → 80-120)           | Phase 2E S1             | **No** — guide doesn't note creep risk                                                                                            | **Low**                                 |
| C5-L7 | `ParameterValidationError` rejected                     | Phase 2E M1             | **No** — guide doesn't propose new error classes                                                                                  | **Low**                                 |
| C5-L8 | Shape-assertion template rejected                       | Phase 2D H4             | **No** — guide describes type tests without noting compilation-only                                                               | **Low**                                 |
| C5-L9 | Space encoding: `%20` not `+`                           | Phase 1 M4              | **No** — guide doesn't specify                                                                                                    | **Low**                                 |
| —     | `_metadata` fixture pattern = hallucinated              | Phase 2A C1             | N/A — guide doesn't reference `_metadata`                                                                                         | ✅                                      |
| —     | Fixture validation pipeline rejected                    | Phase 2A H2             | N/A — guide doesn't propose it                                                                                                    | ✅                                      |
| —     | `@specification` traceability dismantled                | Phase 2C C2             | N/A — dismantled before guide needed it                                                                                           | ✅                                      |
| —     | Colocated `.spec.ts` files                              | Phase 1 H2              | Reflected — guide shows colocated files                                                                                           | ✅                                      |
| —     | Path `src/ogc-api/csapi/`                               | Phase 2B M2             | Reflected — guide uses correct path                                                                                               | ✅                                      |
| —     | Coverage >80%                                           | Phase 3 H3              | Reflected — guide states >80%                                                                                                     | ✅                                      |
| —     | Conformance URI namespace corrected                     | Phase 1 M1              | **No** — guide doesn't list URIs explicitly                                                                                       | **Low**                                 |
| —     | SensorThings terminology corrected                      | Phase 1 H1              | See Check 12                                                                                                                      | —                                       |

**Summary:** 4 Medium, 9 Low, 4 N/A, 4 Reflected.

---

### Check 6: Client Responsibility Model

The 5 client responsibilities from Phase 0:

| #   | Responsibility                               | In Guide §3/§4?       |
| --- | -------------------------------------------- | --------------------- |
| 1   | **Parse** — Service documents                | Not explicitly stated |
| 2   | **Construct** — URLs with parameters         | Not explicitly stated |
| 3   | **Transform** — Responses to typed objects   | Not explicitly stated |
| 4   | **Handle** — Errors, edge cases, negotiation | Not explicitly stated |
| 5   | **Validate** — Inputs before requests        | Not explicitly stated |

The guide implicitly demonstrates all 5 through its components but never states this as a foundational framing. The §7 Validator section describes rules that blur client-side validation and server data correctness, which could be misinterpreted as AP3/AP4 without the client responsibility lens.

| ID    | Severity   | Finding                                                                                 | Resolution                                                            |
| ----- | ---------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| C6-M1 | **Medium** | Client responsibility model (5 responsibilities) not explicitly stated in §3/§4         | Add 5-responsibility statement to §3 Purpose and Scope                |
| C6-L1 | **Low**    | §7 Validator rules could be misinterpreted as test criteria for server data correctness | Add note clarifying these are implementation specs, not test criteria |

---

### Check 7: Architectural Patterns Refined by Test Research

| ID    | Pattern                                                                                  | Status                                                                                              | Severity   |
| ----- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------- |
| C7-M1 | Fixture directory not specified — §9 (line 2987) says "CSAPI test fixtures" without path | **Not reflected**                                                                                   | **Medium** |
| C7-M2 | Test file count: guide says 17 (line 4000), should be 22 per Doc 19                      | **Not reflected**                                                                                   | **Medium** |
| C7-M3 | `OgcApiEndpoint.fromUrl()` used in §11 (line 3089) — method doesn't exist                | **Incorrect**                                                                                       | **Medium** |
| C7-L1 | Test utility structure (3 files from Doc 34) not referenced                              | **Not reflected**                                                                                   | **Low**    |
| C7-L2 | Mocking convention (`globalThis.fetch`) not specified in §9/§16                          | **Not reflected**                                                                                   | **Low**    |
| C7-L3 | URL space encoding `%20` not `+` not specified                                           | **Not reflected**                                                                                   | **Low**    |
| —     | SensorThings terminology                                                                 | **Clean** — 2 instances of `FeaturesOfInterest` (lines 1459, 2731) are correct CSAPI/SensorML usage | ✅         |
| —     | QueryBuilder-not-standalone warning                                                      | **Present** — extensively documented in §4, §6 (lines 245, 485)                                     | ✅         |
| —     | File naming `*.spec.ts`                                                                  | **Reflected** — guide uses correct naming                                                           | ✅         |
| —     | `parseAndValidateUrl()`                                                                  | N/A — test utility, correctly absent from guide                                                     | ✅         |

---

### Check 8: Specification Details Discovered During Test Research

| ID    | Detail                                                                                                                     | Source      | Guide Gap                                                                             | Severity   |
| ----- | -------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------- | ---------- |
| C8-M1 | 16 parent-child relationships with 3-type taxonomy (Hierarchical/Compositional/Associative)                                | Doc 26      | Guide mentions "16 patterns" (line 936) but no type classification                    | **Medium** |
| C8-M2 | Temporal applicability matrix: which of 5 params applies to which resource types + `latest` special value for `resultTime` | Doc 28      | Guide lists params but no applicability matrix; no `latest`                           | **Medium** |
| C8-M3 | Bbox validation rules: antimeridian = 400 error, lat/lon ranges, 4 or 6 values, CRS84 only, null geometry exclusion        | Doc 29      | Guide shows `encodeBBox`/`validateBBox` (lines 782-799) but no validation constraints | **Medium** |
| C8-M4 | Command status lifecycle: PENDING→ACCEPTED→EXECUTING→COMPLETED\|FAILED\|CANCELED                                           | Docs 08, 31 | Guide describes `getCommandStatus()` but no state values or transitions               | **Medium** |
| C8-M5 | `obsFormat`/`cmdFormat` required parameters on schema endpoints                                                            | Doc 08      | Guide describes schema endpoints but not the required format parameter                | **Medium** |
| C8-L1 | Canonical URL equivalence guarantee                                                                                        | Doc 26      | Not stated                                                                            | **Low**    |
| C8-L2 | ISO 8601 format catalog (7 instant + 6 interval formats)                                                                   | Doc 28      | Guide shows one example only                                                          | **Low**    |
| C8-L3 | Properties resource is non-feature: `resources`/`itemType` not `features`/`featureType`                                    | Doc 08      | Guide treats all resources uniformly                                                  | **Low**    |

---

### Check 9: Convention and Standards Alignment

**Forward (Guide → Test Research):**

| Convention                         | Guide §16                 | Test Research              | Status                                               |
| ---------------------------------- | ------------------------- | -------------------------- | ---------------------------------------------------- |
| TypeScript strict mode             | ✅ Line 4157              | Consistent                 | **Aligned**                                          |
| >80% coverage (statement + branch) | ✅ Lines 4159, 4186, 3041 | Phase 3 H3: >80% mandatory | **Aligned**                                          |
| 100% public API JSDoc              | ✅ Line 4158              | Doc 35                     | **Aligned**                                          |
| Lint-clean code (ESLint)           | ✅ Line 4160              | Consistent                 | **Aligned**                                          |
| Three-tier type hierarchy          | ✅ Line 4164              | Doc 21                     | **Aligned**                                          |
| Helper methods, no inheritance     | ✅ Line 4165              | Phase 0 lesson             | **Aligned**                                          |
| Write tests as you implement       | ✅ Line 4151              | ROADMAP v3 cadence         | **Aligned** (but guide is less specific — see below) |
| Jest test framework                | ✅ Lines 2987, 3047       | All test docs assume Jest  | **Aligned**                                          |

**Reverse (Test Research → Guide):**

| Convention                                                     | Test Research Source    | In Guide §16?                                                                   | Status                     | Severity   |
| -------------------------------------------------------------- | ----------------------- | ------------------------------------------------------------------------------- | -------------------------- | ---------- |
| Anti-pattern catalog (AP1-AP5)                                 | Phase 0                 | **Not referenced**                                                              | **Missing**                | **Medium** |
| "Meaningful vs trivial" testing standard                       | Doc 06                  | **Not referenced**                                                              | **Missing**                | **Low**    |
| `globalThis.fetch` mocking convention                          | Phase 0 AP2             | **Not specified**                                                               | **Missing**                | **Low**    |
| Incremental cadence (31 checkpoints, max 2-3 hrs, max 800 LOC) | Phase 2F P2, ROADMAP v3 | **Partial** — line 4151 says "write tests as you implement" without quantifying | **Missing quantification** | **Low**    |

**Check 9 Findings:**

| ID    | Severity   | Finding                                                                      | Resolution                            |
| ----- | ---------- | ---------------------------------------------------------------------------- | ------------------------------------- |
| C9-M1 | **Medium** | Anti-pattern catalog (AP1-AP5) not referenced in §16 Development Standards   | Add cross-reference or summary to §16 |
| C9-L1 | **Low**    | "Meaningful vs trivial" testing standard (Doc 06) not referenced             | Consider adding as quality standard   |
| C9-L2 | **Low**    | `globalThis.fetch` mocking convention not in §9/§16                          | Add to §9 testing conventions         |
| C9-L3 | **Low**    | Incremental testing cadence quantification missing (max 2-3 hrs is unstated) | Add specific cadence to §16           |

---

### Check 10: Anti-Pattern Compliance

**AP Definitions (Phase 0):**

- **AP1:** Testing Response Content — asserting fixture data values
- **AP2:** Live Server Dependencies — real HTTP in tests
- **AP3:** Server Conformance Testing — testing spec compliance vs client behavior
- **AP4:** Asserting Data Shape — testing structure rather than behavior
- **AP5:** Over-Engineered Test Infrastructure — custom frameworks

**Guide Code Example Audit:**

23 TypeScript code blocks were audited across §6, §7, §11, §12. None are test examples (no `expect()`, `describe()`, `it()`). All are implementation/usage examples. The risk is indirect — a developer using these as test templates.

| Section                             | Blocks | AP Risk    | Details                                                                                                                                                                                                                                                                                                                |
| ----------------------------------- | ------ | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| §6 QueryBuilder (11 blocks)         | 11     | **Low**    | URL construction examples. Only 1 block (#9, line 1082) shows explicit `fetch()` — Command Execution Tracking pattern                                                                                                                                                                                                  |
| §7 Format Handlers (0 blocks)       | 0      | **None**   | No TypeScript code blocks in §7                                                                                                                                                                                                                                                                                        |
| §11 Developer Experience (7 blocks) | 7      | **Medium** | Block #13 (line 3121, Type-Safe Usage): strongest AP4 vector — enumerates `system.properties.name`, `.type`, `.geometry?.coordinates`. Blocks #14-15 (parser integration): AP4 risk from property enumeration. Blocks #16, #18 (error handling): **Good patterns** — correctly demonstrate client behavior testing     |
| §12 Usage Scenarios (5 blocks)      | 5      | **High**   | **All 5 scenario blocks use explicit `fetch()` against named live URLs** (`https://api.weather.com/csapi`, `https://api.uav-fleet.com/csapi`, etc.) with no mocking. 6-8+ `fetch()` calls per block. If copied as test templates → AP2. Response property access (`.properties.result`, `.properties.name`) → AP1 risk |

**Check 10 Findings:**

| ID     | Severity   | Finding                                                                                                                                                                                                                                                          | Resolution                                                                                                                                                                                                    |
| ------ | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C10-H1 | **High**   | §12 Usage Scenarios (lines 3350-3905): All 5 scenario blocks use explicit `fetch()` against live URLs with no mocking. These are the highest AP2 risk in the entire guide. A developer copying these as test templates would produce forbidden live-server tests | Add a note at start of §12 clarifying these are **application usage examples**, not test patterns. Consider adding a "Testing equivalent" sidebar showing how each scenario would be tested with mocked fetch |
| C10-M1 | **Medium** | §11 Type-Safe Usage (line 3121): Property enumeration pattern (`system.properties.name`, `.type`, `.geometry?.coordinates`) could template AP4 shape-assertion tests                                                                                             | Add comment or note distinguishing "accessing properties" (valid in implementation) from "asserting properties exist" (AP4 if testing fixture data)                                                           |
| C10-L1 | **Low**    | §11 Parser Integration (lines 3165-3253): SensorML and SWE Common parser usage shows deep property access that emphasizes structure enumeration over behavioral assertions                                                                                       | Risk mitigated by C2/H1/H2 review flags on Docs 09/10                                                                                                                                                         |

---

### Check 11: Fixture Strategy Alignment

**Forward (Guide → Test Research):**

| Aspect             | Guide §9                                                                                    | Test Research (Doc 15)                      | Status      |
| ------------------ | ------------------------------------------------------------------------------------------- | ------------------------------------------- | ----------- |
| Fixture concept    | ✅ "CSAPI test fixtures" (line 2987)                                                        | ✅ ~80-100 fixtures                         | **Aligned** |
| Fixture categories | ✅ Lines 3033-3039: spec examples, edge cases, large datasets, all formats, errors, schemas | ✅ Doc 15 §1.1 matches                      | **Aligned** |
| Fixture sourcing   | ✅ "example responses from CSAPI Parts 1 & 2 specifications" (line 3033)                    | ✅ Doc 15 §1.1-§4: OGC specs + hand-crafted | **Aligned** |

**Reverse (Test Research → Guide):**

| Aspect                                                  | Doc 15 Finding             | In Guide?                               | Status            | Severity                 |
| ------------------------------------------------------- | -------------------------- | --------------------------------------- | ----------------- | ------------------------ |
| Fixture directory path: `fixtures/csapi/sample-server/` | Doc 15 §5.2, Phase 2A H3   | **No** — path not specified             | **Missing**       | Already counted in C7-M1 |
| URL-path-mirroring convention                           | Doc 15 §5.1-§5.3           | **No** — not referenced                 | **Missing**       | See below                |
| No embedded metadata (hallucinated `_metadata`)         | Doc 15 Part 2, Phase 2A C1 | N/A — guide doesn't propose metadata    | **Clean**         | —                        |
| Fixture count: ~80-100 (revised from ~280)              | Doc 15 §1.1                | **No** — count not specified            | **Not reflected** | Already counted in C5-L5 |
| 3-phase sourcing plan                                   | Doc 15 §4                  | **No** — phased approach not referenced | **Not reflected** | See below                |

**Check 11 Findings:**

| ID     | Severity | Finding                                                                                                                                                                                                                                  | Resolution                         |
| ------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| C11-I1 | **Info** | Fixture strategy is broadly aligned (categories match, sourcing approach matches). The missing pieces are implementation details (directory path, URL-path-mirroring, fixture count, phased sourcing) already counted in C7-M1 and C5-L5 | No new findings — already captured |

---

### Check 12: Terminology Consistency

**"Integration test" vs "end-to-end" alignment:**

| Term               | Guide Usage                                                               | Test Research Definition (Phase 4 H6) | Status        |
| ------------------ | ------------------------------------------------------------------------- | ------------------------------------- | ------------- |
| "Integration test" | Line 2987: "integration tests (multi-component interaction)"              | Multi-component with mocked HTTP      | **Aligned**   |
| "End-to-End"       | Line 3018: **"Integration Tests (End-to-End Workflows)"** — parenthetical | Real servers, OUT OF SCOPE            | **Conflated** |

The guide's §9 heading "Integration Tests (End-to-End Workflows)" merges the two terms. Per test research conventions, "integration" = mocked multi-component tests and "end-to-end" = real servers (out of scope). The parenthetical "(End-to-End Workflows)" creates ambiguity about whether these tests use real HTTP or mocks.

**SensorThings API terminology scan:**

| Term Searched               | Occurrences          | Status                                                                                             |
| --------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| `ObservedProperties`        | 0                    | ✅ Clean                                                                                           |
| `SensorThings`              | 0                    | ✅ Clean                                                                                           |
| `FeaturesOfInterest`        | 2 (lines 1459, 2731) | ✅ **Correct usage** — DataStream property name and SensorML element name, not resource type names |
| `Sensors` (as STA resource) | 0                    | ✅ Clean — guide uses "Systems" throughout                                                         |

**9 CSAPI resource type names consistency:**

| Resource Type     | Guide Usage | Consistent? |
| ----------------- | ----------- | ----------- |
| Systems           | Throughout  | ✅          |
| Deployments       | Throughout  | ✅          |
| Procedures        | Throughout  | ✅          |
| Sampling Features | Throughout  | ✅          |
| Properties        | Throughout  | ✅          |
| DataStreams       | Throughout  | ✅          |
| Observations      | Throughout  | ✅          |
| Control Streams   | Throughout  | ✅          |
| Commands          | Throughout  | ✅          |

**Check 12 Findings:**

| ID     | Severity   | Finding                                                                                                                                                                                                                             | Resolution                                                                              |
| ------ | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| C12-M1 | **Medium** | §9 heading "Integration Tests (End-to-End Workflows)" (line 3018) conflates "integration" and "end-to-end". Test research defines these as distinct: integration = mocked multi-component, end-to-end = real servers (out of scope) | Rename to "Integration Tests (Multi-Component Workflows)" or simply "Integration Tests" |
| —      | —          | SensorThings terminology                                                                                                                                                                                                            | ✅ Clean                                                                                |
| —      | —          | 9 resource type names                                                                                                                                                                                                               | ✅ Consistent throughout                                                                |

---

## Recommendations

Prioritized action list across all 12 checks. Items grouped by priority tier.

**Document Key:**

- **Guide** = `docs/planning/csapi-implementation-guide.md` (the implementation guide)
- **Doc NN** = `docs/research/testing/findings/NN-*.md` (test research document)
- **Phase 0** = `docs/research/testing/review/phase-0-initial-assessment.md`

### Priority 1: Fix Before Coding (High + Top Medium)

| #   | Finding ID    | Action                                                                                                                                                                                    | Document to Change | Location in Document                                        |
| --- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ----------------------------------------------------------- |
| 1   | C10-H1        | Add note: "These are application usage examples, not test patterns. For test patterns, use mocked fetch per §9."                                                                          | **Guide**          | §12, before first scenario (line ~3340)                     |
| 2   | C5-M4 / C7-M3 | Replace `OgcApiEndpoint.fromUrl()` with `new OgcApiEndpoint()`                                                                                                                            | **Guide**          | §11, line 3089                                              |
| 3   | C3-M1 / C7-M2 | Update test file count from 17 to 22 per Doc 19                                                                                                                                           | **Guide**          | §13 Code Volume Summary, line 4000                          |
| 4   | C5-M3         | ~~WITHDRAWN~~ — Binary SWE parsing is in scope per guide and Doc 10 Phase 2D P4. Only the `PARSE_SWE_BINARY` worker message type (Doc 16) is deferred to Phase 4. No guide change needed. | N/A                | N/A                                                         |
| 5   | C8-M4         | Add command status lifecycle: `PENDING→ACCEPTED→EXECUTING→COMPLETED\|FAILED\|CANCELED`                                                                                                    | **Guide**          | §6 Commands Resource Methods                                |
| 6   | C8-M5         | Add `obsFormat` (required) to DataStream schema endpoint and `cmdFormat` (required) to ControlStream schema endpoint                                                                      | **Guide**          | §6 DataStreams + §6 ControlStreams schema method signatures |

### Priority 2: Incorporate Before Coding (Medium)

| #   | Finding ID | Action                                                                                                                                                                                      | Document to Change                                      | Location in Document                                                                   |
| --- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 7   | C6-M1      | Add explicit 5-responsibility model: Parse, Construct, Transform, Handle, Validate — "the client does these 5 things; everything else is the server's job"                                  | **Guide**                                               | §3 Purpose and Scope                                                                   |
| 8   | C9-M1      | Add cross-reference to AP1-AP5 anti-pattern catalog (Phase 0 report) as a development standard: "See Phase 0 report for 5 anti-patterns to avoid in test design"                            | **Guide**                                               | §16 Development Standards                                                              |
| 9   | C12-M1     | Rename heading from "Integration Tests (End-to-End Workflows)" to "Integration Tests (Multi-Component Workflows)"                                                                           | **Guide**                                               | §9 Testing, line 3018                                                                  |
| 10  | C8-M2      | Add table: which temporal params (`datetime`, `phenomenonTime`, `resultTime`, `executionTime`, `issueTime`) apply to which resource types. Add `latest` special value note for `resultTime` | **Guide**                                               | §6 Query Parameters Reference                                                          |
| 11  | C8-M3      | Add bbox validation rules: lat ±90, lon ±180, 4 or 6 values, antimeridian crossing = 400, CRS84 only, null geometry exclusion                                                               | **Guide**                                               | §6 helper methods (`validateBBox`)                                                     |
| 12  | C8-M1      | Add 3-type relationship taxonomy (Hierarchical: 2, Compositional: 12, Associative: 2) to navigation pattern documentation                                                                   | **Guide**                                               | §6 Navigation Patterns                                                                 |
| 13  | C5-M1      | Add scope exclusion: "Performance testing is out of scope for initial contribution"                                                                                                         | **Guide**                                               | §9 Testing or §3 Scope                                                                 |
| 14  | C5-M2      | Add scope exclusion: "Real-world server testing is out of scope — all tests use mocked HTTP (AP2)"                                                                                          | **Guide**                                               | §9 Testing or §3 Scope                                                                 |
| 15  | C7-M1      | Add fixture directory path: `fixtures/csapi/sample-server/` with URL-path-mirroring convention                                                                                              | **Guide**                                               | §9 Testing, Test Fixtures section                                                      |
| 16  | C10-M1     | Add note distinguishing "accessing parsed properties in implementation code" (valid) from "asserting raw fixture properties exist in tests" (AP4 violation)                                 | **Guide**                                               | §11 Type-Safe Usage, after code block at line 3121                                     |
| 17  | C1-M3      | Add test scenarios for format detection via document structure analysis when Content-Type is ambiguous/missing                                                                              | **Doc 25** (`25-format-content-negotiation-testing.md`) | New section or addendum                                                                |
| 18  | C1-M1      | Add note: "Helper methods (`buildResourceUrl`, `buildQueryString`, `extractAvailableResources`) are tested indirectly through all public API method tests, not via dedicated unit tests"    | **Guide**                                               | §6 Helper Methods section or §9 Testing                                                |
| 19  | C1-M2      | Add explicit test code examples for all 9 resource type interfaces (currently only 4/9 have explicit examples; 5 say "Similar tests for other resources")                                   | **Doc 21** (`21-type-system-testing-strategy.md`)       | §3-§4 test patterns for Procedure, SamplingFeature, Datastream, ControlStream, Command |

### Priority 3: Nice-to-Have (Low)

| #   | Finding ID | Action                                                                                                                                                  | Document to Change                                 |
| --- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 20  | C9-L1      | Reference Doc 06 "meaningful vs trivial" standard as a development standard                                                                             | **Guide** — §16                                    |
| 21  | C9-L2      | Add `globalThis.fetch` mocking convention                                                                                                               | **Guide** — §9                                     |
| 22  | C9-L3      | Quantify incremental cadence: max 2-3 hrs / max 800 LOC between test runs                                                                               | **Guide** — §16                                    |
| 23  | C5-L1      | Add note: worker extensions are Phase 4 only                                                                                                            | **Guide** — §8                                     |
| 24  | C5-L5      | Add estimated fixture count (~80-100 files)                                                                                                             | **Guide** — §9                                     |
| 25  | C8-L1      | Note canonical URL equivalence guarantee                                                                                                                | **Guide** — §6 Navigation                          |
| 26  | C8-L2      | Add ISO 8601 format catalog (7 instant + 6 interval patterns)                                                                                           | **Guide** — §6 Query Params                        |
| 27  | C8-L3      | Note Properties/Part 2 resources use `resources`/`itemType` not `features`/`featureType`                                                                | **Guide** — §6 Properties                          |
| 28  | C4-M1      | Reduce Doc 25 scope to match actual implementation (~13 lines); flag or remove 45/50 server-behavior scenarios                                          | **Doc 25**                                         |
| 29  | C2-L1      | ~~Add `sortBy`/`sortOrder` parameter test scenarios~~ **RESOLVED** — brought back into scope (MEDIUM priority). Guide §6 updated, Doc 12 §24.2 aligned. | **Doc 12** (`12-querybuilder-testing-strategy.md`) |
| 30+ | Various    | Remaining Low/Info findings from Checks 1-8                                                                                                             | See interim reports for details                    |

---

## Acceptance Criteria Checklist

From the A1 research plan's 12 acceptance criteria:

**Forward (Implementation Guide → Test Research):**

- [x] All 12 implementation components have verified test coverage (Check 1) — 7 Complete, 5 Partial, 0 Missing
- [x] All ~70-80 QueryBuilder methods have verified test scenarios (Check 2) — 198 scenarios across all 80 methods
- [x] Test estimates are reconciled to one authoritative number (Check 3) — Doc 19: 22 files, 4,040-5,340 lines
- [x] All orphan test specs are accounted for (Check 4) — 2 properly flagged, 1 deferred, 1 not orphaned

**Reverse (Test Research → Implementation Guide):**

- [x] All scope decisions verified as propagated or flagged (Check 5) — 21 checked, 4 propagated, 13 flagged, 4 N/A
- [x] Client responsibility model verified in implementation guide (Check 6) — Not present, flagged as C6-M1
- [x] Architectural patterns verified as current (Check 7) — 3 need update, 4 clean, 3 N/A
- [x] Specification enrichment opportunities documented (Check 8) — 8 opportunities documented (5 Medium, 3 Low)

**Bidirectional:**

- [x] All conventions aligned in both directions (Check 9) — 8 forward aligned, 4 reverse gaps flagged
- [x] All anti-patterns accounted for in both documents (Check 10) — All 5 APs checked; §12 High risk, §11 Medium risk
- [x] Fixture strategy aligned in both documents (Check 11) — Broadly aligned, detail gaps already captured in C7-M1/C5-L5
- [x] Terminology consistent across both documents (Check 12) — "Integration/End-to-End" conflation flagged; resource types clean

**Final:**

- [x] Report generated with severity-rated findings
- [ ] All Critical and High findings resolved — 0 Critical (pass), 1 High (C10-H1 — needs guide update)
- [ ] Implementation guide updated where warranted — Updates deferred to A1→Guide Update task

---

## Conclusion

The implementation guide and test research corpus are **well-aligned structurally** but have a **significant propagation gap** due to the 7-day timeline difference between guide v7.0 (Feb 5) and the review phases (Feb 12-13). The 1 High and 21 Medium findings are primarily addressable through guide text updates — no structural redesign is needed.

The most important actions before coding begins:

1. Fix `OgcApiEndpoint.fromUrl()` in §11 (incorrect API)
2. Update file count to 22 in §13
3. ~~Add Binary SWE deferral note to §7~~ (withdrawn — binary parsing is in scope; only worker offloading deferred)
4. Add AP2 warning to §12 scenarios
5. Add command state machine to §6

All 12 acceptance criteria checks are complete. The report identifies the specific updates needed to bring the implementation guide to full alignment with the test research corpus.

---

_Generated by A1 execution (Passes 1-3). Interim files retained for reference:_

- _A1-pass-1-forward-checks.md_
- _A1-pass-2-reverse-checks.md_
