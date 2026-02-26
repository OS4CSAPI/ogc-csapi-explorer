# Component 3: Collections Reader - Complete Analysis

**Status:** ✅ RESEARCH COMPLETE  
**Component:** Collection Filtering for CSAPI Support  
**Date:** February 2, 2026  
**Research Phase:** Complete Blueprint Ready for Implementation

---

## Executive Summary

This document provides complete implementation specifications for adding CSAPI collection filtering to the OGC API client library. The implementation consists of **two parts totaling ~15 lines of code** following the exact pattern established by EDR collection filtering.

**Key Finding:** CSAPI collection detection requires checking either `itemType` OR `featureType` properties on collection metadata, as CSAPI uses both properties depending on whether resources are Feature-based (Part 1) or non-Feature resources (Part 2).

**Implementation Scope:**

- **Filter Function:** ~9 lines in info.ts (extend `parseCollections()` function)
- **Getter:** ~6 lines in endpoint.ts (add `csapiCollections` getter)
- **Total:** ~15 lines following EDR pattern exactly

---

## 1. Collection Metadata Structure

### 1.1 Existing Collection Type

**Location:** `src/ogc-api/model.ts` line 85

```typescript
export interface OgcApiCollectionInfo {
  links: any;
  title: string;
  description: string;
  id: string;
  itemType?: 'feature' | 'record';  // ← Current type is limited
  itemFormats: MimeType[];
  bulkDownloadLinks: Record<string, MimeType>;
  jsonDownloadLink: string;
  crs: CrsCode[];
  storageCrs?: CrsCode;
  itemCount: number;
  keywords?: string[];
  language?: string;
  updated?: Date;
  extent?: BoundingBox;
  publisher?: {...};
  license?: string;
  queryables: CollectionParameter[];
  sortables: CollectionParameter[];
  mapTileFormats: MimeType[];
  vectorTileFormats: MimeType[];
  supportedTileMatrixSets: string[];
  data_queries?: {...};  // ← EDR-specific property
  parameter_names?: Record<string, EdrParameterInfo>;
}
```

### 1.2 CSAPI Collection Metadata

**CSAPI collections include:**

- `itemType` property (for Part 2 non-Feature resources)
- `featureType` property (for Part 1 Feature resources)
- Both may be URI strings (not limited to 'feature' | 'record')

**Example CSAPI Collection:**

```json
{
  "id": "weather-systems",
  "title": "Weather Monitoring Systems",
  "itemType": "http://www.w3.org/ns/sosa/System",
  "featureType": "http://www.w3.org/ns/sosa/System",
  "extent": {...},
  "links": [...]
}
```

### 1.3 Type Extension Needed

**Current Issue:** `itemType` is typed as `'feature' | 'record'` - too restrictive for CSAPI URIs.

**Solution:** Type already accepts undefined/optional, and TypeScript will allow any string at runtime. No type changes needed - just check for SOSA/SSN URI patterns.

---

## 2. CSAPI Resource Type Indicators

### 2.1 Part 1 Feature Resources (use `featureType`)

**Valid featureType URIs:**

- `http://www.w3.org/ns/sosa/System`
- `http://www.w3.org/ns/sosa/Deployment`
- `http://www.w3.org/ns/sosa/Procedure`
- `http://www.w3.org/ns/sosa/Sample` (Sampling Features)

**Spec Requirements:**

- Collections containing Systems MUST set `featureType=sosa:System` (Requirement 8)
- Collections containing Deployments MUST set `featureType=sosa:Deployment` (Requirement 18)
- Collections containing Procedures MUST set `featureType=sosa:Procedure` (Requirement 28)
- Collections containing Sampling Features MUST set `featureType=sosa:Sample` (Requirement 33)

### 2.2 Part 1 Non-Feature Resources (use `itemType`)

**Valid itemType URIs:**

- `http://www.w3.org/ns/sosa/Property`

**Spec Requirements:**

- Collections containing Properties MUST set `itemType=sosa:Property` (Requirement 37)

### 2.3 Part 2 Resources (use `itemType`)

**Valid itemType values:**

