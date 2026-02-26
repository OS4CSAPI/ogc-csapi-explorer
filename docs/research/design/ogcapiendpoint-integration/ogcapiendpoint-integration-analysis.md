# OgcApiEndpoint Integration - Component Analysis Report

**Component:** Component 1 - OgcApiEndpoint Integration  
**Phase:** Phase 1 - Foundation  
**Date:** February 2, 2026  
**Research Status:** ✅ COMPLETE

---

## Executive Summary

This analysis defines how CSAPI functionality integrates into the `OgcApiEndpoint` class following the proven EDR pattern from PR #114. The integration adds approximately **48 lines across 2-3 files** (endpoint.ts, info.ts, index.ts) to expose CSAPI capabilities through a single developer-facing factory method: `endpoint.csapi(collection_id)`.

**Key Finding:** The integration is minimal, non-breaking, and directly replicates the EDR architecture. Developers access all CSAPI functionality through one method that returns a `CSAPIQueryBuilder` instance with methods for all 9 resource types.

**Integration Footprint:**

- **endpoint.ts:** ~43 lines (import, cache field, collections getter, factory method)
- **info.ts:** ~16 lines (conformance getter + helper function)
- **index.ts:** ~6 lines (exports)
- **Total:** ~65 lines across 3 files (slightly more than EDR's 48 lines due to more conformance classes)

**Critical Architectural Principle:** This is a **factory method pattern**, not inheritance. `CSAPIQueryBuilder` is instantiated and returned; `OgcApiEndpoint` does not extend or inherit CSAPI functionality. This composition-over-inheritance approach keeps the codebase maintainable and testable.

---

## 1. Factory Method Signature

### Method Definition

**File:** `endpoint.ts` (line ~283 in current codebase, after `hasEnvironmentalDataRetrieval` getter)

````typescript
/**
 * Returns a CSAPI query builder for constructing URLs to Connected Systems API resources.
 * The query builder provides methods for accessing Systems, Deployments, Procedures,
 * Sampling Features, Properties, DataStreams, Observations, Control Streams, and Commands.
 *
 * @param collection_id The collection identifier that contains CSAPI resources
 * @returns Promise resolving to a CSAPIQueryBuilder instance
 * @throws {EndpointError} If the endpoint does not support Connected Systems API
 *
 * @example
 * ```typescript
 * const endpoint = new OgcApiEndpoint('https://server.com/api');
 * const csapi = await endpoint.csapi('sensors-collection');
 * const systemsUrl = csapi.getSystems({ bbox: [0, 0, 10, 10], recursive: true });
 * ```
 */
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  const cache = this.collection_id_to_csapi_builder_;
  if (cache.has(collection_id)) {
    return cache.get(collection_id);
  }
  const collection = await this.getCollectionInfo(collection_id);
  const result = new CSAPIQueryBuilder(collection);
  cache.set(collection_id, result);
  return result;
}
````

### Method Characteristics

**Parameter Requirements:**

- **collection_id:** String - REQUIRED
  - Must be a valid collection ID returned by `endpoint.csapiCollections` or `endpoint.allCollections`
  - Collection must support CSAPI resources (indicated by conformance classes and collection metadata)
  - Invalid collection IDs should throw descriptive errors

**Return Type:**

- `Promise<CSAPIQueryBuilder>` - Async operation that fetches collection metadata before instantiation
- Resolves to a fully-initialized QueryBuilder with all methods available immediately
- No need for additional `.isReady()` calls - QueryBuilder is ready upon return

**Error Conditions:**

1. **No CSAPI Support:** Throws `EndpointError` if `hasConnectedSystems` is false
2. **Invalid Collection:** Throws error from `getCollectionInfo()` if collection doesn't exist
3. **Missing Metadata:** CSAPIQueryBuilder constructor should validate collection has required CSAPI metadata

**Caching Behavior:**

- Uses `Map<string, CSAPIQueryBuilder>` as cache storage
- Cache key is the `collection_id` string
- Same builder instance returned for repeated calls with same collection_id
- Cache prevents redundant HTTP requests for collection metadata
- Cache lives for lifetime of OgcApiEndpoint instance

### EDR Pattern Comparison

**EDR Factory Method (Reference):**

```typescript
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
```

**CSAPI Adaptation Strategy:**

1. Replace `EDRQueryBuilder` → `CSAPIQueryBuilder`
2. Replace `hasEnvironmentalDataRetrieval` → `hasConnectedSystems`
3. Replace cache field name `collection_id_to_edr_builder_` → `collection_id_to_csapi_builder_`
4. Keep all other logic identical (conformance check, cache lookup, builder instantiation, cache storage)

**Key Insight:** This is a proven pattern with ~2 years of production use. No architectural innovation needed - just apply EDR pattern to CSAPI.

---

## 2. Constructor Pattern

### CSAPIQueryBuilder Constructor

**File:** `src/ogc-api/csapi/url_builder.ts`

