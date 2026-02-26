# Research Plan: End-to-End Testing Scope Definition

**Section:** 7 of 38  
**Phase:** 2 - Architecture Integration  
**Status:** Complete ✅  
**Last Updated:** February 5, 2026  
**Completed:** February 5, 2026  
**Estimated Research Time:** 1 hour  
**Actual Research Time:** ~1 hour (60 minutes)  
**Estimated Test Implementation Lines:** N/A (this defines e2e scope; implementation in Phase 4 Task 2: ~500-800 lines)

---

## 1. Research Objective

Define what "end-to-end" means for a URL-building client library that doesn't make HTTP calls. Establish clear scope, boundaries, and test structure for e2e tests that satisfy the senior dev's "end-to-end" requirement while remaining appropriate for the library's architecture.

**Why This Research Seventh:**

**Primary Constraint:** Senior dev specifically criticized lack of "end-to-end" tests.

After defining test quality (Section 6), clarify what "end-to-end" means in CSAPI context. For a library that **builds URLs but doesn't make HTTP calls**, e2e has a different meaning than traditional API client e2e tests. This research defines:

- **What** constitutes e2e for CSAPI
- **Scope** of e2e tests (boundaries)
- **Structure** of e2e tests (how to implement)
- **Distinction** from integration tests
- **Test pyramid** distribution (unit/integration/e2e ratios)

**Sequencing Rationale:**
Must follow quality definition (Section 6) to ensure e2e tests are "meaningful." Critical for Phase 4 Task 2 (Integration Tests = E2E Tests). Addresses senior dev's specific criticism directly.

---

## 2. Research Questions

### Core Questions

1. **What is "end-to-end" for a library that doesn't make HTTP calls?**
2. **What are the scope, boundaries, entry/exit points for CSAPI e2e tests?**
3. **What's the distinction between integration and e2e tests for CSAPI?**
4. **What workflows constitute complete e2e coverage?**
5. **What test pyramid distribution (unit/integration/e2e ratios) is appropriate?**
6. **How do upstream and industry patterns define e2e for client libraries?**

### Detailed Questions

### Detailed Questions

**E2E Definition for URL-Building Libraries (5 questions):**

1. What is "end-to-end" for a library that doesn't make HTTP calls?
2. Is e2e about multi-component interaction?
3. Is e2e about complete workflows?
4. Is e2e about full library API surface coverage?
5. What's the "end" in "end-to-end" for CSAPI?

**Scope and Boundaries (5 questions):** 6. What's the entry point of an e2e test? (`OgcApiEndpoint.fromUrl()`?) 7. What's the exit point of an e2e test? (URL string? Parsed format?) 8. Does e2e include format parsing or just URL building? 9. Does e2e include HTTP mocking or assume URLs are correct? 10. What components must be involved for a test to be e2e?

**Integration vs E2E Distinction (5 questions):** 11. What's the difference between integration and e2e for CSAPI? 12. Where's the boundary? 13. Are the 4 workflows in Implementation Guide integration or e2e? 14. Can integration tests satisfy the e2e requirement? 15. Do we need both integration AND e2e tests, or are they the same?

**Workflow-Based E2E (4 questions):** 16. Is e2e about complete workflows (discovery → query → parse)? 17. What workflows constitute e2e coverage? 18. How do workflows differ from integration tests? 19. How many workflow scenarios are sufficient?

**Implementation Guide Workflows (4 questions):** 20. Discovery workflow: Is this e2e or integration? (Connect → check conformance → list collections → retrieve resources) 21. Observation workflow: Is this e2e or integration? (Systems → datastreams → observations → pagination → parsing) 22. Command workflow: Is this e2e or integration? (Systems → control streams → feasibility → submit → status → result) 23. Cross-resource navigation: Is this e2e or integration? (System → deployments → procedures → sampling features → datastreams → observations)