- `DataStream` (or full URI format)
- `Observation` (or full URI format)
- `ControlStream` (or full URI format)
- `Command` (or full URI format)
- `Feasibility` (or full URI format)
- `SystemEvent` (or full URI format)

**Note:** Part 2 may use shorter names without full URIs, unlike Part 1.

### 2.4 Detection Strategy

**Check BOTH `itemType` AND `featureType` properties:**

- Part 1 Feature resources use `featureType` (System, Deployment, Procedure, Sample)
- Part 1 non-Feature resources use `itemType` (Property)
- Part 2 resources use `itemType` (DataStream, Observation, etc.)

**Detection Logic:**

```typescript
const hasCSAPIType =
  (collection.featureType && collection.featureType.includes('sosa')) ||
  (collection.itemType &&
    (collection.itemType.includes('sosa') ||
      collection.itemType === 'DataStream' ||
      collection.itemType === 'Observation' ||
      collection.itemType === 'ControlStream' ||
      collection.itemType === 'Command' ||
      collection.itemType === 'Feasibility' ||
      collection.itemType === 'SystemEvent'));
```

---

## 3. Filter Function Design

### 3.1 Extend parseCollections Function

**Location:** `src/ogc-api/info.ts` line 229

**Current Implementation:**

```typescript
export function parseCollections(doc: OgcApiDocument): Array<{
  name: string;
  hasRecords?: boolean;
  hasFeatures?: boolean;
  hasVectorTiles?: boolean;
  hasMapTiles?: boolean;
  hasDataQueries?: boolean;
}> {
  return doc.collections.map((collection) => {
    const result: {...} = {
      name: collection.id as string,
    };

    // Existing checks for Records, Features, Tiles, EDR
    if (collection.itemType === 'record') {
      result.hasRecords = true;
    }
    if (collection.itemType === 'feature' || !collection.itemType) {
      result.hasFeatures = true;
    }
    // ... tile and EDR checks

    if (collection.data_queries) {
      result.hasDataQueries = true;
    }

    return result;
  });
}
```

### 3.2 Add CSAPI Detection

**Add to Return Type:**

```typescript
{
  name: string;
  hasRecords?: boolean;
  hasFeatures?: boolean;
  hasVectorTiles?: boolean;
  hasMapTiles?: boolean;
  hasDataQueries?: boolean;
  hasConnectedSystems?: boolean;  // ← NEW
}
```

**Add Detection Logic (~9 lines):**

```typescript
export function parseCollections(doc: OgcApiDocument): Array<{
  name: string;
  hasRecords?: boolean;
  hasFeatures?: boolean;
  hasVectorTiles?: boolean;
  hasMapTiles?: boolean;
  hasDataQueries?: boolean;
  hasConnectedSystems?: boolean;
}> {
  return doc.collections.map((collection) => {
    const result: {...} = {
      name: collection.id as string,
    };

    // ... existing checks ...

    // CSAPI check - Part 1 Feature resources (featureType)
    if (
      collection.featureType &&
      typeof collection.featureType === 'string' &&
      collection.featureType.includes('sosa')
    ) {
      result.hasConnectedSystems = true;
    }

    // CSAPI check - Part 1 non-Feature + Part 2 resources (itemType)
    if (
      collection.itemType &&
      typeof collection.itemType === 'string' &&
      (collection.itemType.includes('sosa') ||
        collection.itemType === 'DataStream' ||
        collection.itemType === 'Observation' ||
        collection.itemType === 'ControlStream' ||
        collection.itemType === 'Command' ||
        collection.itemType === 'Feasibility' ||
        collection.itemType === 'SystemEvent')
    ) {
      result.hasConnectedSystems = true;
    }

    return result;
  });
}
```

### 3.3 Rationale for Detection Logic

**Why check BOTH `featureType` AND `itemType`:**

- Part 1 uses `featureType` for GeoJSON Feature resources (System, Deployment, Procedure, Sample)
- Part 1 uses `itemType` for non-Feature resources (Property)
- Part 2 uses `itemType` for all resources (DataStream, Observation, etc.)
- Must check both to catch all CSAPI collections

