# Phase 2D: CSAPI-Specific Testing Category Deep Dive

**Review Date:** February 2026  
**Reviewer:** AI Review Agent  
**Phase:** 2D of multi-phase research document review  
**Category:** CSAPI-Specific Testing Requirements (6 documents)  
**Anti-Pattern Catalog:** [Phase 0: Lessons from Failed Attempt](phase-0-lessons-from-failed-attempt.md)

---

## 1. Phase Overview

### 1.1 Documents Reviewed

| #   | Document                                                                                            | Lines | Status      | Verdict               |
| --- | --------------------------------------------------------------------------------------------------- | ----- | ----------- | --------------------- |
| 08  | [csapi-specification-test-requirements.md](../findings/08-csapi-specification-test-requirements.md) | 1,321 | ✅ Reviewed | ❌ Critical Issues    |
| 09  | [sensorml-testing-requirements.md](../findings/09-sensorml-testing-requirements.md)                 | 1,253 | ✅ Reviewed | ❌ Critical Issues    |
| 10  | [swe-common-testing-requirements.md](../findings/10-swe-common-testing-requirements.md)             | 1,952 | ✅ Reviewed | ❌ Significant Issues |
| 11  | [geojson-csapi-testing-requirements.md](../findings/11-geojson-csapi-testing-requirements.md)       | 2,565 | ✅ Reviewed | ⚠️ Issues Found       |
| 21  | [typescript-type-testing-strategy.md](../findings/21-typescript-type-testing-strategy.md)           | 2,083 | ✅ Reviewed | ⚠️ Issues Found       |
| 22  | [conformance-capability-testing.md](../findings/22-conformance-capability-testing.md)               | 1,680 | ✅ Reviewed | ✅ Mostly Sound       |

**Total Lines Reviewed:** 10,854

### 1.2 Review Focus

These 6 documents define the CSAPI-specific testing requirements: specification extraction, format parser testing (SensorML, SWE Common, GeoJSON), TypeScript type testing, and conformance/capability testing. The review evaluates:

1. **Client vs. Server Orientation** — Do tests verify client code behavior (URL construction, parsing, error handling) or server spec-compliance?
2. **Anti-Pattern Cross-Reference** — Do documents avoid the 5 anti-patterns from Phase 0?
3. **Specification Accuracy** — Are CSAPI Parts 1 & 2, SensorML 3.0, and SWE Common 3.0 references correct?
4. **Implementation Guide Alignment** — Do requirements map to the actual component architecture (CSAPIQueryBuilder, format parsers, conformance extensions)?
5. **Realistic Scope** — Are testing efforts proportionate to the implementation scope?
6. **Format-Specific Patterns** — Are parser testing approaches appropriate for each format?

---

## 2. Review Methodology

### 2.1 Anti-Pattern Cross-Reference

Each document was checked against all 5 Phase 0 anti-patterns:

| ID  | Anti-Pattern                 | Description                                                   |
| --- | ---------------------------- | ------------------------------------------------------------- |
| AP1 | Testing Response Content     | Tests validate server responses rather than client code       |
| AP2 | Hybrid Fixture/Live          | Tests designed to run against live servers OR fixtures        |
| AP3 | OGC Requirement Traceability | Test structure mirrors spec requirements, not client code     |
| AP4 | Asserting Data Shape         | Tests check response structure without testing transformation |
| AP5 | Graceful Skipping            | Tests skip based on fixture content rather than failing       |

### 2.2 Cross-Reference Documents

| Document                                                                       | Purpose                                     |
| ------------------------------------------------------------------------------ | ------------------------------------------- |
| [Phase 0: Lessons from Failed Attempt](phase-0-lessons-from-failed-attempt.md) | Anti-pattern catalog with concrete examples |
| [Implementation Guide](../../../planning/csapi-implementation-guide.md)        | Authoritative component architecture        |
| Upstream `camptocamp/ogc-client`                                               | Reference test patterns                     |

### 2.3 Client vs. Server Test Criteria

For each test pattern, example, or recommendation, the review asked:

- Does it test **our code's behavior** (URL building, response parsing, error handling, type construction)?
- Are fixtures used as **input to our code**, not as assertions about server correctness?
- Do test assertions target **client outputs** (URLs, parsed objects, thrown errors, return types)?
- Does the test structure mirror **client code modules**, not OGC spec sections?

---

## 3. Overall Assessment

### 3.1 Verdict: Conditional Go

**The implementation can proceed, but 3 of 6 documents require fundamental reorientation before their test recommendations can be used.** The core problem is the same one identified in Phase 0: documents designed to test CSAPI specification compliance (a server concern) have been labeled as client library testing strategies.

### 3.2 Anti-Pattern Severity by Document

| Document                     | AP1         | AP2         | AP3         | AP4          | AP5    | Overall         |
| ---------------------------- | ----------- | ----------- | ----------- | ------------ | ------ | --------------- |
| 08 (CSAPI Spec Requirements) | 🔴 Severe   | ⚠️ Moderate | 🔴 Severe   | 🔴 Severe    | —      | ❌ Critical     |
| 09 (SensorML Testing)        | 🔴 High     | ⚠️ Moderate | 🔴 High     | 🔴 High      | ⚠️ Low | ❌ Critical     |
| 10 (SWE Common Testing)      | ⚠️ Moderate | ⚠️ Moderate | 🔴 Strong   | ⚠️ Moderate  | ⚠️ Low | ❌ Significant  |
| 11 (GeoJSON Testing)         | ⚠️ Moderate | —           | ⚠️ Moderate | ⚠️ Moderate  | —      | ⚠️ Issues       |
| 21 (Type Testing)            | —           | —           | —           | 🔴 Pervasive | —      | ⚠️ Issues       |
| 22 (Conformance Testing)     | —           | ⚠️ Minor    | ⚠️ Moderate | —            | —      | ✅ Mostly Sound |

### 3.3 The Fundamental Problem

**Documents 08, 09, and 10 are specification compliance test suites disguised as client library test plans.** They catalog what servers MUST do (spec SHALL/MUST statements) and label this as "client testing." The Phase 0 anti-pattern catalog predicted exactly this failure mode.

Key evidence:

- **Doc 08** contains 334 requirement IDs (SYS-001 through CMD-082, VAL-GJ-001 through VAL-SWE-072) tracing to spec sections — the document IS a traceability matrix
- **Doc 09** defines 43 validation/error IDs (VAL-SML-_, ERR-SML-_) that test whether SensorML documents conform to the spec, not what the parser outputs
- **Doc 10** is organized around SWE Common spec sections (§7.2.1–§7.7), not parser module functions

**None of these documents define what the client code's API looks like.** They exhaustively catalog spec requirements but never specify: What does `parseSensorML()` return? What TypeScript interface does the parser produce? What methods does the CSAPIQueryBuilder expose?

**Documents 11, 21, and 22 are progressively better:** Doc 11 mixes server validation with genuine parser testing; Doc 21 has correct upstream analysis but proposes shape-assertion tests; Doc 22 is the best-oriented with nearly every test verifying actual client behavior.

---

## 4. Critical Issues

### C1: Doc 08 — Entire Document is a Server Compliance Test Suite

**Severity:** CRITICAL  
**Document:** [08-csapi-specification-test-requirements.md](../findings/08-csapi-specification-test-requirements.md)  
**Anti-Patterns:** AP1 (Severe), AP3 (Severe), AP4 (Severe)

**Problem:** Doc 08's stated purpose is to "extract all 250+ testable normative requirements (SHALL/MUST statements)" with "complete requirement-to-test traceability." SHALL/MUST statements in OGC specifications are **server requirements** — they define what a conformant server must do. A client library does not "claim conformance" to API specifications; it consumes them.

Evidence:

- **334 requirement IDs** mapping 1:1 from spec sections to test cases
- **9 occurrences of "Server exposes"** as test requirements (SYS-011, DEP-011, PROC-011, etc.)
- **Section 11 "Conformance Claim Validation"** is the OGC framework for server implementations to claim conformance
- **Section 4 Error Conditions** specifies exact server error message templates
- **Zero mentions** of client method signatures, QueryBuilder API, parser functions, or URL construction
- **Section 8 Endpoint Requirements Matrix** catalogs HTTP methods and response formats per endpoint — an API surface catalog, not a client behavior spec

**What the document should be:** A reference document cataloging CSAPI spec details that inform the implementation. It is useful as background knowledge but must not be used as a test plan. Tests should be organized around `CSAPIQueryBuilder` methods, parser functions, and conformance detection logic — not around spec requirement IDs.

**Fix Required:** Reclassify from "test requirements" to "specification reference." Do not use requirement IDs (SYS-001, etc.) as test case identifiers. Test plans should be organized by client code modules (url_builder.ts methods, parser functions, conformance detection).

---

### C2: Doc 09 — SensorML Testing Validates Documents, Not Parser

**Severity:** CRITICAL  
**Document:** [09-sensorml-testing-requirements.md](../findings/09-sensorml-testing-requirements.md)  
**Anti-Patterns:** AP1 (High), AP2 (Moderate), AP3 (High), AP4 (High)

**Problem:** Doc 09 defines 43 validation/error IDs (VAL-SML-001 through VAL-SML-081, ERR-SML-001 through ERR-SML-052) that test whether SensorML JSON documents conform to the SensorML 3.0 specification. A client parser's job is to transform input into a useful TypeScript model, not to be a conformance validator.

Critical concerns:

- **No output model defined.** The document catalogs every SensorML property, validation rule, and error scenario but never defines what `parseSensorML()` returns. What TypeScript interface is the parser output? Unspecified.
- **"Parser" conflated with "validator."** Line 271: "MUST enforce: Parser rejects invalid documents." A client parser should parse what it receives and produce a useful model — not act as a specification conformance validator.
- **Test structure mirrors the SensorML spec**, not client code. Tests organized by SensorML structure types (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess) and spec sections (§7, §8.3), not by parser functions.
- **Live server dependency.** OpenSensorHub demo server URL (`https://api.georobotix.io/ogc/t18/api`) included as fixture source with planned fetch strategy.
- **Two-tier testing.** "Spec examples: MUST pass" vs "OpenSensorHub examples: SHOULD handle gracefully" — hybrid testing with different assertion standards for live vs spec data.

**What the document should do:** Define the SensorML parser's TypeScript output interface, then test that `parseSensorML(fixture) → expectedTypedObject`. Tests should be organized around the parser's functions (`parseSensorML()`, `parsePhysicalSystem()`, `parseComponents()`), not around spec validation rules.

**Fix Required:** Define the parser output model. Remove all VAL-SML/ERR-SML IDs. Remove OpenSensorHub live server fixture sourcing. Reframe tests as `parseSensorML(fixtureInput) → expectedTypedOutput`.

---

## 5. High-Priority Issues

### H1: Doc 10 — SWE Common Testing Organized by Spec, Not Parser Code

**Severity:** HIGH  
**Document:** [10-swe-common-testing-requirements.md](../findings/10-swe-common-testing-requirements.md)  
**Anti-Patterns:** AP3 (Strong), AP2 (Moderate)

**Problem:** Doc 10 is a 1,952-line specification compliance test plan organized around the SWE Common 3.0 spec's component type taxonomy (12+ component types × 3 encodings × properties × edge cases = 195 tests). It never defines what the parser's API looks like or how its functions should be tested.

Key issues:

- **Spec-driven organization.** Tests organized by SWE Common §7.2.1–§7.7, not by parser modules (e.g., `BinaryReader`, `JsonComponentParser`).
- **22 error IDs** (`ERR-SWE-JSON-001` through `ERR-SWE-BIN-010`) mimic OGC requirement ID naming.
- **98 research questions** organized by specification concepts (Q1-Q98), not by client code concerns.
- **OpenSensorHub live server fixture sourcing** — Section 9 describes fetching from `https://api.georobotix.io/ogc/t18/api` with endpoints like `/datastreams/{id}/observations?encoding=binary`.
- **Two-tier assertion strategy** — "Spec examples: MUST pass" vs "OpenSensorHub examples: SHOULD handle gracefully."

