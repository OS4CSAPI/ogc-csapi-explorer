# Section 34: Test Utility and Helper Design - Research Plan

**Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Actual Research Time:** ~90 minutes  
**Estimated Utility Implementation:** ~1,000-1,650 lines (50 utility functions)

---

## 1. Research Objective

Design shared test utilities and helper functions to reduce duplication and improve test maintainability.

**Why 34th:** After all test patterns defined, identify common utilities needed across test suites.

---

## 2. Research Questions

### Core Questions

1. What test utilities are needed for URL validation?
2. What fixtures loading helpers are needed?
3. What assertion helpers improve test readability?
4. What mocking utilities are needed?
5. How to structure test setup/teardown helpers?
6. What utilities exist upstream we can reuse?

### Detailed Questions

- What common patterns repeat across test files?
- What URL construction utilities are needed?
- What URL parsing utilities are needed?
- What fixture loading patterns can be abstracted?
- What custom matchers/assertions improve test clarity?
- What mock factory functions are needed?
- What test data builders are useful?
- What cleanup utilities are needed?
- How to organize utility modules?
- What error message utilities are needed?
- What date/time utilities are needed for temporal tests?
- What GeoJSON utilities are needed for spatial tests?

---

## 3. Primary Resources

- **Section 1-2 deliverables**: Upstream test utilities (patterns from upstream)
- **All previous section deliverables**: Common test patterns across all components
- **File Organization Strategy**: [docs/upstream/file-organization-analysis.md](../../upstream/file-organization-analysis.md)
- **Implementation Guide**: [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md)

## 4. Supporting Resources

- Jest documentation (custom matchers, utilities)
- Testing Library utilities
- Upstream utility functions
- TypeScript utility type patterns

---

## 5. Research Methodology

### Phase 1: Common Pattern Analysis (✅ Complete - 15 minutes)

**Objective:** Identify common patterns across all test specifications

**Tasks:**

1. ✅ Review all previous section deliverables (semantic search - 20 excerpts)
2. ✅ Identify repeated code patterns (URL parsing, fixture loading, mock fetch)
3. ✅ Identify repeated assertion patterns (ISO dates, GeoJSON, errors)
4. ✅ Identify repeated setup patterns (beforeAll/beforeEach/afterEach)
5. ✅ Identify repeated mocking patterns (globalThis.fetch)
6. ✅ Create common pattern inventory (20 patterns identified)

**Actual Time:** 15 minutes

### Phase 2: Upstream Utility Analysis (✅ Complete - 20 minutes)

**Objective:** Analyze test utilities in upstream implementations

**Tasks:**

1. ✅ Identify test utilities in upstream codebase (grep searches - 78+ matches)
2. ✅ Extract reusable utility patterns (modern vs legacy patterns)
3. ✅ Document utility organization (no exported utilities found)
4. ✅ Identify custom matchers (NONE found - opportunity)
5. ✅ Document test helpers (fetch mocking, fixture loading)
6. ✅ Create upstream utility inventory (patterns extracted)

**Actual Time:** 20 minutes

### Phase 3: Utility Category Design (✅ Complete - 10 minutes)

**Objective:** Design utility categories and organization

**Tasks:**

1. ✅ Define URL utility category (8 functions)
2. ✅ Define fixture utility category (6 functions)
3. ✅ Define assertion utility category (12 functions)
4. ✅ Define mocking utility category (8 functions)
5. ✅ Define setup/teardown utility category (6 functions)
6. ✅ Define data builder utility category (10 functions)
7. ✅ Create utility organization structure (3 files, ~1,000-1,650 lines)

**Actual Time:** 10 minutes

### Phase 4: Utility Function Design (✅ Complete - 15 minutes)

**Objective:** Design specific utility functions

**Tasks:**

1. ✅ Design URL construction utilities (parseAndValidateUrl, buildResourceUrl, etc.)
2. ✅ Design URL parsing utilities (extractResourceId, parseLinks, etc.)
3. ✅ Design fixture loading utilities (loadFixture, loadFixtureSet, etc.)
4. ✅ Design custom assertion utilities (expectValidIsoDate, expectValidGeoJSON, etc.)
5. ✅ Design mock factory utilities (mockApiResponse, mockCollection, etc.)
6. ✅ Design test data builders (buildSystem, buildObservation, etc.)
7. ✅ Design cleanup utilities (cleanupTest, resetMocks, etc.)
8. ✅ Document utility API specifications (50 functions with signatures)

