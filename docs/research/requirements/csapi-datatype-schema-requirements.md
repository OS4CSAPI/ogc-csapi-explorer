# CSAPI Data Type and Schema Requirements

**Document:** Section 8 - Type System Requirements and Scope Definition  
**Source:** OpenAPI schemas from OGC API – Connected Systems Part 1 & Part 2  
**Date:** 2026-01-31  
**Status:** Complete

---

## Executive Summary

This document defines the TypeScript type system requirements for the ogc-client CSAPI library based on comprehensive analysis of the OpenAPI 3.1 schema definitions from both Part 1 (Feature Resources) and Part 2 (Dynamic Data). The analysis covers 100+ schema definitions spanning resource types, data components, encodings, geometries, and supporting structures.

**Key Findings:**

- **50+ Resource and Data Types** requiring TypeScript interfaces
- **Hierarchical Type System** with inheritance (System → AbstractProcess → DescribedObject)
- **Union Types** for polymorphic structures (AnyComponent, geometryGeoJSON, etc.)
- **Generic Types** needed for collections, responses, and links
- **30+ SWE Common Data Components** with complex composition patterns
- **Multiple Encoding Formats** (JSON, SWE Common JSON/Text/Binary, GeoJSON, SensorML)
- **Strict Type Safety** for schema validation, query parameters, and CRUD operations

---

## Table of Contents

