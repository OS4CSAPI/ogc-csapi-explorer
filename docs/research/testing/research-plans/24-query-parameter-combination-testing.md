# Section 24: Query Parameter Combination Testing - Research Plan

**Status:** ✅ Complete  
**Research Date:** February 6, 2026  
**Total Research Time:** 5.5 hours  
**Deliverable:** [findings/24-query-parameter-combination-testing.md](../findings/24-query-parameter-combination-testing.md)  
**Estimated Test Implementation Lines:** ~3,200 lines (120 scenarios)

---

## 1. Research Objective

Define testing strategy for 30+ query parameter combinations and precedence rules.

**Why 24th:** After pagination (Section 23), test complex query parameter interactions across spatial, temporal, and relationship parameters.

---

## 2. Research Questions

### Core Questions

1. What query parameters does CSAPI define?
2. How to test valid parameter combinations?
3. How to test invalid parameter combinations?
4. What parameter precedence rules exist?
5. How to test spatial + temporal + relationship parameters together?
6. What happens with conflicting parameters?

### Detailed Questions

- What are all the CSAPI query parameters?
- Which parameters can be combined?
- Which parameters are mutually exclusive?
- What is the precedence order?
- How do spatial parameters interact (bbox vs near vs within)?
- How do temporal parameters interact (datetime vs from/to)?
- How to test parameter validation?
- What error messages should appear for invalid combinations?
- How to test parameter encoding (URL encoding)?
- What are the default values?
- How to test parameter case sensitivity?

---

## 3. Primary Resources

- **Query Parameter Requirements**: [docs/research/requirements/query-parameter-requirements.md](../../requirements/query-parameter-requirements.md)
- **CSAPI OpenAPI Specifications**: Multiple parts define query parameters
- **OGC API - Common Query Parameters**: Standard parameters (bbox, datetime, limit, offset)
- **Implementation Guide**: [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md)

## 4. Supporting Resources

- Section 8 deliverable (CSAPI Spec Review - parameter definitions)
- Section 23 deliverable (Pagination - limit/offset/cursor parameters)
- Section 13 deliverable (Resource methods - parameter handling)
- OGC API - Features query parameter patterns

---

## 5. Research Methodology

### Phase 1: Query Parameter Inventory (TBD minutes)

**Objective:** Create complete inventory of CSAPI query parameters

**Tasks:**

1. Extract query parameters from CSAPI Part 1
2. Extract query parameters from CSAPI Part 2
3. Extract query parameters from CSAPI Part 3
4. Categorize parameters (spatial, temporal, relationship, pagination, format)
5. Document parameter data types and constraints
6. Create query parameter matrix (30+ parameters)

### Phase 2: Combination Rules Analysis (TBD minutes)

**Objective:** Analyze valid and invalid parameter combinations

**Tasks:**

1. Identify mutually exclusive parameters
2. Identify complementary parameters
3. Document parameter precedence rules
4. Identify spatial parameter interactions
5. Identify temporal parameter interactions
6. Identify relationship parameter rules
7. Create combination rules matrix

### Phase 3: Upstream Parameter Testing Analysis (TBD minutes)

**Objective:** Analyze parameter testing in upstream implementations

**Tasks:**

1. Identify parameter combination tests in upstream
2. Extract parameter validation test patterns
3. Document parameter mocking approaches
4. Identify parameter error test coverage
5. Extract best practices

### Phase 4: Test Scenario Design (TBD minutes)

**Objective:** Design test scenarios for parameter combinations

**Tasks:**

1. Design valid combination test scenarios
2. Design invalid combination test scenarios
3. Design precedence test scenarios
4. Design spatial + temporal + relationship test scenarios
5. Design parameter validation test scenarios
6. Design parameter encoding test scenarios
7. Document scenario matrix (100+ scenarios)

### Phase 5: Fixture Design (TBD minutes)

**Objective:** Design fixtures for parameter combination testing

**Tasks:**

1. Design query string fixtures
2. Design response fixtures for different parameter combinations
3. Design error response fixtures for invalid combinations
4. Document fixture requirements
5. Estimate fixture counts

### Phase 6: Synthesis (TBD minutes)

**Objective:** Create comprehensive query parameter combination testing strategy

**Tasks:**

1. Consolidate parameter combinations
2. Create parameter test templates
3. Document fixture requirements
4. Estimate test implementation effort
5. Create deliverable document

---

## 6. Success Criteria

