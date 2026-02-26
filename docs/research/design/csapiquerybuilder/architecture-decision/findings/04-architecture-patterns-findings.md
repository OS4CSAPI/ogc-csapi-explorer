# Research Plan 04: Architecture Patterns in ogc-client - FINDINGS

**Research Question:** What are the established architectural patterns in ogc-client, and do they favor single-class or multi-class designs?

**Source Document:** [docs/research/upstream/architecture-patterns-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/architecture-patterns-analysis.md)

**Date Completed:** February 4, 2026

---

## Executive Summary

**CRITICAL FINDING:** ogc-client uses a **universal single-class pattern** for ALL OGC API implementations. Zero multi-class examples exist. The pattern is lightweight, modular, and proven across WFS, WMS, WMTS, EDR.

**Key Architectural Characteristics:**

- **Composition over Inheritance:** No endpoint subclassing
- **QueryBuilder Pattern:** Single standalone class per API family
- **Minimal Core Impact:** ~115 lines to integrate new API (~55 lines to endpoint.ts, ~10 lines to info.ts, ~50 lines to model.ts)
- **Link-Driven Navigation:** Follow hypermedia, never construct URLs
- **Factory Method + Caching:** Map-based caching by collection ID
- **Isolated Implementation:** Each API in own subfolder

**Pattern Consistency:** 100% - ALL implementations use identical pattern

**For CSAPI:** Follow EDR pattern exactly. Single CSAPIQueryBuilder class with 9 resource query methods.

---

## Finding 1: Universal Single-Class Pattern

### Evidence from All Implementations

**1. EDR Implementation:**

```
src/ogc-api/edr/
├── url_builder.ts      # Single EDRQueryBuilder class (561 lines)
├── model.ts            # EDR-specific types
└── helpers.ts          # Utility functions
```

**2. Features Implementation (Implicit in endpoint.ts):**

- Single `getCollectionItemsUrl()` method
- No separate FeaturesQueryBuilder class
- Direct URL building in endpoint

**3. Tiles Implementation (Implicit in endpoint.ts):**

- Single `getTileUrl()` method
- No separate TilesQueryBuilder class
- Direct URL building in endpoint

**4. Styles Implementation (Implicit in endpoint.ts):**

- Single `getStyleUrl()` method
- No separate StylesQueryBuilder class
- Direct URL building in endpoint

### Pattern Structure (Consistent Across All)

**Core Components:**

1. **Conformance Check Function** (`info.ts`)
2. **Capability Getter** (`endpoint.ts`)
3. **Collection Filter Getter** (`endpoint.ts`)
4. **Factory Method with Caching** (`endpoint.ts`)
5. **Standalone QueryBuilder Class** (subfolder)

**Integration Code: ~115 lines across 3 files**

| File                      | Lines Added    | Purpose                            |
| ------------------------- | -------------- | ---------------------------------- |
| `src/ogc-api/info.ts`     | ~10            | Conformance check function         |
| `src/ogc-api/endpoint.ts` | ~55            | Getters + factory method + caching |
| `src/ogc-api/model.ts`    | ~50            | Collection metadata enrichment     |
| **Total Core Impact**     | **~115 lines** | **Minimal modification**           |

### QueryBuilder Structure (Consistent Pattern)

**Standard Structure:**

```typescript
export default class {APIName}QueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {
    // Validate collection supports API
    // Extract links and capabilities
    // Immutable after construction
  }

  // Query methods (50-100 lines each)
  async query{Type1}(params): Promise<URL> { ... }
  async query{Type2}(params): Promise<URL> { ... }
  // ... more query types
}
```

**EDR Example:**

```typescript
export default class EDRQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {
    if (!collection.data_queries) {
      throw new Error('No data queries found');
    }
  }

  // 7 query type methods
  buildPositionDownloadUrl(coords, optional_params) { ... }
  buildAreaDownloadUrl(coords, optional_params) { ... }
  buildRadiusDownloadUrl(coords, radius, optional_params) { ... }
  buildCubeDownloadUrl(bbox, optional_params) { ... }
  buildTrajectoryDownloadUrl(coords, optional_params) { ... }
  buildCorridorDownloadUrl(coords, width, optional_params) { ... }
  buildItemsDownloadUrl(optional_params) { ... }
}
```

**Class Size: 561 lines for 7 query types = ~80 lines per query type**

### Key Architectural Principle: Composition Over Inheritance

**❌ NOT Used (Inheritance):**

```typescript
// This pattern is NEVER used in ogc-client
class EDREndpoint extends OgcApiEndpoint {
  buildPositionDownloadUrl() { ... }
}
```

**✅ Used Universally (Composition):**

```typescript
// This pattern is ALWAYS used
class OgcApiEndpoint {
  async edr(collectionId): Promise<EDRQueryBuilder> {
    return new EDRQueryBuilder(collection);
  }
}

class EDRQueryBuilder {
  constructor(collection: OgcApiCollectionInfo) { ... }
  buildPositionDownloadUrl() { ... }
}
```

**Advantages:**

