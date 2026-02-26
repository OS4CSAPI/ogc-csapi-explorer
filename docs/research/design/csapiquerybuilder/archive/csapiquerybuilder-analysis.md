# CSAPIQueryBuilder Component Analysis Report

**Component:** CSAPIQueryBuilder (Component 4)
**Analysis Date:** February 2, 2026
**Research Phase:** Session 1 - Foundation (Tasks 1-2)
**Status:** IN PROGRESS

---

## Executive Summary

This analysis report documents findings from researching the EDRQueryBuilder pattern and designing the URL construction architecture for the CSAPIQueryBuilder component. The CSAPIQueryBuilder is the largest and most critical component of the CSAPI implementation, representing approximately 70% of the total new code volume (10k-14k lines) and providing URL construction methods for all 9 CSAPI resource types.

### Key Findings

**EDRQueryBuilder Pattern:**

- Follows factory method pattern with caching at endpoint level
- Encapsulates collection metadata immutably
- Provides both URL-building and query-execution methods
- Validates capabilities at construction and method invocation
- Uses native JavaScript URL API for all URL manipulation

**Single-Class Architecture:**

- One comprehensive class containing methods for all 9 resource types
- Methods organized by resource type sections (not by CRUD operation)
- Naming convention: `get<Resource>()`, `create<Resource>()`, `update<Resource>()`, `delete<Resource>()`
- Code reuse through private helper methods for common patterns
- Separate methods for nested endpoints (not parameter-based)

**URL Construction Approach:**

- Link-based navigation (hypermedia principle) - never manually construct URLs
- Extract all base URLs from collection links
- Use native URL API for parameter assembly and encoding
- Automatic URL encoding via `searchParams.set()`
- Arrays serialize as comma-separated values

**CRUD Operations Design:**

- HTTP method mapping: GET=Read, POST=Create, PUT=Replace, PATCH=Update, DELETE=Delete
- Request bodies as typed method parameters with TypeScript interfaces
- Content-Type varies by resource: `application/geo+json` for spatial, `application/sml+json` for sensors
- Methods execute requests and return typed data (not just URLs)
- Cascade delete via optional parameter, not separate method

### Implementation Scope

**For Session 1 (Foundation completed):**

- ✅ EDRQueryBuilder pattern study (Questions 1-7)
- ✅ Single-class architecture design (Questions 8-12)
- ✅ URL construction patterns (Questions 13-18)
- ✅ CRUD operations design (Questions 19-23)

**Remaining Sessions:**

- Session 2: Query parameters & Part 1 Resources (Questions 24-69)
- Session 3: Part 2 Resources & Implementation (Questions 70-108)

---

## 1. EDRQueryBuilder Pattern Analysis

### 1.1 Factory Method Implementation

The EDRQueryBuilder is instantiated via a factory method in the OgcApiEndpoint class, following a well-defined lifecycle:

**Factory Method Signature:**

```typescript
public async edr(collection_id: string): Promise<EDRQueryBuilder>
```

**Implementation Steps:**

1. **Conformance Check (Fail Fast):**

   ```typescript
   if (!this.hasEnvironmentalDataRetrieval) {
     throw new EndpointError('Endpoint does not support EDR');
   }
   ```

   Ensures endpoint supports EDR API before attempting to create builder.

2. **Cache Lookup:**

   ```typescript
   const cache = this.collection_id_to_edr_builder_;
   if (cache.has(collection_id)) {
     return cache.get(collection_id); // Return cached instance
   }
   ```

   Checks private Map for existing QueryBuilder instance. If found, returns same object reference (=== equality).

3. **Metadata Fetch:**

   ```typescript
   const collection = await this.getCollectionInfo(collection_id);
   ```

   Makes HTTP request to retrieve collection metadata document if not cached.

4. **Instantiation:**

   ```typescript
   const result = new EDRQueryBuilder(collection);
   ```

   Creates new QueryBuilder instance, passing full collection metadata to constructor.

5. **Caching:**

   ```typescript
   cache.set(collection_id, result);
   ```

   Stores instance in Map with collection ID as key for future reuse.

6. **Return:**
   ```typescript
   return result;
   ```
   Returns configured QueryBuilder ready for use.

**Key Characteristics:**

- **Asynchronous:** Factory method is async due to potential HTTP request
- **Cached:** Subsequent calls return same instance (performance optimization)
- **Validated:** Fails fast if endpoint doesn't support API family
- **Isolated:** Each collection gets its own QueryBuilder instance

### 1.2 Metadata Encapsulation

The EDRQueryBuilder encapsulates collection-specific metadata passed from OgcApiCollectionInfo:

**Private State (Implementation Details):**

```typescript
private collection: OgcApiCollectionInfo;
private supported_query_types: {
  area: boolean;
  cube: boolean;
  trajectory: boolean;
  corridor: boolean;
  radius: boolean;
  position: boolean;
  locations: boolean;
  instances: boolean;
};
```

**Public State (User-Facing):**

```typescript
public supported_parameters: Record<string, EdrParameterInfo> = {};
public supported_crs: CrsCode[] = [];
public links: Array<{rel: string, href: string}> = [];
```

**Extracted from OgcApiCollectionInfo:**

1. **`data_queries` object** → Determines which query types are available

   - Each query type (position, area, cube, etc.) has a link with href
   - Presence/absence of link determines support
   - Stored as boolean flags in `supported_query_types`

2. **`parameter_names` dictionary** → Available query parameters

   - Maps parameter names to metadata (units, description, etc.)
   - Used for parameter validation before adding to URLs
   - Exposed publicly for user inspection

3. **`crs` array** → Supported Coordinate Reference Systems

   - Array of CRS codes (e.g., 'EPSG:4326', 'EPSG:3857')
   - Used for CRS parameter validation
   - Exposed publicly for user inspection

4. **`links` array** → Navigation links
   - Used to extract base URLs for query construction
   - Standard OGC API hypermedia pattern
   - Exposed publicly for advanced users

**Derived State Computed in Constructor:**

```typescript
constructor(private collection: OgcApiCollectionInfo) {
  this.supported_query_types = {
    area: collection.data_queries.area !== undefined,
    cube: collection.data_queries.cube !== undefined,
    // ... computed from presence of links
  };

  this.supported_parameters = collection.parameter_names;
  this.supported_crs = collection.crs;
  this.links = collection.links;
}
```

**Immutability:** All state is set once in constructor and never modified. This ensures QueryBuilder instances remain consistent throughout their lifetime.

### 1.3 Caching Strategy

The caching strategy is implemented at the **endpoint level**, not within the QueryBuilder itself:

**Cache Structure:**

```typescript
// In OgcApiEndpoint class
private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> = new Map();
```

**Cache Key:** Collection ID string (e.g., "temperature", "humidity", "wind")

**Cache Behavior:**

| Scenario                              | Behavior                                                      | Result                                          |
| ------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------- |
| First call to `endpoint.edr('temp')`  | Cache miss → Fetch metadata → Create builder → Store in cache | New instance created                            |
| Second call to `endpoint.edr('temp')` | Cache hit → Return cached builder                             | Same instance returned (`===` equality)         |
| Call to `endpoint.edr('humidity')`    | Cache miss for different collection → Create new builder      | Different instance created                      |
| Different endpoint instance           | New cache (per-endpoint)                                      | Different instances even for same collection ID |

**Cache Lifetime:**

- Tied to endpoint instance lifetime
- No automatic invalidation or expiration
- Persists until endpoint instance is garbage collected
- No explicit cache clearing API

**Cache Benefits:**

1. **Performance:** Eliminates redundant HTTP requests for collection metadata
   - First call: 1 HTTP request (fetch collection)
   - Subsequent calls: 0 HTTP requests (use cache)
2. **Consistency:** Same collection always returns same builder instance
   - Users can compare instances with `===`
   - No duplicate objects in memory for same collection
3. **Memory Efficiency:** One builder per collection accessed (not per method call)
   - Reasonable memory footprint
   - Scales to hundreds of collections without issue

**Cache Scope:** Per-endpoint instance, not global:

```typescript
const endpoint1 = new OgcApiEndpoint('https://api.example.com');
const endpoint2 = new OgcApiEndpoint('https://api.example.com');

const builder1 = await endpoint1.edr('temp'); // Creates and caches
const builder2 = await endpoint2.edr('temp'); // Creates NEW builder (different cache)

// builder1 !== builder2 (different endpoint instances have separate caches)
```

### 1.4 Constructor Lifecycle

The EDRQueryBuilder constructor performs validation and state initialization:

**Constructor Signature:**

```typescript
constructor(private collection: OgcApiCollectionInfo)
```

**Lifecycle Steps:**

**Step 1: Store Collection Reference**

```typescript
constructor(private collection: OgcApiCollectionInfo) {
  // 'private' modifier automatically creates and assigns:
  // this.collection = collection;
```

**Step 2: Validate Required Data**

```typescript
if (!collection.data_queries) {
  throw new Error('No data queries found, so cannot issue EDR queries');
}
```

- Checks if collection has EDR-specific metadata
- Throws immediately if data is missing (fail fast)
- Prevents creation of non-functional QueryBuilder