**Why `.includes('sosa')`:**

- Handles both short form (`sosa:System`) and full URI (`http://www.w3.org/ns/sosa/System`)
- Future-proof for variations in URI format
- All Part 1 resources use SOSA namespace

**Why explicit Part 2 checks:**

- Part 2 may use shorter names without full URIs
- More specific matching prevents false positives
- Matches spec requirements exactly

---

## 4. Getter Implementation

### 4.1 Getter Signature

```typescript
get csapiCollections(): Promise<string[]>
```

**Characteristics:**

- Public getter on OgcApiEndpoint class
- Returns Promise<string[]> (array of collection IDs)
- No parameters (reads from internal data and conformance)
- Follows exact pattern of `edrCollections` getter

### 4.2 Complete Implementation

**Location:** `src/ogc-api/endpoint.ts` (~line 210, after `edrCollections`)

```typescript
/**
 * A Promise which resolves to an array of CSAPI collection identifiers as strings.
 */
get csapiCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasConnectedSystems])
    .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasConnectedSystems))
    .then((collections) => collections.map((collection) => collection.name));
}
```

### 4.3 Implementation Breakdown

**Line 1:** Promise.all combines collection data with conformance check

- `this.data` - Promise resolving to OgcApiDocument with collections
- `this.hasConnectedSystems` - Promise resolving to boolean (from Component 2)

**Line 2:** Return empty collections if no CSAPI conformance

- If `hasCSAPI` is false, return empty document to skip processing
- If `hasCSAPI` is true, proceed with actual data

**Line 3:** Parse collections to extract metadata

- Calls `parseCollections()` which adds `hasConnectedSystems` flag

**Line 4:** Filter to only collections with CSAPI resources

- Keep only collections where `hasConnectedSystems === true`

**Line 5:** Map to array of collection IDs

- Extract just the `name` property (collection ID string)

### 4.4 Comparison with EDR Getter

**EDR Implementation (Reference):**

```typescript
get edrCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasEnvironmentalDataRetrieval])
    .then(([data, hasEDR]) => (hasEDR ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasDataQueries))
    .then((collections) => collections.map((collection) => collection.name));
}
```

**Differences:**

- **CSAPI**: Checks `hasConnectedSystems`, filters by `c.hasConnectedSystems`
- **EDR**: Checks `hasEnvironmentalDataRetrieval`, filters by `c.hasDataQueries`
- **Pattern**: Identical - just different property names

---

## 5. Integration Points

### 5.1 info.ts Integration

**File:** `src/ogc-api/info.ts`  
**Location:** Inside `parseCollections()` function body (~line 260)  
**Lines Added:** ~9 lines (two if-blocks for featureType and itemType)

**Integration Steps:**

1. Add `hasConnectedSystems?: boolean` to return type annotation
2. Add featureType check after existing itemType checks
3. Add itemType CSAPI check after featureType check
4. No new imports needed

### 5.2 endpoint.ts Integration

**File:** `src/ogc-api/endpoint.ts`  
**Location:** After `edrCollections` getter (~line 210)  
**Lines Added:** ~6 lines (getter with JSDoc)

**Integration Steps:**

1. Add `csapiCollections` getter after `edrCollections`
2. Add JSDoc comment following existing pattern
3. Use Promise.all pattern with `hasConnectedSystems` from Component 2
4. No new imports needed (parseCollections already imported)

### 5.3 No Type Changes Needed

**Important:** No changes to `OgcApiCollectionInfo` type definition required.

**Why:**

- `itemType` is already optional (`itemType?: 'feature' | 'record'`)
- TypeScript union types don't prevent additional string values at runtime
- Collections API may return any string in `itemType`/`featureType` fields
- Detection logic works with runtime values, not compile-time types
- Changing type would affect existing code (Features, Records, etc.)

---

## 6. Error Handling Strategy

### 6.1 Empty Collections Array

**Scenario:** `/collections` endpoint returns no collections

**Handling:**

- `parseCollections()` receives empty array from `doc.collections`
- Returns empty array `[]`
- Getter filters empty array → returns `[]`
- **Result:** Empty array `[]` (not error, not null)

