# Component 2: Conformance Reader - Complete Analysis

**Status:** ✅ RESEARCH COMPLETE  
**Component:** Conformance Detection for CSAPI Support  
**Date:** February 2, 2026  
**Research Phase:** Complete Blueprint Ready for Implementation

---

## Executive Summary

This document provides complete implementation specifications for adding CSAPI conformance detection to the OGC API client library. The implementation consists of **two functions totaling ~7 lines of code** in `info.ts` following the exact pattern established by EDR conformance detection.

**Key Finding:** CSAPI conformance detection is significantly simpler than EDR - it only requires checking for conformance class URIs without needing to examine collections or metadata.

---

## 1. Conformance Check Function Specification

### 1.1 Function Signature

```typescript
export function checkHasConnectedSystems([conformance]: [
  ConformanceClass[]
]): boolean;
```

**Parameters:**

- `conformance`: Array of ConformanceClass (which is `type ConformanceClass = string`)
- Pattern uses destructured array parameter (same as EDR)

**Return Value:**

- `true` if endpoint supports CSAPI (Part 1 OR Part 2 Core detected)
- `false` otherwise

### 1.2 Implementation Logic

**Detection Strategy:**
Check for **either** Part 1 Core **OR** Part 2 Core conformance class.

**Complete Implementation:**

```typescript
export function checkHasConnectedSystems([conformance]: [
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common'
    ) > -1 ||
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common'
    ) > -1
  );
}
```

**Rationale for "api-common" Classes:**

- Part 1 api-common: Required for all Part 1 implementations
- Part 2 api-common: Required for all Part 2 implementations
- These are the core conformance classes that indicate CSAPI support
- More specific than checking for individual resource types (system, datastream, etc.)

### 1.3 Comparison with EDR Pattern

**EDR Implementation (Reference):**

```typescript
export function checkHasEnvironmentalDataRetrieval([conformance]: [
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core'
    ) > -1
  );
}
```

**Key Differences:**

- **CSAPI**: Checks for **two** conformance classes (Part 1 OR Part 2)
- **EDR**: Checks for **one** conformance class
- **CSAPI**: Uses `api-common` (foundational)
- **EDR**: Uses `core` (foundational)
- **Pattern**: Identical destructuring, indexOf, boolean return

---

## 2. Endpoint Getter Specification

### 2.1 Getter Signature

```typescript
get hasConnectedSystems(): Promise<boolean>
```

**Characteristics:**

- Public getter on OgcApiEndpoint class
- Returns Promise<boolean> (async conformance check)
- No parameters (reads from internal conformanceClasses)
- JSDoc comment follows established pattern

### 2.2 Implementation

**Location:** `src/ogc-api/endpoint.ts` (~line 275, after `hasEnvironmentalDataRetrieval`)

**Complete Implementation:**

```typescript
  /**
   * A Promise which resolves to a boolean indicating whether the endpoint offers Connected Systems API support.
   */
  get hasConnectedSystems(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasConnectedSystems
    );
  }
```

**Pattern Analysis:**

- Uses `Promise.all()` even though only one promise (consistency with EDR)
- Destructures array for `checkHasConnectedSystems` function
- Follows exact pattern of `hasEnvironmentalDataRetrieval`

### 2.3 Comparison with Other Getters

**Simple Pattern (Tiles, Styles, EDR):**

```typescript
get hasTiles(): Promise<boolean> {
  return this.conformanceClasses.then(checkTileConformance);
}

get hasEnvironmentalDataRetrieval(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasEnvironmentalDataRetrieval
  );
}
```

**Complex Pattern (Features, Records):**

```typescript
get hasFeatures(): Promise<boolean> {
  return Promise.all([
    this.data.then((data) => (data ? data.collections : [])),
    this.conformanceClasses,
  ]).then(checkHasFeatures);
}
```

**CSAPI Uses Simple Pattern:**

