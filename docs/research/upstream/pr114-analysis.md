# PR #114 (EDR Implementation) Analysis

**Date:** 2026-01-30  
**Status:** CRITICAL RESEARCH - FOUNDATION FOR CSAPI IMPLEMENTATION  
**PR:** camptocamp/ogc-client#114 (merged 2025-08-29)

## Executive Summary

PR #114 adds OGC API - Environmental Data Retrieval (EDR) support. This is our **direct blueprint** for CSAPI implementation.

### Critical Discovery: Terminology Resolution

**QUESTION RESOLVED:** What does PR #114 call the object returned by `endpoint.edr()`?

**ANSWER:** `EDRQueryBuilder` (NOT "navigator")

```typescript
// From app/examples/edr.ts:
const edr_builder = await api.edr(collection);

// From src/ogc-api/endpoint.ts:
public async edr(collection_id: string): Promise<EDRQueryBuilder> {
  // ...
  const result = new EDRQueryBuilder(collection);
  return result;
}
```

**IMPLICATION:** For CSAPI, we will use `CSAPIQueryBuilder` (following the exact pattern).

---

## Code Volume Metrics

**Total Changes:**

- **2858 additions**
- **54 deletions**
- **18 files changed**
- **43 commits** (squashed)

**Net Addition:** ~2800 lines (including tests and fixtures)

**Breakdown by Category:**

1. **Implementation:** ~750 lines
   - `url_builder.ts`: 561 lines (main builder class)
   - `model.ts`: 125 lines (types and helpers)
   - `helpers.ts`: 23 lines (date formatting)
   - `endpoint.ts`: 43 lines (integration)
2. **Tests:** ~375 lines
   - `endpoint.spec.ts`: 298 lines (integration tests)
   - `model.spec.ts`: 38 lines (ZParameter tests)
   - `helpers.spec.ts`: 39 lines (datetime tests)
3. **Fixtures:** ~1700 lines (test data JSON files)

**Code Volume Assessment for CSAPI:**

- **PR #114 baseline:** ~2800 lines total
- **Fixture ratio:** 61% fixtures, 27% implementation, 13% tests
- **Implementation-only:** ~750 lines for 7 query types
- **CSAPI projection:**
  - 9 CSAPI resource types ≈ 1.3x EDR query types
  - Expected implementation: ~975 lines (1.3x × 750)
  - With tests & fixtures: ~3500 lines total
  - **Target:** Stay under 4000 lines total

**Comparison to Original Concern:**

- Previous CSAPI attempt was "2x upstream repo size"
- Upstream repo is ~8500 lines (from PR metadata)
- PR #114 is 2800 lines (~33% of upstream)
- CSAPI at 3500 lines would be ~41% of upstream
- **Verdict:** Acceptable if we follow EDR patterns closely

---

## File Organization

### New Files Created

**Implementation Files (3):**

```
src/ogc-api/edr/
├── url_builder.ts      (561 lines) - Main query builder class
├── model.ts            (125 lines) - TypeScript types & helpers
└── helpers.ts          (23 lines)  - Date/time formatting utilities
```

**Test Files (3):**

```
src/ogc-api/edr/
├── helpers.spec.ts     (39 lines)  - Helper function tests
└── model.spec.ts       (38 lines)  - Model serialization tests

src/ogc-api/
└── endpoint.spec.ts    (+298 lines) - Integration tests
```

**Example Files (1):**

```
app/examples/
└── edr.ts             (28 lines)  - Usage demonstration
```

**Fixture Files (8):**

```
fixtures/ogc-api/edr/
├── sample-data-hub.json
├── sample-data-hub/
│   ├── collections.json            (715 lines)
│   ├── conformance.json            (22 lines)
│   ├── reservoir-api.json          (194 lines)
│   └── collections/
│       └── reservoir-api.json      (574 lines)
```

**Modified Files (3):**

