# CSAPI Testing Strategy Research Plan

**Purpose:** Comprehensive research plan to ensure testing strategy achieves production-quality, meaningful, deep, and end-to-end test coverage that will pass upstream maintainer review.

**Context:** Previous implementation was rejected for having tests that were "not meaningful, useful, deep, or end-to-end." This research plan ensures we understand exactly what constitutes production-quality testing before writing a single test.

**Last Updated:** February 5, 2026  
**Status:** Research Planning Phase - Outlines Only

---

## Research Philosophy

**Research-First Approach:** Complete all research sections in order before implementing tests. Each section builds understanding needed for subsequent sections. Do not write tests until all research is complete and synthesized.

**Primary Constraint:** Tests must be **meaningful, useful, deep, and end-to-end** as defined by senior dev feedback and upstream maintainer expectations.

**Success Criteria:** After completing this research, we can answer:

1. What specific patterns define "meaningful" vs "trivial" tests in this codebase?
2. What coverage targets and test structures will upstream maintainers accept?
3. What fixtures, assertions, and test depth are required for each component?
4. How do we validate our tests are production-quality before submitting?

---

## Research Section Outline

> **Note:** Each section below is a placeholder for a comprehensive research plan that will be developed later. Sections are ordered by dependency - complete in sequence.

---

### Section 1: Upstream Blueprint Analysis (PR #114 - EDR Implementation)

**Objective:** Extract the complete testing blueprint from the accepted EDR implementation (PR #114).

**Why First:** This is our direct pattern reference. EDR was accepted by upstream maintainers, so their test strategy is proven. Everything else validates against this.

**Key Questions:**

- What test file structure did EDR use?
- What test-to-code ratio did they achieve?
- What coverage % did they target?
- How did they structure describe/it blocks?
- What assertions define "meaningful" vs "trivial"?
- What fixture patterns did they use?
- How deep did they test (happy path vs edge cases vs error cases)?
- What makes their tests "end-to-end" for a URL-building library?

**Resources:**

- [PR #114 Analysis](../../upstream/pr114-analysis.md) (starting point, needs deep dive)
- camptocamp/ogc-client PR #114 diff and review comments
- EDR test files in upstream repository

**Deliverable:** Complete EDR test pattern analysis document with concrete examples

---

### Section 2: Existing Upstream Test Pattern Survey

**Objective:** Identify consistent testing patterns across all existing ogc-client implementations.

**Why Second:** After understanding EDR (newest, closest match), validate patterns are consistent across WFS, WMS, WMTS, STAC implementations. Identifies library-wide conventions.

**Key Questions:**

- What patterns are consistent across ALL implementations?
- What test file naming conventions are used?
- How are fixtures organized?
- How do they test TypeScript types?
- How do they test conformance detection?
- How do they test URL builders?
- What test utilities are shared?
- What's the typical test-to-code ratio?

**Resources:**

- camptocamp/ogc-client existing test files (WFS, WMS, WMTS, STAC, EDR)
- [Architecture Patterns Analysis](../../upstream/architecture-patterns-analysis.md)
- [File Organization Strategy](../../upstream/file-organization-analysis.md)

**Deliverable:** Upstream test pattern consistency matrix with examples from each implementation

---

### Section 3: TypeScript Client Library Testing Best Practices

**Objective:** Understand industry-standard testing practices for TypeScript client libraries independent of OGC context.

**Why Third:** Provides broader context beyond OGC-specific patterns. Validates upstream patterns align with industry standards or identifies gaps.

**Key Questions:**

- What defines "production-quality" testing for client libraries?
- What coverage targets are industry standard?
- How to test without actual HTTP calls (mocking strategies)?
- How to validate generated URLs thoroughly?
- How to test TypeScript interfaces and types?
- What's unit vs integration vs e2e for a URL-building library?
- How to test error conditions comprehensively?

**Resources:**

- TypeScript testing guides and documentation
- Client library examples (axios, @octokit/rest, aws-sdk)
- Testing best practices articles
- Jest documentation (library's test framework)

**Deliverable:** TypeScript client library testing standards document with benchmark comparisons

---

### Section 4: Implementation Guide Testing Requirements Analysis

**Objective:** Extract all testing requirements, estimates, and specifications from the complete Implementation Guide.

**Why Fourth:** Now that we understand external patterns (upstream + industry), analyze our own architectural decisions and how they constrain testing strategy.

**Key Questions:**

- What test structure does the Implementation Guide specify?
- What are the test line estimates by phase?
- What coverage targets are documented?
- What test types are defined (format, resource, query builder, integration)?
- What fixtures are specified?
- How does the 34-task roadmap structure inform test organization?

**Resources:**

- [CSAPI Implementation Guide](../../planning/csapi-implementation-guide.md) (Section 9: Testing Components)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Component specifications with test requirements)

**Deliverable:** Implementation Guide testing requirements extraction with validation against upstream patterns

---

### Section 5: Roadmap Testing Integration Strategy

**Objective:** Understand how the 34-task incremental roadmap structures testing (write tests after each subtask).

**Why Fifth:** The roadmap specifies "test immediately after each subtask" - need to understand how this incremental approach affects test organization, when to write what tests, and how to avoid test debt.

**Key Questions:**

- How does "test after each subtask" affect test file organization?
- When do we write unit tests vs integration tests in the roadmap?
- How do Phase 1-4 testing requirements differ?
- What's the test accumulation pattern across 34 tasks?
- How do we prevent test debt with incremental development?
- What's the commit strategy for tests (per subtask vs per phase)?

**Resources:**

- [ROADMAP.md](../../planning/ROADMAP.md) (All 4 phases with test-immediately pattern)
- [ROADMAP.md](../../planning/ROADMAP.md) (Development Standards section)

**Deliverable:** Incremental testing workflow document aligned with 34-task roadmap structure

---

### Section 6: "Meaningful vs Trivial" Definition

**Objective:** Create concrete definition of what makes tests meaningful vs trivial based on senior dev feedback and upstream patterns.

**Why Sixth:** After understanding all patterns (upstream + industry + our architecture), synthesize specific criteria for test quality. This is the core constraint from senior dev feedback.

**Key Questions:**

- What specific patterns define "trivial" tests? (concrete examples)
- What specific patterns define "meaningful" tests? (concrete examples)
- How deep should assertions go? (URL structure validation depth)
- What fixture quality is required? (real spec examples vs mocks)
- What edge cases must be covered? (boundary conditions, errors, malformed data)
- How to measure "usefulness" objectively?
- What makes tests "deep" for a URL-building library?

**Resources:**

- Section 1 deliverable (PR #114 patterns)
- Section 2 deliverable (upstream consistency)
- Section 3 deliverable (industry standards)
- Senior dev feedback from previous iteration
- [Lessons Learned Analysis](../requirements/lessons-learned-analysis.md)
- [Gap Analysis](../requirements/csapi-gap-analysis.md)

**Deliverable:** "Meaningful vs Trivial" test quality guide with side-by-side examples

---

### Section 7: End-to-End Testing Scope Definition

**Objective:** Define what "end-to-end" means for a URL-building client library and how to achieve it.

**Why Seventh:** Senior dev specifically criticized lack of "end-to-end" tests. After understanding test quality (Section 6), define scope and boundaries of e2e tests.

**Key Questions:**

- What is "end-to-end" for a library that builds URLs but doesn't make HTTP calls?
- What's the boundary between integration and e2e tests?
- Do e2e tests mock HTTP responses or use real servers?
- What workflows constitute e2e tests?
- How do the 4 workflow types in Implementation Guide map to e2e tests?
- How to test multi-resource navigation end-to-end?
- What's the test pyramid distribution (unit/integration/e2e)?

**Resources:**

- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Integration Tests section - 4 workflow types)
- Section 1-2 deliverables (upstream e2e patterns)
- Section 3 deliverable (industry e2e standards)

**Deliverable:** End-to-end testing scope and workflow definition with test pyramid specification

---

### Section 8: CSAPI Specification Test Requirements

**Objective:** Extract testable requirements from CSAPI Parts 1 & 2 specifications and OpenAPI definitions.

**Why Eighth:** After understanding test patterns and quality standards, extract what MUST be tested from the normative specifications.

**Key Questions:**

- What are the normative testing requirements in CSAPI specs?
- Are there conformance test suites we should reference?
- What specification examples can be used as test fixtures?
- What query parameter combinations are specified?
- What error conditions are defined in the spec?
- What format validation rules are normative?

**Resources:**

- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html)
- [CSAPI Part 1 OpenAPI](../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml)
- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html)
- [CSAPI Part 2 OpenAPI](../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml)
- [Part 1 Requirements Analysis](../requirements/csapi-part1-requirements.md)
- [Part 2 Requirements Analysis](../requirements/csapi-part2-requirements.md)