- No need to check collections (unlike Features/Records)
- No need to check metadata (unlike EDR's per-collection checks)
- Pure conformance class detection

---

## 3. Type Definitions

### 3.1 Existing Types (No Changes Required)

**ConformanceClass Type:**

```typescript
export type ConformanceClass = string;
```

**Location:** `src/ogc-api/model.ts` (line 3)

**Usage:**

- Already used by all conformance check functions
- Array parameter: `ConformanceClass[]`
- Return value from `parseConformance()`

### 3.2 No New Types Needed

Unlike EDR which requires metadata types (`DataQueryType`, `EdrParameterInfo`), CSAPI conformance detection requires **no new types**.

**Comparison:**

- **EDR**: Adds 5+ new types for data queries, parameters, metadata
- **CSAPI**: Uses only existing `ConformanceClass` type
- **Reason**: Conformance detection is metadata-agnostic

---

## 4. Integration Points

### 4.1 info.ts Integration

**File:** `src/ogc-api/info.ts`  
**Location:** After `checkHasEnvironmentalDataRetrieval` (~line 105)  
**Lines Added:** ~7 lines (function + whitespace)

**Import Requirements:**

- None (uses existing `ConformanceClass` type)

**Export Requirements:**

```typescript
export function checkHasConnectedSystems([conformance]: [
  ConformanceClass[]
]): boolean;
```

### 4.2 endpoint.ts Integration

**File:** `src/ogc-api/endpoint.ts`  
**Location:** After `hasEnvironmentalDataRetrieval` (~line 278)  
**Lines Added:** ~5 lines (getter + comment)

**Import Requirements:**

```typescript
import {
  checkHasConnectedSystems, // ADD THIS
  checkHasEnvironmentalDataRetrieval,
  checkHasFeatures,
  checkHasRecords,
  // ... other imports
} from './info.js';
```

**Export Requirements:**

- Getter is automatically exported as public class member
- No explicit export needed

### 4.3 index.ts Integration

**File:** `src/ogc-api/index.ts`  
**Action:** No changes required

**Reason:**

- Only exports `OgcApiEndpoint` class (which includes getter)
- Does not export individual conformance check functions
- Pattern: EDR check function not exported either

---

## 5. Conformance Class URI Reference

### 5.1 CSAPI Conformance Class URIs

**Part 1 Base URI:**

```
http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/
```

**Part 2 Base URI:**

```
http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/
```

**Core Classes Used for Detection:**

1. **Part 1 Common (Primary Detection):**

   ```
   http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common
   ```

2. **Part 2 Common (Primary Detection):**
   ```
   http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common
   ```

### 5.2 Complete Part 1 Conformance Classes

**Required:**

- `api-common` - Common patterns and requirements

**Resource Types:**

- `system` - System resources
- `subsystem` - Subsystem resources
- `deployment` - Deployment resources
- `subdeployment` - Subdeployment resources
- `procedure` - Procedure resources
- `sf` - Sampling Feature resources
- `property` - Property resources

**Optional Features:**

- `advanced-filtering` - Advanced query capabilities
- `create-replace-delete` - Write operations
- `update` - Patch operations
- `geojson` - GeoJSON encoding
- `sensorml` - SensorML encoding

### 5.3 Complete Part 2 Conformance Classes

**Required:**

- `api-common` - Common patterns and requirements

**Resource Types:**

- `datastream` - Data stream resources
- `controlstream` - Control stream resources
- `feasibility` - Feasibility check resources
- `system-event` - System event resources

**Optional Features:**

- `advanced-filtering` - Advanced query capabilities
- `create-replace-delete` - Write operations
- `update` - Patch operations
- `json` - JSON encoding
- `swecommon-json` - SWE Common JSON encoding
- `swecommon-text` - SWE Common text encoding
- `swecommon-binary` - SWE Common binary encoding

### 5.4 Why Use "api-common" for Detection?

**Reasoning:**

1. **Foundational**: All implementations MUST support api-common
2. **Comprehensive**: Presence indicates full CSAPI support capability
3. **Unambiguous**: Clear indicator of standard compliance
4. **Extensible**: Works even if new resource types added later
5. **Consistent**: Mirrors approach used by other OGC APIs

**Alternative Rejected:**

- Checking for specific resource types (system, datastream) - too narrow
- Checking for multiple classes - unnecessary complexity
- Pattern matching on URI prefix - not precise enough

---

## 6. Error Handling Strategy

### 6.1 No Explicit Error Handling Required

**Pattern:** Same as EDR and other conformance checks

**Characteristics:**

- Returns `false` if conformance classes not found
- No exceptions thrown
- No validation of conformance array

**Code Behavior:**

```typescript
// Empty array
checkHasConnectedSystems([[]]); // returns false

// Null safety (handled by caller)
endpoint.conformanceClasses; // handles fetch errors upstream

// Malformed URIs
// No validation - exact string match only
```

### 6.2 Error Handling Location

**Upstream Handling:**

- `endpoint.conformanceClasses` getter handles fetch errors
- `parseConformance()` extracts array from response
- Errors propagate as rejected Promise

**Downstream Handling:**

- `endpoint.hasConnectedSystems` returns rejected Promise if fetch fails
- Caller must handle Promise rejection

**Pattern Consistency:**

- Identical to EDR, Features, Tiles, Records
- No special error handling in conformance check function

---

## 7. Testing Strategy

### 7.1 Unit Tests Required

**File:** `src/ogc-api/info.spec.ts`  
**Test Suite:** `checkHasConnectedSystems`

**Test Cases (Minimum):**

```typescript
describe('checkHasConnectedSystems', () => {
  it('returns true when Part 1 api-common is present', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(true);
  });

  it('returns true when Part 2 api-common is present', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(true);
  });

  it('returns true when both Part 1 and Part 2 api-common are present', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common',
      'http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(true);
  });

  it('returns false when no CSAPI conformance classes present', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
      'http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(false);
  });

  it('returns false when conformance array is empty', () => {
    expect(checkHasConnectedSystems([[]])).toBe(false);
  });

  it('returns true when Part 1 system class is present (but not api-common)', () => {
    // Should return false since we're checking for api-common specifically
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/system',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(false);
  });
});
```

### 7.2 Integration Tests Required

**File:** `src/ogc-api/endpoint.spec.ts`  
**Test Suite:** `OgcApiEndpoint` → `#hasConnectedSystems`

**Test Cases (Minimum):**

```typescript
describe('#hasConnectedSystems', () => {
  describe('with Part 1 support', () => {
    beforeEach(() => {
      // Mock fixture with Part 1 api-common conformance class
      endpoint = new OgcApiEndpoint('http://local/csapi-part1/');
    });

    it('returns true', async () => {
      await expect(endpoint.hasConnectedSystems).resolves.toBe(true);
    });
  });

  describe('with Part 2 support', () => {
    beforeEach(() => {
      // Mock fixture with Part 2 api-common conformance class
      endpoint = new OgcApiEndpoint('http://local/csapi-part2/');
    });

    it('returns true', async () => {
      await expect(endpoint.hasConnectedSystems).resolves.toBe(true);
    });
  });

  describe('without CSAPI support', () => {
    beforeEach(() => {
      endpoint = new OgcApiEndpoint('http://local/sample-data/');
    });

    it('returns false', async () => {
      await expect(endpoint.hasConnectedSystems).resolves.toBe(false);
    });
  });
});
```

### 7.3 Test Fixtures Required

**File:** `fixtures/ogc-api/csapi-test-endpoint/root.json`

**Minimum Conformance Document:**

```json
{
  "title": "Test CSAPI Endpoint",
  "description": "Test endpoint for CSAPI conformance detection",
  "links": [
    {
      "rel": "conformance",
      "href": "/conformance?f=json"
    },
    {
      "rel": "service-desc",
      "href": "/api?f=json"
    },
    {
      "rel": "data",
      "href": "/collections?f=json"
    }
  ]
}
```

**File:** `fixtures/ogc-api/csapi-test-endpoint/conformance.json`

**Part 1 Support:**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/system"
  ]
}
```

**Part 2 Support:**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/datastream"
  ]
}
```

