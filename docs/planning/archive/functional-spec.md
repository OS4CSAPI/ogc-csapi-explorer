# CSAPI Client Library - Functional Specification

**Version:** 1.0  
**Date:** 2026-01-31  
**Status:** Draft  
**Authors:** Development Team

---

## Document Purpose

This functional specification defines the complete implementation of the Connected Systems API (CSAPI) client library for integration into [camptocamp/ogc-client](https://github.com/camptocamp/ogc-client). It translates research findings (Sections 16-19) into actionable design and implementation requirements.

**Research Foundation:**

- [Section 16](../research/requirements/csapi-52north-analysis.md): 52°North CSAPI server analysis
- [Section 17](../research/requirements/csapi-gap-analysis.md): Gap analysis of previous implementation
- [Section 18](../research/requirements/upstream-expectations.md): Upstream library expectations
- [Section 19](../research/requirements/mvp-definition.md): Full implementation scope

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Public API Specification](#3-public-api-specification)
4. [Format Abstraction Layer](#4-format-abstraction-layer)
5. [Resource Implementation](#5-resource-implementation)
6. [Worker Architecture](#6-worker-architecture)
7. [Error Handling](#7-error-handling)
8. [Caching Strategy](#8-caching-strategy)
9. [Testing Strategy](#9-testing-strategy)
10. [Implementation Plan](#10-implementation-plan)

---

## 1. Executive Summary

### 1.1 Project Overview

**Goal:** Implement a complete TypeScript client library for the OGC Connected Systems API (CSAPI) specification, providing developers with a robust, type-safe interface to interact with CSAPI-compliant servers.

**Scope:** Full CSAPI specification coverage

- **Part 1 Resources:** Systems, Deployments, Procedures, Sampling Features, Properties
- **Part 2 Resources:** DataStreams, Observations, Control Streams, Commands
- **Format Support:** GeoJSON, SensorML 2.0+, SWE Common 2.0 (all components, all encodings)
- **Features:** Complete CRUD, query parameters, bulk operations, streaming, CQL2 filtering

**Timeline:** 8-10 weeks  
**Lines of Code:** ~10,000 lines  
**Test Coverage:** 90%+ required

### 1.2 Key Requirements

**Functional Requirements:**

1. Parse CSAPI service metadata (landing page, conformance, collections)
2. Access all 9 CSAPI resource types (GET collection, GET by ID, CRUD operations)
3. Parse all CSAPI formats (GeoJSON, SensorML, SWE Common)
4. Support all query parameters (bbox, datetime, limit, offset, filter, properties, sortby)
5. Handle bulk operations (observation insert, command submission)
6. Provide streaming support for large datasets
7. Validate requests and responses

**Non-Functional Requirements:**

1. Follow upstream patterns (WFS/WMS/WMTS endpoint architecture)
2. 90%+ test coverage
3. Comprehensive JSDoc documentation
4. Browser and Node.js compatibility
5. Bundle size < 150KB (gzipped, with all formats)
6. Performance: 10K observations parsed < 5 seconds

### 1.3 Success Criteria

**Technical Criteria:**

- ✅ All 9 resource types accessible via CSAPIEndpoint
- ✅ All format parsers functional (GeoJSON, SensorML, SWE Common)
- ✅ 90%+ test coverage
- ✅ 0 TypeScript/ESLint errors
- ✅ Passes CI/CD checks

**Acceptance Criteria:**

- ✅ PR approved by camptocamp maintainers
- ✅ Merged to main branch
- ✅ Documentation complete (JSDoc + README)
- ✅ Integration tests passing with real server (52°North demo)

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Application                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CSAPIEndpoint                             │
│  - Parse landing page, conformance, collections                 │
│  - Resource getters (getSystems, getDataStreams, etc.)          │
│  - Query builders (bbox, datetime, filter)                      │
│  - CRUD URL builders                                             │
└───────────────┬───────────────┬──────────────┬──────────────────┘
                │               │              │
                ▼               ▼              ▼
    ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
    │ HTTP Utilities│  │    Cache     │  │Worker Handler│
    │  - fetch      │  │  - useCache  │  │ - offload    │
    │  - auth       │  │  - invalidate│  │ - fallback   │
    └───────┬───────┘  └──────────────┘  └──────┬───────┘
            │                                     │
            ▼                                     ▼
    ┌──────────────────────────────────────────────────┐
    │            Format Abstraction Layer              │
    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
    │  │ GeoJSON  │  │ SensorML │  │ SWE Common   │  │
    │  │ Parser   │  │ Parser   │  │ Parser       │  │
    │  └──────────┘  └──────────┘  └──────────────┘  │
    │  ┌──────────────────────────────────────────┐  │
    │  │     Format Detector & Validator          │  │
    │  └──────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────┘
```

### 2.2 Module Structure

```
src/csapi/
├── endpoint.ts              # CSAPIEndpoint class (main entry point)
├── conformance.ts           # Parse /conformance endpoint
├── collections.ts           # Parse /collections endpoint
├── model.ts                 # All TypeScript type definitions
├── url.ts                   # URL builders for all operations
├── formats/
│   ├── geojson.ts          # GeoJSON parser (500 lines)
│   ├── sensorml.ts         # SensorML parser (1,500 lines)
│   ├── swe-common.ts       # SWE Common parser (2,000 lines)
│   ├── detector.ts         # Format detection (300 lines)
│   └── validator.ts        # Format validation (600 lines)
├── resources/
│   ├── systems.ts          # System operations
│   ├── deployments.ts      # Deployment operations
│   ├── procedures.ts       # Procedure operations
│   ├── sampling-features.ts # Sampling Feature operations
│   ├── properties.ts       # Property operations
│   ├── datastreams.ts      # DataStream operations
│   ├── observations.ts     # Observation operations
│   ├── control-streams.ts  # Control Stream operations
│   └── commands.ts         # Command operations
└── endpoint.spec.ts        # Integration tests
```

### 2.3 Design Patterns

**Pattern 1: Endpoint Pattern (from Section 18)**

```typescript
// Constructor initiates async operations
constructor(url: string) {
  this._initPromise = this._initialize();
}

// isReady() resolves when endpoint ready to use
async isReady(): Promise<this> {
  await this._initPromise;
  return this;
}

// Synchronous getters after initialization
getServiceInfo(): CSAPIEndpointInfo {
  return this._info;
}
```

**Pattern 2: Builder Pattern (URL construction)**

```typescript
// Fluent API for complex queries
const url = new DataStreamQueryBuilder(baseUrl)
  .bbox([-180, -90, 180, 90])
  .datetime('2024-01-01T00:00:00Z/..')
  .limit(100)
  .build();
```

**Pattern 3: Strategy Pattern (format parsing)**

```typescript
// Format-specific parsers implement common interface
interface FormatParser<T> {
  detect(data: unknown): boolean;
  parse(data: unknown): T;
  validate(data: unknown): ValidationResult;
}
```

**Pattern 4: Worker Delegation Pattern**

```typescript
// Heavy parsing offloaded to worker
export function parseSensorML(url: string): Promise<ParsedSensorML> {
  if (isWorkerAvailable()) {
    return sendMessageToWorker('parseSensorML', { url });
  }
  return parseSensorMLFallback(url);
}
```

---

## 3. Public API Specification

### 3.1 CSAPIEndpoint Class

````typescript
/**
 * Represents a CSAPI endpoint providing access to connected systems resources.
 *
 * @example
 * ```typescript
 * const endpoint = new CSAPIEndpoint('https://api.example.com/csapi');
 * await endpoint.isReady();
 * const systems = await endpoint.getSystems();
 * ```
 */
export default class CSAPIEndpoint {
  /**
   * Create a new CSAPI endpoint.
   * @param url - Base URL of the CSAPI endpoint
   * @param options - Optional configuration (auth, fetch options)
   */
  constructor(url: string, options?: CSAPIEndpointOptions);

  /**
   * Resolves when the endpoint is ready to use.
   * @throws {CSAPIError} If initialization fails
   */
  isReady(): Promise<CSAPIEndpoint>;

  /**
   * Get service metadata (title, description, provider, etc.)
   */
  getServiceInfo(): CSAPIEndpointInfo;

  /**
   * Get list of conformance classes supported by the server.
   */
  getConformanceClasses(): string[];

  /**
   * Get all collections advertised by the service.
   */
  getCollections(): CSAPICollection[];

  // Part 1 Resources
  getSystems(options?: QueryOptions): Promise<SystemCollection>;
  getSystemById(id: string, options?: GetByIdOptions): Promise<SystemFeature>;
  createSystem(system: SystemInput): Promise<string>; // Returns created ID
  updateSystem(id: string, system: SystemInput): Promise<void>;
  deleteSystem(id: string): Promise<void>;

  getDeployments(options?: QueryOptions): Promise<DeploymentCollection>;
  getDeploymentById(
    id: string,
    options?: GetByIdOptions
  ): Promise<DeploymentFeature>;
  createDeployment(deployment: DeploymentInput): Promise<string>;
  updateDeployment(id: string, deployment: DeploymentInput): Promise<void>;
  deleteDeployment(id: string): Promise<void>;

  getProcedures(options?: QueryOptions): Promise<ProcedureCollection>;
  getProcedureById(id: string, options?: GetByIdOptions): Promise<Procedure>;
  createProcedure(procedure: ProcedureInput): Promise<string>;
  updateProcedure(id: string, procedure: ProcedureInput): Promise<void>;
  deleteProcedure(id: string): Promise<void>;

  getSamplingFeatures(
    options?: QueryOptions
  ): Promise<SamplingFeatureCollection>;
  getSamplingFeatureById(
    id: string,
    options?: GetByIdOptions
  ): Promise<SamplingFeatureFeature>;
  createSamplingFeature(feature: SamplingFeatureInput): Promise<string>;
  updateSamplingFeature(
    id: string,
    feature: SamplingFeatureInput
  ): Promise<void>;
  deleteSamplingFeature(id: string): Promise<void>;

  getProperties(options?: QueryOptions): Promise<PropertyCollection>;
  getPropertyById(id: string, options?: GetByIdOptions): Promise<Property>;

  // Part 2 Resources
  getDataStreams(options?: QueryOptions): Promise<DataStreamCollection>;
  getDataStreamById(id: string, options?: GetByIdOptions): Promise<DataStream>;
  getSystemDataStreams(
    systemId: string,
    options?: QueryOptions
  ): Promise<DataStreamCollection>;
  createDataStream(datastream: DataStreamInput): Promise<string>;
  updateDataStream(id: string, datastream: DataStreamInput): Promise<void>;
  deleteDataStream(id: string): Promise<void>;

  getObservations(options?: QueryOptions): Promise<ObservationCollection>;
  getObservationById(
    id: string,
    options?: GetByIdOptions
  ): Promise<Observation>;
  getDataStreamObservations(
    datastreamId: string,
    options?: QueryOptions
  ): Promise<ObservationCollection>;
  createObservations(observations: ObservationInput[]): Promise<string[]>; // Bulk insert

  getControlStreams(options?: QueryOptions): Promise<ControlStreamCollection>;
  getControlStreamById(
    id: string,
    options?: GetByIdOptions
  ): Promise<ControlStream>;
  getSystemControlStreams(
    systemId: string,
    options?: QueryOptions
  ): Promise<ControlStreamCollection>;
  createControlStream(stream: ControlStreamInput): Promise<string>;
  updateControlStream(id: string, stream: ControlStreamInput): Promise<void>;
  deleteControlStream(id: string): Promise<void>;

  getCommands(options?: QueryOptions): Promise<CommandCollection>;
  getCommandById(id: string, options?: GetByIdOptions): Promise<Command>;
  getControlStreamCommands(
    controlStreamId: string,
    options?: QueryOptions
  ): Promise<CommandCollection>;
  createCommands(commands: CommandInput[]): Promise<string[]>; // Bulk submit

  // Helper methods
  getVersion(): string | undefined;
  clearCache(): void;
}
````

### 3.2 Query Options

```typescript
interface QueryOptions {
  /** Bounding box filter [minx, miny, maxx, maxy] */
  bbox?: BoundingBox;

  /** Temporal filter (ISO 8601 interval or instant) */
  datetime?: string;

  /** Maximum number of results */
  limit?: number;

  /** Pagination offset */
  offset?: number;

  /** CQL2 filter expression */
  filter?: string;

  /** Property selection (comma-separated) */
  properties?: string[];

  /** Sort by property(s) */
  sortby?: string;

  /** Output format (MIME type) */
  f?: string;
}

interface GetByIdOptions {
  /** Output format (MIME type) */
  f?: string;
}
```

### 3.3 Core Types

```typescript
// Shared types (from upstream)
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;
export type MimeType = string;

// CSAPI-specific endpoint info
export interface CSAPIEndpointInfo extends GenericEndpointInfo {
  // Extends upstream GenericEndpointInfo with CSAPI-specific fields
  conformsTo?: string[];
  version?: string;
}

export interface CSAPICollection {
  id: string;
  title: string;
  description?: string;
  links: Link[];
  extent?: {
    spatial?: { bbox: BoundingBox[] };
    temporal?: { interval: string[][] };
  };
  itemType?: string; // 'system', 'deployment', etc.
}

export interface Link {
  href: string;
  rel: string;
  type?: string;
  title?: string;
}
```

### 3.4 Resource Types

```typescript
// System (Part 1)
export interface SystemFeature {
  type: 'Feature';
  id: string;
  geometry?: Geometry;
  properties: {
    name: string;
    description?: string;
    featureType: string;
    validTime?: TemporalExtent;
    // ... SensorML properties
  };
  links?: Link[];
}

export interface SystemCollection {
  type: 'FeatureCollection';
  features: SystemFeature[];
  links?: Link[];
  numberMatched?: number;
  numberReturned?: number;
}

// DataStream (Part 2)
export interface DataStream {
  id: string;
  name: string;
  description?: string;
  observedProperty: Link;
  phenomenonTime?: TemporalExtent;
  resultTime?: TemporalExtent;
  system: Link;
  procedure?: Link;
  observedArea?: Geometry;
  outputName?: string;
  schema: SWEComponent; // SWE Common component defining result structure
  encoding?: SWEEncoding; // How results are encoded (JSON, text, binary)
  links?: Link[];
}

// Observation (Part 2)
export interface Observation {
  id: string;
  phenomenonTime: string; // ISO 8601
  resultTime: string; // ISO 8601
  result: unknown; // Parsed according to DataStream schema
  datastream: Link;
  featureOfInterest?: Link;
  parameters?: Record<string, unknown>;
  links?: Link[];
}

// ... (Additional resource types: Deployment, Procedure, SamplingFeature, Property, ControlStream, Command)
```

---

## 4. Format Abstraction Layer

### 4.1 Format Detection

**Strategy:** Multi-level detection

1. **Content-Type header** (most reliable)
2. **Body structure analysis** (JSON key patterns)
3. **Context inference** (resource type + operation)
4. **Fallback heuristics** (educated guesses)

**Implementation:**

```typescript
export interface FormatDetector {
  detect(
    contentType: string | undefined,
    body: unknown,
    context: DetectionContext
  ): DetectedFormat;
}

export interface DetectionContext {
  resourceType?: 'system' | 'deployment' | 'datastream' | 'observation' | /* ... */;
  operation?: 'list' | 'get' | 'create' | 'update';
  expectedFormats?: MimeType[];
}

export interface DetectedFormat {
  format: 'geojson' | 'sensorml' | 'swe-common' | 'json' | 'unknown';
  confidence: 'high' | 'medium' | 'low';
  mimeType?: string;
}
```

**Detection Rules:**

```typescript
// Rule 1: Content-Type header
if (contentType === 'application/geo+json') return 'geojson';
if (contentType === 'application/sensorml+json') return 'sensorml';
if (contentType === 'application/swe+json') return 'swe-common';

// Rule 2: GeoJSON structure
if (body.type === 'Feature' || body.type === 'FeatureCollection')
  return 'geojson';

// Rule 3: SensorML structure
if (
  body.definition?.startsWith(
    'http://www.opengis.net/def/observationType/OGC-OM/2.0/'
  )
) {
  if (body.type === 'PhysicalSystem' || body.type === 'PhysicalComponent')
    return 'sensorml';
}

// Rule 4: Context-based (e.g., Systems use GeoJSON or SensorML)
if (context.resourceType === 'system' && hasGeometry(body)) return 'geojson';
```

### 4.2 GeoJSON Parser

**Scope:** All geometry types + Feature/FeatureCollection

**Implementation:**

```typescript
export interface GeoJSONParser {
  parseFeature(data: unknown): Feature;
  parseFeatureCollection(data: unknown): FeatureCollection;
  parseGeometry(data: unknown): Geometry;
  validate(data: unknown): ValidationResult;
}

// Supported geometry types
export type Geometry =
  | Point
  | LineString
  | Polygon
  | MultiPoint
  | MultiLineString
  | MultiPolygon
  | GeometryCollection;

export interface Point {
  type: 'Point';
  coordinates: Position; // [lon, lat] or [lon, lat, elevation]
}

// ... (other geometry types)
```

**Validation Rules:**

- `type` field required
- `coordinates` must be valid arrays
- CRS (if present) must be valid
- Bbox (if present) must match geometry extent

**Estimated LOC:** ~500 lines

### 4.3 SensorML Parser

**Scope:** All process types (SimpleProcess, PhysicalSystem, PhysicalComponent, AggregateProcess, ProcessChain), all versions (2.0, 2.1)

**Implementation:**

```typescript
export interface SensorMLParser {
  parse(data: unknown): SensorMLProcess;
  validate(data: unknown): ValidationResult;
}

export type SensorMLProcess =
  | SimpleProcess
  | PhysicalSystem
  | PhysicalComponent
  | AggregateProcess
  | ProcessChain;

export interface PhysicalSystem {
  type: 'PhysicalSystem';
  id: string;
  definition: string;
  uniqueId?: string;
  label?: string;
  description?: string;
  identification?: IdentifierList;
  classification?: ClassifierList;
  validTime?: TimePeriod;
  securityConstraints?: ConstraintList;
  legalConstraints?: ConstraintList;
  characteristics?: CharacteristicList;
  capabilities?: CapabilityList;
  contacts?: ContactList;
  documentation?: DocumentList;
  history?: EventList;
  position?: Position;
  components?: ComponentList; // Nested systems/sensors
  connections?: ConnectionList; // Data flow between components
}

// ... (other process types with similar structure)
```

**Key Elements to Parse:**

1. **Identification:** Identifiers, classifiers, long name, short name
2. **Characteristics:** Physical properties (size, weight, power, etc.)
3. **Capabilities:** Measurement capabilities (range, resolution, accuracy)
4. **Position:** Location (Point/Pose), orientation (Vector), reference frame
5. **Components:** Nested systems/sensors (recursive parsing)
6. **Connections:** Links between components (data flow)

**Validation Rules:**

- `type` must be valid SensorML process type
- `definition` must be valid URI
- Position coordinates must be valid
- Components (if present) must be valid SensorML processes
- Connections must reference existing components

**Estimated LOC:** ~1,500 lines

### 4.4 SWE Common Parser

**Scope:** All component types, all encodings (JSON, Text, Binary)

**Implementation:**

```typescript
export interface SWECommonParser {
  parseComponent(data: unknown): SWEComponent;
  parseEncoding(data: unknown): SWEEncoding;
  parseValue(value: unknown, component: SWEComponent): ParsedValue;
  validate(data: unknown, schema?: SWEComponent): ValidationResult;
}

export type SWEComponent =
  | DataRecord
  | DataArray
  | Vector
  | Quantity
  | Count
  | Boolean
  | Text
  | Category
  | Time
  | DataChoice
  | Matrix;

export interface DataRecord {
  type: 'DataRecord';
  label?: string;
  description?: string;
  definition?: string;
  fields: SWEField[];
}

export interface SWEField {
  name: string;
  component: SWEComponent;
}

export interface Quantity {
  type: 'Quantity';
  label?: string;
  description?: string;
  definition?: string;
  uom: UnitOfMeasure; // Unit of measure
  constraint?: AllowedValues; // Range, intervals, etc.
  quality?: Quality;
}

export interface DataArray {
  type: 'DataArray';
  label?: string;
  description?: string;
  definition?: string;
  elementCount?: Count;
  elementType: SWEComponent;
  encoding?: SWEEncoding;
  values?: unknown[]; // Actual data values
}

// Encodings
export type SWEEncoding =
  | JSONEncoding
  | TextEncoding
  | BinaryEncoding
  | XMLEncoding;

export interface TextEncoding {
  type: 'TextEncoding';
  tokenSeparator: string; // e.g., ','
  blockSeparator: string; // e.g., '\n'
  decimalSeparator?: string; // e.g., '.'
  collapseWhiteSpaces?: boolean;
}

export interface BinaryEncoding {
  type: 'BinaryEncoding';
  byteOrder: 'bigEndian' | 'littleEndian';
  byteEncoding: 'base64' | 'raw';
  members: BinaryMember[];
}
```

**Component Parsing Logic:**

1. Detect component type from `type` field
2. Parse common properties (label, description, definition)
3. Parse type-specific properties (uom for Quantity, fields for DataRecord, etc.)
4. Recursively parse nested components (DataRecord fields, DataArray elements)

**Encoding Support:**

- **JSON Encoding:** Default, parse as JavaScript objects/arrays
- **Text Encoding:** Parse CSV-like strings using token/block separators
- **Binary Encoding:** Parse base64-encoded or raw binary data using member definitions

**Value Parsing:**

```typescript
// Parse observation result against DataStream schema
const result = parseValue(observation.result, datastream.schema);

// Example: DataRecord with Quantity fields
// Schema: { type: 'DataRecord', fields: [
//   { name: 'temperature', component: { type: 'Quantity', uom: 'degC' } },
//   { name: 'humidity', component: { type: 'Quantity', uom: '%' } }
// ]}
// Value: { temperature: 25.5, humidity: 60.2 }
// Result: { temperature: { value: 25.5, uom: 'degC' }, humidity: { value: 60.2, uom: '%' } }
```

**Validation Rules:**

- Component `type` must be valid
- Quantity must have `uom`
- DataRecord must have `fields` array
- DataArray must have `elementType`
- Values must match schema constraints (allowed values, ranges, etc.)

**Estimated LOC:** ~2,000 lines

### 4.5 Format Validation

**Validation Levels:**

1. **Structural:** JSON structure matches expected format
2. **Type:** Field types correct (string, number, array, object)
3. **Required:** Required fields present
4. **Constraints:** Values within allowed ranges/enumerations
5. **Semantic:** Relationships valid (e.g., bbox matches geometry extent)
6. **Cross-Resource:** Foreign keys valid (e.g., datastream references existing system)

**Implementation:**

```typescript
export interface Validator {
  validate(data: unknown, schema: ValidationSchema): ValidationResult;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  path: string; // JSON path (e.g., 'properties.validTime.begin')
  message: string;
  expected?: unknown;
  actual?: unknown;
}

export type ValidationMode = 'strict' | 'lenient';
// strict: throw on any error
// lenient: log warnings, continue parsing
```

**Validation Strategy:**

- **Pre-Request:** Validate create/update payloads before sending to server
- **Post-Response:** Validate server responses to catch malformed data
- **Configurable:** Allow users to set validation mode (strict vs lenient)

**Estimated LOC:** ~600 lines

---

## 5. Resource Implementation

### 5.1 Resource Implementation Pattern

**All resources follow same pattern:**

```typescript
// resources/systems.ts
export async function getSystems(
  endpoint: CSAPIEndpoint,
  options: QueryOptions = {}
): Promise<SystemCollection> {
  // 1. Build URL with query parameters
  const url = buildSystemsUrl(endpoint.baseUrl, options);

  // 2. Fetch data
  const response = await fetchWithOptions(url, endpoint.fetchOptions);

  // 3. Detect format
  const format = detectFormat(
    response.headers.get('content-type'),
    await response.json(),
    { resourceType: 'system', operation: 'list' }
  );

  // 4. Parse based on format
  let systems: SystemCollection;
  if (format.format === 'geojson') {
    systems = parseGeoJSON(response.body) as SystemCollection;
  } else if (format.format === 'sensorml') {
    // Convert SensorML to canonical format
    systems = convertSensorMLToCollection(parseSensorML(response.body));
  }

  // 5. Validate (optional)
  if (endpoint.validationMode === 'strict') {
    validateSystemCollection(systems);
  }

  // 6. Return typed result
  return systems;
}

export function buildCreateSystemUrl(baseUrl: string): string {
  return `${baseUrl}/systems`;
}

export function buildSystemUrl(baseUrl: string, id: string): string {
  return `${baseUrl}/systems/${encodeURIComponent(id)}`;
}

export function buildSystemsUrl(
  baseUrl: string,
  options: QueryOptions
): string {
  const url = new URL(`${baseUrl}/systems`);
  if (options.bbox) {
    url.searchParams.set('bbox', options.bbox.join(','));
  }
  if (options.datetime) {
    url.searchParams.set('datetime', options.datetime);
  }
  if (options.limit) {
    url.searchParams.set('limit', String(options.limit));
  }
  // ... other query params
  return url.toString();
}
```

### 5.2 Resource Modules

**Part 1 Resources:**

- `systems.ts` - System operations (~150 lines)
- `deployments.ts` - Deployment operations (~150 lines)
- `procedures.ts` - Procedure operations (~100 lines)
- `sampling-features.ts` - Sampling Feature operations (~100 lines)
- `properties.ts` - Property operations (~80 lines)

**Part 2 Resources:**

- `datastreams.ts` - DataStream operations (~200 lines, includes schema parsing)
- `observations.ts` - Observation operations (~250 lines, includes bulk insert, streaming)
- `control-streams.ts` - Control Stream operations (~150 lines)
- `commands.ts` - Command operations (~200 lines, includes bulk submit)

**Total:** ~1,380 lines

### 5.3 Nested Resources

**Pattern:** Some resources are nested under others

```typescript
// /systems/{systemId}/datastreams
export async function getSystemDataStreams(
  endpoint: CSAPIEndpoint,
  systemId: string,
  options: QueryOptions = {}
): Promise<DataStreamCollection> {
  const url = buildSystemDataStreamsUrl(endpoint.baseUrl, systemId, options);
  // ... same as getDataStreams but different URL
}

// /datastreams/{datastreamId}/observations
export async function getDataStreamObservations(
  endpoint: CSAPIEndpoint,
  datastreamId: string,
  options: QueryOptions = {}
): Promise<ObservationCollection> {
  const url = buildDataStreamObservationsUrl(
    endpoint.baseUrl,
    datastreamId,
    options
  );
  // ... same as getObservations but different URL
}
```

---

## 6. Worker Architecture

### 6.1 Worker Usage Strategy

**What runs in worker:**

- Conformance parsing (JSON parsing)
- Collections parsing (JSON parsing + format detection)
- SensorML parsing (heavy JSON parsing + validation)
- SWE Common parsing (complex schema parsing)
- Observation parsing (potentially large datasets)
- Format validation (CPU-intensive)

**What stays in main thread:**

- HTTP requests (fetch API)
- Cache management
- URL building
- Lightweight operations

### 6.2 Worker Implementation

**Worker Handler Registration:**

```typescript
// worker/worker.ts
import * as conformance from '../csapi/conformance.js';
import * as sensorml from '../csapi/formats/sensorml.js';
import * as sweCommon from '../csapi/formats/swe-common.js';

addTaskHandler('parseConformance', globalThis, ({ url }: { url: string }) =>
  queryJsonDocument(url).then((json) => conformance.parse(json))
);

addTaskHandler('parseSensorML', globalThis, ({ data }: { data: unknown }) =>
  sensorml.parse(data)
);

addTaskHandler('parseSWEComponent', globalThis, ({ data }: { data: unknown }) =>
  sweCommon.parseComponent(data)
);

addTaskHandler(
  'parseObservations',
  globalThis,
  ({ data, schema }: { data: unknown; schema: SWEComponent }) =>
    sweCommon.parseValues(data, schema)
);
```

**Worker API:**

```typescript
// worker/index.ts
export function parseConformance(url: string): Promise<ConformanceDocument> {
  return sendMessageToWorker('parseConformance', { url });
}

export function parseSensorML(data: unknown): Promise<SensorMLProcess> {
  return sendMessageToWorker('parseSensorML', { data });
}

export function parseSWEComponent(data: unknown): Promise<SWEComponent> {
  return sendMessageToWorker('parseSWEComponent', { data });
}

export function parseObservations(
  data: unknown,
  schema: SWEComponent
): Promise<ParsedObservation[]> {
  return sendMessageToWorker('parseObservations', { data, schema });
}
```

**Fallback Mode:**

```typescript
// Enable fallback when workers not available (e.g., Node.js, old browsers)
import { enableFallbackWithoutWorker } from '@camptocamp/ogc-client/worker';

// In non-browser environments
if (typeof Worker === 'undefined') {
  enableFallbackWithoutWorker();
}
```

---

## 7. Error Handling

### 7.1 Error Types

```typescript
/**
 * Base error class for all CSAPI errors.
 */
export class CSAPIError extends Error {
  constructor(message: string, public code: string, public cause?: Error) {
    super(message);
    this.name = 'CSAPIError';
  }
}

/**
 * Error during format parsing (GeoJSON, SensorML, SWE Common).
 */
export class FormatParseError extends CSAPIError {
  constructor(
    message: string,
    public format: string,
    public path: string,
    cause?: Error
  ) {
    super(message, 'FORMAT_PARSE_ERROR', cause);
    this.name = 'FormatParseError';
  }
}

/**
 * Error during format validation.
 */
export class ValidationError extends CSAPIError {
  constructor(
    message: string,
    public path: string,
    public expected?: unknown,
    public actual?: unknown
  ) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

/**
 * Server returned an error (4xx, 5xx).
 */
export class ServerError extends CSAPIError {
  constructor(
    message: string,
    public statusCode: number,
    public response?: unknown
  ) {
    super(message, 'SERVER_ERROR');
    this.name = 'ServerError';
  }
}

/**
 * Network error (connection failed, timeout, etc.).
 */
export class NetworkError extends CSAPIError {
  constructor(message: string, cause?: Error) {
    super(message, 'NETWORK_ERROR', cause);
    this.name = 'NetworkError';
  }
}
```

### 7.2 Error Handling Strategy

**At HTTP Layer:**

```typescript
async function fetchWithOptions(
  url: string,
  options: FetchOptions
): Promise<Response> {
  try {
    const response = await fetch(url, options);

    // Check for HTTP errors
    if (!response.ok) {
      const body = await response.text();
      // Try to parse OGC Exception Report
      const exception = parseOGCException(body);
      throw new ServerError(
        exception?.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        exception
      );
    }

    return response;
  } catch (error) {
    if (error instanceof ServerError) throw error;
    throw new NetworkError(`Failed to fetch ${url}`, error as Error);
  }
}
```

**At Parsing Layer:**

```typescript
function parseSensorML(data: unknown): SensorMLProcess {
  try {
    // Structural validation
    if (!isObject(data)) {
      throw new FormatParseError(
        'SensorML data must be an object',
        'sensorml',
        '$'
      );
    }

    // Type validation
    if (!data.type || !VALID_SENSORML_TYPES.includes(data.type)) {
      throw new FormatParseError(
        `Invalid SensorML type: ${data.type}`,
        'sensorml',
        '$.type'
      );
    }

    // Parse fields
    // ...
  } catch (error) {
    if (error instanceof FormatParseError) throw error;
    throw new FormatParseError(
      `Failed to parse SensorML: ${error.message}`,
      'sensorml',
      '$',
      error as Error
    );
  }
}
```

**At Validation Layer:**

```typescript
function validateSystem(system: SystemFeature): ValidationResult {
  const errors: ValidationError[] = [];

  // Required fields
  if (!system.properties?.name) {
    errors.push(
      new ValidationError(
        'System name is required',
        '$.properties.name',
        'string',
        undefined
      )
    );
  }

  // Geometry validation
  if (system.geometry && !isValidGeometry(system.geometry)) {
    errors.push(
      new ValidationError(
        'Invalid geometry',
        '$.geometry',
        'valid GeoJSON geometry',
        system.geometry
      )
    );
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings: [],
  };
}
```

### 7.3 OGC Exception Report Parsing

```typescript
interface OGCException {
  code: string;
  locator?: string;
  message: string;
}

function parseOGCException(body: string): OGCException | null {
  try {
    const json = JSON.parse(body);

    // OGC API style exception
    if (json.code && json.description) {
      return {
        code: json.code,
        locator: json.locator,
        message: json.description,
      };
    }

    // Try XML format (older OGC services)
    // ...
  } catch {
    return null;
  }
}
```

---

## 8. Caching Strategy

### 8.1 What Gets Cached

**Static Metadata (cache indefinitely):**

- Landing page (`/`)
- Conformance classes (`/conformance`)
- Collections (`/collections`)

**Dynamic Resources (no caching or short TTL):**

- Resource collections (systems, observations, etc.) - data changes frequently
- Individual resources by ID - may be updated

**Parsed Results (cache in memory):**

- Format detection results (for same URL)
- Parsed schemas (DataStream schemas reused for observations)

### 8.2 Cache Implementation

**Use upstream cache utility:**

```typescript
import { useCache } from '../shared/cache.js';

// Cache landing page
this._landingPagePromise = useCache(
  () => queryJsonDocument(this._url),
  'CSAPI',
  'LANDING_PAGE',
  this._url
);

// Cache conformance
this._conformancePromise = useCache(
  () => parseConformance(`${this._url}/conformance`),
  'CSAPI',
  'CONFORMANCE',
  this._url
);

// Cache collections
this._collectionsPromise = useCache(
  () => parseCollections(`${this._url}/collections`),
  'CSAPI',
  'COLLECTIONS',
  this._url
);
```

**Cache Invalidation:**

```typescript
export class CSAPIEndpoint {
  /**
   * Clear all cached data for this endpoint.
   * Call this if server data has changed.
   */
  clearCache(): void {
    clearCacheForPrefix('CSAPI', this._url);
  }
}
```

---

## 9. Testing Strategy

### 9.1 Test Structure

```
src/csapi/
├── endpoint.spec.ts          # Integration tests
├── conformance.spec.ts       # Unit tests
├── collections.spec.ts       # Unit tests
├── formats/
│   ├── geojson.spec.ts      # Unit tests
│   ├── sensorml.spec.ts     # Unit tests
│   ├── swe-common.spec.ts   # Unit tests
│   ├── detector.spec.ts     # Unit tests
│   └── validator.spec.ts    # Unit tests
└── resources/
    ├── systems.spec.ts       # Unit tests
    ├── datastreams.spec.ts   # Unit tests
    └── observations.spec.ts  # Unit tests
```

### 9.2 Test Fixtures

**Fixture Organization:**

```
fixtures/csapi/
├── conformance.json
├── collections.json
├── landing-page.json
├── systems/
│   ├── collection-geojson.json
│   ├── collection-sensorml.json
│   ├── physical-system.json
│   ├── physical-component.json
│   ├── aggregate-process.json
│   └── invalid-system.json
├── deployments/
├── datastreams/
│   ├── datastream-quantity.json
│   ├── datastream-datarecord.json
│   └── datastream-dataarray.json
├── observations/
│   ├── obs-json-encoding.json
│   ├── obs-text-encoding.txt
│   ├── obs-binary-encoding.b64
│   └── obs-bulk-10k.json
└── sensorml/
    ├── v2.0/
    └── v2.1/
```

**Fixture Sources:**

1. **52°North Demo Server:** Download real responses (Section 16.1)
2. **Spec Examples:** Use examples from CSAPI specification
3. **Manual Creation:** Create edge cases, invalid examples

### 9.3 Unit Tests

**Format Parser Tests:**

```typescript
describe('SensorML Parser', () => {
  describe('PhysicalSystem', () => {
    it('parses valid PhysicalSystem', () => {
      const data = loadFixture('sensorml/physical-system.json');
      const result = parseSensorML(data);

      expect(result.type).toBe('PhysicalSystem');
      expect(result.id).toBe('weatherStation01');
      expect(result.components).toHaveLength(3);
    });

    it('throws on missing required fields', () => {
      const data = { type: 'PhysicalSystem' }; // Missing id, definition

      expect(() => parseSensorML(data)).toThrow(FormatParseError);
    });

    it('parses nested components recursively', () => {
      const data = loadFixture('sensorml/aggregate-process.json');
      const result = parseSensorML(data);

      expect(result.components[0].type).toBe('PhysicalComponent');
    });
  });
});
```

**Resource Operation Tests:**

```typescript
describe('Systems Resource', () => {
  beforeEach(() => {
    globalThis.fetchResponseFactory = (url) => {
      if (url.includes('/systems')) {
        return loadFixture('systems/collection-geojson.json');
      }
    };
  });

  it('getSystems returns system collection', async () => {
    const endpoint = new CSAPIEndpoint('https://api.example.com/csapi');
    await endpoint.isReady();

    const systems = await endpoint.getSystems();

    expect(systems.type).toBe('FeatureCollection');
    expect(systems.features).toHaveLength(5);
  });

  it('getSystems with bbox filter', async () => {
    const endpoint = new CSAPIEndpoint('https://api.example.com/csapi');
    await endpoint.isReady();

    const systems = await endpoint.getSystems({
      bbox: [-180, -90, 180, 90],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('bbox=-180,-90,180,90')
    );
  });
});
```

### 9.4 Integration Tests

**End-to-End Workflow:**

```typescript
describe('CSAPI Integration', () => {
  let endpoint: CSAPIEndpoint;

  beforeAll(async () => {
    // Use mock server or real 52°North demo
    endpoint = new CSAPIEndpoint('https://ogc-demo.services.52north.org/csapi');
    await endpoint.isReady();
  });

  it('complete workflow: discover systems, get datastreams, fetch observations', async () => {
    // 1. Get systems
    const systems = await endpoint.getSystems({ limit: 10 });
    expect(systems.features.length).toBeGreaterThan(0);

    // 2. Get datastreams for first system
    const systemId = systems.features[0].id;
    const datastreams = await endpoint.getSystemDataStreams(systemId);
    expect(datastreams.items.length).toBeGreaterThan(0);

    // 3. Get observations for first datastream
    const datastreamId = datastreams.items[0].id;
    const observations = await endpoint.getDataStreamObservations(
      datastreamId,
      {
        limit: 100,
      }
    );
    expect(observations.items.length).toBeGreaterThan(0);

    // 4. Validate observation results match datastream schema
    const schema = datastreams.items[0].schema;
    observations.items.forEach((obs) => {
      const validResult = validateValue(obs.result, schema);
      expect(validResult.valid).toBe(true);
    });
  });
});
```

### 9.5 Performance Tests

```typescript
describe('Performance', () => {
  it('parses 10K observations in < 5 seconds', async () => {
    const data = loadFixture('observations/obs-bulk-10k.json');
    const schema = loadFixture('datastreams/datastream-datarecord.json').schema;

    const start = Date.now();
    const results = parseObservations(data, schema);
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(5000);
    expect(results).toHaveLength(10000);
  });

  it('worker parsing is faster than sync for large datasets', async () => {
    const data = loadFixture('observations/obs-bulk-10k.json');
    const schema = loadFixture('datastreams/datastream-datarecord.json').schema;

    // Sync parsing
    const syncStart = Date.now();
    parseObservationsSync(data, schema);
    const syncDuration = Date.now() - syncStart;

    // Worker parsing
    const workerStart = Date.now();
    await parseObservationsWorker(data, schema);
    const workerDuration = Date.now() - workerStart;

    expect(workerDuration).toBeLessThan(syncDuration);
  });
});
```

### 9.6 Coverage Requirements

**Target: 90%+ overall coverage**

**Critical Paths (100% coverage required):**

- Format parsers (GeoJSON, SensorML, SWE Common)
- Format detection
- Error handling
- Resource URL builders

**Medium Priority (80-90% coverage):**

- Validation
- Worker handlers
- Cache management

**Lower Priority (70-80% coverage):**

- Helper methods
- Type guards
- Utility functions

---

## 10. Implementation Plan

### 10.1 Week-by-Week Timeline

**Week 1: Core Infrastructure + GeoJSON**

- Days 1-2: Project setup, CSAPIEndpoint skeleton, landing page/conformance/collections parsing
- Days 3-4: Cache implementation, HTTP utilities, error types
- Day 5: GeoJSON parser (all geometry types) + tests

**Week 2: SensorML Parser**

- Days 1-2: SimpleProcess parsing + tests
- Days 3-4: PhysicalSystem, PhysicalComponent parsing + tests
- Day 5: AggregateProcess, ProcessChain parsing + tests

**Week 3: SWE Common Core**

- Days 1-2: Basic types (Quantity, Count, Boolean, Text, Category, Time) + tests
- Days 3-4: Structured types (DataRecord, Vector, DataArray) + tests
- Day 5: Advanced types (DataChoice, Matrix) + tests

**Week 4: SWE Common Encodings + Validation**

- Days 1-2: JSON encoding (complete) + tests
- Days 3-4: Text encoding, Binary encoding + tests
- Day 5: Format detector, format validator + tests

**Week 5: Part 1 Resources**

- Days 1-2: Systems, Deployments (GET, CRUD) + tests
- Days 3-4: Procedures, Sampling Features (GET, CRUD) + tests
- Day 5: Properties (GET) + query parameters (bbox, datetime, limit, offset) + tests

**Week 6: Part 2 Resources - DataStreams/Observations Start**

- Days 1-2: DataStreams (GET, CRUD, nested) + tests
- Days 3-4: DataStream schema parsing integration + tests
- Day 5: Observations (GET, nested) - basic + tests

**Week 7: Part 2 Resources - Observations Complete + Control**

- Days 1-2: Observation bulk insert, pagination + tests
- Days 3-4: Control Streams (GET, CRUD, nested) + tests
- Day 5: Commands (GET, nested, bulk) + tests

**Week 8: Advanced Features + Worker Support**

- Days 1-2: CQL2 filter support, property selection, sorting + tests
- Days 3-4: Association helpers, link traversal + tests
- Day 5: Worker handlers (all parsers), fallback mode + tests

**Week 9: Comprehensive Testing**

- Days 1-2: Unit test coverage review (target 90%+), fix gaps
- Days 3-4: Integration tests with 52°North demo server
- Day 5: Performance tests (10K+ observations), profiling

**Week 10: Documentation + Polish**

- Days 1-2: JSDoc on all public APIs, ensure completeness
- Days 3-4: README with comprehensive examples (all resources)
- Day 5: Final polish, PR preparation, request upstream review

### 10.2 Deliverables Checklist

**Code Deliverables:**

- [ ] `src/csapi/endpoint.ts` - CSAPIEndpoint class
- [ ] `src/csapi/conformance.ts` - Conformance parsing
- [ ] `src/csapi/collections.ts` - Collections parsing
- [ ] `src/csapi/model.ts` - All TypeScript types
- [ ] `src/csapi/url.ts` - URL builders
- [ ] `src/csapi/formats/geojson.ts` - GeoJSON parser
- [ ] `src/csapi/formats/sensorml.ts` - SensorML parser
- [ ] `src/csapi/formats/swe-common.ts` - SWE Common parser
- [ ] `src/csapi/formats/detector.ts` - Format detector
- [ ] `src/csapi/formats/validator.ts` - Format validator
- [ ] `src/csapi/resources/*.ts` - All 9 resource modules
- [ ] `src/worker/worker.ts` - Worker handlers
- [ ] `src/worker/index.ts` - Worker API

**Test Deliverables:**

- [ ] Unit tests for all modules (90%+ coverage)
- [ ] Integration tests with fixtures
- [ ] Performance tests
- [ ] Test fixtures from 52°North demo server

**Documentation Deliverables:**

- [ ] JSDoc on all public classes/methods/types
- [ ] README with installation + examples
- [ ] Type definitions (.d.ts files)
- [ ] Migration guide (if applicable)

**Quality Deliverables:**

- [ ] 0 TypeScript errors
- [ ] 0 ESLint errors
- [ ] Passes Prettier formatting
- [ ] Passes CI/CD checks
- [ ] PR approved by maintainers

### 10.3 Dependencies and Blockers

**External Dependencies:**

- camptocamp/ogc-client repository access (for PR)
- 52°North demo server availability (for integration testing)
- Maintainer availability for review

**Potential Blockers:**

- Binary encoding complexity (SWE Common) - may need extra time
- CQL2 filter implementation - spec still evolving
- Performance issues with 10K+ observations - may need optimization

**Mitigation:**

- Engage maintainers early (Week 1-2)
- Have backup plan for complex features (defer if needed)
- Profile early and often (Week 6-9)

---

## Appendix A: File Structure

```
src/
├── csapi/
│   ├── endpoint.ts              # 300 lines
│   ├── conformance.ts           # 150 lines
│   ├── collections.ts           # 200 lines
│   ├── model.ts                 # 800 lines (all types)
│   ├── url.ts                   # 400 lines (all URL builders)
│   ├── formats/
│   │   ├── geojson.ts          # 500 lines
│   │   ├── sensorml.ts         # 1,500 lines
│   │   ├── swe-common.ts       # 2,000 lines
│   │   ├── detector.ts         # 300 lines
│   │   └── validator.ts        # 600 lines
│   ├── resources/
│   │   ├── systems.ts          # 150 lines
│   │   ├── deployments.ts      # 150 lines
│   │   ├── procedures.ts       # 100 lines
│   │   ├── sampling-features.ts # 100 lines
│   │   ├── properties.ts       # 80 lines
│   │   ├── datastreams.ts      # 200 lines
│   │   ├── observations.ts     # 250 lines
│   │   ├── control-streams.ts  # 150 lines
│   │   └── commands.ts         # 200 lines
│   └── endpoint.spec.ts        # 200 lines (integration tests)
├── worker/
│   ├── worker.ts               # 200 lines (add CSAPI handlers)
│   └── index.ts                # 200 lines (add CSAPI exports)
└── index.ts                     # 50 lines (add CSAPI exports)

Total LOC: ~9,880 lines
Test LOC: ~1,000 lines (separate)
```

## Appendix B: Type Definitions Example

```typescript
// Complete type definitions for Systems resource
export interface SystemFeature extends Feature {
  id: string;
  type: 'Feature';
  geometry?: Geometry;
  properties: {
    uid: string;
    name: string;
    description?: string;
    featureType: string;
    samplingFeatures?: Link[];
    validTime?: TemporalExtent;
    links?: Link[];
    // SensorML properties (when format is SensorML)
    definition?: string;
    uniqueId?: string;
    identification?: IdentifierList;
    classification?: ClassifierList;
    characteristics?: CharacteristicList;
    capabilities?: CapabilityList;
    contacts?: ContactList;
    documentation?: DocumentList;
    position?: PositionType;
    components?: ComponentList;
  };
  links?: Link[];
}

export interface SystemCollection extends FeatureCollection {
  type: 'FeatureCollection';
  features: SystemFeature[];
  links?: Link[];
  numberMatched?: number;
  numberReturned?: number;
}

export interface SystemInput {
  geometry?: Geometry;
  properties: {
    name: string;
    description?: string;
    featureType: string;
    validTime?: TemporalExtent;
    // ... additional properties
  };
}
```

---

## Appendix C: Success Metrics Summary

| Metric                 | Target           | Measurement             |
| ---------------------- | ---------------- | ----------------------- |
| Test Coverage          | 90%+             | Jest coverage report    |
| Lines of Code          | ~10,000          | cloc tool               |
| TypeScript Errors      | 0                | tsc --noEmit            |
| ESLint Errors          | 0                | eslint .                |
| Bundle Size            | < 150KB (gzip)   | webpack-bundle-analyzer |
| Endpoint Init Time     | < 2s             | Performance test        |
| 10K Observation Parse  | < 5s             | Performance test        |
| JSDoc Coverage         | 100% public APIs | Manual review           |
| Integration Tests Pass | 100%             | CI/CD                   |
| PR Approval            | Yes              | GitHub PR               |

---

## Document Change Log

| Version | Date       | Changes                          |
| ------- | ---------- | -------------------------------- |
| 1.0     | 2026-01-31 | Initial functional specification |

---

**End of Functional Specification**