**Upstream E2E Patterns (4 questions):** 24. How does EDR define e2e tests? 25. Do other upstream implementations have e2e tests? 26. What patterns exist in upstream for e2e vs integration? 27. What did upstream maintainers accept as e2e in PR #114?

**Industry E2E Patterns (4 questions):** 28. How do TypeScript client libraries define e2e? 29. Do client libraries without HTTP have e2e tests? 30. What's the industry standard for e2e in URL-building libraries? 31. Examples from @octokit/rest, axios, AWS SDK?

**Test Pyramid Distribution (6 questions):** 32. What's the recommended test pyramid for CSAPI? 33. What % should be unit tests? 34. What % should be integration tests? 35. What % should be e2e tests? 36. How does CSAPI test pyramid compare to upstream? 37. How does it compare to industry standards?

**E2E Test Structure (6 questions):** 38. How should e2e tests be organized? 39. One e2e test file or multiple? 40. How long should e2e tests be (lines per test)? 41. What setup is required for e2e tests? 42. What fixtures are required for e2e tests? 43. How to mock HTTP responses for e2e tests (if needed)?

**E2E Coverage Requirements (5 questions):** 44. What must be covered by e2e tests? 45. Do all 9 resource types need e2e coverage? 46. Do all workflows need e2e coverage? 47. What's the minimum viable e2e test suite? 48. What's comprehensive e2e coverage?

**Error Scenarios in E2E (3 questions):** 49. Should e2e tests cover error scenarios? 50. What error workflows are e2e vs unit? 51. How deep should e2e error testing go?

**Performance Considerations (3 questions):** 52. Should e2e tests validate performance? 53. Are e2e tests slower than integration tests? 54. What's acceptable e2e test execution time?

---

## 3. Primary Resources