---

## 8. Implementation Checklist

### Phase 1: Core Function (Day 1, 30 minutes)

- [ ] **1.1** Add `checkHasConnectedSystems` function to `info.ts`

  - Location: After `checkHasEnvironmentalDataRetrieval` (line ~105)
  - Implementation: 7 lines (including whitespace)
  - Pattern: Exact copy of EDR pattern with CSAPI URIs

- [ ] **1.2** Add import to `endpoint.ts`

  - Location: Import block (line ~2)
  - Change: Add `checkHasConnectedSystems` to existing import list
  - Lines: 1 line modified

- [ ] **1.3** Add `hasConnectedSystems` getter to `endpoint.ts`
  - Location: After `hasEnvironmentalDataRetrieval` (line ~278)
  - Implementation: 5 lines (including comment)
  - Pattern: Exact copy of EDR getter pattern

### Phase 2: Unit Tests (Day 1, 1 hour)

- [ ] **2.1** Create `info.spec.ts` test suite

  - Test: `checkHasConnectedSystems` function
  - Cases: 6 test cases minimum
  - Coverage: Part 1, Part 2, both, none, empty, edge cases

- [ ] **2.2** Run unit tests locally
  - Command: `npm test -- info.spec.ts`
  - Verify: All tests pass
  - Coverage: 100% for new function