1. **Minimal Core Impact:** Core endpoint class stays lean
2. **Isolation:** Each API family is self-contained
3. **Clarity:** Clear separation of concerns
4. **Testability:** QueryBuilders are independently testable
5. **Maintainability:** Changes to one API don't affect others

### Answer to Key Question: Multi-Class Examples?

**ANSWER: ZERO multi-class implementations exist**

**All implementations use exactly one of these patterns:**

1. **Standalone QueryBuilder Class** (EDR)

   - Single class with all query types
   - Helper functions allowed
   - No helper classes for delegation

2. **Direct Endpoint Methods** (Features, Tiles, Styles)
   - Simple APIs with 1-2 query types
   - Methods directly in OgcApiEndpoint
   - No separate QueryBuilder class needed

**NO implementations use:**

- Multiple QueryBuilder classes
- Multiple resource client classes
- Facade pattern with delegation
- Sub-resource classes
- Nested QueryBuilder hierarchy

---

## Finding 2: Factory Method Pattern (Universal)

### Consistent Signature Across All Implementations

**Pattern:**

```typescript
public async {apiName}(collection_id: string): Promise<{API}QueryBuilder>
```

**Examples:**

**EDR:**

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

**CSAPI (Projected):**

```typescript
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
```

### Standard Factory Method Structure (7 Steps)

**Step 1: Conformance Guard**

```typescript
if (!this.hasEnvironmentalDataRetrieval) {
  throw new EndpointError('Endpoint does not support EDR');
}
```

**Step 2: Check Cache**

```typescript
const cache = this.collection_id_to_edr_builder_;
if (cache.has(collection_id)) {
  return cache.get(collection_id);
}
```

**Step 3: Fetch Collection Metadata**

```typescript
const collection = await this.getCollectionInfo(collection_id);
```

**Step 4: Instantiate QueryBuilder**

```typescript
const result = new EDRQueryBuilder(collection);
```

**Step 5: Cache Instance**

```typescript
cache.set(collection_id, result);
```

**Step 6: Return**

```typescript
return result;
```

**Step 7: Cache Declaration (Class-Level)**

```typescript
private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> = new Map();
```

### Why Map-Based Caching?

**Performance:**

- Avoid repeated collection metadata fetches
- Avoid repeated QueryBuilder instantiation
- Collection metadata is immutable (safe to cache)

**Pattern:**

- Cache key: `collection_id` (string)
- Cache value: QueryBuilder instance
- Cache lifetime: Endpoint instance lifetime
- No cache invalidation needed

**For CSAPI:**

```typescript
private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();
```

---

## Finding 3: Conformance-Based Capability Detection

### Two-Level Capability Checking

**Level 1: Endpoint-Level (Conformance Classes)**

Check if service supports API family:

```typescript
// src/ogc-api/info.ts
export function checkHasEnvironmentalDataRetrieval([conformance]: [
  ConformanceClass[]
]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core'
    ) > -1
  );
}

// src/ogc-api/endpoint.ts
get hasEnvironmentalDataRetrieval(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasEnvironmentalDataRetrieval
  );
}
```

**Level 2: Collection-Level (Metadata)**

Check if specific collection supports API operations:

```typescript
const collection = await this.getCollectionInfo(collection_id);
if (!collection.data_queries) {
  throw new Error('No data queries found, so cannot issue EDR queries');
}
```

### Conformance Check Patterns

**Pattern 1: Single Conformance Class**

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

**Pattern 2: Multiple Conformance Classes (OR)**

```typescript
export function checkStyleConformance(conformance: ConformanceClass[]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-styles-1/0.0/conf/core'
    ) > -1 ||
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-styles-1/1.0/conf/core'
    ) > -1
  );
}
```

**Pattern 3: Conformance + Collection Check (AND)**

```typescript
export function checkHasFeatures([collections, conformance]: [
  OgcApiCollectionInfo[],
  ConformanceClass[]
]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core'
    ) > -1 &&
    collections.some(
      (collection) => collection.itemType === 'feature' || !collection.itemType
    )
  );
}
```

### CSAPI Conformance URIs

**Core Conformance:**

```
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core
```

**Part-Specific Conformance (May be required):**

```
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system-features
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sampling-features
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/datastream-schema
```

**CSAPI Check Function:**

```typescript
export function checkHasConnectedSystems([conformance]: [ConformanceClass[]]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1
  );
}
```

### Collection Filtering Pattern

**Pattern:**

```typescript
get {api}Collections(): Promise<string[]> {
  return Promise.all([this.data, this.has{API}])
    .then(([data, hasAPI]) => (hasAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.has{Feature}))
    .then((collections) => collections.map((collection) => collection.name));
}
```

**EDR Example:**

```typescript
get edrCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasEnvironmentalDataRetrieval])
    .then(([data, hasEDR]) => (hasEDR ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasDataQueries))
    .then((collections) => collections.map((collection) => collection.name));
}
```

**CSAPI Example:**

```typescript
get csapiCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasConnectedSystems])
    .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasConnectedSystems))
    .then((collections) => collections.map((collection) => collection.name));
}
```

---

## Finding 4: Link-Driven Navigation (Hypermedia-First)