This research is complete when:

- [ ] All 30+ query parameters are inventoried
- [ ] Valid and invalid combinations are defined
- [ ] Parameter precedence rules are documented
- [ ] Spatial + temporal + relationship interactions are specified
- [ ] Parameter validation tests are designed
- [ ] Parameter combination fixtures are defined
- [ ] Test scenario matrix is complete (100+ scenarios)
- [ ] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Query parameter combination testing strategy covering 30+ parameters**

Content includes:

- Complete query parameter inventory (30+ parameters)
- Parameter categorization (spatial, temporal, relationship, pagination, format)
- Valid combination matrix
- Invalid combination scenarios
- Parameter precedence rules
- Spatial parameter interaction tests
- Temporal parameter interaction tests
- Relationship parameter tests
- Parameter validation test patterns
- Parameter encoding tests
- 100+ test scenario matrix
- Fixture requirements
- Implementation estimates

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 8: CSAPI Specification Review (parameter definitions)
- Section 13: Resource Method Testing Patterns (parameter handling)
- Section 23: Pagination Testing Strategy (pagination parameters)

**Blocks:**

- Query parameter implementation
- Parameter validation implementation
- Section 19: Test Organization and File Structure (parameter test organization)

---

## 9. Research Status Checklist

- [x] Phase 1: Query Parameter Inventory - Complete (1 hour)
  - Extracted 32 query parameters across 7 categories
  - Created parameter applicability matrix
  - Documented parameter types and constraints
- [x] Phase 2: Combination Rules Analysis - Complete (1.5 hours)
  - Documented logical operators (AND/OR)
  - Extracted parameter precedence rules
  - Identified parameter interactions
- [x] Phase 3: Upstream Parameter Testing Analysis - Complete (0.5 hours)
  - Reviewed EDR parameter testing patterns (PR #114)
  - Analyzed Section 13 individual parameter tests
  - Analyzed Section 23 pagination testing
- [x] Phase 4: Test Scenario Design - Complete (1.5 hours)
  - Designed 60 valid combination scenarios
  - Designed 30 invalid combination scenarios
  - Designed 20 validation scenarios
  - Designed 10 encoding scenarios
  - Total: 120 test scenarios
- [x] Phase 5: Fixture Design - Complete (0.5 hours)
  - Designed query string fixtures
  - Designed response fixtures
  - Designed error response fixtures
  - Total: ~120 fixtures
- [x] Phase 6: Synthesis - Complete (0.5 hours)
  - Created comprehensive findings document
  - Documented test organization and implementation estimates
  - Validated against success criteria
- [x] Deliverable document created and reviewed
- [x] Cross-references updated in related documents

**Total Time:** 5.5 hours

---

## 10. Key Findings Summary

**Parameter Inventory:**

- **32 total parameters** across 7 categories
- **5 Standard OGC API parameters**: bbox, datetime, limit, offset, f
- **4 CSAPI Common parameters**: id, uid, q, {propertyName}
- **1 Hierarchical parameter**: recursive
- **8 Relationship parameters**: parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType
- **4 Part 2 Temporal parameters**: phenomenonTime, resultTime, executionTime, issueTime
- **3 Part 2 Format parameters**: format, obsFormat, cmdFormat
- **1 Part 2 Pagination parameter**: cursor

**Combination Rules:**

- **Logical AND** between different parameters (all must match)
- **Logical OR** within single parameter (comma-separated values)
- **No mutually exclusive parameters** (precedence rules handle conflicts)
- **Precedence rules**: f > Accept header, phenomenonTime > datetime, cursor > offset

**Test Scenarios:**

- **60 valid combination scenarios** (2-4+ parameter combinations)
- **30 invalid combination scenarios** (wrong parameter for resource, invalid values)
- **20 validation scenarios** (type, range, format, encoding)
- **10 encoding scenarios** (URL encoding edge cases)
- **Total: 120 test scenarios**

**Implementation:**

- **Estimated ~3,200 lines of test code**
- **~120 fixtures** for query strings, responses, and errors
- **Estimated 34-49 hours** total implementation effort
- **Utilities needed**: ParameterValidator, ParameterEncoder, ParameterValidationError

**Key Recommendations:**

1. Prioritize validation tests and 2-parameter combinations (HIGH)
2. Use parameterized tests for pattern reuse
3. Focus on common use cases, not exhaustive combinations
4. Type-based validation (not resource-based) enables code reuse

---