**Mitigating factor:** The binary parsing section (~50% of the document's test effort) is genuinely client-oriented. Byte-level parsing tests (endianness, IEEE 754 edge cases, buffer truncation) directly test parser implementation behavior.

**Fix Required:** Remove OpenSensorHub live server fixture strategy. Remove ERR-SWE-\* IDs. Define the parser's TypeScript output interfaces. Reorganize tests by parser functions rather than spec sections. The binary parsing content is sound and can remain.

---

### H2: Doc 09+10 — Live Server Fixture Sourcing (AP2)

**Severity:** HIGH  
**Documents:** [09-sensorml-testing-requirements.md](../findings/09-sensorml-testing-requirements.md), [10-swe-common-testing-requirements.md](../findings/10-swe-common-testing-requirements.md)

**Problem:** Both documents plan to source fixtures from OpenSensorHub's demo server (`https://api.georobotix.io/ogc/t18/api`). The strategy includes:

- Fetching sample systems/datastreams from live endpoints
- Requesting specific formats (SensorML via Accept header, SWE Common encodings)
- Creating a two-tier test system where spec-sourced fixtures have strict assertions (MUST) and live-sourced fixtures have weak assertions (SHOULD handle gracefully)

This is the AP2 (Hybrid Fixture/Live) anti-pattern. Upstream tests use no live server dependencies. Fixtures are static files versioned with the code.

**Fix Required:** Remove all live server fixture sourcing. Use only static fixture files. If spec examples are insufficient, create realistic fixtures manually based on spec schemas.

---

### H3: Doc 11 — Server Data Validation Functions (AP1/AP4)

**Severity:** HIGH  
**Document:** [11-geojson-csapi-testing-requirements.md](../findings/11-geojson-csapi-testing-requirements.md)  
**Anti-Patterns:** AP1 (Moderate), AP4 (Moderate)

**Problem:** Doc 11 contains genuinely useful client parser testing alongside significant server data validation. Sections 5-7 (~420 lines) focus on validating whether server-provided values are correct:

- `validateUID()` — tests whether server-provided URIs are valid formats
- `validateName()` — tests whether server-provided names are non-empty strings
- `validateFeatureType()` — tests whether server vocabulary values match an allowed list
- `validateLinks()` — tests whether server link structures have correct `rel`/`href`
- Section 7 Vocabulary Validation — tests whether `systemType` values match SOSA ontology terms

A client parser should **extract** these values, not **validate** them. If the server sends an invalid URI as `uniqueIdentifier`, the client should store it, not reject it. Server data validation is the server's responsibility.

**Mitigating factors:** Doc 11 also contains well-oriented client testing — `parseValidTime()` transformation tests, `parseAssociationLinks()` parsing, `identifyResourceType()` logic, and Section 16 (anti-patterns) explicitly warns against re-testing RFC 7946. This makes the document partially usable after corrections.

**Fix Required:** Remove vocabulary validation functions (`validateUID`, `validateName`, `validateFeatureType`). Reframe as property extraction tests: "does the parser extract `systemType` from the fixture?" not "is `systemType` a valid SOSA term?" Keep transformation tests (`parseValidTime`, `parseAssociationLinks`, `identifyResourceType`).

---

### H4: Doc 21 — Shape-Assertion Tests Add No Value (AP4)

**Severity:** HIGH  
**Document:** [21-typescript-type-testing-strategy.md](../findings/21-typescript-type-testing-strategy.md)  
**Anti-Pattern:** AP4 (Pervasive)

**Problem:** Doc 21's proposed `model.spec.ts` template (~250 lines) consists entirely of tests that construct objects matching TypeScript interfaces and assert the values they just set:

```typescript
it('accepts valid system object', () => {
  const system: System = { id: 'sys-001', type: 'System', ... };
  expect(system.properties.name).toBe('Temperature Sensor');
});
```

This tests nothing. The TypeScript compiler already validates that the object literal matches the `System` interface at compile time. The runtime assertion `expect(system.properties.name).toBe('Temperature Sensor')` only verifies that the value assigned on the previous line equals itself.

The document correctly identifies this limitation in Section 5 (Runtime vs Compile-Time Strategy) and correctly concludes "CSAPI needs minimal runtime validation" — but still recommends ~6 hours implementing shape-assertion tests.

**Mitigating factors:** The document's upstream analysis (Section 1) is excellent. Its tool evaluation (Section 2) correctly recommends TypeScript compiler-only approach. Type guard tests (`isSystem()`) and integration tests (QueryBuilder type safety) are genuinely useful.

**Fix Required:** Remove the `model.spec.ts` shape-assertion template. Keep compile-time type validation (types compile = types work). Keep type guard tests and integration tests. The document's analysis sections are sound — only the proposed test templates need correction.

---

## 6. Medium-Priority Issues

### M1: Doc 08 — Useful Spec Reference Buried Under Test Framework

**Severity:** MEDIUM  
**Document:** [08-csapi-specification-test-requirements.md](../findings/08-csapi-specification-test-requirements.md)

**Problem:** Doc 08 contains genuinely useful reference information — conformance class hierarchies (19 classes), endpoint catalogs (50+ endpoints), query parameter inventories, temporal format specifications, and spec ambiguity documentation — but frames it all as a "test requirements matrix." This useful content is obscured by the server-testing framing.

**Recommendation:** Reclassify as "CSAPI Specification Reference" and remove the testing framing (requirement IDs, traceability framework, conformance claim validation). The reference tables are valuable for developers implementing the CSAPIQueryBuilder; they just shouldn't be test cases.

---

### M2: Doc 10 — Binary Parsing Tests Are Sound But Buried

**Severity:** MEDIUM  
**Document:** [10-swe-common-testing-requirements.md](../findings/10-swe-common-testing-requirements.md)

**Problem:** The binary parsing section (§2.3, §3, §10.2, ~50% of the document's test effort) is genuinely client-oriented: byte-level parsing, endianness handling, IEEE 754 edge cases, buffer truncation, UTF-8 decoding. These are legitimate parser implementation concerns. However, they're mixed with spec-oriented content in the same document, making it difficult to separate what's usable from what needs reorientation.

**Recommendation:** The binary parsing content (hex dumps, expected.json, encoding.json fixture strategy, byte-level unit tests) can be used directly. The JSON/Text encoding sections need the same reorientation as the main document — tests should verify parser output, not spec conformance.

---

### M3: Doc 11 — Property Matrix Mirrors Spec Structure (AP3)

**Severity:** MEDIUM  
**Document:** [11-geojson-csapi-testing-requirements.md](../findings/11-geojson-csapi-testing-requirements.md)  
**Anti-Pattern:** AP3 (Moderate)

**Problem:** Section 4 (Resource Type Property Matrix) catalogs every property for all 5 Part 1 resource types with their spec-defined types, requiredness, and validation rules. This mirrors the specification structure, not the client parser code structure. Tests organized as "Systems Properties → Deployments Properties → Procedures Properties" follow the spec's organization, not the parser's modules.

**Mitigating factor:** For a parser, some alignment with spec structure is natural — the parser must handle each resource type. The concern is that the property matrices define 150+ validation rules that test data correctness rather than parsing correctness.

**Recommendation:** Keep the property matrices as reference material but don't implement validation tests for every property rule. Tests should verify "does the parser extract all properties from a fixture into the typed output?" not "is each property value individually valid?"

---

### M4: Doc 22 — Live Server Profiles as Context (AP2 Minor)

**Severity:** MEDIUM  
**Document:** [22-conformance-capability-testing.md](../findings/22-conformance-capability-testing.md)

**Problem:** Section 2 documents real server profiles with live URLs (`http://45.55.99.236:8080/sensorhub/api`, `https://csa.demo.52north.org/`), pagination limits, backend databases, and encoding preferences. While the actual test implementations correctly use mocked fetch (not live servers), the detailed server documentation creates potential for future drift toward live-server testing.

**Mitigating factor:** All test code in the document uses `mockFetchForProfile()` with fixtures. The live server information is contextual, not prescriptive for tests.

**Recommendation:** Add a clear note that server profiles are reference context only, not test targets. Tests must always use mocked fetch with static fixtures.

---

## 7. Low-Priority Issues

### L1: Doc 21 — 6-Hour Estimate for Low-Value Tests

**Severity:** LOW  
**Document:** [21-typescript-type-testing-strategy.md](../findings/21-typescript-type-testing-strategy.md)

**Problem:** The implementation estimate allocates ~6 hours for model type tests that consist primarily of shape-assertion tests (AP4). The document's own analysis correctly identifies these as low-value, yet budgets significant time.

**Recommendation:** Reduce estimate to ~1 hour for compile-time validation (types compile = types work) plus type guard tests. Save the remaining 5 hours for actual behavior testing.

---

### L2: Doc 11 — Over-Specified Test Organization

**Severity:** LOW  
**Document:** [11-geojson-csapi-testing-requirements.md](../findings/11-geojson-csapi-testing-requirements.md)

**Problem:** Section 14 specifies a highly granular test file structure with naming conventions, organization rules, and directory layouts before any CSAPI parsing code exists. This is premature — test organization should emerge from the implementation, following upstream conventions.

**Recommendation:** Let test organization follow upstream patterns organically. The EDR module has 2 test files; the CSAPI parser tests should similarly start simple.

---

### L3: Doc 10 — Research Questions Count (98) Disproportionate

**Severity:** LOW  
**Document:** [10-swe-common-testing-requirements.md](../findings/10-swe-common-testing-requirements.md)

**Problem:** The document lists 98 research questions, all organized by specification concepts. This is disproportionate to the implementation scope (a parser with 3 encoding modes) and reinforces the spec-compliance orientation.

**Recommendation:** No fix needed — this is background research, not prescriptive. Note that the high question count reflects the spec-oriented research methodology, not the testing scope.

---

## 8. Positive Findings

### P1: Doc 22 — Excellent Client-Testing Orientation

Doc 22 (Conformance and Capability Testing) is the strongest document in this category. Nearly every test verifies actual client behavior:

- `CSAPIClient` conformance detection: `hasConnectedSystems`, `detectCapabilities()`
- Method availability guarding: CRUD methods throw `ConformanceError` when server doesn't support them
- Graceful degradation: subsystem/datastream accessors return `null` when unsupported
- Progressive complexity: 8 scenarios from minimal server to missing/malformed conformance
- Clean mock strategy: `mockFetchForProfile()` with fixture-based approach, no live server dependencies

This document demonstrates what the other documents should look like — tests organized around client code behavior, not spec requirements.

### P2: Doc 11 — Good Reuse Strategy

Doc 11 explicitly avoids duplicating RFC 7946/geometry tests already covered by the upstream `parseFeaturePropsGeojson` parser. It defines clear "DO test / DON'T test" boundaries and includes a Section 16 (Anti-Patterns) warning against re-testing framework behavior. The `parseValidTime()`, `parseAssociationLinks()`, and `identifyResourceType()` tests are genuinely client-focused.

### P3: Doc 21 — Correct Upstream Analysis and Tool Evaluation

Doc 21 accurately documents upstream type testing patterns (EDR `ZParameter`, `DateTimeParameter` with `zParameterToString` behavioral tests) and correctly recommends against specialized type testing tools (tsd, dtslint, expect-type). The recommendation to use TypeScript compiler-only approach aligns with upstream practice. The analysis is sound — only the proposed test templates misapply it.

### P4: Doc 10 — Binary Parsing Tests Are Genuinely Client-Oriented

The binary parsing section of Doc 10 is well-designed for client testing. Byte-level test fixtures (hex dumps), endianness handling, IEEE 754 edge cases (NaN, ±Infinity, subnormals), buffer truncation errors, and the 4-file fixture format (.bin + .hex + expected.json + encoding.json) are legitimate parser implementation tests. This represents ~50% of the document and is directly usable.

### P5: Doc 08 — Spec Ambiguity Documentation

Doc 08 Section 13 (Gaps and Ambiguities) documents 7 specification ambiguities and 4 OpenAPI-vs-specification conflicts with pragmatic resolution strategies. The principle "Specification text takes precedence over OpenAPI" is useful guidance. The temporal format catalog (ISO 8601 variations) is also directly useful for parameter encoding tests.

### P6: Doc 09 — Recursive Structure and Error Handling

Doc 09's recursive structure testing (nesting levels 0-4+, circular reference detection, missing component references) and error handling design (22 ERR-SML scenarios with severity levels) address legitimate parser concerns. If reoriented toward client behavior (what the parser returns/throws), this content is valuable.

---

## 9. Cross-Document Consistency Analysis

### 9.1 Server-Testing Orientation Gradient

The 6 documents form a clear gradient from server-oriented to client-oriented:

```
Most Server-Oriented                                           Most Client-Oriented
        ↓                                                              ↓
   Doc 08 ────── Doc 09 ────── Doc 10 ────── Doc 11 ────── Doc 21 ────── Doc 22
   (100% spec    (90% spec     (~50% spec    (mixed,       (AP4 but      (client
    traceability  validation,   + 50% binary  good parser   correct       behavior
    matrix)       no output     parsing)      tests in      analysis)     testing)
                  model)                      parts)
```

### 9.2 Common Pattern: No Client API Definition

Documents 08, 09, and 10 share a critical blind spot — they exhaustively catalog what the specification defines but never define what the client code's API looks like. None specify:

- What `CSAPIQueryBuilder` methods exist (documented in Implementation Guide)
- What `parseSensorML()` returns (no TypeScript interface defined)
- What `parseSWECommon()` returns (no TypeScript interface defined)
- How the client handles unsupported conformance classes (only Doc 22 addresses this)

The Implementation Guide defines the component architecture (CSAPIQueryBuilder, SensorML parser, SWE Common parser, conformance extensions, GeoJSON handler), but Docs 08-10 don't reference this architecture when designing tests.

### 9.3 Implementation Guide Alignment

| Implementation Guide Component       | Relevant Doc(s) | Alignment                                                                  |
| ------------------------------------ | --------------- | -------------------------------------------------------------------------- |
| CSAPIQueryBuilder (URL construction) | 08              | ❌ Doc 08 catalogs endpoints but never mentions QueryBuilder               |
| SensorML 3.0 Parser                  | 09              | ⚠️ Doc 09 covers input format but not output interface                     |
| SWE Common 3.0 Parser                | 10              | ⚠️ Doc 10 covers encodings but not output interface; binary section usable |
| Conformance Reader (extension)       | 22              | ✅ Doc 22 directly tests conformance detection behavior                    |
| GeoJSON Handler (extension)          | 11              | ⚠️ Mixed — transformation tests good, validation tests server-oriented     |
| model.ts Type Definitions            | 21              | ⚠️ Analysis sound but proposed tests are shape-assertions                  |

### 9.4 Requirement ID Inflation

| Document  | Unique Requirement IDs | Type                                                               |
| --------- | ---------------------- | ------------------------------------------------------------------ |
| Doc 08    | 334                    | SYS-001, DEP-001, ..., VAL-GJ-001, ..., VAL-SWE-072                |
| Doc 09    | 43                     | VAL-SML-001..021, ERR-SML-001..022                                 |
| Doc 10    | 22                     | ERR-SWE-JSON-001..006, ERR-SWE-TEXT-001..006, ERR-SWE-BIN-001..010 |
| Doc 11    | 0                      | Uses priority labels (P0-P3)                                       |
| Doc 21    | 0                      | Uses pattern names                                                 |
| Doc 22    | 0                      | Uses scenario numbers (S1-S8)                                      |
| **Total** | **399**                | —                                                                  |

There are 399 requirement IDs across Docs 08-10, every one tracing to a spec section. Docs 11, 21, 22 (the better-oriented documents) use zero requirement IDs. The correlation is clear: the more requirement IDs, the more server-oriented the document.

---

## 10. Recommendations

### 10.1 Immediate Actions (Before Implementation)

1. **CRITICAL: Reclassify Doc 08** from "test requirements" to "specification reference." Do not use requirement IDs as test identifiers. The document is a useful reference catalog but must not drive test design.

2. **CRITICAL: Define parser output interfaces** for SensorML and SWE Common parsers before writing tests. Docs 09 and 10 catalog input formats exhaustively but never define output types. Tests should be `parseSensorML(fixture) → expectedTypedObject`.

3. **HIGH: Remove live server fixture sourcing** from Docs 09 and 10. Remove OpenSensorHub URLs, fetch strategies, and two-tier assertion logic. Use static fixtures only.

4. **HIGH: Remove server data validation** from Doc 11. Functions like `validateUID()`, `validateName()`, `validateFeatureType()` test server correctness, not client behavior. Keep transformation tests.

5. **HIGH: Remove shape-assertion test templates** from Doc 21. The `model.spec.ts` template adds no value beyond what the TypeScript compiler provides. Keep type guard and integration tests.

### 10.2 Documents Usable As-Is

- **Doc 22** — Sound client-testing orientation. Minor note needed about server profile context.

### 10.3 Documents Usable After Targeted Corrections

- **Doc 11** — Remove validation functions, keep transformation tests. Good foundation.
- **Doc 21** — Remove shape-assertion templates, keep analysis and type guard tests.
- **Doc 10** (binary section only) — Binary parsing tests are directly usable.

### 10.4 Documents Requiring Fundamental Reorientation

- **Doc 08** — Reclassify entirely. Useful as reference, not as test plan.
- **Doc 09** — Define output model, remove validation IDs, remove live server sourcing.
- **Doc 10** (non-binary sections) — Define output model, remove spec-organized structure.

### 10.5 Next Phase

Proceed to **Phase 2E** covering remaining document categories, or begin targeted corrections on the critical and high-priority issues identified here.

---

## 11. Issue Tracker

| ID  | Severity | Document(s) | Issue                                                                                     | Status      |
| --- | -------- | ----------- | ----------------------------------------------------------------------------------------- | ----------- |
| C1  | CRITICAL | 08          | Entire document is server compliance test suite with 334 requirement IDs                  | ✅ Resolved |
| C2  | CRITICAL | 09          | SensorML testing validates documents, not parser — no output model defined                | ✅ Resolved |
| H1  | HIGH     | 10          | SWE Common testing organized by spec sections with 22 error IDs, not parser code          | ✅ Resolved |
| H2  | HIGH     | 09, 10      | Live server fixture sourcing from OpenSensorHub (AP2)                                     | ✅ Resolved |
| H3  | HIGH     | 11          | Server data validation functions (validateUID, validateName, etc.)                        | ✅ Resolved |
| H4  | HIGH     | 21          | Shape-assertion model.spec.ts template tests nothing TypeScript compiler doesn't validate | ✅ Resolved |
| M1  | MEDIUM   | 08          | Useful spec reference buried under test framework framing                                 | ✅ Resolved |
| M2  | MEDIUM   | 10          | Sound binary parsing tests buried alongside spec-oriented content                         | ✅ Resolved |
| M3  | MEDIUM   | 11          | Property matrix mirrors spec structure (AP3)                                              | ✅ Resolved |
| M4  | MEDIUM   | 22          | Live server profiles included as reference context                                        | ✅ Resolved |
| L1  | LOW      | 21          | 6-hour estimate for low-value shape-assertion tests                                       | ✅ Resolved |
| L2  | LOW      | 11          | Over-specified test organization before code exists                                       | ✅ Resolved |
| L3  | LOW      | 10          | 98 research questions disproportionate to implementation scope                            | ✅ Resolved |

**Summary:** 2 Critical, 4 High, 4 Medium, 3 Low — **13 total issues**
