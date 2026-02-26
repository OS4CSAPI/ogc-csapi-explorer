# CSAPI-Specific Architectural Decisions

**Purpose:** Document architectural choices for cleanly implementing 9 CSAPI resource types within ogc-client patterns with full format support.

**Context:** CSAPI has more resource types (9) than any other OGC API in ogc-client (WFS: 1, STAC: 2, EDR: 1). Must design architecture that handles this complexity without bloat. **CRITICAL REQUIREMENT:** Full format handling for GeoJSON, SensorML 3.0, and SWE Common 3.0.

**Date:** 2026-02-04 (Updated)
**Original Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [CSAPI Resource Landscape](#2-csapi-resource-landscape)
3. [Resource Type Patterns](#3-resource-type-patterns)
4. [Part 1 vs Part 2 Architecture](#4-part-1-vs-part-2-architecture)
5. [Sub-Resource Handling](#5-sub-resource-handling)
6. [Shared vs Unique Implementation](#6-shared-vs-unique-implementation)
7. [Resource Discovery](#7-resource-discovery)
8. [Format Handling: GeoJSON, SensorML 3.0, and SWE Common 3.0](#8-format-handling-geojson-sensorml-30-and-swe-common-30)
9. [Implementation Strategy](#9-implementation-strategy)
10. [Complete Architecture Design](#10-complete-architecture-design)

---

## 1. Overview

### The Challenge

**CSAPI has 9 resource types** (vs 1-2 for other OGC APIs in ogc-client):

**Part 1: Feature Resources (5 types)**

1. Systems - Sensor devices and platforms
2. Deployments - System installations over time
3. Procedures - Observation/processing methods
4. Sampling Features - Locations where observations occur
5. Properties - Measurable properties

**Part 2: Dynamic Data (4 types)** 6. Datastreams - Time series data channels 7. Observations - Individual measurements 8. Control Streams - Command channels 9. Commands - Control instructions

**Question:** How to implement 9 resources cleanly without creating 9x the code volume?

### Key Constraints

**From upstream patterns:**

- Single QueryBuilder class per API
- URL building only (no data fetching)
- Methods return strings, not objects
- Minimal validation (trust TypeScript + server)

**From governance:**

- Minimal impact on existing code
- Follow EDR pattern (PR #114)
- No over-engineering
- Justify any code volume

**FIRM DESIGN DECISION (2026-02-04):**

- ✅ **Full format handling required**
- ✅ GeoJSON parsing (all resources)
- ✅ SensorML 3.0 parsing (systems, deployments, procedures)
- ✅ SWE Common 3.0 parsing (datastreams, control streams)
- ❌ NO support for older versions (SensorML 2.0/2.1, SWE Common 2.0)

---

## 2. CSAPI Resource Landscape

### Resource Inventory

**Part 1 Resources (Feature-based):**

| Resource          | Endpoints | Sub-resources                                          | History | Formats Supported     |
| ----------------- | --------- | ------------------------------------------------------ | ------- | --------------------- |
| Systems           | 5         | subsystems, deployments, samplingFeatures, datastreams | Yes     | GeoJSON, SensorML 3.0 |
| Deployments       | 4         | subdeployments, systems                                | Yes     | GeoJSON, SensorML 3.0 |
| Procedures        | 3         | None                                                   | Yes     | GeoJSON, SensorML 3.0 |
| Sampling Features | 3         | None                                                   | Yes     | GeoJSON               |
| Properties        | 3         | None                                                   | No      | GeoJSON               |

**Part 2 Resources (Dynamic Data):**

| Resource        | Endpoints | Sub-resources        | Timing          | Formats Supported       |
| --------------- | --------- | -------------------- | --------------- | ----------------------- |
| Datastreams     | 4         | observations, schema | No              | GeoJSON, SWE Common 3.0 |
| Observations    | 3         | None                 | Time filtering  | GeoJSON, custom         |
| Control Streams | 4         | commands, schema     | No              | GeoJSON, SWE Common 3.0 |
| Commands        | 5         | status, result       | Status tracking | GeoJSON, custom         |

### URL Pattern Analysis

**Top-level endpoints (9):**

```
/systems
/deployments
/procedures
/samplingFeatures
/properties
/datastreams
/observations
/controlstreams
/commands
```

**Sub-resource endpoints (10):**

```
/systems/{id}/subsystems
/systems/{id}/deployments
/systems/{id}/samplingFeatures
/systems/{id}/datastreams
/systems/{id}/controlstreams

/deployments/{id}/subdeployments
/deployments/{id}/systems

/datastreams/{id}/observations
/datastreams/{id}/schema

/controlstreams/{id}/commands
/controlstreams/{id}/schema
```

**Special endpoints (5):**

```
/commands/{id}/status
/commands/{id}/status/{statusId}
/commands/{id}/result
/commands/{id}/result/{resultId}

/systems/{id}/history (and similar for other resources)
```

**Total unique URL patterns:** ~60-70

---

## 3. Resource Type Patterns

### Common CRUD Pattern

**All 9 resources share similar CRUD operations:**

**Pattern:**

```
GET    /{resources}           - List
GET    /{resources}/{id}      - Read single
POST   /{resources}           - Create
PUT    /{resources}/{id}      - Update
DELETE /{resources}/{id}      - Delete
```

**8 of 9 resources** follow this pattern (observations are read-only via collection endpoint).

### History Pattern

**5 resources support history:**

- Systems
- Deployments
- Procedures
- Sampling Features
- Properties

**Pattern:**

```
GET /{resource}/{id}/history[?validTime=...]
```

**Implementation:** Single helper method, parameterized by resource type.

### Schema Pattern

**2 resources have schemas:**

- Datastreams (observations schema)
- Control Streams (commands schema)

**Pattern:**

```
GET /{resource}/{id}/schema[?f=swe|proto]
```

**Implementation:** Two similar methods in respective sections.

### Command Status Pattern

**Only Commands** have status tracking:

**Pattern:**

```
GET    /commands/{id}/status
GET    /commands/{id}/status/{statusId}
POST   /commands/{id}/status
DELETE /commands/{id}/status/{statusId}

GET    /commands/{id}/result
GET    /commands/{id}/result/{resultId}
```

**Implementation:** Unique to Commands, ~6 methods.

---

## 4. Part 1 vs Part 2 Architecture

### Conceptual Differences

**Part 1: Feature Resources**

- Static or slowly-changing metadata
- Describe systems and their context
- Spatial (GeoJSON) or descriptive (SensorML)
- Support full CRUD operations
- Have validity time periods (history)

**Part 2: Dynamic Data**

- Rapidly-changing time series data
- Observations and commands stream continuously
- Tied to specific systems/datastreams
- Often append-only (observations)
- Time-based filtering critical

### Should Parts Be Separate Modules?

**Option 1: Single CSAPIQueryBuilder**

```typescript
export default class CSAPIQueryBuilder {
  // Part 1 resources
  async getSystems(options?: QueryOptions): Promise<string>;
  async getSystem(id: string): Promise<string>;

  async getDeployments(options?: QueryOptions): Promise<string>;
  async getDeployment(id: string): Promise<string>;

  // ... (all 5 Part 1 resources)

  // Part 2 resources
  async getDatastreams(options?: QueryOptions): Promise<string>;
  async getDatastream(id: string): Promise<string>;

  async getObservations(options?: QueryOptions): Promise<string>;
  async getObservation(id: string): Promise<string>;

  // ... (all 4 Part 2 resources)
}
```

**Pros:**

- Matches upstream pattern (1 builder per API)
- Single entry point for users
- Shared cache and base URL
- Simpler endpoint integration

**Cons:**

- Large class (~70-80 methods)
- Mixes conceptually different concerns
- May be harder to navigate

**Option 2: Separate Builders**

```typescript
// Part 1
export class CSAPIFeatureBuilder {
  async getSystems(...): Promise<string>
  async getDeployments(...): Promise<string>
  // ...
}

// Part 2
export class CSAPIDynamicDataBuilder {
  async getDatastreams(...): Promise<string>
  async getObservations(...): Promise<string>
  // ...
}

// In endpoint.ts
endpoint.csapi(collectionId) // Returns both?
endpoint.csapiFeatures(collectionId)
endpoint.csapiDynamicData(collectionId)
```

**Pros:**

- Cleaner separation of concerns
- Smaller classes
- Users can import only what they need

**Cons:**

- **Breaks upstream pattern** (all other APIs have single builder)
- More complex endpoint integration
- Duplicate cache/base URL handling
- More exports in index.ts

### Recommendation: Single Builder

**Rationale:**

- Matches EDR pattern (single builder)
- CSAPI is logically one API (just has 2 parts)
- Class size manageable (~70-80 methods)
- Implementation grouped by resource type
- Users work with one object

**Implementation:**

```typescript
export default class CSAPIQueryBuilder {
  // ========================================
  // PART 1: FEATURE RESOURCES
  // ========================================

  // Systems (12 methods)
  async getSystems(options?: QueryOptions): Promise<string>;
  async getSystem(systemId: string): Promise<string>;
  async getSystemHistory(
    systemId: string,
    options?: HistoryOptions
  ): Promise<string>;
  async getSubsystems(
    systemId: string,
    options?: QueryOptions
  ): Promise<string>;
  async getSystemDeployments(
    systemId: string,
    options?: QueryOptions
  ): Promise<string>;
  async getSystemSamplingFeatures(
    systemId: string,
    options?: QueryOptions
  ): Promise<string>;
  // ... more system methods

  // Deployments (8 methods)
  async getDeployments(options?: QueryOptions): Promise<string>;
  // ...

  // Procedures, Sampling Features, Properties...

  // ========================================
  // PART 2: DYNAMIC DATA
  // ========================================

  // Datastreams (11 methods)
  async getDatastreams(options?: QueryOptions): Promise<string>;
  // ...

  // Observations, Control Streams, Commands...
}
```

**Clear organization via comments, single class.**

---

## 5. Sub-Resource Handling

### Sub-Resource Patterns

**Type 1: Parent owns children**

- `/systems/{id}/subsystems` - System contains subsystems
- `/deployments/{id}/subdeployments` - Deployment contains subdeployments

**Type 2: Relationships**

- `/systems/{id}/deployments` - Deployments of a system
- `/deployments/{id}/systems` - Systems in a deployment
- `/systems/{id}/samplingFeatures` - Sampling features for a system

**Type 3: Data channels**

- `/systems/{id}/datastreams` - Datastreams from a system
- `/systems/{id}/controlstreams` - Control streams for a system
- `/datastreams/{id}/observations` - Observations in a datastream
- `/controlstreams/{id}/commands` - Commands in a control stream

### URL Building Strategy

**Pattern: Parent ID as parameter**

```typescript
// Type 1: Subsystems
async getSubsystems(
  systemId: string,
  options?: QueryOptions
): Promise<string> {
  const baseUrl = await this.getSystem(systemId); // Get parent URL
  return `${baseUrl}/subsystems${this.buildQueryString(options)}`;
}

// Type 2: Relationships
async getSystemDeployments(
  systemId: string,
  options?: QueryOptions
): Promise<string> {
  const baseUrl = await this.getSystem(systemId);
  return `${baseUrl}/deployments${this.buildQueryString(options)}`;
}

// Type 3: Data channels
async getSystemDatastreams(
  systemId: string,
  options?: QueryOptions
): Promise<string> {
  const baseUrl = await this.getSystem(systemId);
  return `${baseUrl}/datastreams${this.buildQueryString(options)}`;
}
```

**Characteristics:**

- Parent ID required
- Append sub-resource path
- Same query options support
- Cache parent URLs

### Alternative: Link-Based Navigation

**EDR uses collection links:**

```typescript
// In EDR url_builder.ts
const positionUrl = getLinkUrl(
  this.collection_,
  'position',
  this.baseUrl,
  undefined,
  true
);
```

**CSAPI could use item links:**

```typescript
// Option: Navigate via links in system resource
const system = await fetch(await builder.getSystem('sys-123'));
const systemJson = await system.json();

const datastreamsUrl = getLinkUrl(
  systemJson,
  'datastreams',
  baseUrl,
  undefined,
  false
);
```

**Problem:** Requires fetching parent first, breaks "URL only" pattern.

### Recommendation: Path Concatenation

**Use path concatenation pattern:**

```typescript
async getSystemDatastreams(
  systemId: string,
  options?: QueryOptions
): Promise<string> {
  // Build parent URL
  const systemUrl = await this.getSystem(systemId);

  // Append sub-resource path
  return `${systemUrl}/datastreams${this.buildQueryString(options)}`;
}
```

**Rationale:**

- No fetch required
- Follows REST URL patterns
- Simple and predictable
- Matches CSAPI spec URL structure

**Total sub-resource methods:** ~10-12

---

## 6. Shared vs Unique Implementation

### Code Reuse Opportunities

**Shared patterns across resources:**

1. **List + Get pattern (9 resources):**

   ```typescript
   async get{Resources}(options?: QueryOptions): Promise<string>
   async get{Resource}(id: string): Promise<string>
   ```

2. **History pattern (5 resources):**

   ```typescript
   async get{Resource}History(
     id: string,
     options?: HistoryOptions
   ): Promise<string>
   ```

3. **Query string building (all methods):**
   ```typescript
   private buildQueryString(options?: QueryOptions): string
   ```

### Should There Be Base Classes?

**Option 1: Abstract base for resources**

```typescript
abstract class ResourceNavigator {
  abstract resourcePath: string;
  abstract hasHistory: boolean;

  async list(options?: QueryOptions): Promise<string> {
    const url = `${this.baseUrl}/${this.resourcePath}`;
    return `${url}${this.buildQueryString(options)}`;
  }

  async get(id: string): Promise<string> {
    return `${this.baseUrl}/${this.resourcePath}/${id}`;
  }

  async history(id: string, options?: HistoryOptions): Promise<string> {
    if (!this.hasHistory) throw new Error('Resource does not support history');
    return `${this.get(id)}/history${this.buildQueryString(options)}`;
  }
}

class SystemsNavigator extends ResourceNavigator {
  resourcePath = 'systems';
  hasHistory = true;

  // System-specific methods
  async getSubsystems(id: string, options?: QueryOptions): Promise<string> {
    return `${this.get(id)}/subsystems${this.buildQueryString(options)}`;
  }
}
```

**Pros:**

- Reduces code duplication
- Clear inheritance hierarchy
- Easy to add new resources

**Cons:**

- **Breaks upstream pattern** (no other API uses inheritance)
- More complex to understand
- Harder to navigate (methods split across classes)
- Doesn't align with EDR approach

**Option 2: Helper methods + explicit implementations**

```typescript
export default class CSAPIQueryBuilder {
  // Helper for building URLs
  private buildResourceUrl(
    resourceType: string,
    id?: string,
    subPath?: string,
    options?: QueryOptions
  ): string {
    let url = `${this.baseUrl}/${resourceType}`;
    if (id) url += `/${id}`;
    if (subPath) url += `/${subPath}`;
    return url + this.buildQueryString(options);
  }

  // Explicit method implementations
  async getSystems(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('systems', undefined, undefined, options);
  }

  async getSystem(systemId: string): Promise<string> {
    return this.buildResourceUrl('systems', systemId);
  }

  async getSystemHistory(
    systemId: string,
    options?: HistoryOptions
  ): Promise<string> {
    return this.buildResourceUrl('systems', systemId, 'history', options);
  }

  async getDeployments(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('deployments', undefined, undefined, options);
  }

  // ... explicit methods for all resources
}
```

**Pros:**

- Matches upstream pattern (EDR does similar)
- All methods visible in one class
- Helper reduces duplication
- Easy to understand and navigate

**Cons:**

- Some repetition in method signatures
- More lines of code

### Recommendation: Helper Methods

**Use private helpers, explicit public methods:**

```typescript
export default class CSAPIQueryBuilder {
  // ========================================
  // PRIVATE HELPERS
  // ========================================

  private buildResourceUrl(
    resourceType: string,
    id?: string,
    subPath?: string,
    options?: QueryOptions
  ): string {
    let url = `${this.baseUrl}/${resourceType}`;
    if (id) url += `/${id}`;
    if (subPath) url += `/${subPath}`;
    return url + this.buildQueryString(options);
  }

  private buildQueryString(options?: QueryOptions): string {
    if (!options) return '';
    const params = new URLSearchParams();
    if (options.limit) params.set('limit', options.limit.toString());
    if (options.offset) params.set('offset', options.offset.toString());
    if (options.bbox) params.set('bbox', options.bbox.join(','));
    if (options.datetime)
      params.set('datetime', formatDateTime(options.datetime));
    if (options.f) params.set('f', options.f);
    const query = params.toString();
    return query ? `?${query}` : '';
  }

  // ========================================
  // PUBLIC METHODS (9 RESOURCES)
  // ========================================

  // Systems (12 methods)
  async getSystems(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('systems', undefined, undefined, options);
  }

  async getSystem(systemId: string): Promise<string> {
    return this.buildResourceUrl('systems', systemId);
  }

  async getSystemHistory(
    systemId: string,
    options?: HistoryOptions
  ): Promise<string> {
    return this.buildResourceUrl('systems', systemId, 'history', options);
  }

  async getSubsystems(
    systemId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl('systems', systemId, 'subsystems', options);
  }

  // ... 8 more system methods

  // Deployments (8 methods)
  async getDeployments(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('deployments', undefined, undefined, options);
  }

  async getDeployment(deploymentId: string): Promise<string> {
    return this.buildResourceUrl('deployments', deploymentId);
  }

  // ... 6 more deployment methods

  // ... 7 more resources (Procedures, Sampling Features, Properties,
  //     Datastreams, Observations, Control Streams, Commands)
}
```

**Result:** ~70-80 public methods, ~2-3 private helpers, no inheritance.

---

## 7. Resource Discovery

### How to Know What Resources Are Available?

**Problem:** Not all CSAPI endpoints support all 9 resources.

**Example:**

- Endpoint A: Only systems, deployments, datastreams
- Endpoint B: All 9 resources
- Endpoint C: Only observations (data access only)

### Discovery Mechanisms

**Mechanism 1: Conformance classes**

```typescript
// In info.ts
export function checkHasConnectedSystemsCore([conformance]: [
  OgcApiConformance
]): boolean {
  return conformance.conformsTo.includes(
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
  );
}

export function checkHasConnectedSystemsDynamicData([conformance]: [
  OgcApiConformance
]): boolean {
  return conformance.conformsTo.includes(
    'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/dynamic-data'
  );
}
```

**Tells you Part 1 vs Part 2 support, not individual resources.**

**Mechanism 2: Collection links**

```typescript
// In CSAPIQueryBuilder constructor
private extractAvailableResources(): Set<string> {
  const resources = new Set<string>();
  const linkRels = this.collection_.links.map(l => l.rel);

  // Part 1 resources
  if (linkRels.includes('systems')) resources.add('systems');
  if (linkRels.includes('deployments')) resources.add('deployments');
  if (linkRels.includes('procedures')) resources.add('procedures');
  if (linkRels.includes('samplingFeatures')) resources.add('samplingFeatures');
  if (linkRels.includes('properties')) resources.add('properties');

  // Part 2 resources
  if (linkRels.includes('datastreams')) resources.add('datastreams');
  if (linkRels.includes('observations')) resources.add('observations');
  if (linkRels.includes('controlstreams')) resources.add('controlstreams');
  if (linkRels.includes('commands')) resources.add('commands');

  return resources;
}

// Expose as public property
public readonly availableResources: Set<string>;
```

**Tells you exactly which resources this collection supports.**

### Should Methods Check Availability?

**Option 1: Throw error if resource unavailable**

```typescript
async getSystems(options?: QueryOptions): Promise<string> {
  if (!this.availableResources.has('systems')) {
    throw new Error('Collection does not support systems resource');
  }
  return this.buildResourceUrl('systems', undefined, undefined, options);
}
```

**Pros:**

- Fail fast with clear message
- Prevents invalid URLs

**Cons:**

- Adds ~1 line per method (~70-80 lines total)
- Server will 404 anyway
- Breaks "minimal validation" pattern

**Option 2: Let server validate**

```typescript
async getSystems(options?: QueryOptions): Promise<string> {
  // No check - just build URL
  return this.buildResourceUrl('systems', undefined, undefined, options);
}

// User code:
if (builder.availableResources.has('systems')) {
  const url = await builder.getSystems();
  // ... fetch
}
```

**Pros:**

- Minimal validation (matches error handling strategy)
- Trusts server to 404
- Less code

**Cons:**

- User must check manually
- May generate invalid URLs

### Recommendation: Expose Availability, Don't Validate

**Pattern:**

```typescript
export default class CSAPIQueryBuilder {
  // Public property for users to check
  public readonly availableResources: Set<string>;

  constructor(private collection_: OgcApiCollectionInfo) {
    this.availableResources = this.extractAvailableResources();
  }

  // No validation in methods
  async getSystems(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('systems', undefined, undefined, options);
  }

  // ... other methods
}

// User code:
const builder = await endpoint.csapi('collection-123');

// User checks before calling
if (builder.availableResources.has('systems')) {
  const url = await builder.getSystems();
  const response = await fetch(url);
  if (response.ok) {
    const systems = await response.json();
  }
}
```

**Rationale:**

- Follows "minimal validation" principle (Section 9)
- User has visibility into capabilities
- Server validates via HTTP 404
- Less code (~0 lines vs ~70-80 lines)

---

## 8. Format Handling: GeoJSON, SensorML 3.0, and SWE Common 3.0

**FIRM DESIGN DECISION (2026-02-04):** This project WILL implement full format handling for GeoJSON, SensorML 3.0, and SWE Common 3.0. This is a MANDATED requirement and is IN-SCOPE for the project.

### Format Requirements

**Formats to Support:**

**1. GeoJSON (RFC 7946) - ALL Resources**

- Standard GeoJSON features
- Geometry + properties
- Built-in TypeScript support
- Native JSON parsing
- **Status: ✅ SUPPORTED** - No additional parsing needed

**2. SensorML 3.0 - Systems, Deployments, Procedures**

- XML-based system descriptions
- SimpleProcess, AggregateProcess, PhysicalSystem
- Complex nested structures
- **Status: ✅ REQUIRED** - Full parsing implementation needed
- **Version: 3.0 ONLY** (not 2.0/2.1)

**3. SWE Common 3.0 - Datastreams, Control Streams**

- Data component definitions
- DataArray, DataRecord, Quantity, Time, etc.
- JSON and XML encodings
- **Status: ✅ REQUIRED** - Full parsing implementation needed
- **Version: 3.0 ONLY** (not 2.0)

### Why Full Format Handling?

**Original Decision (2026-01-30):** Follow upstream pattern - no format parsing, URL building only.

**New Decision (2026-02-04):** Full format handling is REQUIRED because:

1. **CSAPI-Specific Complexity:** SensorML and SWE Common are fundamental to CSAPI, unlike CoverageJSON in EDR which is optional
2. **User Experience:** Parsing these formats manually creates significant friction
3. **Type Safety:** TypeScript interfaces for SensorML/SWE provide strong typing
4. **Ecosystem Gap:** No mature TypeScript libraries exist for SensorML 3.0 / SWE Common 3.0
5. **Value Proposition:** Full format support differentiates this client library

**This decision OVERRIDES the original "no parsing" recommendation from Section 8.**

### Implementation Requirements

#### File Structure

```
src/ogc-api/csapi/
├── url_builder.ts              # CSAPIQueryBuilder class
├── formats/
│   ├── index.ts                # Format exports
│   ├── geojson.ts              # GeoJSON types (re-export standard types)
│   ├── sensorml/
│   │   ├── index.ts            # SensorML 3.0 parser entry point
│   │   ├── parser.ts           # XML parsing logic
│   │   ├── types.ts            # TypeScript interfaces
│   │   ├── simple-process.ts   # SimpleProcess handling
│   │   ├── aggregate-process.ts# AggregateProcess handling
│   │   └── physical-system.ts  # PhysicalSystem handling
│   ├── swecommon/
│   │   ├── index.ts            # SWE Common 3.0 parser entry point
│   │   ├── parser.ts           # JSON/XML parsing logic
│   │   ├── types.ts            # TypeScript interfaces
│   │   ├── data-record.ts      # DataRecord handling
│   │   ├── data-array.ts       # DataArray handling
│   │   └── components.ts       # Component types (Quantity, Time, etc.)
│   └── constants.ts            # Format MIME types and identifiers
├── model.ts                    # CSAPI-specific types
└── helpers.ts                  # URL/param helpers
```

#### Format Parser APIs

**SensorML 3.0 Parser:**

```typescript
// In src/ogc-api/csapi/formats/sensorml/index.ts

export interface SensorML30Document {
  version: '3.0';
  type: 'SimpleProcess' | 'AggregateProcess' | 'PhysicalSystem';
  id: string;
  name?: string;
  description?: string;
  keywords?: string[];
  identification?: Identification[];
  classification?: Classification[];
  validTime?: TimePeriod;
  capabilities?: Capabilities[];
  contacts?: Contact[];
  documentation?: Documentation[];
  history?: Event[];
  components?: Component[]; // For AggregateProcess
  connections?: Connection[]; // For AggregateProcess
  attachedTo?: string; // For PhysicalSystem
  localReferenceFrame?: ReferenceFrame;
  position?: Position;
  // ... more fields
}

export function parseSensorML30(xml: string): SensorML30Document {
  // XML parsing implementation
}

export function serializeSensorML30(doc: SensorML30Document): string {
  // XML serialization implementation
}
```

**SWE Common 3.0 Parser:**

```typescript
// In src/ogc-api/csapi/formats/swecommon/index.ts

export interface SWECommon30DataRecord {
  type: 'DataRecord';
  label?: string;
  description?: string;
  fields: SWECommonField[];
}

export interface SWECommon30DataArray {
  type: 'DataArray';
  label?: string;
  description?: string;
  elementCount: Count;
  elementType: SWECommonDataComponent;
  encoding: Encoding;
  values?: any[]; // Depends on encoding
}

export type SWECommonDataComponent =
  | SWECommon30DataRecord
  | SWECommon30DataArray
  | Quantity
  | Count
  | Boolean
  | Category
  | Text
  | Time
  | TimeRange
  | QuantityRange;

export function parseSWECommon30(
  input: string | object
): SWECommonDataComponent {
  // JSON or XML parsing implementation
}

export function serializeSWECommon30(
  component: SWECommonDataComponent,
  format: 'json' | 'xml'
): string {
  // Serialization implementation
}
```

**Format Constants:**

```typescript
// In src/ogc-api/csapi/formats/constants.ts

export const CSAPI_FORMATS = {
  GEOJSON: 'application/geo+json',
  SENSORML_30: 'application/sml+xml; version=3.0',
  SWE_COMMON_30_JSON: 'application/swe+json; version=3.0',
  SWE_COMMON_30_XML: 'application/swe+xml; version=3.0',
} as const;

export type CSAPIFormat = (typeof CSAPI_FORMATS)[keyof typeof CSAPI_FORMATS];

export const FORMAT_SHORTCUTS = {
  json: CSAPI_FORMATS.GEOJSON,
  sml: CSAPI_FORMATS.SENSORML_30,
  'swe-json': CSAPI_FORMATS.SWE_COMMON_30_JSON,
  'swe-xml': CSAPI_FORMATS.SWE_COMMON_30_XML,
} as const;
```

### Code Volume Estimation

**Format parsing implementation:**

| Component                 | Lines           | Description                                   |
| ------------------------- | --------------- | --------------------------------------------- |
| **SensorML 3.0 Parser**   |                 |                                               |
| types.ts                  | 400-600         | TypeScript interfaces for all SensorML types  |
| parser.ts                 | 600-800         | XML parsing logic (DOM traversal, validation) |
| simple-process.ts         | 150-200         | SimpleProcess-specific handling               |
| aggregate-process.ts      | 200-250         | AggregateProcess-specific handling            |
| physical-system.ts        | 200-250         | PhysicalSystem-specific handling              |
| index.ts                  | 50-100          | Exports and convenience functions             |
| **SensorML Subtotal**     | **1,600-2,200** | **Complete SensorML 3.0 support**             |
|                           |                 |                                               |
| **SWE Common 3.0 Parser** |                 |                                               |
| types.ts                  | 400-600         | TypeScript interfaces for all SWE types       |
| parser.ts                 | 500-700         | JSON/XML parsing logic                        |
| data-record.ts            | 150-200         | DataRecord handling                           |
| data-array.ts             | 200-250         | DataArray handling                            |
| components.ts             | 300-400         | All component types (Quantity, Time, etc.)    |
| index.ts                  | 50-100          | Exports and convenience functions             |
| **SWE Common Subtotal**   | **1,600-2,250** | **Complete SWE Common 3.0 support**           |
|                           |                 |                                               |
| **Supporting Code**       |                 |                                               |
| geojson.ts                | 50-100          | GeoJSON type re-exports                       |
| constants.ts              | 50-100          | Format constants and MIME types               |
| **Supporting Subtotal**   | **100-200**     | **Format infrastructure**                     |
|                           |                 |                                               |
| **TOTAL FORMAT CODE**     | **3,300-4,650** | **Full format handling**                      |

**Tests for format parsing:**

| Component              | Lines           | Description                             |
| ---------------------- | --------------- | --------------------------------------- |
| SensorML 3.0 tests     | 1,500-2,000     | Parser tests, type validation, examples |
| SWE Common 3.0 tests   | 1,500-2,000     | Parser tests, type validation, examples |
| Integration tests      | 500-700         | Format integration with QueryBuilder    |
| **TOTAL FORMAT TESTS** | **3,500-4,700** | **Comprehensive test coverage**         |

**Total format handling code volume: ~6,800-9,350 lines (implementation + tests)**

### Integration with CSAPIQueryBuilder

**QueryBuilder remains focused on URL building:**

```typescript
// URL building methods (unchanged)
async getSystem(
  systemId: string,
  options?: { f?: 'json' | 'sml' }
): Promise<string> {
  const url = this.buildResourceUrl('systems', systemId);
  if (options?.f) {
    return `${url}?f=${options.f}`;
  }
  return url;
}

// NO parsing in QueryBuilder - users call parsers separately
```

**Users access format parsers separately:**

```typescript
import { CSAPIQueryBuilder } from 'ogc-client';
import { parseSensorML30, parseSWECommon30 } from 'ogc-client/csapi/formats';

const builder = await endpoint.csapi('collection-123');

// Get system as SensorML
const smlUrl = await builder.getSystem('sys-123', { f: 'sml' });
const response = await fetch(smlUrl);
const smlXml = await response.text();
const system = parseSensorML30(smlXml);

// Get datastream schema as SWE Common
const schemaUrl = await builder.getDatastreamSchema('ds-456', {
  f: 'swe-json',
});
const schemaResponse = await fetch(schemaUrl);
const schemaJson = await schemaResponse.json();
const schema = parseSWECommon30(schemaJson);
```

**Separation of concerns:**

- ✅ CSAPIQueryBuilder = URL building
- ✅ Format parsers = Data parsing
- ✅ Users choose when to parse
- ✅ No forced coupling

### Updated Implementation Checklist

✅ **Architecture:**

- [x] Single CSAPIQueryBuilder class (~500-700 lines)
- [x] 2-3 private helper methods
- [x] 70-80 public URL-building methods
- [x] Resource discovery via links
- [x] No validation in methods

✅ **Integration:**

- [x] endpoint.hasConnectedSystems getter
- [x] endpoint.csapi(collectionId) factory
- [x] Collection caching
- [x] Conformance checking in info.ts

✅ **Formats (NEW REQUIREMENTS):**

- [x] **GeoJSON support** (standard JSON parsing)
- [x] **SensorML 3.0 parser** (~1,600-2,200 lines)
- [x] **SWE Common 3.0 parser** (~1,600-2,250 lines)
- [x] Format constants export (~50-100 lines)
- [x] Format parsers as separate imports
- [x] NO support for SensorML 2.0/2.1 or SWE Common 2.0

✅ **Code volume:**

- [x] QueryBuilder: ~560-760 lines
- [x] **Format parsing: ~3,300-4,650 lines (NEW)**
- [x] **Format tests: ~3,500-4,700 lines (NEW)**
- [x] **Total: ~7,360-10,110 lines**

### Rationale for Format Handling Decision

**Why this differs from upstream pattern:**

1. **CSAPI Uniqueness:** Unlike EDR's CoverageJSON (user can choose JSON or NetCDF), SensorML/SWE are CORE to CSAPI
2. **Complexity Barrier:** Manual parsing of SensorML 3.0 XML or SWE Common JSON is significant friction
3. **Type Safety Value:** Strong TypeScript types for complex formats provide immediate developer value
4. **Ecosystem Gap:** No mature TypeScript libraries for SensorML 3.0 / SWE Common 3.0
5. **Differentiation:** Full format support makes this a complete CSAPI client, not just URL builder
6. **Maintainability:** Single source of truth for format handling across all CSAPI users

**Trade-offs accepted:**

| Trade-off            | Impact                  | Mitigation                                    |
| -------------------- | ----------------------- | --------------------------------------------- |
| Code volume increase | +6,800-9,350 lines      | Organized in separate formats/ subfolder      |
| Maintenance burden   | Format spec changes     | Version-specific (3.0 only), clear separation |
| Bundle size          | +~100-150 KB            | Tree-shakeable, can import parsers separately |
| Testing complexity   | +3,500-4,700 test lines | Comprehensive examples from specs             |

**Decision confidence: HIGH**

This is a **strategic decision** to make ogc-client-CSAPI a **complete CSAPI client library** rather than just a URL builder. The value proposition justifies the code volume increase.

---

## 9. Implementation Strategy

### File Organization

**Updated file structure with format support:**

```
src/ogc-api/csapi/
├── url_builder.ts              (~500-700 lines)
├── model.ts                    (~200-300 lines)
├── helpers.ts                  (~50-100 lines)
├── index.ts                    (~10-20 lines)
├── formats/
│   ├── index.ts                (~50-100 lines)
│   ├── geojson.ts              (~50-100 lines)
│   ├── constants.ts            (~50-100 lines)
│   ├── sensorml/
│   │   ├── index.ts            (~50-100 lines)
│   │   ├── types.ts            (~400-600 lines)
│   │   ├── parser.ts           (~600-800 lines)
│   │   ├── simple-process.ts   (~150-200 lines)
│   │   ├── aggregate-process.ts(~200-250 lines)
│   │   └── physical-system.ts  (~200-250 lines)
│   └── swecommon/
│       ├── index.ts            (~50-100 lines)
│       ├── types.ts            (~400-600 lines)
│       ├── parser.ts           (~500-700 lines)
│       ├── data-record.ts      (~150-200 lines)
│       ├── data-array.ts       (~200-250 lines)
│       └── components.ts       (~300-400 lines)
```

**Total:** ~4,110-5,520 lines for CSAPI implementation (including formats).

### Method Count

**Detailed count by resource:**

| Resource          | Methods | Notes                                                                                              |
| ----------------- | ------- | -------------------------------------------------------------------------------------------------- |
| Systems           | 12      | List, Get, History, Subsystems, Deployments, SamplingFeatures, Datastreams, ControlStreams, + CRUD |
| Deployments       | 8       | List, Get, History, Subdeployments, Systems, + CRUD                                                |
| Procedures        | 8       | List, Get, History, + CRUD                                                                         |
| Sampling Features | 8       | List, Get, History, + CRUD                                                                         |
| Properties        | 6       | List, Get, + CRUD (no history)                                                                     |
| Datastreams       | 11      | List, Get, Observations, Schema, + CRUD, + system-scoped                                           |
| Observations      | 9       | List, Get, + Create, + datastream-scoped, time filtering                                           |
| Control Streams   | 8       | List, Get, Commands, Schema, + CRUD, + system-scoped                                               |
| Commands          | 10      | List, Get, Status, Result, + CRUD, + control-stream-scoped                                         |

**Total:** ~70-80 public methods in QueryBuilder.

**Plus:**

- 2-3 private helpers (buildResourceUrl, buildQueryString)
- 1 constructor
- 1 resource discovery method
- ~10 properties (baseUrl, collection, availableResources, etc.)

**QueryBuilder class size:** ~500-700 lines.

**Format parsing:** ~3,300-4,650 lines (separate from QueryBuilder).

### Code Volume Comparison

**EDR (PR #114) QueryBuilder:**

- ~400 lines
- 1 resource type (coverage data)
- 6 query types (position, radius, area, cube, trajectory, corridor)
- ~15-20 public methods
- **No format parsing**

**CSAPI QueryBuilder (projected):**

- ~500-700 lines
- 9 resource types
- ~70-80 public methods
- Similar complexity per method
- **PLUS ~3,300-4,650 lines for format parsing**

**Ratio:** ~1.5-1.75x EDR size for QueryBuilder, but 4.5x more resource types.

**Per-resource average:** ~60-80 lines per resource type (EDR: ~400 lines for 1 resource type).

**Conclusion:** CSAPI QueryBuilder is actually **more efficient** per resource than EDR, and format parsing is cleanly separated.

### TypeScript Interfaces

**Query options interfaces:**

```typescript
// Shared options
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: [number, number, number, number];
  datetime?: string | [string, string];
  f?: string;
}

// History options
export interface HistoryOptions {
  validTime?: string | [string, string];
  limit?: number;
  offset?: number;
}

// System query options
export interface SystemQueryOptions extends QueryOptions {
  // Future: add system-specific filters
}

// Similar for other resources...
```

**Total:** ~50-100 lines for all interfaces.

**Format type interfaces:** ~800-1,200 lines (in formats/ subfolder).

---

## 10. Complete Architecture Design

### Final Architecture

**Structure:**

```
src/ogc-api/csapi/
├── url_builder.ts               (~500-700 lines)
├── model.ts                     (~200-300 lines)
├── helpers.ts                   (~50-100 lines)
├── index.ts                     (~10-20 lines)
├── formats/                     (~3,300-4,650 lines total)
│   ├── index.ts
│   ├── geojson.ts
│   ├── constants.ts
│   ├── sensorml/                (~1,600-2,200 lines)
│   └── swecommon/               (~1,600-2,250 lines)
```

**Integration:**

```typescript
// In src/ogc-api/endpoint.ts (~30 lines added)
import CSAPIQueryBuilder from './csapi/url_builder.js';

export default class OgcApiEndpoint {
  private collection_id_to_csapi_builder_ = new Map<
    string,
    CSAPIQueryBuilder
  >();

  get hasConnectedSystems(): Promise<boolean> {
    return this.featureCheckFactory_(checkHasConnectedSystems);
  }

  async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
    if (!(await this.hasConnectedSystems)) {
      throw new EndpointError(
        'Endpoint does not support Connected Systems API'
      );
    }
    const cache = this.collection_id_to_csapi_builder_;
    if (cache.has(collection_id)) {
      return cache.get(collection_id)!;
    }
    const collection = await this.getCollectionInfo(collection_id);
    const builder = new CSAPIQueryBuilder(collection);
    cache.set(collection_id, builder);
    return builder;
  }
}
```

**CSAPIQueryBuilder class (unchanged from original):**

```typescript
export default class CSAPIQueryBuilder {
  private collection_: OgcApiCollectionInfo;
  private baseUrl: string;
  public readonly availableResources: Set<string>;

  constructor(collection: OgcApiCollectionInfo) {
    this.collection_ = collection;
    this.baseUrl = getLinkUrl(collection, 'self' /* ... */);
    this.availableResources = this.extractAvailableResources();
  }

  // ... (same as Section 10 in original document)
}
```

**Format parser usage:**

```typescript
// User code with format parsing
import { CSAPIQueryBuilder } from 'ogc-client';
import {
  parseSensorML30,
  parseSWECommon30,
  CSAPI_FORMATS,
} from 'ogc-client/csapi/formats';

const endpoint = await OgcApiEndpoint.fromUrl('https://api.example.com');
const builder = await endpoint.csapi('sensors');

// Get system as SensorML 3.0
const smlUrl = await builder.getSystem('temp-sensor-01', { f: 'sml' });
const response = await fetch(smlUrl);
const smlXml = await response.text();
const system = parseSensorML30(smlXml);

console.log(system.type); // 'PhysicalSystem'
console.log(system.name); // 'Temperature Sensor 01'
console.log(system.capabilities); // Array of capabilities

// Get datastream schema as SWE Common 3.0
const schemaUrl = await builder.getDatastreamSchema('temp-stream', {
  f: 'swe-json',
});
const schemaResponse = await fetch(schemaUrl);
const schemaJson = await schemaResponse.json();
const schema = parseSWECommon30(schemaJson);

console.log(schema.type); // 'DataRecord'
console.log(schema.fields); // Array of field definitions
```

### Updated Code Volume Summary

**CSAPI implementation:**

| Component                | Lines           | Description                           |
| ------------------------ | --------------- | ------------------------------------- |
| **Core QueryBuilder**    |                 |                                       |
| url_builder.ts           | 500-700         | QueryBuilder class with 70-80 methods |
| model.ts                 | 200-300         | CSAPI-specific types                  |
| helpers.ts               | 50-100          | URL/param helpers                     |
| index.ts                 | 10-20           | Exports                               |
| **Core Subtotal**        | **760-1,120**   | **URL building functionality**        |
|                          |                 |                                       |
| **Format Parsing**       |                 |                                       |
| formats/geojson.ts       | 50-100          | GeoJSON type re-exports               |
| formats/constants.ts     | 50-100          | Format constants                      |
| formats/sensorml/        | 1,600-2,200     | Complete SensorML 3.0 support         |
| formats/swecommon/       | 1,600-2,250     | Complete SWE Common 3.0 support       |
| **Format Subtotal**      | **3,300-4,650** | **Full format parsing**               |
|                          |                 |                                       |
| **Integration**          |                 |                                       |
| endpoint.ts additions    | 30              | hasConnectedSystems + csapi() method  |
| info.ts additions        | 15              | Conformance checking                  |
| **Integration Subtotal** | **45**          | **Core integration**                  |
|                          |                 |                                       |
| **TOTAL IMPLEMENTATION** | **4,105-5,815** | **Complete CSAPI support**            |

**Per-resource efficiency (QueryBuilder only):**

- 9 resources = 760-1,120 lines total
- Average: ~84-124 lines per resource type
- EDR: ~400 lines for 1 resource type
- **QueryBuilder is 3-5x more efficient per resource**

**Format parsing (separate concern):**

- SensorML 3.0: ~1,600-2,200 lines
- SWE Common 3.0: ~1,600-2,250 lines
- Supporting code: ~100-200 lines
- **Format parsing is optional for users** (can import separately)

**Comparison to upstream:**

- ogc-client core (excluding tests): ~3000-4000 lines
- CSAPI addition: ~4,105-5,815 lines (~100-145% increase)
- **Significant but justified** for complete CSAPI support with formats

---

## Summary

### Key Architectural Decisions

1. **Single QueryBuilder** - CSAPIQueryBuilder contains all 70-80 methods
2. **No separate Part 1/Part 2** - Logical sections via comments
3. **Helper methods, not inheritance** - buildResourceUrl + buildQueryString
4. **Path concatenation for sub-resources** - No link navigation
5. **Resource discovery exposed, not validated** - availableResources property
6. **FULL FORMAT HANDLING** - GeoJSON, SensorML 3.0, SWE Common 3.0 parsers (**NEW**)
7. **Follow EDR pattern for QueryBuilder** - Same structure, same approach
8. **Format parsers as separate imports** - Clean separation of concerns

### Implementation Checklist

✅ **Architecture:**

- [x] Single CSAPIQueryBuilder class (~500-700 lines)
- [x] 2-3 private helper methods
- [x] 70-80 public URL-building methods
- [x] Resource discovery via links
- [x] No validation in methods

✅ **Integration:**

- [x] endpoint.hasConnectedSystems getter
- [x] endpoint.csapi(collectionId) factory
- [x] Collection caching
- [x] Conformance checking in info.ts

✅ **Formats (REQUIRED):**

- [x] **GeoJSON support** (standard JSON parsing)
- [x] **SensorML 3.0 parser** (~1,600-2,200 lines)
- [x] **SWE Common 3.0 parser** (~1,600-2,250 lines)
- [x] **Format constants** (~50-100 lines)
- [x] **Format parsers as separate imports**
- [x] **Version-specific: 3.0 ONLY**

✅ **Code volume:**

- [x] QueryBuilder: ~760-1,120 lines
- [x] Format parsing: ~3,300-4,650 lines
- [x] Integration: ~45 lines
- [x] **Total: ~4,105-5,815 lines**
- [x] Tests: ~3,500-4,700 lines (formats) + ~2,000 lines (QueryBuilder)
- [x] **Grand Total: ~9,605-12,515 lines**

### Result

**Complete CSAPI client library** following upstream patterns where applicable, with strategic decision to include full format handling. 9 resources handled with **same approach** as EDR's 1 resource (QueryBuilder), PLUS comprehensive format parsing for SensorML 3.0 and SWE Common 3.0. Clean separation of concerns: URL building in QueryBuilder, format parsing in separate modules.

**This represents a COMPLETE implementation** that provides:

- ✅ URL building for all 9 CSAPI resources
- ✅ Full GeoJSON, SensorML 3.0, and SWE Common 3.0 support
- ✅ Strong TypeScript typing throughout
- ✅ Tree-shakeable format parsers
- ✅ Professional-grade CSAPI client library