**Step 3: Extract Query Type Support**

```typescript
this.supported_query_types = {
  area: collection.data_queries.area !== undefined,
  locations: collection.data_queries.locations !== undefined,
  cube: collection.data_queries.cube !== undefined,
  trajectory: collection.data_queries.trajectory !== undefined,
  corridor: collection.data_queries.corridor !== undefined,
  radius: collection.data_queries.radius !== undefined,
  position: collection.data_queries.position !== undefined,
  instances: collection.data_queries.instances !== undefined,
};
```

- Computes boolean flag for each EDR query type
- Presence of link in `data_queries` indicates support
- Used for runtime validation in query methods

**Step 4: Store Public Metadata**

```typescript
  this.supported_parameters = collection.parameter_names;
  this.supported_crs = collection.crs;
  this.links = collection.links;
}
```

- Exposes collection capabilities to users
- No copying - direct reference assignment
- Enables pre-flight capability checking

**State After Construction:**

- All state initialized and immutable
- Boolean flags set for supported query types
- Public properties expose collection capabilities
- QueryBuilder ready to build/execute queries

**Error Handling:**

- Constructor throws on invalid input
- No partial initialization - all or nothing
- Factory method catches and re-throws with context

### 1.5 Method Organization

EDRQueryBuilder organizes methods by query type, with consistent naming patterns:

**Method Grouping:** By query type (position, area, cube, etc.), not by operation type

**Method Naming Convention:**

1. **URL Builder Methods (Synchronous):**

   - Pattern: `build<QueryType>DownloadUrl(...): string`
   - Examples:
     - `buildPositionDownloadUrl(coords, optional_params = {}): string`
     - `buildAreaDownloadUrl(area_coords, optional_params = {}): string`
     - `buildCubeDownloadUrl(bbox, optional_params = {}): string`
   - Purpose: Construct URL string without executing query
   - Use case: User wants URL for external use

2. **Query Executor Methods (Asynchronous):**
   - Pattern: `async get<QueryType>(...): Promise<EdrData>`
   - Examples:
     - `async getPosition(coords, optional_params = {}): Promise<EdrData>`
     - `async getArea(area_coords, optional_params = {}): Promise<EdrData>`
     - `async getCube(bbox, optional_params = {}): Promise<EdrData>`
   - Purpose: Build URL, execute query, return parsed data
   - Use case: User wants data directly

**Method Organization Structure:**

```typescript
class EDRQueryBuilder {
  // Constructor
  constructor(private collection: OgcApiCollectionInfo) { }

  // Capability getter
  get supported_queries(): Set<DataQueryType> { }

  // Position query methods
  buildPositionDownloadUrl(...): string { }
  async getPosition(...): Promise<EdrData> { }

  // Area query methods
  buildAreaDownloadUrl(...): string { }
  async getArea(...): Promise<EdrData> { }

  // Cube query methods
  buildCubeDownloadUrl(...): string { }
  async getCube(...): Promise<EdrData> { }

  // Trajectory query methods
  buildTrajectoryDownloadUrl(...): string { }
  async getTrajectory(...): Promise<EdrData> { }

  // Corridor query methods
  buildCorridorDownloadUrl(...): string { }
  async getCorridor(...): Promise<EdrData> { }

  // Radius query methods
  buildRadiusDownloadUrl(...): string { }
  async getRadius(...): Promise<EdrData> { }

  // Locations query methods
  buildLocationsDownloadUrl(...): string { }
  async getLocations(...): Promise<EdrData> { }
}
```

**Total Methods:** 14 public methods (7 query types × 2 patterns) + 1 getter

**Parameter Pattern:**

- Required parameters: Direct function parameters
- Optional parameters: Destructured options object with default `= {}`
- Example: `buildPositionDownloadUrl(coords: {lon, lat}, optional_params: optionalPositionParams = {})`

**No Sectioning:** All methods at same level in class (no nested classes, no separate modules)

### 1.6 URL Building vs Query Execution

EDRQueryBuilder provides **both patterns** for maximum flexibility:

**Pattern 1: Build URL (Synchronous, Returns String)**

**Purpose:** User wants URL for external use (logging, debugging, manual fetch, etc.)

**Implementation:**

```typescript
buildPositionDownloadUrl(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}
): string {
  // 1. Validate query type is supported
  if (!this.supported_query_types.position) {
    throw new Error('Collection does not support position queries');
  }

  // 2. Get base URL from collection links
  const url = new URL(this.collection.data_queries?.position?.link.href);

  // 3. Add required parameters
  url.searchParams.set('coords', `POINT(${coords.lon} ${coords.lat})`);

  // 4. Add optional parameters with validation
  if (optional_params.parameter_name) {
    for (const param of optional_params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(`Parameter '${param}' not supported`);
      }
    }
    url.searchParams.set('parameter-name', optional_params.parameter_name.join(','));
  }

  // 5. Return URL string
  return url.toString();
}
```

**Characteristics:**

- Synchronous (no await)
- Returns string
- Validates parameters
- Does not execute HTTP request

**Pattern 2: Execute Query (Asynchronous, Returns Data)**

**Purpose:** User wants data directly, doesn't need URL

**Implementation:**

```typescript
async getPosition(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}
): Promise<EdrData> {
  // 1. Build URL using build method
  const url = this.buildPositionDownloadUrl(coords, optional_params);

  // 2. Fetch data
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // 3. Parse response
  const data = await response.json();

  // 4. Return typed data
  return data as EdrData;
}
```

**Characteristics:**

- Asynchronous (await required)
- Returns typed data object
- Reuses build method (DRY principle)
- Handles HTTP errors

**Relationship:** Execute methods **internally call** build methods:

```
getPosition() → buildPositionDownloadUrl() → fetch() → parse() → return
```

**User Choice:**

```typescript
const builder = await endpoint.edr('temperature');

// Option 1: Get URL only
const url = builder.buildPositionDownloadUrl(
  { lon: -73.935242, lat: 40.73061 },
  { parameter_name: ['temperature'] }
);
console.log(url); // User can fetch themselves

// Option 2: Get data directly
const data = await builder.getPosition(
  { lon: -73.935242, lat: 40.73061 },
  { parameter_name: ['temperature'] }
);
console.log(data.features); // Data ready to use
```

**Most Common Usage:** Execute methods (~90% of users). Build methods for advanced use cases.

### 1.7 Collection Validation

EDRQueryBuilder validates capabilities at two levels:

**Level 1: Constructor Validation (Fail Fast)**

**Check:** Does collection have EDR-specific data at all?

```typescript
constructor(private collection: OgcApiCollectionInfo) {
  if (!collection.data_queries) {
    throw new Error('No data queries found, so cannot issue EDR queries');
  }
  // ... continue initialization
}
```

**Result:**

- If no `data_queries`: Constructor throws, no instance created
- If has `data_queries`: Constructor succeeds, instance created

**Error Type:** Thrown in constructor, caught by factory method

**Level 2: Method Validation (Per Query Type)**

**Check:** Does collection support this specific query type?

```typescript
buildPositionDownloadUrl(...): string {
  if (!this.supported_query_types.position) {
    throw new Error('Collection does not support position queries');
  }
  // ... build URL
}
```

**Result:**

- If query type not supported: Method throws immediately
- If query type supported: Method proceeds with URL building

**Error Type:** Thrown at method invocation, caught by user

**Level 3: Parameter Validation (Per Parameter)**

**Check:** Is this parameter valid for this collection?

```typescript
buildPositionDownloadUrl(coords, optional_params): string {
  // ... capability check above

  if (optional_params.parameter_name) {
    for (const param of optional_params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(
          `The following parameter name does not exist on this collection: '${param}'.`
        );
      }
    }
    url.searchParams.set('parameter-name', optional_params.parameter_name.join(','));
  }

  if (optional_params.crs) {
    if (!this.supported_crs.includes(optional_params.crs)) {
      throw new Error(
        `The following crs does not exist on this collection: '${optional_params.crs}'.`
      );
    }
    url.searchParams.set('crs', optional_params.crs);
  }
  // ... continue
}
```

**Result:**

- If parameter not in `supported_parameters`: Throw error
- If CRS not in `supported_crs`: Throw error
- If valid: Add parameter to URL

**User-Facing Capability Exposure:**

Users can check capabilities **before** calling methods to avoid errors:

```typescript
const builder = await endpoint.edr('temperature');

// Check what query types are supported
console.log(builder.supported_queries);
// Set { 'position', 'cube', 'area' }

// Check before calling
if (builder.supported_queries.has('trajectory')) {
  const data = await builder.getTrajectory(...);
} else {
  console.log('Trajectory queries not supported on this collection');
}

// Check parameters
console.log(builder.supported_parameters);
// { temperature: {...}, humidity: {...}, pressure: {...} }

// Check CRS
console.log(builder.supported_crs);
// ['EPSG:4326', 'EPSG:3857']
```

**Validation Strategy Summary:**

| Level       | What                | When               | Result                                        |
| ----------- | ------------------- | ------------------ | --------------------------------------------- |
| Constructor | Has EDR data        | Instance creation  | Throw if no EDR support at all                |
| Method      | Supports query type | Method invocation  | Throw if query type not available             |
| Parameter   | Parameter validity  | URL building       | Throw if parameter not in collection metadata |
| User Check  | Pre-flight check    | Before method call | Expose capabilities via public properties     |

