# Research Plan 01: PR #114 EDR Pattern Analysis - FINDINGS

**Research Completed:** February 4, 2026  
**Source Document:** [docs/research/upstream/pr114-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md)  
**Researcher:** GitHub Copilot

---

## Executive Summary

**CRITICAL FINDING:** PR #114 definitively uses a **single `EDRQueryBuilder` class** pattern for all 7 query types. This establishes upstream's clear expectation for consolidated QueryBuilder implementations.

**Key Metrics:**

- **Single class:** `EDRQueryBuilder` (561 lines)
- **Method count:** 7 primary URL building methods (one per query type)
- **Total implementation:** ~750 lines (including types and helpers)
- **Integration complexity:** 115 lines across 4 core files
- **Test coverage:** ~375 lines of tests

**Architecture Decision Impact:** This **strongly favors** the single CSAPIQueryBuilder class approach. Deviation from this pattern risks PR rejection.

---

## Detailed Findings

### 1. Class Organization: Single Consolidated Class ✅

**Finding:** EDR uses ONE `EDRQueryBuilder` class in `src/ogc-api/edr/url_builder.ts` (561 lines).

**Evidence:**

```typescript
export default class EDRQueryBuilder {
  // Constructor with metadata encapsulation
  constructor(private collection: OgcApiCollectionInfo) {
    // Validates and stores collection metadata
  }

  // 7 query type methods:
  buildAreaDownloadUrl(coords, params);
  buildLocationsDownloadUrl(locationId, params);
  buildCubeDownloadUrl(bbox, params);
  buildTrajectoryDownloadUrl(coords, params);
  buildCorridorDownloadUrl(coords, params);
  buildRadiusDownloadUrl(coords, params);
  buildPositionDownloadUrl(coords, params);

  // Plus helper getters and validation methods
}
```

**Method Organization:**

- Each query type has ONE dedicated method
- Methods are ~50-80 lines each
- Organized sequentially (not by sections/comments)
- No sub-classes or helper classes for query types

**Scalability Evidence:**

- 7 query types handled successfully in single class
- No signs of code bloat or maintainability issues
- Clean, readable implementation
- Each method follows identical pattern

---

### 2. Integration Pattern: Minimal Core Modifications ✅

**Factory Method Signature in `endpoint.ts`:**

```typescript
export default class OgcApiEndpoint {
  // Caching map (private property)
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();

  // Factory method (public async)
  public async edr(collection_id: string): Promise<EDRQueryBuilder> {
    if (!this.hasEnvironmentalDataRetrieval) {
      throw new EndpointError('Endpoint does not support EDR');
    }
    const cache = this.collection_id_to_edr_builder_;
    if (cache.has(collection_id)) {
      return cache.get(collection_id); // Return cached instance
    }
    const collection = await this.getCollectionInfo(collection_id);
    const result = new EDRQueryBuilder(collection);
    cache.set(collection_id, result); // Cache new instance
    return result;
  }
}
```

**Caching Implementation:**

- Map-based cache: `Map<string, EDRQueryBuilder>`
- Key: collection_id (string)
- Value: EDRQueryBuilder instance
- Pattern: Check cache → Return cached OR fetch+create+cache

**Files Modified for Integration:**

1. **endpoint.ts** (+43 lines)

   - Factory method: `edr(collection_id)`
   - Getter: `edrCollections`
   - Cache property: `collection_id_to_edr_builder_`

2. **info.ts** (+16 lines)

   - Conformance checker: `checkHasEnvironmentalDataRetrieval()`
   - Returns boolean based on conformance class presence

3. **model.ts** (+47 lines)

   - Type: `DataQueryType` (union of 7 query types)
   - Interface extensions: `OgcApiCollectionInfo.data_queries`
   - Helper type: `EdrParameterInfo`

4. **link-utils.ts** (+9 lines)
   - Type signature updates to support OgcApiCollectionInfo

**Total Integration LOC:** 115 lines across 4 files

---

### 3. Conformance Checking Pattern ✅

**Implementation in `info.ts`:**

```typescript
export function checkHasEnvironmentalDataRetrieval([conformance]: [
  ConformanceClass[]
]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core'
    ) > -1
  );
}
```

**Pattern:**

- Single function that checks for conformance class URI
- Boolean return (endpoint supports EDR or not)
- Used by `hasEnvironmentalDataRetrieval` getter

**Conformance Class Checked:**

- `http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core`

**CSAPI Equivalent:**

```typescript
export function checkHasConnectedSystems([conformance]: [ConformanceClass[]]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1
  );
}
```

---

### 4. Method Organization Strategy ✅

**Pattern Analysis:**

Each URL building method follows this exact structure:

```typescript
build[QueryType]DownloadUrl(
  requiredParams,
  optional_params: Optional[QueryType]Params = {}
): string {
  // 1. GUARD: Check if query type is supported
  if (!this.supported_query_types.[queryType]) {
    throw new Error('Collection does not support [queryType] queries');
  }

  // 2. BASE URL: Extract from collection metadata
  const url = new URL(this.collection.data_queries?.[queryType]?.link.href);

  // 3. REQUIRED PARAMS: Set mandatory parameters
  url.searchParams.set('coords', coords); // or similar

  // 4. OPTIONAL PARAMS: Set with validation
  if (optional_params.z !== undefined)
    url.searchParams.set('z', zParameterToString(optional_params.z));
  if (optional_params.datetime !== undefined)
    url.searchParams.set('datetime', DateTimeParameterToEDRString(optional_params.datetime));
  if (optional_params.parameter_name) {
    // Validate parameter exists
    for (const param of optional_params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(`Parameter '${param}' does not exist`);
      }
    }
    url.searchParams.set('parameter-name', optional_params.parameter_name.join(','));
  }
  // ... more optional params

  // 5. RETURN: Built URL string
  return url.toString();
}
```

**Method Count:** 7 primary methods (one per query type)

**Grouping Strategy:**

- NO section comments or visual separators
- Methods appear sequentially in file
- Each method is self-contained
- Pattern repetition provides consistency

**Helper Methods:**

- `supported_queries` getter (returns Set of enabled query types)
- Constructor (validation and metadata storage)
- No helper methods for URL building (all inline)

---

### 5. Code Volume and Scalability ✅

**Breakdown:**

| Category           | Lines  | Files |
| ------------------ | ------ | ----- |
| **Implementation** | 750    | 3     |
| - url_builder.ts   | 561    | 1     |
| - model.ts         | 125    | 1     |
| - helpers.ts       | 23     | 1     |
| - Integration      | 115    | 4     |
| **Tests**          | 375    | 3     |
| - endpoint.spec.ts | 298    | 1     |
| - model.spec.ts    | 38     | 1     |
| - helpers.spec.ts  | 39     | 1     |
| **Fixtures**       | 1,700+ | 8     |
| **TOTAL**          | ~2,800 | 18    |

**Scalability Analysis:**

EDR: 7 query types → 561-line QueryBuilder

- **Per-type average:** 80 lines/query type
- **Efficiency:** High code reuse, minimal duplication

CSAPI Projection: 9 resource types → ~720 lines (9 × 80)

- **BUT:** CSAPI has nested resources (System → Datastream → Observations)
- **Complexity multiplier:** Sub-resources add ~20-30% overhead
- **Realistic estimate:** 850-950 lines for CSAPIQueryBuilder

**Maintainability Evidence:**

- Clear method boundaries
- Consistent patterns reduce cognitive load
- No signs of "God object" anti-pattern
- Single class easier to understand than 9 separate files

---

### 6. Testing Strategy Pattern ✅

**Test Categories (from endpoint.spec.ts):**

1. **Conformance Detection** (2 tests)

   ```typescript
   it('supports EDR', async () => {
     await expect(endpoint.hasEnvironmentalDataRetrieval).resolves.toBe(true);
   });
   ```

2. **Collection Listing** (1 test)

   ```typescript
   it('can list all the EDR collections', async () => {
     await expect(endpoint.edrCollections).resolves.toEqual(['reservoir-api']);
   });
   ```

3. **Builder Instantiation** (2 tests)

   ```typescript
   it('can produce a EDR query builder', async () => {
     const builder = await endpoint.edr('reservoir-api');
     expect(builder).toBeTruthy();
     expect(builder.supported_queries).toEqual(
       new Set(['area', 'locations', 'cube'])
     );
   });
   ```

4. **Caching Behavior** (1 test)

   ```typescript
   it('caches properly', async () => {
     const spy = jest.spyOn(endpoint, 'getCollectionInfo');
     const builder1 = await endpoint.edr('reservoir-api');
     const builder2 = await endpoint.edr('reservoir-api');
     expect(builder1).toBe(builder2); // Same instance
     expect(spy).toHaveBeenCalledTimes(1); // Fetched once
   });
   ```

5. **URL Building** (5+ tests per query type)

   ```typescript
   it('can produce EDR area queries with or without optional parameters', async () => {
     const builder = await endpoint.edr('reservoir-api');
     const urlNoParams = builder.buildAreaDownloadUrl('POLYGON(...)');
     const urlWithParams = builder.buildAreaDownloadUrl('POLYGON(...)', {
       parameter_name: ['Water Temperature'],
     });
     expect(urlNoParams).toEqual('...');
     expect(urlWithParams).toContain('parameter-name=Water+Temperature');
   });
   ```

6. **Error Handling** (2+ tests per query type)
   ```typescript
   it('throws an error when called with invalid parameter', async () => {
     const builder = await endpoint.edr('reservoir-api');
     expect(() =>
       builder.buildAreaDownloadUrl('POLYGON(...)', {
         parameter_name: ['BadParam'],
       })
     ).toThrow();
   });
   ```

