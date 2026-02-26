# ogc-client Architecture Patterns Analysis

**Purpose:** Document the consistent architectural patterns used in ogc-client for adding new OGC API support.

**Context:** Research for CSAPI implementation - need to understand how upstream structures their code to follow the same patterns.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [Pattern for Adding New API Support](#2-pattern-for-adding-new-api-support)
3. [Endpoint Extension Pattern](#3-endpoint-extension-pattern)
4. [Collection Capability Determination](#4-collection-capability-determination)
5. [Type Organization Strategy](#5-type-organization-strategy)
6. [Adding Methods to Endpoint](#6-adding-methods-to-endpoint)
7. [Conformance Class Checking](#7-conformance-class-checking)
8. [Shared Utilities](#8-shared-utilities)
9. [Link Handling Pattern](#9-link-handling-pattern)
10. [Pagination Implementation](#10-pagination-implementation)
11. [DateTime and BBox Parameters](#11-datetime-and-bbox-parameters)
12. [Summary: CSAPI Application](#12-summary-csapi-application)

---

## 1. Overview

**Files Analyzed:**

- `src/ogc-api/endpoint.ts` (762 lines) - Core OgcApiEndpoint class
- `src/ogc-api/info.ts` (278 lines) - Conformance and parsing utilities
- `src/index.ts` (68 lines) - Public API surface
- `src/ogc-api/edr/` - EDR implementation as reference
- `src/shared/` - Shared utilities and models

**Key Finding:** ogc-client uses a **lightweight extension pattern** where new API families are integrated into the existing `OgcApiEndpoint` class via:

1. Conformance checking functions
2. Capability getter properties
3. Factory methods that return specialized query builders
4. Minimal modifications to core files

---

## 2. Pattern for Adding New API Support

### The Standard Pattern (Based on EDR)

**Step 1: Add Conformance Check Function (`info.ts`)**

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
```

**Pattern:** Function that checks conformance array for required OGC conformance class URIs.

**Step 2: Add Capability Getter (`endpoint.ts`)**

```typescript
// src/ogc-api/endpoint.ts
get hasEnvironmentalDataRetrieval(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasEnvironmentalDataRetrieval
  );
}
```

**Pattern:** Async getter that uses conformance check function.

**Step 3: Add Collection Filter Getter (`endpoint.ts`)**

```typescript
// src/ogc-api/endpoint.ts
get edrCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasEnvironmentalDataRetrieval])
    .then(([data, hasEDR]) => (hasEDR ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasDataQueries))
    .then((collections) => collections.map((collection) => collection.name));
}
```

**Pattern:** Filters all collections to those supporting the API family.

**Step 4: Add Factory Method (`endpoint.ts`)**

```typescript
// src/ogc-api/endpoint.ts
private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> = new Map();

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

**Pattern:**

- Check conformance
- Check cache first
- Fetch collection metadata
- Instantiate QueryBuilder
- Cache and return

**Step 5: Import and Export (`index.ts`)**

```typescript
// src/index.ts
export { default as OgcApiEndpoint } from './ogc-api/endpoint.js';
export * from './ogc-api/model.js';
// EDR types would be exported from model.ts
```

**Pattern:** Export QueryBuilder and types from main index.

---

## 3. Endpoint Extension Pattern

### Key Finding: No Subclassing

**OgcApiEndpoint is NOT extended via inheritance.** Instead:

1. **QueryBuilder Pattern:** Specialized classes (e.g., `EDRQueryBuilder`) are instantiated and returned by endpoint methods
2. **Composition over Inheritance:** Endpoint contains references to QueryBuilders, doesn't inherit from them
3. **Standalone Classes:** QueryBuilders are self-contained with no dependency on endpoint instance

### Why This Matters

```typescript
// ❌ NOT how it works
class EDREndpoint extends OgcApiEndpoint { ... }

// ✅ How it actually works
class OgcApiEndpoint {
  async edr(collectionId): Promise<EDRQueryBuilder> { ... }
}

class EDRQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) { ... }
}
```

**Advantage:**

- Minimal changes to core endpoint class
- Each API family is isolated in its own subfolder
- Clear separation of concerns

---

## 4. Collection Capability Determination

### Pattern: Conformance + Collection Metadata

**Two-Level Check:**

1. **Endpoint-Level:** Conformance classes indicate API support

   ```typescript
   get hasEnvironmentalDataRetrieval(): Promise<boolean> {
     return Promise.all([this.conformanceClasses]).then(
       checkHasEnvironmentalDataRetrieval
     );
   }
   ```

2. **Collection-Level:** Collection metadata indicates resource support
   ```typescript
   const collection = await this.getCollectionInfo(collection_id);
   if (!collection.data_queries) {
     throw new Error('No data queries found, so cannot issue EDR queries');
   }
   ```

### Collection Metadata Enrichment

The `getCollectionInfo()` method fetches and enriches collection data:

```typescript
async getCollectionInfo(collectionId: string): Promise<OgcApiCollectionInfo> {
  const collectionDoc = await this.getCollectionDocument(collectionId);
  const baseInfo = parseBaseCollectionInfo(collectionDoc);

  // Fetch additional capability links
  const [queryables, sortables, tilesetsVector, tilesetsMap] = await Promise.all([
    fetchLink(collectionDoc, ['queryables', ...], this.baseUrl)
      .then(parseCollectionParameters)
      .catch(() => []),
    // ... more links
  ]);

  return {
    ...baseInfo,
    queryables,
    sortables,
    mapTileFormats,
    vectorTileFormats,
    supportedTileMatrixSets,
  };
}
```

**Pattern:**

1. Fetch collection document
2. Parse base info (id, title, extent, links)
3. Follow links to fetch additional capabilities
4. Return enriched metadata object

---

## 5. Type Organization Strategy

### Shared Types (`src/shared/models.ts`)

**Common across all API families:**

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

**Usage:** Imported by all implementations.

### API-Specific Types (`src/ogc-api/model.ts`)

**OGC API family types:**

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

### Implementation-Specific Types (`src/ogc-api/edr/model.ts`)

**EDR-only types:**

```typescript
export type WellKnownTextString = string;

export interface optionalAreaParams {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: number | [number, number];
  crs?: CrsCode;
  f?: string;
}

export interface bboxWithoutVerticalAxis {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}
```

### Organization Hierarchy

```
src/
├── shared/
│   └── models.ts          # Cross-API primitives (BoundingBox, CrsCode, etc.)
├── ogc-api/
│   ├── model.ts           # OGC API common types (OgcApiCollectionInfo, etc.)
│   └── edr/
│       └── model.ts       # EDR-specific types (query params, etc.)
```

**Rule:** Types flow from general → specific.

---

## 6. Adding Methods to Endpoint

### Pattern: Async Factory Methods

**Structure:**

```typescript
class OgcApiEndpoint {
  // 1. Private cache
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();

  // 2. Public async method
  public async edr(collection_id: string): Promise<EDRQueryBuilder> {
    // 3. Conformance guard
    if (!this.hasEnvironmentalDataRetrieval) {
      throw new EndpointError('Endpoint does not support EDR');
    }

    // 4. Check cache
    const cache = this.collection_id_to_edr_builder_;
    if (cache.has(collection_id)) {
      return cache.get(collection_id);
    }

    // 5. Fetch metadata
    const collection = await this.getCollectionInfo(collection_id);

    // 6. Instantiate
    const result = new EDRQueryBuilder(collection);

    // 7. Cache and return
    cache.set(collection_id, result);
    return result;
  }
}
```

### Method Naming Convention

- `has{Feature}`: Boolean capability checks (e.g., `hasEnvironmentalDataRetrieval`)
- `{feature}Collections`: Get collection IDs supporting feature (e.g., `edrCollections`)
- `{api}(collectionId)`: Factory for QueryBuilder (e.g., `edr(collectionId)`)
- `get{Resource}`: Fetch data (e.g., `getCollectionInfo`)

---

## 7. Conformance Class Checking

### Pattern: Dedicated Check Functions

**Location:** `src/ogc-api/info.ts`

**Structure:**

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

**Variations:**

1. **Single Conformance Class:**

   ```typescript
   export function checkTileConformance(conformance: ConformanceClass[]) {
     return (
       conformance.indexOf(
         'http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core'
       ) > -1
     );
   }
   ```

2. **Multiple Conformance Classes (OR):**

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

3. **Multiple Classes + Collection Check:**
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
         (collection) =>
           collection.itemType === 'feature' || !collection.itemType
       )
     );
   }
   ```

### Conformance URIs

**Standard Format:** `http://www.opengis.net/spec/{standard}/conf/{class}`

**Examples:**

- EDR: `http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core`
- Features: `http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core`
- Tiles: `http://www.opengis.net/spec/ogcapi-tiles-1/1.0/conf/core`

**CSAPI URIs:** Will be:

- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core`
- Plus part-specific classes

---

## 8. Shared Utilities

### URL Utilities (`src/shared/url-utils.ts`)

**Available Functions:**

```typescript
// Get base URL
export function getBaseUrl(url?: string): string | URL;

// Navigate to parent path
export function getParentPath(url: string): string | null;

// Navigate to child path
export function getChildPath(url: string, childFragment: string): string;
```

**Usage in EDR:**

```typescript
// Not heavily used - EDR gets URLs directly from collection links
const url = new URL(this.collection.data_queries?.area?.link.href);
```

### Link Utilities (`src/ogc-api/link-utils.ts`)

**Core Functions:**

```typescript
// Fetch a document by following a link relation
export function fetchLink(
  doc: OgcApiDocument,
  rels: string | string[],
  baseUrl: string,
  type?: MimeType
): Promise<OgcApiDocument>;

// Extract URL from link relation
export function getLinkUrl(
  doc: OgcApiDocument,
  rels: string | string[],
  baseUrl: string,
  type?: MimeType,
  ignoreErrors?: boolean
): string | null;

// Get all links matching criteria
export function getLinks(
  doc: OgcApiDocument,
  rels: string | string[],
  type?: MimeType,
  ignoreErrors?: boolean
): Array<{ rel: string; href: string; type?: string }>;

// Check if document has links
export function hasLinks(doc: OgcApiDocument, rels: string | string[]): boolean;
```

**Usage Pattern:**

```typescript
// Fetch collection document
const collectionDoc = await this.getCollectionDocument(collectionId);

// Follow link to queryables
const queryables = await fetchLink(
  collectionDoc,
  ['queryables', 'http://www.opengis.net/def/rel/ogc/1.0/queryables'],
  this.baseUrl
)
  .then(parseCollectionParameters)
  .catch(() => []);
```

### HTTP Utilities (`src/shared/http-utils.ts`)

Fetch wrappers with error handling (assumed to exist based on usage).

### MIME Type Utilities (`src/shared/mime-type.ts`)

**Type Checking Functions:**

```typescript
export function isMimeTypeJson(type: string): boolean;
export function isMimeTypeGeoJson(type: string): boolean;
export function isMimeTypeJsonFg(type: string): boolean;
```

**Usage:** Content negotiation and format detection.

---

## 9. Link Handling Pattern

### OGC API Link Structure

**Standard Link Object:**

```json
{
  "rel": "items",
  "href": "https://example.com/collections/foo/items",
  "type": "application/geo+json"
}
```

### Pattern: Follow Links, Don't Construct URLs

**❌ Bad (URL Construction):**

```typescript
const itemsUrl = `${baseUrl}/collections/${collectionId}/items`;
```

**✅ Good (Link Following):**

```typescript
const itemsUrl = getLinkUrl(collectionDoc, 'items', this.baseUrl);
```

### Why This Matters

1. **Flexibility:** Server can structure URLs however it wants
2. **Robustness:** Works with non-standard URL patterns
3. **Standard Compliance:** OGC APIs are hypermedia-driven

### Common Link Relations

- `self`: The document itself
- `items`: Collection items endpoint
- `conformance`: Conformance classes
- `data`: Collections list
- `queryables`: Queryable properties
- `http://www.opengis.net/def/rel/ogc/1.0/{type}`: OGC-specific relations

### Link Handling in QueryBuilder

```typescript
class EDRQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {
    // Collection links are passed in
    this.links = collection.links;
  }

  buildAreaDownloadUrl(coords, optional_params): string {
    // Extract URL from collection's data_queries links
    const url = new URL(this.collection.data_queries?.area?.link.href);
    // ... add parameters
    return url.toString();
  }
}
```

**Pattern:** Links come from collection metadata, not hardcoded paths.

---

## 10. Pagination Implementation

### Pattern: limit + offset Query Parameters

**Implementation in `getCollectionItemsUrl()`:**

```typescript
getCollectionItemsUrl(
  collectionId: string,
  options: {
    limit?: number;
    offset?: number;
    // ... other options
  } = {}
): Promise<string> {
  return this.getCollectionDocument(collectionId)
    .then((collectionDoc) => {
      const url = new URL(getLinkUrl(collectionDoc, 'items', this.baseUrl));

      // Add pagination parameters
      if (options.limit !== undefined)
        url.searchParams.set('limit', options.limit.toString());
      if (options.offset !== undefined)
        url.searchParams.set('offset', options.offset.toString());

      return url.toString();
    });
}
```

### Pagination in EDR

**Not heavily used** - EDR queries typically return complete datasets, not paginated results.

### CSAPI Pagination

CSAPI will need pagination for:

- Systems list
- Sampling features list
- Observations list

**Should follow same pattern:**

```typescript
getSystems(options: { limit?: number; offset?: number }): Promise<System[]>
```

---

## 11. DateTime and BBox Parameters

### DateTimeParameter Type

**Definition (`src/shared/models.ts`):**

```typescript
export type DateTimeParameter = Date | { start: Date; end?: Date };
```

**Usage:**

```typescript
// Single datetime
datetime: new Date('2024-01-01')

// Range
datetime: { start: new Date('2024-01-01'), end: new Date('2024-12-31') }

// Open-ended range
datetime: { start: new Date('2024-01-01') }
```

### Encoding Pattern

**In `getCollectionItemsUrl()`:**

```typescript
if (options.dateTime !== undefined) {
  const dateTime = options.dateTime;
  url.searchParams.set(
    'datetime',
    dateTime instanceof Date
      ? dateTime.toISOString()
      : `${'start' in dateTime ? dateTime.start.toISOString() : '..'}/${
          'end' in dateTime ? dateTime.end.toISOString() : '..'
        }`
  );
}
```

**Result:**

- Single: `datetime=2024-01-01T00:00:00.000Z`
- Range: `datetime=2024-01-01T00:00:00.000Z/2024-12-31T00:00:00.000Z`
- Open start: `datetime=../2024-12-31T00:00:00.000Z`
- Open end: `datetime=2024-01-01T00:00:00.000Z/..`

### BoundingBox Type

**Definition (`src/shared/models.ts`):**

```typescript
export type BoundingBox = number[];
```

**Usage:**

```typescript
boundingBox: [-180, -90, 180, 90]; // [minX, minY, maxX, maxY]
```

**Encoding:**

```typescript
if (options.extent?.length > 0)
  url.searchParams.set('bbox', options.extent.join(',').toString());
```

**Result:** `bbox=-180,-90,180,90`

### EDR DateTime Handling

EDR has its own helper:

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

**CSAPI:** Can reuse the same pattern or use shared implementation.

---

## 12. Summary: CSAPI Application

### Implementation Checklist

Based on the patterns identified, CSAPI implementation should:

#### Core Modifications

**`src/ogc-api/info.ts`:**

```typescript
export function checkHasConnectedSystems([conformance]: [ConformanceClass[]]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1
  );
}
```

**`src/ogc-api/endpoint.ts`:**

```typescript
// Capability getter
get hasConnectedSystems(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasConnectedSystems
  );
}

// Collection filter
get csapiCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasConnectedSystems])
    .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasConnectedSystems))
    .then((collections) => collections.map((collection) => collection.name));
}

// Factory method with caching
private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();

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

**`src/ogc-api/endpoint.ts` - Import:**

```typescript
import CSAPIQueryBuilder from './csapi/url_builder.js';
```

#### CSAPI Implementation

**`src/ogc-api/csapi/url_builder.ts`:**

```typescript
export default class CSAPIQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {
    // Validate collection supports CSAPI
    // Extract links and capabilities
  }

  // Resource access methods
  async getSystems(options?: QueryOptions): Promise<System[]>;
  async getSystem(systemId: string): Promise<System>;
  async getSamplingFeatures(options?: QueryOptions): Promise<SamplingFeature[]>;
  // ... more resource methods
}
```

**`src/ogc-api/csapi/model.ts`:**

```typescript
// CSAPI-specific types
export interface System { ... }
export interface SamplingFeature { ... }
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
}
```

**`src/ogc-api/model.ts`:**

```typescript
// Add to OgcApiCollectionInfo
export interface OgcApiCollectionInfo {
  // ... existing fields
  hasConnectedSystems?: boolean; // Flag for CSAPI support
}
```

#### Exports

**`src/index.ts`:**

```typescript
// No changes needed - types exported via ogc-api/model.ts
```

### File Structure

```
src/ogc-api/csapi/
├── url_builder.ts     # CSAPIQueryBuilder class
├── model.ts           # CSAPI-specific types
├── helpers.ts         # URL/param helpers (if needed)
├── url_builder.spec.ts
├── model.spec.ts
└── helpers.spec.ts
```

### Estimated Code Volume

- **`info.ts`:** +10 lines (conformance check)
- **`endpoint.ts`:** +40 lines (getters + factory method)
- **`model.ts`:** +5 lines (collection flag)
- **`csapi/url_builder.ts`:** ~400-500 lines (9 resources × ~50 lines each)
- **`csapi/model.ts`:** ~200-300 lines (types for 9 resources)
- **`csapi/helpers.ts`:** ~50 lines (if needed)
- **Tests:** ~2000-2500 lines

**Total Implementation:** ~3000-3500 lines (matches projection)

### Key Utilities to Reuse

1. **Link Following:** `getLinkUrl()`, `fetchLink()`, `getLinks()`
2. **Path Building:** `getChildPath()` (for nested resources)
3. **Type Checking:** `isMimeTypeJson()`, etc.
4. **Shared Types:** `BoundingBox`, `DateTimeParameter`, `CrsCode`

### Critical Patterns to Follow

1. ✅ **No endpoint subclassing** - use QueryBuilder pattern
2. ✅ **Cache QueryBuilder instances** - Map by collection ID
3. ✅ **Follow links, don't construct URLs** - use collection metadata
4. ✅ **Minimal core changes** - ~55 lines to endpoint.ts + info.ts
5. ✅ **Isolated implementation** - all CSAPI code in subfolder
6. ✅ **Reuse shared types** - don't reinvent primitives
7. ✅ **Standard parameter names** - limit, offset, bbox, datetime
8. ✅ **Conformance-first** - check before instantiating
9. ✅ **Async everywhere** - all public methods return Promises
10. ✅ **Type safety** - TypeScript types for all resources

---

## Conclusion

The ogc-client architecture uses a **lightweight, modular pattern** for adding new OGC API support:

- **Minimal core impact:** ~55 lines to existing files
- **Isolated implementation:** Each API family in its own subfolder
- **QueryBuilder pattern:** Specialized classes for each API
- **Link-driven navigation:** Follow hypermedia, don't construct URLs
- **Conformance-based capability detection:** Standard OGC conformance classes
- **Caching strategy:** Map-based caching of QueryBuilder instances
- **Shared utilities:** Reuse link handling, parameter encoding, type definitions

**For CSAPI:** Follow EDR's implementation pattern exactly. The architecture is proven and maintainer-accepted.

**Estimated Total Code:** ~3000-3500 lines (75% tests, 25% implementation)

**Core Modifications:** ~115 lines across 3 files (endpoint.ts, info.ts, model.ts)