**Deliverable:** CSAPI specification test requirement matrix with spec section references

---

### Section 9: SensorML 3.0 Format Testing Requirements

**Objective:** Define comprehensive testing requirements for SensorML 3.0 parser based on specification.

**Why Ninth:** Format parsing is a major rejection risk from previous iteration. Need deep understanding of what "complete" SensorML testing looks like.

**Key Questions:**

- What SensorML 3.0 structures must be tested?
- What specification examples can be used as fixtures?
- What edge cases exist in SensorML (recursive components, missing properties)?
- How deep to validate nested structures?
- What integration tests needed with SWE Common?
- What error cases must be handled?
- What validation rules are normative?

**Resources:**

- [SensorML 3.0 Specification](https://docs.ogc.org/is/23-000r1/23-000r1.html)
- SensorML 3.0 JSON Schema: https://schemas.opengis.net/sensorml/3.0/
- [Format Requirements Analysis](../requirements/csapi-format-requirements.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (SensorML parser specification)
- [OpenSensorHub Analysis](../requirements/csapi-opensensorhub-analysis.md) (real-world examples)

**Deliverable:** SensorML 3.0 parser testing specification with fixture inventory

---

### Section 10: SWE Common 3.0 Format Testing Requirements

**Objective:** Define comprehensive testing requirements for SWE Common 3.0 parser covering all three encodings (JSON/Text/Binary).

**Why Tenth:** SWE Common is the most complex format (3 encodings, 12+ component types). Binary encoding is particularly critical and error-prone.

**Key Questions:**

- What SWE Common structures must be tested (DataRecord, DataArray, all 12 components)?
- How to test all three encodings (JSON, Text, Binary)?
- What binary encoding edge cases exist (endianness, IEEE 754, multi-byte)?
- What specification examples can be used as fixtures?
- What validation rules are normative?
- How to test schema validation for observations?
- What error cases must be handled per encoding?

**Resources:**

- [SWE Common 3.0 Specification](https://docs.ogc.org/is/23-011r1/23-011r1.html)
- SWE Common 3.0 JSON Schema: https://schemas.opengis.net/sweCommon/3.0/
- [Format Requirements Analysis](../requirements/csapi-format-requirements.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (SWE Common parser specification)
- [OpenSensorHub Analysis](../requirements/csapi-opensensorhub-analysis.md) (real-world examples)

**Deliverable:** SWE Common 3.0 parser testing specification with encoding-specific fixture inventory

---

### Section 11: GeoJSON CSAPI Extensions Testing Requirements

**Objective:** Define testing requirements for CSAPI-specific GeoJSON extensions on top of existing GeoJSON parser.

**Why Eleventh:** GeoJSON is the primary format for Part 1 resources. Need to test CSAPI property extraction and validation while reusing existing parser.

**Key Questions:**

- What CSAPI properties must be extracted from GeoJSON features?
- What validation rules are specific to CSAPI (uniqueIdentifier URI format, systemType vocab)?
- How to test all Part 1 resource types (Systems, Deployments, etc.)?
- What geometry types must be tested?
- How much of existing GeoJSON parser can be reused vs needs CSAPI tests?
- What featureType values must be recognized?

**Resources:**

- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html) (GeoJSON encoding requirements)
- [GeoJSON RFC 7946](https://tools.ietf.org/html/rfc7946)
- [Format Requirements Analysis](../requirements/csapi-format-requirements.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (GeoJSON handler extensions)

**Deliverable:** GeoJSON CSAPI extensions testing specification with Part 1 resource fixture inventory

---

### Section 12: QueryBuilder URL Construction Testing Strategy ✅

**Status:** ✅ COMPLETE (February 5, 2026)  
**Deliverable:** [12-querybuilder-testing-strategy.md](findings/12-querybuilder-testing-strategy.md) (30,000 words, 25 sections)

**Objective:** Define comprehensive testing strategy for all 70-80 CSAPIQueryBuilder methods covering all 9 resource types.

**Why Twelfth:** QueryBuilder is the core API surface. After understanding format testing (Sections 9-11), define URL construction testing patterns.

**Key Research Completed:**

- ✅ All 80 methods inventoried across 9 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands)
- ✅ "Meaningful" URL testing approach defined (parseAndValidateUrl utility)
- ✅ Query parameter testing strategy for 10 parameter categories
- ✅ URL encoding edge cases identified (15 scenarios)
- ✅ Nested endpoint testing patterns (15 parent-child chains)
- ✅ Resource availability validation strategy
- ✅ Test organization structure (multiple files recommended: 1 shared + 9 per-resource)
- ✅ Test utilities specified (parseAndValidateUrl, validateEncoding, createTestEndpoint)
- ✅ Fixture requirements (5 JSON files)
- ✅ Testing estimates (188 tests, 1,880-2,256 lines, 22-29 hours)

**Key Findings:**

- **Method Count:** 80 methods total (12 Systems, 8 Deployments, 8 Procedures, 8 SamplingFeatures, 6 Properties, 11 DataStreams, 9 Observations, 8 ControlStreams, 10 Commands)
- **Test Scenarios:** ~188 tests with 2.4 tests per method average
- **URL Validation Depth:** Parse URL into components (protocol, host, pathname, query), validate query parameters as objects, verify encoding
- **File Organization:** Multiple files recommended (1 shared utilities + 9 per-resource files of 90-220 lines each)
- **Test Priorities:** CRITICAL (75 tests), HIGH (65 tests), MEDIUM (35 tests), LOW (13 tests)
- **Fixtures Needed:** 5 JSON files (conformance-all-resources, conformance-part1-only, collection-info-all-resources, collection-info-part1-only, collection-info-no-csapi)

**Resources:**

- [Implementation Guide](../../planning/csapi-implementation-guide.md) (CSAPIQueryBuilder specification)
- [ROADMAP.md](../../planning/ROADMAP.md) (Phase 2: 9 resource type tasks)
- [URL Building Architecture](../../upstream/url-building-analysis.md)
- [Query Parameter Requirements](../requirements/csapi-query-parameters.md)
- Section 1-2 deliverables (upstream URL builder test patterns)

**Deliverable:** ✅ QueryBuilder testing strategy with method-by-method test specifications

---

### Section 13: Resource Method Testing Patterns (9 Resource Types)

**Objective:** Define consistent testing pattern for resource methods (CRUD operations) across all 9 CSAPI resource types.

**Why Thirteenth:** After QueryBuilder URL testing strategy (Section 12), define testing for the resource operations built on those URLs.

**Key Questions:**

- What CRUD operations exist per resource type?
- How to test GET/POST/PUT/PATCH/DELETE systematically?
- What request body validation is needed for write operations?
- How to test query parameters specific to each resource type?
- What error conditions must be tested per operation?
- How to structure tests consistently across 9 resource types?

**Resources:**

- [CRUD Operations Requirements](../requirements/csapi-crud-operations.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Resource Method Tests specification)
- [Part 1 Requirements](../requirements/csapi-part1-requirements.md)
- [Part 2 Requirements](../requirements/csapi-part2-requirements.md)

**Deliverable:** Resource method testing template applicable to all 9 resource types

---

### Section 14: Integration Test Workflow Design

**Objective:** Design the 4 integration test workflows defined in Implementation Guide with concrete test scenarios.

**Why Fourteenth:** After unit-level testing patterns (Sections 12-13), design multi-component workflows that test interactions.

**Key Questions:**

- How to structure Discovery workflow tests?
- How to structure Observation workflow tests?
- How to structure Command workflow tests?
- How to structure Cross-resource navigation tests?
- What mocking strategy for HTTP responses?
- What fixtures needed for multi-step workflows?
- How to validate state changes across workflow steps?

**Resources:**

- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Integration Tests section - 4 workflows)
- [Usage Scenarios](../requirements/csapi-usage-scenarios.md)
- Section 7 deliverable (e2e scope definition)
- Section 1-2 deliverables (upstream integration test patterns)

**Deliverable:** Integration test workflow specifications with scenario details and fixtures

---

### Section 15: Fixture Sourcing and Organization Strategy

**Objective:** Create comprehensive plan for sourcing, organizing, and maintaining test fixtures for all components.

**Why Fifteenth:** After defining all test requirements (Sections 8-14), identify what fixtures are needed and where to source them.

**Key Questions:**

- What fixtures can be extracted from CSAPI specifications?
- What fixtures can be sourced from OpenSensorHub demo server?
- What fixtures need to be hand-crafted (edge cases, errors)?
- How to organize fixtures by resource type and format?
- How to structure fixture files for reusability?
- How to document fixture provenance?
- How to keep fixtures in sync with spec updates?

**Resources:**

- [OpenSensorHub Analysis](../requirements/csapi-opensensorhub-analysis.md) (live server access)
- [52°North Analysis](../requirements/csapi-52north-analysis.md) (server examples)
- All CSAPI specification example sections
- All SensorML 3.0 specification examples
- All SWE Common 3.0 specification examples
- Section 8-11 deliverables (format-specific fixture requirements)

**Deliverable:** Complete fixture inventory with sourcing plan and directory structure

---

### Section 16: Worker Extensions Testing Strategy

**Objective:** Define testing strategy for the 9 Web Worker message types and background processing.

**Why Sixteenth:** Worker testing has unique challenges (async, message passing, fallback behavior). Address after core testing patterns established.

**Key Questions:**

- How to test Worker message types in Jest?
- How to test async parsing operations?
- How to test fallback for non-worker environments?
- What fixtures needed for heavy parsing operations?
- How to test performance characteristics?
- What integration tests needed with parsers?

**Resources:**

- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Worker Extensions section)
- [ROADMAP.md](../../planning/ROADMAP.md) (Phase 4: Task 1)
- Existing worker tests in camptocamp/ogc-client

**Deliverable:** Worker testing strategy with message type test specifications

---

### Section 17: Coverage Targets and Metrics Definition

**Objective:** Define specific coverage targets for each component type and how to measure meaningful coverage (not just %).

**Why Seventeenth:** After defining all test types, set concrete coverage targets validated against upstream standards.

**Key Questions:**

- What overall coverage % is required?
- What coverage targets per component type (QueryBuilder, parsers, types)?
- How to measure branch coverage vs statement coverage?
- What's acceptable for type definition coverage?
- How to measure "meaningful" coverage vs just % coverage?
- What modules require 95%+ coverage vs 80%?
- How to track coverage by phase during incremental development?

**Resources:**

- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Coverage targets: >80%)
- Section 1-2 deliverables (upstream coverage analysis)
- Section 3 deliverable (industry standards)
- Jest coverage tools documentation

**Deliverable:** Coverage target specification by component with measurement strategy

---

### Section 18: Error Condition Testing Strategy

**Objective:** Comprehensive strategy for testing all error conditions across all components.

**Why Eighteenth:** Error handling is often under-tested. After all component testing patterns defined, systematically address error scenarios.

**Key Questions:**

- What error types must be tested (validation, network, parse, conformance)?
- How to test error messages are meaningful?
- What error conditions does CSAPI spec define?
- How to test resource validation errors?
- How to test malformed data errors in parsers?
- How to test missing/invalid query parameter errors?
- How to structure error tests consistently?

**Resources:**

- [Error Handling Design Analysis](../../upstream/error-handling-analysis.md)
- [CSAPI Part 1 OpenAPI](../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) (error schemas)
- [CSAPI Part 2 OpenAPI](../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) (error schemas)
- All previous section deliverables (component-specific error cases)

**Deliverable:** Error condition test matrix with test patterns for each error type

---

### Section 19: Test Organization and File Structure

**Objective:** Define complete test file structure, naming conventions, and organization strategy.

**Why Nineteenth:** After all test content defined, organize it into coherent file structure matching upstream patterns.

**Key Questions:**

- What test files are needed? (names and purposes)
- How to organize tests by component vs resource type?
- Where to locate test files (colocated vs separate test/ directory)?
- How to name test files consistently with upstream?
- How to structure describe/it blocks?
- How to organize test utilities and helpers?
- How to organize fixtures?

**Resources:**

- [File Organization Strategy](../../upstream/file-organization-analysis.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Test file specifications)
- Section 1-2 deliverables (upstream test file patterns)
- Section 15 deliverable (fixture organization)

**Deliverable:** Complete test file structure specification with naming conventions

---

### Section 20: Test-to-Code Ratio Validation

**Objective:** Validate estimated test-to-code ratio (~0.9:1) is reasonable compared to upstream implementations.

**Why Twentieth:** Implementation Guide estimates ~4,850-6,500 implementation lines + ~4,500-6,000 test lines. Validate this is appropriate.

**Key Questions:**

- What's the test-to-code ratio in EDR implementation?
- What's the ratio in other ogc-client implementations?
- Is ~0.9:1 reasonable for a client library?
- Does ratio vary by component type (QueryBuilder vs parsers)?
- How does incremental testing affect ratio?
- Are our estimates missing any test types?

**Resources:**

- Section 1-2 deliverables (upstream ratio analysis)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (line estimates)
- [ROADMAP.md](../../planning/ROADMAP.md) (phase-by-phase estimates)

**Deliverable:** Test-to-code ratio validation report with adjustments if needed

---

### Section 21: TypeScript Type Testing Strategy

**Objective:** Define strategy for testing TypeScript type definitions, interfaces, and type safety.

**Why 21st:** Type testing is often overlooked but critical for TypeScript libraries. Address after concrete component testing patterns established.

**Key Questions:**

- How to test TypeScript interfaces compile correctly?
- How to test type discrimination (union types)?
- How to test generic type constraints?
- How to test type inference?
- What's the upstream pattern for type testing?
- Are compilation tests sufficient or runtime tests needed?

**Resources:**

- [TypeScript Types Analysis](../../upstream/typescript-types-analysis.md)
- [Datatype Schema Requirements](../requirements/csapi-datatype-schema-requirements.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Type system specification)
- Section 1-2 deliverables (upstream type test patterns)

**Deliverable:** TypeScript type testing strategy with patterns for interfaces, unions, generics

---

### Section 22: Conformance and Capability Testing

**Objective:** Define testing strategy for conformance class detection and capability-based behavior.

**Why 22nd:** Client must adapt to different server capabilities. After all component testing defined, test adaptive behavior.

**Key Questions:**

- How to test conformance class detection from /conformance endpoint?
- How to test `hasConnectedSystems` method?
- How to test resource availability checking?
- How to test graceful degradation when resources unavailable?
- What conformance scenarios must be tested?
- How to mock different server capability profiles?

**Resources:**

- [Conformance Capabilities Requirements](../requirements/csapi-conformance-capabilities.md)
- [52°North Analysis](../requirements/csapi-52north-analysis.md) (partial conformance example)
- [OpenSensorHub Analysis](../requirements/csapi-opensensorhub-analysis.md) (full conformance example)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Conformance checking specification)

