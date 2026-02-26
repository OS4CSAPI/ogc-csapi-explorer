# SensorML 3.0 Parser Testing Specification

> **⚠️ REVIEW NOTICE (Phase 2D, C2):** This document was identified in Phase 2D review as having CRITICAL issues: it defines 43 validation/error IDs (VAL-SML-001 through VAL-SML-081, ERR-SML-001 through ERR-SML-052) that test whether SensorML JSON documents **conform to the SensorML 3.0 specification** — a server/document concern, not a client parser concern.
>
> **Key problems identified:**
>
> 1. **No parser output model defined.** The document catalogs every SensorML property and validation rule but never defines what `parseSensorML()` returns — no TypeScript interface for the parser output is specified anywhere.
> 2. **"Parser" conflated with "validator."** Enforcement levels say "MUST enforce: Parser rejects invalid documents." A client parser should parse what it receives and produce a useful TypeScript model, not act as a specification conformance validator.
> 3. **Live server fixture sourcing.** Section 8 plans to fetch fixtures from OpenSensorHub (`https://api.georobotix.io/ogc/t18/api`) with a two-tier assertion strategy (spec examples = MUST pass; live data = SHOULD handle gracefully). This is anti-pattern AP2.
> 4. **Test structure mirrors the SensorML spec**, organized by spec structure types and sections, not by parser functions.
>
> **What to use from this document:** The property matrices (Section 2), recursive structure strategies (Section 4), SWE Common integration points (Section 5), fixture directory structure (Section 11), and phased implementation plan (Section 14) contain valuable reference material. The spec example fixture inventory (Section 7) is directly useful.
>
> **What NOT to use:** Do not use the VAL-SML-_/ERR-SML-_ IDs as test identifiers. Do not implement the enforcement levels as defined (parser-as-validator). Do not source fixtures from live servers. Instead, define the parser's TypeScript output interface first, then test `parseSensorML(fixture) → expectedTypedObject`. See [Phase 2D review](../review/phase-2d-csapi-specific-testing-category.md) for details.

**Research Plan:** [Research Plan 09: SensorML 3.0 Format Testing Requirements](../research-plans/09-sensorml-testing-requirements.md)  
**Research Questions:** 80 questions about SensorML 3.0 structure types, JSON schema analysis, recursive structure testing, identification and classification, characteristics and capabilities integration, components and nesting depth, temporal validity, observable properties, error handling, specification examples, real-world examples, and parser implementation testing  
**Methodology:** 4-phase systematic analysis (SensorML 3.0 specification deep dive extracting structure types and normative statements → JSON schema analysis for format constraints → Example analysis from spec and real-world data → Test strategy design creating parser test specification)  
**Research Time:** ~2 hours (February 5, 2026)

**Primary Source(s):**

