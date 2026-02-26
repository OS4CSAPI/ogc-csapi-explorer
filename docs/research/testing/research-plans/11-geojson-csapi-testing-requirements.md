# Research Plan: GeoJSON CSAPI Extensions Testing Requirements

**Section:** 11 of 38  
**Status:** ✅ COMPLETED  
**Last Updated:** February 5, 2026  
**Completion Date:** February 5, 2026  
**Actual Time:** 2 hours  
**Actual Lines:** 15,000 words / ~1,200 lines  
**Deliverable:** [11-geojson-csapi-testing-requirements.md](../11-geojson-csapi-testing-requirements.md)

---

## 1. Research Objective

Define comprehensive testing requirements for CSAPI-specific GeoJSON extensions that build on existing GeoJSON parser. Identify what CSAPI property validation and resource-specific logic must be tested beyond standard GeoJSON compliance.

### Why This Research Eleventh

**Dependency Chain:** After SensorML and SWE Common testing (Sections 9-10), address the simpler but equally important GeoJSON format for Part 1 resources.

**Context:** GeoJSON is the primary encoding for CSAPI Part 1 resources (Systems, Deployments, Procedures, SamplingFeatures, Properties). The library already has a GeoJSON parser from upstream, so testing focuses on:

- **CSAPI-specific properties:** uniqueIdentifier, featureType, systemType, etc.
- **Property validation:** URI formats, vocabulary values, required vs optional
- **Resource type differentiation:** How testing differs across 5 Part 1 resource types
- **Integration with existing parser:** What's inherited vs what's new
- **Minimal duplication:** Don't re-test standard GeoJSON (already tested upstream)

This research defines:

- **CSAPI Extension Testing:** What properties are CSAPI-specific
- **Validation Rules:** URI formats, controlled vocabularies, temporal validity
- **Resource Type Coverage:** 5 Part 1 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties)
- **Reuse Strategy:** What to inherit from existing GeoJSON tests
- **Test Depth:** What constitutes "meaningful" GeoJSON CSAPI testing

### Sequencing Rationale

Sections 9-10 addressed the complex formats (SensorML, SWE Common). Section 11 addresses GeoJSON CSAPI extensions, which is simpler but equally critical. GeoJSON is the primary encoding for all CSAPI Part 1 resources. Since upstream ogc-client already has a GeoJSON parser with RFC 7946 compliance tests, this research focuses exclusively on CSAPI-specific extensions: property validation (uniqueIdentifier, featureType, vocabularies), temporal properties (validTime), and resource-specific properties (systemType, deployedSystem, observableProperty). This minimizes test duplication while ensuring comprehensive CSAPI coverage.

---

## 2. Research Questions

### Core Questions

1. What GeoJSON properties are CSAPI-specific vs standard RFC 7946?
2. What validation rules (URI formats, controlled vocabularies, temporal) must be tested?
3. How does testing differ across 5 Part 1 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties)?
4. What can be reused from existing upstream GeoJSON tests vs what must be CSAPI-specific?
5. What constitutes "meaningful" GeoJSON CSAPI extension testing without duplicating RFC 7946 tests?
6. What fixtures are available (spec examples vs OpenSensorHub) for each resource type?

### Detailed Questions

### Detailed Questions

**CSAPI Part 1 GeoJSON Requirements (8 questions):**

1. What GeoJSON properties are standard (inherited from RFC 7946)?
2. What GeoJSON properties are CSAPI-specific?
3. What properties are common across all Part 1 resources?
4. What properties are resource-specific?
5. What validation rules apply to CSAPI properties?
6. What controlled vocabularies must be validated?
7. What temporal properties exist (validTime, phenomenonTime)?
8. What relationship properties exist (links, associations)?

**Existing GeoJSON Parser Analysis (6 questions):** 9. What GeoJSON parser exists in upstream ogc-client? 10. What does the existing parser already test? 11. What test coverage exists for standard GeoJSON? 12. What can be reused vs must be CSAPI-specific? 13. How does CSAPI extend the existing parser? 14. What integration points exist with existing parser?

**Resource Type Differentiation (7 questions):** 15. **Systems:** What CSAPI-specific properties must be tested? 16. **Deployments:** What CSAPI-specific properties must be tested? 17. **Procedures:** What CSAPI-specific properties must be tested? 18. **SamplingFeatures:** What CSAPI-specific properties must be tested? 19. **Properties:** What CSAPI-specific properties must be tested? 20. What properties are shared across all 5 resource types? 21. What properties are unique per resource type?

