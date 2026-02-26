# CSAPIQueryBuilder Component Research Plan

**Component:** CSAPIQueryBuilder (Component 4)
**Type:** BUILDING NEW CODE
**Pattern:** Single class following EDRQueryBuilder pattern
**Scope:** ~10k-14k lines (~70% of total new code)
**Location:** `src/ogc-api/csapi/url_builder.js`

---

## 1. Purpose

Document research objectives and methodology for implementing the CSAPIQueryBuilder class, which is the heart of the CSAPI implementation. This single class provides URL construction methods for all 9 CSAPI resource types (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands), implementing approximately 60-70 unique URL patterns with full CRUD operations, comprehensive query parameters, spatial/temporal/hierarchical filtering, pagination support, and schema endpoints. The QueryBuilder follows the EDRQueryBuilder pattern from upstream PR #114 where one comprehensive class per API family handles all URL construction for that API, accessed via `endpoint.csapi(collectionId)`. This component defines the URL patterns and query parameter structures that all downstream format handlers will parse and all validators will check, making it the architectural foundation that other components build upon.

---

## 2. Context

### Implementation Type

**BUILDING NEW CODE** - This is a new class we're adding to the library, not extending existing functionality.

### Upstream Pattern

The CSAPIQueryBuilder follows the **EDRQueryBuilder pattern** established in the upstream repository:

- Single comprehensive class accessed via factory method: `endpoint.csapi(collectionId)`
- Contains methods for all resource types (not 9 separate classes)
- Instantiated by OgcApiEndpoint and cached for reuse
- Encapsulates collection-specific metadata (from CSAPI collection info)
- Provides both URL-building methods and optional query execution methods
- Validates parameters against collection capabilities

### Key References

