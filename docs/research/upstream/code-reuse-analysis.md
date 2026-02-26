# Code Reuse vs Duplication Strategy

**Purpose:** Define when to reuse upstream utilities vs duplicate code for CSAPI implementation.

**Context:** Governance requires minimal coupling to upstream code. Must balance DRY principle against isolation and maintainability.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [Shared Utilities Inventory](#2-shared-utilities-inventory)
3. [Reuse Patterns in Upstream](#3-reuse-patterns-in-upstream)
4. [Coupling vs Isolation Trade-offs](#4-coupling-vs-isolation-trade-offs)
5. [CSAPI Dependencies](#5-csapi-dependencies)
6. [Duplication Scenarios](#6-duplication-scenarios)
7. [Import Guidelines](#7-import-guidelines)
8. [Complete Dependency Map](#8-complete-dependency-map)

---

## 1. Overview

### The Tension

**DRY Principle (Don't Repeat Yourself):**

- Reuse existing utilities
- Reduce code volume
- Leverage tested code
- Align with upstream patterns

**Isolation Principle:**

- Minimize coupling
- Reduce merge conflict risk
- Make code self-contained
- Ease future maintenance

### Governance Constraints

**From AI_OPERATIONAL_CONSTRAINTS.md:**

- Minimize changes to existing upstream files
- Prefer duplication over refactoring shared code
- Keep CSAPI additions isolated

**From FEATURE_SPEC.md:**

- Non-negotiable: minimal impact on existing code
- Additive-only approach
- Each modification must be justified

### Resolution Strategy

**Balance approach:**

1. **Always reuse:** Stable, well-tested shared utilities (bbox, datetime, errors)
2. **Selective reuse:** OGC API utilities (link-utils, endpoint patterns)
3. **Duplicate when:** CSAPI-specific logic, isolation improves clarity
4. **Never reuse:** Implementation-specific helpers from other APIs

---

## 2. Shared Utilities Inventory

### Available Shared Utilities

**From `src/shared/`:**

| Utility         | Purpose                              | Stability | CSAPI Use                               |
| --------------- | ------------------------------------ | --------- | --------------------------------------- |
| `bbox-utils.ts` | BoundingBox validation               | High      | ✅ Yes - query params                   |
| `cache.ts`      | Response caching                     | High      | ❌ No - endpoint handles                |
| `crs-utils.ts`  | CRS code handling                    | High      | ❌ No - not needed                      |
| `encoding.ts`   | String encoding                      | High      | ❌ No - not needed                      |
| `errors.ts`     | EndpointError, ServiceExceptionError | High      | ✅ Yes - error handling                 |
| `http-utils.ts` | Fetch configuration                  | High      | ❌ No - endpoint handles                |
| `id.ts`         | Unique ID generation                 | High      | ❌ No - not needed                      |
| `mime-type.ts`  | MIME type checking                   | Medium    | ❌ No - format strings only             |
| `models.ts`     | TypeScript types                     | High      | ✅ Yes - BoundingBox, DateTimeParameter |
| `url-utils.ts`  | URL manipulation                     | High      | ✅ Yes - getChildPath                   |
| `xml-utils.ts`  | XML parsing                          | High      | ❌ No - CSAPI is JSON                   |
| `ows.ts`        | OWS XML parsing                      | High      | ❌ No - CSAPI not OWS                   |

**From `src/ogc-api/`:**

| Utility         | Purpose              | Stability | CSAPI Use                     |
| --------------- | -------------------- | --------- | ----------------------------- |
| `link-utils.ts` | Link extraction      | High      | ✅ Yes - resource discovery   |
| `model.ts`      | OGC API types        | High      | ✅ Yes - OgcApiCollectionInfo |
| `info.ts`       | Conformance checking | High      | ✅ Yes - add CSAPI checks     |
| `endpoint.ts`   | Endpoint class       | High      | ✅ Yes - add csapi() method   |

### Reuse Categories

**Category 1: Core Types (Always Reuse)**

```typescript
// From src/shared/models.ts
import {
  BoundingBox,
  DateTimeParameter,
  MimeType,
} from '../../shared/models.js';

// From src/ogc-api/model.ts
import { OgcApiCollectionInfo, OgcApiDocument } from '../model.js';
```

**Usage:** Query option types, collection metadata.

**Rationale:** Standard types, stable, no behavior coupling.

**Category 2: Error Classes (Always Reuse)**

```typescript
// From src/shared/errors.ts
import { EndpointError } from '../../shared/errors.js';
```

**Usage:** Throwing errors for conformance checks, missing resources.

**Rationale:** Consistent error handling, established pattern.

**Category 3: OGC API Utilities (Selective Reuse)**

```typescript
// From src/ogc-api/link-utils.ts
import { getLinkUrl, hasLinks } from '../link-utils.js';

// From src/shared/url-utils.ts
import { getChildPath } from '../../shared/url-utils.js';
```

**Usage:** Link extraction for resource URLs, path building.

**Rationale:** OGC API patterns, tested, saves code.

**Category 4: API-Specific Logic (Never Reuse)**

```typescript
// ❌ Don't import from other APIs
import { ... } from '../edr/url_builder.js';  // NO
import { ... } from '../stac/api.js';          // NO
import { ... } from '../wfs/capabilities.js';  // NO
```

**Rationale:** Creates coupling between APIs, reduces isolation.

---

## 3. Reuse Patterns in Upstream

### EDR Reuse Pattern

**From `src/ogc-api/edr/url_builder.ts`:**

```typescript
// EDR imports
import { CrsCode } from '../../shared/models.js'; // Type only
import { DateTimeParameter } from '../../shared/models.js'; // Type only

// No other imports from shared
// No imports from other OGC APIs
```

**Pattern:** Minimal imports, types only, no utilities.

**EDR implements its own:**

- Query string building
- Parameter validation
- URL construction

### STAC Reuse Pattern

**From `src/ogc-api/stac/api.ts`:**

```typescript
// STAC imports
import { OgcApiCollectionInfo } from '../model.js'; // Core type
import { sharedFetch } from '../../shared/http-utils.js'; // HTTP utility

// Note: STAC is different - it fetches data, not just builds URLs
```

**Pattern:** Uses shared HTTP because STAC fetches and parses responses.

### WFS Reuse Pattern

**From `src/wfs/capabilities.ts`:**

```typescript
// WFS imports
import { Provider, GenericEndpointInfo } from '../shared/models.js'; // Types
import { queryXmlDocument } from '../shared/http-utils.js'; // XML fetch
import { parseCapabilities } from '../shared/ows.js'; // OWS parsing

// WFS is XML-based, uses XML utilities
```

**Pattern:** Heavy reuse of XML/OWS utilities (XML API family).

### Upstream Pattern Summary

**By API family:**

| API  | Import Count | Categories      | Note             |
| ---- | ------------ | --------------- | ---------------- |
| EDR  | 2-3          | Types only      | Minimal coupling |
| STAC | 5-7          | Types + HTTP    | Fetches data     |
| WFS  | 10-15        | Types + XML/OWS | XML family       |
| WMS  | 10-15        | Types + XML/OWS | XML family       |
| WMTS | 10-15        | Types + XML/OWS | XML family       |

**CSAPI pattern:** Follow EDR (JSON API, URL building only).

---

## 4. Coupling vs Isolation Trade-offs

### When to Reuse

**Reuse when:**

1. **Type definitions:**

   ```typescript
   import { BoundingBox } from '../../shared/models.js';
   ```

   **Trade-off:** Zero coupling (types disappear at runtime), full alignment.

2. **Stable, tested utilities:**

   ```typescript
   import { EndpointError } from '../../shared/errors.js';
   ```

   **Trade-off:** Minimal coupling, consistent error handling.

3. **OGC API patterns:**

   ```typescript
   import { getLinkUrl } from '../link-utils.js';
   ```

   **Trade-off:** Slight coupling, but CSAPI is OGC API so alignment is good.

4. **Would require significant code duplication:**

   ```typescript
   import { getChildPath } from '../../shared/url-utils.js';

   // Alternative: Duplicate 10-15 lines
   function getChildPath(url: string, child: string): string {
     const urlObj = new URL(url);
     if (urlObj.pathname.endsWith('/')) {
       urlObj.pathname += child;
     } else {
       urlObj.pathname += `/${child}`;
     }
     return urlObj.toString();
   }
   ```

   **Trade-off:** Import saves ~15 lines, utility is stable.

### When to Duplicate

**Duplicate when:**

1. **CSAPI-specific logic:**

   ```typescript
   // ✅ Duplicate - CSAPI-specific resource discovery
   private extractAvailableResources(): Set<string> {
     const resources = new Set<string>();
     const linkRels = this.collection_.links.map(l => l.rel);

     if (linkRels.includes('systems')) resources.add('systems');
     if (linkRels.includes('datastreams')) resources.add('datastreams');
     // ... CSAPI resource types

     return resources;
   }
   ```

   **Rationale:** Specific to CSAPI, wouldn't be shared anyway.

2. **Simple helpers (< 5 lines):**

   ```typescript
   // ✅ Duplicate - trivial helper
   private formatDateTime(dt: DateTimeParameter): string {
     if (dt instanceof Date) return dt.toISOString();
     if ('start' in dt && 'end' in dt) return `${dt.start.toISOString()}/${dt.end.toISOString()}`;
     if ('start' in dt) return `${dt.start.toISOString()}/..`;
     return `../${dt.end.toISOString()}`;
   }
   ```

   **Rationale:** 5-line function, self-contained, no dependency.

3. **Clarity improvement:**

   ```typescript
   // ✅ Duplicate - clearer when inline
   private buildQueryString(options?: QueryOptions): string {
     if (!options) return '';
     const params = new URLSearchParams();
     if (options.limit !== undefined) {
       params.set('limit', options.limit.toString());
     }
     // ... more params
     return params.toString() ? `?${params.toString()}` : '';
   }
   ```

   **Rationale:** Simple, readable, no need for shared utility.

4. **Isolation from API-specific patterns:**
   ```typescript
   // ✅ Duplicate - don't couple to EDR patterns
   // Even if EDR has similar buildUrl logic, keep separate
   private buildResourceUrl(
     resourceType: string,
     id?: string,
     subPath?: string,
     options?: QueryOptions
   ): string {
     // CSAPI-specific URL building
   }
   ```
   **Rationale:** CSAPI URL patterns differ from EDR, keep independent.

### Acceptable Duplication Threshold

**Guidelines:**

| Code Size   | Action                        | Rationale                       |
| ----------- | ----------------------------- | ------------------------------- |
| 1-5 lines   | Always duplicate              | Trivial, no value in extracting |
| 6-15 lines  | Duplicate if CSAPI-specific   | Isolation > DRY for small code  |
| 16-30 lines | Consider extracting to helper | Balance point                   |
| 31+ lines   | Extract or import             | DRY > isolation for large code  |

**Exception:** If upstream already has utility for 31+ lines, always import.

---

## 5. CSAPI Dependencies

### Required Imports

**Types (zero coupling):**

```typescript
// In src/ogc-api/csapi/url_builder.ts
import type { BoundingBox, DateTimeParameter } from '../../shared/models.js';

import type { OgcApiCollectionInfo, OgcApiDocument } from '../model.js';
```

**Utilities (minimal coupling):**

```typescript
import { EndpointError } from '../../shared/errors.js';
import { getLinkUrl } from '../link-utils.js';
import { getChildPath } from '../../shared/url-utils.js';
```

**Total imports:** ~7-8 lines.

### Query Options Types

**Option 1: Import BoundingBox and DateTimeParameter**

```typescript
import type { BoundingBox, DateTimeParameter } from '../../shared/models.js';

export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox; // [number, number, number, number]
  datetime?: DateTimeParameter; // Date | { start: Date } | ...
  f?: string;
}
```

**Pros:**

- Consistent with upstream types
- Well-documented types
- Zero runtime coupling

**Cons:**

- None (types are free)

**Option 2: Duplicate types**

```typescript
// In url_builder.ts
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: [number, number, number, number];
  datetime?:
    | Date
    | { start: Date }
    | { end: Date }
    | { start: Date; end: Date };
  f?: string;
}
```

**Pros:**

- Self-contained
- No imports

**Cons:**

- Inconsistent with upstream
- Duplicates well-established types
- Loses type documentation

**Recommendation:** Import types (zero coupling, better consistency).

### URL Building

**getLinkUrl usage:**

```typescript
// In url_builder.ts
constructor(private collection_: OgcApiCollectionInfo) {
  // Get base URL for this collection
  const baseUrl = getLinkUrl(
    this.collection_,
    'self',
    this.baseUrl,
    undefined,
    true  // required
  );
  // getLinkUrl throws EndpointError if link not found
}
```

**Alternative: Duplicate link finding:**

```typescript
// ❌ Duplication not justified
private findLink(rel: string): string {
  const link = this.collection_.links.find(l => l.rel === rel);
  if (!link) {
    throw new EndpointError(`Could not find link with type: ${rel}`);
  }
  return link.href;
}
```

**Verdict:** Import getLinkUrl (saves ~20 lines, tested, consistent).

### Path Building

**getChildPath usage:**

```typescript
async getSystem(systemId: string): Promise<string> {
  const systemsUrl = await this.getSystems();
  return getChildPath(systemsUrl, systemId);
}

// Builds: https://api.example.com/systems -> .../systems/system-123
```

**Alternative: Inline path building:**

```typescript
async getSystem(systemId: string): Promise<string> {
  const systemsUrl = await this.getSystems();
  const url = new URL(systemsUrl);
  if (url.pathname.endsWith('/')) {
    url.pathname += systemId;
  } else {
    url.pathname += `/${systemId}`;
  }
  return url.toString();
}
```

**Verdict:** Import getChildPath (saves ~8 lines, handles edge cases).

---

## 6. Duplication Scenarios

### Scenario 1: Query String Building

**Reuse approach:**

```typescript
// Create shared utility in src/ogc-api/query-utils.ts
export function buildOgcApiQueryString(options?: {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  f?: string;
}): string {
  // ... implementation
}

// In url_builder.ts
import { buildOgcApiQueryString } from '../query-utils.js';
```

**Problems:**

1. Creates new shared file (modifies upstream structure)
2. Couples CSAPI to new abstraction
3. No other API needs this (EDR builds inline)

**Duplication approach:**

```typescript
// In url_builder.ts
private buildQueryString(options?: QueryOptions): string {
  if (!options) return '';
  const params = new URLSearchParams();
  if (options.limit !== undefined) {
    params.set('limit', options.limit.toString());
  }
  if (options.offset !== undefined) {
    params.set('offset', options.offset.toString());
  }
  if (options.bbox) {
    params.set('bbox', options.bbox.join(','));
  }
  if (options.datetime) {
    params.set('datetime', this.formatDateTime(options.datetime));
  }
  if (options.f) {
    params.set('f', options.f);
  }
  const query = params.toString();
  return query ? `?${query}` : '';
}
```

**Verdict:** Duplicate (~20 lines, CSAPI-specific, isolated).

### Scenario 2: DateTime Formatting

**Reuse approach:**

```typescript
// Look for existing datetime formatter in shared/
// None exists - would need to create one
```

**Duplication approach:**

```typescript
private formatDateTime(dt: DateTimeParameter): string {
  if (dt instanceof Date) {
    return dt.toISOString();
  }
  if ('start' in dt && 'end' in dt) {
    return `${dt.start.toISOString()}/${dt.end.toISOString()}`;
  }
  if ('start' in dt) {
    return `${dt.start.toISOString()}/..`;
  }
  return `../${dt.end.toISOString()}`;
}
```

**Verdict:** Duplicate (~10 lines, simple logic, no shared utility exists).

### Scenario 3: Resource Discovery

**Reuse approach:**

```typescript
// Extract to shared utility?
// src/ogc-api/resource-utils.ts
export function extractResourceLinks(
  collection: OgcApiCollectionInfo,
  resourceTypes: string[]
): Set<string> {
  // ...
}
```

**Problems:**

1. Only CSAPI needs this
2. Creates coupling to new abstraction
3. Resource types are CSAPI-specific

**Duplication approach:**

```typescript
private extractAvailableResources(): Set<string> {
  const resources = new Set<string>();
  const linkRels = this.collection_.links.map(l => l.rel);

  if (linkRels.includes('systems')) resources.add('systems');
  if (linkRels.includes('deployments')) resources.add('deployments');
  // ... all 9 resources

  return resources;
}
```

**Verdict:** Duplicate (~15 lines, CSAPI-specific, clear).

### Scenario 4: URL Building Helper

**Reuse approach:**

```typescript
// Use getChildPath for single-level
import { getChildPath } from '../../shared/url-utils.js';

async getSystem(systemId: string): Promise<string> {
  const baseUrl = await this.getSystems();
  return getChildPath(baseUrl, systemId);
}
```

**Duplication approach:**

```typescript
async getSystem(systemId: string): Promise<string> {
  const baseUrl = await this.getSystems();
  return `${baseUrl}/${systemId}`;
}
```

**Problems with duplication:**

- Doesn't handle trailing slashes
- Doesn't handle URL encoding
- Missing edge case handling

**Verdict:** Import getChildPath (utility exists, handles edge cases).

---

## 7. Import Guidelines

### Import Checklist

**Before importing, ask:**

1. ✅ **Is it a type?** → Always import (zero coupling)
2. ✅ **Is it stable and well-tested?** → Check test coverage, review history
3. ✅ **Would duplication be significant (>15 lines)?** → Consider importing
4. ✅ **Is it OGC API-specific (not API-family specific)?** → Safe to import
5. ❌ **Is it from another API implementation?** → Never import
6. ❌ **Would it require creating new shared utilities?** → Duplicate instead

### Safe Imports

**Always safe:**

```typescript
// Types
import type { BoundingBox, DateTimeParameter } from '../../shared/models.js';
import type { OgcApiCollectionInfo } from '../model.js';

// Errors
import { EndpointError } from '../../shared/errors.js';

// OGC API utilities
import { getLinkUrl, hasLinks } from '../link-utils.js';
import { getChildPath } from '../../shared/url-utils.js';
```

**Total: ~7 imports.**

### Avoid Imports

**Never import:**

```typescript
// ❌ Other API implementations
import { EDRQueryBuilder } from '../edr/url_builder.js';
import { STACApi } from '../stac/api.js';

// ❌ XML utilities (CSAPI is JSON)
import { queryXmlDocument } from '../../shared/http-utils.js';
import { parseCapabilities } from '../../shared/ows.js';

// ❌ HTTP utilities (endpoint handles fetch)
import { sharedFetch } from '../../shared/http-utils.js';

// ❌ Utilities that don't exist yet
import { buildQueryString } from '../query-utils.js'; // Would need to create
```

### Rationale Summary

| Import Type         | Action       | Reason                     |
| ------------------- | ------------ | -------------------------- |
| Shared types        | ✅ Import    | Zero coupling, consistency |
| Shared errors       | ✅ Import    | Consistent error handling  |
| OGC API utils       | ✅ Import    | CSAPI is OGC API           |
| URL utils           | ✅ Import    | Stable, tested, saves code |
| Query building      | ❌ Duplicate | CSAPI-specific, isolated   |
| DateTime formatting | ❌ Duplicate | Simple, no utility exists  |
| Resource discovery  | ❌ Duplicate | CSAPI-specific             |
| Other APIs          | ❌ Never     | Creates coupling           |
| XML/OWS utils       | ❌ Never     | Wrong API family           |

---

## 8. Complete Dependency Map

### CSAPI File Structure

```
src/ogc-api/csapi/
  url_builder.ts           (CSAPIQueryBuilder class)
  formats.ts               (optional format constants)
  index.ts                 (exports)
```

### Dependency Graph

**url_builder.ts dependencies:**

```typescript
// Types (compile-time only)
import type { BoundingBox, DateTimeParameter } from '../../shared/models.js';

import type { OgcApiCollectionInfo } from '../model.js';

// Runtime utilities
import { EndpointError } from '../../shared/errors.js';
import { getLinkUrl } from '../link-utils.js';
import { getChildPath } from '../../shared/url-utils.js';

// Total: 7 imports
// Lines: ~7 lines
```

**endpoint.ts additions:**

```typescript
// Add to existing imports
import CSAPIQueryBuilder from './csapi/url_builder.js';

// Add to class
private collection_id_to_csapi_builder_ = new Map<string, CSAPIQueryBuilder>();

get hasConnectedSystems(): Promise<boolean> {
  return this.featureCheckFactory_(checkHasConnectedSystems);
}

async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  // ... factory method
}

// Total: ~30 lines added
```

**info.ts additions:**

```typescript
// Add conformance checker
export function checkHasConnectedSystems([conformance]: [
  OgcApiConformance
]): boolean {
  return conformance.conformsTo.includes(
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
  );
}

// Total: ~15 lines added
```

**index.ts additions:**

```typescript
// Add CSAPI exports
export { default as CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';
export type {
  QueryOptions,
  HistoryOptions,
} from './ogc-api/csapi/url_builder.js';

// Total: ~3 lines added
```

### Code Volume Breakdown

**New files:**

- url_builder.ts: ~500-700 lines (implementation)
- formats.ts: ~10 lines (optional)
- index.ts: ~3 lines (exports)

**Modified files:**

- endpoint.ts: +30 lines
- info.ts: +15 lines
- index.ts: +3 lines

**Total new code:** ~560-760 lines
**Total modified code:** ~48 lines
**Import lines:** ~7 lines

**Dependency ratio:** ~1% imports, ~99% implementation.

### Upstream Impact

**Files modified:**

- `src/ogc-api/endpoint.ts` - Add csapi() method
- `src/ogc-api/info.ts` - Add conformance check
- `src/index.ts` - Add exports

**Files created:**

- `src/ogc-api/csapi/url_builder.ts`
- `src/ogc-api/csapi/formats.ts`
- `src/ogc-api/csapi/index.ts`

**Files NOT modified:**

- `src/shared/*` - No changes to shared utilities
- `src/ogc-api/edr/*` - No changes to EDR
- `src/ogc-api/stac/*` - No changes to STAC
- `src/ogc-api/link-utils.ts` - No changes to link utils

**Impact:** ~1-2% of ogc-client core code, additive only.

---

## Summary

### Code Reuse Strategy

**Import these (justified):**

1. ✅ Types: BoundingBox, DateTimeParameter, OgcApiCollectionInfo
2. ✅ Errors: EndpointError
3. ✅ OGC API: getLinkUrl, hasLinks
4. ✅ URL utils: getChildPath

**Duplicate these (isolated):**

1. ✅ Query string building (~20 lines)
2. ✅ DateTime formatting (~10 lines)
3. ✅ Resource discovery (~15 lines)
4. ✅ URL construction helpers (~30 lines)

### Guidelines

**Reuse when:**

- Type definitions (zero coupling)
- Stable shared utilities (>15 lines)
- OGC API patterns (CSAPI is OGC API)

**Duplicate when:**

- Simple helpers (<15 lines)
- CSAPI-specific logic
- Isolation improves clarity
- No shared utility exists

### Final Dependency Count

**Total imports:** ~7 lines
**Total dependencies:** 4 utilities + 3 types
**Code volume:** ~560-760 lines implementation
**Modified upstream:** ~48 lines (3 files)

**Verdict:** Minimal, justified coupling with strong isolation.
