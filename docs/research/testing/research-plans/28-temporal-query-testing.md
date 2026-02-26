# Section 28: Temporal Query Testing Strategy - Research Plan

**Status:** Research Planning Phase - Outline Only  
**Last Updated:** February 5, 2026  
**Estimated Research Time:** TBD  
**Estimated Test Implementation Lines:** TBD

---

## 1. Research Objective

Define comprehensive testing strategy for all temporal query parameters (datetime, phenomenonTime, resultTime, executionTime, issueTime).

**Why 28th:** Temporal queries are critical for observations and commands. After query parameter testing (Section 24), deep dive on temporal.

---

## 2. Research Questions

### Core Questions

1. How to test all ISO 8601 interval formats?
2. How to test open-ended intervals (`../..`, `2024-01-01/..`, `../2024-12-31`)?
3. How to test instant vs interval queries?
4. How to test temporal parameter combinations?
5. What temporal edge cases must be tested?
6. How to test temporal validation errors?

### Detailed Questions

- What temporal parameters does CSAPI define?
- What is the difference between phenomenonTime, resultTime, executionTime, issueTime?
- Which resources support which temporal parameters?
- What ISO 8601 formats must be supported?
- How to test timezone handling (UTC, offset, Z notation)?
- How to test date-only vs datetime queries?
- How to test duration intervals (P1D, P1M, PT1H)?
- How to test unbounded intervals (`..`)?
- What happens with invalid ISO 8601 formats?
- What happens with temporally inconsistent ranges (end before start)?
- How to test temporal parameter precedence?
- How to test temporal queries with pagination?

---

## 3. Primary Resources

- **Query Parameter Requirements**: [docs/research/requirements/csapi-query-parameters.md](../../requirements/csapi-query-parameters.md) (temporal parameters)
- **ISO 8601 Specification**: Date and time format standard
- **CSAPI Part 2 Specification**: https://docs.ogc.org/is/23-002/23-002.html (temporal queries)
- **OGC API - Common**: Temporal query patterns

## 4. Supporting Resources

- Section 24 deliverable (Query Parameter Combination Testing - parameter interactions)
- Section 23 deliverable (Pagination - temporal queries with pagination)
- Section 8 deliverable (CSAPI Spec Review - temporal parameter definitions)
- RFC 3339 (ISO 8601 profile for internet timestamps)

---

## 5. Research Methodology

### Phase 1: Temporal Parameter Specification Analysis (TBD minutes)

**Objective:** Extract temporal parameter requirements from CSAPI

**Tasks:**

1. Identify all temporal parameters (datetime, phenomenonTime, resultTime, executionTime, issueTime)
2. Document temporal parameter semantics (what each represents)
3. Map temporal parameters to resource types
4. Extract ISO 8601 format requirements
5. Document temporal parameter precedence rules
6. Create temporal parameter matrix

### Phase 2: ISO 8601 Format Analysis (TBD minutes)

**Objective:** Identify all ISO 8601 formats requiring testing

**Tasks:**

1. Document instant formats (date, datetime, timezone variations)
2. Document interval formats (start/end, start/duration, duration/end)
3. Document open-ended interval formats (`..`)
4. Document duration formats (P1Y, P1M, P1D, PT1H, etc.)
5. Identify edge cases (leap years, DST, leap seconds)
6. Create ISO 8601 format test matrix

### Phase 3: Upstream Temporal Testing Analysis (TBD minutes)

**Objective:** Analyze temporal query testing in upstream

**Tasks:**

1. Identify temporal query tests in upstream
2. Extract ISO 8601 parsing test patterns
3. Extract temporal validation patterns
4. Identify temporal edge case coverage
5. Extract best practices

### Phase 4: Test Scenario Design (TBD minutes)

**Objective:** Design test scenarios for temporal queries

**Tasks:**

1. Design instant query test scenarios
2. Design interval query test scenarios (bounded and unbounded)
3. Design duration query test scenarios
4. Design temporal parameter combination scenarios
5. Design timezone handling test scenarios
6. Design temporal validation error scenarios
7. Design temporal edge case scenarios
8. Document scenario matrix

### Phase 5: Fixture Design (TBD minutes)

**Objective:** Design fixtures for temporal query testing

**Tasks:**

1. Design temporal query string fixtures (all ISO 8601 formats)
2. Design temporal response fixtures
3. Design temporal error fixtures
4. Design temporal edge case fixtures
5. Estimate fixture counts

### Phase 6: Synthesis (TBD minutes)

**Objective:** Create comprehensive temporal query testing strategy

**Tasks:**

1. Consolidate temporal scenarios
2. Create temporal query test templates
3. Document fixture requirements
4. Estimate test implementation effort
5. Create deliverable document

---

## 6. Success Criteria

This research is complete when:

- [ ] All temporal parameters are specified (datetime, phenomenonTime, resultTime, executionTime, issueTime)
- [ ] All ISO 8601 formats are documented and tested
- [ ] Open-ended interval handling is defined
- [ ] Temporal parameter combinations are specified
- [ ] Timezone handling is fully tested
- [ ] Temporal edge cases are identified
- [ ] Temporal validation error scenarios are defined
- [ ] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Temporal query testing strategy with ISO 8601 format coverage**

Content includes:

- Complete temporal parameter inventory and semantics
- Temporal parameter mapping to resource types
- ISO 8601 instant format test patterns (date, datetime, timezone)
- ISO 8601 interval format test patterns (start/end, start/duration, duration/end)
- Open-ended interval test patterns (`..`, `2024-01-01/..`, `../2024-12-31`)
- Duration format test patterns (P1Y, P1M, P1D, PT1H)
- Timezone handling test scenarios (UTC, offset, Z notation)
- Temporal parameter combination tests
- Temporal validation error scenarios
- Temporal edge cases (leap years, DST, midnight boundaries)
- Temporal query + pagination interaction tests
- Fixture requirements
- Implementation estimates

**Example Temporal Formats:**

- **Instants**: `2024-01-15`, `2024-01-15T10:30:00Z`, `2024-01-15T10:30:00+05:00`
- **Intervals**: `2024-01-01/2024-12-31`, `2024-01-01/P1M`, `P1Y/2024-12-31`
- **Open-ended**: `../2024-12-31`, `2024-01-01/..`, `../..`
- **Durations**: `P1Y` (1 year), `P1M` (1 month), `P1D` (1 day), `PT1H` (1 hour)

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 24: Query Parameter Combination Testing (parameter interaction patterns)
- Section 8: CSAPI Specification Review (temporal parameter definitions)
- Section 23: Pagination Testing Strategy (temporal + pagination)

**Blocks:**

- Temporal query implementation
- ISO 8601 parsing implementation
- Temporal validation logic

---

## 9. Research Status Checklist

- [x] Phase 1: Temporal Parameter Specification Analysis - Complete
- [x] Phase 2: ISO 8601 Format Analysis - Complete
- [x] Phase 3: Upstream Temporal Testing Analysis - Complete
- [x] Phase 4: Test Scenario Design - Complete
- [x] Phase 5: Fixture Design - Complete
- [x] Phase 6: Synthesis - Complete
- [x] Deliverable document created and reviewed
- [x] Cross-references updated in related documents

**Status:** ✅ Complete  
**Completion Date:** February 6, 2026  
**Time Spent:** ~180 minutes (3 hours)

---

## 10. Notes and Open Questions

<!-- Add notes and unresolved questions here as research progresses -->

**Research Completed:** February 6, 2026

**Key Findings:**

1. **Five Temporal Parameters Identified:**

   - `datetime` - Generic temporal filter (OGC API - Common) for validTime
   - `phenomenonTime` - When observation was made (Part 2)
   - `resultTime` - When observation result was produced (Part 2)
   - `executionTime` - When command was executed (Part 2)
   - `issueTime` - When command was issued (Part 2)

2. **ISO 8601 Format Complexity:**

   - **Instants:** 7+ format variations (date-only, datetime, timezones, fractional seconds)
   - **Intervals:** 4 types (closed, open-start, open-end, fully open)
   - **Durations:** 7+ formats (P1Y, P1M, P1D, PT1H, PT30M, combined)
   - **Special Values:** `latest` (resultTime only)

3. **Open-Ended Intervals Critical:**

   - `../..` - All data (no temporal bounds)
   - `2024-01-01/..` - All data from 2024 onwards
   - `../2024-12-31` - All data up to end of 2024
   - **Use Case:** Streaming/real-time queries ("all observations after time X")

4. **Timezone Handling:**

   - Z notation (UTC): `2024-01-15T12:00:00Z`
   - Offset notation: `2024-01-15T12:00:00+05:30`
   - Valid range: -12:00 to +14:00
   - Default: Assume UTC if omitted

5. **Temporal Parameter Semantics Matter:**

   - `phenomenonTime` vs `resultTime` captures sampling/processing delay
   - `issueTime` vs `executionTime` captures command scheduling delay
   - `latest` special value only for `resultTime` (real-time dashboards)

6. **Edge Cases Identified:**
   - Leap years (February 29th)
   - DST transitions (spring forward, fall back)
   - Leap seconds (23:59:60)
   - Midnight boundaries (24:00:00 vs 00:00:00 next day)
   - Antimeridian crossing (date line)

**Test Coverage:**

- **72 tests** across 9 test categories
- **~950-1,300 lines** of test code
- **55 fixtures** (query strings, responses, errors, edge cases)
- **Priority:** 53 CRITICAL tests, 9 HIGH, 10 MEDIUM

**Implementation Estimates:**

- **Test Development:** 25-36 hours
- **Fixture Creation:** 6-8 hours
- **Total Effort:** 31-44 hours

**Deliverable Location:** [findings/28-temporal-query-testing.md](../findings/28-temporal-query-testing.md)

**No Open Questions** - Research complete and comprehensive.
