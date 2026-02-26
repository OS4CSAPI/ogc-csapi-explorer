# Research Plan: QueryBuilder URL Construction Testing Strategy

**Section:** 12 of 38  
**Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Estimated Time:** 2-3 hours  
**Actual Time:** ~3 hours  
**Estimated Lines:** 1,880-2,256 lines of test code  
**Actual Deliverable:** 30,000-word testing strategy document (2,652 lines)

---

## 1. Research Objective

Define comprehensive testing strategy for CSAPIQueryBuilder covering all ~70-80 methods across 9 resource types. Create systematic approach for URL validation that ensures deep, meaningful testing beyond trivial string checks.

### Why This Research Twelfth

**Dependency Chain:** After format testing requirements (Sections 9-11), address the QueryBuilder that constructs URLs for those resources.

**Core API Surface:** CSAPIQueryBuilder is the primary developer-facing API with:

- **70-80 methods** across 9 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands)
- **Complex query parameters:** Temporal (phenomenonTime, resultTime, validTime), spatial (bbox, geometry), filtering (systemType, property filters), pagination (limit, offset), format negotiation, sorting
- **Resource availability validation:** Checking if endpoints exist before constructing URLs (via conformance and collection info)
- **Nested endpoint construction:** System → DataStreams → Observations chains, System → Deployments, ControlStream → Commands
- **URL correctness:** Protocol, host, path structure, query parameter encoding, special character handling

This research defines:

- **Method Coverage:** All 70-80 methods with test specifications per resource type
- **URL Validation Depth:** What constitutes "meaningful" URL testing (parse protocol/host/path/query, not just string.includes checks)
- **Query Parameter Testing:** Systematic coverage of all parameter combinations (pagination, temporal, spatial, filtering, optional parameters)
- **Edge Cases:** Optional parameters, encoding edge cases (spaces, special chars, international), availability checks, already-encoded values
- **Test Organization:** How to structure 70-80 method tests maintainably (single vs multiple files, shared utilities)
- **Fixture Requirements:** Collection info, conformance responses for all 9 resource types

### Sequencing Rationale

- **Position 12:** After format testing requirements (9: SensorML, 10: SWE Common, 11: GeoJSON CSAPI) establishes what resources need URLs, now define how QueryBuilder constructs those URLs
- **Before Section 13:** Resource method testing requires QueryBuilder to construct request URLs
- **Before Section 14:** Integration workflows require QueryBuilder methods
- **Critical Foundation:** QueryBuilder is the primary API surface developers interact with (~70-80 methods)

---

## 2. Research Questions

### Core Questions

1. How many methods exist in CSAPIQueryBuilder across all 9 resource types?
2. What constitutes "meaningful" URL testing vs "trivial" (is `url.includes('/systems')` sufficient)?
3. What query parameter categories exist and how to test them systematically?
4. How should tests be organized for ~70-80 methods (single file or per-resource)?
5. What test utilities are needed (URL parsing, query parameter validation, encoding validation)?
6. What fixtures are required (conformance responses, collection info)?

### Detailed Questions

### Detailed Questions

**CSAPIQueryBuilder Architecture (7 questions):**

1. How many methods exist in CSAPIQueryBuilder?
2. What are the method categories (GET/POST/PUT/PATCH/DELETE)?
3. What resource types are covered (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands)?
4. How many methods per resource type?
5. What query parameters are supported per method?
6. What validation logic exists in QueryBuilder?
7. What dependencies exist (collection info, conformance)?

**Method Inventory (10 questions):** 8. **Systems:** What methods exist? (getSystems, getSystem, createSystem, updateSystem, patchSystem, deleteSystem, getSystemDataStreams, getSystemDeployments, etc.) 9. **Deployments:** What methods exist? 10. **Procedures:** What methods exist? 11. **SamplingFeatures:** What methods exist? 12. **Properties:** What methods exist? 13. **DataStreams:** What methods exist? 14. **Observations:** What methods exist? 15. **ControlStreams:** What methods exist? 16. **Commands:** What methods exist? 17. What cross-resource navigation methods exist?

**URL Validation Depth (8 questions):** 18. What constitutes "meaningful" URL testing vs "trivial"? 19. Is checking `url.includes('/systems')` sufficient? (NO - need protocol, host, path, query parsing) 20. What URL components must be validated (protocol, host, path, query, hash)? 21. How to validate path structure systematically? 22. How to validate query parameters systematically? 23. How to validate URL encoding? 24. What tools/utilities for URL parsing and validation? 25. How to create parseAndValidateUrl utility?

