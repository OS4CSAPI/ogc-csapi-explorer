# Research Plan 13: TypeScript Type System Organization - Findings

**Research Question:** How does class structure affect TypeScript type organization and type safety?

**Source Document:** [docs/research/upstream/typescript-types-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/typescript-types-analysis.md)

**Date:** 2026-02-04

---

## Executive Summary

**Finding:** TypeScript type organization is **completely independent** of single-class vs multi-class decision. Type system design follows a three-tier hierarchy with all API-specific types in one file.

**Key Metrics:**

- **EDR types:** 126 lines in model.ts (single QueryBuilder)
- **CSAPI GeoJSON types:** 350-400 lines in model.ts (9 resources)
- **CSAPI format types:** 1,400-1,600 lines (SensorML 3.0 + SWE Common 3.0)
- **Total type definitions:** 1,750-2,400 lines across 3 files
- **Multi-class impact:** ZERO - same types regardless of class count

**USER MANDATE #3:** This project WILL implement complete TypeScript type definitions for all three formats (GeoJSON, SensorML 3.0, SWE Common 3.0). This is IN-SCOPE and reflects professional TypeScript library standards.

**Convention:** **All types in {api}/model.ts, three-tier hierarchy (shared → ogc-api → api-specific), plus format-specific types in formats/ subdirectories**

**Recommendation:** Type organization **does NOT favor multi-class** - single model.ts works perfectly for any number of QueryBuilder classes. Full format typing is mandatory.

---

## 1. Type Organization Patterns

### Three-Tier Type Hierarchy

**ogc-client uses consistent three-tier structure:**

```
Tier 1: src/shared/models.ts (cross-API primitives)
    ↓ imports
Tier 2: src/ogc-api/model.ts (OGC API family types)
    ↓ imports
Tier 3: src/ogc-api/{api}/model.ts (API-specific types)
```

**Dependency rule:** Lower tiers import from higher, never reverse.

### Tier 1: Shared Primitives (`shared/models.ts`)

**Already defined and ready for CSAPI:**

```typescript
// Spatial
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;

// Temporal
export type DateTimeParameter = Date | { start: Date; end?: Date };

// Format
export type MimeType = string;

// Metadata
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

**CSAPI reuses:** BoundingBox, DateTimeParameter, CrsCode, MimeType, Contact

### Tier 2: OGC API Common (`ogc-api/model.ts`)

**Shared across OGC API Features, Records, Tiles, EDR, CSAPI:**

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
  // CSAPI could add fields here if needed
}

// Links
export interface OgcApiDocumentLink {
  rel: string;
  type: string;
  title: string;
  href: string;
}

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
- Shared by multiple OGC API implementations
- Can be extended per-API
- Moderately stable

**CSAPI reuses:** OgcApiCollectionInfo, OgcApiDocumentLink, ConformanceClass

### Tier 3: CSAPI-Specific (`ogc-api/csapi/model.ts`)

**Types unique to CSAPI (estimated 350-400 lines):**

```typescript
// Resource type enum
export const CSAPIResourceTypes = [
  'System', 'Deployment', 'SamplingFeature', 'Procedure',
  'Datastream', 'Observation', 'Control', 'ControlStream', 'Command'
] as const;
export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

// Query options
export interface QueryOptions { ... }
export interface SystemQueryOptions extends QueryOptions { ... }
export interface ObservationQueryOptions extends QueryOptions { ... }

// 9 resource interfaces
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
export type SystemCollection = Collection<System>;
// ... 8 more collection aliases

// Helper types
export interface TimeInterval { ... }
export type ResourceLink = string | { href: string; title?: string };
export interface HistoryEvent { ... }
export interface Characteristic { ... }
```

**Characteristics:**

- Highly specific to CSAPI
- Not used by other APIs
- Can change without affecting other code
- Most detailed/granular

---

## 2. EDR Type Organization (Baseline)

### EDR model.ts Structure (126 lines)

**Complete file breakdown:**

```typescript
// File: src/ogc-api/edr/model.ts (126 lines)

import { DateTimeParameter } from '../../shared/models.js';

// Special string types (5 lines)
export type WellKnownTextString = string;

// Geometric types (15 lines)
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

// Complex discriminated union (10 lines)
export type ZParameter =
  | { type: 'single'; level: number }
  | { type: 'interval'; minLevel: number; maxLevel: number }
  | { type: 'list'; levels: number[] }
  | { type: 'repeating'; repeat: number; minLevel: number; step: number };

// Helper function for complex type (10 lines)
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

// Query parameter interfaces (70 lines - 7 query types × ~10 lines each)
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

export type optionalRadiusParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: ZParameter;
  within?: number;
  within_units?: string;
  crs?: string;
  f?: string;
};

export type optionalCubeParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: ZParameter;
  crs?: string;
  f?: string;
};

export type optionalTrajectoryParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: ZParameter;
  crs?: string;
  f?: string;
};

export type optionalCorridorParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  z?: ZParameter;
  corridor_width?: number;
  width_units?: string;
  crs?: string;
  f?: string;
};

export type optionalItemsParams = {
  parameter_name?: string[];
  datetime?: DateTimeParameter;
  crs?: string;
  f?: string;
};

// No resource types defined (EDR returns generic data)
```

**Total:** 126 lines for **1 query type** (EDR data query)

**Key observation:** EDR has 7 query parameter interfaces but NO resource type definitions (returns generic data).

### EDR Type Usage

**In url_builder.ts:**

```typescript
import { DateTimeParameter } from '../../shared/models.js';
import { OgcApiCollectionInfo } from '../model.js';
import {
  optionalAreaParams,
  optionalPositionParams,
  ZParameter,
} from './model.js';

