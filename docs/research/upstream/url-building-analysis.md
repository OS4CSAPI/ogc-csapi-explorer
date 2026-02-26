# URL Building Architecture Analysis

**Purpose:** Document the URL building patterns and practices used in ogc-client.

**Context:** CSAPI needs to build URLs for 9 resource types with nested paths and query parameters. Understanding upstream patterns ensures consistency.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [Base URL Strategy](#2-base-url-strategy)
3. [Query Parameter Assembly](#3-query-parameter-assembly)
4. [URL Encoding](#4-url-encoding)
5. [Parameter Modeling](#5-parameter-modeling)
6. [Array Parameters](#6-array-parameters)
7. [Base Path Construction](#7-base-path-construction)
8. [Resource Path Structure](#8-resource-path-structure)
9. [URL Builder Utilities](#9-url-builder-utilities)
10. [Avoiding Duplication](#10-avoiding-duplication)
11. [Sub-Resource URL Pattern](#11-sub-resource-url-pattern)
12. [CSAPI URL Building Strategy](#12-csapi-url-building-strategy)

---

## 1. Overview

### Core Principle: Links Over Construction

**ogc-client follows the OGC API hypermedia principle:**

✅ **Do:** Extract URLs from link relations

```typescript
const url = getLinkUrl(collection, 'items', baseUrl);
```

❌ **Don't:** Construct URLs manually

```typescript
const url = `${baseUrl}/collections/${id}/items`; // Fragile, non-standard
```

### Why This Matters

1. **Flexibility:** Server can use any URL structure
2. **Robustness:** Works with non-standard implementations
3. **Standards Compliance:** OGC APIs are hypermedia-driven
4. **Future-Proof:** Changes to server paths don't break client

### URL Building Locations

**Two main contexts:**

1. **Endpoint Class** (`src/ogc-api/endpoint.ts`)
   - Builds URLs for collection metadata, items, tilesets
   - Uses link-utils extensively
2. **QueryBuilder Classes** (e.g., `src/ogc-api/edr/url_builder.ts`)
   - Builds API-specific query URLs
   - Gets base URLs from collection metadata
   - Adds query parameters

---

## 2. Base URL Strategy

### No Base URL Builder Class

**Finding:** There is **NO** base URL builder class in ogc-client.

**Why?**

- Native JavaScript `URL` API is sufficient
- Link-based navigation eliminates most URL construction
- Each QueryBuilder handles its own URL building inline

### URL Sources

**URLs come from three sources:**

1. **Constructor Parameter** (endpoint base URL)

   ```typescript
   const endpoint = new OgcApiEndpoint('https://api.example.com');
   ```

2. **Link Relations** (most common)

   ```typescript
   const itemsUrl = getLinkUrl(collection, 'items', baseUrl);
   ```

3. **Collection Metadata** (for query types)
   ```typescript
   const queryUrl = this.collection.data_queries?.position?.link.href;
   ```

### Native URL API Usage

**All URL building uses JavaScript's built-in `URL` class:**

```typescript
// Create URL from string
const url = new URL('https://api.example.com/collections/foo/items');

// Or with base
const url = new URL('/collections/foo/items', 'https://api.example.com');

// Add query parameters
url.searchParams.set('limit', '10');
url.searchParams.set('bbox', '-180,-90,180,90');

// Get final URL
const finalUrl = url.toString();
// Result: https://api.example.com/collections/foo/items?limit=10&bbox=-180,-90,180,90
```

### Pattern: Extract, Don't Construct

**Typical flow:**

```typescript
// 1. Get URL from link
const baseUrl = getLinkUrl(collectionDoc, 'items', this.baseUrl);

// 2. Create URL object
const url = new URL(baseUrl);

// 3. Add parameters
url.searchParams.set('limit', options.limit.toString());

// 4. Return string
return url.toString();
```

---

## 3. Query Parameter Assembly

### Using searchParams API

**All parameter assembly uses `URL.searchParams`:**

```typescript
const url = new URL(baseUrl);

// Set individual parameters
url.searchParams.set('limit', '10');
url.searchParams.set('offset', '0');
url.searchParams.set('bbox', '-180,-90,180,90');

// Result: ?limit=10&offset=0&bbox=-180,-90,180,90
```

### Conditional Parameter Addition

**Pattern: Check before setting**

```typescript
getCollectionItemsUrl(collectionId: string, options: {...}): Promise<string> {
  // ... get base URL

  // Add only provided parameters
  if (options.limit !== undefined)
    url.searchParams.set('limit', options.limit.toString());

  if (options.offset !== undefined)
    url.searchParams.set('offset', options.offset.toString());

  if (options.skipGeometry !== undefined)
    url.searchParams.set('skipGeometry', options.skipGeometry.toString());

  if (options.sortBy !== undefined)
    url.searchParams.set('sortby', options.sortBy.join(','));

  if (options.properties !== undefined)
    url.searchParams.set('properties', options.properties.join(','));

  if (options.extent?.length > 0)
    url.searchParams.set('bbox', options.extent.join(','));

  return url.toString();
}
```

**Key points:**

- Check `!== undefined` (not just truthiness)
- Convert to string explicitly
- Join arrays with comma
- Check array length before adding

### Parameter Type Conversions

**Common conversions:**

```typescript
// Number to string
url.searchParams.set('limit', options.limit.toString());

// Boolean to string
url.searchParams.set('skipGeometry', options.skipGeometry.toString());

// Array to comma-separated string
url.searchParams.set('properties', options.properties.join(','));

// Date to ISO string
url.searchParams.set('datetime', dateTime.toISOString());

// Range to ISO interval
url.searchParams.set('datetime', `${start.toISOString()}/${end.toISOString()}`);
```

### Special Cases: DateTime

**Single datetime:**

```typescript
if (options.dateTime instanceof Date) {
  url.searchParams.set('datetime', options.dateTime.toISOString());
}
```

**DateTime range:**

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

**Results:**

- Single: `datetime=2024-01-01T00:00:00.000Z`
- Range: `datetime=2024-01-01T00:00:00.000Z/2024-12-31T23:59:59.999Z`
- Open start: `datetime=../2024-12-31T23:59:59.999Z`
- Open end: `datetime=2024-01-01T00:00:00.000Z/..`

### Format Negotiation

**Pattern: Check links for format, fallback to f parameter**

```typescript
getCollectionItemsUrl(collectionId, options): Promise<string> {
  const itemLinks = getLinks(collectionDoc, 'items', undefined, true);

  let url: URL;

  if (options.asJson) {
    // Try JSON-FG, GeoJSON, or JSON
    const linkWithFormat =
      itemLinks.find((link) => isMimeTypeJsonFg(link.type)) ||
      itemLinks.find((link) => isMimeTypeGeoJson(link.type)) ||
      itemLinks.find((link) => isMimeTypeJson(link.type));

    if (linkWithFormat) {
      url = new URL(linkWithFormat.href, baseUrl);
    } else {
      url = new URL(itemLinks[0].href, baseUrl);
    }
  } else if (options.outputFormat) {
    // Try to find link with specific format
    const linkWithFormat = itemLinks.find(
      (link) => link.type === options.outputFormat
    );

    if (linkWithFormat) {
      url = new URL(linkWithFormat.href, baseUrl);
    } else {
      // Fallback: use f parameter
      url = new URL(itemLinks[0].href, baseUrl);
      url.searchParams.set('f', options.outputFormat);
    }
  } else {
    url = new URL(itemLinks[0].href, baseUrl);
  }

  // ... add other parameters

  return url.toString();
}
```

**Strategy:**

1. Look for link with desired format type
2. If found, use that link's URL
3. If not found, use default link and add `f` parameter
4. Add remaining query parameters

---

## 4. URL Encoding

### Automatic Encoding

**Key finding:** ogc-client does **NOT** manually encode URLs.

**Why?** JavaScript's `URL` class handles encoding automatically.

### Examples

```typescript
// Spaces encoded automatically
url.searchParams.set('coords', 'POINT(-73.935242 40.730610)');
// Result: ?coords=POINT%28-73.935242%2040.730610%29

// Special characters encoded
url.searchParams.set('filter', 'name="New York"');
// Result: ?filter=name%3D%22New%20York%22

// Commas preserved (used for arrays)
url.searchParams.set('bbox', '-180,-90,180,90');
// Result: ?bbox=-180,-90,180,90

// UTF-8 characters encoded
url.searchParams.set('query', 'café');
// Result: ?query=caf%C3%A9
```

### Manual Encoding Edge Case

**Found one instance in endpoint.ts:**

```typescript
if (options.query !== undefined)
  url.search += (url.search ? '&' : '') + encodeURI(options.query);
```

**Context:** Freeform query string appended to URL.

**Why manual?** `options.query` is already a query string, not a single parameter.

**Example:**

```typescript
options.query = 'foo=bar&baz=qux';
// Becomes: ?limit=10&foo=bar&baz=qux
```

**Note:** This is the exception, not the rule. Use searchParams for normal parameters.

### No Need for Encoding Utilities

**Conclusion:** No URL encoding utilities needed. Use native `URL` API.

---

## 5. Parameter Modeling

### Required vs Optional Parameters

**Pattern: Function signature separates them**

```typescript
// EDR example
buildPositionDownloadUrl(
  coords: { lon: number; lat: number },  // REQUIRED - direct parameter
  optional_params: optionalPositionParams = {}  // OPTIONAL - options object
): string
```

**Endpoint example:**

```typescript
getCollectionItems(
  collectionId: string,      // REQUIRED
  limit: number = 10,        // OPTIONAL with default
  offset: number = 0,        // OPTIONAL with default
  skipGeometry: boolean = null,  // OPTIONAL nullable
  sortBy: string[] = null,   // OPTIONAL nullable
  boundingBox: BoundingBox = null,  // OPTIONAL nullable
  properties: string[] = null,  // OPTIONAL nullable
  dateTime: DateTimeParameter = null,  // OPTIONAL nullable
  query: string = null       // OPTIONAL nullable
): Promise<OgcApiCollectionItem[]>
```

**Modern endpoint pattern:**

```typescript
getCollectionItemsUrl(
  collectionId: string,      // REQUIRED - always needed
  options: {                 // OPTIONAL - destructured object
    query?: string;
    asJson?: boolean;
    outputFormat?: MimeType;
    limit?: number;
    offset?: number;
    outputCrs?: CrsCode;
    extent?: BoundingBox;
    extentCrs?: CrsCode;
    skipGeometry?: boolean;
    sortBy?: string[];
    properties?: string[];
    dateTime?: DateTimeParameter;
  } = {}
): Promise<string>
```

**Evolution:** Older code uses many parameters, newer code uses options object.

### Type Definitions for Parameters

**Define interfaces for complex parameter sets:**

```typescript
// EDR parameter interfaces
export interface optionalPositionParams {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: number | [number, number];
  crs?: CrsCode;
  f?: string;
}

export interface optionalAreaParams {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: number | [number, number];
  crs?: CrsCode;
  f?: string;
}

export interface optionalCubeParams {
  datetime?: DateTimeParameter;
  parameter_name?: string[];
  z?: number | [number, number];
  crs?: CrsCode;
  f?: string;
}
```

**Benefits:**

- Type safety at compile time
- IDE autocomplete
- Documentation via types
- Reusable across methods

### Default Values

**Pattern: Empty object default for options**

```typescript
buildPositionDownloadUrl(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}  // Default empty
): string {
  // Can safely check optional_params.datetime without null check
  if (optional_params.datetime !== undefined) {
    // ...
  }
}
```

**Don't use `null` defaults for options objects** - use `{}`.

---

## 6. Array Parameters

### Comma-Separated Encoding

**Standard pattern: Join with comma**

```typescript
// Properties array
if (options.properties !== undefined)
  url.searchParams.set('properties', options.properties.join(','));

// SortBy array
if (options.sortBy !== undefined)
  url.searchParams.set('sortby', options.sortBy.join(','));

// Parameter names
if (optional_params.parameter_name) {
  url.searchParams.set(
    'parameter-name',
    optional_params.parameter_name.join(',')
  );
}
```

**Results:**

- `properties=name,description,geometry`
- `sortby=name,date`
- `parameter-name=temperature,humidity,pressure`

### BBox as Array

**BBox is special - already formatted as comma-separated numbers:**

```typescript
export type BoundingBox = number[];

// Usage
if (options.extent?.length > 0)
  url.searchParams.set('bbox', options.extent.join(','));

// Example
const bbox: BoundingBox = [-180, -90, 180, 90];
// Result: ?bbox=-180,-90,180,90
```

### Z-Axis Range

**Can be single value or range:**

```typescript
export type zParameter = number | [number, number];

// Helper function
function zParameterToString(z: number | [number, number]): string {
  if (Array.isArray(z)) {
    return z.join('/');
  }
  return z.toString();
}

// Usage
if (optional_params.z !== undefined)
  url.searchParams.set('z', zParameterToString(optional_params.z));

// Results:
// z=100 (single value)
// z=0/1000 (range)
```

### Validation Before Joining

**Pattern: Validate array contents before encoding**

```typescript
if (optional_params.parameter_name) {
  // Validate each parameter exists
  for (const param of optional_params.parameter_name) {
    if (!this.supported_parameters[param]) {
      throw new Error(
        `The following parameter name does not exist on this collection: '${param}'.`
      );
    }
  }

  // Only add if validation passes
  url.searchParams.set(
    'parameter-name',
    optional_params.parameter_name.join(',')
  );
}
```

---

## 7. Base Path Construction

### Link-Based Construction

**Pattern: Get base paths from link relations**

```typescript
// From endpoint root
const collectionsUrl = getLinkUrl(
  root,
  ['data', 'http://www.opengis.net/def/rel/ogc/1.0/data'],
  this.baseUrl
);

// From collection
const itemsUrl = getLinkUrl(collectionDoc, 'items', this.baseUrl);

// From collection with format preference
const itemsUrl = getLinkUrl(
  collectionDoc,
  'items',
  this.baseUrl,
  'application/geo+json'
);
```

### Path Utilities

**Available in `src/shared/url-utils.ts`:**

```typescript
// Get parent path
export function getParentPath(url: string): string | null;

// Get child path
export function getChildPath(url: string, childFragment: string): string;
```

**Usage example:**

```typescript
// Build item URL
const itemsUrl = getLinkUrl(collectionDoc, 'items', this.baseUrl);
const itemUrl = getChildPath(itemsUrl, itemId);
// Result: https://api.example.com/collections/foo/items/bar
```

### Nested Resource Paths

**Pattern: Build from collection URL**

```typescript
async getCollectionItem(
  collectionId: string,
  itemId: string
): Promise<OgcApiCollectionItem> {
  return this.getCollectionDocument(collectionId)
    .then((collectionDoc) => {
      // Get items URL from link
      const url = new URL(
        getLinkUrl(collectionDoc, 'items', this.baseUrl),
        getBaseUrl()
      );

      // Append item ID
      url.pathname += `/${itemId}`;

      return url.toString();
    })
    .then(fetchDocument<OgcApiCollectionItem>);
}
```

---

## 8. Resource Path Structure

### Hypermedia Structure

**OGC API paths follow hypermedia pattern:**

```
Root
 ├─ /conformance
 ├─ /collections
 │   ├─ /collections/{id}
 │   │   ├─ /items
 │   │   │   └─ /items/{itemId}
 │   │   ├─ /queryables
 │   │   ├─ /sortables
 │   │   ├─ /tiles
 │   │   └─ (API-specific endpoints)
 └─ /styles
```

### API-Specific Paths

**EDR adds query type paths:**

```
/collections/{id}
 ├─ /position
 ├─ /area
 ├─ /cube
 ├─ /trajectory
 ├─ /corridor
 ├─ /radius
 └─ /locations
```

**These come from collection metadata:**

```typescript
collection.data_queries = {
  position: { link: { href: '.../collections/temp/position' } },
  area: { link: { href: '.../collections/temp/area' } },
  // ...
};
```

### CSAPI Path Structure

**CSAPI will have:**

```
/collections/{id}
 ├─ /systems
 │   └─ /systems/{systemId}
 │       ├─ /datastreams
 │       │   └─ /datastreams/{datastreamId}
 │       │       └─ /observations
 │       ├─ /controls
 │       └─ /controlStreams
 │           └─ /controlStreams/{controlStreamId}
 │               └─ /commands
 ├─ /deployments
 │   └─ /deployments/{deploymentId}
 ├─ /samplingFeatures
 │   └─ /samplingFeatures/{featureId}
 └─ /procedures
     └─ /procedures/{procedureId}
```

**All paths come from collection links** - never hardcoded.

---

## 9. URL Builder Utilities

### What Exists

**Location:** `src/shared/url-utils.ts`

**Functions:**

```typescript
// Get base URL
export function getBaseUrl(url?: string): string | URL;

// Navigate up
export function getParentPath(url: string): string | null;

// Navigate down
export function getChildPath(url: string, childFragment: string): string;
```

### What Doesn't Exist

**No dedicated URL builder class or complex utilities.**

**Why?** Native `URL` API + link relations are sufficient.

### Link Utilities

**More important:** `src/ogc-api/link-utils.ts`

```typescript
// Fetch document by following link
export function fetchLink(
  doc: OgcApiDocument,
  rels: string | string[],
  baseUrl: string,
  type?: MimeType
): Promise<OgcApiDocument>;

// Extract URL from link
export function getLinkUrl(
  doc: OgcApiDocument,
  rels: string | string[],
  baseUrl: string,
  type?: MimeType,
  ignoreErrors?: boolean
): string | null;

// Get all matching links
export function getLinks(
  doc: OgcApiDocument,
  rels: string | string[],
  type?: MimeType,
  ignoreErrors?: boolean
): Array<{ rel: string; href: string; type?: string }>;

// Check if links exist
export function hasLinks(doc: OgcApiDocument, rels: string | string[]): boolean;
```

**These are the primary URL building tools.**

### Should CSAPI Add URL Utilities?

**No.** Reuse existing utilities:

- `getLinkUrl()` for extracting resource URLs
- `getChildPath()` for nested resources
- Native `URL` class for query parameters

**Only add helpers if:**

- Specific parameter encoding logic needed (e.g., datetime formatting)
- Multiple methods share complex URL building code

---

## 10. Avoiding Duplication

### Challenge: 9 Resources in CSAPI

**Each resource needs:**

- List method (`getSystems()`)
- Get by ID method (`getSystem(id)`)
- URL building
- Parameter handling
- Error handling

**Risk:** Duplicating this logic 9 times.

### Duplication in EDR

**EDR has 7 query types, each with similar structure:**

```typescript
buildPositionDownloadUrl(coords, optional_params): string {
  if (!this.supported_query_types.position) throw new Error(...);
  const url = new URL(this.collection.data_queries?.position?.link.href);
  url.searchParams.set('coords', formatCoords(coords));
  if (optional_params.datetime) url.searchParams.set('datetime', formatDatetime(...));
  if (optional_params.parameter_name) url.searchParams.set('parameter-name', ...);
  if (optional_params.crs) url.searchParams.set('crs', ...);
  if (optional_params.f) url.searchParams.set('f', ...);
  return url.toString();
}

buildAreaDownloadUrl(coords, optional_params): string {
  if (!this.supported_query_types.area) throw new Error(...);
  const url = new URL(this.collection.data_queries?.area?.link.href);
  url.searchParams.set('coords', coords);
  if (optional_params.datetime) url.searchParams.set('datetime', formatDatetime(...));
  if (optional_params.parameter_name) url.searchParams.set('parameter-name', ...);
  if (optional_params.crs) url.searchParams.set('crs', ...);
  if (optional_params.f) url.searchParams.set('f', ...);
  return url.toString();
}

// ... 5 more similar methods
```

**Analysis:** ~70% of code is duplicated across methods.

### EDR Solution: Accept Duplication

**EDR chose to duplicate** rather than abstract.

**Why?**

- Each query type has slightly different requirements
- Abstractions would add complexity
- Code is straightforward and maintainable
- ~50 lines per method is reasonable

### Alternative: Helper Functions

**Could extract common parameter handling:**

```typescript
class EDRQueryBuilder {
  private addOptionalParams(url: URL, optional_params: optionalParams): void {
    if (optional_params.datetime) {
      url.searchParams.set(
        'datetime',
        this.formatDatetime(optional_params.datetime)
      );
    }
    if (optional_params.parameter_name) {
      this.validateParameters(optional_params.parameter_name);
      url.searchParams.set(
        'parameter-name',
        optional_params.parameter_name.join(',')
      );
    }
    if (optional_params.crs) {
      this.validateCrs(optional_params.crs);
      url.searchParams.set('crs', optional_params.crs);
    }
    if (optional_params.f) {
      url.searchParams.set('f', optional_params.f);
    }
  }

  buildPositionDownloadUrl(coords, optional_params): string {
    this.checkSupported('position');
    const url = new URL(this.collection.data_queries?.position?.link.href);
    url.searchParams.set('coords', this.formatPositionCoords(coords));
    this.addOptionalParams(url, optional_params);
    return url.toString();
  }
}
```

**Benefit:** Less duplication
**Cost:** More abstraction, harder to understand individual methods

### CSAPI Strategy

**Recommendation:** Start with duplication, extract if needed.

**Approach:**

1. **Implement first resource completely** (systems)
2. **Copy-paste for second resource** (deployments)
3. **Identify duplicated code** during implementation
4. **Extract helpers if duplication is excessive** (>80%)
5. **Keep methods readable** - prefer explicit over DRY

**Acceptable duplication:**

```typescript
async getSystems(options: QueryOptions = {}): Promise<System[]> {
  // This pattern repeated 9 times is OK
  if (!this.supported_resources.has('systems')) throw new Error(...);
  const url = this.buildListUrl('systems', options);
  const response = await fetch(url);
  const data = await response.json();
  return data.items as System[];
}
```

**Extract if helpers make it clearer:**

```typescript
class CSAPIQueryBuilder {
  private buildListUrl(resource: string, options: QueryOptions): string {
    const baseUrl = getLinkUrl(this.collection, resource, '');
    const url = new URL(baseUrl);
    this.addQueryParams(url, options);
    return url.toString();
  }

  private addQueryParams(url: URL, options: QueryOptions): void {
    if (options.limit) url.searchParams.set('limit', options.limit.toString());
    if (options.offset)
      url.searchParams.set('offset', options.offset.toString());
    if (options.bbox) url.searchParams.set('bbox', options.bbox.join(','));
    if (options.datetime)
      url.searchParams.set('datetime', this.formatDatetime(options.datetime));
  }

  async getSystems(options: QueryOptions = {}): Promise<System[]> {
    this.checkResource('systems');
    const url = this.buildListUrl('systems', options);
    return this.fetchItems<System>(url);
  }
}
```

---

## 11. Sub-Resource URL Pattern

### Nested Resource Structure

**CSAPI has nested resources:**

```
/systems/{systemId}
 ├─ /datastreams
 │   └─ /datastreams/{datastreamId}
 │       └─ /observations
 ├─ /controls
 └─ /controlStreams
     └─ /controlStreams/{streamId}
         └─ /commands
```

### Pattern: Path Concatenation

**Build nested URLs by appending to parent:**

```typescript
async getDatastreams(
  systemId: string,
  options: QueryOptions = {}
): Promise<Datastream[]> {
  // 1. Get systems base URL
  const systemsUrl = getLinkUrl(this.collection, 'systems', '');

  // 2. Build path to specific system's datastreams
  const url = new URL(`${systemsUrl}/${systemId}/datastreams`);

  // 3. Add query params
  if (options.limit) url.searchParams.set('limit', options.limit.toString());
  if (options.offset) url.searchParams.set('offset', options.offset.toString());

  // 4. Fetch
  const response = await fetch(url.toString());
  const data = await response.json();
  return data.items as Datastream[];
}
```

### Alternative: getChildPath Utility

**Using existing utility:**

```typescript
async getDatastreams(
  systemId: string,
  options: QueryOptions = {}
): Promise<Datastream[]> {
  const systemsUrl = getLinkUrl(this.collection, 'systems', '');

  // Build nested path
  let url = getChildPath(systemsUrl, systemId);
  url = getChildPath(url, 'datastreams');

  // Convert to URL object for params
  const finalUrl = new URL(url);
  if (options.limit) finalUrl.searchParams.set('limit', options.limit.toString());

  const response = await fetch(finalUrl.toString());
  const data = await response.json();
  return data.items as Datastream[];
}
```

### Deep Nesting: Observations

**Three levels deep:**

```typescript
async getObservations(
  systemId: string,
  datastreamId: string,
  options: QueryOptions = {}
): Promise<Observation[]> {
  const systemsUrl = getLinkUrl(this.collection, 'systems', '');

  // Build deeply nested path
  const url = new URL(
    `${systemsUrl}/${systemId}/datastreams/${datastreamId}/observations`
  );

  // Add query params (important for observations - could be large)
  if (options.limit) url.searchParams.set('limit', options.limit.toString());
  if (options.offset) url.searchParams.set('offset', options.offset.toString());
  if (options.datetime) {
    url.searchParams.set('datetime', this.formatDatetime(options.datetime));
  }

  const response = await fetch(url.toString());
  const data = await response.json();
  return data.items as Observation[];
}
```

### Link Relations for Nested Resources

**Better approach: Use link relations if available**

If the parent resource provides links:

```typescript
async getDatastreams(systemId: string): Promise<Datastream[]> {
  // 1. Get the system
  const system = await this.getSystem(systemId);

  // 2. Check if system has datastreams link
  if (system.links) {
    const datastreamsUrl = getLinkUrl(system, 'datastreams', '');
    if (datastreamsUrl) {
      const response = await fetch(datastreamsUrl);
      const data = await response.json();
      return data.items as Datastream[];
    }
  }

  // 3. Fallback to path construction
  const systemsUrl = getLinkUrl(this.collection, 'systems', '');
  const url = `${systemsUrl}/${systemId}/datastreams`;
  const response = await fetch(url);
  const data = await response.json();
  return data.items as Datastream[];
}
```

**Pros:** More robust, follows hypermedia principles
**Cons:** Requires extra fetch for parent resource

**Recommendation:** Use path construction for simplicity, add link following if needed later.

---

## 12. CSAPI URL Building Strategy

### Overall Strategy

**Based on upstream patterns:**

1. ✅ **Get base URLs from collection links** (never construct)
2. ✅ **Use native URL API** for all URL building
3. ✅ **Use searchParams** for all query parameters
4. ✅ **Accept some duplication** across resource methods
5. ✅ **Extract helpers only if >80% duplication**
6. ✅ **Build nested paths via concatenation** (with parent IDs)
7. ✅ **Validate parameters before adding** to URL

### URL Sources by Resource Type

| Resource          | URL Source             | Example                                                           |
| ----------------- | ---------------------- | ----------------------------------------------------------------- |
| Systems           | Collection link        | `getLinkUrl(collection, 'systems')`                               |
| Deployments       | Collection link        | `getLinkUrl(collection, 'deployments')`                           |
| Sampling Features | Collection link        | `getLinkUrl(collection, 'samplingFeatures')`                      |
| Procedures        | Collection link        | `getLinkUrl(collection, 'procedures')`                            |
| Datastreams       | Parent system path     | `{systemsUrl}/{systemId}/datastreams`                             |
| Observations      | Parent datastream path | `{systemsUrl}/{systemId}/datastreams/{datastreamId}/observations` |
| Controls          | Parent system path     | `{systemsUrl}/{systemId}/controls`                                |
| Control Streams   | Parent system path     | `{systemsUrl}/{systemId}/controlStreams`                          |
| Commands          | Parent stream path     | `{systemsUrl}/{systemId}/controlStreams/{streamId}/commands`      |

### Common Query Parameters

**All CSAPI resources should support:**

```typescript
interface QueryOptions {
  limit?: number; // Pagination
  offset?: number; // Pagination
  bbox?: BoundingBox; // Spatial filter
  datetime?: DateTimeParameter; // Temporal filter
}
```

**Add to URL consistently:**

```typescript
private addCommonParams(url: URL, options: QueryOptions): void {
  if (options.limit !== undefined) {
    url.searchParams.set('limit', options.limit.toString());
  }
  if (options.offset !== undefined) {
    url.searchParams.set('offset', options.offset.toString());
  }
  if (options.bbox && options.bbox.length > 0) {
    url.searchParams.set('bbox', options.bbox.join(','));
  }
  if (options.datetime !== undefined) {
    url.searchParams.set('datetime', this.formatDatetime(options.datetime));
  }
}
```

### Helper Functions to Create

**Recommended helpers:**

```typescript
class CSAPIQueryBuilder {
  // Format datetime to OGC API string
  private formatDatetime(datetime: DateTimeParameter): string {
    if (datetime instanceof Date) {
      return datetime.toISOString();
    }
    const start = 'start' in datetime ? datetime.start.toISOString() : '..';
    const end = 'end' in datetime ? datetime.end.toISOString() : '..';
    return `${start}/${end}`;
  }

  // Add common query parameters
  private addCommonParams(url: URL, options: QueryOptions): void {
    // ... as shown above
  }

  // Build list URL for a resource
  private buildListUrl(resource: string, options: QueryOptions): string {
    const baseUrl = getLinkUrl(this.collection, resource, '');
    const url = new URL(baseUrl);
    this.addCommonParams(url, options);
    return url.toString();
  }

  // Build URL for specific resource item
  private buildItemUrl(resource: string, itemId: string): string {
    const baseUrl = getLinkUrl(this.collection, resource, '');
    return `${baseUrl}/${itemId}`;
  }

  // Build nested resource URL
  private buildNestedUrl(
    parentResource: string,
    parentId: string,
    childResource: string,
    options?: QueryOptions
  ): string {
    const baseUrl = getLinkUrl(this.collection, parentResource, '');
    const url = new URL(`${baseUrl}/${parentId}/${childResource}`);
    if (options) {
      this.addCommonParams(url, options);
    }
    return url.toString();
  }

  // Validate resource is available
  private checkResource(resource: string): void {
    if (!this.supported_resources.has(resource)) {
      throw new Error(
        `Resource '${resource}' is not available on this collection`
      );
    }
  }

  // Generic fetch for items
  private async fetchItems<T>(url: string): Promise<T[]> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    return data.items as T[];
  }

  // Generic fetch for single item
  private async fetchItem<T>(url: string): Promise<T> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    return data as T;
  }
}
```

### Example Implementation

**Using helpers:**

```typescript
class CSAPIQueryBuilder {
  // ... helpers above

  // Top-level resource
  async getSystems(options: QueryOptions = {}): Promise<System[]> {
    this.checkResource('systems');
    const url = this.buildListUrl('systems', options);
    return this.fetchItems<System>(url);
  }

  async getSystem(systemId: string): Promise<System> {
    this.checkResource('systems');
    const url = this.buildItemUrl('systems', systemId);
    return this.fetchItem<System>(url);
  }

  // Nested resource (one level)
  async getDatastreams(
    systemId: string,
    options: QueryOptions = {}
  ): Promise<Datastream[]> {
    this.checkResource('systems'); // Parent must be available
    const url = this.buildNestedUrl(
      'systems',
      systemId,
      'datastreams',
      options
    );
    return this.fetchItems<Datastream>(url);
  }

  async getDatastream(
    systemId: string,
    datastreamId: string
  ): Promise<Datastream> {
    this.checkResource('systems');
    const baseUrl = getLinkUrl(this.collection, 'systems', '');
    const url = `${baseUrl}/${systemId}/datastreams/${datastreamId}`;
    return this.fetchItem<Datastream>(url);
  }

  // Nested resource (two levels)
  async getObservations(
    systemId: string,
    datastreamId: string,
    options: QueryOptions = {}
  ): Promise<Observation[]> {
    this.checkResource('systems');
    const baseUrl = getLinkUrl(this.collection, 'systems', '');
    const url = new URL(
      `${baseUrl}/${systemId}/datastreams/${datastreamId}/observations`
    );
    this.addCommonParams(url, options);
    return this.fetchItems<Observation>(url.toString());
  }
}
```

**Result:** ~10 lines per resource method, with shared logic in helpers.

---

## Conclusion

### Key Findings

1. **No base URL builder class** - Native `URL` API is sufficient
2. **Links, not construction** - Always get URLs from link relations
3. **searchParams for parameters** - No manual encoding needed
4. **Options object for optional params** - Modern pattern preferred
5. **Arrays join with comma** - Standard OGC API encoding
6. **Accept some duplication** - EDR duplicates ~70% of code across methods
7. **Helper functions recommended** - For datetime formatting, parameter addition
8. **Path concatenation for nesting** - Build nested URLs by appending IDs
9. **Automatic encoding** - URL API handles all encoding
10. **Format negotiation via links** - Check link types before adding `f` parameter

### CSAPI URL Building Approach

**Recommended strategy:**

```typescript
class CSAPIQueryBuilder {
  // Private helpers (200-250 lines)
  private formatDatetime(...)
  private addCommonParams(...)
  private buildListUrl(...)
  private buildItemUrl(...)
  private buildNestedUrl(...)
  private checkResource(...)
  private fetchItems(...)
  private fetchItem(...)

  // Public resource methods (~10 lines each × 18 methods = 180 lines)
  async getSystems(...)
  async getSystem(...)
  async getDeployments(...)
  async getDeployment(...)
  async getSamplingFeatures(...)
  async getSamplingFeature(...)
  async getProcedures(...)
  async getProcedure(...)
  async getDatastreams(...)
  async getDatastream(...)
  async getObservations(...)
  async getControls(...)
  async getControl(...)
  async getControlStreams(...)
  async getControlStream(...)
  async getCommands(...)
  async getCommand(...)
}
```

**Total:** ~430-480 lines for URL building logic

**Benefit:** Minimal duplication while keeping code readable and maintainable.