### Phase 3: Integration Tests (Day 1, 1 hour)

- [ ] **3.1** Create test fixtures

  - Files: `fixtures/ogc-api/csapi-test-endpoint/`
  - Documents: root.json, conformance.json
  - Variants: Part 1 only, Part 2 only

- [ ] **3.2** Add `endpoint.spec.ts` test cases

  - Test: `#hasConnectedSystems` getter
  - Cases: 3 test cases minimum
  - Setup: Mock OgcApiEndpoint with fixtures

- [ ] **3.3** Run integration tests locally
  - Command: `npm test -- endpoint.spec.ts`
  - Verify: All new tests pass
  - Check: No regressions in existing tests

### Phase 4: Validation (Day 2, 30 minutes)

- [ ] **4.1** Manual testing with live endpoint

  - Test: Real CSAPI endpoint (if available)
  - Verify: `hasConnectedSystems` returns true
  - Document: Endpoint URL and results

- [ ] **4.2** Code review checklist
  - Pattern: Matches EDR implementation
  - Naming: Consistent with other conformance checks
  - Documentation: JSDoc comments complete
  - Imports: All necessary imports added
  - Exports: Function exported from info.ts

### Phase 5: Documentation (Day 2, 30 minutes)

- [ ] **5.1** Update type documentation

  - No changes required (using existing ConformanceClass)

- [ ] **5.2** Update README examples (if applicable)

  - Add example: Check CSAPI support
  - Code: `const hasCSAPI = await endpoint.hasConnectedSystems;`

- [ ] **5.3** Update CHANGELOG
  - Entry: "Add CSAPI conformance detection support"
  - Details: New `hasConnectedSystems` getter

---

## 9. Dependencies and Prerequisites

### 9.1 Depends On (Must Complete First)

**None** - This component is fully independent.

**Characteristics:**

- Self-contained conformance detection
- No dependencies on other CSAPI components
- No dependencies on collections metadata
- Only uses existing conformance system

### 9.2 Required By (Blocks These Components)

**Component 1: OgcApiEndpoint Integration**

- Needs: `hasConnectedSystems` getter
- Usage: Factory method validation
- Code: `if (!this.hasConnectedSystems) throw EndpointError`

**Component 3: Collections Reader**

- Needs: `hasConnectedSystems` getter
- Usage: Collections list filtering
- Code: `Promise.all([this.data, this.hasConnectedSystems])`

### 9.3 Integration Timeline

```
Day 1 (Morning):  Component 2 Implementation Complete
Day 1 (Afternoon): Component 1 can proceed (uses Component 2)
Day 2 (Morning):  Component 3 can proceed (uses Component 2)
Day 2 (Afternoon): Full integration testing
```

---

## 10. Key Design Decisions

### Decision 1: Use "api-common" Classes for Detection

**Options Considered:**

1. Check for `api-common` (CHOSEN)
2. Check for specific resource types (system, datastream)
3. Check for URI prefix pattern
4. Check for multiple classes with AND logic

