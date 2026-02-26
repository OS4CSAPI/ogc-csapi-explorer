# Research Plan: Resource Method Testing Patterns (9 Resource Types)

**Section:** 13 of 38  
**Status:** Complete ✅  
**Last Updated:** February 6, 2026  
**Completion Date:** February 6, 2026  
**Actual Time:** 2 hours  
**Estimated Time:** 1.5-2 hours  
**Actual Lines:** 1,668 lines (20,000 words)  
**Estimated Lines:** 1,390-1,668 lines (overlaps with Section 12 QueryBuilder tests)  
**Deliverable:** `13-resource-method-testing-patterns.md`

---

## 1. Research Objective

Define consistent testing pattern for resource methods (CRUD operations) that can be applied systematically across all 9 CSAPI resource types. Create reusable template that ensures uniform test coverage and quality.

### Why This Research Thirteenth

**Dependency Chain:** After QueryBuilder URL construction testing (Section 12), define testing for the resource operations that use those URLs.

**Consistency Need:** With 9 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands), need consistent testing approach to:

- **Avoid duplication:** Don't write same tests 9 times - create reusable template
- **Ensure completeness:** All resource types get equal coverage (GET collection/item, POST, PUT, PATCH, DELETE)
- **Maintain quality:** Uniform "meaningful" test depth across all resource types
- **Enable reuse:** Template/pattern that scales as new resource types are added

This research defines:

- **CRUD Pattern:** Consistent testing for Create, Read, Update, Delete operations applicable to all 9 resource types
- **Query Pattern:** Consistent testing for collection queries with pagination, filtering, temporal/spatial parameters
- **Template:** Reusable test structure (describe blocks, test utilities, assertions) applicable to all resource types
- **Differentiation:** What's unique per resource type (systemType for Systems, phenomenonTime for Observations) vs shared (limit, offset, bbox)
- **Test Depth:** What constitutes "meaningful" resource method testing (URL validation, query parameter encoding, error conditions)

### Sequencing Rationale

- **Position 13:** After QueryBuilder testing strategy (Section 12) establishes how URLs are constructed, now define the consistent pattern for testing those methods across all resource types
- **Before Section 14:** Integration workflows require resource methods, this establishes the testing pattern
- **Template Focus:** Emphasizes consistency and reusability across 9 resource types to avoid duplication and ensure quality
- **Integration with Section 12:** Resource method tests ARE QueryBuilder tests - this section defines the pattern, Section 12 defines the implementation

---

## 2. Research Questions

### Core Questions

1. What CRUD operations exist per resource type and are they consistent?
2. What's the universal test template that applies to all 9 resource types?
3. What's resource-specific vs shared across all resource types?
4. How to design tests for maximum reusability (shared utilities, parametrized tests)?
5. How many tests per resource type using the template (base + resource-specific)?
6. What fixtures are needed (universal vs resource-specific)?

### Detailed Questions

### Detailed Questions

**CRUD Operations Overview (5 questions):**

1. What CRUD operations exist per resource type (GET collection, GET item, POST, PUT, PATCH, DELETE)?
2. Are all operations supported for all 9 resource types consistently?
3. What operations are read-only vs read-write?
4. What's the priority of operations (GET > POST > PUT > PATCH > DELETE)?
5. How do operations differ between resource types?

**GET Collection Pattern (7 questions):** 6. What's consistent across all `getSomethings()` methods (pagination, bbox)? 7. What query parameters are common (limit, offset, bbox)? 8. What query parameters are resource-specific (systemType, phenomenonTime, validTime)? 9. How to test pagination systematically? 10. How to test filtering systematically? 11. What assertions are needed for collection responses? 12. What fixtures are needed for collection responses?

**GET Item Pattern (5 questions):** 13. What's consistent across all `getSomething(id)` methods? 14. How to test item retrieval systematically? 15. What assertions are needed for item responses? 16. What error conditions (404 not found, etc.)? 17. What fixtures are needed for item responses?