```
src/ogc-api/
├── endpoint.ts         (+43 lines)  - Add edr() method
├── info.ts             (+16 lines)  - Add EDR conformance check
├── model.ts            (+47 lines)  - Add DataQueryType, EdrParameterInfo
└── link-utils.ts       (+9 lines)   - Support OgcApiCollectionInfo
```

**CSAPI Mapping:**

```
src/ogc-api/csapi/
├── url_builder.ts      (~600 lines estimated)
├── model.ts            (~150 lines estimated)
├── helpers.ts          (~50 lines estimated)
├── helpers.spec.ts     (~50 lines estimated)
└── model.spec.ts       (~50 lines estimated)

src/ogc-api/
└── endpoint.spec.ts    (+400 lines estimated)
```

---

## Architecture Pattern

### 1. Main Class: `EDRQueryBuilder`

**Location:** `src/ogc-api/edr/url_builder.ts`

**Constructor Pattern:**

```typescript
export default class EDRQueryBuilder {
  private supported_query_types: {
    area: boolean;
    locations: boolean;
    cube: boolean;
    trajectory: boolean;
    corridor: boolean;
    radius: boolean;
    position: boolean;
    instances: boolean;
  };

  public supported_parameters: Record<string, EdrParameterInfo> = {};
  public supported_crs: CrsCode[] = [];
  public links: OgcApiDocumentLink[] = [];

  constructor(private collection: OgcApiCollectionInfo) {
    if (!collection.data_queries) {
      throw new Error('No data queries found, so cannot issue EDR queries');
    }
    this.supported_query_types = {
      area: collection.data_queries.area !== undefined,
      // ... etc
    };
    this.supported_parameters = collection.parameter_names;
    this.supported_crs = collection.crs;
    this.links = collection.links;
  }

  // Getter for supported queries
  get supported_queries(): Set<DataQueryType> {
    const queries: Set<DataQueryType> = new Set();
    for (const [key, value] of Object.entries(this.supported_query_types)) {
      if (value) queries.add(key as DataQueryType);
    }
    return queries;
  }
}
```

**CSAPI Pattern:**

```typescript
export default class CSAPIQueryBuilder {
  private supported_resource_types: {
    systems: boolean;
    procedures: boolean;
    deployments: boolean;
    samplingFeatures: boolean;
    properties: boolean;
    datastreams: boolean;
    observations: boolean;
    controlStreams: boolean;
    commands: boolean;
  };

  public collection: OgcApiCollectionInfo;
  public links: OgcApiDocumentLink[] = [];

  constructor(private collection: OgcApiCollectionInfo) {
    // Similar validation pattern
  }
}
```

### 2. Endpoint Integration

**Pattern from `endpoint.ts`:**

```typescript
export default class OgcApiEndpoint {
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();

  get edrCollections(): Promise<string[]> {
    return Promise.all([this.data, this.hasEnvironmentalDataRetrieval])
      .then(([data, hasEDR]) => (hasEDR ? data : { collections: [] }))
      .then(parseCollections)
      .then((collections) => collections.filter((c) => c.hasDataQueries))
      .then((collections) => collections.map((collection) => collection.name));
  }

  get hasEnvironmentalDataRetrieval(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasEnvironmentalDataRetrieval
    );
  }

  public async edr(collection_id: string): Promise<EDRQueryBuilder> {
    if (!this.hasEnvironmentalDataRetrieval) {
      throw new EndpointError('Endpoint does not support EDR');
    }
    const cache = this.collection_id_to_edr_builder_;
    if (cache.has(collection_id)) {
      return cache.get(collection_id);
    }
    const collection = await this.getCollectionInfo(collection_id);
    const result = new EDRQueryBuilder(collection);
    cache.set(collection_id, result);
    return result;
  }
}
```

**CSAPI Pattern:**