- [csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md#csapiquerybuilder-building-new-query-construction-class): Specification for CSAPIQueryBuilder including all 9 resource types
- [querybuilder-pattern-analysis.md](../../../research/upstream/querybuilder-pattern-analysis.md): Detailed analysis of QueryBuilder pattern from EDR implementation
- [url-building-analysis.md](../../../research/upstream/url-building-analysis.md): URL construction patterns and query parameter assembly
- [OGC API - Connected Systems Part 1: OpenAPI](../../../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Part 1 endpoint definitions
- [OGC API - Connected Systems Part 2: OpenAPI](../../../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): Part 2 endpoint definitions

### Scope and Complexity

This is the largest single component in the CSAPI implementation:

- **Code volume:** ~10k-14k lines (70% of total new code)
- **URL patterns:** 60-70 unique URL patterns across 9 resource types
- **Operations:** Full CRUD (Create, Read, Update, Delete) not just read-only
- **Query parameters:** Spatial (bbox), temporal (datetime, phenomenonTime), hierarchical (recursive), relationship (parent, system, foi), pagination (offset-based, cursor-based), format negotiation (f, obsFormat, cmdFormat), property-based filtering
- **Resource types:** Part 1 (Systems, Deployments, Procedures, Sampling Features, Properties) + Part 2 (DataStreams, Observations, Control Streams, Commands)
- **Special endpoints:** Schema endpoints, command status/result endpoints, feasibility checking, bulk operations

---

## 3. Research Objectives

### Primary Objectives

1. **Understand EDRQueryBuilder Pattern:**

   - How is EDRQueryBuilder instantiated via factory method?
   - What metadata does it encapsulate from collection info?
   - How does caching work in the factory method?
   - What is the lifecycle of a QueryBuilder instance?
   - How are query methods organized (URL building vs execution)?

2. **Design Single-Class Architecture for 9 Resource Types:**

   - How should methods be organized within one class?
   - What method naming conventions follow EDR pattern?
   - How to group methods logically by resource type?
   - How to avoid code duplication across resource types?
   - How to maintain consistency across 60-70 URL patterns?

3. **Implement URL Construction for All CSAPI Resources:**

   - What are the canonical endpoint patterns for each resource type?
   - What are the nested endpoint patterns (e.g., `/systems/{id}/subsystems`)?
   - How to build URLs with query parameters?
   - How to encode array parameters (multiple IDs, bounding boxes)?
   - How to handle format negotiation (`f` parameter)?

4. **Support Full CRUD Operations:**

   - What HTTP methods (GET, POST, PUT, PATCH, DELETE) for each operation?
   - How to construct bodies for POST/PUT/PATCH requests?
   - How to pass request bodies through URL builder methods?
   - What validation should occur before making requests?
   - How to handle cascade delete parameters?

5. **Implement Comprehensive Query Parameter Support:**

   - What are ALL standard OGC API parameters (bbox, datetime, limit, offset, f)?
   - What are ALL CSAPI common parameters (id, uid, q, propertyName filters)?
   - What are hierarchical parameters (recursive)?
   - What are relationship parameters (parent, system, foi, observedProperty, etc.)?
   - What are temporal parameters (phenomenonTime, resultTime, executionTime, issueTime)?
   - How to combine multiple parameters (AND logic)?
   - How to encode spatial bounding boxes (2D vs 3D)?
   - How to encode temporal intervals (ISO 8601)?

6. **Support Pagination:**

   - How does offset-based pagination work (Part 1 style)?
   - How does cursor-based pagination work (Part 2 style)?
   - What are the limit parameter constraints (1 to 10,000 for Part 2)?
   - How to extract next/prev cursor tokens from responses?

7. **Implement Resource-Specific Requirements:**

   - **Systems:** Hierarchical queries (recursive subsystems), relationship filtering, spatial queries
   - **Deployments:** Spatial extent queries, temporal validity, system associations
   - **Procedures:** System associations, SensorML format support
   - **Sampling Features:** Spatial queries, feature of interest relationships, system associations
   - **Properties:** Property hierarchies (baseProperty), system associations, read-only operations
   - **DataStreams:** Schema endpoints, system/property relationships, result format parameters
   - **Observations:** Temporal queries (phenomenonTime primary), cursor-based pagination, bulk operations, schema validation
   - **Control Streams:** Schema endpoints, controlled property relationships, execution modes
   - **Commands:** Temporal queries, status/result endpoints, feasibility checking, bulk operations, status filtering

8. **Define Data Structures for Handlers:**
   - What TypeScript interfaces should be defined for query parameters?
   - What parameter validation is needed?
   - What response structures will handlers parse?
   - How to type method return values?

### Secondary Objectives

1. **Performance Optimization:**

   - How to efficiently encode query strings?
   - When to validate parameters (before request vs on server)?
   - How to reuse URL construction logic across resource types?

2. **Error Handling:**

   - What validations should throw errors vs warnings?
   - How to validate collection capabilities before building URLs?
   - How to handle missing required parameters?

3. **Extensibility:**
   - How to design for future CSAPI extensions?
   - How to add new resource types without breaking existing code?
   - How to support custom query parameters?

---

## 4. Critical Research Questions

### A. EDRQueryBuilder Pattern Study

**Questions:**

1. **Instantiation:** How is EDRQueryBuilder instantiated in `endpoint.edr(collectionId)`? What's the factory method implementation?

**Answer:** EDRQueryBuilder is instantiated via a factory method in OgcApiEndpoint that follows this pattern:

1. Check if endpoint supports EDR (conformance check - fail fast if not)
2. Check cache (`collection_id_to_edr_builder_` Map) for existing instance
3. If cached, return cached instance (same object reference)
4. If not cached, fetch collection metadata via `await this.getCollectionInfo(collection_id)`
5. Instantiate new `EDRQueryBuilder(collection)` passing collection metadata
6. Cache instance with collection ID as key: `cache.set(collection_id, result)`
7. Return the QueryBuilder instance

The factory method signature: `public async edr(collection_id: string): Promise<EDRQueryBuilder>`

2. **Metadata Encapsulation:** What metadata from `OgcApiCollectionInfo` does EDRQueryBuilder encapsulate? What properties are extracted?

**Answer:** EDRQueryBuilder encapsulates and extracts the following from `OgcApiCollectionInfo`:

- **`collection` object** (stored privately): Full collection metadata reference
- **`data_queries` object**: Contains links for query types (position, area, cube, trajectory, corridor, radius, locations, instances)
- **`parameter_names`**: Dictionary of available parameters (temperature, humidity, etc.) with metadata
- **`crs`**: Array of supported Coordinate Reference System codes
- **`links`**: Array of link objects with rel and href for navigation
- **Derived `supported_query_types`**: Boolean flags computed from `data_queries` (e.g., `area: collection.data_queries.area !== undefined`)

These are extracted in the constructor and stored as instance properties (some private, some public).

3. **Caching Strategy:** How does the factory method cache QueryBuilder instances? What is the cache key? When is cache invalidated?

**Answer:** Caching strategy:

- **Cache location:** Private Map in OgcApiEndpoint class: `collection_id_to_edr_builder_: Map<string, EDRQueryBuilder>`
- **Cache key:** Collection ID string (e.g., "temperature", "humidity")
- **Cache behavior:** One instance per collection per endpoint instance
- **Cache lifetime:** Tied to endpoint instance lifetime - no automatic invalidation
- **Cache invalidation:** Only when endpoint instance is destroyed (no explicit invalidation API)
- **Cache benefits:** Avoids redundant HTTP requests for collection metadata, ensures same collection always returns same builder instance

Example: `endpoint.edr('temp')` twice returns the exact same object (`===` equality).

4. **Lifecycle:** What happens in the EDRQueryBuilder constructor? What validation occurs? What state is initialized?

**Answer:** Constructor lifecycle:

1. **Store collection metadata:** `constructor(private collection: OgcApiCollectionInfo)`
2. **Validate required data exists:** Check `if (!collection.data_queries)` throw error "No data queries found, so cannot issue EDR queries"
3. **Extract query type support:** Compute boolean flags for each query type from presence in `data_queries` object:
   ```typescript
   this.supported_query_types = {
     area: collection.data_queries.area !== undefined,
     cube: collection.data_queries.cube !== undefined,
     // ... for all 7 EDR query types
   };
   ```
4. **Extract metadata:** Store public properties:
   - `this.supported_parameters = collection.parameter_names`
   - `this.supported_crs = collection.crs`
   - `this.links = collection.links`
5. **State is immutable** after construction - no further changes

If validation fails (no `data_queries`), constructor throws immediately and no instance is created.

5. **Method Organization:** How are EDR query methods organized? Are they grouped by query type? What naming conventions are used?

**Answer:** Method organization in EDRQueryBuilder:

- **Grouped by query type:** Each of 7 EDR query types gets two methods (build URL + execute query)
- **Naming convention:**
  - URL builders: `build<QueryType>DownloadUrl()` (e.g., `buildPositionDownloadUrl()`, `buildAreaDownloadUrl()`)
  - Query executors: `get<QueryType>()` (e.g., `getPosition()`, `getArea()`)
- **Parameter pattern:** Required params as direct arguments, optional params as options object with default `= {}`
- **Method pairs:** Each query type has both patterns (14 methods total for 7 query types)
- **Capability getter:** `get supported_queries(): Set<DataQueryType>` exposes what's available
- **No sectioning:** All methods at same level in class (no nested classes or sections)

Example: `buildPositionDownloadUrl(coords, optional_params = {})` and `async getPosition(coords, optional_params = {})`

6. **URL Building vs Execution:** Does EDRQueryBuilder provide both `buildXxxUrl()` methods (return URL) and `getXxx()` methods (execute and return data)? What's the pattern?

**Answer:** Yes, EDRQueryBuilder provides BOTH patterns:

**Build URL methods (synchronous):**

- Pattern: `build<QueryType>DownloadUrl(...): string`
- Returns: URL string
- Use case: User wants URL to fetch themselves or use in other context
- Example: `buildPositionDownloadUrl(coords, optional_params)` → `"https://api.example.com/collections/temp/position?coords=POINT(...)"`

**Execute query methods (asynchronous):**

- Pattern: `async get<QueryType>(...): Promise<EdrData>`
- Implementation: Calls build method + fetch + parse
- Returns: Typed data object
- Use case: User wants data directly, doesn't care about URL
- Example: `await getPosition(coords, optional_params)` → `{ type: 'FeatureCollection', features: [...] }`

**Relationship:** Execute methods internally call build methods: `const url = this.buildPositionDownloadUrl(coords, optional_params);`

7. **Collection Validation:** How does EDRQueryBuilder validate that a collection supports EDR operations? What errors are thrown?

**Answer:** Validation occurs at two levels:

**Constructor validation (fail fast):**

- Check: `if (!collection.data_queries)`
- Error: `throw new Error('No data queries found, so cannot issue EDR queries')`
- Result: No QueryBuilder instance created if collection doesn't support EDR at all

**Method-level validation (per query type):**

- Check: `if (!this.supported_query_types.position)` (example for position queries)
- Error: `throw new Error('Collection does not support position queries')`
- Result: Runtime error if user tries to call unsupported query type

**User-facing capability exposure:**

- Property: `builder.supported_queries` returns `Set<'position' | 'area' | 'cube' | ...>`
- Pattern: User checks capabilities before calling methods to avoid errors
- Example: `if (builder.supported_queries.has('trajectory')) { ... }`

Additional validation in methods: Parameter validation (check `supported_parameters` and `supported_crs` before adding to URL).

### B. Single-Class Architecture for 9 Resource Types

**Questions:**

8. **Method Grouping:** How should we organize methods for 9 resource types within one class? By resource type sections? By operation type (CRUD)? Both?

**Answer:** Organize by **resource type sections** (not by CRUD operation) following EDR pattern:

- Group all methods for each resource together (Systems, Deployments, Procedures, etc.)
- Within each resource group, order by: list/query → get by ID → create → update → delete → nested resources
- Use JSDoc section comments to mark resource boundaries: `// ========== Systems Resource Methods ==========`
- No nested classes or modules - all methods at same level in one class
- Example structure:

  ```typescript
  class CSAPIQueryBuilder {
    // ========== Systems ==========
    getSystems(options?) {}
    getSystem(id) {}
    createSystem(body) {}
    updateSystem(id, body) {}
    deleteSystem(id, cascade?) {}
    getSubsystems(parentId, options?) {}

    // ========== Deployments ==========
    getDeployments(options?) {}
    getDeployment(id) {}
    // ... etc
  }
  ```

  This mirrors how EDR groups methods by query type (position, area, cube, etc.).

9. **Method Naming:** What naming convention should we use for methods? `getSystems()`, `getSystemById(id)`, `createSystem(body)`, `updateSystem(id, body)`, `deleteSystem(id)`? How does this scale to 9 resource types?

**Answer:** Follow EDR pattern with CRUD-based naming:

- **List/query:** `get<ResourcePlural>(options?)` → `getSystems()`, `getDeployments()`, `getObservations()`
- **Get by ID:** `get<ResourceSingular>(id)` → `getSystem(id)`, `getDeployment(id)`, `getObservation(id)`
- **Create:** `create<ResourceSingular>(body)` → `createSystem(body)`, `createDeployment(body)`
- **Update:** `update<ResourceSingular>(id, body)` → `updateSystem(id, body)`
- **Delete:** `delete<ResourceSingular>(id, cascade?)` → `deleteSystem(id, cascade)`
- **Nested resources:** `get<Nested>(parentId, options?)` → `getSubsystems(parentId)`, `getDatastreams(systemId)`

**Scaling:** This pattern scales well - each resource type gets 4-6 methods (list, get, create, update, delete, potentially nested). For 9 resources with full CRUD, expect ~50-60 methods total.

**Naming rationale:** "get" prefix indicates read operations (GET), "create/update/delete" prefixes match HTTP verbs, singular vs plural indicates single vs multiple results.

10. **Code Reuse:** What patterns can reduce duplication across resource types? Can we abstract common URL construction logic? Can we use helper methods?

**Answer:** Several code reuse patterns based on EDR approach:

**1. Private helper methods for common operations:**

```typescript
private buildResourceListUrl(resourcePath: string, options: QueryOptions): string {
  const baseUrl = this.getResourceLink(resourcePath);
  const url = new URL(baseUrl);
  if (options.limit) url.searchParams.set('limit', options.limit.toString());
  if (options.offset) url.searchParams.set('offset', options.offset.toString());
  if (options.bbox) url.searchParams.set('bbox', options.bbox.join(','));
  return url.toString();
}
```

**2. Shared parameter encoding:**

```typescript
private addQueryParams(url: URL, options: QueryOptions): void {
  if (options.limit !== undefined) url.searchParams.set('limit', options.limit.toString());
  if (options.offset !== undefined) url.searchParams.set('offset', options.offset.toString());
  // ... common parameters
}
```

**3. Link extraction helper:**

```typescript
private getResourceLink(rel: string): string {
  const link = this.collection.links.find(l => l.rel === rel);
  if (!link) throw new Error(`Resource '${rel}' not available`);
  return link.href;
}
```

**4. Common fetch/parse logic:**

```typescript
private async fetchResource<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await response.json();
}
```

**Pattern:** Extract common logic into private helpers, call from public methods. EDR doesn't abstract much because each query type is unique; CSAPI can abstract more because resources share common patterns.

11. **Nested Endpoints:** How to handle nested endpoints like `/systems/{id}/subsystems`? Separate methods like `getSubsystems(parentId)` or parameters like `getSystems({ parent: id })`?

**Answer:** Use **separate dedicated methods** for nested endpoints, not parameters:

**✅ Recommended approach (explicit):**

```typescript
// Dedicated method for nested resource
getSubsystems(parentId: string, options?: QueryOptions): Promise<System[]> {
  const url = this.buildResourceUrl(`systems/${parentId}/subsystems`);
  // ... add query params, fetch, return
}

// Usage: clear intent
const subsystems = await builder.getSubsystems('system-123');
```

**❌ Not recommended (parameter-based):**

```typescript
getSystems(options?: { parent?: string, ... }): Promise<System[]> {
  // Builds /systems OR /systems/{parent}/subsystems based on options
  // LESS CLEAR, mixes concerns
}
```

**Rationale:**

1. **Clarity:** Separate methods make nested relationships explicit
2. **Type safety:** Different return types possible (subsystems vs all systems)
3. **URL patterns:** Different endpoints may have different query parameter support
4. **Follows REST:** Each endpoint is a distinct resource with its own method
5. **Scalability:** Easy to add more nested patterns (e.g., `getSystemDatastreams(systemId)`)

**For hierarchical queries via parent parameter:** Use the `parent` query parameter when querying the canonical endpoint: `GET /systems?parent=system-123` vs nested endpoint `GET /systems/system-123/subsystems`.

12. **State Management:** What state should CSAPIQueryBuilder maintain? Collection metadata? Supported resource types? Capabilities flags?

**Answer:** Following EDR pattern, CSAPIQueryBuilder should maintain:

**Private state (encapsulated):**

- `private collection: OgcApiCollectionInfo` - Full collection metadata reference
- `private supported_resources: Set<string>` - Computed from links (which resources are available)

**Public state (exposed to users):**

- `public links: Array<{rel: string, href: string}>` - Collection links for resource navigation
- `public id: string` - Collection ID
- `public title: string` - Collection title
- Potentially: `public extent: Extent` - Spatial/temporal extent
- Potentially: `public crs: string[]` - Supported CRS codes (if relevant for CSAPI)

**Derived getters:**

```typescript
get supportedResources(): Set<string> {
  return new Set(this.supported_resources); // Return copy, not reference
}
```

**State characteristics:**

- **Immutable after construction:** All state set in constructor, never modified
- **Derived from collection:** All state comes from `OgcApiCollectionInfo` passed to constructor
- **No shared state:** Each collection gets own QueryBuilder instance with isolated state
- **Source of truth:** Collection metadata from server is authoritative

**What NOT to maintain:**

- Runtime query state (no caching of results)
- User preferences (stateless service object)
- Connection pools (leave to fetch implementation)

### C. URL Construction Patterns

**Questions:**

13. **Canonical Endpoints:** What are the URL patterns for canonical resource endpoints? `/systems`, `/deployments`, `/procedures`, `/samplingFeatures`, `/properties`, `/datastreams`, `/observations`, `/controlstreams`, `/commands`?

**Answer:** Based on OpenAPI specs, the canonical endpoint patterns are:

**Part 1 Resources:**

- `/systems` - List/create systems
- `/systems/{systemId}` - Get/update/delete specific system
- `/deployments` - List/create deployments
- `/deployments/{deploymentId}` - Get/update/delete specific deployment
- `/procedures` - List/create procedures
- `/procedures/{procedureId}` - Get/update/delete specific procedure
- `/samplingFeatures` - List/create sampling features
- `/samplingFeatures/{featureId}` - Get/update/delete specific sampling feature
- `/properties` - List properties (read-only)
- `/properties/{propId}` - Get specific property (read-only)

**Part 2 Resources:**

- `/datastreams` - List/create datastreams
- `/datastreams/{dataStreamId}` - Get/update/delete specific datastream
- `/observations` - List/create observations (canonical, not commonly used)
- `/observations/{obsId}` - Get/update/delete specific observation
- `/controlstreams` - List/create control streams
- `/controlstreams/{controlStreamId}` - Get/update/delete specific control stream
- `/commands` - List/create commands (canonical, not commonly used)
- `/commands/{cmdId}` - Get/update/delete specific command

**Important:** CSAPI follows standard OGC API pattern: plural resource name for collections, `{id}` parameter for individual resources.

14. **Nested Endpoints:** What are ALL nested endpoint patterns? (e.g., `/systems/{id}/subsystems`, `/systems/{id}/datastreams`, `/datastreams/{id}/observations`, `/controlstreams/{id}/commands`)?

**Answer:** Nested endpoint patterns from OpenAPI specs:

**Systems nested resources:**

- `/systems/{systemId}/subsystems` - Subsystems of a specific system (hierarchical)
- `/systems/{systemId}/deployments` - Deployments for a specific system
- `/systems/{systemId}/samplingFeatures` - Sampling features for a specific system
- `/systems/{systemId}/datastreams` - Datastreams for a specific system (Part 2)
- `/systems/{systemId}/controlstreams` - Control streams for a specific system (Part 2)

**Deployments nested resources:**

- `/deployments/{deploymentId}/subdeployments` - Subdeployments of a specific deployment (hierarchical)

**DataStreams nested resources:**

- `/datastreams/{dataStreamId}/observations` - Observations for a specific datastream (most common pattern for querying observations)

**ControlStreams nested resources:**

- `/controlstreams/{controlStreamId}/commands` - Commands for a specific control stream (most common pattern for querying commands)

**Commands nested resources:**

- `/commands/{cmdId}/status` - Status updates for a specific command
- `/commands/{cmdId}/status/{statusId}` - Specific status update
- `/commands/{cmdId}/result` - Result of a specific command
- `/commands/{cmdId}/result/{resultId}` - Specific result

**Pattern:** Nested endpoints follow format `/{parentResource}/{parentId}/{childResource}` and are used for:

1. Hierarchical relationships (subsystems, subdeployments)
2. Association navigation (system → datastreams, datastream → observations)
3. Sub-resources (command → status/result)

4. **Schema Endpoints:** What are the schema endpoint patterns? `/datastreams/{id}/schema`, `/controlstreams/{id}/schema`?

**Answer:** Schema endpoint patterns from OpenAPI specs:

**DataStream schema:**

- `/datastreams/{dataStreamId}/schema` - Returns SWE Common DataComponent schema defining structure of observation results for this datastream
- HTTP Method: GET
- Response: JSON schema document (SWE Common 3.0 format)
- Purpose: Clients use this to understand observation result structure before parsing observations

**ControlStream schema:**

- `/controlstreams/{controlStreamId}/schema` - Returns SWE Common DataComponent schema defining structure of command parameters for this control stream
- HTTP Method: GET
- Response: JSON schema document (SWE Common 3.0 format)
- Purpose: Clients use this to understand command parameter structure before submitting commands

**Pattern:** `/{resourceType}/{resourceId}/schema` where schema is a sub-resource providing metadata about data structure.

**Note:** Only DataStreams and ControlStreams have schema endpoints because they deal with structured data (observations and commands respectively). Other resources (Systems, Deployments, etc.) don't have schema endpoints as they use fixed GeoJSON/SensorML formats.

16. **Special Endpoints:** What are the special-purpose endpoints? `/commands/{id}/status`, `/commands/{id}/result`, `/controlstreams/{id}/feasibility`?

**Answer:** Special-purpose endpoints from OpenAPI specs:

**Command status tracking:**

- `/commands/{cmdId}/status` - GET: Retrieve current status of command execution
- `/commands/{cmdId}/status` - POST: Add status update (typically by system, not client)
- `/commands/{cmdId}/status/{statusId}` - GET: Retrieve specific status update by ID
- Returns: Status object with fields like `status` (pending/executing/completed/failed), `percentCompletion`, `statusMessage`, `updateTime`

**Command result retrieval:**

- `/commands/{cmdId}/result` - GET: Retrieve result after command execution completes
- `/commands/{cmdId}/result` - PUT: Set result (typically by system, not client)
- `/commands/{cmdId}/result/{resultId}` - GET: Retrieve specific result by ID
- Returns: Result object with execution output data

**Feasibility checking:**

- `/controlstreams/{controlStreamId}/feasibility` - POST: Check if command parameters are feasible before actual submission
- Request body: Command parameters (same structure as command)
- Response: Feasibility report indicating whether parameters are valid/achievable
- Purpose: Pre-validation before committing to command execution

**Other potential special endpoints:**

- `/commands/{cmdId}/cancel` - POST: Cancel pending/executing command (if supported by server)

**Pattern:** These are sub-resources or actions on parent resources, typically using POST for operations beyond standard CRUD.

17. **Query String Assembly:** How to construct query strings from parameter objects? How to handle URL encoding? How to serialize arrays?

**Answer:** Following EDR pattern, use native JavaScript URL API:

**Basic pattern:**

```typescript
const url = new URL(baseUrl); // Base URL from links
if (options.limit !== undefined) {
  url.searchParams.set('limit', options.limit.toString());
}
if (options.offset !== undefined) {
  url.searchParams.set('offset', options.offset.toString());
}
return url.toString();
```

**URL encoding:** Automatic via `URL.searchParams.set()` - no manual encoding needed:

```typescript
url.searchParams.set('q', 'weather station');
// Automatically encodes spaces: ?q=weather%20station
```

**Array serialization:** Join with comma (OGC API standard):

```typescript
if (options.id?.length > 0) {
  url.searchParams.set('id', options.id.join(','));
}
// Result: ?id=sys1,sys2,sys3
```

**Conditional addition:** Always check for undefined before adding:

```typescript
if (options.bbox !== undefined) {
  url.searchParams.set('bbox', options.bbox.join(','));
}
// Only adds parameter if provided
```

**Boolean serialization:** Convert to string:

```typescript
if (options.recursive !== undefined) {
  url.searchParams.set('recursive', options.recursive.toString());
}
// Result: ?recursive=true or ?recursive=false
```

**Temporal parameters:** Pass through as-is (already ISO 8601 formatted):

```typescript
if (options.datetime) {
  url.searchParams.set('datetime', options.datetime);
}
// Result: ?datetime=2024-01-01T00:00:00Z/2024-01-31T23:59:59Z
```

**Key principles:** Use native URL API, check undefined before adding, join arrays with comma, toString() for primitives.

18. **Base URL Construction:** How to combine base URL + collection path + resource path + query string? How to handle trailing slashes?

**Answer:** Following OGC API hypermedia principle, **NEVER construct base URLs manually** - always extract from links:

**✅ Correct approach - link-based:**

```typescript
// 1. Get URL from collection links (provided by server)
const baseUrl = this.getResourceLink('systems');
// Server provides: "https://api.example.com/collections/sensors/systems"

// 2. Create URL object
const url = new URL(baseUrl);

// 3. For specific resource, append ID
const resourceUrl = new URL(`${baseUrl}/${systemId}`);
// Result: "https://api.example.com/collections/sensors/systems/system-123"

// 4. Add query parameters
url.searchParams.set('limit', '10');

// 5. Return string
return url.toString();
```

**❌ Wrong approach - manual construction:**

```typescript
// DON'T DO THIS - fragile, non-standard
const url = `${this.endpoint}/collections/${this.collectionId}/systems`;
```

**Trailing slash handling:** Let URL API normalize:

```typescript
new URL('/systems/123', 'https://api.example.com').toString();
// Result: https://api.example.com/systems/123 (no trailing slash)

new URL('systems/123', 'https://api.example.com/').toString();
// Result: https://api.example.com/systems/123 (URL API handles normalization)
```

**For nested resources:**

```typescript
const systemsUrl = this.getResourceLink('systems');
const subsystemsUrl = `${systemsUrl}/${parentId}/subsystems`;
const url = new URL(subsystemsUrl);
```

**Rationale:** Servers can use ANY URL structure. By using links, client works with any compliant implementation (even non-standard paths).

19. **HTTP Methods:** What HTTP methods map to what CRUD operations? GET = Read, POST = Create, PUT = Replace, PATCH = Update, DELETE = Delete?

**Answer:** HTTP method mapping for CSAPI (from OpenAPI specs):

**GET - Read/Retrieve:**

- List resources: `GET /systems` → array of systems
- Get by ID: `GET /systems/{id}` → single system
- Nested resources: `GET /systems/{id}/subsystems` → array of subsystems
- Schema: `GET /datastreams/{id}/schema` → schema document
- Status/Result: `GET /commands/{id}/status` → status object

**POST - Create:**

- Create resource: `POST /systems` with body → 201 Created with Location header
- Create nested: `POST /systems/{id}/subsystems` with body → 201 Created
- Bulk create: `POST /datastreams/{id}/observations` with array → 201 Created
- Actions: `POST /controlstreams/{id}/feasibility` → feasibility report
- Submit command: `POST /controlstreams/{id}/commands` with body → 201 Created

**PUT - Replace (complete):**

- Full replacement: `PUT /systems/{id}` with complete body → 200 OK or 204 No Content
- Replace result: `PUT /commands/{id}/result` with result → 200 OK
- **Idempotent:** Same request produces same result

**PATCH - Update (partial):**

- Partial update: `PATCH /systems/{id}` with partial body (JSON Patch or JSON Merge Patch) → 200 OK
- Update status: `PATCH /commands/{id}/status` with status fields → 200 OK
- **Non-idempotent:** May produce different results

**DELETE - Remove:**

- Delete resource: `DELETE /systems/{id}` → 204 No Content
- Cascade delete: `DELETE /systems/{id}?cascade=true` → 204 No Content
- **Note:** Some resources may be retained (archives) rather than truly deleted

**Response codes:**

- 200 OK - successful GET/PUT/PATCH with response body
- 201 Created - successful POST with Location header
- 204 No Content - successful DELETE or PUT/PATCH without response body
- 400 Bad Request - validation error
- 404 Not Found - resource doesn't exist
- 409 Conflict - constraint violation (e.g., can't delete system with datastreams)

20. **Request Bodies:** For POST/PUT/PATCH, how to pass request bodies? Method parameter? TypeScript interface for body structure?

**Answer:** Pass request bodies as typed method parameters:

**Method signature pattern:**

```typescript
async createSystem(body: SystemInput): Promise<System> {
  const url = this.getResourceLink('systems');
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/geo+json' },
    body: JSON.stringify(body)
  });
  // ... handle response
}
```

**TypeScript interfaces for bodies:**

```typescript
interface SystemInput {
  type: 'Feature';
  geometry: GeoJSONGeometry;
  properties: {
    name: string;
    description?: string;
    systemType: string; // URI like 'http://www.w3.org/ns/sosa/Sensor'
    uniqueIdentifier?: string; // URN
    validTime?: TemporalPeriod;
    // ... other system properties
  };
}

interface ObservationInput {
  phenomenonTime: string; // ISO 8601
  resultTime?: string;
  result: any; // Structure defined by datastream schema
  resultQuality?: QualityInfo;
  parameters?: Record<string, any>;
}

interface CommandInput {
  issueTime?: string;
  executionTime?: string;
  parameters: any; // Structure defined by controlstream schema
  priority?: number;
}
```

**For bulk operations (arrays):**

```typescript
async createObservations(
  datastreamId: string,
  observations: ObservationInput[]
): Promise<Observation[]> {
  const url = `${this.getDatastreamUrl(datastreamId)}/observations`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(observations) // Array directly
  });
  // ...
}
```

**For updates (partial):**

```typescript
async updateSystem(
  id: string,
  updates: Partial<SystemInput> // Partial type for PATCH
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

**Pattern:** Strongly typed body parameter, serialize with JSON.stringify(), set appropriate Content-Type header.

21. **Content-Type Headers:** What Content-Type headers for different body formats? `application/json`, `application/geo+json`, `application/sml+json`?

**Answer:** Content-Type headers vary by resource type and format:

**GeoJSON resources (Systems, Deployments, Sampling Features):**

- `Content-Type: application/geo+json` - Preferred for GeoJSON Feature/FeatureCollection
- `Content-Type: application/json` - Also acceptable (GeoJSON is valid JSON)
- Used for: POST/PUT/PATCH of Part 1 spatial resources

**SensorML resources (Systems, Procedures with detailed descriptions):**

- `Content-Type: application/sml+json` - SensorML 3.0 JSON encoding
- Used for: POST/PUT of Systems or Procedures with detailed sensor metadata

**Standard JSON resources (DataStreams, ControlStreams, Properties):**

- `Content-Type: application/json` - Standard JSON
- Used for: POST/PUT/PATCH of Part 2 resources and metadata resources

**SWE Common resources (Observations, Commands):**

- `Content-Type: application/json` - For JSON-encoded observations/commands
- `Content-Type: application/swe+json` - SWE Common JSON encoding (if server supports)
- `Content-Type: text/csv` or `application/swe+text` - For CSV/text-encoded observations (bulk data)
- `Content-Type: application/octet-stream` - For binary-encoded observations (high-volume streaming)

**Partial updates (PATCH):**

- `Content-Type: application/merge-patch+json` - JSON Merge Patch (RFC 7396)
- `Content-Type: application/json-patch+json` - JSON Patch (RFC 6902)

**Format negotiation via Accept header (GET requests):**

- `Accept: application/geo+json` - Request GeoJSON format
- `Accept: application/sml+json` - Request SensorML format
- `Accept: application/json` - Request standard JSON
- Or use `?f=geojson` query parameter

**Pattern:** Match Content-Type to resource format: GeoJSON for spatial, SensorML for detailed sensors, JSON for others.

22. **Response Handling:** Should QueryBuilder methods return URLs only or execute requests and return parsed data? Or both patterns?

**Answer:** Follow EDR pattern - provide BOTH approaches but **ONLY implement execute pattern** initially:

**Recommended approach (execute and return data):**

```typescript
async getSystems(options?: QueryOptions): Promise<System[]> {
  const url = this.buildSystemsUrl(options);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data = await response.json();
  return data.features || data.items; // Handle both formats
}
```

**Optional approach (build URL only) - for advanced users:**

```typescript
buildSystemsUrl(options?: QueryOptions): string {
  const baseUrl = this.getResourceLink('systems');
  const url = new URL(baseUrl);
  this.addQueryParams(url, options);
  return url.toString();
}

// User can fetch themselves:
const url = builder.buildSystemsUrl({ limit: 10 });
const response = await fetch(url);
```

**Recommendation for CSAPI:**

- **Start with execute methods only:** `getSystems()`, `getSystem()`, etc.
- **Add build methods later if needed:** `buildSystemsUrl()`, `buildSystemUrl()`
- **Rationale:**
  - Most users want data, not URLs
  - Execute methods can use build methods internally (DRY)
  - Build methods add API surface area (more to document/test)
  - EDR provides both but most users use execute methods

**Return type pattern:**

- List methods: `Promise<Resource[]>`
- Get by ID: `Promise<Resource>`
- Create: `Promise<Resource>` (returns created resource with ID)
- Update: `Promise<Resource>` (returns updated resource)
- Delete: `Promise<void>` (no return value on 204 No Content)

23. **Cascade Delete:** How to support cascade delete? Query parameter `?cascade=true`? Separate method?

**Answer:** Use **query parameter** approach (not separate method):

**Recommended implementation:**

```typescript
async deleteSystem(
  id: string,
  options?: { cascade?: boolean }
): Promise<void> {
  const baseUrl = this.getResourceLink('systems');
  const url = new URL(`${baseUrl}/${id}`);

  // Add cascade parameter if requested
  if (options?.cascade) {
    url.searchParams.set('cascade', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'DELETE'
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  // DELETE returns 204 No Content on success
}
```

**Usage:**

```typescript
// Delete system only (fails if has dependencies)
await builder.deleteSystem('system-123');

// Delete system and all dependent resources
await builder.deleteSystem('system-123', { cascade: true });
```

**❌ Not recommended (separate method):**

```typescript
// Creates API bloat
async deleteSystem(id: string): Promise<void> { }
async deleteSystemCascade(id: string): Promise<void> { }
```

**Cascade behavior from OpenAPI specs:**

- `cascade=false` or omitted: Delete fails if resource has dependents (409 Conflict)
- `cascade=true`: Delete resource and ALL dependent resources (subsystems, datastreams, observations, etc.)
- **Dangerous operation:** Potentially deletes large amounts of data
- **Server-side validation:** Server checks authorization and constraints

**Applies to:** Systems, Deployments, DataStreams, ControlStreams (resources that can have dependents).

**Does NOT apply to:** Observations, Commands, Procedures, Sampling Features, Properties (leaf nodes or shared resources).

### E. Standard OGC API Query Parameters

**Questions:**

24. **bbox Parameter:** How to encode spatial bounding box? Comma-separated coordinates? 2D vs 3D support? CRS parameter?

**Answer:** The `bbox` parameter filters resources by spatial bounding box:

**Format:** Comma-separated coordinates in WGS 84 (EPSG:4326) by default: `minLon,minLat,maxLon,maxLat`

**Examples:**

```
bbox=-180,-90,180,90           # Global extent
bbox=-10.0,50.0,2.0,60.0       # Part of Europe
bbox=-122.4,37.7,-122.3,37.8   # San Francisco area
```

**3D Support (optional):** Add elevation values for 3D bbox: `minLon,minLat,minElev,maxLon,maxLat,maxElev`

```
bbox=-122.4,37.7,0,-122.3,37.8,1000  # With elevation range
```

**CRS Parameter:** While OGC API standard supports CRS negotiation via `bbox-crs` parameter, CSAPI Part 1 spec uses WGS 84 as default and primary CRS. Most implementations accept only WGS 84 for bbox queries.

**Behavior:** Only resources with geometry that **intersects** the bounding box are returned (not just contained within).

**TypeScript signature:**

```typescript
bbox?: [number, number, number, number] | [number, number, number, number, number, number]
```

**URL encoding:**

```typescript
if (options.bbox) {
  url.searchParams.set('bbox', options.bbox.join(','));
}
// Result: ?bbox=-180,-90,180,90
```

25. **datetime Parameter:** How to encode temporal intervals? ISO 8601 format? Single instant vs interval? Open intervals (`../2024-01-31`, `2024-01-01/..`)?

**Answer:** The `datetime` parameter filters resources by temporal extent using ISO 8601 format:

**Single instant (exact time):**

```
datetime=2024-02-02T12:00:00Z     # Specific instant
datetime=2024-02-02                # Whole day (shorthand)
```

**Closed interval (start and end):**

```
datetime=2024-01-01T00:00:00Z/2024-01-31T23:59:59Z   # January 2024
datetime=2024-01-01/2024-01-31                        # Shorthand (whole days)
```

**Open start (everything up to date):**

```
datetime=../2024-01-31             # Everything before Feb 1, 2024
datetime=../2024-01-31T23:59:59Z   # Everything before midnight
```

**Open end (everything from date onwards):**

```
datetime=2024-01-01/..             # Everything from Jan 1, 2024 onwards
datetime=2024-01-01T00:00:00Z/..   # Same with explicit time
```

**Special keywords:**

```
datetime=now/..                    # From current time onwards
datetime=../now                    # Everything up to now
datetime=latest                    # Most recent resource only
```

**Behavior:** Resources with `validTime` that **intersects** the specified datetime/interval are returned.

**TypeScript signature:**

```typescript
datetime?: string  // ISO 8601 instant or interval
```

**URL encoding:** Pass string directly (already properly formatted):

```typescript
if (options.datetime) {
  url.searchParams.set('datetime', options.datetime);
}
```

**Note:** Part 1 resources use `datetime` for validity periods. Part 2 resources use specialized temporal parameters (`phenomenonTime`, `resultTime`, etc.) for observations/commands.

26. **limit Parameter:** What are valid range values? 1 to 10,000 for Part 2? Different defaults for Part 1 vs Part 2?

**Answer:** The `limit` parameter controls maximum number of items returned:

**Valid range:** 1 to 10,000 (inclusive)

```
limit=1        # Minimum (single resource)
limit=100      # Common page size
limit=10000    # Maximum allowed
```

**Default value:** 10 (if limit not specified)

**Part 1 vs Part 2:**

- **Part 1** (Systems, Deployments, etc.): Default 10, max 10,000
- **Part 2** (DataStreams, Observations, etc.): Default 10, max 10,000
- **Same limits for both parts** per OpenAPI specs

**Behavior:** Limits items at **first level only** (nested objects don't count toward limit)

**TypeScript signature:**

```typescript
limit?: number  // 1-10000, default 10
```

**URL encoding:**

```typescript
if (options.limit !== undefined) {
  if (options.limit < 1 || options.limit > 10000) {
    throw new Error('limit must be between 1 and 10000');
  }
  url.searchParams.set('limit', options.limit.toString());
}
```

**Server behavior:**

- Returns up to `limit` items
- May return fewer if insufficient matches
- If more items exist, provides pagination links (next/prev)
- Returns HTTP 400 Bad Request if limit out of range

27. **offset Parameter:** How does offset-based pagination work? Combined with limit? Start at 0 or 1?

**Answer:** The `offset` parameter implements offset-based pagination for Part 1 resources:

**Format:** Non-negative integer (0-based index)

```
offset=0       # First page (default)
offset=10      # Skip first 10 items
offset=100     # Skip first 100 items
```

**Combined with limit:**

```
limit=10&offset=0    # Items 0-9 (page 1)
limit=10&offset=10   # Items 10-19 (page 2)
limit=10&offset=20   # Items 20-29 (page 3)
```

**Calculate next page offset:**

```typescript
const nextOffset = currentOffset + limit;
```

**TypeScript signature:**

```typescript
interface PaginationOptions {
  limit?: number; // Items per page (default 10)
  offset?: number; // Zero-based starting index (default 0)
}
```

**URL encoding:**

```typescript
if (options.offset !== undefined) {
  url.searchParams.set('offset', options.offset.toString());
}
if (options.limit !== undefined) {
  url.searchParams.set('limit', options.limit.toString());
}
// Result: ?limit=10&offset=20
```

**Part 1 vs Part 2:**

- **Part 1:** Uses offset-based pagination (offset + limit)
- **Part 2:** May use cursor-based pagination (cursor + limit) for observations/commands (better for streaming data)

**Important:** Part 1 spec does NOT explicitly document `offset` parameter in OpenAPI spec, but it's part of OGC API - Features standard that CSAPI Part 1 extends. Servers SHOULD support it.

28. **f Parameter:** What format values are supported? `json`, `geojson`, `sml+json`, `swe+json`, `swe+text`, `html`?

**Answer:** The `f` parameter specifies response format (content negotiation):

**Supported format values:**

**Part 1 Resources (Systems, Deployments, Procedures, Sampling Features):**

- `f=json` - Standard JSON
- `f=geojson` - GeoJSON (default for spatial resources)
- `f=sml+json` - SensorML 3.0 JSON (for detailed system descriptions)
- `f=html` - Human-readable HTML representation

**Part 2 Resources (DataStreams, ControlStreams, Properties):**

- `f=json` - Standard JSON (default for non-spatial resources)
- `f=swe+json` - SWE Common JSON encoding

**Observations/Commands:**

- `f=json` - Standard JSON (default)
- `f=swe+json` - SWE Common JSON
- `f=swe+text` - CSV/text encoding (for bulk observations)
- `f=swe+binary` - Binary encoding (high-performance streaming)
- `f=om+json` - O&M JSON (legacy format)

**Examples:**

```
GET /systems?f=geojson       # GeoJSON Feature Collection
GET /systems/sys1?f=sml+json # SensorML document
GET /procedures/p1?f=sml+json # Detailed procedure description
GET /observations?f=swe+text  # CSV format
```

**TypeScript signature:**

```typescript
type Format =
  | 'json'
  | 'geojson'
  | 'sml+json'
  | 'swe+json'
  | 'swe+text'
  | 'html';

interface QueryOptions {
  f?: Format;
}
```

**URL encoding:**

```typescript
if (options.f) {
  url.searchParams.set('f', options.f);
}
```

**Alternative:** Use HTTP `Accept` header instead of query parameter:

```typescript
headers: {
  'Accept': 'application/geo+json'  // Same as f=geojson
}
```

**Default formats (when f not specified):**

- Systems, Deployments, Sampling Features → `application/geo+json`
- Procedures → `application/sml+json` or `application/geo+json`
- DataStreams, ControlStreams, Properties → `application/json`
- Observations, Commands → `application/json`

### F. CSAPI-Specific Query Parameters

**Questions:**

29. **id Parameter:** How to filter by multiple IDs? Comma-separated list? OR logic? Example: `id=sys1,sys2,sys3`?

**Answer:** The `id` parameter filters resources by one or more identifiers:

**Format:** Comma-separated list of local IDs or unique IDs (URIs)

```
id=sys1                                    # Single local ID
id=sys1,sys2,sys3                          # Multiple local IDs (OR logic)
id=urn:example:system:001                  # Single unique ID (URN)
id=urn:example:system:001,urn:example:system:002  # Multiple URNs
```

**Logic:** OR operation - returns resources matching **any** of the provided IDs

**Applies to:** All resource types (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, ControlStreams, Commands)

**TypeScript signature:**

```typescript
id?: string[]  // Array of IDs (local or URN)
```

**URL encoding:**

```typescript
if (options.id?.length > 0) {
  url.searchParams.set('id', options.id.join(','));
}
// Result: ?id=sys1,sys2,sys3
```

**OpenAPI spec schema:**

```yaml
schema:
  oneOf:
    - type: string # Single ID
    - type: array # Multiple IDs
      items:
        type: string
```

**Note:** `id` parameter is different from `{systemId}` path parameter. Query parameter filters collections; path parameter accesses specific resource.

30. **uid Parameter:** How to filter by unique identifier? URN format? Single value or multiple?

**Answer:** CSAPI does NOT have a separate `uid` parameter. The `id` parameter accepts **both** local IDs and unique identifiers (UIDs):

**Rationale:** The `id` parameter is polymorphic - accepts local IDs OR URN/URI identifiers:

```
id=sys1                           # Local ID
id=urn:uuid:550e8400-e29b-41d4    # UUID URN
id=urn:ogc:def:identifier:001     # OGC URN
id=http://example.org/systems/s1  # HTTP URI
```

**No separate uid parameter needed** - use `id` with URN/URI values.

**Schema note:** OpenAPI spec defines `idListSchema` as:

```yaml
idListSchema:
  description: List of resource local IDs or unique identifiers (URIs)
  oneOf:
    - type: string # Can be local ID or URI
    - type: array # Array of IDs or URIs
```

**Usage:**

```typescript
// Filter by unique IDs
getSystems({
  id: ['urn:uuid:123', 'urn:uuid:456'],
});
```

31. **q Parameter:** How does full-text search work? What properties are searched? Case sensitivity?

**Answer:** The `q` parameter performs full-text keyword search:

**Format:** Comma-separated list of keywords (1-50 characters each)

```
q=temperature                    # Single keyword
q=temp,humidity,pressure         # Multiple keywords (OR logic)
q=weather,station                # Multiple keywords
```

**Searched properties:**

- `name` (always searched)
- `description` (always searched)
- Other textual fields (server-dependent)

**Search behavior:**

- **OR logic:** Resources matching **any** keyword are returned
- **Partial match:** Keyword can match part of text (e.g., "temp" matches "temperature")
- **Case insensitive:** Search is case-insensitive by default
- **Server-dependent:** Exact matching rules vary by implementation

**TypeScript signature:**

```typescript
q?: string[]  // Array of keywords (1-50 chars each)
```

**URL encoding:**

```typescript
if (options.q?.length > 0) {
  const keywords = options.q.filter((k) => k.length >= 1 && k.length <= 50);
  url.searchParams.set('q', keywords.join(','));
}
// Result: ?q=temp,humidity
```

**OpenAPI spec:**

```yaml
keyword:
  name: q
  schema:
    type: array
    items:
      type: string
      minLength: 1
      maxLength: 50
  explode: false
```

**Applies to:** All resource types

32. **Property Filters:** How to filter by arbitrary resource properties? Example: `name=Weather%20Station`, `systemType=sosa:Sensor`?

**Answer:** CSAPI does NOT support arbitrary property filtering via query parameters in the OpenAPI spec.

**What IS supported:**

- `id` - Filter by resource IDs
- `q` - Full-text keyword search (searches name, description, and other text fields)
- Specific relationship filters: `parent`, `system`, `procedure`, `foi`, `observedProperty`, `controlledProperty`, `baseProperty`
- Spatial filters: `bbox`, `geom`
- Temporal filters: `datetime`, `phenomenonTime`, `resultTime`, etc.

**What is NOT supported:**

- Generic property filters like `name=value`, `systemType=uri`, `assetType=sensor`
- JSONPath or dot notation for nested properties
- Custom property filters

**Workaround:** Use `q` parameter for text-based properties:

```
q=weather,station  # Finds resources with "weather" or "station" in name/description
```

**Future consideration:** Some server implementations MAY support vendor-specific property filters, but these are not standardized in CSAPI spec.

**For exact property matching:** Client must fetch all resources and filter locally, or use relationship parameters (parent, system, etc.) to narrow search scope.

33. **recursive Parameter:** How does hierarchical recursion work? Boolean flag? `recursive=true` for all descendants?

**Answer:** The `recursive` parameter enables hierarchical traversal for nested resources:

**Format:** Boolean flag (`true` or `false`)

```
recursive=true     # Include all descendants recursively
recursive=false    # Direct children only (default)
```

**Applies to:**

- **Systems:** `GET /systems?recursive=true` - includes subsystems, sub-subsystems, etc.
- **Systems subsystems:** `GET /systems/{id}/subsystems?recursive=true` - all nested subsystems
- **Deployments:** `GET /deployments?recursive=true` - includes subdeployments at all levels
- **Deployments subdeployments:** `GET /deployments/{id}/subdeployments?recursive=true` - all nested subdeployments

**Behavior:**

- `recursive=false` (default): Returns only immediate children
- `recursive=true`: Returns entire hierarchy tree (all descendants)

**Example:**

```
System A
  ├─ Subsystem B
  │   └─ Subsystem D
  └─ Subsystem C

GET /systems/A/subsystems?recursive=false
→ Returns: [B, C]

GET /systems/A/subsystems?recursive=true
→ Returns: [B, C, D]
```

**TypeScript signature:**

```typescript
recursive?: boolean  // Default false
```

**URL encoding:**

```typescript
if (options.recursive !== undefined) {
  url.searchParams.set('recursive', options.recursive.toString());
}
```

**OpenAPI spec:**

```yaml
recursive:
  name: recursive
  schema:
    type: boolean
    default: false
  description: If true, instructs the server to include nested resources in the search results
```

**Performance note:** Recursive queries can return large result sets for deep hierarchies. Use with limit parameter to control response size.

34. **parent Parameter:** How to filter by parent resource? Single ID or multiple? Apply to systems and deployments?

**Answer:** The `parent` parameter filters resources by their parent resource ID:

**Format:** Comma-separated list of parent IDs (local or URN)

```
parent=sys1                         # Single parent
parent=sys1,sys2                    # Multiple parents (OR logic)
parent=urn:example:system:parent001 # Parent by URN
```

**Applies to:**

- **Systems:** Filter systems by parent system ID
- **Deployments:** Filter deployments by parent deployment ID

**Logic:** OR operation - returns resources with parent matching **any** of the provided IDs

**TypeScript signature:**

```typescript
parent?: string[]  // Array of parent IDs
```

**URL encoding:**

```typescript
if (options.parent?.length > 0) {
  url.searchParams.set('parent', options.parent.join(','));
}
// Result: ?parent=sys1,sys2
```

**OpenAPI spec:**

```yaml
parentIdList:
  name: parent
  schema:
    description: List of resource local IDs or unique IDs (URI)
    oneOf:
      - type: string
      - type: array
        items:
          type: string
```

**Usage examples:**

```typescript
// Get all subsystems of sys1 (without recursion)
GET /systems?parent=sys1

// Get all subdeployments of deployment123
GET /deployments?parent=deployment123

// Equivalent to nested endpoint (but uses canonical endpoint)
GET /systems?parent=sys1  ≈  GET /systems/sys1/subsystems
```

**Note:** Using nested endpoint (`/systems/{id}/subsystems`) is preferred over `parent` parameter for better RESTful semantics.

35. **system Parameter:** How to filter resources by associated system? Single ID or multiple? Apply to which resource types?

**Answer:** The `system` parameter filters resources by associated system ID:

**Format:** Comma-separated list of system IDs (local or URN)

```
system=sys1                         # Single system
system=sys1,sys2,sys3               # Multiple systems (OR logic)
system=urn:example:system:sensor001 # System by URN
```

**Applies to:**

- **Deployments:** Filter by deployed system
- **Procedures:** Filter by system implementing the procedure
- **Sampling Features:** Filter by system that uses the sampling feature
- **Properties:** Filter by system that measures/controls the property
- **DataStreams** (Part 2): Filter by system producing observations
- **Observations** (Part 2): Filter by observing system
- **ControlStreams** (Part 2): Filter by controlled system
- **Commands** (Part 2): Filter by target system

**Logic:** OR operation - returns resources associated with **any** of the provided systems

**TypeScript signature:**

```typescript
system?: string[]  // Array of system IDs
```

**URL encoding:**

```typescript
if (options.system?.length > 0) {
  url.searchParams.set('system', options.system.join(','));
}
// Result: ?system=sys1,sys2
```

**OpenAPI spec:**

```yaml
systemIdList:
  name: system
  schema:
    description: List of system local IDs or unique IDs (URI)
    oneOf:
      - type: string
      - type: array
        items:
          type: string
```

**Usage examples:**

```typescript
// Get all deployments of specific system
GET /deployments?system=weather-station-1

// Get all datastreams from multiple systems
GET /datastreams?system=sys1,sys2,sys3

// Equivalent to nested endpoint
GET /datastreams?system=sys1  ≈  GET /systems/sys1/datastreams
```

36. **deployment Parameter:** How to filter by deployment? Single ID or multiple?

**Answer:** The `deployment` parameter filters resources by deployment ID:

**Format:** Comma-separated list of deployment IDs (local or URN)

```
deployment=dep1                        # Single deployment
deployment=dep1,dep2                   # Multiple deployments (OR logic)
deployment=urn:example:deployment:mission01  # Deployment by URN
```

**Applies to:**

- **Systems:** Filter systems by deployment they're part of
- **Procedures:** Filter procedures by deployment context
- **Sampling Features:** Filter by deployment
- **DataStreams** (Part 2): Filter by deployment context
- **Observations** (Part 2): Filter by deployment during which observation was made
- **ControlStreams** (Part 2): Filter by deployment
- **Commands** (Part 2): Filter by deployment context

**Logic:** OR operation - returns resources associated with **any** of the provided deployments

**TypeScript signature:**

```typescript
deployment?: string[]  // Array of deployment IDs
```

**URL encoding:**

```typescript
if (options.deployment?.length > 0) {
  url.searchParams.set('deployment', options.deployment.join(','));
}
// Result: ?deployment=dep1,dep2
```

**Note:** OpenAPI spec does NOT explicitly define `deployment` parameter in Part 1. It's **implied** by the spec structure but not formally documented. Implementations SHOULD support it for consistency.

37. **procedure Parameter:** How to filter by procedure? Single ID or multiple?

**Answer:** The `procedure` parameter filters resources by procedure ID:

**Format:** Comma-separated list of procedure IDs (local or URN)

```
procedure=proc1                         # Single procedure
procedure=proc1,proc2                   # Multiple procedures (OR logic)
procedure=urn:example:procedure:method1 # Procedure by URN
```

**Applies to:**

- **Systems:** Filter systems that implement specific procedure(s)
- **DataStreams** (Part 2): Filter by acquisition procedure
- **Observations** (Part 2): Filter by observation procedure

**Logic:** OR operation - returns resources using **any** of the provided procedures

**TypeScript signature:**

```typescript
procedure?: string[]  // Array of procedure IDs
```

**URL encoding:**

```typescript
if (options.procedure?.length > 0) {
  url.searchParams.set('procedure', options.procedure.join(','));
}
// Result: ?procedure=proc1,proc2
```

**OpenAPI spec:**

```yaml
procedureIdList:
  name: procedure
  schema:
    description: List of procedure local IDs or unique IDs (URI)
    oneOf:
      - type: string
      - type: array
        items:
          type: string
```

**Usage:**

```typescript
// Get all systems implementing calibration procedure
GET /systems?procedure=calibration-method-v2

// Get observations made with specific procedure
GET /observations?procedure=satellite-imaging-v1
```

38. **foi Parameter:** How to filter by feature of interest? Single ID or multiple?

**Answer:** The `foi` parameter filters resources by feature of interest ID:

**Format:** Comma-separated list of FOI IDs (local or URN)

```
foi=sf1                                 # Single FOI
foi=sf1,sf2,sf3                         # Multiple FOIs (OR logic)
foi=urn:example:feature:location001     # FOI by URN
```

**Applies to:**

- **Systems:** Filter systems observing specific feature(s)
- **Deployments:** Filter deployments related to specific feature(s)
- **Sampling Features:** Filter by related feature of interest
- **DataStreams** (Part 2): Filter by ultimate feature of interest
- **Observations** (Part 2): Filter by feature being observed

**Logic:** OR operation - returns resources associated with **any** of the provided features

**TypeScript signature:**

```typescript
foi?: string[]  // Array of feature of interest IDs
```

**URL encoding:**

```typescript
if (options.foi?.length > 0) {
  url.searchParams.set('foi', options.foi.join(','));
}
// Result: ?foi=sf1,sf2
```

**OpenAPI spec:**

```yaml
foiIdList:
  name: foi
  schema:
    description: List of feature local IDs or unique IDs (URI)
    oneOf:
      - type: string
      - type: array
        items:
          type: string
```

**Usage:**

```typescript
// Get all observations of specific building
GET /observations?foi=building-123

// Get datastreams observing multiple locations
GET /datastreams?foi=loc1,loc2,loc3
```

39. **observedProperty Parameter:** How to filter by observed property? URI or ID? Single or multiple?

**Answer:** The `observedProperty` parameter filters resources by observed property:

**Format:** Comma-separated list of property IDs or URIs

```
observedProperty=temp                                    # Single property (local ID)
observedProperty=temp,humidity,pressure                  # Multiple (OR logic)
observedProperty=http://mmisw.org/ont/cf/parameter/air_temperature  # Property URI
```

**Applies to:**

- **Systems:** Filter systems observing specific property/properties
- **DataStreams** (Part 2): Filter by observed property
- **Observations** (Part 2): Filter by property being observed
- **Properties:** Filter properties by ID (redundant, but supported)

**ID vs URI:** Can use either local property ID OR full semantic URI

**Logic:** OR operation - returns resources observing **any** of the provided properties

**TypeScript signature:**

```typescript
observedProperty?: string[]  // Array of property IDs or URIs
```

**URL encoding:**

```typescript
if (options.observedProperty?.length > 0) {
  url.searchParams.set('observedProperty', options.observedProperty.join(','));
}
// Result: ?observedProperty=temp,humidity
```

**OpenAPI spec:**

```yaml
obsPropIdList:
  name: observedProperty
  schema:
    description: List of property local IDs or unique IDs (URI)
    oneOf:
      - type: string
      - type: array
        items:
          type: string
```

**Usage:**

```typescript
// Get all temperature datastreams
GET /datastreams?observedProperty=air-temperature

// Get observations of multiple properties
GET /observations?observedProperty=temp,humidity,pressure
```

40. **controlledProperty Parameter:** How to filter by controlled property? URI or ID? Single or multiple?

**Answer:** The `controlledProperty` parameter filters resources by controlled property:

**Format:** Comma-separated list of property IDs or URIs

```
controlledProperty=pan                                   # Single property (local ID)
controlledProperty=pan,tilt                              # Multiple (OR logic)
controlledProperty=http://example.org/ont/pan_angle      # Property URI
```

**Applies to:**

- **Systems:** Filter systems controlling specific property/properties
- **ControlStreams** (Part 2): Filter by controlled property
- **Commands** (Part 2): Filter by property being controlled
- **Properties:** Filter properties that are controllable

**ID vs URI:** Can use either local property ID OR full semantic URI

**Logic:** OR operation - returns resources controlling **any** of the provided properties

**TypeScript signature:**

```typescript
controlledProperty?: string[]  // Array of property IDs or URIs
```

**URL encoding:**

```typescript
if (options.controlledProperty?.length > 0) {
  url.searchParams.set(
    'controlledProperty',
    options.controlledProperty.join(',')
  );
}
// Result: ?controlledProperty=pan,tilt
```

**OpenAPI spec:**

```yaml
controlPropIdList:
  name: controlledProperty
  schema:
    description: List of property local IDs or unique IDs (URI)
    oneOf:
      - type: string
      - type: array
        items:
          type: string
```

**Usage:**

```typescript
// Get all pan-tilt control streams
GET /controlstreams?controlledProperty=pan,tilt

// Get commands controlling specific property
GET /commands?controlledProperty=camera-zoom
```

41. **baseProperty Parameter:** How to filter properties by base property? Property hierarchy?

**Answer:** The `baseProperty` parameter filters properties by their base property (parent in property hierarchy):

**Format:** Comma-separated list of base property IDs or URIs

```
baseProperty=temperature                                  # Single base property
baseProperty=temp,pressure                                # Multiple (OR logic)
baseProperty=http://mmisw.org/ont/cf/parameter/temperature  # Base property URI
```

**Applies to:**

- **Properties ONLY:** Filter derived properties by their base property

**Property hierarchy example:**

```
temperature (base)
  ├─ air_temperature (derived)
  ├─ water_temperature (derived)
  └─ surface_temperature (derived)
```

**Usage:**

```typescript
// Get all temperature-related properties
GET /properties?baseProperty=temperature
// Returns: air_temperature, water_temperature, surface_temperature

// Get properties derived from multiple base properties
GET /properties?baseProperty=temperature,pressure
```

**Logic:** OR operation - returns properties derived from **any** of the provided base properties

**TypeScript signature:**

```typescript
baseProperty?: string[]  // Array of base property IDs or URIs
```

**URL encoding:**

```typescript
if (options.baseProperty?.length > 0) {
  url.searchParams.set('baseProperty', options.baseProperty.join(','));
}
// Result: ?baseProperty=temperature,pressure
```

**OpenAPI spec:**

```yaml
basePropIdList:
  name: baseProperty
  schema:
    description: List of property local IDs or unique IDs (URI)
    oneOf:
      - type: string
      - type: array
        items:
          type: string
```

**Note:** Property hierarchy enables semantic querying - finding all temperature properties regardless of specific type.

### G. Part 2 Temporal Query Parameters

**Questions:**

42. **phenomenonTime Parameter:** How to encode when observation was made? ISO 8601 intervals? Primary temporal filter for observations?

**Answer:** The `phenomenonTime` parameter filters observations by when the phenomenon was observed:

**Format:** ISO 8601 instant or interval (same syntax as `datetime`)

**Single instant:**

```
phenomenonTime=2024-02-02T12:00:00Z     # Exact observation time
phenomenonTime=2024-02-02                # Shorthand (whole day)
```

**Closed interval:**

```
phenomenonTime=2024-01-01T00:00:00Z/2024-01-31T23:59:59Z  # January observations
phenomenonTime=2024-01-01/2024-01-31                       # Shorthand
```

**Open intervals:**

```
phenomenonTime=../2024-01-31             # All observations before Feb 1
phenomenonTime=2024-01-01/..             # All observations from Jan 1 onwards
phenomenonTime=../now                    # All observations up to now
phenomenonTime=now/..                    # Future scheduled observations
```

**Special keyword:**

```
phenomenonTime=latest                    # Most recent observation only
```

**Applies to:**

- **DataStreams:** Filter by phenomenon time extent
- **Observations:** **Primary temporal filter** - when phenomenon was observed

**Behavior:** Returns observations where `phenomenonTime` **intersects** the specified interval

**TypeScript signature:**

```typescript
phenomenonTime?: string  // ISO 8601 instant or interval
```

**URL encoding:**

```typescript
if (options.phenomenonTime) {
  url.searchParams.set('phenomenonTime', options.phenomenonTime);
}
```

**OpenAPI spec:**

```yaml
phenomenonTime:
  name: phenomenonTime
  schema:
    type: string # ISO 8601 format
  description: Filter observations by phenomenon time
```

**Note:** `phenomenonTime` is the **when the phenomenon occurred** (e.g., when temperature was 25°C), distinct from `resultTime` (when result became available).

43. **resultTime Parameter:** How to encode when result became available? ISO 8601 intervals?

**Answer:** The `resultTime` parameter filters by when the observation result was produced/became available:

**Format:** ISO 8601 instant or interval (same syntax as `phenomenonTime`)

**Examples:**

```
resultTime=2024-02-02T12:05:00Z          # Result available at specific time
resultTime=2024-01-01/2024-01-31         # Results produced in January
resultTime=../now                        # All results available up to now
resultTime=latest                        # Most recently produced result
```

**Applies to:**

- **DataStreams:** Filter by result time extent
- **Observations:** Filter by when result was produced

**Phenomenon time vs Result time:**

- `phenomenonTime`: When phenomenon occurred (e.g., 12:00:00 - temperature measured)
- `resultTime`: When result became available (e.g., 12:05:00 - after processing/transmission)
- Usually `resultTime >= phenomenonTime` (processing delay)
- Can be equal for real-time systems

**Use cases:**

- Find observations processed/received in specific timeframe
- Query by data availability rather than phenomenon occurrence
- Filter by data latency

**TypeScript signature:**

```typescript
resultTime?: string  // ISO 8601 instant or interval
```

**URL encoding:**

```typescript
if (options.resultTime) {
  url.searchParams.set('resultTime', options.resultTime);
}
```

**OpenAPI spec:**

```yaml
resultTime:
  name: resultTime
  schema:
    type: string # ISO 8601 format
  description: Filter observations by result time
```

44. **executionTime Parameter:** How to encode when command should be/was executed? ISO 8601 intervals?

**Answer:** The `executionTime` parameter filters commands by their scheduled/actual execution time:

**Format:** ISO 8601 instant or interval

**Examples:**

```
executionTime=2024-02-02T14:00:00Z       # Command executed at specific time
executionTime=2024-01-01/2024-01-31      # Commands executed in January
executionTime=now/..                     # Commands scheduled for future
executionTime=../now                     # Commands already executed
```

**Applies to:**

- **ControlStreams:** Filter by execution time extent
- **Commands:** Filter by when command should be/was executed

**Semantics:**

- **Scheduled:** When command should execute (future time)
- **Actual:** When command was executed (past time)
- Can be used for both scheduling and historical queries

**TypeScript signature:**

```typescript
executionTime?: string  // ISO 8601 instant or interval
```

**URL encoding:**

```typescript
if (options.executionTime) {
  url.searchParams.set('executionTime', options.executionTime);
}
```

**OpenAPI spec:** Part 2 spec does NOT explicitly document `executionTime` as query parameter, but `executionTime` is a property of commands, so filtering by it is **implied**. Implementations SHOULD support it.

45. **issueTime Parameter:** How to encode when command was issued? ISO 8601 intervals?

**Answer:** The `issueTime` parameter filters commands by when they were issued/submitted:

**Format:** ISO 8601 instant or interval

**Examples:**

```
issueTime=2024-02-02T13:00:00Z           # Command issued at specific time
issueTime=2024-01-01/2024-01-31          # Commands issued in January
issueTime=../now                         # All commands issued up to now
issueTime=2024-02-01/..                  # Commands issued from Feb 1 onwards
```

**Applies to:**

- **Commands:** Filter by when command was submitted to system

**Issue time vs Execution time:**

- `issueTime`: When command was submitted by client
- `executionTime`: When command should be/was executed by system
- Usually `executionTime >= issueTime` (scheduled for future or immediate)

**Use cases:**

- Find commands submitted in specific timeframe
- Query command history by submission time
- Audit trail of command issuance

**TypeScript signature:**

```typescript
issueTime?: string  // ISO 8601 instant or interval
```

**URL encoding:**

```typescript
if (options.issueTime) {
  url.searchParams.set('issueTime', options.issueTime);
}
```

**OpenAPI spec:** Part 2 spec does NOT explicitly document `issueTime` as query parameter, but `issueTime` is a property of commands, so filtering by it is **implied**. Implementations SHOULD support it.

46. **Temporal Interval Syntax:** What is the complete ISO 8601 interval syntax? Single instant, closed interval, open start, open end, multiple disjoint intervals?

**Answer:** Complete ISO 8601 temporal syntax for CSAPI query parameters:

**1. Single instant (exact time):**

```
2024-02-02T12:00:00Z                     # With time zone (UTC)
2024-02-02T12:00:00-05:00                # With time zone offset
2024-02-02                                # Date only (shorthand for whole day)
```

**2. Closed interval (start and end):**

```
2024-01-01T00:00:00Z/2024-01-31T23:59:59Z   # Full timestamp interval
2024-01-01/2024-01-31                        # Date interval (shorthand)
2024-01-15T10:00:00Z/PT1H                    # Start + duration (1 hour)
PT1H/2024-01-15T11:00:00Z                    # Duration + end
```

**3. Open start (everything before end):**

```
../2024-01-31                            # Everything up to Jan 31
../2024-01-31T23:59:59Z                  # Everything up to end of Jan 31
../now                                   # Everything up to current time
```

**4. Open end (everything after start):**

```
2024-01-01/..                            # Everything from Jan 1 onwards
2024-01-01T00:00:00Z/..                  # Everything from start of Jan 1
now/..                                   # Everything from now onwards (future)
```

**5. Special keywords:**

```
now                                      # Current time (can be used as instant or in interval)
latest                                   # Most recent resource only
```

**6. Duration format (ISO 8601 duration):**

```
PT1H                                     # 1 hour
PT30M                                    # 30 minutes
PT1H30M                                  # 1 hour 30 minutes
P1D                                      # 1 day
P1M                                      # 1 month
P1Y                                      # 1 year
P1DT12H                                  # 1 day 12 hours
```

**NOT supported (non-standard):**

- Multiple disjoint intervals: `2024-01-01/2024-01-15,2024-02-01/2024-02-15` ❌
- For multiple intervals, use separate queries and merge results client-side

**TypeScript types:**

```typescript
type ISO8601Instant = string; // "2024-02-02T12:00:00Z"
type ISO8601Interval = string; // "2024-01-01/2024-01-31"
type TemporalQuery = ISO8601Instant | ISO8601Interval | 'now' | 'latest';
```

**Parsing pattern:**

- Single date/time: Instant
- Contains `/`: Interval
- Contains `..`: Open interval
- `now` or `latest`: Special keyword

47. **Offset-Based Pagination:** How to implement Part 1 style pagination? `limit` + `offset` parameters? How to calculate next page offset?

**Answer:** Part 1 offset-based pagination using `limit` and `offset` parameters:

**Parameters:**

- `limit`: Number of items per page (default 10, max 10,000)
- `offset`: Zero-based starting index (default 0)

**Page calculation:**

```typescript
// Page 1 (first 10 items)
GET /systems?limit=10&offset=0

// Page 2 (next 10 items)
GET /systems?limit=10&offset=10

// Page 3
GET /systems?limit=10&offset=20

// Calculate next page offset
const nextOffset = currentOffset + limit;
```

**Implementation pattern:**

```typescript
async function getSystems(options: {
  limit?: number;
  offset?: number;
  // ... other filters
}): Promise<{ items: System[]; hasMore: boolean }> {
  const limit = options.limit ?? 10;
  const offset = options.offset ?? 0;

  const url = new URL(baseUrl);
  url.searchParams.set('limit', limit.toString());
  url.searchParams.set('offset', offset.toString());

  const response = await fetch(url.toString());
  const data = await response.json();

  return {
    items: data.features || data.items,
    hasMore: data.features?.length === limit, // More items if full page returned
  };
}
```

**Pagination logic:**

```typescript
// Fetch all pages
async function getAllSystems(): Promise<System[]> {
  const allSystems: System[] = [];
  let offset = 0;
  const limit = 100;
  let hasMore = true;

  while (hasMore) {
    const { items, hasMore: more } = await getSystems({ limit, offset });
    allSystems.push(...items);
    hasMore = more;
    offset += limit;
  }

  return allSystems;
}
```

**Advantages:**

- Simple to implement
- Easy to jump to specific page
- Predictable page sizes

**Disadvantages:**

- Performance degrades with large offsets (database skips many rows)
- Inconsistent results if data changes between requests (items added/deleted)
- Not ideal for real-time streaming data

**Part 1 resources using offset pagination:**

- Systems
- Deployments
- Procedures
- Sampling Features
- Properties

48. **Cursor-Based Pagination:** How to implement Part 2 style pagination? `limit` + `cursor` parameters? How to extract cursor from responses?

**Answer:** Part 2 MAY use cursor-based pagination for streaming data (observations, commands):

**Parameters:**

- `limit`: Number of items per page (default 10, max 10,000)
- `cursor`: Opaque pagination token (from previous response)

**Pattern:**

```typescript
// First request (no cursor)
GET /observations?limit=100

// Subsequent requests (with cursor from previous response)
GET /observations?limit=100&cursor=eyJpZCI6MTIzLCJ0aW1lIjoiMjAyNC0wMS0zMVQyMzo1OTo1OVoifQ==
```

**Response structure (with pagination metadata):**

```json
{
  "items": [
    /* observations */
  ],
  "links": [
    {
      "rel": "next",
      "href": "https://api.example.com/observations?limit=100&cursor=xyz123"
    },
    {
      "rel": "prev",
      "href": "https://api.example.com/observations?limit=100&cursor=abc456"
    }
  ]
}
```

**Implementation:**

```typescript
async function getObservations(options: {
  limit?: number;
  cursor?: string;
  // ... other filters
}): Promise<{
  items: Observation[];
  nextCursor?: string;
  hasMore: boolean;
}> {
  const limit = options.limit ?? 10;
  const url = new URL(baseUrl);
  url.searchParams.set('limit', limit.toString());

  if (options.cursor) {
    url.searchParams.set('cursor', options.cursor);
  }

  const response = await fetch(url.toString());
  const data = await response.json();

  // Extract next cursor from Link header or response body
  const nextLink = data.links?.find((l: any) => l.rel === 'next');
  const nextCursor = nextLink
    ? new URL(nextLink.href).searchParams.get('cursor')
    : undefined;

  return {
    items: data.items,
    nextCursor: nextCursor ?? undefined,
    hasMore: !!nextCursor,
  };
}
```

**Advantages:**

- Efficient for large datasets (no skipping rows)
- Consistent results even if data changes
- Ideal for streaming/real-time data
- No performance degradation

**Disadvantages:**

- Cannot jump to arbitrary page
- Must traverse sequentially
- Cursors are opaque (server-specific encoding)

**Note:** CSAPI Part 2 spec does NOT explicitly require cursor-based pagination. It's an **implementation choice** - servers MAY use offset or cursor pagination for Part 2 resources.

**Fallback:** If server doesn't provide cursor, use offset pagination for Part 2 resources.

49. **Pagination Limits:** What are the limit constraints? Min 1, max 10,000 for Part 2? Different for Part 1?

**Answer:** Pagination limits are **consistent across Part 1 and Part 2**:

**Constraints:**

- **Minimum:** 1 (single item)
- **Maximum:** 10,000 (ten thousand items)
- **Default:** 10 (if not specified)

**OpenAPI spec (both Part 1 and Part 2):**

```yaml
limit:
  name: limit
  schema:
    type: integer
    minimum: 1
    maximum: 10000
    default: 10
```

**Validation:**

```typescript
function validateLimit(limit?: number): number {
  const value = limit ?? 10;

  if (value < 1) {
    throw new Error('limit must be at least 1');
  }

  if (value > 10000) {
    throw new Error('limit cannot exceed 10000');
  }

  return value;
}
```

**Server behavior:**

- `limit` < 1: Server returns HTTP 400 Bad Request
- `limit` > 10,000: Server returns HTTP 400 Bad Request
- No `limit` specified: Server uses default (10)
- Server MAY return fewer items than limit (if insufficient matches)

**Practical recommendations:**

- **Interactive UIs:** Use limit=10-50 for responsive pagination
- **Batch processing:** Use limit=1000-10000 for efficient bulk retrieval
- **Streaming data:** Use smaller limits (100-500) with cursor pagination
- **Export/download:** Multiple requests with limit=10000 to minimize round trips

**Part 1 vs Part 2 - No difference:**

- Part 1 (Systems, Deployments, etc.): min 1, max 10,000, default 10
- Part 2 (DataStreams, Observations, etc.): min 1, max 10,000, default 10

50. **Link Headers:** Should QueryBuilder parse Link headers for next/prev pages? Or leave to handlers?

**Answer:** QueryBuilder should **parse links from response body**, NOT Link headers:

**CSAPI response structure (JSON body):**

```json
{
  "items": [
    /* resources */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.com/systems?limit=10&offset=0",
      "type": "application/json"
    },
    {
      "rel": "next",
      "href": "https://api.example.com/systems?limit=10&offset=10",
      "type": "application/json"
    },
    {
      "rel": "prev",
      "href": "https://api.example.com/systems?limit=10&offset=0",
      "type": "application/json"
    }
  ]
}
```

**Recommended approach:**

```typescript
interface PaginatedResponse<T> {
  items: T[];
  links?: Array<{
    rel: string;
    href: string;
    type?: string;
  }>;
}

async function getSystems(
  options?: QueryOptions
): Promise<PaginatedResponse<System>> {
  const url = buildSystemsUrl(options);
  const response = await fetch(url);
  const data = await response.json();

  return {
    items: data.features || data.items,
    links: data.links, // Return links from response body
  };
}

// Helper to extract next page URL
function getNextPageUrl(response: PaginatedResponse<any>): string | undefined {
  return response.links?.find((l) => l.rel === 'next')?.href;
}

// Helper to fetch next page
async function getNextPage<T>(
  response: PaginatedResponse<T>
): Promise<PaginatedResponse<T> | undefined> {
  const nextUrl = getNextPageUrl(response);
  if (!nextUrl) return undefined;

  const nextResponse = await fetch(nextUrl);
  return await nextResponse.json();
}
```

**Why body links over HTTP Link headers:**

1. **OGC API standard:** Specifies links in JSON response body
2. **Typed:** Links in body are part of JSON schema (type-safe)
3. **Consistent:** All OGC APIs use body links
4. **Metadata:** Body links include `type`, `title`, `uid` (not in HTTP headers)
5. **Cross-origin:** Body links work with CORS (headers may be filtered)

**HTTP Link headers (if present):**
Some servers MAY include HTTP Link headers for backwards compatibility:

```
Link: <https://api.example.com/systems?limit=10&offset=10>; rel="next"
Link: <https://api.example.com/systems?limit=10&offset=0>; rel="prev"
```

**Recommendation:**

- **Primary:** Parse links from response body
- **Fallback:** Parse Link headers if body links not present
- **Return:** Expose links to caller (don't hide pagination logic)
- **Helpers:** Provide utility methods for common pagination patterns

### I. Systems Resource Methods

**Questions:**

51. **Systems Endpoints:** What are ALL Systems endpoints? List all, get by ID, query, subsystems, by deployment, by procedure, in collection?

**Answer:** Complete list of Systems endpoints from OpenAPI Part 1 spec:

**Canonical endpoints:**

- `GET /systems` - List/query all top-level systems
- `POST /systems` - Create new top-level system
- `GET /systems/{systemId}` - Get specific system by ID
- `PUT /systems/{systemId}` - Replace system (complete update)
- `DELETE /systems/{systemId}` - Delete system (with optional cascade)

**Hierarchical endpoints:**

- `GET /systems/{systemId}/subsystems` - List subsystems of specific system
- `POST /systems/{systemId}/subsystems` - Add subsystem to specific system

**Association endpoints:**

- `GET /systems/{systemId}/deployments` - List deployments of specific system (association navigation)
- `GET /systems/{systemId}/samplingFeatures` - List sampling features of specific system
- `GET /systems/{systemId}/datastreams` - List datastreams of specific system (Part 2)
- `GET /systems/{systemId}/controlstreams` - List control streams of specific system (Part 2)

**Query by relationship (canonical endpoint with filters):**

- `GET /systems?deployment={id}` - Systems in specific deployment
- `GET /systems?procedure={id}` - Systems implementing specific procedure
- `GET /systems?foi={id}` - Systems observing specific feature
- `GET /systems?parent={id}` - Subsystems of specific parent (alternative to nested)

**History (if supported by server):**

- `GET /systems/{systemId}/history` - Historical versions of system description

**Total: 13+ distinct endpoint patterns for Systems**

52. **Systems Query Parameters:** What query parameters apply to Systems? bbox, datetime, recursive, parent, deployment, procedure, foi, id, uid, q, properties, limit, offset, f?

**Answer:** Query parameters for Systems endpoints from OpenAPI Part 1 spec:

**Spatial filters:**

- `bbox` - Bounding box (comma-separated: minLon,minLat,maxLon,maxLat)
- `geom` - WKT geometry for spatial intersection

**Temporal filters:**

- `datetime` - ISO 8601 instant/interval for validity period

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Text search:**

- `q` - Comma-separated keywords for full-text search

**Relationship filters:**

- `parent` - Filter by parent system ID (for hierarchical queries)
- `deployment` - Filter by deployment ID
- `procedure` - Filter by procedure ID
- `foi` - Filter by feature of interest ID
- `observedProperty` - Filter by observed property
- `controlledProperty` - Filter by controlled property

**Hierarchical control:**

- `recursive` - Boolean flag (true = include all descendants)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (default 0)

**Format negotiation:**

- `f` - Response format (json, geojson, sml+json, html)

**Complete TypeScript interface:**

```typescript
interface SystemQueryOptions {
  // Spatial
  bbox?: [number, number, number, number];
  geom?: string; // WKT geometry

  // Temporal
  datetime?: string; // ISO 8601

  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Relationships
  parent?: string[];
  deployment?: string[];
  procedure?: string[];
  foi?: string[];
  observedProperty?: string[];
  controlledProperty?: string[];

  // Hierarchical
  recursive?: boolean;

  // Pagination
  limit?: number;
  offset?: number;

  // Format
  f?: 'json' | 'geojson' | 'sml+json' | 'html';
}
```

**Note:** Not all parameters apply to all endpoints (e.g., `parent` doesn't make sense for `/systems/{id}/subsystems`).

53. **Subsystems Hierarchy:** How to query subsystems? Recursive flag? `/systems/{id}/subsystems?recursive=true`?

**Answer:** Subsystems can be queried via nested endpoint with recursive flag:

**Nested endpoint (preferred):**

```
GET /systems/{systemId}/subsystems
GET /systems/{systemId}/subsystems?recursive=true
GET /systems/{systemId}/subsystems?recursive=false
```

**Canonical endpoint with parent filter (alternative):**

```
GET /systems?parent={systemId}
GET /systems?parent={systemId}&recursive=true
```

**Recursive behavior:**

**Non-recursive (recursive=false or omitted):**

```
System A
  ├─ Subsystem B
  │   └─ Subsystem D
  └─ Subsystem C

GET /systems/A/subsystems
Returns: [B, C]  (direct children only)
```

**Recursive (recursive=true):**

```
System A
  ├─ Subsystem B
  │   └─ Subsystem D
  └─ Subsystem C

GET /systems/A/subsystems?recursive=true
Returns: [B, C, D]  (all descendants)
```

**Method signatures:**

```typescript
// Direct children only
async getSubsystems(
  parentId: string,
  options?: Omit<SystemQueryOptions, 'parent'>
): Promise<System[]>

// With recursive flag
async getSubsystems(
  parentId: string,
  options?: SystemQueryOptions & { recursive?: boolean }
): Promise<System[]>
```

**Implementation:**

```typescript
async getSubsystems(
  parentId: string,
  options?: SystemQueryOptions
): Promise<System[]> {
  const baseUrl = this.getResourceLink('systems');
  const url = new URL(`${baseUrl}/${parentId}/subsystems`);

  // Add recursive parameter
  if (options?.recursive !== undefined) {
    url.searchParams.set('recursive', options.recursive.toString());
  }

  // Add other query parameters
  this.addStandardQueryParams(url, options);

  return this.fetchResource<System[]>(url.toString());
}
```

**Use cases:**

- **Non-recursive:** UI tree view with lazy loading (load one level at a time)
- **Recursive:** Export/analysis needing complete system hierarchy
- **Performance:** Recursive queries can return large datasets - use `limit` to control size

54. **Systems CRUD:** What CRUD operations for Systems? POST `/systems`, PUT/PATCH `/systems/{id}`, DELETE `/systems/{id}?cascade=true`?

**Answer:** Complete CRUD operations for Systems from OpenAPI Part 1 spec:

**CREATE (POST):**

```
POST /systems
Content-Type: application/geo+json | application/sml+json
Body: System resource (without ID - server assigns)

Response: 201 Created
Location: https://api.example.com/systems/{new-id}
```

**CREATE subsystem (POST to nested):**

```
POST /systems/{parentId}/subsystems
Content-Type: application/geo+json | application/sml+json
Body: Subsystem resource

Response: 201 Created
Location: https://api.example.com/systems/{new-subsystem-id}
```

**READ (GET):**

```
GET /systems/{systemId}
Accept: application/geo+json | application/sml+json

Response: 200 OK
Body: System resource
```

**UPDATE - Replace (PUT):**

```
PUT /systems/{systemId}
Content-Type: application/geo+json | application/sml+json
Body: Complete system resource

Response: 204 No Content (or 200 OK with body)
```

**UPDATE - Partial (PATCH):**

```
PATCH /systems/{systemId}
Content-Type: application/merge-patch+json
Body: Partial system properties to update

Response: 204 No Content (or 200 OK with body)
```

**Note:** OpenAPI spec defines PUT but NOT PATCH. PATCH support is **implementation-dependent**.

**DELETE:**

```
DELETE /systems/{systemId}

Response: 204 No Content (success)
         409 Conflict (has dependents, cascade required)
```

**DELETE with cascade:**

```
DELETE /systems/{systemId}?cascade=true

Response: 204 No Content
Deletes: System + subsystems + datastreams + observations + controlstreams + commands
```

**Method signatures:**

```typescript
// Create
async createSystem(body: SystemInput): Promise<System>
async createSubsystem(parentId: string, body: SystemInput): Promise<System>

// Read
async getSystem(systemId: string, options?: { datetime?: string, f?: Format }): Promise<System>

// Update
async updateSystem(systemId: string, body: SystemInput): Promise<System>
async patchSystem(systemId: string, updates: Partial<SystemInput>): Promise<System>

// Delete
async deleteSystem(systemId: string, options?: { cascade?: boolean }): Promise<void>
```

**Response codes:**

- 200 OK - Successful GET/PUT/PATCH with body
- 201 Created - Successful POST (with Location header)
- 204 No Content - Successful DELETE or PUT/PATCH without body
- 400 Bad Request - Validation error
- 404 Not Found - System doesn't exist
- 409 Conflict - Cannot delete (has dependents)
- 422 Unprocessable Entity - Semantic validation error

### J. Deployments Resource Methods

**Questions:**

55. **Deployments Endpoints:** What are ALL Deployments endpoints? List all, get by ID, query, subdeployments, by system, in collection?

**Answer:** Complete list of Deployments endpoints from OpenAPI Part 1 spec:

**Canonical endpoints:**

- `GET /deployments` - List/query all top-level deployments
- `POST /deployments` - Create new top-level deployment
- `GET /deployments/{deploymentId}` - Get specific deployment by ID
- `PUT /deployments/{deploymentId}` - Replace deployment (complete update)
- `DELETE /deployments/{deploymentId}` - Delete deployment

**Hierarchical endpoints:**

- `GET /deployments/{deploymentId}/subdeployments` - List subdeployments of specific deployment
- `POST /deployments/{deploymentId}/subdeployments` - Add subdeployment to specific deployment

**Association endpoints (reverse navigation):**

- `GET /systems/{systemId}/deployments` - List deployments of specific system

**Query by relationship (canonical endpoint with filters):**

- `GET /deployments?system={id}` - Deployments containing specific system
- `GET /deployments?foi={id}` - Deployments at specific feature of interest
- `GET /deployments?parent={id}` - Subdeployments of specific parent

**History (if supported):**

- `GET /deployments/{deploymentId}/history` - Historical versions

**Total: 10+ distinct endpoint patterns for Deployments**

56. **Deployments Query Parameters:** What query parameters apply to Deployments? bbox, datetime, system, recursive, parent, id, uid, q, properties, limit, offset, f?

**Answer:** Query parameters for Deployments endpoints from OpenAPI Part 1 spec:

**Spatial filters:**

- `bbox` - Bounding box for deployment location
- `geom` - WKT geometry for spatial intersection

**Temporal filters:**

- `datetime` - ISO 8601 instant/interval for deployment validity period

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Text search:**

- `q` - Comma-separated keywords for full-text search

**Relationship filters:**

- `parent` - Filter by parent deployment ID (for hierarchical queries)
- `system` - Filter by deployed system ID
- `foi` - Filter by feature of interest ID
- `observedProperty` - Filter by observed property (systems in deployment)
- `controlledProperty` - Filter by controlled property (systems in deployment)

**Hierarchical control:**

- `recursive` - Boolean flag (true = include all subdeployments recursively)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (default 0)

**Format negotiation:**

- `f` - Response format (json, geojson, html)

**TypeScript interface:**

```typescript
interface DeploymentQueryOptions {
  // Spatial
  bbox?: [number, number, number, number];
  geom?: string;

  // Temporal
  datetime?: string;

  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Relationships
  parent?: string[];
  system?: string[];
  foi?: string[];
  observedProperty?: string[];
  controlledProperty?: string[];

  // Hierarchical
  recursive?: boolean;

  // Pagination
  limit?: number;
  offset?: number;

  // Format
  f?: 'json' | 'geojson' | 'html';
}
```

57. **Subdeployments Hierarchy:** How to query subdeployments? Recursive flag? `/deployments/{id}/subdeployments?recursive=true`?

**Answer:** Subdeployments can be queried via nested endpoint with recursive flag:

**Nested endpoint (preferred):**

```
GET /deployments/{deploymentId}/subdeployments
GET /deployments/{deploymentId}/subdeployments?recursive=true
```

**Canonical endpoint with parent filter (alternative):**

```
GET /deployments?parent={deploymentId}
GET /deployments?parent={deploymentId}&recursive=true
```

**Recursive behavior (same as Systems):**

```
Deployment A
  ├─ Subdeployment B
  │   └─ Subdeployment D
  └─ Subdeployment C

GET /deployments/A/subdeployments
Returns: [B, C]  (direct children only)

GET /deployments/A/subdeployments?recursive=true
Returns: [B, C, D]  (all descendants)
```

**Method signature:**

```typescript
async getSubdeployments(
  parentId: string,
  options?: DeploymentQueryOptions
): Promise<Deployment[]> {
  const baseUrl = this.getResourceLink('deployments');
  const url = new URL(`${baseUrl}/${parentId}/subdeployments`);

  if (options?.recursive !== undefined) {
    url.searchParams.set('recursive', options.recursive.toString());
  }

  this.addStandardQueryParams(url, options);
  return this.fetchResource<Deployment[]>(url.toString());
}
```

**Use cases:**

- **Mission planning:** Nested deployments for complex missions (e.g., Arctic mission with multiple platform deployments)
- **Hierarchical campaigns:** Multi-level deployment structures (campaign → mission → platform)

58. **Deployments CRUD:** What CRUD operations for Deployments? POST, PUT/PATCH, DELETE with cascade?

**Answer:** Complete CRUD operations for Deployments from OpenAPI Part 1 spec:

**CREATE (POST):**

```
POST /deployments
Content-Type: application/geo+json
Body: Deployment resource (without ID)

Response: 201 Created
Location: https://api.example.com/deployments/{new-id}
```

**CREATE subdeployment:**

```
POST /deployments/{parentId}/subdeployments
Content-Type: application/geo+json
Body: Subdeployment resource

Response: 201 Created
```

**READ (GET):**

```
GET /deployments/{deploymentId}
Accept: application/geo+json

Response: 200 OK
Body: Deployment resource
```

**UPDATE - Replace (PUT):**

```
PUT /deployments/{deploymentId}
Content-Type: application/geo+json
Body: Complete deployment resource

Response: 204 No Content
```

**DELETE:**

```
DELETE /deployments/{deploymentId}

Response: 204 No Content (success)
         409 Conflict (has subdeployments or other dependents)
```

**Method signatures:**

```typescript
// Create
async createDeployment(body: DeploymentInput): Promise<Deployment>
async createSubdeployment(parentId: string, body: DeploymentInput): Promise<Deployment>

// Read
async getDeployment(deploymentId: string, options?: { f?: Format }): Promise<Deployment>

// Update
async updateDeployment(deploymentId: string, body: DeploymentInput): Promise<Deployment>

// Delete
async deleteDeployment(deploymentId: string): Promise<void>
```

**Note:** OpenAPI spec does NOT define `cascade` parameter for Deployments DELETE. Deletion fails (409 Conflict) if deployment has subdeployments or other dependencies.

### K. Procedures Resource Methods

**Questions:**

59. **Procedures Endpoints:** What are ALL Procedures endpoints? List all, get by ID, query, by system, in collection?

**Answer:** Complete list of Procedures endpoints from OpenAPI Part 1 spec:

**Canonical endpoints:**

- `GET /procedures` - List/query all procedures
- `POST /procedures` - Create new procedure
- `GET /procedures/{procedureId}` - Get specific procedure by ID
- `PUT /procedures/{procedureId}` - Replace procedure (complete update)
- `DELETE /procedures/{procedureId}` - Delete procedure

**Query by relationship (canonical endpoint with filters):**

- `GET /procedures?system={id}` - Procedures implemented by specific system

**No nested endpoints:** Procedures don't have hierarchical structure (no subprocedures)

**No association endpoints:** No reverse navigation from systems to procedures (use canonical with filter)

**History (if supported):**

- `GET /procedures/{procedureId}/history` - Historical versions of procedure

**Total: 6 distinct endpoint patterns for Procedures**

**Note:** Procedures are often **shared resources** (multiple systems implement same procedure), so they're typically managed separately from systems.

60. **Procedures Query Parameters:** What query parameters apply to Procedures? system, id, uid, q, properties, limit, offset, f?

**Answer:** Query parameters for Procedures endpoints from OpenAPI Part 1 spec:

**NO spatial/temporal filters:** Procedures are abstract methods (not spatially/temporally bound)

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Text search:**

- `q` - Comma-separated keywords for full-text search

**Relationship filters:**

- `system` - Filter by system ID (procedures implemented by system)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (default 0)

**Format negotiation:**

- `f` - Response format (json, geojson, sml+json, html)

**TypeScript interface:**

```typescript
interface ProcedureQueryOptions {
  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Relationships
  system?: string[];

  // Pagination
  limit?: number;
  offset?: number;

  // Format
  f?: 'json' | 'geojson' | 'sml+json' | 'html';
}
```

**Simplified compared to Systems/Deployments:** No bbox, datetime, parent, recursive (procedures are simple resources)

61. **Procedures CRUD:** What CRUD operations for Procedures? POST, PUT/PATCH, DELETE?

**Answer:** Complete CRUD operations for Procedures from OpenAPI Part 1 spec:

**CREATE (POST):**

```
POST /procedures
Content-Type: application/sml+json | application/geo+json
Body: Procedure resource (without ID)

Response: 201 Created
Location: https://api.example.com/procedures/{new-id}
```

**READ (GET):**

```
GET /procedures/{procedureId}
Accept: application/sml+json | application/geo+json

Response: 200 OK
Body: Procedure resource (detailed SensorML description)
```

**UPDATE - Replace (PUT):**

```
PUT /procedures/{procedureId}
Content-Type: application/sml+json
Body: Complete procedure resource

Response: 204 No Content
```

**DELETE:**

```
DELETE /procedures/{procedureId}

Response: 204 No Content (success)
         409 Conflict (procedure in use by systems/datastreams)
```

**Method signatures:**

```typescript
// Create
async createProcedure(body: ProcedureInput): Promise<Procedure>

// Read
async getProcedure(procedureId: string, options?: { f?: Format }): Promise<Procedure>

// Update
async updateProcedure(procedureId: string, body: ProcedureInput): Promise<Procedure>

// Delete
async deleteProcedure(procedureId: string): Promise<void>
```

**Important:** Procedures are often **referenced** by multiple systems. Deleting a procedure may fail (409 Conflict) if systems/datastreams reference it. No cascade delete for procedures.

62. **SensorML Format:** How to handle SensorML format for Procedures? `f=sml+json` parameter?

**Answer:** Procedures support SensorML 3.0 JSON format for detailed method descriptions:

**Format negotiation via query parameter:**

```
GET /procedures/{id}?f=sml+json
GET /procedures/{id}?f=geojson
GET /procedures/{id}?f=json
```

**Format negotiation via Accept header:**

```
GET /procedures/{id}
Accept: application/sml+json

GET /procedures/{id}
Accept: application/geo+json
```

**SensorML format characteristics:**

- **Detailed:** Complete procedure specification (inputs, outputs, parameters, algorithms)
- **Semantic:** Rich metadata with definitions and ontology links
- **Structured:** Hierarchical process description
- **Standard:** SensorML 3.0 JSON encoding

**GeoJSON format characteristics:**

- **Simple:** Basic procedure information (name, description, links)
- **Lightweight:** Minimal metadata
- **Spatial:** Can include geometry if procedure is location-specific

**Method signature:**

```typescript
async getProcedure(
  procedureId: string,
  options?: { f?: 'sml+json' | 'geojson' | 'json' }
): Promise<Procedure>
```

**Implementation:**

```typescript
async getProcedure(
  procedureId: string,
  options?: { f?: Format }
): Promise<Procedure> {
  const baseUrl = this.getResourceLink('procedures');
  const url = new URL(`${baseUrl}/${procedureId}`);

  // Add format parameter
  if (options?.f) {
    url.searchParams.set('f', options.f);
  }

  // Alternatively, use Accept header
  const headers: Record<string, string> = {};
  if (options?.f === 'sml+json') {
    headers['Accept'] = 'application/sml+json';
  } else if (options?.f === 'geojson') {
    headers['Accept'] = 'application/geo+json';
  }

  const response = await fetch(url.toString(), { headers });
  return await response.json();
}
```

**Use cases:**

- **SensorML:** Detailed procedure documentation, calibration specs, algorithm descriptions
- **GeoJSON:** Quick procedure lookup, UI display, simple queries

**Default:** Server returns GeoJSON by default if no format specified

### L. Sampling Features Resource Methods

**Questions:**

63. **Sampling Features Endpoints:** What are ALL Sampling Features endpoints? List all, get by ID, query, by system, by foi, in collection?

**Answer:** Complete list of Sampling Features endpoints from OpenAPI Part 1 spec:

**Canonical endpoints:**

- `GET /samplingFeatures` - List/query all sampling features
- `POST /samplingFeatures` - Create new sampling feature
- `GET /samplingFeatures/{featureId}` - Get specific sampling feature by ID
- `PUT /samplingFeatures/{featureId}` - Replace sampling feature (complete update)
- `DELETE /samplingFeatures/{featureId}` - Delete sampling feature

**Association endpoints (reverse navigation):**

- `GET /systems/{systemId}/samplingFeatures` - List sampling features of specific system

**Query by relationship (canonical endpoint with filters):**

- `GET /samplingFeatures?system={id}` - Sampling features used by specific system
- `GET /samplingFeatures?foi={id}` - Sampling features related to specific feature of interest

**No hierarchical structure:** Sampling features don't have parent-child relationships (flat structure)

**History (if supported):**

- `GET /samplingFeatures/{featureId}/history` - Historical versions

**Total: 7 distinct endpoint patterns for Sampling Features**

64. **Sampling Features Query Parameters:** What query parameters apply to Sampling Features? bbox, system, foi, relatedSamplingFeature, id, uid, q, properties, limit, offset, f?

**Answer:** Query parameters for Sampling Features endpoints from OpenAPI Part 1 spec:

**Spatial filters:**

- `bbox` - Bounding box (sampling features have locations)
- `geom` - WKT geometry for spatial intersection

**NO temporal filter:** Sampling features don't have temporal extent (use system/deployment datetime instead)

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Text search:**

- `q` - Comma-separated keywords for full-text search

**Relationship filters:**

- `system` - Filter by system ID (sampling features used by system)
- `foi` - Filter by ultimate feature of interest ID

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (default 0)

**Format negotiation:**

- `f` - Response format (json, geojson, html)

**TypeScript interface:**

```typescript
interface SamplingFeatureQueryOptions {
  // Spatial
  bbox?: [number, number, number, number];
  geom?: string;

  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Relationships
  system?: string[];
  foi?: string[];

  // Pagination
  limit?: number;
  offset?: number;

  // Format
  f?: 'json' | 'geojson' | 'html';
}
```

**Note:** OpenAPI spec does NOT define `relatedSamplingFeature` parameter. Sampling feature relationships are typically expressed via `foi` parameter or geometry relationships.

65. **Sampling Features CRUD:** What CRUD operations for Sampling Features? POST, PUT/PATCH, DELETE?

**Answer:** Complete CRUD operations for Sampling Features from OpenAPI Part 1 spec:

**CREATE (POST):**

```
POST /samplingFeatures
Content-Type: application/geo+json
Body: Sampling feature resource (without ID)

Response: 201 Created
Location: https://api.example.com/samplingFeatures/{new-id}
```

**READ (GET):**

```
GET /samplingFeatures/{featureId}
Accept: application/geo+json

Response: 200 OK
Body: Sampling feature resource (GeoJSON Feature)
```

**UPDATE - Replace (PUT):**

```
PUT /samplingFeatures/{featureId}
Content-Type: application/geo+json
Body: Complete sampling feature resource

Response: 204 No Content
```

**DELETE:**

```
DELETE /samplingFeatures/{featureId}

Response: 204 No Content (success)
         409 Conflict (feature referenced by observations/datastreams)
```

**Method signatures:**

```typescript
// Create
async createSamplingFeature(body: SamplingFeatureInput): Promise<SamplingFeature>

// Read
async getSamplingFeature(featureId: string, options?: { f?: Format }): Promise<SamplingFeature>

// Update
async updateSamplingFeature(featureId: string, body: SamplingFeatureInput): Promise<SamplingFeature>

// Delete
async deleteSamplingFeature(featureId: string): Promise<void>
```

**Important:** Sampling features are often **shared resources** (multiple observations/datastreams reference same sampling feature). Deleting may fail (409 Conflict) if referenced. No cascade delete.

### M. Properties Resource Methods

**Questions:**

66. **Properties Endpoints:** What are ALL Properties endpoints? List all, get by ID, query, by system, by base property, in collection?

**Answer:** Complete list of Properties endpoints from OpenAPI Part 1 spec:

**Canonical endpoints (READ-ONLY):**

- `GET /properties` - List/query all properties
- `GET /properties/{propId}` - Get specific property by ID

**Query by relationship (canonical endpoint with filters):**

- `GET /properties?system={id}` - Properties observed/controlled by specific system
- `GET /properties?baseProperty={id}` - Properties derived from specific base property (hierarchy)
- `GET /properties?objectType={uri}` - Properties of specific object type

**NO CREATE/UPDATE/DELETE:** Properties are **read-only** (managed by server, not user-editable)

**NO nested endpoints:** Properties are flat resources (no sub-properties via nested paths)

**NO association endpoints:** No reverse navigation from systems to properties

**Total: 4 endpoint patterns for Properties (all read-only)**

**Rationale:** Properties define the vocabulary of observable/controllable phenomena. They're typically managed centrally (not created by individual users).

67. **Properties Query Parameters:** What query parameters apply to Properties? system, baseProperty, id, uid, q, properties, limit, offset, f?

**Answer:** Query parameters for Properties endpoints from OpenAPI Part 1 spec:

**NO spatial/temporal filters:** Properties are abstract concepts (not spatially/temporally bound)

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Text search:**

- `q` - Comma-separated keywords for full-text search

**Relationship filters:**

- `system` - Filter by system ID (properties measured/controlled by system)
- `baseProperty` - Filter by base property ID (for hierarchy queries)
- `objectType` - Filter by object type URI (semantic classification)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (default 0)

**Format negotiation:**

- `f` - Response format (json, html)

**TypeScript interface:**

```typescript
interface PropertyQueryOptions {
  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Relationships
  system?: string[];
  baseProperty?: string[];
  objectType?: string[]; // URIs

  // Pagination
  limit?: number;
  offset?: number;

  // Format
  f?: 'json' | 'html';
}
```

**Note:** Properties don't use GeoJSON format (no spatial component).

68. **Properties Read-Only:** Are Properties read-only (GET only)? No CRUD operations?

**Answer:** Yes, Properties are **READ-ONLY** resources:

**Supported operations:**

```
GET /properties               ✓ List all properties
GET /properties/{propId}      ✓ Get specific property
```

**NOT supported:**

```
POST /properties              ✗ Cannot create properties
PUT /properties/{propId}      ✗ Cannot update properties
DELETE /properties/{propId}   ✗ Cannot delete properties
```

**Method signatures:**

```typescript
// Only read operations
async getProperties(options?: PropertyQueryOptions): Promise<Property[]>
async getProperty(propId: string, options?: { f?: Format }): Promise<Property>

// No create/update/delete methods
```

**Rationale:**

1. **Vocabulary management:** Properties define standard terminology (centrally managed)
2. **Semantic consistency:** Prevents users from creating conflicting property definitions
3. **Interoperability:** Ensures consistent property URIs across systems
4. **Ontology-driven:** Properties typically derived from standard ontologies (CF, QUDT, etc.)

**Server management:** Properties are typically:

- Pre-populated from standard vocabularies
- Managed by administrators (not regular API users)
- Updated through server configuration (not API calls)

**For custom properties:** Servers MAY provide admin endpoints outside CSAPI spec, but this is implementation-specific.

69. **Property Hierarchy:** How to query property hierarchies? `baseProperty` parameter for parent-child relationships?

**Answer:** Property hierarchies are queried using `baseProperty` parameter:

**Hierarchy example:**

```
temperature (base)
  ├─ air_temperature (derived)
  ├─ water_temperature (derived)
  └─ surface_temperature (derived)

pressure (base)
  ├─ air_pressure (derived)
  └─ water_pressure (derived)
```

**Query derived properties:**

```
GET /properties?baseProperty=temperature
Returns: [air_temperature, water_temperature, surface_temperature]

GET /properties?baseProperty=temperature,pressure
Returns: [air_temperature, water_temperature, surface_temperature, air_pressure, water_pressure]
```

**Query specific property:**

```
GET /properties/air_temperature
Response:
{
  "id": "air_temperature",
  "name": "Air Temperature",
  "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
  "baseProperty@link": {
    "href": "https://api.example.com/properties/temperature",
    "uid": "http://mmisw.org/ont/cf/parameter/temperature"
  },
  "objectType": "http://www.w3.org/ns/ssn/Property"
}
```

**Method signature:**

```typescript
async getProperties(options?: {
  baseProperty?: string[];  // Filter by base property
  // ... other options
}): Promise<Property[]>
```

**Implementation:**

```typescript
async getProperties(options?: PropertyQueryOptions): Promise<Property[]> {
  const url = new URL(this.getResourceLink('properties'));

  // Add baseProperty filter
  if (options?.baseProperty?.length > 0) {
    url.searchParams.set('baseProperty', options.baseProperty.join(','));
  }

  this.addStandardQueryParams(url, options);
  return this.fetchResource<Property[]>(url.toString());
}
```

**Use cases:**

- **Semantic search:** Find all temperature-related properties
- **Property discovery:** Explore property vocabulary
- **UI filtering:** Group properties by category
- **Query expansion:** Query observations for any temperature type

**Note:** Hierarchy is **single-level** (base → derived). No multi-level hierarchies in CSAPI spec.

### N. DataStreams Resource Methods

**Questions:**

70. **DataStreams Endpoints:** What are ALL DataStreams endpoints? List all, get by ID, query, by system, schema endpoint, in collection?

**Answer:** Complete list of DataStreams endpoints from OpenAPI Part 2 spec:

**Canonical endpoints:**

- `GET /datastreams` - List/query all datastreams
- `POST /datastreams` - Create new datastream
- `GET /datastreams/{datastreamId}` - Get specific datastream by ID
- `PUT /datastreams/{datastreamId}` - Replace datastream (complete update)
- `DELETE /datastreams/{datastreamId}` - Delete datastream

**Association endpoints (reverse navigation):**

- `GET /systems/{systemId}/datastreams` - List datastreams of specific system
- `POST /systems/{systemId}/datastreams` - Create datastream for specific system

**Schema endpoint:**

- `GET /datastreams/{datastreamId}/schema` - Get observation schema for datastream
- Format negotiation: `?f=json`, `?f=proto`, `?f=swe+json`

**Observations endpoint (nested):**

- `GET /datastreams/{datastreamId}/observations` - Get observations from datastream (key endpoint!)
- `POST /datastreams/{datastreamId}/observations` - Add observations to datastream (bulk insert)

**No hierarchical structure:** DataStreams are flat (no subdatastreams)

**Total: 9 distinct endpoint patterns for DataStreams**

71. **DataStreams Query Parameters:** What query parameters apply to DataStreams? system, observedProperty, foi, samplingFeature, procedure, datetime, id, uid, q, properties, limit, offset, f?

**Answer:** Query parameters for DataStreams endpoints from OpenAPI Part 2 spec:

**NO spatial filters:** DataStreams don't have spatial extent (use system or feature of interest for spatial queries)

**Temporal filters:**

- `phenomenonTime` - Filter by phenomenon time extent (ISO 8601 instant/interval)
- `resultTime` - Filter by result time extent (ISO 8601 instant/interval)

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Text search:**

- `q` - Comma-separated keywords for full-text search

**Relationship filters:**

- `system` - Filter by system ID (datastreams from specific system)
- `observedProperty` - Filter by observed property ID or URI
- `foi` - Filter by feature of interest ID
- `procedure` - Filter by procedure ID (implied, not formally documented)
- `deployment` - Filter by deployment (implied, not formally documented)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (default 0) OR
- `cursor` - Cursor token for cursor-based pagination (server-dependent)

**Format negotiation:**

- `f` - Response format (json, html)

**TypeScript interface:**

```typescript
interface DataStreamQueryOptions {
  // Temporal
  phenomenonTime?: string;
  resultTime?: string;

  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Relationships
  system?: string[];
  observedProperty?: string[];
  foi?: string[];
  procedure?: string[]; // implied
  deployment?: string[]; // implied

  // Pagination
  limit?: number;
  offset?: number;
  cursor?: string; // for cursor-based pagination

  // Format
  f?: 'json' | 'html';
}
```

**Note:** OpenAPI spec does NOT define `samplingFeature` as query parameter (use `foi` instead).

72. **Schema Endpoint:** How to construct schema endpoint URL? `/datastreams/{id}/schema`? What format?

**Answer:** Schema endpoint provides observation structure for a datastream:

**Endpoint pattern:**

```
GET /datastreams/{datastreamId}/schema
GET /datastreams/{datastreamId}/schema?f=json
GET /datastreams/{datastreamId}/schema?f=proto
GET /datastreams/{datastreamId}/schema?f=swe+json
```

**Format negotiation:**

- `f=json` - JSON Schema format (default)
- `f=proto` - Protocol Buffers schema
- `f=swe+json` - SWE Common JSON schema

**Response structure (JSON Schema format):**

```json
{
  "obsFormat": "application/json",
  "resultSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "temp",
        "type": "Quantity",
        "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
        "label": "Air Temperature",
        "uom": { "code": "Cel" }
      },
      {
        "name": "humidity",
        "type": "Quantity",
        "definition": "http://mmisw.org/ont/cf/parameter/relative_humidity",
        "label": "Relative Humidity",
        "uom": { "code": "%" }
      }
    ]
  }
}
```

**Method signature:**

```typescript
async getDataStreamSchema(
  datastreamId: string,
  options?: { f?: 'json' | 'proto' | 'swe+json' }
): Promise<DataStreamSchema>
```

**Implementation:**

```typescript
async getDataStreamSchema(
  datastreamId: string,
  options?: { f?: string }
): Promise<DataStreamSchema> {
  const baseUrl = this.getResourceLink('datastreams');
  const url = new URL(`${baseUrl}/${datastreamId}/schema`);

  if (options?.f) {
    url.searchParams.set('f', options.f);
  }

  const response = await fetch(url.toString());
  return await response.json();
}
```

**Use cases:**

- **Client validation:** Parse schema before submitting observations
- **UI generation:** Auto-generate forms from schema
- **Data parsing:** Understand observation structure

**Schema format:** SWE Common Data Record schema (fields, types, units, constraints)

73. **DataStreams CRUD:** What CRUD operations for DataStreams? POST, PUT/PATCH, DELETE with cascade?

**Answer:** Complete CRUD operations for DataStreams from OpenAPI Part 2 spec:

**CREATE (POST):**

```
POST /datastreams
Content-Type: application/json
Body: DataStream resource with schema

Response: 201 Created
Location: https://api.example.com/datastreams/{new-id}
```

**CREATE for specific system:**

```
POST /systems/{systemId}/datastreams
Content-Type: application/json
Body: DataStream resource

Response: 201 Created
```

**READ (GET):**

```
GET /datastreams/{datastreamId}
Accept: application/json

Response: 200 OK
Body: DataStream resource
```

**UPDATE - Replace (PUT):**

```
PUT /datastreams/{datastreamId}
Content-Type: application/json
Body: Complete datastream resource

Response: 204 No Content
```

**DELETE:**

```
DELETE /datastreams/{datastreamId}

Response: 204 No Content (success)
         409 Conflict (has observations)
```

**DELETE with cascade (implicit):**
Deleting datastream deletes all associated observations.

**Method signatures:**

```typescript
// Create
async createDataStream(body: DataStreamInput): Promise<DataStream>
async createDataStreamForSystem(systemId: string, body: DataStreamInput): Promise<DataStream>

// Read
async getDataStream(datastreamId: string, options?: { f?: Format }): Promise<DataStream>

// Update
async updateDataStream(datastreamId: string, body: DataStreamInput): Promise<DataStream>

// Delete
async deleteDataStream(datastreamId: string): Promise<void>
```

**Important:** DataStream schema is **immutable** after creation. To change schema, must delete and recreate datastream (loses historical observations).

74. **Result Format Parameters:** Are there special format parameters for DataStreams? `obsFormat` parameter?

**Answer:** Yes, `obsFormat` parameter controls observation format for DataStream operations:

**Usage context:** The `obsFormat` is part of the DataStream **schema definition**, not a query parameter:

**DataStream schema property:**

```json
{
  "id": "ds1",
  "name": "Weather Observations",
  "schema": {
    "obsFormat": "application/json", // Observation format
    "resultSchema": {
      /* SWE schema */
    }
  }
}
```

**Supported observation formats:**

- `application/json` - JSON observations (default, most common)
- `application/swe+json` - SWE Common JSON format
- `application/swe+text` - SWE Common text format (CSV-like)
- `application/swe+binary` - SWE Common binary format (efficient for high-volume)
- `application/om+json` - O&M JSON format

**Format determines observation structure:**

**JSON format (obsFormat="application/json"):**

```json
{
  "phenomenonTime": "2024-02-02T12:00:00Z",
  "resultTime": "2024-02-02T12:01:00Z",
  "result": {
    "temp": 25.3,
    "humidity": 60.5
  }
}
```

**SWE text format (obsFormat="application/swe+text"):**

```
2024-02-02T12:00:00Z,2024-02-02T12:01:00Z,25.3,60.5
2024-02-02T12:05:00Z,2024-02-02T12:06:00Z,25.4,60.4
```

**Query parameter for GET operations:**
When retrieving observations, can specify format:

```
GET /datastreams/{id}/observations?f=json
GET /datastreams/{id}/observations?f=swe+json
GET /datastreams/{id}/observations?f=swe+text
```

**Note:** `obsFormat` is NOT a query parameter for listing datastreams. It's part of datastream metadata and defines the observation format for that specific datastream.

### O. Observations Resource Methods

**Questions:**

75. **Observations Endpoints:** What are ALL Observations endpoints? List all, get by ID, by datastream, query with temporal filters?

**Answer:** Complete list of Observations endpoints from OpenAPI Part 2 spec:

**Canonical endpoints:**

- `GET /observations` - List/query all observations across all datastreams
- `GET /observations/{obsId}` - Get specific observation by ID
- `DELETE /observations/{obsId}` - Delete specific observation

**DataStream-scoped endpoints (MOST COMMON):**

- `GET /datastreams/{datastreamId}/observations` - Get observations from specific datastream
- `POST /datastreams/{datastreamId}/observations` - Add observation(s) to specific datastream

**NO standalone POST:** Must POST to datastream (observations belong to a datastream)

**NO PUT/PATCH:** Observations are immutable once created (delete and recreate if correction needed)

**Total: 5 endpoint patterns for Observations**

**Key pattern:** Most queries use datastream-scoped endpoint since observations are always associated with a datastream.

76. **Observations Query Parameters:** What query parameters apply to Observations? phenomenonTime (PRIMARY), resultTime, foi, id, limit, offset, cursor, f, obsFormat?

**Answer:** Query parameters for Observations endpoints from OpenAPI Part 2 spec:

**Temporal filters (PRIMARY):**

- `phenomenonTime` - ISO 8601 instant/interval - when phenomenon occurred (MOST IMPORTANT FILTER)
- `resultTime` - ISO 8601 instant/interval - when result became available

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Relationship filters:**

- `datastream` - Filter by datastream ID (only for canonical /observations endpoint)
- `foi` - Filter by feature of interest ID
- `system` - Filter by system ID (implied)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (offset-based pagination) OR
- `cursor` - Cursor token (cursor-based pagination, server-dependent)

**Format negotiation:**

- `f` - Response format (json, swe+json, swe+text, swe+binary)

**TypeScript interface:**

```typescript
interface ObservationQueryOptions {
  // Temporal (PRIMARY FILTERS)
  phenomenonTime?: string; // ISO 8601 instant or interval
  resultTime?: string; // ISO 8601 instant or interval

  // Identifiers
  id?: string[];

  // Relationships
  datastream?: string[]; // Only for /observations endpoint
  foi?: string[];
  system?: string[];

  // Pagination
  limit?: number;
  offset?: number;
  cursor?: string;

  // Format
  f?: 'json' | 'swe+json' | 'swe+text' | 'swe+binary';
}
```

**Note:** `obsFormat` is NOT a query parameter - it's part of datastream schema. Use `f` parameter for format negotiation.

77. **Temporal Queries:** What are ALL phenomenonTime query patterns? Single instant, closed interval, open start, open end, multiple disjoint intervals?

**Answer:** Complete phenomenonTime query patterns (applies to all temporal parameters):

**1. Single instant (exact time):**

```
phenomenonTime=2024-02-02T12:00:00Z
phenomenonTime=2024-02-02
phenomenonTime=now
phenomenonTime=latest
```

**2. Closed interval (start and end):**

```
phenomenonTime=2024-01-01T00:00:00Z/2024-01-31T23:59:59Z
phenomenonTime=2024-01-01/2024-01-31
phenomenonTime=2024-01-15T10:00:00Z/PT1H              # Start + duration
phenomenonTime=PT1H/2024-01-15T11:00:00Z              # Duration + end
```

**3. Open start (everything before end):**

```
phenomenonTime=../2024-01-31T23:59:59Z
phenomenonTime=../2024-01-31
phenomenonTime=../now
phenomenonTime=../latest
```

**4. Open end (everything after start):**

```
phenomenonTime=2024-01-01T00:00:00Z/..
phenomenonTime=2024-01-01/..
phenomenonTime=now/..
```

**5. Special keywords:**

```
now            # Current time (server evaluates)
latest         # Most recent observation only
```

**6. Duration format (ISO 8601 duration):**

```
PT1H           # 1 hour
PT30M          # 30 minutes
PT1H30M        # 1 hour 30 minutes
P1D            # 1 day
P1M            # 1 month
P1Y            # 1 year
P1DT12H        # 1 day 12 hours
```

**NOT SUPPORTED:**

- Multiple disjoint intervals: `2024-01-01/2024-01-15,2024-02-01/2024-02-15` ❌
- Use separate queries and merge results client-side

**URL encoding examples:**

```typescript
// Closed interval
encodeURIComponent('2024-01-01T00:00:00Z/2024-01-31T23:59:59Z');
// Result: 2024-01-01T00%3A00%3A00Z%2F2024-01-31T23%3A59%3A59Z

// Open interval
encodeURIComponent('../2024-01-31');
// Result: ..%2F2024-01-31
```

**TypeScript helper:**

```typescript
function buildTemporalQuery(time: string | [string, string]): string {
  if (typeof time === 'string') {
    return time; // Single instant
  }
  return `${time[0]}/${time[1]}`; // Interval
}

// Usage:
buildTemporalQuery('2024-02-02T12:00:00Z'); // Single instant
buildTemporalQuery(['2024-01-01', '2024-01-31']); // Interval
buildTemporalQuery(['..', 'now']); // Open start
buildTemporalQuery(['now', '..']); // Open end
```

78. **Cursor Pagination:** How to implement cursor-based pagination for Observations? Extract cursor from response headers or body? Pass as query parameter?

**Answer:** Cursor-based pagination for Observations (server-dependent feature):

**Response structure with cursor:**

```json
{
  "items": [
    /* observations */
  ],
  "links": [
    {
      "rel": "next",
      "href": "https://api.example.com/datastreams/ds1/observations?limit=100&cursor=eyJpZCI6MTIzLCJ0aW1lIjoiMjAyNC0wMS0zMVQyMzo1OTo1OVoifQ=="
    }
  ]
}
```

**Extract cursor from response:**

```typescript
function extractNextCursor(response: ObservationResponse): string | undefined {
  const nextLink = response.links?.find((link) => link.rel === 'next');
  if (!nextLink) return undefined;

  const url = new URL(nextLink.href);
  return url.searchParams.get('cursor') ?? undefined;
}
```

**Pagination loop:**

```typescript
async function* getAllObservations(
  datastreamId: string,
  options?: { phenomenonTime?: string; limit?: number }
): AsyncGenerator<Observation[], void, unknown> {
  let cursor: string | undefined = undefined;
  const limit = options?.limit ?? 100;

  while (true) {
    const url = buildObservationsUrl(datastreamId, {
      ...options,
      limit,
      cursor,
    });

    const response = await fetch(url);
    const data = await response.json();

    yield data.items;

    // Extract next cursor
    cursor = extractNextCursor(data);
    if (!cursor) break; // No more pages
  }
}

// Usage:
for await (const batch of getAllObservations('ds1', { limit: 1000 })) {
  processBatch(batch);
}
```

**Fallback to offset pagination:**
If server doesn't provide cursor, use offset-based:

```typescript
async function getAllObservationsOffset(
  datastreamId: string,
  options?: { phenomenonTime?: string; limit?: number }
): Promise<Observation[]> {
  const limit = options?.limit ?? 100;
  let offset = 0;
  const allObservations: Observation[] = [];

  while (true) {
    const response = await getObservations(datastreamId, {
      ...options,
      limit,
      offset,
    });

    if (response.items.length === 0) break;
    allObservations.push(...response.items);

    if (response.items.length < limit) break; // Last page
    offset += limit;
  }

  return allObservations;
}
```

**Key points:**

- Cursor extracted from **response body links**, not HTTP headers
- Cursor is **opaque** (server-specific encoding)
- Fallback to offset if cursor not available
- Cursor is more efficient for large temporal queries

79. **Observations CRUD:** What CRUD operations for Observations? POST single, POST bulk array, PUT (rare), DELETE?

**Answer:** CRUD operations for Observations from OpenAPI Part 2 spec:

**CREATE single observation (POST):**

```
POST /datastreams/{datastreamId}/observations
Content-Type: application/json
Body: Single observation object

Response: 201 Created
Location: https://api.example.com/observations/{new-id}
```

**CREATE bulk observations (POST array):**

```
POST /datastreams/{datastreamId}/observations
Content-Type: application/json
Body: Array of observation objects

Response: 201 Created
Body: Array of created observation IDs or full observations
```

**READ (GET):**

```
GET /observations/{obsId}
Accept: application/json

Response: 200 OK
Body: Single observation
```

**NO UPDATE:** Observations are **immutable** after creation

```
PUT /observations/{obsId}    ✗ Not supported
PATCH /observations/{obsId}  ✗ Not supported
```

**DELETE:**

```
DELETE /observations/{obsId}

Response: 204 No Content
```

**Method signatures:**

```typescript
// Create single
async createObservation(
  datastreamId: string,
  observation: ObservationInput
): Promise<Observation>

// Create bulk
async createObservations(
  datastreamId: string,
  observations: ObservationInput[]
): Promise<Observation[]>

// Read
async getObservation(obsId: string, options?: { f?: Format }): Promise<Observation>

// Delete
async deleteObservation(obsId: string): Promise<void>

// NO UPDATE METHODS
```

**Rationale for immutability:**

- Observations are **historical records** (should not be changed)
- For corrections: Delete incorrect observation, create new corrected one
- Maintains data integrity and audit trail

80. **Bulk Operations:** How to support bulk observation creation? POST array to `/datastreams/{id}/observations`?

**Answer:** Bulk observation creation via POST array:

**Request format:**

```
POST /datastreams/{datastreamId}/observations
Content-Type: application/json
Body: Array of observations

[
  {
    "phenomenonTime": "2024-02-02T12:00:00Z",
    "resultTime": "2024-02-02T12:01:00Z",
    "result": { "temp": 25.3, "humidity": 60.5 }
  },
  {
    "phenomenonTime": "2024-02-02T12:05:00Z",
    "resultTime": "2024-02-02T12:06:00Z",
    "result": { "temp": 25.4, "humidity": 60.4 }
  },
  /* ... up to 10,000 observations */
]
```

**Response:**

```json
{
  "items": [
    {
      "id": "obs1",
      "phenomenonTime": "2024-02-02T12:00:00Z",
      "resultTime": "2024-02-02T12:01:00Z",
      "result": { "temp": 25.3, "humidity": 60.5 }
    }
    /* ... */
  ]
}
```

**Implementation:**

```typescript
async createObservations(
  datastreamId: string,
  observations: ObservationInput[]
): Promise<Observation[]> {
  const baseUrl = this.getResourceLink('datastreams');
  const url = `${baseUrl}/${datastreamId}/observations`;

  // Batch into chunks of max 10,000
  const batchSize = 10000;
  const allCreated: Observation[] = [];

  for (let i = 0; i < observations.length; i += batchSize) {
    const batch = observations.slice(i, i + batchSize);

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batch)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    allCreated.push(...result.items);
  }

  return allCreated;
}
```

**Performance recommendations:**

- **Batch size:** 100-1000 observations per request (balance latency vs throughput)
- **Max size:** 10,000 observations per request (server limit)
- **Compression:** Use gzip compression for large batches
- **Parallel requests:** Consider parallel POST for independent batches

**Error handling:**

- Partial failure: Some observations may succeed, others fail
- Server should return details of failed observations
- Client should retry failed items

81. **Limit Constraints:** What is max limit for Observations? 10,000 for Part 2?

**Answer:** Pagination limits for Observations are **same as Part 1**:

**Constraints:**

- **Minimum:** 1
- **Maximum:** 10,000
- **Default:** 10

**Consistent across Part 1 and Part 2:**

```yaml
# Part 1 (Systems, Deployments, etc.)
limit:
  minimum: 1
  maximum: 10000
  default: 10

