# Research Plan A3: Contribution Goal ↔ Implementation Guide Alignment

**Date:** February 13, 2026  
**Phase:** Pre-Implementation Alignment  
**Step:** A3 (follows A1: Test Research ↔ Impl Guide, A2: ROADMAP ↔ Impl Guide + Test Research)  
**Status:** Not Started  
**Prerequisite:** A1 findings resolved — Implementation Guide is authoritative

---

## Objective

Cross-reference the **Contribution Goal and Definition** (v1.0, 32 lines) against the **updated Implementation Guide** (v7.0+, ~4,200+ lines) to verify that the Contribution Goal accurately summarizes the full implementation scope — no overclaims, no omissions, no stale numbers.

**Directionality:** The Implementation Guide (post-A1) is the **definitive source of truth**. The Contribution Goal is a high-level summary that should faithfully reflect what the guide specifies. This plan is almost entirely one-directional: checking the summary against the spec. A small reverse check verifies whether the Contribution Goal's framing (ecosystem positioning, value proposition) contains context the Implementation Guide could benefit from acknowledging.

**Core Questions:**

- Does every claim in the Contribution Goal match what the Implementation Guide actually defines?
- Are the numbers (methods, files, lines, resource types) accurate and current?
- Does the Contribution Goal omit any significant scope areas the Implementation Guide covers?
- Does the Contribution Goal promise anything the Implementation Guide doesn't deliver?
- Are terminology and naming consistent between the two documents?

---

## Documents Under Review

### Contribution Goal and Definition (the "scope summary" document)

**Contribution Goal and Definition** (`docs/planning/contribution-goal-and-definition.md`, v1.0, 32 lines)

A concise document stating the contribution's purpose, what it delivers, and its quality standards. Written early in the planning process. Has not been updated since v1.0 (February 5, 2026), meaning it predates all test research review findings and any A1 updates to the Implementation Guide.

### Implementation Guide (authoritative "what to build" document — post-A1)

**CSAPI Implementation Guide** (`docs/planning/csapi-implementation-guide.md`, v7.0+, ~4,200+ lines)

After A1 resolution, this is the canonical specification. Any discrepancy between the Contribution Goal and this document should be resolved by updating the Contribution Goal.

---

## Part I: Forward Checks (Contribution Goal → Implementation Guide)

_"Does every claim in the Contribution Goal match the Implementation Guide?"_

### Check 1: Goal Statement Accuracy

**Question:** Does the Contribution Goal's high-level purpose statement accurately reflect what the Implementation Guide defines?

**Procedure:**

1. Read the Contribution Goal's opening paragraph:
   > "Enable developers to interact with sensor networks, observation data, and system control through the Camptocamp OGC Client Library using the same unified interface they already use for other OGC APIs."
2. Verify against Implementation Guide §3 (Purpose and Scope) and §4 (Architecture Overview)
3. Check whether "sensor networks", "observation data", "system control" accurately describe the CSAPI scope
4. Check whether "unified interface" / "same interface they already use" is the correct integration framing for the factory method pattern
5. Verify the second paragraph's claims: "specification-complete", "critical ecosystem gap", "TypeScript support", "sensor system discovery, real-time observation queries, historical data analysis, remote system control"

**Deliverable:** Goal statement accuracy assessment — accurate / needs rewording.

---

### Check 2: Core Integration Claims

**Question:** Do the five Core Integration bullet points match the Implementation Guide?

**Procedure:**

1. **"Single QueryBuilder class with 70-80 methods covering all 9 CSAPI resource types"**

   - Verify "single class" matches Implementation Guide §6 (is it one class or multiple?)
   - Verify method count: does the guide define 70-80 methods? (Check post-A1 count)
   - Verify all 9 resource types listed match the guide's resource types exactly: Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands

2. **"Factory method integration pattern following established library architecture (EDR pattern)"**

   - Verify the guide specifies a factory method pattern (§5, OgcApiEndpoint integration)
   - Verify the EDR pattern is the correct upstream reference

3. **"Resource validation in all methods with fail-fast error handling"**

   - Verify the guide specifies resource validation (~2 lines per method, §6)
   - Verify "fail-fast" matches the guide's error handling strategy (§11)