---

## 2. Single-Class Architecture Design

### 2.1 Method Grouping Strategy

For CSAPIQueryBuilder with 9 resource types, organize methods by **resource type sections**:

**Recommended Structure:**

```typescript
export default class CSAPIQueryBuilder {
  // ============================================================
  // CONSTRUCTOR AND STATE
  // ============================================================

  constructor(private collection: OgcApiCollectionInfo) { }
  private supported_resources: Set<string>;
  public links: Array<{rel: string, href: string}>;

  // ============================================================
  // CAPABILITY GETTERS
  // ============================================================

  get supportedResources(): Set<string> { }

  // ============================================================
  // SYSTEMS RESOURCE METHODS
  // ============================================================

  async getSystems(options?: SystemQueryOptions): Promise<System[]> { }
  async getSystem(systemId: string): Promise<System> { }
  async createSystem(body: SystemInput): Promise<System> { }
  async updateSystem(systemId: string, body: Partial<SystemInput>): Promise<System> { }
  async deleteSystem(systemId: string, options?: {cascade?: boolean}): Promise<void> { }
  async getSubsystems(parentId: string, options?: SystemQueryOptions): Promise<System[]> { }

  // ============================================================
  // DEPLOYMENTS RESOURCE METHODS
  // ============================================================

  async getDeployments(options?: DeploymentQueryOptions): Promise<Deployment[]> { }
  async getDeployment(deploymentId: string): Promise<Deployment> { }
  async createDeployment(body: DeploymentInput): Promise<Deployment> { }
  async updateDeployment(deploymentId: string, body: Partial<DeploymentInput>): Promise<Deployment> { }
  async deleteDeployment(deploymentId: string, options?: {cascade?: boolean}): Promise<void> { }
  async getSubdeployments(parentId: string, options?: DeploymentQueryOptions): Promise<Deployment[]> { }

  // ============================================================
  // PROCEDURES RESOURCE METHODS
  // ============================================================

  async getProcedures(options?: ProcedureQueryOptions): Promise<Procedure[]> { }
  async getProcedure(procedureId: string): Promise<Procedure> { }
  async createProcedure(body: ProcedureInput): Promise<Procedure> { }
  async updateProcedure(procedureId: string, body: Partial<ProcedureInput>): Promise<Procedure> { }
  async deleteProcedure(procedureId: string): Promise<void> { }

  // ... Similar sections for:
  // - SAMPLING FEATURES RESOURCE METHODS
  // - PROPERTIES RESOURCE METHODS (read-only, no create/update/delete)
  // - DATASTREAMS RESOURCE METHODS
  // - OBSERVATIONS RESOURCE METHODS
  // - CONTROL STREAMS RESOURCE METHODS
  // - COMMANDS RESOURCE METHODS

  // ============================================================
  // PRIVATE HELPER METHODS
  // ============================================================

  private buildResourceListUrl(...): string { }
  private getResourceLink(...): string { }
  private addQueryParams(...): void { }
  private async fetchResource<T>(...): Promise<T> { }
}
```

**Grouping Rationale:**

1. **Resource-Centric:** Each resource type is a logical unit
2. **Predictable:** Methods for same resource are adjacent
3. **Maintainable:** Easy to find methods for specific resource
4. **Scalable:** Adding new resource type = add new section
5. **Documented:** JSDoc section markers clarify structure

**Section Order Within Resource:**

1. List/query (most common)
2. Get by ID
3. Create
4. Update
5. Delete
6. Nested resources (if applicable)

**Not Recommended:**

- ❌ Group by CRUD operation (all gets, all creates, etc.) - harder to navigate
- ❌ Separate classes per resource - adds complexity, breaks single-class pattern
- ❌ Nested modules - over-engineering for 50-60 methods

### 2.2 Method Naming Convention

Following EDR pattern, use CRUD-based naming with clear singular/plural distinction:

**Naming Rules:**

| Operation  | Pattern                                         | Examples                                                      |
| ---------- | ----------------------------------------------- | ------------------------------------------------------------- |
| List/Query | `get<ResourcePlural>(options?)`                 | `getSystems()`, `getDeployments()`, `getObservations()`       |
| Get by ID  | `get<ResourceSingular>(id)`                     | `getSystem(id)`, `getDeployment(id)`, `getObservation(id)`    |
| Create     | `create<ResourceSingular>(body)`                | `createSystem()`, `createDeployment()`, `createObservation()` |
| Update     | `update<ResourceSingular>(id, body)`            | `updateSystem()`, `updateDeployment()`                        |
| Delete     | `delete<ResourceSingular>(id, options?)`        | `deleteSystem()`, `deleteDeployment()`                        |
| Nested     | `get<NestedResourcePlural>(parentId, options?)` | `getSubsystems()`, `getSubdeployments()`                      |
| Schema     | `get<ResourceSingular>Schema(id)`               | `getDatastreamSchema()`, `getControlstreamSchema()`           |
| Special    | Action-based                                    | `getCommandStatus()`, `getCommandResult()`                    |

**Full Method Catalog for 9 Resource Types:**

```typescript
// Systems (6 methods)
getSystems(options?): Promise<System[]>
getSystem(id): Promise<System>
createSystem(body): Promise<System>
updateSystem(id, body): Promise<System>
deleteSystem(id, options?): Promise<void>
getSubsystems(parentId, options?): Promise<System[]>

// Deployments (6 methods)
getDeployments(options?): Promise<Deployment[]>
getDeployment(id): Promise<Deployment>
createDeployment(body): Promise<Deployment>
updateDeployment(id, body): Promise<Deployment>
deleteDeployment(id, options?): Promise<void>
getSubdeployments(parentId, options?): Promise<Deployment[]>

// Procedures (5 methods)
getProcedures(options?): Promise<Procedure[]>
getProcedure(id): Promise<Procedure>
createProcedure(body): Promise<Procedure>
updateProcedure(id, body): Promise<Procedure>
deleteProcedure(id): Promise<void>

// Sampling Features (5 methods)
getSamplingFeatures(options?): Promise<SamplingFeature[]>
getSamplingFeature(id): Promise<SamplingFeature>
createSamplingFeature(body): Promise<SamplingFeature>
updateSamplingFeature(id, body): Promise<SamplingFeature>
deleteSamplingFeature(id): Promise<void>

// Properties (2 methods - READ ONLY)
getProperties(options?): Promise<Property[]>
getProperty(id): Promise<Property>

// DataStreams (6 methods)
getDatastreams(options?): Promise<Datastream[]>
getDatastream(id): Promise<Datastream>
getDatastreamSchema(id): Promise<SchemaDocument>
createDatastream(body): Promise<Datastream>
updateDatastream(id, body): Promise<Datastream>
deleteDatastream(id, options?): Promise<void>

// Observations (5 methods)
getObservations(options?): Promise<Observation[]>
getObservation(id): Promise<Observation>
getDatastreamObservations(datastreamId, options?): Promise<Observation[]>
createObservations(datastreamId, observations): Promise<Observation[]>
deleteObservation(id): Promise<void>

// Control Streams (6 methods)
getControlstreams(options?): Promise<Controlstream[]>
getControlstream(id): Promise<Controlstream>
getControlstreamSchema(id): Promise<SchemaDocument>
createControlstream(body): Promise<Controlstream>
updateControlstream(id, body): Promise<Controlstream>
deleteControlstream(id, options?): Promise<void>

// Commands (8 methods)
getCommands(options?): Promise<Command[]>
getCommand(id): Promise<Command>
getControlstreamCommands(controlstreamId, options?): Promise<Command[]>
getCommandStatus(id): Promise<CommandStatus>
getCommandResult(id): Promise<CommandResult>
createCommands(controlstreamId, commands): Promise<Command[]>
updateCommandStatus(id, status): Promise<void>
deleteCommand(id): Promise<void>
```

**Total Methods:** ~55 methods across 9 resource types

**Scaling:** Pattern scales well - clear, consistent, predictable naming for all resources.

### 2.3 Code Reuse Patterns

To avoid duplication across 55 methods, use private helper methods for common operations:

**Helper Method 1: Build Resource List URL**

```typescript
private buildResourceListUrl(
  resourcePath: string,
  options?: QueryOptions
): string {
  const baseUrl = this.getResourceLink(resourcePath);
  const url = new URL(baseUrl);
  this.addStandardQueryParams(url, options);
  return url.toString();
}

// Usage in public methods:
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  const url = this.buildResourceListUrl('systems', options);
  return this.fetchResource<System[]>(url);
}
```

**Helper Method 2: Add Standard Query Parameters**

```typescript
private addStandardQueryParams(
  url: URL,
  options?: QueryOptions
): void {
  if (options?.limit !== undefined) {
    url.searchParams.set('limit', options.limit.toString());
  }
  if (options?.offset !== undefined) {
    url.searchParams.set('offset', options.offset.toString());
  }
  if (options?.bbox) {
    url.searchParams.set('bbox', options.bbox.join(','));
  }
  if (options?.datetime) {
    url.searchParams.set('datetime', options.datetime);
  }
  // ... other common parameters
}
```