**Rationale:**

- `api-common` is required by all implementations
- Most foundational and unambiguous
- Future-proof (works with new resource types)
- Consistent with OGC API architecture

**Rejected Alternatives:**

- Resource types: Too narrow, misses valid implementations
- URI prefix: Not precise, could match invalid URIs
- Multiple classes: Unnecessary complexity, false negatives

### Decision 2: OR Logic for Part 1 and Part 2

**Options Considered:**

1. Part 1 OR Part 2 (CHOSEN)
2. Part 1 AND Part 2
3. Part 1 only
4. Part 2 only

**Rationale:**

- Servers may implement only one part
- Both parts are valid CSAPI implementations
- Maximizes compatibility
- Follows principle of least surprise

**Rejected Alternatives:**

- AND logic: Too restrictive, breaks valid servers
- Single part: Arbitrary limitation, breaks use cases

### Decision 3: Simple Pattern (No Collection Check)

**Options Considered:**

1. Conformance-only check (CHOSEN)
2. Conformance + collection metadata check
3. Conformance + resource discovery

**Rationale:**

- Conformance classes are sufficient
- Collections metadata not required for detection
- Simpler implementation (7 lines vs 20+ lines)
- Faster execution (no additional HTTP requests)
- Consistent with Tiles/Styles pattern

**Rejected Alternatives:**

- Collection check: Unnecessary complexity, no benefit
- Resource discovery: Premature, belongs in Component 3

### Decision 4: No New Type Definitions

**Options Considered:**

1. Use existing ConformanceClass type (CHOSEN)
2. Create CSAPIConformanceClass type
3. Create conformance validation types

**Rationale:**

- Conformance detection doesn't need type safety beyond string
- Reduces code footprint
- Consistent with EDR/Tiles/Features approach
- Type safety handled by upstream parseConformance

**Rejected Alternatives:**

- Custom types: Unnecessary complexity, no benefit
- Validation types: Out of scope for detection

### Decision 5: Promise.all Wrapper Pattern

**Options Considered:**

1. Use Promise.all([]) wrapper (CHOSEN)
2. Direct .then() chaining
3. Async/await pattern

**Rationale:**

- Consistent with EDR pattern
- Prepares for future multiple-promise scenarios
- Uniform pattern across all conformance getters
- Matches existing codebase style

**Rejected Alternatives:**

- Direct chaining: Inconsistent with established pattern
- Async/await: Not used in getters throughout codebase

---

## Appendix A: Complete Code Implementation

### A.1 info.ts Addition

```typescript
// File: src/ogc-api/info.ts
// Location: After checkHasEnvironmentalDataRetrieval (line ~105)

export function checkHasConnectedSystems([conformance]: [
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common'
    ) > -1 ||
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common'
    ) > -1
  );
}
```

### A.2 endpoint.ts Import Addition

```typescript
// File: src/ogc-api/endpoint.ts
// Location: Import block (line ~2)

import {
  checkHasConnectedSystems, // ADD THIS LINE
  checkHasEnvironmentalDataRetrieval,
  checkHasFeatures,
  checkHasRecords,
  checkStyleConformance,
  checkTileConformance,
  parseBaseCollectionInfo,
  parseBasicStyleInfo,
  parseCollectionParameters,
  parseCollections,
  parseConformance,
  parseEndpointInfo,
  parseFullStyleInfo,
  parseTileMatrixSets,
} from './info.js';
```

### A.3 endpoint.ts Getter Addition

```typescript
// File: src/ogc-api/endpoint.ts
// Location: After hasEnvironmentalDataRetrieval (line ~278)

  /**
   * A Promise which resolves to a boolean indicating whether the endpoint offers Connected Systems API support.
   */
  get hasConnectedSystems(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasConnectedSystems
    );
  }
```

---

## Appendix B: Conformance Class Reference Table

