# Section 19: Test Organization and File Structure

**Research Plan:** [Research Plan 19: Test Organization and File Structure](../research-plans/19-test-organization-file-structure.md)

**Research Questions:** 7 core questions about test file inventory (names and purposes), organization by component vs resource type, file location (colocated vs separate test/ directory), naming conventions consistent with upstream, describe/it block structure, test utilities and helpers organization, and fixture organization

**Methodology:** 6-phase systematic analysis (Phase 1: Upstream Test Structure Analysis of file patterns → Phase 2: Test File Inventory compilation from all component sections → Phase 3: Directory Structure Design for tests/fixtures/utilities → Phase 4: Naming Convention Definition for files and blocks → Phase 5: Test Structure Templates creation by test type → Phase 6: Synthesis into comprehensive organization specification)

**Research Time:** ~95 minutes (February 5, 2025)

**Primary Source(s):**

- [File Organization Strategy](../../upstream/file-organization-analysis.md)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Test file specifications)

**Supporting Resources:**

- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream test file patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (organization patterns across implementations)
- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (test file requirements)
- Section 9: [SensorML Testing Requirements](09-sensorml-testing-requirements.md) (test file requirements)
- Section 10: [SWE Common Testing Requirements](10-swe-common-testing-requirements.md) (test file requirements)
- Section 11: [GeoJSON CSAPI Testing Requirements](11-geojson-csapi-testing-requirements.md) (test file requirements)
- Section 12: [QueryBuilder Testing Strategy](12-querybuilder-testing-strategy.md) (test file requirements)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (test file requirements)
- Section 14: [Integration Test Workflow Design](14-integration-test-workflow-design.md) (test file requirements)
- Section 15: [Fixture Sourcing Organization](15-fixture-sourcing-organization.md) (fixture structure integration)
- Section 16: [Worker Extensions Testing](16-worker-extensions-testing.md) (test file requirements)
- Section 17: [Coverage Targets and Metrics](17-coverage-targets-and-metrics.md) (test file requirements)
- Section 18: [Error Condition Testing Strategy](18-error-condition-testing-strategy.md) (test file requirements)