### Core Principle: NEVER Construct URLs

**❌ Bad Practice (URL Construction):**

```typescript
const itemsUrl = `${baseUrl}/collections/${collectionId}/items`;
const systemUrl = `${baseUrl}/collections/${collectionId}/systems/${systemId}`;
```

**✅ Standard Practice (Link Following):**

```typescript
const itemsUrl = getLinkUrl(collectionDoc, 'items', this.baseUrl);
const systemUrl = getLinkUrl(systemDoc, 'self', this.baseUrl);
```

### Why Link-Driven Navigation?

**1. Flexibility:**

- Server can structure URLs however it wants
- Works with non-standard URL patterns
- Supports proxies, URL rewriting, etc.

**2. Robustness:**

- Doesn't break if server changes URL structure
- Works with custom path prefixes
- Handles edge cases automatically

**3. Standard Compliance:**

- OGC APIs are hypermedia-driven (HATEOAS)
- Links are the primary navigation mechanism
- Conformance classes require specific link relations

### Link Handling Utilities

**Available Functions (`src/ogc-api/link-utils.ts`):**

**1. fetchLink() - Fetch document by following link:**

```typescript
export function fetchLink(
  doc: OgcApiDocument,
  rels: string | string[],
  baseUrl: string,
  type?: MimeType
): Promise<OgcApiDocument>;
```

**2. getLinkUrl() - Extract URL from link:**

```typescript
export function getLinkUrl(
  doc: OgcApiDocument,
  rels: string | string[],
  baseUrl: string,
  type?: MimeType,
  ignoreErrors?: boolean
): string | null;
```

**3. getLinks() - Get all matching links:**

```typescript
export function getLinks(
  doc: OgcApiDocument,
  rels: string | string[],
  type?: MimeType,
  ignoreErrors?: boolean
): Array<{ rel: string; href: string; type?: string }>;
```

**4. hasLinks() - Check if links exist:**

```typescript
export function hasLinks(doc: OgcApiDocument, rels: string | string[]): boolean;
```

### Link Relations Used

**Standard Link Relations:**

- `self` - The document itself
- `items` - Collection items endpoint
- `conformance` - Conformance classes
- `data` - Collections list
- `queryables` - Queryable properties
- `describedby` - Schema/metadata

**OGC-Specific Relations:**

- `http://www.opengis.net/def/rel/ogc/1.0/queryables`
- `http://www.opengis.net/def/rel/ogc/1.0/tilesets-vector`
- `http://www.opengis.net/def/rel/ogc/1.0/tilesets-map`

**CSAPI Relations (Projected):**

- `http://www.opengis.net/def/rel/ogc/1.0/systems`
- `http://www.opengis.net/def/rel/ogc/1.0/procedures`
- `http://www.opengis.net/def/rel/ogc/1.0/sampling-features`
- `http://www.opengis.net/def/rel/ogc/1.0/datastreams`
- `http://www.opengis.net/def/rel/ogc/1.0/observations`

### EDR Link Handling Example

```typescript
class EDRQueryBuilder {
  buildAreaDownloadUrl(coords, optional_params): string {
    // Get URL from collection's data_queries links
    const url = new URL(this.collection.data_queries?.area?.link.href);

    // Add query parameters
    url.searchParams.set('coords', coords.join(','));
    if (optional_params.datetime) {
      url.searchParams.set(
        'datetime',
        DateTimeParameterToEDRString(optional_params.datetime)
      );
    }

    return url.toString();
  }
}
```

**Key Points:**

1. URL comes from `collection.data_queries.area.link.href`
2. Base URL never constructed
3. Only query parameters added
4. Links come from collection metadata

### CSAPI Link Handling Pattern

**Collection Document Structure (Projected):**

```json
{
  "id": "sensor_collection",
  "title": "Sensor Collection",
  "links": [
    {
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/systems",
      "href": "https://example.com/collections/sensor_collection/systems",
      "type": "application/json"
    },
    {
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/sampling-features",
      "href": "https://example.com/collections/sensor_collection/samplingFeatures",
      "type": "application/json"
    }
  ]
}
```

**QueryBuilder Implementation:**

```typescript
class CSAPIQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {
    // Extract links from collection
    this.systemsUrl = getLinkUrl(
      collection,
      'http://www.opengis.net/def/rel/ogc/1.0/systems',
      this.baseUrl
    );
    this.samplingFeaturesUrl = getLinkUrl(
      collection,
      'http://www.opengis.net/def/rel/ogc/1.0/sampling-features',
      this.baseUrl
    );
    // ... more links
  }

  buildSystemsUrl(options?: QueryOptions): string {
    const url = new URL(this.systemsUrl);
    if (options?.limit) url.searchParams.set('limit', options.limit.toString());
    if (options?.offset)
      url.searchParams.set('offset', options.offset.toString());
    return url.toString();
  }
}
```

---

## Finding 5: Type Organization Hierarchy

### Three-Level Type System

**Level 1: Shared Types (`src/shared/models.ts`)**

Cross-API primitives used by ALL implementations:

```typescript
export type BoundingBox = number[];
export type CrsCode = string;
export type MimeType = string;
export type DateTimeParameter = Date | { start: Date; end?: Date };

export interface GenericEndpointInfo {
  title: string;
  description?: string;
  attribution?: string;
}
```

**Level 2: OGC API Common Types (`src/ogc-api/model.ts`)**

OGC API family types used by all OGC API implementations:

```typescript
export type ConformanceClass = string;

export interface OgcApiEndpointInfo {
  title: string;
  description?: string;
  attribution?: string;
}

export interface OgcApiCollectionInfo {
  id: string;
  title: string;
  description?: string;
  extent?: {
    spatial?: { bbox: number[][] };
    temporal?: { interval: (string | null)[][] };
  };
  links: Array<{ rel: string; href: string; type?: string }>;
  // ... more fields
}
```

**Level 3: Implementation-Specific Types (`src/ogc-api/{api}/model.ts`)**

API-specific types used only by that implementation:

```typescript
// src/ogc-api/edr/model.ts
export type WellKnownTextString = string;

export interface optionalAreaParams {
  parameter_name?: string[];
  datetime?: DateTimeParameter; // Reuses shared type
  z?: number | [number, number];
  crs?: CrsCode; // Reuses shared type
  f?: string;
}

export interface bboxWithoutVerticalAxis {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}
```

### Type Flow: General → Specific

```
src/shared/models.ts
    ↓ (imports)
src/ogc-api/model.ts
    ↓ (imports)
src/ogc-api/edr/model.ts
```

**Rule:** Types flow from general → specific. Never reverse.

### CSAPI Type Organization

**`src/shared/models.ts`:**

- No changes needed
- Reuse `BoundingBox`, `DateTimeParameter`, `CrsCode`, `MimeType`

**`src/ogc-api/model.ts`:**

```typescript
export interface OgcApiCollectionInfo {
  // ... existing fields
  hasConnectedSystems?: boolean; // Add CSAPI flag
}
```

**`src/ogc-api/csapi/model.ts`:**

```typescript
import {
  DateTimeParameter,
  BoundingBox,
  CrsCode,
} from '../../shared/models.js';

// Resource types
export interface System {
  id: string;
  name?: string;
  description?: string;
  systemType?: string;
  validTime?: DateTimeParameter;
  // ... more fields
}

export interface SamplingFeature {
  id: string;
  name?: string;
  description?: string;
  sampledFeature?: string;
  shape?: BoundingBox;
  // ... more fields
}

// Query options
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
}

// SensorML/SWE Common types
export interface SensorMLSystem {
  // ... SensorML structure
}

export interface SWECommonDataRecord {
  // ... SWE Common structure
}
```

**Estimated Size:** ~200-300 lines for 9 resource types

---

## Finding 6: File Organization Pattern

### Standard File Structure

**Pattern for Simple APIs (no QueryBuilder):**

```
src/ogc-api/
├── endpoint.ts         # Contains API methods directly
└── model.ts            # Types
```

**Pattern for Complex APIs (with QueryBuilder):**

```
src/ogc-api/{api}/
├── url_builder.ts      # {API}QueryBuilder class
├── model.ts            # API-specific types
├── helpers.ts          # Utility functions (optional)
├── url_builder.spec.ts # QueryBuilder tests
├── model.spec.ts       # Type/parsing tests
└── helpers.spec.ts     # Helper tests (if helpers exist)
```

### EDR File Structure (Reference)

```
src/ogc-api/edr/
├── url_builder.ts      # EDRQueryBuilder (561 lines)
├── model.ts            # EDR types (200 lines)
├── helpers.ts          # EDR utilities (50 lines)
├── url_builder.spec.ts # QueryBuilder tests (1500 lines)
├── model.spec.ts       # Type tests (200 lines)
└── helpers.spec.ts     # Helper tests (100 lines)
```

**Total:** ~2,600 lines (75% tests, 25% implementation)

### CSAPI File Structure (Projected)

```
src/ogc-api/csapi/
├── url_builder.ts      # CSAPIQueryBuilder (~850-950 lines)
├── model.ts            # CSAPI types (~200-300 lines)
├── helpers.ts          # Utilities (~50 lines) [if needed]
├── url_builder.spec.ts # QueryBuilder tests (~2000 lines)
├── model.spec.ts       # Type tests (~300 lines)
└── helpers.spec.ts     # Helper tests (~50 lines) [if needed]
```

**Total:** ~3,400-3,650 lines (75% tests, 25% implementation)

### Naming Conventions

**Files:**

- `url_builder.ts` - QueryBuilder class (not `query_builder.ts`)
- `model.ts` - Types
- `helpers.ts` - Utilities
- `{file}.spec.ts` - Tests

**Classes:**

- `{API}QueryBuilder` - Main class (e.g., `EDRQueryBuilder`, `CSAPIQueryBuilder`)
- No prefix/suffix beyond API name

**Methods:**

- `build{QueryType}DownloadUrl()` - EDR pattern
- `get{Resource}Url()` - Features pattern
- `build{Resource}Url()` - Alternative pattern

