# Error Handling Design Analysis

**Purpose:** Document error handling patterns in ogc-client to guide CSAPI error strategy.

**Context:** CSAPI needs clear error handling for validation, missing resources, and non-conforming endpoints. Must balance helpful errors vs. library complexity.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [Error Classes](#2-error-classes)
3. [Error Patterns](#3-error-patterns)
4. [Validation Errors](#4-validation-errors)
5. [Missing Resource Errors](#5-missing-resource-errors)
6. [Conformance Errors](#6-conformance-errors)
7. [Network Errors](#7-network-errors)
8. [User Error vs Library Error](#8-user-error-vs-library-error)
9. [CSAPI Error Strategy](#9-csapi-error-strategy)
10. [Complete Error Handling Design](#10-complete-error-handling-design)

---

## 1. Overview

### Error Handling Philosophy

**ogc-client uses minimal, targeted error handling:**

**Principles:**

1. Throw errors for library-detectable problems
2. Let HTTP errors propagate naturally
3. Use specific error types for different categories
4. Validate only what's necessary for library correctness
5. Trust servers to validate their own requirements

### Error Types

**Two custom error classes:**

| Class                   | Usage                                    | Location           |
| ----------------------- | ---------------------------------------- | ------------------ |
| `EndpointError`         | Endpoint configuration/capability issues | `shared/errors.ts` |
| `ServiceExceptionError` | OWS XML exception reports                | `shared/errors.ts` |

**Plus:**

- Generic `Error` - Parameter validation, unsupported operations
- Native `fetch` errors - Network issues (not caught)

---

## 2. Error Classes

### EndpointError

**Definition:**

```typescript
export class EndpointError extends Error {
  constructor(
    message: string,
    public readonly httpStatus?: number,
    public readonly isCrossOriginRelated?: boolean
  ) {
    super(message);
    this.name = 'EndpointError';
  }
}
```

**Usage contexts:**

1. **Missing capabilities:**

   ```typescript
   if (!this.hasEnvironmentalDataRetrieval) {
     throw new EndpointError('Endpoint does not support EDR');
   }
   ```

2. **Missing resources:**

   ```typescript
   throw new EndpointError(`Collection not found: ${collectionId}`);
   ```

3. **Missing links:**

   ```typescript
   throw new EndpointError(`Could not find link with type: ${relType}`);
   ```

4. **Network issues:**
   ```typescript
   throw new EndpointError(
     `Fetching the document failed either due to network errors or unreachable host, error is: ${error.message}`,
     0,
     false
   );
   ```

**Characteristics:**

- General-purpose endpoint issues
- Optional HTTP status code
- Optional CORS indicator
- Used across all OGC API implementations

### ServiceExceptionError

**Definition:**

```typescript
export class ServiceExceptionError extends Error {
  public constructor(
    message: string,
    public readonly requestUrl?: string,
    public readonly code?: string,
    public readonly locator?: string,
    public readonly response?: XmlDocument
  ) {
    super(message);
    this.name = 'ServiceExceptionError';
  }
}
```

**Usage context:**

Only used for XML-based services (WMS, WFS, WMTS):

```typescript
const rootElName = stripNamespace(getElementName(rootEl));
if (rootElName === 'ServiceExceptionReport') {
  const error = findChildElement(rootEl, 'ServiceException');
  if (error) {
    throw parse(error, url);
  }
}
```

**Not used by OGC API** - JSON APIs don't have ServiceExceptionReport.

### Generic Error

**Used for parameter validation:**

```typescript
// EDR validation
if (!this.supported_query_types.position) {
  throw new Error('Collection does not support position queries');
}

if (!this.supported_parameters[parameter]) {
  throw new Error(
    `The following parameter name does not exist on this collection: '${parameter}'.`
  );
}

// Bounds checking
if (minX > maxX) {
  throw new Error('minX must be less than or equal to maxX');
}

// Invalid input
throw new Error('Invalid DateTimeParameter');
```

**Characteristics:**

- Simple validation errors
- Parameter checking
- Logical constraints
- No special metadata needed

---

## 3. Error Patterns

### Pattern 1: Check Capability Before Use

**Used by:** endpoint.ts for API-specific methods

```typescript
public async edr(collection_id: string): Promise<EDRQueryBuilder> {
  if (!this.hasEnvironmentalDataRetrieval) {
    throw new EndpointError('Endpoint does not support EDR');
  }
  // ... proceed with EDR logic
}
```

**Pattern:**

- Check conformance first
- Throw EndpointError if not supported
- Descriptive message

**CSAPI equivalent:**

```typescript
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  // ... proceed
}
```

### Pattern 2: Validate Parameters at Use

**Used by:** EDR url_builder.ts

```typescript
buildPositionDownloadUrl(
  coords: WellKnownTextString,
  optional_params: optionalPositionParams = {}
): string {
  // Check query type support
  if (!this.supported_query_types.position) {
    throw new Error('Collection does not support position queries');
  }

  // ... build URL

  // Validate parameter names
  if (optional_params.parameter_name) {
    for (const parameter of optional_params.parameter_name) {
      if (!this.supported_parameters[parameter]) {
        throw new Error(
          `The following parameter name does not exist on this collection: '${parameter}'.`
        );
      }
    }
  }

  // Validate CRS
  if (optional_params.crs !== undefined) {
    if (!this.supported_crs.includes(optional_params.crs)) {
      throw new Error(
        `The following crs does not exist on this collection: '${optional_params.crs}'.`
      );
    }
  }
}
```

**What's validated:**

- Query type availability
- Parameter name existence
- CRS support

**What's NOT validated:**

- Coordinate format
- DateTime string format
- Numeric ranges (except logical bounds)

### Pattern 3: Assert Required Links

**Used by:** link-utils.ts

```typescript
export function assertHasLinks(
  doc: OgcApiDocument,
  relType: string | string[]
) {
  if (!hasLinks(doc, relType)) {
    throw new EndpointError(`Could not find link with type: ${relType}`);
  }
}
```

**Usage:**

```typescript
// In info.ts
assertHasLinks(rootDoc, ['service-doc', 'service-desc']);
assertHasLinks(rootDoc, [
  'conformance',
  'http://www.opengis.net/def/rel/ogc/1.0/conformance',
]);
```

**Pattern:**

- Validate critical links exist
- Fail fast with clear message
- Use at initialization time

### Pattern 4: Warn Instead of Error

**Used by:** endpoint.ts for optional features

```typescript
if (options?.outputFormat && !linkWithFormat) {
  console.warn(
    `[ogc-client] The following output format type was not found in the collection '${collectionId}': ${options.outputFormat}`
  );
  // Still add as query parameter (server may support it)
  url.searchParams.set('f', options.outputFormat);
}
```

**When to warn vs throw:**

- ✅ Warn: Optional feature may still work
- ❌ Throw: Required feature missing

---

## 4. Validation Errors

### What Gets Validated

**EDR validates:**

1. **Query type availability:**

   ```typescript
   if (!this.supported_query_types.position) {
     throw new Error('Collection does not support position queries');
   }
   ```

2. **Parameter existence:**

   ```typescript
   if (!this.supported_parameters[parameter]) {
     throw new Error(
       `Parameter '${parameter}' does not exist on this collection`
     );
   }
   ```

3. **CRS support:**

   ```typescript
   if (!this.supported_crs.includes(crs)) {
     throw new Error(`CRS '${crs}' not supported by this collection`);
   }
   ```

4. **Logical bounds:**
   ```typescript
   if (minX > maxX) {
     throw new Error('minX must be less than or equal to maxX');
   }
   ```

### What Doesn't Get Validated

**Trust TypeScript types:**

- No runtime type checking
- No instanceof checks
- No property existence checks (beyond null/undefined)

**Trust server:**

- Coordinate format validity
- DateTime ISO 8601 format
- URL validity
- JSON schema compliance

**Trust user:**

- Parameter values within valid ranges
- Format strings (MIME types)
- Resource IDs exist

### Validation Strategy

**Principle:** Validate **only** what library needs to function correctly.

**Examples:**

✅ **Validate:** Collection supports query type (library needs this info)

```typescript
if (!this.supported_query_types.area) {
  throw new Error('Collection does not support area queries');
}
```

❌ **Don't validate:** Coordinate string format (server will validate)

```typescript
// ❌ Don't do this:
if (!/^POINT\(.+\)$/.test(coords)) {
  throw new Error('Invalid WKT format');
}
```

✅ **Validate:** Parameter name exists in collection metadata

```typescript
if (!this.supported_parameters[param]) {
  throw new Error(`Parameter '${param}' not in collection`);
}
```

❌ **Don't validate:** Parameter value is reasonable

```typescript
// ❌ Don't do this:
if (limit < 1 || limit > 10000) {
  throw new Error('Limit must be between 1 and 10000');
}
```

---

## 5. Missing Resource Errors

### Collection Not Found

**Pattern in endpoint.ts:**

```typescript
async getCollectionInfo(collectionId: string): Promise<OgcApiCollectionInfo> {
  const collection = allCollections.find((c) => c.id === collectionId);
  if (!collection) {
    throw new EndpointError(`Collection not found: ${collectionId}`);
  }
  return collection;
}
```

**When to check:**

- Collection lookup in endpoint methods
- Before creating QueryBuilder

**Not checked:**

- Individual resource IDs (e.g., system-123)
- Sub-resources (e.g., datastream items)

**Reason:** Server validates resource existence via HTTP 404.

### Link Not Found

**Pattern in link-utils.ts:**

```typescript
export function getLinkUrl(
  doc: OgcApiDocument,
  rel: string | string[],
  baseUrl: string,
  mimeType?: MimeType,
  required?: boolean
): string | null {
  const links = getLinks(doc, rel, mimeType, required);
  if (required && !links.length) {
    throw new EndpointError(
      `Could not find link with required type. This might not be a compliant OGC API endpoint.`
    );
  }
  return links[0]?.href || null;
}
```

**Pattern:**

- Optional `required` flag
- Returns null if not required and not found
- Throws EndpointError if required and not found

### Style/Resource Not Found

**Pattern in endpoint.ts:**

```typescript
const style = allStyles.find((s) => s.id === styleId);
if (!style) {
  throw new EndpointError(`Style not found: "${styleId}".`);
}
```

**Consistent pattern:**

1. Look up resource in collection/list
2. If not found, throw EndpointError
3. Use descriptive message with ID

---

## 6. Conformance Errors

### Non-Conforming Endpoints

**Pattern in endpoint.ts:**

```typescript
private get root(): Promise<OgcApiDocument> {
  if (!this.root_) {
    this.root_ = fetchRoot(this.baseUrl).catch((e) => {
      throw new Error(`The endpoint appears non-conforming, the following error was encountered:
${e.message}`);
    });
  }
  return this.root_;
}
```

**Pattern in info.ts:**

```typescript
export function parseEndpointInfo(rootDoc: OgcApiDocument): OgcApiEndpointInfo {
  try {
    assertHasLinks(rootDoc, ['service-doc', 'service-desc']);
    assertHasLinks(rootDoc, [
      'conformance',
      'http://www.opengis.net/def/rel/ogc/1.0/conformance',
    ]);
  } catch (e) {
    throw new EndpointError(`The endpoint appears non-conforming, the following error was encountered:
${e.message}`);
  }
  // ...
}
```

**Conformance checks:**

1. Root document fetchable
2. Required links present
3. Conformance classes advertised

**Not checked:**

- Full OGC API compliance
- All optional features
- Response format validity

### Missing API Support

**Pattern in endpoint.ts:**

```typescript
public async edr(collection_id: string): Promise<EDRQueryBuilder> {
  if (!this.hasEnvironmentalDataRetrieval) {
    throw new EndpointError('Endpoint does not support EDR');
  }
  // ...
}
```

**Simple conformance check:**

- Based on conformance class URIs
- Checked before creating QueryBuilder
- Clear error message

---

## 7. Network Errors

### Fetch Errors

**ogc-client lets fetch errors propagate:**

```typescript
// No try-catch around fetch
const response = await fetch(url);
const data = await response.json();
```

**Not caught:**

- Network timeouts
- DNS resolution failures
- TLS/SSL errors
- CORS errors (mostly)

**Reason:** Users can handle fetch errors themselves.

### CORS Detection

**Limited CORS detection in http-utils.ts:**

```typescript
return sharedFetch(url).catch(() =>
  // attempt a HEAD to see if failure comes from CORS or unreachable host
  fetch(url, { ...getFetchOptions(), method: 'HEAD', mode: 'no-cors' })
    .catch((error) => {
      throw new EndpointError(
        `Fetching the document failed either due to network errors or unreachable host, error is: ${error.message}`,
        0,
        false
      );
    })
    .then(() => {
      throw new EndpointError(
        `Fetching the document failed likely due to CORS configuration of the endpoint.`,
        0,
        true
      );
    })
);
```

**Pattern:**

- Try normal fetch
- On failure, try no-cors HEAD
- If HEAD succeeds, assume CORS issue
- Set `isCrossOriginRelated` flag

**Used only in XML parsing** - not in OGC API JSON fetching.

---

## 8. User Error vs Library Error

### Library Errors (Library Throws)

**When library throws:**

1. **Library can't proceed:**

   ```typescript
   throw new EndpointError('Endpoint does not support EDR');
   ```

2. **Required data missing:**

   ```typescript
   throw new EndpointError(`Collection not found: ${collectionId}`);
   ```

3. **Invalid library state:**

   ```typescript
   throw new Error('No data queries found, so cannot issue EDR queries');
   ```

4. **Logical impossibility:**
   ```typescript
   throw new Error('minX must be less than or equal to maxX');
   ```

### User Errors (Server Returns HTTP Error)

**When library doesn't throw (lets server validate):**

1. **Invalid resource ID:**

   ```typescript
   // User requests:
   const url = await builder.getSystem('invalid-id');
   const response = await fetch(url);
   // Server returns: 404 Not Found
   ```

2. **Invalid parameter values:**

   ```typescript
   // User requests:
   const url = await builder.getSystems({ limit: 999999 });
   // Server returns: 400 Bad Request
   ```

3. **Invalid format string:**

   ```typescript
   // User requests:
   const url = await builder.getSystems({ f: 'invalid/format' });
   // Server returns: 406 Not Acceptable
   ```

4. **Unauthorized access:**
   ```typescript
   // Server returns: 401 Unauthorized or 403 Forbidden
   ```

### Decision Matrix

| Scenario                    | Library Action              | Reason                             |
| --------------------------- | --------------------------- | ---------------------------------- |
| Non-CSAPI endpoint          | Throw EndpointError         | Library can detect via conformance |
| Collection not found        | Throw EndpointError         | Library has collection list        |
| Query type not supported    | Throw Error                 | Library has collection metadata    |
| Parameter not in collection | Throw Error                 | Library has parameter list         |
| Invalid system ID           | Let server handle           | Library doesn't know all IDs       |
| Invalid limit value         | Let server handle           | Library doesn't know limits        |
| Invalid bbox coordinates    | Let server handle           | Server validates geometry          |
| Missing required parameter  | Let TypeScript types handle | Compile-time checking              |

---

## 9. CSAPI Error Strategy

### Error Categories

**4 error categories for CSAPI:**

1. **Conformance errors** - Endpoint doesn't support CSAPI
2. **Collection errors** - Collection not found
3. **Validation errors** - Invalid parameters library can detect
4. **Network/server errors** - Let propagate

### Conformance Errors

**Pattern: Check before factory method**

```typescript
// In endpoint.ts
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  // ...
}
```

**Single check, early failure.**

### Collection Errors

**Pattern: Validate collection exists**

```typescript
// In endpoint.ts (already done by getCollectionInfo)
const collection = await this.getCollectionInfo(collection_id);
// Throws EndpointError if not found
```

**Reuse existing validation.**

### Validation Errors

**What CSAPI should validate:**

1. **Resource type support (optional):**

   ```typescript
   // If collection metadata includes supported resources
   if (this.collection_.supportedResources) {
     if (!this.collection_.supportedResources.includes('systems')) {
       throw new Error('Collection does not support systems resource');
     }
   }
   ```

2. **Logical bounds:**
   ```typescript
   // Only if library performs calculation
   if (options.limit !== undefined && options.limit < 1) {
     throw new Error('Limit must be positive');
   }
   ```

**What CSAPI should NOT validate:**

1. ❌ Resource ID format
2. ❌ Property existence (beyond TypeScript)
3. ❌ Numeric ranges (let server decide)
4. ❌ DateTime format
5. ❌ BBox coordinate validity
6. ❌ Format string validity

### Recommended CSAPI Errors

**Minimal validation strategy:**

```typescript
export default class CSAPIQueryBuilder {
  constructor(collection: OgcApiCollectionInfo) {
    // No validation in constructor
    this.collection_ = collection;
    this.cache_ = new Map();
  }

  async getSystems(options?: SystemQueryOptions): Promise<string> {
    // No validation - just build URL
    const baseUrl = getLinkUrl(
      this.collection_,
      ['systems', 'http://www.opengis.net/def/rel/ogc/1.0/systems'],
      this.baseUrl
    );

    // getLinkUrl throws if link not found (library needs link)

    return this.buildUrl(baseUrl, options);
  }

  async getSystem(systemId: string): Promise<string> {
    // No validation of systemId - server will 404 if invalid
    const collectionUrl = await this.getSystems();
    return getChildPath(collectionUrl, systemId);
  }

  private buildUrl(base: string, options?: QueryOptions): string {
    const url = new URL(base);

    // No validation of parameter values - server validates
    if (options?.limit) url.searchParams.set('limit', options.limit.toString());
    if (options?.bbox) url.searchParams.set('bbox', options.bbox.join(','));
    // ... more params

    return url.toString();
  }
}
```

**Result:** ~0 explicit error throws in CSAPIQueryBuilder.

**Errors come from:**

- `getLinkUrl()` - throws if required link missing
- `new URL()` - throws if URL construction fails
- Native TypeScript - throws if accessing undefined

---

## 10. Complete Error Handling Design

### Error Handling Checklist

**For CSAPI:**

#### Conformance Check (endpoint.ts)

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
  // getCollectionInfo throws EndpointError if collection not found
  const result = new CSAPIQueryBuilder(collection);
  cache.set(collection_id, result);
  return result;
}
```

**Errors thrown:**

- `EndpointError` - Endpoint doesn't support CSAPI
- `EndpointError` - Collection not found (from getCollectionInfo)

#### URL Builder (url_builder.ts)

```typescript
export default class CSAPIQueryBuilder {
  private collection_: OgcApiCollectionInfo;
  private cache_: Map<string, any>;

  constructor(collection: OgcApiCollectionInfo) {
    // No validation - trust endpoint.ts
    this.collection_ = collection;
    this.cache_ = new Map();
  }

  async getSystems(options?: SystemQueryOptions): Promise<string> {
    const baseUrl = getLinkUrl(
      this.collection_,
      ['systems', 'http://www.opengis.net/def/rel/ogc/1.0/systems'],
      this.baseUrl,
      undefined,
      true // required = true
    );
    // getLinkUrl throws EndpointError if link not found

    return this.buildUrl(baseUrl, options);
  }

  async getSystem(systemId: string): Promise<string> {
    const collectionUrl = await this.getSystems();
    return getChildPath(collectionUrl, systemId);
  }

  // ... 16 more resource methods (similar pattern)

  private buildUrl(base: string, options?: QueryOptions): string {
    // No validation - trust types and server
    const url = new URL(base);

    if (options?.limit) {
      url.searchParams.set('limit', options.limit.toString());
    }

    if (options?.offset) {
      url.searchParams.set('offset', options.offset.toString());
    }

    if (options?.bbox) {
      url.searchParams.set('bbox', options.bbox.join(','));
    }

    if (options?.datetime) {
      url.searchParams.set('datetime', formatDateTime(options.datetime));
    }

    if (options?.f) {
      url.searchParams.set('f', options.f);
    }

    return url.toString();
  }
}
```

**Errors thrown:**

- `EndpointError` - Required link not found (from getLinkUrl)
- Native errors - URL construction fails (from new URL)

**No explicit validation errors.**

### Error Messages

**Clear, actionable messages:**

✅ **Good:**

```typescript
throw new EndpointError('Endpoint does not support Connected Systems API');
throw new EndpointError(`Collection not found: ${collectionId}`);
```

❌ **Bad (too vague):**

```typescript
throw new Error('Invalid input');
throw new Error('Operation failed');
```

❌ **Bad (too prescriptive):**

```typescript
throw new Error(
  'The systemId parameter must be a valid UUID matching RFC 4122'
);
```

### Error Handling Summary

**CSAPI error strategy:**

| Error Type               | When                       | Where          | Class                           |
| ------------------------ | -------------------------- | -------------- | ------------------------------- |
| No CSAPI support         | Endpoint conformance check | endpoint.ts    | EndpointError                   |
| Collection not found     | Factory method             | endpoint.ts    | EndpointError                   |
| Required link missing    | URL building               | url_builder.ts | EndpointError (from getLinkUrl) |
| Invalid URL construction | URL building               | url_builder.ts | Native Error                    |
| Everything else          | Server validation          | N/A            | HTTP status codes               |

**Total explicit error throws in CSAPI code:** 1 (conformance check)

**Result:** Minimal error handling, trust TypeScript types and server validation.

---

## Summary

### Key Findings

1. **Two error classes** - EndpointError (general), ServiceExceptionError (XML only)
2. **Minimal validation** - Only what library needs to function
3. **Trust server** - Let HTTP errors propagate
4. **Trust TypeScript** - No runtime type checking
5. **Clear messages** - Descriptive, actionable error text
6. **Fail fast** - Check conformance before operations
7. **No custom CSAPI errors** - Reuse EndpointError and Error

### CSAPI Error Handling Checklist

✅ **Implementation:**

- [x] Conformance check in endpoint.csapi() method
- [x] Reuse getCollectionInfo() for collection validation
- [x] Let getLinkUrl() handle missing links
- [x] No parameter validation in QueryBuilder
- [x] No resource ID validation
- [x] No custom error classes

✅ **Error count:**

- Explicit throws: 1 (conformance check)
- Implicit throws: 2-3 (from utilities)
- Total error handling code: ~3 lines

✅ **Result:** Minimal, clear error handling following established patterns.

---

## Conclusion

CSAPI should use **minimal error handling** following EDR pattern:

**Only throw when:**

1. Endpoint doesn't support CSAPI (conformance check)
2. Collection not found (reuse existing validation)
3. Required link missing (let getLinkUrl throw)

**Never throw for:**

- Resource ID validation
- Parameter value validation
- Format validation
- Server-side constraints

**Total error handling code:** ~3 lines, maximum trust in TypeScript types and server validation.