```typescript
export default class OgcApiEndpoint {
  private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =
    new Map();

  get csapiCollections(): Promise<string[]> {
    // Similar pattern
  }

  get hasConnectedSystems(): Promise<boolean> {
    // Check for CSAPI conformance classes
  }

  public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
    // Identical caching pattern
  }
}
```

**KEY INSIGHT:** Caching pattern prevents redundant collection info fetches.

### 3. Conformance Detection

**From `info.ts`:**

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

**CSAPI Pattern:**

```typescript
export function checkHasConnectedSystems([conformance]: [ConformanceClass[]]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1
  );
}
```

**NOTE:** Must verify exact conformance class URI from CSAPI spec.

### 4. Type Extensions

**From `model.ts`:**

```typescript
export const DataQueryTypes = [
  'items',
  'locations',
  'cube',
  'area',
  'trajectory',
  'radius',
  'corridor',
  'position',
  'instances',
] as const;

export type DataQueryType = (typeof DataQueryTypes)[number];

export interface OgcApiCollectionInfo {
  // ... existing props

  data_queries?: {
    [K in DataQueryType]?: {
      link: {
        href: string;
        rel: string;
      };
    };
  };
  parameter_names?: Record<string, EdrParameterInfo>;
}
```

**CSAPI Pattern:**

```typescript
export const CSAPIResourceTypes = [
  'systems',
  'procedures',
  'deployments',
  'samplingFeatures',
  'properties',
  'datastreams',
  'observations',
  'controlStreams',
  'commands',
] as const;

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

export interface OgcApiCollectionInfo {
  // ... existing props

  csapi_resources?: {
    [K in CSAPIResourceType]?: {
      link: {
        href: string;
        rel: string;
      };
    };
  };
}
```

---

## URL Building Pattern

### Method Signature Pattern

**From `url_builder.ts` (Example: Area Query):**

```typescript
buildAreaDownloadUrl(
  coords: WellKnownTextString,
  optional_params: optionalAreaParams = {}
): string {
  // 1. Check if query type is supported
  if (!this.supported_query_types.area) {
    throw new Error('Collection does not support area queries');
  }

  // 2. Create URL from collection metadata
  const url = new URL(this.collection.data_queries?.area?.link.href);

  // 3. Set required parameters
  url.searchParams.set('coords', coords);

  // 4. Set optional parameters with validation
  if (optional_params.z !== undefined)
    url.searchParams.set('z', zParameterToString(optional_params.z));
  if (optional_params.datetime !== undefined)
    url.searchParams.set(
      'datetime',
      DateTimeParameterToEDRString(optional_params.datetime)
    );
  if (optional_params.parameter_name) {
    for (const param of optional_params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(
          `The following parameter name does not exist on this collection: '${param}'.`
        );
      }
    }
    url.searchParams.set(
      'parameter-name',
      optional_params.parameter_name.join(',')
    );
  }
  if (optional_params.crs !== undefined) {
    if (!this.supported_crs.includes(optional_params.crs)) {
      throw new Error(
        `The following crs does not exist on this collection: '${optional_params.crs}'.`
      );
    }
    url.searchParams.set('crs', optional_params.crs);
  }
  if (optional_params.f !== undefined)
    url.searchParams.set('f', optional_params.f);

  // 5. Return built URL string
  return url.toString();
}
```

**CSAPI Pattern (Example: Systems Resource):**

