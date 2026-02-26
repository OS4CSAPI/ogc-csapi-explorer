# Section 02: Existing Upstream Test Pattern Survey - Research Plan

**Status:** Complete ✅  
**Last Updated:** February 5, 2026  
**Estimated Research Time:** 2-3 hours  
**Actual Research Time:** 2.5 hours  
**Start Time:** February 5, 2026 10:30 AM  
**Completion Time:** February 5, 2026 1:00 PM  
**Estimated Test Implementation Lines:** N/A (Research produces analysis document, not tests)

---

## 1. Research Objective

Survey and document consistent testing patterns across all existing ogc-client implementations (WFS, WMS, WMTS, STAC, EDR). Identify library-wide conventions, test-to-code ratios, shared utilities, and quality standards that define the expected testing approach for any new OGC API implementation.

**Why 2nd:** After understanding EDR (Section 1) - the newest and closest match to CSAPI - we need to validate those patterns are consistent across the entire library. This identifies:

- **Library-wide conventions** that all implementations follow
- **Mature patterns** from older implementations (WFS, WMS, WMTS)
- **Evolution** of testing practices over time
- **Shared infrastructure** we should leverage
- **Gaps** where EDR differs from established patterns

---

## 2. Research Questions

### Core Questions

1. What testing patterns are consistent (universal) across all ogc-client implementations?
2. What are the library-wide conventions that CSAPI must follow?
3. How have testing practices evolved from oldest to newest implementations?
4. What shared test infrastructure exists that CSAPI should leverage?
5. What test-to-code ratios and coverage targets are standard?
6. Do EDR patterns (from Section 1) align with library-wide standards?

### Detailed Questions

### Detailed Questions

**Implementation Inventory:**

1. What implementations exist in camptocamp/ogc-client?
2. When was each implementation added (chronological order)?
3. What's the maturity level of each (lines of code, features)?
4. Which implementations have the most comprehensive tests?

**Test File Consistency:** 5. What test file naming conventions are consistent across implementations? 6. Where are test files located (always colocated? always separate?)? 7. What's the standard test file structure template? 8. Are there variations in organization? Why?

**Coverage Consistency:** 9. What's the coverage % for each implementation? 10. Is there a consistent coverage target? 11. Which implementations exceed/fall short of targets? 12. How does coverage vary by component type (QueryBuilder vs parsers vs types)?

**Test Structure Patterns:** 13. Are describe/it block patterns consistent? 14. Do all implementations use the same test framework (Jest)? 15. Are there consistent setup/teardown patterns? 16. How are tests grouped (by file? by describe block?)?

**Assertion Patterns:** 17. What assertion patterns are used consistently across implementations? 18. Are URL validation patterns consistent? 19. Are query parameter validation patterns consistent? 20. Are error assertion patterns consistent? 21. What assertion depth is standard?

**Fixture Organization:** 22. How are fixtures organized in each implementation? 23. Is there a standard fixture directory structure? 24. Are fixtures real spec examples or synthetic mocks (consistent approach)? 25. How are fixtures named? 26. Are fixtures shared across implementations?

**Test Utility Patterns:** 27. What shared test utilities exist? 28. What test helpers are implementation-specific? 29. Are there mock creation utilities? 30. Are there fixture loading utilities? 31. What assertion helpers exist?

**Test-to-Code Ratios:** 32. What's the test-to-code ratio for each implementation? 33. Is there a consistent ratio across implementations? 34. How does ratio correlate with implementation complexity? 35. What's considered "good" coverage ratio?

**Type System Testing:** 36. How are TypeScript types tested across implementations? 37. Are type tests consistent? 38. What's the standard approach for interface testing? 39. Are generic types tested? How?

**Integration Test Patterns:** 40. What qualifies as "integration" test across implementations? 41. Are integration tests consistently structured? 42. What integration scenarios are common? 43. Is there a standard integration test file?

**Error Handling Patterns:** 44. How are errors tested across implementations? 45. What error types are consistently tested? 46. Are error messages validated consistently? 47. What error assertion patterns are standard?

**Conformance Testing:** 48. How is conformance detection tested in each implementation? 49. Are conformance tests consistent? 50. What conformance scenarios are tested?

**Format Handling:** 51. How are format parsers tested across implementations? 52. Are format tests consistent in structure? 53. What format validation depth is standard?

**QueryBuilder/Navigator Testing:** 54. How are QueryBuilder classes tested consistently? 55. What method testing patterns are universal? 56. Are parameter testing approaches consistent?

**Documentation Standards:** 57. What test documentation exists across implementations? 58. Are tests documented with JSDoc consistently? 59. How is test intent communicated?