### 6.2 Failed Conformance Check

**Scenario:** `hasConnectedSystems` resolves to `false`

**Handling:**

- Getter line 2: `hasCSAPI ? data : { collections: [] }`
- Returns empty collections document
- `parseCollections()` processes empty array
- **Result:** Empty array `[]`

### 6.3 Missing itemType/featureType

**Scenario:** Collection has no `itemType` or `featureType` property

**Handling:**

- Detection checks: `if (collection.featureType && ...)`
- Undefined values skip the check (no error)
- `hasConnectedSystems` not set on result object
- Filter excludes this collection (undefined !== true)
- **Result:** Collection not included in results

### 6.4 Malformed Properties

**Scenario:** `itemType` or `featureType` is not a string

**Handling:**

- Type guard: `typeof collection.featureType === 'string'`
- Non-string values skip the check
- **Result:** Collection not included in results

### 6.5 HTTP Failures

**Scenario:** `/collections` endpoint returns 404 or error

**Handling:**

- Handled upstream by `this.data` Promise
- `OgcApiEndpoint` class manages HTTP errors
- Getter receives rejected Promise, error propagates
- **Result:** Promise rejection (caller handles error)

### 6.6 Conservative Approach

**Philosophy:**

- Never assume CSAPI support - require explicit indicators
- Empty array is safer than false positives
- Let upstream HTTP handling deal with network errors
- No throwing from filter logic - just skip problematic collections

---

## 7. Testing Strategy

### 7.1 Unit Tests (info.spec.ts)

**Test File:** `src/ogc-api/info.spec.ts`  
**Function Under Test:** `parseCollections()`

**Test Cases:**

**Test 1: Part 1 System Collection (featureType)**

```typescript
test('parseCollections identifies Part 1 System collections', () => {
  const doc = {
    collections: [
      {
        id: 'weather-systems',
        featureType: 'http://www.w3.org/ns/sosa/System',
        links: [],
        // ... other required properties
      },
    ],
  };

  const result = parseCollections(doc);
  expect(result[0].hasConnectedSystems).toBe(true);
  expect(result[0].name).toBe('weather-systems');
});
```

**Test 2: Part 1 Property Collection (itemType)**

```typescript
test('parseCollections identifies Part 1 Property collections', () => {
  const doc = {
    collections: [
      {
        id: 'observableproperties',
        itemType: 'http://www.w3.org/ns/sosa/Property',
        links: [],
      },
    ],
  };

  const result = parseCollections(doc);
  expect(result[0].hasConnectedSystems).toBe(true);
});
```

**Test 3: Part 2 DataStream Collection**

```typescript
test('parseCollections identifies Part 2 DataStream collections', () => {
  const doc = {
    collections: [
      {
        id: 'sensor-datastreams',
        itemType: 'DataStream',
        links: [],
      },
    ],
  };

  const result = parseCollections(doc);
  expect(result[0].hasConnectedSystems).toBe(true);
});
```

**Test 4: Non-CSAPI Collection**

```typescript
test('parseCollections does not mark non-CSAPI collections', () => {
  const doc = {
    collections: [
      {
        id: 'buildings',
        itemType: 'feature',
        links: [],
      },
    ],
  };

  const result = parseCollections(doc);
  expect(result[0].hasConnectedSystems).toBeUndefined();
  expect(result[0].hasFeatures).toBe(true);
});
```

**Test 5: Empty Collections**

```typescript
test('parseCollections handles empty collections array', () => {
  const doc = { collections: [] };
  const result = parseCollections(doc);
  expect(result).toEqual([]);
});
```

**Test 6: Missing Properties**

```typescript
test('parseCollections handles missing itemType/featureType', () => {
  const doc = {
    collections: [
      {
        id: 'unknown',
        links: [],
        // no itemType or featureType
      },
    ],
  };

  const result = parseCollections(doc);
  expect(result[0].hasConnectedSystems).toBeUndefined();
});
```

### 7.2 Integration Tests (endpoint.spec.ts)

**Test File:** `src/ogc-api/endpoint.spec.ts`  
**Property Under Test:** `csapiCollections` getter