**Helper Method 3: Get Resource Link**

```typescript
private getResourceLink(rel: string): string {
  const link = this.collection.links.find(l => l.rel === rel);
  if (!link) {
    throw new Error(`Resource '${rel}' not available on this collection`);
  }
  return link.href;
}
```

**Helper Method 4: Fetch and Parse Resource**

```typescript
private async fetchResource<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data = await response.json();

  // Handle both array and single resource responses
  if (Array.isArray(data)) {
    return data as T;
  }
  if (data.features) {
    return data.features as T; // GeoJSON FeatureCollection
  }
  if (data.items) {
    return data.items as T; // Standard collection
  }
  return data as T; // Single resource
}
```

**Helper Method 5: Build Nested Resource URL**

```typescript
private buildNestedResourceUrl(
  parentResource: string,
  parentId: string,
  childResource: string,
  options?: QueryOptions
): string {
  const baseUrl = this.getResourceLink(parentResource);
  const url = new URL(`${baseUrl}/${parentId}/${childResource}`);
  this.addStandardQueryParams(url, options);
  return url.toString();
}

// Usage:
async getSubsystems(parentId: string, options?: SystemQueryOptions): Promise<System[]> {
  const url = this.buildNestedResourceUrl('systems', parentId, 'subsystems', options);
  return this.fetchResource<System[]>(url);
}
```

**Code Reuse Benefits:**

| Helper Method            | Reused By         | Lines Saved |
| ------------------------ | ----------------- | ----------- |
| `buildResourceListUrl`   | 9 list methods    | ~45 lines   |
| `addStandardQueryParams` | All query methods | ~200 lines  |
| `getResourceLink`        | All methods       | ~90 lines   |
| `fetchResource`          | All read methods  | ~150 lines  |
| `buildNestedResourceUrl` | 5 nested methods  | ~25 lines   |

**Total:** ~510 lines saved through code reuse, reducing implementation from ~5500 lines to ~5000 lines.

**Pattern:** Extract common logic into private helpers, keep public methods focused on business logic.

### 2.4 Nested Endpoints Handling

Use **separate dedicated methods** for nested endpoints (not parameter-based):

**✅ Recommended Pattern:**

```typescript
// Dedicated method for hierarchical navigation
async getSubsystems(
  parentId: string,
  options?: SystemQueryOptions
): Promise<System[]> {
  const url = this.buildNestedResourceUrl('systems', parentId, 'subsystems', options);
  return this.fetchResource<System[]>(url);
}

// Dedicated method for association navigation
async getSystemDatastreams(
  systemId: string,
  options?: DatastreamQueryOptions
): Promise<Datastream[]> {
  const url = this.buildNestedResourceUrl('systems', systemId, 'datastreams', options);
  return this.fetchResource<Datastream[]>(url);
}

// Dedicated method for most common observation query pattern
async getDatastreamObservations(
  datastreamId: string,
  options?: ObservationQueryOptions
): Promise<Observation[]> {
  const url = this.buildNestedResourceUrl('datastreams', datastreamId, 'observations', options);
  return this.fetchResource<Observation[]>(url);
}
```

**Usage Example:**

```typescript
const builder = await endpoint.csapi('sensor-network');

// Clear, explicit hierarchical query
const subsystems = await builder.getSubsystems('system-123');

// Clear association navigation
const datastreams = await builder.getSystemDatastreams('system-123');

// Most common pattern for observations
const observations = await builder.getDatastreamObservations('ds-456', {
  phenomenonTime: '2024-01-01/2024-01-31',
  limit: 100,
});
```

**❌ Not Recommended (Parameter-Based):**

```typescript
// Unclear - mixes canonical and nested endpoints
async getSystems(options?: {
  parent?: string, // If provided, queries /systems/{parent}/subsystems
  limit?: number,
  ...
}): Promise<System[]> {
  // Complex logic to determine URL based on parameters
  // Less type-safe, harder to document
}
```

**Rationale for Separate Methods:**

1. **Clarity:** Intent is explicit in method name
2. **Type Safety:** Different options types for different endpoints
3. **Discoverability:** IDE autocomplete shows all endpoint patterns
4. **Documentation:** Each method documents specific endpoint behavior
5. **Flexibility:** Nested endpoints may have different query parameters
6. **RESTful:** Each endpoint is distinct resource with own method

**All Nested Endpoints to Implement:**

```typescript
// Hierarchical
getSubsystems(parentId, options?): Promise<System[]>
getSubdeployments(parentId, options?): Promise<Deployment[]>

// Association navigation
getSystemDeployments(systemId, options?): Promise<Deployment[]>
getSystemSamplingFeatures(systemId, options?): Promise<SamplingFeature[]>
getSystemDatastreams(systemId, options?): Promise<Datastream[]>
getSystemControlstreams(systemId, options?): Promise<Controlstream[]>

// Primary data access patterns
getDatastreamObservations(datastreamId, options?): Promise<Observation[]>
getControlstreamCommands(controlstreamId, options?): Promise<Command[]>

// Sub-resources
getCommandStatus(commandId): Promise<CommandStatus>
getCommandResult(commandId): Promise<CommandResult>
```

**Total Nested Methods:** ~12 methods providing clear navigation patterns.

### 2.5 State Management

Following EDR pattern, CSAPIQueryBuilder maintains immutable state:

**Private State (Encapsulated):**

```typescript
export default class CSAPIQueryBuilder {
  // Full collection metadata reference (never exposed)
  private collection: OgcApiCollectionInfo;

  // Computed capability flags (used for validation)
  private supported_resources: Set<string>;
}
```

**Public State (Exposed to Users):**

```typescript
export default class CSAPIQueryBuilder {
  // Navigation links for resource access
  public links: Array<{ rel: string; href: string; type?: string }>;

  // Collection identification
  public id: string;
  public title: string;
  public description?: string;

  // Spatial/temporal extent (if relevant)
  public extent?: {
    spatial?: BBox;
    temporal?: [string, string];
  };
}
```

**Derived Getters (Computed Properties):**

```typescript
export default class CSAPIQueryBuilder {
  // Return copy of supported resources (prevent external modification)
  get supportedResources(): Set<string> {
    return new Set(this.supported_resources);
  }

  // Check if specific resource is available
  hasResource(resource: string): boolean {
    return this.supported_resources.has(resource);
  }
}
```

**State Initialization in Constructor:**

```typescript
constructor(private collection: OgcApiCollectionInfo) {
  // Validate collection supports CSAPI
  if (!this.hasConnectedSystemsLinks()) {
    throw new Error('Collection does not support Connected Systems API');
  }

  // Extract public metadata
  this.id = collection.id;
  this.title = collection.title;
  this.description = collection.description;
  this.links = collection.links;
  this.extent = collection.extent;

  // Compute supported resources from links
  this.supported_resources = this.extractSupportedResources();
}

private extractSupportedResources(): Set<string> {
  const resources = new Set<string>();
  const linkRels = this.collection.links.map(l => l.rel);

  // Check for each CSAPI resource type
  if (linkRels.includes('systems')) resources.add('systems');
  if (linkRels.includes('deployments')) resources.add('deployments');
  if (linkRels.includes('procedures')) resources.add('procedures');
  if (linkRels.includes('samplingFeatures')) resources.add('samplingFeatures');
  if (linkRels.includes('properties')) resources.add('properties');
  if (linkRels.includes('datastreams')) resources.add('datastreams');
  if (linkRels.includes('observations')) resources.add('observations');
  if (linkRels.includes('controlstreams')) resources.add('controlstreams');
  if (linkRels.includes('commands')) resources.add('commands');

  return resources;
}
```

**State Characteristics:**

1. **Immutable After Construction:** All state set once, never modified
2. **Derived from Collection:** Source of truth is server-provided metadata
3. **Validated on Construction:** Throws if collection doesn't support CSAPI
4. **Isolated Per Instance:** Each collection gets own state (no shared state)
5. **Type-Safe:** TypeScript interfaces ensure consistency

**What NOT to Maintain:**

- ❌ Query results (no caching of data)
- ❌ User preferences (stateless service object)
- ❌ Connection state (leave to fetch implementation)
- ❌ Request history (no tracking of past queries)

**User Capability Checking:**

```typescript
const builder = await endpoint.csapi('sensor-network');

// Check what resources are available
console.log(builder.supportedResources);
// Set { 'systems', 'deployments', 'datastreams', 'observations' }

// Check before calling
if (builder.hasResource('controlstreams')) {
  const streams = await builder.getControlstreams();
} else {
  console.log('Control streams not available on this collection');
}
```

---

## 3. URL Construction Patterns

### 3.1 Canonical Endpoint Patterns

Based on OpenAPI specification analysis, CSAPI defines the following canonical endpoints:

**Part 1 Resources (OGC API - Connected Systems Part 1):**

