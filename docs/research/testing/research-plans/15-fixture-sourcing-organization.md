# Section 15: Fixture Sourcing and Organization Strategy - Research Plan

**Status:** ✅ COMPLETE  
**Last Updated:** January 31, 2025  
**Research Time:** 3.5 hours (Estimated: 2-3 hours)  
**Fixture Count:** ~280 fixtures identified

---

## 1. Research Objective

Create comprehensive plan for sourcing, organizing, and maintaining test fixtures for all components.

**Why Fifteenth:** After defining all test requirements (Sections 8-14), identify what fixtures are needed and where to source them.

---

## 2. Research Questions ✅

### Core Questions - ANSWERED

1. ✅ What fixtures can be extracted from CSAPI specifications? **25+ examples from Parts 1 & 2**
2. ✅ What fixtures can be sourced from OpenSensorHub demo server? **NONE - Server unavailable (404)**
3. ✅ What fixtures need to be hand-crafted (edge cases, errors)? **~110 fixtures (GeoJSON, workflows, errors)**
4. ✅ How to organize fixtures by resource type and format? **Test-type hierarchy with resource subdirectories**
5. ✅ How to structure fixture files for reusability? **Universal fixtures, cross-format equivalence, composition**
6. ✅ How to document fixture provenance? **Embedded metadata + sidecar files + SOURCES.md**
7. ✅ How to keep fixtures in sync with spec updates? **Automated validation, quarterly review, changelog**

### Detailed Questions - ANSWERED

- ✅ What fixture formats are needed? **JSON (primary), CSV (SWE text), Binary (SWE base64)**
- ✅ How many fixture variants per resource type? **4 variants: valid (2), invalid (2) for GeoJSON; 3 encodings for SWE**
- ✅ What edge case fixtures are essential? **30 fixtures: empty, null, invalid, schema violations, HTTP errors, extreme**
- ✅ How to handle large vs small fixtures? **Size-based complexity classification: simple (15-30 min), medium (30-60 min), complex (1-3 hrs)**
- ✅ What naming conventions for fixtures? **kebab-case: `<category>-<subcategory>-<variant>.<ext>`**
- ✅ How to version fixtures alongside code? **Metadata tracking, schema pinning, changelog**
- ✅ What fixture validation is needed? **Schema (Ajv), semantic (vocabularies), integration (link integrity)**

---

## 3. Primary Resources ✅

- ✅ **CSAPI Part 1 Specification**: Extracted 11 Part 1 examples
- ✅ **CSAPI Part 2 Specification**: Extracted 14+ Part 2 examples
- ✅ **SensorML 3.0 Specification**: https://docs.ogc.org/is/23-000/23-000.html (Accessible, examples extracted)
  - JSON Schema Repository: https://schemas.opengis.net/sensorML/3.0/json/
  - JSON Example Repository: https://schemas.opengis.net/sensorML/3.0/json/examples/
- ✅ **SWE Common 3.0 Specification**: https://docs.ogc.org/is/24-014/24-014.html (Accessible, examples extracted)
  - JSON Schema Repository: https://schemas.opengis.net/sweCommon/3.0/json/
  - Annex B.1: Text encoding examples
  - Annex B.2: JSON encoding examples
- ⚠️ **OpenSensorHub Demo Server**: http://sensiasoft.net:8181/sensorhub/api/ (UNAVAILABLE - 404 error)
- ⏳ **52°North Server**: Not yet accessed (potential alternative source)

## 4. Supporting Resources ✅

- ✅ Section 8 deliverable (CSAPI specification fixture requirements) - 25+ fixtures
- ✅ Section 9 deliverable (SensorML fixture requirements) - ~25 fixtures
- ✅ Section 10 deliverable (SWE Common fixture requirements) - ~120 fixtures
- ✅ Section 11 deliverable (GeoJSON fixture requirements) - ~20 fixtures
- ✅ Section 12 deliverable (QueryBuilder fixture needs) - 5 fixtures
- ✅ Section 13 deliverable (Resource method fixture needs) - 23 fixtures
- ✅ Section 14 deliverable (Integration workflow fixture needs) - 33 fixtures

---

## 5. Research Methodology ✅

### Phase 1: Fixture Inventory ✅ (90 minutes)