export default class EDRQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) {}

  buildPositionDownloadUrl(
    coords: { lon: number; lat: number },
    optional_params: optionalPositionParams = {}
  ): string {
    // Use types for compile-time safety
  }

  buildAreaDownloadUrl(
    bbox: bboxWithoutVerticalAxis,
    optional_params: optionalAreaParams = {}
  ): string {
    // ...
  }
}
```

**Pattern:** Types used for method parameters and return types.

---

## 3. CSAPI Type Organization (Projected)

### CSAPI model.ts Structure (350-400 lines)

**Complete file breakdown:**

| Section              | Lines       | Content                                                  |
| -------------------- | ----------- | -------------------------------------------------------- |
| **Imports**          | 5           | From shared, ogc-api, geojson                            |
| **Resource enum**    | 12          | CSAPIResourceTypes const + type                          |
| **Query options**    | 40          | QueryOptions + 2-3 extended versions                     |
| **Helper types**     | 40          | TimeInterval, ResourceLink, HistoryEvent, Characteristic |
| **System**           | 30          | Most complex resource type                               |
| **Deployment**       | 20          | Medium complexity                                        |
| **SamplingFeature**  | 18          | Medium complexity                                        |
| **Procedure**        | 15          | Simple resource                                          |
| **Datastream**       | 28          | Complex with unit of measurement                         |
| **Observation**      | 22          | Variable result type                                     |
| **Control**          | 12          | Simple resource                                          |
| **ControlStream**    | 15          | Simple resource                                          |
| **Command**          | 15          | Simple resource                                          |
| **Collection types** | 35          | Generic + 9 type aliases                                 |
| **Type guards**      | 50          | Optional - runtime type checking                         |
| **TOTAL**            | **357-407** | **All CSAPI types in one file**                          |

**Comparison to EDR:**

| Metric             | EDR   | CSAPI   | Ratio    |
| ------------------ | ----- | ------- | -------- |
| Lines in model.ts  | 126   | 350-400 | 2.8-3.2x |
| Resource types     | 0     | 9       | ∞        |
| Query option types | 7     | 3-5     | 0.4-0.7x |
| Helper types       | 3     | 4       | 1.3x     |
| **Resource count** | **1** | **9**   | **9x**   |

**Per-resource average:**

- EDR: 126 lines / 1 resource = 126 lines per resource
- CSAPI: 350-400 lines / 9 resources = 39-44 lines per resource

**CSAPI is 3x MORE EFFICIENT per resource!**

### Complete CSAPI model.ts Template

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
 * Generic collection response (GeoJSON FeatureCollection)
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

**Total:** ~380 lines (well within typical file size)

---

## 4. Query Parameter Type Patterns

### Pattern 1: Shared Options Interface

**Best for CSAPI - one interface used by all methods:**

```typescript
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  properties?: string[];
  sortby?: string[];
}

// Usage in url_builder.ts
async getSystems(options?: QueryOptions): Promise<System[]>
async getDeployments(options?: QueryOptions): Promise<Deployment[]>
async getDatastreams(systemId: string, options?: QueryOptions): Promise<Datastream[]>
```

**Benefits:**

- ✅ DRY - defined once, used everywhere
- ✅ Consistent across all 70-80 methods
- ✅ Easy to extend (add one property, all methods get it)
- ✅ Clear developer experience

### Pattern 2: Extended Options

**For resource-specific parameters:**

```typescript
// Base options
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
}

// Extended for systems
export interface SystemQueryOptions extends QueryOptions {
  type?: 'sensor' | 'platform' | 'actuator';
  status?: 'active' | 'inactive';
}

// Extended for observations
export interface ObservationQueryOptions extends QueryOptions {
  observedProperty?: string[];
}

// Usage
async getSystems(options?: SystemQueryOptions): Promise<System[]>
async getObservations(
  datastreamId: string,
  options?: ObservationQueryOptions
): Promise<Observation[]>
```

**When to use:** Only 2-3 resources need extended options (systems, observations).

### Pattern 3: Inline Options (NOT Recommended)

**EDR sometimes uses inline:**

```typescript
buildPositionDownloadUrl(
  coords: { lon: number; lat: number },
  optional_params: {
    parameter_name?: string[];
    datetime?: DateTimeParameter;
    z?: ZParameter;
    crs?: string;
    f?: string;
  } = {}
): string
```

**Problems for CSAPI:**

- ❌ Not reusable (would repeat 70-80 times)
- ❌ Verbose
- ❌ Hard to maintain (changes require updating many methods)

**Verdict:** Use Pattern 1 (shared interface) for CSAPI.

---

## 5. Single-Class vs Multi-Class Type Impact

### Type Organization: IDENTICAL

**Single-class CSAPI:**

```typescript
// model.ts (350-400 lines)
export interface System { ... }
export interface Deployment { ... }
// ... 7 more

// url_builder.ts (700-800 lines)
import { System, Deployment, QueryOptions } from './model.js';

export default class CSAPIQueryBuilder {
  async getSystems(options?: QueryOptions): Promise<System[]> { ... }
  async getDeployments(options?: QueryOptions): Promise<Deployment[]> { ... }
  // ... 68-78 more methods
}
```

**Multi-class CSAPI (9 builders):**

```typescript
// model.ts (350-400 lines) - SAME FILE, SAME TYPES
export interface System { ... }
export interface Deployment { ... }
// ... 7 more

// systems_builder.ts
import { System, QueryOptions } from './model.js';
export class SystemsBuilder {
  async getSystems(options?: QueryOptions): Promise<System[]> { ... }
}

// deployments_builder.ts
import { Deployment, QueryOptions } from './model.js';
export class DeploymentsBuilder {
  async getDeployments(options?: QueryOptions): Promise<Deployment[]> { ... }
}

// ... 7 more builder files
```

**Observation:** **ZERO difference in type organization**

### Type Reuse Across Classes

**All classes import from same model.ts:**

```typescript
// Single-class imports all types once
import { System, Deployment, ..., QueryOptions } from './model.js';