**Query Parameter Testing (11 questions):** 26. What query parameters exist across all methods? 27. **Pagination:** limit, offset - how to test defaults, edge cases (0, very large)? 28. **Filtering:** property filters, systemType - how to test vocabulary values, multiple filters? 29. **Temporal:** phenomenonTime, resultTime, validTime - how to test ISO 8601 formats (instant, interval)? 30. **Spatial:** bbox, geometry - how to test coordinate formats, encoding? 31. **Format negotiation:** format, encoding - how to test valid values, defaults? 32. **Sorting:** sortBy, sortOrder - how to test valid fields, asc/desc? 33. **Relationships:** parent, children, related resources - how to test? 34. How to test parameter combinations systematically? 35. How to test optional parameters (presence vs absence)? 36. How to test array parameters?

**Resource Availability Validation (4 questions):** 37. Does QueryBuilder check if resource endpoint exists before constructing URL? 38. How to test resource availability logic? 39. What error handling exists for unavailable resources? 40. What fixtures needed (collection info, conformance)?

**Nested Endpoint Construction (6 questions):** 41. What nested endpoint chains exist? 42. System → DataStreams → Observations 43. System → Deployments 44. System → ControlStreams → Commands 45. How to test nested endpoint construction? 46. How to validate parent-child relationships?

**URL Encoding Edge Cases (6 questions):** 47. How to test space encoding (%20 vs +)? 48. How to test special character encoding (/, &, =, +)? 49. How to test international characters (UTF-8)? 50. How to test reserved characters in values? 51. How to test already-encoded values (double-encoding prevention)? 52. What encoding validation utility is needed?

**Implementation Guide Specifications (5 questions):** 53. What QueryBuilder testing specifications exist in Implementation Guide? 54. What test structure is recommended? 55. What test depth is specified? 56. What fixtures are specified? 57. What coverage targets are specified?

**Upstream URL Builder Patterns (5 questions):** 58. How do other implementations test URL builders (EDR, OGC API)? 59. What URL validation depth exists upstream? 60. What query parameter testing patterns exist? 61. What assertion patterns are used for URLs? 62. What URL parsing utilities exist?

**Method Categories and Testing Strategies (6 questions):** 63. **GET methods:** How to test collection queries (pagination, filtering)? 64. **GET methods:** How to test single resource retrieval (ID handling, encoding)? 65. **POST methods:** How to test resource creation URLs? 66. **PUT methods:** How to test full resource update URLs? 67. **PATCH methods:** How to test partial resource update URLs? 68. **DELETE methods:** How to test resource deletion URLs?

**Error Handling (5 questions):** 69. What error conditions must be tested? 70. How to handle unavailable resources (not in conformance)? 71. How to handle invalid parameters (wrong type, format)? 72. How to handle missing required parameters? 73. What error messages should be provided?

**Fixture Requirements (4 questions):** 74. What collection info fixtures are needed (one per resource type)? 75. What conformance response fixtures are needed (all resources, subset)? 76. What resource availability scenarios need fixtures? 77. How to organize fixtures for 9 resource types?

**Test Organization Strategies (5 questions):** 78. One test file or multiple (per resource type)? 79. How to structure describe blocks? 80. How to avoid repetitive test code? 81. What test utilities can reduce duplication? 82. What's the test-to-method ratio (1:1, 2:1, 3:1)?

**Test Depth Per Method (4 questions):** 83. How many tests per method (average ~3)? 84. What scenarios must be tested per method (no params, all params, optional params, encoding)? 85. Happy path only or edge cases too? 86. How to prioritize test scenarios (CRITICAL/HIGH/MEDIUM/LOW)?

---

## 3. Primary Resources

- **CSAPI Implementation Guide:** [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) (CSAPIQueryBuilder specification with all method signatures)
- **ROADMAP.md:** [docs/planning/ROADMAP.md](../../../planning/ROADMAP.md) (Phase 2 lists 9 resource type tasks)
- **URL Building Architecture:** [docs/research/upstream/url-building-analysis.md](../../upstream/url-building-analysis.md)

---

## 4. Supporting Resources

- **Section 8 Deliverable:** CSAPI specification requirements (query parameter specs from Part 1 & 2)
- **Section 6 Deliverable:** "Meaningful vs Trivial" Definition (URL testing depth guidance)
- **Section 1-2 Deliverables:** Upstream URL builder test patterns (EDR, OGC API)
- **Query Parameter Requirements:** [docs/research/requirements/csapi-query-parameters.md](../../requirements/csapi-query-parameters.md)
- URL parsing library (Node.js `URL` API)
- Query string parser
- URL encoding utilities