```typescript
buildSystemsUrl(
  optional_params: SystemsParams = {}
): string {
  // 1. Check if resource type is supported
  if (!this.supported_resource_types.systems) {
    throw new Error('Collection does not support systems resource');
  }

  // 2. Create URL from collection metadata
  const url = new URL(this.collection.csapi_resources?.systems?.link.href);

  // 3. Set optional parameters (most CSAPI params are optional)
  if (optional_params.q !== undefined)
    url.searchParams.set('q', optional_params.q);
  if (optional_params.id !== undefined)
    url.searchParams.set('id', optional_params.id.join(','));
  if (optional_params.parent !== undefined)
    url.searchParams.set('parent', optional_params.parent);
  if (optional_params.keyword !== undefined)
    url.searchParams.set('keyword', optional_params.keyword.join(','));
  if (optional_params.procedure !== undefined)
    url.searchParams.set('procedure', optional_params.procedure);
  if (optional_params.foi !== undefined)
    url.searchParams.set('foi', optional_params.foi);
  if (optional_params.observedProperty !== undefined)
    url.searchParams.set('observedProperty', optional_params.observedProperty.join(','));
  if (optional_params.controlledProperty !== undefined)
    url.searchParams.set('controlledProperty', optional_params.controlledProperty.join(','));
  if (optional_params.validTime !== undefined)
    url.searchParams.set('validTime', formatDateTime(optional_params.validTime));
  if (optional_params.geom !== undefined)
    url.searchParams.set('geom', optional_params.geom);
  if (optional_params.datetime !== undefined)
    url.searchParams.set('datetime', formatDateTime(optional_params.datetime));
  if (optional_params.bbox !== undefined)
    url.searchParams.set('bbox', formatBBox(optional_params.bbox));
  if (optional_params.limit !== undefined)
    url.searchParams.set('limit', optional_params.limit.toString());
  if (optional_params.select !== undefined)
    url.searchParams.set('select', optional_params.select.join(','));
  if (optional_params.f !== undefined)
    url.searchParams.set('f', optional_params.f);

  // 4. Return built URL string
  return url.toString();
}
```

**KEY PATTERN ELEMENTS:**

1. **Guard clause:** Check resource type support first
2. **Base URL:** Extract from collection metadata
3. **Parameter validation:** Validate against collection metadata
4. **Parameter serialization:** Convert TypeScript types to URL-safe strings
5. **Error handling:** Throw descriptive errors for invalid params

---

## Testing Strategy

### Test File Structure

**Pattern from `endpoint.spec.ts`:**

```typescript
describe('OgcApiEndpoint with EDR', () => {
  let endpoint: OgcApiEndpoint;

  describe('nominal case', () => {
    beforeEach(() => {
      endpoint = new OgcApiEndpoint('http://local/edr/sample-data-hub');
    });

    describe('#info', () => {
      it('returns endpoint info', async () => {
        await expect(endpoint.info).resolves.toEqual({
          attribution: undefined,
          description: 'this dummy server is used for testing edr compliance',
          title: 'dummy server',
        });
      });

      it('supports EDR ', async () => {
        await expect(endpoint.hasEnvironmentalDataRetrieval).resolves.toBe(
          true
        );
      });

      it('can list all the EDR collections', async () => {
        await expect(endpoint.edrCollections).resolves.toEqual([
          'reservoir-api',
        ]);
      });

      it('can produce a EDR query builder that provides info and download urls', async () => {
        const builder = await endpoint.edr('reservoir-api');
        expect(builder).toBeTruthy();
        expect(builder.supported_queries).toEqual(
          new Set(['area', 'locations', 'cube'])
        );
        expect(Object.keys(builder.supported_parameters)).toEqual([
          'Elevation',
          'Water Temperature',
          'Air Temperature',
        ]);
      });

      it('caches properly', async () => {
        const spy = jest.spyOn(endpoint, 'getCollectionInfo');
        const builder1 = await endpoint.edr('reservoir-api');
        const builder2 = await endpoint.edr('reservoir-api');
        expect(builder1).toBe(builder2); // same object is returned
        expect(spy).toHaveBeenCalledTimes(1); // only called once
      });

      it('can produce EDR area queries with or without optional parameters', async () => {
        const builder = await endpoint.edr('reservoir-api');
        const areaUrlWithoutParam = builder.buildAreaDownloadUrl(
          'POLYGON((-1.0 50.0, -1.0 51.0, 0.0 51.0, 0.0 50.0, -1.0 50.0))'
        );
        expect(areaUrlWithoutParam).toEqual(
          'https://dummy.edr.app/collections/reservoir-api/area?coords=...'
        );

        const areaUrlWithParam = builder.buildAreaDownloadUrl(
          'POLYGON((-1.0 50.0, -1.0 51.0, 0.0 51.0, 0.0 50.0, -1.0 50.0))',
          { parameter_name: ['Water Temperature'] }
        );
        expect(areaUrlWithParam).toContain('parameter-name=Water+Temperature');
      });

      it("throws an error when called with a parameter that doesn't exist", async () => {
        const builder = await endpoint.edr('reservoir-api');
        expect(() =>
          builder.buildAreaDownloadUrl(
            'POLYGON((-1.0 50.0, -1.0 51.0, 0.0 51.0, 0.0 50.0, -1.0 50.0))',
            { parameter_name: ['BadParameterName'] }
          )
        ).toThrow();
      });

      it('throws an error with an invalid bbox for the cube query', async () => {
        const builder = await endpoint.edr('reservoir-api');
        expect(() =>
          builder.buildCubeDownloadUrl({
            minX: 0,
            minY: 10,
            maxX: -10, // invalid: max < min
            maxY: 12,
          })
        ).toThrow();
      });
    });
  });
});
```