# Part 2 (DataStreams, Observations, etc.)
limit:
  minimum: 1
  maximum: 10000
  default: 10
```

**Practical recommendations for Observations:**

**Interactive queries (dashboards):**

```
limit=50-100  # Responsive UI, quick load
```

**Batch processing (analysis):**

```
limit=1000-10000  # Efficient bulk retrieval
```

**Real-time streaming:**

```
limit=10-50  # Low latency, frequent polls
```

**Historical export:**

```
limit=10000  # Minimize round trips
```

**TypeScript validation:**

```typescript
function validateLimit(limit?: number): number {
  const value = limit ?? 10;

  if (value < 1 || value > 10000) {
    throw new RangeError('limit must be between 1 and 10,000');
  }

  return value;
}
```

**Note:** Server MAY return fewer observations than limit if insufficient matches exist. Check response length to detect last page.

### P. Control Streams Resource Methods

**Questions:**

82. **Control Streams Endpoints:** What are ALL Control Streams endpoints? List all, get by ID, query, by system, schema endpoint, in collection?

**Answer:** Complete list of ControlStreams endpoints from OpenAPI Part 2 spec:

**Canonical endpoints:**

- `GET /controlstreams` - List/query all control streams
- `POST /controlstreams` - Create new control stream
- `GET /controlstreams/{controlstreamId}` - Get specific control stream by ID
- `PUT /controlstreams/{controlstreamId}` - Replace control stream (complete update)
- `DELETE /controlstreams/{controlstreamId}` - Delete control stream

**Association endpoints (reverse navigation):**

- `GET /systems/{systemId}/controlstreams` - List control streams of specific system
- `POST /systems/{systemId}/controlstreams` - Create control stream for specific system

**Schema endpoint:**

- `GET /controlstreams/{controlstreamId}/schema` - Get command schema for control stream
- Format negotiation: `?f=json`, `?f=proto`, `?f=swe+json`

**Commands endpoint (nested):**

- `GET /controlstreams/{controlstreamId}/commands` - Get commands for control stream
- `POST /controlstreams/{controlstreamId}/commands` - Submit command(s) to control stream

**No hierarchical structure:** ControlStreams are flat (no sub-control streams)

**Total: 9 distinct endpoint patterns for ControlStreams**

83. **Control Streams Query Parameters:** What query parameters apply to Control Streams? system, controlledProperty, id, uid, q, properties, limit, offset, f?

**Answer:** Query parameters for ControlStreams endpoints from OpenAPI Part 2 spec:

**NO spatial/temporal filters:** ControlStreams don't have spatial/temporal extent

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Text search:**

- `q` - Comma-separated keywords for full-text search

**Relationship filters:**

- `system` - Filter by system ID (control streams for specific system)
- `controlledProperty` - Filter by controlled property ID or URI
- `foi` - Filter by feature of interest ID (implied)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (default 0) OR
- `cursor` - Cursor token for cursor-based pagination (server-dependent)

**Format negotiation:**

- `f` - Response format (json, html)

**TypeScript interface:**

```typescript
interface ControlStreamQueryOptions {
  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Relationships
  system?: string[];
  controlledProperty?: string[];
  foi?: string[];