**Deliverable:** Conformance testing strategy with server capability test scenarios

---

### Section 23: Pagination Testing Strategy

**Objective:** Define comprehensive testing strategy for both offset-based (Part 1) and cursor-based (Part 2) pagination.

**Why 23rd:** Pagination is critical for large datasets. After resource method testing defined (Section 13), test pagination thoroughly.

**Key Questions:**

- How to test offset-based pagination (limit/offset)?
- How to test cursor-based pagination (limit/cursor)?
- What edge cases exist (empty pages, boundary conditions)?
- How to test pagination with filtering?
- How to test pagination link parsing?
- What fixtures needed for multi-page scenarios?

**Resources:**

- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (cursor-based pagination)
- [Part 2 Requirements](../requirements/csapi-part2-requirements.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Pagination specifications)

**Deliverable:** Pagination testing strategy covering both pagination modes with edge cases

---

### Section 24: Query Parameter Combination Testing

**Objective:** Define strategy for testing complex query parameter combinations and precedence.

**Why 24th:** CSAPI has 30+ query parameters with complex interactions. After individual parameter testing (Section 12), test combinations.

**Key Questions:**

- What query parameter combinations are valid?
- What combinations are invalid/conflicting?
- How to test parameter precedence rules?
- How to test spatial + temporal + relationship parameters together?
- What edge cases exist in parameter encoding?
- How to structure combination tests systematically (not exhaustive)?