---

## 5. Research Methodology

---

## 5. Research Methodology

**Phase 1: QueryBuilder Method Inventory (30-45 minutes)**

- Read Implementation Guide CSAPIQueryBuilder specification
- List all CSAPIQueryBuilder methods (expected ~70-80 methods)
- Categorize by resource type (9 types) and HTTP method (GET/POST/PUT/PATCH/DELETE)
- Document query parameters per method
- Document nested endpoint methods (System → DataStreams, etc.)
- Create method inventory matrix (methods per resource type)
- Estimated time: 30-45 minutes

**Phase 2: Upstream URL Builder Analysis (30-45 minutes)**

- Review Section 1-2 deliverables (EDR and upstream URL builder patterns)
- Analyze URL builder test patterns from upstream
- Document URL validation depth (how deep do upstream tests go?)
- Extract assertion patterns (parseAndValidateUrl approaches)
- Identify test utilities (URL parsing, query parameter validation)
- Create URL testing best practices guide
- Estimated time: 30-45 minutes

**Phase 3: URL Validation Strategy Design (30-45 minutes)**

- Define "meaningful" URL testing criteria (protocol, host, path, query parsing vs trivial string.includes)
- Design URL parsing/validation approach (parseAndValidateUrl utility spec)
- Document query parameter testing strategy (systematic coverage of pagination, temporal, spatial, filtering, optional, encoding)
- Design encoding validation approach (edge cases: spaces, special chars, international, already-encoded)
- Create URL validation utility specifications
- Define test depth standards per method
- Estimated time: 30-45 minutes

**Phase 4: Method-by-Method Test Planning (45-60 minutes)**

- For each resource type, document test requirements per method
- Identify shared test patterns across methods
- Design test organization structure (single file vs multiple files per resource)
- Define fixture requirements (conformance responses, collection info)
- Estimate test count and lines per resource type
- Create test specification template
- Estimated time: 45-60 minutes

**Total Estimated Time: 2-3 hours**

---

## 6. Success Criteria

- [ ] All ~70-80 CSAPIQueryBuilder methods inventoried (across 9 resource types)
- [ ] Method categories documented (GET collection/item, POST, PUT, PATCH, DELETE per resource)
- [ ] "Meaningful" URL testing approach defined (protocol/host/path/query parsing, not trivial string checks)
- [ ] Query parameter testing strategy comprehensive (pagination, temporal, spatial, filtering, optional, encoding)
- [ ] URL encoding edge cases identified (spaces, special chars, international, already-encoded, reserved chars)
- [ ] Nested endpoint testing strategy defined (System → DataStreams → Observations chains)
- [ ] Resource availability validation approach defined (conformance checking fixtures)
- [ ] Test organization structure decided (recommendation: multiple files per resource type)
- [ ] Test utilities specified (parseAndValidateUrl, validateQueryParams, validateEncoding)
- [ ] Fixture requirements documented (~11 fixtures: conformance responses, collection info per resource)
- [ ] Testing estimates realistic (188 tests, 1,880-2,256 lines, 22-29 hours)

**Validation:**

- All 86 research questions answered
- All methods from Implementation Guide covered
- Test depth meets "meaningful" criteria from Section 6
- URL validation goes beyond trivial string checks
- Query parameter coverage systematic
- Fixture count manageable
- Test organization maintainable

---

## 7. Deliverable

**Document Location:** `docs/deliverables/testing/querybuilder-testing-strategy.md`

**Required Sections:**

### 1. Executive Summary

- Total methods to test: ~70-80 across 9 resource types
- Testing priorities (CRITICAL: GET methods, query parameters; HIGH: POST/PUT/PATCH; MEDIUM: DELETE, edge cases)
- URL validation approach (parseAndValidateUrl utility for protocol/host/path/query)
- Estimated test lines (1,880-2,256 lines)
- Test organization strategy (multiple files recommended: one per resource type)

### 2. Method Inventory Matrix

- Table showing methods per resource type and HTTP method category
- Expected breakdown: 9 GET collection, 9 GET item, 9 POST, 9 PUT, 9 PATCH, 9 DELETE = 54 base methods
- Additional: ~15 nested endpoint methods, ~5 cross-resource navigation
- **Grand Total: ~70-80 methods**

### 3. "Meaningful" URL Testing Definition