4. **"Complete query parameter support (spatial, temporal, hierarchical, relationship-based, property-based filters)"**

   - Verify all 5 parameter categories exist in the guide
   - Check whether the guide lists any additional parameter categories not mentioned here

5. **"Both pagination modes (offset-based and cursor-based)"**
   - Verify the guide specifies both modes (§6 or parameter docs)

**Deliverable:** Per-bullet accuracy assessment with specific discrepancies noted.

---

### Check 3: Format Support Claims

**Question:** Do the four Format Support bullet points match the Implementation Guide §7?

**Procedure:**

1. **"SensorML 3.0 parser with complete type system for all system models and recursive component parsing"**

   - Verify the guide specifies SensorML 3.0 parsing (§7)
   - Verify "all system models" — does the guide list SimpleProcess, AggregateProcess, PhysicalSystem, PhysicalComponent? Does the Contribution Goal's claim match?
   - Verify "recursive component parsing" is in the guide

2. **"SWE Common 3.0 parser supporting all three encodings (JSON, Text/CSV, Binary) with schema validation"**

   - Verify all three encodings are in the guide
   - **Critical check:** The `PARSE_SWE_BINARY` worker message type (Doc 16) is deferred to Phase 4, but binary SWE _parsing_ itself (Doc 10) is IN SCOPE per the implementation guide §7 and Phase 2D assessment (M2/P4: "sound and directly usable"). The Contribution Goal's "all three encodings" is correct for parsing.
   - Verify "schema validation" matches the guide's validator component

3. **"GeoJSON extensions recognizing all CSAPI-specific resource types and properties"**

   - Verify against guide §7 GeoJSON handler section
   - Verify "all CSAPI-specific resource types" is accurate (featureType recognition)

4. **"Format detection and content negotiation for all CSAPI media types"**
   - Verify format detector extensions in the guide (§7)
   - Check whether "content negotiation" is accurately described or overscoped

**Deliverable:** Per-bullet accuracy assessment. Note: Binary SWE _parsing_ is in scope (Doc 10); only `PARSE_SWE_BINARY` worker offloading (Doc 16) is deferred to Phase 4.

---

### Check 4: Number Accuracy

**Question:** Are all specific numbers in the Contribution Goal current and consistent with post-A1 Implementation Guide values?

**Procedure:**

1. **"70-80 methods"** — verify against Implementation Guide §6 actual count
2. **"9 CSAPI resource types"** — verify count
3. **"1,750-2,400 lines of interfaces"** — verify against Implementation Guide model.ts estimate
4. **">80% test coverage"** — verify against Implementation Guide §9 / post-A1 reconciled target
5. **"24 implementation files (~4,614-6,094 lines)"** — verify against Implementation Guide §14 file inventory
6. **"17 test files (~4,500-6,000 lines)"** — verify against Implementation Guide (and check for 17 vs 22 discrepancy from A1/A2)
7. Cross-reference all numbers against the ROADMAP summary table for three-way consistency

**Deliverable:** Number reconciliation table with current authoritative values.

---

### Check 5: Quality Standards Accuracy

**Question:** Do the Quality Standards claims match the Implementation Guide's actual requirements?

**Procedure:**

1. **"Full TypeScript type safety with three-tier type hierarchy"** — verify the guide specifies three-tier (shared → ogc-api → csapi)
2. **">80% test coverage with comprehensive unit, integration, and end-to-end tests"**
   - Verify >80% target
   - **Critical check:** "end-to-end tests" — does this contradict the test research decision that real-server/e2e testing is OUT OF SCOPE (AP2)? The Contribution Goal may need rewording if "end-to-end" means real-server tests
3. **"JSDoc documentation for all public APIs"** — verify against guide §16
4. **"Compliance with OGC API - Connected Systems specifications (Parts 1 & 2)"** — verify scope matches (Parts 1 & 2 only, no Part 3)
5. **"Zero-breaking-change integration with existing library functionality"** — verify the guide addresses backward compatibility

**Deliverable:** Quality standards audit with e2e terminology flag.

---

### Check 6: Completeness — Omissions Check

**Question:** Does the Contribution Goal omit any significant scope areas that the Implementation Guide covers?

**Procedure:**