**Objective:** Catalog all fixtures needed across all test types

**Tasks:**

1. ✅ Extract fixture requirements from Section 8-14 deliverables
2. ✅ Categorize fixtures by resource type and format
3. ✅ Identify fixture variants needed (valid, invalid, edge cases)
4. ✅ Document fixture count estimates per category
5. ✅ Create fixture requirements matrix

**Deliverables:**

- ✅ Complete fixture inventory: ~280 fixtures
- ✅ Fixture matrix (Section 2.1 of deliverable)
- ✅ Complexity analysis (Section 2.2)
- ✅ Category breakdown (Section 3)

### Phase 2: Fixture Sourcing Analysis ✅ (60 minutes)

**Objective:** Identify optimal sources for each fixture type

**Tasks:**

1. ✅ Identified CSAPI specification examples (25+)
2. ✅ Accessed SensorML 3.0 specification (SUCCESS - full spec retrieved)
3. ✅ Accessed SWE Common 3.0 specification (SUCCESS - full spec retrieved)
4. ⚠️ Attempted OpenSensorHub demo server (FAILED - 404 error)
5. ⏳ 52°North server (deferred - not critical)
6. ✅ Identified gaps requiring hand-crafted fixtures (~110)
7. ✅ Documented fixture sourcing plan (Section 4)

**Deliverables:**

- ✅ Sourcing strategy by category (Section 4.1-4.8)
- ✅ Specification access confirmed
- ✅ OpenSensorHub unavailability documented
- ✅ Hand-crafting requirements identified

### Phase 3: Organization Structure Design ✅ (45 minutes)

**Objective:** Design fixture directory structure and naming conventions

**Tasks:**

1. ✅ Analyzed upstream fixture patterns (hierarchical by test type)
2. ✅ Designed directory structure: test-type primary, resource/workflow secondary
3. ✅ Defined naming conventions: kebab-case with variant indicators
4. ✅ Designed metadata system: embedded + sidecar files
5. ✅ Created organization specification (Section 5-7 of deliverable)

**Deliverables:**

- ✅ Directory structure design (30 directories) - Section 5
- ✅ File naming conventions with variant indicators - Section 6
- ✅ Metadata schema and provenance system - Section 7

### Phase 4: Reusability and Maintenance Strategy ✅ (30 minutes)

**Objective:** Define how fixtures will be shared and maintained

**Tasks:**

1. ✅ Identified fixture reuse opportunities across tests (universal fixtures)
2. ✅ Designed fixture loading utilities (composition patterns)
3. ✅ Defined fixture validation process (schema, semantic, integration)
4. ✅ Created fixture update/sync procedures (spec updates, quarterly review)
5. ✅ Documented fixture maintenance guidelines (Section 9)

**Deliverables:**

- ✅ Reusability patterns documentation - Section 8
- ✅ Maintenance procedures - Section 9
- ✅ Validation requirements - Section 10

### Phase 5: Synthesis ✅ (45 minutes)

**Objective:** Create comprehensive fixture sourcing and organization plan

**Tasks:**

1. ✅ Consolidated fixture inventory (~280 fixtures cataloged)
2. ✅ Created complete sourcing plan with URLs/sources (Section 4)
3. ✅ Finalized directory structure specification (Section 5)
4. ✅ Documented fixture management procedures (Section 9)
5. ✅ Created deliverable document (15 sections, ~25,000 words)

**Deliverables:**

- ✅ 3-phase execution plan with day-by-day tasks - Section 11
- ✅ Implementation priorities (~290 hours estimated) - Section 12
- ✅ Risk assessment (9 risks with mitigations) - Section 13
- ✅ Success criteria (4 categories) - Section 14
- ✅ Complete deliverable document

---

## 6. Success Criteria ✅

This research is complete when:

- ✅ Complete fixture inventory exists for all test types (~280 fixtures)
- ✅ Fixture sources are identified with specific URLs/locations (specs, hand-craft)
- ✅ Directory structure is designed and validated (30 directories)
- ✅ Naming conventions are documented (kebab-case with variant indicators)
- ✅ Reusability strategy is defined (universal, cross-format, composition)
- ✅ Maintenance procedures are documented (spec updates, quarterly review)
- ✅ Deliverable document is peer-reviewed (ready for commit)