**Test Categories:**

1. **Endpoint detection tests**

   - Conformance class detection
   - Collection listing
   - Support flags

2. **Builder instantiation tests**

   - Constructor validation
   - Caching behavior
   - Metadata parsing

3. **URL building tests**

   - Required parameters only
   - Optional parameters
   - Parameter combinations

4. **Validation tests**

   - Invalid parameters
   - Unsupported query types
   - Malformed inputs

5. **Helper function tests** (separate file)
   - Date formatting
   - Parameter serialization

**CSAPI Test Projection:**

- ~400 lines of integration tests (1.3x EDR)
- ~100 lines of unit tests (2x EDR for more complex helpers)
- Total: ~500 lines of tests

---

## Key Learnings

### 1. Minimal Upstream Modifications

**Modified Core Files:**

- `endpoint.ts`: +43 lines (1 getter, 1 method, 1 cache)
- `info.ts`: +16 lines (1 function, 1 type extension)
- `model.ts`: +47 lines (1 type, 2 interfaces)
- `link-utils.ts`: +9 lines (type signature updates)

**Total Core Changes:** 115 lines

**LESSON:** Keep core modifications minimal. Most implementation lives in dedicated subfolder.

### 2. Self-Contained Implementation

**EDR-Specific Code Location:**

```
src/ogc-api/edr/
├── url_builder.ts    (self-contained)
├── model.ts          (self-contained)
└── helpers.ts        (self-contained)
```

**LESSON:** Implementation is isolated. Easy to remove for upstream PR if rejected.

### 3. Fixture-Driven Testing

**Fixture Breakdown:**

- Root endpoint metadata
- Conformance document
- Collections list
- Individual collection metadata

**LESSON:** Create realistic fixtures from live CSAPI endpoints (use pygeoapi test server).

### 4. Progressive Enhancement Pattern

**EDR adds to endpoint without breaking existing functionality:**

```typescript
// Existing pattern
endpoint.featureCollections; // Still works
endpoint.tileCollections; // Still works

// New pattern
endpoint.edrCollections; // Added without conflict
```

**LESSON:** CSAPI should follow same pattern. Don't modify existing properties/methods.

---

## Open Questions

### Q1: Subresource URL Building

**EDR Pattern:**

```typescript
// EDR has flat query types: position, cube, area, etc.
buildPositionDownloadUrl(coords, params);
buildCubeDownloadUrl(bbox, params);
```

**CSAPI Challenge:**

```typescript
// CSAPI has nested resources:
// /systems
// /systems/{id}
// /systems/{id}/procedures
// /systems/{id}/datastreams
// /systems/{id}/datastreams/{id}/observations
```