**Test 1: Returns CSAPI Collections When Conformance True**

```typescript
describe('#csapiCollections', () => {
  test('returns CSAPI collection IDs when server supports CSAPI', async () => {
    const endpoint = new OgcApiEndpoint('https://api.example.org');
    // Mock hasConnectedSystems = true
    // Mock collections with CSAPI types

    await expect(endpoint.csapiCollections).resolves.toEqual([
      'weather-systems',
      'sensor-datastreams',
    ]);
  });
});
```

**Test 2: Returns Empty Array When No Conformance**

```typescript
test('returns empty array when server lacks CSAPI conformance', async () => {
  const endpoint = new OgcApiEndpoint('https://api.example.org');
  // Mock hasConnectedSystems = false

  await expect(endpoint.csapiCollections).resolves.toEqual([]);
});
```

**Test 3: Filters Non-CSAPI Collections**

```typescript
test('filters out non-CSAPI collections', async () => {
  const endpoint = new OgcApiEndpoint('https://api.example.org');
  // Mock hasConnectedSystems = true
  // Mock mixed collections (CSAPI + non-CSAPI)

  await expect(endpoint.csapiCollections).resolves.toEqual([
    'weather-systems', // only CSAPI collection
  ]);
});
```

### 7.3 Fixture Requirements

**Create Test Fixtures:**

- `fixtures/ogc-api/csapi-collections.json` - Sample collections with CSAPI types
- Include Part 1 System, Deployment examples
- Include Part 2 DataStream, Observation examples
- Include mixed CSAPI + non-CSAPI collections

**Example Fixture Structure:**

```json
{
  "collections": [
    {
      "id": "weather-systems",
      "title": "Weather Systems",
      "featureType": "http://www.w3.org/ns/sosa/System",
      "links": []
    },
    {
      "id": "sensor-datastreams",
      "title": "Sensor Data Streams",
      "itemType": "DataStream",
      "links": []
    },
    {
      "id": "buildings",
      "title": "Buildings",
      "itemType": "feature",
      "links": []
    }
  ]
}
```

---

## 8. Implementation Checklist

### Phase 1: Extend parseCollections Function (2 hours)

**File:** `src/ogc-api/info.ts`

1. **Add Return Type Property** (5 min)

   - [ ] Locate return type annotation (~line 229)
   - [ ] Add `hasConnectedSystems?: boolean` to return type object
   - [ ] Verify TypeScript compiles

2. **Add featureType Check** (30 min)

   - [ ] Locate insertion point (~line 260, after itemType checks)
   - [ ] Add featureType detection if-block (~4 lines)
   - [ ] Verify logic: check exists, is string, includes 'sosa'
   - [ ] Set `result.hasConnectedSystems = true`

3. **Add itemType CSAPI Check** (30 min)

   - [ ] Add second if-block after featureType check (~5 lines)
   - [ ] Verify logic: check exists, is string
   - [ ] Check for sosa OR Part 2 type names
   - [ ] Set `result.hasConnectedSystems = true`

4. **Run Linting** (5 min)

   - [ ] Run `npm run lint`
   - [ ] Fix any formatting issues
   - [ ] Verify no TypeScript errors

5. **Manual Testing** (30 min)
   - [ ] Create test document with CSAPI collection
   - [ ] Call `parseCollections()` directly
   - [ ] Verify `hasConnectedSystems` flag set correctly
   - [ ] Test with Part 1 and Part 2 types

### Phase 2: Add csapiCollections Getter (1 hour)

**File:** `src/ogc-api/endpoint.ts`

1. **Add Getter** (20 min)

   - [ ] Locate insertion point (~line 210, after `edrCollections`)
   - [ ] Add JSDoc comment
   - [ ] Add getter signature
   - [ ] Implement Promise.all pattern (copy from EDR, modify names)

2. **Verify Integration** (20 min)

   - [ ] Confirm `hasConnectedSystems` imported/accessible (from Component 2)
   - [ ] Confirm `parseCollections` imported (already should be)
   - [ ] Run TypeScript compiler
   - [ ] Fix any type errors