**Resources:**

- [Query Parameter Requirements](../requirements/csapi-query-parameters.md)
- [CSAPI Part 1 OpenAPI](../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml)
- [CSAPI Part 2 OpenAPI](../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml)
- Section 12 deliverable (QueryBuilder testing strategy)

**Deliverable:** Query parameter combination testing strategy with priority matrix

---

### Section 25: Format Negotiation Testing Strategy

**Objective:** Define testing strategy for format negotiation (Accept headers, query parameters, link-based discovery).

**Why 25th:** Multiple formats per resource type require negotiation. After format parsing testing (Sections 9-11), test negotiation.

**Key Questions:**

- How to test Accept header format selection?
- How to test query parameter format selection (`f=geojson` vs `f=sensorml`)?
- How to test link-based format discovery?
- What format fallback scenarios must be tested?
- How to test media type parsing?
- What fixtures needed for format negotiation scenarios?

**Resources:**

- [Format Negotiation Architecture](../../upstream/format-negotiation-analysis.md)
- [Format Requirements](../requirements/csapi-format-requirements-3.1.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Format negotiation specifications)

**Deliverable:** Format negotiation testing strategy with media type scenarios

---

### Section 26: Sub-Resource Navigation Testing

**Objective:** Define testing strategy for all nested resource navigation patterns (e.g., `/systems/{id}/datastreams`).