**Evolution Analysis:** 60. How have testing patterns evolved from oldest to newest implementations? 61. What patterns were deprecated? 62. What new patterns emerged with EDR? 63. What should CSAPI adopt vs avoid?

---

## 3. Primary Resources

- **camptocamp/ogc-client repository:** Local clone required for comprehensive analysis
- All existing test files in implementations:
  - `src/wfs/*.spec.ts` or similar
  - `src/wms/*.spec.ts` or similar
  - `src/wmts/*.spec.ts` or similar
  - `src/ogc-api/stac/*.spec.ts` or similar
  - `src/ogc-api/edr/*.spec.ts` or similar

## 4. Supporting Resources

- **Section 1 Deliverable:** EDR Test Blueprint (for comparison and validation)
- **Architecture Patterns Analysis:** [docs/research/upstream/architecture-patterns-analysis.md](../../upstream/architecture-patterns-analysis.md)
- **File Organization Strategy:** [docs/research/upstream/file-organization-analysis.md](../../upstream/file-organization-analysis.md)
- Git history for implementation dates and evolution
- Coverage reports (if available in repository)

---

## 5. Research Methodology

## 5. Research Methodology

### Phase 1: Implementation Identification and Inventory (15 minutes)

**Objective:** Create complete inventory of ogc-client implementations with metadata

**Tasks:**

1. Survey camptocamp/ogc-client repository structure
2. List all OGC API implementations with test files
3. Use git history to identify implementation dates (git log for each implementation)
4. Categorize by maturity (lines of code, feature count, test coverage %)
5. Create implementation inventory table

### Phase 2: Per-Implementation Analysis (1.5-2 hours)

**Objective:** Detailed analysis of test patterns for each implementation

**Tasks:**
For each implementation (WFS, WMS, WMTS, STAC, EDR):

1. Locate all test files and count
2. Count test file lines and test case count
3. Measure coverage % (use coverage tools if available)
4. Document test structure patterns (describe/it conventions)
5. Extract fixture patterns and organization
6. Identify test utilities used (shared vs implementation-specific)
7. Calculate test-to-code ratio
8. Extract 2-3 representative test pattern examples
9. Document any unique patterns or deviations

### Phase 3: Consistency Matrix Creation (30-45 minutes)

**Objective:** Create comprehensive consistency comparison matrix

**Tasks:**

1. Create comparison matrix table across all implementations
2. Identify universal patterns (present in 100% of implementations)
3. Identify standard patterns (present in 80%+ implementations)
4. Identify emerging patterns (present in 40-60% implementations)
5. Identify outlier patterns (unique to one implementation)
6. Document pattern evolution timeline (oldest to newest)
7. Calculate consistency percentages for each pattern
8. Categorize recommendations (MUST, SHOULD, CONSIDER, AVOID)

### Phase 4: Synthesis and Documentation (30 minutes)

**Objective:** Create comprehensive deliverable document

**Tasks:**

1. Synthesize findings into consistency matrix document
2. Document universal patterns CSAPI MUST follow
3. Document standard patterns CSAPI SHOULD follow
4. Document emerging patterns CSAPI should CONSIDER
5. Document deprecated patterns CSAPI should AVOID
6. Create actionable recommendations for CSAPI
7. Compare findings with Section 1 EDR blueprint
8. Identify any EDR deviations from library standards

---

## 6. Success Criteria

This research is complete when:

- [ ] All implementations surveyed with quantifiable metrics (test file count, line count, coverage %)
- [ ] Complete consistency matrix created with % ratings for each pattern
- [ ] Universal patterns identified (100% consistency - MUST follow)
- [ ] Standard patterns identified (80%+ consistency - SHOULD follow)
- [ ] Emerging patterns identified (40-60% consistency - CONSIDER)
- [ ] Clear, actionable recommendations for CSAPI documented
- [ ] Pattern evolution timeline documented (oldest to newest)
- [ ] Test-to-code ratio benchmarks established
- [ ] Section 1 EDR patterns validated or contradicted against library standards
- [ ] All 64 research questions answered with specific findings

---

## 7. Deliverable

**Upstream Test Pattern Consistency Matrix document**

**Location:** `docs/research/testing/findings/02-upstream-test-consistency.md`

Content includes:

1. **Executive Summary**

   - Implementations surveyed (count, names, dates added)
   - Key consistency findings
   - Universal patterns identified
   - Variations and evolution observed
   - High-level recommendations for CSAPI

2. **Implementation Inventory**

   - Complete list with metadata (name, date added, maturity)
   - Lines of code per implementation
   - Test file count per implementation
   - Test coverage % summary
   - Implementation timeline (chronological order)

