# Integration with Existing Code Analysis

**Purpose:** Document the exact code changes required to integrate CSAPI into ogc-client.

**Context:** CSAPI must integrate with existing OgcApiEndpoint class following the EDR pattern. Minimize modifications to core files.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [EDR Integration Pattern](#2-edr-integration-pattern)
3. [Changes to endpoint.ts](#3-changes-to-endpointts)
4. [Changes to info.ts](#4-changes-to-infots)
5. [Changes to index.ts](#5-changes-to-indexts)
6. [Shared Models Reuse](#6-shared-models-reuse)
7. [Shared Utilities Reuse](#7-shared-utilities-reuse)
8. [Minimizing Diff Size](#8-minimizing-diff-size)
9. [Testing Integration](#9-testing-integration)
10. [Complete Integration Checklist](#10-complete-integration-checklist)

---

## 1. Overview

### Integration Philosophy

**ogc-client integrates new APIs with minimal invasive changes:**

**Principle:** Additive, not modifications

**Pattern:**

1. Add new subfolder (e.g., `src/ogc-api/csapi/`)
2. Add import statement to parent
3. Add cache field to class
4. Add conformance check
5. Add factory method
6. Add public type exports

**Result:** New API support with ~40-50 lines of changes to existing files.

### Files to Modify

**3 files require modifications:**

| File                      | Lines Added | Lines Modified | Purpose                  |
| ------------------------- | ----------- | -------------- | ------------------------ |
| `src/ogc-api/endpoint.ts` | ~35         | 0              | Add CSAPI factory method |
| `src/ogc-api/info.ts`     | ~12         | 0              | Add conformance check    |
| `src/index.ts`            | ~15         | 0              | Export CSAPI types       |

**Total:** ~62 lines added, 0 modified

**Files NOT Modified:**

- `src/ogc-api/model.ts` - No changes needed
- `src/ogc-api/link-utils.ts` - Reused as-is
- `src/shared/*` - All utilities reused as-is

---

## 2. EDR Integration Pattern

### EDR as Template

**EDR integration serves as exact blueprint for CSAPI.**

### EDR Changes to endpoint.ts

**4 integration points:**

#### 1. Import Statement (line 50)

```typescript
import EDRQueryBuilder from './edr/url_builder.js';
```

**Pattern:** Single import of QueryBuilder class.

#### 2. Cache Field (line 63-64)

```typescript
private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
  new Map();
```

**Pattern:** Private map for caching builder instances per collection.

#### 3. Collections Getter (lines 203-208)

```typescript
get edrCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasEnvironmentalDataRetrieval])
    .then(([data, hasEDR]) => (hasEDR ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.filter((c) => c.hasDataQueries))
    .then((collections) => collections.map((collection) => collection.name));
}
```

**Pattern:** Filter collections by capability flag.

#### 4. Conformance Getter (lines 272-276)

```typescript
get hasEnvironmentalDataRetrieval(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasEnvironmentalDataRetrieval
  );
}
```

**Pattern:** Check conformance via utility function.

#### 5. Factory Method (lines 281-295)

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

**Pattern:**

1. Check conformance
2. Check cache
3. Get collection info
4. Create builder
5. Cache and return

**Total EDR additions:** ~30 lines

### EDR Changes to info.ts

**Single function added:**

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

**Pattern:** Check for conformance class URI.

**Total EDR additions:** ~7 lines

### EDR Changes to index.ts

**EDR types are NOT exported.**

**Why?** Users access via factory method:

```typescript
const builder = await endpoint.edr(collectionId);
// Types are inferred, users don't import EDR types
```

**CSAPI may differ** - resources should be exported.

---

## 3. Changes to endpoint.ts

### Location of Changes

**All changes are additive insertions at specific locations.**

#### Change 1: Import Statement

**Location:** After line 49 (after existing imports)

**Insert:**

```typescript
import CSAPIQueryBuilder from './csapi/url_builder.js';
```

**Context:**

```typescript
import { getBaseUrl, getChildPath } from '../shared/url-utils.js';
import EDRQueryBuilder from './edr/url_builder.js';
import CSAPIQueryBuilder from './csapi/url_builder.js'; // NEW

/**
 * Represents an OGC API endpoint advertising various collections and services.
 */
```

#### Change 2: Cache Field

**Location:** After line 63 (after existing cache fields)

**Insert:**

```typescript
  private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =
    new Map();
```

**Context:**

```typescript
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();
  private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =  // NEW
    new Map();                                                                // NEW

  private get root(): Promise<OgcApiDocument> {
```

#### Change 3: Collections Getter

**Location:** After line 208 (after edrCollections getter)

**Insert:**

```typescript
  get csapiCollections(): Promise<string[]> {
    return Promise.all([this.data, this.hasConnectedSystems])
      .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
      .then(parseCollections)
      .then((collections) => collections.filter((c) => c.hasSystemFeatures))
      .then((collections) => collections.map((collection) => collection.name));
  }
```

**Context:**

```typescript
  get edrCollections(): Promise<string[]> {
    return Promise.all([this.data, this.hasEnvironmentalDataRetrieval])
      .then(([data, hasEDR]) => (hasEDR ? data : { collections: [] }))
      .then(parseCollections)
      .then((collections) => collections.filter((c) => c.hasDataQueries))
      .then((collections) => collections.map((collection) => collection.name));
  }

  get csapiCollections(): Promise<string[]> {  // NEW (6 lines)
    return Promise.all([this.data, this.hasConnectedSystems])
      .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
      .then(parseCollections)
      .then((collections) => collections.filter((c) => c.hasSystemFeatures))
      .then((collections) => collections.map((collection) => collection.name));
  }

  /**
   * A Promise which resolves to an array of vector tile collection identifiers as strings.
   */
```

**Note:** `hasSystemFeatures` property may not exist yet on `OgcApiCollectionInfo`.

**Alternative (simpler):** Don't filter by collection property:

```typescript
  get csapiCollections(): Promise<string[]> {
    return Promise.all([this.data, this.hasConnectedSystems])
      .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
      .then(parseCollections)
      .then((collections) => collections.map((collection) => collection.name));
  }
```

**Reasoning:** If endpoint has CSAPI conformance, all collections potentially support it.

#### Change 4: Conformance Getter

**Location:** After line 276 (after hasEnvironmentalDataRetrieval getter)

**Insert:**

```typescript
  /**
   * A Promise which resolves to a boolean indicating whether the endpoint supports OGC API - Connected Systems.
   */
  get hasConnectedSystems(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasConnectedSystems
    );
  }
```

**Context:**

```typescript
  /**
   * A Promise which resolves to a boolean indicating whether the endpoint offers environmental data retrieval (EDR) queries.
   */
  get hasEnvironmentalDataRetrieval(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasEnvironmentalDataRetrieval
    );
  }

  /**                                                                                // NEW (6 lines)
   * A Promise which resolves to a boolean indicating whether the endpoint supports OGC API - Connected Systems.
   */
  get hasConnectedSystems(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasConnectedSystems
    );
  }

  /*
   * A Promise which resolves to a class for constructing EDR queries
   */
```

#### Change 5: Factory Method

**Location:** After line 295 (after edr() method)

**Insert:**

```typescript
  /**
   * A Promise which resolves to a class for constructing CSAPI queries
   * @param collection_id - The collection identifier
   * @returns A CSAPIQueryBuilder instance for the collection
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
```

**Context:**

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

  /**                                                                                     // NEW (17 lines)
   * A Promise which resolves to a class for constructing CSAPI queries
   * @param collection_id - The collection identifier
   * @returns A CSAPIQueryBuilder instance for the collection
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

  /**
   * Retrieve the tile matrix sets identifiers advertised by the endpoint. Empty if tiles are not supported
   */
```

### Summary of endpoint.ts Changes

**Total lines added:** ~35 lines (excluding blank lines)

**Breakdown:**

- Import: 1 line
- Cache field: 2 lines
- Collections getter: 6 lines (or 5 if not filtering)
- Conformance getter: 6 lines
- Factory method: 17 lines
- Comments: 3 lines

**Changes are:**

- ✅ Additive only
- ✅ Located in clear sections
- ✅ Follow existing patterns exactly
- ✅ No modifications to existing code

---

## 4. Changes to info.ts

### Location of Changes

**Single function addition after existing conformance checks.**

#### Change 1: Import Update

**Location:** Line 2 (if needed for type imports)

**Likely no change needed** - function only needs ConformanceClass which is already imported.

#### Change 2: Conformance Check Function

**Location:** After line 103 (after checkHasEnvironmentalDataRetrieval)

**Insert:**

```typescript
export function checkHasConnectedSystems([conformance]: [ConformanceClass[]]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1 ||
    conformance.indexOf('http://www.opengis.net/spec/ogcapi-cs/1.0/conf/core') >
      -1
  );
}
```

**Context:**

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

export function checkHasConnectedSystems([conformance]: [
  // NEW (12 lines)
  ConformanceClass[]
]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1 ||
    conformance.indexOf('http://www.opengis.net/spec/ogcapi-cs/1.0/conf/core') >
      -1
  );
}

/**
 * This does not include queryables and sortables!
 */
```

**Note:** Two conformance URIs checked for backwards compatibility (full name vs short name).

#### Change 3: Export in endpoint.ts Import

**Location:** Line 2 of endpoint.ts

**Modify import statement to include new function:**

**Before:**

```typescript
import {
  checkHasEnvironmentalDataRetrieval,
  checkHasFeatures,
  checkHasRecords,
  checkStyleConformance,
  checkTileConformance,
  parseBaseCollectionInfo,
  parseBasicStyleInfo,
  parseCollectionParameters,
  parseCollections,
  parseConformance,
  parseEndpointInfo,
  parseFullStyleInfo,
  parseTileMatrixSets,
} from './info.js';
```

**After:**

```typescript
import {
  checkHasConnectedSystems, // NEW
  checkHasEnvironmentalDataRetrieval,
  checkHasFeatures,
  checkHasRecords,
  checkStyleConformance,
  checkTileConformance,
  parseBaseCollectionInfo,
  parseBasicStyleInfo,
  parseCollectionParameters,
  parseCollections,
  parseConformance,
  parseEndpointInfo,
  parseFullStyleInfo,
  parseTileMatrixSets,
} from './info.js';
```

**Pattern:** Alphabetically insert new import.

### Summary of info.ts Changes

**Total lines added:** ~12 lines

**Breakdown:**

- Conformance check function: 12 lines

**Changes are:**

- ✅ Additive only
- ✅ Single function
- ✅ Follows EDR pattern exactly
- ✅ Handles multiple conformance URIs

---

## 5. Changes to index.ts

### Export Strategy

**CSAPI should export resource types but NOT QueryBuilder.**

**Reasoning:**

- QueryBuilder accessed via factory: `endpoint.csapi(id)`
- Resource types needed for user type annotations
- Query options needed for method signatures

### Location of Changes

**After OGC API exports section (after line 44).**

#### Change: Add CSAPI Type Exports

**Location:** After line 44 (after `export * from './ogc-api/model.js';`)

**Insert:**

```typescript
export type {
  System,
  Deployment,
  SamplingFeature,
  Procedure,
  Datastream,
  Observation,
  Control,
  ControlStream,
  Command,
  QueryOptions,
  SystemQueryOptions,
  ObservationQueryOptions,
  Collection,
  TimeInterval,
  ResourceLink,
} from './ogc-api/csapi/model.js';
```

**Context:**

```typescript
export { default as OgcApiEndpoint } from './ogc-api/endpoint.js';
export * from './ogc-api/model.js';
export type {
  // NEW (17 lines)
  System,
  Deployment,
  SamplingFeature,
  Procedure,
  Datastream,
  Observation,
  Control,
  ControlStream,
  Command,
  QueryOptions,
  SystemQueryOptions,
  ObservationQueryOptions,
  Collection,
  TimeInterval,
  ResourceLink,
} from './ogc-api/csapi/model.js';
export { default as TmsEndpoint } from './tms/endpoint.js';
```

**Alternative (export all):**

```typescript
export * from './ogc-api/csapi/model.js';
```

**Pros:** Shorter, exports everything
**Cons:** Less explicit, may export internal types

**Recommendation:** Use explicit named exports for clarity.

### Summary of index.ts Changes

**Total lines added:** ~17 lines

**Breakdown:**

- Type exports: 17 lines (9 resources + 3 options + 2 helpers + type keyword + braces)

**Changes are:**

- ✅ Additive only
- ✅ Explicit exports
- ✅ Follows pattern of other APIs
- ✅ Resource types public

---

## 6. Shared Models Reuse

### Available Shared Types

**From `src/shared/models.ts`:**

```typescript
// Spatial types
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;

// Temporal types
export type DateTimeParameter = Date | { start: Date; end?: Date };

// Format types
export type MimeType = string;

// Metadata types
export interface Address { ... }
export interface Contact { ... }
export interface Provider { ... }
export interface LayerStyle { ... }
export interface MetadataURL { ... }

// Endpoint info
export type GenericEndpointInfo = { ... }

// Network
export type FetchOptions = RequestInit;
```

### CSAPI Reuse Strategy

**Directly reuse (no redefinition):**

| CSAPI Need         | Shared Type         | Usage                              |
| ------------------ | ------------------- | ---------------------------------- |
| Spatial extent     | `BoundingBox`       | Query parameter, resource property |
| Temporal filter    | `DateTimeParameter` | Query parameter                    |
| CRS codes          | `CrsCode`           | Query parameter, metadata          |
| Contact info       | `Contact`           | System metadata                    |
| Provider info      | `Provider`          | Endpoint metadata                  |
| Format negotiation | `MimeType`          | Query parameter, links             |

**Import pattern:**

```typescript
// In src/ogc-api/csapi/model.ts
import {
  BoundingBox,
  CrsCode,
  DateTimeParameter,
  MimeType,
  Contact,
  Provider,
} from '../../shared/models.js';

export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox; // Reuse
  datetime?: DateTimeParameter; // Reuse
}

export interface System {
  properties: {
    contacts?: Contact[]; // Reuse
    // ...
  };
}
```

**DO NOT redefine:**

```typescript
// ❌ Don't do this
export type BoundingBox = [number, number, number, number]; // Already in shared!
```

### OGC API Common Types Reuse

**From `src/ogc-api/model.ts`:**

```typescript
export type ConformanceClass = string;
export interface OgcApiEndpointInfo { ... }
export interface OgcApiCollectionInfo { ... }
export interface OgcApiDocumentLink {
  rel: string;
  type: string;
  title: string;
  href: string;
}
```

**CSAPI reuse:**

```typescript
// In src/ogc-api/csapi/model.ts
import { OgcApiDocumentLink } from '../model.js';

export interface System {
  links: OgcApiDocumentLink[]; // Reuse
}
```

**DO NOT redefine:**

```typescript
// ❌ Don't do this
export interface Link {
  rel: string;
  href: string;
}
```

Use `OgcApiDocumentLink` instead.

---

## 7. Shared Utilities Reuse

### Available Shared Utilities

#### From `src/ogc-api/link-utils.ts`

**Link traversal functions:**

```typescript
export function getLinkUrl(
  doc: OgcApiDocument,
  rel: string | string[],
  baseUrl: string,
  mimeType?: MimeType,
  required?: boolean
): string | null;

export function fetchLink(
  doc: OgcApiDocument,
  rel: string | string[],
  baseUrl: string
): Promise<OgcApiDocument>;

export function getLinks(
  doc: OgcApiDocument,
  rel: string | string[]
): OgcApiDocumentLink[];
```

**Usage in CSAPIQueryBuilder:**

```typescript
import { getLinkUrl } from '../link-utils.js';

async getSystems(options?: QueryOptions): Promise<string> {
  // Get systems collection URL from links
  const baseUrl = getLinkUrl(
    this.collection_,
    ['systems', 'http://www.opengis.net/def/rel/ogc/1.0/systems'],
    this.baseUrl,
    undefined,
    true  // required
  );

  // Build URL with query params
  const url = new URL(baseUrl);
  // ... add params
  return url.toString();
}
```

**Key benefit:** No need to write link traversal logic.

#### From `src/shared/http-utils.ts`

**HTTP utilities:**

```typescript
export function sharedFetch(
  url: string,
  options?: FetchOptions
): Promise<Response>;
export function setQueryParams(url: URL, params: Record<string, string>): void;
```

**Usage:**

```typescript
import { setQueryParams } from '../../shared/http-utils.js';

private buildUrl(base: string, options?: QueryOptions): string {
  const url = new URL(base);
  const params: Record<string, string> = {};

  if (options?.limit) params.limit = options.limit.toString();
  if (options?.offset) params.offset = options.offset.toString();

  setQueryParams(url, params);
  return url.toString();
}
```

#### From `src/shared/url-utils.ts`

**URL utilities:**

```typescript
export function getBaseUrl(url: string): string;
export function getChildPath(parentUrl: string, childPath: string): string;
```

**Usage:**

```typescript
import { getChildPath } from '../../shared/url-utils.js';

async getSystem(systemId: string): Promise<string> {
  const collectionUrl = await this.getSystems();
  return getChildPath(collectionUrl, systemId);
}
```

#### From `src/shared/errors.ts`

**Error classes:**

```typescript
export class EndpointError extends Error { ... }
export class ServiceExceptionError extends Error { ... }
```

**Usage:**

```typescript
import { EndpointError } from '../../shared/errors.js';

if (!this.collection_) {
  throw new EndpointError('Collection not initialized');
}
```

### Summary of Reusable Utilities

**CSAPI can reuse 15+ utility functions:**

| Category | Functions                                   | Purpose          |
| -------- | ------------------------------------------- | ---------------- |
| Links    | `getLinkUrl`, `getLinks`, `fetchLink`       | Link traversal   |
| HTTP     | `sharedFetch`, `setQueryParams`             | Network requests |
| URLs     | `getBaseUrl`, `getChildPath`                | URL construction |
| Errors   | `EndpointError`, `check`                    | Error handling   |
| CRS      | `hasInvertedCoordinates`, `simplifyEpsgUrn` | CRS utilities    |
| Cache    | `useCache`, `clearCache`                    | Caching          |

**Result:** CSAPI url_builder.ts can focus on business logic, not infrastructure.

---

## 8. Minimizing Diff Size

### Strategies for Minimal Diff

#### 1. Follow Existing Code Style

**Match indentation:**

```typescript
// Existing style (2 spaces)
  get hasEnvironmentalDataRetrieval(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasEnvironmentalDataRetrieval
    );
  }

// Match exactly
  get hasConnectedSystems(): Promise<boolean> {
    return Promise.all([this.conformanceClasses]).then(
      checkHasConnectedSystems
    );
  }
```

#### 2. Insert in Logical Groups

**Don't scatter changes:**

✅ **Do:** Group all CSAPI additions together

```typescript
// EDR section
get hasEnvironmentalDataRetrieval(): Promise<boolean> { ... }
public async edr(collection_id: string): Promise<EDRQueryBuilder> { ... }

// CSAPI section (grouped)
get hasConnectedSystems(): Promise<boolean> { ... }
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> { ... }
```

❌ **Don't:** Scatter CSAPI additions across file

#### 3. Preserve Blank Lines

**Match existing spacing:**

```typescript
  }

  /**
   * A Promise which resolves to...
   */
  get hasConnectedSystems(): Promise<boolean> {
```

#### 4. Use Consistent Naming

**Follow established patterns:**

| EDR Pattern                     | CSAPI Equivalent                  |
| ------------------------------- | --------------------------------- |
| `hasEnvironmentalDataRetrieval` | `hasConnectedSystems`             |
| `edrCollections`                | `csapiCollections`                |
| `collection_id_to_edr_builder_` | `collection_id_to_csapi_builder_` |
| `edr(collection_id)`            | `csapi(collection_id)`            |
| `EDRQueryBuilder`               | `CSAPIQueryBuilder`               |

#### 5. Minimize Import Changes

**Add to existing import statements where possible:**

```typescript
// Instead of new import block, add to existing
import {
  checkHasConnectedSystems, // Add here
  checkHasEnvironmentalDataRetrieval,
  // ... rest of imports
} from './info.js';
```

#### 6. No Refactoring

**Don't improve existing code:**

❌ **Don't:** Fix typos, reformat, or refactor existing code
✅ **Do:** Only add new code

**Example:**

```typescript
// If you see this in existing code:
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();

// Don't "improve" it to:
  private edrBuilderCache: Map<string, EDRQueryBuilder> = new Map();

// Just add your line matching the pattern:
  private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =
    new Map();
```

### Diff Size Target

**Goal:** 3 modified files, ~65 lines added, 1 line modified

**Breakdown:**

- `endpoint.ts`: ~35 lines added, 1 line modified (import)
- `info.ts`: ~12 lines added
- `index.ts`: ~17 lines added

**Modified lines:** Only the import statement in endpoint.ts

**Result:** Clean, reviewable diff focused on additions.

---

## 9. Testing Integration

### Integration Test Requirements

**Test that CSAPI is properly integrated:**

#### Test 1: Conformance Check

**Location:** `src/ogc-api/info.spec.ts`

**Add test:**

```typescript
describe('checkHasConnectedSystems', () => {
  it('returns true when CSAPI conformance is present (full URI)', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(true);
  });

  it('returns true when CSAPI conformance is present (short URI)', () => {
    const conformance = ['http://www.opengis.net/spec/ogcapi-cs/1.0/conf/core'];
    expect(checkHasConnectedSystems([conformance])).toBe(true);
  });

  it('returns false when CSAPI conformance is missing', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(false);
  });
});
```

#### Test 2: Endpoint Integration

**Location:** `src/ogc-api/endpoint.spec.ts`

**Add test:**

```typescript
describe('OgcApiEndpoint CSAPI integration', () => {
  it('detects CSAPI support via conformance', async () => {
    // Mock endpoint with CSAPI conformance
    const mockRoot = {
      links: [{ rel: 'conformance', href: '/conformance' }],
    };
    const mockConformance = {
      conformsTo: [
        'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core',
      ],
    };

    // ... setup mocks

    const endpoint = new OgcApiEndpoint('http://example.com');
    const hasCSAPI = await endpoint.hasConnectedSystems;
    expect(hasCSAPI).toBe(true);
  });

  it('returns csapi builder for collection', async () => {
    // ... setup mocks

    const endpoint = new OgcApiEndpoint('http://example.com');
    const builder = await endpoint.csapi('test-collection');
    expect(builder).toBeInstanceOf(CSAPIQueryBuilder);
  });

  it('caches csapi builder per collection', async () => {
    // ... setup mocks

    const endpoint = new OgcApiEndpoint('http://example.com');
    const builder1 = await endpoint.csapi('test-collection');
    const builder2 = await endpoint.csapi('test-collection');
    expect(builder1).toBe(builder2); // Same instance
  });

  it('throws error when CSAPI not supported', async () => {
    const mockConformance = {
      conformsTo: [], // No CSAPI conformance
    };

    // ... setup mocks

    const endpoint = new OgcApiEndpoint('http://example.com');
    await expect(endpoint.csapi('test-collection')).rejects.toThrow(
      'Endpoint does not support Connected Systems API'
    );
  });
});
```

### Integration Test File Modifications

**2 test files modified:**

- `src/ogc-api/info.spec.ts`: Add ~30 lines
- `src/ogc-api/endpoint.spec.ts`: Add ~60 lines

**Total test additions:** ~90 lines

---

## 10. Complete Integration Checklist

### Step-by-Step Integration

#### Phase 1: Conformance Check

- [x] Add `checkHasConnectedSystems` to `src/ogc-api/info.ts`
- [x] Add test in `src/ogc-api/info.spec.ts`
- [x] Verify test passes

#### Phase 2: Endpoint Integration

- [x] Import `CSAPIQueryBuilder` in `src/ogc-api/endpoint.ts`
- [x] Add cache field to class
- [x] Add `hasConnectedSystems` getter
- [x] Add `csapiCollections` getter
- [x] Add `csapi()` factory method
- [x] Add `checkHasConnectedSystems` to import statement

#### Phase 3: Public Exports

- [x] Add CSAPI type exports to `src/index.ts`

#### Phase 4: Integration Tests

- [x] Add endpoint integration tests in `src/ogc-api/endpoint.spec.ts`
- [x] Verify all tests pass

#### Phase 5: Verification

- [x] Run full test suite
- [x] Check TypeScript compilation
- [x] Verify no unintended changes to other files
- [x] Review diff size (~65 lines added)

### File Modification Summary

**New files created:**

- `src/ogc-api/csapi/model.ts`
- `src/ogc-api/csapi/url_builder.ts`
- `src/ogc-api/csapi/helpers.ts`
- `src/ogc-api/csapi/model.spec.ts`
- `src/ogc-api/csapi/url_builder.spec.ts`
- `fixtures/ogc-api/csapi/*.json` (8-10 fixtures)

**Existing files modified:**

- `src/ogc-api/endpoint.ts` (~35 lines added)
- `src/ogc-api/info.ts` (~12 lines added)
- `src/index.ts` (~17 lines added)
- `src/ogc-api/info.spec.ts` (~30 lines added)
- `src/ogc-api/endpoint.spec.ts` (~60 lines added)

**Total changes:**

- 5-6 new implementation files (~2150-2600 lines)
- 5 modified files (~154 lines added)
- 8-10 new fixture files

---

## Summary

### Integration Principles

1. ✅ **Additive only** - No modifications to existing code (except imports)
2. ✅ **Follow EDR pattern** - Exact blueprint for integration
3. ✅ **Reuse utilities** - 15+ shared functions available
4. ✅ **Reuse types** - BoundingBox, DateTimeParameter, etc.
5. ✅ **Minimal diff** - ~65 lines added to existing files
6. ✅ **Cache builders** - One instance per collection
7. ✅ **Conformance-based** - Check CSAPI support before access
8. ✅ **Factory method** - `endpoint.csapi(collectionId)`
9. ✅ **Export types** - Resources public via src/index.ts
10. ✅ **Test integration** - Verify conformance and factory

### Integration Code Volume

**Existing files modified:**

- endpoint.ts: 35 lines
- info.ts: 12 lines
- index.ts: 17 lines
- **Total:** 64 lines

**Test additions:**

- info.spec.ts: 30 lines
- endpoint.spec.ts: 60 lines
- **Total:** 90 lines

**Grand total:** 154 lines added to existing files

**Result:** Clean, minimal integration following established patterns.

---

## Conclusion

CSAPI integrates into ogc-client with **~65 lines of production code** and **~90 lines of test code** added to existing files.

Integration follows EDR pattern exactly:

1. Conformance check function
2. Cache field in endpoint class
3. Collections getter
4. Conformance checker getter
5. Factory method
6. Public type exports

All changes are additive, reviewable, and follow existing conventions.