**POST Create Pattern (6 questions):** 18. What's consistent across all `createSomething()` methods? 19. How to test resource creation URLs? 20. What request body validation is needed? 21. What response validation is needed? 22. What error conditions (400 bad request, 409 conflict, etc.)? 23. What fixtures are needed (request bodies)?

**PUT Update Pattern (6 questions):** 24. What's consistent across all `updateSomething(id)` methods? 25. How to test full resource update? 26. What request body validation is needed? 27. What response validation is needed? 28. What error conditions (404, 400, etc.)? 29. What fixtures are needed?

**PATCH Update Pattern (6 questions):** 30. What's consistent across all `patchSomething(id)` methods? 31. How to test partial resource update? 32. What request body validation is needed? 33. What response validation is needed? 34. What error conditions? 35. What fixtures are needed?

**DELETE Pattern (4 questions):** 36. What's consistent across all `deleteSomething(id)` methods? 37. How to test resource deletion? 38. What response validation is needed? 39. What error conditions (404, 409 conflict, etc.)?

**Resource-Specific Testing (9 questions):** 40. **Systems:** What's unique to Systems resource methods (systemType, parent filters)? 41. **Deployments:** What's unique to Deployments resource methods (validTime temporal filter)? 42. **Procedures:** What's unique to Procedures resource methods (procedureType filter)? 43. **SamplingFeatures:** What's unique to SamplingFeatures resource methods (samplingFeatureType, sampledFeature)? 44. **Properties:** What's unique to Properties resource methods (observableProperty)? 45. **DataStreams:** What's unique to DataStreams resource methods (observedProperty, phenomenonTime)? 46. **Observations:** What's unique to Observations resource methods (datastream, phenomenonTime, resultTime)? 47. **ControlStreams:** What's unique to ControlStreams resource methods (systemId)? 48. **Commands:** What's unique to Commands resource methods (controlstream, executionTime)?

**Query Parameters by Operation (5 questions):** 49. What query parameters apply to GET collections across all resource types? 50. Do POST/PUT/PATCH have query parameters? 51. What temporal parameters exist per resource type (validTime, phenomenonTime, resultTime, executionTime)? 52. What spatial parameters exist per resource type (bbox, geometry)? 53. What filtering parameters exist per resource type (systemType, parent, datastream, etc.)?

**Request Body Validation (6 questions):** 54. What validation is needed for POST bodies? 55. What validation is needed for PUT bodies? 56. What validation is needed for PATCH bodies? 57. How to test required vs optional fields? 58. How to test invalid field types? 59. How to test missing required fields?

**Response Validation (5 questions):** 60. What status codes are expected per operation (200, 201, 204, 404, 400, 409)? 61. What response body structure is expected? 62. What headers are expected (Location, ETag, etc.)? 63. How to validate response matches request? 64. What error response structure is expected?

**Error Conditions by Operation (6 questions):** 65. GET collection: What errors are possible? 66. GET item: What errors are possible (404 not found, etc.)? 67. POST create: What errors are possible (400 bad request, 409 conflict, etc.)? 68. PUT update: What errors are possible (404, 400, etc.)? 69. PATCH update: What errors are possible? 70. DELETE: What errors are possible (404, 409 conflict, etc.)?

**Template Design (5 questions):** 71. What describe block structure scales across 9 resource types? 72. What test utilities can be shared (parseAndValidateUrl from Section 12)? 73. What fixtures can be reused across resource types? 74. How to parametrize tests for multiple resource types? 75. What's the test-to-operation ratio (tests per CRUD operation)?

---

## 3. Primary Resources

- **CSAPI Implementation Guide:** [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) (Resource Method Tests specification)
- **ROADMAP.md:** [docs/planning/ROADMAP.md](../../../planning/ROADMAP.md) (Phase 2 lists 9 resource type tasks)
- **CRUD Operations Requirements:** [docs/research/requirements/csapi-crud-operations.md](../../requirements/csapi-crud-operations.md)

---

## 4. Supporting Resources

