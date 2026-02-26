# CSAPI-Specific Architectural Decisions

**Purpose:** Document architectural choices for cleanly implementing 9 CSAPI resource types within ogc-client patterns.

**Context:** CSAPI has more resource types (9) than any other OGC API in ogc-client (WFS: 1, STAC: 2, EDR: 1). Must design architecture that handles this complexity without bloat.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [CSAPI Resource Landscape](#2-csapi-resource-landscape)
3. [Resource Type Patterns](#3-resource-type-patterns)
4. [Part 1 vs Part 2 Architecture](#4-part-1-vs-part-2-architecture)
5. [Sub-Resource Handling](#5-sub-resource-handling)
6. [Shared vs Unique Implementation](#6-shared-vs-unique-implementation)
7. [Resource Discovery](#7-resource-discovery)
8. [SWE Common and SensorML](#8-swe-common-and-sensorml)
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

---

## 2. CSAPI Resource Landscape

### Resource Inventory

**Part 1 Resources (Feature-based):**

| Resource          | Endpoints | Sub-resources                                          | History | Format            |
| ----------------- | --------- | ------------------------------------------------------ | ------- | ----------------- |
| Systems           | 5         | subsystems, deployments, samplingFeatures, datastreams | Yes     | GeoJSON, SensorML |
| Deployments       | 4         | subdeployments, systems                                | Yes     | GeoJSON, SensorML |
| Procedures        | 3         | None                                                   | Yes     | GeoJSON, SensorML |
| Sampling Features | 3         | None                                                   | Yes     | GeoJSON           |
| Properties        | 3         | None                                                   | No      | GeoJSON           |

**Part 2 Resources (Dynamic Data):**

| Resource        | Endpoints | Sub-resources        | Timing          | Format              |
| --------------- | --------- | -------------------- | --------------- | ------------------- |
| Datastreams     | 4         | observations, schema | No              | GeoJSON, SWE Common |
| Observations    | 3         | None                 | Time filtering  | GeoJSON, custom     |
| Control Streams | 4         | commands, schema     | No              | GeoJSON, SWE Common |
| Commands        | 5         | status, result       | Status tracking | GeoJSON, custom     |

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

## 8. SWE Common and SensorML

### Format Complexity

**CSAPI supports multiple formats:**

**GeoJSON (Simple):**

- Standard GeoJSON features
- Geometry + properties
- All resources support

**SensorML 3.0 (Complex):**

- XML-based system descriptions
- SimpleProcess, AggregateProcess, PhysicalSystem
- Only systems, deployments, procedures

**SWE Common 3.0 (Very Complex):**

- Data component definitions
- DataArray, DataRecord, Quantity, Time, etc.
- Datastreams and control streams

### Should Library Parse These Formats?

**Parsing means:**

- SensorML XML parser (~500-1000 lines)
- SWE Common JSON/XML parser (~500-1000 lines)
- TypeScript interfaces for all structures (~300-500 lines)
- Tests for parsing (~500-1000 lines)

**Total:** ~2000-4000 lines for format parsing.

### Upstream Pattern: No Parsing

**WFS approach:**

```typescript
// ogc-client returns URL, user fetches
const url = endpoint.getFeatures({ outputFormat: 'application/json' });
const response = await fetch(url);
const geojson = await response.json(); // User parses
```

**EDR approach:**

```typescript
// EDR returns URL, user fetches
const url = builder.buildPositionDownloadUrl(coords, { f: 'CoverageJSON' });
const response = await fetch(url);
const coverage = await response.json(); // User parses
```

**STAC approach:**

```typescript
// STAC returns URL, user fetches
const url = stac.items({ limit: 10 });
const response = await fetch(url);
const itemCollection = await response.json(); // User parses
```

**Pattern:** Library builds URLs with format parameters, user handles parsing.

### CSAPI Format Handling

**Follow upstream pattern:**

```typescript
// URL building with format parameter
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

// User code:
const smlUrl = await builder.getSystem('sys-123', { f: 'sml' });
const response = await fetch(smlUrl);
const sensorML = await response.text(); // User handles XML parsing

// Or with a SensorML library:
import { parseSensorML } from 'sensorml-parser'; // Not in ogc-client
const sml = parseSensorML(await response.text());
```

**For datastream schemas:**

```typescript
async getDatastreamSchema(
  datastreamId: string,
  options?: { f?: 'swe' | 'proto' }
): Promise<string> {
  const url = this.buildResourceUrl('datastreams', datastreamId, 'schema');
  if (options?.f) {
    return `${url}?f=${options.f}`;
  }
  return url;
}

// User code:
const schemaUrl = await builder.getDatastreamSchema('ds-456', { f: 'swe' });
const response = await fetch(schemaUrl);
const sweSchema = await response.json(); // User handles SWE Common parsing
```

### Optional: Format Constants

**Provide convenience exports (like Section 8):**

```typescript
// In src/ogc-api/csapi/formats.ts
export const CSAPI_FORMATS = {
  GEOJSON: 'json',
  SENSORML: 'sml',
  SWE_COMMON: 'swe',
  PROTOBUF: 'proto',
} as const;

export type CSAPIFormat = (typeof CSAPI_FORMATS)[keyof typeof CSAPI_FORMATS];
```

**Total:** ~10 lines, optional export.

### Recommendation: No Format Parsing

**CSAPI format handling:**

- ✅ Accept format parameter in URL methods
- ✅ Optional format constants export
- ❌ No SensorML parsing
- ❌ No SWE Common parsing
- ❌ No format validation

**Rationale:**

- Follows upstream pattern
- Avoids 2000-4000 lines of format code
- Users can choose their own parsing libraries
- Keeps ogc-client focused on URL building

**Code volume:** ~10 lines (constants only).

---

## 9. Implementation Strategy

### File Organization

**Single file approach (like EDR):**

```
src/ogc-api/csapi/
  url_builder.ts           (~500-700 lines for 70-80 methods)
  formats.ts               (~10 lines for format constants)
  index.ts                 (~3 lines for exports)
```

**Total:** ~500-720 lines for CSAPI URL building.

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

**Total:** ~70-80 public methods.

**Plus:**

- 2-3 private helpers (buildResourceUrl, buildQueryString)
- 1 constructor
- 1 resource discovery method
- ~10 properties (baseUrl, collection, availableResources, etc.)

**Total class size:** ~500-700 lines.

### Code Volume Comparison

**EDR (PR #114) QueryBuilder:**

- ~400 lines
- 1 resource type (coverage data)
- 6 query types (position, radius, area, cube, trajectory, corridor)
- ~15-20 public methods

**CSAPI QueryBuilder (projected):**

- ~500-700 lines
- 9 resource types
- ~70-80 public methods
- Similar complexity per method

**Ratio:** ~1.5-1.75x EDR size, but 4.5x more resource types.

**Per-resource average:** ~60-80 lines per resource type (EDR: ~400 lines for 1 resource type).

**Conclusion:** CSAPI is actually **more efficient** per resource than EDR.

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

---

## 10. Complete Architecture Design

### Final Architecture

**Structure:**

```
src/ogc-api/csapi/
  url_builder.ts               (~500-700 lines)
  formats.ts                   (~10 lines)
  index.ts                     (~3 lines)
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

**CSAPIQueryBuilder class:**

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

  // ========================================
  // PRIVATE HELPERS
  // ========================================

  private extractAvailableResources(): Set<string> {
    const resources = new Set<string>();
    const linkRels = this.collection_.links.map((l) => l.rel);

    if (linkRels.includes('systems')) resources.add('systems');
    if (linkRels.includes('deployments')) resources.add('deployments');
    if (linkRels.includes('procedures')) resources.add('procedures');
    if (linkRels.includes('samplingFeatures'))
      resources.add('samplingFeatures');
    if (linkRels.includes('properties')) resources.add('properties');
    if (linkRels.includes('datastreams')) resources.add('datastreams');
    if (linkRels.includes('observations')) resources.add('observations');
    if (linkRels.includes('controlstreams')) resources.add('controlstreams');
    if (linkRels.includes('commands')) resources.add('commands');

    return resources;
  }

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
    if (options.limit !== undefined)
      params.set('limit', options.limit.toString());
    if (options.offset !== undefined)
      params.set('offset', options.offset.toString());
    if (options.bbox) params.set('bbox', options.bbox.join(','));
    if (options.datetime)
      params.set('datetime', formatDateTime(options.datetime));
    if (options.f) params.set('f', options.f);
    const query = params.toString();
    return query ? `?${query}` : '';
  }

  // ========================================
  // PART 1: FEATURE RESOURCES
  // ========================================

  // --- Systems (12 methods) ---

  async getSystems(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('systems', undefined, undefined, options);
  }

  async getSystem(systemId: string, options?: { f?: string }): Promise<string> {
    return this.buildResourceUrl('systems', systemId, undefined, options);
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

  async getSystemDeployments(
    systemId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl('systems', systemId, 'deployments', options);
  }

  async getSystemSamplingFeatures(
    systemId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'systems',
      systemId,
      'samplingFeatures',
      options
    );
  }

  async getSystemDatastreams(
    systemId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl('systems', systemId, 'datastreams', options);
  }

  async getSystemControlStreams(
    systemId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'systems',
      systemId,
      'controlstreams',
      options
    );
  }

  // + 4 CRUD methods (create, update, delete, patch)

  // --- Deployments (8 methods) ---

  async getDeployments(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('deployments', undefined, undefined, options);
  }

  async getDeployment(
    deploymentId: string,
    options?: { f?: string }
  ): Promise<string> {
    return this.buildResourceUrl(
      'deployments',
      deploymentId,
      undefined,
      options
    );
  }

  async getDeploymentHistory(
    deploymentId: string,
    options?: HistoryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'deployments',
      deploymentId,
      'history',
      options
    );
  }

  async getSubdeployments(
    deploymentId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'deployments',
      deploymentId,
      'subdeployments',
      options
    );
  }

  async getDeploymentSystems(
    deploymentId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'deployments',
      deploymentId,
      'systems',
      options
    );
  }

  // + 3 CRUD methods

  // --- Procedures (8 methods) ---

  async getProcedures(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('procedures', undefined, undefined, options);
  }

  async getProcedure(
    procedureId: string,
    options?: { f?: string }
  ): Promise<string> {
    return this.buildResourceUrl('procedures', procedureId, undefined, options);
  }

  async getProcedureHistory(
    procedureId: string,
    options?: HistoryOptions
  ): Promise<string> {
    return this.buildResourceUrl('procedures', procedureId, 'history', options);
  }

  // + 5 CRUD methods

  // --- Sampling Features (8 methods) ---

  async getSamplingFeatures(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl(
      'samplingFeatures',
      undefined,
      undefined,
      options
    );
  }

  async getSamplingFeature(
    featureId: string,
    options?: { f?: string }
  ): Promise<string> {
    return this.buildResourceUrl(
      'samplingFeatures',
      featureId,
      undefined,
      options
    );
  }

  async getSamplingFeatureHistory(
    featureId: string,
    options?: HistoryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'samplingFeatures',
      featureId,
      'history',
      options
    );
  }

  // + 5 CRUD methods

  // --- Properties (6 methods) ---

  async getProperties(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('properties', undefined, undefined, options);
  }

  async getProperty(propertyId: string): Promise<string> {
    return this.buildResourceUrl('properties', propertyId);
  }

  // + 4 CRUD methods (no history for properties)

  // ========================================
  // PART 2: DYNAMIC DATA
  // ========================================

  // --- Datastreams (11 methods) ---

  async getDatastreams(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('datastreams', undefined, undefined, options);
  }

  async getDatastream(
    datastreamId: string,
    options?: { f?: string }
  ): Promise<string> {
    return this.buildResourceUrl(
      'datastreams',
      datastreamId,
      undefined,
      options
    );
  }

  async getDatastreamObservations(
    datastreamId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'datastreams',
      datastreamId,
      'observations',
      options
    );
  }

  async getDatastreamSchema(
    datastreamId: string,
    options?: { f?: 'swe' | 'proto' }
  ): Promise<string> {
    return this.buildResourceUrl(
      'datastreams',
      datastreamId,
      'schema',
      options
    );
  }

  // + 7 CRUD methods + system-scoped access

  // --- Observations (9 methods) ---

  async getObservations(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('observations', undefined, undefined, options);
  }

  async getObservation(observationId: string): Promise<string> {
    return this.buildResourceUrl('observations', observationId);
  }

  // + 7 methods (create, datastream-scoped, time filtering, etc.)

  // --- Control Streams (8 methods) ---

  async getControlStreams(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl(
      'controlstreams',
      undefined,
      undefined,
      options
    );
  }

  async getControlStream(
    controlStreamId: string,
    options?: { f?: string }
  ): Promise<string> {
    return this.buildResourceUrl(
      'controlstreams',
      controlStreamId,
      undefined,
      options
    );
  }

  async getControlStreamCommands(
    controlStreamId: string,
    options?: QueryOptions
  ): Promise<string> {
    return this.buildResourceUrl(
      'controlstreams',
      controlStreamId,
      'commands',
      options
    );
  }

  async getControlStreamSchema(
    controlStreamId: string,
    options?: { f?: 'swe' | 'proto' }
  ): Promise<string> {
    return this.buildResourceUrl(
      'controlstreams',
      controlStreamId,
      'schema',
      options
    );
  }

  // + 4 CRUD methods + system-scoped access

  // --- Commands (10 methods) ---

  async getCommands(options?: QueryOptions): Promise<string> {
    return this.buildResourceUrl('commands', undefined, undefined, options);
  }

  async getCommand(commandId: string): Promise<string> {
    return this.buildResourceUrl('commands', commandId);
  }

  async getCommandStatus(commandId: string): Promise<string> {
    return this.buildResourceUrl('commands', commandId, 'status');
  }

  async getCommandStatusById(
    commandId: string,
    statusId: string
  ): Promise<string> {
    return `${this.buildResourceUrl(
      'commands',
      commandId,
      'status'
    )}/${statusId}`;
  }

  async getCommandResult(commandId: string): Promise<string> {
    return this.buildResourceUrl('commands', commandId, 'result');
  }

  async getCommandResultById(
    commandId: string,
    resultId: string
  ): Promise<string> {
    return `${this.buildResourceUrl(
      'commands',
      commandId,
      'result'
    )}/${resultId}`;
  }

  // + 4 CRUD methods + control-stream-scoped access
}
```

### Code Volume Summary

**CSAPI implementation:**

| Component                | Lines       | Description                           |
| ------------------------ | ----------- | ------------------------------------- |
| url_builder.ts           | 500-700     | QueryBuilder class with 70-80 methods |
| formats.ts               | 10          | Optional format constants             |
| index.ts                 | 3           | Exports                               |
| endpoint.ts additions    | 30          | hasConnectedSystems + csapi() method  |
| info.ts additions        | 15          | Conformance checking                  |
| **Total implementation** | **560-760** | **Core CSAPI code**                   |

**Per-resource efficiency:**

- 9 resources = 560-760 lines total
- Average: ~62-84 lines per resource type
- EDR: ~400 lines for 1 resource type
- **CSAPI is 5-6x more efficient per resource**

**Comparison to upstream:**

- ogc-client core (excluding tests): ~3000-4000 lines
- CSAPI addition: ~560-760 lines (~15-19% increase)
- Reasonable contribution size

---

## Summary

### Key Architectural Decisions

1. **Single QueryBuilder** - CSAPIQueryBuilder contains all 70-80 methods
2. **No separate Part 1/Part 2** - Logical sections via comments
3. **Helper methods, not inheritance** - buildResourceUrl + buildQueryString
4. **Path concatenation for sub-resources** - No link navigation
5. **Resource discovery exposed, not validated** - availableResources property
6. **No format parsing** - URL building with format parameter only
7. **Follow EDR pattern** - Same structure, same approach

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

✅ **Formats:**

- [x] Optional CSAPI_FORMATS constants (~10 lines)
- [x] No parsing, no validation

✅ **Code volume:**

- [x] Total: ~560-760 lines
- [x] Per resource: ~62-84 lines average
- [x] 5-6x more efficient than EDR per resource

### Result

**Clean, simple architecture** following upstream patterns. 9 resources handled with **same approach** as EDR's 1 resource, just scaled up proportionally. No over-engineering, no unnecessary abstraction, minimal code volume.