**Property Validation Requirements (9 questions):** 22. **uniqueIdentifier:** What URI validation is required? 23. **featureType:** What vocabulary values are valid? 24. **systemType:** What vocabulary values are valid (for Systems)? 25. **samplingFeatureType:** What vocabulary values are valid (for SamplingFeatures)? 26. **definition:** What URI validation is required? 27. **validTime:** What temporal format validation is required? 28. **phenomenonTime:** What temporal format validation is required? 29. **resultTime:** What temporal format validation is required? 30. **links:** What link structure validation is required?

**Geometry Handling (4 questions):** 31. Does CSAPI add geometry requirements beyond RFC 7946? 32. What geometry types are used per resource type? 33. Are there CSAPI-specific CRS requirements? 34. How to test geometry parsing without duplicating RFC 7946 tests?

**featureType Vocabulary (6 questions):** 35. What featureType values are defined for Systems? 36. What featureType values are defined for Deployments? 37. What featureType values are defined for Procedures? 38. What featureType values are defined for SamplingFeatures? 39. What featureType values are defined for Properties? 40. Is featureType validation strict or permissive?

**Temporal Property Validation (5 questions):** 41. What temporal formats must be supported (ISO 8601)? 42. How to validate instant vs interval formats? 43. What edge cases exist (open intervals, null values)? 44. How to test validTime for Deployments? 45. How to test phenomenonTime for observations (if applicable)?

**Link Validation (4 questions):** 46. What link relations are defined in CSAPI? 47. What link structure is required (href, rel, type)? 48. How to validate link URIs? 49. What relationships exist between resource types?

**FeatureCollection Testing (4 questions):** 50. How to test FeatureCollection parsing? 51. What CSAPI-specific collection properties exist? 52. How to test pagination links in collections? 53. How to test mixed resource types in collections?

**Error Handling (6 questions):** 54. What error conditions must be tested? 55. How to handle missing required CSAPI properties? 56. How to handle invalid property values (wrong type, format)? 57. How to handle invalid vocabulary values? 58. How to handle malformed temporal properties? 59. What error messages should be provided?

**Specification Examples (4 questions):** 60. What GeoJSON examples exist in CSAPI Part 1 spec? 61. What examples exist per resource type? 62. Can all spec examples be extracted as fixtures? 63. What edge case examples exist?

**OpenSensorHub Real-World Examples (5 questions):** 64. What GeoJSON examples available from OpenSensorHub? 65. What property complexity exists in real-world data? 66. What edge cases do real-world examples expose? 67. What validation issues exist in real-world data? 68. Can OpenSensorHub examples supplement spec examples?

**Parser Implementation Testing (6 questions):** 69. What parsing functions are CSAPI-specific? 70. What integration tests needed with existing GeoJSON parser? 71. What test organization (one file or per resource type)? 72. What test depth per resource type? 73. How many fixtures per resource type? 74. What's the balance between spec examples and hand-crafted tests?

---

## 3. Primary Resources

- **CSAPI Part 1 Specification:** https://docs.ogc.org/is/23-001/23-001.html (GeoJSON encoding sections)
- **GeoJSON RFC 7946:** https://tools.ietf.org/html/rfc7946
- **CSAPI Implementation Guide:** [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) (GeoJSON handler extensions)

---

## 4. Supporting Resources

- **Section 8 Deliverable:** CSAPI specification requirements (GeoJSON validation rules from Part 1)
- **Part 1 Requirements Analysis:** [docs/research/requirements/csapi-part1-requirements.md](../../requirements/csapi-part1-requirements.md)
- **Format Requirements Analysis:** [docs/research/requirements/csapi-format-requirements.md](../../requirements/csapi-format-requirements.md)
- **OpenSensorHub Analysis:** [docs/research/requirements/csapi-opensensorhub-analysis.md](../../requirements/csapi-opensensorhub-analysis.md)
- Section 6 Deliverable: "Meaningful vs Trivial" guide (quality context for test depth)
- Section 1-2 Deliverables: Upstream GeoJSON parser and tests (reuse strategy)
- GeoJSON validator (tool)
- JSON schema validator (tool)
- OpenSensorHub API access (tool)