**Why 26th:** CSAPI has rich hierarchical relationships. After resource method testing (Section 13), test navigation.

**Key Questions:**

- How to test all nested endpoint patterns?
- How to test bidirectional navigation?
- How to test query parameters on nested endpoints?
- What relationship endpoint variations must be tested?
- How to test link relation parsing for navigation?
- What fixtures needed for hierarchy scenarios?

**Resources:**

- [Sub-Resource Navigation Requirements](../requirements/csapi-subresource-navigation.md)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Navigation methods)
- [ROADMAP.md](../../planning/ROADMAP.md) (Phase 2: All navigation methods)

**Deliverable:** Sub-resource navigation testing strategy with relationship matrix

---

### Section 27: Schema-Driven Validation Testing

**Objective:** Define testing strategy for schema validation (DataStream schemas for Observations, ControlStream schemas for Commands).

**Why 27th:** Schema validation is unique to CSAPI Part 2. After format testing (Section 10), test schema-driven validation.

**Key Questions:**

- How to test observation result validation against DataStream schema?
- How to test command parameter validation against ControlStream schema?
- What schema mismatch scenarios must be tested?
- How to test schema parsing (SWE Common schemas)?
- What fixtures needed for schema validation scenarios?
- How to test error messages for schema violations?

**Resources:**

- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (schema requirements)
- [Part 2 Requirements](../requirements/csapi-part2-requirements.md)
- [SWE Common 3.0 Specification](https://docs.ogc.org/is/23-011r1/23-011r1.html)
- Section 10 deliverable (SWE Common testing specification)

**Deliverable:** Schema-driven validation testing strategy with mismatch scenarios

---

### Section 28: Temporal Query Testing Strategy

**Objective:** Define comprehensive testing strategy for all temporal query parameters (datetime, phenomenonTime, resultTime, executionTime, issueTime).

**Why 28th:** Temporal queries are critical for observations and commands. After query parameter testing (Section 24), deep dive on temporal.

**Key Questions:**

- How to test all ISO 8601 interval formats?
- How to test open-ended intervals (`../..`, `2024-01-01/..`, `../2024-12-31`)?
- How to test instant vs interval queries?
- How to test temporal parameter combinations?
- What temporal edge cases must be tested?
- How to test temporal validation errors?

**Resources:**

- [Query Parameter Requirements](../requirements/csapi-query-parameters.md) (temporal parameters)
- ISO 8601 specification
- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (temporal queries)

**Deliverable:** Temporal query testing strategy with ISO 8601 format coverage

---

### Section 29: Spatial Query Testing Strategy

**Objective:** Define testing strategy for spatial query parameters (bbox, geometry intersection).

**Why 29th:** Spatial queries are critical for Part 1 resources. After query parameter testing (Section 24), deep dive on spatial.

**Key Questions:**

- How to test bbox query parameter?
- How to test geometry intersection queries?
- What CRS handling is required?
- What spatial edge cases must be tested (antimeridian, poles)?
- How to test spatial validation errors?
- What fixtures needed for spatial scenarios?

**Resources:**

- [Query Parameter Requirements](../requirements/csapi-query-parameters.md) (spatial parameters)
- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html) (spatial queries)
- GeoJSON RFC 7946 (spatial structures)

**Deliverable:** Spatial query testing strategy with geometry scenario coverage

---

### Section 30: Bulk Operations Testing Strategy

**Objective:** Define testing strategy for bulk observation and command creation operations.

**Why 30th:** Bulk operations have unique performance and validation considerations. After individual operation testing (Section 13), test bulk.

**Key Questions:**

- How to test bulk observation creation?
- How to test bulk command creation?
- What request size limits must be tested?
- How to test partial success/failure in bulk operations?
- What error handling is specific to bulk operations?
- What fixtures needed for bulk scenarios?

**Resources:**

- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (bulk operations)
- [Part 2 Requirements](../requirements/csapi-part2-requirements.md)
- [CRUD Operations Requirements](../requirements/csapi-crud-operations.md)

**Deliverable:** Bulk operations testing strategy with performance consideration

---

### Section 31: Command Lifecycle Testing Strategy

**Objective:** Define testing strategy for complete command lifecycle (submission → status tracking → result retrieval → cancel).

