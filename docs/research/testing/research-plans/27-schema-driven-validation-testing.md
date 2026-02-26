# Section 27: Schema-Driven Validation Testing - Research Plan

**Status:** ✅ COMPLETE  
**Research Completed:** February 6, 2026  
**Actual Research Time:** ~3.5 hours  
**Estimated Test Implementation Lines:** 990-1,200 lines (66 tests)

---

## 1. Research Objective

Define testing strategy for schema validation (DataStream schemas for Observations, ControlStream schemas for Commands).

**Why 27th:** Schema validation is unique to CSAPI Part 2. After format testing (Section 10), test schema-driven validation.

---

## 2. Research Questions

### Core Questions

1. How to test observation result validation against DataStream schema?
2. How to test command parameter validation against ControlStream schema?
3. What schema mismatch scenarios must be tested?
4. How to test schema parsing (SWE Common schemas)?
5. What fixtures needed for schema validation scenarios?
6. How to test error messages for schema violations?

### Detailed Questions

- What is the structure of DataStream schemas?
- What is the structure of ControlStream schemas?
- How are schemas defined in SWE Common 3.0?
- What validation rules apply to observation results?
- What validation rules apply to command parameters?
- How to test type mismatches (e.g., numeric field receives string)?
- How to test missing required fields?
- How to test extra unexpected fields?
- How to test constraint violations (e.g., value out of range)?
- What are the expected error messages for schema violations?
- How to test schema evolution scenarios?
- Can schemas reference other schemas?

---

## 3. Primary Resources

- **CSAPI Part 2 Specification**: https://docs.ogc.org/is/23-002/23-002.html (schema requirements)
- **Part 2 Requirements**: [docs/research/requirements/csapi-part2-requirements.md](../../requirements/csapi-part2-requirements.md)
- **SWE Common 3.0 Specification**: https://docs.ogc.org/is/24-014/24-014.html
- **Section 10 deliverable**: SWE Common testing specification

## 4. Supporting Resources

- Section 1-2 deliverables (upstream schema validation patterns)
- Section 8 deliverable (CSAPI Spec Review - schema definitions)
- Implementation Guide (schema validation specifications)
- JSON Schema standards (if applicable)

---

## 5. Research Methodology

### Phase 1: Schema Specification Analysis (TBD minutes)

**Objective:** Understand DataStream and ControlStream schema requirements

**Tasks:**

1. Extract DataStream schema specification from Part 2
2. Extract ControlStream schema specification from Part 2
3. Document schema structure (SWE Common components)
4. Identify validation rules for observations
5. Identify validation rules for commands
6. Create schema validation requirements matrix

### Phase 2: SWE Common Schema Analysis (TBD minutes)

**Objective:** Understand SWE Common schema definitions

**Tasks:**

1. Review SWE Common component schemas
2. Document schema composition rules
3. Identify constraint types (allowedValues, intervals, etc.)
4. Document schema parsing requirements
5. Create SWE Common schema test patterns

### Phase 3: Upstream Schema Validation Analysis (TBD minutes)

**Objective:** Analyze schema validation testing in upstream

**Tasks:**

1. Identify schema validation tests in upstream
2. Extract schema validation test patterns
3. Document schema mocking approaches
4. Identify error handling patterns
5. Extract best practices

### Phase 4: Validation Scenario Design (TBD minutes)

**Objective:** Design test scenarios for schema validation

**Tasks:**

1. Design observation result validation scenarios
2. Design command parameter validation scenarios
3. Design schema mismatch scenarios (type, missing, extra fields)
4. Design constraint violation scenarios
5. Design error message validation tests
6. Document scenario matrix

### Phase 5: Fixture Design (TBD minutes)

**Objective:** Design fixtures for schema validation testing

**Tasks:**

1. Design valid observation result fixtures
2. Design invalid observation result fixtures
3. Design valid command parameter fixtures
4. Design invalid command parameter fixtures
5. Design DataStream schema fixtures
6. Design ControlStream schema fixtures
7. Estimate fixture counts

### Phase 6: Synthesis (TBD minutes)

**Objective:** Create comprehensive schema-driven validation testing strategy

**Tasks:**

1. Consolidate validation scenarios
2. Create schema validation test templates
3. Document fixture requirements
4. Estimate test implementation effort
5. Create deliverable document

---

## 6. Success Criteria

This research is complete when:

- [ ] DataStream schema validation is fully specified
- [ ] ControlStream schema validation is fully specified
- [ ] Schema mismatch scenarios are documented
- [ ] SWE Common schema parsing tests are defined
- [ ] Error message validation is specified
- [ ] Schema validation fixtures are designed
- [ ] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Schema-driven validation testing strategy with mismatch scenarios**

Content includes:

- DataStream schema structure and validation rules
- ControlStream schema structure and validation rules
- Observation result validation test patterns
- Command parameter validation test patterns
- Schema mismatch test scenarios (type errors, missing/extra fields)
- Constraint violation test scenarios (range, allowedValues)
- SWE Common schema parsing tests
- Error message validation tests
- Valid and invalid fixture requirements
- Schema evolution test scenarios
- Implementation estimates

**Example Validation Scenarios:**

- Observation result with wrong data type (e.g., string instead of number)
- Observation result missing required field
- Command parameter with value out of allowed range
- Schema with complex nested structure validation
- Schema with allowedValues constraint violation

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 10: SWE Common Testing Requirements (schema component testing)
- Section 8: CSAPI Specification Review (schema definitions)
- Section 1-2: Upstream Analysis (schema validation patterns)

**Blocks:**

- DataStream schema validation implementation
- ControlStream schema validation implementation
- Schema-based error reporting

---

## 9. Research Status Checklist

- [x] Phase 1: Schema Specification Analysis - Complete
- [x] Phase 2: SWE Common Schema Analysis - Complete
- [x] Phase 3: Upstream Schema Validation Analysis - Complete
- [x] Phase 4: Validation Scenario Design - Complete
- [x] Phase 5: Fixture Design - Complete
- [x] Phase 6: Synthesis - Complete
- [x] Deliverable document created and reviewed
- [x] Cross-references updated in related documents

**Phase Completion Summary:**

**Phase 1 (Schema Specification Analysis):** ~45 minutes

- Extracted DataStream/ControlStream schema specifications from Part 2
- Documented validation rules (400 for invalid, 409 for schema change)
- Identified schema endpoints and lifecycle constraints

**Phase 2 (SWE Common Schema Analysis):** ~30 minutes

- Documented 12+ component types (Quantity, Count, Boolean, Text, Time, Category, DataRecord, DataArray, etc.)
- Identified constraint types (interval, allowedTokens, pattern, significantFigures, allowedValues)
- Documented validation rules per component type

**Phase 3 (Upstream Schema Validation Analysis):** ~20 minutes

- Found VALIDATE_OBSERVATIONS and VALIDATE_COMMANDS in Worker Extensions (Section 16)
- Extracted validation patterns from Section 8 (CSAPI Specification)
- Documented error message structure patterns

**Phase 4 (Validation Scenario Design):** ~60 minutes

- Designed 66 test scenarios across 8 categories
- Observation validation: 36 tests (type mismatch, missing fields, extra fields, constraints, nesting, array count)
- Command validation: 18 tests (type mismatch, missing fields, constraints, nesting)
- Schema evolution: 8 tests (changes with/without data)
- Error messages: 4 tests (message structure validation)

**Phase 5 (Fixture Design):** ~45 minutes

- Designed 60 fixtures total
- DataStream schemas: 10 fixtures (simple, nested, arrays, all constraint types)
- ControlStream schemas: 5 fixtures (heater, motor, valve, nested, complex)
- Valid observations: 15 fixtures (matching all schema types)
- Invalid observations: 15 fixtures (various error types)
- Valid commands: 5 fixtures
- Invalid commands: 10 fixtures

**Phase 6 (Synthesis):** ~70 minutes

- Created comprehensive deliverable document (27-schema-driven-validation-testing.md)
- Documented all validation scenarios with test templates
- Estimated 990-1,200 lines of test code (66 tests)
- Estimated 28-41 hours implementation time
- Documented workflow and validation utilities

**Total Research Time:** ~3.5 hours
**Deliverable:** [findings/27-schema-driven-validation-testing.md](../findings/27-schema-driven-validation-testing.md)

---

## 10. Notes and Open Questions

**Research Completed:** February 6, 2026

### Key Findings

**Dual Schema System:**

- DataStream resultSchema - Defines observation result structure (SWE Common DataRecord/DataArray)
- ControlStream parametersSchema - Defines command parameter structure (SWE Common DataRecord)
- Both use SWE Common 3.0 DataComponent structure with 12+ component types

**Validation Points:**