  // Pagination
  limit?: number;
  offset?: number;
  cursor?: string;

  // Format
  f?: 'json' | 'html';
}
```

84. **Schema Endpoint:** How to construct schema endpoint URL? `/controlstreams/{id}/schema`? What format?

**Answer:** Schema endpoint provides command structure for a control stream:

**Endpoint pattern:**

```
GET /controlstreams/{controlstreamId}/schema
GET /controlstreams/{controlstreamId}/schema?f=json
GET /controlstreams/{controlstreamId}/schema?f=proto
GET /controlstreams/{controlstreamId}/schema?f=swe+json
```

**Format negotiation:**

- `f=json` - JSON Schema format (default)
- `f=proto` - Protocol Buffers schema
- `f=swe+json` - SWE Common JSON schema

**Response structure (JSON Schema format):**

```json
{
  "cmdFormat": "application/json",
  "parametersSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "pan",
        "type": "Quantity",
        "definition": "http://example.org/ont/pan_angle",
        "label": "Pan Angle",
        "uom": { "code": "deg" },
        "constraint": {
          "type": "AllowedValues",
          "intervals": [[-180, 180]]
        }
      },
      {
        "name": "tilt",
        "type": "Quantity",
        "definition": "http://example.org/ont/tilt_angle",
        "label": "Tilt Angle",
        "uom": { "code": "deg" },
        "constraint": {
          "type": "AllowedValues",
          "intervals": [[-90, 90]]
        }
      }
    ]
  }
}
```

**Method signature:**

```typescript
async getControlStreamSchema(
  controlstreamId: string,
  options?: { f?: 'json' | 'proto' | 'swe+json' }
): Promise<ControlStreamSchema>
```

**Use cases:**

- **Client validation:** Validate commands before submission
- **UI generation:** Auto-generate control forms from schema
- **Parameter parsing:** Understand command structure

85. **Control Streams CRUD:** What CRUD operations for Control Streams? POST, PUT/PATCH, DELETE with cascade?

**Answer:** Complete CRUD operations for ControlStreams from OpenAPI Part 2 spec:

**CREATE (POST):**

```
POST /controlstreams
Content-Type: application/json
Body: ControlStream resource with schema