- **Section 12 Deliverable:** QueryBuilder testing strategy (resource methods use QueryBuilder to construct URLs)
- **Section 8 Deliverable:** CSAPI specification requirements (resource operation specs from Part 1 & 2)
- **Part 1 Requirements:** [docs/research/requirements/csapi-part1-requirements.md](../../requirements/csapi-part1-requirements.md)
- **Part 2 Requirements:** [docs/research/requirements/csapi-part2-requirements.md](../../requirements/csapi-part2-requirements.md)
- **Section 6 Deliverable:** "Meaningful vs Trivial" Definition (test depth guidance)
- **Section 1-2 Deliverables:** Upstream resource method test patterns

---

## 5. Research Methodology

---

## 5. Research Methodology

**Phase 1: CRUD Operations Analysis (20-30 minutes)**

- Review Implementation Guide resource method specifications
- Document CRUD operations per resource type (GET collection, GET item, POST, PUT, PATCH, DELETE)
- Identify common patterns across operations (all use QueryBuilder, all have pagination)
- Identify resource-specific variations (systemType for Systems, phenomenonTime for Observations)
- Create CRUD operation matrix (9 resource types × 6 operations)
- Estimated time: 20-30 minutes

**Phase 2: Upstream Resource Method Analysis (20-30 minutes)**

- Review Section 1-2 deliverables (upstream patterns from EDR, OGC API)
- Analyze how upstream tests resource methods
- Extract assertion patterns (URL validation, response structure)
- Document test utilities (parseAndValidateUrl, validateQueryParams)
- Create resource method testing best practices
- Estimated time: 20-30 minutes

**Phase 3: Template Design (30-45 minutes)**

- Design consistent test structure for all resource types (describe block hierarchy)
- Define shared test utilities (from Section 12)
- Design fixture organization (universal vs resource-specific)
- Create test template with placeholders (ResourceType, resourcetypes path)
- Document how to apply template to each resource type
- Estimated time: 30-45 minutes

**Phase 4: Resource-Specific Differentiation (20-30 minutes)**

- Document what's unique per resource type (query parameters, fixtures)
- Define how to extend template for uniqueness (additional tests within describe blocks)
- Create resource-specific test addendum examples (Systems, Deployments, Observations)
- Document fixture requirements per resource type (2 fixtures per type)
- Estimated time: 20-30 minutes

**Total Estimated Time: 1.5-2 hours**

---

## 6. Success Criteria

- [ ] Universal test template defined and applicable to all 9 resource types
- [ ] CRUD operation matrix complete (9 resource types × 6 operations)
- [ ] Resource-specific variations documented for each type (query parameters, fixtures)
- [ ] Query parameter testing checklist complete (universal + per-resource)
- [ ] Test depth meets "meaningful" criteria from Section 6 (URL validation, query parameters, encoding, error conditions)
- [ ] Fixture requirements defined (universal + resource-specific)
- [ ] Testing estimates realistic per resource type (12 base tests + 2-7 resource-specific = 14-19 tests per type)
- [ ] Application guide clear for new resource types (7-step process)
- [ ] Template design emphasizes reusability and consistency

**Validation:**

- All 75 research questions answered
- Template structure proven reusable across different resource types
- Resource-specific variations identified for all 9 types
- Test depth goes beyond trivial checks
- Fixture count manageable (~25 fixtures total)
- Test estimates align with Section 12 (combined ~1,400-1,700 lines)
- Template is maintainable and scalable

---

## 7. Deliverable

**Document Location:** `docs/deliverables/testing/resource-method-testing-template.md`

**Required Sections:**

### 1. Executive Summary

- Universal CRUD pattern across 9 resource types
- Consistent test structure and depth
- Reusable template with resource-specific extensions
- Estimated test lines per resource type (140-228 lines)
- Test organization strategy (part of QueryBuilder tests from Section 12)

### 2. CRUD Operations Matrix

- Table: 9 resource types × 6 operations (GET collection, GET item, POST, PUT, PATCH, DELETE)
- All operations supported across all resource types
- Priority per resource type (CRITICAL: Systems, DataStreams, Observations; HIGH: Deployments, SamplingFeatures, Properties; MEDIUM: Procedures, ControlStreams, Commands)