```typescript
export default class CSAPIQueryBuilder {
  private collection: OgcApiCollectionInfo;
  private baseUrl: string;
  private supported_resource_types: Set<CSAPIResourceType>;
  private supported_schemas: Record<string, SchemaInfo>;

  /**
   * Creates a new CSAPI query builder for the specified collection.
   * Validates that the collection has CSAPI metadata and extracts resource type support.
   *
   * @param collection Collection metadata from OgcApiEndpoint.getCollectionInfo()
   * @throws {Error} If collection is missing required CSAPI metadata
   */
  constructor(collection: OgcApiCollectionInfo) {
    this.collection = collection;
    this.baseUrl = collection.id; // or extract from links

    // Validate collection has CSAPI metadata
    if (!collection.csapi_resources) {
      throw new Error(
        `Collection '${collection.id}' does not contain CSAPI resource metadata`
      );
    }

    // Extract supported resource types from collection metadata
    this.supported_resource_types = new Set();
    const resources = collection.csapi_resources;

    if (resources.systems) this.supported_resource_types.add('systems');
    if (resources.deployments) this.supported_resource_types.add('deployments');
    if (resources.procedures) this.supported_resource_types.add('procedures');
    if (resources.samplingFeatures)
      this.supported_resource_types.add('samplingFeatures');
    if (resources.properties) this.supported_resource_types.add('properties');
    if (resources.datastreams) this.supported_resource_types.add('datastreams');
    if (resources.observations)
      this.supported_resource_types.add('observations');
    if (resources.controlstreams)
      this.supported_resource_types.add('controlstreams');
    if (resources.commands) this.supported_resource_types.add('commands');

    // Extract schema information for Part 2 resources
    this.supported_schemas = this.extractSchemaInfo(resources);
  }

  /**
   * Helper to extract schema metadata for DataStreams and ControlStreams
   */
  private extractSchemaInfo(
    resources: CSAPIResourcesMetadata
  ): Record<string, SchemaInfo> {
    const schemas: Record<string, SchemaInfo> = {};

    // DataStream schemas
    if (resources.datastreams?.schemas) {
      schemas['datastreams'] = resources.datastreams.schemas;
    }

    // ControlStream schemas
    if (resources.controlstreams?.schemas) {
      schemas['controlstreams'] = resources.controlstreams.schemas;
    }

    return schemas;
  }

  // ... URL building methods follow ...
}
```

### Constructor Parameters

**Required Input:**

- `collection: OgcApiCollectionInfo` - Collection metadata object from `endpoint.getCollectionInfo()`

**What Collection Info Must Contain:**

```typescript
interface OgcApiCollectionInfo {
  id: string; // Collection identifier
  title?: string; // Human-readable title
  description?: string; // Collection description

  // CSAPI-specific additions (extend existing type)
  csapi_resources?: {
    systems?: {
      link: { href: string; rel: string };
      operations?: string[]; // ['GET', 'POST']
    };
    deployments?: {
      link: { href: string; rel: string };
      operations?: string[];
    };
    procedures?: {
      link: { href: string; rel: string };
      operations?: string[];
    };
    samplingFeatures?: {
      link: { href: string; rel: string };
      operations?: string[];
    };
    properties?: {
      link: { href: string; rel: string };
      operations?: string[];
    };
    datastreams?: {
      link: { href: string; rel: string };
      operations?: string[];
      schemas?: SchemaInfo; // SWE Common schema metadata
    };
    observations?: {
      link: { href: string; rel: string };
      operations?: string[];
    };
    controlstreams?: {
      link: { href: string; rel: string };
      operations?: string[];
      schemas?: SchemaInfo; // SWE Common schema metadata
    };
    commands?: {
      link: { href: string; rel: string };
      operations?: string[];
    };
  };

  // Existing properties
  itemFormats?: string[]; // Supported formats
  extent?: {
    spatial?: BoundingBox;
    temporal?: TemporalExtent;
  };
  links?: Array<{
    href: string;
    rel: string;
    type?: string;
    title?: string;
  }>;
}
```

### Constructor Validation

**Validation Checks:**

1. **CSAPI Metadata Presence:** Verify `collection.csapi_resources` exists
2. **At Least One Resource Type:** Verify at least one resource type is supported
3. **Valid Link Metadata:** Verify each resource has valid `link.href` and `link.rel`

**Error Messages:**

```typescript
// Missing metadata
throw new Error(
  `Collection '${collection.id}' does not contain CSAPI resource metadata`
);

// No supported resources
throw new Error(
  `Collection '${collection.id}' does not support any CSAPI resource types`
);

// Invalid link metadata
throw new Error(
  `Resource type 'systems' in collection '${collection.id}' has invalid link metadata`
);
```

### EDR Pattern Comparison

**EDR Constructor (Reference):**

```typescript
constructor(collection: OgcApiCollectionInfo) {
  this.collection = collection;

  // Validate collection has EDR metadata
  if (!collection.data_queries) {
    throw new Error(
      `Collection '${collection.id}' does not support data queries`
    );
  }

  // Extract supported query types
  this.supported_query_types = {};
  const queries = collection.data_queries;

  if (queries.position) this.supported_query_types.position = true;
  if (queries.area) this.supported_query_types.area = true;
  if (queries.cube) this.supported_query_types.cube = true;
  // ... etc for all EDR query types

  // Extract parameter metadata
  this.supported_parameters = collection.parameter_names || {};
}
```

**CSAPI Differences:**

- EDR uses `data_queries` → CSAPI uses `csapi_resources`
- EDR has 9 query types → CSAPI has 9 resource types
- EDR extracts parameters → CSAPI extracts schemas (Part 2 only)
- Same validation pattern (check metadata exists, extract capabilities, validate links)

---

## 3. Caching Strategy

### Cache Implementation

**Cache Storage:**

```typescript
// In OgcApiEndpoint class
private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();
```

**Cache Operations:**

1. **Initialization:** Cache starts empty when `OgcApiEndpoint` is instantiated
2. **Lookup:** Before creating QueryBuilder, check `cache.has(collection_id)`
3. **Store:** After creating QueryBuilder, store with `cache.set(collection_id, builder)`
4. **Retrieval:** If cache hit, return with `cache.get(collection_id)`

### Cache Lifecycle

**When Cache is Populated:**

- First call to `endpoint.csapi('collection-A')` → fetches metadata, creates builder, caches
- Second call to `endpoint.csapi('collection-A')` → returns cached builder (no HTTP request)
- Call to `endpoint.csapi('collection-B')` → fetches metadata for B, creates new builder, caches

**Cache Scope:**

- Cache lives for lifetime of `OgcApiEndpoint` instance
- Each endpoint instance has its own cache (not shared across instances)
- Cache is NOT persisted (lost when endpoint instance is garbage collected)

**Cache Benefits:**

1. **Performance:** Eliminates redundant HTTP requests for collection metadata
2. **Consistency:** Same builder instance ensures consistent behavior
3. **Memory:** Minimal memory footprint (one QueryBuilder per collection)

### Cache Key Strategy

**Key Format:**

- Simple string: `collection_id` parameter passed to `csapi()` method
- Example keys: `'sensors-collection'`, `'weather-stations'`, `'observation-data'`

**Key Uniqueness:**

