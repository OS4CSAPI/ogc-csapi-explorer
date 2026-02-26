# Format Negotiation Architecture Analysis

**Purpose:** Document format negotiation patterns in ogc-client to guide CSAPI format handling.

**Context:** CSAPI supports multiple formats (GeoJSON, JSON-FG, SensorML). Need clear strategy for format selection and content negotiation.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [Format Negotiation Patterns](#2-format-negotiation-patterns)
3. [Accept Header Strategy](#3-accept-header-strategy)
4. [Query Parameter Format Selection](#4-query-parameter-format-selection)
5. [Link-Based Format Discovery](#5-link-based-format-discovery)
6. [Format Detection](#6-format-detection)
7. [Format Constants](#7-format-constants)
8. [CSAPI Format Strategy](#8-csapi-format-strategy)
9. [Parser Architecture](#9-parser-architecture)
10. [Complete Format Handling Design](#10-complete-format-handling-design)

---

## 1. Overview

### Format Negotiation Mechanisms

**ogc-client uses three mechanisms for format negotiation:**

1. **Query parameter (`f`)** - Explicit format request in URL
2. **Accept header** - HTTP content negotiation
3. **Link rel/type** - Follow link with specific MIME type

**Priority order:**

1. Explicit `f` parameter (highest priority)
2. Link type-based selection
3. Accept header (fallback)

### Where Format Logic Lives

**Not centralized in utility module** - spread across endpoint classes:

| Location                         | Format Logic                  |
| -------------------------------- | ----------------------------- |
| `src/shared/mime-type.ts`        | MIME type detection utilities |
| `src/shared/http-utils.ts`       | Accept header handling        |
| `src/ogc-api/endpoint.ts`        | Link-based format selection   |
| `src/stac/endpoint.ts`           | Accept header from links      |
| `src/ogc-api/edr/url_builder.ts` | `f` parameter handling        |

**No dedicated format negotiation module** - each API handles it inline.

---

## 2. Format Negotiation Patterns

### Pattern 1: Query Parameter (`f`)

**Used by:** EDR, OGC API

**Pattern:**

```typescript
// In optionalParams interface
export type optionalPositionParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  f?: string; // Format parameter
};

// In URL builder
if (optional_params.f !== undefined) {
  url.searchParams.set('f', optional_params.f);
}
```

**Usage:**

```typescript
const url = builder.buildPositionDownloadUrl('POINT(0 51)', {
  f: 'application/json',
});
// Results in: .../position?coords=POINT(0%2051)&f=application%2Fjson
```

**Characteristics:**

- Simple string parameter
- No validation (trusts user input)
- No format enum
- Server validates format support

### Pattern 2: Link Selection with MIME Type

**Used by:** OGC API Features, STAC

**Pattern:**

```typescript
// Find link matching desired format
const itemLinks = getLinks(collectionDoc, 'items', undefined, true);
let linkWithFormat = itemLinks.find(
  (link) => link.type === options?.outputFormat
);

// Fallback to JSON-FG, GeoJSON, or JSON
if (options.asJson) {
  linkWithFormat =
    itemLinks.find((link) => isMimeTypeJsonFg(link.type)) ||
    itemLinks.find((link) => isMimeTypeGeoJson(link.type)) ||
    itemLinks.find((link) => isMimeTypeJson(link.type));
}

// Use the link
const url = new URL(linkWithFormat.href);
```

**Usage:**

```typescript
const url = await endpoint.getCollectionItemsUrl('myCollection', {
  outputFormat: 'application/geo+json',
});
```

**Characteristics:**

- Link-based discovery
- Type matching from collection metadata
- Fallback chain for JSON formats
- Error if format not available

### Pattern 3: Accept Header from Link Type

**Used by:** STAC

**Pattern:**

```typescript
// Get link with type
const itemsLink = getLinks(collectionDoc, 'items')[0];
const acceptType = itemsLink?.type; // e.g., 'application/geo+json'

// Use as Accept header
const doc = await fetchStacDocument(
  url.toString(),
  acceptType // Passed as custom Accept header
);
```

**In http-utils.ts:**

```typescript
export function sharedFetch(
  url: string,
  method: 'GET' | 'HEAD' = 'GET',
  asJson?: boolean,
  customAcceptHeader?: string
) {
  // ...
  if (customAcceptHeader) {
    options.headers['Accept'] = customAcceptHeader;
  } else if (asJson) {
    options.headers['Accept'] = 'application/json,application/schema+json';
  }
  // ...
}
```

**Characteristics:**

- Automatic from link metadata
- HTTP content negotiation
- Server chooses based on Accept header

---

## 3. Accept Header Strategy

### Current Implementation

**Location:** `src/shared/http-utils.ts`

```typescript
export function sharedFetch(
  url: string,
  method: 'GET' | 'HEAD' = 'GET',
  asJson?: boolean,
  customAcceptHeader?: string
) {
  let fetchKey = `${method}#${url}`;
  if (asJson || customAcceptHeader) {
    fetchKey = `${method}#asJson#${url}`;
  }
  if (fetchPromises.has(fetchKey)) {
    return fetchPromises.get(fetchKey);
  }
  const options: RequestInit = { ...getFetchOptions() };
  options.method = method;
  if (customAcceptHeader) {
    options.headers = 'headers' in options ? options.headers : {};
    options.headers['Accept'] = customAcceptHeader;
  } else if (asJson) {
    options.headers = 'headers' in options ? options.headers : {};
    options.headers['Accept'] = 'application/json,application/schema+json';
  }
  // ... rest of implementation
}
```

### Accept Header Patterns

**Default (no format specified):**

- No Accept header set
- Server returns default format

**JSON requested (`asJson: true`):**

```
Accept: application/json,application/schema+json
```

**Custom format:**

```typescript
sharedFetch(url, 'GET', false, 'application/geo+json');
// Results in: Accept: application/geo+json
```

**Multiple formats (quality values not supported):**

❌ **Not implemented:**

```
Accept: application/geo+json;q=0.9,application/json;q=0.8
```

### When Accept Headers Are Used

**STAC uses Accept headers:**

```typescript
const itemsDoc = await fetchStacDocument(
  url.toString(),
  acceptType // From link.type
);
```

**OGC API does NOT use Accept headers:**

```typescript
// Uses link selection instead
const linkWithFormat = itemLinks.find(
  (link) => link.type === options?.outputFormat
);
```

**EDR does NOT use Accept headers:**

```typescript
// Uses 'f' query parameter instead
url.searchParams.set('f', optional_params.f);
```

### Why Different Approaches?

**Query parameter (`f`) advantages:**

- URL is self-documenting
- Easy to cache by URL
- Simple implementation
- Works with proxy caching

**Accept header advantages:**

- Standard HTTP content negotiation
- Cleaner URLs
- Multiple format preferences

**ogc-client prefers query parameters** for OGC APIs.

---

## 4. Query Parameter Format Selection

### EDR Pattern

**All EDR methods accept optional `f` parameter:**

```typescript
export type optionalPositionParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: ZParameter;
  crs?: string;
  f?: string; // Format parameter
};
```

**Implementation:**

```typescript
buildPositionDownloadUrl(
  coords: WellKnownTextString,
  optional_params: optionalPositionParams = {}
): string {
  // ... build base URL

  if (optional_params.f !== undefined) {
    url.searchParams.set('f', optional_params.f);
  }

  return url.toString();
}
```

**No validation, no constants:**

```typescript
// User provides format string directly
const url = builder.buildPositionDownloadUrl('POINT(0 51)', {
  f: 'CoverageJSON',
});
```

**Benefits:**

- Simple implementation
- Flexible (any format string)
- No maintenance (no format enum to update)

**Drawbacks:**

- No type safety
- No autocomplete
- User must know valid formats
- Typos not caught

### OGC API Features Pattern

**Uses `outputFormat` option:**

```typescript
getCollectionItemsUrl(
  collectionId: string,
  options: {
    outputFormat?: MimeType;  // Type alias for string
    // ...
  } = {}
): Promise<string> {
  // Find link matching format
  let linkWithFormat = itemLinks.find(
    (link) => link.type === options?.outputFormat
  );

  // If not found in links, add as 'f' parameter
  if (options?.outputFormat && !linkWithFormat) {
    url.searchParams.set('f', options.outputFormat);
  }

  return url.toString();
}
```

**Pattern:**

1. Try to find link with matching type
2. If not found, add `f` query parameter
3. Warn if format not in collection metadata

---

## 5. Link-Based Format Discovery

### Link Structure

**OGC API links include MIME type:**

```json
{
  "links": [
    {
      "rel": "items",
      "type": "application/geo+json",
      "href": "https://api.example.com/collections/mycol/items"
    },
    {
      "rel": "items",
      "type": "text/html",
      "href": "https://api.example.com/collections/mycol/items.html"
    }
  ]
}
```

### Format Selection Logic

**In `endpoint.ts`:**

```typescript
const itemLinks = getLinks(collectionDoc, 'items', undefined, true);

// Option 1: Explicit format requested
let linkWithFormat = itemLinks.find(
  (link) => link.type === options?.outputFormat
);

// Option 2: JSON formats (precedence: JSON-FG > GeoJSON > JSON)
if (options.asJson) {
  linkWithFormat =
    itemLinks.find((link) => isMimeTypeJsonFg(link.type)) ||
    itemLinks.find((link) => isMimeTypeGeoJson(link.type)) ||
    itemLinks.find((link) => isMimeTypeJson(link.type));
}

// Option 3: Use first link (default)
if (!linkWithFormat) {
  linkWithFormat = itemLinks[0];
}

// Build URL from selected link
const url = new URL(linkWithFormat.href);
```

### Format Validation

**Warn if format not available:**

```typescript
if (options?.outputFormat && !linkWithFormat) {
  console.warn(
    `[ogc-client] The following output format type was not found in the collection '${collectionId}': ${options.outputFormat}`
  );
  // Still add as query parameter (server may support it)
  url.searchParams.set('f', options.outputFormat);
}
```

**Pattern:** Graceful degradation, trust server.

---

## 6. Format Detection

### MIME Type Utilities

**Location:** `src/shared/mime-type.ts`

```typescript
export function isMimeTypeJson(mimeType: string): boolean {
  return mimeType.toLowerCase().indexOf('json') > -1;
}

export function isMimeTypeGeoJson(mimeType: string): boolean {
  return /geo.?json/.test(mimeType);
}

export function isMimeTypeJsonFg(mimeType: string): boolean {
  return /json.?fg|fg.?json/.test(mimeType);
}
```

**Usage:**

```typescript
const link = links.find((link) => isMimeTypeGeoJson(link.type));
// Matches: 'application/geo+json', 'application/geojson', etc.
```

**Pattern:** Regex-based detection, case-insensitive.

### Content-Type Detection

**Not explicitly done** - ogc-client assumes server returns correct format.

**No runtime validation:**

```typescript
// ❌ Not done:
const response = await fetch(url);
const contentType = response.headers.get('Content-Type');
if (!isMimeTypeGeoJson(contentType)) {
  throw new Error('Unexpected format returned');
}
```

**Reason:** Trusts server compliance with OGC standards.

---

## 7. Format Constants

### Current State: No Constants

**No format enums or constants defined:**

```typescript
// ❌ This doesn't exist:
export const CSAPIFormats = {
  GEOJSON: 'application/geo+json',
  JSON_FG: 'application/vnd.ogc.fg+json',
  SENSOR_ML: 'application/sensorml+json',
  HTML: 'text/html',
} as const;
```

**Why?** Flexibility and simplicity.

### When Constants Make Sense

**Pros of constants:**

- Type safety
- Autocomplete
- Avoid typos
- Documentation

**Cons of constants:**

- Maintenance burden
- Less flexible
- May not cover all formats
- OGC standards evolve

### MimeType Type Alias

**Current approach:**

```typescript
// src/shared/models.ts
export type MimeType = string;
```

**Not a union type:**

```typescript
// ❌ Not done:
export type MimeType =
  | 'application/geo+json'
  | 'application/json'
  | 'text/html';
// ... exhaustive list
```

**Reason:** Too restrictive, standards evolve.

---

## 8. CSAPI Format Strategy

### CSAPI Supported Formats

**From OGC API - Connected Systems spec:**

| Format        | MIME Type                     | Usage                  |
| ------------- | ----------------------------- | ---------------------- |
| GeoJSON       | `application/geo+json`        | Default JSON format    |
| JSON-FG       | `application/vnd.ogc.fg+json` | Features with geometry |
| SensorML JSON | `application/sensorml+json`   | System descriptions    |
| SensorML XML  | `application/sensorml+xml`    | Legacy format          |
| HTML          | `text/html`                   | Human-readable         |

### Recommended Format Handling

**Follow EDR pattern:** Use `f` query parameter.

**QueryOptions interface:**

```typescript
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  f?: string; // Format parameter (MIME type)
}
```

**URL building:**

```typescript
async getSystems(options?: QueryOptions): Promise<string> {
  const baseUrl = getLinkUrl(
    this.collection_,
    ['systems', 'http://www.opengis.net/def/rel/ogc/1.0/systems'],
    this.baseUrl,
    undefined,
    true
  );

  const url = new URL(baseUrl);

  if (options?.f) {
    url.searchParams.set('f', options.f);
  }

  // ... other parameters

  return url.toString();
}
```

**Usage:**

```typescript
// Default format (server decides)
const url1 = await builder.getSystems();

// Request GeoJSON explicitly
const url2 = await builder.getSystems({
  f: 'application/geo+json',
});

// Request SensorML
const url3 = await builder.getSystem('sys-123', {
  f: 'application/sensorml+json',
});
```

### Optional: Format Constants for Documentation

**If desired for user convenience:**

```typescript
// In model.ts
export const CSAPIFormats = {
  GeoJSON: 'application/geo+json',
  JSON_FG: 'application/vnd.ogc.fg+json',
  SensorML_JSON: 'application/sensorml+json',
  SensorML_XML: 'application/sensorml+xml',
  HTML: 'text/html',
} as const;

// Usage (optional, for convenience)
const url = await builder.getSystem('sys-123', {
  f: CSAPIFormats.SensorML_JSON,
});
```

**Recommendation:** Optional export, not required for type signature.

### No Link-Based Format Selection

**CSAPI doesn't need link-based format discovery:**

**Reason:** Collection links typically don't have multiple format variants for same relation.

**CSAPI links structure:**

```json
{
  "links": [
    {
      "rel": "systems",
      "href": ".../systems"
    }
  ]
}
```

**Not:**

```json
{
  "links": [
    {
      "rel": "systems",
      "type": "application/geo+json",
      "href": ".../systems"
    },
    {
      "rel": "systems",
      "type": "application/sensorml+json",
      "href": ".../systems.sml"
    }
  ]
}
```

**Pattern:** Single link per relation, format via query parameter.

### No Accept Header Handling

**CSAPI doesn't need custom Accept headers:**

**Reason:** Query parameter (`f`) is simpler and standard for OGC APIs.

**Implementation:**

```typescript
// ❌ Don't do this:
async getSystems(options?: { accept?: string }): Promise<string> {
  // No need for Accept header logic
}

// ✅ Do this:
async getSystems(options?: { f?: string }): Promise<string> {
  if (options?.f) {
    url.searchParams.set('f', options.f);
  }
}
```

---

## 9. Parser Architecture

### Current Parser Pattern

**ogc-client has minimal parsing:**

**JSON parsing:**

```typescript
const response = await fetch(url);
const data = await response.json(); // Built-in JSON parsing
return data;
```

**XML parsing:**

```typescript
import { parseXmlString } from '../shared/xml-utils.js';

const response = await fetch(url);
const text = await response.text();
const doc = parseXmlString(text);
// ... extract data from XML DOM
```

### No Format-Specific Validators

**No runtime validation of response format:**

```typescript
// ❌ This doesn't exist:
function validateGeoJSON(data: any): System {
  if (data.type !== 'Feature') {
    throw new Error('Invalid GeoJSON');
  }
  // ... validate structure
  return data as System;
}
```

**Reason:** Trusts TypeScript types and server compliance.

### CSAPI Parsing Strategy

**Keep it simple:**

1. **JSON formats (GeoJSON, JSON-FG):**

   - Use native `response.json()`
   - Return as typed objects
   - No validation

2. **XML formats (SensorML XML):**

   - Return raw string or parse to DOM
   - Don't type XML responses (too complex)

3. **HTML:**
   - Not parsed
   - Return raw string

**Implementation:**

```typescript
// In url_builder.ts - only returns URLs
async getSystems(options?: QueryOptions): Promise<string> {
  // Build and return URL
  return url.toString();
}

// Users fetch themselves:
const url = await builder.getSystems({ f: 'application/geo+json' });
const response = await fetch(url);
const systems: SystemCollection = await response.json();
```

**Alternative (if fetching in library):**

```typescript
async getSystems(options?: QueryOptions): Promise<SystemCollection | string> {
  const url = this.buildSystemsUrl(options);

  // If XML format requested, return raw
  if (options?.f?.includes('xml')) {
    const response = await fetch(url);
    return await response.text();
  }

  // Otherwise return parsed JSON
  const response = await fetch(url);
  return await response.json();
}
```

**Recommendation:** Return URLs only (like EDR), let users fetch.

---

## 10. Complete Format Handling Design

### CSAPI Format Architecture

**Location of format logic:** Inline in url_builder.ts

**No separate format module** - follow EDR pattern.

#### 1. Model Definition

**File:** `src/ogc-api/csapi/model.ts`

```typescript
// Optional format constants (for user convenience)
export const CSAPIFormats = {
  GeoJSON: 'application/geo+json',
  JSON_FG: 'application/vnd.ogc.fg+json',
  SensorML_JSON: 'application/sensorml+json',
  SensorML_XML: 'application/sensorml+xml',
  HTML: 'text/html',
} as const;

export type CSAPIFormat = (typeof CSAPIFormats)[keyof typeof CSAPIFormats];

// Query options with format parameter
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  f?: string; // Format (MIME type) - using string for flexibility
}
```

**Pattern:**

- Constants optional (exported for convenience)
- Type uses `string` for flexibility
- No validation (trusts server)

#### 2. URL Builder Implementation

**File:** `src/ogc-api/csapi/url_builder.ts`

```typescript
export default class CSAPIQueryBuilder {
  private collection_: OgcApiCollectionInfo;
  private cache_: Map<string, any>;

  constructor(collection: OgcApiCollectionInfo) {
    this.collection_ = collection;
    this.cache_ = new Map();
  }

  /**
   * Get systems collection URL
   * @param options Query options including format
   * @returns URL string
   */
  async getSystems(options?: SystemQueryOptions): Promise<string> {
    const baseUrl = getLinkUrl(
      this.collection_,
      ['systems', 'http://www.opengis.net/def/rel/ogc/1.0/systems'],
      this.baseUrl,
      undefined,
      true
    );

    return this.buildUrl(baseUrl, options);
  }

  /**
   * Get single system URL
   * @param systemId System identifier
   * @param options Query options including format
   * @returns URL string
   */
  async getSystem(systemId: string, options?: QueryOptions): Promise<string> {
    const collectionUrl = await this.getSystems();
    const baseUrl = getChildPath(collectionUrl, systemId);

    return this.buildUrl(baseUrl, options);
  }

  /**
   * Build URL with query parameters
   * @private
   */
  private buildUrl(base: string, options?: QueryOptions): string {
    const url = new URL(base);

    if (options?.limit !== undefined) {
      url.searchParams.set('limit', options.limit.toString());
    }

    if (options?.offset !== undefined) {
      url.searchParams.set('offset', options.offset.toString());
    }

    if (options?.bbox !== undefined) {
      url.searchParams.set('bbox', options.bbox.join(','));
    }

    if (options?.datetime !== undefined) {
      url.searchParams.set('datetime', formatDateTime(options.datetime));
    }

    if (options?.f !== undefined) {
      url.searchParams.set('f', options.f);
    }

    return url.toString();
  }
}
```

**Pattern:**

- Format parameter treated like any other query param
- No validation
- No format-specific URLs
- Simple string parameter

#### 3. Usage Examples

**Example 1: Default format**

```typescript
const endpoint = new OgcApiEndpoint('https://api.example.com');
const builder = await endpoint.csapi('sensors-collection');

// Server returns default format
const url = await builder.getSystems();
// https://api.example.com/collections/sensors-collection/systems
```

**Example 2: Explicit GeoJSON**

```typescript
const url = await builder.getSystems({
  f: 'application/geo+json',
  limit: 10,
});
// https://api.example.com/collections/sensors-collection/systems?f=application%2Fgeo%2Bjson&limit=10
```

**Example 3: Using constants (optional)**

```typescript
import { CSAPIFormats } from 'ogc-client';

const url = await builder.getSystem('sensor-123', {
  f: CSAPIFormats.SensorML_JSON,
});
// https://api.example.com/collections/sensors-collection/systems/sensor-123?f=application%2Fsensorml%2Bjson
```

**Example 4: HTML format**

```typescript
const url = await builder.getSystems({ f: 'text/html' });
// Returns URL to HTML representation
```

### Format Negotiation Summary

**CSAPI format handling:**

| Aspect               | Implementation                   |
| -------------------- | -------------------------------- |
| Format selection     | Query parameter `f`              |
| Format constants     | Optional export for convenience  |
| Format validation    | None (trust server)              |
| Accept headers       | Not used                         |
| Link-based discovery | Not used                         |
| Parser/validators    | None (return URLs only)          |
| Format-specific URLs | Single URL, format via `f` param |
| Default behavior     | Server chooses format            |

**Design principles:**

1. ✅ Simple query parameter approach
2. ✅ No validation (trust server)
3. ✅ Optional constants for user convenience
4. ✅ Flexible (any MIME type string)
5. ✅ Follow EDR pattern exactly
6. ✅ No custom Accept headers
7. ✅ No link-based format selection
8. ✅ Return URLs, not fetched data

---

## Summary

### Key Findings

1. **Query parameter preferred** - ogc-client favors `f` parameter over Accept headers
2. **No centralized format module** - logic inline in endpoint classes
3. **No validation** - trusts server to validate formats
4. **Simple string types** - `MimeType = string`, not unions
5. **Optional constants** - for convenience, not required
6. **Link-based selection** - used by Features, not needed for CSAPI
7. **No parsers** - return URLs, let users fetch
8. **Follow EDR** - exact same pattern for consistency

### CSAPI Format Strategy Checklist

✅ **Implementation:**

- [x] Add `f?: string` to QueryOptions
- [x] Set `f` query parameter in buildUrl helper
- [x] Optional: Export format constants for user convenience
- [x] No validation (trust server)
- [x] No Accept headers
- [x] No link-based format selection
- [x] Return URLs only

✅ **Estimated code:**

- Format constants: ~10 lines (optional)
- Query parameter handling: ~3 lines
- Total: ~13 lines

✅ **Result:** Simple, flexible format handling following established patterns.

---

## Conclusion

CSAPI should use **query parameter (`f`) format selection** following EDR pattern exactly.

No need for:

- Custom Accept headers
- Link-based format discovery
- Format validators
- Parsers
- Complex format negotiation

Simple implementation:

1. Add `f?: string` to QueryOptions
2. Set as query parameter if provided
3. Optionally export format constants

Total code: ~13 lines, follows established patterns, maximum flexibility.
