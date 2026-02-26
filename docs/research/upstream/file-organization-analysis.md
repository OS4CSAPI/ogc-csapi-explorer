# File Organization Strategy Analysis

**Purpose:** Document file organization patterns in ogc-client to guide CSAPI implementation structure.

**Context:** CSAPI adds 9 resource types with QueryBuilder, types, helpers, and tests. Need clear organization for maintainability and PR review.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [EDR File Structure](#2-edr-file-structure)
3. [Other API Patterns](#3-other-api-patterns)
4. [Test File Organization](#4-test-file-organization)
5. [Fixture Organization](#5-fixture-organization)
6. [Export Strategy](#6-export-strategy)
7. [File Naming Conventions](#7-file-naming-conventions)
8. [Import Path Patterns](#8-import-path-patterns)
9. [Public vs Internal APIs](#9-public-vs-internal-apis)
10. [CSAPI File Organization Design](#10-csapi-file-organization-design)

---

## 1. Overview

### Project Structure Philosophy

**ogc-client organizes code by API type, not by technical layer:**

```
src/
  shared/          # Cross-API utilities
  wfs/             # WFS implementation
  wms/             # WMS implementation
  wmts/            # WMTS implementation
  tms/             # TMS implementation
  ogc-api/         # OGC API family
    endpoint.ts    # Main OGC API endpoint
    info.ts        # Parsing utilities
    link-utils.ts  # Link traversal
    model.ts       # Common OGC API types
    edr/           # EDR-specific code
  stac/            # STAC implementation
  worker/          # Web worker support
```

**Key principle:** Each API is self-contained in its own directory.

### No Subdirectories Within API Folders

**Observation:** Neither EDR, STAC, nor XML-based APIs use subdirectories.

**EDR structure (flat):**

```
src/ogc-api/edr/
  model.ts
  url_builder.ts
  helpers.ts
  model.spec.ts
  helpers.spec.ts
```

**Not this:**

```
src/ogc-api/edr/
  models/          # ❌ Not used
  builders/        # ❌ Not used
  utils/           # ❌ Not used
```

**Reason:** With only 3-5 implementation files, subdirectories add complexity without benefit.

---

## 2. EDR File Structure

### Complete EDR Implementation

**5 files total (3 implementation + 2 test):**

| File              | Lines | Purpose               |
| ----------------- | ----- | --------------------- |
| `model.ts`        | 126   | Type definitions      |
| `url_builder.ts`  | 380   | EDRQueryBuilder class |
| `helpers.ts`      | 26    | Utility functions     |
| `model.spec.ts`   | 97    | Model tests           |
| `helpers.spec.ts` | 45    | Helper tests          |

**Total:** ~675 lines (including tests)

### File Purposes

#### `model.ts` - Type Definitions

**Contains:**

- Type aliases (`WellKnownTextString`, `bboxWithoutVerticalAxis`)
- Discriminated unions (`ZParameter`)
- Query parameter interfaces (`optionalAreaParams`, etc.)
- Type conversion functions (`zParameterToString`)

**Pattern:**

```typescript
// Simple type alias
export type WellKnownTextString = string;

// Complex parameter interface
export type optionalAreaParams = {
  parameter_name?: string[];
  z?: ZParameter;
  datetime?: DateTimeParameter;
  crs?: string;
  f?: string;
};

// Helper function with type
export function zParameterToString(z: ZParameter): string {
  // ...
}
```

**Rule:** All exports are public.

#### `url_builder.ts` - QueryBuilder Class

**Contains:**

- Single default export class
- All query building methods
- Private cache management
- URL construction logic

**Pattern:**

```typescript
export default class EDRQueryBuilder {
  private collection_: OgcApiCollectionInfo;
  private cache_: Map<string, any>;

  constructor(collection: OgcApiCollectionInfo) {
    this.collection_ = collection;
    this.cache_ = new Map();
  }

  // Public query methods
  async getAreaData(...): Promise<...> { }
  async getPositionData(...): Promise<...> { }

  // Private helpers
  private buildUrl(...): string { }
}
```

**Rule:** One class per file, default export.

#### `helpers.ts` - Utility Functions

**Contains:**

- Pure utility functions
- Type conversion helpers
- Shared logic used by url_builder

**Pattern:**

```typescript
import { DateTimeParameter } from '../../shared/models.js';

export function DateTimeParameterToEDRString(param: DateTimeParameter): string {
  const format = (d: Date) => d.toISOString();

  if (param instanceof Date) {
    return format(param);
  }

  if ('start' in param && 'end' in param) {
    return `${format(param.start)}/${format(param.end)}`;
  }

  // ... more cases
}
```

**Rule:** Named exports, pure functions only.

### Import Pattern in url_builder.ts

**EDR imports from three tiers:**

```typescript
// Tier 1: Shared primitives
import { DateTimeParameter, BoundingBox } from '../../shared/models.js';

// Tier 2: OGC API common
import { OgcApiCollectionInfo } from '../model.js';
import { getLinkUrl } from '../link-utils.js';

// Tier 3: EDR-specific
import {
  optionalAreaParams,
  optionalPositionParams,
  bboxWithVerticalAxis,
  ZParameter,
} from './model.js';
import { DateTimeParameterToEDRString } from './helpers.js';
```

**Pattern:** Relative imports with `.js` extension.

---

## 3. Other API Patterns

### STAC Organization (7 files)

**STAC has similar flat structure:**

```
src/stac/
  endpoint.ts         # Main STAC endpoint class
  endpoint.spec.ts    # Endpoint tests
  info.ts             # Parsing functions
  link-utils.ts       # STAC-specific link utilities
  link-utils.spec.ts  # Link utility tests
  model.ts            # STAC type definitions
  index.ts            # Re-export barrel file
```

**Notable:** STAC has `index.ts` barrel file, EDR does not.

**STAC index.ts:**

```typescript
export { default as StacEndpoint } from './endpoint.js';
export type { GetCollectionItemsOptions } from './endpoint.js';
export type { StacEndpointInfo, StacItemsDocument } from './info.js';
export * from './model.js';
```

### WFS Organization (11 files)

**WFS has more files but still flat:**

```
src/wfs/
  capabilities.ts       # XML parsing
  capabilities.spec.ts
  endpoint.ts           # Main class
  endpoint.spec.ts
  featureprops.ts       # Property utilities
  featureprops.spec.ts
  featuretypeinfo.ts    # Type info parsing
  featuretypeinfo.spec.ts
  model.ts              # Types
  url.ts                # URL utilities
  url.spec.ts
```

**Pattern:** Multiple utility files (capabilities, featureprops, url), all flat.

### WMS Organization (7 files)

**WMS similar to STAC:**

```
src/wms/
  capabilities.ts       # XML parsing
  capabilities.spec.ts
  endpoint.ts           # Main class
  endpoint.spec.ts
  model.ts              # Types
  url.ts                # URL utilities
  url.spec.ts
```

### Common Patterns Across APIs

**All APIs follow these rules:**

1. **Flat structure** - No subdirectories
2. **Colocated tests** - Test files next to implementation
3. **Separate concerns** - Different files for parsing, models, endpoints
4. **Barrel files optional** - Only STAC has index.ts
5. **Default exports for classes** - Named exports for utilities/types

---

## 4. Test File Organization

### Test File Naming

**Pattern:** `{filename}.spec.ts`

**Examples:**

- `model.ts` → `model.spec.ts`
- `url_builder.ts` → (no test file exists for EDR, but would be `url_builder.spec.ts`)
- `helpers.ts` → `helpers.spec.ts`
- `endpoint.ts` → `endpoint.spec.ts`

**Rule:** Tests are colocated with implementation in same directory.

### Test File Structure

**Example from `helpers.spec.ts`:**

```typescript
import { describe, expect, it } from 'vitest';
import { DateTimeParameterToEDRString } from './helpers.js';

describe('DateTimeParameterToEDRString', () => {
  it('formats a single Date', () => {
    const date = new Date('2021-01-01T00:00:00Z');
    expect(DateTimeParameterToEDRString(date)).toBe('2021-01-01T00:00:00.000Z');
  });

  it('formats an interval', () => {
    const interval = {
      start: new Date('2021-01-01T00:00:00Z'),
      end: new Date('2021-12-31T23:59:59Z'),
    };
    expect(DateTimeParameterToEDRString(interval)).toBe(
      '2021-01-01T00:00:00.000Z/2021-12-31T23:59:59.000Z'
    );
  });

  // ... more tests
});
```

**Pattern:**

- Import from relative path (`./helpers.js`)
- One `describe` block per function/class
- Multiple `it` blocks for test cases

### Test Coverage

**EDR test breakdown:**

| File              | Test Lines | Implementation Lines | Ratio |
| ----------------- | ---------- | -------------------- | ----- |
| `model.spec.ts`   | 97         | 126                  | 77%   |
| `helpers.spec.ts` | 45         | 26                   | 173%  |

**Observation:** Tests are substantial but not exhaustive. Model types have basic tests, helpers are well-tested.

---

## 5. Fixture Organization

### Fixture Directory Structure

**Fixtures are organized by API family:**

```
fixtures/
  ogc-api/
    sample-data.json
    sample-data-2.json
    root-path.json
    invalid.json
    edr/
      sample-data-hub.json
    sample-data/         # Collection subdirectory
      collections.json
      conformance.json
      ...
  stac/
    root.json
    conformance.json
    collections.json
    collections/
      collection1.json
      ...
  wfs/
    capabilities-pigma-1-1-0.xml
    getfeature-props-states-2-0-0.json
    ...
```

### EDR Fixture Structure

**EDR has minimal fixtures:**

```
fixtures/ogc-api/edr/
  sample-data-hub.json    # Single EDR collection document
```

**EDR mostly reuses parent fixtures:**

- `fixtures/ogc-api/sample-data.json` - Root document
- `fixtures/ogc-api/sample-data/` - Collection responses

### Fixture Naming Conventions

**Patterns observed:**

1. **Root documents:** `{name}.json` (e.g., `sample-data.json`)
2. **Endpoint-specific:** `{endpoint}-{description}.json` (e.g., `sample-data-hub.json`)
3. **XML fixtures:** `{operation}-{source}-{version}.xml` (e.g., `capabilities-pigma-1-1-0.xml`)
4. **Collections:** Subdirectory named after endpoint (e.g., `sample-data/`)

### Fixture Usage in Tests

**Example from endpoint.spec.ts:**

```typescript
import { readFileSync } from 'fs';
import { describe, expect, it } from 'vitest';

const rootDoc = JSON.parse(
  readFileSync('fixtures/ogc-api/sample-data.json', 'utf-8')
);

describe('OgcApiEndpoint', () => {
  it('parses endpoint info', () => {
    const info = parseEndpointInfo(rootDoc);
    expect(info.title).toBe('Sample Data');
  });
});
```

**Pattern:** Relative path from project root.

---

## 6. Export Strategy

### Public Exports in Main index.ts

**Top-level `src/index.ts` exports:**

```typescript
// OGC API exports
export { default as OgcApiEndpoint } from './ogc-api/endpoint.js';
export * from './ogc-api/model.js';  // All types

// Other APIs
export { default as WfsEndpoint } from './wfs/endpoint.js';
export type { ... } from './wfs/model.js';
export { default as StacEndpoint } from './stac/endpoint.js';
export * from './stac/model.js';
```

**Pattern:**

- Default export for main endpoint class
- Export all types from model.ts
- Named exports for specific types if needed

### EDR NOT Exported from Top Level

**EDR is not in main index.ts:**

```typescript
// ❌ NOT in src/index.ts
export { default as EDRQueryBuilder } from './ogc-api/edr/url_builder.js';
```

**Why?** EDR is accessed through OgcApiEndpoint:

```typescript
const endpoint = new OgcApiEndpoint(url);
const edrBuilder = await endpoint.edr(collectionId); // Returns EDRQueryBuilder
```

**Pattern:** Sub-API classes are accessed via factory methods, not direct exports.

### STAC Index File (Optional)

**STAC has barrel file for convenience:**

```typescript
// src/stac/index.ts
export { default as StacEndpoint } from './endpoint.js';
export type { GetCollectionItemsOptions } from './endpoint.js';
export type { StacEndpointInfo, StacItemsDocument } from './info.js';
export * from './model.js';
```

**Usage:** Main index.ts can import from stac/index.ts:

```typescript
// src/index.ts
export * from './stac/index.js';
```

**But EDR doesn't have this** - likely because it's accessed via factory method.

---

## 7. File Naming Conventions

### Implementation Files

| Pattern           | Example                     | Purpose                |
| ----------------- | --------------------------- | ---------------------- |
| `endpoint.ts`     | All APIs                    | Main endpoint class    |
| `model.ts`        | All APIs                    | Type definitions       |
| `{feature}.ts`    | `capabilities.ts`, `url.ts` | Specific functionality |
| `{class_name}.ts` | `url_builder.ts`            | Single class file      |
| `helpers.ts`      | EDR                         | Utility functions      |
| `info.ts`         | OGC API, STAC               | Parsing functions      |
| `link-utils.ts`   | OGC API, STAC               | Link traversal         |

### Test Files

**Pattern:** Always `{filename}.spec.ts`

**Never:** `test/{filename}.ts` or `__tests__/{filename}.ts`

### Casing Conventions

**Files:**

- **Kebab-case:** `link-utils.ts`, `url_builder.ts` (inconsistent: some use snake_case)
- **Single word lowercase:** `endpoint.ts`, `model.ts`, `helpers.ts`

**Classes:**

- **PascalCase:** `OgcApiEndpoint`, `EDRQueryBuilder`, `WfsEndpoint`

**Functions:**

- **camelCase:** `parseEndpointInfo`, `getLinkUrl`, `fetchDocument`

**Types:**

- **PascalCase:** `OgcApiCollectionInfo`, `DateTimeParameter`
- **camelCase for params:** `optionalAreaParams`, `bboxWithVerticalAxis`

---

## 8. Import Path Patterns

### Relative Imports

**All internal imports use relative paths with `.js` extension:**

```typescript
// From url_builder.ts
import { optionalAreaParams } from './model.js';
import { OgcApiCollectionInfo } from '../model.js';
import { DateTimeParameter } from '../../shared/models.js';
```

**Never:**

```typescript
// ❌ Don't use absolute imports
import { optionalAreaParams } from 'src/ogc-api/edr/model';
```

### Import Tier Pattern

**Code in `src/ogc-api/edr/` imports from three tiers:**

```typescript
// Tier 1: Shared (../../shared/)
import { DateTimeParameter, BoundingBox } from '../../shared/models.js';

// Tier 2: OGC API (../)
import { OgcApiCollectionInfo } from '../model.js';
import { getLinkUrl } from '../link-utils.js';

// Tier 3: EDR (.)
import { optionalAreaParams } from './model.js';
import { DateTimeParameterToEDRString } from './helpers.js';
```

**Rule:** Can import from same level or up, never down.

### External Package Imports

**No path for npm packages:**

```typescript
import { Geometry } from 'geojson';
```

---

## 9. Public vs Internal APIs

### What Gets Exported Publicly

**From main `src/index.ts`:**

✅ **Exported:**

- Endpoint classes (`OgcApiEndpoint`, `WfsEndpoint`, etc.)
- All model types (`export * from './ogc-api/model.js'`)
- Shared types (`BoundingBox`, `DateTimeParameter`, etc.)

❌ **NOT Exported:**

- Utility functions (`parseEndpointInfo`, `getLinkUrl`)
- Internal classes (QueryBuilders accessed via factory)
- Test files
- Helper functions (unless in model.ts)

### Why EDR Types Are Accessible

**Even though EDRQueryBuilder isn't exported, its types are:**

```typescript
// Users can import EDR types
import type { optionalAreaParams, ZParameter } from 'ogc-client';

// Because ogc-api/model.ts doesn't export EDR types
// But users get them through:
const builder: EDRQueryBuilder = await endpoint.edr(collectionId);
```

**Actually, EDR types are NOT in main exports!**

Checking `src/index.ts`:

```typescript
export * from './ogc-api/model.js'; // Only common OGC API types
// EDR types are NOT exported
```

**Implication:** EDR types are internal. Users interact with EDRQueryBuilder methods, don't need to import `optionalAreaParams`.

### Public API Surface

**For CSAPI:**

1. **QueryBuilder accessed via factory:**

   ```typescript
   const csapiBuilder = await endpoint.csapi(collectionId);
   ```

2. **Types may or may not be exported:**

   - If users need to construct query options → export
   - If users just call methods → internal

3. **Resources are likely exported:**
   ```typescript
   export type { System, Deployment, ... } from './ogc-api/csapi/model.js';
   ```

---

## 10. CSAPI File Organization Design

### Recommended File Structure

**CSAPI should follow EDR pattern with flat structure:**

```
src/ogc-api/csapi/
  model.ts              # ~350-400 lines: All types (resources, options, helpers)
  url_builder.ts        # ~700-800 lines: CSAPIQueryBuilder class
  helpers.ts            # ~50-80 lines: Utility functions
  model.spec.ts         # ~200-300 lines: Type/helper tests
  url_builder.spec.ts   # ~800-1000 lines: QueryBuilder tests
  (optional) index.ts   # ~10 lines: Re-export barrel file
```

**Total:** 5-6 files, ~2100-2600 implementation lines + ~1000-1300 test lines

### File Breakdown

#### `model.ts` (~350-400 lines)

**Contents:**

- Resource type enum (`CSAPIResourceTypes`)
- Query options interfaces (`QueryOptions`, `SystemQueryOptions`, etc.)
- Helper types (`TimeInterval`, `ResourceLink`, etc.)
- Resource interfaces (`System`, `Deployment`, etc. × 9)
- Collection generic type (`Collection<T>`)

**Pattern:**

```typescript
// Imports
import { Geometry } from 'geojson';
import { BoundingBox, DateTimeParameter, Contact } from '../../shared/models.js';
import { OgcApiDocumentLink } from '../model.js';

// Enum
export const CSAPIResourceTypes = [...] as const;
export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

// Query options
export interface QueryOptions { ... }
export interface SystemQueryOptions extends QueryOptions { ... }

// Helper types
export interface TimeInterval { ... }

// Resources (9 interfaces)
export interface System { ... }
export interface Deployment { ... }
// ... 7 more

// Collections
export interface Collection<T> { ... }
```

**Rule:** All exports, organized by category with comments.

#### `url_builder.ts` (~700-800 lines)

**Contents:**

- `CSAPIQueryBuilder` class (default export)
- Methods for each resource × query type
- Private URL building helpers
- Cache management

**Estimated methods:**

- Systems: `getSystems()`, `getSystem(id)`
- Deployments: `getDeployments()`, `getDeployment(id)`, `getDeploymentSystems(id)`
- SamplingFeatures: `getSamplingFeatures()`, `getSamplingFeature(id)`
- Procedures: `getProcedures()`, `getProcedure(id)`
- Datastreams: `getDatastreams()`, `getDatastream(id)`, `getDatastreamObservations(id)`
- Observations: `getObservations(datastreamId)`, `getObservation(id)`
- Controls: `getControls()`, `getControl(id)`
- ControlStreams: `getControlStreams()`, `getControlStream(id)`
- Commands: `getCommands(controlStreamId)`, `getCommand(id)`

**Total:** ~18 public methods + 5-10 private helpers

**Pattern:**

```typescript
export default class CSAPIQueryBuilder {
  private collection_: OgcApiCollectionInfo;
  private cache_: Map<string, any>;

  constructor(collection: OgcApiCollectionInfo) {
    this.collection_ = collection;
    this.cache_ = new Map();
  }

  // Public query methods
  async getSystems(options?: SystemQueryOptions): Promise<string> {}
  async getSystem(systemId: string): Promise<string> {}
  async getDeployments(options?: QueryOptions): Promise<string> {}
  // ... 15 more public methods

  // Private helpers
  private buildCollectionUrl(
    resourceType: string,
    options?: QueryOptions
  ): string {}

  private buildItemUrl(resourceType: string, itemId: string): string {}

  private buildSubResourceUrl(
    parentType: string,
    parentId: string,
    childType: string,
    options?: QueryOptions
  ): string {}
}
```

#### `helpers.ts` (~50-80 lines)

**Contents:**

- Parameter formatting functions
- Type conversion utilities
- Shared logic extracted from url_builder

**Possible functions:**

- `formatQueryOptions(options: QueryOptions): URLSearchParams`
- `formatDateTime(datetime: DateTimeParameter): string`
- `formatBBox(bbox: BoundingBox): string`
- `validateResourceId(id: string): void`

**Pattern:**

```typescript
import { DateTimeParameter, BoundingBox } from '../../shared/models.js';

export function formatDateTime(datetime: DateTimeParameter): string {
  if (datetime instanceof Date) {
    return datetime.toISOString();
  }

  const start = datetime.start.toISOString();
  const end = datetime.end ? datetime.end.toISOString() : '..';
  return `${start}/${end}`;
}

export function formatBBox(bbox: BoundingBox): string {
  return bbox.join(',');
}

export function formatQueryOptions(
  options: QueryOptions
): Record<string, string> {
  const params: Record<string, string> = {};

  if (options.limit !== undefined) {
    params.limit = options.limit.toString();
  }

  if (options.bbox !== undefined) {
    params.bbox = formatBBox(options.bbox);
  }

  if (options.datetime !== undefined) {
    params.datetime = formatDateTime(options.datetime);
  }

  // ... more parameters

  return params;
}
```

#### `model.spec.ts` (~200-300 lines)

**Contents:**

- Tests for type conversion functions (if any in model.ts)
- Tests for helper types/enums
- Validation tests

**Pattern:**

```typescript
import { describe, expect, it } from 'vitest';
import { CSAPIResourceTypes, CSAPIResourceType } from './model.js';

describe('CSAPIResourceTypes', () => {
  it('contains all expected resource types', () => {
    expect(CSAPIResourceTypes).toHaveLength(9);
    expect(CSAPIResourceTypes).toContain('System');
    expect(CSAPIResourceTypes).toContain('Deployment');
    // ... more
  });

  it('type union works correctly', () => {
    const type: CSAPIResourceType = 'System';
    expect(CSAPIResourceTypes).toContain(type);
  });
});
```

#### `url_builder.spec.ts` (~800-1000 lines)

**Contents:**

- Tests for all 18 query methods
- Tests for URL construction
- Tests for parameter handling
- Tests for error cases

**Pattern:**

```typescript
import { describe, expect, it, beforeEach } from 'vitest';
import CSAPIQueryBuilder from './url_builder.js';
import type { OgcApiCollectionInfo } from '../model.js';

describe('CSAPIQueryBuilder', () => {
  let builder: CSAPIQueryBuilder;
  let mockCollection: OgcApiCollectionInfo;

  beforeEach(() => {
    mockCollection = {
      id: 'test-collection',
      links: [
        { rel: 'systems', href: 'https://api.example.com/systems' },
        { rel: 'deployments', href: 'https://api.example.com/deployments' },
        // ... more
      ],
      // ... other properties
    };
    builder = new CSAPIQueryBuilder(mockCollection);
  });

  describe('getSystems', () => {
    it('returns collection URL', async () => {
      const url = await builder.getSystems();
      expect(url).toBe('https://api.example.com/systems');
    });

    it('adds query parameters', async () => {
      const url = await builder.getSystems({ limit: 10, type: 'sensor' });
      expect(url).toContain('limit=10');
      expect(url).toContain('type=sensor');
    });

    it('handles bbox parameter', async () => {
      const url = await builder.getSystems({ bbox: [-180, -90, 180, 90] });
      expect(url).toContain('bbox=-180,-90,180,90');
    });
  });

  describe('getSystem', () => {
    it('returns item URL', async () => {
      const url = await builder.getSystem('system-123');
      expect(url).toBe('https://api.example.com/systems/system-123');
    });
  });

  // ... 16 more describe blocks for other methods
});
```

#### `index.ts` (optional, ~10 lines)

**Contents:**

- Barrel file for convenient imports

**Pattern:**

```typescript
export { default as CSAPIQueryBuilder } from './url_builder.js';
export * from './model.js';
export * from './helpers.js';
```

**Usage in parent:**

```typescript
// src/index.ts
export type { System, Deployment, ... } from './ogc-api/csapi/model.js';
// Note: CSAPIQueryBuilder NOT exported (accessed via factory)
```

### Why No Subdirectories?

**Reasons for flat structure:**

1. **EDR precedent** - 5 files, no subdirectories
2. **Easy navigation** - All files visible at once
3. **Simple imports** - No deep paths
4. **PR reviewability** - Clear file list
5. **No artificial boundaries** - Files naturally grouped by API

**When subdirectories make sense:**

- 20+ files (CSAPI has 5-6)
- Multiple distinct concerns (CSAPI is cohesive)
- Separate parsers for formats (CSAPI uses GeoJSON)

### Fixture Organization for CSAPI

**Recommended structure:**

```
fixtures/ogc-api/csapi/
  sample-csapi-endpoint.json     # Root document with CSAPI conformance
  systems.json                   # Systems collection
  system-sensor-123.json         # Single system
  deployments.json               # Deployments collection
  deployment-456.json            # Single deployment
  datastreams.json               # Datastreams collection
  observations.json              # Observations collection
  observation-789.json           # Single observation
```

**Why this structure?**

- Follows EDR pattern (one directory under `fixtures/ogc-api/`)
- Each resource type has collection + item examples
- Root document separate from resources
- Clear naming: `{resource-type}.json` for collections, `{resource-type}-{id}.json` for items

### Integration with endpoint.ts

**CSAPI will need integration in `src/ogc-api/endpoint.ts`:**

**Additions required:**

1. **Import CSAPIQueryBuilder:**

   ```typescript
   import CSAPIQueryBuilder from './csapi/url_builder.js';
   ```

2. **Add cache field:**

   ```typescript
   private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();
   ```

3. **Add conformance check:**

   ```typescript
   get hasConnectedSystems(): Promise<boolean> {
     return this.conformance.then(checkHasConnectedSystems);
   }
   ```

4. **Add collections getter:**

   ```typescript
   get csapiCollections(): Promise<string[]> {
     // Similar to edrCollections
   }
   ```

5. **Add factory method:**
   ```typescript
   public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
     if (!this.hasConnectedSystems) {
       throw new EndpointError('Endpoint does not support CSAPI');
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

**Total addition:** ~30 lines to endpoint.ts

### Integration with info.ts

**CSAPI will need conformance checking in `src/ogc-api/info.ts`:**

**Addition required:**

```typescript
export function checkHasConnectedSystems([conformance]: [
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1 ||
    conformance.indexOf('http://www.opengis.net/spec/ogcapi-cs/1.0/conf/core') >
      -1
  );
}
```

**Total addition:** ~10 lines to info.ts

### Public Exports in src/index.ts

**CSAPI types should be exported:**

```typescript
// src/index.ts additions
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
} from './ogc-api/csapi/model.js';

// Note: CSAPIQueryBuilder NOT exported directly
// Accessed via: endpoint.csapi(collectionId)
```

**Total addition:** ~15 lines to src/index.ts

---

## Summary

### Key File Organization Principles

1. ✅ **Flat structure** - No subdirectories for <10 files
2. ✅ **Colocated tests** - Test files next to implementation
3. ✅ **Separate concerns** - model.ts, url_builder.ts, helpers.ts
4. ✅ **Default export for classes** - Named exports for utilities/types
5. ✅ **Relative imports** - Always use relative paths with `.js`
6. ✅ **Fixtures organized by API** - `fixtures/ogc-api/csapi/`
7. ✅ **Factory method access** - QueryBuilder via endpoint.csapi()
8. ✅ **Export resource types** - Users may need them
9. ✅ **Internal helpers** - Don't export utility functions
10. ✅ **Minimal endpoint integration** - ~40 lines total (endpoint.ts + info.ts)

### CSAPI File Checklist

✅ **Implementation files (5-6):**

- [x] `model.ts` - All types (~350-400 lines)
- [x] `url_builder.ts` - CSAPIQueryBuilder class (~700-800 lines)
- [x] `helpers.ts` - Utility functions (~50-80 lines)
- [x] `model.spec.ts` - Type tests (~200-300 lines)
- [x] `url_builder.spec.ts` - QueryBuilder tests (~800-1000 lines)
- [x] `index.ts` - Optional barrel file (~10 lines)

✅ **Integration files (2):**

- [x] Modify `src/ogc-api/endpoint.ts` (~30 lines added)
- [x] Modify `src/ogc-api/info.ts` (~10 lines added)
- [x] Modify `src/index.ts` (~15 lines added)

✅ **Fixtures (8-10 files):**

- [x] Root document
- [x] Collection responses (9 resource types)
- [x] Item responses (sample items)

**Total new files:** 5-6 implementation + 8-10 fixtures = 13-16 new files
**Total modified files:** 3 (endpoint.ts, info.ts, index.ts)
**Total lines added:** ~2150-2600 implementation + ~1000-1300 tests = ~3150-3900 lines

---

## Conclusion

CSAPI should follow EDR's flat file organization pattern:

**5 core files in `src/ogc-api/csapi/`:**

1. `model.ts` - All types
2. `url_builder.ts` - QueryBuilder class
3. `helpers.ts` - Utilities
4. `model.spec.ts` - Type tests
5. `url_builder.spec.ts` - QueryBuilder tests

**No subdirectories needed** - structure is clear and maintainable.

**Easy PR review** - 5 new files + 3 modified files, organized by concern.

**Follows established patterns** - consistent with EDR, STAC, and other APIs.