- Collection IDs are globally unique within an endpoint
- No risk of collisions (endpoint provides the collection IDs)
- Case-sensitive matching (keys must match exactly)

### Cache Invalidation

**When Cache Should Be Cleared:**

- **Never automatically:** Cache is valid for endpoint lifetime
- **Manual clearing:** User can create new endpoint instance if metadata changes
- **Future enhancement:** Could add `clearCache()` method if needed

**Why No Auto-Invalidation:**

- Collection metadata is static for most use cases
- Server-side changes to collections are rare during client session
- Re-creating endpoint instance is simple if invalidation needed

### EDR Pattern Comparison

**EDR Cache Implementation:**

```typescript
// Same pattern as CSAPI
private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> = new Map();

// Usage
const cache = this.collection_id_to_edr_builder_;
if (cache.has(collection_id)) {
  return cache.get(collection_id);
}
```

**CSAPI Adaptation:**

- Identical pattern, just different type names
- No architectural changes needed
- Proven to work in production for ~2 years

---

## 4. Conformance Detection

### Conformance Checking Method

**File:** `info.ts` (alongside `checkHasEnvironmentalDataRetrieval`)

```typescript
/**
 * Checks if the endpoint supports OGC API - Connected Systems API.
 *
 * @param conformanceClasses Array of conformance class URIs from /conformance endpoint
 * @returns True if endpoint supports CSAPI (either Part 1 or Part 2), false otherwise
 */
export function checkHasConnectedSystems(
  conformanceClasses: ConformanceClass[]
): boolean {
  const csapiPart1Core =
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/core';
  const csapiPart2Core =
    'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/core';

  // Check if endpoint advertises CSAPI Part 1 OR Part 2 support
  return conformanceClasses.some(
    (conformanceClass) =>
      conformanceClass.includes(csapiPart1Core) ||
      conformanceClass.includes(csapiPart2Core)
  );
}
```

### Conformance Getter

**File:** `endpoint.ts` (alongside `hasEnvironmentalDataRetrieval` getter)

```typescript
/**
 * A Promise which resolves to a boolean indicating whether the endpoint offers
 * Connected Systems API (CSAPI) resources.
 */
get hasConnectedSystems(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasConnectedSystems
  );
}
```

### Conformance Classes to Detect

**Part 1 Conformance Classes:**

```typescript
// Core (required for Part 1 support)
'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/core';

// Resource Types (optional but common)
'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/system';
'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/deployment';
'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/procedure';
'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/samplingFeature';
'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/property';
```

**Part 2 Conformance Classes:**

```typescript
// Core (required for Part 2 support)
'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/core';

// Resource Types (optional but common)
'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/datastream';
'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/observation';
'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/controlstream';
'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/command';
```

### Detection Logic

**Basic Detection (Recommended):**

- Check for Part 1 Core **OR** Part 2 Core conformance class
- If either is present, endpoint supports CSAPI
- Specific resource type support determined from collection metadata, not conformance

**Rationale:**

- Core conformance indicates endpoint implements CSAPI standard
- Resource-specific conformance classes are optional in spec
- Collection metadata is authoritative source for resource type support

**Alternative Detection (More Strict):**

```typescript
export function checkHasConnectedSystems(
  conformanceClasses: ConformanceClass[]
): boolean {
  // Require at least one resource type conformance class
  const csapiClasses = [
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/core',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/system',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/deployment',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/procedure',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/samplingFeature',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/property',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/core',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/datastream',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/observation',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/controlstream',
    'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/command',
  ];

  return conformanceClasses.some((cc) =>
    csapiClasses.some((csapiClass) => cc.includes(csapiClass))
  );
}
```

### EDR Pattern Comparison

**EDR Conformance Check (Reference):**

```typescript
export function checkHasEnvironmentalDataRetrieval(
  conformanceClasses: ConformanceClass[]
): boolean {
  return conformanceClasses.some(
    (conformanceClass) =>
      conformanceClass.includes(
        'http://www.opengis.net/spec/ogcapi-edr-1/1.1/req/core'
      ) ||
      conformanceClass.includes(
        'http://www.opengis.net/spec/ogcapi-edr-1/1.0/req/core'
      )
  );
}

get hasEnvironmentalDataRetrieval(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasEnvironmentalDataRetrieval
  );
}
```

**CSAPI Adaptation:**

- Same structure (function + getter)
- Check for Part 1 OR Part 2 core classes (EDR checks multiple versions)
- Return boolean Promise
- No changes to calling pattern

---

## 5. Collections Filtering

### Collections Getter

**File:** `endpoint.ts` (alongside `edrCollections` getter)

```typescript
/**
 * A Promise which resolves to an array of collection identifiers that support
 * Connected Systems API resources.
 */
get csapiCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasConnectedSystems])
    .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) =>
      collections.filter((c) => c.csapi_resources !== undefined)
    )
    .then((collections) => collections.map((c) => c.name));
}
```

### Filtering Logic

**Step-by-Step Process:**

1. **Check CSAPI Support:** If `hasConnectedSystems` is false, return empty array
2. **Parse Collections:** Extract collection metadata from `/collections` response
3. **Filter CSAPI Collections:** Keep only collections with `csapi_resources` metadata
4. **Extract Names:** Map filtered collections to their identifier strings

**Collection Detection Criteria:**

```typescript
// Collection must have csapi_resources metadata
interface ParsedCollection {
  name: string;
  csapi_resources?: {
    systems?: ResourceMetadata;
    deployments?: ResourceMetadata;
    datastreams?: ResourceMetadata;
    // ... other resource types
  };
}

// Filter function
collections.filter((c) => c.csapi_resources !== undefined);
```

### Resource Type Filtering (Optional Enhancement)

**If needed, add specific resource type getters:**

