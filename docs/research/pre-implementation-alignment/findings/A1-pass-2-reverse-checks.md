# A1 Pass 2: Reverse Checks (Test Research → Implementation Guide)

**Date:** February 13, 2026  
**Phase:** Pre-Implementation Alignment  
**Step:** A1, Pass 2 of 3  
**Status:** Complete

---

## Summary

Pass 2 executes the four reverse checks from the A1 research plan, asking: _"Has the test research discovered anything the implementation guide should incorporate?"_

**Overall Assessment:** The test research corpus (Phases 0-4, 115 issues resolved) produced **significant scope refinements, terminology corrections, pattern fixes, and specification details** that the implementation guide has **not yet absorbed**. The guide was last updated Feb 5, 2026; the review phases completed Feb 12-13, 2026. This 7-day gap means nearly all review-phase decisions are NOT reflected in the guide.

**Quick Stats:**

- Scope decisions checked: 9 primary + 12 additional
- Propagated to guide: 2 of 21 (10%)
- Not propagated: 19 of 21 (90%)
- Client responsibilities in guide: 0 of 5 explicitly stated
- Architectural pattern issues found: 4 of 6 checked
- Specification enrichment opportunities: 8 identified

---

## Check 5: Scope Decisions Not Yet Reflected

**Question:** Did the test research make scope decisions that the implementation guide should formally incorporate?

### Scope Decision Propagation Status

| #   | Scope Decision                                       | Source                   | Guide Location Expected | Status                                                                                                                                                                                                                            | Severity                 |
| --- | ---------------------------------------------------- | ------------------------ | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 1   | Performance testing OUT OF SCOPE                     | Phase 2F H2, Phase 3 H1  | §9 Testing, §16         | **Not reflected** — §9 mentions "Performance profiling for heavy operations" as a quality standard in §16 without noting it's excluded from test scope                                                                            | **Medium**               |
| 2   | Real-world server testing rejected (AP2)             | Phase 2E C1 (Doc 32)     | §9 or §16               | **Not reflected** — no mention of test scope exclusions                                                                                                                                                                           | **Medium**               |
| 3   | `PARSE_SWE_BINARY` worker offloading deferred        | Phase 2F H3, Phase 2E L1 | §8 Worker               | **Correctly not reflected** — §7 SWE Common correctly treats binary parsing as in-scope (Doc 10, Phase 2D P4: "sound and directly usable"). Only the worker message type (Doc 16) is deferred to Phase 4. Guide is correct as-is. | ~~Medium~~ **Withdrawn** |
| 4   | Worker extensions = Phase 4 only                     | Phase 2F H1              | §8 Worker               | **Not reflected** — §8 describes worker extensions without phasing constraint                                                                                                                                                     | **Low**                  |
| 5   | `_metadata` fixture pattern = hallucinated           | Phase 2A C1, Phase 4 H4  | §9 fixture guidance     | **Not applicable** — guide does not reference `_metadata` pattern                                                                                                                                                                 | ✅ N/A                   |
| 6   | Enterprise review process simplified                 | Phase 2C H2              | §16                     | **Not reflected** — §16 says "Write tests as you implement" but doesn't reference the 31-checkpoint cadence or max 2-3 hr rule                                                                                                    | **Low**                  |
| 7   | Incremental testing cadence (max 2-3 hrs)            | Phase 2F P2, ROADMAP v3  | §16                     | **Not reflected** — §16 says only "Write tests as you implement (not deferred to later)" without quantifying the cadence                                                                                                          | **Low**                  |
| 8   | `@specification` traceability system dismantled      | Phase 2C C2              | §16                     | **Not reflected** — §16 doesn't reference this at all (acceptable since the system was dismantled before the guide needed it)                                                                                                     | ✅ N/A                   |
| 9   | Doc 08 reclassified from test plan to spec reference | Phase 2D C1              | §4 Research Foundation  | **Not reflected** — §4 Research Foundation doesn't mention Doc 08's reclassification                                                                                                                                              | **Low**                  |

### Additional Scope Decisions Not in Original Checklist