**CSAPI Method Names:**

```typescript
buildSystemsUrl(options?: QueryOptions): string
buildSystemUrl(systemId: string): string
buildSamplingFeaturesUrl(options?: QueryOptions): string
buildSamplingFeatureUrl(featureId: string): string
buildDatastreamsUrl(options?: QueryOptions): string
buildDatastreamUrl(datastreamId: string): string
buildObservationsUrl(options?: QueryOptions): string
buildObservationUrl(observationId: string): string
buildControlStreamsUrl(options?: QueryOptions): string
// ... more
```

---

## Finding 7: Helper Function Pattern

### Allowed Helper Organization

**✅ Helper Functions (Allowed):**

```typescript
// src/ogc-api/edr/helpers.ts
export function DateTimeParameterToEDRString(
  datetime: DateTimeParameter
): string {
  if (datetime instanceof Date) {
    return datetime.toISOString();
  }
  return `${'start' in datetime ? datetime.start.toISOString() : '..'}/${
    'end' in datetime ? datetime.end.toISOString() : '..'
  }`;
}
```

**Purpose:**

- Format conversion
- Parameter encoding
- Validation
- String manipulation

**Characteristics:**

- Pure functions
- No state
- Exported from `helpers.ts`
- Used by QueryBuilder

**❌ Helper Classes (NO Precedent):**

```typescript
// This pattern is NOT used in ogc-client
class SystemsClient {
  getSystems() { ... }
}

class DeploymentsClient {
  getDeployments() { ... }
}

class CSAPIQueryBuilder {
  systems: SystemsClient;
  deployments: DeploymentsClient;
}
```

### Why No Helper Classes?

**Reasons:**

1. **Pattern Consistency:** ALL implementations use single class
2. **Complexity:** Helper classes add unnecessary indirection
3. **Testability:** Single class easier to test
4. **API Surface:** Single class = cleaner API
5. **Maintainability:** Fewer files = easier maintenance

### CSAPI Helper Functions (Projected)

**Potential Helpers:**

```typescript
// src/ogc-api/csapi/helpers.ts

/**
 * Format datetime parameter for CSAPI queries
 */
export function formatDateTime(datetime: DateTimeParameter): string {
  if (datetime instanceof Date) {
    return datetime.toISOString();
  }
  return `${datetime.start.toISOString()}/${
    datetime.end ? datetime.end.toISOString() : '..'
  }`;
}

/**
 * Format bbox parameter for CSAPI queries
 */
export function formatBBox(bbox: BoundingBox): string {
  return bbox.join(',');
}

/**
 * Validate system ID format
 */
export function validateSystemId(systemId: string): void {
  if (!systemId || systemId.trim().length === 0) {
    throw new Error('System ID cannot be empty');
  }
}

/**
 * Parse SensorML response to System object
 */
export function parseSensorML(xml: string): System {
  // ... parsing logic
}

/**
 * Parse SWE Common datastream schema
 */
export function parseSWECommon(json: object): DatastreamSchema {
  // ... parsing logic
}
```

**Estimated Size:** ~50-100 lines (if needed)

**Note:** Many helpers may not be needed if functionality is simple enough to inline in QueryBuilder methods.

---

## Finding 8: Standard Parameter Encoding

### Common Query Parameters

**Pattern Across All Implementations:**

**1. Pagination:**

```typescript
if (options.limit !== undefined)
  url.searchParams.set('limit', options.limit.toString());
if (options.offset !== undefined)
  url.searchParams.set('offset', options.offset.toString());
```

**2. BBox:**

```typescript
if (options.bbox) url.searchParams.set('bbox', options.bbox.join(','));
```

**3. DateTime:**

```typescript
if (options.datetime) {
  const datetime = options.datetime;
  url.searchParams.set(
    'datetime',
    datetime instanceof Date
      ? datetime.toISOString()
      : `${datetime.start.toISOString()}/${
          datetime.end ? datetime.end.toISOString() : '..'
        }`
  );
}
```

**4. CRS:**

```typescript
if (options.crs) url.searchParams.set('crs', options.crs);
```

**5. Format:**

```typescript
if (options.format) url.searchParams.set('f', options.format);
```

### DateTimeParameter Encoding

**Type Definition:**

```typescript
export type DateTimeParameter = Date | { start: Date; end?: Date };
```

**Encoding Rules:**

| Input                                                            | Output                                              |
| ---------------------------------------------------------------- | --------------------------------------------------- |
| `new Date('2024-01-01')`                                         | `2024-01-01T00:00:00.000Z`                          |
| `{ start: new Date('2024-01-01'), end: new Date('2024-12-31') }` | `2024-01-01T00:00:00.000Z/2024-12-31T00:00:00.000Z` |
| `{ start: new Date('2024-01-01') }`                              | `2024-01-01T00:00:00.000Z/..`                       |

**Open-ended ranges:**

- Start only: `2024-01-01T00:00:00.000Z/..`
- End only: `../2024-12-31T00:00:00.000Z` (not common)

### BoundingBox Encoding

**Type Definition:**