3. **Consistency Matrix**
   - Pattern-by-pattern comparison table
   - Universal patterns (100% consistency) - MUST follow
   - Standard patterns (80%+ consistency) - SHOULD follow
   - Emerging patterns (40-60% consistency) - CONSIDER
   - Outlier patterns (unique to one) - Document rationale
   - Consistency percentage for each pattern

**Matrix Format Example:**

```markdown
| Pattern                   | WFS | WMS | WMTS | STAC | EDR | Consistency | Recommendation |
| ------------------------- | --- | --- | ---- | ---- | --- | ----------- | -------------- |
| Colocated test files      | ✅  | ✅  | ✅   | ✅   | ✅  | 100%        | MUST           |
| Jest framework            | ✅  | ✅  | ✅   | ✅   | ✅  | 100%        | MUST           |
| >80% coverage             | ✅  | ⚠️  | ✅   | ✅   | ✅  | 80%         | SHOULD         |
| URL parseUrl() validation | ❌  | ❌  | ✅   | ✅   | ✅  | 60%         | CONSIDER       |
```

4. **Test File Organization**

   - Naming conventions (consistent patterns vs variations)
   - Location patterns (colocated vs separate test/)
   - Structure patterns (file organization strategies)
   - Recommendations for CSAPI

5. **Coverage Analysis**

   - Coverage % per implementation (table)
   - Coverage targets identified from patterns
   - Coverage consistency assessment
   - Coverage by component type (QueryBuilder, parsers, types)
   - Recommended coverage targets for CSAPI

6. **Test Structure Standards**

   - Describe/it block patterns (consistent conventions)
   - Setup/teardown patterns (beforeEach, afterEach usage)
   - Test naming conventions
   - Test grouping strategies
   - Nesting depth patterns
   - Recommended structure template for CSAPI

7. **Assertion Standards**

   - URL validation patterns (consistent approaches)
   - Query parameter validation patterns
   - Error assertion patterns
   - Assertion depth standards (meaningful vs trivial)
   - Matcher usage patterns (toBe, toEqual, toMatchObject)
   - Recommended assertion approaches for CSAPI

8. **Fixture Standards**

   - Fixture organization patterns (directory structure)
   - Fixture naming patterns
   - Fixture quality standards (real spec examples vs synthetic mocks)
   - Fixture sharing patterns across implementations
   - Fixture variations (minimal, typical, maximal, edge cases)
   - Recommended fixture approach for CSAPI

9. **Test Utility Analysis**

   - Shared utilities inventory (library-wide utilities)
   - Implementation-specific utilities
   - Common utility patterns
   - Mock creation utilities
   - Fixture loading utilities
   - Assertion helpers
   - Recommended utilities for CSAPI to leverage or create

10. **Test-to-Code Ratios**

    - Test-to-code ratio per implementation (table)
    - Average ratio across all implementations
    - Ratio by component type (QueryBuilder vs parsers vs types)
    - Ratio correlation with implementation complexity
    - Recommended ratio range for CSAPI

11. **Pattern Evolution Timeline**

    - Chronological evolution of testing practices
    - Patterns from oldest implementations (WFS, WMS, WMTS)
    - New patterns in newer implementations (STAC, EDR)
    - Deprecated patterns no longer used
    - Emerging patterns in recent implementations
    - Lessons learned from evolution
    - What CSAPI should adopt based on evolution