| Part | Class                 | URI                                                             | Required? | Purpose                 |
| ---- | --------------------- | --------------------------------------------------------------- | --------- | ----------------------- |
| 1    | API Common            | `.../ogcapi-connected-systems-1/1.0/conf/api-common`            | ✅ Yes    | Core patterns           |
| 1    | System                | `.../ogcapi-connected-systems-1/1.0/conf/system`                | ❌ No     | System resources        |
| 1    | Subsystem             | `.../ogcapi-connected-systems-1/1.0/conf/subsystem`             | ❌ No     | Subsystem resources     |
| 1    | Deployment            | `.../ogcapi-connected-systems-1/1.0/conf/deployment`            | ❌ No     | Deployment resources    |
| 1    | Subdeployment         | `.../ogcapi-connected-systems-1/1.0/conf/subdeployment`         | ❌ No     | Subdeployment resources |
| 1    | Procedure             | `.../ogcapi-connected-systems-1/1.0/conf/procedure`             | ❌ No     | Procedure resources     |
| 1    | Sampling Features     | `.../ogcapi-connected-systems-1/1.0/conf/sf`                    | ❌ No     | Sampling features       |
| 1    | Property              | `.../ogcapi-connected-systems-1/1.0/conf/property`              | ❌ No     | Property resources      |
| 1    | Advanced Filtering    | `.../ogcapi-connected-systems-1/1.0/conf/advanced-filtering`    | ❌ No     | Query capabilities      |
| 1    | Create/Replace/Delete | `.../ogcapi-connected-systems-1/1.0/conf/create-replace-delete` | ❌ No     | Write operations        |
| 1    | Update                | `.../ogcapi-connected-systems-1/1.0/conf/update`                | ❌ No     | Patch operations        |
| 1    | GeoJSON               | `.../ogcapi-connected-systems-1/1.0/conf/geojson`               | ❌ No     | GeoJSON encoding        |
| 1    | SensorML              | `.../ogcapi-connected-systems-1/1.0/conf/sensorml`              | ❌ No     | SensorML encoding       |
| 2    | API Common            | `.../ogcapi-connected-systems-2/1.0/conf/api-common`            | ✅ Yes    | Core patterns           |
| 2    | DataStream            | `.../ogcapi-connected-systems-2/1.0/conf/datastream`            | ❌ No     | Data streams            |
| 2    | ControlStream         | `.../ogcapi-connected-systems-2/1.0/conf/controlstream`         | ❌ No     | Control streams         |
| 2    | Feasibility           | `.../ogcapi-connected-systems-2/1.0/conf/feasibility`           | ❌ No     | Feasibility checks      |
| 2    | System Events         | `.../ogcapi-connected-systems-2/1.0/conf/system-event`          | ❌ No     | System events           |
| 2    | Advanced Filtering    | `.../ogcapi-connected-systems-2/1.0/conf/advanced-filtering`    | ❌ No     | Query capabilities      |
| 2    | Create/Replace/Delete | `.../ogcapi-connected-systems-2/1.0/conf/create-replace-delete` | ❌ No     | Write operations        |
| 2    | Update                | `.../ogcapi-connected-systems-2/1.0/conf/update`                | ❌ No     | Patch operations        |
| 2    | JSON                  | `.../ogcapi-connected-systems-2/1.0/conf/json`                  | ❌ No     | JSON encoding           |
| 2    | SWE Common JSON       | `.../ogcapi-connected-systems-2/1.0/conf/swecommon-json`        | ❌ No     | SWE JSON                |
| 2    | SWE Common Text       | `.../ogcapi-connected-systems-2/1.0/conf/swecommon-text`        | ❌ No     | SWE text                |
| 2    | SWE Common Binary     | `.../ogcapi-connected-systems-2/1.0/conf/swecommon-binary`      | ❌ No     | SWE binary              |

**Detection Logic:**

- **Minimum Required:** Part 1 api-common **OR** Part 2 api-common
- **Detection Function:** Checks only required classes (✅ rows)
- **All Other Classes:** Optional, not checked for detection

---

## Appendix C: Pattern Comparison with Other APIs

### C.1 EDR Pattern (Current Implementation)