**Document Purpose:** Defines complete test file structure with 22 test files in flat colocated organization, naming conventions matching upstream patterns (.spec.ts), directory structure for ~280 fixtures, test utility organization, and reusable test templates by type

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Upstream Test Organization Patterns](#2-upstream-test-organization-patterns)
3. [Test File Inventory](#3-test-file-inventory)
4. [Directory Structure Specification](#4-directory-structure-specification)
5. [File Naming Conventions](#5-file-naming-conventions)
6. [Test Structure Standards](#6-test-structure-standards)
7. [Test File Templates](#7-test-file-templates)
8. [Test Utility Organization](#8-test-utility-organization)
9. [Fixture Organization Integration](#9-fixture-organization-integration)
10. [Implementation Guidelines](#10-implementation-guidelines)
11. [Success Criteria](#11-success-criteria)

---

## 1. Executive Summary

### 1.1 Overview

This document defines the complete test organization strategy for CSAPI implementation, specifying:

- **22 test files** (plus 5-6 implementation files) organized in flat colocated structure
- **Upstream-aligned patterns** matching EDR/STAC/WFS/WMS organization
- **~4,000-5,300 lines** of test code across all test files
- **~280 fixtures** organized by test type and format
- **Clear naming conventions** for discoverability and maintainability

**Key Design Principles:**

1. **Flat structure** - No test subdirectories, following upstream pattern
2. **Colocated tests** - Test files next to implementation files
3. **Clear separation** - Unit tests, integration tests, format parsers separated
4. **Fixture reuse** - Shared fixtures across test types, minimal duplication
5. **Maintainability** - Small focused files (50-300 lines each)

### 1.2 Key Decisions

| Decision                           | Rationale                                             | Upstream Alignment                       |
| ---------------------------------- | ----------------------------------------------------- | ---------------------------------------- |
| **Flat colocated structure**       | All upstream APIs use this pattern, no subdirectories | ✅ EDR, STAC, WMS, WFS, WMTS             |
| **`.spec.ts` naming**              | Standard upstream convention                          | ✅ All upstream APIs                     |
| **Multiple test files per module** | Large modules (url_builder) split by resource type    | ⚠️ Improvement over upstream single-file |
| **Shared test utilities**          | Common helpers in separate file                       | ✅ Upstream pattern                      |
| **Fixtures by test type**          | Organized by unit/integration/parser                  | ✅ Section 15 strategy                   |

### 1.3 File Count Summary

| Category                | File Count     | Lines (Est.)     | Purpose                                               |
| ----------------------- | -------------- | ---------------- | ----------------------------------------------------- |
| **Implementation**      | 5-6 files      | ~2,100-2,600     | Model, URL builder, helpers, index                    |
| **Unit Tests**          | 15 files       | ~1,900-2,400     | Model, helpers, URL builder (9 resources)             |
| **Integration Tests**   | 4 files        | ~900-1,200       | Discovery, observation, command, navigation workflows |
| **Format Parser Tests** | 3 files        | ~1,000-1,300     | SensorML, SWE Common, GeoJSON parsers                 |
| **Test Utilities**      | 3 files        | ~300-400         | Shared helpers, fixtures, mocks                       |
| **Fixtures**            | ~280 files     | N/A (data)       | JSON, CSV, binary test data                           |
| **Test files subtotal** | **22 files**   | **~4,100-5,300** | Unit + integration + parser + utility tests           |
| **All files total**     | **~308 files** | -                | Including implementation (5-6) + fixtures (~280)      |

---

## 2. Upstream Test Organization Patterns

### 2.1 File Organization Philosophy

**Upstream Pattern Analysis (EDR/STAC/WMS/WFS):**

**Common Patterns Across All APIs:**

1. **Flat structure** - No subdirectories within API folders
2. **Colocated tests** - Test files next to implementation (`.spec.ts` naming)
3. **Separate concerns** - Different files for parsing, models, endpoints
4. **Barrel files optional** - Only STAC has `index.ts`, others export directly
5. **Default exports for classes** - Named exports for utilities

**EDR Structure Example** (Baseline for CSAPI):

```
src/ogc-api/edr/
  model.ts              (126 lines) - Type definitions
  url_builder.ts        (380 lines) - EDRQueryBuilder class
  helpers.ts            (26 lines) - Utility functions
  model.spec.ts         (97 lines) - Model tests
  helpers.spec.ts       (45 lines) - Helper tests
```

**Test File Characteristics:**

- **Naming**: `{filename}.spec.ts` pattern
- **Location**: Same directory as implementation
- **Structure**: One `describe` block per function/class
- **Coverage**: 77-173% test-to-code ratios (EDR)

### 2.2 Test Organization Standards

**describe/it Block Structure** (from Section 1):

```typescript
describe('FunctionName or ClassName', () => {
  // Setup
  let variable: Type;

  beforeEach(() => {
    // Initialize test state
  });

  // Test cases grouped by scenario
  it('handles valid input', () => {
    expect(result).toBe(expected);
  });

  it('handles edge case', () => {
    expect(result).toThrow(/error message/);
  });
});
```

**Patterns Observed:**

- One top-level `describe` per exported function/class
- Nested `describe` blocks for method groupings
- Clear test case names describing behavior
- Imports from relative paths (`./helpers.js`)

### 2.3 Fixture Organization

**Upstream Fixture Pattern** (from file-organization-analysis.md):

```
fixtures/
  ogc-api/
    sample-data.json           # Root documents
    edr/
      sample-data-hub.json     # EDR-specific
    sample-data/               # Collection subdirectory
      collections.json
      conformance.json
```

**CSAPI Fixture Strategy** (from Section 15):

```
fixtures/
  csapi-querybuilder/          # QueryBuilder test fixtures (23)
    universal/                 # Shared across all resources (5)
    resources/                 # Per-resource responses (18)
  geojson-csapi/               # GeoJSON parser fixtures (~20)
  sensorml/                    # SensorML parser fixtures (~25)
  swe-common/                  # SWE Common parser fixtures (~120)
  integration/                 # Integration workflow fixtures (33)
  errors/                      # Error and edge cases (~30)
```

### 2.4 Deviations from Upstream

**CSAPI-Specific Improvements:**

1. **Multiple Test Files for Large Modules**

   - **Upstream**: EDR has no url_builder.spec.ts (would be 800+ lines)
   - **CSAPI**: Split url_builder tests into 9 files (one per resource type)
   - **Benefit**: Maintainability, parallel test execution, easier code review

2. **Explicit Resource Availability Testing**

   - **Upstream**: Resource availability implicit in endpoint usage
   - **CSAPI**: Explicit tests for conformance checking
   - **Benefit**: Ensures methods fail gracefully when resources unavailable

3. **Integration Test Organization**
   - **Upstream**: Integration tests not systematically organized
   - **CSAPI**: Dedicated integration test files for workflows
   - **Benefit**: Clear separation of unit vs integration tests

**No Conflicts**: All upstream patterns preserved, only enhancements added

---

## 3. Test File Inventory

### 3.1 Implementation Files (5-6 files)

| File                 | Lines    | Purpose                               | Exports        |
| -------------------- | -------- | ------------------------------------- | -------------- |
| `model.ts`           | ~350-400 | Type definitions, enums, interfaces   | Named exports  |
| `url_builder.ts`     | ~700-800 | CSAPIQueryBuilder class (~80 methods) | Default export |
| `helpers.ts`         | ~50-80   | Utility functions                     | Named exports  |
| `index.ts`           | ~10      | Barrel file (optional)                | Re-exports     |
| _(parser files TBD)_ | ~500-800 | SensorML/SWE/GeoJSON parsers          | Named exports  |

**Total Implementation:** ~1,610-2,090 lines (excluding parsers)

### 3.2 Unit Test Files (15 files)

#### Core Unit Tests (3 files)

| File                       | Lines    | Tests  | Purpose                                         |
| -------------------------- | -------- | ------ | ----------------------------------------------- |
| `model.spec.ts`            | ~200-300 | ~30-40 | Type helpers, enums, validation functions       |
| `helpers.spec.ts`          | ~100-150 | ~15-20 | Utility function tests                          |
| `url_builder-base.spec.ts` | ~150-200 | ~20-25 | Base URL builder setup, availability validation |

#### URL Builder Resource Tests (9 files, one per resource)

| File                                   | Lines    | Tests | Purpose                                       |
| -------------------------------------- | -------- | ----- | --------------------------------------------- |
| `url_builder-systems.spec.ts`          | ~200-250 | ~32   | Systems resource methods (12 methods)         |
| `url_builder-deployments.spec.ts`      | ~150-180 | ~21   | Deployments resource methods (8 methods)      |
| `url_builder-procedures.spec.ts`       | ~120-150 | ~17   | Procedures resource methods (8 methods)       |
| `url_builder-samplingfeatures.spec.ts` | ~140-170 | ~19   | SamplingFeatures resource methods (8 methods) |
| `url_builder-properties.spec.ts`       | ~100-130 | ~14   | Properties resource methods (6 methods)       |
| `url_builder-datastreams.spec.ts`      | ~200-240 | ~28   | DataStreams resource methods (11 methods)     |
| `url_builder-observations.spec.ts`     | ~160-190 | ~22   | Observations resource methods (9 methods)     |
| `url_builder-controlstreams.spec.ts`   | ~150-180 | ~21   | ControlStreams resource methods (8 methods)   |
| `url_builder-commands.spec.ts`         | ~170-200 | ~24   | Commands resource methods (10 methods)        |

**Unit Test Subtotal:** ~1,840-2,440 lines, ~243-275 tests

#### Format Parser Tests (3 files)

| File                           | Lines    | Tests  | Purpose                                  |
| ------------------------------ | -------- | ------ | ---------------------------------------- |
| `sensorml-parser.spec.ts`      | ~300-400 | ~35-40 | SensorML 3.0 parsing (5 system types)    |
| `swe-parser.spec.ts`           | ~400-500 | ~45-50 | SWE Common 3.0 parsing (3 encodings)     |
| `geojson-csapi-parser.spec.ts` | ~300-400 | ~30-35 | GeoJSON CSAPI parsing (5 resource types) |

**Parser Test Subtotal:** ~1,000-1,300 lines, ~110-125 tests

**Total Unit Tests:** ~2,840-3,740 lines, ~353-400 tests

### 3.3 Integration Test Files (4 files)

| File                              | Lines    | Tests  | Purpose                                                     |
| --------------------------------- | -------- | ------ | ----------------------------------------------------------- |
| `integration-discovery.spec.ts`   | ~200-250 | ~12-15 | Discovery workflow (root → systems → datastreams)           |
| `integration-observation.spec.ts` | ~250-300 | ~15-18 | Observation workflow (property → datastream → observations) |
| `integration-command.spec.ts`     | ~200-250 | ~12-15 | Command workflow (controlstream → commands → status)        |
| `integration-navigation.spec.ts`  | ~250-350 | ~15-20 | Multi-hop navigation (systems → subsystems → components)    |

**Integration Test Subtotal:** ~900-1,150 lines, ~54-68 tests

### 3.4 Test Utility Files (3 files)

| File               | Lines    | Purpose                                                        |
| ------------------ | -------- | -------------------------------------------------------------- |
| `test-utils.ts`    | ~150-200 | Shared utilities (parseAndValidateUrl, validateEncoding, etc.) |
| `test-helpers.ts`  | ~100-150 | Test setup helpers (createTestEndpoint, mockFetch, etc.)       |
| `test-fixtures.ts` | ~50-100  | Fixture loading utilities                                      |

**Test Utility Subtotal:** ~300-450 lines

### 3.5 Complete Test File Summary

| Category                | Files  | Lines            | Tests        | Coverage                      |
| ----------------------- | ------ | ---------------- | ------------ | ----------------------------- |
| **Core unit tests**     | 3      | ~450-650         | ~65-85       | Model, helpers, base          |
| **URL builder tests**   | 9      | ~1,390-1,790     | ~198-220     | 80 methods across 9 resources |
| **Format parser tests** | 3      | ~1,000-1,300     | ~110-125     | SensorML, SWE, GeoJSON        |
| **Integration tests**   | 4      | ~900-1,150       | ~54-68       | 4 workflows                   |
| **Test utilities**      | 3      | ~300-450         | N/A          | Shared helpers                |
| **TOTAL**               | **22** | **~4,040-5,340** | **~427-498** | Complete suite                |

---

## 4. Directory Structure Specification

### 4.1 CSAPI Module Structure

**Complete Directory Layout:**

```
src/ogc-api/csapi/
  # Implementation files (5-6 files, ~1,610-2,090 lines)
  model.ts                              (~350-400 lines) - Types, enums, interfaces
  url_builder.ts                        (~700-800 lines) - CSAPIQueryBuilder class
  helpers.ts                            (~50-80 lines) - Utility functions
  index.ts                              (~10 lines) - Barrel file (optional)

  # Core unit tests (3 files, ~450-650 lines)
  model.spec.ts                         (~200-300 lines) - Model/type tests
  helpers.spec.ts                       (~100-150 lines) - Helper function tests
  url_builder-base.spec.ts              (~150-200 lines) - Base QueryBuilder tests

  # URL builder resource tests (9 files, ~1,390-1,790 lines)
  url_builder-systems.spec.ts           (~200-250 lines) - Systems methods (32 tests)
  url_builder-deployments.spec.ts       (~150-180 lines) - Deployments methods (21 tests)
  url_builder-procedures.spec.ts        (~120-150 lines) - Procedures methods (17 tests)
  url_builder-samplingfeatures.spec.ts  (~140-170 lines) - SamplingFeatures methods (19 tests)
  url_builder-properties.spec.ts        (~100-130 lines) - Properties methods (14 tests)
  url_builder-datastreams.spec.ts       (~200-240 lines) - DataStreams methods (28 tests)
  url_builder-observations.spec.ts      (~160-190 lines) - Observations methods (22 tests)
  url_builder-controlstreams.spec.ts    (~150-180 lines) - ControlStreams methods (21 tests)
  url_builder-commands.spec.ts          (~170-200 lines) - Commands methods (24 tests)

  # Format parser tests (3 files, ~1,000-1,300 lines)
  sensorml-parser.spec.ts               (~300-400 lines) - SensorML parsing tests
  swe-parser.spec.ts                    (~400-500 lines) - SWE Common parsing tests
  geojson-csapi-parser.spec.ts          (~300-400 lines) - GeoJSON CSAPI parsing tests

  # Integration tests (4 files, ~900-1,150 lines)
  integration-discovery.spec.ts         (~200-250 lines) - Discovery workflow
  integration-observation.spec.ts       (~250-300 lines) - Observation workflow
  integration-command.spec.ts           (~200-250 lines) - Command workflow
  integration-navigation.spec.ts        (~250-350 lines) - Navigation workflow

  # Test utilities (3 files, ~300-450 lines)
  test-utils.ts                         (~150-200 lines) - Shared test utilities
  test-helpers.ts                       (~100-150 lines) - Test setup helpers
  test-fixtures.ts                      (~50-100 lines) - Fixture loading utilities
```

**Total Files:** 5-6 implementation + 22 test files = **27-28 files**  
**Total Lines:** ~1,610-2,090 implementation + ~4,040-5,340 test = **~5,650-7,430 lines**

### 4.2 Rationale for Flat Structure

**Why No Subdirectories:**

1. **Upstream Consistency** - All upstream APIs (EDR, STAC, WMS, WFS, WMTS) use flat structure
2. **Discoverability** - All files visible in single directory listing
3. **Simplicity** - No navigation overhead, clear file relationships
4. **Import Paths** - Short relative imports (`./model.ts`, not `../models/model.ts`)
5. **Scalability** - 27-28 files is manageable in single directory (upstream precedent: WMS has 12 files)

**Comparison to Alternatives:**

| Alternative                                     | Pros                                      | Cons                                     | Decision      |
| ----------------------------------------------- | ----------------------------------------- | ---------------------------------------- | ------------- |
| **Flat structure** (chosen)                     | ✅ Upstream aligned, simple, discoverable | ⚠️ Many files in one directory           | ✅ **CHOSEN** |
| **Subdirectories** (models/, builders/, tests/) | ✅ Grouped by type                        | ❌ Not upstream pattern, complex imports | ❌ Rejected   |
| **Separate test/ directory**                    | ✅ Tests isolated                         | ❌ Not colocated, not upstream pattern   | ❌ Rejected   |

### 4.3 Fixture Directory Structure

**Fixture Organization** (from Section 15):

```
fixtures/
  csapi-querybuilder/                   # QueryBuilder test fixtures (23 files)
    universal/                          # Shared across resources (5 files)
      conformance-all-resources.json
      conformance-part1-only.json
      collection-info-all-resources.json
      collection-info-part1-only.json
      collection-info-no-csapi.json
    resources/                          # Per-resource responses (18 files)
      systems/
        systems-collection-response.json
        systems-item-response.json
      deployments/
        deployments-collection-response.json
        deployments-item-response.json
      # ... (7 more resource directories)

  geojson-csapi/                        # GeoJSON parser fixtures (~20 files)
    systems/
    deployments/
    procedures/
    samplingfeatures/
    properties/

  sensorml/                             # SensorML parser fixtures (~25 files)
    physicalsystem/
    physicalcomponent/
    simpleprocess/
    aggregateprocess/

  swe-common/                           # SWE Common parser fixtures (~120 files)
    json/
    text/
    binary/

  integration/                          # Integration workflow fixtures (33 files)
    discovery/
    observation/
    command/
    navigation/

  errors/                               # Error and edge cases (~30 files)
    empty/
    invalid/
    schema-violations/
    http-errors/
```

**Total Fixtures:** ~280 files organized by test type

> **Fixture Count Cross-Reference:** This ~280 total (from Section 15) is the aggregate across all test categories. It includes the 23 resource method unit test fixtures from Section 13 (5 universal + 18 resource-specific), the 33 integration workflow fixtures from Section 14 (discovery, observation, command, navigation), plus ~224 additional fixtures for format parsing (SensorML, SWE Common, GeoJSON), worker extensions, and error/edge case scenarios.

---

## 5. File Naming Conventions

### 5.1 Test File Naming

**Pattern:** `{module}.spec.ts`

**Examples:**

- `model.spec.ts` - Tests for `model.ts`
- `helpers.spec.ts` - Tests for `helpers.ts`
- `url_builder-systems.spec.ts` - Tests for Systems methods in `url_builder.ts`

**Rationale:**

- ✅ Upstream standard (`.spec.ts` used by all APIs)
- ✅ Clear one-to-one mapping to implementation files
- ✅ Jest automatically discovers `*.spec.ts` files
- ✅ VS Code shows test files adjacent to implementation in explorer

**Alternative Rejected:** `.test.ts` suffix (not upstream standard)

### 5.2 Resource-Specific Test File Naming

**Pattern:** `url_builder-{resource}.spec.ts`

**Format:**

- Resource name: lowercase, plural form
- Hyphen separator: `url_builder-{resource}`
- File extension: `.spec.ts`

**Complete List:**

1. `url_builder-base.spec.ts` - Base QueryBuilder setup, availability
2. `url_builder-systems.spec.ts` - Systems resource methods
3. `url_builder-deployments.spec.ts` - Deployments resource methods
4. `url_builder-procedures.spec.ts` - Procedures resource methods
5. `url_builder-samplingfeatures.spec.ts` - SamplingFeatures resource methods
6. `url_builder-properties.spec.ts` - Properties resource methods
7. `url_builder-datastreams.spec.ts` - DataStreams resource methods
8. `url_builder-observations.spec.ts` - Observations resource methods
9. `url_builder-controlstreams.spec.ts` - ControlStreams resource methods
10. `url_builder-commands.spec.ts` - Commands resource methods

**Rationale:**

- ✅ Clear resource scope per file
- ✅ Searchable by resource name
- ✅ Maintainable file sizes (90-250 lines each)
- ✅ Parallel test execution per resource

### 5.3 Integration Test File Naming

**Pattern:** `integration-{workflow}.spec.ts`

**Examples:**

- `integration-discovery.spec.ts` - Discovery workflow tests
- `integration-observation.spec.ts` - Observation workflow tests
- `integration-command.spec.ts` - Command workflow tests
- `integration-navigation.spec.ts` - Navigation workflow tests

**Rationale:**

- ✅ `integration-` prefix clearly distinguishes from unit tests
- ✅ Workflow name describes test scope
- ✅ Searchable by workflow type

### 5.4 Format Parser Test File Naming

**Pattern:** `{format}-parser.spec.ts`

**Examples:**

- `sensorml-parser.spec.ts` - SensorML 3.0 parsing tests
- `swe-parser.spec.ts` - SWE Common 3.0 parsing tests
- `geojson-csapi-parser.spec.ts` - GeoJSON CSAPI parsing tests

**Rationale:**

- ✅ Clear format scope
- ✅ `-parser` suffix indicates parsing functionality
- ✅ Searchable by format name

### 5.5 Test Utility File Naming

**Pattern:** `test-{purpose}.ts` (NO `.spec.ts` suffix)

**Examples:**

- `test-utils.ts` - Shared utilities (parseAndValidateUrl, etc.)
- `test-helpers.ts` - Test setup helpers (createTestEndpoint, etc.)
- `test-fixtures.ts` - Fixture loading utilities

**Rationale:**

- ✅ `test-` prefix indicates test-related code
- ✅ NO `.spec.ts` suffix (not test files, utility files)
- ✅ Clear purpose in filename

### 5.6 Fixture File Naming

**From Section 15 Fixture Naming Conventions:**

**Pattern:** `{resource}-{variant}-{format}.{ext}`

**Examples:**

- `conformance-all-resources.json` - Conformance with all resources
- `systems-collection-response.json` - Systems collection GET response
- `physicalsystem-weather-station.json` - SensorML PhysicalSystem example
- `datarecord-temperature-json.json` - SWE DataRecord in JSON encoding
- `datarecord-temperature-text.csv` - SWE DataRecord in Text (CSV) encoding

**Special Cases:**

- **Error fixtures:** `error-{code}-{description}.json` (e.g., `error-404-resource-not-found.json`)
- **Edge cases:** `edge-{description}.json` (e.g., `edge-empty-collection-systems.json`)
- **Workflow fixtures:** `{workflow}-{step}-{description}.json` (e.g., `discovery-step1-landing-page.json`)

---

## 6. Test Structure Standards

### 6.1 describe/it Block Organization

**Standard Pattern:**

```typescript
describe('ModuleName or ClassName', () => {
  // Optional: Shared setup
  let variable: Type;

  beforeEach(() => {
    // Initialize test state before each test
  });

  describe('methodName or functionName', () => {
    it('handles typical case', () => {
      // Arrange
      const input = createInput();

      // Act
      const result = functionUnderTest(input);

      // Assert
      expect(result).toBe(expected);
    });

    it('handles edge case', () => {
      expect(() => functionUnderTest(invalidInput)).toThrow(/error message/);
    });
  });

  describe('another method', () => {
    it('test case 1', () => {
      /* ... */
    });
    it('test case 2', () => {
      /* ... */
    });
  });
});
```

**Nesting Levels:**

1. **Level 1** (top-level): Module or class name
2. **Level 2**: Method or function name
3. **Level 3** (optional): Scenario grouping (e.g., "with valid input", "with error conditions")

**Naming Conventions:**

| Level               | Convention                                    | Example                                                |
| ------------------- | --------------------------------------------- | ------------------------------------------------------ |
| **Module/Class**    | PascalCase for classes, lowercase for modules | `describe('CSAPIQueryBuilder', ...)`                   |
| **Method/Function** | camelCase, descriptive                        | `describe('getSystems', ...)`                          |
| **Test Case**       | Sentence case, starts with verb               | `it('constructs URL with pagination parameters', ...)` |

### 6.2 Test Case Naming Patterns

**Format:** `it('{verb} {behavior} {context}', () => {})`

**Good Examples:**

- ✅ `it('constructs systems collection URL without parameters', ...)`
- ✅ `it('encodes spaces as %20 in query parameter values', ...)`
- ✅ `it('throws error when resource type not available', ...)`
- ✅ `it('applies pagination parameters', ...)`

**Bad Examples:**

- ❌ `it('works', ...)` - Too vague
- ❌ `it('test getSystems', ...)` - Not descriptive
- ❌ `it('getSystems() returns correct URL', ...)` - Redundant function name

**Verb Choices by Test Type:**

| Test Type            | Common Verbs                   | Examples                                 |
| -------------------- | ------------------------------ | ---------------------------------------- |
| **URL Construction** | constructs, builds, generates  | `constructs systems URL with filters`    |
| **Validation**       | validates, checks, verifies    | `validates bbox coordinates`             |
| **Error Handling**   | throws, rejects, fails         | `throws error when resource unavailable` |
| **Parsing**          | parses, decodes, converts      | `parses SensorML PhysicalSystem`         |
| **Integration**      | navigates, discovers, executes | `navigates from system to datastreams`   |

### 6.3 Import Organization

**Standard Import Order:**

```typescript
// 1. External dependencies (Jest, test libraries)
import { describe, it, expect, beforeEach } from '@jest/globals';

// 2. Internal dependencies (implementation)
import { CSAPIQueryBuilder } from './url_builder';
import { SystemType, DeploymentType } from './model';
import { encodeBBox, encodeDateTime } from './helpers';

// 3. Test utilities
import { parseAndValidateUrl, validateEncoding } from './test-utils';
import { createTestEndpoint, mockFetch } from './test-helpers';
import { loadFixture } from './test-fixtures';

// 4. Type imports (if needed)
import type { CSAPIQueryOptions } from './model';
```

**Rationale:**

- ✅ Clear dependency categories
- ✅ Easy to spot missing imports
- ✅ Consistent across all test files

### 6.4 Test Utilities Usage Pattern

**Common Pattern:**

```typescript
describe('CSAPIQueryBuilder - Systems', () => {
  let builder: CSAPIQueryBuilder;
  let baseUrl: string;

  beforeEach(async () => {
    // Use test helper to create endpoint
    const endpoint = await createTestEndpoint();
    builder = await endpoint.csapi('test-collection');
    baseUrl = 'https://api.example.com';
  });

  it('constructs systems collection URL', async () => {
    const url = builder.getSystems();

    // Use test utility for URL validation
    parseAndValidateUrl(url, {
      protocol: 'https:',
      host: 'api.example.com',
      pathname: '/systems',
    });
  });
});
```

**Benefits:**

- ✅ Consistent setup across tests
- ✅ Reusable validation logic
- ✅ Minimal duplication

---

## 7. Test File Templates

### 7.1 Unit Test Template (Model/Helpers)

**File:** `model.spec.ts` or `helpers.spec.ts`

```typescript
import { describe, it, expect } from '@jest/globals';
import {
  // Import functions/types to test
  functionName,
  TypeName,
} from './model'; // or './helpers'

describe('ModuleName', () => {
  describe('functionName', () => {
    it('handles valid input', () => {
      // Arrange
      const input = createValidInput();

      // Act
      const result = functionName(input);

      // Assert
      expect(result).toBe(expectedValue);
    });

    it('handles edge case', () => {
      const edgeInput = createEdgeCase();
      const result = functionName(edgeInput);
      expect(result).toBeDefined();
    });

    it('throws error for invalid input', () => {
      const invalidInput = createInvalidInput();
      expect(() => functionName(invalidInput)).toThrow(/expected error/);
    });
  });

  describe('anotherFunction', () => {
    it('test case 1', () => {
      /* ... */
    });
    it('test case 2', () => {
      /* ... */
    });
  });
});
```

**Estimated Size:** 100-300 lines per file

### 7.2 URL Builder Test Template (Resource-Specific)

**File:** `url_builder-{resource}.spec.ts`

```typescript
import { describe, it, expect, beforeEach } from '@jest/globals';
import { CSAPIQueryBuilder } from './url_builder';
import { parseAndValidateUrl } from './test-utils';
import { createTestEndpoint } from './test-helpers';

describe('CSAPIQueryBuilder - ResourceName', () => {
  let builder: CSAPIQueryBuilder;
  let baseUrl: string;

  beforeEach(async () => {
    const endpoint = await createTestEndpoint();
    builder = await endpoint.csapi('test-collection');
    baseUrl = 'https://api.example.com';
  });

  describe('getResources()', () => {
    it('constructs collection URL without parameters', async () => {
      const url = builder.getResources();
      parseAndValidateUrl(url, {
        protocol: 'https:',
        pathname: '/resources',
      });
    });

    it('applies pagination parameters', async () => {
      const url = builder.getResources({ limit: 50, offset: 100 });
      parseAndValidateUrl(url, {
        pathname: '/resources',
        query: {
          limit: '50',
          offset: '100',
        },
      });
    });

    it('applies filtering parameters', async () => {
      const url = builder.getResources({
        systemType: 'sosa:Sensor',
        q: 'temperature',
      });
      parseAndValidateUrl(url, {
        pathname: '/resources',
        query: {
          systemType: 'sosa:Sensor',
          q: 'temperature',
        },
      });
    });
  });

  describe('getResource()', () => {
    it('constructs single resource URL', async () => {
      const url = builder.getResource('res-123');
      parseAndValidateUrl(url, {
        pathname: '/resources/res-123',
      });
    });

    it('encodes resource ID with special characters', async () => {
      const url = builder.getResource('res/123');
      parseAndValidateUrl(url, {
        pathname: '/resources/res%2F123',
      });
    });
  });

  describe('createResource()', () => {
    it('constructs POST URL', async () => {
      const url = builder.createResource({
        /* body */
      });
      parseAndValidateUrl(url, {
        pathname: '/resources',
      });
    });
  });

  // Additional methods: update, delete, nested endpoints
});
```

**Estimated Size:** 90-250 lines per file

### 7.3 Integration Test Template (Workflow)

**File:** `integration-{workflow}.spec.ts`

```typescript
import { describe, it, expect, beforeEach } from '@jest/globals';
import { OgcApiEndpoint } from '../endpoint';
import { mockFetch } from './test-helpers';
import { loadFixture } from './test-fixtures';

describe('Integration - WorkflowName Workflow', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(async () => {
    // Mock fetch for all requests in workflow
    mockFetch({
      'https://api.example.com/': loadFixture(
        'integration/workflow/step1-root.json'
      ),
      'https://api.example.com/collections': loadFixture(
        'integration/workflow/step2-collections.json'
      ),
      // ... more mocked responses
    });

    endpoint = await OgcApiEndpoint.create('https://api.example.com/');
  });

  it('completes workflow end-to-end', async () => {
    // Step 1: Initial discovery
    const collections = await endpoint.getCollections();
    expect(collections).toHaveLength(1);

    // Step 2: Get resource collection
    const builder = await endpoint.csapi(collections[0].id);
    const resources = builder.getResources();

    // Step 3: Verify results
    expect(resources).toBeDefined();
    expect(resources.features).toHaveLength(10);
  });

  it('handles empty collection in workflow', async () => {
    mockFetch({
      'https://api.example.com/resources': loadFixture(
        'integration/workflow/empty-collection.json'
      ),
    });

    const builder = await endpoint.csapi('test-collection');
    const resources = builder.getResources();
    expect(resources.features).toHaveLength(0);
  });

  it('handles error condition in workflow', async () => {
    mockFetch({
      'https://api.example.com/resources': {
        status: 404,
        body: loadFixture('errors/error-404.json'),
      },
    });

    const builder = await endpoint.csapi('test-collection');
    await expect(builder.getResources()).rejects.toThrow(/404/);
  });
});
```

**Estimated Size:** 200-350 lines per file

### 7.4 Format Parser Test Template

**File:** `{format}-parser.spec.ts`

```typescript
import { describe, it, expect } from '@jest/globals';
import { parseFormat, FormatType } from './format-parser';
import { loadFixture } from './test-fixtures';

describe('FormatName Parser', () => {
  describe('parseFormat() - valid documents', () => {
    it('parses simple document', () => {
      const json = loadFixture('format/simple-document.json');
      const result = parseFormat(json);

      expect(result.type).toBe('ExpectedType');
      expect(result.id).toBe('expected-id');
      expect(result.properties).toBeDefined();
    });

    it('parses complex document with nested components', () => {
      const json = loadFixture('format/complex-document.json');
      const result = parseFormat(json);

      expect(result.components).toHaveLength(3);
      expect(result.components[0].type).toBe('ComponentType');
    });

    it('parses document with optional properties', () => {
      const json = loadFixture('format/minimal-document.json');
      const result = parseFormat(json);

      expect(result).toBeDefined();
      // Optional properties may be undefined
      expect(result.optionalProperty).toBeUndefined();
    });
  });

  describe('parseFormat() - error handling', () => {
    it('throws error for missing required field', () => {
      const invalidJson = loadFixture('format/missing-required-field.json');
      expect(() => parseFormat(invalidJson)).toThrow(/required field/);
    });

    it('throws error for invalid type', () => {
      const invalidJson = loadFixture('format/invalid-type.json');
      expect(() => parseFormat(invalidJson)).toThrow(/invalid type/);
    });
  });

  describe('parseFormat() - edge cases', () => {
    it('handles empty arrays', () => {
      const json = loadFixture('format/empty-arrays.json');
      const result = parseFormat(json);
      expect(result.components).toHaveLength(0);
    });

    it('handles null geometry', () => {
      const json = loadFixture('format/null-geometry.json');
      const result = parseFormat(json);
      expect(result.geometry).toBeNull();
    });
  });
});
```

**Estimated Size:** 300-500 lines per file

### 7.5 Test Utility File Template

**File:** `test-utils.ts` (NOT a test file, no `.spec.ts`)

```typescript
import { URL } from 'url';
import { expect } from '@jest/globals';

/**
 * Parse and validate URL structure
 */
export interface ParsedURL {
  protocol: string;
  host: string;
  port: string;
  pathname: string;
  query: Record<string, string>;
  hash: string;
}

export function parseAndValidateUrl(
  url: string,
  expected: {
    protocol?: string;
    host?: string;
    port?: string;
    pathname?: string;
    query?: Record<string, string>;
  }
): ParsedURL {
  const parsed = new URL(url);

  if (expected.protocol !== undefined) {
    expect(parsed.protocol).toBe(expected.protocol);
  }

  if (expected.host !== undefined) {
    expect(parsed.host).toBe(expected.host);
  }

  if (expected.pathname !== undefined) {
    expect(parsed.pathname).toBe(expected.pathname);
  }

  const query: Record<string, string> = {};
  parsed.searchParams.forEach((value, key) => {
    query[key] = value;
  });

  if (expected.query !== undefined) {
    expect(query).toEqual(expected.query);
  }

  return {
    protocol: parsed.protocol,
    host: parsed.host,
    port: parsed.port,
    pathname: parsed.pathname,
    query,
    hash: parsed.hash,
  };
}

/**
 * Validate URL encoding
 */
export function validateEncoding(url: string, expectedEncoding: string): void {
  expect(url).toContain(expectedEncoding);
}

// Additional utility functions...
```

**Estimated Size:** 150-200 lines

---

## 8. Test Utility Organization

### 8.1 Shared Test Utilities

**File:** `test-utils.ts` (~150-200 lines)

**Contents:**

```typescript
// URL validation
export function parseAndValidateUrl(
  url: string,
  expected: UrlExpectation
): ParsedURL;
export function validateEncoding(url: string, expectedEncoding: string): void;

// Data validation
export function validateGeoJSON(feature: any): void;
export function validateSensorML(document: any): void;
export function validateSWECommon(document: any): void;

// Comparison utilities
export function compareDates(date1: string, date2: string): boolean;
export function compareCoordinates(coord1: number[], coord2: number[]): boolean;
```

### 8.2 Test Setup Helpers

**File:** `test-helpers.ts` (~100-150 lines)

**Contents:**

```typescript
// Endpoint creation
export async function createTestEndpoint(
  options?: TestEndpointOptions
): Promise<OgcApiEndpoint>;
export async function createTestQueryBuilder(
  resourceType?: string
): Promise<CSAPIQueryBuilder>;

// Mocking utilities
export function mockFetch(responses: Record<string, any>): void;
export function resetMocks(): void;

// Fixture utilities (may be separate file)
export function loadFixture(path: string): any;
export function createMinimalFixture(type: string): any;
```

### 8.3 Fixture Loading Utilities

**File:** `test-fixtures.ts` (~50-100 lines)

**Contents:**

```typescript
import * as fs from 'fs';
import * as path from 'path';

/**
 * Load fixture from fixtures directory
 */
export function loadFixture(relativePath: string): any {
  const fixturePath = path.join(__dirname, '../../../fixtures', relativePath);
  const content = fs.readFileSync(fixturePath, 'utf-8');

  // Handle JSON, CSV, binary based on extension
  const ext = path.extname(fixturePath);
  if (ext === '.json') {
    return JSON.parse(content);
  } else if (ext === '.csv') {
    return content; // Return as string
  } else if (ext === '.bin') {
    return fs.readFileSync(fixturePath); // Return as Buffer
  }

  return content;
}

/**
 * Load all fixtures matching pattern
 */
export function loadFixtures(pattern: string): Record<string, any>;

/**
 * Create minimal fixture programmatically
 */
export function createMinimalFixture(type: 'system' | 'deployment' | ...): any;
```

### 8.4 Usage Guidelines

**When to Use Test Utilities:**

| Utility               | Use When                          | Don't Use When                   |
| --------------------- | --------------------------------- | -------------------------------- |
| `parseAndValidateUrl` | Testing URL construction          | Simple string checks             |
| `validateEncoding`    | Testing query parameter encoding  | Full URL validation              |
| `loadFixture`         | Loading external test data        | Simple inline objects            |
| `createTestEndpoint`  | Setting up endpoint in beforeEach | Testing endpoint creation itself |
| `mockFetch`           | Integration tests                 | Unit tests (no network calls)    |

**Example Usage:**

```typescript
describe('CSAPIQueryBuilder', () => {
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    // Use helper for consistent setup
    builder = await createTestQueryBuilder();
  });

  it('constructs URL correctly', async () => {
    const url = builder.getSystems({ limit: 10 });

    // Use utility for structured validation
    parseAndValidateUrl(url, {
      pathname: '/systems',
      query: { limit: '10' },
    });
  });
});
```

---

## 9. Fixture Organization Integration

### 9.1 Fixture Directory Structure

**From Section 15 - Complete Fixture Organization:**

```
fixtures/
  README.md                          # Fixture library overview
  SOURCES.md                         # Provenance documentation

  csapi-querybuilder/                # QueryBuilder test fixtures (23 files)
    universal/                       # Shared across resources (5 files)
    resources/                       # Per-resource responses (18 files)
      systems/
      deployments/
      procedures/
      samplingfeatures/
      properties/
      datastreams/
      observations/
      controlstreams/
      commands/

  geojson-csapi/                     # GeoJSON parser fixtures (~20 files)
    systems/
    deployments/
    procedures/
    samplingfeatures/
    properties/

  sensorml/                          # SensorML parser fixtures (~25 files)
    physicalsystem/
    physicalcomponent/
    simpleprocess/
    aggregateprocess/

  swe-common/                        # SWE Common parser fixtures (~120 files)
    json/
    text/
    binary/

  integration/                       # Integration workflow fixtures (33 files)
    discovery/
    observation/
    command/
    navigation/

  errors/                            # Error and edge cases (~30 files)
    empty/
    invalid/
    schema-violations/
    http-errors/
```

**Total Fixtures:** ~280 files

### 9.2 Fixture Usage Patterns

**Universal Fixtures** (shared across all tests):

```typescript
// In url_builder-*.spec.ts files
beforeEach(async () => {
  const conformance = loadFixture(
    'csapi-querybuilder/universal/conformance-all-resources.json'
  );
  const collectionInfo = loadFixture(
    'csapi-querybuilder/universal/collection-info-all-resources.json'
  );

  const endpoint = await createTestEndpoint({ conformance, collectionInfo });
  builder = await endpoint.csapi('test-collection');
});
```

**Resource-Specific Fixtures**:

```typescript
// In url_builder-systems.spec.ts
it('parses systems collection response', () => {
  const response = loadFixture(
    'csapi-querybuilder/resources/systems/systems-collection-response.json'
  );
  // Test logic...
});
```

**Format Parser Fixtures**:

```typescript
// In sensorml-parser.spec.ts
it('parses PhysicalSystem', () => {
  const sensorml = loadFixture(
    'sensorml/physicalsystem/physicalsystem-weather-station.json'
  );
  const result = parseSensorML(sensorml);
  // Assertions...
});
```

**Integration Workflow Fixtures**:

```typescript
// In integration-discovery.spec.ts
beforeEach(() => {
  mockFetch({
    'https://api.example.com/': loadFixture(
      'integration/discovery/discovery-root-landing-page.json'
    ),
    'https://api.example.com/conformance': loadFixture(
      'integration/discovery/discovery-conformance.json'
    ),
    // ... more fixtures
  });
});
```

### 9.3 Fixture Reusability

**Reuse Patterns:**

| Fixture Category                 | Shared Across                         | Reusability                             |
| -------------------------------- | ------------------------------------- | --------------------------------------- |
| **Universal** (5 files)          | All URL builder tests                 | HIGH - Used in every resource test file |
| **Resource-specific** (18 files) | Single resource tests                 | MEDIUM - Used in one test file each     |
| **GeoJSON** (~20 files)          | GeoJSON parser tests                  | LOW - Parser-specific                   |
| **SensorML** (~25 files)         | SensorML parser tests                 | LOW - Parser-specific                   |
| **SWE Common** (~120 files)      | SWE parser tests                      | LOW - Parser-specific                   |
| **Integration** (33 files)       | Integration tests                     | MEDIUM - Workflow-specific, some shared |
| **Errors** (~30 files)           | Error handling tests across all files | HIGH - Error cases used in many tests   |

**Optimization Strategy:**

1. **Universal fixtures** loaded once and reused across all tests
2. **Resource fixtures** loaded per-file (not shared outside resource)
3. **Error fixtures** shared across all test types (error handling common)

---

## 10. Implementation Guidelines

### 10.1 Test Implementation Order

**Phase 1: Core Unit Tests** (Week 1, ~450-650 lines)

1. ✅ Create `test-utils.ts` (shared utilities)
2. ✅ Create `test-helpers.ts` (setup helpers)
3. ✅ Create `test-fixtures.ts` (fixture loading)
4. ✅ Implement `model.spec.ts` (type tests)
5. ✅ Implement `helpers.spec.ts` (utility function tests)
6. ✅ Implement `url_builder-base.spec.ts` (base QueryBuilder tests)

**Phase 2: URL Builder Resource Tests** (Weeks 2-3, ~1,390-1,790 lines) 7. ✅ Implement `url_builder-systems.spec.ts` (32 tests, CRITICAL) 8. ✅ Implement `url_builder-datastreams.spec.ts` (28 tests, CRITICAL) 9. ✅ Implement `url_builder-observations.spec.ts` (22 tests, CRITICAL) 10. ✅ Implement `url_builder-commands.spec.ts` (24 tests, HIGH) 11. ✅ Implement `url_builder-deployments.spec.ts` (21 tests, HIGH) 12. ✅ Implement `url_builder-controlstreams.spec.ts` (21 tests, HIGH) 13. ✅ Implement `url_builder-samplingfeatures.spec.ts` (19 tests, MEDIUM) 14. ✅ Implement `url_builder-procedures.spec.ts` (17 tests, MEDIUM) 15. ✅ Implement `url_builder-properties.spec.ts` (14 tests, MEDIUM)

**Phase 3: Format Parser Tests** (Week 4, ~1,000-1,300 lines) 16. ✅ Implement `geojson-csapi-parser.spec.ts` (~300-400 lines) 17. ✅ Implement `sensorml-parser.spec.ts` (~300-400 lines) 18. ✅ Implement `swe-parser.spec.ts` (~400-500 lines)

**Phase 4: Integration Tests** (Week 5, ~900-1,150 lines) 19. ✅ Implement `integration-discovery.spec.ts` (12-15 tests) 20. ✅ Implement `integration-observation.spec.ts` (15-18 tests) 21. ✅ Implement `integration-command.spec.ts` (12-15 tests) 22. ✅ Implement `integration-navigation.spec.ts` (15-20 tests)

**Total Implementation Time:** ~5 weeks (~200 hours)

> **Estimate Context:** The 200-hour estimate is an upper bound that includes research, fixture creation/validation, test utility development, code review iteration, and CI integration — not just test code writing. Actual code writing for ~4,100–5,300 lines of test code with templates and shared utilities would be a subset of this total.

### 10.2 Development Best Practices

**1. Write Tests Incrementally:**

- ✅ Implement tests as you implement features
- ✅ Don't wait until all implementation is complete
- ✅ Tests guide implementation (TDD where appropriate)

**2. Reuse Utilities:**

- ✅ Use `parseAndValidateUrl` for all URL validation
- ✅ Use `createTestEndpoint` for consistent setup
- ✅ Use `loadFixture` for external test data

**3. Keep Tests Focused:**

- ✅ One test case tests one behavior
- ✅ Test names describe what is being tested
- ✅ Avoid testing multiple behaviors in one test

**4. Maintain Fixtures:**

- ✅ Validate fixtures against schemas
- ✅ Document fixture provenance (where it came from)
- ✅ Keep fixtures minimal (only necessary data)

**5. Run Tests Frequently:**

- ✅ Run tests before committing
- ✅ Run tests in watch mode during development
- ✅ Use Jest's `--onlyChanged` flag for speed

### 10.3 Code Review Checklist

**For Test Files:**

- [ ] Test file named correctly (`{module}.spec.ts`)
- [ ] describe/it blocks follow naming conventions
- [ ] Imports organized (external → internal → test utils)
- [ ] Uses shared utilities (parseAndValidateUrl, createTestEndpoint)
- [ ] No hardcoded URLs (use fixtures or test helpers)
- [ ] Error cases tested (not just happy path)
- [ ] Test names are descriptive
- [ ] No commented-out tests (remove or fix)

**For Test Utilities:**

- [ ] Utility file does NOT have `.spec.ts` suffix
- [ ] Functions are reusable (not specific to one test)
- [ ] Functions are well-documented (JSDoc comments)
- [ ] Functions handle edge cases

**For Fixtures:**

- [ ] Fixture in correct directory
- [ ] Fixture named according to conventions
- [ ] Fixture documented in SOURCES.md (provenance)
- [ ] Fixture validated against schema (if applicable)

### 10.4 CI/CD Integration

**Jest Configuration:**

```javascript
// jest.config.cjs
module.exports = {
  // Test file patterns
  testMatch: ['**/*.spec.ts'],

  // Coverage thresholds
  coverageThresholds: {
    global: {
      branches: 80,
      functions: 85,
      lines: 85,
      statements: 85,
    },
  },

  // Test organization
  testPathIgnorePatterns: ['/node_modules/', '/dist/'],

  // Parallel execution
  maxWorkers: '50%',
};
```

**GitHub Actions Workflow:**

```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - run: npm ci
      - run: npm test -- --coverage
      - run: npm run test:integration
```

---

## 11. Success Criteria

### 11.1 Completeness Criteria

**File Structure:**

- [x] All 22 test files identified and documented
- [x] Directory structure specified
- [x] File naming conventions defined
- [x] Test structure templates created
- [x] Fixture organization integrated

**Alignment:**

- [x] Test organization matches upstream patterns (flat, colocated)
- [x] Test file naming matches upstream (`.spec.ts`)
- [x] Test structure matches upstream (describe/it patterns)
- [x] No conflicts with upstream conventions

**Documentation:**

- [x] Complete test file inventory with line estimates
- [x] All templates documented with examples
- [x] Fixture integration clearly specified
- [x] Implementation guidelines provided

### 11.2 Quality Criteria

**Maintainability:**

- ✅ Test files focused (50-350 lines each)
- ✅ Clear naming conventions
- ✅ Reusable utilities
- ✅ Minimal duplication

**Scalability:**

- ✅ Flat structure supports growth (upstream precedent: WMS 12 files)
- ✅ Resource-specific files enable parallel development
- ✅ Fixture organization scales to 280+ files
- ✅ Test utilities reduce boilerplate

**Discoverability:**

- ✅ All test files in single directory (flat structure)
- ✅ Clear file naming (`url_builder-{resource}.spec.ts`)
- ✅ Fixtures organized by test type
- ✅ Documentation comprehensive

### 11.3 Validation Checklist

- [x] **Phase 1 Complete:** Upstream test structure analyzed
- [x] **Phase 2 Complete:** Test file inventory compiled (22 files)
- [x] **Phase 3 Complete:** Directory structure designed
- [x] **Phase 4 Complete:** Naming conventions defined
- [x] **Phase 5 Complete:** Test structure templates created (5 templates)
- [x] **Phase 6 Complete:** Deliverable document synthesized

**Cross-References:**

- [x] Integration with Section 1 (upstream patterns)
- [x] Integration with Section 2 (test organization)
- [x] Integration with Section 12 (QueryBuilder testing)
- [x] Integration with Section 15 (fixture organization)
- [x] Integration with Sections 8-14 (test specifications)

---

## Document Metadata

**Status:** ✅ Complete  
**Word Count:** ~10,000 words  
**Sections:** 11  
**Test Files Specified:** 22 files  
**Fixtures Organized:** ~280 files  
**Templates Created:** 5 templates  
**Estimated Implementation Time:** ~5 weeks (200 hours upper bound; includes research, fixture creation, review iteration, and CI integration — not just code writing)

**Review Checklist:**

- [x] All research questions answered (7 core + 8 detailed)
- [x] Upstream patterns documented and aligned
- [x] Complete test file inventory (22 files with line estimates)
- [x] Directory structure specified (flat colocated)
- [x] File naming conventions defined (`.spec.ts` pattern)
- [x] Test structure standards documented (describe/it patterns)
- [x] Test file templates created (5 templates)
- [x] Test utility organization specified (3 utility files)
- [x] Fixture organization integrated (280 fixtures from Section 15)
- [x] Implementation guidelines provided
- [x] Success criteria defined and validated

**Dependencies Satisfied:**

- ✅ Section 1: Upstream Blueprint Analysis
- ✅ Section 2: Upstream Test Pattern Survey
- ✅ Section 8-14: Component Testing Requirements
- ✅ Section 15: Fixture Sourcing and Organization Strategy
- ✅ File Organization Analysis

**Next Steps:**

1. ✅ Update research plan status (Section 9 + 10)
2. ✅ Commit deliverable document
3. ⏳ Begin test implementation (Phase 1: Core unit tests)
4. ⏳ Create test utility files (test-utils.ts, test-helpers.ts, test-fixtures.ts)
5. ⏳ Implement first test file (model.spec.ts)

---

**End of Document**