1. [Type System Architecture](#1-type-system-architecture)
2. [Core Resource Types](#2-core-resource-types)
3. [Dynamic Data Types](#3-dynamic-data-types)
4. [SWE Common Data Component Types](#4-swe-common-data-component-types)
5. [Geometry Types](#5-geometry-types)
6. [SensorML Process Types](#6-sensorml-process-types)
7. [Collection and Pagination Types](#7-collection-and-pagination-types)
8. [Query Parameter Types](#8-query-parameter-types)
9. [Request and Response Types](#9-request-and-response-types)
10. [Generic and Utility Types](#10-generic-and-utility-types)
11. [Type Scope and Balance](#11-type-scope-and-balance)
12. [Implementation Strategy](#12-implementation-strategy)

---

## 1. Type System Architecture

### 1.1 Design Principles

**Principle 1: Type Safety Without Runtime Overhead**

- All types compile away - zero runtime cost
- Catch errors at compile time, not production
- Autocomplete and IntelliSense for developer experience

**Principle 2: Follow OpenAPI Schema Exactly**

- One-to-one mapping from OpenAPI schemas to TypeScript interfaces
- Preserve required/optional distinctions
- Honor enum values, format constraints, and validation rules

**Principle 3: Composition Over Duplication**

- Use extends for inheritance relationships
- Use union types (|) for oneOf schemas
- Use intersection types (&) for allOf schemas
- Extract common patterns into reusable utility types

**Principle 4: Progressive Disclosure**

- Export simple types for common use cases
- Provide detailed types for advanced scenarios
- Allow users to opt into stricter types when needed

**Principle 5: Flexibility at Boundaries**

- Strict types for client library internals
- Flexible types for user-provided data (accept broader input types)
- Narrow types for library outputs (guarantee specific return types)

### 1.2 Type Hierarchy Overview

```
Resource Types (10)
├── Part 1 Feature Resources (5)
│   ├── System
│   ├── Deployment
│   ├── Procedure
│   ├── SamplingFeature
│   └── Property
└── Part 2 Dynamic Data (5)
    ├── DataStream
    ├── Observation
    ├── ControlStream
    ├── Command
    └── SystemEvent

Data Component Types (30+)
├── Simple Components (11)
│   ├── Boolean, Count, Quantity, Time, Category, Text
│   └── CountRange, QuantityRange, TimeRange, CategoryRange, Geometry
├── Aggregate Components (6)
│   ├── DataRecord, Vector, DataArray, Matrix, DataChoice
│   └── ObservableProperty
└── Metadata Components (10+)
    ├── UnitReference, NilValues, Constraints
    └── Encoding (JSON, Text, Binary, XML)

Supporting Types (50+)
├── GeoJSON Geometries (8)
├── SensorML Processes (4)
├── Links and References (3)
├── Collections and Pagination (5)
├── Time Types (4)
├── Query Parameters (20+)
└── Request/Response Wrappers (10+)
```

---

## 2. Core Resource Types

### 2.1 Part 1 Feature Resource Interfaces

#### 2.1.1 System

**Base Interface:**

```typescript
interface System extends GeoJSONFeature {
  type: 'Feature';
  geometry: Point | null;
  properties: SystemProperties;
  links?: Link[];
}

interface SystemProperties {
  // Required
  featureType: SystemType;
  uid: string; // URI format
  name: string; // min length: 1

  // Optional
  description?: string;
  assetType?: AssetType;
  validTime?: TimePeriod;

  // Associations (links to related resources)
  'systemKind@link'?: Link;
  'subsystems@link'?: Link;
  'deployments@link'?: Link;
  'datastreams@link'?: Link;
  'controlstreams@link'?: Link;
  'samplingFeatures@link'?: Link;
  'procedures@link'?: Link;
}

type SystemType =
  | 'http://www.w3.org/ns/sosa/Sensor'
  | 'sosa:Sensor'
  | 'http://www.w3.org/ns/sosa/Actuator'
  | 'sosa:Actuator'
  | 'http://www.w3.org/ns/sosa/Platform'
  | 'sosa:Platform'
  | 'http://www.w3.org/ns/sosa/Sampler'
  | 'sosa:Sampler'
  | 'http://www.w3.org/ns/sosa/System'
  | 'sosa:System';

type AssetType =
  | 'Equipment'
  | 'Human'
  | 'LivingThing'
  | 'Simulation'
  | 'Process'
  | 'Group'
  | 'Other';
```

**SensorML Representation:**

```typescript
interface SystemSensorML extends DescribedObject {
  type:
    | 'SimpleProcess'
    | 'AggregateProcess'
    | 'PhysicalComponent'
    | 'PhysicalSystem';
  uniqueId: string; // URI
  label: string;
  description?: string;
  validTime?: TimePeriod;

  // Process-specific
  definition?: string; // URI
  typeOf?: Link;
  configuration?: Settings;
  featuresOfInterest?: FeatureList;
  inputs?: InputList;
  outputs?: OutputList;
  parameters?: ParameterList;
  modes?: Mode[];

  // Physical-specific (PhysicalComponent, PhysicalSystem)
  attachedTo?: Link;
  localReferenceFrames?: SpatialFrame[];
  localTimeFrames?: TemporalFrame[];
  position?: Position;

  // Aggregate-specific (AggregateProcess, PhysicalSystem)
  components?: ComponentList;
  connections?: ConnectionList;
}
```

**Client Type Strategy:**

- **Accept:** `System | SystemSensorML` (union of both representations)
- **Return:** Format-specific based on Accept header negotiation
- **Query:** Both representations queryable, format indicated in response

#### 2.1.2 Deployment

```typescript
interface Deployment extends GeoJSONFeature {
  type: 'Feature';
  geometry: Geometry | null; // Any GeoJSON geometry or null
  properties: DeploymentProperties;
  links?: Link[];
}

interface DeploymentProperties {
  // Required
  featureType: DeploymentType;
  uid: string;
  name: string;
  validTime: TimePeriod; // Required for deployments

  // Optional
  description?: string;
  deploymentType?: string; // URI

  // Associations
  'deployedSystems@link'?: Link[];
  'subdeployments@link'?: Link;
  'platform@link'?: Link;
  'featuresOfInterest@link'?: Link[];
  'samplingFeatures@link'?: Link[];
  'datastreams@link'?: Link;
  'controlstreams@link'?: Link;
}

type DeploymentType =
  | 'http://www.w3.org/ns/sosa/Deployment'
  | 'sosa:Deployment';
```

#### 2.1.3 Procedure

```typescript
interface Procedure extends GeoJSONFeature {
  type: 'Feature';
  geometry: null; // Procedures have no geometry
  properties: ProcedureProperties;
  links?: Link[];
}

interface ProcedureProperties {
  // Required
  featureType: ProcedureType;
  uid: string;
  name: string;

  // Optional
  description?: string;

  // Associations
  'implementingSystems@link'?: Link[];
}

type ProcedureType =
  | SystemType // Includes all system types (datasheets)
  | 'http://www.w3.org/ns/sosa/Procedure'
  | 'sosa:Procedure'
  | 'http://www.w3.org/ns/sosa/ObservingProcedure'
  | 'sosa:ObservingProcedure'
  | 'http://www.w3.org/ns/sosa/SamplingProcedure'
  | 'sosa:SamplingProcedure'
  | 'http://www.w3.org/ns/sosa/ActuatingProcedure'
  | 'sosa:ActuatingProcedure';
```

#### 2.1.4 SamplingFeature

```typescript
interface SamplingFeature extends GeoJSONFeature {
  type: 'Feature';
  geometry: Geometry | null;
  properties: SamplingFeatureProperties;
  links?: Link[];
}

interface SamplingFeatureProperties {
  // Required
  featureType: string; // URI - type of sampling feature
  uid: string;
  name: string;

  // Optional
  description?: string;
  validTime?: TimePeriod;
  samplingTime?: string; // date-time
  materialClass?: string; // URI

  // Associations
  'sampledFeature@link': Link; // Required
  'parentSystem@link': Link; // Required
  'sampleOf@link'?: Link[]; // Sub-sampling
  'datastreams@link'?: Link;
  'controlstreams@link'?: Link;
}
```

#### 2.1.5 Property

```typescript
interface PropertyResource {
  id: string;
  uniqueId: string; // URI
  label: string;
  description?: string;
  baseProperty: string; // URI - required
  objectType?: string; // URI
  statistic?: string; // URI
  qualifiers?: SimpleComponent[];
  links?: Link[];
}

// Properties are NOT GeoJSON features (non-spatial)
```

### 2.2 Type Discriminators

**Purpose:** Enable type guards and runtime type narrowing

```typescript
// Type guard example
function isSystem(resource: Resource): resource is System {
  return (
    'geometry' in resource &&
    'properties' in resource &&
    'featureType' in resource.properties &&
    resource.properties.featureType.includes('System')
  );
}

// Resource union type
type Part1Resource =
  | System
  | Deployment
  | Procedure
  | SamplingFeature
  | PropertyResource;

// Generic feature type
interface Resource {
  id: string;
  links?: Link[];
}
```

---

## 3. Dynamic Data Types

### 3.1 DataStream

```typescript
interface DataStream {
  // Identity (required, read-only)
  id: string;
  name: string;
  formats: string[]; // Available encoding formats

  // Metadata (optional)
  description?: string;
  validTime?: TimePeriod;

  // Associations (required, read-only)
  'system@link': Link;

  // Associations (optional, read-only)
  outputName?: string;
  'procedure@link'?: Link;
  'deployment@link'?: Link;
  'featureOfInterest@link'?: Link;
  'samplingFeature@link'?: Link;

  // Observed properties
  observedProperties?: ObservedProperty[] | null;

  // Temporal extent (read-only)
  phenomenonTime?: TimePeriod | null;
  phenomenonTimeInterval?: string; // ISO 8601 duration
  resultTime?: TimePeriod | null;
  resultTimeInterval?: string; // ISO 8601 duration

  // Classification
  type?: 'status' | 'observation';
  resultType?: ResultType | null;

  // Live streaming
  live?: boolean | null;

  // Schema (write-only for create/update)
  schema?: ObservationSchema;
}

interface ObservedProperty {
  definition: string; // URI
  label?: string;
  description?: string;
}

type ResultType =
  | 'measure' // Single quantity
  | 'vector' // Array of quantities
  | 'record' // Structured data
  | 'coverage' // Spatial/temporal coverage
  | 'complex'; // Any other type
```

### 3.2 Observation

```typescript
interface Observation {
  // Identity (read-only)
  id?: string;

  // Required temporal properties
  phenomenonTime: string | TimePeriod; // When observed
  resultTime: string; // date-time - When result produced

  // Optional references
  'procedure@id'?: string;
  'foi@id'?: string;

  // Optional parameters
  parameters?: Record<string, any>;

  // Result (varies by type)
  result: ObservationResult;
}

// Type-specific observation interfaces
interface MeasureObservation extends Observation {
  result: number;
}

interface VectorObservation extends Observation {
  result: number[];
}

interface RecordObservation extends Observation {
  result: Record<string, any>;
}

interface ComplexObservation extends Observation {
  result: any;
}

type ObservationResult = number | number[] | Record<string, any> | any;

// Collection type
interface ObservationCollection {
  items: Observation[];
  links?: Link[];
}
```

### 3.3 Observation Schema

```typescript
// Union of all observation schema types
type ObservationSchema =
  | ObservationSchemaJson
  | ObservationSchemaSwe
  | ObservationSchemaProtobuf
  | ObservationSchemaCustom;

interface ObservationSchemaJson {
  obsFormat: 'application/json';
  parametersSchema?: DataRecord;
  resultSchema: DataComponent; // Required
}

interface ObservationSchemaSwe {
  obsFormat:
    | 'application/swe+json'
    | 'application/swe+binary'
    | 'application/swe+text';
  observationStructure: DataRecord; // Must contain: phenomenonTime, resultTime, foi, result
  observationEncoding?: Encoding;
}

interface ObservationSchemaProtobuf {
  obsFormat: 'application/protobuf';
  messageSchema: string; // Protocol Buffers schema
}

interface ObservationSchemaCustom {
  obsFormat: string; // Custom media type
  schemaEncoding: string;
  schema: string;
}
```

### 3.4 ControlStream

```typescript
interface ControlStream {
  // Identity (required, read-only)
  id: string;
  name: string;
  formats: string[];

  // Metadata
  description?: string;
  validTime?: TimePeriod;

  // Associations (required, read-only)
  'system@link': Link;

  // Associations (optional, read-only)
  inputName?: string;
  'procedure@link'?: Link;
  'deployment@link'?: Link;
  'featureOfInterest@link'?: Link;
  'samplingFeature@link'?: Link;

  // Controlled properties
  controlledProperties?: ControlledProperty[] | null;

  // Temporal extent (read-only)
  issueTime?: TimePeriod | null;
  executionTime?: TimePeriod | null;

  // Live control
  live?: boolean | null;

  // Schema (write-only)
  schema?: CommandSchema;
}

interface ControlledProperty {
  definition: string; // URI
  label?: string;
  description?: string;
}
```

### 3.5 Command

```typescript
interface Command {
  // Identity (read-only)
  id?: string;

  // Required temporal properties
  issueTime: string; // date-time
  executionTime: string | TimePeriod; // When to execute

  // Optional metadata
  sender?: string;

  // Parameters (required)
  params: Record<string, any> | any[];
}

interface CommandCollection {
  items: Command[];
  links?: Link[];
}
```

### 3.6 Command Schema

```typescript
type CommandSchema =
  | CommandSchemaJson
  | CommandSchemaSwe
  | CommandSchemaProtobuf
  | CommandSchemaCustom;

interface CommandSchemaJson {
  cmdFormat: 'application/json';
  paramsSchema: DataComponent; // Required
}

interface CommandSchemaSwe {
  cmdFormat:
    | 'application/swe+json'
    | 'application/swe+binary'
    | 'application/swe+text';
  commandStructure: DataRecord; // Must contain: issueTime, executionTime, params
  commandEncoding?: Encoding;
}

interface CommandSchemaProtobuf {
  cmdFormat: 'application/protobuf';
  messageSchema: string;
}

interface CommandSchemaCustom {
  cmdFormat: string;
  schemaEncoding: string;
  schema: string;
}
```

### 3.7 CommandStatus

```typescript
type CommandStatusCode =
  | 'pending'
  | 'queued'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'canceled'
  | 'rejected';

interface CommandStatus {
  // Identity (read-only)
  id?: string;

  // Required
  reportTime: string; // date-time
  statusCode: CommandStatusCode;

  // Optional
  executionTime?: string; // date-time - actual execution time
  percentCompletion?: number; // 0-100
  message?: string;
  updatedParams?: Record<string, any>;
}

interface CommandStatusCollection {
  items: CommandStatus[];
  links?: Link[];
}
```

### 3.8 CommandResult

```typescript
interface CommandResult {
  // Identity (read-only)
  id?: string;

  // Required
  resultTime: string; // date-time
  result: CommandResultData;
}

// Result can be simple or complex
type CommandResultData = SimpleComponent | DataComponent;

interface CommandResultCollection {
  items: CommandResult[];
  links?: Link[];
}
```

### 3.9 SystemEvent

```typescript
interface SystemEvent extends Event {
  // Identity (read-only)
  id?: string;

  // Required (from Event)
  label: string;
  time: string | TimePeriod; // Event occurrence time

  // Required (SystemEvent-specific)
  reportTime: string; // date-time
  relatedSystems: Link[]; // Affected systems

  // Optional (from Event)
  definition?: string; // URI
  identifiers?: Term[];
  classifiers?: Term[];
  contacts?: ResponsibleParty[];
  documentation?: Document[];
  properties?: Property[];
  configuration?: Settings;
}

interface SystemEventCollection {
  items: SystemEvent[];
  links?: Link[];
}
```

---

## 4. SWE Common Data Component Types

### 4.1 Component Type Hierarchy

```typescript
// Base abstract types
interface AbstractSWE {
  id?: string; // Local URI fragment
}

interface AbstractSweIdentifiable extends AbstractSWE {
  label?: string;
  description?: string;
}

interface AbstractDataComponent extends AbstractSweIdentifiable {
  type: string; // Component type discriminator
  updatable?: boolean; // Default: false
  optional?: boolean; // Default: false
  definition?: string; // URI - semantic property
}

interface AbstractSimpleComponent extends AbstractDataComponent {
  referenceFrame?: string; // URI
  axisID?: string;
  nilValues?: NilValue[];
  constraint?: Constraint;
  value?: any; // Inline value
}
```

### 4.2 Scalar Components

```typescript
interface BooleanComponent extends AbstractSimpleComponent {
  type: 'Boolean';
  definition: string; // Required
  label: string; // Required
  value?: boolean;
}

interface CountComponent extends AbstractSimpleComponent {
  type: 'Count';
  definition: string;
  label: string;
  value?: number; // Integer
  constraint?: AllowedValues;
  nilValues?: NilValuesInteger[];
}

interface QuantityComponent extends AbstractSimpleComponent {
  type: 'Quantity';
  definition: string;
  label: string;
  uom: UnitReference; // Required
  value?: number | 'NaN' | 'Infinity' | '+Infinity' | '-Infinity';
  constraint?: AllowedValues;
  nilValues?: NilValuesNumber[];
}

interface TimeComponent extends AbstractSimpleComponent {
  type: 'Time';
  definition: string;
  label: string;
  uom: UnitReference; // Required
  referenceTime?: string; // date-time - epoch
  localFrame?: string; // URI
  value?: string | number; // ISO date-time or numeric
  constraint?: AllowedTimes;
  nilValues?: NilValuesTime[];
}

interface CategoryComponent extends AbstractSimpleComponent {
  type: 'Category';
  definition: string;
  label: string;
  codeSpace?: string; // URI - dictionary
  value?: string; // Token
  constraint?: AllowedTokens;
  nilValues?: NilValuesText[];
}

interface TextComponent extends AbstractSimpleComponent {
  type: 'Text';
  definition: string;
  label: string;
  value?: string;
  constraint?: AllowedTokens;
  nilValues?: NilValuesText[];
}
```

### 4.3 Range Components

```typescript
interface CountRangeComponent extends AbstractSimpleComponent {
  type: 'CountRange';
  definition: string;
  label: string;
  value?: [number, number]; // [min, max]
}

interface QuantityRangeComponent extends AbstractSimpleComponent {
  type: 'QuantityRange';
  definition: string;
  label: string;
  uom: UnitReference; // Required
  value?: [number, number];
  constraint?: AllowedValues;
  nilValues?: NilValuesNumber[];
}

interface TimeRangeComponent extends AbstractSimpleComponent {
  type: 'TimeRange';
  definition: string;
  label: string;
  uom: UnitReference; // Required
  referenceTime?: string;
  localFrame?: string;
  value?: [string | number, string | number];
  constraint?: AllowedTimes;
  nilValues?: NilValuesTime[];
}

interface CategoryRangeComponent extends AbstractSimpleComponent {
  type: 'CategoryRange';
  definition: string;
  label: string;
  codeSpace?: string; // URI
  value?: [string, string];
}
```

### 4.4 Aggregate Components

```typescript
interface DataRecordComponent extends AbstractDataComponent {
  type: 'DataRecord';
  fields: Field[]; // Min: 1
}

interface Field {
  name: string; // NameToken pattern: ^[A-Za-z][A-Za-z0-9_\-]*$
  component: DataComponent; // Any component type
}

interface VectorComponent extends AbstractDataComponent {
  type: 'Vector';
  definition: string; // Required
  label: string; // Required
  referenceFrame: string; // URI - required
  localFrame?: string; // URI
  coordinates: (CountComponent | QuantityComponent | TimeComponent)[]; // Required
}

interface DataArrayComponent extends AbstractDataComponent {
  type: 'DataArray';
  elementCount?: ElementCount;
  elementType: DataComponent; // Required
  encoding?: Encoding;
  values?: EncodedValues;
}

interface MatrixComponent extends DataArrayComponent {
  type: 'Matrix';
  referenceFrame?: string; // URI
  localFrame?: string; // URI
}

interface DataChoiceComponent extends AbstractDataComponent {
  type: 'DataChoice';
  choiceValue?: CategoryComponent;
  items: Field[]; // Required, min: 1
}

interface GeometryComponent extends AbstractSimpleComponent {
  type: 'Geometry';
  definition: string; // Required
  label: string; // Required
  srs: string; // URI - required
  constraint?: {
    geomTypes?: (
      | 'Point'
      | 'MultiPoint'
      | 'LineString'
      | 'MultiLineString'
      | 'Polygon'
      | 'MultiPolygon'
      | 'GeometryCollection'
    )[];
  };
  nilValues?: NilValuesText[];
  value?: GeoJSONGeometry;
}
```

### 4.5 Union Types for Polymorphism

```typescript
// Simple components (no aggregation)
type SimpleComponent =
  | BooleanComponent
  | CountComponent
  | QuantityComponent
  | TimeComponent
  | CategoryComponent
  | TextComponent
  | CountRangeComponent
  | QuantityRangeComponent
  | TimeRangeComponent
  | CategoryRangeComponent;

// Any data component
type DataComponent =
  | SimpleComponent
  | DataRecordComponent
  | VectorComponent
  | DataArrayComponent
  | MatrixComponent
  | DataChoiceComponent
  | GeometryComponent
  | ObservablePropertyComponent;

// Observable property (used in inputs/outputs)
interface ObservablePropertyComponent {
  type: 'ObservableProperty';
  definition: string; // URI - required
}
```

### 4.6 Constraints

```typescript
interface AllowedValues {
  type: 'AllowedValues';
  values?: (number | 'NaN' | 'Infinity' | '+Infinity' | '-Infinity')[]; // Min: 1
  intervals?: [number, number][]; // Inclusive ranges
  significantFigures?: number; // 1-40
}

interface AllowedTimes {
  type: 'AllowedTimes';
  values?: (string | number | 'NaN' | 'Infinity' | '+Infinity' | '-Infinity')[];
  intervals?: [string | number, string | number][];
  significantFigures?: number;
}

interface AllowedTokens {
  type: 'AllowedTokens';
  values?: string[]; // Enumerated values
  pattern?: string; // Regex pattern
}

type Constraint = AllowedValues | AllowedTimes | AllowedTokens;
```

### 4.7 Nil Values

```typescript
interface NilValuesInteger {
  reason: string; // URI
  value: number; // Integer
}

interface NilValuesNumber {
  reason: string; // URI
  value: number | 'NaN' | 'Infinity' | '+Infinity' | '-Infinity';
}

interface NilValuesTime {
  reason: string; // URI
  value: string | number | 'NaN' | 'Infinity' | '+Infinity' | '-Infinity';
}

interface NilValuesText {
  reason: string; // URI
  value: string;
}

type NilValue =
  | NilValuesInteger
  | NilValuesNumber
  | NilValuesTime
  | NilValuesText;
```

### 4.8 Unit of Measure

```typescript
interface UnitReference {
  label?: string; // Human readable
  symbol?: string; // Unit symbol (e.g., "m/s", "°C")
  code?: string; // UCUM code
  href?: string; // URI reference
  // Required: code OR href
}
```

### 4.9 Encodings

```typescript
type Encoding = BinaryEncoding | TextEncoding | XMLEncoding | JSONEncoding;

interface BinaryEncoding {
  type: 'BinaryEncoding';
  byteOrder: 'bigEndian' | 'littleEndian'; // Required
  byteEncoding: 'base64' | 'raw'; // Required
  byteLength?: number;
  members: (ComponentMember | BlockMember)[]; // Required, min: 1
}

interface ComponentMember {
  type: 'Component';
  encryption?: string; // URI
  significantBits?: number;
  bitLength?: number;
  byteLength?: number;
  dataType: string; // URI - required
  ref: string; // Required - component reference
}

interface BlockMember {
  type: 'Block';
  compression?: string; // URI
  encryption?: string; // URI
  'paddingBytes-before'?: number;
  'paddingBytes-after'?: number;
  byteLength?: number;
  ref: string; // Required - aggregate component reference
}

interface TextEncoding {
  type: 'TextEncoding';
  collapseWhiteSpaces?: boolean;
  decimalSeparator?: string;
  tokenSeparator: string; // Required
  blockSeparator: string; // Required
}

interface XMLEncoding {
  type: 'XMLEncoding';
  namespace?: string; // URI
}

interface JSONEncoding {
  type: 'JSONEncoding';
  recordsAsArrays?: boolean; // Default: false
  vectorsAsArrays?: boolean; // Default: false
}
```

---

## 5. Geometry Types

### 5.1 GeoJSON Geometry Types

```typescript
// Base GeoJSON geometry
interface GeoJSONGeometry {
  type: string;
  coordinates?: any;
  geometries?: GeoJSONGeometry[];
}

// Specific geometry types
interface PointGeoJSON {
  type: 'Point';
  coordinates: [number, number] | [number, number, number]; // [lon, lat] or [lon, lat, elevation]
}

interface MultiPointGeoJSON {
  type: 'MultiPoint';
  coordinates: [number, number][] | [number, number, number][];
}

interface LineStringGeoJSON {
  type: 'LineString';
  coordinates: [number, number][] | [number, number, number][]; // Min: 2 points
}

interface MultiLineStringGeoJSON {
  type: 'MultiLineString';
  coordinates: ([number, number][] | [number, number, number][])[];
}

interface PolygonGeoJSON {
  type: 'Polygon';
  coordinates: ([number, number][] | [number, number, number][])[];
  // First array is exterior ring, subsequent arrays are holes
  // Each ring: min 4 points, first and last must be identical
}

interface MultiPolygonGeoJSON {
  type: 'MultiPolygon';
  coordinates: ([number, number][] | [number, number, number][])[][];
}

interface GeometryCollectionGeoJSON {
  type: 'GeometryCollection';
  geometries: Geometry[];
}

// Union type for any geometry
type Geometry =
  | PointGeoJSON
  | MultiPointGeoJSON
  | LineStringGeoJSON
  | MultiLineStringGeoJSON
  | PolygonGeoJSON
  | MultiPolygonGeoJSON
  | GeometryCollectionGeoJSON;
```

### 5.2 GeoJSON Feature Types

```typescript
interface GeoJSONFeature {
  type: 'Feature';
  geometry: Geometry | null;
  properties: Record<string, any> | null;
  id?: string | number;
  links?: Link[];
}

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
  links?: Link[];
  timeStamp?: string; // date-time
  numberMatched?: number; // Min: 0
  numberReturned?: number; // Min: 0
}
```

### 5.3 Position and Pose Types

```typescript
// Position representations
type Position =
  | PositionText
  | PositionPoint
  | PositionPose
  | PositionProcess
  | PositionDataStream
  | PositionVector // Deprecated
  | PositionDataRecord // Deprecated
  | PositionTrajectory; // Deprecated

interface PositionText {
  type: 'Text';
  value: string; // Textual description
}

interface PositionPoint {
  type: 'Point';
  coordinates: [number, number] | [number, number, number];
}

interface PositionPose {
  pose: Pose;
}

interface PositionProcess {
  process: AbstractProcess; // Dynamic position
}

interface PositionDataStream {
  'datastream@link': Link;
}

// GeoPose representations
type Pose =
  | GeoPoseYPR
  | GeoPoseQuaternion
  | RelativePoseYPR
  | RelativePoseQuaternion;

interface GeoPoseYPR {
  type: 'GeoPose';
  ltpReferenceFrame?: string; // URI
  position: PositionGeo;
  angles: AnglesYPR;
}

interface GeoPoseQuaternion {
  type: 'GeoPose';
  ltpReferenceFrame?: string;
  position: PositionGeo;
  quaternion: Quaternion;
}

interface RelativePoseYPR {
  type: 'RelativePose';
  referenceFrame: string; // URI - required
  position: PositionXYZ;
  angles: AnglesYPR;
}

interface RelativePoseQuaternion {
  type: 'RelativePose';
  referenceFrame: string; // Required
  position: PositionXYZ;
  quaternion: Quaternion;
}

interface PositionGeo {
  lat: number; // WGS84 latitude (degrees)
  lon: number; // WGS84 longitude (degrees)
  h: number; // Height above WGS84 ellipsoid (meters)
}

interface PositionXYZ {
  x: number; // meters
  y: number; // meters
  z: number; // meters
}

interface AnglesYPR {
  yaw: number; // degrees
  pitch: number; // degrees
  roll: number; // degrees
}

interface Quaternion {
  x: number;
  y: number;
  z: number;
  w: number;
}
```

---

## 6. SensorML Process Types

### 6.1 Base Process Hierarchy

```typescript
interface DescribedObject {
  type: string; // Discriminator
  id?: string; // Local ID
  uniqueId: string; // URI - required
  label: string; // Required
  description?: string;
  lang?: string; // Language code
  keywords?: string[];
  identifiers?: Term[];
  classifiers?: Term[];
  validTime?: TimePeriod;
  securityConstraints?: any[];
  legalConstraints?: LegalConstraint[];
  characteristics?: CharacteristicList[];
  capabilities?: CapabilityList[];
  contacts?: (ResponsibleParty | Link)[];
  documentation?: Document[];
  history?: Event[];
}

interface AbstractProcess extends DescribedObject {
  definition?: string; // URI - process type
  typeOf?: Link; // Base process reference
  configuration?: Settings;
  featuresOfInterest?: FeatureList;
  inputs?: InputList;
  outputs?: OutputList;
  parameters?: ParameterList;
  modes?: Mode[];
}

interface SimpleProcess extends AbstractProcess {
  type: 'SimpleProcess';
  method?: ProcessMethod;
}

interface AggregateProcess extends AbstractProcess {
  type: 'AggregateProcess';
  components: ComponentList; // Required
  connections?: ConnectionList;
}

interface AbstractPhysicalProcess extends AbstractProcess {
  attachedTo?: Link;
  localReferenceFrames?: SpatialFrame[];
  localTimeFrames?: TemporalFrame[];
  position?: Position;
}

interface PhysicalComponent extends AbstractPhysicalProcess {
  type: 'PhysicalComponent';
  method?: ProcessMethod;
}

interface PhysicalSystem extends AbstractPhysicalProcess {
  type: 'PhysicalSystem';
  components: ComponentList; // Required
  connections?: ConnectionList;
}
```

### 6.2 Supporting Process Types

```typescript
interface Term {
  definition?: string; // URI
  label: string; // Required
  codeSpace?: string; // URI
  value: string; // Required
}

interface ResponsibleParty {
  individualName?: string;
  organisationName?: string;
  positionName?: string;
  contactInfo?: Contact;
  role: string; // URI - required
  // Required: individualName OR organisationName
}

interface Contact {
  phone?: Phone;
  address?: Address;
  website?: string;
  hoursOfService?: string;
  contactInstructions?: string;
}

interface Phone {
  voice?: string[];
  facsimile?: string[];
}

interface Address {
  deliveryPoint?: string[];
  city?: string;
  administrativeArea?: string;
  postalCode?: string;
  country?: string;
  electronicMailAddress?: string[]; // Email format
}

interface Document {
  role?: string; // URI
  name: string; // Required
  description?: string;
  link: Link; // Required
}

interface Event {
  definition?: string; // URI
  identifiers?: Term[];
  classifiers?: Term[];
  contacts?: ResponsibleParty[];
  documentation?: Document[];
  time: string | TimePeriod; // Required
  properties?: Property[];
  configuration?: Settings;
}

interface Settings {
  setValues?: SetValue[];
  setArrayValues?: SetArrayValue[];
  setModes?: SetMode[];
  setConstraints?: SetConstraint[];
  setStatus?: SetStatus[];
}

interface SetValue {
  ref: string; // PathRef - required
  value: number | string; // Required
}

interface SetArrayValue {
  ref: string; // Required
  value: any[]; // Required
}

interface SetMode {
  ref: string; // Required
  value: string; // Required
}

interface SetConstraint {
  ref: string; // Required
  // + constraint properties
}

interface SetStatus {
  ref: string; // Required
  value: 'enabled' | 'disabled' | 'required'; // Required
}

interface CharacteristicList {
  definition?: string; // URI
  conditions?: SimpleComponent[];
  characteristics: Property[]; // Required
}

interface CapabilityList {
  definition?: string; // URI
  conditions?: SimpleComponent[];
  capabilities: Property[]; // Required
}

interface LegalConstraint {
  useLimitations?: string[];
  accessConstraints?: string[]; // CodeListValue
  useConstraints?: string[]; // CodeListValue
  otherConstraints?: string[];
}

interface Mode extends DescribedObject {
  configuration?: Settings;
}

interface ProcessMethod {
  algorithm?: Algorithm;
  description?: string;
}

interface Algorithm {
  description?: string;
  implementation?: Link;
}

interface SpatialFrame {
  origin: string; // Required
  axes: Axis[]; // Required
}

interface Axis {
  name: string; // Required
  description: string; // Required
}

interface TemporalFrame {
  origin: string; // Required
}

// List types
type ComponentList = (
  | SimpleProcess
  | AggregateProcess
  | PhysicalComponent
  | PhysicalSystem
  | Link
)[];
type FeatureList = Link[];
type InputList = (Field | Link)[];
type OutputList = (Field | Link)[];
type ParameterList = (Field | Link)[];
type ConnectionList = Connection[];

interface Connection {
  source: string; // PathRef
  destination: string; // PathRef
}

// PathRef pattern: ^(components|inputs|outputs|parameters|modes)/([A-Za-z][A-Za-z0-9_\-]*/)*[A-Za-z][A-Za-z0-9_\-]*$
type PathRef = string;
```

---

## 7. Collection and Pagination Types

### 7.1 Collection Metadata

```typescript
interface Collection {
  // Required
  id: string;
  links: Link[]; // Min: 1

  // Optional metadata
  title?: string;
  description?: string;
  extent?: Extent;
  itemType?: string; // Default: "feature"
  featureType?: string; // For Part 1 feature resources
  crs?: string[]; // Supported CRS
}

interface Extent {
  spatial?: SpatialExtent;
  temporal?: TemporalExtent;
}

interface SpatialExtent {
  bbox: BBox[]; // Min: 1
  crs?:
    | 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
    | 'http://www.opengis.net/def/crs/OGC/0/CRS84h';
}

interface TemporalExtent {
  interval: TimeInterval[]; // Min: 1
  trs?: 'http://www.opengis.net/def/uom/ISO-8601/0/Gregorian';
}

type BBox =
  | [number, number, number, number]
  | [number, number, number, number, number, number];
// [minLon, minLat, maxLon, maxLat] or [minLon, minLat, minElevation, maxLon, maxLat, maxElevation]

type TimeInterval = [string | null, string | null]; // [start, end] - nullable for open intervals
```

### 7.2 Collection Response Types

```typescript
interface CollectionList {
  collections: Collection[];
  links?: Link[];
}

// Resource collection wrappers
interface SystemCollection {
  items: System[];
  links?: Link[];
  timeStamp?: string;
  numberMatched?: number;
  numberReturned?: number;
}

interface DeploymentCollection {
  items: Deployment[];
  links?: Link[];
  timeStamp?: string;
  numberMatched?: number;
  numberReturned?: number;
}

interface DataStreamCollection {
  items: DataStream[];
  links?: Link[];
}

// Generic collection type
interface ResourceCollection<T> {
  items: T[];
  links?: Link[];
  timeStamp?: string;
  numberMatched?: number;
  numberReturned?: number;
}
```

### 7.3 Pagination Types

```typescript
interface PaginationLinks {
  self: Link;
  next?: Link;
  prev?: Link;
  first?: Link;
  last?: Link;
}

interface PaginationParams {
  limit?: number; // 1-10000, default: 10
  offset?: number; // Default: 0
}

interface PageInfo {
  numberMatched?: number; // Total results
  numberReturned: number; // Results in this page
  offset?: number;
  limit?: number;
}
```

---

## 8. Query Parameter Types

### 8.1 Common Query Parameters

```typescript
interface CommonQueryParams {
  // Pagination
  limit?: number; // 1-10000
  offset?: number; // 0+

  // Temporal filters
  datetime?: string | [string, string]; // ISO 8601 instant or interval

  // Spatial filters
  bbox?: BBox;
  geom?: Geometry; // Intersects filter

  // Text search
  keyword?: string | string[];
  q?: string; // Full-text search
}
```

### 8.2 Part 1 Advanced Filtering Parameters

```typescript
interface SystemQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[]; // Local IDs or UIDs
  uid?: string | string[]; // Unique identifiers

  // Relationship filters
  parent?: string; // Parent system ID
  procedure?: string | string[]; // Implementing procedures
  foi?: string | string[]; // Features of interest (transitive)
  observedProperty?: string | string[]; // Via datastreams
  controlledProperty?: string | string[]; // Via controlstreams

  // Recursive queries
  recursive?: boolean; // Include nested subsystems
}

interface DeploymentQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];
  uid?: string | string[];

  // Relationship filters
  system?: string | string[]; // Deployed systems
  foi?: string | string[]; // Features of interest
  observedProperty?: string | string[];
  controlledProperty?: string | string[];

  // Recursive queries
  recursive?: boolean; // Include subdeployments
}

interface ProcedureQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];
  uid?: string | string[];
}

interface SamplingFeatureQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];
  uid?: string | string[];

  // Relationship filters
  parent?: string; // Parent system
  procedure?: string | string[];
  foi?: string | string[]; // Sampled features
  observedProperty?: string | string[];
  controlledProperty?: string | string[];
}

interface PropertyQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];
  uid?: string | string[];

  // Property-specific filters
  baseProperty?: string | string[]; // Base property URIs
  objectType?: string | string[]; // Object type URIs
}
```

### 8.3 Part 2 Advanced Filtering Parameters

```typescript
interface DataStreamQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];

  // Relationship filters
  system?: string | string[]; // Producer system
  procedure?: string | string[];
  deployment?: string | string[];
  foi?: string | string[]; // Feature of interest
  observedProperty?: string | string[]; // Observed properties

  // Temporal filters for observations
  phenomenonTime?: string | [string, string]; // Phenomenon time extent
  resultTime?: string | [string, string]; // Result time extent
}

interface ObservationQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];

  // Relationship filters
  datastream?: string; // Parent datastream ID
  foi?: string | string[];

  // Temporal filters
  phenomenonTime?: string | [string, string];
  resultTime?: string | [string, string];

  // Result filters (if Advanced Filtering conformance)
  resultValue?: number | [number, number]; // Value or range
}

interface ControlStreamQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];

  // Relationship filters
  system?: string | string[]; // Target system
  procedure?: string | string[];
  deployment?: string | string[];
  foi?: string | string[];
  controlledProperty?: string | string[];

  // Temporal filters for commands
  issueTime?: string | [string, string];
  executionTime?: string | [string, string];
}

interface CommandQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];

  // Relationship filters
  controlstream?: string; // Parent control stream ID

  // Temporal filters
  issueTime?: string | [string, string];
  executionTime?: string | [string, string];

  // Status filter
  status?: CommandStatusCode | CommandStatusCode[];
}

interface SystemEventQueryParams extends CommonQueryParams {
  // ID filters
  id?: string | string[];

  // Relationship filters
  system?: string | string[]; // Related systems

  // Temporal filter
  time?: string | [string, string]; // Event occurrence time
  reportTime?: string | [string, string]; // Report time

  // Classification filters
  type?: string | string[]; // Event type URIs
}
```

---

## 9. Request and Response Types

### 9.1 HTTP Request Types

```typescript
// GET requests - no body
type GetRequest = void;

// POST requests - create resources
interface CreateSystemRequest {
  body: System | System[];
  headers?: {
    'Content-Type': 'application/geo+json' | 'application/sml+json';
    Accept?: string;
  };
}

interface CreateDataStreamRequest {
  body: DataStream;
  headers?: {
    'Content-Type': 'application/json';
    Accept?: string;
  };
}

interface CreateObservationRequest {
  body: Observation | Observation[];
  headers?: {
    'Content-Type':
      | 'application/json'
      | 'application/swe+json'
      | 'application/swe+text'
      | 'application/swe+binary';
    Accept?: string;
  };
}

interface CreateCommandRequest {
  body: Command | Command[];
  headers?: {
    'Content-Type':
      | 'application/json'
      | 'application/swe+json'
      | 'application/swe+text'
      | 'application/swe+binary';
    Accept?: string;
  };
}

// PUT requests - replace resources
interface ReplaceResourceRequest<T> {
  body: T;
  headers?: {
    'Content-Type': string;
    Accept?: string;
  };
}

// PATCH requests - update resources
interface UpdateResourceRequest {
  body: Record<string, any>; // JSON Merge Patch (RFC 7396)
  headers?: {
    'Content-Type': 'application/merge-patch+json';
    Accept?: string;
  };
}

// DELETE requests - no body
interface DeleteRequest {
  params?: {
    cascade?: boolean; // Cascade delete nested resources
  };
}
```

### 9.2 HTTP Response Types

```typescript
interface SuccessResponse<T> {
  status: 200 | 201 | 204;
  data?: T;
  headers?: {
    Location?: string; // For 201 Created
    'Content-Type'?: string;
  };
}

interface ErrorResponse {
  status: 400 | 401 | 403 | 404 | 409 | 500 | 503;
  error: {
    code?: string;
    message: string;
    details?: any;
  };
}

// Specific response types
interface ListResponse<T> {
  status: 200;
  data: ResourceCollection<T>;
  headers: {
    'Content-Type': string;
  };
}

interface GetResponse<T> {
  status: 200;
  data: T;
  headers: {
    'Content-Type': string;
  };
}

interface CreateResponse {
  status: 201;
  data?: any;
  headers: {
    Location: string; // Canonical URL
    'Content-Type'?: string;
  };
}

interface UpdateResponse {
  status: 204;
}

interface DeleteResponse {
  status: 204;
}
```

---

## 10. Generic and Utility Types

### 10.1 Link Types

```typescript
interface Link {
  href: string; // Required
  rel?: string; // Relation type
  type?: string; // Media type
  hreflang?: string; // Language (pattern: ^([a-z]{2}(-[A-Z]{2})?)|x-default$)
  title?: string;
  uid?: string; // Target UID (URI)
  rt?: string; // Semantic type (RFC 6690, URI)
  if?: string; // Interface (RFC 6690, URI)
}

// Link relation types
type LinkRelation =
  | 'self'
  | 'canonical'
  | 'alternate'
  | 'collection'
  | 'item'
  | 'next'
  | 'prev'
  | 'first'
  | 'last'
  | 'create'
  | 'update'
  | 'delete'
  | 'conformance'
  | 'service-desc'
  | 'service-doc'
  | string; // Allow custom relations
```

### 10.2 Time Types

```typescript
type TimeInstant = string; // ISO 8601 date-time

type TimeInstantOrNow = TimeInstant | 'now';

type TimePeriod = [TimeInstantOrNow, TimeInstantOrNow];

// Query parameter time type
type DateTimeQuery =
  | TimeInstant // Single instant
  | TimePeriod // Time range
  | 'now' // Current time
  | 'latest' // Latest available
  | '../now' // Open start to now
  | 'now/..' // Now to open end
  | `${string}/${string}`; // ISO 8601 interval
```

### 10.3 Generic Resource Types

```typescript
// Generic resource with type parameter
interface Resource<TProperties = any> {
  id: string;
  properties: TProperties;
  links?: Link[];
}

// Generic feature with geometry
interface Feature<TProperties = any, TGeometry = Geometry>
  extends Resource<TProperties> {
  type: 'Feature';
  geometry: TGeometry | null;
}

// Generic collection
interface Collection<T> {
  items: T[];
  links?: Link[];
}

// Generic response with pagination
interface PaginatedResponse<T> extends Collection<T> {
  timeStamp?: string;
  numberMatched?: number;
  numberReturned?: number;
}
```

### 10.4 Conditional Types for CRUD Operations

```typescript
// Properties that are read-only (set by server)
type ReadOnlyProps<T> = {
  readonly [K in keyof T]?: T[K];
};

// Properties for create requests (exclude read-only)
type CreateProps<T> = Omit<T, 'id' | 'links'>;

// Properties for update requests (all optional)
type UpdateProps<T> = Partial<Omit<T, 'id'>>;

// Properties for replace requests (required minus ID)
type ReplaceProps<T> = Omit<T, 'id'>;
```

### 10.5 Type Guards

```typescript
// Resource type guards
function isSystem(resource: any): resource is System {
  return (
    resource?.type === 'Feature' &&
    resource?.properties?.featureType?.includes('System')
  );
}

function isDataStream(resource: any): resource is DataStream {
  return (
    typeof resource?.id === 'string' &&
    Array.isArray(resource?.formats) &&
    'system@link' in resource
  );
}

function isObservation(resource: any): resource is Observation {
  return (
    typeof resource?.phenomenonTime === 'string' &&
    typeof resource?.resultTime === 'string' &&
    'result' in resource
  );
}

// Component type guards
function isQuantity(component: DataComponent): component is QuantityComponent {
  return component.type === 'Quantity';
}

function isDataRecord(
  component: DataComponent
): component is DataRecordComponent {
  return component.type === 'DataRecord';
}

// Geometry type guards
function isPoint(geometry: Geometry): geometry is PointGeoJSON {
  return geometry.type === 'Point';
}

function isPolygon(geometry: Geometry): geometry is PolygonGeoJSON {
  return geometry.type === 'Polygon';
}
```

### 10.6 Utility Types for Format Negotiation

```typescript
// Media type constants
const MediaTypes = {
  // GeoJSON
  GEOJSON: 'application/geo+json',

  // SensorML
  SENSORML_JSON: 'application/sml+json',

  // SWE Common
  SWE_JSON: 'application/swe+json',
  SWE_TEXT: 'application/swe+text',
  SWE_BINARY: 'application/swe+binary',

  // Standard JSON
  JSON: 'application/json',

  // Other
  PROTOBUF: 'application/protobuf',
} as const;

type MediaType = (typeof MediaTypes)[keyof typeof MediaTypes];

// Format-specific return types
type FormatResponse<T, F extends MediaType> = F extends 'application/geo+json'
  ? GeoJSONFeature
  : F extends 'application/sml+json'
  ? SystemSensorML
  : F extends 'application/json'
  ? T
  : T;
```

---

## 11. Type Scope and Balance

### 11.1 Type Safety vs Flexibility Trade-offs

**Strict Types (Internal Library Use):**

```typescript
// Strict - enforces all requirements
interface StrictSystem
  extends Required<Pick<System, 'type' | 'geometry' | 'properties'>> {
  properties: Required<Pick<SystemProperties, 'featureType' | 'uid' | 'name'>>;
}

// Used internally for validated resources
function processValidatedSystem(system: StrictSystem): void {
  // All required properties guaranteed to exist
  console.log(system.properties.name); // No null checks needed
}
```

**Flexible Types (User-Facing API):**

```typescript
// Flexible - accepts broader input
type SystemInput = Partial<System> & Pick<System, 'properties'>;

// Used in public API to accept incomplete data
function createSystem(input: SystemInput): Promise<System> {
  // Library validates and fills in defaults
  return validateAndCreate(input);
}
```

### 11.2 Minimal vs Comprehensive Type Exports

**Minimal Export Strategy (Recommended for v1):**

- Core resource types only (10 types)
- Basic query parameter types (5 types)
- Response wrappers (3 types)
- Essential utilities (Link, TimePeriod, Geometry)
- **Total: ~25 exported types**

**Comprehensive Export Strategy (For Advanced Users):**

- All 100+ types exported
- Full SWE Common component hierarchy
- All SensorML process types
- Complete encoding definitions
- Every constraint and validation type
- **Total: 100+ exported types**

**Recommended Approach:**

```typescript
// src/types/index.ts - Public API
export {
  // Core Resources (10)
  System,
  Deployment,
  Procedure,
  SamplingFeature,
  PropertyResource,
  DataStream,
  Observation,
  ControlStream,
  Command,
  SystemEvent,

  // Collections (3)
  SystemCollection,
  DataStreamCollection,
  ObservationCollection,

  // Query Parameters (5)
  SystemQueryParams,
  DataStreamQueryParams,
  ObservationQueryParams,
  ControlStreamQueryParams,
  CommonQueryParams,

  // Utilities (7)
  Link,
  TimePeriod,
  TimeInstant,
  Geometry,
  Point,
  Collection,
  PaginatedResponse,
};

// src/types/advanced.ts - Advanced API (opt-in)
export * from './swe-components';
export * from './sensorml-processes';
export * from './encodings';
export * from './constraints';
```

### 11.3 Type Depth Control

**Shallow Types (Default):**

```typescript
// Links not expanded - just references
interface System {
  properties: {
    'subsystems@link'?: Link; // Just href + rel
  };
}
```

**Deep Types (Opt-in via Generic Parameter):**

```typescript
// Links expanded to full resources
interface SystemDeep {
  properties: {
    subsystems?: System[]; // Full nested systems
  };
}

// Generic type with depth control
type Expand<T, D extends number = 0> = D extends 3
  ? T
  : T extends Link
  ? Resource
  : T;
```

### 11.4 Runtime Validation Integration

**Zod Schema Generation (Optional):**

```typescript
import { z } from 'zod';

// Generate runtime validators from TypeScript types
const SystemSchema = z.object({
  type: z.literal('Feature'),
  geometry: z.custom<Point>().nullable(),
  properties: z.object({
    featureType: z.enum([
      'http://www.w3.org/ns/sosa/Sensor',
      'sosa:Sensor',
      // ... other types
    ]),
    uid: z.string().url(),
    name: z.string().min(1),
    description: z.string().optional(),
    // ... other properties
  }),
  links: z.array(LinkSchema).optional(),
});

// Use for runtime validation
function validateSystem(data: unknown): System {
  return SystemSchema.parse(data); // Throws if invalid
}
```

**Validation Strategy:**

- TypeScript types for compile-time safety
- Optional Zod schemas for runtime validation
- Users can choose validation library (Zod, Yup, io-ts, etc.)
- Library provides type definitions only by default

---

## 12. Implementation Strategy

### 12.1 Type Generation Approach

**Option 1: Manual Type Definitions**

- Pro: Full control, optimized for TypeScript
- Pro: Can add documentation comments
- Pro: Can simplify/improve OpenAPI schemas
- Con: Manual maintenance burden
- Con: Risk of drift from OpenAPI spec

**Option 2: Automated Generation from OpenAPI**

- Pro: Always in sync with spec
- Pro: Less maintenance
- Con: Generated types may be verbose
- Con: May need post-processing
- Tools: openapi-typescript, swagger-typescript-api

**Recommended: Hybrid Approach**

1. Generate initial types from OpenAPI YAML
2. Review and refine generated types
3. Add JSDoc comments and examples
4. Extract common patterns into utilities
5. Re-run generator periodically, merge changes manually

### 12.2 Type Organization

```
src/types/
├── index.ts                      # Public API exports
├── advanced.ts                   # Advanced types (opt-in)
├── resources/
│   ├── part1/
│   │   ├── system.ts
│   │   ├── deployment.ts
│   │   ├── procedure.ts
│   │   ├── sampling-feature.ts
│   │   └── property.ts
│   └── part2/
│       ├── datastream.ts
│       ├── observation.ts
│       ├── control-stream.ts
│       ├── command.ts
│       └── system-event.ts
├── data-components/
│   ├── base.ts                   # Abstract base types
│   ├── scalars.ts                # Boolean, Count, Quantity, etc.
│   ├── ranges.ts                 # Range components
│   ├── aggregates.ts             # DataRecord, Vector, DataArray, etc.
│   └── index.ts
├── geometries/
│   ├── geojson.ts                # GeoJSON geometry types
│   ├── position.ts               # Position and Pose types
│   └── index.ts
├── sensorml/
│   ├── processes.ts              # Process hierarchy
│   ├── metadata.ts               # Terms, Contacts, Documents, etc.
│   └── index.ts
├── encodings/
│   ├── binary.ts
│   ├── text.ts
│   ├── json.ts
│   └── xml.ts
├── constraints/
│   ├── allowed-values.ts
│   ├── nil-values.ts
│   └── index.ts
├── collections/
│   ├── collection.ts             # Collection metadata
│   ├── pagination.ts             # Pagination types
│   └── index.ts
├── query-params/
│   ├── common.ts                 # Common query params
│   ├── part1.ts                  # Part 1 filtering
│   ├── part2.ts                  # Part 2 filtering
│   └── index.ts
├── requests/
│   ├── create.ts
│   ├── update.ts
│   ├── replace.ts
│   └── delete.ts
├── responses/
│   ├── success.ts
│   ├── error.ts
│   └── index.ts
└── utilities/
    ├── link.ts
    ├── time.ts
    ├── generics.ts
    ├── type-guards.ts
    └── index.ts
```

### 12.3 Documentation Strategy

**JSDoc Comments:**

````typescript
/**
 * System resource representing sensors, actuators, platforms, and systems.
 *
 * @see {@link https://docs.ogc.org/is/23-001/23-001.html#system-resource OGC API - Connected Systems Part 1 § 7.2}
 *
 * @example
 * ```typescript
 * const sensor: System = {
 *   type: 'Feature',
 *   geometry: { type: 'Point', coordinates: [-122.4194, 37.7749] },
 *   properties: {
 *     featureType: 'sosa:Sensor',
 *     uid: 'urn:uuid:550e8400-e29b-41d4-a716-446655440000',
 *     name: 'Temperature Sensor',
 *     description: 'High-precision temperature sensor',
 *     assetType: 'Equipment',
 *   },
 * };
 * ```
 */
export interface System extends GeoJSONFeature {
  // ...
}
````

**README with Type Usage Examples:**

- Common type patterns
- Type narrowing with type guards
- Format negotiation examples
- Generic type parameter usage

### 12.4 Versioning Strategy

**Semantic Versioning for Types:**

- **Major version change:** Breaking changes to public types
- **Minor version change:** New types added (non-breaking)
- **Patch version change:** Documentation or internal type fixes

**Compatibility Guarantees:**

- Public API types (index.ts) follow strict semver
- Advanced types (advanced.ts) can have breaking changes in minor versions
- Internal types can change freely

### 12.5 Testing Strategy

**Type Tests:**

```typescript
// tests/types/system.test-d.ts (using tsd or vitest)
import { expectType, expectError } from 'tsd';
import type { System, SystemProperties } from '../src/types';

// Test required properties
expectError<System>({ type: 'Feature' }); // Missing properties

// Test valid system
expectType<System>({
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [0, 0] },
  properties: {
    featureType: 'sosa:Sensor',
    uid: 'urn:test',
    name: 'Test',
  },
});

// Test type guards
const resource: unknown = {};
if (isSystem(resource)) {
  expectType<System>(resource); // Narrowed to System
}
```

**Integration with Runtime Tests:**

```typescript
// tests/integration/types.test.ts
import { describe, it, expect } from 'vitest';
import { SystemSchema } from '../src/validation/schemas';

describe('System type validation', () => {
  it('validates correct system', () => {
    const system = {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [0, 0] },
      properties: {
        featureType: 'sosa:Sensor',
        uid: 'urn:test',
        name: 'Test Sensor',
      },
    };

    expect(() => SystemSchema.parse(system)).not.toThrow();
  });

  it('rejects invalid system', () => {
    const invalid = { type: 'Feature' };
    expect(() => SystemSchema.parse(invalid)).toThrow();
  });
});
```

---

## Summary

### Type System Requirements:

1. **Core Resource Types (10):** System, Deployment, Procedure, SamplingFeature, Property, DataStream, Observation, ControlStream, Command, SystemEvent

2. **SWE Common Components (30+):** Complete hierarchy from simple (Boolean, Quantity) to aggregate (DataRecord, DataArray) components

3. **Geometry Types (8):** Full GeoJSON geometry support plus GeoPose representations

4. **SensorML Processes (4):** SimpleProcess, AggregateProcess, PhysicalComponent, PhysicalSystem

5. **Supporting Types (50+):** Collections, pagination, links, time types, query parameters, constraints, encodings

6. **Generic Types:** Resource<T>, Collection<T>, PaginatedResponse<T>, conditional types for CRUD

7. **Type Guards:** Runtime type checking for discriminated unions

8. **Format-Specific Types:** GeoJSON, SensorML, SWE Common representations

### Implementation Recommendations:

1. **Hybrid generation:** Start with OpenAPI generation, refine manually
2. **Progressive disclosure:** Simple public API, advanced opt-in types
3. **JSDoc comments:** Comprehensive documentation with examples
4. **Type testing:** Compile-time and runtime validation tests
5. **Strict versioning:** Follow semver for type changes
6. **Flexible inputs, strict outputs:** Accept broader types, return specific types
7. **Optional runtime validation:** Provide Zod schemas for users who want them

### Balance Achieved:

- **Type Safety:** Compile-time error detection, autocomplete support
- **Flexibility:** Union types, optional properties, format negotiation
- **Maintainability:** Clear organization, automated generation, comprehensive tests
- **Developer Experience:** Progressive disclosure, helpful documentation, type guards
- **Performance:** Zero runtime overhead, types compile away

This type system provides a solid foundation for the ogc-client CSAPI library while remaining flexible enough to accommodate future spec evolution and user needs.