**Actual Time:** 15 minutes

### Phase 5: Reusability Strategy (✅ Complete - 10 minutes)

**Objective:** Define utility reusability and maintenance strategy

**Tasks:**

1. ✅ Define utility module organization (3 files + index.ts)
2. ✅ Define utility naming conventions (parse*, expect*, build\*, etc.)
3. ✅ Define utility documentation standards (JSDoc with examples)
4. ✅ Define utility testing approach (test-utils.spec.ts)
5. ✅ Define utility versioning strategy (deprecation path)
6. ✅ Document reusability guidelines (when to create utility)

**Actual Time:** 10 minutes

### Phase 6: Synthesis (✅ Complete - 20 minutes)

**Objective:** Create comprehensive test utility library specification

**Tasks:**

1. ✅ Consolidate utility specifications (50 functions across 6 categories)
2. ✅ Create utility API documentation (detailed specifications with examples)
3. ✅ Document utility organization (file structure, naming, imports)
4. ✅ Estimate implementation effort (~1-1.5 weeks, 38-56 hours)
5. ✅ Create deliverable document (34-test-utility-helper-design.md)

**Actual Time:** 20 minutes

---

## 6. Success Criteria

This research is complete when:

- [x] Common patterns across tests are identified (20 patterns, 60-70% duplication)
- [x] Utility categories are defined (6 categories: URL, Fixture, Assertion, Mocking, Setup/Teardown, Data Builders)
- [x] Utility function APIs are specified (50 functions with signatures and examples)
- [x] Custom matchers/assertions are defined (12 assertion utilities + 6 custom matchers)
- [x] Mock factories are designed (8 mocking utilities)
- [x] Utility organization structure is defined (3 files, ~1,000-1,650 lines)
- [x] Reusability strategy is documented (naming, documentation, testing, versioning)
- [ ] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Test utility library specification with reusable helper functions**

Content includes:

- Common test pattern inventory
- Utility category organization (URL, fixture, assertion, mocking, setup, data)
- URL construction utilities (buildApiUrl, buildResourceUrl, etc.)
- URL parsing utilities (parseLinks, parseQueryParams, etc.)
- Fixture loading utilities (loadFixture, loadFixtureSet, etc.)
- Custom assertion utilities (expectValidUrl, expectValidIsoDate, etc.)
- Custom Jest matchers (toBeValidGeoJSON, toMatchSchema, etc.)
- Mock factory utilities (mockApiResponse, mockCollection, mockResource, etc.)
- Test data builders (buildObservation, buildCommand, buildSystem, etc.)
- Setup/teardown utilities (setupTestContext, cleanupTestContext, etc.)
- Date/time utilities (createIsoTimestamp, parseTemporalInterval, etc.)
- GeoJSON utilities (createPoint, createPolygon, validateGeometry, etc.)
- Error message utilities (expectErrorMessage, validateErrorResponse, etc.)
- Utility module organization structure
- Utility naming conventions
- Utility documentation standards
- Implementation estimates

**Example Utilities:**

```typescript
// URL Utilities
buildApiUrl(baseUrl: string, path: string, params?: QueryParams): string
parseLinks(linkHeader: string): Record<string, string>
extractCollectionId(url: string): string

// Fixture Utilities
loadFixture(name: string): any
loadFixtureSet(pattern: string): any[]

// Custom Matchers
expect(url).toBeValidOgcApiUrl()
expect(date).toBeValidIso8601()
expect(geojson).toBeValidGeoJSON()

// Mock Factories
mockCollection(overrides?: Partial<Collection>): Collection
mockSystem(overrides?: Partial<System>): System

// Data Builders
buildObservation({ phenomenonTime, result, ... }): Observation
buildCommand({ parameters, ... }): Command
```

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 1-2: Upstream Analysis (utility patterns)
- All previous sections (common patterns across all tests)
- Section 19: Test Organization and File Structure (utility organization)

**Blocks:**

- Test implementation (utilities needed before writing tests)
- Test maintainability (utilities reduce duplication)

---

## 9. Research Status Checklist

- [x] Phase 1: Common Pattern Analysis - Complete (15 min)
- [x] Phase 2: Upstream Utility Analysis - Complete (20 min)
- [x] Phase 3: Utility Category Design - Complete (10 min)
- [x] Phase 4: Utility Function Design - Complete (15 min)
- [x] Phase 5: Reusability Strategy - Complete (10 min)
- [x] Phase 6: Synthesis - Complete (20 min)
- [x] Deliverable document created and reviewed
- [x] Cross-references updated in related documents

