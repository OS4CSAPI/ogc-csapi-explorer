# Section 30: Bulk Operations Testing Strategy - Research Plan

**Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Actual Research Time:** ~1.5 hours  
**Estimated Test Implementation Lines:** 450-600 lines (28 tests)

---

## 1. Research Objective

Define testing strategy for bulk observation and command creation operations.

**Why 30th:** Bulk operations have unique performance and validation considerations. After individual operation testing (Section 13), test bulk.

---

## 2. Research Questions

### Core Questions

1. How to test bulk observation creation?
2. How to test bulk command creation?
3. What request size limits must be tested?
4. How to test partial success/failure in bulk operations?
5. What error handling is specific to bulk operations?
6. What fixtures needed for bulk scenarios?

### Detailed Questions

- What is the structure of bulk operation requests?
- What is the maximum number of items in a bulk request?
- How to test transaction semantics (all-or-nothing vs partial success)?
- How to test individual item validation in bulk?
- What error response structure is used for bulk failures?
- How to test bulk operation with mixed valid/invalid items?
- How to test performance with large bulk requests?
- How to test bulk operation timeouts?
- What status codes are returned for bulk operations?
- How to test bulk operations with schema validation?
- Can bulk operations be paginated?

---

## 3. Primary Resources

- **CSAPI Part 2 Specification**: https://docs.ogc.org/is/23-002/23-002.html (bulk operations)
- **Part 2 Requirements**: [docs/research/requirements/csapi-part2-requirements.md](../../requirements/csapi-part2-requirements.md)
- **CRUD Operations Requirements**: [docs/research/requirements/csapi-crud-operations.md](../../requirements/csapi-crud-operations.md)
- **Implementation Guide**: [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md)

## 4. Supporting Resources

- Section 13 deliverable (Resource Method Testing - individual operations)
- Section 18 deliverable (Error Condition Testing - error patterns)
- Section 27 deliverable (Schema-Driven Validation - bulk item validation)
- Section 33 deliverable (Performance Testing - bulk performance)

---

## 5. Research Methodology

### Phase 1: Bulk Operation Specification Analysis (TBD minutes)

**Objective:** Extract bulk operation requirements from CSAPI

**Tasks:**

1. Identify bulk operation endpoints (observations, commands)
2. Document bulk request structure
3. Document bulk response structure
4. Extract size limits and constraints
5. Document transaction semantics
6. Create bulk operation matrix

### Phase 2: Error Handling Analysis (TBD minutes)

**Objective:** Understand bulk operation error handling

**Tasks:**

1. Document partial success/failure semantics
2. Identify error response structure for bulk operations
3. Document item-level error reporting
4. Identify rollback vs continue-on-error behavior
5. Create bulk error scenario matrix

### Phase 3: Upstream Bulk Testing Analysis (TBD minutes)

**Objective:** Analyze bulk operation testing in upstream

**Tasks:**

1. Identify bulk operation tests in upstream
2. Extract bulk validation test patterns
3. Extract partial failure test patterns
4. Identify performance test approaches
5. Extract best practices

### Phase 4: Test Scenario Design (TBD minutes)

**Objective:** Design test scenarios for bulk operations

**Tasks:**

1. Design all-valid bulk operation scenarios
2. Design all-invalid bulk operation scenarios
3. Design mixed valid/invalid scenarios
4. Design size limit test scenarios
5. Design transaction semantics scenarios
6. Design performance test scenarios
7. Document scenario matrix

### Phase 5: Fixture Design (TBD minutes)

**Objective:** Design fixtures for bulk operation testing

**Tasks:**

1. Design small bulk request fixtures (10-50 items)
2. Design large bulk request fixtures (100-1000+ items)
3. Design mixed valid/invalid fixtures
4. Design bulk response fixtures
5. Design bulk error fixtures
6. Estimate fixture counts

### Phase 6: Synthesis (TBD minutes)

**Objective:** Create comprehensive bulk operations testing strategy

**Tasks:**

1. Consolidate bulk operation scenarios
2. Create bulk operation test templates
3. Document fixture requirements
4. Estimate test implementation effort
5. Create deliverable document

---

## 6. Success Criteria

This research is complete when:

- [ ] Bulk observation creation is fully specified
- [ ] Bulk command creation is fully specified
- [ ] Size limits are documented and tested
- [ ] Partial success/failure handling is defined
- [ ] Error response structure is specified
- [ ] Performance considerations are documented
- [ ] Bulk operation fixtures are designed
- [ ] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Bulk operations testing strategy with performance consideration**

Content includes:

- Bulk observation creation test patterns
- Bulk command creation test patterns
- Bulk request structure specification
- Bulk response structure specification
- Size limit test scenarios
- Transaction semantics tests (all-or-nothing vs partial success)
- Partial success/failure test scenarios
- Item-level validation tests
- Mixed valid/invalid item scenarios
- Error response structure for bulk operations
- Performance test scenarios (100-1000+ items)
- Timeout handling tests
- Schema validation in bulk operations
- Fixture requirements
- Implementation estimates

**Example Bulk Request:**

