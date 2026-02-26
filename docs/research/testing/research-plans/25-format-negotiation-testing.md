# Section 25: Format Negotiation Testing Strategy - Research Plan

**Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Actual Research Time:** 4.0 hours  
**Estimated Test Implementation Lines:** ~1,800 lines

---

## 1. Research Objective

Define testing strategy for format negotiation via Accept headers, query parameters, and link discovery.

**Why 25th:** After query parameter testing (Section 24), test format negotiation mechanisms across all three methods.

---

## 2. Research Questions

### Core Questions

1. How to test Accept header format negotiation?
2. How to test query parameter format selection (f=geojson)?
3. How to test format discovery via links?
4. What media types does CSAPI support?
5. How to test format precedence (Accept vs query param)?
6. What happens with unsupported formats?

### Detailed Questions

- What are all the CSAPI-supported media types?
- Which resources support which formats?
- How is format negotiation prioritized (Accept header vs f= parameter)?
- What is the default format?
- How to test wildcard Accept headers (_/_)?
- How to test complex Accept headers with quality values?
- How to test format links in resource representations?
- What error responses occur for unsupported formats?
- How to test format fallback scenarios?
- How to test format encoding (charset)?
- What is the role of the Vary header?

---

## 3. Primary Resources

- **Format Negotiation Architecture**: [docs/architecture/responses/format-negotiation.md](../../../architecture/responses/format-negotiation.md)
- **Format Requirements**: [docs/research/requirements/format-requirements.md](../../requirements/format-requirements.md)
- **CSAPI Specifications**: Media type definitions across all parts
- **Implementation Guide**: [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md)

## 4. Supporting Resources

- HTTP Content Negotiation (RFC 7231)
- OGC API - Common format negotiation patterns
- Section 8 deliverable (CSAPI Spec Review - format specifications)
- Section 24 deliverable (Query Parameter Testing - f= parameter)

---

## 5. Research Methodology

### Phase 1: Format Specification Analysis (TBD minutes)

**Objective:** Extract format negotiation requirements from CSAPI

**Tasks:**

1. Identify all CSAPI media types
2. Document media type support by resource type
3. Extract Accept header requirements
4. Extract f= query parameter requirements
5. Extract link-based format discovery requirements
6. Document format precedence rules
7. Create format negotiation matrix

### Phase 2: Upstream Format Testing Analysis (TBD minutes)

**Objective:** Analyze format negotiation testing in upstream

**Tasks:**

1. Identify format negotiation tests in upstream
2. Extract Accept header test patterns
3. Extract query parameter format test patterns
4. Extract link parsing test patterns
5. Document format mocking approaches
6. Extract best practices

### Phase 3: Test Scenario Design (TBD minutes)

**Objective:** Design test scenarios for format negotiation

**Tasks:**

1. Design Accept header test scenarios
2. Design f= query parameter test scenarios
3. Design link-based format discovery test scenarios
4. Design format precedence test scenarios
5. Design unsupported format test scenarios
6. Design format fallback test scenarios
7. Document scenario matrix

### Phase 4: Media Type Matrix Creation (TBD minutes)

**Objective:** Create comprehensive media type support matrix

**Tasks:**

1. Map media types to resource types
2. Document default formats
3. Document format precedence
4. Identify format-specific representations
5. Create media type test matrix

### Phase 5: Fixture Design (TBD minutes)

**Objective:** Design fixtures for format negotiation testing

**Tasks:**

1. Design Accept header fixtures
2. Design format-specific response fixtures
3. Design link relation fixtures
4. Design error response fixtures
5. Estimate fixture counts

### Phase 6: Synthesis (TBD minutes)

**Objective:** Create comprehensive format negotiation testing strategy

**Tasks:**

1. Consolidate format negotiation scenarios
2. Create format test templates
3. Document fixture requirements
4. Estimate test implementation effort
5. Create deliverable document

---

## 6. Success Criteria

This research is complete when:

- [ ] All CSAPI media types are inventoried
- [ ] Format negotiation methods are fully specified (Accept, f=, links)
- [ ] Format precedence rules are documented
- [ ] Media type support matrix is complete
- [ ] Format fallback scenarios are defined
- [ ] Format test patterns are documented
- [ ] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Format negotiation testing strategy covering all three negotiation methods**

Content includes:

- Complete CSAPI media type inventory
- Media type support matrix by resource type
- Accept header test patterns
- Query parameter (f=) test patterns
- Link-based format discovery test patterns
- Format precedence test scenarios
- Unsupported format test scenarios
- Format fallback test scenarios
- Wildcard Accept header tests
- Quality value (q=) Accept header tests
- Format-specific fixture requirements
- Implementation estimates

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 8: CSAPI Specification Review (media type definitions)
- Section 24: Query Parameter Combination Testing (f= parameter)
- Format Negotiation Architecture document

**Blocks:**

- Format negotiation implementation
- Media type selection logic
- Section 19: Test Organization and File Structure (format test organization)

---

## 9. Research Status Checklist

- [x] Phase 1: Format Specification Analysis - Complete (1.5 hours)
- [x] Phase 2: Upstream Format Testing Analysis - Complete (0.5 hours)
- [x] Phase 3: Test Scenario Design - Complete (1.0 hours)
- [x] Phase 4: Media Type Matrix Creation - Complete (0.5 hours)
- [x] Phase 5: Fixture Design - Complete (0.5 hours)
- [x] Phase 6: Synthesis - Complete (1.0 hours)
- [x] Deliverable document created and reviewed
- [ ] Cross-references updated in related documents

**Completion Date:** February 6, 2026

**Total Time:** 4.0 hours (research), 18-28 hours estimated for implementation

---

## 10. Notes and Key Findings

**Key Findings from Research:**

**7 Media Types Identified:**

1. `application/json` - Base JSON (REQUIRED, all resources)
2. `application/geo+json` - GeoJSON (REQUIRED, spatial resources)
3. `application/sml+json` - SensorML (REQUIRED, systems/procedures)
4. `application/swe+json` - SWE Common JSON (OPTIONAL, observations/commands)
5. `application/swe+text` - SWE Common CSV (OPTIONAL, 2-5x smaller)
6. `application/swe+binary` - SWE Common Binary (OPTIONAL, 10-100x smaller)
7. `text/uri-list` - URI list (OPTIONAL, collection additions)

**3 Format Negotiation Methods:**

1. Query parameter (`f` or `format`) - PRIMARY (highest precedence)
2. Accept header - FALLBACK (second precedence)
3. Server default - LAST RESORT

**Precedence Rule:** Query parameter > Accept header > Server default > 406 Not Acceptable

**Part 1 vs Part 2 Differences:**

- Part 1: Short format names (f=json, f=geojson, f=sml)
- Part 2: Full media types required (f=application/swe+json)

**URL Encoding Critical:**

- Plus character (+) MUST be encoded as %2B
- Example: application/swe+json → application/swe%2Bjson

**Format Advertisement:**

- Part 1: Implicit (via API metadata)
- Part 2: Explicit (formats property in DataStream/ControlStream)

**No Link-Based Format Discovery:**

- Research plan mentioned link-based selection
- CSAPI follows EDR pattern (query parameter only)
- Links are informational only

**50 Test Scenarios Designed:**

- 20 query parameter tests
- 10 Accept header tests
- 5 default format tests
- 5 URL encoding tests
- 5 error handling tests (406 Not Acceptable)
- 5 format advertisement tests

**37 Fixtures Designed:**

- 15 valid query strings
- 5 invalid query strings
- 6 Accept header variations
- 2 unsupported Accept headers
- 6 format-specific responses
- 3 error responses

**Implementation Estimates:**

- Test Implementation: 9-14 hours
- Fixture Creation: 3-4 hours
- Validation Utilities: 4-7 hours
- **Total: 18-28 hours**

---

**Next Steps:**

1. Implement format negotiation tests (~9-14 hours)
2. Create format validation utilities (~4-7 hours)
3. Create format-specific fixtures (~3-4 hours)
4. Update Section 19 with format test organization