Response: 201 Created
Location: https://api.example.com/controlstreams/{new-id}
```

**CREATE for specific system:**

```
POST /systems/{systemId}/controlstreams
Content-Type: application/json
Body: ControlStream resource

Response: 201 Created
```

**READ (GET):**

```
GET /controlstreams/{controlstreamId}
Accept: application/json

Response: 200 OK
Body: ControlStream resource
```

**UPDATE - Replace (PUT):**

```
PUT /controlstreams/{controlstreamId}
Content-Type: application/json
Body: Complete control stream resource

Response: 204 No Content
```

**DELETE:**

```
DELETE /controlstreams/{controlstreamId}

Response: 204 No Content (success)
         409 Conflict (has commands)
```

**DELETE with cascade (implicit):**
Deleting control stream deletes all associated commands.

**Method signatures:**

```typescript
// Create
async createControlStream(body: ControlStreamInput): Promise<ControlStream>
async createControlStreamForSystem(systemId: string, body: ControlStreamInput): Promise<ControlStream>

// Read
async getControlStream(controlstreamId: string, options?: { f?: Format }): Promise<ControlStream>

// Update
async updateControlStream(controlstreamId: string, body: ControlStreamInput): Promise<ControlStream>

// Delete
async deleteControlStream(controlstreamId: string): Promise<void>
```

**Important:** ControlStream schema is **immutable** after creation. To change schema, must delete and recreate control stream.

86. **Parameter Format:** Are there special format parameters for Control Streams? `cmdFormat` parameter?

**Answer:** Yes, `cmdFormat` parameter controls command format for ControlStream operations:

**Usage context:** The `cmdFormat` is part of the ControlStream **schema definition**, not a query parameter:

**ControlStream schema property:**

```json
{
  "id": "cs1",
  "name": "Pan/Tilt Control",
  "schema": {
    "cmdFormat": "application/json", // Command format
    "parametersSchema": {
      /* SWE schema */
    }
  }
}
```

**Supported command formats:**

- `application/json` - JSON commands (default, most common)
- `application/swe+json` - SWE Common JSON format
- `application/swe+text` - SWE Common text format
- `application/swe+binary` - SWE Common binary format

**Format determines command structure:**

**JSON format (cmdFormat="application/json"):**

```json
{
  "issueTime": "2024-02-02T12:00:00Z",
  "executionTime": "2024-02-02T12:05:00Z",
  "parameters": {
    "pan": 45.0,
    "tilt": 30.0
  }
}
```

**Query parameter for GET operations:**
When retrieving commands, can specify format:

```
GET /controlstreams/{id}/commands?f=json
GET /controlstreams/{id}/commands?f=swe+json
```

**Note:** `cmdFormat` is NOT a query parameter for listing control streams. It's part of control stream metadata and defines the command format for that specific control stream.

### Q. Commands Resource Methods

**Questions:**

87. **Commands Endpoints:** What are ALL Commands endpoints? List all, get by ID, by controlstream, query with temporal filters, status endpoint, result endpoint, feasibility endpoint?

**Answer:** Complete list of Commands endpoints from OpenAPI Part 2 spec:

**Canonical endpoints:**

- `GET /commands` - List/query all commands across all control streams
- `GET /commands/{cmdId}` - Get specific command by ID
- `DELETE /commands/{cmdId}` - Delete/cancel command

**ControlStream-scoped endpoints (MOST COMMON):**

- `GET /controlstreams/{controlstreamId}/commands` - Get commands for specific control stream
- `POST /controlstreams/{controlstreamId}/commands` - Submit command(s) to specific control stream

**Status endpoints:**

- `GET /commands/{cmdId}/status` - Get all status updates for command
- `GET /commands/{cmdId}/status/{statusId}` - Get specific status update
- `POST /commands/{cmdId}/status` - Add status update to command

**Result endpoints:**

- `GET /commands/{cmdId}/result` - Get all results for command
- `GET /commands/{cmdId}/result/{resultId}` - Get specific result
- `POST /commands/{cmdId}/result` - Add result to command

**Feasibility endpoint (NOT IMPLEMENTED IN SPEC):**

- `POST /controlstreams/{controlstreamId}/feasibility` - Check command feasibility (FUTURE FEATURE)

**Total: 11 distinct endpoint patterns for Commands**

**Key pattern:** Most operations use controlstream-scoped endpoint since commands are always associated with a control stream.

88. **Commands Query Parameters:** What query parameters apply to Commands? issueTime (PRIMARY), executionTime, status, controlstream, id, limit, offset, cursor, f, cmdFormat?

**Answer:** Query parameters for Commands endpoints from OpenAPI Part 2 spec:

**Temporal filters (PRIMARY):**

- `issueTime` - ISO 8601 instant/interval - when command was issued (MOST IMPORTANT FILTER)
- `executionTime` - ISO 8601 instant/interval - when command should be/was executed

**Status filter:**

- `statusCode` - Comma-separated list of status codes (PENDING, ACCEPTED, REJECTED, SCHEDULED, UPDATED, CANCELED, EXECUTING, FAILED, COMPLETED)

**Identifier filters:**

- `id` - Comma-separated list of local IDs or URNs

**Relationship filters:**

- `controlStream` - Filter by control stream ID (only for canonical /commands endpoint)
- `system` - Filter by system ID
- `foi` - Filter by feature of interest ID
- `controlledProperty` - Filter by controlled property ID or URI
- `sender` - Filter by sender ID (who issued command)

**Pagination:**

- `limit` - Max items per page (1-10000, default 10)
- `offset` - Zero-based starting index (offset-based pagination) OR
- `cursor` - Cursor token (cursor-based pagination, server-dependent)

**Format negotiation:**

- `f` - Response format (json, swe+json)

**TypeScript interface:**

```typescript
interface CommandQueryOptions {
  // Temporal (PRIMARY FILTERS)
  issueTime?: string; // ISO 8601 instant or interval
  executionTime?: string; // ISO 8601 instant or interval