- Trivial example (DON'T DO): `expect(url).toContain('/systems')`
- Meaningful example (DO THIS): Parse URL, validate protocol/host/pathname, validate query parameters as objects
- URL validation utility specification: `parseAndValidateUrl(url, expected: {protocol, host, pathname, query})`

### 4. Query Parameter Testing Strategy

- Table of parameter categories: Pagination, Temporal, Spatial, Filtering, Format, Sorting, Optional, Arrays, Encoding
- Test approach per category (test with values, test defaults, test edge cases, test encoding)
- Priority per category

### 5. Resource Type Testing Requirements

- Per resource type matrix (Systems example provided)
- Columns: Method, Parameters, URL Pattern, Test Scenarios, Test Count, Priority
- Repeat for all 9 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands)

### 6. Nested Endpoint Testing

- Table of nested chains: System → DataStreams, System → Deployments, DataStream → Observations, System → ControlStreams, ControlStream → Commands
- URL patterns for each nested chain
- Test scenarios (valid ID, params, encoding)

### 7. URL Encoding Edge Cases

- Table: Edge Case, Test Input, Expected Encoding, Test Priority
- Cases: Space (%20), Forward slash (%2F), Ampersand (%26), Equals (%3D), Plus (%2B), International (UTF-8 %), Already encoded (no double-encoding)

### 8. Resource Availability Validation Testing

- Table: Scenario, Test Requirement, Priority
- Cases: Resource available (construct URL), Resource unavailable (throw error/return null), Nested resource unavailable (check parent), Collection info missing (handle gracefully)
- Fixtures needed: conformance-all-resources.json, conformance-subset.json, collection-info-{resourcetype}.json

### 9. Error Condition Testing

- Table: Error Condition, Test Scenario, Expected Behavior, Priority
- Cases: Invalid parameter value, Missing required parameter, Resource not available, Invalid temporal format, Invalid bbox format

### 10. Test Organization Structure

- **Option 1:** Single file (~1,200-1,800 lines) - describe block structure
- **Option 2 (RECOMMENDED):** Multiple files (one per resource type, ~120-300 lines each, total ~1,200-1,880 lines)
- File naming: `csapi-query-builder-{resourcetype}.spec.ts`

### 11. Test Utility Specifications

- `parseAndValidateUrl(url, expected)` - returns parsed URL after validating structure
- `validateQueryParams(url, expected)` - validates query parameters as object
- `validateEncoding(url, param, expectedValue)` - validates URL encoding correctness

### 12. Fixture Requirements

- Directory: `fixtures/csapi-querybuilder/`
- conformance-all-resources.json (all 9 resource types available)
- conformance-subset.json (only some resources available)
- collection-info-{resourcetype}.json (9 files, one per resource type)
- **Total: ~11 fixtures**

### 13. Testing Estimates

- Table per resource type: Methods, Tests per Method (~3 avg), Total Tests, Lines per Test (~11 avg), Total Lines, Time Estimate
- **Grand Total: 188 tests, 1,880-2,256 lines, 22-29 hours**

### 14. Testing Priorities

- **CRITICAL:** All GET collection methods (9), all GET item methods (9), query parameter validation, URL encoding, nested endpoints (top 5)
- **HIGH:** POST/PUT/PATCH methods (27), optional parameter handling, resource availability validation
- **MEDIUM:** DELETE methods (9), advanced parameter combinations, edge case encoding
- **LOW:** Performance testing, very large parameter values, complex filter combinations

### 15. Validation Against Upstream Patterns

- Compare with Section 1-2 findings (EDR, OGC API URL builder tests)
- URL validation depth alignment
- Assertion pattern alignment
- Quality standards alignment

### 16. Integration with Implementation Guide

- Cross-validate with Implementation Guide QueryBuilder specification
- Document alignment (✅), gaps (⚠️), conflicts (❌)

### 17. Risks and Edge Cases

- Table: Risk/Edge Case, Likelihood, Impact, Mitigation
- Risks: Test suite very large, URL validation utilities missing, Encoding edge cases missed, Resource availability logic complex, Parameter combinations explosive

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 8: CSAPI Specification Test Requirements (query parameter specs from Part 1 & 2)
- Section 6: "Meaningful vs Trivial" Definition (URL testing depth guidance)
- Section 1-2: Upstream URL Builder Test Patterns (EDR, OGC API patterns)
- Implementation Guide: CSAPIQueryBuilder specification (method signatures, parameters)

**This Section Blocks:**

