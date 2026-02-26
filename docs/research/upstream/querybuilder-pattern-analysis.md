# QueryBuilder Pattern Analysis

**Purpose:** Document the QueryBuilder pattern used in ogc-client for API-specific query operations.

**Context:** Previous work used the term "navigator" - this was incorrect. The actual pattern is called "QueryBuilder" and this document explains how it works.

**Date:** 2026-01-30

---

## Table of Contents

1. [Terminology Correction](#1-terminology-correction)
2. [What is a QueryBuilder](#2-what-is-a-querybuilder)
3. [QueryBuilder Lifecycle](#3-querybuilder-lifecycle)
4. [EDRQueryBuilder Deep Dive](#4-edrquerybuilder-deep-dive)
5. [State Management](#5-state-management)
6. [Caching Strategy](#6-caching-strategy)
7. [Interface vs Implementation](#7-interface-vs-implementation)
8. [Resource Availability Checking](#8-resource-availability-checking)
9. [URL Construction Pattern](#9-url-construction-pattern)
10. [Method Patterns](#10-method-patterns)
11. [CSAPI QueryBuilder Design](#11-csapi-querybuilder-design)

---

## 1. Terminology Correction

### ❌ Previous (Incorrect) Terminology

In previous implementation attempts at https://github.com/OS4CSAPI/ogc-client-CSAPI, the term **"navigator"** was used:

```typescript
// ❌ Previous incorrect naming
class CSAPINavigator { ... }
endpoint.csapi() // returns a "navigator"
```

**Origin:** Unknown - possibly invented term, not from upstream sources.

### ✅ Correct Terminology

The actual pattern in ogc-client is **"QueryBuilder"**:

```typescript
// ✅ Correct naming from upstream
class EDRQueryBuilder { ... }
endpoint.edr() // returns EDRQueryBuilder
```

**Source:**

- PR #114 implementation
- Class name: `EDRQueryBuilder`
- File: `src/ogc-api/edr/url_builder.ts`

### Why This Matters

1. **Code Review:** Maintainers expect "QueryBuilder" naming
2. **Consistency:** Matches existing EDR implementation
3. **Clarity:** "QueryBuilder" describes what it does (builds query URLs)
4. **Documentation:** All references must use correct term

### Corrected CSAPI Naming

```typescript
// What CSAPI should use:
class CSAPIQueryBuilder { ... }

// Method naming:
endpoint.csapi(collectionId): Promise<CSAPIQueryBuilder>

// User code:
const builder = await endpoint.csapi('sensors');
const systems = await builder.getSystems();
```

---

## 2. What is a QueryBuilder?

### Definition

A **QueryBuilder** is a standalone class that:

1. Encapsulates collection-specific metadata
2. Provides methods to build query URLs
3. Optionally executes queries and returns typed results
4. Validates parameters against collection capabilities

### Not a Subclass

**Critical:** QueryBuilder is NOT a subclass of OgcApiEndpoint.

```typescript
// ❌ NOT how it works
class EDRQueryBuilder extends OgcApiEndpoint { ... }

// ✅ How it actually works
class EDRQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) { ... }
}
```

### Relationship to Endpoint

```
User Code
   ↓
OgcApiEndpoint.edr(collectionId)
   ↓
Creates/returns EDRQueryBuilder
   ↓
User calls builder.buildPositionDownloadUrl(...)
```

**Pattern:** Factory method on endpoint → QueryBuilder instance → Query methods

### Responsibilities

| Responsibility             | QueryBuilder | Endpoint |
| -------------------------- | ------------ | -------- |
| Fetch collection metadata  | ❌           | ✅       |
| Cache QueryBuilders        | ❌           | ✅       |
| Check endpoint conformance | ❌           | ✅       |
| Build query URLs           | ✅           | ❌       |
| Validate query parameters  | ✅           | ❌       |
| Execute queries            | ✅           | ❌       |
| Store collection state     | ✅           | ❌       |

**Separation of concerns:** Endpoint = discovery, QueryBuilder = querying

---

## 3. QueryBuilder Lifecycle

### Phase 1: Instantiation

**Triggered by:** `await endpoint.edr(collectionId)`

```typescript
// In OgcApiEndpoint
public async edr(collection_id: string): Promise<EDRQueryBuilder> {
  // 1. Check conformance
  if (!this.hasEnvironmentalDataRetrieval) {
    throw new EndpointError('Endpoint does not support EDR');
  }

  // 2. Check cache
  const cache = this.collection_id_to_edr_builder_;
  if (cache.has(collection_id)) {
    return cache.get(collection_id);
  }

  // 3. Fetch collection info
  const collection = await this.getCollectionInfo(collection_id);

  // 4. Instantiate QueryBuilder
  const result = new EDRQueryBuilder(collection);

  // 5. Cache for reuse
  cache.set(collection_id, result);

  // 6. Return
  return result;
}
```

**Steps:**

1. Conformance check (fail fast if not supported)
2. Cache lookup (avoid re-fetching metadata)
3. Metadata fetch (HTTP request for collection details)
4. Instantiation (new QueryBuilder with metadata)
5. Caching (store for future calls)
6. Return (builder ready to use)

### Phase 2: Configuration

**In constructor:**

```typescript
class EDRQueryBuilder {
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
  public links: Array<{...}> = [];

  constructor(private collection: OgcApiCollectionInfo) {
    // Validate required data exists
    if (!collection.data_queries) {
      throw new Error('No data queries found, so cannot issue EDR queries');
    }

    // Extract capabilities
    this.supported_query_types = {
      area: collection.data_queries.area !== undefined,
      locations: collection.data_queries.locations !== undefined,
      // ... etc
    };

    // Store metadata
    this.supported_parameters = collection.parameter_names;
    this.supported_crs = collection.crs;
    this.links = collection.links;
  }
}
```

**Actions:**

- Validate collection has required data
- Extract query type support flags
- Store supported parameters
- Store supported CRS codes
- Store links for URL construction

### Phase 3: Usage

**User calls query methods:**

```typescript
const builder = await endpoint.edr('temperature');

// Check what's supported
if (builder.supported_queries.has('position')) {
  // Build query URL
  const url = builder.buildPositionDownloadUrl(
    { lon: -73.935242, lat: 40.730610 },
    { datetime: new Date('2024-01-01'), parameter_name: ['temperature'] }
  );

  // Or execute query directly
  const data = await builder.getPosition(...);
}
```

### Phase 4: Reuse

**Subsequent calls to same collection:**

```typescript
// First call: fetches metadata, creates builder, caches
const builder1 = await endpoint.edr('temperature');

// Second call: returns cached builder (no HTTP request)
const builder2 = await endpoint.edr('temperature');

// builder1 === builder2 (same instance)
```

**Performance:** Caching prevents redundant metadata fetches.

---

## 4. EDRQueryBuilder Deep Dive

### Class Structure

```typescript
// File: src/ogc-api/edr/url_builder.ts

export default class EDRQueryBuilder {
  // Private state
  private supported_query_types: {...};
  private collection: OgcApiCollectionInfo;

  // Public metadata
  public supported_parameters: Record<string, EdrParameterInfo> = {};
  public supported_crs: CrsCode[] = [];
  public links: Array<{...}> = [];

  // Constructor
  constructor(private collection: OgcApiCollectionInfo) { ... }

  // Capability getter
  get supported_queries(): Set<DataQueryType> { ... }

  // Query building methods
  buildPositionDownloadUrl(...): string { ... }
  buildAreaDownloadUrl(...): string { ... }
  buildCubeDownloadUrl(...): string { ... }
  buildTrajectoryDownloadUrl(...): string { ... }
  buildCorridorDownloadUrl(...): string { ... }
  buildRadiusDownloadUrl(...): string { ... }
  buildLocationsDownloadUrl(...): string { ... }

  // Query execution methods
  async getPosition(...): Promise<EdrData> { ... }
  async getArea(...): Promise<EdrData> { ... }
  // ... etc
}
```

### Properties Exposed

**Read-only access to collection capabilities:**

```typescript
const builder = await endpoint.edr('temperature');

// What query types are supported?
builder.supported_queries; // Set<'position' | 'area' | 'cube' | ...>

// What parameters can I query?
builder.supported_parameters; // { temperature: {...}, humidity: {...}, ... }

// What CRS are supported?
builder.supported_crs; // ['EPSG:4326', 'EPSG:3857', ...]

// What links are available?
builder.links; // [{ rel: 'items', href: '...' }, ...]

// Original collection metadata
builder.collection; // Full OgcApiCollectionInfo object
```

### Method Pattern: Build URL

**Each query type has a build method:**

```typescript
buildPositionDownloadUrl(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}
): string {
  // 1. Check if query type is supported
  if (!this.supported_query_types.position) {
    throw new Error('Collection does not support position queries');
  }

  // 2. Get base URL from collection links
  const url = new URL(this.collection.data_queries?.position?.link.href);

  // 3. Add required parameters
  url.searchParams.set('coords', `POINT(${coords.lon} ${coords.lat})`);

  // 4. Add optional parameters with validation
  if (optional_params.parameter_name) {
    // Validate parameters exist on collection
    for (const param of optional_params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(`Parameter '${param}' not supported`);
      }
    }
    url.searchParams.set('parameter-name', optional_params.parameter_name.join(','));
  }

  if (optional_params.crs) {
    // Validate CRS is supported
    if (!this.supported_crs.includes(optional_params.crs)) {
      throw new Error(`CRS '${optional_params.crs}' not supported`);
    }
    url.searchParams.set('crs', optional_params.crs);
  }

  // 5. Return URL string
  return url.toString();
}
```

**Pattern steps:**

1. Capability check
2. Base URL from links
3. Required params
4. Optional params with validation
5. Return URL

### Method Pattern: Execute Query

**Some methods execute the query and return typed data:**

```typescript
async getPosition(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}
): Promise<EdrData> {
  // 1. Build URL
  const url = this.buildPositionDownloadUrl(coords, optional_params);

  // 2. Fetch data
  const response = await fetch(url);

  // 3. Parse and return
  const data = await response.json();
  return data as EdrData;
}
```

**Pattern:** Build URL → Fetch → Parse → Return

---

## 5. State Management

### Instance State

Each QueryBuilder instance stores:

```typescript
class EDRQueryBuilder {
  // Collection metadata (passed in constructor)
  private collection: OgcApiCollectionInfo;

  // Derived state (computed from collection)
  private supported_query_types: {...};
  public supported_parameters: {...};
  public supported_crs: string[];
  public links: Array<...>;
}
```

**Immutable after construction** - state is set in constructor and never changes.

### No Shared State

Each collection gets its own QueryBuilder instance:

```typescript
const builder1 = await endpoint.edr('temperature'); // Instance for 'temperature'
const builder2 = await endpoint.edr('humidity'); // Instance for 'humidity'

// builder1.supported_parameters !== builder2.supported_parameters
// Each has different collection metadata
```

**Isolation:** Changes to one builder don't affect others.

### State Source: Collection Metadata

All state comes from `OgcApiCollectionInfo`:

```typescript
interface OgcApiCollectionInfo {
  id: string;
  title: string;
  description?: string;
  extent?: {...};
  crs?: CrsCode[];
  data_queries?: {
    position?: { link: { href: string } };
    area?: { link: { href: string } };
    // ... other query types
  };
  parameter_names?: Record<string, EdrParameterInfo>;
  links: Array<{...}>;
  // ... more fields
}
```

**Flow:**

1. Endpoint fetches collection document (HTTP)
2. Parses into OgcApiCollectionInfo
3. Passes to QueryBuilder constructor
4. QueryBuilder extracts and stores relevant fields

---

## 6. Caching Strategy

### Where Caching Happens

**In the endpoint, NOT in the QueryBuilder:**

```typescript
// OgcApiEndpoint class
class OgcApiEndpoint {
  // Cache: Map<collection_id, QueryBuilder_instance>
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();

  public async edr(collection_id: string): Promise<EDRQueryBuilder> {
    const cache = this.collection_id_to_edr_builder_;

    // Check cache first
    if (cache.has(collection_id)) {
      return cache.get(collection_id); // Return cached instance
    }

    // Create new instance
    const collection = await this.getCollectionInfo(collection_id);
    const result = new EDRQueryBuilder(collection);

    // Cache for future calls
    cache.set(collection_id, result);

    return result;
  }
}
```

### Cache Key

**Collection ID** is the cache key:

```typescript
endpoint.edr('temperature'); // Creates and caches builder for 'temperature'
endpoint.edr('temperature'); // Returns cached builder
endpoint.edr('humidity'); // Creates and caches NEW builder for 'humidity'
```

### Cache Benefits

1. **Performance:** Avoid redundant HTTP requests for collection metadata
2. **Consistency:** Same collection always returns same builder instance
3. **Memory:** Reasonable - one builder per collection accessed

### Cache Lifetime

**Tied to endpoint instance lifetime:**

```typescript
const endpoint1 = new OgcApiEndpoint('https://api.example.com');
await endpoint1.edr('temp'); // Creates and caches

const endpoint2 = new OgcApiEndpoint('https://api.example.com');
await endpoint2.edr('temp'); // NEW cache, creates builder again

// endpoint1's cache !== endpoint2's cache
```

**Scope:** Per-endpoint instance, not global.

---

## 7. Interface vs Implementation

### No Formal Interface

EDRQueryBuilder has **no interface definition**. It's a concrete class.

```typescript
// ❌ NOT in the code
interface IEDRQueryBuilder { ... }
class EDRQueryBuilder implements IEDRQueryBuilder { ... }

// ✅ What actually exists
class EDRQueryBuilder { ... }
```

### Public API Surface

**Public API = exported class + public members:**

```typescript
export default class EDRQueryBuilder {
  // Public properties
  public supported_parameters: Record<string, EdrParameterInfo>;
  public supported_crs: CrsCode[];
  public links: Array<...>;

  // Public getters
  get supported_queries(): Set<DataQueryType>;

  // Public methods
  buildPositionDownloadUrl(...): string;
  buildAreaDownloadUrl(...): string;
  // ... etc

  async getPosition(...): Promise<EdrData>;
  // ... etc
}
```

### Internal Implementation

**Private members are implementation details:**

```typescript
class EDRQueryBuilder {
  // Private - users can't access
  private supported_query_types: {...};
  private collection: OgcApiCollectionInfo;

  // Helper methods (could be private, currently aren't)
  // None in current implementation - validation inline
}
```

### Why No Interface?

1. **Simplicity:** Single implementation, no need for abstraction
2. **Flexibility:** Can add methods without interface changes
3. **TypeScript:** Class itself provides type checking

### Implications for CSAPI

**Follow the same pattern:**

```typescript
// ✅ What CSAPI should do
export default class CSAPIQueryBuilder {
  public supported_resources: Set<string>;
  // ... public members

  async getSystems(...): Promise<System[]>;
  async getDeployments(...): Promise<Deployment[]>;
  // ... etc
}

// ❌ Don't create unnecessary interface
interface ICSAPIQueryBuilder { ... }
```

---

## 8. Resource Availability Checking

### Constructor Validation

**Fail fast if required data is missing:**

```typescript
class EDRQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {
    // Validate collection has EDR-specific data
    if (!collection.data_queries) {
      throw new Error('No data queries found, so cannot issue EDR queries');
    }

    // Extract what's available
    this.supported_query_types = {
      area: collection.data_queries.area !== undefined,
      cube: collection.data_queries.cube !== undefined,
      // ... etc
    };
  }
}
```

**If collection doesn't support EDR at all → throw immediately.**

### Runtime Capability Checks

**Each method validates its query type is supported:**

```typescript
buildAreaDownloadUrl(...): string {
  // Check before building URL
  if (!this.supported_query_types.area) {
    throw new Error('Collection does not support area queries');
  }

  // Proceed with URL building
  const url = new URL(this.collection.data_queries?.area?.link.href);
  // ...
}
```

**If query type not available on this collection → throw helpful error.**

### User-Facing Capability Info

**Expose what's available before calling methods:**

```typescript
const builder = await endpoint.edr('temperature');

// Check what query types are supported
console.log(builder.supported_queries);
// Set { 'position', 'cube', 'area' }

// User can check before calling
if (builder.supported_queries.has('trajectory')) {
  const url = builder.buildTrajectoryDownloadUrl(...);
} else {
  console.log('Trajectory queries not supported on this collection');
}
```

**Pattern:** Expose capabilities → user checks → user calls appropriate methods.

### Parameter Validation

**Validate parameters against collection metadata:**

```typescript
buildPositionDownloadUrl(coords, optional_params): string {
  // ...

  if (optional_params.parameter_name) {
    for (const param of optional_params.parameter_name) {
      // Validate parameter exists
      if (!this.supported_parameters[param]) {
        throw new Error(
          `The following parameter name does not exist on this collection: '${param}'.`
        );
      }
    }
    url.searchParams.set('parameter-name', optional_params.parameter_name.join(','));
  }

  if (optional_params.crs) {
    // Validate CRS is supported
    if (!this.supported_crs.includes(optional_params.crs)) {
      throw new Error(
        `The following crs does not exist on this collection: '${optional_params.crs}'.`
      );
    }
    url.searchParams.set('crs', optional_params.crs);
  }

  // ...
}
```

**Pattern:** Check optional params against metadata before adding to URL.

---

## 9. URL Construction Pattern

### Base URL from Collection Links

**Always get URLs from collection metadata, never construct:**

```typescript
// ✅ Good - from collection links
const url = new URL(this.collection.data_queries?.position?.link.href);

// ❌ Bad - manual construction
const url = new URL(`${baseUrl}/collections/${collectionId}/position`);
```

**Why:** OGC APIs are hypermedia-driven. Servers can use any URL structure.

### Query Parameter Addition

**Use native URL API:**

```typescript
const url = new URL(baseUrl);

// Set required parameters
url.searchParams.set('coords', 'POINT(-73.935242 40.730610)');

// Set optional parameters conditionally
if (optional_params.datetime) {
  url.searchParams.set('datetime', formatDatetime(optional_params.datetime));
}

if (optional_params.parameter_name) {
  url.searchParams.set(
    'parameter-name',
    optional_params.parameter_name.join(',')
  );
}

// Return URL string
return url.toString();
```

**Pattern:**

- Create URL object from base
- Use `searchParams.set()` for each parameter
- Arrays join with comma
- Return `url.toString()`

### Array Parameters

**Join with comma:**

```typescript
// User provides array
optional_params.parameter_name = ['temperature', 'humidity', 'pressure'];

// Join into comma-separated string
url.searchParams.set(
  'parameter-name',
  optional_params.parameter_name.join(',')
);

// Result: ?parameter-name=temperature,humidity,pressure
```

### No Manual Encoding

**URL API handles encoding automatically:**

```typescript
url.searchParams.set('coords', 'POINT(-73.935242 40.730610)');
// Automatically encodes spaces and special characters
// Result: ?coords=POINT%28-73.935242%2040.730610%29
```

---

## 10. Method Patterns

### Build URL Methods

**Pattern: Synchronous, returns string**

```typescript
buildPositionDownloadUrl(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}
): string {
  // Validate
  if (!this.supported_query_types.position) {
    throw new Error('Collection does not support position queries');
  }

  // Build
  const url = new URL(this.collection.data_queries?.position?.link.href);
  url.searchParams.set('coords', `POINT(${coords.lon} ${coords.lat})`);

  // Add optional params
  if (optional_params.datetime) {
    url.searchParams.set('datetime', formatDatetime(optional_params.datetime));
  }

  // Return
  return url.toString();
}
```

**Use case:** User wants URL to fetch themselves or use in other context.

### Execute Query Methods

**Pattern: Async, returns typed data**

```typescript
async getPosition(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}
): Promise<EdrData> {
  // Build URL using the build method
  const url = this.buildPositionDownloadUrl(coords, optional_params);

  // Fetch
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // Parse
  const data = await response.json();

  // Return typed
  return data as EdrData;
}
```

**Use case:** User wants data directly, don't care about URL.

### Parameter Patterns

**Required parameters:** Direct function parameters

```typescript
buildPositionDownloadUrl(
  coords: { lon: number; lat: number }, // Required
  optional_params = {}                   // Optional
): string
```

**Optional parameters:** Destructured options object

```typescript
interface optionalPositionParams {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: number | [number, number];
  crs?: CrsCode;
  f?: string;
}

buildPositionDownloadUrl(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {} // Default empty object
): string
```

**Validation:** Check optional params before using

```typescript
if (optional_params.parameter_name) {
  // Validate
  for (const param of optional_params.parameter_name) {
    if (!this.supported_parameters[param]) {
      throw new Error(`Parameter '${param}' not supported`);
    }
  }
  // Use
  url.searchParams.set(
    'parameter-name',
    optional_params.parameter_name.join(',')
  );
}
```

---

## 11. CSAPI QueryBuilder Design

### Class Structure

```typescript
// File: src/ogc-api/csapi/url_builder.ts

export default class CSAPIQueryBuilder {
  // Private collection metadata
  private collection: OgcApiCollectionInfo;

  // Public capability info
  public supported_resources: Set<string>;
  public links: Array<{...}>;

  constructor(private collection: OgcApiCollectionInfo) {
    // Validate collection supports CSAPI
    if (!collection.hasConnectedSystems) {
      throw new Error('Collection does not support Connected Systems API');
    }

    // Extract available resources from links
    this.supported_resources = this.extractSupportedResources();
    this.links = collection.links;
  }

  private extractSupportedResources(): Set<string> {
    const resources = new Set<string>();
    const linkRels = this.collection.links.map(l => l.rel);

    // Check for CSAPI resource link relations
    if (linkRels.includes('systems')) resources.add('systems');
    if (linkRels.includes('deployments')) resources.add('deployments');
    if (linkRels.includes('samplingFeatures')) resources.add('samplingFeatures');
    // ... etc for all 9 resources

    return resources;
  }

  // Resource access methods
  async getSystems(options?: QueryOptions): Promise<System[]> { ... }
  async getSystem(systemId: string): Promise<System> { ... }

  async getDeployments(options?: QueryOptions): Promise<Deployment[]> { ... }
  async getDeployment(deploymentId: string): Promise<Deployment> { ... }

  async getSamplingFeatures(options?: QueryOptions): Promise<SamplingFeature[]> { ... }
  async getSamplingFeature(featureId: string): Promise<SamplingFeature> { ... }

  async getProcedures(options?: QueryOptions): Promise<Procedure[]> { ... }
  async getProcedure(procedureId: string): Promise<Procedure> { ... }

  async getDatastreams(systemId: string, options?: QueryOptions): Promise<Datastream[]> { ... }
  async getDatastream(systemId: string, datastreamId: string): Promise<Datastream> { ... }

  async getObservations(datastreamId: string, options?: QueryOptions): Promise<Observation[]> { ... }

  async getControls(systemId: string, options?: QueryOptions): Promise<Control[]> { ... }

  async getControlStreams(systemId: string, options?: QueryOptions): Promise<ControlStream[]> { ... }

  async getCommands(controlStreamId: string, options?: QueryOptions): Promise<Command[]> { ... }
}
```

### Endpoint Integration

```typescript
// In src/ogc-api/endpoint.ts

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

### Usage Example

```typescript
const endpoint = new OgcApiEndpoint('https://api.example.com');

// Get QueryBuilder for collection
const builder = await endpoint.csapi('sensor-network');

// Check what resources are available
console.log(builder.supported_resources);
// Set { 'systems', 'deployments', 'samplingFeatures', 'datastreams', 'observations' }

// Fetch systems with pagination
const systems = await builder.getSystems({
  limit: 10,
  offset: 0,
  bbox: [-180, -90, 180, 90],
});

// Get specific system
const system = await builder.getSystem('system-123');

// Get datastreams for a system
const datastreams = await builder.getDatastreams('system-123', {
  limit: 5,
});

// Get observations for a datastream
const observations = await builder.getObservations('datastream-456', {
  datetime: { start: new Date('2024-01-01'), end: new Date('2024-01-31') },
  limit: 100,
});
```

### Key Differences from EDR

| Aspect      | EDR                                             | CSAPI                                                  |
| ----------- | ----------------------------------------------- | ------------------------------------------------------ |
| Query types | 7 query geometries (position, area, cube, etc.) | 9 resource types (systems, deployments, etc.)          |
| Methods     | Build URL + execute query                       | Fetch resources + fetch by ID                          |
| Nesting     | Flat queries                                    | Nested resources (system → datastreams → observations) |
| Parameters  | Geospatial (coords, bbox, z)                    | Standard OGC API (limit, offset, bbox, datetime)       |
| Validation  | Check query type + parameters                   | Check resource availability + parameters               |

### Method Pattern for CSAPI

**List resource:**

```typescript
async getSystems(options: QueryOptions = {}): Promise<System[]> {
  // 1. Check resource is available
  if (!this.supported_resources.has('systems')) {
    throw new Error('Systems resource not available on this collection');
  }

  // 2. Get base URL from links
  const baseUrl = getLinkUrl(this.collection, 'systems', '');
  if (!baseUrl) {
    throw new Error('Systems link not found in collection');
  }

  // 3. Build URL with query params
  const url = new URL(baseUrl);
  if (options.limit) url.searchParams.set('limit', options.limit.toString());
  if (options.offset) url.searchParams.set('offset', options.offset.toString());
  if (options.bbox) url.searchParams.set('bbox', options.bbox.join(','));

  // 4. Fetch
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  // 5. Parse and return
  const data = await response.json();
  return data.items as System[];
}
```

**Get by ID:**

```typescript
async getSystem(systemId: string): Promise<System> {
  // 1. Check resource is available
  if (!this.supported_resources.has('systems')) {
    throw new Error('Systems resource not available on this collection');
  }

  // 2. Build URL for specific system
  const baseUrl = getLinkUrl(this.collection, 'systems', '');
  const url = `${baseUrl}/${systemId}`;

  // 3. Fetch
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  // 4. Parse and return
  const data = await response.json();
  return data as System;
}
```

**Nested resource:**

```typescript
async getDatastreams(
  systemId: string,
  options: QueryOptions = {}
): Promise<Datastream[]> {
  // 1. Check resource is available
  if (!this.supported_resources.has('datastreams')) {
    throw new Error('Datastreams resource not available on this collection');
  }

  // 2. Build nested URL: /systems/{id}/datastreams
  const baseUrl = getLinkUrl(this.collection, 'systems', '');
  const url = new URL(`${baseUrl}/${systemId}/datastreams`);

  // 3. Add query params
  if (options.limit) url.searchParams.set('limit', options.limit.toString());
  if (options.offset) url.searchParams.set('offset', options.offset.toString());

  // 4. Fetch
  const response = await fetch(url.toString());
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  // 5. Parse and return
  const data = await response.json();
  return data.items as Datastream[];
}
```

---

## Conclusion

### Key Takeaways

1. **Terminology:** It's "QueryBuilder", not "navigator"
2. **Pattern:** Standalone class, not endpoint subclass
3. **Lifecycle:** Created by endpoint factory method, cached by collection ID
4. **State:** Immutable after construction, derived from collection metadata
5. **Validation:** Fail fast in constructor, validate params in methods
6. **URLs:** Always from links, never constructed manually
7. **Methods:** Build URL (sync) or execute query (async)
8. **Caching:** In endpoint, keyed by collection ID

### CSAPI Implementation

**Follows same pattern:**

- Class: `CSAPIQueryBuilder`
- Factory: `endpoint.csapi(collectionId)`
- Methods: One per resource type (`getSystems`, `getDeployments`, etc.)
- Validation: Check `supported_resources` before accessing
- URLs: From collection links
- Caching: Map in endpoint

**Estimated size:** ~400-500 lines for QueryBuilder class (9 resources × ~50 lines each)

**Total with tests:** ~2500-3000 lines in csapi/ subfolder