3. **Run Linting** (5 min)

   - [ ] Run `npm run lint`
   - [ ] Fix formatting

4. **Manual Testing** (15 min)
   - [ ] Create test endpoint instance
   - [ ] Mock conformance and collections data
   - [ ] Call `csapiCollections` getter
   - [ ] Verify returns array of collection IDs

### Phase 3: Unit Tests (2 hours)

**File:** `src/ogc-api/info.spec.ts`

1. **Write Test Cases** (1.5 hours)

   - [ ] Test 1: Part 1 System collection (featureType)
   - [ ] Test 2: Part 1 Property collection (itemType with sosa)
   - [ ] Test 3: Part 2 DataStream collection (itemType without sosa)
   - [ ] Test 4: Non-CSAPI collection (should not have flag)
   - [ ] Test 5: Empty collections array
   - [ ] Test 6: Missing itemType/featureType properties

2. **Run Tests** (30 min)
   - [ ] Run `npm test -- info.spec.ts`
   - [ ] Debug any failures
   - [ ] Verify all tests pass

### Phase 4: Integration Tests (2 hours)

**File:** `src/ogc-api/endpoint.spec.ts`

1. **Create Test Fixtures** (30 min)

   - [ ] Create `fixtures/ogc-api/csapi-collections.json`
   - [ ] Add CSAPI collections (Part 1 and Part 2)
   - [ ] Add non-CSAPI collections (for filtering tests)

2. **Write Test Cases** (1 hour)

   - [ ] Test 1: Returns CSAPI collections when conformance true
   - [ ] Test 2: Returns empty array when no conformance
   - [ ] Test 3: Filters out non-CSAPI collections
   - [ ] Mock `hasConnectedSystems` appropriately

3. **Run Tests** (30 min)
   - [ ] Run `npm test -- endpoint.spec.ts`
   - [ ] Debug any failures
   - [ ] Verify all tests pass

### Phase 5: Validation & Documentation (1 hour)

1. **Run Full Test Suite** (20 min)

   - [ ] Run `npm test`
   - [ ] Verify no regressions in existing tests
   - [ ] Check code coverage (should be >80%)

2. **Verify Integration** (20 min)

   - [ ] Test Component 2 integration (conformance check)
   - [ ] Test with real CSAPI endpoint (if available)
   - [ ] Verify getter works end-to-end

3. **Code Review** (20 min)
   - [ ] Review code against EDR pattern
   - [ ] Verify follows existing style
   - [ ] Check for edge cases
   - [ ] Verify error handling

### Estimated Timeline

- **Phase 1:** 2 hours (parseCollections extension)
- **Phase 2:** 1 hour (getter implementation)
- **Phase 3:** 2 hours (unit tests)
- **Phase 4:** 2 hours (integration tests)
- **Phase 5:** 1 hour (validation & docs)
- **Total:** ~8 hours (1 day)

---

## 9. Dependencies

### 9.1 Depends On

**Component 2 (Conformance Reader):**

- Provides `hasConnectedSystems` getter
- Used in `csapiCollections` getter to check CSAPI support
- Without conformance check, would return all collections

**Existing Infrastructure:**

- `parseCollections()` function exists - we extend it
- `this.data` property exists - provides collections data
- Pattern established by EDR (`edrCollections` getter)

### 9.2 Required By

**Component 1 (OgcApiEndpoint Integration):**

- Factory method may use `csapiCollections` to validate collection ID
- Optional: Check if collection ID is in `csapiCollections` before creating QueryBuilder

**Component 4 (CSAPIQueryBuilder):**

- Developers use `csapiCollections` to discover available collections
- Essential for user experience - shows what's available

### 9.3 Integration Example

```typescript
// Component 2 provides conformance check
if (!this.hasConnectedSystems) {
  // No CSAPI support
}

// Component 3 provides collection filtering
const collections = await this.csapiCollections;
// ['weather-systems', 'sensor-datastreams']

// Component 1 uses collection ID
const csapi = await this.csapi('weather-systems');

// Component 4 provides query building
const url = csapi.getSystems();
```

---