```typescript
export type BoundingBox = number[];
```

**Encoding:**

```typescript
// Input: [minX, minY, maxX, maxY]
[-180, -90, 180, 90];

// Output: "bbox=-180,-90,180,90"
url.searchParams.set('bbox', bbox.join(','));
```

### CSAPI Parameter Encoding

**Standard Parameters:**

```typescript
interface QueryOptions {
  limit?: number; // ?limit=10
  offset?: number; // ?offset=20
  bbox?: BoundingBox; // ?bbox=-180,-90,180,90
  datetime?: DateTimeParameter; // ?datetime=2024-01-01T00:00:00.000Z/..
}
```

**CSAPI-Specific Parameters (Projected):**

```typescript
interface CSAPIQueryOptions extends QueryOptions {
  systemType?: string; // ?systemType=sensor
  procedure?: string; // ?procedure=proc123
  foi?: string; // ?foi=foi456 (feature of interest)
  observedProperty?: string; // ?observedProperty=temperature
  // ... more as needed
}
```

---

## Finding 9: Estimated Code Volume for CSAPI

### Breakdown by File

**Core Modifications:**

| File                      | Lines Added    | Purpose                   |
| ------------------------- | -------------- | ------------------------- |
| `src/ogc-api/info.ts`     | ~10            | Conformance check         |
| `src/ogc-api/endpoint.ts` | ~55            | Getters + factory + cache |
| `src/ogc-api/model.ts`    | ~50            | Collection metadata       |
| **Subtotal**              | **~115 lines** | **Core integration**      |

**CSAPI Implementation:**

| File             | Lines                  | Purpose                      |
| ---------------- | ---------------------- | ---------------------------- |
| `url_builder.ts` | ~850-950               | CSAPIQueryBuilder class      |
| `model.ts`       | ~200-300               | TypeScript types             |
| `helpers.ts`     | ~50-100                | Utility functions (optional) |
| **Subtotal**     | **~1,100-1,350 lines** | **Implementation**           |

**Tests:**

| File                  | Lines                  | Purpose                 |
| --------------------- | ---------------------- | ----------------------- |
| `url_builder.spec.ts` | ~2,000                 | QueryBuilder tests      |
| `model.spec.ts`       | ~300                   | Type tests              |
| `helpers.spec.ts`     | ~50-100                | Helper tests (optional) |
| **Subtotal**          | **~2,350-2,400 lines** | **Tests**               |

**Total Project Size:**

| Category           | Lines                  | Percentage |
| ------------------ | ---------------------- | ---------- |
| Core modifications | ~115                   | 3%         |
| Implementation     | ~1,100-1,350           | 32%        |
| Tests              | ~2,350-2,400           | 65%        |
| **TOTAL**          | **~3,565-3,865 lines** | **100%**   |

### Comparison to EDR

**EDR Actual:**

- Core: ~115 lines
- Implementation: ~811 lines (561 + 200 + 50)
- Tests: ~1,800 lines
- Total: ~2,726 lines

**CSAPI Projected:**

- Core: ~115 lines (same)
- Implementation: ~1,100-1,350 lines (40% more - 9 resources vs 7 query types)
- Tests: ~2,350-2,400 lines (30% more)
- Total: ~3,565-3,865 lines (40% more)

**Scaling Factor:** 9 CSAPI resources / 7 EDR queries = 1.29x → ~40% more code

---

## Finding 10: Critical Patterns to Follow

### Mandatory Patterns (Non-Negotiable)

**1. Single QueryBuilder Class**

- ✅ All implementations use single class
- ❌ Zero multi-class examples
- Pattern: One main class with all query methods

**2. Factory Method with Caching**

- ✅ Signature: `async {api}(collection_id: string): Promise<{API}QueryBuilder>`
- ✅ Map-based caching by collection_id
- ✅ Conformance guard before instantiation

**3. Composition Over Inheritance**

- ✅ QueryBuilder is standalone (not endpoint subclass)
- ✅ Endpoint contains QueryBuilder instances (composition)
- ❌ Never subclass OgcApiEndpoint

**4. Link-Driven Navigation**

- ✅ Follow links from collection metadata
- ❌ Never construct URLs from patterns
- ✅ Use `getLinkUrl()`, `fetchLink()`, etc.

**5. Conformance-Based Capability Detection**

- ✅ Check endpoint conformance classes
- ✅ Check collection metadata
- ✅ Guard factory method with conformance check

**6. Minimal Core Impact**

- ✅ ~115 lines to integrate new API
- ✅ Changes isolated to 3 files (info.ts, endpoint.ts, model.ts)
- ✅ All implementation in subfolder

**7. Type Organization Hierarchy**

- ✅ Shared types in `src/shared/models.ts`
- ✅ OGC API types in `src/ogc-api/model.ts`
- ✅ Implementation types in `src/ogc-api/{api}/model.ts`

**8. Standard Parameter Encoding**

- ✅ `limit`, `offset` for pagination
- ✅ `bbox` for spatial filter
- ✅ `datetime` for temporal filter
- ✅ Standard encoding formats

**9. Async Everywhere**