12. **CSAPI Recommendations**
    - **MUST Follow:** Universal patterns (100% consistency)
    - **SHOULD Follow:** Standard patterns (80%+ consistency)
    - **CONSIDER:** Emerging patterns (40-60% consistency)
    - **AVOID:** Deprecated patterns or anti-patterns
    - CSAPI-specific adaptations needed for unique complexity
    - Validation of Section 1 EDR patterns against library standards
    - Deviations between EDR and other implementations explained

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 1: Upstream Blueprint Analysis (PR #114) - provides EDR baseline to validate against

**Blocks:**

- Section 4: Implementation Guide requirements validation (uses consistency findings)
- Section 12: QueryBuilder testing strategy (follows consistent patterns)
- Section 19: Test organization and file structure (uses naming conventions)
- Section 34: Test utility design (leverages shared utilities)
- All subsequent testing sections (guided by universal patterns)

---

## 9. Research Status Checklist

- [x] Phase 1: Implementation Identification and Inventory (15 min) - Complete
- [x] Phase 2: Per-Implementation Analysis (1.5-2 hrs) - Complete
- [x] Phase 3: Consistency Matrix Creation (30-45 min) - Complete
- [x] Phase 4: Synthesis and Documentation (30 min) - Complete
- [x] Deliverable document created and reviewed
- [x] Cross-references updated in related documents
- [x] Section 1 EDR patterns validated against consistency matrix

**Actual Time Taken:**

- Phase 1: 20 minutes
- Phase 2: 1 hour 10 minutes
- Phase 3: 35 minutes
- Phase 4: 25 minutes
- **Total: 2.5 hours** (within 2-3 hour estimate)

---

## 10. Notes and Open Questions

**Final Research Findings:**

**1. Universal Patterns Identified (100% consistency):**

- Jest framework with .spec.ts colocated files
- describe/it/beforeEach structure
- Mock fetch with fixtures in fixtures/<protocol>/
- Real spec examples as fixtures
- Standard matchers (toBe, toEqual, toMatchObject, toContain, resolves/rejects)
- Integration and error handling tests

**2. Emerging Patterns from Newer Implementations:**

- Async fixture loading with fs/promises (STAC, EDR, OGC-API)
- jest.fn() mocks instead of globalThis factories
- afterEach with jest.runAllTimersAsync()
- Jest fake timers for async control
- URL parsing validation with new URL()
- Type-safe parameter interfaces (EDR innovation)

**3. Test-to-Code Ratio Standards:**

- Mature implementations: 1.0-2.4× (average 1.44×)
- EDR at 0.53× is below average (new implementation, tests still being added)
- CSAPI should target 1.2-1.6× from the start (~1,400-1,800 test lines)

**4. EDR Patterns Validated:**

- ✅ EDR patterns align with library standards
- ✅ EDR innovations (model.spec.ts, helpers.spec.ts, type-safe params) are good patterns for CSAPI
- ✅ EDR's lower test ratio explained (new implementation, will mature to 1.0-2.0×)

**5. Pattern Evolution Timeline:**

- **2022-2023:** XML fixtures, sync loading, basic patterns (WFS, WMS)
- **2024:** Refinement, mix of XML/JSON (WMTS, TMS)
- **2025:** Modern async patterns, JSON-only for OGC APIs (STAC, EDR)

**Deliverable Created:**

- `docs/research/testing/findings/02-upstream-test-consistency.md` (1,595 lines)
- Comprehensive consistency matrix with 12 sections
- All 63 research questions answered
- Clear MUST/SHOULD/CONSIDER/AVOID recommendations for CSAPI

**Sections Unblocked:**

- Section 4: Implementation Guide requirements validation
- Section 12: QueryBuilder testing strategy
- Section 19: Test organization and file structure
- Section 34: Test utility design
- All subsequent testing sections

**Key Insights:**

- Library has strong, consistent testing conventions
- Newer implementations show clear evolution toward better patterns
- EDR serves as good CSAPI baseline with validated patterns
- CSAPI should adopt emerging patterns, not legacy patterns
- Test coverage should start at 1.2-1.6×, not grow into it

**Initial Observations:**

- Survey covered 6 implementations (WFS, WMS, WMTS, TMS, STAC, EDR) spanning 3 years
- Older implementations (WFS, WMS) established foundation patterns
- Recent implementations (STAC, EDR) reflect current best practices
- Clear evolution trajectory identified from legacy to modern patterns

**Risks and Mitigation:**

**Risk:** Older implementations (WFS, WMS) may have outdated test patterns  
**Mitigation:** ✅ Weighted recent implementations more heavily; documented evolution trajectory; identified deprecated patterns to avoid

**Risk:** Different implementations may have different complexity requiring different patterns  
**Mitigation:** ✅ Normalized comparisons by component type; identified complexity-driven variations (parsers 1.5-4.5×, endpoints 0.7-2.1×)

**Risk:** Coverage metrics may not be consistently available across all implementations  
**Mitigation:** ✅ Used line counts and test case counts; calculated ratios retrospectively; identified patterns clearly

**Risk:** Time-consuming to analyze 5+ implementations deeply  
**Mitigation:** ✅ Focused on pattern presence/absence with quantitative metrics; sampled representative tests from oldest (WFS), middle (WMTS), newest (STAC, EDR) for depth

**Validation Against Section 1:**

- ✅ Section 1 EDR patterns align with library standards
- ✅ EDR innovations validated as good patterns for CSAPI
- ✅ EDR's lower test ratio explained (new, will mature)
- ✅ All EDR recommendations confirmed by consistency analysis
- This section validates EDR patterns are consistent with library standards
- Any EDR deviations from library patterns should be documented and explained
- If EDR introduces new patterns not in older implementations, document as emerging patterns

**Next Steps After Completion:**

1. Compare consistency matrix findings with Section 1 EDR blueprint
2. Validate universal patterns are present in EDR
3. Identify and explain any EDR deviations from standard patterns
4. Use consistency matrix to guide all subsequent test design decisions
5. Update Section 3 research with library-specific context

---

**Actual Research Time:** _[To be filled during research execution]_  
**Started:** _[Date when research begins]_  
**Completed:** _[Date when deliverable is finished]_