## 10. Key Design Decisions

### Decision 1: Check Both itemType AND featureType

**Rationale:**

- Part 1 Feature resources use `featureType` (System, Deployment, Procedure, Sample)
- Part 1 non-Feature resources use `itemType` (Property)
- Part 2 resources use `itemType` (DataStream, Observation, etc.)
- Must check both properties to catch all CSAPI collections

**Alternative Considered:** Only check `itemType`

- **Rejected:** Would miss Part 1 Feature resources (System, Deployment, etc.)

### Decision 2: Use .includes('sosa') for featureType

**Rationale:**

- Handles both short form (`sosa:System`) and full URI (`http://www.w3.org/ns/sosa/System`)
- Future-proof for URI format variations
- All Part 1 Feature resources use SOSA namespace
- Simple and reliable

**Alternative Considered:** Exact string matching

- **Rejected:** Too fragile, requires knowing exact URI format

### Decision 3: Explicit Part 2 Type Names

**Rationale:**

- Part 2 uses short names without full URIs
- `DataStream`, `Observation`, `ControlStream`, etc.
- More specific prevents false positives
- Matches spec requirements exactly

**Alternative Considered:** Pattern matching or includes()

- **Rejected:** Could match unintended strings

### Decision 4: Extend parseCollections Instead of New Function

**Rationale:**

- Follows established pattern (Records, Features, Tiles, EDR all use same function)
- Single pass through collections array (efficient)
- Consistent with library architecture
- No new function exports needed

**Alternative Considered:** Create separate `parseCSAPICollections()` function

- **Rejected:** Violates library patterns, less efficient

### Decision 5: Return Empty Array on No Conformance

**Rationale:**

- Conservative approach - don't process collections if no CSAPI support
- Matches EDR pattern exactly
- Prevents wasted work parsing non-CSAPI collections
- Clear signal to caller (empty = none available)

**Alternative Considered:** Process all collections anyway

- **Rejected:** Wastes resources, could return false positives

### Decision 6: No Type Changes to OgcApiCollectionInfo

**Rationale:**

- `itemType` already optional, accepts any string at runtime
- Changing type would affect existing code
- Detection logic works with runtime values
- TypeScript types don't prevent additional string values

**Alternative Considered:** Add `itemType?: string` or union type

- **Rejected:** Breaking change, unnecessary complexity

---

## Development Standards

All implementation work for Component 3 must adhere to the project's [Development Standards](../../../planning/csapi-implementation-guide.md#development-standards) defined in the CSAPI Implementation Guide.

### Key Standards for This Component

**Development Workflow:**

1. Write function signatures before implementation (done in this analysis)
2. Add comprehensive JSDoc comments with parameters, return types
3. Implement functionality following EDR pattern exactly
4. Write tests as you implement (not deferred to later)
5. Document edge cases and validation rules as discovered

**Code Quality Requirements:**

- TypeScript strict mode enabled
- 100% public API JSDoc coverage (add JSDoc to `csapiCollections` getter)
- > 80% test coverage (statement and branch)
- Lint-clean code (ESLint configuration)
- No magic strings (CSAPI type names should be constants if reused)
- Consistent error handling patterns (return empty array, never throw from filter logic)

**Documentation Requirements:**

- Clear, concise method descriptions
- Parameter descriptions with types and constraints
- Return type documentation
- Error condition documentation
- Links to relevant CSAPI specification sections

**Testing Requirements:**

- Test positive cases (Part 1 System, Part 2 DataStream, etc.)
- Test negative cases (non-CSAPI collections, empty arrays)
- Test edge cases (undefined, null, malformed properties)
- Use fixtures from fixtures/ogc-api/ directory

---

## Summary

Component 3 (Collections Reader) is a **straightforward extension** requiring **~15 lines of code** across two functions. The implementation follows the exact pattern established by EDR collection filtering, with the key difference being the need to check BOTH `itemType` AND `featureType` properties to catch all CSAPI collection types.

**Ready for Implementation:** ✅ All specifications complete, no outstanding questions.

**Next Steps:** Proceed to implementation following the checklist in Section 8.