- Section 13: Resource Method Testing Requirements (uses QueryBuilder to construct request URLs)
- Section 14: Integration Test Workflows (uses QueryBuilder methods for discovery, observation retrieval, command workflows)
- Section 15: Fixture Sourcing Strategy (conformance and collection info fixtures)
- Section 36: Test Quality Checklist (QueryBuilder test validation criteria)

---

## 9. Research Status Checklist

**Start Date:** February 5, 2026  
**Completion Date:** February 5, 2026  
**Actual Time:** ~3 hours

- [x] **Phase 1 Complete:** QueryBuilder method inventory (80 methods across 9 resource types - Systems: 12, Deployments: 8, Procedures: 8, SamplingFeatures: 8, Properties: 6, DataStreams: 11, Observations: 9, ControlStreams: 8, Commands: 10)
- [x] **Phase 2 Complete:** Upstream URL builder analysis (validated against EDR patterns, aligned URL validation depth, confirmed no conflicts)
- [x] **Phase 3 Complete:** URL validation strategy designed (parseAndValidateUrl utility specified, meaningful vs trivial testing defined with examples)
- [x] **Phase 4 Complete:** Method-by-method test planning (all 80 methods have test specifications across Sections 5-13 of deliverable, 188 test scenarios total)

---

## 10. Notes and Open Questions

**URL Validation Depth:**

- "Meaningful" URL testing requires parsing URL into components (protocol, host, pathname, query parameters as objects)
- Trivial tests like `expect(url).toContain('/systems')` are insufficient - must validate structure systematically
- parseAndValidateUrl utility is critical for consistent validation across all tests

**Test Organization:**

- **Recommendation:** Multiple files (one per resource type) for maintainability
- Single file would be 1,800+ lines, hard to navigate
- Per-resource files: ~150-300 lines each, easier to maintain and review
- Shared utilities (parseAndValidateUrl, validateQueryParams, validateEncoding) reduce duplication

**Query Parameter Testing Strategy:**

- Systematic coverage required: pagination, temporal, spatial, filtering, format, sorting, optional parameters, arrays, encoding
- Parameter combinations can explode - prioritize common combinations, use parametrized tests where appropriate
- Edge cases critical: spaces (%20), special chars (/, &, =, +), international (UTF-8), already-encoded (no double-encoding)

**Resource Availability Validation:**

- QueryBuilder should check conformance/collection info before constructing URLs
- Need explicit fixtures: conformance-all-resources.json, conformance-subset.json, collection-info-{resourcetype}.json (9 files)
- Test scenarios: resource available (success), resource unavailable (error/null), nested resource unavailable (check parent)

**Nested Endpoint Complexity:**

- Key chains: System → DataStreams, System → Deployments, DataStream → Observations, System → ControlStreams, ControlStream → Commands
- Must validate parent-child relationship construction
- Test ID encoding, parameter passing, path structure

**Risks and Mitigation:**

- **Risk:** Test suite becomes unmaintainably large (2,000+ lines) → **Mitigation:** Multiple files per resource, shared utilities
- **Risk:** URL validation utilities insufficient → **Mitigation:** Robust parseAndValidateUrl, extensive query parameter utilities
- **Risk:** Parameter combinations create test explosion → **Mitigation:** Prioritize common combinations, parametrize tests
- **Risk:** Resource availability logic untested → **Mitigation:** Explicit fixtures and test scenarios

**Research Completed:**

- ✅ Deliverable created: [12-querybuilder-testing-strategy.md](../findings/12-querybuilder-testing-strategy.md)
- ✅ All 80 methods inventoried with complete test specifications
- ✅ URL validation approach defined (parseAndValidateUrl, validateEncoding, createTestEndpoint utilities)
- ✅ Query parameter testing strategy for 10 categories
- ✅ 15 URL encoding edge cases identified
- ✅ Test organization recommended: 1 shared utilities + 9 per-resource files (90-220 lines each)
- ✅ Fixture requirements: 5 JSON files documented
- ✅ Testing estimates: 188 tests, 1,880-2,256 lines, 22-29 hours
- ✅ Validated against upstream patterns and Implementation Guide

**Next Steps After Completion:**

1. Use test requirements to implement QueryBuilder tests (Phase 2, Tasks 2-10)
2. Create parseAndValidateUrl test utility
3. Create conformance and collection info fixtures (5 total: conformance-all-resources, conformance-part1-only, collection-info-all-resources, collection-info-part1-only, collection-info-no-csapi)
4. Implement multi-file test organization (9 files: one per resource type)
5. Validate test coverage against all 80 methods