---

## 7. Deliverable ✅

**Complete fixture inventory with sourcing plan and directory structure**

Content includes:

- ✅ Fixture requirements matrix (by resource type, format, variant) - Section 2
- ✅ Fixture sourcing plan with specific sources/URLs - Section 4
- ✅ Directory structure specification - Section 5
- ✅ File naming conventions - Section 6
- ✅ Fixture metadata/provenance templates - Section 7
- ✅ Reusability patterns and utilities - Section 8
- ✅ Maintenance and sync procedures - Section 9
- ✅ Fixture validation requirements - Section 10
- ✅ Fixture count estimates (~280 total)
- ✅ 3-phase execution plan (5 weeks) - Section 11
- ✅ Implementation priorities - Section 12
- ✅ Risk assessment and mitigations - Section 13
- ✅ Success criteria with acceptance checklist - Section 14

**File:** `docs/research/testing/findings/15-fixture-sourcing-organization.md`  
**Size:** ~25,000 words, 15 sections  
**Status:** ✅ COMPLETE - Ready for commit

---

## 8. Dependencies ✅

**Must Complete Before Starting:**

- ✅ Section 8: CSAPI Specification Test Requirements
- ✅ Section 9: SensorML 3.0 Format Testing Requirements
- ✅ Section 10: SWE Common 3.0 Format Testing Requirements
- ✅ Section 11: GeoJSON CSAPI Extensions Testing Requirements
- ✅ Section 12: QueryBuilder URL Construction Testing Strategy
- ✅ Section 13: Resource Method Testing Patterns
- ✅ Section 14: Integration Test Workflow Design

**Blocks (Now Unblocked):**

- Section 16: Test Coverage Requirements (can use fixture count)
- Section 17: Mocking and Stubbing Strategy (can use fixture organization)
- Section 18: Test Data Generation Strategies (can use sourcing plan)
- Section 19: Test Organization and File Structure (can use directory structure)
- ROADMAP Phase 4: Test Implementation (fixtures can now be created)

---

## 9. Research Status Checklist ✅

- ✅ Phase 1: Fixture Inventory - Complete (90 minutes)
- ✅ Phase 2: Fixture Sourcing Analysis - Complete (60 minutes)
- ✅ Phase 3: Organization Structure Design - Complete (45 minutes)
- ✅ Phase 4: Reusability and Maintenance Strategy - Complete (30 minutes)
- ✅ Phase 5: Synthesis - Complete (45 minutes)
- ✅ Deliverable document created and reviewed
- ✅ Cross-references updated in related documents
- ✅ Research plan updated with completion status

**Total Research Time:** 3.5 hours (Estimated: 2-3 hours)  
**Completion Date:** January 31, 2025

---

## 10. Key Findings

**Fixture Sources:**

- ✅ CSAPI Specs: 25+ examples from Parts 1 & 2
- ✅ SensorML 3.0: https://docs.ogc.org/is/23-000/23-000.html + examples repo
- ✅ SWE Common 3.0: https://docs.ogc.org/is/24-014/24-014.html (Annex B.1/B.2: 15 examples)
- ⚠️ OpenSensorHub: http://sensiasoft.net:8181/sensorhub/api/ **UNAVAILABLE (404)**
- ⏳ 52°North: Not accessed (deferred)

**Fixture Breakdown:**

- From Specs: ~170 fixtures
- Hand-Crafted: ~110 fixtures
- Total: ~280 fixtures minimum

**Critical Priorities (MVP):**

- 46 fixtures for critical path: QueryBuilder (5), CSAPI Part 1 (11), GeoJSON valid (10), Integration discovery (8), Resource universal (5), SensorML basic (7)

**Execution Plan:**

- Phase 1 (Weeks 1-2): Spec extraction (~170 fixtures)
- Phase 2 (Weeks 3-4): Hand-crafting (~80 fixtures)
- Phase 3 (Week 5): Validation and integration
- Total Effort: ~290 hours (~7.5 weeks)
- SensorML/SWE Common specifications contain extensive examples
- Need to verify fixture licensing/attribution requirements

---

**Next Steps:** Compile fixture requirements from all previous section deliverables.