```typescript
/**
 * Collections that support CSAPI Systems resource
 */
get csapiSystemCollections(): Promise<string[]> {
  return this.csapiCollections.then((collections) =>
    collections.filter(async (collectionId) => {
      const info = await this.getCollectionInfo(collectionId);
      return info.csapi_resources?.systems !== undefined;
    })
  );
}

/**
 * Collections that support CSAPI DataStreams resource
 */
get csapiDataStreamCollections(): Promise<string[]> {
  return this.csapiCollections.then((collections) =>
    collections.filter(async (collectionId) => {
      const info = await this.getCollectionInfo(collectionId);
      return info.csapi_resources?.datastreams !== undefined;
    })
  );
}

// Similar getters for deployments, procedures, observations, etc.
```

**Recommendation:** Start with basic `csapiCollections` getter. Add resource-specific getters only if user demand exists.

### EDR Pattern Comparison

**EDR Collections Getter (Reference):**

```typescript
get edrCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasEnvironmentalDataRetrieval])
    .then(([data, hasEDR]) => (hasEDR ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasDataQueries))
    .then((collections) => collections.map((collection) => collection.name));
}
```

**CSAPI Adaptation:**

- Replace `hasEnvironmentalDataRetrieval` → `hasConnectedSystems`
- Replace filter `c.hasDataQueries` → `c.csapi_resources !== undefined`
- Keep all other logic identical
- Return array of collection ID strings

---

## 6. Type Definitions

### Core Type Additions

**File:** `src/ogc-api/csapi/types.ts` (new file)

```typescript
/**
 * CSAPI resource types (from Parts 1 & 2)
 */
export const CSAPIResourceTypes = [
  'systems',
  'deployments',
  'procedures',
  'samplingFeatures',
  'properties',
  'datastreams',
  'observations',
  'controlstreams',
  'commands',
] as const;

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

/**
 * Metadata for a single CSAPI resource type within a collection
 */
export interface CSAPIResourceMetadata {
  link: {
    href: string; // URL to the resource endpoint
    rel: string; // Relation type
    type?: string; // Media type
    title?: string; // Human-readable title
  };
  operations?: string[]; // Supported HTTP methods ['GET', 'POST', 'PUT', 'DELETE']
  schemas?: SchemaInfo; // For DataStreams/ControlStreams only
}

/**
 * Schema information for Part 2 resources
 */
export interface SchemaInfo {
  encoding: 'json' | 'text' | 'binary';
  definition: {
    href: string; // URL to schema definition
    type: string; // Media type (application/swe+json, etc.)
  };
}

/**
 * Complete CSAPI resources metadata for a collection
 */
export interface CSAPIResourcesMetadata {
  systems?: CSAPIResourceMetadata;
  deployments?: CSAPIResourceMetadata;
  procedures?: CSAPIResourceMetadata;
  samplingFeatures?: CSAPIResourceMetadata;
  properties?: CSAPIResourceMetadata;
  datastreams?: CSAPIResourceMetadata;
  observations?: CSAPIResourceMetadata;
  controlstreams?: CSAPIResourceMetadata;
  commands?: CSAPIResourceMetadata;
}
```

### Collection Info Extension

**File:** `src/ogc-api/model.ts` (extend existing type)

```typescript
export interface OgcApiCollectionInfo {
  // ... existing properties ...

  /**
   * CSAPI resource metadata (added for CSAPI support)
   */
  csapi_resources?: CSAPIResourcesMetadata;
}
```

### Query Parameter Types

**File:** `src/ogc-api/csapi/types.ts`

```typescript
/**
 * Common query parameters for CSAPI resources
 */
export interface CSAPICommonParams {
  // Standard OGC API params
  bbox?: number[]; // [minX, minY, maxX, maxY] or [minX, minY, minZ, maxX, maxY, maxZ]
  datetime?: DateTimeParameter; // ISO 8601 interval or instant
  limit?: number; // Max results per page (1-10000)
  offset?: number; // Skip N results
  f?: string; // Format (json, geojson, sml+json, swe+json, swe+text)

  // CSAPI common params
  id?: string | string[]; // Filter by resource ID(s)
  uid?: string | string[]; // Filter by UID(s)
  q?: string; // Full-text search

  // Hierarchical params
  parent?: string; // Filter by parent resource
  recursive?: boolean; // Include children recursively

  // Property filters (dynamic)
  [propertyName: string]: any; // Filter by any resource property
}

/**
 * Systems-specific query parameters
 */
export interface SystemsParams extends CSAPICommonParams {
  procedure?: string; // Filter by associated procedure
  foi?: string; // Filter by feature of interest
  observedProperty?: string[]; // Filter by observed properties
  controlledProperty?: string[]; // Filter by controlled properties
  validTime?: DateTimeParameter; // Filter by temporal validity
  geom?: string; // Filter by geometry (WKT)
}

/**
 * Observations-specific query parameters
 */
export interface ObservationsParams extends CSAPICommonParams {
  phenomenonTime?: DateTimeParameter; // Filter by observation time
  resultTime?: DateTimeParameter; // Filter by result reception time
  select?: string[]; // Select specific properties
}

// ... similar interfaces for other resource types ...
```

### EDR Pattern Comparison

**EDR Type Definitions (Reference):**

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

**CSAPI Adaptation:**