| #   | Scope Decision                                                             | Source      | Status                                                                                                                          | Severity     |
| --- | -------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| 10  | Fixture count: ~280 → ~80-100                                              | Phase 2A H1 | **Not reflected** — §9 doesn't specify fixture counts                                                                           | **Low**      |
| 11  | Fixture validation pipeline rejected                                       | Phase 2A H2 | **Not applicable** — guide doesn't propose fixture validation                                                                   | ✅ N/A       |
| 12  | Aggregate scope creep flagged (~683 tests → ~80-120 initial)               | Phase 2E S1 | **Not reflected** — guide estimates ~4,500-6,000 test lines without noting the aggregate creep risk                             | **Low**      |
| 13  | `OgcApiEndpoint.fromUrl()` doesn't exist — use `new OgcApiEndpoint()`      | Phase 1 M3  | **Partially reflected** — guide uses `OgcApiEndpoint.fromUrl()` in §11 Developer Experience (line 3089)                         | **Medium**   |
| 14  | `ParameterValidationError` rejected — use native `Error` / `EndpointError` | Phase 2E M1 | **Not reflected** — guide doesn't mention this restriction, though it doesn't propose new error classes either                  | **Low**      |
| 15  | Shape-assertion model.spec.ts template rejected                            | Phase 2D H4 | **Not reflected** — guide's §9 describes type tests without noting the compilation-only approach                                | **Low**      |
| 16  | Test file location: colocated `.spec.ts`, not `__tests__/`                 | Phase 1 H2  | **Partially reflected** — guide shows `model.spec.ts` and `url_builder.spec.ts` colocated in file structure diagram (line 1892) | ✅ Reflected |
| 17  | Space encoding: `%20` not `+`                                              | Phase 1 M4  | **Not reflected** — guide doesn't specify URL space encoding convention                                                         | **Low**      |
| 18  | Path corrected: `src/csapi-querybuilder/` → `src/ogc-api/csapi/`           | Phase 2B M2 | **Reflected** — guide uses `src/ogc-api/csapi/` throughout                                                                      | ✅ Reflected |
| 19  | Coverage targets: >80% minimum, not 90/85/88%                              | Phase 3 H3  | **Reflected** — guide says ">80% test coverage (statement and branch)" in §16                                                   | ✅ Reflected |
| 20  | SensorThings terminology corrected (ObservedProperties → Properties, etc.) | Phase 1 H1  | **See Check 7**                                                                                                                 | —            |
| 21  | Conformance URI namespace corrected (hyphenated → no hyphen)               | Phase 1 M1  | **Not reflected** — guide doesn't list conformance URIs explicitly                                                              | **Low**      |

### Check 5 Findings Summary

| Severity                | Count | Key Items                                                                                                                                                                             |
| ----------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Medium**              | 3     | Performance testing exclusion not noted; real-world testing exclusion not noted; `OgcApiEndpoint.fromUrl()` still used in examples (binary SWE deferral withdrawn — guide is correct) |
| **Low**                 | 9     | Worker phasing, review cadence, fixture counts, Doc 08 reclassification, space encoding, error class restriction, template rejection, aggregate scope, conformance URIs               |
| **N/A (already clear)** | 4     | `_metadata`, fixture validation, traceability system, path correction                                                                                                                 |
| **Reflected**           | 4     | Colocated tests, path `src/ogc-api/csapi/`, coverage >80%, file structure                                                                                                             |

---

## Check 6: Client Responsibility Model

**Question:** Does the implementation guide clearly articulate the 5 client responsibilities, and do its examples consistently demonstrate them?

### 6a. Explicit Statement of Responsibilities

The 5 client responsibilities identified in Phase 0:

| #   | Responsibility | Definition                                                 | In Guide §3/§4?           |
| --- | -------------- | ---------------------------------------------------------- | ------------------------- |
| 1   | **Parse**      | Service documents (capabilities, conformance, collections) | **Not explicitly stated** |
| 2   | **Construct**  | URLs with correct parameters                               | **Not explicitly stated** |
| 3   | **Transform**  | Responses into typed TypeScript objects                    | **Not explicitly stated** |
| 4   | **Handle**     | Errors, edge cases, and format negotiation                 | **Not explicitly stated** |
| 5   | **Validate**   | Inputs before making requests                              | **Not explicitly stated** |

**Assessment:** The implementation guide's §3 (Purpose and Scope) and §4 (Architecture Overview) describe _what_ is being built but **never explicitly states these 5 client responsibilities**. The guide implicitly demonstrates all 5 through its components (Conformance Reader parses, QueryBuilder constructs, Format Handlers transform, Error Handling handles, Resource Validation validates), but this foundational framing — "the client does 5 things, everything else is the server's job" — is absent.