- [SensorML 3.0 Specification (23-000)](https://docs.ogc.org/is/23-000/23-000.html)
- [SensorML 3.0 JSON Schema](https://schemas.opengis.net/sensorML/3.0/)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (SensorML parser specification)

**Supporting Resources:**

- Section 8: [CSAPI Specification Reference](08-csapi-specification-test-requirements.md) (SensorML specification details)
- [Format Requirements Analysis](../../requirements/csapi-format-requirements.md) (SensorML subset for CSAPI)
- [OpenSensorHub Analysis](../../requirements/csapi-opensensorhub-analysis.md) (real-world SensorML examples)
- Section 6: [Meaningful vs Trivial Definition](06-meaningful-vs-trivial-definition.md) (quality context for test depth)
- Section 1-2: Upstream format parser test patterns

**Document Purpose:** Define testing requirements for the SensorML 3.0 parser covering all 4 structure types (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess), recursive component parsing up to 3 levels deep, SWE Common integration, error handling, and fixture requirements (~25 fixtures from spec examples), with estimated 500-800 test lines. **Note:** This document must be supplemented with a parser output TypeScript interface definition before tests can be implemented — see review notice above.

---

## Executive Summary

This document defines comprehensive testing requirements for the SensorML 3.0 parser, covering all structure types, validation rules, recursive component parsing, SWE Common integration, and error handling. SensorML 3.0 is the primary format for Systems, Procedures, and Deployments resources in CSAPI Part 1, making its parser critical for client library functionality.

### Key Findings

**Total Structure Types:** 4 types requiring comprehensive testing

- PhysicalSystem (CRITICAL - most common, complex component hierarchies)
- PhysicalComponent (HIGH - individual sensors/actuators)
- SimpleProcess (MEDIUM - algorithms, simulations)
- AggregateProcess (HIGH - composite processes with connections)

**Testing Priorities:**

- **CRITICAL:** PhysicalSystem parsing, component nesting (1-2 levels), uniqueIdentifier validation, basic error handling
- **HIGH:** PhysicalComponent parsing, AggregateProcess parsing, characteristics/capabilities (SWE Common integration), spec example coverage
- **MEDIUM:** SimpleProcess parsing, deep nesting (3+ levels), advanced error conditions
- **LOW:** Contacts/documentation parsing, position/location (defer to geometry parser)

**Fixture Requirements:** ~25 fixtures

- 5 PhysicalSystem (weather station, vehicle, UAV, buoy, satellite)
- 3 PhysicalComponent (temp sensor, camera, accelerometer)
- 2 SimpleProcess (algorithm, computation)
- 3 AggregateProcess (processing chain, workflow)
- 4 Composite systems (1-level, 2-level, 3-level nesting)
- 5 Error cases (missing-id, invalid-uri, malformed, circular-ref, unknown-type)
- 3 Spec examples (from Part 1, Annex B)

**Estimated Test Implementation:** 500-800 lines

- PhysicalSystem: 150-225 lines (12-15 tests)
- PhysicalComponent: 80-120 lines (8-10 tests)
- SimpleProcess: 50-72 lines (5-6 tests)
- AggregateProcess: 80-150 lines (8-10 tests)
- Error handling: 64-100 lines (8-10 tests)
- Recursive structures: 75-120 lines (5-6 tests)

**Key Testing Challenges:**

1. **Recursive component parsing** - Deep nesting with stack overflow prevention
2. **SWE Common integration** - Characteristics/capabilities parsing requires SWE Common parser
3. **Reference resolution** - External links to components, datasheets, features
4. **Circular reference detection** - Components referencing themselves
5. **Non-standard extensions** - Real-world data may have custom properties

---

## 1. Structure Type Testing Requirements

| Structure Type        | Priority     | Required Tests                                   | Fixtures Needed | Test Lines Estimate | Notes                                       |
| --------------------- | ------------ | ------------------------------------------------ | --------------- | ------------------- | ------------------------------------------- |
| **PhysicalSystem**    | **CRITICAL** | Full parsing, validation, components, nesting    | 5-8             | 150-225             | Most common, supports component hierarchies |
| **PhysicalComponent** | HIGH         | Full parsing, validation, characteristics        | 3-5             | 80-120              | Individual hardware elements                |
| **SimpleProcess**     | MEDIUM       | Basic parsing, validation, method                | 2-3             | 50-72               | Software/algorithms, less complex           |
| **AggregateProcess**  | HIGH         | Full parsing, component aggregation, connections | 3-4             | 80-150              | Composite processes with data flow          |

**Rationale:**

- PhysicalSystem is CRITICAL because it's the primary representation for sensor systems (weather stations, platforms, networks)
- PhysicalComponent is HIGH because it represents individual sensors referenced by systems
- AggregateProcess is HIGH because it enables complex processing workflows
- SimpleProcess is MEDIUM because it's less commonly used for physical systems (more for procedures)

---

## 2. Property Testing Matrices

### 2.1 PhysicalSystem Property Testing

**Structure Type:** PhysicalSystem  
**Media Type:** `application/sml+json`  
**Priority:** **CRITICAL**

| Property                            | Required/Optional     | Validation Rules                    | Edge Cases                                         | Test Type   | Priority     | Spec Reference                      |
| ----------------------------------- | --------------------- | ----------------------------------- | -------------------------------------------------- | ----------- | ------------ | ----------------------------------- |
| **Core Identification**             |
| `type`                              | Required              | Must be "PhysicalSystem"            | Missing, wrong type                                | Unit        | **CRITICAL** | SensorML 3.0, §7                    |
| `uniqueId`                          | Required              | Valid URI (preferably URN)          | Missing, invalid URI, relative URI                 | Unit        | **CRITICAL** | Part 1, Req 2; SensorML 3.0, §7.2   |
| `definition`                        | Required              | Valid URI (sosa:System or subclass) | Missing, invalid URI                               | Unit        | HIGH         | SensorML 3.0, §7                    |
| `label`                             | Required              | Non-empty string                    | Missing, empty, very long (>1000 chars)            | Unit        | HIGH         | SensorML 3.0, §7.2                  |
| `id`                                | Optional              | String local identifier             | Missing, duplicate in collection                   | Unit        | MEDIUM       | CSAPI convention                    |
| `description`                       | Optional              | String                              | Missing, empty, very long                          | Unit        | LOW          | SensorML 3.0, §7                    |
| **Identification & Classification** |
| `identifiers`                       | Optional              | Array of Terms                      | Empty array, invalid terms, duplicate definitions  | Unit        | HIGH         | SensorML 3.0, §7.2                  |
| `identifiers[].definition`          | Required (if present) | Valid URI                           | Missing, invalid URI                               | Unit        | HIGH         | SensorML 3.0, §7.2                  |
| `identifiers[].label`               | Optional              | String                              | Missing, empty                                     | Unit        | LOW          | SensorML 3.0, §7.2                  |
| `identifiers[].value`               | Required (if present) | String                              | Missing, empty                                     | Unit        | HIGH         | SensorML 3.0, §7.2                  |
| `classifiers`                       | Optional              | Array of Terms                      | Empty array, invalid terms                         | Unit        | HIGH         | SensorML 3.0, §7.3                  |
| `classifiers[].definition`          | Required (if present) | Valid URI                           | Missing, invalid URI                               | Unit        | HIGH         | SensorML 3.0, §7.3                  |
| `classifiers[].value`               | Required (if present) | String from vocabulary              | Missing, invalid value                             | Unit        | MEDIUM       | SensorML 3.0, §7.3; Part 1, Table 6 |
| **Temporal Validity**               |
| `validTime`                         | Optional              | Array of 2 ISO 8601 datetimes       | Invalid format, start > end, open intervals (null) | Unit        | MEDIUM       | SensorML 3.0, §7; CSAPI             |
| **Process Metadata**                |
| `typeOf`                            | Optional              | Link object with href               | Invalid href, missing href                         | Unit        | LOW          | SensorML 3.0, §7                    |
| `inputs`                            | Optional              | Array of SWE Common components      | Malformed components, invalid types                | Integration | MEDIUM       | SensorML 3.0, §7                    |
| `outputs`                           | Optional              | Array of SWE Common components      | Malformed components, invalid types                | Integration | MEDIUM       | SensorML 3.0, §7                    |
| `parameters`                        | Optional              | Array of SWE Common components      | Malformed components, missing values               | Integration | MEDIUM       | SensorML 3.0, §7                    |
| **Characteristics & Capabilities**  |
| `characteristics`                   | Optional              | Array of CharacteristicList         | Malformed, invalid SWE Common DataRecord           | Integration | HIGH         | SensorML 3.0, §7.6                  |
| `capabilities`                      | Optional              | Array of CapabilityList             | Malformed, invalid SWE Common DataRecord           | Integration | HIGH         | SensorML 3.0, §7.5                  |
| **Physical Properties**             |
| `attachedTo`                        | Optional              | Link to parent platform             | Invalid href, circular reference                   | Unit        | MEDIUM       | SensorML 3.0, §8                    |
| `position`                          | Optional              | Point, Pose, Text, or DataStream    | Invalid geometry, malformed                        | Unit        | LOW          | SensorML 3.0, §8                    |
| **Components (Composite Systems)**  |
| `components`                        | Optional              | Array of component objects          | Empty array, invalid components, circular refs     | Integration | **CRITICAL** | SensorML 3.0, §8.3                  |
| `components[].name`                 | Required (if present) | String                              | Missing, duplicate names                           | Unit        | HIGH         | SensorML 3.0, §8.3                  |
| `components[].href`                 | Required (if present) | Valid URI or system object          | Missing, invalid URI, malformed inline system      | Integration | HIGH         | SensorML 3.0, §8.3                  |
| `connections`                       | Optional              | Array of connection objects         | Malformed, invalid refs, orphan connections        | Integration | MEDIUM       | SensorML 3.0, §8.3                  |
| **Additional Metadata**             |
| `contacts`                          | Optional              | Array of ResponsibleParty           | Malformed contact objects                          | Unit        | LOW          | SensorML 3.0, §7                    |
| `documentation`                     | Optional              | Array of Document links             | Invalid hrefs                                      | Unit        | LOW          | SensorML 3.0, §7                    |
| `links`                             | Optional              | Array of Link objects               | Malformed links, missing rel                       | Unit        | MEDIUM       | CSAPI convention                    |

**Test Coverage Notes:**

- All CRITICAL properties must have positive and negative tests
- Component nesting tested up to 3 levels deep
- Circular reference detection tested with hand-crafted fixtures
- SWE Common integration tested via dedicated integration tests (coordinate with Section 10)

---

### 2.2 PhysicalComponent Property Testing

**Structure Type:** PhysicalComponent  
**Priority:** HIGH

| Property                            | Required/Optional | Validation Rules                             | Edge Cases                                             | Test Type   | Priority | Spec Reference                    |
| ----------------------------------- | ----------------- | -------------------------------------------- | ------------------------------------------------------ | ----------- | -------- | --------------------------------- |
| **Core Identification**             |
| `type`                              | Required          | Must be "PhysicalComponent"                  | Missing, wrong type                                    | Unit        | HIGH     | SensorML 3.0, §7                  |
| `uniqueId`                          | Required          | Valid URI                                    | Missing, invalid URI                                   | Unit        | HIGH     | Part 1, Req 2; SensorML 3.0, §7.2 |
| `definition`                        | Required          | Valid URI (sosa:Sensor, sosa:Actuator, etc.) | Missing, invalid URI                                   | Unit        | HIGH     | SensorML 3.0, §7                  |
| `label`                             | Required          | Non-empty string                             | Missing, empty                                         | Unit        | HIGH     | SensorML 3.0, §7.2                |
| `id`                                | Optional          | String local identifier                      | Missing                                                | Unit        | MEDIUM   | CSAPI convention                  |
| **Identification & Classification** |
| `identifiers`                       | Optional          | Array of Terms                               | Empty array, common identifiers (serial number, model) | Unit        | MEDIUM   | SensorML 3.0, §7.2                |
| `classifiers`                       | Optional          | Array of Terms                               | Component type classifiers                             | Unit        | MEDIUM   | SensorML 3.0, §7.3                |
| **Physical Properties**             |
| `attachedTo`                        | Optional          | Link to parent system                        | Valid parent reference                                 | Unit        | MEDIUM   | SensorML 3.0, §8                  |
| `position`                          | Optional          | Point or Pose                                | Component location within system                       | Unit        | LOW      | SensorML 3.0, §8                  |
| **Process Metadata**                |
| `method`                            | Optional          | Link or inline process description           | Measurement methodology                                | Unit        | LOW      | SensorML 3.0, §8                  |
| `inputs`                            | Optional          | Array of SWE Common components               | Observed phenomena inputs                              | Integration | MEDIUM   | SensorML 3.0, §7                  |
| `outputs`                           | Optional          | Array of SWE Common components               | Measurement outputs                                    | Integration | MEDIUM   | SensorML 3.0, §7                  |
| `parameters`                        | Optional          | Array of SWE Common components               | Configuration parameters                               | Integration | LOW      | SensorML 3.0, §7                  |
| **Characteristics & Capabilities**  |
| `characteristics`                   | Optional          | Array of CharacteristicList                  | Physical properties (size, weight, power)              | Integration | MEDIUM   | SensorML 3.0, §7.6                |
| `capabilities`                      | Optional          | Array of CapabilityList                      | Measurement range, accuracy, resolution                | Integration | HIGH     | SensorML 3.0, §7.5                |
| **Temporal Validity**               |
| `validTime`                         | Optional          | Array of 2 ISO 8601 datetimes                | Component operational period                           | Unit        | LOW      | SensorML 3.0, §7                  |
| **Additional Metadata**             |
| `contacts`                          | Optional          | Array of ResponsibleParty                    | Manufacturer, operator                                 | Unit        | LOW      | SensorML 3.0, §7                  |
| `documentation`                     | Optional          | Array of Document links                      | Datasheet, manual                                      | Unit        | LOW      | SensorML 3.0, §7                  |

**Test Coverage Notes:**

- Focus on capabilities testing (measurement specifications)
- Test realistic component types (thermometer, camera, GPS, accelerometer)
- Characteristics testing coordinates with SWE Common tests

---

### 2.3 SimpleProcess Property Testing

**Structure Type:** SimpleProcess  
**Priority:** MEDIUM

| Property                | Required/Optional | Validation Rules                     | Edge Cases                   | Test Type   | Priority | Spec Reference     |
| ----------------------- | ----------------- | ------------------------------------ | ---------------------------- | ----------- | -------- | ------------------ |
| **Core Identification** |
| `type`                  | Required          | Must be "SimpleProcess"              | Missing, wrong type          | Unit        | MEDIUM   | SensorML 3.0, §7   |
| `uniqueId`              | Required          | Valid URI                            | Missing, invalid URI         | Unit        | MEDIUM   | SensorML 3.0, §7.2 |
| `definition`            | Required          | Valid URI (process type)             | Missing                      | Unit        | MEDIUM   | SensorML 3.0, §7   |
| `label`                 | Required          | Non-empty string                     | Missing                      | Unit        | MEDIUM   | SensorML 3.0, §7.2 |
| **Process Description** |
| `method`                | Optional          | Link or inline algorithm description | Missing, complex methodology | Unit        | LOW      | SensorML 3.0, §7   |
| **Process IO**          |
| `inputs`                | Optional          | Array of SWE Common components       | Algorithm inputs             | Integration | LOW      | SensorML 3.0, §7   |
| `outputs`               | Optional          | Array of SWE Common components       | Algorithm outputs            | Integration | LOW      | SensorML 3.0, §7   |
| `parameters`            | Optional          | Array of SWE Common components       | Algorithm parameters         | Integration | LOW      | SensorML 3.0, §7   |
| **Additional Metadata** |
| `identifiers`           | Optional          | Array of Terms                       | Version identifiers          | Unit        | LOW      | SensorML 3.0, §7.2 |
| `documentation`         | Optional          | Array of Document links              | Algorithm documentation      | Unit        | LOW      | SensorML 3.0, §7   |

**Test Coverage Notes:**

- Lower priority due to less common usage for physical systems
- Focus on basic parsing and validation
- Test representative use cases (data processing algorithms, simulations)

---

### 2.4 AggregateProcess Property Testing

**Structure Type:** AggregateProcess  
**Priority:** HIGH

| Property                    | Required/Optional | Validation Rules               | Edge Cases                      | Test Type   | Priority | Spec Reference     |
| --------------------------- | ----------------- | ------------------------------ | ------------------------------- | ----------- | -------- | ------------------ |
| **Core Identification**     |
| `type`                      | Required          | Must be "AggregateProcess"     | Missing, wrong type             | Unit        | HIGH     | SensorML 3.0, §7   |
| `uniqueId`                  | Required          | Valid URI                      | Missing, invalid URI            | Unit        | HIGH     | SensorML 3.0, §7.2 |
| `definition`                | Required          | Valid URI                      | Missing                         | Unit        | HIGH     | SensorML 3.0, §7   |
| `label`                     | Required          | Non-empty string               | Missing                         | Unit        | HIGH     | SensorML 3.0, §7.2 |
| **Component Aggregation**   |
| `components`                | Required          | Array of component processes   | Empty array, invalid components | Integration | HIGH     | SensorML 3.0, §8.3 |
| `components[].name`         | Required          | String                         | Missing, duplicate names        | Unit        | HIGH     | SensorML 3.0, §8.3 |
| `components[].href`         | Required          | Valid URI or inline process    | Missing, invalid reference      | Integration | HIGH     | SensorML 3.0, §8.3 |
| `connections`               | Optional          | Array of connection objects    | Data flow between components    | Integration | HIGH     | SensorML 3.0, §8.3 |
| `connections[].source`      | Required          | Valid ref to component output  | Missing, invalid ref            | Unit        | MEDIUM   | SensorML 3.0, §8.3 |
| `connections[].destination` | Required          | Valid ref to component input   | Missing, invalid ref            | Unit        | MEDIUM   | SensorML 3.0, §8.3 |
| **Process IO**              |
| `inputs`                    | Optional          | Array of SWE Common components | Aggregate inputs                | Integration | MEDIUM   | SensorML 3.0, §7   |
| `outputs`                   | Optional          | Array of SWE Common components | Aggregate outputs               | Integration | MEDIUM   | SensorML 3.0, §7   |
| `parameters`                | Optional          | Array of SWE Common components | Workflow parameters             | Integration | LOW      | SensorML 3.0, §7   |

**Test Coverage Notes:**

- Connections testing critical for data flow validation
- Test multi-step processing workflows
- Validate component reference resolution

---

## 3. Validation Rule Checklist

> **⚠️ REVIEW NOTICE (Phase 2D, C2):** The VAL-SML-\* IDs below catalog SensorML specification conformance rules — they define what a valid SensorML document looks like, not what a client parser should test. A client parser test should verify `parseSensorML(fixture) → correctTypedOutput`, not validate whether a document conforms to the spec. These rules are retained as **reference material** for understanding what input shapes the parser will encounter, but should NOT be used as test case identifiers. The "Enforcement Level" column is particularly problematic — see notice below the table.

| Validation Rule ID                 | Description                                                        | Normative/Schema | Enforcement Level | Test Coverage    | Priority     | Spec Reference                    |
| ---------------------------------- | ------------------------------------------------------------------ | ---------------- | ----------------- | ---------------- | ------------ | --------------------------------- |
| **Core Structure**                 |
| VAL-SML-001                        | Root element valid SensorML type                                   | Normative        | MUST enforce      | Unit test        | HIGH         | SensorML 3.0, Part 1              |
| VAL-SML-002                        | Systems must be PhysicalSystem, AggregateProcess, or SimpleProcess | Normative        | MUST enforce      | Unit test        | HIGH         | SensorML 3.0, §7; Part 1, Table 9 |
| VAL-SML-003                        | Procedures must be PhysicalComponent or SimpleProcess              | Normative        | SHOULD enforce    | Unit test        | MEDIUM       | SensorML 3.0, §7; Part 1          |
| **Identification**                 |
| VAL-SML-010                        | Systems must have identification section                           | Normative        | SHOULD have       | Unit test        | HIGH         | SensorML 3.0, §7.2                |
| VAL-SML-011                        | uniqueID identifier required                                       | Normative        | MUST have         | Unit test        | **CRITICAL** | SensorML 3.0, §7.2; Part 1, Req 2 |
| VAL-SML-012                        | uniqueID must be valid URI                                         | Schema           | MUST enforce      | Unit test        | **CRITICAL** | Part 1, Req 2                     |
| VAL-SML-013                        | label or description required                                      | Normative        | MUST have one     | Unit test        | HIGH         | SensorML 3.0, §7.2                |
| **Classification**                 |
| VAL-SML-020                        | Classification section for systemType                              | Normative        | SHOULD have       | Unit test        | MEDIUM       | SensorML 3.0, §7.3                |
| VAL-SML-021                        | systemType classifier from Table 6 vocabulary                      | Schema           | SHOULD enforce    | Unit test        | MEDIUM       | Part 1, Table 6                   |
| **Components**                     |
| VAL-SML-030                        | Components section references valid systems                        | Normative        | MUST enforce      | Integration test | MEDIUM       | SensorML 3.0, §8.3                |
| VAL-SML-031                        | Component links valid (internal or external)                       | Normative        | MUST validate     | Integration test | MEDIUM       | SensorML 3.0, §8.3                |
| VAL-SML-032                        | Component names unique within system                               | Schema           | SHOULD enforce    | Unit test        | MEDIUM       | SensorML 3.0, §8.3                |
| **Characteristics & Capabilities** |
| VAL-SML-040                        | Capabilities section valid SWE Common DataRecord                   | Normative        | MUST parse        | Integration test | MEDIUM       | SensorML 3.0, §7.5                |
| VAL-SML-041                        | Characteristics section valid SWE Common DataRecord                | Normative        | MUST parse        | Integration test | MEDIUM       | SensorML 3.0, §7.6                |
| **Temporal**                       |
| VAL-SML-050                        | validTime valid ISO 8601 interval                                  | Schema           | SHOULD validate   | Unit test        | MEDIUM       | SensorML 3.0, §7                  |
| VAL-SML-051                        | validTime start <= end (if closed interval)                        | Schema           | SHOULD validate   | Unit test        | LOW          | ISO 8601                          |
| **Links & References**             |
| VAL-SML-060                        | All href properties valid URIs                                     | Schema           | MUST validate     | Unit test        | MEDIUM       | SensorML 3.0                      |
| VAL-SML-061                        | typeOf reference valid process link                                | Schema           | SHOULD validate   | Unit test        | LOW          | SensorML 3.0, §7                  |
| **Process IO**                     |
| VAL-SML-070                        | Inputs valid SWE Common components                                 | Normative        | MUST parse        | Integration test | MEDIUM       | SensorML 3.0, §7                  |
| VAL-SML-071                        | Outputs valid SWE Common components                                | Normative        | MUST parse        | Integration test | MEDIUM       | SensorML 3.0, §7                  |
| VAL-SML-072                        | Parameters valid SWE Common components                             | Normative        | MUST parse        | Integration test | LOW          | SensorML 3.0, §7                  |
| **Connections**                    |
| VAL-SML-080                        | Connection source refs valid component outputs                     | Normative        | MUST validate     | Integration test | MEDIUM       | SensorML 3.0, §8.3                |
| VAL-SML-081                        | Connection destination refs valid component inputs                 | Normative        | MUST validate     | Integration test | MEDIUM       | SensorML 3.0, §8.3                |

**Total Validation Rules:** 21 rules (11 CRITICAL/HIGH priority, 10 MEDIUM/LOW priority)

**Enforcement Level Definitions (REVIEW NOTICE — these conflate parser with validator):**

> **⚠️ Phase 2D, C2:** These enforcement levels define the parser as a specification conformance validator ("Parser rejects invalid documents"). A client parser's job is to **transform input into a useful TypeScript model**, not to enforce specification conformance. The parser should extract what it can from the input and produce a typed output object. It should throw only when the input is unparseable (e.g., missing `type` field so the parser can't determine the structure type), not when a document violates a spec SHOULD requirement.

- ~~**MUST enforce:** Parser rejects invalid documents~~ → Parser should extract value if present; throw only if structurally unparseable
- ~~**SHOULD enforce:** Parser warns about violations but continues~~ → Parser should extract value without validation
- **SHOULD have:** Parser accepts documents without property ~~but logs info message~~ → uses default/undefined
- **MUST parse:** Parser extracts ~~and validates~~ structure into typed output
- ~~**MUST validate:** Parser checks constraints and reports errors~~ → Parser extracts value as-is

---

## 4. Recursive Structure Testing

| Nesting Level            | Test Scenario                             | Fixture Needed      | Expected Behavior                            | Test Type   | Priority     | Notes                                            |
| ------------------------ | ----------------------------------------- | ------------------- | -------------------------------------------- | ----------- | ------------ | ------------------------------------------------ |
| **Level 0 (No Nesting)** |
| Simple System            | System with no components                 | Yes (spec example)  | Parse all properties correctly               | Unit        | **CRITICAL** | Baseline test                                    |
| **Level 1 (Shallow)**    |
| System with Components   | System → 3 Components (flat)              | Yes (spec example)  | Parse all components, extract names          | Integration | **CRITICAL** | Most common pattern                              |
| **Level 2 (Medium)**     |
| Nested System            | System → Component → Subcomponent         | Yes (hand-craft)    | Parse 2-level hierarchy, maintain references | Integration | HIGH         | Weather station with sensor platform             |
| **Level 3 (Deep)**       |
| Deep Hierarchy           | System → Component → Sub → Sub-sub        | Yes (hand-craft)    | Parse 3-level hierarchy                      | Integration | MEDIUM       | Complex platform like satellite                  |
| **Level 4+ (Very Deep)** |
| Excessive Nesting        | System → ... → n-level deep               | No (document limit) | Either parse or limit depth gracefully       | Integration | LOW          | Edge case - set practical limit (e.g., 5 levels) |
| **Circular References**  |
| Self-Reference           | System references itself in components    | Yes (hand-craft)    | Detect circular reference, error gracefully  | Integration | MEDIUM       | Prevent infinite loops                           |
| Loop Reference           | System A → B → A                          | Yes (hand-craft)    | Detect loop, error gracefully                | Integration | LOW          | Complex circular dependency                      |
| **Missing References**   |
| External Component       | Component href points to non-existent URI | Yes (hand-craft)    | Error handling, clear message                | Integration | MEDIUM       | Network/server issues                            |
| Broken Inline            | Component inline object malformed         | Yes (hand-craft)    | Parse error with context                     | Integration | MEDIUM       | Validation error                                 |
| **Mixed Nesting**        |
| Hybrid Structure         | System with inline + external components  | Yes (hand-craft)    | Parse both types correctly                   | Integration | MEDIUM       | Real-world pattern                               |

**Nesting Depth Strategy:**

- **Recommended Limit:** 5 levels (practical limit for most real-world systems)
- **Stack Overflow Prevention:** Iterative parsing with explicit depth tracking
- **Circular Reference Detection:** Track visited component IDs during traversal
- **Error Messages:** Include component path in error messages (e.g., "components[2].components[1]")

**Test Coverage:**

- Levels 1-2: **Comprehensive** (multiple fixtures, all structure types)
- Level 3: **Representative** (2-3 fixtures, common patterns)
- Level 4+: **Edge cases** (1-2 fixtures, stress testing)
- Circular refs: **Dedicated** (3-4 fixtures, various patterns)

---

## 5. SWE Common Integration Testing

| Integration Point         | SWE Common Type                          | Test Requirement                                     | Priority     | Coordination with Section 10          | Notes                                |
| ------------------------- | ---------------------------------------- | ---------------------------------------------------- | ------------ | ------------------------------------- | ------------------------------------ |
| **Characteristics**       |
| Physical Properties       | DataRecord                               | Parse structure, extract field names and definitions | HIGH         | Test with Section 10 DataRecord tests | Weight, size, power requirements     |
| Material Properties       | DataRecord                               | Parse nested DataRecords                             | MEDIUM       | Use shared SWE Common fixtures        | Material type, composition           |
| Environmental Tolerances  | DataRecord with constraints              | Parse value ranges and intervals                     | MEDIUM       | Constraint parsing tests              | Operating temp range, humidity range |
| **Capabilities**          |
| Measurement Range         | QuantityRange                            | Parse min/max values with units                      | **CRITICAL** | Section 10 QuantityRange tests        | -40 to +85°C range                   |
| Accuracy                  | Quantity                                 | Parse value with unit                                | **CRITICAL** | Section 10 Quantity tests             | ±0.1°C accuracy                      |
| Resolution                | Quantity                                 | Parse value with unit                                | HIGH         | Section 10 Quantity tests             | 0.01°C resolution                    |
| Response Time             | Quantity with time unit                  | Parse temporal quantity                              | MEDIUM       | Section 10 time unit tests            | 30s response time                    |
| **Observable Properties** |
| Input Definitions         | Array of DataComponents                  | Parse component array                                | MEDIUM       | Section 10 component array tests      | What system observes                 |
| Output Definitions        | Array of DataComponents                  | Parse component array                                | MEDIUM       | Section 10 component array tests      | What system produces                 |
| Parameter Definitions     | Array of DataComponents with values      | Parse components and extract values                  | MEDIUM       | Section 10 parameter tests            | Configuration settings               |
| **Complex Structures**    |
| Nested DataRecords        | DataRecord > DataRecord                  | Parse multi-level nesting                            | MEDIUM       | Section 10 nesting tests              | Grouped characteristics              |
| Mixed Component Types     | DataRecord with Quantity, Text, Category | Parse heterogeneous fields                           | HIGH         | Section 10 mixed type tests           | Real-world property sets             |

**Integration Test Strategy:**

1. **Unit tests:** Verify SensorML parser extracts SWE Common structures correctly (structure, not deep parsing)
2. **Integration tests:** Pass extracted structures to SWE Common parser, validate full parsing
3. **Shared fixtures:** Use same SWE Common fixtures in both Section 9 and Section 10 tests
4. **Error propagation:** SWE Common parsing errors reported through SensorML parser error messages
5. **Lazy parsing:** Parser can skip SWE Common deep parsing if not needed (performance optimization)

**Coordination Points with Section 10:**

- Share fixtures for characteristics/capabilities DataRecords
- Consistent error message format for SWE Common validation errors
- Parser interface design (pass raw JSON vs parsed objects)
- Performance considerations (parse once, reuse results)

---

## 6. Error Condition Testing

> **⚠️ REVIEW NOTICE (Phase 2D, C2):** The ERR-SML-\* IDs below define 22 error scenarios, many of which validate server data correctness rather than testing client parser behavior. A client parser should only throw errors when the input is **structurally unparseable** (e.g., invalid JSON, missing `type` field needed for dispatch). It should NOT reject documents for having an "invalid URI format" in `uniqueId` or a `validTime` with `start > end` — these are server data quality issues, not parser concerns. The parser should extract these values as-is and let the client code decide what to do with them.
>
> **Retain as parser error tests:** ERR-SML-001/002 (malformed JSON), ERR-SML-010 (missing `type`), ERR-SML-022 (unknown type value), ERR-SML-030 (circular reference — stack overflow prevention). These test genuine parser failure modes.
>
> **Reclassify as non-errors:** ERR-SML-011/012/013 (missing optional-like properties), ERR-SML-020/021 (URI format validation), ERR-SML-023/024 (temporal validation), ERR-SML-040/041/042 (SWE Common structure validation). The parser should extract whatever is there, not validate it.

| Error ID                        | Error Condition                | Test Scenario                            | Expected Error               | Test Type   | Priority     | Error Message Example                                                                                                 |
| ------------------------------- | ------------------------------ | ---------------------------------------- | ---------------------------- | ----------- | ------------ | --------------------------------------------------------------------------------------------------------------------- |
| **Malformed JSON**              |
| ERR-SML-001                     | Invalid JSON syntax            | Malformed JSON document                  | Parse error with line/column | Unit        | MEDIUM       | "Invalid JSON at line 23, column 15: unexpected token '}'"                                                            |
| ERR-SML-002                     | Missing required braces        | Incomplete JSON object                   | Parse error                  | Unit        | MEDIUM       | "Unexpected end of JSON input"                                                                                        |
| **Missing Required Properties** |
| ERR-SML-010                     | Missing type                   | System without type property             | Validation error             | Unit        | HIGH         | "Missing required property 'type'"                                                                                    |
| ERR-SML-011                     | Missing uniqueId               | System without uniqueId                  | Validation error             | Unit        | **CRITICAL** | "Missing required property 'uniqueId' (Part 1, Req 2)"                                                                |
| ERR-SML-012                     | Missing definition             | System without definition                | Validation error             | Unit        | HIGH         | "Missing required property 'definition'"                                                                              |
| ERR-SML-013                     | Missing label                  | System without label                     | Validation warning           | Unit        | MEDIUM       | "Missing recommended property 'label'"                                                                                |
| **Invalid Property Values**     |
| ERR-SML-020                     | Invalid URI format             | uniqueId = "not a uri"                   | Validation error             | Unit        | **CRITICAL** | "Invalid URI format for 'uniqueId': 'not a uri'"                                                                      |
| ERR-SML-021                     | Relative URI                   | uniqueId = "../system"                   | Validation error             | Unit        | HIGH         | "uniqueId must be absolute URI, got relative: '../system'"                                                            |
| ERR-SML-022                     | Invalid type value             | type = "UnknownSystem"                   | Validation error             | Unit        | MEDIUM       | "Unknown SensorML type 'UnknownSystem'. Expected: PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess" |
| ERR-SML-023                     | Invalid validTime format       | validTime = "not a date"                 | Validation error             | Unit        | MEDIUM       | "Invalid ISO 8601 format for 'validTime[0]': 'not a date'"                                                            |
| ERR-SML-024                     | validTime start > end          | validTime = ["2025-01-01", "2024-01-01"] | Validation error             | Unit        | LOW          | "validTime start '2025-01-01' is after end '2024-01-01'"                                                              |
| **Component Errors**            |
| ERR-SML-030                     | Circular reference             | System references itself in components   | Detection error              | Integration | MEDIUM       | "Circular reference detected: system 'urn:system:A' references itself"                                                |
| ERR-SML-031                     | Missing component href         | Component without href or inline object  | Validation error             | Integration | MEDIUM       | "Component 'sensor1' missing 'href' property"                                                                         |
| ERR-SML-032                     | Invalid component ref          | Component href = "invalid-uri"           | Validation error             | Integration | MEDIUM       | "Invalid component reference: 'invalid-uri'"                                                                          |
| ERR-SML-033                     | Duplicate component name       | Two components with name "sensor1"       | Validation warning           | Integration | LOW          | "Duplicate component name 'sensor1' at components[2]"                                                                 |
| **SWE Common Errors**           |
| ERR-SML-040                     | Malformed characteristics      | characteristics not valid DataRecord     | Validation error             | Integration | HIGH         | "Invalid characteristics: expected DataRecord, got object without 'type'"                                             |
| ERR-SML-041                     | Malformed capabilities         | capabilities not valid DataRecord        | Validation error             | Integration | HIGH         | "Invalid capabilities: expected CapabilityList with DataRecord"                                                       |
| ERR-SML-042                     | Invalid SWE component          | Input/output with unknown type           | Validation error             | Integration | MEDIUM       | "Invalid SWE Common component type 'UnknownType' in inputs[0]"                                                        |
| **Connection Errors**           |
| ERR-SML-050                     | Invalid connection source      | Source ref points nowhere                | Validation error             | Integration | MEDIUM       | "Connection source 'components/sensor1/outputs/temp' not found"                                                       |
| ERR-SML-051                     | Invalid connection destination | Destination ref points nowhere           | Validation error             | Integration | MEDIUM       | "Connection destination 'outputs/temperature' not found"                                                              |
| ERR-SML-052                     | Orphan connection              | Connection without matching components   | Validation warning           | Integration | LOW          | "Connection references component 'sensor2' not in components array"                                                   |

**Total Error Scenarios:** 22 scenarios (8 CRITICAL/HIGH, 10 MEDIUM, 4 LOW)

**Error Handling Strategy:**

- **CRITICAL errors:** Stop parsing, throw exception
- **HIGH errors:** Continue parsing, collect errors, report at end
- **MEDIUM errors:** Log warnings, attempt to recover
- **LOW errors:** Info-level messages, continue silently

**Error Message Structure:**

```typescript
interface SensorMLParsingError {
  code: string; // ERR-SML-###
  severity: 'error' | 'warning' | 'info';
  message: string; // Human-readable description
  path?: string; // JSON path to error location (e.g., "components[2].uniqueId")
  line?: number; // Line number (for JSON syntax errors)
  column?: number; // Column number (for JSON syntax errors)
  specReference?: string; // Relevant spec section (e.g., "SensorML 3.0, §7.2")
}
```

---

## 7. Specification Example Fixtures

| Spec Section                   | Example Type       | Structure Type    | Complexity | Usable as Fixture | Source Location    | Notes                                                                   |
| ------------------------------ | ------------------ | ----------------- | ---------- | ----------------- | ------------------ | ----------------------------------------------------------------------- |
| **CSAPI Part 1 Annex B**       |
| Part 1, Annex B.1              | Complete system    | PhysicalSystem    | Simple     | ✅ Yes            | Part 1, Example 47 | Basic weather station with identification, classification, capabilities |
| Part 1, Annex B.2              | Composite system   | PhysicalSystem    | Complex    | ✅ Yes            | Part 1, Example 48 | Weather station with 3 components (thermometer, barometer, anemometer)  |
| Part 1, Annex B.3              | Individual sensor  | PhysicalComponent | Medium     | ✅ Yes            | Part 1, Example 49 | Temperature sensor with characteristics and capabilities                |
| **SensorML 3.0 Specification** |
| SensorML 3.0, §8.2             | Physical system    | PhysicalSystem    | Medium     | ✅ Yes            | SensorML 3.0 spec  | System with inputs, outputs, parameters                                 |
| SensorML 3.0, §8.3             | Composite system   | PhysicalSystem    | Complex    | ✅ Yes            | SensorML 3.0 spec  | System with components and connections                                  |
| SensorML 3.0, §8.4             | Physical component | PhysicalComponent | Simple     | ✅ Yes            | SensorML 3.0 spec  | Individual sensor                                                       |
| SensorML 3.0, §7.4             | Simple process     | SimpleProcess     | Simple     | ✅ Yes            | SensorML 3.0 spec  | Algorithm/computation                                                   |
| SensorML 3.0, §7.5             | Aggregate process  | AggregateProcess  | Medium     | ✅ Yes            | SensorML 3.0 spec  | Processing workflow                                                     |

**Total Spec Examples:** 8 usable fixtures

**Fixture Extraction Strategy:**

1. Copy examples verbatim from specification documents
2. Add provenance metadata (source, spec section, URL)
3. Validate against SensorML 3.0 JSON schema
4. Create test cases that parse and validate each fixture
5. Document expected property values for assertions

**Example Fixture Format:**

```json
{
  "_fixture_metadata": {
    "name": "weather-station-simple",
    "description": "Basic weather station from CSAPI Part 1, Annex B, Example 47",
    "source": "CSAPI Part 1 (OGC 23-001)",
    "spec_section": "Annex B.1",
    "spec_url": "https://docs.ogc.org/is/23-001/23-001.html#annex-b",
    "structure_type": "PhysicalSystem",
    "complexity": "simple",
    "nesting_level": 0,
    "has_components": false,
    "has_characteristics": true,
    "has_capabilities": true
  },
  "type": "PhysicalSystem",
  "uniqueId": "urn:x-ogc:def:sensor:station01",
  "definition": "http://www.w3.org/ns/sosa/Platform",
  "label": "Weather Station 01",
  ...
}
```

---

## 8. OpenSensorHub Fixture Inventory

> **⚠️ REVIEW NOTICE (Phase 2D, C2 / H2):** This section plans to source fixtures from the OpenSensorHub demo server (`https://api.georobotix.io/ogc/t18/api`) — this is anti-pattern AP2 (Hybrid Fixture/Live). Upstream tests use no live server dependencies; fixtures are static files versioned with the code. **Do not fetch fixtures from live servers.** If spec examples are insufficient, create realistic fixtures manually based on spec schemas. The two-tier assertion strategy ("Spec examples: MUST pass" vs "OpenSensorHub examples: SHOULD handle gracefully") should also not be used — all fixtures should have the same assertion rigor.
>
> The analysis strategy below is retained as reference for understanding real-world SensorML complexity, but should NOT drive fixture sourcing.

**OpenSensorHub Demo Server (REFERENCE ONLY — do not use for fixture sourcing):** https://api.georobotix.io/ogc/t18/api

| Resource URL                              | Structure Type                      | Complexity | Issues Found | Usable | Priority     | Notes                        |
| ----------------------------------------- | ----------------------------------- | ---------- | ------------ | ------ | ------------ | ---------------------------- |
| **Systems Endpoints**                     |
| `/systems`                                | PhysicalSystem collection           | Varies     | TBD          | Yes    | HIGH         | List of real-world systems   |
| `/systems/{id}`                           | PhysicalSystem or PhysicalComponent | Varies     | TBD          | Yes    | HIGH         | Individual system details    |
| `/systems/{id}?f=application/sml+json`    | PhysicalSystem (SensorML)           | High       | TBD          | Yes    | **CRITICAL** | Full SensorML representation |
| **Procedures Endpoints**                  |
| `/procedures`                             | SimpleProcess collection            | Low-Medium | TBD          | Yes    | MEDIUM       | List of procedures           |
| `/procedures/{id}?f=application/sml+json` | SimpleProcess (SensorML)            | Medium     | TBD          | Yes    | MEDIUM       | Procedure methodologies      |

**OpenSensorHub Analysis Strategy:**

1. **Fetch sample systems** from `/systems` endpoint (limit=10)
2. **Request SensorML format** via Accept header (`application/sml+json`)
3. **Analyze structure complexity**:
   - Count components (nesting depth)
   - Check for characteristics/capabilities
   - Identify SWE Common usage
   - Look for non-standard extensions
4. **Document issues**:
   - Missing required properties
   - Invalid property values
   - Non-standard extensions
   - Validation failures
5. **Categorize by usability**:
   - **Fully usable:** Valid, representative, good coverage
   - **Partially usable:** Minor issues, can be hand-fixed
   - **Not usable:** Major issues, use as negative test case
6. **Select representative samples** (5-10 systems) covering:
   - Simple systems (weather stations, buoys)
   - Complex systems (satellites, platforms with many sensors)
   - Various component counts (0, 1-3, 4-10, 10+ components)
   - Different domains (environmental, oceanographic, atmospheric)

**Expected OpenSensorHub Findings:**

- **Real-world complexity:** More complex than spec examples (10-20 components common)
- **Non-standard properties:** Custom extensions beyond SensorML 3.0 spec
- **Missing optional properties:** Real systems often omit documentation, contacts
- **Validation issues:** Some systems may not fully conform to spec
- **Performance implications:** Large component trees require efficient parsing

**Fixture Sourcing Strategy (CORRECTED per Phase 2D):**

- **Spec examples:** Primary fixture source — extract from CSAPI Part 1 Annex B and SensorML 3.0 spec
- **Hand-crafted fixtures:** Secondary source — create realistic fixtures for edge cases, error scenarios, and nesting depths not covered by spec examples
- ~~**OpenSensorHub examples:** Real-world validation (SHOULD handle gracefully)~~ → Do not source fixtures from live servers
- **Assertion rigor:** All fixtures receive the same assertion treatment — no two-tier MUST/SHOULD distinction

---

## 9. Test Organization

### Test File Structure

**File:** `tests/csapi/formats/sensorml.spec.ts`  
**Estimated Lines:** 500-800 lines

**Describe Block Structure:**

```typescript
describe('SensorML 3.0 Parser', () => {
  describe('PhysicalSystem Parsing', () => {
    describe('Core Properties', () => {
      it('should parse simple PhysicalSystem from spec example');
      it('should extract type, uniqueId, definition, label');
      it('should parse validTime as ISO 8601 interval');
      it('should parse optional description');
      it('should parse optional id property');
    });

    describe('Identification and Classification', () => {
      it('should parse identifiers array');
      it('should parse identifier Terms with definition, label, value');
      it('should parse classifiers array');
      it('should parse classifier Terms with systemType vocabulary');
    });

    describe('Characteristics and Capabilities', () => {
      it('should parse characteristics as CharacteristicList');
      it('should extract characteristic DataRecord structure');
      it('should parse capabilities as CapabilityList');
      it('should extract capability DataRecord structure');
    });

    describe('Components and Nesting', () => {
      it('should parse components array');
      it('should parse component with name and href');
      it('should parse 1-level component hierarchy');
      it('should parse 2-level component hierarchy');
      it('should parse 3-level component hierarchy');
      it('should handle inline component objects');
      it('should handle external component references');
    });

    describe('Connections', () => {
      it('should parse connections array');
      it('should parse connection source and destination refs');
      it('should validate connection refs point to valid components');
    });

    describe('Process Metadata', () => {
      it('should parse inputs array');
      it('should parse outputs array');
      it('should parse parameters array');
      it('should extract SWE Common component definitions from IO');
    });

    describe('Additional Metadata', () => {
      it('should parse contacts array');
      it('should parse documentation array');
      it('should parse links array');
      it('should parse position (Point or Pose)');
      it('should parse attachedTo link');
    });
  });

  describe('PhysicalComponent Parsing', () => {
    it('should parse simple PhysicalComponent from spec example');
    it('should extract type, uniqueId, definition, label');
    it('should parse component characteristics');
    it('should parse component capabilities (measurement specs)');
    it('should parse attachedTo parent reference');
    it('should parse component position');
    it('should parse method (measurement methodology)');
  });

  describe('SimpleProcess Parsing', () => {
    it('should parse simple SimpleProcess');
    it('should extract type, uniqueId, definition, label');
    it('should parse method (algorithm description)');
    it('should parse process inputs/outputs/parameters');
  });

  describe('AggregateProcess Parsing', () => {
    it('should parse AggregateProcess with components');
    it('should extract type, uniqueId, definition, label');
    it('should parse component processes array');
    it('should parse connections between components');
    it('should validate connection source/destination refs');
    it('should parse aggregate inputs/outputs/parameters');
  });

  describe('Validation Rules', () => {
    it(
      'should enforce required properties (type, uniqueId, definition, label)'
    );
    it('should validate uniqueId is valid URI');
    it('should validate definition is valid URI');
    it('should validate type is known SensorML type');
    it('should validate validTime ISO 8601 format');
    it('should validate validTime start <= end');
    it('should validate systemType from vocabulary (if present)');
    it('should validate component names are unique');
  });

  describe('Error Handling', () => {
    it('should error on malformed JSON');
    it('should error on missing required property: type');
    it('should error on missing required property: uniqueId');
    it('should error on missing required property: definition');
    it('should error on missing required property: label');
    it('should error on invalid URI format (uniqueId)');
    it('should error on invalid type value');
    it('should error on invalid validTime format');
    it('should error on missing component href');
    it('should error on invalid component reference');
  });

  describe('Recursive Structure Handling', () => {
    it('should handle system with no components (Level 0)');
    it('should handle system with 3 components (Level 1)');
    it('should handle 2-level component nesting');
    it('should handle 3-level component nesting');
    it('should detect circular references (system references itself)');
    it('should handle missing external component references gracefully');
  });

  describe('SWE Common Integration', () => {
    it('should extract characteristics DataRecord structure');
    it('should extract capabilities DataRecord structure');
    it('should extract input/output SWE Common component definitions');
    it('should handle complex nested DataRecords in characteristics');
    it('should handle QuantityRange in capabilities');
  });

  describe('Real-World Examples (OpenSensorHub)', () => {
    it('should parse real weather station system');
    it('should parse real satellite platform system');
    it('should handle non-standard extensions gracefully');
    it('should parse complex systems with 10+ components');
  });
});
```

**Test Count Estimate:** 46-57 tests

---

## 10. Test Depth Definition

### "Meaningful" SensorML Test Characteristics

**✅ DO (Comprehensive Testing):**

1. **Parse Complete Fixtures**

   - Use real spec examples or OpenSensorHub data
   - Validate ALL extracted properties (not just presence)
   - Check property types, formats, constraints

2. **Validate Nested Structures**

   - Parse components array completely
   - Verify characteristics/capabilities DataRecord structure
   - Extract all identifiers/classifiers

3. **Test Recursive Parsing**

   - Test 1-3 levels of component nesting
   - Use realistic component counts (3-10 components per level)
   - Verify parent-child relationships maintained

4. **Strict URI Validation**

   - Validate uniqueId format (absolute URI, preferably URN)
   - Validate definition format (valid ontology URI)
   - Check all href properties

5. **SWE Common Integration**

   - Verify characteristics/capabilities structures extracted
   - Coordinate with Section 10 tests
   - Test with shared SWE Common fixtures

6. **Error Conditions with Clear Assertions**

   - Test all CRITICAL/HIGH error scenarios
   - Verify error messages include context (JSON path, property name)
   - Check error severity levels

7. **Use Specification Examples**
   - Prioritize examples from CSAPI Part 1, Annex B
   - Use SensorML 3.0 specification examples
   - Supplement with OpenSensorHub real-world data

**❌ DON'T (Trivial Testing):**

1. **Just Check Existence**

   - `expect(result).toBeDefined()` - too weak
   - `expect(result.uniqueId).toBeTruthy()` - no validation

2. **Skip Nested Structure Validation**

   - Not checking component array contents
   - Not validating characteristics/capabilities structure

3. **Use Overly Simple Fixtures**

   - Hand-crafted minimal JSON without realistic properties
   - Fixtures with only 1-2 properties

4. **Test Only Happy Path**

   - No error condition testing
   - No edge case testing (empty arrays, missing optional properties)

5. **Shallow Property Checks**

   - Only checking first level of nesting
   - Not validating nested DataRecords

6. **Ignore SWE Common Integration**
   - Not testing characteristics/capabilities parsing
   - Not coordinating with Section 10 tests

**Test Quality Criteria:**

| Criterion               | Meaningful Test                     | Trivial Test              |
| ----------------------- | ----------------------------------- | ------------------------- |
| **Fixture Quality**     | Spec examples or OpenSensorHub data | Hand-crafted minimal JSON |
| **Property Validation** | Type, format, constraints checked   | Just existence check      |
| **Nesting Depth**       | 2-3 levels tested                   | Only flat structures      |
| **Error Coverage**      | 15+ error scenarios                 | Only happy path           |
| **SWE Integration**     | Characteristics/capabilities parsed | Ignored or minimal        |
| **Component Count**     | 3-10 components tested              | 0-1 components            |
| **Assertions per Test** | 5-15 assertions                     | 1-3 assertions            |

---

## 11. Fixture Requirements

### Fixture Directory Structure

```
fixtures/sensorml/
├── spec-examples/               # From CSAPI Part 1 Annex B
│   ├── weather-station-simple.json
│   ├── weather-station-composite.json
│   ├── temperature-sensor.json
│   └── sensorml30-examples.json
├── physical-systems/
│   ├── weather-station-01.json
│   ├── uav-platform-01.json
│   ├── ocean-buoy-01.json
│   ├── satellite-platform-01.json
│   └── vehicle-sensor-system-01.json
├── physical-components/
│   ├── thermometer-01.json
│   ├── camera-01.json
│   ├── gps-receiver-01.json
│   └── accelerometer-01.json
├── simple-processes/
│   ├── data-processing-algorithm.json
│   └── simulation-model.json
├── aggregate-processes/
│   ├── processing-workflow-01.json
│   ├── sensor-fusion-process.json
│   └── qa-qc-pipeline.json
├── composite-systems/
│   ├── 1-level-nesting.json       # System → 3 components
│   ├── 2-level-nesting.json       # System → Component → Subcomponent
│   ├── 3-level-nesting.json       # System → ... → Sub-subcomponent
│   └── mixed-inline-external.json # Inline + external refs
├── error-cases/
│   ├── missing-uniqueid.json
│   ├── invalid-uri.json
│   ├── malformed-json.txt
│   ├── unknown-type.json
│   ├── circular-reference.json
│   ├── missing-component-ref.json
│   └── invalid-validtime.json
└── opensensorhub/
    ├── real-weather-station.json
    ├── real-satellite.json
    └── real-ocean-buoy.json
```

**Total Fixtures:** ~27 fixtures

### Required Fixtures by Category

| Category           | Count | Purpose                                      | Priority     |
| ------------------ | ----- | -------------------------------------------- | ------------ |
| Spec Examples      | 3-4   | Normative baseline from CSAPI Part 1 Annex B | **CRITICAL** |
| PhysicalSystems    | 5     | Various domains, complexity levels           | HIGH         |
| PhysicalComponents | 4     | Individual sensors/actuators                 | MEDIUM       |
| SimpleProcesses    | 2     | Algorithms, simulations                      | LOW          |
| AggregateProcesses | 3     | Processing workflows                         | MEDIUM       |
| Composite Systems  | 4     | Nesting levels 1-3, mixed patterns           | HIGH         |
| Error Cases        | 7     | Malformed, missing props, invalid values     | HIGH         |
| OpenSensorHub      | 3     | Real-world validation                        | MEDIUM       |

**Fixture Metadata (in each file):**

```json
{
  "_fixture_metadata": {
    "name": "fixture-name",
    "description": "Brief description",
    "source": "CSAPI Part 1 | SensorML 3.0 | OpenSensorHub | Hand-crafted",
    "spec_section": "Section reference (if applicable)",
    "structure_type": "PhysicalSystem | PhysicalComponent | SimpleProcess | AggregateProcess",
    "complexity": "simple | medium | complex",
    "nesting_level": 0 | 1 | 2 | 3,
    "has_components": true | false,
    "has_characteristics": true | false,
    "has_capabilities": true | false,
    "test_purpose": "What this fixture tests"
  },
  ...actual SensorML document...
}
```

---

## 12. Validation Against Upstream Patterns

**Comparison with Section 1-2 Findings (EDR Client Tests):**

| Aspect                | EDR Client Pattern                                | SensorML Parser Plan                             | Alignment                           |
| --------------------- | ------------------------------------------------- | ------------------------------------------------ | ----------------------------------- |
| **Test Organization** | Single spec file per resource type                | Single spec file for all SensorML types          | ✅ Aligned - complexity appropriate |
| **Fixture Usage**     | Real EDR server responses                         | Spec examples + OpenSensorHub data               | ✅ Aligned - similar priority       |
| **Test Depth**        | Parse complete responses, validate all properties | Parse complete SensorML, validate all properties | ✅ Aligned - comprehensive          |
| **Error Handling**    | Test malformed responses, missing properties      | Test malformed JSON, missing required properties | ✅ Aligned - thorough               |
| **Nesting**           | N/A (flat responses)                              | Test 1-3 levels of component nesting             | ⚠️ Additional - unique to SensorML  |
| **Integration**       | EDR collections → EDR queries                     | SensorML → SWE Common parsing                    | ✅ Aligned - similar pattern        |
| **Performance**       | Not explicitly tested                             | Not priority (focus on correctness)              | ✅ Aligned - correctness first      |
| **Test Count**        | ~30-40 tests per resource                         | ~46-57 tests total                               | ✅ Aligned - similar density        |

**Upstream Quality Standards Met:**

- ✅ Real fixtures prioritized over hand-crafted
- ✅ Comprehensive property validation (not just existence)
- ✅ Error conditions thoroughly tested
- ✅ Integration points with other components identified
- ✅ Test organization follows upstream pattern

**SensorML-Specific Additions:**

- Recursive component parsing (unique to SensorML hierarchies)
- Circular reference detection (not in EDR)
- SWE Common integration (coordination with Section 10)
- Nesting depth testing (not applicable to EDR)

---

## 13. Integration with Implementation Guide

**Cross-Validation with Implementation Guide SensorML Parser Specification:**

| Aspect                     | Implementation Guide                                                                                                                                                              | This Test Plan                                                          | Status                                                |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------- |
| **Parser Scope**           | Parse SimpleProcess, AggregateProcess, PhysicalComponent, PhysicalSystem                                                                                                          | Test PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess | ✅ Aligned                                            |
| **SensorML Elements**      | Identification, classification, characteristics, capabilities, contacts, documentation, featuresOfInterest, inputs, outputs, parameters, modes, components, connections, position | All covered in property matrices                                        | ✅ Aligned                                            |
| **Recursive Parsing**      | Nested PhysicalSystems with full component hierarchy                                                                                                                              | Test 1-3 levels of nesting                                              | ✅ Aligned                                            |
| **SWE Common Integration** | Complete parsing of all DataComponent types                                                                                                                                       | Integration tests with Section 10                                       | ✅ Aligned                                            |
| **Unit of Measure**        | UCUM code support                                                                                                                                                                 | Test via SWE Common integration                                         | ✅ Aligned                                            |
| **Reference Resolution**   | External link dereferencing                                                                                                                                                       | Test external component references                                      | ✅ Aligned                                            |
| **Position Parsing**       | GeoJSON geometry plus orientation                                                                                                                                                 | Test position property (defer complex to geometry parser)               | ⚠️ Partial - complex orientation deferred             |
| **Mode/Configuration**     | Operational modes with state definitions                                                                                                                                          | Not prioritized in initial tests                                        | ⚠️ Gap - LOW priority, document as future enhancement |
| **Connection Graphs**      | Component connection mapping                                                                                                                                                      | Test connections array, source/destination validation                   | ✅ Aligned                                            |
| **Vocabulary Resolution**  | Automatic fetching from code spaces                                                                                                                                               | Not in initial scope                                                    | ⚠️ Gap - MEDIUM priority, document as enhancement     |

**Alignment Status:**

- ✅ **Fully Aligned (10 items):** Core parsing, SWE Common integration, recursive components, connections
- ⚠️ **Partial Alignment (2 items):** Complex position/orientation parsing (defer to specialized parser), mode/configuration (LOW priority)
- ⚠️ **Gaps Identified (1 item):** Vocabulary resolution (MEDIUM priority enhancement)

**Recommendations:**

1. **Initial Implementation:** Focus on CRITICAL/HIGH priority items (fully aligned with Implementation Guide core requirements)
2. **Phase 2 Enhancements:** Add mode/configuration parsing (optional SensorML features)
3. **Phase 3 Enhancements:** Add vocabulary resolution (automatic dereferencing)
4. **Coordinate with Geometry Parser:** Complex position/orientation parsing (Pose with quaternions/euler angles)

**Implementation Guide Updates Needed:**

- Document test strategy for SensorML parser
- Add fixture requirements to Implementation Guide
- Note LOW priority items (modes, complex position) for future phases
- Add vocabulary resolution as enhancement (not blocking)

---

## 14. Testing Estimates

| Test Category                 | Test Count | Lines per Test | Total Lines | Time Estimate (Implementation) | Priority     |
| ----------------------------- | ---------- | -------------- | ----------- | ------------------------------ | ------------ |
| **PhysicalSystem Parsing**    | 12-15      | 12-15          | 150-225     | 2-3 hours                      | **CRITICAL** |
| Core properties               | 5          | 10-12          | 50-60       | 30-45 min                      | CRITICAL     |
| Identification/classification | 3          | 12-15          | 36-45       | 30-45 min                      | HIGH         |
| Characteristics/capabilities  | 2          | 15-20          | 30-40       | 45-60 min                      | HIGH         |
| Components/nesting            | 4          | 15-20          | 60-80       | 60-90 min                      | CRITICAL     |
| **PhysicalComponent Parsing** | 8-10       | 10-12          | 80-120      | 1-2 hours                      | HIGH         |
| Core properties               | 5          | 10-12          | 50-60       | 30-45 min                      | HIGH         |
| Characteristics/capabilities  | 3          | 10-12          | 30-36       | 30-45 min                      | HIGH         |
| **SimpleProcess Parsing**     | 5-6        | 10-12          | 50-72       | 1 hour                         | MEDIUM       |
| Core properties               | 3          | 10-12          | 30-36       | 20-30 min                      | MEDIUM       |
| Process IO                    | 2-3        | 10-12          | 20-36       | 30-45 min                      | LOW          |
| **AggregateProcess Parsing**  | 8-10       | 10-15          | 80-150      | 1-2 hours                      | HIGH         |
| Core properties               | 3          | 10-12          | 30-36       | 20-30 min                      | HIGH         |
| Components/connections        | 5-7        | 10-15          | 50-105      | 60-90 min                      | HIGH         |
| **Validation Rules**          | 8-10       | 8-10           | 64-100      | 1 hour                         | HIGH         |
| URI validation                | 3          | 8-10           | 24-30       | 20-30 min                      | CRITICAL     |
| Type validation               | 2          | 8-10           | 16-20       | 15-20 min                      | HIGH         |
| Temporal validation           | 2          | 8-10           | 16-20       | 15-20 min                      | MEDIUM       |
| Component validation          | 1-3        | 8-10           | 8-30        | 15-30 min                      | MEDIUM       |
| **Error Handling**            | 8-10       | 8-10           | 64-100      | 1 hour                         | HIGH         |
| Malformed JSON                | 2          | 8-10           | 16-20       | 15-20 min                      | MEDIUM       |
| Missing properties            | 4          | 8-10           | 32-40       | 20-30 min                      | HIGH         |
| Invalid values                | 4          | 8-10           | 32-40       | 20-30 min                      | HIGH         |
| **Recursive Structures**      | 5-6        | 15-20          | 75-120      | 1-2 hours                      | HIGH         |
| Level 0-1                     | 2          | 12-15          | 24-30       | 20-30 min                      | CRITICAL     |
| Level 2-3                     | 2          | 15-20          | 30-40       | 30-45 min                      | HIGH         |
| Circular refs                 | 1-2        | 15-20          | 15-40       | 30-45 min                      | MEDIUM       |
| **SWE Common Integration**    | 4-5        | 12-15          | 48-75       | 1 hour                         | HIGH         |
| **Real-World Examples**       | 3-4        | 10-12          | 30-48       | 1 hour                         | MEDIUM       |
| **TOTAL**                     | **46-57**  | **~12 avg**    | **499-787** | **7-11 hours**                 | -            |

**Phased Implementation Plan:**

**Phase 1 (CRITICAL - 3-4 hours):**

- PhysicalSystem core parsing (5 tests)
- Component nesting Level 0-1 (2 tests)
- URI validation (3 tests)
- Basic error handling (4 tests)
- **Deliverable:** 14 tests, ~150 lines

**Phase 2 (HIGH - 3-4 hours):**

- PhysicalComponent parsing (8-10 tests)
- AggregateProcess parsing (8-10 tests)
- Recursive structures Level 2-3 (2 tests)
- SWE Common integration (4-5 tests)
- **Deliverable:** 22-27 tests, ~250 lines

**Phase 3 (MEDIUM - 2-3 hours):**

- SimpleProcess parsing (5-6 tests)
- Advanced error handling (4 tests)
- Real-world examples (3-4 tests)
- **Deliverable:** 12-14 tests, ~150 lines

**Phase 4 (LOW - Optional):**

- Contacts/documentation parsing
- Complex position/orientation
- Performance testing
- **Deliverable:** TBD

---

## 15. Testing Priorities

### CRITICAL (Must Have - Phase 1)

**What:**

- PhysicalSystem parsing (most common structure type)
- Component nesting (Levels 0-1)
- uniqueIdentifier validation (URI format)
- Basic error handling (malformed JSON, missing required properties)

**Why Critical:**

- PhysicalSystem is primary representation for sensors, platforms, weather stations
- Component parsing enables subsystem navigation (key CSAPI feature)
- URI validation enforces CSAPI conformance (Part 1, Req 2)
- Error handling prevents silent failures

**Test Lines:** ~150 lines  
**Implementation Time:** 3-4 hours

---

### HIGH (Should Have - Phase 2)

**What:**

- PhysicalComponent parsing
- AggregateProcess parsing
- Characteristics/capabilities parsing (SWE Common integration)
- All spec example coverage
- Recursive structures (Levels 2-3)

**Why High:**

- PhysicalComponent represents individual sensors referenced by systems
- AggregateProcess enables composite processing workflows
- Characteristics/capabilities critical for measurement specifications
- Spec examples are normative baseline
- Level 2-3 nesting covers real-world platforms (e.g., satellites)

**Test Lines:** ~250 lines  
**Implementation Time:** 3-4 hours

---

### MEDIUM (Nice to Have - Phase 3)

**What:**

- SimpleProcess parsing (less common for physical systems)
- Deep nesting (3+ levels)
- Advanced error conditions (circular refs, orphan connections)
- OpenSensorHub real-world examples

**Why Medium:**

- SimpleProcess more common for procedures than systems
- Deep nesting (4+ levels) rare in practice
- Advanced errors edge cases (unlikely but possible)
- OpenSensorHub validates real-world handling (nice validation, not baseline)

**Test Lines:** ~150 lines  
**Implementation Time:** 2-3 hours

---

### LOW (Optional - Phase 4+)

**What:**

- Contacts/documentation parsing
- Position/location parsing (complex Pose with orientation)
- Modes/configuration parsing
- Performance testing (large component trees)

**Why Low:**

- Contacts/documentation rarely used for discovery/querying
- Complex position parsing can be deferred to specialized geometry parser
- Modes/configuration advanced SensorML feature (optional)
- Performance optimization after correctness established

**Test Lines:** TBD (not in initial 500-800 estimate)  
**Implementation Time:** TBD (future enhancement)

---

## 16. Risks and Edge Cases

| Risk/Edge Case                             | Likelihood | Impact | Mitigation Strategy                                                                 | Priority |
| ------------------------------------------ | ---------- | ------ | ----------------------------------------------------------------------------------- | -------- |
| **Deep Recursion Stack Overflow**          | Medium     | High   | Limit nesting depth to 5 levels; use iterative parsing with explicit depth tracking | HIGH     |
| **Circular References**                    | Low        | Medium | Track visited component IDs during traversal; detect loops; error gracefully        | MEDIUM   |
| **Very Large Component Lists**             | Low        | Low    | Test with realistic counts (10-20 components); document performance limits          | LOW      |
| **Non-Standard Extensions**                | High       | Medium | Parse core properties; ignore unknown properties; log warnings                      | HIGH     |
| **OpenSensorHub Data Issues**              | High       | Medium | Prioritize spec examples for baseline; use OpenSensorHub for validation only        | MEDIUM   |
| **SWE Common Parsing Failures**            | Medium     | High   | Robust error handling; clear error messages; coordinate with Section 10             | HIGH     |
| **External Component Resolution**          | Low        | Medium | Test with external hrefs; handle network errors gracefully                          | MEDIUM   |
| **Missing Component References**           | Medium     | Medium | Validate component hrefs; error clearly with component name and path                | MEDIUM   |
| **Malformed Characteristics/Capabilities** | Medium     | High   | Validate DataRecord structure; handle parsing errors; provide clear messages        | HIGH     |
| **Invalid URI Formats**                    | Medium     | High   | Strict URI validation; reject relative URIs; clear error messages                   | HIGH     |
| **Temporal Validation Complexity**         | Low        | Low    | Support open intervals (null); validate ISO 8601; handle various formats            | MEDIUM   |

**Mitigation Priorities:**

1. **Stack overflow prevention** (iterative parsing, depth limits)
2. **SWE Common integration** (robust error handling, coordination)
3. **Non-standard extensions** (ignore gracefully, core properties only)
4. **Invalid URI formats** (strict validation, clear errors)
5. **Circular references** (detection, graceful errors)

**Testing Strategy for Each Risk:**

- **Deep recursion:** Create 4-5 level nesting fixture, verify no stack overflow
- **Circular refs:** Hand-craft self-referencing system, verify detection
- **Large component lists:** Use realistic fixtures (10-20 components), measure parse time
- **Non-standard extensions:** Use OpenSensorHub data with custom properties
- **SWE Common failures:** Inject malformed DataRecords, verify error handling
- **External refs:** Mock network failures, verify graceful degradation
- **Missing refs:** Create fixture with broken hrefs, verify error messages
- **Malformed characteristics:** Inject invalid DataRecord structures, verify validation
- **Invalid URIs:** Test various invalid URI formats, verify rejection
- **Temporal validation:** Test open intervals, various ISO 8601 formats

---

## 17. Summary and Next Steps

### Research Summary

> **⚠️ REVIEW NOTICE (Phase 2D, C2):** This document was reclassified in Phase 2D review. The findings below are accurate as specification analysis, but the testing framework (VAL-SML/ERR-SML IDs, enforcement levels, OpenSensorHub fixture sourcing) must not be used as-is for client parser tests. **Before implementing tests, define the parser's TypeScript output interface** — what does `parseSensorML()` return? Tests should be `parseSensorML(fixture) → expectedTypedObject`, not specification conformance checks.

**Completed:**

- ✅ All 4 SensorML structure types analyzed (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess)
- ✅ All specification validation rules documented (21 rules from CSAPI Part 1 and SensorML 3.0) — **use as input reference, not test IDs**
- ✅ Recursive structure testing strategy defined (1-3 levels, circular reference detection)
- ✅ Fixture inventory complete (~24 fixtures: 3-4 spec examples, ~20 hand-crafted) — **OpenSensorHub fixtures removed per AP2 correction**
- ✅ Test depth defined meeting "meaningful" criteria (comprehensive property extraction, nested structures, error conditions)
- ✅ Error handling requirements specified (subset of 22 scenarios — **only structurally unparseable inputs should cause errors**)
- ✅ SWE Common integration points identified (characteristics, capabilities, inputs/outputs/parameters)
- ✅ Test organization documented (single spec file, ~46-57 tests, 500-800 lines)
- ✅ Validated against upstream patterns (aligned with EDR client test approach)
- ✅ Cross-validated with Implementation Guide (aligned with parser specification)
- ✅ All 80 research questions answered

**Testing Priorities Established:**

- **CRITICAL:** PhysicalSystem parsing, component nesting (Levels 0-1), URI validation, basic error handling
- **HIGH:** PhysicalComponent, AggregateProcess, characteristics/capabilities, spec example coverage
- **MEDIUM:** SimpleProcess, deep nesting (3+ levels), advanced errors, OpenSensorHub examples
- **LOW:** Contacts/documentation, complex position, modes/configuration

**Estimated Implementation:**

- **Total Test Lines:** 500-800 lines
- **Total Implementation Time:** 7-11 hours
- **Phase 1 (CRITICAL):** ~150 lines, 3-4 hours
- **Phase 2 (HIGH):** ~250 lines, 3-4 hours
- **Phase 3 (MEDIUM):** ~150 lines, 2-3 hours

### Answers to All Research Questions

**SensorML 3.0 Specification Analysis (Questions 1-10):**

1. **Structure types:** PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess
2. **Mandatory vs optional:** Core (type, uniqueId, definition, label) required; all else optional
3. **Normative rules:** 21 rules documented in Section 3
4. **Recursive structures:** Components array allows nesting; depth unbounded but test 1-3 levels
5. **System type distinctions:** Physical* for hardware, *Process for software/simulations
6. **Nesting depth:** Unbounded in spec; recommend 5-level limit to prevent stack overflow
7. **Identifier rules:** uniqueId must be valid URI (preferably URN); identifiers array optional
8. **Classifier/characteristic structures:** Arrays of Terms (definition, label, value) and CharacteristicLists (with SWE Common DataRecords)
9. **Temporal validity:** validTime as ISO 8601 interval [start, end]; null for open intervals
10. **Reference resolution:** External hrefs via URI; inline components as objects

**JSON Schema Validation Rules (Questions 11-18):** 11. **Schema rules:** Type constraints, required properties, format constraints (URI, datetime) 12. **Format constraints:** URI format for uniqueId/definition; ISO 8601 for validTime 13. **Enumeration constraints:** systemType from vocabulary (Table 6); SWE Common component types 14. **Required vs optional:** All structure types require type, uniqueId, definition, label 15. **Array constraints:** None specified (components, identifiers, classifiers can be empty) 16. **Nested object constraints:** Components must have name + (href | inline object) 17. **Schema variations:** No - same base structure for all types 18. **Parser enforcement:** MUST enforce required properties, URI formats; SHOULD validate vocabulary values

**SensorML Structure Types (Questions 19-25):** 19. **PhysicalSystem:** Full parsing, components, nesting, characteristics/capabilities 20. **PhysicalComponent:** Full parsing, attachedTo, characteristics/capabilities (measurement specs) 21. **SimpleProcess:** Basic parsing, method, inputs/outputs/parameters 22. **AggregateProcess:** Full parsing, components, connections (data flow) 23. **Testing differences:** PhysicalSystem CRITICAL (most common); PhysicalComponent HIGH; others MEDIUM 24. **Shared properties:** type, uniqueId, definition, label, description, identifiers, classifiers, validTime 25. **Type-specific:** components/connections (composite types); attachedTo/position (physical types); method (process types)

**Identification and Classification (Questions 26-31):** 26. **Identification testing:** Parse identifiers array, validate Terms (definition, label, value) 27. **Identifier types:** Short name, serial number, model number, manufacturer part number 28. **Classification testing:** Parse classifiers array, validate Terms 29. **Classifier types:** Sensor type, actuator type, platform type, intended application 30. **uniqueIdentifier validation:** Strict URI format, preferably URN, reject relative URIs 31. **Label/name validation:** Required non-empty string

**Characteristics and Capabilities (Questions 32-36):** 32. **Characteristics testing:** Parse CharacteristicList, extract DataRecord structure 33. **Capabilities testing:** Parse CapabilityList, extract DataRecord structure 34. **SWE Common parsing level:** Extract structure, pass to SWE Common parser for deep parsing 35. **Fully parse vs validate:** Extract structure in SensorML parser; deep parse in SWE Common parser (Section 10) 36. **Integration tests:** Test with shared fixtures; coordinate error handling; lazy parsing option

**Components and Recursive Structures (Questions 37-42):** 37. **Component lists testing:** Parse components array, validate name + href/inline object 38. **Nesting depth:** Test 1-3 levels (realistic); document 5-level limit 39. **Recursive edge cases:** Circular references, missing refs, deep nesting (4+ levels) 40. **Circular references:** Track visited IDs; detect loops; error gracefully with clear message 41. **Missing component refs:** Validate hrefs; error with component name and path context 42. **Performance with deep nesting:** Test realistic counts (10-20 components); iterative parsing to prevent stack overflow

**Temporal Validity (Questions 43-46):** 43. **validTime testing:** Parse ISO 8601 interval [start, end] 44. **Temporal formats:** ISO 8601 instants and intervals; support open intervals (null) 45. **Interval vs instant:** Support both; validate start <= end for closed intervals 46. **Edge cases:** Open intervals (null start/end), single instant (start = end), invalid formats

**Observable Properties (Questions 47-50):** 47. **observableProperty testing:** Parse inputs/outputs arrays, extract SWE Common component definitions 48. **URI validation:** Validate definition URIs in input/output components 49. **Property definitions vs refs:** Both supported; definitions inline as SWE Common components; refs as URIs 50. **Integration with CSAPI properties:** CSAPI Property resources define semantics; SensorML inputs/outputs reference them

**Contacts and Documentation (Questions 51-54):** 51. **Contacts testing:** Parse contacts array, extract ResponsibleParty objects 52. **Documentation testing:** Parse documentation array, extract Document links 53. **Priority:** LOW - rarely used for discovery/querying 54. **Validation rules:** Validate structure, optional validation of hrefs

**Position and Location (Questions 55-58):** 55. **Position testing:** Parse position property (Point, Pose, Text, DataStream link) 56. **Geometry types:** Point (GeoJSON), Pose (position + orientation), Text, DataStream 57. **Validation depth:** Basic structure validation; defer complex Pose parsing to geometry parser 58. **CRS handling:** Support EPSG codes, default WGS84; coordinate with geometry parser

**Error Handling (Questions 59-64):** 59. **Error conditions:** 22 scenarios documented in Section 6 60. **Malformed SensorML:** JSON syntax errors, invalid structure 61. **Missing required properties:** type, uniqueId, definition, label 62. **Invalid property values:** Invalid URI formats, unknown types, invalid temporal formats 63. **Unsupported structure types:** Unknown type values, warn and attempt to parse common properties 64. **Error messages:** Include JSON path, property name, expected vs actual, spec reference

**Specification Examples (Questions 65-69):** 65. **Complete system examples:** CSAPI Part 1 Annex B (3-4 examples) 66. **Component examples:** SensorML 3.0 spec (various examples) 67. **Recursive structure examples:** CSAPI Part 1 Annex B.2 (weather station with 3 components) 68. **Edge case examples:** Limited in spec; hand-craft for errors, circular refs 69. **Extraction as fixtures:** Yes - all spec examples usable with provenance metadata

**OpenSensorHub Real-World Examples (Questions 70-74):** 70. **Examples available:** Systems, Procedures endpoints with `f=application/sml+json` 71. **Structure complexity:** Higher than spec (10-20 components common) 72. **Edge cases exposed:** Non-standard extensions, missing optional properties, validation issues 73. **Validation issues:** Expected - prioritize spec examples for baseline 74. **Supplement spec examples:** Yes - validate real-world handling, not normative baseline

**Parser Implementation Testing (Questions 75-80):** 75. **Parsing functions to unit test:** Structure type detection, property extraction, validation rules, component traversal 76. **Integration tests:** Full system parsing, SWE Common integration, recursive nesting 77. **Test organization:** Single spec file (~500-800 lines, ~46-57 tests) 78. **Test depth per structure type:** PhysicalSystem 12-15 tests; PhysicalComponent 8-10; SimpleProcess 5-6; AggregateProcess 8-10 79. **Fixtures per structure type:** PhysicalSystem 5-8; PhysicalComponent 3-5; SimpleProcess 2-3; AggregateProcess 3-4 80. **Balance:** Prioritize spec examples (normative); supplement with hand-crafted (edge cases); validate with OpenSensorHub (real-world)

### Next Steps

**Immediate (Implementation):**

1. **Define parser output TypeScript interface** — what does `parseSensorML()` return? This is the critical missing piece.
2. Create fixture directory structure (`fixtures/sensorml/`)
3. Extract spec examples from CSAPI Part 1 Annex B (3-4 fixtures)
4. Create hand-crafted fixtures (~20 fixtures covering all structure types, nesting levels, error cases) — **do not fetch from live servers**
5. Implement SensorML parser (coordinate with SWE Common parser design from Section 10)
6. Write Phase 1 tests as `parseSensorML(fixture) → expectedTypedObject` (CRITICAL - ~150 lines, 14 tests)

**Near-Term:** 7. Write Phase 2 tests (HIGH - ~250 lines, 22-27 tests) 8. Write Phase 3 tests (MEDIUM - ~150 lines, 12-14 tests) 9. Validate against all fixtures 10. Cross-validate with Section 10 (SWE Common parser tests) 11. Update Implementation Guide with fixture requirements and test strategy

**Long-Term:** 12. Phase 4 enhancements (LOW priority - contacts/documentation, complex position, modes/configuration) 13. Performance optimization (after correctness established) 14. Vocabulary resolution enhancement (automatic dereferencing)

### What This Unblocks

- ✅ **Section 10:** SWE Common 3.0 Format Testing (coordinate characteristics/capabilities fixtures and integration tests)
- ✅ **Section 12:** QueryBuilder URL Construction Testing (systems endpoint testing requires SensorML parsing)
- ✅ **Section 14:** Integration Test Workflow Design (system discovery workflow uses SensorML)
- ✅ **Section 15:** Fixture Sourcing Strategy (SensorML fixture inventory feeds overall fixture organization)
- ✅ **Section 36:** Test Quality Checklist (SensorML test validation criteria established)

**Research Status:** COMPLETE ✅  
**All Success Criteria Met:** ✅  
**Reclassified:** Parser output model must be defined before tests can be implemented (Phase 2D, C2)  
**Ready for Implementation:** After defining parser TypeScript output interface  
**Estimated Implementation Effort:** 7-11 hours across 3 phases