```typescript
// Function
export function checkHasEnvironmentalDataRetrieval([conformance]: [
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core'
    ) > -1
  );
}

// Getter
get hasEnvironmentalDataRetrieval(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasEnvironmentalDataRetrieval
  );
}
```

**Characteristics:**

- Single conformance class check
- Simple indexOf pattern
- Promise.all wrapper (even though single promise)
- Boolean return value

### C.2 Features Pattern (Current Implementation)

```typescript
// Function
export function checkHasFeatures([collections, conformance]: [
  OgcApiCollectionInfo[],
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core'
    ) > -1 &&
    collections.some(
      (collection) => collection.itemType === 'feature' || !collection.itemType
    )
  );
}

// Getter
get hasFeatures(): Promise<boolean> {
  return Promise.all([
    this.data.then((data) => (data ? data.collections : [])),
    this.conformanceClasses,
  ]).then(checkHasFeatures);
}
```

**Characteristics:**

- Two-parameter check (conformance + collections)
- AND logic (must have both conformance + collection data)
- More complex getter (fetches data)
- Boolean return value

### C.3 CSAPI Pattern (Proposed Implementation)

```typescript
// Function
export function checkHasConnectedSystems([conformance]: [
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common'
    ) > -1 ||
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common'
    ) > -1
  );
}

// Getter
get hasConnectedSystems(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasConnectedSystems
  );
}
```

**Characteristics:**

- Single parameter (conformance only)
- OR logic (Part 1 OR Part 2)
- Simple getter (like EDR)
- Boolean return value

### C.4 Pattern Analysis Summary

| API          | Parameters                | Logic                | Complexity | Line Count |
| ------------ | ------------------------- | -------------------- | ---------- | ---------- |
| **Tiles**    | Conformance               | Single check         | Simple     | ~5 lines   |
| **Styles**   | Conformance               | OR (2 versions)      | Simple     | ~7 lines   |
| **EDR**      | Conformance               | Single check         | Simple     | ~7 lines   |
| **Features** | Conformance + Collections | AND + filter         | Complex    | ~12 lines  |
| **Records**  | Conformance + Collections | Multi-check + filter | Complex    | ~15 lines  |
| **CSAPI**    | Conformance               | OR (2 parts)         | Simple     | ~7 lines   |

**Pattern Classification:**

- **Simple Pattern:** Tiles, Styles, EDR, **CSAPI**
- **Complex Pattern:** Features, Records

**CSAPI is a Simple Pattern implementation.**

---

## Summary

Component 2 (Conformance Reader) is a **simple, self-contained addition** requiring **~7 lines of code** across two functions. The implementation follows the exact pattern established by EDR conformance detection, with the only difference being the check for two conformance classes (Part 1 OR Part 2) instead of one.

**Ready for Implementation:** ✅ All specifications complete, no outstanding questions.

**Next Steps:** Proceed to implementation following the checklist in Section 8.

---

## Development Standards

All implementation work for Component 2 must adhere to the project's [Development Standards](../../../planning/csapi-implementation-guide.md#development-standards) defined in the CSAPI Implementation Guide.

### Key Standards for This Component

**Development Workflow:**

1. Write function signatures before implementation (done in this analysis)
2. Add comprehensive JSDoc comments with parameters, return types, examples
3. Implement functionality following EDR pattern exactly
4. Write tests as you implement (not deferred to later)
5. Document edge cases and validation rules as discovered

**Code Quality Requirements:**

- TypeScript strict mode enabled
- 100% public API JSDoc coverage (add JSDoc to `hasConnectedSystems` getter)
- > 80% test coverage (statement and branch)
- Lint-clean code (ESLint configuration)
- No magic numbers or strings (use constants for conformance URIs)
- Consistent error handling patterns (return false, never throw)

**Documentation Requirements:**

- Clear, concise method descriptions
- Parameter descriptions with types and constraints
- Return type documentation
- Links to relevant CSAPI specification sections
- Error condition documentation

**Testing Requirements:**

- Test positive cases (Part 1, Part 2, both)
- Test negative cases (empty array, wrong classes)
- Test edge cases (undefined, null, malformed URIs)
- Use fixtures from fixtures/ogc-api/ directory

---