**QUESTION:** Should we have separate methods for each nesting level?

```typescript
buildSystemsUrl(params);
buildSystemUrl(systemId);
buildSystemProceduresUrl(systemId, params);
buildSystemDatastreamsUrl(systemId, params);
buildSystemDatastreamObservationsUrl(systemId, datastreamId, params);
```

**OR:** Use a hierarchical approach?

```typescript
systems(params); // /systems
system(id).get(); // /systems/{id}
system(id).procedures(); // /systems/{id}/procedures
system(id).datastreams(); // /systems/{id}/datastreams
system(id).datastream(id).observations(); // /systems/{id}/datastreams/{id}/observations
```

**DECISION NEEDED:** Research more complex OGC API implementations.

### Q2: Collection Association

**EDR Pattern:**

```typescript
// EDR queries are collection-scoped:
endpoint.edr('reservoir-api').buildAreaDownloadUrl(...)
```

**CSAPI Pattern Option 1 (Collection-Scoped):**

```typescript
// Same pattern:
endpoint.csapi('weather-stations').buildSystemsUrl(...)
```

**CSAPI Pattern Option 2 (Top-Level):**

```typescript
// CSAPI resources might be top-level:
endpoint.csapi().buildSystemsUrl(...)
```

**QUESTION:** Does CSAPI scope resources to collections, or are they top-level?

**ACTION:** Check CSAPI OpenAPI specs to determine resource hierarchy.

### Q3: Format Negotiation

**EDR Pattern:**

```typescript
// Format is optional parameter:
buildAreaDownloadUrl(coords, { f: 'json' });
```

**CSAPI Support:**

- GeoJSON (RFC 7946)
- SensorML 3.0 (XML/JSON)
- SWE Common 3.0 (XML/JSON)

**QUESTION:** Should we validate format parameter against supported formats per resource type?

**CONSIDERATION:** SensorML for systems/procedures, GeoJSON for sampling features, etc.

---

## Next Steps

### Immediate (This Session)

1. **✅ DONE:** Analyze PR #114 structure
2. **✅ DONE:** Document terminology (EDRQueryBuilder pattern)
3. **✅ DONE:** Measure code volume
4. **NEXT:** Review testing strategy document
5. **NEXT:** Compare with existing testing patterns

### Phase 2 (Next Session)

1. **Verify CSAPI resource hierarchy** from OpenAPI specs
2. **Design CSAPI URL builder API**
3. **Create fixture plan** (identify test endpoints)
4. **Map CSAPI resources to builder methods**

### Documentation Updates Needed

1. **Update FEATURE_SPEC.md Section 3** with architecture findings
2. **Update testing-strategy-research.md** with PR #114 test patterns
3. **Update design-strategy-research.md** with answers to critical questions

---

## Critical Findings Summary

### ✅ TERMINOLOGY RESOLVED

- **Object name:** `EDRQueryBuilder` (NOT "navigator")
- **CSAPI equivalent:** `CSAPIQueryBuilder`

### ✅ CODE VOLUME ACCEPTABLE

- **PR #114:** ~2800 lines total (750 implementation)
- **CSAPI projection:** ~3500 lines total (975 implementation)
- **Verdict:** Within acceptable range (~41% of upstream vs. previous 2x)

### ✅ PATTERN IDENTIFIED

- **Minimal core modifications:** 115 lines across 4 files
- **Self-contained implementation:** All in `edr/` subfolder
- **Progressive enhancement:** Doesn't break existing API

### ⚠️ OPEN QUESTIONS

1. How to handle CSAPI subresource URL building?
2. Are CSAPI resources collection-scoped or top-level?
3. How to handle format negotiation for multiple content types?

---

**RECOMMENDATION:** Proceed with Phase 1 implementation planning. Architecture pattern is clear and proven. Focus next on resolving open questions through CSAPI spec analysis.