  // Status filter
  statusCode?: CommandStatus[];

  // Identifiers
  id?: string[];

  // Relationships
  controlStream?: string[]; // Only for /commands endpoint
  system?: string[];
  foi?: string[];
  controlledProperty?: string[];
  sender?: string[];

  // Pagination
  limit?: number;
  offset?: number;
  cursor?: string;

  // Format
  f?: 'json' | 'swe+json';
}

type CommandStatus =
  | 'PENDING' // Submitted, not yet processed
  | 'ACCEPTED' // Accepted for execution
  | 'REJECTED' // Rejected (validation failed)
  | 'SCHEDULED' // Scheduled for future execution
  | 'UPDATED' // Command parameters updated
  | 'CANCELED' // Canceled by user
  | 'EXECUTING' // Currently executing
  | 'FAILED' // Execution failed
  | 'COMPLETED'; // Successfully completed
```

89. **Status Endpoint:** How to construct command status endpoint? `/commands/{id}/status`? What does it return?

**Answer:** Command status endpoint provides execution status history:

**Endpoint patterns:**

```
GET /commands/{cmdId}/status           # Get all status updates
GET /commands/{cmdId}/status/{statusId} # Get specific status update
POST /commands/{cmdId}/status          # Add status update (server/system use)
```

**Response structure (GET all statuses):**

```json
{
  "items": [
    {
      "id": "status1",
      "time": "2024-02-02T12:00:00Z",
      "statusCode": "PENDING",
      "message": "Command queued for processing"
    },
    {
      "id": "status2",
      "time": "2024-02-02T12:00:05Z",
      "statusCode": "ACCEPTED",
      "message": "Command validated and accepted"
    },
    {
      "id": "status3",
      "time": "2024-02-02T12:05:00Z",
      "statusCode": "EXECUTING",
      "message": "Executing command"
    },
    {
      "id": "status4",
      "time": "2024-02-02T12:05:30Z",
      "statusCode": "COMPLETED",
      "message": "Command completed successfully"
    }
  ]
}
```

**Method signatures:**

```typescript
// Get all status updates
async getCommandStatuses(cmdId: string): Promise<CommandStatus[]>

// Get specific status update
async getCommandStatus(cmdId: string, statusId: string): Promise<CommandStatus>

// Add status update (server/system use)
async addCommandStatus(cmdId: string, status: CommandStatusInput): Promise<CommandStatus>
```

**Status lifecycle:**

```
PENDING → ACCEPTED → SCHEDULED → EXECUTING → COMPLETED
         ↘ REJECTED
                    ↘ CANCELED
                               ↘ FAILED
```

**Use cases:**

- **Client polling:** Check command execution progress
- **Audit trail:** Track command lifecycle
- **Error diagnosis:** Understand failure reasons

90. **Result Endpoint:** How to construct command result endpoint? `/commands/{id}/result`? What does it return?

**Answer:** Command result endpoint provides execution results:

**Endpoint patterns:**

```
GET /commands/{cmdId}/result           # Get all results
GET /commands/{cmdId}/result/{resultId} # Get specific result
POST /commands/{cmdId}/result          # Add result (server/system use)
```

**Response structure (GET all results):**

```json
{
  "items": [
    {
      "id": "result1",
      "time": "2024-02-02T12:05:30Z",
      "value": {
        "actualPan": 44.8,
        "actualTilt": 29.9,
        "executionDuration": 30.5
      }
    }
  ]
}
```

**Method signatures:**

```typescript
// Get all results
async getCommandResults(cmdId: string): Promise<CommandResult[]>

// Get specific result
async getCommandResult(cmdId: string, resultId: string): Promise<CommandResult>

// Add result (server/system use)
async addCommandResult(cmdId: string, result: CommandResultInput): Promise<CommandResult>
```

**Result vs Status:**

- **Status:** Execution state (PENDING, EXECUTING, COMPLETED, etc.)
- **Result:** Actual execution outcome (measured values, confirmation data)

**Use cases:**

- **Verification:** Confirm command execution
- **Telemetry:** Get actual achieved values (e.g., actual pan/tilt vs commanded)
- **Quality control:** Validate execution accuracy

91. **Feasibility Endpoint:** How to construct feasibility endpoint? `POST /controlstreams/{id}/feasibility` with parameters?

**Answer:** Feasibility endpoint checks if command is feasible **without executing it**:

**Endpoint pattern:**

```
POST /controlstreams/{controlstreamId}/feasibility
Content-Type: application/json
Body: Command parameters to check
```

**Request:**

```json
{
  "executionTime": "2024-02-02T12:05:00Z",
  "parameters": {
    "pan": 45.0,
    "tilt": 30.0
  }
}
```

**Response:**

```json
{
  "feasible": true,
  "message": "Command can be executed",
  "estimatedDuration": "PT30S",
  "constraints": {
    "maxPan": 180.0,
    "minPan": -180.0,
    "maxTilt": 90.0,
    "minTilt": -90.0
  }
}
```

**OR (if not feasible):**

```json
{
  "feasible": false,
  "message": "Cannot execute: Pan angle exceeds maximum",
  "violations": [
    {
      "parameter": "pan",
      "value": 200.0,
      "constraint": "max",
      "limit": 180.0
    }
  ]
}
```

**Method signature:**

```typescript
async checkCommandFeasibility(
  controlstreamId: string,
  command: CommandInput
): Promise<FeasibilityResult>

interface FeasibilityResult {
  feasible: boolean;
  message: string;
  estimatedDuration?: string;  // ISO 8601 duration
  constraints?: Record<string, any>;
  violations?: Array<{
    parameter: string;
    value: any;
    constraint: string;
    limit: any;
  }>;
}
```

**Note:** OpenAPI Part 2 spec does **NOT** formally define feasibility endpoint. It's a **proposed future feature**. Implementation is server-dependent.

**Use cases:**

- **Pre-validation:** Check command before submission
- **UI feedback:** Show feasibility in real-time
- **Conflict avoidance:** Prevent impossible commands

92. **Status Filtering:** How to filter commands by status? `status` parameter with multiple values (pending, executing, completed, failed, cancelled)?

**Answer:** Filter commands by status using `statusCode` parameter:

**Query pattern:**

```
GET /commands?statusCode=PENDING
GET /commands?statusCode=EXECUTING,SCHEDULED
GET /commands?statusCode=COMPLETED,FAILED
GET /controlstreams/{id}/commands?statusCode=PENDING
```

**Status codes (from OpenAPI spec):**

- `PENDING` - Submitted, awaiting processing
- `ACCEPTED` - Validated and accepted
- `REJECTED` - Validation failed
- `SCHEDULED` - Scheduled for future execution
- `UPDATED` - Command parameters updated
- `CANCELED` - Canceled by user (note: American spelling)
- `EXECUTING` - Currently executing
- `FAILED` - Execution failed
- `COMPLETED` - Successfully completed

**TypeScript implementation:**

```typescript
enum CommandStatusCode {
  PENDING = 'PENDING',
  ACCEPTED = 'ACCEPTED',
  REJECTED = 'REJECTED',
  SCHEDULED = 'SCHEDULED',
  UPDATED = 'UPDATED',
  CANCELED = 'CANCELED',
  EXECUTING = 'EXECUTING',
  FAILED = 'FAILED',
  COMPLETED = 'COMPLETED',
}

interface CommandQueryOptions {
  statusCode?: CommandStatusCode[];
  // ... other options
}

// Build query string
if (options.statusCode?.length > 0) {
  url.searchParams.set('statusCode', options.statusCode.join(','));
}
// Result: ?statusCode=PENDING,EXECUTING
```

**Common use cases:**

```typescript
// Get pending commands
getCommands({ statusCode: [CommandStatusCode.PENDING] });

// Get active commands (executing or scheduled)
getCommands({
  statusCode: [CommandStatusCode.EXECUTING, CommandStatusCode.SCHEDULED],
});

// Get completed/failed commands (historical)
getCommands({
  statusCode: [CommandStatusCode.COMPLETED, CommandStatusCode.FAILED],
});

// Get all non-terminal commands (can still change)
getCommands({
  statusCode: [
    CommandStatusCode.PENDING,
    CommandStatusCode.ACCEPTED,
    CommandStatusCode.SCHEDULED,
    CommandStatusCode.EXECUTING,
  ],
});
```

93. **Temporal Queries:** What are issueTime and executionTime query patterns? ISO 8601 intervals?

**Answer:** Temporal queries for commands use same ISO 8601 syntax as observations:

**issueTime query patterns (when command was submitted):**

```
issueTime=2024-02-02T12:00:00Z                           # Exact time
issueTime=2024-02-02                                     # Whole day
issueTime=2024-01-01/2024-01-31                          # January commands
issueTime=../now                                         # All commands up to now
issueTime=2024-02-01/..                                  # From Feb 1 onwards
issueTime=latest                                         # Most recent command
```

**executionTime query patterns (when command should be/was executed):**

```
executionTime=2024-02-02T14:00:00Z                       # Exact execution time
executionTime=2024-02-02/2024-02-03                      # Executed in date range
executionTime=now/..                                     # Scheduled for future
executionTime=../now                                     # Already executed
executionTime=2024-02-02T12:00:00Z/PT1H                  # Within 1 hour window
```

**Combining filters:**

```
# Commands issued today for future execution
GET /commands?issueTime=2024-02-02&executionTime=now/..

# Commands issued last month that failed
GET /commands?issueTime=2024-01-01/2024-01-31&statusCode=FAILED

# Commands executed yesterday
GET /commands?executionTime=2024-02-01
```

**TypeScript helper:**

```typescript
interface CommandTemporalQuery {
  issueTime?: string; // When command was submitted
  executionTime?: string; // When command should be/was executed
}

// Find commands issued but not yet executed
const pendingCommands = await getCommands({
  issueTime: '../now',
  executionTime: 'now/..',
  statusCode: [CommandStatusCode.SCHEDULED],
});

// Find commands that failed during execution
const failedCommands = await getCommands({
  executionTime: '../now',
  statusCode: [CommandStatusCode.FAILED],
});
```

94. **Commands CRUD:** What CRUD operations for Commands? POST single, POST bulk array, PATCH status/result, POST cancel?

**Answer:** CRUD operations for Commands from OpenAPI Part 2 spec:

**CREATE single command (POST):**

```
POST /controlstreams/{controlstreamId}/commands
Content-Type: application/json
Body: Single command object

Response: 201 Created (async) OR 200 OK (sync)
Location: https://api.example.com/commands/{new-id}
```

**CREATE bulk commands (POST array):**

```
POST /controlstreams/{controlstreamId}/commands
Content-Type: application/json
Body: Array of command objects

Response: 201 Created
Body: Array of created command IDs
```

**READ (GET):**

```
GET /commands/{cmdId}
Accept: application/json

Response: 200 OK
Body: Single command with current status
```

**UPDATE status (POST to status endpoint):**

```
POST /commands/{cmdId}/status
Content-Type: application/json
Body: Status update

Response: 201 Created
```

**UPDATE result (POST to result endpoint):**

```
POST /commands/{cmdId}/result
Content-Type: application/json
Body: Result data

Response: 201 Created
```

**CANCEL (DELETE):**

```
DELETE /commands/{cmdId}

Response: 204 No Content
Side effect: Status changes to CANCELED
```

**NO PUT/PATCH on command itself:** Once submitted, command parameters are immutable. Can only update status/result or cancel.

**Method signatures:**

```typescript
// Create single
async submitCommand(
  controlstreamId: string,
  command: CommandInput
): Promise<Command>

// Create bulk
async submitCommands(
  controlstreamId: string,
  commands: CommandInput[]
): Promise<Command[]>

// Read
async getCommand(cmdId: string, options?: { f?: Format }): Promise<Command>

// Update status (server/system use)
async updateCommandStatus(cmdId: string, status: CommandStatusInput): Promise<CommandStatus>

// Update result (server/system use)
async updateCommandResult(cmdId: string, result: CommandResultInput): Promise<CommandResult>

// Cancel
async cancelCommand(cmdId: string): Promise<void>
```

95. **Bulk Operations:** How to support bulk command submission? POST array to `/controlstreams/{id}/commands`?

**Answer:** Bulk command submission via POST array:

**Request format:**

```
POST /controlstreams/{controlstreamId}/commands
Content-Type: application/json
Body: Array of commands

[
  {
    "issueTime": "2024-02-02T12:00:00Z",
    "executionTime": "2024-02-02T12:05:00Z",
    "parameters": { "pan": 45.0, "tilt": 30.0 }
  },
  {
    "issueTime": "2024-02-02T12:00:00Z",
    "executionTime": "2024-02-02T12:10:00Z",
    "parameters": { "pan": 90.0, "tilt": 15.0 }
  },
  /* ... up to 10,000 commands */
]
```

**Response:**

```json
{
  "items": [
    {
      "id": "cmd1",
      "issueTime": "2024-02-02T12:00:00Z",
      "executionTime": "2024-02-02T12:05:00Z",
      "statusCode": "PENDING",
      "parameters": { "pan": 45.0, "tilt": 30.0 }
    }
    /* ... */
  ]
}
```

**Implementation:**

```typescript
async submitCommands(
  controlstreamId: string,
  commands: CommandInput[]
): Promise<Command[]> {
  const baseUrl = this.getResourceLink('controlstreams');
  const url = `${baseUrl}/${controlstreamId}/commands`;

  // Batch into chunks of max 10,000
  const batchSize = 10000;
  const allSubmitted: Command[] = [];

  for (let i = 0; i < commands.length; i += batchSize) {
    const batch = commands.slice(i, i + batchSize);

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batch)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    allSubmitted.push(...result.items);
  }

  return allSubmitted;
}
```

**Use cases:**

- **Scheduled commands:** Submit sequence of commands for automated execution
- **Mission planning:** Pre-program entire mission sequence
- **Batch control:** Update multiple systems simultaneously

96. **Synchronous vs Asynchronous:** How do sync vs async command execution differ? Different response codes (200 vs 201)?

**Answer:** Commands support both synchronous and asynchronous execution:

**Asynchronous execution (MOST COMMON):**

```
POST /controlstreams/{id}/commands
Body: Command

Response: 201 Created
Location: https://api.example.com/commands/{cmd-id}
Body: {
  "id": "cmd123",
  "statusCode": "PENDING",
  "issueTime": "2024-02-02T12:00:00Z",
  "executionTime": "2024-02-02T12:05:00Z"
}
```

**Client workflow:**

```typescript
// 1. Submit command
const command = await submitCommand(controlstreamId, {
  /* params */
});

// 2. Poll status
while (true) {
  const statuses = await getCommandStatuses(command.id);
  const latestStatus = statuses[statuses.length - 1];

  if (latestStatus.statusCode === 'COMPLETED') {
    break;
  } else if (latestStatus.statusCode === 'FAILED') {
    throw new Error('Command failed');
  }

  await sleep(1000); // Poll every second
}

// 3. Get result
const results = await getCommandResults(command.id);
```

**Synchronous execution (RARE):**

```
POST /controlstreams/{id}/commands
Body: Command

Response: 200 OK
Body: {
  "id": "cmd123",
  "statusCode": "COMPLETED",
  "issueTime": "2024-02-02T12:00:00Z",
  "executionTime": "2024-02-02T12:00:05Z",
  "result": {
    "actualPan": 44.8,
    "actualTilt": 29.9
  }
}
```

**Response code differences:**

- **201 Created:** Command accepted, will execute asynchronously (client must poll)
- **200 OK:** Command executed synchronously, result included in response (rare)

**Server behavior:**

- **Async:** Server returns immediately, command queued for execution
- **Sync:** Server waits for execution to complete before responding (blocks)

**Sync execution conditions:**

- Command has immediate `executionTime` (now)
- System supports synchronous execution
- Execution is fast (< 1 second)
- Client explicitly requests sync (implementation-specific)

**Recommendation:** **Always assume asynchronous** - design for polling status endpoint.

### R. TypeScript Type Definitions

**Questions:**

97. **Query Parameter Interfaces:** What TypeScript interfaces should be defined for query parameters? One per resource type? Common parameters interface?

**Answer:** Define **base interface + resource-specific extensions** for query parameters:

**Base interface (common parameters):**

```typescript
interface BaseQueryOptions {
  // Identifiers
  id?: string[];

  // Text search
  q?: string[];

  // Pagination
  limit?: number;
  offset?: number;
  cursor?: string;

  // Format
  f?: 'json' | 'geojson' | 'html';
}
```

**Spatial extension:**

```typescript
interface SpatialQueryOptions {
  bbox?: [number, number, number, number];
  geom?: string; // WKT geometry
}
```

**Temporal extension:**

```typescript
interface TemporalQueryOptions {
  datetime?: string; // ISO 8601 instant or interval
}
```

**Resource-specific interfaces:**

```typescript
// Systems
interface SystemQueryOptions
  extends BaseQueryOptions,
    SpatialQueryOptions,
    TemporalQueryOptions {
  parent?: string[];
  deployment?: string[];
  procedure?: string[];
  foi?: string[];
  observedProperty?: string[];
  controlledProperty?: string[];
  recursive?: boolean;
  f?: 'json' | 'geojson' | 'sml+json' | 'html';
}

// Deployments
interface DeploymentQueryOptions
  extends BaseQueryOptions,
    SpatialQueryOptions,
    TemporalQueryOptions {
  parent?: string[];
  system?: string[];
  foi?: string[];
  observedProperty?: string[];
  controlledProperty?: string[];
  recursive?: boolean;
  f?: 'json' | 'geojson' | 'html';
}

// Procedures
interface ProcedureQueryOptions extends BaseQueryOptions {
  system?: string[];
  f?: 'json' | 'geojson' | 'sml+json' | 'html';
}

// Sampling Features
interface SamplingFeatureQueryOptions
  extends BaseQueryOptions,
    SpatialQueryOptions {
  system?: string[];
  foi?: string[];
  f?: 'json' | 'geojson' | 'html';
}

// Properties
interface PropertyQueryOptions extends BaseQueryOptions {
  system?: string[];
  baseProperty?: string[];
  objectType?: string[];
  f?: 'json' | 'html';
}

// DataStreams
interface DataStreamQueryOptions extends BaseQueryOptions {
  phenomenonTime?: string;
  resultTime?: string;
  system?: string[];
  observedProperty?: string[];
  foi?: string[];
  procedure?: string[];
  deployment?: string[];
  f?: 'json' | 'html';
}

// Observations
interface ObservationQueryOptions extends BaseQueryOptions {
  phenomenonTime?: string; // PRIMARY filter
  resultTime?: string;
  datastream?: string[]; // Only for /observations endpoint
  foi?: string[];
  system?: string[];
  f?: 'json' | 'swe+json' | 'swe+text' | 'swe+binary';
}

// ControlStreams
interface ControlStreamQueryOptions extends BaseQueryOptions {
  system?: string[];
  controlledProperty?: string[];
  foi?: string[];
  f?: 'json' | 'html';
}

// Commands
interface CommandQueryOptions extends BaseQueryOptions {
  issueTime?: string; // PRIMARY filter
  executionTime?: string;
  statusCode?: CommandStatus[];
  controlStream?: string[]; // Only for /commands endpoint
  system?: string[];
  foi?: string[];
  controlledProperty?: string[];
  sender?: string[];
  f?: 'json' | 'swe+json';
}
```

**Benefit of this pattern:**

- Code reuse via extends
- Type safety for each resource type
- Intellisense support
- Clear documentation of supported parameters

98. **Request Body Types:** What TypeScript types for CRUD request bodies? GeoJSON features? SensorML documents? Observation/command arrays?

**Answer:** Define **input types** for request bodies (separate from response types):

**Part 1 resource inputs:**

```typescript
// Systems (GeoJSON or SensorML)
interface SystemInput {
  name: string;
  description?: string;
  validTime?: [string, string]; // ISO 8601 period
  geometry?: GeoJSON.Geometry;
  properties?: Record<string, any>;
  // ... SensorML properties if using sml+json format
}

// Deployments (GeoJSON)
interface DeploymentInput {
  name: string;
  description?: string;
  validTime?: [string, string];
  geometry?: GeoJSON.Geometry;
  properties?: Record<string, any>;
}

// Procedures (GeoJSON or SensorML)
interface ProcedureInput {
  name: string;
  description?: string;
  // ... SensorML properties if using sml+json format
}

// Sampling Features (GeoJSON)
interface SamplingFeatureInput extends GeoJSON.Feature {
  properties: {
    name: string;
    description?: string;
    sampledFeature?: string; // FOI link
    [key: string]: any;
  };
}
```

**Part 2 resource inputs:**

```typescript
// DataStreams
interface DataStreamInput {
  name: string;
  description?: string;
  system: string; // Required: system ID
  outputName?: string;
  schema: {
    obsFormat: string; // 'application/json', etc.
    resultSchema: SWEDataRecord; // SWE Common schema
    parametersSchema?: SWEDataRecord;
  };
}

// Observations
interface ObservationInput {
  phenomenonTime: string; // Required: ISO 8601
  resultTime?: string;
  result: any; // Structure defined by datastream schema
  resultQuality?: QualityInfo;
  parameters?: Record<string, any>;
}

// ControlStreams
interface ControlStreamInput {
  name: string;
  description?: string;
  system: string; // Required: system ID
  inputName?: string;
  schema: {
    cmdFormat: string; // 'application/json', etc.
    parametersSchema: SWEDataRecord; // SWE Common schema
  };
}

// Commands
interface CommandInput {
  issueTime?: string; // ISO 8601 (defaults to now)
  executionTime?: string; // ISO 8601 (defaults to immediate)
  parameters: any; // Structure defined by controlstream schema
  priority?: number;
}
```

**Array types for bulk operations:**

```typescript
type ObservationBulkInput = ObservationInput[];
type CommandBulkInput = CommandInput[];
```

**Utility types:**

```typescript
// For PATCH operations (all properties optional)
type SystemUpdate = Partial<SystemInput>;
type DeploymentUpdate = Partial<DeploymentInput>;

// For responses (includes server-assigned fields)
interface SystemResponse extends SystemInput {
  id: string; // Server-assigned
  links: Link[];
  // ... other read-only fields
}
```

99. **Response Types:** Should methods return typed responses or leave typing to handlers?

**Answer:** **QueryBuilder methods should return typed responses**, not raw fetch responses:

**Pattern: Strongly typed method returns**

```typescript
class CSAPIQueryBuilder {
  // Returns typed resource, not Response
  async getSystems(options?: SystemQueryOptions): Promise<System[]> {
    const url = this.buildSystemsUrl(options);
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.features || data.items; // Handle both formats
  }

