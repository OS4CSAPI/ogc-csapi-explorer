# Testing Strategy Research

**Purpose:** Define what constitutes meaningful, production-quality testing for the CSAPI client implementation.

**Context:** Previous test suite was criticized as "trivial" and lacking depth. Need to understand:

- What upstream maintainers expect
- What "end-to-end" means for a URL-building client library
- How to test CSAPI/SensorML/SWE/GeoJSON properly
- Industry standards for TypeScript client library testing

---

## Research Questions

### 1. Upstream Testing Patterns

**Primary Reference: [PR #114 - EDR Implementation](https://github.com/camptocamp/ogc-client/pull/114)**

**Questions to answer:**

- [ ] How many test files did EDR add?
- [ ] What types of tests? (unit, integration, e2e?)
- [ ] What's the test coverage %?
- [ ] How do they test URL builders?
- [ ] What fixtures do they use? (real data vs mocks?)
- [ ] How do they test format negotiation?
- [ ] What edge cases do they cover?
- [ ] How do they structure test files?
- [ ] What testing libraries/frameworks do they use?

**Action:** Deep dive into PR #114 test files and document patterns

---

### 2. Existing ogc-client Test Patterns

**Sources to study:**

- WFS implementation tests
- STAC implementation tests
- OgcApiEndpoint tests
- Shared utility tests

**Questions to answer:**

- [ ] What's the consistent test structure across implementations?
- [ ] How do they test conformance detection?
- [ ] How do they test collection handling?
- [ ] What mocking strategies do they use?
- [ ] How do they test TypeScript types?
- [ ] What's the typical test-to-code ratio?
- [ ] How do they organize test fixtures?

**Action:** Survey existing test files in upstream repo

---

### 3. TypeScript Client Library Testing Best Practices

**Questions to answer:**

- [ ] What does "meaningful" testing look like for a client library?
- [ ] What's considered good coverage %? (line, branch, function)
- [ ] How to test without actual HTTP calls?
- [ ] How to validate generated URLs thoroughly?
- [ ] How to test TypeScript interfaces and types?
- [ ] What's the difference between unit and integration tests in this context?
- [ ] How to test error conditions?

**Resources to investigate:**

- TypeScript testing guides
- Client library testing patterns (axios, fetch-wrappers, etc.)
- OGC/geospatial client library examples

---

### 4. CSAPI-Specific Testing Requirements

**Questions to answer:**

- [ ] Does CSAPI spec define test requirements or conformance tests?
- [ ] Are there CSAPI test suites we should reference?
- [ ] What are the critical paths that MUST be tested?
- [ ] What CSAPI-specific edge cases exist?
- [ ] How to test all 9 resource types systematically?
- [ ] What query parameter combinations are most critical?

**Sources:**

- [CSAPI Part 1 Spec](../research/ogcapi-connectedsystems-1.bundled.oas31.yaml)
- [CSAPI Part 2 Spec](../research/ogcapi-connectedsystems-2.bundled.oas31.yaml)
- OGC conformance test suites (if they exist)

---

### 5. Format Validation Testing (SensorML/SWE/GeoJSON)

**Questions to answer:**

- [ ] What constitutes "real" test data vs trivial mocks?
- [ ] Where to get valid SensorML 3.0 examples?
- [ ] Where to get valid SWE Common 3.0 examples?
- [ ] What GeoJSON variations must be tested?
- [ ] How deep to validate nested structures?
- [ ] How to test format detection?
- [ ] How to test invalid/malformed data?

**Sources:**

- SensorML 3.0 spec examples
- SWE Common 3.0 spec examples
- CSAPI spec example responses
- OpenSensorHub test data
- 52°North test data

---

### 6. URL Builder Testing Patterns

**Specific challenges:**

- [ ] How to validate complete URL structure (protocol, host, path, query)?
- [ ] How to test URL encoding (spaces, special chars, arrays)?
- [ ] How to test query parameter combinations (10+ params × multiple values)?
- [ ] How to test optional vs required parameters?
- [ ] How to test parameter precedence/conflicts?
- [ ] How to test base URL handling?
- [ ] How to verify URLs match OpenAPI spec?

**Action:** Find examples of thorough URL builder tests in similar libraries

---

### 7. Coverage Targets and Metrics

**Questions to answer:**

- [ ] What coverage % should we target overall?
- [ ] Which modules need 95%+ coverage?
- [ ] Which modules can be lower priority?
- [ ] How to measure meaningful coverage (not just %)?
- [ ] What's acceptable for:
  - Statement coverage?
  - Branch coverage?
  - Function coverage?
  - Line coverage?

**Benchmark:** What does PR #114 have?

---

### 8. Integration Test Strategy

**Questions to answer:**

- [ ] What counts as "integration" vs "unit" for this project?
- [ ] Should we test against mock CSAPI endpoints?
- [ ] Should we test against real CSAPI servers? (Answer: No - that's what CSAPI-Live-Testing was for)
- [ ] How to test OgcApiEndpoint integration?
- [ ] How to test navigator caching?
- [ ] How to test conformance class detection?

---

### 9. Test Organization and Structure

**Questions to answer:**

- [ ] How to organize test files? (per resource? per functionality?)
- [ ] How to organize fixtures?
- [ ] How to share test utilities?
- [ ] How to name test files?
- [ ] How to structure describe/it blocks?
- [ ] How to document test intent?

---

### 10. Previous Work - Lessons Learned

**From [ogc-client-CSAPI](https://github.com/OS4CSAPI/ogc-client-CSAPI):**

- [ ] What tests existed? (196 initial, 499 final)
- [ ] What feedback did we get?
- [ ] What was "trivial"?
- [ ] What coverage did we achieve? (81.46%)
- [ ] What modules had low coverage?
- [ ] What tests should we keep vs rewrite?

**Action:** Review test suite from second iteration and identify gaps

---

## Research Deliverables

### Phase 1: Investigation (Complete these first)

1. **PR #114 Test Analysis Document** - Line-by-line breakdown of EDR test strategy
2. **Upstream Test Pattern Summary** - Common patterns across WFS/STAC/EDR
3. **Test Data Inventory** - Where to get real SensorML/SWE/GeoJSON examples

### Phase 2: Strategy Definition

4. **Test Specification Template** - Standardized structure for each resource type
5. **Coverage Requirements by Module** - Specific targets for each code area
6. **Test Fixture Plan** - What fixtures to create and where to source them

### Phase 3: Implementation Guide

7. **Testing Playbook** - Step-by-step guide for writing tests
8. **Test Examples** - Concrete "good" vs "trivial" examples
9. **Quality Checklist** - How to validate tests are meaningful

---

## Success Criteria

Research is complete when we can answer:

1. ✅ "What would a maintainer expect to see in our test suite?"
2. ✅ "How do we know if our tests are meaningful vs trivial?"
3. ✅ "What specific fixtures and data should we use?"
4. ✅ "What coverage targets should we hit for each module?"
5. ✅ "How do we structure tests to match upstream patterns?"

---

## Next Steps

1. Start with PR #114 analysis (it's our blueprint)
2. Document findings in this file as we discover them
3. Create separate detailed analysis docs if needed
4. Update FEATURE_SPEC.md testing section as we learn
5. Create testing playbook before writing any code

---

## Notes & Findings

_(Add research findings here as we investigate)_