| Resource          | List Endpoint            | Individual Endpoint                    | Operations |
| ----------------- | ------------------------ | -------------------------------------- | ---------- |
| Systems           | `GET /systems`           | `GET /systems/{systemId}`              | Full CRUD  |
|                   | `POST /systems`          | `PUT /systems/{systemId}`              |            |
|                   |                          | `PATCH /systems/{systemId}`            |            |
|                   |                          | `DELETE /systems/{systemId}`           |            |
| Deployments       | `GET /deployments`       | `GET /deployments/{deploymentId}`      | Full CRUD  |
|                   | `POST /deployments`      | `PUT /deployments/{deploymentId}`      |            |
|                   |                          | `PATCH /deployments/{deploymentId}`    |            |
|                   |                          | `DELETE /deployments/{deploymentId}`   |            |
| Procedures        | `GET /procedures`        | `GET /procedures/{procedureId}`        | Full CRUD  |
|                   | `POST /procedures`       | `PUT /procedures/{procedureId}`        |            |
|                   |                          | `PATCH /procedures/{procedureId}`      |            |
|                   |                          | `DELETE /procedures/{procedureId}`     |            |
| Sampling Features | `GET /samplingFeatures`  | `GET /samplingFeatures/{featureId}`    | Full CRUD  |
|                   | `POST /samplingFeatures` | `PUT /samplingFeatures/{featureId}`    |            |
|                   |                          | `PATCH /samplingFeatures/{featureId}`  |            |
|                   |                          | `DELETE /samplingFeatures/{featureId}` |            |
| Properties        | `GET /properties`        | `GET /properties/{propId}`             | Read-only  |

**Part 2 Resources (OGC API - Connected Systems Part 2):**

| Resource        | List Endpoint          | Individual Endpoint                        | Operations             |
| --------------- | ---------------------- | ------------------------------------------ | ---------------------- |
| DataStreams     | `GET /datastreams`     | `GET /datastreams/{dataStreamId}`          | Full CRUD              |
|                 | `POST /datastreams`    | `PUT /datastreams/{dataStreamId}`          |                        |
|                 |                        | `PATCH /datastreams/{dataStreamId}`        |                        |
|                 |                        | `DELETE /datastreams/{dataStreamId}`       |                        |
| Observations    | `GET /observations`    | `GET /observations/{obsId}`                | Limited CRUD           |
|                 | `POST /observations`   | `DELETE /observations/{obsId}`             | (rarely used directly) |
| Control Streams | `GET /controlstreams`  | `GET /controlstreams/{controlStreamId}`    | Full CRUD              |
|                 | `POST /controlstreams` | `PUT /controlstreams/{controlStreamId}`    |                        |
|                 |                        | `PATCH /controlstreams/{controlStreamId}`  |                        |
|                 |                        | `DELETE /controlstreams/{controlStreamId}` |                        |
| Commands        | `GET /commands`        | `GET /commands/{cmdId}`                    | Limited CRUD           |
|                 | `POST /commands`       | `DELETE /commands/{cmdId}`                 | (rarely used directly) |

**URL Pattern Characteristics:**

