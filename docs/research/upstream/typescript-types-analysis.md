# TypeScript Type System Design Analysis

**Purpose:** Document the TypeScript type organization and design patterns used in ogc-client.

**Context:** CSAPI needs comprehensive type definitions for 9 resource types with shared and resource-specific parameters. Understanding upstream patterns ensures type safety and maintainability.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [Type Hierarchy](#2-type-hierarchy)
3. [Query Parameter Type Patterns](#3-query-parameter-type-patterns)
4. [Resource Type Modeling](#4-resource-type-modeling)
5. [Shared vs Specific Parameters](#5-shared-vs-specific-parameters)
6. [Type Safety Strategies](#6-type-safety-strategies)
7. [Type Granularity](#7-type-granularity)
8. [Type Definition Location](#8-type-definition-location)
9. [Format-Specific Types](#9-format-specific-types)
10. [Optional Properties](#10-optional-properties)
11. [CSAPI Type System Design](#11-csapi-type-system-design)

---

## 1. Overview

### Type Organization Philosophy

**ogc-client uses a three-tier type hierarchy:**

```
src/shared/models.ts          # Cross-API primitives
    ↓
src/ogc-api/model.ts          # OGC API family types
    ↓
src/ogc-api/{api}/model.ts    # API-specific types
```

**Key principles:**

1. **Reuse shared primitives** (BoundingBox, CrsCode, etc.)
2. **Define API-agnostic OGC types** at ogc-api level
3. **Keep API-specific types isolated** in subfolders
4. **Use TypeScript features** (union types, const assertions, mapped types)
5. **Export everything** that users might need

### TypeScript Features Used

**Observed patterns:**

- Union types for variants (`DateTimeParameter = Date | { start: Date, end?: Date }`)
- Const assertions for enums (`as const` arrays)
- Mapped types for optional fields (`Partial<T>`)
- Type aliases for clarity (`type CrsCode = string`)
- Interfaces for objects
- Discriminated unions for complex variants (EDR ZParameter)
- Optional properties (`property?: type`)
- Generic types (`Promise<T>`, `Record<K, V>`)

---

## 2. Type Hierarchy

### Tier 1: Shared Primitives (`src/shared/models.ts`)

**Cross-API types used by all implementations:**

```typescript
// Spatial
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;

// Temporal
export type DateTimeParameter = Date | { start: Date; end?: Date };

// Format
export type MimeType = string;

// Metadata
export interface Address {
  deliveryPoint?: string;
  city?: string;
  administrativeArea?: string;
  postalCode?: string;
  country?: string;
}

export interface Contact {
  name?: string;
  organization?: string;
  position?: string;
  phone?: string;
  email?: string;
  address?: Address;
}

export interface Provider {
  name?: string;
  site?: string;
  contact?: Contact;
}

export type GenericEndpointInfo = {
  name: string;
  title: string;
  abstract: string;
  fees: string;
  constraints: string;
  keywords: string[];
  provider?: Provider;
  outputFormats?: MimeType[];
  infoFormats?: MimeType[];
};
```

**Characteristics:**

- Simple types and interfaces
- No OGC API-specific logic
- Used by WFS, WMS, WMTS, OGC API, etc.
- Stable - rarely changes

### Tier 2: OGC API Family (`src/ogc-api/model.ts`)

**Types shared across all OGC API implementations (Features, Records, Tiles, EDR, CSAPI):**

```typescript
// Conformance
export type ConformanceClass = string;

// Endpoint
export interface OgcApiEndpointInfo {
  title: string;
  description?: string;
  attribution?: string;
}

// Collections
export interface OgcApiCollectionInfo {
  links: any;
  title: string;
  description: string;
  id: string;
  itemType?: 'feature' | 'record';
  itemFormats: MimeType[];
  bulkDownloadLinks: Record<string, MimeType>;
  jsonDownloadLink: string;
  crs: CrsCode[];
  storageCrs?: CrsCode;
  itemCount: number;
  keywords?: string[];
  language?: string;
  updated?: Date;
  extent?: BoundingBox;
  publisher?: {...};
  license?: string;
  queryables: CollectionParameter[];
  sortables: CollectionParameter[];
  mapTileFormats: MimeType[];
  vectorTileFormats: MimeType[];
  supportedTileMatrixSets: string[];

  // API-specific extensions
  data_queries?: {...};  // EDR
  parameter_names?: Record<string, EdrParameterInfo>;  // EDR
  // CSAPI would add its fields here
}

// Links
export interface OgcApiDocumentLink {
  rel: string;
  type: string;
  title: string;
  href: string;
}

// Documents
export type OgcApiDocument = {
  links: OgcApiDocumentLink[];
  // ... other properties
};

// Parameters
export const CollectionParameterTypes = [
  'string', 'number', 'integer', 'date',
  'point', 'linestring', 'polygon', 'geometry',
] as const;

export type CollectionParameterType = (typeof CollectionParameterTypes)[number];

export interface CollectionParameter {
  name: string;
  title?: string;
  type: CollectionParameterType;
}
```

**Characteristics:**

- OGC API standard types
- Shared by EDR, Features, Records, Tiles, CSAPI
- Can be extended per-API (see `OgcApiCollectionInfo`)
- Moderately stable

### Tier 3: API-Specific (`src/ogc-api/edr/model.ts`)

**Types unique to EDR:**

```typescript
// Special string types
export type WellKnownTextString = string;

// Geometric types
export type bboxWithoutVerticalAxis = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
};

export type bboxWithVerticalAxis = bboxWithoutVerticalAxis & {
  minZ: number;
  maxZ: number;
};

// Complex discriminated union
export type ZParameter =
  | { type: 'single'; level: number }
  | { type: 'interval'; minLevel: number; maxLevel: number }
  | { type: 'list'; levels: number[] }
  | { type: 'repeating'; repeat: number; minLevel: number; step: number };

// Helper functions for complex types
export function zParameterToString(z: ZParameter): string {
  switch (z.type) {
    case 'single':
      return `${z.level}`;
    case 'interval':
      return `${z.minLevel}/${z.maxLevel}`;
    case 'list':
      return z.levels.join(',');
    case 'repeating':
      return `R${z.repeat}/${z.minLevel}/${z.step}`;
  }
}

// Query parameter interfaces
export type optionalAreaParams = {
  parameter_name?: string[];
  z?: ZParameter;
  datetime?: DateTimeParameter;
  crs?: string;
  f?: string;
};

export type optionalPositionParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: ZParameter;
  crs?: string;
  f?: string;
};

// ... one for each query type
```

**Characteristics:**

- Highly specific to EDR
- Not used by other APIs
- Can change without affecting other code
- Most detailed/granular

### Dependency Flow

```
EDR QueryBuilder
    ↓ imports
src/ogc-api/edr/model.ts (optionalAreaParams, ZParameter, etc.)
    ↓ imports
src/ogc-api/model.ts (OgcApiCollectionInfo, CollectionParameter, etc.)
    ↓ imports
src/shared/models.ts (BoundingBox, CrsCode, DateTimeParameter, etc.)
```

**Rule:** Lower tiers can import from higher tiers, never the reverse.

---

## 3. Query Parameter Type Patterns

### Pattern 1: Optional Parameters Interface

**EDR uses this pattern extensively:**

```typescript
export type optionalPositionParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: ZParameter;
  crs?: string;
  f?: string;
};
```

**Usage:**

```typescript
buildPositionDownloadUrl(
  coords: { lon: number; lat: number },
  optional_params: optionalPositionParams = {}
): string
```

**Benefits:**

- Type-safe optional parameters
- IDE autocomplete
- Clear documentation of what's optional
- Default empty object works with undefined checks

### Pattern 2: Inline Options Type

**Used in endpoint.ts:**

```typescript
getCollectionItemsUrl(
  collectionId: string,
  options: {
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

**Benefits:**

- All parameters in one place
- No need for separate type definition
- Good for one-off methods

**Drawbacks:**

- Not reusable
- Verbose if same options used multiple times

### Pattern 3: Shared Options Type

**Better for CSAPI with 9 resources:**

```typescript
// Define once
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
}

// Use everywhere
async getSystems(options?: QueryOptions): Promise<System[]>
async getDeployments(options?: QueryOptions): Promise<Deployment[]>
async getObservations(datastreamId: string, options?: QueryOptions): Promise<Observation[]>
```

**Benefits:**

- DRY - defined once
- Consistent across all resources
- Easy to extend (add one property, all methods get it)

### Pattern 4: Extended Options

**For resource-specific parameters:**

```typescript
// Base options
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
}

// Extended for specific resource
export interface SystemQueryOptions extends QueryOptions {
  type?: 'sensor' | 'platform' | 'actuator';
  status?: 'active' | 'inactive';
}

// Usage
async getSystems(options?: SystemQueryOptions): Promise<System[]>
```

---

## 4. Resource Type Modeling

### Pattern: Interface for Resource Shape

**Define structure of each resource:**

```typescript
// System resource
export interface System {
  id: string;
  type: 'System';
  properties: {
    name: string;
    description?: string;
    keywords?: string[];
    identifier?: string;
    contacts?: Contact[];
    documentation?: DocumentLink[];
    history?: HistoryEvent[];
  };
  geometry?: Geometry; // From @types/geojson
  links: OgcApiDocumentLink[];
}

// Deployment resource
export interface Deployment {
  id: string;
  type: 'Deployment';
  properties: {
    name: string;
    description?: string;
    platform?: string | Link;
    systems?: Array<string | Link>;
    validTime?: TimeInterval;
  };
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
}
```

### GeoJSON Alignment

**CSAPI resources follow GeoJSON structure:**

```typescript
// GeoJSON-like structure
interface CSAPIResource {
  id: string; // Required
  type: string; // Resource type name
  properties: {
    // Resource-specific properties
    name: string;
    description?: string;
    // ... more
  };
  geometry?: Geometry; // Optional spatial data
  links: OgcApiDocumentLink[]; // HATEOAS links
}
```

**Import GeoJSON types:**

```typescript
import { Geometry, Point, Polygon } from 'geojson';

export interface System {
  // ...
  geometry?: Geometry | Point | Polygon;
}
```

**Why?** CSAPI resources can have spatial extent.

### Collections vs Items

**Collection response:**

```typescript
export interface SystemCollection {
  type: 'FeatureCollection';
  features: System[];
  links: OgcApiDocumentLink[];
  numberMatched?: number;
  numberReturned: number;
  timeStamp: string;
}
```

**Or simpler:**

```typescript
export interface ResourceCollection<T> {
  items: T[];
  links: OgcApiDocumentLink[];
  numberMatched?: number;
  numberReturned: number;
}
```

---

## 5. Shared vs Specific Parameters

### Shared Parameters (from `shared/models.ts`)

**Already defined and ready to use:**

```typescript
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;
export type MimeType = string;
export type DateTimeParameter = Date | { start: Date; end?: Date };
```

**Don't redefine these in CSAPI types.**

### OGC API Standard Parameters

**Common across all OGC APIs:**

- `limit` - Max number of results
- `offset` - Pagination offset
- `bbox` - Bounding box filter
- `datetime` - Temporal filter
- `properties` - Property selection
- `sortby` - Sort order
- `f` - Format (mime type)

**Pattern: Define once as shared options**

```typescript
export interface OgcApiQueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  properties?: string[];
  sortby?: string[];
  f?: MimeType;
}
```

### CSAPI-Specific Parameters

**Parameters unique to CSAPI:**

```typescript
// Filtering by system type
export interface SystemQueryOptions extends OgcApiQueryOptions {
  type?: 'sensor' | 'platform' | 'actuator';
}

// Filtering observations by phenomenon
export interface ObservationQueryOptions extends OgcApiQueryOptions {
  observedProperty?: string[];
}

// Filtering procedures
export interface ProcedureQueryOptions extends OgcApiQueryOptions {
  procedureType?: string;
}
```

**Only define when needed** - most resources just use base options.

---

## 6. Type Safety Strategies

### Strategy 1: Discriminated Unions

**EDR's ZParameter is excellent example:**

```typescript
export type ZParameter =
  | { type: 'single'; level: number }
  | { type: 'interval'; minLevel: number; maxLevel: number }
  | { type: 'list'; levels: number[] }
  | { type: 'repeating'; repeat: number; minLevel: number; step: number };

// TypeScript can narrow type based on discriminant
function handleZ(z: ZParameter) {
  switch (z.type) {
    case 'single':
      // TypeScript knows z.level exists here
      return z.level;
    case 'interval':
      // TypeScript knows z.minLevel and z.maxLevel exist here
      return `${z.minLevel}/${z.maxLevel}`;
    // ...
  }
}
```

**Use for:** Complex parameters with multiple valid structures.

### Strategy 2: Const Assertions for Enums

**Creates union type from array:**

```typescript
export const CollectionParameterTypes = [
  'string',
  'number',
  'integer',
  'date',
  'point',
  'linestring',
  'polygon',
  'geometry',
] as const;

// Creates: 'string' | 'number' | 'integer' | ...
export type CollectionParameterType = (typeof CollectionParameterTypes)[number];
```

**Benefits:**

- Single source of truth
- Can iterate array at runtime
- Type safety at compile time

**CSAPI example:**

```typescript
export const CSAPIResourceTypes = [
  'System',
  'Deployment',
  'SamplingFeature',
  'Procedure',
  'Datastream',
  'Observation',
  'Control',
  'ControlStream',
  'Command',
] as const;

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];
```

### Strategy 3: Strict Null Checks

**All ogc-client types assume `strictNullChecks: true`:**

```typescript
// Optional properties use ? or undefined
export interface System {
  id: string; // Required - never undefined
  name?: string; // Optional - string | undefined
  description?: string; // Optional - string | undefined
}

// vs nullable (less common)
export interface System {
  id: string;
  name: string | null; // Can be null
}
```

**Rule:** Use `?` for optional, not `| undefined | null`.

### Strategy 4: Generic Types

**For reusable collection types:**

```typescript
export interface Collection<T> {
  items: T[];
  links: OgcApiDocumentLink[];
  numberMatched?: number;
  numberReturned: number;
  timeStamp: string;
}

// Usage
type SystemCollection = Collection<System>;
type DeploymentCollection = Collection<Deployment>;
```

### Strategy 5: Type Guards

**For runtime type checking:**

```typescript
export function isSystem(obj: any): obj is System {
  return obj && typeof obj === 'object' && obj.type === 'System';
}

export function isDeployment(obj: any): obj is Deployment {
  return obj && typeof obj === 'object' && obj.type === 'Deployment';
}

// Usage
const resource: System | Deployment = await fetch(...);
if (isSystem(resource)) {
  // TypeScript knows resource is System here
  console.log(resource.properties.name);
}
```

---

## 7. Type Granularity

### Granularity Levels Observed

**Level 1: Coarse** (primitive type aliases)

```typescript
export type CrsCode = string;
export type MimeType = string;
```

**Level 2: Medium** (simple interfaces)

```typescript
export interface Contact {
  name?: string;
  email?: string;
  phone?: string;
}
```

**Level 3: Fine** (detailed interfaces)

```typescript
export interface OgcApiCollectionInfo {
  // 20+ properties with specific types
  links: any;
  title: string;
  description: string;
  id: string;
  itemType?: 'feature' | 'record';
  // ... many more
}
```

**Level 4: Very Fine** (discriminated unions)

```typescript
export type ZParameter =
  | { type: 'single'; level: number }
  | { type: 'interval'; minLevel: number; maxLevel: number }
  | { type: 'list'; levels: number[] }
  | { type: 'repeating'; repeat: number; minLevel: number; step: number };
```

### When to Use Each Level

**Coarse:**

- When type is fundamentally a primitive
- When validation happens at runtime
- When structure is too variable to type precisely

**Medium:**

- Standard data structures (contacts, addresses, metadata)
- Simple resource representations
- When users need to construct objects

**Fine:**

- Core domain objects (collections, endpoints, resources)
- When many optional properties exist
- When documentation value is high

**Very Fine:**

- Complex parameters with multiple valid forms
- When compile-time validation prevents errors
- When discriminant enables type narrowing

### CSAPI Granularity Strategy

**Use fine granularity for:**

- System, Deployment, SamplingFeature, Procedure (core resources)
- Datastream, Observation (frequently used)
- Collection metadata

**Use medium granularity for:**

- ControlStream, Control, Command (less common)
- Nested objects (contacts, links, etc.)

**Use coarse granularity for:**

- String identifiers
- Format types
- Timestamps (use Date or string)

---

## 8. Type Definition Location

### Location Rules

**Rule 1: Shared primitives → `src/shared/models.ts`**

```typescript
// These go in shared/models.ts
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;
export type DateTimeParameter = Date | { start: Date; end?: Date };
```

**Rule 2: OGC API common → `src/ogc-api/model.ts`**

```typescript
// These go in ogc-api/model.ts
export type ConformanceClass = string;
export interface OgcApiCollectionInfo { ... }
export interface OgcApiDocumentLink { ... }
```

**Rule 3: CSAPI-specific → `src/ogc-api/csapi/model.ts`**

```typescript
// These go in ogc-api/csapi/model.ts
export interface System { ... }
export interface Deployment { ... }
export interface QueryOptions { ... }
```

### What Goes Where?

| Type                         | Location           | Reason                       |
| ---------------------------- | ------------------ | ---------------------------- |
| `System`, `Deployment`, etc. | `csapi/model.ts`   | CSAPI resources              |
| `QueryOptions`               | `csapi/model.ts`   | CSAPI query parameters       |
| `CSAPIResourceType`          | `csapi/model.ts`   | CSAPI enum                   |
| `TimeInterval` (if new)      | `csapi/model.ts`   | CSAPI-specific temporal type |
| `BoundingBox`                | `shared/models.ts` | Already exists, reuse        |
| `DateTimeParameter`          | `shared/models.ts` | Already exists, reuse        |
| `OgcApiDocumentLink`         | `ogc-api/model.ts` | Already exists, reuse        |
| `Geometry`                   | `@types/geojson`   | External package             |

### File Organization

**Single model.ts file for CSAPI:**

```typescript
// src/ogc-api/csapi/model.ts

// Imports
import { Geometry } from 'geojson';
import { BoundingBox, DateTimeParameter, Contact } from '../../shared/models.js';
import { OgcApiDocumentLink } from '../model.js';

// Resource type enum
export const CSAPIResourceTypes = [...] as const;
export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

// Query options
export interface QueryOptions { ... }
export interface SystemQueryOptions extends QueryOptions { ... }

// Resource types (one per resource)
export interface System { ... }
export interface Deployment { ... }
export interface SamplingFeature { ... }
export interface Procedure { ... }
export interface Datastream { ... }
export interface Observation { ... }
export interface Control { ... }
export interface ControlStream { ... }
export interface Command { ... }

// Collection types
export interface Collection<T> { ... }

// Helper types
export interface TimeInterval { ... }
export interface Link { ... }
```

**Estimated size:** ~300-400 lines

---

## 9. Format-Specific Types

### Challenge: Multiple Representations

CSAPI resources can be returned in different formats:

- GeoJSON / JSON-FG
- SensorML (XML)
- JSON-LD

**Question:** Do we need separate types per format?

### EDR Approach: Format-Agnostic

**EDR doesn't define format-specific types:**

```typescript
// No separate GeoJSON vs CoverageJSON types
async getPosition(...): Promise<EdrData>  // Generic
```

**Why?**

- Formats have different structures
- TypeScript types for XML are impractical
- Response parsing is format-dependent anyway
- Users specify format, know what they'll get

### Recommended CSAPI Approach

**Define types for primary format only (GeoJSON/JSON-FG):**

```typescript
// GeoJSON representation
export interface System {
  id: string;
  type: 'System';
  properties: { ... };
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
}

// SensorML representation - NOT TYPED
// Users requesting f=application/xml get `any` or `unknown`
```

**For XML/SensorML:**

```typescript
async getSystem(
  systemId: string,
  format?: 'geojson' | 'sensorml'
): Promise<System | unknown> {
  if (format === 'sensorml') {
    // Return unknown or string (XML)
    return await fetchXml(...);
  }
  return await fetchJson<System>(...);
}
```

**Or simpler:**

```typescript
// Only type JSON format
async getSystem(systemId: string): Promise<System>

// Users wanting SensorML can:
const url = builder.getSystemUrl(systemId);
const response = await fetch(url, { headers: { Accept: 'application/xml' } });
const xml = await response.text();
```

**Conclusion:** Type the JSON/GeoJSON format, leave others as `string` or `unknown`.

---

## 10. Optional Properties

### Pattern: Use `?` for Optional

**All optional properties use `?` operator:**

```typescript
export interface System {
  id: string; // Required
  type: 'System'; // Required
  properties: {
    name: string; // Required
    description?: string; // Optional - property may not exist
    keywords?: string[]; // Optional
    contacts?: Contact[]; // Optional
  };
  geometry?: Geometry; // Optional
  links: OgcApiDocumentLink[]; // Required (but array can be empty)
}
```

**Not this:**

```typescript
// ❌ Don't do this
export interface System {
  id: string;
  description: string | undefined; // Use ? instead
  contacts: Contact[] | null; // Use ? instead
}
```

### When Properties Are Required

**Based on CSAPI spec:**

- `id` - Always required (unique identifier)
- `type` - Always required (resource type discriminant)
- `links` - Always required (HATEOAS)
- `properties.name` - Usually required (human-readable name)

**Everything else is optional** unless spec says otherwise.

### Arrays and Optional

**Empty array vs undefined:**

```typescript
// If contacts can be empty array or missing:
contacts?: Contact[];  // undefined | Contact[]

// Usage
if (system.contacts?.length > 0) {
  // Has contacts
}

// NOT this:
contacts: Contact[];  // Never undefined, but can be []
```

**Rule:** Use `?` if property might not exist at all.

### Nested Optional

**Deep optional properties:**

```typescript
export interface System {
  properties: {
    validTime?: {
      start: Date;
      end?: Date;
    };
  };
}

// Access safely
const startTime = system.properties.validTime?.start;
const endTime = system.properties.validTime?.end;
```

---

## 11. CSAPI Type System Design

### Complete Type System

```typescript
// File: src/ogc-api/csapi/model.ts

import { Geometry, Point } from 'geojson';
import {
  BoundingBox,
  DateTimeParameter,
  Contact,
} from '../../shared/models.js';
import { OgcApiDocumentLink } from '../model.js';

//═══════════════════════════════════════════════════════════
// Resource Type Enum
//═══════════════════════════════════════════════════════════

export const CSAPIResourceTypes = [
  'System',
  'Deployment',
  'SamplingFeature',
  'Procedure',
  'Datastream',
  'Observation',
  'Control',
  'ControlStream',
  'Command',
] as const;

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

//═══════════════════════════════════════════════════════════
// Query Options
//═══════════════════════════════════════════════════════════

/**
 * Standard OGC API query parameters supported by CSAPI
 */
export interface QueryOptions {
  /** Maximum number of items to return */
  limit?: number;

  /** Starting index for pagination */
  offset?: number;

  /** Bounding box filter [minX, minY, maxX, maxY] */
  bbox?: BoundingBox;

  /** Temporal filter */
  datetime?: DateTimeParameter;

  /** Property selection (return only specified properties) */
  properties?: string[];

  /** Sort order (e.g., ['name', '-updated']) */
  sortby?: string[];
}

/**
 * Extended options for system queries
 */
export interface SystemQueryOptions extends QueryOptions {
  /** Filter by system type */
  type?: 'sensor' | 'platform' | 'actuator';
}

/**
 * Extended options for observation queries
 */
export interface ObservationQueryOptions extends QueryOptions {
  /** Filter by observed property */
  observedProperty?: string[];
}

//═══════════════════════════════════════════════════════════
// Helper Types
//═══════════════════════════════════════════════════════════

/**
 * Time interval with optional start/end
 */
export interface TimeInterval {
  start?: Date;
  end?: Date;
}

/**
 * Link to related resource (can be inline or reference)
 */
export type ResourceLink = string | { href: string; title?: string };

/**
 * History event
 */
export interface HistoryEvent {
  time: Date;
  description: string;
}

/**
 * Characteristic (name-value pair with unit)
 */
export interface Characteristic {
  name: string;
  description?: string;
  value: number | string | boolean;
  unit?: string;
}

//═══════════════════════════════════════════════════════════
// Resource Types
//═══════════════════════════════════════════════════════════

/**
 * System resource - represents a sensor, platform, or actuator
 */
export interface System {
  id: string;
  type: 'System';
  properties: {
    name: string;
    description?: string;
    systemType?: 'sensor' | 'platform' | 'actuator';
    featureOfInterest?: ResourceLink;
    keywords?: string[];
    identifier?: string;
    contacts?: Contact[];
    documentation?: OgcApiDocumentLink[];
    history?: HistoryEvent[];
    characteristics?: Characteristic[];
    capabilities?: Characteristic[];
    validTime?: TimeInterval;
  };
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
}

/**
 * Deployment resource - represents deployment of a system
 */
export interface Deployment {
  id: string;
  type: 'Deployment';
  properties: {
    name: string;
    description?: string;
    platform?: ResourceLink;
    deployedSystems?: ResourceLink[];
    validTime?: TimeInterval;
  };
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
}

/**
 * Sampling Feature resource - represents location where observations are made
 */
export interface SamplingFeature {
  id: string;
  type: 'SamplingFeature';
  properties: {
    name: string;
    description?: string;
    featureType?: string;
    sampledFeature?: ResourceLink;
  };
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
}

/**
 * Procedure resource - describes how observations are made
 */
export interface Procedure {
  id: string;
  type: 'Procedure';
  properties: {
    name: string;
    description?: string;
    procedureType?: string;
    implementation?: string;
  };
  links: OgcApiDocumentLink[];
}

/**
 * Datastream resource - series of observations from a system
 */
export interface Datastream {
  id: string;
  type: 'Datastream';
  properties: {
    name: string;
    description?: string;
    observedProperty: ResourceLink;
    observationType?: string;
    procedure?: ResourceLink;
    unitOfMeasurement?: {
      name: string;
      symbol: string;
      definition: string;
    };
    phenomenonTime?: TimeInterval;
    resultTime?: TimeInterval;
  };
  links: OgcApiDocumentLink[];
}

/**
 * Observation resource - single measurement or observation
 */
export interface Observation {
  id: string;
  type: 'Observation';
  properties: {
    phenomenonTime: Date | TimeInterval;
    resultTime?: Date;
    result: number | string | boolean | object;
    resultQuality?: string[];
    validTime?: TimeInterval;
    parameters?: Record<string, any>;
  };
  geometry?: Point;
  links: OgcApiDocumentLink[];
}

/**
 * Control resource - controllable aspect of a system
 */
export interface Control {
  id: string;
  type: 'Control';
  properties: {
    name: string;
    description?: string;
    controlType?: string;
  };
  links: OgcApiDocumentLink[];
}

/**
 * Control Stream resource - series of commands to a control
 */
export interface ControlStream {
  id: string;
  type: 'ControlStream';
  properties: {
    name: string;
    description?: string;
    control: ResourceLink;
  };
  links: OgcApiDocumentLink[];
}

/**
 * Command resource - single command to a control
 */
export interface Command {
  id: string;
  type: 'Command';
  properties: {
    executionTime: Date;
    parameters?: Record<string, any>;
    result?: string;
  };
  links: OgcApiDocumentLink[];
}

//═══════════════════════════════════════════════════════════
// Collection Types
//═══════════════════════════════════════════════════════════

/**
 * Generic collection response
 */
export interface Collection<T> {
  type: 'FeatureCollection';
  features: T[];
  links: OgcApiDocumentLink[];
  numberMatched?: number;
  numberReturned: number;
  timeStamp: string;
}

// Convenience type aliases
export type SystemCollection = Collection<System>;
export type DeploymentCollection = Collection<Deployment>;
export type SamplingFeatureCollection = Collection<SamplingFeature>;
export type ProcedureCollection = Collection<Procedure>;
export type DatastreamCollection = Collection<Datastream>;
export type ObservationCollection = Collection<Observation>;
export type ControlCollection = Collection<Control>;
export type ControlStreamCollection = Collection<ControlStream>;
export type CommandCollection = Collection<Command>;
```

### Type System Summary

**Total types defined:** ~20 interfaces + 3 type aliases + 1 enum

**Size estimate:** ~350-400 lines

**Structure:**

1. Resource type enum (10 lines)
2. Query options (30 lines)
3. Helper types (40 lines)
4. Resource interfaces (250 lines, ~25-30 per resource)
5. Collection types (30 lines)

**Dependencies:**

- `geojson` package for Geometry types
- `shared/models.ts` for primitives
- `ogc-api/model.ts` for link types

---

## Conclusion

### Key Findings

1. **Three-tier hierarchy** - shared → ogc-api → csapi
2. **Optional parameters interface** - One per query type or shared
3. **Resource interfaces** - One per CSAPI resource type
4. **Reuse shared types** - BoundingBox, DateTimeParameter, etc.
5. **Optional properties with `?`** - Never `| null | undefined`
6. **Const assertions for enums** - Type-safe string unions
7. **GeoJSON alignment** - id, type, properties, geometry, links
8. **Format-agnostic** - Only type JSON/GeoJSON format
9. **Generic collections** - Collection<T> for all resource lists
10. **Single model.ts file** - All CSAPI types in one place

### CSAPI Type System Checklist

✅ **Defined:**

- [x] 9 resource interfaces (System, Deployment, etc.)
- [x] Query options (base + extended)
- [x] Helper types (TimeInterval, ResourceLink, etc.)
- [x] Collection generic type
- [x] Resource type enum

✅ **Reused from upstream:**

- [x] BoundingBox
- [x] DateTimeParameter
- [x] CrsCode
- [x] MimeType
- [x] Contact
- [x] OgcApiDocumentLink
- [x] Geometry (from geojson)

✅ **Pattern followed:**

- [x] Three-tier hierarchy
- [x] Optional with `?`
- [x] GeoJSON structure
- [x] Const assertions
- [x] Type safety strategies

**Result:** Comprehensive, type-safe CSAPI implementation ready for coding.