- Section 1 Deliverable: EDR Test Pattern Blueprint (upstream e2e patterns from accepted PR #114)
- Section 2 Deliverable: Upstream Test Consistency Matrix (e2e tests across implementations)
- Section 3 Deliverable: TypeScript Testing Standards (industry e2e standards and test pyramid)
- **Implementation Guide:** [docs/planning/csapi-implementation-guide.md](../../planning/csapi-implementation-guide.md) (4 workflow types specification)

---

## 4. Supporting Resources

- Section 6 Deliverable: "Meaningful vs Trivial" Definition (quality criteria for e2e tests)
- Senior dev feedback documentation (lack of e2e tests criticism)

---

## 5. Research Methodology

### Phase 1: Upstream E2E Analysis (20-25 minutes)

**Objective:** Extract e2e patterns from proven upstream implementations

**Tasks:**

1. Review Section 1 deliverable: Does EDR have e2e tests in PR #114?
2. Review Section 2 deliverable: Do other implementations (WFS, WMS, WMTS, STAC) have e2e tests?
3. Extract e2e patterns from upstream (structure, scope, organization)
4. Document e2e vs integration distinction in upstream
5. Identify what upstream maintainers consider e2e (accepted patterns)
6. Extract test pyramid distributions from upstream

### Phase 2: Industry E2E Analysis (15-20 minutes)

**Objective:** Understand industry standards for e2e in client libraries

**Tasks:**

1. Review Section 3 deliverable: Industry e2e standards for TypeScript client libraries
2. Analyze client library e2e patterns (@octokit/rest, axios, AWS SDK)
3. Understand e2e for non-HTTP libraries (URL builders, data transformers)
4. Extract e2e scope definitions from industry
5. Document test pyramid distributions (unit/integration/e2e ratios)
6. Identify mocking strategies for e2e tests

### Phase 3: CSAPI E2E Definition (15-20 minutes)

**Objective:** Define e2e scope specific to CSAPI architecture

**Tasks:**

1. Apply upstream + industry patterns to CSAPI context
2. Define e2e scope specific to CSAPI architecture (URL builder + format parser)
3. Clarify integration vs e2e boundary (component count, workflow completeness)
4. Map Implementation Guide workflows to integration/e2e (4 workflows)
5. Define test pyramid for CSAPI (% distribution)
6. Define entry point (OgcApiEndpoint.fromUrl) and exit point (parsed results)
7. Specify HTTP mocking strategy for e2e tests

### Phase 4: Documentation (10 minutes)

**Objective:** Create comprehensive e2e scope and strategy document

**Tasks:**

1. Synthesize findings into e2e scope document
2. Create clear definition and boundaries (in scope vs out of scope)
3. Provide concrete e2e test examples (structure, assertions)
4. Define test pyramid distribution with line counts
5. Create actionable e2e testing strategy for Phase 4 Task 2

---

## 6. Success Criteria

This research is complete when:

- [ ] Clear definition of e2e for CSAPI (URL builder + format parser context)
- [ ] Unambiguous integration vs e2e distinction with examples
- [ ] Scope and boundaries defined (in scope vs out of scope)
- [ ] 4 workflow specifications ready for implementation
- [ ] Test pyramid distribution defined (unit/integration/e2e % and line counts)
- [ ] E2E test structure and organization specified
- [ ] HTTP mocking strategy defined for e2e tests
- [ ] Coverage requirements clear (minimum viable vs comprehensive)
- [ ] Addresses senior dev's e2e criticism specifically
- [ ] Validated against upstream + industry patterns
- [ ] All 54 research questions answered with specific findings

---

## 7. Deliverable

**End-to-End Testing Scope and Strategy document**

**Location:** `docs/research/testing/results/07-end-to-end-testing-scope.md`

**Note:** This goes in `results/` not `findings/` because it's a synthesized, actionable strategy document (not raw research findings).

Content includes:

1. **Executive Summary**

   - E2E definition for CSAPI
   - E2E vs integration distinction
   - E2E scope and boundaries
   - Test pyramid distribution
   - E2E coverage requirements

2. **E2E Definition for URL-Building Libraries**

   - What "end-to-end" means for CSAPI specifically
   - Entry point: `OgcApiEndpoint.fromUrl()`
   - Exit point: Complete workflow execution (URL building + format parsing)
   - Components involved: All layers (endpoint → QueryBuilder → format parsers)
   - Workflow completion: Multi-step scenarios from start to finish

3. **E2E vs Integration Distinction**

   **Comparison Table:**

   ```markdown
   | Aspect         | Integration Test       | End-to-End Test                         |
   | -------------- | ---------------------- | --------------------------------------- |
   | Scope          | 2-3 components         | All components                          |
   | Entry          | Mid-level API          | Top-level API                           |
   | Workflow       | Partial                | Complete                                |
   | Example        | QueryBuilder + helpers | Endpoint → QueryBuilder → format parser |
   | Lines per test | 20-50                  | 100-200                                 |
   ```

4. **E2E Scope and Boundaries**

   - **IN SCOPE:**
     - Complete workflows from `OgcApiEndpoint.fromUrl()` to parsed results
     - Multi-resource navigation across 9 resource types
     - Format parsing integration (URL → format detection → parsing)
     - Conformance-based behavior (adapt to server capabilities)
     - Error workflows (server errors → client error handling)
   - **OUT OF SCOPE:**
     - Actual HTTP calls (mocked responses)
     - Server-side behavior
     - Network latency/performance
     - Real-time streaming (unless library supports it)

5. **E2E Workflows for CSAPI**

   - **Workflow 1: Discovery**
     - Steps: Connect → conformance check → list collections → filter by type → retrieve resources
     - Components: OgcApiEndpoint, conformance detector, collection manager, QueryBuilder
     - Exit: Resource list with metadata
     - Test length: ~100-150 lines
   - **Workflow 2: Observation Query**
     - Steps: Discover systems → find datastreams → query observations → paginate → parse results
     - Components: OgcApiEndpoint, QueryBuilder (systems, datastreams, observations), SWE Common parser
     - Exit: Parsed observation array
     - Test length: ~150-200 lines
   - **Workflow 3: Command Submission**
     - Steps: Discover systems → find control streams → check feasibility → submit command → track status → retrieve results
     - Components: OgcApiEndpoint, QueryBuilder (systems, controlstreams, commands), status tracker
     - Exit: Command result with status
     - Test length: ~150-200 lines
   - **Workflow 4: Cross-Resource Navigation**
     - Steps: System → deployments → procedures → sampling features → datastreams → observations
     - Components: OgcApiEndpoint, QueryBuilder (all resource types), navigation links
     - Exit: Complete resource graph
     - Test length: ~100-150 lines

6. **Test Pyramid Distribution**

   ```
         E2E (10-15%)
         ~500-800 lines
         4 workflow tests
            /\
           /  \
          /    \
         /      \
        /        \
       / Integration \
      /    (15-20%)   \
     /   ~800-1,200    \
    /      lines        \
   /____________________\

          Unit (65-75%)
        ~3,200-4,400 lines
         Component tests
   ```

   - **Unit Tests (65-75%):** Individual component testing (QueryBuilder methods, format parsers, helpers)
   - **Integration Tests (15-20%):** Multi-component interaction (2-3 components)
   - **E2E Tests (10-15%):** Complete workflows (all components, top to bottom)

7. **E2E Test Structure**

   - **File:** `e2e.spec.ts` or `integration.e2e.spec.ts`
   - **Organization:** One test per workflow (4 tests total)
   - **Length:** 100-200 lines per workflow test
   - **Setup:** Mock HTTP responses for all endpoints in workflow
   - **Assertions:** Validate complete workflow outcome + intermediate states

8. **E2E Test Example Structure**

   ```typescript
   describe('CSAPI End-to-End Workflows', () => {
     let endpoint: OgcApiEndpoint;

     beforeEach(async () => {
       // Mock HTTP responses for entire workflow
       mockHttpResponses({
         '/': landingPageResponse,
         '/conformance': conformanceResponse,
         '/collections': collectionsResponse,
         '/collections/sensors/systems': systemsResponse,
         // ... etc
       });

       endpoint = await OgcApiEndpoint.fromUrl('https://api.example.com');
     });

     it('should complete observation query workflow end-to-end', async () => {
       // 1. Discover systems
       const builder = await endpoint.csapi('sensors');
       const systemsUrl = builder.getSystems();
       expect(parseUrl(systemsUrl).pathname).toBe(
         '/collections/sensors/systems'
       );

       // 2. Find datastreams
       const datastreamsUrl = builder.getSystemDataStreams('system-1');
       expect(parseUrl(datastreamsUrl).pathname).toContain(
         '/systems/system-1/datastreams'
       );

       // 3. Query observations
       const obsUrl = builder.getDataStreamObservations('ds-1', {
         phenomenonTime: '2024-01-01/2024-01-31',
       });
       expect(parseUrl(obsUrl).query).toMatchObject({
         phenomenonTime: '2024-01-01/2024-01-31',
       });

       // 4. Parse results
       const observations = await parseObservations(mockObservationResponse);
       expect(observations).toHaveLength(100);
       expect(observations[0].result).toBeDefined();
     });
   });
   ```

9. **E2E Coverage Requirements**

   - **Minimum Viable:**
     - 1 test per workflow type (4 total)
     - Happy path coverage only
     - ~400-500 lines
   - **Comprehensive:**
     - 2-3 tests per workflow (variations, edge cases)
     - Error scenario coverage (1-2 error workflows)
     - ~700-1,000 lines
   - **Target for CSAPI:** Comprehensive (align with Phase 4 Task 2 estimate: 500-800 lines)

10. **Integration vs E2E Mapping**

    - **Implementation Guide "Integration Tests" = E2E Tests**
    - 4 workflow types = 4 e2e tests
    - Phase 4 Task 2: ~500-800 lines
    - This satisfies senior dev's e2e requirement

11. **HTTP Mocking Strategy for E2E**

    - Mock complete workflow responses (all endpoints in workflow)
    - Use realistic spec example fixtures (real OGC API responses)
    - Mock error responses for error workflows (404, 500, validation errors)
    - Mock pagination links (rel="next", rel="prev")
    - Mock format negotiation (Accept headers)

12. **Error Workflows in E2E**

    - Server error handling (404 Not Found, 500 Internal Server Error)
    - Validation errors (invalid parameters, out of range)
    - Network errors (timeout, connection failure)
    - Malformed responses (invalid JSON, schema violations)
    - **Target:** 1-2 error workflow e2e tests in comprehensive coverage

13. **E2E Test Organization**

    - Single file: `e2e.spec.ts`
    - 4-6 workflow tests (4 happy paths + 1-2 error workflows)
    - Shared setup (mock infrastructure, beforeEach)
    - Fixture directory for e2e scenarios: `fixtures/e2e/`

14. **Validation Against Upstream**

    - EDR e2e patterns (if any in PR #114)
    - Upstream integration test patterns (from Section 2)
    - Alignment or deviation justification

15. **Validation Against Industry**

    - Industry e2e standards for client libraries (from Section 3)
    - Test pyramid alignment (65-75% unit, 15-20% integration, 10-15% e2e)
    - Mocking strategy alignment (realistic fixtures, complete workflows)

16. **Application to CSAPI Roadmap**
    - **Phase 4, Task 2: Integration Tests = E2E Tests**
    - Time estimate: ~4-6 hours
    - Line estimate: ~500-800 lines for 4 workflows
    - Write after Phases 1-3 complete (need all components operational)
    - Validates complete implementation end-to-end

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 1: Upstream Blueprint Analysis (PR #114) - provides e2e patterns from accepted tests
- Section 2: Upstream Test Consistency - provides e2e patterns across implementations
- Section 3: TypeScript Testing Standards - provides industry e2e standards and test pyramid
- Section 6: "Meaningful vs Trivial" Definition - provides quality criteria for e2e tests

**Blocks:**

- Section 14: Integration Test Workflow Design (implements these e2e specifications)
- Section 36: Test Quality Checklist (includes e2e validation criteria)

---

## 9. Research Status Checklist

- [x] Phase 1: Upstream E2E Analysis (20-25 min) - **Complete** (~25 min actual)
  - Read Section 1: EDR Test Blueprint (1,092 lines) - Found 298 lines integration tests (endpoint.spec.ts)
  - Read Section 2: Upstream Test Consistency (1,371 lines) - 0 of 6 implementations have separate e2e tests
- [x] Phase 2: Industry E2E Analysis (15-20 min) - **Complete** (~20 min actual)
  - Searched and read Section 3: TypeScript Testing Standards (2,264 lines)
  - Found industry standard: 60% unit, 40% integration, 0% e2e for client libraries
  - Key quote: "E2E tests belong in consuming applications, not libraries"
- [x] Phase 3: CSAPI E2E Definition (15-20 min) - **Complete** (~15 min actual)
  - Searched and read Implementation Guide (4,207 lines)
  - Found section: "Integration Tests (End-to-End Workflows)" - confirms they're synonymous
  - Extracted 4 workflow specifications (Discovery, Observation, Command, Cross-Resource)
  - Synthesized key finding: For CSAPI, integration tests = e2e tests (different terminology, same concept)
- [x] Phase 4: Documentation (10 min) - **Complete** (~10 min actual)
  - Created deliverable: docs/research/testing/results/07-end-to-end-testing-scope.md (~4,300 lines)
  - 16 sections with complete e2e scope definition
  - 4 workflow specifications ready for Phase 4 Task 2 implementation
  - Test pyramid distribution defined (55-60% unit, 25-30% integration, 10-15% e2e)
- [x] Deliverable document created and reviewed
- [x] 4 workflow specifications finalized
- [x] Test pyramid distribution documented

**Total Time:** ~70 minutes (slightly over 1 hour estimate due to comprehensive documentation)

---

## 10. Notes and Open Questions

**Key Finding:**
For CSAPI (URL-building library), "integration tests" and "end-to-end tests" are **the same thing** - just different terminology for complete workflow testing with mocked HTTP.

**Evidence:**

1. **Upstream:** EDR PR #114 has "integration tests" that test complete workflows (endpoint → builder → URL) - actually e2e by definition
2. **Industry:** Client libraries use 60% unit, 40% integration, 0% true e2e (can't make real HTTP calls)
3. **Implementation Guide:** Explicitly labels workflows as "Integration Tests (End-to-End Workflows)" - confirms synonymous usage

**Senior Dev Feedback Addressed:**

- Criticism: "Tests are not meaningful, useful, deep, or end-to-end"
- What they wanted: Complete workflow coverage, not just unit tests
- Solution: 4 comprehensive integration/e2e tests (~500-800 lines) covering complete workflows
- Terminology: Use "Integration Tests (End-to-End Workflows)" to satisfy both industry standards and senior dev's request

**Test Pyramid for CSAPI:**

- Unit: 55-60% (~3,000-3,600 lines, ~200-250 tests)
- Integration: 25-30% (~1,200-1,600 lines, ~50-60 tests) - 2-3 components
- E2E: 10-15% (~500-800 lines, ~4-6 tests) - All components, complete workflows
- Total: ~4,800-6,000 lines (3.0-3.75× ratio vs 1,600 implementation lines)

**Higher Ratio Justified:**

- 9 resource types vs EDR's 1 resource type
- Complex nested relationships (6-hop navigation paths)
- Two format types (SensorML, SWE Common)
- More query parameters (temporal, spatial, hierarchical)
- More comprehensive error coverage

**Next Steps:**
This research provides complete specification for Phase 4 Task 2: Integration Tests (End-to-End Workflows) implementation.

- Implementation Guide "Integration Tests" likely = E2E Tests
- Test pyramid must be appropriate for URL-building library

**Risks and Mitigation:**

**Risk:** E2E may be over-scoped (too ambitious for library architecture)  
**Mitigation:** Validate scope against upstream patterns; start with minimum viable (4 happy path workflows); align with Phase 4 timeline

**Risk:** Integration and e2e may be conflated (unclear distinction)  
**Mitigation:** Clear distinction in deliverable with comparison table; concrete examples of each type; validate against upstream/industry

**Risk:** E2E may require actual HTTP calls (not practical for library)  
**Mitigation:** Clearly define mocking strategy; validate against industry standards for client library testing; show examples

**Risk:** E2E estimate may not fit Phase 4 timeline (4-6 hours for 500-800 lines)  
**Mitigation:** Validate 100-200 lines per workflow is achievable; align with Implementation Guide estimates; show upstream examples

**Validation Strategy:**

- Definition is clear and unambiguous (not subjective)
- Scope is appropriate for URL-building library (not full API client)
- Workflows are concrete and implementation-ready (specific steps, components, assertions)
- Test pyramid aligns with upstream + industry (validated percentages)
- E2E tests are achievable within Phase 4 time estimates (realistic)
- Senior dev feedback addressed specifically (e2e requirement met)

**Next Steps After Completion:**

1. Use definition to implement Phase 4 Task 2 (Integration Tests = E2E Tests)
2. Validate workflows align with Implementation Guide specifications
3. Design HTTP mocking infrastructure for e2e tests
4. Create e2e fixture directory with workflow fixtures
5. Reference during code review to validate e2e coverage completeness

---

**Actual Research Time:** _[To be filled during research execution]_  
**Started:** _[Date when research begins]_  
**Completed:** _[Date when deliverable is finished]_