  // Returns single typed resource
  async getSystem(systemId: string, options?: { f?: Format }): Promise<System> {
    const url = this.buildSystemUrl(systemId, options);
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  // Returns paginated response with metadata
  async getSystemsPaginated(options?: SystemQueryOptions): Promise<{
    items: System[];
    links?: Link[];
    totalResults?: number;
  }> {
    const url = this.buildSystemsUrl(options);
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      items: data.features || data.items,
      links: data.links,
      totalResults: data.numberMatched,
    };
  }
}
```

**Response type hierarchy:**

```typescript
// Individual resource response
interface System {
  id: string;
  name: string;
  description?: string;
  validTime?: [string, string];
  geometry?: GeoJSON.Geometry;
  properties?: Record<string, any>;
  links: Link[];
}

// Collection response
interface SystemCollection {
  items: System[];
  links?: Link[];
  numberMatched?: number;
  numberReturned?: number;
}

// Paginated response (generic)
interface PaginatedResponse<T> {
  items: T[];
  links?: Link[];
  totalResults?: number;
}
```

**Benefits:**

- **Type safety:** Catch errors at compile time
- **Intellisense:** Auto-completion in IDE
- **Documentation:** Types serve as documentation
- **Consistency:** All methods return same structure

**Alternative (URL-only pattern) - NOT RECOMMENDED:**

```typescript
// DON'T DO THIS - returns URL string, caller must fetch
buildSystemsUrl(options?: SystemQueryOptions): string {
  // ... build URL
  return url.toString();
}
```

**Recommendation:** Follow EDRQueryBuilder pattern - return typed responses.

100. **Optional vs Required Parameters:** How to type optional parameters? Partial types? Undefined allowed?

**Answer:** Use **optional properties with undefined** for query parameters:

**Pattern: Optional properties with `?`**

```typescript
interface SystemQueryOptions {
  // All parameters are optional
  bbox?: [number, number, number, number];  // Can be undefined
  datetime?: string;                        // Can be undefined
  id?: string[];                            // Can be undefined
  limit?: number;                           // Can be undefined
  // ...
}

// Method signature
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  // options itself is optional
  // All properties within options are optional
}
```

**Required vs optional parameters:**

```typescript
// Resource ID is REQUIRED (not optional)
async getSystem(
  systemId: string,  // REQUIRED - no ?
  options?: {
    datetime?: string;  // OPTIONAL
    f?: Format;         // OPTIONAL
  }
): Promise<System>

// Both resource ID and body are REQUIRED
async createSystem(
  body: SystemInput  // REQUIRED - no ?
): Promise<System>

// Parent ID is REQUIRED, options are optional
async getSubsystems(
  parentId: string,    // REQUIRED
  options?: SystemQueryOptions  // OPTIONAL
): Promise<System[]>
```

**Partial types for updates:**

```typescript
// For PATCH operations - all properties become optional
async patchSystem(
  systemId: string,          // REQUIRED
  updates: Partial<SystemInput>  // All fields optional
): Promise<System>

// Allows partial updates
patchSystem('sys1', { name: 'New Name' })  // Only update name
patchSystem('sys1', { description: 'New Description', validTime: [...] })
```

**Strict null checks:**

```typescript
// Enable in tsconfig.json
{
  "compilerOptions": {
    "strictNullChecks": true,  // Distinguish undefined from null
    "strict": true              // Enable all strict checks
  }
}
```

**Validation patterns:**

```typescript
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  // Validate optional parameters
  if (options?.limit !== undefined) {
    if (options.limit < 1 || options.limit > 10000) {
      throw new RangeError('limit must be between 1 and 10,000');
    }
  }

  if (options?.bbox !== undefined) {
    if (options.bbox.length !== 4) {
      throw new Error('bbox must have exactly 4 values');
    }
  }

  // ... build URL and fetch
}
```

**Default values:**

```typescript
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  // Provide defaults for undefined parameters
  const limit = options?.limit ?? 10;
  const offset = options?.offset ?? 0;
  const format = options?.f ?? 'geojson';

  // ... use defaults
}
```

**Key principle:** All query parameters are optional; only path parameters (resource IDs) and request bodies are required.

### S. Code Organization and Structure

**Questions:**

101. **File Structure:** Should CSAPIQueryBuilder be one file or split across multiple files? If split, how to organize?

**Answer:** Use **multiple files with modular organization**:

```
src/csapi/
  index.ts                    // Main export
  CSAPIQueryBuilder.ts        // Main class
  types/
    index.ts                  // Re-export all types
    common.ts                 // BaseQueryOptions, Link, etc.
    systems.ts                // System, SystemQueryOptions, SystemInput
    deployments.ts            // Deployment, DeploymentQueryOptions
    procedures.ts             // Procedure, ProcedureQueryOptions
    samplingFeatures.ts       // SamplingFeature, SamplingFeatureQueryOptions
    properties.ts             // Property, PropertyQueryOptions
    datastreams.ts            // DataStream, DataStreamQueryOptions
    observations.ts           // Observation, ObservationQueryOptions
    controlstreams.ts         // ControlStream, ControlStreamQueryOptions
    commands.ts               // Command, CommandQueryOptions, CommandStatus
  methods/
    index.ts                  // Re-export all methods
    systems.ts                // getSystems, getSystem, createSystem, etc.
    deployments.ts            // getDeployments, getDeployment, etc.
    procedures.ts             // getProcedures, getProcedure, etc.
    samplingFeatures.ts       // getSamplingFeatures, getSamplingFeature, etc.
    properties.ts             // getProperties, getProperty, etc.
    datastreams.ts            // getDataStreams, getDataStream, etc.
    observations.ts           // getObservations, getObservation, etc.
    controlstreams.ts         // getControlStreams, getControlStream, etc.
    commands.ts               // getCommands, getCommand, etc.
  utils/
    index.ts                  // Re-export all utils
    url-builder.ts            // buildUrl, buildQueryString, encodeValue
    validators.ts             // validateBbox, validateDatetime, validateLimit
    formatters.ts             // formatDatetime, formatBbox
  constants.ts                // DEFAULT_LIMIT, MAX_LIMIT, etc.
```

**Main class uses composition:**

```typescript
// CSAPIQueryBuilder.ts
import * as systemMethods from './methods/systems';
import * as deploymentMethods from './methods/deployments';
// ... import all methods

export class CSAPIQueryBuilder {
  constructor(private baseUrl: string) {}

  // Delegate to method modules
  getSystems = systemMethods.getSystems.bind(this);
  getSystem = systemMethods.getSystem.bind(this);
  createSystem = systemMethods.createSystem.bind(this);
  // ... bind all methods
}
```

**Each method file is self-contained:**

```typescript
// methods/systems.ts
import { System, SystemQueryOptions } from '../types/systems';
import { buildUrl } from '../utils/url-builder';

export async function getSystems(
  this: { baseUrl: string }, // 'this' context type
  options?: SystemQueryOptions
): Promise<System[]> {
  const url = buildUrl(`${this.baseUrl}/systems`, options);
  // ... fetch and parse
}
```

**Benefits:**

- **Modularity:** Easy to find and modify code for each resource type
- **Testability:** Each module can be tested independently
- **Maintainability:** Add new resource types without modifying existing files
- **Bundle splitting:** Unused resource types can be tree-shaken

102. **Helper Functions:** What helper functions are needed? URL encoding? Query string construction? Parameter validation?

**Answer:** Extract **common operations into utility functions**:

**URL Building:**

```typescript
// utils/url-builder.ts

/**
 * Build URL with query parameters
 */
export function buildUrl(
  basePath: string,
  params?: Record<string, any>
): string {
  const url = new URL(basePath);

  if (params) {
    const queryString = buildQueryString(params);
    if (queryString) {
      url.search = queryString;
    }
  }

  return url.toString();
}

/**
 * Build query string from parameters
 */
export function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) {
      continue; // Skip undefined/null
    }

    if (Array.isArray(value)) {
      // Multiple values: id=1&id=2&id=3
      value.forEach((v) => searchParams.append(key, String(v)));
    } else {
      searchParams.append(key, String(value));
    }
  }

  return searchParams.toString();
}

/**
 * Encode special characters in parameter values
 */
export function encodeValue(value: any): string {
  if (typeof value === 'string') {
    return encodeURIComponent(value);
  }
  return String(value);
}

/**
 * Build path with resource ID
 */
export function buildResourcePath(
  basePath: string,
  resourceId: string
): string {
  return `${basePath}/${encodeURIComponent(resourceId)}`;
}
```

**Validation:**

```typescript
// utils/validators.ts

/**
 * Validate bounding box
 */
export function validateBbox(bbox: number[]): void {
  if (bbox.length !== 4) {
    throw new Error('bbox must have exactly 4 values');
  }

  const [minLon, minLat, maxLon, maxLat] = bbox;

  if (minLon < -180 || minLon > 180 || maxLon < -180 || maxLon > 180) {
    throw new RangeError('Longitude must be between -180 and 180');
  }

  if (minLat < -90 || minLat > 90 || maxLat < -90 || maxLat > 90) {
    throw new RangeError('Latitude must be between -90 and 90');
  }

  if (minLon >= maxLon) {
    throw new Error('minLon must be less than maxLon');
  }

  if (minLat >= maxLat) {
    throw new Error('minLat must be less than maxLat');
  }
}

/**
 * Validate datetime parameter
 */
export function validateDatetime(datetime: string): void {
  // Check for instant
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(datetime)) {
    return; // Valid ISO 8601 instant
  }

  // Check for interval
  if (datetime.includes('/')) {
    const [start, end] = datetime.split('/');

    if (start !== '..' && !/^\d{4}-\d{2}-\d{2}/.test(start)) {
      throw new Error(`Invalid start: ${start}`);
    }

    if (end !== '..' && !/^\d{4}-\d{2}-\d{2}/.test(end)) {
      throw new Error(`Invalid end: ${end}`);
    }

    return;
  }

  // Check for special keywords
  if (['now', 'latest'].includes(datetime)) {
    return;
  }

  throw new Error(`Invalid datetime: ${datetime}`);
}

/**
 * Validate limit parameter
 */
export function validateLimit(limit: number, max = 10000): void {
  if (!Number.isInteger(limit)) {
    throw new TypeError('limit must be an integer');
  }

  if (limit < 1 || limit > max) {
    throw new RangeError(`limit must be between 1 and ${max}`);
  }
}

/**
 * Validate pagination parameters
 */
export function validatePagination(
  limit?: number,
  offset?: number,
  cursor?: string
): void {
  if (limit !== undefined) {
    validateLimit(limit);
  }

  if (offset !== undefined && cursor !== undefined) {
    throw new Error('Cannot use both offset and cursor pagination');
  }

  if (offset !== undefined) {
    if (!Number.isInteger(offset) || offset < 0) {
      throw new RangeError('offset must be a non-negative integer');
    }
  }
}
```

**Formatting:**

```typescript
// utils/formatters.ts

/**
 * Format Date to ISO 8601 string
 */
export function formatDatetime(date: Date): string {
  return date.toISOString();
}

/**
 * Format bbox to comma-separated string
 */
export function formatBbox(bbox: [number, number, number, number]): string {
  return bbox.join(',');
}

/**
 * Format array for query parameter
 */
export function formatArray<T>(values: T[]): string[] {
  return values.map((v) => String(v));
}
```

**Error handling:**

```typescript
// utils/errors.ts

/**
 * Custom error for API errors
 */
export class CSAPIError extends Error {
  constructor(
    public statusCode: number,
    public statusText: string,
    public url: string
  ) {
    super(`HTTP ${statusCode}: ${statusText}`);
    this.name = 'CSAPIError';
  }
}

/**
 * Throw error from HTTP response
 */
export async function handleResponse(response: Response): Promise<void> {
  if (!response.ok) {
    throw new CSAPIError(response.status, response.statusText, response.url);
  }
}
```

103. **Constants:** What constants should be defined? Default limits? Valid format values? Status values?

**Answer:** Define **constants for reusable values**:

```typescript
// constants.ts

/**
 * Pagination constants
 */
export const DEFAULT_LIMIT = 10;
export const MAX_LIMIT = 10000;
export const MAX_BULK_OBSERVATIONS = 10000;
export const MAX_BULK_COMMANDS = 10000;

/**
 * Format values
 */
export const FORMAT = {
  JSON: 'json',
  GEOJSON: 'geojson',
  HTML: 'html',
  SML_JSON: 'sml+json',
  SWE_JSON: 'swe+json',
  SWE_TEXT: 'swe+text',
  SWE_BINARY: 'swe+binary',
  PROTOBUF: 'proto',
} as const;

export type Format = (typeof FORMAT)[keyof typeof FORMAT];

/**
 * Command status codes
 */
export const COMMAND_STATUS = {
  PENDING: 'PENDING',
  ACCEPTED: 'ACCEPTED',
  REJECTED: 'REJECTED',
  SCHEDULED: 'SCHEDULED',
  UPDATED: 'UPDATED',
  CANCELED: 'CANCELED',
  EXECUTING: 'EXECUTING',
  FAILED: 'FAILED',
  COMPLETED: 'COMPLETED',
} as const;

export type CommandStatus =
  (typeof COMMAND_STATUS)[keyof typeof COMMAND_STATUS];

/**
 * Common query parameters
 */
export const QUERY_PARAM = {
  ID: 'id',
  Q: 'q',
  BBOX: 'bbox',
  GEOM: 'geom',
  DATETIME: 'datetime',
  LIMIT: 'limit',
  OFFSET: 'offset',
  CURSOR: 'cursor',
  FORMAT: 'f',

  // Part 2 temporal
  PHENOMENON_TIME: 'phenomenonTime',
  RESULT_TIME: 'resultTime',
  ISSUE_TIME: 'issueTime',
  EXECUTION_TIME: 'executionTime',

  // Part 2 filtering
  DATASTREAM: 'datastream',
  CONTROL_STREAM: 'controlStream',
  STATUS_CODE: 'statusCode',

  // Resource relationships
  PARENT: 'parent',
  SYSTEM: 'system',
  DEPLOYMENT: 'deployment',
  PROCEDURE: 'procedure',
  FOI: 'foi',
  OBSERVED_PROPERTY: 'observedProperty',
  CONTROLLED_PROPERTY: 'controlledProperty',
  SENDER: 'sender',

  // Flags
  RECURSIVE: 'recursive',
} as const;

/**
 * Endpoint paths
 */
export const ENDPOINT = {
  SYSTEMS: '/systems',
  DEPLOYMENTS: '/deployments',
  PROCEDURES: '/procedures',
  SAMPLING_FEATURES: '/samplingFeatures',
  PROPERTIES: '/properties',
  DATASTREAMS: '/datastreams',
  OBSERVATIONS: '/observations',
  CONTROL_STREAMS: '/controlStreams',
  COMMANDS: '/commands',
} as const;

/**
 * Special datetime values
 */
export const DATETIME_SPECIAL = {
  NOW: 'now',
  LATEST: 'latest',
} as const;

/**
 * Validation limits
 */
export const VALIDATION = {
  MIN_LONGITUDE: -180,
  MAX_LONGITUDE: 180,
  MIN_LATITUDE: -90,
  MAX_LATITUDE: 90,
  MIN_LIMIT: 1,
  MAX_LIMIT: 10000,
  MIN_OFFSET: 0,
} as const;
```

**Usage in code:**

```typescript
import {
  DEFAULT_LIMIT,
  MAX_LIMIT,
  FORMAT,
  COMMAND_STATUS,
  ENDPOINT
} from './constants';

// Use in method
async getSystems(options?: SystemQueryOptions): Promise<System[]> {
  const limit = options?.limit ?? DEFAULT_LIMIT;
  const format = options?.f ?? FORMAT.GEOJSON;

  validateLimit(limit, MAX_LIMIT);

  const url = buildUrl(
    `${this.baseUrl}${ENDPOINT.SYSTEMS}`,
    { ...options, limit, f: format }
  );

  // ... fetch
}

// Use in validation
if (statusCode && !Object.values(COMMAND_STATUS).includes(statusCode)) {
  throw new Error(`Invalid status code: ${statusCode}`);
}
```

104. **Documentation:** How to document 60-70 methods? JSDoc for each? Examples?

**Answer:** Use **comprehensive JSDoc with examples and links**:

**Method documentation pattern:**

```typescript
/**
 * Retrieve systems matching query criteria.
 *
 * @param options - Query options for filtering and pagination
 * @returns Promise resolving to array of System resources
 *
 * @throws {RangeError} If limit is outside valid range (1-10000)
 * @throws {CSAPIError} If HTTP request fails
 *
 * @example
 * // Get all systems
 * const systems = await builder.getSystems();
 *
 * @example
 * // Get systems in bounding box
 * const systems = await builder.getSystems({
 *   bbox: [-122.5, 37.7, -122.3, 37.9]
 * });
 *
 * @example
 * // Get systems with pagination
 * const systems = await builder.getSystems({
 *   limit: 50,
 *   offset: 0
 * });
 *
 * @see {@link https://example.com/csapi/systems | Systems API}
 */
async getSystems(options?: SystemQueryOptions): Promise<System[]>

/**
 * Retrieve a single system by ID.
 *
 * @param systemId - System identifier
 * @param options - Optional format parameter
 * @returns Promise resolving to System resource
 *
 * @throws {CSAPIError} If system not found (404) or request fails
 *
 * @example
 * const system = await builder.getSystem('sys123');
 *
 * @example
 * // Get system as SensorML
 * const system = await builder.getSystem('sys123', { f: 'sml+json' });
 */
async getSystem(
  systemId: string,
  options?: { f?: Format }
): Promise<System>

/**
 * Create a new system resource.
 *
 * @param body - System properties
 * @returns Promise resolving to created System with server-assigned ID
 *
 * @throws {CSAPIError} If validation fails (400) or creation fails
 *
 * @example
 * const newSystem = await builder.createSystem({
 *   name: 'Weather Station 1',
 *   description: 'Measures temperature and humidity',
 *   geometry: {
 *     type: 'Point',
 *     coordinates: [-122.4, 37.8]
 *   }
 * });
 *
 * console.log(newSystem.id);  // 'sys456' (server-assigned)
 */
async createSystem(body: SystemInput): Promise<System>
```

**Part 2 resource documentation with temporal queries:**

```typescript
/**
 * Retrieve observations matching query criteria.
 *
 * **Temporal Filtering:**
 * Use `phenomenonTime` parameter to filter by observation time:
 * - Single instant: `"2024-02-02T12:00:00Z"`
 * - Closed interval: `"2024-01-01/2024-01-31"`
 * - Open start: `"../2024-01-31"` (all observations before date)
 * - Open end: `"2024-01-01/.."` (all observations after date)
 * - Special keywords: `"now"`, `"latest"`
 *
 * **Pagination:**
 * Use cursor-based pagination for large datasets:
 * 1. Extract `cursor` from response `links` array
 * 2. Pass cursor in next request
 *
 * @param datastreamId - DataStream identifier
 * @param options - Query options for filtering and pagination
 * @returns Promise resolving to array of Observation resources
 *
 * @throws {RangeError} If limit is outside valid range (1-10000)
 * @throws {CSAPIError} If HTTP request fails
 *
 * @example
 * // Get observations for datastream
 * const observations = await builder.getObservations('ds1');
 *
 * @example
 * // Get observations in time range
 * const observations = await builder.getObservations('ds1', {
 *   phenomenonTime: '2024-01-01/2024-01-31'
 * });
 *
 * @example
 * // Get latest observations
 * const observations = await builder.getObservations('ds1', {
 *   phenomenonTime: 'latest',
 *   limit: 100
 * });
 *
 * @example
 * // Paginate with cursor
 * let cursor: string | undefined;
 * while (true) {
 *   const result = await builder.getObservationsPaginated('ds1', {
 *     limit: 1000,
 *     cursor
 *   });
 *
 *   processObservations(result.items);
 *
 *   // Extract next cursor from links
 *   const nextLink = result.links?.find(l => l.rel === 'next');
 *   if (!nextLink) break;
 *
 *   cursor = new URL(nextLink.href).searchParams.get('cursor') ?? undefined;
 * }
 *
 * @see {@link https://example.com/csapi/observations | Observations API}
 */
async getObservations(
  datastreamId: string,
  options?: ObservationQueryOptions
): Promise<Observation[]>
```

**Commands documentation with status codes:**

```typescript
/**
 * Retrieve commands matching query criteria.
 *
 * **Status Filtering:**
 * Filter by command lifecycle status:
 * - `PENDING` - Submitted, awaiting processing
 * - `ACCEPTED` - Validated and accepted
 * - `REJECTED` - Validation failed
 * - `SCHEDULED` - Scheduled for future execution
 * - `EXECUTING` - Currently executing
 * - `COMPLETED` - Successfully completed
 * - `FAILED` - Execution failed
 * - `CANCELED` - Canceled by user
 *
 * **Temporal Filtering:**
 * - `issueTime` - When command was submitted
 * - `executionTime` - When command was executed
 *
 * @param controlStreamId - ControlStream identifier
 * @param options - Query options for filtering and pagination
 * @returns Promise resolving to array of Command resources
 *
 * @example
 * // Get all commands for control stream
 * const commands = await builder.getCommands('cs1');
 *
 * @example
 * // Get pending and executing commands
 * const commands = await builder.getCommands('cs1', {
 *   statusCode: ['PENDING', 'EXECUTING']
 * });
 *
 * @example
 * // Get commands issued today
 * const today = new Date().toISOString().split('T')[0];
 * const commands = await builder.getCommands('cs1', {
 *   issueTime: `${today}/..`
 * });
 */
async getCommands(
  controlStreamId: string,
  options?: CommandQueryOptions
): Promise<Command[]>
```

**Type documentation:**

```typescript
/**
 * Query options for systems endpoint.
 */
interface SystemQueryOptions extends BaseQueryOptions {
  /**
   * Bounding box filter [minLon, minLat, maxLon, maxLat].
   * Coordinates in WGS84 (EPSG:4326).
   *
   * @example [-122.5, 37.7, -122.3, 37.9]
   */
  bbox?: [number, number, number, number];

  /**
   * Temporal filter (ISO 8601).
   *
   * @example "2024-01-01/2024-01-31" - Date range
   * @example "now/.." - From now onwards
   */
  datetime?: string;

  /**
   * Filter by parent system ID.
   */
  parent?: string[];

  /**
   * Include subsystems recursively.
   *
   * @default false
   */
  recursive?: boolean;
}
```

**Key documentation practices:**

- All public methods have JSDoc
- Include @param, @returns, @throws
- Provide 2-3 examples per method
- Link to API specification with @see
- Document temporal query patterns
- Document status codes and lifecycles
- Include @default for optional parameters

### T. Testing Strategy

**Questions:**

105. **Unit Tests:** What should be unit tested? Each URL construction method? Parameter validation? Query string encoding?

**Answer:** Unit test **individual functions in isolation** with mocked dependencies:

**URL construction tests:**

```typescript
// tests/utils/url-builder.test.ts

describe('buildUrl', () => {
  it('builds URL without parameters', () => {
    const url = buildUrl('https://api.example.com/systems');
    expect(url).toBe('https://api.example.com/systems');
  });

  it('builds URL with single parameter', () => {
    const url = buildUrl('https://api.example.com/systems', { limit: 10 });
    expect(url).toBe('https://api.example.com/systems?limit=10');
  });

  it('builds URL with array parameter', () => {
    const url = buildUrl('https://api.example.com/systems', {
      id: ['sys1', 'sys2', 'sys3'],
    });
    expect(url).toBe('https://api.example.com/systems?id=sys1&id=sys2&id=sys3');
  });

  it('skips undefined parameters', () => {
    const url = buildUrl('https://api.example.com/systems', {
      limit: 10,
      offset: undefined,
      bbox: null,
    });
    expect(url).toBe('https://api.example.com/systems?limit=10');
  });

  it('encodes special characters', () => {
    const url = buildUrl('https://api.example.com/systems', {
      q: 'temperature sensor',
    });
    expect(url).toBe('https://api.example.com/systems?q=temperature%20sensor');
  });
});
```

**Query string construction tests:**

```typescript
describe('buildQueryString', () => {
  it('handles empty parameters', () => {
    expect(buildQueryString({})).toBe('');
  });

  it('handles single parameter', () => {
    expect(buildQueryString({ limit: 10 })).toBe('limit=10');
  });

  it('handles multiple parameters', () => {
    const qs = buildQueryString({ limit: 10, offset: 0 });
    expect(qs).toMatch(/limit=10/);
    expect(qs).toMatch(/offset=0/);
  });

  it('handles array parameters', () => {
    expect(buildQueryString({ id: ['a', 'b', 'c'] })).toBe('id=a&id=b&id=c');
  });

  it('skips undefined and null', () => {
    expect(
      buildQueryString({
        limit: 10,
        offset: undefined,
        cursor: null,
      })
    ).toBe('limit=10');
  });
});
```

**Validation tests:**

```typescript
// tests/utils/validators.test.ts

describe('validateBbox', () => {
  it('accepts valid bbox', () => {
    expect(() => validateBbox([-122.5, 37.7, -122.3, 37.9])).not.toThrow();
  });

  it('rejects bbox with wrong length', () => {
    expect(() => validateBbox([-122.5, 37.7, -122.3])).toThrow(
      'bbox must have exactly 4 values'
    );
  });

  it('rejects invalid longitude', () => {
    expect(() => validateBbox([-200, 37.7, -122.3, 37.9])).toThrow(RangeError);
  });

  it('rejects invalid latitude', () => {
    expect(() => validateBbox([-122.5, -100, -122.3, 37.9])).toThrow(
      RangeError
    );
  });

  it('rejects min >= max', () => {
    expect(() => validateBbox([-122.3, 37.7, -122.5, 37.9])).toThrow(
      'minLon must be less than maxLon'
    );
  });
});

describe('validateDatetime', () => {
  it('accepts ISO 8601 instant', () => {
    expect(() => validateDatetime('2024-02-02T12:00:00Z')).not.toThrow();
  });

  it('accepts closed interval', () => {
    expect(() => validateDatetime('2024-01-01/2024-01-31')).not.toThrow();
  });

  it('accepts open start', () => {
    expect(() => validateDatetime('../2024-01-31')).not.toThrow();
  });

  it('accepts open end', () => {
    expect(() => validateDatetime('2024-01-01/..')).not.toThrow();
  });

  it('accepts special keywords', () => {
    expect(() => validateDatetime('now')).not.toThrow();
    expect(() => validateDatetime('latest')).not.toThrow();
  });

  it('rejects invalid format', () => {
    expect(() => validateDatetime('invalid')).toThrow('Invalid datetime');
  });
});