### 3. Universal Test Template

- Complete TypeScript template with describe block structure
- Apply to each resource type by replacing placeholders
- Covers: GET collection (no params, pagination, filtering), GET item (valid ID, encoding), POST create, PUT update, PATCH update, DELETE, error handling
- Uses parseAndValidateUrl utility from Section 12

### 4. Resource-Specific Variations

- **Systems:** systemType filter, parent filter
- **Deployments:** validTime temporal filter
- **Procedures:** procedureType filter
- **SamplingFeatures:** samplingFeatureType filter, sampledFeature reference
- **Properties:** observableProperty validation
- **DataStreams:** observedProperty, phenomenonTime filter
- **Observations:** datastream filter, phenomenonTime filter, resultTime filter
- **ControlStreams:** systemId filter
- **Commands:** controlstream filter, executionTime filter

### 5. Query Parameter Testing Checklist

- Universal parameters table: limit, offset, bbox (all resource types)
- Resource-specific parameters table: per resource type with test scenarios

### 6. Test Depth Definition

- "Meaningful" characteristics: Use parseAndValidateUrl, validate complete URL structure, test query parameters systematically, test resource-specific parameters, test encoding, test error conditions, use realistic fixtures
- "Trivial" to avoid: Just check url.includes(), skip query parameter validation, skip resource-specific tests, skip encoding, skip error conditions

### 7. Test Organization

- **Recommendation:** Resource method tests are part of QueryBuilder tests (Section 12 multi-file organization)
- Not separate files - methods are thin wrappers around QueryBuilder
- This section defines the pattern, Section 12 defines the implementation

### 8. Fixture Requirements

- Directory: fixtures/csapi-resource-methods/
- Universal fixtures: conformance-all-resources.json, collections-info.json
- Resource-specific fixtures: 2 per resource type (collection response, item response) = 18 fixtures
- Error fixtures: 404-not-found.json, 400-bad-request.json, 409-conflict.json
- **Total: ~25 fixtures**

### 9. Testing Estimates per Resource Type

- Table per resource type: Base Tests (Template), Resource-Specific Tests, Total Tests, Lines per Test, Total Lines, Time Estimate
- **Grand Total: 139 tests, 1,390-1,668 lines, 19-23 hours**
- **Note:** These estimates overlap with Section 12 QueryBuilder testing

### 10. Testing Priorities

- **CRITICAL:** GET collection with pagination (all 9), GET item (all 9), resource-specific query parameters (Systems, Deployments, Observations)
- **HIGH:** GET collection with all query parameters, POST/PUT/PATCH methods, encoding tests, error conditions
- **MEDIUM:** DELETE methods, advanced query parameter combinations, edge case encoding
- **LOW:** Performance testing, very large result sets

### 11. Validation Against Upstream Patterns

- Compare with Section 1-2 findings
- Assertion pattern alignment
- Test depth alignment
- Quality standards alignment

### 12. Integration with Implementation Guide

- Cross-validate with Implementation Guide resource method specifications
- Document alignment (✅), gaps (⚠️), conflicts (❌)

### 13. Application Guide

- **How to Apply Template to New Resource Type** (7 steps):
  1. Copy template describe block structure
  2. Replace `ResourceType` with actual resource type name
  3. Replace `resourcetypes` with actual path segment
  4. Add resource-specific query parameter tests
  5. Add resource-specific error condition tests
  6. Create 2 fixtures (collection response, item response)
  7. Run tests to verify ~12-15 tests pass
- **Estimated Time per Resource Type:** 1-2 hours (after template established)

### 14. Risks and Mitigation

- Table: Risk, Likelihood, Impact, Mitigation
- Risks: Template doesn't fit all types, resource-specific variations missed, test duplication, template becomes outdated

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 12: QueryBuilder Testing Strategy (resource methods use QueryBuilder to construct URLs)
- Section 8: CSAPI Specification Test Requirements (resource operation specs from Part 1 & 2)
- Section 6: "Meaningful vs Trivial" Definition (test depth guidance)
- Section 1-2: Upstream Resource Method Test Patterns
- CRUD Operations Requirements: [docs/research/requirements/csapi-crud-operations.md](../../requirements/csapi-crud-operations.md)