1. **Plural Resource Names:** All collection endpoints use plural (`/systems`, not `/system`)
2. **Path Parameters:** Individual resources use `{resourceId}` pattern
3. **No File Extensions:** Paths don't include `.json`, `.geojson`, etc. (format negotiation via headers)
4. **Consistent Structure:** All resources follow same pattern (predictable)
5. **Hypermedia-Driven:** Actual URLs provided by server via links (client doesn't construct)

**Important Note:** While canonical endpoints exist, **most queries use nested endpoints** for better performance and logical data access patterns (e.g., `/datastreams/{id}/observations` instead of `/observations`).

### 3.2 Nested Endpoint Patterns

CSAPI uses nested endpoints extensively for hierarchical relationships and association navigation:

**Systems Nested Endpoints:**

| Pattern                                | Purpose                                        | HTTP Methods |
| -------------------------------------- | ---------------------------------------------- | ------------ |
| `/systems/{systemId}/subsystems`       | Hierarchical: child systems                    | GET, POST    |
| `/systems/{systemId}/deployments`      | Association: system → deployments              | GET          |
| `/systems/{systemId}/samplingFeatures` | Association: system → sampling features        | GET          |
| `/systems/{systemId}/datastreams`      | Association: system → datastreams (Part 2)     | GET, POST    |
| `/systems/{systemId}/controlstreams`   | Association: system → control streams (Part 2) | GET, POST    |

**Deployments Nested Endpoints:**

| Pattern                                      | Purpose                         | HTTP Methods |
| -------------------------------------------- | ------------------------------- | ------------ |
| `/deployments/{deploymentId}/subdeployments` | Hierarchical: child deployments | GET, POST    |

**DataStreams Nested Endpoints:**

| Pattern                                    | Purpose                                       | HTTP Methods |
| ------------------------------------------ | --------------------------------------------- | ------------ |
| `/datastreams/{dataStreamId}/observations` | **Primary pattern for querying observations** | GET, POST    |
| `/datastreams/{dataStreamId}/schema`       | Schema metadata                               | GET          |

**ControlStreams Nested Endpoints:**

| Pattern                                      | Purpose                                              | HTTP Methods |
| -------------------------------------------- | ---------------------------------------------------- | ------------ |
| `/controlstreams/{controlStreamId}/commands` | **Primary pattern for querying/submitting commands** | GET, POST    |
| `/controlstreams/{controlStreamId}/schema`   | Schema metadata                                      | GET          |

**Commands Nested Endpoints (Sub-Resources):**

| Pattern                               | Purpose                  | HTTP Methods |
| ------------------------------------- | ------------------------ | ------------ |
| `/commands/{cmdId}/status`            | Command execution status | GET, POST    |
| `/commands/{cmdId}/status/{statusId}` | Specific status update   | GET          |
| `/commands/{cmdId}/result`            | Command execution result | GET, PUT     |
| `/commands/{cmdId}/result/{resultId}` | Specific result          | GET          |

**Endpoint Pattern Categories:**

1. **Hierarchical (subsystem/subdeployment):**

   - Format: `/{parentType}/{parentId}/sub{parentType}`
   - Purpose: Navigate parent-child relationships
   - Example: `/systems/weather-station-1/subsystems`

2. **Association Navigation (system → datastreams):**

   - Format: `/{sourceType}/{sourceId}/{targetType}`
   - Purpose: Navigate relationships between different resource types
   - Example: `/systems/sensor-123/datastreams`

3. **Primary Data Access (datastream → observations):**

   - Format: `/{containerType}/{containerId}/{dataType}`
   - Purpose: Access data within context of parent resource
   - Example: `/datastreams/temp-stream/observations`
   - **Most Common Usage Pattern:** 90% of observation queries use this

4. **Sub-Resources (command → status/result):**
   - Format: `/{resourceType}/{resourceId}/{subResource}`
   - Purpose: Access resource-specific metadata or state
   - Example: `/commands/cmd-456/status`

**Total Nested Patterns:** ~12 distinct nested endpoint patterns across all resources.

### 3.3 Schema Endpoint Patterns

Schema endpoints provide introspection of data structures for DataStreams and ControlStreams:

**DataStream Schema Endpoint:**

```
GET /datastreams/{dataStreamId}/schema
```

**Purpose:** Returns SWE Common 3.0 DataComponent schema defining the structure of observation results for this datastream.

**Response Format:** JSON document (SWE Common schema)

**Response Example:**

```json
{
  "type": "DataRecord",
  "label": "Weather Observation Result",
  "fields": [
    {
      "name": "temperature",
      "type": "Quantity",
      "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
      "uom": {
        "code": "Cel"
      }
    },
    {
      "name": "humidity",
      "type": "Quantity",
      "definition": "http://mmisw.org/ont/cf/parameter/relative_humidity",
      "uom": {
        "code": "%"
      }
    }
  ]
}
```

**Usage:** Clients fetch schema before parsing observations to understand result structure.

**ControlStream Schema Endpoint:**

```
GET /controlstreams/{controlStreamId}/schema
```

**Purpose:** Returns SWE Common 3.0 DataComponent schema defining the structure of command parameters for this control stream.

**Response Format:** JSON document (SWE Common schema)

**Response Example:**

```json
{
  "type": "DataRecord",
  "label": "Pan-Tilt Command Parameters",
  "fields": [
    {
      "name": "pan",
      "type": "Quantity",
      "definition": "http://example.org/def/pan_angle",
      "uom": {
        "code": "deg"
      },
      "constraint": {
        "type": "AllowedValues",
        "interval": [-180, 180]
      }
    },
    {
      "name": "tilt",
      "type": "Quantity",
      "definition": "http://example.org/def/tilt_angle",
      "uom": {
        "code": "deg"
      },
      "constraint": {
        "type": "AllowedValues",
        "interval": [-90, 90]
      }
    }
  ]
}
```

**Usage:** Clients fetch schema before submitting commands to understand parameter structure and constraints.

**Why Only DataStreams and ControlStreams Have Schemas:**

- **DataStreams:** Observation results are structured data (not fixed format) → schema describes structure
- **ControlStreams:** Command parameters are structured data (not fixed format) → schema describes structure
- **Other Resources:** Use fixed GeoJSON/SensorML formats → no schema endpoint needed

**Schema Endpoint Methods:**

```typescript
async getDatastreamSchema(datastreamId: string): Promise<SchemaDocument> {
  const url = `${this.getResourceLink('datastreams')}/${datastreamId}/schema`;
  return this.fetchResource<SchemaDocument>(url);
}

async getControlstreamSchema(controlstreamId: string): Promise<SchemaDocument> {
  const url = `${this.getResourceLink('controlstreams')}/${controlstreamId}/schema`;
  return this.fetchResource<SchemaDocument>(url);
}
```

### 3.4 Special-Purpose Endpoints

CSAPI defines special endpoints for command lifecycle management:

**Command Status Tracking:**

| Endpoint                              | HTTP Method | Purpose                                             |
| ------------------------------------- | ----------- | --------------------------------------------------- |
| `/commands/{cmdId}/status`            | GET         | Retrieve current status of command execution        |
| `/commands/{cmdId}/status`            | POST        | Add status update (typically by system, not client) |
| `/commands/{cmdId}/status/{statusId}` | GET         | Retrieve specific status update by ID               |

**Status Response Example:**

```json
{
  "status": "executing",
  "percentCompletion": 45,
  "statusMessage": "Calibrating sensors",
  "updateTime": "2024-02-02T10:15:30Z"
}
```

**Status Values:**

- `pending`: Command accepted, awaiting execution
- `accepted`: Command validated and queued
- `executing`: Command currently running
- `completed`: Command finished successfully
- `failed`: Command execution failed
- `cancelled`: Command was cancelled before completion

**Command Result Retrieval:**

| Endpoint                              | HTTP Method | Purpose                                           |
| ------------------------------------- | ----------- | ------------------------------------------------- |
| `/commands/{cmdId}/result`            | GET         | Retrieve result after command execution completes |
| `/commands/{cmdId}/result`            | PUT         | Set result (typically by system, not client)      |
| `/commands/{cmdId}/result/{resultId}` | GET         | Retrieve specific result by ID                    |

**Result Response Example:**

```json
{
  "completionTime": "2024-02-02T10:20:00Z",
  "result": {
    "panPosition": -45.3,
    "tiltPosition": 12.7
  },
  "resultQuality": {
    "accuracy": 0.1
  }
}
```

**Feasibility Checking:**

| Endpoint                                        | HTTP Method | Purpose                                                    |
| ----------------------------------------------- | ----------- | ---------------------------------------------------------- |
| `/controlstreams/{controlStreamId}/feasibility` | POST        | Check if command parameters are feasible before submission |

**Feasibility Request:**

```json
{
  "parameters": {
    "pan": -45,
    "tilt": 15
  }
}
```

**Feasibility Response:**

```json
{
  "feasible": true,
  "message": "Command parameters are within operational limits",
  "estimatedExecutionTime": "PT5S"
}
```

**Other Potential Special Endpoints:**

- `/commands/{cmdId}/cancel` - POST: Cancel pending/executing command (if server supports)

**Method Signatures:**

```typescript
async getCommandStatus(commandId: string): Promise<CommandStatus> {
  const url = `${this.getResourceLink('commands')}/${commandId}/status`;
  return this.fetchResource<CommandStatus>(url);
}

async getCommandResult(commandId: string): Promise<CommandResult> {
  const url = `${this.getResourceLink('commands')}/${commandId}/result`;
  return this.fetchResource<CommandResult>(url);
}

async checkFeasibility(
  controlstreamId: string,
  parameters: Record<string, any>
): Promise<FeasibilityReport> {
  const url = `${this.getResourceLink('controlstreams')}/${controlstreamId}/feasibility`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parameters })
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await response.json();
}
```

### 3.5 Query String Assembly

Following EDR pattern, use native JavaScript URL API for all query string construction:

**Basic Pattern:**

```typescript
const url = new URL(baseUrl); // Base URL from collection links

// Add parameters conditionally (check for undefined)
if (options.limit !== undefined) {
  url.searchParams.set('limit', options.limit.toString());
}

if (options.offset !== undefined) {
  url.searchParams.set('offset', options.offset.toString());
}

// Return URL string
return url.toString();
```

**Automatic URL Encoding:**

The `URL.searchParams.set()` method automatically encodes special characters:

```typescript
// Spaces encoded
url.searchParams.set('q', 'weather station');
// Result: ?q=weather%20station

// Special characters encoded
url.searchParams.set('name', 'Temp & Humidity');
// Result: ?name=Temp%20%26%20Humidity

// URI values passed through
url.searchParams.set('systemType', 'http://www.w3.org/ns/sosa/Sensor');
// Result: ?systemType=http%3A%2F%2Fwww.w3.org%2Fns%2Fsosa%2FSensor
```

**No manual encoding required** - URL API handles it automatically.

**Array Serialization (Comma-Separated):**

OGC API standard uses comma-separated values for arrays:

```typescript
// Multiple IDs
if (options.id?.length > 0) {
  url.searchParams.set('id', options.id.join(','));
}
// Result: ?id=sys1,sys2,sys3

// Bounding box (4 coordinates)
if (options.bbox) {
  url.searchParams.set('bbox', options.bbox.join(','));
}
// Result: ?bbox=-180,-90,180,90

// Multiple properties
if (options.observedProperty?.length > 0) {
  url.searchParams.set('observedProperty', options.observedProperty.join(','));
}
// Result: ?observedProperty=temp,humidity,pressure
```

**Boolean Serialization:**

Convert booleans to string:

```typescript
if (options.recursive !== undefined) {
  url.searchParams.set('recursive', options.recursive.toString());
}
// Result: ?recursive=true or ?recursive=false
```

**Temporal Parameter Serialization:**

Pass ISO 8601 strings directly (no conversion needed):

```typescript
if (options.datetime) {
  url.searchParams.set('datetime', options.datetime);
}
// Result: ?datetime=2024-01-01T00:00:00Z/2024-01-31T23:59:59Z

if (options.phenomenonTime) {
  url.searchParams.set('phenomenonTime', options.phenomenonTime);
}
// Result: ?phenomenonTime=2024-02-01/2024-02-02
```

**Helper Method for Common Parameters:**

```typescript
private addStandardQueryParams(url: URL, options?: QueryOptions): void {
  if (options?.limit !== undefined) {
    url.searchParams.set('limit', options.limit.toString());
  }

  if (options?.offset !== undefined) {
    url.searchParams.set('offset', options.offset.toString());
  }

  if (options?.bbox) {
    url.searchParams.set('bbox', options.bbox.join(','));
  }

  if (options?.datetime) {
    url.searchParams.set('datetime', options.datetime);
  }

  if (options?.id?.length > 0) {
    url.searchParams.set('id', options.id.join(','));
  }

  if (options?.q) {
    url.searchParams.set('q', options.q);
  }

  if (options?.recursive !== undefined) {
    url.searchParams.set('recursive', options.recursive.toString());
  }

  // ... other common parameters
}
```

**Key Principles:**

1. Always check `!== undefined` before adding parameters
2. Convert primitives to string with `.toString()`
3. Join arrays with comma
4. Let URL API handle encoding
5. Use helper methods to avoid duplication

### 3.6 Base URL Construction

**CRITICAL:** NEVER manually construct base URLs. Always use hypermedia links from server.

**✅ Correct Approach - Link-Based:**

**Step 1: Get URL from collection links**

```typescript
private getResourceLink(rel: string): string {
  const link = this.collection.links.find(l => l.rel === rel);
  if (!link) {
    throw new Error(`Resource '${rel}' not available on this collection`);
  }
  return link.href;
}
```

**Step 2: Create URL object**

```typescript
const baseUrl = this.getResourceLink('systems');
// Server provides: "https://api.example.com/collections/sensors/systems"

const url = new URL(baseUrl);
```

**Step 3: For specific resource, append ID**

```typescript
const resourceUrl = new URL(`${baseUrl}/${systemId}`);
// Result: "https://api.example.com/collections/sensors/systems/system-123"
```

**Step 4: Add query parameters**

```typescript
url.searchParams.set('limit', '10');
url.searchParams.set('bbox', '-180,-90,180,90');
```

**Step 5: Return URL string**

```typescript
return url.toString();
// Result: "https://api.example.com/collections/sensors/systems?limit=10&bbox=-180,-90,180,90"
```

**❌ Wrong Approach - Manual Construction:**

```typescript
// DON'T DO THIS - fragile, assumes URL structure
const url = `${this.endpoint}/collections/${this.collectionId}/systems`;

// DON'T DO THIS - hardcoded paths break with non-standard servers
const url = this.baseUrl + '/systems';
```

**Why Link-Based Approach:**

1. **Server Freedom:** Server can use ANY URL structure
   - Standard: `/collections/{id}/systems`
   - Custom: `/api/v2/sensor-networks/{name}/systems`
   - Legacy: `/ogc/csapi/{id}/system-list`
2. **Standards Compliance:** OGC APIs are hypermedia-driven
   - Links are part of the API contract
   - URLs are opaque identifiers, not templates
3. **Robustness:** Works with non-standard implementations
   - Custom path structures
   - Proxied/rewritten URLs
   - Cloud-hosted services with complex paths

**Trailing Slash Handling:**

URL API automatically normalizes trailing slashes:

```typescript
// No trailing slash
new URL('/systems/123', 'https://api.example.com').toString();
// Result: "https://api.example.com/systems/123"

// With trailing slash
new URL('systems/123', 'https://api.example.com/').toString();
// Result: "https://api.example.com/systems/123"

// URL API handles normalization
```

**For Nested Resources:**

```typescript
const systemsUrl = this.getResourceLink('systems');
const subsystemsUrl = `${systemsUrl}/${parentId}/subsystems`;
const url = new URL(subsystemsUrl);

// Result: Properly constructed nested URL from server-provided base
```

**Complete Example:**

```typescript
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  // 1. Get base URL from links (hypermedia)
  const baseUrl = this.getResourceLink('systems');

  // 2. Create URL object
  const url = new URL(baseUrl);

  // 3. Add query parameters
  this.addStandardQueryParams(url, options);

  // 4. Fetch and return
  return this.fetchResource<System[]>(url.toString());
}
```

**Rationale:** By using links, client works with ANY compliant CSAPI server, regardless of URL structure. This is the fundamental principle of RESTful, hypermedia-driven APIs.

---

## 4. CRUD Operations Design

### 4.1 HTTP Method Mapping

CSAPI follows standard HTTP semantics for CRUD operations:

**HTTP Method Semantics:**

| HTTP Method | CRUD Operation     | Idempotent | Safe | Request Body        | Response Body               |
| ----------- | ------------------ | ---------- | ---- | ------------------- | --------------------------- |
| GET         | Read/Retrieve      | Yes        | Yes  | No                  | Yes (resource data)         |
| POST        | Create             | No         | No   | Yes (new resource)  | Yes (created resource)      |
| PUT         | Replace (complete) | Yes        | No   | Yes (full resource) | Optional (updated resource) |
| PATCH       | Update (partial)   | No         | No   | Yes (partial data)  | Optional (updated resource) |
| DELETE      | Delete             | Yes        | No   | No                  | No (204 No Content)         |

**CSAPI Operation Mappings:**

**GET - Read/Retrieve Operations:**

```
GET /systems                            → List all systems
GET /systems/{id}                       → Get specific system
GET /systems/{id}/subsystems            → List subsystems
GET /datastreams/{id}/observations      → List observations (with temporal query)
GET /datastreams/{id}/schema            → Get datastream schema
GET /commands/{id}/status               → Get command status
GET /commands/{id}/result               → Get command result
```

**POST - Create Operations:**

```
POST /systems                           → Create new system (201 Created + Location header)
POST /systems/{id}/subsystems           → Create subsystem under parent
POST /datastreams/{id}/observations     → Create observation(s) - single or bulk array
POST /controlstreams/{id}/commands      → Submit command(s) - single or bulk array
POST /controlstreams/{id}/feasibility   → Check command feasibility (action, not create)
POST /commands/{id}/status              → Add status update (typically system-side)
```

**PUT - Replace Operations:**

```
PUT /systems/{id}                       → Replace entire system document
PUT /deployments/{id}                   → Replace entire deployment document
PUT /commands/{id}/result               → Set command result (typically system-side)
```

**PATCH - Update Operations:**

```
PATCH /systems/{id}                     → Partial update of system
PATCH /datastreams/{id}                 → Partial update of datastream
PATCH /commands/{id}/status             → Update command status fields
```

**DELETE - Delete Operations:**

```
DELETE /systems/{id}                    → Delete system (409 if has dependents)
DELETE /systems/{id}?cascade=true       → Delete system and all dependents
DELETE /datastreams/{id}?cascade=true   → Delete datastream and all observations
DELETE /observations/{id}               → Delete specific observation (rare)
DELETE /commands/{id}                   → Delete command (if not executed)
```

**Response Status Codes:**

| Status Code               | Meaning                       | Used For                               |
| ------------------------- | ----------------------------- | -------------------------------------- |
| 200 OK                    | Success with response body    | GET, PUT, PATCH (with body)            |
| 201 Created               | Resource created              | POST (with Location header)            |
| 204 No Content            | Success without response body | DELETE, PUT/PATCH (without body)       |
| 400 Bad Request           | Validation error              | Invalid request body or parameters     |
| 401 Unauthorized          | Authentication required       | Missing or invalid credentials         |
| 403 Forbidden             | Authorization failed          | Insufficient permissions               |
| 404 Not Found             | Resource doesn't exist        | GET/PUT/PATCH/DELETE non-existent ID   |
| 409 Conflict              | Constraint violation          | DELETE with dependents, duplicate ID   |
| 422 Unprocessable Entity  | Semantic validation error     | Valid JSON but violates business rules |
| 500 Internal Server Error | Server error                  | Unexpected server failure              |

### 4.2 Request Body Handling

Pass request bodies as typed method parameters with TypeScript interfaces:

**Method Signature Pattern:**

```typescript
async createResource(body: ResourceInput): Promise<Resource> {
  const url = this.getResourceLink('resource');
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/geo+json' },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // Parse response - created resource with server-assigned ID
  const created = await response.json();
  return created as Resource;
}
```

**TypeScript Input Interfaces:**

**Systems (GeoJSON Feature):**

```typescript
interface SystemInput {
  type: 'Feature';
  geometry: GeoJSONGeometry | null;
  properties: {
    name: string;
    description?: string;
    systemType: string; // URI: 'http://www.w3.org/ns/sosa/Sensor'
    assetType?: 'sensor' | 'actuator' | 'sampler' | 'platform';
    uniqueIdentifier?: string; // URN
    validTime?: TemporalPeriod;
    // ... other properties
  };
}
```

**DataStreams (JSON):**

```typescript
interface DatastreamInput {
  name: string;
  description?: string;
  system: string; // Link to system ID (required)
  observedProperties: string[]; // Array of property URIs
  resultSchema: DataComponent; // SWE Common schema
  resultFormat?: 'json' | 'text' | 'binary';
  phenomenonTimeRange?: [string, string]; // ISO 8601
  samplingFeatures?: string[]; // Links to sampling feature IDs
  featuresOfInterest?: string[]; // Links to FOI IDs
}
```

**Observations (JSON or Array):**

```typescript
interface ObservationInput {
  phenomenonTime: string; // ISO 8601 (required)
  resultTime?: string; // ISO 8601
  result: any; // Structure defined by datastream schema
  resultQuality?: QualityInfo;
  parameters?: Record<string, any>;
  featureOfInterest?: string; // Link or inline
}

// Bulk create - array of observations
async createObservations(
  datastreamId: string,
  observations: ObservationInput[]
): Promise<Observation[]>
```

**Commands (JSON or Array):**

```typescript
interface CommandInput {
  issueTime?: string; // ISO 8601 (defaults to now)
  executionTime?: string; // ISO 8601 (when to execute)
  parameters: any; // Structure defined by controlstream schema
  priority?: number;
  sender?: string;
}

// Bulk submit - array of commands
async createCommands(
  controlstreamId: string,
  commands: CommandInput[]
): Promise<Command[]>
```

**Partial Updates (PATCH):**

```typescript
async updateSystem(
  id: string,
  updates: Partial<SystemInput> // Partial type allows any subset of properties
): Promise<System> {
  const url = `${this.getResourceLink('systems')}/${id}`;
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/merge-patch+json' },
    body: JSON.stringify(updates)
  });
  // ...
}
```

**Body Serialization:**

- Always use `JSON.stringify(body)` for request body
- Set appropriate `Content-Type` header
- Let fetch API handle encoding

**Response Parsing:**

- Parse response with `await response.json()`
- Return typed object: `return created as Resource`
- Handle errors before parsing (check `response.ok`)

### 4.3 Content-Type Headers

Content-Type headers vary by resource type and format:

**GeoJSON Resources (Spatial Resources):**

```typescript
// Systems, Deployments, Sampling Features
headers: {
  'Content-Type': 'application/geo+json' // Preferred
  // OR
  'Content-Type': 'application/json'     // Also acceptable
}
```

**SensorML Resources (Detailed Sensor Descriptions):**

```typescript
// Systems or Procedures with detailed metadata
headers: {
  'Content-Type': 'application/sml+json' // SensorML 3.0 JSON
}
```

**Standard JSON Resources:**

```typescript
// DataStreams, ControlStreams, Properties
headers: {
  'Content-Type': 'application/json'
}
```

**SWE Common Resources (Observations, Commands):**

```typescript
// JSON encoding
headers: {
  'Content-Type': 'application/json'
  // OR
  'Content-Type': 'application/swe+json' // If server supports SWE JSON
}

// CSV/Text encoding (bulk observations)
headers: {
  'Content-Type': 'text/csv'
  // OR
  'Content-Type': 'application/swe+text'
}

// Binary encoding (high-volume streaming)
headers: {
  'Content-Type': 'application/octet-stream'
}
```

**Partial Updates (PATCH):**

```typescript
// JSON Merge Patch (RFC 7396)
headers: {
  'Content-Type': 'application/merge-patch+json'
}

// JSON Patch (RFC 6902)
headers: {
  'Content-Type': 'application/json-patch+json'
}
```

**Content-Type Selection Logic:**

```typescript
private getContentType(resourceType: string, format?: string): string {
  // Spatial resources → GeoJSON
  if (['systems', 'deployments', 'samplingFeatures'].includes(resourceType)) {
    return 'application/geo+json';
  }

  // Observations with format parameter
  if (resourceType === 'observations' && format) {
    if (format === 'text') return 'text/csv';
    if (format === 'binary') return 'application/octet-stream';
  }

  // Default to standard JSON
  return 'application/json';
}
```

**Accept Header (GET Requests - Format Negotiation):**

```typescript
// Request GeoJSON format
headers: {
  'Accept': 'application/geo+json'
}

// Request SensorML format
headers: {
  'Accept': 'application/sml+json'
}

// Or use query parameter
GET /systems/{id}?f=geojson
GET /systems/{id}?f=sml+json
```

**Complete Request Example:**

```typescript
async createSystem(body: SystemInput): Promise<System> {
  const url = this.getResourceLink('systems');
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/geo+json',
      'Accept': 'application/geo+json'
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json() as System;
}
```

### 4.4 Response Handling Pattern

QueryBuilder methods should **execute requests and return parsed data** (not just URLs):

**Recommended Pattern (Execute and Return Data):**

```typescript
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  // 1. Build URL
  const url = this.buildResourceListUrl('systems', options);

  // 2. Fetch
  const response = await fetch(url);

  // 3. Error handling
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // 4. Parse response
  const data = await response.json();

  // 5. Extract items (handle both GeoJSON and standard formats)
  if (data.features) {
    return data.features as System[]; // GeoJSON FeatureCollection
  }
  if (data.items) {
    return data.items as System[]; // Standard OGC API collection
  }
  if (Array.isArray(data)) {
    return data as System[]; // Direct array
  }

  throw new Error('Unexpected response format');
}
```

**Return Type Patterns:**

| Method Type | Return Type               | Example                                               |
| ----------- | ------------------------- | ----------------------------------------------------- |
| List/query  | `Promise<Resource[]>`     | `getSystems()` → `Promise<System[]>`                  |
| Get by ID   | `Promise<Resource>`       | `getSystem(id)` → `Promise<System>`                   |
| Create      | `Promise<Resource>`       | `createSystem(body)` → `Promise<System>` (with ID)    |
| Update      | `Promise<Resource>`       | `updateSystem(id, body)` → `Promise<System>`          |
| Delete      | `Promise<void>`           | `deleteSystem(id)` → `Promise<void>` (204 No Content) |
| Schema      | `Promise<SchemaDocument>` | `getDatastreamSchema(id)` → `Promise<SchemaDocument>` |
| Status      | `Promise<CommandStatus>`  | `getCommandStatus(id)` → `Promise<CommandStatus>`     |

**Optional: Build URL Methods (for Advanced Users):**

```typescript
// Synchronous method - just returns URL string
buildSystemsUrl(options?: SystemQueryOptions): string {
  const baseUrl = this.getResourceLink('systems');
  const url = new URL(baseUrl);
  this.addStandardQueryParams(url, options);
  return url.toString();
}

// Execute method uses build method internally
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  const url = this.buildSystemsUrl(options);
  return this.fetchResource<System[]>(url);
}
```

**Recommendation:**

- **Start with execute methods only** (`getSystems()`, `createSystem()`, etc.)
- **Add build methods later** if users request them (`buildSystemsUrl()`, etc.)
- **Most users want data**, not URLs (90/10 usage split)

**Error Handling:**

```typescript
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  const url = this.buildResourceListUrl('systems', options);

  try {
    const response = await fetch(url);

    // HTTP error
    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(
        `HTTP ${response.status}: ${response.statusText}. ${errorBody}`
      );
    }

    // Parse error
    const data = await response.json();

    // Format validation
    if (!data.features && !data.items && !Array.isArray(data)) {
      throw new Error('Response format not recognized');
    }

    return this.extractItems(data);

  } catch (error) {
    // Network error or parsing error
    throw new Error(`Failed to fetch systems: ${error.message}`);
  }
}
```

### 4.5 Cascade Delete Implementation

Support cascade delete via **optional parameter** (not separate method):

**Implementation:**

```typescript
async deleteSystem(
  systemId: string,
  options?: { cascade?: boolean }
): Promise<void> {
  const baseUrl = this.getResourceLink('systems');
  const url = new URL(`${baseUrl}/${systemId}`);

  // Add cascade parameter if requested
  if (options?.cascade) {
    url.searchParams.set('cascade', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'DELETE'
  });

  if (!response.ok) {
    // Provide helpful error message
    if (response.status === 409) {
      throw new Error(
        `Cannot delete system: has dependent resources. ` +
        `Use {cascade: true} to delete system and all dependents.`
      );
    }
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // DELETE returns 204 No Content on success (no return value)
}
```

**Usage:**

```typescript
const builder = await endpoint.csapi('sensor-network');

// Delete system only (fails if has dependencies)
try {
  await builder.deleteSystem('system-123');
} catch (error) {
  // Will throw 409 Conflict if system has subsystems, datastreams, etc.
  console.error(error);
}

// Delete system and all dependent resources
await builder.deleteSystem('system-123', { cascade: true });
// Deletes: system + subsystems + datastreams + observations + controlstreams + commands
```

**Cascade Behavior:**

| Cascade Value      | Behavior                                                | Use Case                                    |
| ------------------ | ------------------------------------------------------- | ------------------------------------------- |
| Omitted or `false` | Delete resource only, fail if has dependents            | Safe default, prevents accidental data loss |
| `true`             | Delete resource and ALL dependent resources recursively | Cleanup, removal of entire system hierarchy |

**Server Response Codes:**

| Response         | Meaning                                   |
| ---------------- | ----------------------------------------- |
| `204 No Content` | Delete successful                         |
| `409 Conflict`   | Resource has dependents and cascade=false |
| `404 Not Found`  | Resource doesn't exist                    |
| `403 Forbidden`  | Insufficient permissions                  |

**Resources Supporting Cascade Delete:**

1. **Systems:** Cascades to subsystems, datastreams, observations, controlstreams, commands
2. **Deployments:** Cascades to subdeployments
3. **DataStreams:** Cascades to all observations (large data deletion!)
4. **ControlStreams:** Cascades to all commands

**Resources NOT Supporting Cascade:**

- Observations (leaf nodes)
- Commands (leaf nodes)
- Procedures (shared resources)
- Sampling Features (shared resources)
- Properties (shared resources)

**❌ Not Recommended (Separate Method):**

```typescript
// Creates API bloat
async deleteSystem(id: string): Promise<void> { }
async deleteSystemCascade(id: string): Promise<void> { } // DON'T DO THIS
```

**Warning to Users:**

Cascade delete is a **dangerous operation**:

- Can delete large amounts of data
- Cannot be undone
- Should require explicit user confirmation
- May take significant time for large hierarchies

```typescript
// Good practice - confirm before cascade
if (confirm('This will delete the system and ALL dependent data. Continue?')) {
  await builder.deleteSystem('system-123', { cascade: true });
}
```

---

## Summary: Session 1 Completion

### Research Completed

**Questions Answered:** 23 questions (Questions 1-23)

- Section A: EDRQueryBuilder Pattern Study (7 questions)
- Section B: Single-Class Architecture (5 questions)
- Section C: URL Construction Patterns (6 questions)
- Section D: CRUD Operations Implementation (5 questions)

**Analysis Sections Created:**

1. EDRQueryBuilder Pattern Analysis (7 subsections)
2. Single-Class Architecture Design (5 subsections)
3. URL Construction Patterns (6 subsections)
4. CRUD Operations Design (5 subsections)

### Key Decisions Made

1. **Factory Method Pattern:** Cache QueryBuilder instances at endpoint level with collection ID as key
2. **Method Organization:** Group by resource type sections (not CRUD operation type)
3. **Method Naming:** `get<Resource>()` / `create<Resource>()` / `update<Resource>()` / `delete<Resource>()`
4. **URL Construction:** Link-based navigation (never manually construct), use native URL API
5. **Code Reuse:** Private helper methods for common patterns (saves ~510 lines)
6. **Nested Endpoints:** Separate dedicated methods (not parameter-based)
7. **Request Handling:** Execute and return data (not just URLs)
8. **Cascade Delete:** Optional parameter (not separate method)

### Implementation Scope

**Estimated Class Size:**

- ~55 public methods (across 9 resource types)
- ~10 private helper methods
- ~500 lines per resource type × 9 = ~4500 lines
- With helpers and documentation: **~5000 lines for CSAPIQueryBuilder class**

**Total with tests:** ~10k-12k lines in csapi/ subfolder

### Next Steps

**Session 2 (To Be Completed):**

- Query parameters & Part 1 Resources (Questions 24-69)
- Document ALL query parameters with syntax
- Design methods for Systems, Deployments, Procedures, Sampling Features, Properties

**Session 3 (Future):**

- Part 2 Resources & Implementation (Questions 70-108)
- Design methods for DataStreams, Observations, Control Streams, Commands
- TypeScript type definitions
- Testing strategy and implementation checklist

---

**Document Status:** Session 1 Complete (Foundation established)
**Next Session:** Query Parameters & Part 1 Resources