---

## 5. Research Methodology

**Phase 1: CSAPI Part 1 GeoJSON Requirements (30-40 minutes)**

- Read CSAPI Part 1 spec (focus on GeoJSON encoding sections for all 5 resource types)
- Extract CSAPI-specific property definitions (uniqueIdentifier, featureType, systemType, etc.)
- Document required vs optional properties per resource type
- Document controlled vocabularies (featureType, systemType, samplingFeatureType)
- Document temporal property requirements (validTime, phenomenonTime)
- Document link structure requirements
- Document error conditions
- Estimated time: 30-40 minutes

**Phase 2: Existing Parser Analysis (20-30 minutes)**

- Review upstream ogc-client GeoJSON parser implementation
- Review existing GeoJSON test coverage (RFC 7946 compliance)
- Document what's already tested (geometry parsing, standard properties, collections)
- Document what needs CSAPI-specific testing (property validation, vocabularies)
- Design reuse strategy (inherit existing parser, extend for CSAPI)
- Estimated time: 20-30 minutes

**Phase 3: Resource Type Deep Dive (20-30 minutes)**

- Define Systems-specific testing (systemType, parent, samplingFeatures/properties/datastreams)
- Define Deployments-specific testing (deployedSystem, platform, validTime)
- Define Procedures-specific testing (procedureType, implementation)
- Define SamplingFeatures-specific testing (samplingFeatureType, sampledFeature)
- Define Properties-specific testing (observableProperty, uom)
- Document common property testing (uniqueIdentifier, featureType, definition, validTime, links)
- Determine validation priorities per resource type
- Estimated time: 20-30 minutes

**Phase 4: Example and Fixture Analysis (15-20 minutes)**

- Extract GeoJSON examples from CSAPI Part 1 spec
- Catalog OpenSensorHub examples (if available)
- Determine fixture requirements per resource type
- Plan fixture directory structure (fixtures/geojson-csapi/)
- Estimated time: 15-20 minutes

**Phase 5: Test Strategy Design (15-20 minutes)**

- Define test organization (single file: geojson-csapi.spec.ts)
- Define test depth per resource type (meaningful validation, not trivial)
- Design test structure (describe blocks per resource type)
- Plan integration with existing GeoJSON parser
- Document validation priorities (CRITICAL/HIGH/MEDIUM/LOW)
- Estimated time: 15-20 minutes

**Total Estimated Time: 1.5-2 hours**

---

## 6. Success Criteria