**Why 31st:** Command lifecycle is unique to CSAPI. After individual operations tested (Section 13), test complete workflow.

**Key Questions:**

- How to test command submission?
- How to test status tracking (pending → executing → completed)?
- How to test result retrieval?
- How to test cancel operation?
- How to test sync vs async commands?
- What fixtures needed for lifecycle scenarios?

**Resources:**

- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (command operations)
- [Part 2 Requirements](../requirements/csapi-part2-requirements.md)
- [Usage Scenarios](../requirements/csapi-usage-scenarios.md) (command workflows)

**Deliverable:** Command lifecycle testing strategy with state transition scenarios

---

### Section 32: Real-World Server Compatibility Testing

**Objective:** Define strategy for validating implementation against multiple real CSAPI servers (OpenSensorHub, 52°North).

**Why 32nd:** After all component testing defined, validate against real servers to catch interoperability issues.

**Key Questions:**

- How to test against OpenSensorHub demo server?
- How to test against 52°North demo server?
- What server variations must be accommodated?
- How to test partial conformance scenarios?
- What server-specific quirks must be handled?
- How to structure compatibility test suite?

**Resources:**

- [OpenSensorHub Analysis](../requirements/csapi-opensensorhub-analysis.md) (live server: http://45.55.99.236:8080/sensorhub/api)
- [52°North Analysis](../requirements/csapi-52north-analysis.md) (live server: https://csa.demo.52north.org/)
- [Conformance Capabilities](../requirements/csapi-conformance-capabilities.md)

**Deliverable:** Multi-server compatibility testing strategy with server profile matrix

---

### Section 33: Performance and Efficiency Testing

**Objective:** Define strategy for testing performance characteristics and efficiency (especially for parsers and large datasets).

**Why 33rd:** After functional testing defined, address non-functional requirements like performance.

**Key Questions:**

- What performance benchmarks are required?
- How to test parser performance (especially Binary SWE Common)?
- How to test with large datasets (1000+ observations)?
- What memory usage testing is needed?
- How to test Worker performance for background parsing?
- What performance regression tests are needed?

**Resources:**

- [Implementation Guide](../../planning/csapi-implementation-guide.md) (performance characteristics)
- [SWE Common Specification](https://docs.ogc.org/is/23-011r1/23-011r1.html) (Binary encoding efficiency)
- Section 16 deliverable (Worker testing strategy)

**Deliverable:** Performance testing strategy with benchmark specifications

---

### Section 34: Test Utility and Helper Design

**Objective:** Design shared test utilities and helper functions to reduce duplication and improve test maintainability.

**Why 34th:** After all test patterns defined, identify common utilities needed across test suites.

**Key Questions:**

- What test utilities are needed for URL validation?
- What fixtures loading helpers are needed?
- What assertion helpers improve test readability?
- What mocking utilities are needed?
- How to structure test setup/teardown helpers?
- What utilities exist upstream we can reuse?

**Resources:**

- Section 1-2 deliverables (upstream test utilities)
- All previous section deliverables (common test patterns)
- [File Organization Strategy](../../upstream/file-organization-analysis.md)

**Deliverable:** Test utility library specification with reusable helper functions

---

### Section 35: JSDoc Testing Documentation Standards

**Objective:** Define JSDoc documentation standards for test files to ensure tests are self-documenting.

**Why 35th:** After test organization defined (Section 19), establish documentation standards for test maintainability.

**Key Questions:**

- What JSDoc comments are needed in test files?
- How to document test intent and expected behavior?
- How to document fixture provenance in tests?
- How to document test coverage gaps?
- What examples should be included in test docs?
- How do upstream implementations document tests?

**Resources:**

- [Implementation Guide](../../planning/csapi-implementation-guide.md) (Documentation standards)
- Section 1-2 deliverables (upstream test documentation patterns)
- TypeDoc documentation standards

**Deliverable:** Test documentation standards guide with JSDoc templates

---

### Section 36: Test Quality Checklist and Review Process

**Objective:** Create comprehensive checklist for validating tests meet "meaningful, useful, deep, end-to-end" criteria before considering them complete.

**Why 36th:** Final validation tool. After all testing patterns and standards defined, create quality gate.

**Key Questions:**

- What specific checklist items validate "meaningful" tests?
- What defines "useful" tests objectively?
- What constitutes "deep" testing for each component type?
- What criteria validate "end-to-end" tests?
- How to review tests against checklist?
- What's the sign-off process before tests are considered done?

**Resources:**

- Section 6 deliverable ("Meaningful vs Trivial" guide)
- Section 7 deliverable (e2e scope definition)
- All previous section deliverables (component-specific quality criteria)
- Senior dev feedback from previous iteration

**Deliverable:** Test quality checklist and review process document

---

### Section 37: Test Maintenance and Evolution Strategy

**Objective:** Define strategy for maintaining tests as CSAPI spec evolves and upstream library changes.

**Why 37th:** Tests must remain valuable long-term. After all testing defined, plan for maintenance.

**Key Questions:**

- How to keep tests in sync with spec updates?
- How to handle upstream library changes?
- How to refactor tests when implementation changes?
- What triggers test updates?
- How to prevent test rot?
- How to document test maintenance responsibilities?

**Resources:**

- [Lessons Learned Analysis](../requirements/lessons-learned-analysis.md) (maintenance issues from previous iteration)
- Section 15 deliverable (fixture maintenance)

**Deliverable:** Test maintenance strategy and update workflow

---

### Section 38: Testing Playbook Synthesis

**Objective:** Synthesize all research into a comprehensive step-by-step testing playbook for implementation.

**Why Last:** After all research complete, create the practical guide that developers will follow during Phase 1-4 implementation.

**Key Questions:**

- What's the step-by-step process for writing tests for each component?
- What's the workflow for each roadmap phase?
- How to validate tests as you write them?
- What tools and commands are needed?
- How to measure progress?
- What examples illustrate each pattern?

**Resources:**

- ALL previous section deliverables (comprehensive synthesis)
- [ROADMAP.md](../../planning/ROADMAP.md) (34-task implementation plan)
- [Implementation Guide](../../planning/csapi-implementation-guide.md) (complete specifications)

**Deliverable:** Complete Testing Playbook ready for Phase 1 implementation

---

## Research Execution Plan

**Phase 1: Critical Foundation (Sections 1-3, ~6-8 hours)**

- Section 1: PR #114 Analysis (Blueprint)
- Section 2: Upstream Test Survey (Consistency)
- Section 3: TypeScript Best Practices (Industry standards)

**Phase 2: Architecture Integration (Sections 4-7, ~4-6 hours)**

- Section 4: Implementation Guide Analysis
- Section 5: Roadmap Integration Strategy
- Section 6: "Meaningful vs Trivial" Definition
- Section 7: E2E Testing Scope

**Phase 3: Component Requirements (Sections 8-13, ~8-10 hours)**

- Section 8: CSAPI Spec Test Requirements
- Section 9: SensorML Testing Requirements
- Section 10: SWE Common Testing Requirements
- Section 11: GeoJSON Testing Requirements
- Section 12: QueryBuilder Testing Strategy
- Section 13: Resource Method Testing Patterns

**Phase 4: Integration & Organization (Sections 14-20, ~6-8 hours)**

- Section 14: Integration Test Workflow Design
- Section 15: Fixture Sourcing Strategy
- Section 16: Worker Extensions Testing
- Section 17: Coverage Targets Definition
- Section 18: Error Condition Strategy
- Section 19: Test Organization & File Structure
- Section 20: Test-to-Code Ratio Validation

**Phase 5: Specialized Testing (Sections 21-31, ~10-12 hours)**

- Section 21: TypeScript Type Testing
- Section 22: Conformance Testing
- Section 23: Pagination Testing
- Section 24: Query Parameter Combinations
- Section 25: Format Negotiation Testing
- Section 26: Sub-Resource Navigation
- Section 27: Schema-Driven Validation
- Section 28: Temporal Query Testing
- Section 29: Spatial Query Testing
- Section 30: Bulk Operations Testing
- Section 31: Command Lifecycle Testing

**Phase 6: Quality & Compatibility (Sections 32-34, ~4-6 hours)**

- Section 32: Real-World Server Compatibility
- Section 33: Performance Testing
- Section 34: Test Utility Design

**Phase 7: Documentation & Synthesis (Sections 35-38, ~4-6 hours)**

- Section 35: JSDoc Testing Standards
- Section 36: Test Quality Checklist
- Section 37: Test Maintenance Strategy
- Section 38: Testing Playbook Synthesis

**Total Research Time: 42-56 hours before writing first test**

---

## Success Criteria

Research is complete and ready for implementation when:

✅ **Blueprint Understood:** PR #114 patterns fully documented with concrete examples  
✅ **Patterns Validated:** Upstream consistency confirmed across 5+ implementations  
✅ **Quality Defined:** "Meaningful vs trivial" has objective criteria with examples  
✅ **Scope Clear:** E2E testing boundaries defined and validated  
✅ **Requirements Extracted:** All testable requirements from CSAPI specs documented  
✅ **Formats Specified:** SensorML, SWE Common, GeoJSON testing fully specified  
✅ **Methods Mapped:** All 70-80 QueryBuilder methods have test specifications  
✅ **Workflows Designed:** 4 integration workflows have concrete test scenarios  
✅ **Fixtures Sourced:** Complete fixture inventory with provenance documented  
✅ **Coverage Targeted:** Specific % targets set per component type  
✅ **Organization Defined:** Complete test file structure and naming conventions  
✅ **Quality Validated:** Checklist created to validate test quality before completion  
✅ **Playbook Ready:** Step-by-step testing guide ready for Phase 1 implementation

**Final Gate:** Can answer "What would a maintainer expect to see?" with concrete specifications and examples, not vague descriptions.

---

## Version History

**Version 1.0 (February 5, 2026):**

- Initial research plan outline with 38 sections
- Structured by dependency order (upstream patterns first, specialized testing last)
- Integrated with Implementation Guide and Roadmap as resources
- Comprehensive resource linking to all relevant references
- 42-56 hour research estimate before implementation begins

**Previous Versions:**

- [v1.0 (archived)](archive/testing-strategy-research-v1.md) - Original high-level research questions document (outdated)