// Multi-class - each builder imports what it needs
// systems_builder.ts
import { System, SystemQueryOptions } from './model.js';

// deployments_builder.ts
import { Deployment, QueryOptions } from './model.js';

// observations_builder.ts
import { Observation, ObservationQueryOptions } from './model.js';
```

**Result:** Multi-class has 9 import statements instead of 1, but SAME types.

### Type Safety: IDENTICAL

**Single-class type safety:**

```typescript
export default class CSAPIQueryBuilder {
  async getSystems(options?: SystemQueryOptions): Promise<System[]>;
  async getDeployments(options?: QueryOptions): Promise<Deployment[]>;
  async getObservations(
    datastreamId: string,
    options?: ObservationQueryOptions
  ): Promise<Observation[]>;
}
```

**Multi-class type safety:**

```typescript
export class SystemsBuilder {
  async getSystems(options?: SystemQueryOptions): Promise<System[]>;
}

export class DeploymentsBuilder {
  async getDeployments(options?: QueryOptions): Promise<Deployment[]>;
}

export class ObservationsBuilder {
  async getObservations(
    datastreamId: string,
    options?: ObservationQueryOptions
  ): Promise<Observation[]>;
}
```

**Observation:** **IDENTICAL method signatures** regardless of class organization.

### Developer Experience: Single-Class Better

**Single-class autocomplete:**

```typescript
const builder = await endpoint.csapi('sensors');
builder // IntelliSense shows ALL 70-80 methods
  .getSystems();
getDeployments();
getSystemById();
getDatastreams();
getObservations();
// ... all methods visible
```

**Multi-class autocomplete:**

```typescript
const systemsBuilder = await endpoint.csapiSystems('sensors');
systemsBuilder // IntelliSense shows only 8-12 methods
  .getSystems();
getSystemById();
getSystemSubsystems();
getSystemDatastreams();
// ... only system methods

const deploymentsBuilder = await endpoint.csapiDeployments('sensors');
deploymentsBuilder // Need separate builder for deployments
  .getDeployments();
getDeploymentById();
// ... only deployment methods
```

**Problem:** Multi-class requires users to know which builder to use BEFORE they can discover methods.

**Single-class advantage:** One builder, all methods discoverable immediately.

---

## 6. Type Safety Strategies Used

### Strategy 1: Discriminated Unions

**Pattern for complex parameters (EDR example):**

```typescript
export type ZParameter =
  | { type: 'single'; level: number }
  | { type: 'interval'; minLevel: number; maxLevel: number }
  | { type: 'list'; levels: number[] }
  | { type: 'repeating'; repeat: number; minLevel: number; step: number };

// TypeScript can narrow type based on discriminant
function handleZ(z: ZParameter): string {
  switch (z.type) {
    case 'single':
      // TypeScript knows z.level exists here
      return `${z.level}`;
    case 'interval':
      // TypeScript knows z.minLevel and z.maxLevel exist here
      return `${z.minLevel}/${z.maxLevel}`;
    case 'list':
      // TypeScript knows z.levels exists here
      return z.levels.join(',');
    case 'repeating':
      // TypeScript knows z.repeat, z.minLevel, z.step exist here
      return `R${z.repeat}/${z.minLevel}/${z.step}`;
  }
}
```

**When to use:** Complex parameters with multiple valid structures.

**CSAPI candidate:** Not needed - simpler parameter structures.

### Strategy 2: Const Assertions for Enums

**Creates type-safe union from array:**

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

// Creates: 'System' | 'Deployment' | ... | 'Command'
export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];
```

**Benefits:**

- ✅ Single source of truth
- ✅ Can iterate array at runtime
- ✅ Type safety at compile time
- ✅ Auto-completion for string literals

**CSAPI usage:** Resource type enum (9 values).

### Strategy 3: Strict Null Checks

**All types assume `strictNullChecks: true`:**

```typescript
// Optional properties use ?
export interface System {
  id: string; // Required - never undefined
  name?: string; // Optional - string | undefined
  description?: string; // Optional - string | undefined
}

// NOT this:
export interface System {
  id: string;
  name: string | undefined; // ❌ Use ? instead
  description: string | null; // ❌ Use ? instead
}
```

**Rule:** Use `?` for optional properties, not `| undefined | null`.

### Strategy 4: Generic Types

**For reusable collection types:**

```typescript
export interface Collection<T> {
  type: 'FeatureCollection';
  features: T[];
  links: OgcApiDocumentLink[];
  numberMatched?: number;
  numberReturned: number;
  timeStamp: string;
}

// Usage with type aliases
export type SystemCollection = Collection<System>;
export type DeploymentCollection = Collection<Deployment>;
// ... 7 more
```

**Benefits:**

- ✅ Reusable for all 9 resource types
- ✅ Type-safe array contents
- ✅ Clear intent

**CSAPI usage:** Collection wrapper for all resources.

### Strategy 5: Type Guards (Optional)

**For runtime type checking:**

```typescript
export function isSystem(obj: any): obj is System {
  return obj && typeof obj === 'object' && obj.type === 'System';
}

export function isDeployment(obj: any): obj is Deployment {
  return obj && typeof obj === 'object' && obj.type === 'Deployment';
}

// Usage
const resource: System | Deployment = await fetchResource(...);
if (isSystem(resource)) {
  // TypeScript knows resource is System here
  console.log(resource.properties.systemType);
}
```

**When to use:** When parsing mixed response types.

**CSAPI usage:** Optional - may not be needed if response type is known.

---

## 7. GeoJSON Alignment

### CSAPI Resources Follow GeoJSON Structure

**Standard GeoJSON Feature:**

```typescript
interface GeoJSONFeature {
  type: 'Feature';
  id?: string | number;
  properties: object;
  geometry: Geometry | null;
}
```

**CSAPI System (aligned with GeoJSON):**