```json
{
  "observations": [
    { "phenomenonTime": "2024-01-01T00:00:00Z", "result": 23.5 },
    { "phenomenonTime": "2024-01-01T01:00:00Z", "result": 24.1 },
    { "phenomenonTime": "2024-01-01T02:00:00Z", "result": 24.8 }
  ]
}
```

**Example Bulk Response (Partial Failure):**

```json
{
  "created": ["obs-1", "obs-3"],
  "failed": [
    {
      "index": 1,
      "error": "Schema validation failed: result must be numeric"
    }
  ]
}
```

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 13: Resource Method Testing Patterns (individual operation patterns)
- Section 18: Error Condition Testing (error handling patterns)
- Section 27: Schema-Driven Validation Testing (item validation)

**Blocks:**

- Bulk observation creation implementation
- Bulk command creation implementation
- Section 33: Performance Testing (bulk performance benchmarks)

---

## 9. Research Status Checklist

- [x] Phase 1: Bulk Operation Specification Analysis - Complete
- [x] Phase 2: Error Handling Analysis - Complete
- [x] Phase 3: Upstream Bulk Testing Analysis - Complete
- [x] Phase 4: Test Scenario Design - Complete
- [x] Phase 5: Fixture Design - Complete
- [x] Phase 6: Synthesis - Complete
- [x] Deliverable document created and reviewed
- [x] Cross-references updated in related documents

**Completion Date:** February 6, 2026

---

## 10. Key Findings and Risks

### Key Findings

1. **Bulk Operation Endpoints (2 total):**

   - `POST /datastreams/{id}/observations` - Bulk observation creation (array input)
   - `POST /controlstreams/{id}/commands` - Bulk command creation (array input)

2. **Transaction Semantics - SPEC AMBIGUITY:**

   - CSAPI Part 2 does NOT explicitly define transaction semantics for bulk operations
   - Based on OpenSensorHub analysis: **Partial success is likely** (valid items created, invalid items reported)
   - NOT all-or-nothing (entire request doesn't fail if some items are invalid)

3. **Size Limits (from OpenSensorHub):**

   - **Recommended batch size:** 100-1,000 items per request
   - **Maximum:** 10,000 items per request
   - No explicit limit in CSAPI spec (implementation-dependent)

4. **Error Response Structure:**

   - **Success:** 201 Created with array of created IDs or full resources
   - **Partial success:** 207 Multi-Status or custom response with `created` and `failed` arrays
   - **Complete failure:** 400 Bad Request with validation errors

5. **Schema Validation:**

   - Each item in bulk request validated against datastream/controlstream schema
   - Same validation rules as single-item POST
   - Failed items reported with index and error message

6. **Performance Recommendations:**
   - Auto-chunk large batches into 1,000-item requests
   - Add small delays (100ms) between chunks to prevent server overload
   - Use progress callbacks for large batches

### Risks

**HIGH RISK:**

1. **Spec Ambiguity on Transaction Semantics**
   - CSAPI spec doesn't mandate all-or-nothing vs partial success behavior
   - Different servers may implement differently
   - **Mitigation:** Test both transaction semantics, document server behavior
2. **No Standard Bulk Error Response Format**
   - Spec doesn't define error response structure for partial failures
   - Servers may return different error formats
   - **Mitigation:** Test multiple error response formats, flexible error parsing

**MEDIUM RISK:** 3. **Implementation Variance on Size Limits**

- OpenSensorHub max 10,000, but other servers may differ
- **Mitigation:** Test various batch sizes (10, 100, 1,000, 10,000), document limits per server

4. **Performance Sensitivity**
   - Large batches can timeout or exceed memory limits
   - **Mitigation:** Test performance with realistic high-volume data, document recommended batch sizes

### Testing Priorities

1. **CRITICAL (13-20 hours):**

   - All-valid bulk observations (8 tests, 150-200 lines)
   - Mixed valid/invalid items (6 tests, 80-120 lines)
   - Bulk commands (6 tests, 100-150 lines)

2. **HIGH:**

   - Size limit handling (4 tests, 60-80 lines)
   - Performance testing (4 tests, 60-80 lines)

3. **Fixture Requirements:** ~30 fixtures
   - Bulk request fixtures: 12
   - Bulk response fixtures: 10
   - Performance test fixtures: 8

### What This Unblocks

- Bulk observation creation implementation
- Bulk command creation implementation
- Section 33: Performance Testing (bulk performance benchmarks)

---

## 11. Deliverable Summary

**Primary Deliverable:** [30-bulk-operations-testing.md](../findings/30-bulk-operations-testing.md)

**Contents:**

1. Bulk operation endpoint specifications (observations, commands)
2. Bulk request structure specification (array POST)
3. Bulk response structure specification (success, partial failure, complete failure)
4. Transaction semantics analysis (3 options: all-or-nothing, partial success, sequential)
5. All-valid bulk test patterns (~8 tests for observations, ~6 tests for commands)
6. Mixed valid/invalid test patterns (~6 tests)
7. Size limit test patterns (~4 tests)
8. Performance test patterns (~4 tests)
9. Schema validation integration
10. Fixture requirements (~30 fixtures)
11. Client library design (BulkCreateResult, auto-chunking, fallback to sequential)
12. Implementation estimates (450-600 lines, 13-20 hours)

**Total Tests:** 28 tests  
**Total Lines:** 450-600 lines