- Observation CREATE (POST) - result must match DataStream resultSchema
- Observation UPDATE (PUT/PATCH) - result must match DataStream resultSchema
- Command CREATE (POST) - parameters must match ControlStream parametersSchema
- Command UPDATE (PUT/PATCH) - parameters must match ControlStream parametersSchema
- Schema Evolution - Schema changes rejected if observations/commands exist (409 Conflict)

**Component Types Identified:**

- **Simple:** Quantity, Count, Boolean, Text, Time, Category
- **Range:** QuantityRange, CategoryRange, TimeRange
- **Complex:** DataRecord, DataArray, Vector, Matrix, DataChoice, GeometryData

**Constraint Types:**

- **interval** - Min/max range (Quantity, Count, Time)
- **allowedTokens** - Enumerated values (Category, Text)
- **pattern** - Regex pattern (Text)
- **significantFigures** - Precision limit (Quantity)
- **allowedValues** - Discrete values (Count)

**Testing Priorities:**

- **CRITICAL (46 tests):** Type mismatch, missing fields, constraint violations, schema evolution with data
- **HIGH (16 tests):** Extra fields, nesting, array count, schema evolution without data, error messages
- **MEDIUM (4 tests):** Complex nesting (3+ levels), advanced constraints

**Implementation Estimates:**

- **Test Code:** 990-1,200 lines (66 tests)
- **Fixtures:** 60 total (10 DataStream schemas, 5 ControlStream schemas, 15 valid obs, 15 invalid obs, 5 valid cmd, 10 invalid cmd)
- **Development Time:** 28-41 hours
- **Test Files:** 4 files (observation-validation.spec.ts, command-validation.spec.ts, schema-evolution.spec.ts, validation-error-messages.spec.ts)

### Validation Workflow

**Client-Side Validation:**

1. Fetch DataStream/ControlStream schema
2. Validate result/parameters against schema before submission
3. Check type matching, required fields, constraints
4. Throw ValidationError if invalid
5. Submit to server if valid

**Server-Side Validation:**

1. Receive observation/command
2. Fetch parent DataStream/ControlStream schema
3. Validate result/parameters
4. Return 400 Bad Request with detailed error if invalid
5. Return 201 Created if valid

**Error Response Structure:**

```json
{
  "code": "InvalidParameterValue",
  "description": "Observation result does not match DataStream schema",
  "details": {
    "field": "temperature",
    "expectedType": "number",
    "actualType": "string",
    "expectedValue": "numeric value in range [-50, 100]",
    "actualValue": "twenty-three"
  }
}
```

### Related Sections

- **Section 8:** CSAPI Specification Test Requirements (validation rules, OpenAPI schemas)
- **Section 10:** SWE Common Testing Requirements (component types, encoding tests, constraint validation)
- **Section 12:** QueryBuilder Testing Strategy (schema endpoints: getDataStreamSchema, getControlStreamSchema)
- **Section 16:** Worker Extensions Testing (VALIDATE_OBSERVATIONS, VALIDATE_COMMANDS message types)

### Questions Resolved

✅ How to test observation result validation against DataStream schema?

- Answer: Type matching, required field validation, constraint enforcement, nested structure validation. 36 tests identified.

✅ How to test command parameter validation against ControlStream schema?

- Answer: Similar to observations but with command-specific parameters (setpoint, mode, duration). 18 tests identified.

✅ What schema mismatch scenarios must be tested?

- Answer: Type mismatch (8 obs + 5 cmd), missing fields (5 obs + 3 cmd), extra fields (3 obs), wrong structure. Total: ~25 tests.

✅ How to test schema parsing (SWE Common schemas)?

- Answer: Covered in Section 10 (SWE Common Testing Requirements). This section focuses on validation against parsed schemas.

✅ What fixtures needed for schema validation scenarios?

- Answer: 60 fixtures total - 10 DataStream schemas, 5 ControlStream schemas, 15 valid/15 invalid observations, 5 valid/10 invalid commands.

✅ How to test error messages for schema violations?

- Answer: 4 tests validating error message structure (field name, expected/actual types, constraint details). Error messages must be detailed and actionable.

### Open Questions

None - Research complete.

---

**Research Status:** ✅ COMPLETE  
**Deliverable:** [findings/27-schema-driven-validation-testing.md](../findings/27-schema-driven-validation-testing.md)  
**Next Steps:** Implement validation utilities and test suites according to findings document.