**Severity: Medium.** The absence of an explicit client responsibility model means a developer reading only the implementation guide wouldn't have the same "server behavior ≠ client behavior" lens that the test research established. This is the root-cause framing that led to the 5 anti-patterns (AP1-AP5). Having it in the guide would prevent anti-pattern confusion during implementation.

### 6b. Code Example Audit

Scanning implementation guide code examples in §6, §7, §11, §12 for violations — examples that demonstrate server behavior testing rather than client behavior:

| Section                | Example                                                  | Compliant?       | Notes                                                                                                                                                                                                             |
| ---------------------- | -------------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| §6 QueryBuilder        | `buildResourceUrl()`, `buildQueryString()`               | ✅ Yes           | All examples construct URLs — pure client behavior                                                                                                                                                                |
| §6 Resource Validation | `throw new Error("Collection does not support...")`      | ✅ Yes           | Client-side input validation                                                                                                                                                                                      |
| §6 Navigation Patterns | fluent method chaining (system→datastream→observations)  | ✅ Yes           | URL construction chains                                                                                                                                                                                           |
| §7 GeoJSON Handler     | `parseSensorML30(smlJson)`                               | ✅ Yes           | Parsing (client responsibility #1 and #3)                                                                                                                                                                         |
| §7 SWE Common          | JSON/Text/Binary encoding examples                       | ✅ Yes           | Parsing (client responsibility #3)                                                                                                                                                                                |
| §7 Validator           | Part 1/Part 2 validation rules                           | ⚠️ **Ambiguous** | Some rules validate _server response correctness_ (e.g., "uniqueIdentifier must be valid URI", "systemType must be from SOSA vocabulary"). Client should extract these values, not validate vocabulary membership |
| §11 API Surface        | `endpoint.csapi('sensors')`, `builder.getSystems()`      | ✅ Yes           | URL construction + factory method                                                                                                                                                                                 |
| §11 Type-Safe Usage    | `systems.features.forEach(...)`                          | ✅ Yes           | Response transformation                                                                                                                                                                                           |
| §11 Error Handling     | Error scenarios                                          | ✅ Yes           | Client-side error handling                                                                                                                                                                                        |
| §12 Scenarios          | Temperature monitoring, UAV control, historical analysis | ✅ Yes           | All demonstrate client workflows                                                                                                                                                                                  |

**One area of concern:** §7 Validator section describes extensive validation rules that blur the line between client-side validation and server data correctness testing. The rules for validating SOSA vocabulary membership, URI format correctness, temporal period validity, and spatial coordinate ranges could be interpreted as AP3 (testing server spec compliance). The test research Phase 2D H3 flagged exactly this concern for Doc 11's validation functions.

**Severity: Low.** The §7 Validator section is about _what the validator component will do_ (implementation specification), not about test design. The risk is that someone might write tests that assert server data values match these rules (AP1/AP4), but the guide itself doesn't propose that.

### Check 6 Findings Summary

| Severity   | Count | Details                                                                                 |
| ---------- | ----- | --------------------------------------------------------------------------------------- |
| **Medium** | 1     | Client responsibility model (5 responsibilities) not explicitly stated in §3/§4         |
| **Low**    | 1     | §7 Validator rules could be misinterpreted as test criteria for server data correctness |

---

## Check 7: Architectural Patterns Refined by Test Research

**Question:** Did the test research refine or correct any architectural patterns that the implementation guide should update?

### Architectural Consistency Checklist

| #   | Pattern                                     | Expected (per test research)                                                                                                            | Actual (in guide)                                                                                                                                                                                                                                                                                                                                                                                                                      | Status                                                                                                               | Severity |
| --- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | -------- |
| a   | `parseAndValidateUrl()` signature           | Uses `hostname` (Phase 4 H5, Doc 34 authoritative)                                                                                      | **Not present** — guide does not reference `parseAndValidateUrl()` or any test utility                                                                                                                                                                                                                                                                                                                                                 | ✅ N/A — this is a test utility, not an implementation pattern. Guide correctly doesn't include test-utility details | None     |
| b   | Fixture directory structure                 | `fixtures/csapi/sample-server/` with URL-path-mirroring (Phase 2A H3, Phase 4 H3)                                                       | **Not specified** — §9 Testing section (line 2987) refers to "CSAPI test fixtures" generically without specifying a directory path                                                                                                                                                                                                                                                                                                     | **Medium** — guide should specify the fixture directory to avoid re-discovering this decision                        |
| c   | Test file count                             | 22 files (Doc 19 authoritative, Phase 2B H2 correction)                                                                                 | **17 files** — §13 Code Volume Summary explicitly states "Tests: 17 files, ~4,500-6,000 lines" (line 4000)                                                                                                                                                                                                                                                                                                                             | **Medium** — discrepancy identified in Pass 1 Check 3. Guide has original pre-research count                         |
| d   | Test utility structure from Doc 34          | 50 utility functions across 6 categories in 3 files (test-utils.ts, test-helpers.ts, test-fixtures.ts)                                  | **Not referenced** — §9 (line 2987) mentions "test utilities specific to CSAPI validation" without details                                                                                                                                                                                                                                                                                                                             | **Low** — test utilities are implementation details, but the 3-file structure from Doc 34 could be noted             |
| e   | SensorThings API terminology                | All corrected to CSAPI names per Phase 1 H1 (ObservedProperties → Properties, Sensors → Systems, FeaturesOfInterest → SamplingFeatures) | **Mostly clean** — guide uses correct CSAPI names throughout. Two instances of `FeaturesOfInterest` found: line 1459 (DataStreams property listing: `featuresOfInterest`) and line 2731 (SensorML elements: `FeaturesOfInterest`). **These are CORRECT** — they refer to SensorML 3.0 element names and CSAPI property names, not resource type names. The Phase 1 H1 fix was about resource type naming, not property/element naming. | ✅ Clean                                                                                                             |
| f   | QueryBuilder-not-standalone-clients warning | Explicitly documented in Phase 0 as architectural lesson from failed attempt                                                            | **Present** — guide extensively documents single-class architecture throughout §4, §6. Line 245: "One CSAPIQueryBuilder class with methods for all 9 resource types (not 9 separate classes)." Line 485: "methods within this single CSAPIQueryBuilder class, not separate components." §6 Architecture Validation section provides 500+ lines of justification.                                                                       | ✅ Present                                                                                                           |

### Additional Pattern Checks

| #   | Pattern                              | Test Research                                           | Guide                                                                                                          | Status                                                       | Severity |
| --- | ------------------------------------ | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------- |
| g   | `OgcApiEndpoint.fromUrl()` construct | Doesn't exist — use `new OgcApiEndpoint()` (Phase 1 M3) | **Used in §11** — line 3089: `const endpoint = await OgcApiEndpoint.fromUrl('https://api.example.com/csapi');` | **Medium** — incorrect API usage in developer-facing example |
| h   | Mocking convention                   | `globalThis.fetch` (Phase 0 AP2)                        | **Not specified** — §9, §16 don't mention mocking approach                                                     | **Low** — testing implementation detail                      |
| i   | File naming convention               | `*.spec.ts` (Doc 19)                                    | **Reflected** — guide uses `model.spec.ts`, `url_builder.spec.ts` in file structure                            | ✅ Reflected                                                 |
| j   | Space encoding                       | `%20` not `+` (Phase 1 M4)                              | **Not specified** — guide doesn't mention URL space encoding                                                   | **Low**                                                      |

### Check 7 Findings Summary

| Severity   | Count | Details                                                                                                                          |
| ---------- | ----- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Medium** | 3     | Fixture directory not specified; test file count still 17 (should be 22); `fromUrl()` method used in §11 example (doesn't exist) |
| **Low**    | 3     | Test utility structure not referenced; mocking convention not specified; space encoding not specified                            |
| **Clean**  | 3     | SensorThings terminology clean; QueryBuilder-not-standalone-clients present; file naming correct                                 |
| **N/A**    | 1     | `parseAndValidateUrl` is test utility, correctly absent from guide                                                               |

---

## Check 8: Specification Details Discovered During Test Research

**Question:** Did the test research uncover specification details that would improve the implementation guide's accuracy or completeness?

### Enrichment Opportunities

| #   | Detail                                                                                                                                                                                                                                                                                   | Source         | Guide Section                          | Guide Current State                                                                                                                                                                                                                                                                                        | Enrichment Value                                                                                                                                                                          | Severity |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| E1  | **16 parent-child relationship patterns with 3 relationship types** (Hierarchical: 2, Compositional: 12, Associative: 2)                                                                                                                                                                 | Doc 26         | §6 Navigation Patterns                 | Guide mentions "16 navigation patterns" (line 936) and lists all parent→child endpoints in prose. The relationship type classification (Hierarchical/Compositional/Associative) is NOT present.                                                                                                            | **Medium** — the 3-type taxonomy helps developers understand when `recursive` applies (Hierarchical only) vs simple nesting (Compositional) vs bidirectional queries (Associative)        |
| E2  | **Canonical equivalence**: `GET /observations/obs-456` ≡ `GET /datastreams/ds-123/observations/obs-456` — same resource accessible via canonical or nested endpoint                                                                                                                      | Doc 26         | §6 Navigation                          | **Not stated** — guide describes both canonical and nested endpoints but doesn't guarantee equivalence                                                                                                                                                                                                     | **Low** — useful for testing (verify same response from either URL) but not critical for URL construction                                                                                 |
| E3  | **5 temporal parameters with applicability matrix**: `datetime` (Systems/Deployments/DataStreams/ControlStreams), `phenomenonTime` (DataStreams/Observations), `resultTime` (DataStreams/Observations), `executionTime` (ControlStreams/Commands), `issueTime` (ControlStreams/Commands) | Doc 28         | §6 Query Parameters Reference          | **Partially present** — query parameter section lists all 5 temporal parameters and their brief descriptions. **Missing:** which parameters apply to which resource types (the applicability matrix). Also missing: `latest` special value for `resultTime`                                                | **Medium** — applicability matrix saves developers from trial-and-error. The `latest` special value is a key user-facing feature                                                          |
| E4  | **ISO 8601 format catalog**: 7 instant formats (Date only through Compact), 6 interval formats (Closed through Duration+end), Duration format syntax                                                                                                                                     | Doc 28         | §6 Query Parameters                    | **Not detailed** — guide says "ISO 8601 intervals" and shows one example (`phenomenonTime: '2024-01-01/..'`) but doesn't catalog accepted formats                                                                                                                                                          | **Low** — ISO 8601 is a well-known standard; developers can look it up. But listing supported patterns (especially open intervals `../..` and duration syntax `P1DT12H`) would be helpful |
| E5  | **Bbox validation rules**: minLon ≤ maxLon (antimeridian crossing = 400 error), latitude -90 to 90, longitude -180 to 180, exactly 4 or 6 values, 3D elevation support                                                                                                                   | Doc 29         | §6 Query Parameters, §6 helper methods | **Partially present** — guide shows `encodeBBox()` with `validateBBox()` (line 782-799) using `minLon, minLat, maxLon, maxLat`. **Missing:** explicit validation rules (value ranges, value count, antimeridian behavior), 3D bbox support (6 values), CRS = WGS84 only, null geometry exclusion semantics | **Medium** — validation rules should be specified in the guide to ensure consistent implementation                                                                                        |
| E6  | **Command status lifecycle**: `PENDING` → `ACCEPTED` → `EXECUTING` → `COMPLETED` \| `FAILED` \| `CANCELED`                                                                                                                                                                               | Doc 08, Doc 31 | §6 Commands                            | **Not present as a formal state machine** — guide describes status tracking endpoints (`getCommandStatus()`) but doesn't list the state values or transitions                                                                                                                                              | **Medium** — the state machine is essential for implementing status polling and transition handling                                                                                       |
| E7  | **`obsFormat` and `cmdFormat` required parameters** on schema endpoints: `/datastreams/{id}/schema?obsFormat=...` and `/controlstreams/{id}/schema?cmdFormat=...`                                                                                                                        | Doc 08         | §6 DataStreams, ControlStreams         | **Not specified** — guide describes schema endpoints but doesn't mention the required format parameter                                                                                                                                                                                                     | **Medium** — missing required parameter would cause schema requests to fail                                                                                                               |
| E8  | **Properties resource is non-feature**: Uses `resources`/`resource` terminology, `itemType` not `featureType` in collections. Same for Part 2 resources (DataStreams, Observations, ControlStreams, Commands)                                                                            | Doc 08         | §6 Properties, §6 Part 2 methods       | **Not distinguished** — guide treats all resources uniformly. This distinction matters for collection parsing (Properties/Part 2 responses are NOT GeoJSON FeatureCollections)                                                                                                                             | **Low** — impacts format handler implementation but the handler specs in §7 address this                                                                                                  |

### Specification Detail Summary

Of the 8 enrichment opportunities:

- **5 Medium severity** — would meaningfully improve the guide's precision and developer experience
- **3 Low severity** — useful but not essential; can be discovered during implementation

The most impactful enrichments are:

1. **E3 (Temporal applicability matrix + `latest` value)** — prevents parameter misuse
2. **E5 (Bbox validation rules)** — prevents validation surprises
3. **E6 (Command state machine)** — essential for status tracking
4. **E7 (`obsFormat`/`cmdFormat` required parameters)** — prevents runtime failures

### Check 8 Findings Summary

| Severity   | Count | Details                                                                                                                                                                      |
| ---------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Medium** | 5     | Relationship type taxonomy (E1); temporal applicability matrix + `latest` (E3); bbox validation rules (E5); command state machine (E6); schema endpoint required params (E7) |
| **Low**    | 3     | Canonical equivalence (E2); ISO 8601 format catalog (E4); Properties non-feature distinction (E8)                                                                            |

---

## Pass 2 Consolidated Findings

### By Severity

| Severity      | Count | Source Checks                                      |
| ------------- | ----- | -------------------------------------------------- |
| **Critical**  | 0     | —                                                  |
| **High**      | 0     | —                                                  |
| **Medium**    | 13    | Check 5 (4), Check 6 (1), Check 7 (3), Check 8 (5) |
| **Low**       | 16    | Check 5 (9), Check 6 (1), Check 7 (3), Check 8 (3) |
| **N/A/Clean** | 8     | Check 5 (4), Check 7 (1+3 clean)                   |

### Top 10 Actionable Items (Medium Severity, Prioritized)

| Rank  | Item                                                | Check    | Action                                                                                                                                                              |
| ----- | --------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | **`OgcApiEndpoint.fromUrl()` in §11 example**       | C7g      | Replace with `new OgcApiEndpoint()` — incorrect API that will cause runtime errors if copied                                                                        |
| 2     | **Test file count: 17 → 22**                        | C7c      | Update §13 Code Volume Summary to 22 files per Doc 19                                                                                                               |
| ~~3~~ | ~~Binary SWE deferral not noted~~                   | ~~C5.3~~ | **WITHDRAWN** — Guide correctly treats binary parsing as in-scope. Only `PARSE_SWE_BINARY` worker offloading is deferred (Doc 16, Phase 4). No guide change needed. |
| 4     | **Command state machine not documented**            | C8.E6    | Add state value list and transition diagram to §6 Commands                                                                                                          |
| 5     | **`obsFormat`/`cmdFormat` required params missing** | C8.E7    | Add to §6 DataStreams and ControlStreams schema method docs                                                                                                         |
| 6     | **Client responsibility model absent**              | C6.1     | Add 5-responsibility statement to §3 Purpose and Scope                                                                                                              |
| 7     | **Temporal applicability matrix missing**           | C8.E3    | Add which-params-apply-to-which-resources table to §6 Query Parameters                                                                                              |
| 8     | **Bbox validation rules incomplete**                | C8.E5    | Add validation constraints to §6 helper methods section                                                                                                             |
| 9     | **Performance testing exclusion not stated**        | C5.1     | Add scope exclusion note to §9 Testing                                                                                                                              |
| 10    | **Fixture directory not specified**                 | C7b      | Add `fixtures/csapi/sample-server/` to §9 Testing                                                                                                                   |

### Relationship to Pass 1 Findings

Several Pass 2 findings reinforce or extend Pass 1 findings:

- Pass 1 Check 3 D1 (file count 17 vs 22) → confirmed and elevated in Check 7c
- Pass 1 Check 1 Component 11 (validator coverage partial) → explained by Check 6b (validator rules blur client/server boundary)
- Pass 1 Check 4 (orphan assessment) → contextualizing information from Check 5 (scope decisions not propagated)

---

## Conclusion

The reverse direction (Test Research → Implementation Guide) reveals a **significant propagation gap**. The implementation guide (v7.0, Feb 5) pre-dates the test research review phases (Feb 12-13) by 7 days, and nearly all review-phase scope decisions, corrections, and specification details have not been reflected back.

No critical or high-severity findings exist, but the 13 medium-severity items collectively represent a **meaningful quality gap** that should be addressed before coding begins — especially items #1 (incorrect API), #2 (file count), and #4 (command state machine). (Item #3 binary SWE deferral has been withdrawn — the guide correctly treats binary parsing as in-scope.)

Pass 3 will execute the bidirectional checks (Checks 9-12) and produce the final consolidated report with all update recommendations.

---

_Generated by A1 Pass 2 execution. Next: A1 Pass 3 (Checks 9-12, Bidirectional + Final Report Assembly)._