- [ ] All CSAPI-specific GeoJSON properties defined (uniqueIdentifier, featureType, resource-specific)
- [ ] All 5 Part 1 resource types covered (Systems, Deployments, Procedures, SamplingFeatures, Properties)
- [ ] Common property validation rules documented (uniqueIdentifier, featureType, definition, validTime, links)
- [ ] Resource-specific property validation rules documented (systemType, deployedSystem, observableProperty, etc.)
- [ ] Controlled vocabularies validated (featureType, systemType, samplingFeatureType, procedureType)
- [ ] Temporal property validation rules documented (ISO 8601 formats, intervals, edge cases)
- [ ] Link structure validation rules documented (href, rel, type, title)
- [ ] Reuse strategy clear (what to inherit from existing GeoJSON parser vs what's CSAPI-specific)
- [ ] Fixture requirements defined per resource type (~30 fixtures total)
- [ ] Test organization designed (geojson-csapi.spec.ts with describe blocks)
- [ ] Testing priorities assigned (CRITICAL/HIGH/MEDIUM/LOW)

**Validation:**

- All 74 research questions answered
- All 18 deliverable sections complete
- Validation priorities documented
- No duplication with existing RFC 7946 tests
- Clear integration with existing GeoJSON parser
- OpenSensorHub examples inventoried
- Ready for test implementation in Section 13

---

## 7. Deliverable

**Document Location:** `docs/deliverables/testing/geojson-csapi-testing-specification.md`

**Required Sections:**

### 1. Executive Summary

- CSAPI-specific properties to test (not RFC 7946 duplication)
- 5 Part 1 resource types covered
- Testing priorities (CRITICAL/HIGH/MEDIUM/LOW)
- Fixture count requirements (~30 total)
- Estimated test lines (492-829 lines)
- Reuse strategy for existing GeoJSON tests (inherit RFC 7946 coverage)

### 2. Existing GeoJSON Parser Coverage

- Matrix of what's tested upstream (RFC 7946) vs what needs CSAPI-specific testing
- Reuse strategy (inherit geometry/standard parsing, add CSAPI property validation)

### 3. CSAPI-Specific Property Testing Matrix

- Common properties table (7 properties: uniqueIdentifier, featureType, definition, label, description, validTime, links)
- Required/optional status, validation rules, edge cases, priorities

### 4. Resource Type Specific Testing Requirements

- **Systems Resource:** systemType (vocabulary), parent (URI), samplingFeatures/properties/datastreams (arrays)
- **Deployments Resource:** deployedSystem (required, CRITICAL), platform (optional), validTime (required)
- **Procedures Resource:** procedureType (vocabulary), implementation (URI)
- **SamplingFeatures Resource:** samplingFeatureType (vocabulary), sampledFeature (URI)
- **Properties Resource:** observableProperty (required, CRITICAL), uom (optional, UCUM codes)

### 5. featureType Vocabulary Validation

- Table of valid values per resource type (systems: system/platform/sensor, deployments: deployment, etc.)
- Validation strictness (strict = error on unknown)

### 6. Temporal Property Validation

- ISO 8601 interval formats (validTime, phenomenonTime)
- Valid examples ("2024-01-01/2024-12-31", "../2024-12-31", "2024-01-01/..")
- Invalid examples and error messages

### 7. Link Structure Validation

- Link properties: href (required, URI), rel (required, relation type), type (optional, MIME), title (optional)
- Test scenarios per property

### 8. Error Condition Testing

- 8 error conditions: missing uniqueIdentifier, invalid URI, missing featureType, unknown featureType, invalid systemType, invalid validTime, missing required resource-specific property, malformed link
- Expected error messages

### 9. Specification Example Fixtures

- Extract fixtures from Part 1 spec (one per resource type minimum)
- Catalog by section, resource type, complexity

### 10. OpenSensorHub Fixture Inventory

- Catalog real-world examples by resource type
- Assess CSAPI property coverage and usability

### 11. Test Organization

- Single test file: `src/ogc-api/formats/geojson-csapi.spec.ts`
- 7 describe blocks: Common Properties, Systems, Deployments, Procedures, SamplingFeatures, Properties, FeatureCollection Extensions, Error Handling

### 12. Test Depth Definition

- **DO:** Parse complete fixtures, validate CSAPI properties, validate URI formats strictly, validate controlled vocabularies, validate resource-specific properties, validate temporal properties, test error conditions, use real examples
- **DON'T:** Re-test standard GeoJSON (RFC 7946 covered upstream), just check for null, skip URI validation, skip vocabulary validation, use simple fixtures when spec exists, only test happy path

### 13. Fixture Requirements

- **Directory:** fixtures/geojson-csapi/
- **Per Type:** Systems (5), Deployments (4), Procedures (3), SamplingFeatures (4), Properties (3), FeatureCollections (3), Error cases (5)
- **Total:** ~30 fixtures

### 14. Validation Against Upstream Patterns

- Compare with existing GeoJSON tests
- Ensure no duplication of RFC 7946 coverage
- Document integration points

### 15. Integration with Implementation Guide

- Validate alignment with GeoJSON handler design
- Ensure test coverage matches implementation expectations

### 16. Testing Estimates

- 50-63 tests total
- 492-829 lines of test code
- 8-11 hours implementation time
- Breakdown by category: Common Properties (12-15 tests), Systems (8-10), Deployments (8-10), Procedures (5-6), SamplingFeatures (7-9), Properties (6-8), FeatureCollection (4-5), Error Handling (6-8)

### 17. Testing Priorities

- **CRITICAL:** uniqueIdentifier validation, featureType validation, deployedSystem validation (Deployments), observableProperty validation (Properties)
- **HIGH:** systemType vocabulary, samplingFeatureType vocabulary, validTime validation (Deployments), definition URI validation
- **MEDIUM:** temporal property validation, link validation, parent/sampled feature references, uom validation
- **LOW:** label/description validation, procedure implementation references

### 18. Risks and Edge Cases

- **Risk:** Over-testing standard GeoJSON → **Mitigation:** Clear reuse strategy, focus on CSAPI-specific
- **Risk:** Vocabulary validation too strict → **Mitigation:** Configurable strictness, warning vs error
- **Risk:** OpenSensorHub examples don't cover edge cases → **Mitigation:** Supplement with spec examples and hand-crafted fixtures
- **Risk:** Temporal property validation complexity → **Mitigation:** Use strict ISO 8601 parser, clear error messages
- **Risk:** Real-world data violates CSAPI requirements → **Mitigation:** Document deviations, implement lenient mode

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 8: CSAPI Specification Test Requirements (GeoJSON validation rules extracted from Part 1)
- Section 6: "Meaningful vs Trivial" Definition (test depth guidance)
- Section 1-2: Upstream GeoJSON Parser Analysis and Test Patterns (reuse strategy baseline)
- Part 1 Requirements Analysis: [docs/research/requirements/csapi-part1-requirements.md](../../requirements/csapi-part1-requirements.md) (property definitions)

**This Section Blocks:**

- Section 12: QueryBuilder Testing Requirements (Part 1 resource endpoints require GeoJSON parsing)
- Section 13: Resource Method Testing Requirements (all Part 1 resource methods use GeoJSON encoding)
- Section 14: Integration Test Workflows (discovery workflow uses GeoJSON resources: systems, deployments, sampling features)
- Section 15: Fixture Sourcing Strategy (GeoJSON fixture inventory feeds fixture organization)
- Section 36: Test Quality Checklist (GeoJSON test validation criteria)

---

## 9. Research Status Checklist

- [ ] **Phase 1 Complete:** CSAPI Part 1 GeoJSON requirements extracted (properties, vocabularies, temporal, links)
- [ ] **Phase 2 Complete:** Existing parser coverage documented, reuse strategy defined
- [ ] **Phase 3 Complete:** Resource type deep dive complete (5 resource types, property matrices)
- [ ] **Phase 4 Complete:** Fixture inventory complete (spec examples + OpenSensorHub + ~30 total)
- [ ] **Phase 5 Complete:** Test strategy designed (organization, depth, priorities)

---

## 10. Notes and Open Questions

**Risks and Mitigation:**

- **Over-testing standard GeoJSON:** ✅ RESOLVED - Document clearly specifies reuse strategy, what NOT to test
- **Vocabulary validation strictness:** ✅ ADDRESSED - Defined exact vocabulary lists (SOSA/SSN URIs, assetType enum)
- **OpenSensorHub edge case coverage:** ✅ PLANNED - Fixture plan includes ~30 fixtures: 10-15 spec, 10-15 OSH, 5-10 hand-crafted
- **Temporal property validation complexity:** ✅ SPECIFIED - ISO 8601 validation rules, open-ended intervals, error conditions

**Validation Strategy:**

- ✅ Reuse strategy defined: Extend existing GeoJSON parser, don't duplicate RFC 7946 tests
- ✅ CSAPI property validation: All properties documented with validation rules
- ✅ Controlled vocabularies: Complete SOSA/SSN vocabulary lists documented
- ✅ Temporal properties: ISO 8601 format, intervals, ordering rules specified
- ✅ Link structure: HATEOAS link validation requirements defined
- ✅ Error conditions: 7 error categories with examples

**Research Completion Summary:**

- ✅ All 74 research questions answered
- ✅ All 5 resource types documented (Systems, Deployments, Procedures, SamplingFeatures, Properties)
- ✅ 18 required sections completed
- ✅ Reuse strategy clear (extend existing parser, focus on CSAPI properties)
- ✅ Vocabulary validation requirements defined (SOSA/SSN, assetType)
- ✅ Temporal validation specified (ISO 8601 periods, open-ended intervals)
- ✅ Test organization designed (single file, 7 describe blocks, ~150 tests)
- ✅ Test priorities defined (P0-P3: CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Anti-patterns documented (what NOT to test)
- ✅ Fixture requirements (~30 total across 5 resource types)
- ✅ Example test implementation provided

**Next Steps After Completion:**

1. ✅ COMPLETED: Comprehensive specification document created (15,000 words, 18 sections)
2. TODO: Implement GeoJSON CSAPI tests in `src/ogc-api/formats/geojson-csapi.spec.ts`
3. TODO: Source fixtures from Part 1 spec and OpenSensorHub
4. TODO: Create fixture directory structure (fixtures/csapi-geojson/)
5. TODO: Validate test coverage against deliverable specification
6. TODO: Implement parser extensions following specification