1. Read the Implementation Guide table of contents / section headers
2. Check whether the Contribution Goal mentions or implies each major area:
   - Service Discovery (Conformance Reader, Collections Reader extensions) — mentioned?
   - Worker Extensions (9 CSAPI message types) — mentioned?
   - OgcApiEndpoint integration code (64 lines, §5) — mentioned?
   - Helper utilities (buildResourceUrl, buildQueryString) — mentioned?
   - Test utilities / test infrastructure — mentioned?
   - Error handling patterns (§11) — mentioned?
   - Navigation patterns (16 parent-child relationships) — mentioned?
   - Anti-pattern compliance — mentioned?
3. Assess whether omissions are acceptable for a summary document or represent real scope gaps

**Deliverable:** Omissions list categorized as Acceptable (summary-level detail) or Needs Addition (missing scope area).

---

### Check 7: Overclaim Detection

**Question:** Does the Contribution Goal promise anything the Implementation Guide doesn't actually deliver?

**Procedure:**

1. Check "specification-complete" — does the guide implement every conformance class from OGC 23-001/23-002/23-003, or only selected ones?
2. Check "comprehensive TypeScript support" — is there any CSAPI functionality not covered?
3. Check "real-time observation queries" — does the guide implement real-time/streaming, or only request/response patterns?
4. Check "historical data analysis" — does the guide define analysis capabilities, or only data retrieval?
5. Check "remote system control capabilities" — does the guide implement command/control, or only URL building for command endpoints?
6. Flag any marketing-style language that overstates what the code actually does

**Deliverable:** Overclaim assessment with recommended rewording.

---

## Part II: Reverse Check (Implementation Guide → Contribution Goal)

_"Does the Implementation Guide contain framing the Contribution Goal should echo?"_

### Check 8: Value Proposition and Ecosystem Context

**Question:** Does the Implementation Guide's purpose/scope section contain framing or context that the Contribution Goal should incorporate?

**Procedure:**

1. Read Implementation Guide §3 (Purpose and Scope) for any ecosystem positioning language
2. Read Implementation Guide §4 (Architecture Overview) for integration framing
3. Check whether the guide states the contribution's value differently than the Contribution Goal
4. This is a lightweight check — the Contribution Goal is the natural home for value-proposition framing, not the Implementation Guide. Flag only if the guide contains positioning the Contribution Goal missed.

**Deliverable:** Brief reverse feedback list (expected to be minimal).

---

## Execution Strategy

**Read order:**

1. Contribution Goal in full (32 lines) — extract every claim, number, and term
2. Implementation Guide §3 (Purpose/Scope) — verify goal statement
3. Implementation Guide §5 (Service Discovery) — verify integration claims
4. Implementation Guide §6 (QueryBuilder) — verify method count, resource types, patterns
5. Implementation Guide §7 (Format Handlers) — verify format support claims
6. Implementation Guide §9 (Testing) — verify quality/coverage claims
7. Implementation Guide §11 (Error Handling) — verify error handling claims
8. Implementation Guide §13 (Estimates) — verify all numbers
9. Implementation Guide §14 (File Inventory) — verify file counts
10. Implementation Guide §16 (Standards) — verify quality standards
11. A1 report (if available) — check for any findings that changed numbers or scope

**Estimated effort:** 1-2 hours (the Contribution Goal is only 32 lines — this is primarily a verification pass against the guide, not a deep research effort)

**Output:** Alignment report with severity-rated findings (Critical/High/Medium/Low):

- **Part I findings:** Contribution Goal claims vs Implementation Guide reality
- **Part II findings:** Reverse feedback (expected to be brief)

---

## Acceptance Criteria

The cross-reference is complete when:

**Contribution Goal → Implementation Guide:**

- [ ] Goal statement verified as accurate (Check 1)
- [ ] All Core Integration claims verified (Check 2)
- [ ] All Format Support claims verified, Binary SWE status resolved (Check 3)
- [ ] All numbers current and consistent (Check 4)
- [ ] Quality standards accurate, e2e terminology resolved (Check 5)
- [ ] Omissions assessed and categorized (Check 6)
- [ ] No overclaims remain (Check 7)

**Implementation Guide → Contribution Goal:**

- [ ] Reverse feedback documented (Check 8)

**Final:**

- [ ] Report generated with severity-rated findings
- [ ] All Critical and High findings resolved
- [ ] Contribution Goal updated where warranted