- ✅ All public methods return Promises
- ✅ Factory method is async
- ✅ Collection fetching is async

**10. TypeScript Type Safety**

- ✅ Strong typing for all resources
- ✅ Type exports in model.ts
- ✅ Interface definitions for options

### Flexible Patterns (Allowed Variation)

**1. File Organization**

- ✅ Can organize helpers differently
- ✅ Can split tests differently
- ✅ Can add additional utility files

**2. Helper Functions**

- ✅ Can use helper functions
- ✅ Can organize in separate file
- ✅ Can inline if simple

**3. Method Naming**

- ✅ Can use `build{Resource}Url()` or `get{Resource}Url()`
- ✅ Can use consistent prefix

**4. Type Organization**

- ✅ Can organize types by category
- ✅ Can split into multiple model files
- ✅ Can use interfaces vs types

---

## Synthesis: Architecture Decision Implications

### Single vs Multi-Class: Clear Answer

**Evidence from ALL implementations:**

- ✅ **Single class pattern: 100% (4/4 implementations)**

  - EDR: Single EDRQueryBuilder (561 lines, 7 query types)
  - Features: Single endpoint methods
  - Tiles: Single endpoint methods
  - Styles: Single endpoint methods

- ❌ **Multi-class pattern: 0% (0/4 implementations)**
  - Zero examples of multiple resource clients
  - Zero examples of facade + delegation
  - Zero examples of sub-resource classes

### Why Single Class Pattern is Universal

**1. Architectural Simplicity**

- One entry point per API family
- Clear API surface
- Minimal indirection

**2. Minimal Core Impact**

- ~115 lines to integrate new API
- Changes isolated to 3 files
- Core endpoint stays lean

**3. Pattern Consistency**

- Same pattern across all implementations
- Predictable structure
- Easy to understand

**4. Composition Over Inheritance**

- No subclassing complexity
- Clear separation of concerns
- Each API is isolated

**5. Proven Scalability**

- EDR: 561 lines for 7 query types = ~80 lines/type
- CSAPI: Projected ~850-950 lines for 9 resources = ~95-105 lines/resource
- Within reasonable bounds

### Risk Assessment

**Single CSAPIQueryBuilder Class:**

- ✅ **Pattern Match:** 100% consistent with upstream
- ✅ **Precedent:** Proven in EDR (similar complexity)
- ✅ **Integration:** Minimal core changes (~115 lines)
- ✅ **Maintainability:** Single file, clear structure
- ✅ **Scalability:** 850-950 lines is manageable
- 🟢 **RISK: LOW** - Follows universal pattern

**Multiple Resource Client Classes:**

- ❌ **Pattern Match:** Zero precedent in ogc-client
- ❌ **Integration:** No established integration pattern
- ❌ **Complexity:** More files, more indirection
- ❌ **Acceptance:** High risk of rejection (breaks pattern)
- ❌ **Justification:** Hard to justify vs EDR precedent
- 🔴 **RISK: HIGH** - Uncharted territory

### Recommendation for CSAPI

**STRONG RECOMMENDATION: Single CSAPIQueryBuilder class**

**Structure:**

```typescript
export default class CSAPIQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {
    // Validate and extract links
  }

  // System resources
  buildSystemsUrl(options?: QueryOptions): string { ... }
  buildSystemUrl(systemId: string): string { ... }

  // Deployment resources
  buildDeploymentsUrl(options?: QueryOptions): string { ... }
  buildDeploymentUrl(deploymentId: string): string { ... }

  // Sampling feature resources
  buildSamplingFeaturesUrl(options?: QueryOptions): string { ... }
  buildSamplingFeatureUrl(featureId: string): string { ... }

  // Procedure resources
  buildProceduresUrl(options?: QueryOptions): string { ... }
  buildProcedureUrl(procedureId: string): string { ... }

  // Property resources
  buildPropertiesUrl(options?: QueryOptions): string { ... }
  buildPropertyUrl(propertyId: string): string { ... }

  // Datastream resources
  buildDatastreamsUrl(options?: QueryOptions): string { ... }
  buildDatastreamUrl(datastreamId: string): string { ... }

  // Observation resources
  buildObservationsUrl(options?: QueryOptions): string { ... }
  buildObservationUrl(observationId: string): string { ... }

  // Control stream resources
  buildControlStreamsUrl(options?: QueryOptions): string { ... }
  buildControlStreamUrl(controlStreamId: string): string { ... }

  // Command resources
  buildCommandsUrl(options?: QueryOptions): string { ... }
  buildCommandUrl(commandId: string): string { ... }
}
```

**Estimated Size:** ~850-950 lines (9 resources × 2 methods × ~50 lines)

**File Structure:**

```
src/ogc-api/csapi/
├── url_builder.ts      # CSAPIQueryBuilder (~850-950 lines)
├── model.ts            # Types (~200-300 lines)
├── helpers.ts          # Utilities (~50-100 lines) [optional]
└── [tests]             # ~2,350 lines
```

**Integration:**

- Core changes: ~115 lines across info.ts, endpoint.ts, model.ts
- Factory method: `async csapi(collection_id: string): Promise<CSAPIQueryBuilder>`
- Pattern matches EDR exactly