**Test Organization:**

- Nested describe blocks by functionality
- One `beforeEach` for endpoint setup
- Async/await for Promise-based API
- Jest matchers: `resolves`, `toEqual`, `toThrow`, `toContain`

**CSAPI Test Projection:**

- 9 resource types (vs. 7 query types)
- More complex parameter combinations
- Sub-resource navigation tests
- **Estimated:** 400-500 lines of tests

---

## Architecture Decision Implications

### Strong Evidence for Single-Class Pattern

**Reasons:**

1. **Upstream Precedent:** EDR sets clear expectation

   - PR #114 was accepted and merged
   - Pattern proven at scale (7 types)
   - No modifications requested to split into multiple classes

2. **Scalability Proven:**

   - 561 lines for 7 types is manageable
   - CSAPI estimate: ~850-950 lines for 9 types
   - Well within maintainable range (<1,500 lines)

3. **Integration Simplicity:**

   - Single factory method: `endpoint.csapi(collection_id)`
   - Single cache: `Map<string, CSAPIQueryBuilder>`
   - Minimal core modifications

4. **Consistency Benefits:**

   - All resources accessed through one API
   - Uniform pattern for all URL building
   - Single point of documentation

5. **Testing Benefits:**
   - One test suite structure
   - Consistent test patterns
   - Easier to ensure complete coverage

### Risks of Deviating (Multiple Classes)

1. **PR Rejection Risk:** HIGH

   - Pattern inconsistency with accepted EDR implementation
   - More files to review
   - Breaks established conventions

2. **Integration Complexity:**

   - Multiple factory methods: `endpoint.systems()`, `endpoint.datastreams()`, etc.
   - Multiple caches or complex cache structure
   - More core file modifications

3. **User Experience:**

   - Multiple APIs to learn
   - Inconsistent patterns across resources
   - Harder to discover capabilities

4. **Maintenance Burden:**
   - 9+ files vs. 1 file
   - Code duplication across classes
   - Inconsistent updates/refactoring

---

## Open Questions & Considerations

### Q1: Sub-Resource Navigation Pattern

**Issue:** CSAPI has nested resources (System → Datastream → Observations)

**EDR has no equivalent** (all query types are flat)

**Options:**

1. **Flat methods** (EDR style):

   ```typescript
   buildSystemsUrl(params);
   buildSystemUrl(systemId);
   buildSystemDatastreamsUrl(systemId, params);
   buildSystemDatastreamObservationsUrl(systemId, datastreamId, params);
   ```

2. **Hierarchical chaining** (alternative):
   ```typescript
   systems(params);
   system(id).datastreams();
   system(id).datastream(id).observations();
   ```

**Recommendation:** Research other OGC API implementations for nested resource patterns. Likely need to stay with flat methods to maintain consistency with EDR pattern.

### Q2: Collection vs. Top-Level Resources

**EDR Pattern:** Collection-scoped

```typescript
endpoint.edr('reservoir-api').buildAreaDownloadUrl(...)
```

**CSAPI Question:** Are resources collection-scoped or top-level?

**Action Needed:** Review CSAPI OpenAPI specs (plans 21-22) to determine resource hierarchy.

### Q3: Method Count Estimate

**EDR:** 7 query types → 7 methods

**CSAPI Calculation:**

- 9 resource types (Systems, Deployments, etc.)
- Each resource: ~5 operations (list, get, create, update, delete)
- Sub-resources: ~15 additional patterns (e.g., System → Procedures)
- **Total:** ~60 methods estimated

**Validation Needed:** Count actual endpoint patterns from OpenAPI specs (plans 17-18, 21-22).

---

## Synthesis for Final Recommendations

### Pattern Confirmed: Single `CSAPIQueryBuilder` Class

**Evidence Strength:** CRITICAL

**Key Findings:**

1. ✅ EDR uses single class (561 lines, 7 types)
2. ✅ Pattern is scalable (CSAPI projection: 850-950 lines, 9 types)
3. ✅ Integration is minimal (115 lines, 4 files)
4. ✅ Testing is straightforward (375 lines, proven patterns)
5. ✅ Caching pattern is elegant (Map-based, built-in)
6. ✅ Method organization is clear (sequential, consistent)

**Architecture Decision:** **STRONGLY RECOMMEND** single CSAPIQueryBuilder class following EDR pattern exactly.

**Next Steps:**

1. Analyze QueryBuilder pattern fundamentals (plan 02)
2. Review upstream expectations (plan 10)
3. Validate against previous architectural decisions (plan 03)
4. Compare with OWSLib's separate-class pattern (plan 05)

**Risk Assessment:**

- **Following EDR pattern:** LOW risk (proven, accepted)
- **Deviating to separate classes:** HIGH risk (PR rejection, inconsistency)

---

**STATUS:** ✅ COMPLETE - Ready for synthesis