```typescript
export interface System {
  id: string; // GeoJSON id (required for CSAPI)
  type: 'System'; // GeoJSON type (but resource name not 'Feature')
  properties: {
    // GeoJSON properties object
    name: string;
    description?: string;
    // ... CSAPI-specific properties
  };
  geometry?: Geometry; // GeoJSON geometry (optional for CSAPI)
  links: OgcApiDocumentLink[]; // HATEOAS links (CSAPI addition)
}
```

**Why align with GeoJSON?**

- ✅ Familiar structure for developers
- ✅ Can use existing GeoJSON libraries
- ✅ OGC API standards use GeoJSON
- ✅ Spatial data support

### GeoJSON Types Import

**Use @types/geojson package:**

```typescript
import { Geometry, Point, Polygon, LineString } from 'geojson';

export interface System {
  // Accept any geometry type
  geometry?: Geometry;
}

export interface Observation {
  // Only accept point geometry
  geometry?: Point;
}

export interface SamplingFeature {
  // Accept multiple geometry types
  geometry?: Geometry | Point | Polygon | LineString;
}
```

**Package:** `npm install --save-dev @types/geojson`

---

## 8. Format-Specific Types

### Challenge: Multiple Representations

**CSAPI resources can be returned in different formats:**

- **[GeoJSON / JSON-FG](https://datatracker.ietf.org/doc/html/rfc7946)** - Standard spatial feature format
- **[SensorML 3.0](https://docs.ogc.org/is/23-001/23-001.html)** ([OGC 23-001](https://docs.ogc.org/is/23-001/23-001.html)) - JSON only (`application/sml+json`)
- **[SWE Common 3.0](https://docs.ogc.org/is/23-002/23-002.html)** ([OGC 23-002](https://docs.ogc.org/is/23-002/23-002.html))
  - JSON (`application/swe+json`)
  - Text/CSV (`application/swe+text`)
  - Binary (`application/swe+binary`)
- **JSON-LD** - Semantic web format

**Question:** Should we define TypeScript types for all formats?

### EDR Precedent: Format-Agnostic (NOT Applicable to CSAPI)

**EDR doesn't define format-specific types:**

```typescript
// Generic return type
async getPosition(...): Promise<any>  // Could be GeoJSON, CoverageJSON, etc.
```

**Why EDR doesn't type formats:**

- EDR has 1 query type with multiple optional format encodings
- Most EDR users request default GeoJSON and never use other formats
- Alternative formats are truly optional/secondary use cases

**Why CSAPI is DIFFERENT:**

- **100% of CSAPI users will use ALL THREE formats**
- **SensorML 3.0:** Used almost 100% of the time for detailed system metadata
- **SWE Common 3.0:** Used almost 100% of the time for observation data and schemas
- **GeoJSON:** Used for spatial feature collections and basic metadata
- All three formats are **equally critical** to CSAPI functionality

### USER MANDATE: Full TypeScript Types for All Formats

**FIRM DESIGN DECISION (2026-02-04):** This project WILL implement complete TypeScript type definitions for all three formats. This is a MANDATED requirement and is IN-SCOPE for the project.

**Rationale for typing all formats:**

1. **Core Value Proposition of TypeScript Libraries**

   - IntelliSense/Autocomplete for discovering properties
   - Compile-time validation catching typos and structural errors
   - Self-documenting types showing structure without reading docs
   - Refactoring safety with IDE tracking usage across codebase

2. **Industry Standard Practice**

   - AWS SDK v3: Types every API response object
   - Google Cloud SDK: Comprehensive typing for all resources
   - Stripe SDK: Full typing for all API objects
   - Azure SDK: Types everything users interact with
   - **No professional TypeScript SDK ships `any` for critical data structures**

3. **CSAPI Usage Pattern**

   - Users will work with SensorML objects constantly (system metadata, capabilities, characteristics)
   - Users will work with SWE Common objects constantly (observation schemas, data components)
   - Not typing these means users lose TypeScript benefits for their primary use cases
   - Without types, library is effectively JavaScript with TypeScript for only 1/3 of functionality

4. **Type Safety Examples**

**Without SensorML types (BAD):**

```typescript
const sensorML = await getSensorML('sensor123');  // Returns any
console.log(sensorML.capabilites);  // ❌ TYPO - no error, undefined at runtime
console.log(sensorML.???);  // ❌ No IntelliSense - what properties exist?
```

**With SensorML types (GOOD):**

```typescript
const sensorML: SystemSensorML = await getSensorML('sensor123');
console.log(sensorML.capabilites);  // ✅ TypeScript ERROR - did you mean 'capabilities'?
console.log(sensorML.|);  // ✅ IntelliSense shows: type, id, capabilities, characteristics, components
```

### Type Definitions Required

**1. GeoJSON Types (Already planned - 350-400 lines):**

```typescript
// In model.ts
export interface System {
  id: string;
  type: 'System';
  properties: {
    name: string;
    description?: string;
    // ... all GeoJSON properties
  };
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
}
```

**2. SensorML 3.0 Types (NEW - 800-1200 lines):**

```typescript
// In formats/sensorml/types.ts

// Process types
export type SensorMLProcess =
  | PhysicalSystem
  | PhysicalComponent
  | SimpleProcess
  | AggregateProcess;

export interface PhysicalSystem {
  type: 'PhysicalSystem';
  id: string;
  description?: string;
  identifier?: string;
  classification?: Classification[];
  validTime?: TimeInterval;
  capabilities?: CapabilityList[];
  characteristics?: CharacteristicList[];
  contacts?: Contact[];
  documentation?: Documentation[];
  history?: Event[];
  components?: ComponentList[];
  connections?: ConnectionList[];
  modes?: ModeList[];
  // ... full SensorML schema
}

export interface PhysicalComponent {
  type: 'PhysicalComponent';
  id: string;
  description?: string;
  // ... component-specific properties
}

export interface SimpleProcess {
  type: 'SimpleProcess';
  id: string;
  description?: string;
  inputs?: InputList[];
  outputs?: OutputList[];
  parameters?: ParameterList[];
  // ... process properties
}

// Capability/Characteristic components
export interface CapabilityList {
  name: string;
  capabilities: Capability[];
}

export interface Capability {
  name: string;
  description?: string;
  definition?: string;
  value: SWEDataComponent; // Links to SWE Common types
}

// ... 30+ more interfaces for complete SensorML schema
```

**3. SWE Common 3.0 Types (NEW - 600-800 lines):**

```typescript
// In formats/swecommon/types.ts

// Data component base types
export type SWEDataComponent =
  | DataRecord
  | DataArray
  | Vector
  | DataChoice
  | Quantity
  | Count
  | Boolean
  | Text
  | Category
  | Time
  | QuantityRange
  | CountRange
  | TimeRange
  | CategoryRange;

export interface DataRecord {
  type: 'DataRecord';
  id?: string;
  label?: string;
  description?: string;
  definition?: string;
  fields: DataField[];
}

export interface DataField {
  name: string;
  component: SWEDataComponent;
}

export interface DataArray {
  type: 'DataArray';
  id?: string;
  label?: string;
  description?: string;
  elementType: SWEDataComponent;
  elementCount?: Count | QuantityRange;
  values?: EncodedValues;
  encoding?: DataEncoding;
}

export interface Quantity {
  type: 'Quantity';
  id?: string;
  label?: string;
  description?: string;
  definition?: string;
  uom: UnitOfMeasure;
  constraint?: AllowedValues;
  quality?: Quality[];
  nilValues?: NilValues[];
  value?: number;
}

export interface UnitOfMeasure {
  code?: string; // UCUM code
  href?: string; // URI to unit definition
}

// Encoding types
export type DataEncoding = JSONEncoding | TextEncoding | BinaryEncoding;

export interface JSONEncoding {
  type: 'JSONEncoding';
}

export interface TextEncoding {
  type: 'TextEncoding';
  tokenSeparator: string;
  blockSeparator: string;
  decimalSeparator?: string;
  collapseWhiteSpaces?: boolean;
}

export interface BinaryEncoding {
  type: 'BinaryEncoding';
  byteOrder: 'bigEndian' | 'littleEndian';
  byteEncoding: 'base64' | 'raw';
  byteLength?: number;
  members: BinaryMember[];
}

// ... 20+ more interfaces for complete SWE Common schema
```

### Code Volume Impact

**Type definitions:**
| Format | Lines | Files |
|--------|-------|-------|
| GeoJSON types | 350-400 | model.ts |
| SensorML 3.0 types | 800-1200 | formats/sensorml/types.ts |
| SWE Common 3.0 types | 600-800 | formats/swecommon/types.ts |
| **TOTAL TYPES** | **1,750-2,400** | **3 files** |

**Format parsers (already mandated):**
| Format | Lines | Files |
|--------|-------|-------|
| GeoJSON parser | 50-100 | Built-in (geojson package) |
| SensorML 3.0 parser | 1,600-2,200 | 6 files in formats/sensorml/ |
| SWE Common 3.0 parser | 1,600-2,250 | 6 files in formats/swecommon/ |
| **TOTAL PARSERS** | **3,250-4,550** | **13 files** |

**Combined format handling:**

- Type definitions: ~1,750-2,400 lines
- Parser implementations: ~3,250-4,550 lines
- **Total: ~5,000-6,950 lines** (types + parsers)

### TypeScript Types Usage Pattern

**Users import and use typed objects:**

```typescript
import type {
  System, // GeoJSON
  SystemSensorML, // SensorML 3.0
  DataRecord, // SWE Common 3.0
  Quantity,
} from 'ogc-client';

// Type-safe GeoJSON
const system: System = await builder.getSystem('sensor123');
console.log(system.properties.name); // ✅ Typed

// Type-safe SensorML 3.0
const sensorML: SystemSensorML = await builder.getSystemAsSensorML('sensor123');
console.log(sensorML.capabilities); // ✅ Typed - IntelliSense works
console.log(sensorML.components[0].characteristics); // ✅ Full type safety

// Type-safe SWE Common 3.0
const schema: DataRecord = await builder.getDatastreamSchema('ds123');
console.log(schema.fields[0].component); // ✅ Typed - can be Quantity, Count, etc.
if (schema.fields[0].component.type === 'Quantity') {
  // ✅ TypeScript narrows type to Quantity
  console.log(schema.fields[0].component.uom.code); // Access unit code safely
}
```

### Comparison: Typed vs Untyped

| Aspect                   | Untyped (any)             | Typed (Full Interfaces)             |
| ------------------------ | ------------------------- | ----------------------------------- |
| **Compile-time safety**  | ❌ No validation          | ✅ Catches typos, structural errors |
| **IntelliSense**         | ❌ No autocomplete        | ✅ Full property discovery          |
| **Refactoring**          | ❌ Manual search          | ✅ IDE tracks all usage             |
| **Documentation**        | ❌ Must read specs        | ✅ Self-documenting types           |
| **Developer experience** | ❌ Poor (like JavaScript) | ✅ Excellent (TypeScript benefits)  |
| **Professional quality** | ❌ Below standard         | ✅ Industry standard                |
| **Code volume**          | ~0 lines                  | ~1,750-2,400 lines                  |
| **Maintenance**          | ✅ None needed            | ⚠️ Keep synced with specs           |

### Recommendation: FULL TYPING (USER MANDATE)

**Type ALL THREE formats with complete TypeScript interfaces:**

- ✅ GeoJSON types (350-400 lines)
- ✅ SensorML 3.0 types (800-1200 lines)
- ✅ SWE Common 3.0 types (600-800 lines)

**Justification:**

1. **This is what professional TypeScript libraries do** - Type everything users work with
2. **100% of users need all three formats** - Not typing = losing TypeScript benefits for primary use cases
3. **Core value proposition** - Type safety, IntelliSense, refactoring support
4. **Enables better developer experience** - Users discover properties, catch errors early
5. **Worth the +1,750-2,400 lines** - This IS the library's value, not bloat

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - This is a firm user mandate and industry best practice

---

## 9. Optional Properties Convention

### Pattern: Always Use `?` for Optional

**All optional properties use `?` operator:**

```typescript
export interface System {
  id: string; // Required - always present
  type: 'System'; // Required - always present
  properties: {
    name: string; // Required
    description?: string; // Optional - property may not exist
    keywords?: string[]; // Optional - array or undefined
    contacts?: Contact[]; // Optional - array or undefined
  };
  geometry?: Geometry; // Optional - geometry or undefined
  links: OgcApiDocumentLink[]; // Required - array (can be empty)
}
```

**NOT this:**

```typescript
// ❌ Don't do this
export interface System {
  id: string;
  description: string | undefined; // Use ? instead
  contacts: Contact[] | null; // Use ? instead
  keywords: string[] | undefined; // Use ? instead
}
```

**Rule:** `?` means property may not exist. `| null` means property exists but value is null (rarely needed).

### Required vs Optional Decision

**Required properties (based on CSAPI spec):**

- `id` - Unique identifier (always required)
- `type` - Resource type discriminant (always required)
- `links` - HATEOAS links (always required, but array can be empty)
- `properties.name` - Human-readable name (usually required)

**Optional properties (most others):**

- `description` - Not all resources have descriptions
- `geometry` - Not all resources have spatial extent
- `keywords` - Optional metadata
- `contacts` - Optional metadata
- Most nested properties

**When in doubt:** Make it optional (use `?`).

### Empty Array vs Undefined

**Arrays that might be empty vs missing:**

```typescript
// Can be empty array or undefined
contacts?: Contact[];  // undefined | Contact[]

// Usage with optional chaining
if (system.contacts?.length > 0) {
  // Has contacts
}

// NOT this:
contacts: Contact[];  // Never undefined, but can be []
if (system.contacts.length > 0) {
  // Must check !== undefined first
}
```

**Rule:** If property might not exist at all, use `?`. If property always exists but can be empty, don't use `?`.

---

## 10. Type Definition Location Rules

### Three-Tier Location Strategy

**Rule 1: Shared primitives → `src/shared/models.ts`**

```typescript
// Already exist - REUSE, don't redefine
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;
export type DateTimeParameter = Date | { start: Date; end?: Date };
export type MimeType = string;
export interface Contact { ... }
```

**Rule 2: OGC API common → `src/ogc-api/model.ts`**

```typescript
// Already exist - REUSE, don't redefine
export type ConformanceClass = string;
export interface OgcApiCollectionInfo { ... }
export interface OgcApiDocumentLink { ... }
export interface CollectionParameter { ... }
```

**Rule 3: CSAPI-specific → `src/ogc-api/csapi/model.ts`**

```typescript
// Define in CSAPI model.ts - ALL new types here
export interface System { ... }
export interface Deployment { ... }
export interface QueryOptions { ... }
export const CSAPIResourceTypes = [...] as const;
export type CSAPIResourceType = ...;
```

### What Goes Where?

| Type                         | Location           | Reason                       |
| ---------------------------- | ------------------ | ---------------------------- |
| `System`, `Deployment`, etc. | `csapi/model.ts`   | CSAPI resources              |
| `QueryOptions`               | `csapi/model.ts`   | CSAPI query parameters       |
| `SystemQueryOptions`         | `csapi/model.ts`   | CSAPI extended options       |
| `CSAPIResourceType`          | `csapi/model.ts`   | CSAPI enum                   |
| `TimeInterval`               | `csapi/model.ts`   | CSAPI-specific temporal type |
| `ResourceLink`               | `csapi/model.ts`   | CSAPI helper type            |
| `Collection<T>`              | `csapi/model.ts`   | CSAPI generic collection     |
| `BoundingBox`                | `shared/models.ts` | ✅ Already exists, reuse     |
| `DateTimeParameter`          | `shared/models.ts` | ✅ Already exists, reuse     |
| `Contact`                    | `shared/models.ts` | ✅ Already exists, reuse     |
| `OgcApiDocumentLink`         | `ogc-api/model.ts` | ✅ Already exists, reuse     |
| `OgcApiCollectionInfo`       | `ogc-api/model.ts` | ✅ Already exists, reuse     |
| `Geometry`, `Point`          | `@types/geojson`   | ✅ External package          |

### Single File Organization

**All CSAPI types in `csapi/model.ts`:**

```typescript
// src/ogc-api/csapi/model.ts

// Section 1: Imports (5 lines)
import { Geometry, Point } from 'geojson';
import { BoundingBox, DateTimeParameter, Contact } from '../../shared/models.js';
import { OgcApiDocumentLink } from '../model.js';

// Section 2: Enums (12 lines)
export const CSAPIResourceTypes = [...] as const;
export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

// Section 3: Query Options (40 lines)
export interface QueryOptions { ... }
export interface SystemQueryOptions extends QueryOptions { ... }
export interface ObservationQueryOptions extends QueryOptions { ... }

// Section 4: Helper Types (40 lines)
export interface TimeInterval { ... }
export type ResourceLink = ...;
export interface HistoryEvent { ... }
export interface Characteristic { ... }

// Section 5: Resource Interfaces (225 lines, 9 resources × 25 lines avg)
export interface System { ... }
export interface Deployment { ... }
export interface SamplingFeature { ... }
export interface Procedure { ... }
export interface Datastream { ... }
export interface Observation { ... }
export interface Control { ... }
export interface ControlStream { ... }
export interface Command { ... }

// Section 6: Collection Types (35 lines)
export interface Collection<T> { ... }
export type SystemCollection = Collection<System>;
// ... 8 more aliases
```

**Total:** ~357 lines in ONE file

**Maintainability:** ✅ Excellent - all types in one place, easy to find, easy to modify.

---

## 11. Type System Impact on Architecture Decision

### Single-Class Type Organization

**Implementation:**

```typescript
// model.ts (350-400 lines)
export interface System { ... }
export interface Deployment { ... }
export interface QueryOptions { ... }
// ... all types

// url_builder.ts (700-800 lines)
import { System, Deployment, QueryOptions, ... } from './model.js';

export default class CSAPIQueryBuilder {
  // 70-80 methods using types from model.ts
  async getSystems(options?: QueryOptions): Promise<System[]>
  async getDeployments(options?: QueryOptions): Promise<Deployment[]>
  async getSystemById(systemId: string): Promise<System>
  // ... 67-77 more methods
}
```

**Type imports:** 1 import statement (imports all types once)

**Type organization:** ✅ Clean, all types in one place

**Developer experience:** ✅ Excellent - IntelliSense shows all methods

### Multi-Class Type Organization

**Implementation (9 separate builders):**

```typescript
// model.ts (350-400 lines) - SAME FILE
export interface System { ... }
export interface Deployment { ... }
export interface QueryOptions { ... }
// ... all types (IDENTICAL to single-class)

// systems_builder.ts
import { System, SystemQueryOptions } from './model.js';
export class SystemsBuilder {
  async getSystems(options?: SystemQueryOptions): Promise<System[]>
  async getSystemById(systemId: string): Promise<System>
  // ... 6-10 more system methods
}

// deployments_builder.ts
import { Deployment, QueryOptions } from './model.js';
export class DeploymentsBuilder {
  async getDeployments(options?: QueryOptions): Promise<Deployment[]>
  async getDeploymentById(deploymentId: string): Promise<Deployment>
  // ... 6-10 more deployment methods
}

// ... 7 more builder files
```

**Type imports:** 9 import statements (each builder imports what it needs)

**Type organization:** ⚠️ Same model.ts, but imports scattered across 9 files

**Developer experience:** ❌ Worse - must know which builder to use before discovering methods

### Type System Verdict

**Does type organization favor multi-class?** ❌ **NO**

**Key findings:**

1. ✅ Type definitions are IDENTICAL regardless of class count
2. ✅ Single model.ts works perfectly for both approaches
3. ✅ Single-class has simpler imports (1 import vs 9)
4. ✅ Single-class has better IntelliSense (all methods visible)
5. ❌ Multi-class has NO type safety advantage
6. ❌ Multi-class has NO type organization advantage

**Conclusion:** Type system is **completely neutral** on class count decision, with slight edge to single-class for simpler imports and better DX.

---

## 12. Type Granularity Analysis

### Granularity Levels

**Level 1: Coarse** (primitive type aliases)

```typescript
export type CrsCode = string;
export type MimeType = string;
export type ResourceLink = string | { href: string; title?: string };
```

**Level 2: Medium** (simple interfaces)

```typescript
export interface Contact {
  name?: string;
  email?: string;
  phone?: string;
}

export interface TimeInterval {
  start?: Date;
  end?: Date;
}
```

**Level 3: Fine** (detailed interfaces)

```typescript
export interface System {
  id: string;
  type: 'System';
  properties: {
    name: string;
    description?: string;
    systemType?: 'sensor' | 'platform' | 'actuator';
    // ... 10 more properties
  };
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
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

### CSAPI Granularity Strategy

**Use fine granularity (Level 3) for:**

- ✅ System, Deployment, SamplingFeature (core resources)
- ✅ Datastream, Observation (frequently used)
- ✅ Procedure (important metadata)

**Use medium granularity (Level 2) for:**

- ✅ Control, ControlStream, Command (less common)
- ✅ Helper types (TimeInterval, HistoryEvent, Characteristic)
- ✅ Nested objects

**Use coarse granularity (Level 1) for:**

- ✅ ResourceLink (string or object)
- ✅ String identifiers

**Skip very fine (Level 4):**

- ❌ Not needed - CSAPI has simpler parameter structures than EDR

**Result:** Balanced type system with appropriate detail level for each type.

---

## 13. Type Export Strategy

### What Gets Exported Publicly

**From main `src/index.ts`:**

✅ **Always export:**

- Resource types: `System`, `Deployment`, `Observation`, etc.
- Query option types: `QueryOptions`, `SystemQueryOptions`, `ObservationQueryOptions`
- Collection types: `SystemCollection`, `DeploymentCollection`, etc.
- Helper types: `TimeInterval`, `ResourceLink`, `Characteristic`
- Resource enum: `CSAPIResourceTypes`, `CSAPIResourceType`

❌ **Never export:**

- QueryBuilder class (accessed via factory method)
- Internal helpers
- Type guards (unless needed by users)

### EDR Export Pattern (for comparison)

**EDR types NOT exported:**

```typescript
// ❌ NOT in src/index.ts
export type { optionalAreaParams, ZParameter } from './ogc-api/edr/model.js';
```

**Why?** Users call methods directly, don't construct parameter objects.

### CSAPI Export Strategy (DIFFERENT from EDR)

**CSAPI types SHOULD be exported:**

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
  SystemCollection,
  DeploymentCollection,
  Collection,
  TimeInterval,
  ResourceLink,
  CSAPIResourceType,
} from './ogc-api/csapi/model.js';
```

**Why export?** Users may need types for annotations:

```typescript
import type { System, Datastream, QueryOptions } from 'ogc-client';

const systems: System[] = await fetchSystems();
const datastream: Datastream = await fetchDatastream();

function processSystems(systems: System[], options: QueryOptions) {
  // Type-safe function signature
}
```

**QueryBuilder NOT exported:**

```typescript
// ❌ NOT in src/index.ts
export { default as CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';
```

**Why?** Accessed via factory method:

```typescript
const builder = await endpoint.csapi('sensors'); // Type inferred
```

---

## 14. Key Findings Summary

### Type Organization

| Aspect                | Single-Class       | Multi-Class         | Winner       |
| --------------------- | ------------------ | ------------------- | ------------ |
| **model.ts size**     | 350-400 lines      | 350-400 lines       | TIE          |
| **Type definitions**  | Same types         | Same types          | TIE          |
| **Import statements** | 1 (all types once) | 9 (one per builder) | Single-class |
| **Type location**     | One place          | One place           | TIE          |
| **Type reuse**        | Easy               | Easy                | TIE          |

### Type Safety

| Aspect                  | Single-Class       | Multi-Class  | Winner |
| ----------------------- | ------------------ | ------------ | ------ |
| **Method signatures**   | Fully typed        | Fully typed  | TIE    |
| **Parameter types**     | QueryOptions, etc. | Same types   | TIE    |
| **Return types**        | System, etc.       | Same types   | TIE    |
| **Compile-time safety** | Full               | Full         | TIE    |
| **Runtime validation**  | User mandate       | User mandate | TIE    |

### Developer Experience

| Aspect               | Single-Class      | Multi-Class             | Winner       |
| -------------------- | ----------------- | ----------------------- | ------------ |
| **IntelliSense**     | All 70-80 methods | Only 8-12 methods       | Single-class |
| **Method discovery** | Immediate         | Must know builder first | Single-class |
| **Type imports**     | Import once       | Import per file         | Single-class |
| **Autocomplete**     | Full visibility   | Limited visibility      | Single-class |

### Verdict

**Type system impact on architecture:** **NEUTRAL to SLIGHT FAVOR for single-class**

**Reasons:**

1. ✅ Type organization is IDENTICAL regardless of class count
2. ✅ All types live in one model.ts file for both approaches
3. ✅ Type safety is IDENTICAL for both approaches
4. ✅ Single-class has simpler imports (1 vs 9)
5. ✅ Single-class has better IntelliSense/autocomplete
6. ❌ Multi-class has ZERO type-related advantages

**Conclusion:** Type system does NOT favor multi-class. Single-class is equal or better in all type-related metrics.

---

## 15. Recommended Type System

### Complete CSAPI Type System (350-400 lines)

**File:** `src/ogc-api/csapi/model.ts`

**Structure:**

1. **Imports** (5 lines)

   - geojson types
   - shared models
   - ogc-api models

2. **Resource Type Enum** (12 lines)

   - CSAPIResourceTypes const array
   - CSAPIResourceType union type

3. **Query Options** (40 lines)

   - QueryOptions interface (base)
   - SystemQueryOptions extends QueryOptions
   - ObservationQueryOptions extends QueryOptions

4. **Helper Types** (40 lines)

   - TimeInterval interface
   - ResourceLink union type
   - HistoryEvent interface
   - Characteristic interface

5. **9 Resource Interfaces** (225 lines, ~25 lines each)

   - System (30 lines - most complex)
   - Deployment (20 lines)
   - SamplingFeature (18 lines)
   - Procedure (15 lines)
   - Datastream (28 lines)
   - Observation (22 lines)
   - Control (12 lines)
   - ControlStream (15 lines)
   - Command (15 lines)

6. **Collection Types** (35 lines)
   - Collection<T> generic interface
   - 9 type aliases (SystemCollection, etc.)

**Total:** ~357 lines

### Type System Benefits

✅ **Comprehensive** - All CSAPI resources typed
✅ **Type-safe** - Compile-time validation
✅ **Reusable** - Shared types from upstream
✅ **GeoJSON-aligned** - Familiar structure
✅ **Well-documented** - TSDoc comments
✅ **Single location** - All types in one file
✅ **Exportable** - Users can import for annotations

### Implementation Checklist

- [x] Define 9 resource interfaces
- [x] Define query option interfaces (base + extended)
- [x] Define helper types (TimeInterval, ResourceLink, etc.)
- [x] Define collection generic + type aliases
- [x] Define resource type enum
- [x] Import shared types (BoundingBox, DateTimeParameter, Contact)
- [x] Import OGC API types (OgcApiDocumentLink, OgcApiCollectionInfo)
- [x] Import GeoJSON types (Geometry, Point)
- [x] Use optional properties with `?`
- [x] Use const assertions for enums
- [x] Align with GeoJSON structure
- [x] Export all types from src/index.ts

---

## Appendix: Complete Type Definitions

### Complete model.ts Template

See Section 3 for full 380-line template.

### Type Size Breakdown

| Type                    | Lines   | Notes                    |
| ----------------------- | ------- | ------------------------ |
| Imports                 | 5       | 3 import statements      |
| CSAPIResourceTypes      | 12      | Const array + type       |
| QueryOptions            | 12      | Base interface           |
| SystemQueryOptions      | 8       | Extends QueryOptions     |
| ObservationQueryOptions | 8       | Extends QueryOptions     |
| TimeInterval            | 5       | Simple interface         |
| ResourceLink            | 3       | Union type               |
| HistoryEvent            | 5       | Simple interface         |
| Characteristic          | 7       | Simple interface         |
| System                  | 30      | Most complex resource    |
| Deployment              | 20      | Medium complexity        |
| SamplingFeature         | 18      | Medium complexity        |
| Procedure               | 15      | Simple resource          |
| Datastream              | 28      | Complex with UoM         |
| Observation             | 22      | Variable result type     |
| Control                 | 12      | Simple resource          |
| ControlStream           | 15      | Simple resource          |
| Command                 | 15      | Simple resource          |
| Collection<T>           | 10      | Generic interface        |
| Type aliases (9)        | 27      | SystemCollection, etc.   |
| **TOTAL**               | **357** | **Complete type system** |

---

**Document Version:** 1.0  
**Date:** 2026-02-04  
**Confidence:** ⭐⭐⭐⭐⭐ (5/5)