**Justification:**

- 100% pattern consistency with upstream
- Proven scalable in EDR (561 lines for similar complexity)
- Minimal core impact (~115 lines)
- Low risk of rejection
- Clear, maintainable structure

---

## Key Quotes from Source Document

**On Pattern Consistency:**

> "ogc-client uses a **lightweight extension pattern** where new API families are integrated into the existing `OgcApiEndpoint` class via conformance checking functions, capability getter properties, factory methods that return specialized query builders, and minimal modifications to core files."

**On Endpoint Extension:**

> "**OgcApiEndpoint is NOT extended via inheritance.** Instead: QueryBuilder Pattern: Specialized classes (e.g., `EDRQueryBuilder`) are instantiated and returned by endpoint methods. Composition over Inheritance: Endpoint contains references to QueryBuilders, doesn't inherit from them. Standalone Classes: QueryBuilders are self-contained with no dependency on endpoint instance."

**On Link Following:**

> "**Pattern: Follow Links, Don't Construct URLs**. Why This Matters: 1. Flexibility: Server can structure URLs however it wants. 2. Robustness: Works with non-standard URL patterns. 3. Standard Compliance: OGC APIs are hypermedia-driven."

**On Implementation Size:**

> "**Total Implementation:** ~3000-3500 lines (matches projection)"

**On Critical Patterns:**

> "The ogc-client architecture uses a **lightweight, modular pattern** for adding new OGC API support: Minimal core impact (~55 lines to existing files), Isolated implementation (Each API family in its own subfolder), QueryBuilder pattern (Specialized classes for each API), Link-driven navigation (Follow hypermedia, don't construct URLs)"

---

## Answers to Research Plan Questions

### ✅ Do all OGC API implementations use single QueryBuilder classes?

**YES.** 100% of implementations (EDR, Features, Tiles, Styles) use single QueryBuilder class OR single set of endpoint methods. Zero multi-class examples.

### ✅ Are there any multi-class implementations?

**NO.** Zero multi-class implementations exist. Pattern is universal: one main class (or set of methods) per API family.

### ✅ What is the factory method pattern (consistent signature)?

**Signature:** `public async {apiName}(collection_id: string): Promise<{API}QueryBuilder>`

**Structure:**

1. Conformance guard
2. Check cache (Map by collection_id)
3. Fetch collection metadata
4. Instantiate QueryBuilder
5. Cache and return

**Example:** `public async edr(collection_id: string): Promise<EDRQueryBuilder>`

### ✅ How are types organized across implementations?

**Three-level hierarchy:**

1. **Shared** (`src/shared/models.ts`): Cross-API primitives (BoundingBox, DateTimeParameter, etc.)
2. **OGC API Common** (`src/ogc-api/model.ts`): OGC API family types (OgcApiCollectionInfo, etc.)
3. **Implementation-Specific** (`src/ogc-api/{api}/model.ts`): API-specific types

**Flow:** General → Specific (never reverse)

### ✅ What file structure is standard?

**For complex APIs:**

```
src/ogc-api/{api}/
├── url_builder.ts      # QueryBuilder class
├── model.ts            # Types
├── helpers.ts          # Utilities (optional)
└── [tests]
```

**Core integration:** Changes to info.ts, endpoint.ts, model.ts (~115 lines total)

### ✅ Are there helper classes alongside QueryBuilders?

**NO.** Helper **functions** are used (in helpers.ts), but NO helper **classes** for delegation. All query logic stays in single QueryBuilder class.

### ✅ How consistent are naming conventions?

**Very consistent:**

- Files: `url_builder.ts`, `model.ts`, `helpers.ts`
- Classes: `{API}QueryBuilder` (e.g., EDRQueryBuilder)
- Methods: `build{Type}Url()` or `get{Type}Url()`
- Factory: `async {api}(collection_id): Promise<{API}QueryBuilder>`
- Cache: `private collection_id_to_{api}_builder_: Map<string, {API}QueryBuilder>`

---

## Conclusion

**CRITICAL FINDING:** The architecture pattern in ogc-client is UNIVERSAL and CONSISTENT:

✅ **Single-class pattern: 100% (all implementations)**
❌ **Multi-class pattern: 0% (zero implementations)**

**For CSAPI:** Must follow single CSAPIQueryBuilder class pattern. This is not a preference—it's the established architecture that ALL implementations follow.

**Risk Assessment:**

- Single class: 🟢 LOW risk (universal pattern, proven scalable)
- Multi-class: 🔴 HIGH risk (no precedent, likely rejection)

**Estimated Implementation:**

- Core: ~115 lines (info.ts, endpoint.ts, model.ts)
- QueryBuilder: ~850-950 lines (single class, 9 resources)
- Types: ~200-300 lines
- Tests: ~2,350 lines
- **Total: ~3,565-3,865 lines**

**Recommendation:** Implement single CSAPIQueryBuilder class following exact EDR pattern. Pattern is proven, maintainer-accepted, and scalable for CSAPI's complexity.