- Replace `DataQueryTypes` → `CSAPIResourceTypes`
- Replace `data_queries` → `csapi_resources`
- Add `operations` array for HTTP methods (EDR doesn't need this)
- Add `schemas` for Part 2 resources (EDR doesn't have this)
- Keep link structure identical

---

## 7. Integration Code Locations

### File Modifications Required

**1. src/ogc-api/endpoint.ts**

- **Line ~50:** Add import statement

  ```typescript
  import CSAPIQueryBuilder from './csapi/url_builder.js';
  ```

- **Line ~60:** Add cache field

  ```typescript
  private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();
  ```

- **Line ~200:** Add collections getter (after `edrCollections`)

  ```typescript
  get csapiCollections(): Promise<string[]> { ... }
  ```

- **Line ~280:** Add factory method (after `edr()` method)
  ```typescript
  public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> { ... }
  ```

**Total Changes:** ~43 lines added

---

**2. src/ogc-api/info.ts**

- **Line ~250:** Add conformance check function (after `checkHasEnvironmentalDataRetrieval`)

  ```typescript
  export function checkHasConnectedSystems(
    conformanceClasses: ConformanceClass[]
  ): boolean { ... }
  ```

- **File:** Also update endpoint.ts getter section
- **Line ~270:** Add conformance getter (in endpoint.ts, after `hasEnvironmentalDataRetrieval`)
  ```typescript
  get hasConnectedSystems(): Promise<boolean> { ... }
  ```

**Total Changes:** ~16 lines added (7 in info.ts + 9 in endpoint.ts for getter)

---

**3. src/index.ts**

- **Line ~40:** Add exports (after EDR exports)
  ```typescript
  export { default as CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';
  export type {
    CSAPIResourceType,
    CSAPIResourceMetadata,
    CSAPIResourcesMetadata,
    SchemaInfo,
    SystemsParams,
    ObservationsParams,
    // ... other CSAPI types
  } from './ogc-api/csapi/types.js';
  ```

**Total Changes:** ~6 lines added

---

**4. src/ogc-api/model.ts**

- **Line ~80:** Extend `OgcApiCollectionInfo` interface

  ```typescript
  import type { CSAPIResourcesMetadata } from './csapi/types.js';

  export interface OgcApiCollectionInfo {
    // ... existing properties ...

    /**
     * CSAPI resource metadata (added for CSAPI support)
     */
    csapi_resources?: CSAPIResourcesMetadata;
  }
  ```

**Total Changes:** ~2 lines added (import + property)

---

### New Files Required

**1. src/ogc-api/csapi/types.ts** (~150-200 lines)

- CSAPI type definitions
- Resource types enum
- Metadata interfaces
- Query parameter types

**2. src/ogc-api/csapi/url_builder.ts** (~10,000-14,000 lines)

- CSAPIQueryBuilder class
- Constructor
- 9 resource type method groups
- URL building logic
- Parameter validation

**3. src/ogc-api/csapi/helpers.ts** (~50-100 lines)

- Date formatting functions
- Parameter serialization
- Validation helpers

**4. src/ogc-api/csapi/index.ts** (~5 lines)

- Exports for CSAPI module
- Re-export types and classes

---

### Integration Testing Files

**1. fixtures/ogc-api/csapi/** (~500-800 lines JSON)

- Sample CSAPI root document
- Sample conformance document
- Sample collections document
- Sample collection metadata
- Sample resource responses

**2. src/ogc-api/endpoint.spec.ts** (~400 lines added)

- CSAPI conformance detection tests
- Collections filtering tests
- Factory method tests
- Caching behavior tests
- Error handling tests

**3. src/ogc-api/csapi/url_builder.spec.ts** (~2000-2500 lines)

- Constructor validation tests
- URL building tests for all 9 resource types
- Parameter validation tests
- Edge case tests

---

## 8. Integration with Existing Systems

### How CSAPIQueryBuilder Interacts with Collection Metadata

**Metadata Flow:**

```
OgcApiEndpoint
  ↓ fetches /collections
parseCollections()
  ↓ extracts csapi_resources
OgcApiCollectionInfo
  ↓ passed to constructor
CSAPIQueryBuilder
  ↓ stores and uses for URL building
Resource URLs
```

**Collection Metadata Example:**

```json
{
  "id": "sensors-collection",
  "title": "Weather Sensors",
  "links": [
    {
      "href": "https://server.com/api/collections/sensors-collection/systems",
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/systems",
      "type": "application/geo+json"
    },
    {
      "href": "https://server.com/api/collections/sensors-collection/datastreams",
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/datastreams",
      "type": "application/swe+json"
    }
  ],
  "csapi_resources": {
    "systems": {
      "link": {
        "href": "https://server.com/api/collections/sensors-collection/systems",
        "rel": "http://www.opengis.net/def/rel/ogc/1.0/systems"
      },
      "operations": ["GET", "POST"]
    },
    "datastreams": {
      "link": {
        "href": "https://server.com/api/collections/sensors-collection/datastreams",
        "rel": "http://www.opengis.net/def/rel/ogc/1.0/datastreams"
      },
      "operations": ["GET", "POST", "PUT", "DELETE"],
      "schemas": {
        "encoding": "json",
        "definition": {
          "href": "https://server.com/api/collections/sensors-collection/datastreams/schema",
          "type": "application/swe+json"
        }
      }
    }
  }
}
```

**CSAPIQueryBuilder Usage:**

```typescript
const builder = await endpoint.csapi('sensors-collection');

// Builder uses csapi_resources.systems.link.href as base URL
const systemsUrl = builder.getSystems({ bbox: [0, 0, 10, 10] });
// Result: https://server.com/api/collections/sensors-collection/systems?bbox=0,0,10,10

// Builder uses csapi_resources.datastreams.link.href as base URL
const datastreamsUrl = builder.getDataStreams({ limit: 50 });
// Result: https://server.com/api/collections/sensors-collection/datastreams?limit=50
```

### Relationship to Conformance Classes

**Detection Hierarchy:**

1. **Endpoint Level:** `hasConnectedSystems` checks conformance classes

   - If true, endpoint offers CSAPI support globally
   - If false, no CSAPI collections available

2. **Collection Level:** `csapi_resources` indicates collection capabilities

   - Even if endpoint supports CSAPI, not all collections may have CSAPI resources
   - Collection metadata is authoritative for resource type support

3. **Resource Level:** Each resource type can be individually supported
   - Collection may support Systems but not DataStreams
   - Collection may support Observations but not Commands

**Example Scenarios:**

```typescript
// Scenario 1: Full CSAPI support
await endpoint.hasConnectedSystems; // true
await endpoint.csapiCollections; // ['collection-A', 'collection-B']
const builder = await endpoint.csapi('collection-A');
builder.supported_resource_types; // Set(['systems', 'datastreams', 'observations'])

// Scenario 2: Partial CSAPI support
await endpoint.hasConnectedSystems; // true
await endpoint.csapiCollections; // ['collection-C']
const builder = await endpoint.csapi('collection-C');
builder.supported_resource_types; // Set(['systems']) - only systems supported

// Scenario 3: No CSAPI support
await endpoint.hasConnectedSystems; // false
await endpoint.csapiCollections; // []
await endpoint.csapi('collection-X'); // throws EndpointError
```

### Error Handling at Integration Points

**Conformance Check Failure:**

```typescript
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  // ... rest of method
}
```

**Collection Not Found:**

```typescript
// getCollectionInfo() throws if collection doesn't exist
const collection = await this.getCollectionInfo(collection_id);
// Error message: "Collection 'invalid-id' not found"
```

**Missing CSAPI Metadata:**

```typescript
// CSAPIQueryBuilder constructor validates metadata
constructor(collection: OgcApiCollectionInfo) {
  if (!collection.csapi_resources) {
    throw new Error(
      `Collection '${collection.id}' does not contain CSAPI resource metadata`
    );
  }
  // ... rest of constructor
}
```

**Unsupported Resource Type:**

```typescript
// Each URL building method checks support
getSystems(params?: SystemsParams): string {
  if (!this.supported_resource_types.has('systems')) {
    throw new Error('Collection does not support systems resource');
  }
  // ... build URL
}
```

---

## 9. Testing Strategy

### Integration Tests

**File:** `src/ogc-api/endpoint.spec.ts` (add new describe block)

```typescript
describe('OgcApiEndpoint with CSAPI', () => {
  let endpoint: OgcApiEndpoint;

  describe('nominal case', () => {
    beforeEach(() => {
      endpoint = new OgcApiEndpoint('http://local/csapi/test-endpoint');
    });

    describe('#info', () => {
      it('returns endpoint info', async () => {
        await expect(endpoint.info).resolves.toEqual({
          title: 'Test CSAPI Endpoint',
          description: 'Test endpoint for CSAPI integration',
        });
      });

      it('supports CSAPI', async () => {
        await expect(endpoint.hasConnectedSystems).resolves.toBe(true);
      });

      it('can list all CSAPI collections', async () => {
        await expect(endpoint.csapiCollections).resolves.toEqual([
          'sensors-collection',
          'observations-collection',
        ]);
      });
    });

    describe('#csapi', () => {
      it('can produce a CSAPI query builder', async () => {
        const builder = await endpoint.csapi('sensors-collection');
        expect(builder).toBeTruthy();
        expect(builder.supported_resource_types).toContain('systems');
        expect(builder.supported_resource_types).toContain('datastreams');
      });

      it('caches properly', async () => {
        const spy = jest.spyOn(endpoint, 'getCollectionInfo');
        const builder1 = await endpoint.csapi('sensors-collection');
        const builder2 = await endpoint.csapi('sensors-collection');
        expect(builder1).toBe(builder2); // same object is returned
        expect(spy).toHaveBeenCalledTimes(1); // only called once
      });

      it('throws error if endpoint does not support CSAPI', async () => {
        const noCSAPIEndpoint = new OgcApiEndpoint('http://local/no-csapi');
        await expect(noCSAPIEndpoint.csapi('any-collection')).rejects.toThrow(
          'Endpoint does not support Connected Systems API'
        );
      });

      it('throws error if collection does not exist', async () => {
        await expect(
          endpoint.csapi('nonexistent-collection')
        ).rejects.toThrow();
      });
    });
  });
});
```

### Unit Tests

**File:** `src/ogc-api/csapi/url_builder.spec.ts` (new file)

```typescript
describe('CSAPIQueryBuilder', () => {
  let builder: CSAPIQueryBuilder;
  let mockCollection: OgcApiCollectionInfo;

  beforeEach(() => {
    mockCollection = {
      id: 'sensors-collection',
      title: 'Test Sensors',
      csapi_resources: {
        systems: {
          link: {
            href: 'https://server.com/api/collections/sensors-collection/systems',
            rel: 'systems',
          },
          operations: ['GET', 'POST'],
        },
        datastreams: {
          link: {
            href: 'https://server.com/api/collections/sensors-collection/datastreams',
            rel: 'datastreams',
          },
          operations: ['GET', 'POST', 'PUT', 'DELETE'],
        },
      },
    };
    builder = new CSAPIQueryBuilder(mockCollection);
  });

  describe('constructor', () => {
    it('validates collection has CSAPI metadata', () => {
      const invalidCollection = { id: 'test', title: 'Test' };
      expect(() => new CSAPIQueryBuilder(invalidCollection as any)).toThrow(
        'does not contain CSAPI resource metadata'
      );
    });

    it('extracts supported resource types', () => {
      expect(builder.supported_resource_types).toContain('systems');
      expect(builder.supported_resource_types).toContain('datastreams');
      expect(builder.supported_resource_types).not.toContain('observations');
    });
  });

  describe('#getSystems', () => {
    it('builds URL without parameters', () => {
      const url = builder.getSystems();
      expect(url).toBe(
        'https://server.com/api/collections/sensors-collection/systems'
      );
    });

    it('builds URL with bbox parameter', () => {
      const url = builder.getSystems({ bbox: [0, 0, 10, 10] });
      expect(url).toContain('bbox=0,0,10,10');
    });

    it('throws error if systems not supported', () => {
      const noSystemsCollection = {
        id: 'test',
        csapi_resources: {
          datastreams: mockCollection.csapi_resources.datastreams,
        },
      };
      const noSystemsBuilder = new CSAPIQueryBuilder(
        noSystemsCollection as any
      );
      expect(() => noSystemsBuilder.getSystems()).toThrow(
        'Collection does not support systems resource'
      );
    });
  });

  // ... similar tests for other resource types ...
});
```

### Fixture Requirements

**Files Needed in fixtures/ogc-api/csapi/:**

1. `root.json` - Landing page with CSAPI conformance
2. `conformance.json` - Conformance classes including CSAPI
3. `collections.json` - Collections list with CSAPI metadata
4. `sensors-collection.json` - Sample collection with CSAPI resources
5. `systems-response.json` - Sample systems resource response
6. `datastreams-response.json` - Sample datastreams resource response

**Fixture Example (collections.json):**

```json
{
  "collections": [
    {
      "id": "sensors-collection",
      "title": "Weather Sensors",
      "links": [
        {
          "href": "https://server.com/api/collections/sensors-collection/systems",
          "rel": "http://www.opengis.net/def/rel/ogc/1.0/systems",
          "type": "application/geo+json"
        }
      ],
      "csapi_resources": {
        "systems": {
          "link": {
            "href": "https://server.com/api/collections/sensors-collection/systems",
            "rel": "systems"
          },
          "operations": ["GET", "POST"]
        }
      }
    }
  ]
}
```

---

## 10. Implementation Checklist

### Phase 1: Type Definitions (~1 day)

- [ ] Create `src/ogc-api/csapi/types.ts`
  - [ ] Define `CSAPIResourceTypes` enum
  - [ ] Define `CSAPIResourceMetadata` interface
  - [ ] Define `CSAPIResourcesMetadata` interface
  - [ ] Define `SchemaInfo` interface
  - [ ] Define query parameter interfaces (SystemsParams, etc.)
- [ ] Extend `src/ogc-api/model.ts`
  - [ ] Import CSAPI types
  - [ ] Add `csapi_resources` property to `OgcApiCollectionInfo`

### Phase 2: Conformance Detection (~0.5 day)

- [ ] Add to `src/ogc-api/info.ts`
  - [ ] Implement `checkHasConnectedSystems()` function
  - [ ] Add tests for conformance detection
- [ ] Add to `src/ogc-api/endpoint.ts`
  - [ ] Add `hasConnectedSystems` getter
  - [ ] Test getter behavior

### Phase 3: Collections Filtering (~0.5 day)

- [ ] Add to `src/ogc-api/endpoint.ts`
  - [ ] Implement `csapiCollections` getter
  - [ ] Test collections filtering
  - [ ] Verify empty array when no CSAPI support

### Phase 4: Factory Method (~1 day)

- [ ] Add to `src/ogc-api/endpoint.ts`
  - [ ] Add import statement for CSAPIQueryBuilder
  - [ ] Add cache field declaration
  - [ ] Implement `csapi()` factory method
  - [ ] Test conformance check
  - [ ] Test cache behavior
  - [ ] Test error handling

### Phase 5: CSAPIQueryBuilder Skeleton (~1 day)

- [ ] Create `src/ogc-api/csapi/url_builder.ts`
  - [ ] Implement constructor
  - [ ] Add validation logic
  - [ ] Extract supported resource types
  - [ ] Test constructor with valid/invalid metadata

### Phase 6: URL Building Methods (~10-15 days)

- [ ] Systems resource methods
- [ ] Deployments resource methods
- [ ] Procedures resource methods
- [ ] Sampling Features resource methods
- [ ] Properties resource methods
- [ ] DataStreams resource methods
- [ ] Observations resource methods
- [ ] Control Streams resource methods
- [ ] Commands resource methods

### Phase 7: Helper Functions (~1 day)

- [ ] Create `src/ogc-api/csapi/helpers.ts`
  - [ ] Date formatting functions
  - [ ] Parameter serialization functions
  - [ ] Validation helpers

### Phase 8: Exports (~0.5 day)

- [ ] Update `src/index.ts`
  - [ ] Export CSAPIQueryBuilder
  - [ ] Export CSAPI types
- [ ] Create `src/ogc-api/csapi/index.ts`
  - [ ] Re-export module contents

### Phase 9: Fixtures (~1 day)

- [ ] Create `fixtures/ogc-api/csapi/` directory
  - [ ] Add root.json
  - [ ] Add conformance.json
  - [ ] Add collections.json
  - [ ] Add sample collection metadata
  - [ ] Add sample resource responses

### Phase 10: Integration Tests (~2 days)

- [ ] Update `src/ogc-api/endpoint.spec.ts`
  - [ ] Add CSAPI describe block
  - [ ] Test conformance detection
  - [ ] Test collections filtering
  - [ ] Test factory method
  - [ ] Test caching
  - [ ] Test error handling

### Phase 11: Unit Tests (~3-5 days)

- [ ] Create `src/ogc-api/csapi/url_builder.spec.ts`
  - [ ] Constructor tests
  - [ ] URL building tests for all 9 resource types
  - [ ] Parameter validation tests
  - [ ] Edge case tests

---

## Development Standards

All CSAPI implementation code must follow these Development Standards to ensure consistency with the upstream library and maintainability:

### Code Quality Standards

- **Type Safety:** All functions, parameters, and return values must have explicit TypeScript types. No `any` types except where absolutely necessary with clear justification.
- **Documentation:** All public methods and interfaces must have JSDoc comments explaining purpose, parameters, return values, and examples.
- **Testing:** Minimum 80% test coverage. All public methods must have unit tests. All integration points must have integration tests.
- **Error Handling:** All error conditions must throw descriptive errors with actionable messages. Use `EndpointError` for endpoint-level errors.

### Architecture Standards

- **Factory Pattern:** Follow EDR pattern exactly - factory method in OgcApiEndpoint, QueryBuilder class in dedicated subfolder.
- **Composition Over Inheritance:** No subclassing of OgcApiEndpoint. Use composition and delegation.
- **Progressive Enhancement:** New code must not break existing functionality for Features, Tiles, Records, or EDR.
- **Minimal Core Changes:** Keep modifications to core files (endpoint.ts, info.ts, model.ts) under 50 lines total.

### File Organization Standards

- **CSAPI Module:** All CSAPI code in `src/ogc-api/csapi/` subfolder
- **File Structure:** url_builder.ts, types.ts, helpers.ts, index.ts
- **Fixtures:** All test fixtures in `fixtures/ogc-api/csapi/` subfolder
- **Tests:** Integration tests in endpoint.spec.ts, unit tests in csapi/url_builder.spec.ts

### Naming Conventions

- **Class Names:** PascalCase (CSAPIQueryBuilder, EndpointError)
- **Method Names:** camelCase (getSystems, getObservations)
- **Type Names:** PascalCase (CSAPIResourceType, SystemsParams)
- **Constants:** UPPER_SNAKE_CASE or const arrays (CSAPIResourceTypes)

### Testing Standards

- **Fixture-Driven:** Use realistic JSON fixtures from live CSAPI endpoints
- **Test Organization:** describe blocks for classes, nested describes for methods
- **Coverage:** Test nominal cases, error cases, edge cases, parameter combinations
- **Assertions:** Use Jest matchers (toEqual, toThrow, toContain, etc.)

### Documentation Standards

- **JSDoc Format:** Use `@param`, `@returns`, `@throws`, `@example` tags
- **Examples:** Include runnable code examples in JSDoc
- **References:** Link to CSAPI specifications for complex behavior
- **Changelog:** Document all changes in CHANGELOG.md

**Reference Documents:**

- [Development Standards - CSAPI Implementation Guide](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/csapi-implementation-guide.md#development-standards) - Complete standards section
- [Upstream Library Expectations](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/upstream-expectations.md) - What camptocamp/ogc-client expects

---

## References

### Primary References

- [PR #114 (EDR Implementation) Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md) - **PRIMARY BLUEPRINT** - Complete EDR pattern documentation
- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - Systems, Deployments, Procedures, Sampling Features, Properties
- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - DataStreams, Observations, Control Streams, Commands

### Supporting References

- [CSAPI Implementation Guide](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/csapi-implementation-guide.md) - Complete component inventory
- [Integration with Existing Code](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/integration-analysis.md) - Line-by-line integration requirements
- [QueryBuilder Pattern Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md) - Factory method lifecycle, caching strategy
- [camptocamp/ogc-client Repository](https://github.com/camptocamp/ogc-client) - Upstream repository
- [CSAPI Part 1 OpenAPI Specification](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) - Machine-readable API definition
- [CSAPI Part 2 OpenAPI Specification](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) - Machine-readable API definition

---

## Appendices

### A. Complete Code Example

**Developer Usage (Full Workflow):**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

async function exploreCSAPIEndpoint() {
  // 1. Create endpoint
  const endpoint = new OgcApiEndpoint('https://server.com/api');

  // 2. Check CSAPI support
  if (await endpoint.hasConnectedSystems) {
    console.log('Endpoint supports CSAPI!');

    // 3. List CSAPI collections
    const collections = await endpoint.csapiCollections;
    console.log('CSAPI Collections:', collections);

    // 4. Get query builder for a collection
    const csapi = await endpoint.csapi('sensors-collection');

    // 5. Build URLs for CSAPI resources

    // Systems with spatial filter
    const systemsUrl = csapi.getSystems({
      bbox: [-180, -90, 180, 90],
      recursive: true,
    });
    console.log('Systems URL:', systemsUrl);

    // DataStreams for a specific system
    const datastreamsUrl = csapi.getSystemDataStreams('system-123', {
      observedProperty: ['temperature', 'humidity'],
      limit: 50,
    });
    console.log('DataStreams URL:', datastreamsUrl);

    // Observations with temporal filter
    const observationsUrl = csapi.getObservations('datastream-456', {
      phenomenonTime: '2024-01-01/2024-01-31',
      limit: 1000,
    });
    console.log('Observations URL:', observationsUrl);

    // Commands for a control stream
    const commandsUrl = csapi.getCommands('controlstream-789', {
      resultTime: '2024-01-01/..',
    });
    console.log('Commands URL:', commandsUrl);
  } else {
    console.log('Endpoint does not support CSAPI');
  }
}

exploreCSAPIEndpoint();
```

### B. Conformance Class URIs Reference

**Part 1 - Feature Resources:**

```
Core:              http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/core
System:            http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/system
Deployment:        http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/deployment
Procedure:         http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/procedure
Sampling Feature:  http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/samplingFeature
Property:          http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/property
```

**Part 2 - Dynamic Data:**

```
Core:              http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/core
DataStream:        http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/datastream
Observation:       http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/observation
Control Stream:    http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/controlstream
Command:           http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/command
```

### C. Collection Metadata Example

**Complete Example:**

```json
{
  "id": "sensors-collection",
  "title": "Weather Sensors Network",
  "description": "Network of weather sensors across the region",
  "extent": {
    "spatial": {
      "bbox": [[-180, -90, 180, 90]],
      "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
    },
    "temporal": {
      "interval": [["2020-01-01T00:00:00Z", null]],
      "trs": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"
    }
  },
  "links": [
    {
      "href": "https://server.com/api/collections/sensors-collection",
      "rel": "self",
      "type": "application/json"
    },
    {
      "href": "https://server.com/api/collections/sensors-collection/systems",
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/systems",
      "type": "application/geo+json"
    },
    {
      "href": "https://server.com/api/collections/sensors-collection/datastreams",
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/datastreams",
      "type": "application/swe+json"
    },
    {
      "href": "https://server.com/api/collections/sensors-collection/observations",
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/observations",
      "type": "application/swe+json"
    }
  ],
  "csapi_resources": {
    "systems": {
      "link": {
        "href": "https://server.com/api/collections/sensors-collection/systems",
        "rel": "systems",
        "type": "application/geo+json"
      },
      "operations": ["GET", "POST", "PUT", "DELETE"]
    },
    "deployments": {
      "link": {
        "href": "https://server.com/api/collections/sensors-collection/deployments",
        "rel": "deployments",
        "type": "application/geo+json"
      },
      "operations": ["GET", "POST"]
    },
    "datastreams": {
      "link": {
        "href": "https://server.com/api/collections/sensors-collection/datastreams",
        "rel": "datastreams",
        "type": "application/swe+json"
      },
      "operations": ["GET", "POST", "PUT", "DELETE"],
      "schemas": {
        "encoding": "json",
        "definition": {
          "href": "https://server.com/api/collections/sensors-collection/datastreams/schema",
          "type": "application/swe+json"
        }
      }
    },
    "observations": {
      "link": {
        "href": "https://server.com/api/collections/sensors-collection/observations",
        "rel": "observations",
        "type": "application/swe+json"
      },
      "operations": ["GET", "POST"]
    }
  }
}
```

---

**Analysis Complete:** This document provides the complete blueprint for integrating CSAPI into `OgcApiEndpoint` following the proven EDR pattern. Total integration footprint: ~65 lines across 3 files. Ready for implementation.