**This Section Blocks:**

- Section 14: Integration Test Workflows (uses resource methods for discovery, observation retrieval, command workflows)
- Section 15: Fixture Sourcing Strategy (resource method fixtures)
- Section 36: Test Quality Checklist (resource method test validation criteria)

**Note:** This section provides the PATTERN/TEMPLATE. Section 12 provides the detailed implementation plan. These two sections together define complete QueryBuilder + resource method testing.

---

## 9. Research Status Checklist

- [ ] **Phase 1 Complete:** CRUD operations analysis (matrix of 9 resource types × 6 operations, common patterns identified)
- [ ] **Phase 2 Complete:** Upstream resource method analysis (test patterns, assertion styles, utilities)
- [ ] **Phase 3 Complete:** Template design (universal describe block structure, shared utilities, fixture organization)
- [ ] **Phase 4 Complete:** Resource-specific differentiation (unique parameters per type, extension approach, application guide)

---

## 10. Notes and Open Questions

**Template Design Philosophy:**

- **Reusability First:** Template must work for all 9 resource types with minimal modification
- **Consistency:** All resource types get equal test coverage (12 base tests minimum)
- **Extensibility:** Easy to add resource-specific tests without breaking template structure
- **Maintainability:** Clear placeholders, well-documented application process

**Integration with Section 12:**

- Resource method tests ARE QueryBuilder tests - not separate
- This section (13) defines the pattern/template
- Section 12 defines the implementation details (multi-file organization, fixtures, utilities)
- Together they provide complete testing strategy for ~70-80 methods

**Resource-Specific Variations:**

- **Systems (5 additional tests):** systemType vocabulary, parent reference, nested resources (datastreams, deployments)
- **Deployments (3 additional tests):** validTime temporal filter (required), platform reference
- **Observations (7 additional tests):** Most complex - datastream reference, phenomenonTime, resultTime, multiple temporal filters
- **Others (2-4 additional tests):** Various query parameters, vocabularies, references

**Fixture Strategy:**

- Universal fixtures shared across all resource types (conformance, collections)
- Resource-specific fixtures (2 per type: collection, item) for realistic testing
- Error fixtures shared (404, 400, 409)
- Total: ~25 fixtures (manageable)

**Test Organization:**

- Recommendation: Resource method tests integrated into QueryBuilder test files (from Section 12)
- Alternative: Separate files only if methods have significant logic beyond URL building (not expected)
- Shared utilities critical: parseAndValidateUrl, validateQueryParams, validateEncoding (from Section 12)

**Risks and Mitigation:**

- **Risk:** Template doesn't fit all resource types equally well → **Mitigation:** Design flexible template, document variations, allow extensions
- **Risk:** Resource-specific variations not comprehensive → **Mitigation:** Thorough analysis of all 9 resource types, checklist approach
- **Risk:** Template becomes maintenance burden → **Mitigation:** Keep template simple, focus on reusability, document clearly
- **Risk:** Test duplication across resource types → **Mitigation:** Maximize shared utilities, consider parametrized tests

**Next Steps After Completion:**

1. Apply template to all 9 resource types (Phase 2, Tasks 2-10)
2. Create shared test utilities (parseAndValidateUrl from Section 12)
3. Create universal fixtures (conformance, collections)
4. Create resource-specific fixtures (2 per type, 18 total)
5. Validate template against first implementation (Systems)
6. Iterate template based on learnings from first implementation

// ====================
// DELETE TESTS
// ====================
describe('deleteResourceType(id)', () => {
it('should build delete URL', () => {
const url = builder.deleteResourceType('resource-123');
validateUrl(url, {
pathname: '/collections/collection-id/resourcetypes/resource-123',
query: {}
});
});
});