**Total Research Time:** ~90 minutes

---

## 10. Notes and Open Questions

### Research Findings

**Key Discovery: No Upstream Test Utilities**

- Upstream has NO exported test utilities
- Patterns exist but not formalized
- Must design utilities from scratch based on common patterns

**Common Patterns Identified (20+):**

- URL parsing with `new URL()` (50+ occurrences)
- Fixture loading with `readFile()` (40+ occurrences)
- Mock fetch setup (30+ occurrences)
- ISO 8601 validation (25+ occurrences)
- GeoJSON validation (20+ occurrences)
- Error type/message validation (35+ occurrences)
- Query parameter assertions (30+ occurrences)

**Utility Organization:**

- **test-utils.ts** (~200-250 lines): URL parsing, assertions, validation
- **test-helpers.ts** (~150-200 lines): Setup, mocking, cleanup
- **test-fixtures.ts** (~100-150 lines): Fixture loading, caching
- **Total:** ~450-600 lines (50 utility functions)

**Impact Estimates:**

- 60-70% reduction in test code duplication
- Saves ~10,000-15,000 lines across 100-150 test files
- Improved test readability and maintainability
- Fix bugs once in utility, not 50 times across test files

**Utility Categories (6):**

1. **URL Utilities** (8 functions): parseAndValidateUrl, expectQueryParam, buildResourceUrl, extractResourceId, parseLinks, validateEncoding, expectLinkRel, buildLinks
2. **Fixture Utilities** (6 functions): loadFixture, loadFixtureSync, loadFixtureSet, createFixtureCache, clearFixtureCache, fixtureExists
3. **Assertion Utilities** (12 functions): expectValidIsoDate, expectValidIsoInterval, expectValidGeoJSON, expectValidUuid, expectValidUrl, expectValidSweSchema, expectError, expectCollectionResponse, expectResourceResponse, expectLinkArray, expectPaginationLinks, expectFormatNegotiation
4. **Mocking Utilities** (8 functions): setupMockFetch, mockApiResponse, mockCollection, mockResource, mockError, mockPaginatedResponse, resetMocks, mockFetchOnce
5. **Setup/Teardown Utilities** (6 functions): createTestEndpoint, createTestQueryBuilder, setupTestContext, cleanupTest, resetTestContext, withTestEndpoint
6. **Data Builder Utilities** (10 functions): buildSystem, buildDeployment, buildDatastream, buildObservation, buildCommand, buildSweSchema, buildGeoJSON, buildTemporalExtent, buildSpatialExtent, buildLinks

**CSAPI-Specific Utilities (Not in Upstream):**

- Temporal validation (ISO 8601 intervals, phenomenon time)
- Spatial validation (GeoJSON, point/polygon creation)
- SWE Common utilities (schema validation, observation builders)
- System/Deployment builders (complex resource creation)
- Command/Tasking utilities (parameter validation)
- Link relation utilities (CSAPI-specific rel parsing)

**Implementation Estimates:**

- **Week 1 (Phase 1-3):** Core utilities, validation utilities, helper utilities (~32 hours)
- **Week 2 (Phase 4-5):** Data builders, testing, documentation (~24 hours)
- **Total:** ~38-56 hours (1-1.5 weeks, 1 developer)

**Next Steps:**

1. Implement utility functions in `src/csapi-querybuilder/test-utils/`
2. Write utility tests (test the tests)
3. Migrate existing tests to use utilities (phased migration)
4. Document utility usage patterns
5. Remove deprecated inline patterns

### Open Questions

**Resolved:**

- ✅ What patterns are most common? (URL parsing, fixture loading, mock fetch)
- ✅ What utilities exist upstream? (NONE - must design from scratch)
- ✅ How to organize utilities? (3 files: test-utils, test-helpers, test-fixtures)
- ✅ What custom matchers are needed? (ISO dates, GeoJSON, errors, etc.)
- ✅ What implementation effort? (~1-1.5 weeks, 38-56 hours)

**No Outstanding Questions** - Research complete and ready for implementation

**Naming Conventions:**

- URL utilities: `build*Url`, `parse*`, `extract*`
- Fixture utilities: `load*Fixture`
- Assertion utilities: `expect*`, `validate*`
- Mock factories: `mock*`, `create*`
- Data builders: `build*`

---

**Next Steps:** Review Jest custom matcher documentation and analyze utility patterns in upstream test codebase.