describe('validateLimit', () => {
  it('accepts valid limit', () => {
    expect(() => validateLimit(100)).not.toThrow();
  });

  it('rejects non-integer', () => {
    expect(() => validateLimit(10.5)).toThrow(TypeError);
  });

  it('rejects out of range', () => {
    expect(() => validateLimit(0)).toThrow(RangeError);
    expect(() => validateLimit(10001)).toThrow(RangeError);
  });
});
```

**Method tests (with mocked fetch):**

```typescript
// tests/methods/systems.test.ts

describe('getSystems', () => {
  let builder: CSAPIQueryBuilder;
  let fetchMock: jest.Mock;

  beforeEach(() => {
    fetchMock = jest.fn();
    global.fetch = fetchMock;
    builder = new CSAPIQueryBuilder('https://api.example.com');
  });

  it('builds correct URL for basic request', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ features: [] }),
    });

    await builder.getSystems();

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.com/systems?limit=10',
      expect.any(Object)
    );
  });

  it('builds correct URL with bbox', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ features: [] }),
    });

    await builder.getSystems({
      bbox: [-122.5, 37.7, -122.3, 37.9],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('bbox=-122.5%2C37.7%2C-122.3%2C37.9'),
      expect.any(Object)
    );
  });

  it('throws on HTTP error', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    await expect(builder.getSystems()).rejects.toThrow(CSAPIError);
  });
});
```

**What to unit test:**

- ✅ URL construction with various parameter combinations
- ✅ Query string encoding with special characters
- ✅ Parameter validation (bbox, datetime, limit, etc.)
- ✅ Array parameter handling
- ✅ Undefined/null parameter handling
- ✅ Error handling (HTTP errors, validation errors)
- ✅ Response parsing
- ❌ NOT actual HTTP requests (use mocks)
- ❌ NOT server-side behavior

106. **Integration Tests:** What should be integration tested? Full request/response cycle? Actual CSAPI server interaction?

**Answer:** Integration test **full request/response cycle with real server**:

**Test against live CSAPI server:**

```typescript
// tests/integration/systems.integration.test.ts

describe('Systems Integration', () => {
  let builder: CSAPIQueryBuilder;

  beforeAll(() => {
    const serverUrl =
      process.env.CSAPI_TEST_SERVER || 'https://test.ogc-csapi.org';
    builder = new CSAPIQueryBuilder(serverUrl);
  });

  it('retrieves systems from server', async () => {
    const systems = await builder.getSystems({ limit: 5 });

    expect(systems).toBeInstanceOf(Array);
    expect(systems.length).toBeLessThanOrEqual(5);

    if (systems.length > 0) {
      expect(systems[0]).toHaveProperty('id');
      expect(systems[0]).toHaveProperty('name');
      expect(systems[0]).toHaveProperty('links');
    }
  });

  it('filters systems by bbox', async () => {
    const systems = await builder.getSystems({
      bbox: [-180, -90, 180, 90], // World bbox
      limit: 10,
    });

    expect(systems).toBeInstanceOf(Array);

    // All systems should have geometry within bbox
    systems.forEach((system) => {
      if (system.geometry) {
        expect(system.geometry).toHaveProperty('type');
        expect(system.geometry).toHaveProperty('coordinates');
      }
    });
  });

  it('retrieves specific system by ID', async () => {
    // First get a list to get a valid ID
    const systems = await builder.getSystems({ limit: 1 });

    if (systems.length > 0) {
      const systemId = systems[0].id;
      const system = await builder.getSystem(systemId);

      expect(system.id).toBe(systemId);
      expect(system).toHaveProperty('name');
    }
  });

  it('creates, updates, and deletes system', async () => {
    // Create
    const newSystem = await builder.createSystem({
      name: 'Test System',
      description: 'Integration test',
      geometry: {
        type: 'Point',
        coordinates: [-122.4, 37.8],
      },
    });

    expect(newSystem).toHaveProperty('id');
    expect(newSystem.name).toBe('Test System');

    const systemId = newSystem.id;

    try {
      // Update
      const updated = await builder.patchSystem(systemId, {
        description: 'Updated description',
      });

      expect(updated.description).toBe('Updated description');

      // Verify update
      const retrieved = await builder.getSystem(systemId);
      expect(retrieved.description).toBe('Updated description');
    } finally {
      // Clean up - always delete even if test fails
      await builder.deleteSystem(systemId);

      // Verify deletion
      await expect(builder.getSystem(systemId)).rejects.toThrow(CSAPIError);
    }
  });
});
```

**Test Part 2 resources:**

```typescript
// tests/integration/observations.integration.test.ts

describe('Observations Integration', () => {
  let builder: CSAPIQueryBuilder;
  let datastreamId: string;

  beforeAll(async () => {
    builder = new CSAPIQueryBuilder(process.env.CSAPI_TEST_SERVER!);

    // Get a datastream ID for testing
    const datastreams = await builder.getDataStreams({ limit: 1 });
    if (datastreams.length === 0) {
      throw new Error('No datastreams available for testing');
    }
    datastreamId = datastreams[0].id;
  });

  it('retrieves observations for datastream', async () => {
    const observations = await builder.getObservations(datastreamId, {
      limit: 10,
    });

    expect(observations).toBeInstanceOf(Array);

    observations.forEach((obs) => {
      expect(obs).toHaveProperty('phenomenonTime');
      expect(obs).toHaveProperty('result');
    });
  });

  it('filters observations by phenomenonTime', async () => {
    const now = new Date().toISOString();
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

    const observations = await builder.getObservations(datastreamId, {
      phenomenonTime: `${yesterday}/${now}`,
      limit: 100,
    });

    expect(observations).toBeInstanceOf(Array);

    // All observations should be within time range
    observations.forEach((obs) => {
      const obsTime = new Date(obs.phenomenonTime);
      expect(obsTime.getTime()).toBeGreaterThanOrEqual(
        new Date(yesterday).getTime()
      );
      expect(obsTime.getTime()).toBeLessThanOrEqual(new Date(now).getTime());
    });
  });

  it('paginates observations with cursor', async () => {
    const page1 = await builder.getObservationsPaginated(datastreamId, {
      limit: 10,
    });

    expect(page1.items).toBeInstanceOf(Array);

    if (page1.links) {
      const nextLink = page1.links.find((l) => l.rel === 'next');

      if (nextLink) {
        const cursor = new URL(nextLink.href).searchParams.get('cursor');

        const page2 = await builder.getObservationsPaginated(datastreamId, {
          limit: 10,
          cursor: cursor!,
        });

        expect(page2.items).toBeInstanceOf(Array);

        // Pages should have different observations
        const page1Ids = page1.items.map((o) => o.id);
        const page2Ids = page2.items.map((o) => o.id);
        expect(page1Ids).not.toEqual(page2Ids);
      }
    }
  });

  it('creates and deletes observation', async () => {
    const newObs = await builder.createObservation(datastreamId, {
      phenomenonTime: new Date().toISOString(),
      result: 42.5,
    });

    expect(newObs).toHaveProperty('id');
    expect(newObs.result).toBe(42.5);

    // Clean up
    await builder.deleteObservation(newObs.id);
  });
});
```

**What to integration test:**

- ✅ Full request/response cycle with real server
- ✅ Actual HTTP requests and responses
- ✅ CRUD operations (create, read, update, delete)
- ✅ Query parameter filtering
- ✅ Pagination (offset and cursor)
- ✅ Temporal queries
- ✅ Bulk operations
- ✅ Error responses from server
- ❌ NOT URL construction logic (unit tested)
- ❌ NOT parameter validation (unit tested)

**Test environment:**

```typescript
// jest.integration.config.js
module.exports = {
  testMatch: ['**/*.integration.test.ts'],
  testTimeout: 30000, // 30 seconds for network requests
  maxWorkers: 1, // Run serially to avoid conflicts
  setupFiles: ['<rootDir>/tests/integration/setup.ts'],
};

// tests/integration/setup.ts
if (!process.env.CSAPI_TEST_SERVER) {
  console.warn('CSAPI_TEST_SERVER not set, using default');
  process.env.CSAPI_TEST_SERVER = 'https://test.ogc-csapi.org';
}
```

107. **Test Organization:** How to organize tests for 9 resource types? Separate test files per resource? Single test file with sections?

**Answer:** Use **separate test files per resource type + shared utilities**:

```
tests/
  unit/
    utils/
      url-builder.test.ts       // URL construction tests
      validators.test.ts        // Validation tests
      formatters.test.ts        // Formatting tests
    methods/
      systems.test.ts           // Systems method tests
      deployments.test.ts       // Deployments method tests
      procedures.test.ts        // Procedures method tests
      samplingFeatures.test.ts  // Sampling features method tests
      properties.test.ts        // Properties method tests
      datastreams.test.ts       // DataStreams method tests
      observations.test.ts      // Observations method tests
      controlstreams.test.ts    // ControlStreams method tests
      commands.test.ts          // Commands method tests
    types/
      query-options.test.ts     // Type validation tests

  integration/
    setup.ts                    // Test server configuration
    systems.integration.test.ts
    deployments.integration.test.ts
    procedures.integration.test.ts
    samplingFeatures.integration.test.ts
    properties.integration.test.ts
    datastreams.integration.test.ts
    observations.integration.test.ts
    controlstreams.integration.test.ts
    commands.integration.test.ts

  fixtures/
    mock-systems.ts             // Mock system data
    mock-deployments.ts         // Mock deployment data
    mock-observations.ts        // Mock observation data
    mock-commands.ts            // Mock command data
    mock-responses.ts           // Mock HTTP responses

  helpers/
    fetch-mock.ts               // Mock fetch implementation
    test-server.ts              // Test server utilities
    assertions.ts               // Custom assertions
```

**Benefits:**

- **Modularity:** Easy to find tests for specific resource
- **Parallel execution:** Tests run in parallel for speed
- **Maintainability:** Add new resource tests without modifying existing files
- **Clarity:** Each file focused on single resource type

**Shared test utilities:**

```typescript
// tests/helpers/fetch-mock.ts

export function createFetchMock() {
  const mock = jest.fn();

  mock.mockSuccess = (data: any) => {
    mock.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => data,
    });
  };

  mock.mockError = (status: number, statusText: string) => {
    mock.mockResolvedValue({
      ok: false,
      status,
      statusText,
    });
  };

  return mock;
}

// tests/helpers/assertions.ts

export function expectValidSystem(system: any) {
  expect(system).toHaveProperty('id');
  expect(system).toHaveProperty('name');
  expect(system).toHaveProperty('links');
  expect(Array.isArray(system.links)).toBe(true);
}

export function expectValidObservation(observation: any) {
  expect(observation).toHaveProperty('phenomenonTime');
  expect(observation).toHaveProperty('result');
}
```

**Test suite structure:**

```typescript
// tests/unit/methods/systems.test.ts

import { CSAPIQueryBuilder } from '../../../src/CSAPIQueryBuilder';
import { createFetchMock } from '../../helpers/fetch-mock';
import { expectValidSystem } from '../../helpers/assertions';
import { mockSystems } from '../../fixtures/mock-systems';

describe('Systems Methods', () => {
  let builder: CSAPIQueryBuilder;
  let fetchMock: jest.Mock;

  beforeEach(() => {
    fetchMock = createFetchMock();
    global.fetch = fetchMock;
    builder = new CSAPIQueryBuilder('https://api.example.com');
  });

  describe('getSystems', () => {
    // Multiple tests for getSystems
  });

  describe('getSystem', () => {
    // Multiple tests for getSystem
  });

  describe('createSystem', () => {
    // Multiple tests for createSystem
  });

  // ... other methods
});
```

108. **Mock Data:** What mock data for testing? Mock collection info? Mock server responses?

**Answer:** Create **comprehensive mock fixtures** for testing:

**Mock systems:**

```typescript
// tests/fixtures/mock-systems.ts

export const mockSystem = {
  id: 'sys1',
  name: 'Weather Station 1',
  description: 'Measures temperature and humidity',
  validTime: ['2024-01-01T00:00:00Z', null],
  geometry: {
    type: 'Point',
    coordinates: [-122.4, 37.8],
  },
  properties: {
    manufacturer: 'Acme Corp',
    model: 'WS-100',
  },
  links: [
    { rel: 'self', href: 'https://api.example.com/systems/sys1' },
    {
      rel: 'datastreams',
      href: 'https://api.example.com/systems/sys1/datastreams',
    },
  ],
};

export const mockSystems = [
  mockSystem,
  {
    id: 'sys2',
    name: 'Weather Station 2',
    description: 'Another station',
    geometry: {
      type: 'Point',
      coordinates: [-122.5, 37.9],
    },
    links: [{ rel: 'self', href: 'https://api.example.com/systems/sys2' }],
  },
];

export const mockSystemCollection = {
  items: mockSystems,
  links: [
    { rel: 'self', href: 'https://api.example.com/systems' },
    { rel: 'next', href: 'https://api.example.com/systems?offset=10' },
  ],
  numberMatched: 42,
  numberReturned: 2,
};
```

**Mock observations:**

```typescript
// tests/fixtures/mock-observations.ts

export const mockObservation = {
  id: 'obs1',
  phenomenonTime: '2024-02-02T12:00:00Z',
  resultTime: '2024-02-02T12:00:05Z',
  result: 22.5,
  resultQuality: {
    quality: 'good',
  },
  parameters: {},
};

export const mockObservations = [
  mockObservation,
  {
    id: 'obs2',
    phenomenonTime: '2024-02-02T12:01:00Z',
    resultTime: '2024-02-02T12:01:05Z',
    result: 22.6,
  },
  {
    id: 'obs3',
    phenomenonTime: '2024-02-02T12:02:00Z',
    resultTime: '2024-02-02T12:02:05Z',
    result: 22.7,
  },
];

export const mockObservationCollection = {
  items: mockObservations,
  links: [
    {
      rel: 'self',
      href: 'https://api.example.com/datastreams/ds1/observations',
    },
    {
      rel: 'next',
      href: 'https://api.example.com/datastreams/ds1/observations?cursor=abc123',
    },
  ],
  numberMatched: 1000,
  numberReturned: 3,
};
```

**Mock commands:**

```typescript
// tests/fixtures/mock-commands.ts

export const mockCommand = {
  id: 'cmd1',
  issueTime: '2024-02-02T12:00:00Z',
  executionTime: '2024-02-02T12:00:10Z',
  parameters: {
    angle: 45,
    speed: 10,
  },
  priority: 5,
  status: [
    {
      id: 'status1',
      code: 'PENDING',
      time: '2024-02-02T12:00:00Z',
    },
    {
      id: 'status2',
      code: 'EXECUTING',
      time: '2024-02-02T12:00:10Z',
    },
    {
      id: 'status3',
      code: 'COMPLETED',
      time: '2024-02-02T12:00:15Z',
    },
  ],
  result: [
    {
      id: 'result1',
      time: '2024-02-02T12:00:15Z',
      value: {
        success: true,
        message: 'Command completed successfully',
      },
    },
  ],
  links: [
    { rel: 'self', href: 'https://api.example.com/commands/cmd1' },
    { rel: 'status', href: 'https://api.example.com/commands/cmd1/status' },
    { rel: 'result', href: 'https://api.example.com/commands/cmd1/result' },
  ],
};

export const mockCommands = [mockCommand];
```

**Mock HTTP responses:**

```typescript
// tests/fixtures/mock-responses.ts

export const mockResponse = (data: any, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  statusText: status === 200 ? 'OK' : 'Error',
  json: async () => data,
  text: async () => JSON.stringify(data),
});

export const mockErrorResponse = (status: number, message: string) => ({
  ok: false,
  status,
  statusText: message,
  json: async () => ({
    type: 'error',
    title: message,
    status,
    detail: `Error ${status}: ${message}`,
  }),
});

export const mock404Response = () => mockErrorResponse(404, 'Not Found');
export const mock400Response = () => mockErrorResponse(400, 'Bad Request');
export const mock500Response = () =>
  mockErrorResponse(500, 'Internal Server Error');
```

**Mock DataStreams and ControlStreams:**

```typescript
// tests/fixtures/mock-datastreams.ts

export const mockDataStream = {
  id: 'ds1',
  name: 'Temperature Observations',
  description: 'Temperature readings from sensor',
  system: 'sys1',
  outputName: 'temperature',
  schema: {
    obsFormat: 'application/json',
    resultSchema: {
      type: 'DataRecord',
      fields: [
        {
          name: 'temperature',
          type: 'Quantity',
          uom: 'Cel',
          definition: 'http://sweet.jpl.nasa.gov/ontology/property/Temperature',
        },
      ],
    },
  },
  links: [
    { rel: 'self', href: 'https://api.example.com/datastreams/ds1' },
    {
      rel: 'observations',
      href: 'https://api.example.com/datastreams/ds1/observations',
    },
    { rel: 'schema', href: 'https://api.example.com/datastreams/ds1/schema' },
  ],
};

// tests/fixtures/mock-controlstreams.ts

export const mockControlStream = {
  id: 'cs1',
  name: 'Pan/Tilt Control',
  description: 'Camera pan and tilt control',
  system: 'sys1',
  inputName: 'pan_tilt',
  schema: {
    cmdFormat: 'application/json',
    parametersSchema: {
      type: 'DataRecord',
      fields: [
        {
          name: 'pan',
          type: 'Quantity',
          uom: 'deg',
          constraint: { interval: [-180, 180] },
        },
        {
          name: 'tilt',
          type: 'Quantity',
          uom: 'deg',
          constraint: { interval: [-90, 90] },
        },
      ],
    },
  },
  links: [
    { rel: 'self', href: 'https://api.example.com/controlstreams/cs1' },
    {
      rel: 'commands',
      href: 'https://api.example.com/controlstreams/cs1/commands',
    },
    {
      rel: 'schema',
      href: 'https://api.example.com/controlstreams/cs1/schema',
    },
  ],
};
```

**Usage in tests:**

```typescript
import { mockSystems, mockSystemCollection } from '../fixtures/mock-systems';
import { mockResponse } from '../fixtures/mock-responses';

it('retrieves systems', async () => {
  fetchMock.mockResolvedValue(mockResponse(mockSystemCollection));

  const systems = await builder.getSystems();

  expect(systems).toEqual(mockSystems);
});
```

---

## 5. Research Tasks

### Task 1: Study EDRQueryBuilder Implementation

**Objective:** Understand the EDRQueryBuilder pattern in depth to apply it to CSAPIQueryBuilder.

**Actions:**

- [x] Read querybuilder-pattern-analysis.md completely
- [x] Study EDRQueryBuilder source code in upstream repository
- [x] Document factory method implementation pattern
- [x] Document caching strategy
- [x] Document metadata encapsulation pattern
- [x] Document method organization (URL building vs execution)
- [x] Identify reusable patterns for CSAPI

**Deliverable:** Complete answers to Section A questions (Questions 1-7) ✅

---

### Task 2: Design CSAPI URL Construction Architecture

**Objective:** Define all 60-70 URL patterns for CSAPI resources and design URL construction logic.

**Actions:**

- [x] Read OGC API - Connected Systems Part 1 OpenAPI specification
- [x] Read OGC API - Connected Systems Part 2 OpenAPI specification
- [x] Extract ALL endpoint paths from OpenAPI specs
- [x] Categorize endpoints: canonical, nested, schema, special-purpose
- [x] Design query string assembly logic
- [x] Design parameter encoding logic (arrays, spatial, temporal)
- [x] Document all URL patterns with examples

**Deliverable:** Complete answers to Section C questions (Questions 13-18) ✅

---

### Task 3: Define CSAPI Query Parameter Support

**Objective:** Document ALL query parameters for CSAPI and design parameter handling logic.

**Actions:**

- [x] Read csapi-implementation-guide.md "Complete Query Parameter Support" section
- [x] Read OGC API - Common specification for standard parameters
- [x] Read CSAPI Part 1 specification for Part 1 parameters
- [x] Read CSAPI Part 2 specification for Part 2 parameters
- [x] Document parameter syntax (value formats, encoding)
- [x] Document parameter combinations (AND logic, multiple IDs)
- [x] Document validation requirements
- [x] Design parameter interface types

**Deliverable:** Complete answers to Sections E, F, G, H questions (Questions 24-50) ✅

---

### Task 4: Design Methods for Each Resource Type

**Objective:** Design method signatures and URL patterns for all 9 CSAPI resource types.

**Actions:**

- [x] For each resource type (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands):
  - [x] List ALL endpoints from OpenAPI specs
  - [x] Define method signatures (parameters, return types)
  - [x] Document query parameters supported
  - [x] Document CRUD operations supported
  - [x] Document special endpoints (schema, status, result, feasibility)
  - [x] Document pagination support
  - [x] Document format negotiation
- [x] Design method naming convention
- [x] Design code reuse strategy (helper methods)

**Deliverable:** Complete answers to Sections I-Q questions (Questions 51-96) ✅

---

### Task 5: Design TypeScript Type System

**Objective:** Define TypeScript interfaces and types for CSAPIQueryBuilder.

**Actions:**

- [x] Read typescript-types-analysis.md from upstream research
- [x] Design query parameter interfaces (per resource type)
- [x] Design request body types (GeoJSON, SensorML, observations, commands)
- [x] Design response types (if QueryBuilder executes requests)
- [x] Design optional vs required parameter handling
- [x] Document type definitions

**Deliverable:** Complete answers to Section R questions (Questions 97-100) ✅

---

### Task 6: Plan Implementation and Testing

**Objective:** Create implementation checklist and testing strategy.

**Actions:**

- [x] Design file organization (single file vs multiple files)
- [x] Identify helper functions needed
- [x] Define constants (limits, formats, statuses)
- [x] Design documentation approach (JSDoc examples)
- [x] Design unit testing strategy (what to test, how to organize)
- [x] Design integration testing strategy (mock server vs real server)
- [x] Estimate implementation timeline (likely 2-3 weeks for 10k-14k lines)

**Deliverable:** Complete answers to Sections S-T questions (Questions 101-108) ✅

---

## 6. Development Standards Reference

All implementation work for this component must follow the standards documented in:

**[csapi-implementation-guide.md - Development Standards](../../../planning/csapi-implementation-guide.md#development-standards)**

Key standards include:

- Code style and formatting conventions
- Testing requirements and coverage expectations
- Documentation standards (JSDoc, inline comments)
- Error handling patterns
- TypeScript usage guidelines
- Naming conventions (classes, methods, variables, files)
- File organization principles

---

## 7. Success Criteria

This research phase is complete when:

- [x] All 108 critical research questions answered with detailed findings
- [x] EDRQueryBuilder pattern fully documented and understood
- [x] All 60-70 CSAPI URL patterns documented with examples
- [x] All query parameters documented with syntax and validation rules
- [x] Method signatures designed for all 9 resource types
- [x] TypeScript type definitions designed
- [x] Code organization and file structure decided
- [x] Testing strategy documented (unit + integration)
- [x] Implementation checklist created with timeline estimate
- [x] All research tasks completed and checked off
- [ ] Analysis document created with comprehensive findings
- [x] Ready to begin implementation with clear specifications

---

## 8. Dependencies

### Upstream Research Required

- querybuilder-pattern-analysis.md (EDRQueryBuilder study)
- url-building-analysis.md (URL construction patterns)
- typescript-types-analysis.md (Type system design)
- csapi-architecture-analysis.md (Single-class design rationale)

### Specifications Required

- OGC API - Connected Systems Part 1 (Systems, Deployments, Procedures, Sampling Features, Properties)
- OGC API - Connected Systems Part 2 (DataStreams, Observations, Control Streams, Commands)
- OGC API - Common (Standard query parameters: bbox, datetime, limit, offset, f)
- ISO 8601 (Temporal parameter syntax)

### Previous Components Required

- Component 1: OgcApiEndpoint Integration (factory method pattern for `endpoint.csapi()`)
- Component 2: Conformance Reader (determines if CSAPI is supported)
- Component 3: Collections Reader (provides collection info to QueryBuilder)

### Informs Downstream Components

- Component 5-8: Format handlers (parse the response structures QueryBuilder requests)
- Component 9-12: Infrastructure extensions (validate URLs and parameters QueryBuilder constructs)

---

## 9. Deliverables

### Research Plan (This Document)

- 10 sections covering all aspects of CSAPIQueryBuilder research
- 108 critical research questions requiring answers
- 6 research tasks with detailed action items
- Success criteria checklist
- Dependencies mapping

### Analysis Report (To Be Created)

**File:** `csapiquerybuilder-analysis.md`

**Sections:**

1. **Executive Summary:** High-level findings and design decisions
2. **EDRQueryBuilder Pattern Analysis:** Factory method, caching, metadata encapsulation, lifecycle
3. **Single-Class Architecture Design:** Method organization for 9 resource types, code reuse strategy
4. **URL Construction Patterns:** All 60-70 URL patterns with examples and documentation
5. **Query Parameter Reference:** Complete parameter documentation (syntax, validation, combinations)
6. **Resource Type Methods:** Detailed design for each of 9 resource types (endpoints, methods, parameters, CRUD)
7. **TypeScript Type Definitions:** Interfaces and types for parameters, bodies, responses
8. **Code Organization:** File structure, helper functions, constants, documentation approach
9. **Testing Strategy:** Unit test requirements, integration test requirements, test organization
10. **Implementation Checklist:** Phased implementation plan with timeline estimate (2-3 weeks)

**Appendices:**

- Appendix A: Complete URL Pattern Catalog (all 60-70 patterns)
- Appendix B: Complete Query Parameter Catalog (all parameters with syntax)
- Appendix C: Method Signature Reference (all methods across 9 resource types)
- Appendix D: Code Reuse Patterns (helper functions and abstractions)

**Expected Length:** 2000-3000 lines (significantly larger than previous component analyses due to scope)

---

## 10. Timeline Estimate

### Research Phase (This Document)

- **Duration:** 2-3 days
- **Effort:** Study upstream patterns, read specifications, document 60-70 URL patterns, design 9 resource type method groups

### Analysis Phase (Next Document)

- **Duration:** 2-3 days
- **Effort:** Create comprehensive analysis document, design all methods, document all parameters, create implementation checklist

### Implementation Phase (After Research Complete)

- **Duration:** 2-3 weeks
- **Effort:** Implement ~10k-14k lines of code, 60-70 URL patterns, 9 resource types, comprehensive testing

**Total Time to Complete Component 4:** ~3-4 weeks (research + implementation + testing)

**Note:** This is 5-10x longer than Components 1-3 due to scope (70% of total code volume).

---

## Notes

- This is the most complex component in the entire 12-component design
- Represents ~70% of total new code volume (~10k-14k lines)
- Contains methods for 9 resource types within one class (not 9 separate classes)
- Implements 60-70 unique URL patterns with full CRUD operations
- Defines interfaces that all downstream handlers and validators depend on
- Follows EDRQueryBuilder pattern from upstream PR #114
- Success depends on thorough research of upstream patterns and CSAPI specifications
- Implementation will require careful code organization to avoid duplication across resource types
- Testing strategy must cover all 60-70 URL patterns and all query parameter combinations
- Timeline estimate reflects significantly larger scope than previous components

---

**Status:** ✅ COMPLETE - All 108 research questions answered
**Next Step:** Create csapiquerybuilder-analysis.md document and begin implementation