// ====================
// ERROR HANDLING
// ====================
describe('Error Conditions', () => {
it('should handle missing ID for item operations', () => {
expect(() => builder.getResourceType('')).toThrow();
});

    // Resource-specific error conditions

});
});

````

#### 4. Resource-Specific Variations

**Systems Resource Additions:**

```typescript
// Add to getResourceTypes() describe block:
it('should build collection URL with systemType filter', () => {
  const url = builder.getSystems({ systemType: 'sensor' });
  validateUrl(url, {
    pathname: '/collections/collection-id/systems',
    query: { systemType: 'sensor' }
  });
});

it('should build collection URL with parent filter', () => {
  const url = builder.getSystems({ parent: 'parent-system-id' });
  validateUrl(url, {
    pathname: '/collections/collection-id/systems',
    query: { parent: 'parent-system-id' }
  });
});
````

**Deployments Resource Additions:**

```typescript
// Add to getResourceTypes() describe block:
it('should build collection URL with validTime filter', () => {
  const url = builder.getDeployments({
    validTime: '2024-01-01/2024-12-31',
  });
  validateUrl(url, {
    pathname: '/collections/collection-id/deployments',
    query: { validTime: '2024-01-01/2024-12-31' },
  });
});
```

**Observations Resource Additions:**

```typescript
// Add to getResourceTypes() describe block:
it('should build collection URL with phenomenonTime filter', () => {
  const url = builder.getObservations({
    phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z',
  });
  validateUrl(url, {
    pathname: '/collections/collection-id/observations',
    query: { phenomenonTime: '2024-01-01T00:00:00Z/2024-01-31T23:59:59Z' },
  });
});

it('should build collection URL with resultTime filter', () => {
  const url = builder.getObservations({
    resultTime: '2024-01-01T00:00:00Z',
  });
  validateUrl(url, {
    pathname: '/collections/collection-id/observations',
    query: { resultTime: '2024-01-01T00:00:00Z' },
  });
});

it('should build collection URL with datastream filter', () => {
  const url = builder.getObservations({
    datastream: 'datastream-123',
  });
  validateUrl(url, {
    pathname: '/collections/collection-id/observations',
    query: { datastream: 'datastream-123' },
  });
});
```

#### 5. Query Parameter Testing Checklist

**Universal Parameters (All Resource Types):**

```markdown
| Parameter | Test Scenarios                                                              | Priority |
| --------- | --------------------------------------------------------------------------- | -------- |
| limit     | Valid value (10), zero, very large (1000), negative (should error)          | HIGH     |
| offset    | Valid value (20), zero, very large, negative (should error)                 | HIGH     |
| bbox      | Valid bbox, invalid bbox (wrong format), edge cases (crossing antimeridian) | MEDIUM   |
```

**Resource-Specific Parameters:**

```markdown
| Resource Type    | Unique Parameters                      | Test Scenarios                                 |
| ---------------- | -------------------------------------- | ---------------------------------------------- |
| Systems          | systemType, parent                     | Valid types, invalid type, missing             |
| Deployments      | validTime, platform                    | Valid interval, open intervals, invalid format |
| Procedures       | procedureType                          | Valid type, invalid type                       |
| SamplingFeatures | samplingFeatureType, sampledFeature    | Valid type, invalid type, URI validation       |
| Properties       | observableProperty                     | Valid URI, invalid URI                         |
| DataStreams      | observedProperty, phenomenonTime       | URI validation, temporal validation            |
| Observations     | datastream, phenomenonTime, resultTime | ID validation, temporal validation             |
| ControlStreams   | systemId                               | Valid ID, invalid ID                           |
| Commands         | controlstream, executionTime           | ID validation, temporal validation             |
```

#### 6. Test Depth Definition

**"Meaningful" Resource Method Test Characteristics:**

✅ **DO:**

- Use parseAndValidateUrl utility (from Section 12)
- Validate complete URL structure (protocol, host, path, query)
- Test query parameters systematically (presence, encoding, combinations)
- Test resource-specific parameters thoroughly
- Test encoding of special characters
- Test error conditions (missing ID, invalid parameters)
- Use realistic fixtures when available

❌ **DON'T (Trivial):**

- Just check `url.includes('/resourcetype')`
- Skip query parameter validation
- Skip resource-specific parameter tests
- Skip encoding tests
- Skip error conditions
- Use overly simple fixtures

#### 7. Test Organization

**Option 1: Combined Resource Method Tests (within QueryBuilder test files)**

- Already covered in Section 12 (multi-file organization per resource type)
- Resource method tests are part of QueryBuilder tests

**Option 2: Separate Resource Method Test Files (if distinct from QueryBuilder)**

- Only if resource methods have significant logic beyond URL building
- Not recommended if methods are thin wrappers around QueryBuilder

**Recommendation:** Resource method tests are part of QueryBuilder tests (Section 12). This section defines the consistent pattern to apply.

#### 8. Fixture Requirements

```markdown
Fixture Directory: `fixtures/csapi-resource-methods/`

Universal Fixtures:

- conformance-all-resources.json (used by all)
- collections-info.json (used by all)

Resource-Specific Fixtures (per resource type):

- systems-collection-response.json
- systems-item-response.json
- deployments-collection-response.json
- deployments-item-response.json
- (etc. for all 9 resource types)

Error Fixtures:

- 404-not-found.json
- 400-bad-request.json
- 409-conflict.json

Total: ~25 fixtures (2 per resource type + 5 universal)
```

#### 9. Testing Estimates per Resource Type

```markdown
| Resource Type    | Base Tests (Template) | Resource-Specific Tests | Total Tests | Lines per Test | Total Lines     | Time Estimate   |
| ---------------- | --------------------- | ----------------------- | ----------- | -------------- | --------------- | --------------- |
| Systems          | 12                    | 5                       | 17          | 10-12          | 170-204         | 2-3 hours       |
| Deployments      | 12                    | 3                       | 15          | 10-12          | 150-180         | 2 hours         |
| Procedures       | 12                    | 2                       | 14          | 10-12          | 140-168         | 2 hours         |
| SamplingFeatures | 12                    | 3                       | 15          | 10-12          | 150-180         | 2 hours         |
| Properties       | 12                    | 2                       | 14          | 10-12          | 140-168         | 2 hours         |
| DataStreams      | 12                    | 4                       | 16          | 10-12          | 160-192         | 2-3 hours       |
| Observations     | 12                    | 7                       | 19          | 10-12          | 190-228         | 3 hours         |
| ControlStreams   | 12                    | 2                       | 14          | 10-12          | 140-168         | 2 hours         |
| Commands         | 12                    | 3                       | 15          | 10-12          | 150-180         | 2 hours         |
| **TOTAL**        | **108**               | **31**                  | **139**     | **~11 avg**    | **1,390-1,668** | **19-23 hours** |
```

**Note:** These estimates overlap with Section 12 QueryBuilder testing. Resource method tests ARE QueryBuilder tests.

#### 10. Testing Priorities

**CRITICAL (Must Have):**

- GET collection with pagination (all 9 resource types)
- GET item (all 9 resource types)
- Resource-specific query parameters (Systems, Deployments, Observations)

**HIGH (Should Have):**

- GET collection with all query parameters
- POST/PUT/PATCH methods
- Encoding tests
- Error conditions

**MEDIUM (Nice to Have):**

- DELETE methods
- Advanced query parameter combinations
- Edge case encoding

**LOW (Optional):**

- Performance testing
- Very large result sets

#### 11. Validation Against Upstream Patterns

Compare with Section 1-2 findings:

- How does upstream test resource methods?
- What assertion patterns exist?
- What test depth is used?
- Are we aligned with upstream quality standards?

#### 12. Integration with Implementation Guide

Cross-validate with Implementation Guide resource method specifications:

- ✅ Aligned: Template matches Implementation Guide
- ⚠️ Gap: Template not addressed in Implementation Guide
- ❌ Conflict: Template conflicts with Implementation Guide

#### 13. Application Guide

**How to Apply Template to New Resource Type:**

1. Copy template describe block structure
2. Replace `ResourceType` with actual resource type name (e.g., `Systems`)
3. Replace `resourcetypes` with actual path segment (e.g., `systems`)
4. Add resource-specific query parameter tests (from checklist in Section 5)
5. Add resource-specific error condition tests
6. Create 2 fixtures (collection response, item response)
7. Run tests to verify ~12-15 tests pass

**Estimated Time per Resource Type:** 1-2 hours (after template established)

#### 14. Risks and Mitigation

```markdown
| Risk                                      | Likelihood | Impact | Mitigation                                          |
| ----------------------------------------- | ---------- | ------ | --------------------------------------------------- |
| Template doesn't fit all resource types   | Low        | Medium | Design template flexible; allow extensions          |
| Resource-specific variations missed       | Medium     | Medium | Thorough resource type analysis; checklist          |
| Test duplication across resource types    | High       | Low    | Shared utilities; parametrized tests where possible |
| Template becomes outdated as spec evolves | Medium     | Medium | Document versioning; regular reviews                |
```

### Success Criteria

✅ Universal test template defined and applicable to all 9 resource types  
✅ Resource-specific variations documented for each type  
✅ Query parameter testing checklist complete  
✅ Test depth meets "meaningful" criteria from Section 6  
✅ Fixture requirements defined  
✅ Testing estimates realistic per resource type  
✅ Application guide clear for new resource types  
✅ Validated against upstream patterns  
✅ Cross-validated with Implementation Guide

### Validation

- Template structure proven reusable
- Resource-specific variations identified for all 9 types
- Test depth goes beyond trivial checks
- Fixture count manageable (~25 fixtures)
- Test estimates align with Section 12 (combined ~1,400-1,700 lines)
- Template is maintainable and scalable

---

## Cross-References

**Builds On:**

- Section 12: QueryBuilder Testing Strategy (resource methods use QueryBuilder)
- Section 8: CSAPI Specification Test Requirements (resource operation specs)
- Section 6: "Meaningful vs Trivial" Definition (test depth guidance)
- Section 1-2: Upstream resource method test patterns
- **CRUD Operations Requirements:** [docs/research/requirements/csapi-crud-operations.md](../../requirements/csapi-crud-operations.md)

**Critical For:**

- Section 14: Integration Test Workflows (uses resource methods)
- Section 15: Fixture Sourcing Strategy (resource method fixtures)
- Section 36: Test Quality Checklist (resource method test validation)

**Note:** This section provides the PATTERN/TEMPLATE. Section 12 provides the detailed implementation plan. These two sections together define complete QueryBuilder + resource method testing.

---

## Next Steps After Completion

1. Apply template to all 9 resource types (Phase 2, Tasks 2-10)
2. Create shared test utilities (parseAndValidateUrl from Section 12)
3. Create universal fixtures (conformance, collections)
4. Create resource-specific fixtures (2 per type, 18 total)
5. Validate template against first implementation (Systems)
6. Iterate template based on learnings

---

## Risks and Mitigation

**Risk:** Template doesn't fit all resource types equally well  
**Mitigation:** Design flexible template; document variations; allow extensions

**Risk:** Resource-specific variations not comprehensive  
**Mitigation:** Thorough analysis of all 9 resource types; checklist approach

**Risk:** Template becomes maintenance burden  
**Mitigation:** Keep template simple; focus on reusability; document clearly

**Risk:** Test duplication across resource types  
**Mitigation:** Maximize shared utilities; consider parametrized tests

---

## Research Status

- [ ] Phase 1: CRUD Operations Analysis (20-30 min)
- [ ] Phase 2: Upstream Resource Method Analysis (20-30 min)
- [ ] Phase 3: Template Design (30-45 min)
- [ ] Phase 4: Resource-Specific Differentiation (20-30 min)
- [ ] Deliverable Complete and Reviewed

**Total Estimated Time:** 1.5-2 hours  
**Actual Time:** _[To be filled during research]_  
**Started:** _[Date]_  
**Completed:** _[Date]_
