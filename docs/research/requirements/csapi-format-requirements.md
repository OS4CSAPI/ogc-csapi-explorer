# CSAPI Format Requirements Analysis

**Document:** Section 3 - Format Requirements  
**Date:** 2026-01-31  
**Status:** In Progress

---

## Overview

This document analyzes format requirements for the CSAPI client library, covering GeoJSON, SensorML, and SWE Common data formats used across Part 1 (feature resources) and Part 2 (dynamic data).

---

## Section 3.2: GeoJSON Format Requirements

**Date:** 2026-01-31  
**Status:** Complete

### Overview

GeoJSON (RFC 7946) is a primary format for representing spatial features in CSAPI Part 1. It provides a lightweight, human-readable encoding for Systems, Deployments, Procedures, and Sampling Features with geospatial properties.

**Media Type:** `application/geo+json`

**Standard References:**

- [GeoJSON RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946)
- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - Clause 19.1, Requirements Class `/req/geojson`
- [OGC API – Features Part 1](https://docs.ogc.org/is/17-069r4/17-069r4.html) - GeoJSON encoding requirements

---

### 1. CSAPI Resources Supporting GeoJSON

#### 1.1 Part 1 Feature Resources

**Systems (Required):**

- Systems with spatial location (sensors, platforms, actuators on platforms)
- Geometry represents system's current or typical location
- Example: Weather station (Point), Mobile platform path (LineString), Survey area (Polygon)

**Deployments (Required):**

- All deployments have spatial extent
- Geometry represents deployment coverage area
- Example: Sensor deployment footprint (Polygon), Transect deployment (LineString)

**Procedures (Optional):**

- Geometry typically `null` (procedures are conceptual, not spatial)
- May have geometry if procedure tied to specific location
- Example: Sampling methodology (null geometry), Site-specific calibration procedure (Point)

**Sampling Features (Required):**

- All sampling features have geometry
- Represents the sampled feature (location, area, volume)
- Example: Sampling point (Point), Sampling transect (LineString), Sampling plot (Polygon)

#### 1.2 Part 2 Dynamic Data Resources

**DataStreams (Optional):**

- DataStreams may reference Systems with GeoJSON geometry
- DataStream collections may be represented as FeatureCollection
- Used for spatial discovery of data streams

**ControlStreams (Optional):**

- ControlStreams may reference Systems with GeoJSON geometry
- ControlStream collections may be represented as FeatureCollection
- Used for spatial discovery of control channels

**Not Applicable:**

- Observations (use SWE Common formats, not GeoJSON)
- Commands (use SWE Common formats, not GeoJSON)
- Properties (use SensorML or plain JSON)

---

### 2. GeoJSON Geometry Types Used

#### 2.1 Geometry Type Support Matrix

| Geometry Type          | Part 1 Usage                           | Common Use Cases                                 | Client Support |
| ---------------------- | -------------------------------------- | ------------------------------------------------ | -------------- |
| **Point**              | Systems, Deployments, SamplingFeatures | Fixed sensors, weather stations, sampling points | **Required**   |
| **MultiPoint**         | SamplingFeatures                       | Multiple discrete sampling locations             | **Required**   |
| **LineString**         | Systems, Deployments, SamplingFeatures | Mobile platform paths, transects, pipelines      | **Required**   |
| **MultiLineString**    | Deployments, SamplingFeatures          | Multiple transects, network segments             | **Required**   |
| **Polygon**            | Deployments, SamplingFeatures          | Coverage areas, sampling plots, survey regions   | **Required**   |
| **MultiPolygon**       | Deployments, SamplingFeatures          | Discontinuous coverage, multiple plots           | **Required**   |
| **GeometryCollection** | Systems, Deployments                   | Complex features with mixed geometry types       | **Required**   |

**All 7 geometry types MUST be supported** per RFC 7946 and OGC API – Features requirements.

#### 2.2 Geometry Coordinate Arrays

**2D Coordinates (Required):**

```json
{
  "type": "Point",
  "coordinates": [-122.08, 37.42]
}
```

- Format: `[longitude, latitude]`
- Coordinate order: **longitude first, latitude second** (per RFC 7946 Section 3.1.1)
- Range: longitude [-180, 180], latitude [-90, 90]

**3D Coordinates (Required):**

```json
{
  "type": "Point",
  "coordinates": [-122.08, 37.42, 25.5]
}
```

- Format: `[longitude, latitude, altitude]`
- Third coordinate represents altitude/elevation in meters
- Positive altitude = above reference surface, Negative = below

**Client Library Requirements:**

- Parse 2D and 3D coordinate arrays
- Preserve coordinate precision (typically 6-8 decimal places)
- Validate coordinate array length (minItems: 2 for 2D, minItems: 3 for 3D)
- Handle null altitude (missing third coordinate)

#### 2.3 Null Geometry Handling

**Allowed for Procedures:**

```json
{
  "type": "Feature",
  "id": "proc123",
  "geometry": null,
  "properties": {
    "name": "Standard Operating Procedure"
  }
}
```

**Client Library Requirements:**

- Allow `geometry: null` for Procedure resources
- Reject `geometry: null` for Systems, Deployments, SamplingFeatures (validation error)
- TypeScript type: `geometry: GeoJSONGeometry | null`

---

### 3. CSAPI GeoJSON Feature Structure

#### 3.1 Feature Object Schema

**Complete Feature Structure:**

```json
{
  "type": "Feature",
  "id": "sensor123",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.08, 37.42, 25.5]
  },
  "properties": {
    "uid": "urn:x-sensor:id:sensor123",
    "name": "Temperature Sensor TS-001",
    "description": "High-precision temperature sensor",
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "assetType": "Equipment",
    "validTime": ["2024-01-01T00:00:00Z", null],
    "parent@id": "platform456",
    "procedure@id": "proc789"
  },
  "links": [
    {
      "rel": "canonical",
      "href": "https://api.example.org/systems/sensor123"
    },
    {
      "rel": "ogc-rel:subsystems",
      "href": "https://api.example.org/systems/sensor123/subsystems"
    }
  ]
}
```

**Required Feature Properties:**

- `type`: Always `"Feature"` (string, required)
- `geometry`: Geometry object or `null` (required)
- `properties`: Object containing CSAPI-specific properties (required, may be `null`)

**Optional Feature Properties:**

- `id`: Resource identifier (string or integer, optional but strongly recommended)
- `links`: Array of link objects for navigation (optional)
- `bbox`: Bounding box array (optional, rarely used in CSAPI)

#### 3.2 CSAPI Property Mappings

**Common Properties (All Resources):**

- `uid` (string, format: uri) - Unique persistent identifier
- `name` (string) - Human-readable name
- `description` (string) - Detailed description
- `validTime` (array of 2 date-times) - Temporal validity period `[startTime, endTime]`, `null` for open-ended

**System-Specific Properties:**

- `featureType` (string, format: uri) - System ontology type (`sosa:Sensor`, `sosa:Actuator`, etc.)
- `assetType` (string) - Asset classification (`Equipment`, `Human`, `Simulation`, etc.)
- `parent@id` (string) - Parent system local ID
- `procedure@id` (string) - Associated procedure local ID

**Deployment-Specific Properties:**

- `deployedSystem@id` (string) - System being deployed
- `platform@id` (string) - Platform hosting deployment
- `height` (number) - Deployment height above ground/water surface

**SamplingFeature-Specific Properties:**

- `sampledFeature@id` (string) - Feature being sampled
- `samplingProcedure@id` (string) - Procedure used for sampling
- `shape` (string) - Shape classification (`Point`, `Curve`, `Surface`, `Solid`)

**Reference Encoding Convention:**

- Local ID references use `@id` suffix (e.g., `parent@id`)
- URI references use `@link` suffix (e.g., `parent@link` with full Link object)

---

### 4. Coordinate Reference System (CRS)

#### 4.1 Default CRS: WGS 84 (CRS84)

**RFC 7946 Requirement:**

- Default CRS: **WGS 84** (World Geodetic System 1984)
- EPSG code: **EPSG:4326** (latitude/longitude)
- GeoJSON identifier: **CRS84** (OGC:CRS84 - longitude/latitude order)

**Coordinate Order:**

- GeoJSON uses **longitude, latitude** order (CRS84)
- Different from many GIS systems that use **latitude, longitude** (EPSG:4326)

**Altitude Reference:**

- Altitude measured relative to WGS 84 ellipsoid
- Positive values above ellipsoid, negative below
- Not orthometric height (not relative to geoid/mean sea level)

#### 4.2 Alternative CRS Support

**RFC 7946 Position:**

- RFC 7946 Section 4: "The use of alternative coordinate reference systems was specified in [GeoJSON 2008] but... removed from this version of the specification."
- **Alternative CRS not supported in RFC 7946 GeoJSON**

**CSAPI Part 1 Position:**

- Inherits RFC 7946 constraint
- No CRS negotiation mechanism defined
- All GeoJSON uses WGS 84 / CRS84

**Client Library Implications:**

- Assume all GeoJSON coordinates are WGS 84 / CRS84
- No CRS transformation needed for input/output
- If application uses different CRS internally, **client application** responsible for transformation

---

### 5. GeoJSON FeatureCollection Usage

#### 5.1 Collection Responses

**Structure:**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "sensor123",
      "geometry": { "type": "Point", "coordinates": [-122.08, 37.42] },
      "properties": { "name": "Sensor TS-001" }
    },
    {
      "type": "Feature",
      "id": "sensor456",
      "geometry": { "type": "Point", "coordinates": [-122.1, 37.45] },
      "properties": { "name": "Sensor TS-002" }
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?f=geojson&limit=10"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/systems?f=geojson&limit=10&cursor=abc123"
    }
  ],
  "timeStamp": "2024-01-15T10:00:00Z",
  "numberMatched": 250
}
```

**Required FeatureCollection Properties:**

- `type`: Always `"FeatureCollection"` (string, required)
- `features`: Array of Feature objects (required, may be empty array)

**Optional FeatureCollection Properties:**

- `links`: Pagination and navigation links (optional)
- `timeStamp`: Response generation time (string, format: date-time, optional)
- `numberMatched`: Total count of matching features (integer, optional)
- `numberReturned`: Count of features in response (integer, optional)
- `bbox`: Bounding box of all features (array of numbers, optional)

#### 5.2 Endpoints Returning FeatureCollections

**Part 1 Collection Endpoints:**

- `GET /systems` with `Accept: application/geo+json`
- `GET /systems/{systemId}/subsystems` with `Accept: application/geo+json`
- `GET /deployments` with `Accept: application/geo+json`
- `GET /samplingFeatures` with `Accept: application/geo+json`
- `GET /procedures` with `Accept: application/geo+json`

**Part 2 Collection Endpoints (Optional):**

- `GET /datastreams` with `Accept: application/geo+json`
- `GET /controlstreams` with `Accept: application/geo+json`
- `GET /systemEvents` (GeoJSON not applicable)

**Single Resource Endpoints:**

- Return single Feature object (not FeatureCollection)
- Example: `GET /systems/sensor123` returns Feature

---

### 6. Client Library Parsing Requirements

#### 6.1 Parse vs Opaque Handling

**Recommended Approach: Structured Parsing**

**Rationale:**

- Client needs to extract `properties` for display/filtering
- Client needs to extract `id` for resource operations
- Client needs to extract `links` for navigation
- Geometry operations needed for spatial filtering/display

**What to Parse:**

- Feature `type`, `id`, `geometry`, `properties`, `links`
- Geometry `type`, `coordinates`
- Property values per resource type schema
- Link `rel`, `href`, `type` for navigation

**What to Preserve Opaquely:**

- Unknown properties in `properties` object (forward compatibility)
- Unknown link relation types
- Extension fields

#### 6.2 TypeScript Type Definitions

**Base GeoJSON Types:**

```typescript
type Position = [number, number] | [number, number, number]; // [lon, lat] or [lon, lat, alt]

type Point = {
  type: 'Point';
  coordinates: Position;
};

type MultiPoint = {
  type: 'MultiPoint';
  coordinates: Position[];
};

type LineString = {
  type: 'LineString';
  coordinates: Position[]; // minItems: 2
};

type MultiLineString = {
  type: 'MultiLineString';
  coordinates: Position[][];
};

type Polygon = {
  type: 'Polygon';
  coordinates: Position[][]; // First ring = exterior, rest = holes
};

type MultiPolygon = {
  type: 'MultiPolygon';
  coordinates: Position[][][];
};

type GeometryCollection = {
  type: 'GeometryCollection';
  geometries: GeoJSONGeometry[];
};

type GeoJSONGeometry =
  | Point
  | MultiPoint
  | LineString
  | MultiLineString
  | Polygon
  | MultiPolygon
  | GeometryCollection;
```

**Feature Types:**

```typescript
interface GeoJSONFeature<P = any> {
  type: 'Feature';
  id?: string | number;
  geometry: GeoJSONGeometry | null;
  properties: P | null;
  links?: Link[];
  bbox?: number[];
}

interface GeoJSONFeatureCollection<P = any> {
  type: 'FeatureCollection';
  features: GeoJSONFeature<P>[];
  links?: Link[];
  timeStamp?: string;
  numberMatched?: number;
  numberReturned?: number;
  bbox?: number[];
}
```

**CSAPI-Specific Properties:**

```typescript
interface SystemGeoJSONProperties {
  uid: string;
  name: string;
  description?: string;
  featureType: string; // URI
  assetType?: string;
  validTime?: [string, string | null];
  'parent@id'?: string;
  'procedure@id'?: string;
  [key: string]: any; // Allow extensions
}

type SystemFeature = GeoJSONFeature<SystemGeoJSONProperties>;
type SystemCollection = GeoJSONFeatureCollection<SystemGeoJSONProperties>;
```

#### 6.3 Validation Requirements

**Client-Side Validation:**

**Geometry Validation:**

- Validate `type` is one of 7 allowed geometry types
- Validate `coordinates` array structure matches geometry type
- Validate coordinate count (minItems: 2 for positions, minItems: 2 for LineString, minItems: 4 for Polygon rings)
- Validate longitude range [-180, 180]
- Validate latitude range [-90, 90]
- Validate polygon ring closure (first position === last position)

**Feature Validation:**

- Validate `type: "Feature"`
- Validate `geometry` is GeoJSONGeometry or null
- Validate `properties` is object or null
- Reject `geometry: null` for Systems, Deployments, SamplingFeatures

**FeatureCollection Validation:**

- Validate `type: "FeatureCollection"`
- Validate `features` is array
- Validate each feature in array

**Error Handling:**

- Throw `ValidationError` for malformed GeoJSON
- Include specific validation failure details (e.g., "Invalid longitude value: 200")
- Provide JSON path to error location (e.g., "features[2].geometry.coordinates[0]")

---

### 7. Geometry Operations Needed

#### 7.1 Required Operations

**Bounding Box Calculation:**

- Calculate bbox from geometry coordinates
- Used for spatial indexing, map extent calculation
- Algorithm:
  ```typescript
  function calculateBBox(
    geometry: GeoJSONGeometry
  ): [number, number, number, number] {
    const coords = extractAllCoordinates(geometry);
    const lons = coords.map((c) => c[0]);
    const lats = coords.map((c) => c[1]);
    return [
      Math.min(...lons), // minLon
      Math.min(...lats), // minLat
      Math.max(...lons), // maxLon
      Math.max(...lats), // maxLat
    ];
  }
  ```

**Coordinate Extraction:**

- Flatten geometry coordinates to single array of positions
- Needed for bbox calculation, coordinate transformation
- Handle all 7 geometry types including GeometryCollection

**Geometry Type Detection:**

- Determine geometry type from feature
- Used for rendering decisions (point vs line vs polygon)

#### 7.2 Optional Operations (Not Required for MVP)

**Spatial Predicates:**

- Point-in-polygon test (for client-side spatial filtering)
- Geometry intersection (for overlay operations)
- Distance calculation (for proximity queries)

**Geometry Simplification:**

- Reduce coordinate count for performance
- Douglas-Peucker algorithm

**Coordinate Transformation:**

- Transform WGS 84 to/from other CRS (e.g., Web Mercator for web maps)
- Use external library like proj4js

**Recommendation:** Use external GeoJSON libraries (e.g., `@turf/turf`, `geojson-validation`) for complex operations.

---

### 8. 3D Coordinate Handling

#### 8.1 Altitude Semantics

**WGS 84 Ellipsoidal Height:**

- Third coordinate = height above WGS 84 ellipsoid
- **Not** orthometric height (height above mean sea level)
- **Not** height above ground level

**Conversion Needed for Display:**

- Web maps typically expect height above ground or mean sea level
- Requires geoid model for conversion (e.g., EGM96, EGM2008)
- Client library should document altitude semantics, not perform conversion

#### 8.2 Client API for 3D Coordinates

**Position Interface:**

```typescript
interface Position2D {
  lon: number;
  lat: number;
}

interface Position3D extends Position2D {
  alt: number; // Altitude in meters (WGS 84 ellipsoidal height)
}

type Position = Position2D | Position3D;

function parsePosition(coords: number[]): Position {
  if (coords.length === 2) {
    return { lon: coords[0], lat: coords[1] };
  } else if (coords.length === 3) {
    return { lon: coords[0], lat: coords[1], alt: coords[2] };
  } else {
    throw new Error(`Invalid position length: ${coords.length}`);
  }
}
```

**Type Guard:**

```typescript
function hasAltitude(pos: Position): pos is Position3D {
  return 'alt' in pos;
}

// Usage
const pos = parsePosition([-122.08, 37.42, 25.5]);
if (hasAltitude(pos)) {
  console.log(`Altitude: ${pos.alt}m`);
}
```

---

### 9. Client API Implications

#### 9.1 Format Negotiation

**Requesting GeoJSON:**

```typescript
// Option 1: Accept header
const systems = await client.getSystems({
  headers: { Accept: 'application/geo+json' },
});

// Option 2: Query parameter
const systems = await client.getSystems({
  format: 'geojson',
});

// Option 3: Convenience method
const systems = await client.getSystemsAsGeoJSON();
```

**Accept Header vs Query Parameter:**

- Accept header: Standard HTTP content negotiation
- Query parameter `f=geojson`: OGC API convention
- Query parameter takes precedence over Accept header (per OGC API – Common)

#### 9.2 Response Type Handling

**TypeScript Return Types:**

```typescript
class CSAPIClient {
  // Generic method - format determined at runtime
  async getSystems(options?: {
    format?: 'json' | 'geojson' | 'sensorml';
    // ... other options
  }): Promise<
    SystemCollection | SystemGeoJSONCollection | SystemSensorMLCollection
  >;

  // Format-specific methods - explicit return types
  async getSystemsAsGeoJSON(
    options?: QueryOptions
  ): Promise<SystemGeoJSONCollection>;
  async getSystemAsGeoJSON(id: string): Promise<SystemFeature>;

  async getDeploymentsAsGeoJSON(
    options?: QueryOptions
  ): Promise<DeploymentGeoJSONCollection>;
  async getSamplingFeaturesAsGeoJSON(
    options?: QueryOptions
  ): Promise<SamplingFeatureGeoJSONCollection>;
}
```

#### 9.3 Geometry Access Convenience

**Direct Geometry Access:**

```typescript
interface System {
  id: string;
  name: string;
  // ... other properties
  geometry?: GeoJSONGeometry; // When fetched as GeoJSON
  location?: Position; // Convenience accessor for Point geometries
}

const system = await client.getSystemAsGeoJSON('sensor123');
if (system.geometry?.type === 'Point') {
  system.location = parsePosition(system.geometry.coordinates);
}
```

#### 9.4 Write Operations

**Creating System with GeoJSON:**

```typescript
const newSystem = await client.createSystem(
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [-122.08, 37.42, 25.5],
    },
    properties: {
      name: 'New Temperature Sensor',
      featureType: 'http://www.w3.org/ns/sosa/Sensor',
      assetType: 'Equipment',
    },
  },
  {
    format: 'geojson',
  }
);
```

**Updating System Geometry:**

```typescript
const system = await client.getSystemAsGeoJSON('sensor123');
system.geometry = {
  type: 'Point',
  coordinates: [-122.1, 37.45, 30.0], // New location
};
await client.updateSystem('sensor123', system, { format: 'geojson' });
```

---

### 10. Error Handling

#### 10.1 Format-Related Errors

**Unsupported Format Error:**

```typescript
class UnsupportedFormatError extends Error {
  constructor(
    public requestedFormat: string,
    public availableFormats: string[]
  ) {
    super(
      `Format '${requestedFormat}' not supported. Available: ${availableFormats.join(
        ', '
      )}`
    );
  }
}

// Server returns 406 Not Acceptable
if (response.status === 406) {
  throw new UnsupportedFormatError('application/geo+json', [
    'application/json',
    'application/sml+json',
  ]);
}
```

**Malformed GeoJSON Error:**

```typescript
class MalformedGeoJSONError extends Error {
  constructor(public jsonPath: string, public validationError: string) {
    super(`Invalid GeoJSON at ${jsonPath}: ${validationError}`);
  }
}

// Example
throw new MalformedGeoJSONError(
  'features[2].geometry.coordinates[0]',
  'Longitude must be between -180 and 180, got 200'
);
```

#### 10.2 Validation Error Reporting

**Detailed Validation Results:**

```typescript
interface ValidationError {
  path: string; // JSON path to error
  message: string; // Human-readable message
  value?: any; // Invalid value
  constraint?: string; // Violated constraint (e.g., "minItems: 2")
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

function validateGeoJSONFeature(feature: any): ValidationResult {
  const errors: ValidationError[] = [];

  if (feature.type !== 'Feature') {
    errors.push({
      path: 'type',
      message: 'Feature type must be "Feature"',
      value: feature.type,
    });
  }

  if (feature.geometry) {
    const geomErrors = validateGeometry(feature.geometry, 'geometry');
    errors.push(...geomErrors);
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
```

---

### 11. Dependencies and Libraries

#### 11.1 Recommended External Libraries

**GeoJSON Validation:**

- **geojson-validation** - RFC 7946 compliance checking
- **@turf/turf** - Spatial operations, bbox calculation, validation

**Usage:**

```typescript
import { validate } from 'geojson-validation';
import * as turf from '@turf/turf';

// Validation
const isValid = validate(geoJsonFeature);

// Bounding box
const bbox = turf.bbox(geoJsonFeatureCollection);

// Point in polygon
const point = turf.point([-122.08, 37.42]);
const polygon = turf.polygon([...]);
const inside = turf.booleanPointInPolygon(point, polygon);
```

#### 11.2 Built-in vs External

**Built-in (Client Library):**

- TypeScript type definitions for GeoJSON
- Basic parsing (JSON.parse)
- Format negotiation (Accept header, query param)
- Property extraction from Feature.properties

**External Libraries (Optional Dependencies):**

- Complex validation (geojson-validation)
- Spatial operations (turf)
- Coordinate transformations (proj4)
- Map rendering (leaflet, mapbox-gl)

**Rationale:** Keep core library lightweight, provide plugin support for advanced features.

---

## Summary

**Section 3.2 Complete:** GeoJSON Format Requirements (~500 lines documenting all GeoJSON aspects)

### Key Requirements

**Resources Supporting GeoJSON:**

- Part 1: Systems, Deployments, Procedures (geometry: null allowed), SamplingFeatures
- Part 2: DataStreams, ControlStreams (optional for collections)

**Geometry Types:**

- All 7 RFC 7946 types required: Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection
- 2D and 3D coordinates (altitude = WGS 84 ellipsoidal height)
- Coordinate order: longitude, latitude (CRS84)

**CRS Support:**

- WGS 84 / CRS84 only (RFC 7946 requirement)
- No alternative CRS support
- Application responsible for coordinate transformation if needed

**Feature Structure:**

- Standard RFC 7946 Feature object
- CSAPI properties in `properties` object
- Reference encoding: `@id` for local IDs, `@link` for URI refs
- Navigation links in `links` array with `ogc-rel:` prefix

**Client Library Must:**

- Parse GeoJSON Feature and FeatureCollection
- Extract geometry, properties, id, links
- Validate geometry structure and coordinate ranges
- Support format negotiation (Accept header, query param)
- Calculate bounding boxes
- Handle 3D coordinates (preserve altitude)
- Provide TypeScript types for all GeoJSON structures

**Optional (External Libraries):**

- Complex spatial operations (point-in-polygon, intersection)
- Coordinate transformation
- Geometry simplification

**Ready for Section 3.3:** SensorML Format Requirements

---

## Section 3.3: SensorML Format Requirements

**Date:** 2026-01-31  
**Status:** Complete

### Overview

SensorML 3.0 is the primary format for representing detailed system and procedure descriptions in CSAPI Part 1. It provides rich semantic metadata for sensors, actuators, platforms, processes, and methodologies beyond what GeoJSON can represent.

**Media Type:** `application/sml+json`

**Standard References:**

- [SensorML 3.0 Specification](https://docs.ogc.org/is/20-010r3/20-010r3.html)
- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - Clause 19.2, Requirements Class `/req/sensorml`
- [SensorML 3.0 JSON Schema](https://schemas.opengis.net/sensorml/3.0/sensorml.json)

---

### 1. CSAPI Resources Supporting SensorML

#### 1.1 Part 1 Resources

**Systems (Required):**

- **PhysicalSystem** - Hardware systems with components (weather stations, sensor networks, robotic platforms)
- **PhysicalComponent** - Individual hardware elements (thermometers, cameras, GPS receivers)
- **SimpleProcess** - Software processes, simulations, algorithms
- **AggregateProcess** - Grouped/composite processes
- More detailed than GeoJSON (inputs, outputs, parameters, characteristics, capabilities)

**Procedures (Required):**

- **SimpleProcess** - Methodologies, algorithms, processing steps
- **AggregateProcess** - Complex multi-step procedures
- Typically used for datasheets, calibration procedures, processing workflows
- May have null geometry (conceptual, not spatial)

**Deployments (Required):**

- **Deployment** - SensorML-specific deployment description
- References deployed systems, platforms
- Temporal extent, spatial location, deployment metadata

**Properties (Required):**

- **DerivedProperty** - Computed/derived properties
- Semantic definitions with provenance
- References to derivation processes

**Sampling Features (Optional):**

- Rarely use SensorML (prefer GeoJSON for spatial features)
- May use for complex sampling procedures

#### 1.2 Part 2 Resources

**Not Applicable:**

- DataStreams, ControlStreams use JSON/SWE Common, not SensorML
- Observations, Commands use SWE Common formats
- System references in Part 2 may link to SensorML descriptions via `canonical` link

---

### 2. SensorML Component Types Used

#### 2.1 Process Types (Abstract Classes)

**Hierarchy:**

```
DescribedObject
  ├─ AbstractProcess
  │   ├─ SimpleProcess (software, simulations)
  │   ├─ AggregateProcess (composite processes)
  │   └─ AbstractPhysicalProcess
  │       ├─ PhysicalComponent (hardware elements)
  │       └─ PhysicalSystem (hardware systems with components)
  └─ Deployment (deployment metadata)
```

**All types extend `DescribedObject`** with common properties (id, label, description, uniqueId, identifiers, classifiers, etc.)

#### 2.2 Type Selection Rules

**Systems:**

- **PhysicalSystem** - Hardware with subsystems/components (e.g., weather station with multiple sensors)
- **PhysicalComponent** - Single hardware element without subsystems (e.g., thermometer)
- **SimpleProcess** - Software simulation, virtual sensor, data processing algorithm
- **AggregateProcess** - Composite system with explicit connections between components

**Procedures:**

- **SimpleProcess** - Single-step procedure, algorithm, methodology (e.g., calibration procedure, quality control check)
- **AggregateProcess** - Multi-step workflow with connected processing steps (e.g., data processing chain)

**Rule:** Use Physical* types for hardware/human observers, use *Process types for software/simulations (Requirement 95)

#### 2.3 Component Type Properties Summary

| Type                  | Extends                 | Key Properties                                           | Use Cases                             |
| --------------------- | ----------------------- | -------------------------------------------------------- | ------------------------------------- |
| **SimpleProcess**     | AbstractProcess         | `method` (algorithm, description)                        | Software processes, simple procedures |
| **AggregateProcess**  | AbstractProcess         | `components` (sub-processes), `connections` (data links) | Composite processes, workflows        |
| **PhysicalComponent** | AbstractPhysicalProcess | `method`, `attachedTo`, `position`                       | Individual hardware elements          |
| **PhysicalSystem**    | AbstractPhysicalProcess | `components`, `connections`, `attachedTo`, `position`    | Hardware systems with subsystems      |

---

### 3. Minimal SensorML Subset for CSAPI

#### 3.1 Required Properties (All Types)

**From DescribedObject (Base Class):**

- `type` (string, required) - Component type (`SimpleProcess`, `PhysicalSystem`, etc.)
- `label` (string, required) - Human-readable name
- `uniqueId` (string, format: uri, required) - Globally unique identifier (typically URN)

**From AbstractProcess (Systems/Procedures):**

- `definition` (string, format: uri, required for systems) - Type/ontology reference (e.g., `http://www.w3.org/ns/sosa/Sensor`)

**Additional Required (Per CSAPI):**

- `id` (string, optional but strongly recommended) - Local ID for resource
- `validTime` (array of 2 date-times, optional) - Temporal validity `[startTime, endTime]`, `null` for open-ended
- `links` (array, optional but recommended) - Navigation links

**Example Minimal PhysicalSystem:**

```json
{
  "type": "PhysicalSystem",
  "id": "sensor123",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueId": "urn:x-sensor:id:sensor123",
  "label": "Temperature Sensor TS-001",
  "validTime": ["2024-01-01T00:00:00Z", null]
}
```

#### 3.2 Optional Properties (Rich Metadata)

**Identification:**

- `description` (string) - Detailed description
- `keywords` (array of strings) - Discovery keywords
- `identifiers` (array of Term) - Additional IDs (short name, serial number, model number)
- `classifiers` (array of Term) - Type classifiers (sensor type, process type, application)

**Process Metadata:**

- `typeOf` (Link) - Reference to base process/datasheet (e.g., manufacturer's model description)
- `configuration` (Settings) - Value settings constraining base process
- `featuresOfInterest` (array of Links) - Relevant domain features
- `inputs` (array) - Process inputs with SWE Common component definitions
- `outputs` (array) - Process outputs with SWE Common component definitions
- `parameters` (array) - Process parameters with SWE Common definitions
- `modes` (array) - Operating modes with different parameter sets

**Physical Process Metadata (Physical\* types only):**

- `attachedTo` (Link) - Parent platform/system
- `position` (Point, Pose, Text, or DataStream link) - Spatial location
- `localReferenceFrames` (array of SpatialFrame) - Local coordinate systems
- `localTimeFrames` (array of TemporalFrame) - Local time references

**Characteristics/Capabilities:**

- `characteristics` (array of CharacteristicList) - Physical characteristics (size, weight, power, etc.)
- `capabilities` (array of CapabilityList) - Operational capabilities (measurement range, accuracy, resolution, etc.)

**Contacts/Documentation:**

- `contacts` (array of ResponsibleParty) - Manufacturers, operators, maintainers
- `documents` (array of Document) - User manuals, datasheets, specifications
- `history` (array of Event) - Lifecycle events (deployment, calibration, maintenance)

**Legal/Security:**

- `legalConstraints` (array) - Copyright, licensing, usage restrictions
- `securityConstraints` (array) - Security classification

**Composite Types (PhysicalSystem, AggregateProcess):**

- `components` (array) - Sub-components/sub-processes with names
- `connections` (array) - Data flow connections between component inputs/outputs

---

### 4. Inputs, Outputs, and Parameters

#### 4.1 IO Component Structure

**Format:**

```json
{
  "inputs": [
    {
      "name": "airTemperature",
      "definition": "http://sweet.jpl.nasa.gov/ontology/property/Temperature",
      "type": "Quantity",
      "uom": {
        "code": "Cel"
      }
    }
  ],
  "outputs": [
    {
      "name": "temperature",
      "definition": "http://sweet.jpl.nasa.gov/ontology/property/Temperature",
      "type": "Quantity",
      "uom": {
        "code": "Cel"
      },
      "constraint": {
        "interval": [-40, 85]
      }
    }
  ],
  "parameters": [
    {
      "name": "samplingRate",
      "label": "Sampling Rate",
      "type": "Quantity",
      "uom": {
        "code": "Hz"
      },
      "value": 1.0
    }
  ]
}
```

**IO Component Types (from SWE Common):**

- **Quantity** - Numeric value with unit of measure
- **Count** - Integer value
- **Boolean** - True/false
- **Text** - String value
- **Category** - Categorical value from controlled vocabulary
- **Time** - Temporal value
- **DataRecord** - Composite structured data
- **DataArray** - Array of values
- **Vector** - Multi-dimensional vector
- **Matrix** - Multi-dimensional matrix

**Required Properties:**

- `name` (string) - IO component name (used in data records, connections)
- `type` (string) - SWE Common component type

**Optional Properties:**

- `definition` (uri) - Semantic definition (observable property, parameter type)
- `label` (string) - Human-readable label
- `description` (string) - Detailed description
- `uom` (object) - Unit of measure (with `code` property)
- `constraint` (object) - Value constraints (interval, allowedValues, etc.)
- `value` (any) - Current/default value (for parameters)
- `quality` (array) - Quality metadata

#### 4.2 Connections (Composite Types)

**Purpose:** Explicitly define data flow between component inputs/outputs

**Structure:**

```json
{
  "connections": [
    {
      "source": {
        "ref": "components/thermometer/outputs/temperature"
      },
      "destination": {
        "ref": "outputs/airTemperature"
      }
    },
    {
      "source": {
        "ref": "components/barometer/outputs/pressure"
      },
      "destination": {
        "ref": "outputs/atmosphericPressure"
      }
    }
  ]
}
```

**Required:**

- `source` (PathRef) - JSON path to source output
- `destination` (PathRef) - JSON path to destination input

**Used in:** PhysicalSystem, AggregateProcess with `components`

---

### 5. Identification, Classification, Characteristics, Capabilities

#### 5.1 Identifiers

**Purpose:** Additional identifiers for discovery beyond `uniqueId`

**Structure:**

```json
{
  "identifiers": [
    {
      "definition": "http://sensorml.com/ont/swe/property/ShortName",
      "label": "Short Name",
      "value": "TS-001"
    },
    {
      "definition": "http://sensorml.com/ont/swe/property/SerialNumber",
      "label": "Serial Number",
      "value": "SN-123456789"
    },
    {
      "definition": "http://sensorml.com/ont/swe/property/ModelNumber",
      "label": "Model Number",
      "value": "TS-2000"
    }
  ]
}
```

**Term Properties:**

- `definition` (uri, required) - Property type
- `label` (string) - Human-readable label
- `value` (string, required) - Identifier value

**Common Identifier Types:** Short name, serial number, model number, manufacturer part number, mission ID, platform ID

#### 5.2 Classifiers

**Purpose:** Type classification for discovery

**Structure:**

```json
{
  "classifiers": [
    {
      "definition": "http://www.opengis.net/def/property/OGC/0/SensorType",
      "label": "Sensor Type",
      "value": "Thermometer"
    },
    {
      "definition": "http://www.opengis.net/def/property/OGC/0/IntendedApplication",
      "label": "Intended Application",
      "value": "Weather Monitoring"
    }
  ]
}
```

**Common Classifier Types:** Sensor type, actuator type, platform type, process type, intended application, domain

#### 5.3 Characteristics

**Purpose:** Physical/non-operational properties (size, weight, power consumption)

**Structure:**

```json
{
  "characteristics": [
    {
      "name": "physicalProperties",
      "label": "Physical Properties",
      "characteristics": [
        {
          "name": "weight",
          "label": "Weight",
          "type": "Quantity",
          "uom": { "code": "kg" },
          "value": 0.5
        },
        {
          "name": "dimensions",
          "label": "Dimensions",
          "type": "Vector",
          "referenceFrame": "http://www.opengis.net/def/crs/OGC/0/ENU_LOCAL",
          "coordinates": ["length", "width", "height"],
          "uom": { "code": "m" },
          "value": [0.1, 0.05, 0.03]
        },
        {
          "name": "powerRequirement",
          "label": "Power Requirement",
          "type": "Quantity",
          "uom": { "code": "W" },
          "value": 2.5
        }
      ]
    }
  ]
}
```

**CharacteristicList Properties:**

- `name` (string) - Group name
- `label` (string) - Human-readable label
- `definition` (uri, optional) - Group semantic definition
- `conditions` (array, optional) - Conditions under which characteristics apply
- `characteristics` (array, required) - SWE Common components describing characteristics

**Common Characteristics:** Physical properties (weight, size, power), material properties, environmental tolerances, storage requirements

#### 5.4 Capabilities

**Purpose:** Operational performance properties (measurement range, accuracy, resolution)

**Structure:**

```json
{
  "capabilities": [
    {
      "name": "measurementProperties",
      "label": "Measurement Properties",
      "capabilities": [
        {
          "name": "measurementRange",
          "label": "Measurement Range",
          "type": "QuantityRange",
          "uom": { "code": "Cel" },
          "value": [-40, 85]
        },
        {
          "name": "accuracy",
          "label": "Accuracy",
          "type": "Quantity",
          "uom": { "code": "Cel" },
          "value": 0.1
        },
        {
          "name": "resolution",
          "label": "Resolution",
          "type": "Quantity",
          "uom": { "code": "Cel" },
          "value": 0.01
        },
        {
          "name": "responseTime",
          "label": "Response Time",
          "type": "Quantity",
          "uom": { "code": "s" },
          "value": 30
        }
      ]
    }
  ]
}
```

**CapabilityList Properties:** Same structure as CharacteristicList

**Common Capabilities:** Measurement range, accuracy, precision, resolution, sensitivity, response time, bandwidth, dynamic range

---

### 6. Client Library Parsing Requirements

#### 6.1 Parse vs Opaque Handling

**Recommended Approach: Hybrid Parsing**

**What to Parse (Required):**

- `type`, `id`, `definition`, `uniqueId`, `label`, `description` - Core identification
- `validTime` - Temporal validity
- `links` - Navigation
- `typeOf` - Datasheet/base process reference
- Top-level arrays: `identifiers`, `classifiers`, `inputs`, `outputs`, `parameters`

**What to Preserve Semi-Opaquely:**

- `characteristics`, `capabilities` - Parse structure (name, label, definition), preserve component details
- `components`, `connections` - Parse references, preserve detailed schemas
- `position` - Parse type (Point, Pose, Text), preserve structure
- `contacts`, `documents`, `history` - Preserve as objects

**What to Ignore (Optional Extensions):**

- `configuration`, `modes` - Advanced features
- `localReferenceFrames`, `localTimeFrames` - Specialized positioning
- `legalConstraints`, `securityConstraints` - Specialized metadata

**Rationale:**

- Client needs core metadata for display (label, description, identifiers)
- Client needs IO definitions for understanding system capabilities
- Client needs links for navigation
- Full SWE Common parsing is complex (defer to specialized libraries)
- Preserve extensibility for unknown properties

#### 6.2 TypeScript Type Definitions

**Base SensorML Types:**

```typescript
// Base type for all SensorML objects
interface DescribedObject {
  type: string; // Component type
  id?: string; // Local ID
  uniqueId: string; // Global URI identifier
  label: string; // Human-readable name
  description?: string;
  lang?: string;
  keywords?: string[];
  identifiers?: Term[];
  classifiers?: Term[];
  validTime?: [string, string | null]; // [start, end]
  legalConstraints?: any[];
  securityConstraints?: any[];
  characteristics?: CharacteristicList[];
  capabilities?: CapabilityList[];
  contacts?: (ResponsibleParty | Link)[];
  documents?: Document[];
  history?: Event[];
}

// Term for identifiers/classifiers
interface Term {
  definition: string; // URI
  label?: string;
  value: string;
}

// Process types
interface AbstractProcess extends DescribedObject {
  definition: string; // Type URI
  typeOf?: Link; // Reference to base process
  configuration?: Settings;
  featuresOfInterest?: Link[];
  inputs?: IOComponent[];
  outputs?: IOComponent[];
  parameters?: IOComponent[];
  modes?: Mode[];
}

interface SimpleProcess extends AbstractProcess {
  type: 'SimpleProcess';
  method?: ProcessMethod;
}

interface AggregateProcess extends AbstractProcess {
  type: 'AggregateProcess';
  components: Component[]; // Named sub-processes
  connections?: Connection[];
}

// Physical types
interface AbstractPhysicalProcess extends AbstractProcess {
  attachedTo?: Link;
  position?: Position;
  localReferenceFrames?: SpatialFrame[];
  localTimeFrames?: TemporalFrame[];
}

interface PhysicalComponent extends AbstractPhysicalProcess {
  type: 'PhysicalComponent';
  method?: ProcessMethod;
}

interface PhysicalSystem extends AbstractPhysicalProcess {
  type: 'PhysicalSystem';
  components?: Component[];
  connections?: Connection[];
}

// Union type for all system types
type SystemSensorML =
  | PhysicalSystem
  | PhysicalComponent
  | SimpleProcess
  | AggregateProcess;

// Union type for all procedure types
type ProcedureSensorML = SimpleProcess | AggregateProcess;
```

**IO Components (Simplified):**

```typescript
interface IOComponent {
  name: string;
  type: string; // SWE Common type
  label?: string;
  description?: string;
  definition?: string; // URI
  uom?: UnitOfMeasure;
  constraint?: any; // SWE Common constraint
  value?: any; // For parameters
  quality?: any[];
  [key: string]: any; // Allow SWE Common extensions
}

interface UnitOfMeasure {
  code: string; // UCUM code
  href?: string;
}
```

**Characteristics/Capabilities (Simplified):**

```typescript
interface CharacteristicList {
  name?: string;
  label?: string;
  definition?: string;
  conditions?: any[];
  characteristics: IOComponent[]; // SWE Common components
}

interface CapabilityList {
  name?: string;
  label?: string;
  definition?: string;
  conditions?: any[];
  capabilities: IOComponent[]; // SWE Common components
}
```

**Components/Connections:**

```typescript
interface Component {
  name: string;
  component: SystemSensorML | Link;
}

interface Connection {
  source: PathRef;
  destination: PathRef;
}

interface PathRef {
  ref: string; // JSON path (e.g., "components/sensor1/outputs/temperature")
}
```

#### 6.3 Validation Requirements

**Client-Side Validation:**

**Required Property Validation:**

- Validate `type` is one of: SimpleProcess, AggregateProcess, PhysicalComponent, PhysicalSystem
- Validate `label` is non-empty string
- Validate `uniqueId` is valid URI
- Validate `definition` is valid URI (for systems)
- Validate `validTime` array has 2 elements, first is date-time, second is date-time or null

**Type-Specific Validation:**

- PhysicalSystem: If `components` exists, validate each component has `name` and valid `component`
- AggregateProcess: If `components` exists, validate minItems 1
- Connections: Validate `source` and `destination` have `ref` property

**IO Component Validation:**

- Validate `name` is non-empty
- Validate `type` is valid SWE Common type
- If `uom` exists, validate `code` is present

**Error Handling:**

- Throw `ValidationError` for malformed SensorML
- Include specific validation failure details
- Provide JSON path to error location

---

### 7. SensorML Extensions and Profiles

#### 7.1 CSAPI Extensions

**Additional Properties Beyond SensorML 3.0:**

- `links` (array of Link) - OGC API link relations (not in core SensorML)
- `id` (string) - Local resource ID (CSAPI-specific)

**Link Relations Used:**

- `canonical` - Canonical URL of resource
- `alternate` - Alternate format (GeoJSON)
- `ogc-rel:subsystems` - Subsystems collection
- `ogc-rel:deployments` - Deployments involving system
- `ogc-rel:samplingFeatures` - Associated sampling features
- `ogc-rel:procedures` - Implemented procedures
- `ogc-rel:datastreams` - Associated data streams (Part 2)
- `ogc-rel:controlStreams` - Associated control streams (Part 2)

#### 7.2 SensorML 3.0 vs Previous Versions

**SensorML 3.0 Changes:**

- JSON encoding (vs XML in 2.0)
- Simplified schema structure
- Integrated SWE Common 3.0 components
- GeoPose support for positioning
- Removed deprecated elements

**Client Library:** Support SensorML 3.0 JSON only, not XML or previous versions

---

### 8. Handling Complex SensorML Documents

#### 8.1 Nested Components

**Challenge:** PhysicalSystem can have deep component hierarchies

**Example:**

```json
{
  "type": "PhysicalSystem",
  "label": "Weather Station",
  "components": [
    {
      "name": "temperatureSensor",
      "component": {
        "type": "PhysicalComponent",
        "label": "Thermometer",
        "outputs": [...]
      }
    },
    {
      "name": "humiditySensor",
      "component": {
        "type": "PhysicalComponent",
        "label": "Hygrometer",
        "outputs": [...]
      }
    },
    {
      "name": "dataLogger",
      "component": {
        "type": "PhysicalSystem",
        "label": "Data Logger",
        "components": [...] // Further nesting
      }
    }
  ]
}
```

**Client Library Approach:**

- Parse top-level component list
- Extract component names and types
- Preserve nested component structures as objects
- Provide recursive traversal utilities if needed

#### 8.2 Component References (Links)

**Challenge:** Components can reference external resources via links

**Example:**

```json
{
  "components": [
    {
      "name": "thermometer",
      "component": {
        "type": "Link",
        "rel": "canonical",
        "href": "https://api.example.org/systems/therm-123"
      }
    }
  ]
}
```

**Client Library Approach:**

- Detect `type: "Link"` in component
- Provide link resolution utilities
- Cache resolved components to avoid repeated fetches
- Support both inline and referenced components

#### 8.3 SWE Common Components

**Challenge:** Inputs/outputs/parameters use SWE Common data components with complex schemas

**Client Library Approach:**

- Parse basic SWE Common types (Quantity, Count, Boolean, Text, Category, Time)
- Preserve complex types (DataRecord, DataArray, Vector, Matrix) as objects
- Provide minimal validation (type, name, uom)
- **Defer to external SWE Common library** for full parsing/validation/encoding (e.g., `swe-common-js`)

---

### 9. Client API Implications

#### 9.1 Format Negotiation

**Requesting SensorML:**

```typescript
// Option 1: Accept header
const system = await client.getSystem('sensor123', {
  headers: { Accept: 'application/sml+json' },
});

// Option 2: Query parameter
const system = await client.getSystem('sensor123', {
  format: 'sensorml',
});

// Option 3: Convenience method
const system = await client.getSystemAsSensorML('sensor123');
```

**Accept Header vs Query Parameter:**

- Accept header: `Accept: application/sml+json`
- Query parameter: `?f=sml` or `?format=application/sml+json`
- Query parameter takes precedence (per OGC API – Common)

#### 9.2 Response Type Handling

**TypeScript Return Types:**

```typescript
class CSAPIClient {
  // Generic method - format determined at runtime
  async getSystem(
    id: string,
    options?: {
      format?: 'json' | 'geojson' | 'sensorml';
      headers?: Record<string, string>;
    }
  ): Promise<System | SystemGeoJSON | SystemSensorML>;

  // Format-specific methods - explicit return types
  async getSystemAsSensorML(id: string): Promise<SystemSensorML>;
  async getProcedureAsSensorML(id: string): Promise<ProcedureSensorML>;
  async getDeploymentAsSensorML(id: string): Promise<DeploymentSensorML>;

  // Collection endpoints
  async getSystemsAsSensorML(
    options?: QueryOptions
  ): Promise<SystemSensorMLCollection>;
}
```

#### 9.3 Write Operations

**Creating System with SensorML:**

```typescript
const newSystem = await client.createSystem(
  {
    type: 'PhysicalSystem',
    definition: 'http://www.w3.org/ns/sosa/Sensor',
    uniqueId: 'urn:x-sensor:id:new-sensor',
    label: 'New Temperature Sensor',
    position: {
      type: 'Point',
      coordinates: [-122.08, 37.42, 25.5],
    },
    outputs: [
      {
        name: 'temperature',
        type: 'Quantity',
        definition: 'http://sweet.jpl.nasa.gov/ontology/property/Temperature',
        uom: { code: 'Cel' },
      },
    ],
  },
  {
    format: 'sensorml',
  }
);
```

**Updating System:**

```typescript
const system = await client.getSystemAsSensorML('sensor123');
system.label = 'Updated Sensor Name';
system.description = 'Updated description';
await client.updateSystem('sensor123', system, { format: 'sensorml' });
```

#### 9.4 Metadata Extraction Utilities

**Common Operations:**

```typescript
// Extract all identifiers
function getIdentifier(
  system: SystemSensorML,
  definition: string
): string | undefined {
  return system.identifiers?.find((id) => id.definition === definition)?.value;
}

const serialNumber = getIdentifier(
  system,
  'http://sensorml.com/ont/swe/property/SerialNumber'
);

// Extract all classifiers
function getClassifier(
  system: SystemSensorML,
  definition: string
): string | undefined {
  return system.classifiers?.find((c) => c.definition === definition)?.value;
}

const sensorType = getClassifier(
  system,
  'http://www.opengis.net/def/property/OGC/0/SensorType'
);

// Extract output definitions
function getOutputs(system: SystemSensorML): string[] {
  return system.outputs?.map((o) => o.definition).filter(Boolean) || [];
}

// Extract capabilities by name
function getCapability(system: SystemSensorML, capabilityName: string): any {
  for (const capList of system.capabilities || []) {
    const cap = capList.capabilities.find((c) => c.name === capabilityName);
    if (cap) return cap.value;
  }
  return undefined;
}

const measurementRange = getCapability(system, 'measurementRange');
```

---

### 10. Error Handling

#### 10.1 Format-Related Errors

**Unsupported Format Error:**

```typescript
class UnsupportedFormatError extends Error {
  constructor(
    public requestedFormat: string,
    public availableFormats: string[]
  ) {
    super(
      `Format '${requestedFormat}' not supported. Available: ${availableFormats.join(
        ', '
      )}`
    );
  }
}

// Server returns 406 Not Acceptable
if (response.status === 406) {
  throw new UnsupportedFormatError('application/sml+json', [
    'application/json',
    'application/geo+json',
  ]);
}
```

**Malformed SensorML Error:**

```typescript
class MalformedSensorMLError extends Error {
  constructor(public jsonPath: string, public validationError: string) {
    super(`Invalid SensorML at ${jsonPath}: ${validationError}`);
  }
}

// Example
throw new MalformedSensorMLError(
  'outputs[0]',
  'Output must have "name" property'
);
```

#### 10.2 Type Validation

**Validate System Type:**

```typescript
function validateSystemType(system: any): void {
  const validTypes = [
    'SimpleProcess',
    'AggregateProcess',
    'PhysicalComponent',
    'PhysicalSystem',
  ];
  if (!validTypes.includes(system.type)) {
    throw new MalformedSensorMLError(
      'type',
      `System type must be one of: ${validTypes.join(', ')}, got "${
        system.type
      }"`
    );
  }
}
```

**Validate Required Properties:**

```typescript
function validateRequiredProperties(system: any): void {
  if (!system.label) {
    throw new MalformedSensorMLError('label', 'label is required');
  }
  if (!system.uniqueId) {
    throw new MalformedSensorMLError('uniqueId', 'uniqueId is required');
  }
  // Systems require definition
  if (
    ['PhysicalSystem', 'PhysicalComponent'].includes(system.type) &&
    !system.definition
  ) {
    throw new MalformedSensorMLError(
      'definition',
      'definition is required for systems'
    );
  }
}
```

---

### 11. Dependencies and Libraries

#### 11.1 Recommended External Libraries

**SWE Common Parsing:**

- **@ogc/swe-common** (if exists) - SWE Common 3.0 parsing/validation
- **Custom SWE Common utilities** - Minimal parsing for Quantity, Count, Text, etc.

**Schema Validation:**

- **ajv** - JSON Schema validator for SensorML 3.0 schema validation
- Load SensorML 3.0 JSON Schema from `https://schemas.opengis.net/sensorml/3.0/sensorml.json`

**Usage:**

```typescript
import Ajv from 'ajv';
import sensorMLSchema from 'sensorml-schema.json';

const ajv = new Ajv();
const validate = ajv.compile(sensorMLSchema);

function validateSensorML(document: any): boolean {
  const valid = validate(document);
  if (!valid) {
    throw new MalformedSensorMLError('', ajv.errorsText(validate.errors));
  }
  return true;
}
```

#### 11.2 Built-in vs External

**Built-in (Client Library):**

- TypeScript type definitions for SensorML component types
- Basic parsing (JSON.parse)
- Format negotiation (Accept header, query param)
- Core property extraction (label, uniqueId, identifiers, classifiers, inputs, outputs)
- Link extraction and navigation

**External Libraries (Optional Dependencies):**

- Schema validation (ajv)
- SWE Common parsing (custom or external library)
- Unit conversion (if needed for capabilities/characteristics)

**Rationale:** Keep core library lightweight, provide SensorML type definitions, defer complex SWE Common parsing to specialized libraries.

---

## Summary

**Section 3.3 Complete:** SensorML Format Requirements (~700 lines documenting all SensorML aspects)

### Key Requirements

**Resources Supporting SensorML:**

- Part 1: Systems (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess), Procedures (SimpleProcess, AggregateProcess), Deployments, Properties
- Part 2: Not directly used (JSON/SWE Common instead)

**Component Types:**

- **PhysicalSystem** - Hardware systems with components
- **PhysicalComponent** - Individual hardware elements
- **SimpleProcess** - Software processes, simple procedures
- **AggregateProcess** - Composite processes with connections
- **Deployment** - Deployment descriptions

**Minimal Subset:**

- Required: type, label, uniqueId
- Recommended: id, definition, description, validTime, links
- Optional: identifiers, classifiers, inputs, outputs, parameters, characteristics, capabilities, contacts, documents

**Rich Metadata:**

- Identification: identifiers (serial number, model number), classifiers (sensor type, application)
- Process: inputs, outputs, parameters with SWE Common definitions
- Physical: position, attachedTo, localReferenceFrames
- Performance: characteristics (physical properties), capabilities (measurement range, accuracy, resolution)
- Composite: components (sub-systems), connections (data flow)

**Client Library Must:**

- Parse core SensorML properties (type, label, uniqueId, definition, validTime)
- Extract identifiers, classifiers for discovery
- Extract inputs, outputs, parameters for capability understanding
- Parse links for navigation
- Support format negotiation
- Validate required properties and types
- Provide TypeScript types for all component types

**Complex Handling:**

- Nested components (recursive structures)
- Component references (Links to external resources)
- SWE Common components (defer to external library for full parsing)
- Preserve unknown properties for extensibility

**Optional (External Libraries):**

- Full SWE Common parsing/validation
- JSON Schema validation against SensorML 3.0 schema
- Unit conversion

**Ready for Section 3.4:** SWE Common Format Requirements

---

## Section 3.4: SWE Common Format Requirements

**Date:** 2026-01-31  
**Status:** Complete

### Overview

SWE Common Data Model 3.0 provides standardized formats for encoding observation results, command parameters, and structured sensor data in CSAPI Part 2. It supports multiple encodings (JSON, Text/CSV, Binary) optimized for different use cases from human readability to high-frequency data transmission.

**Media Types:**

- `application/swe+json` - JSON encoding
- `application/swe+csv` - CSV/Text encoding
- `application/swe+binary` - Binary encoding

**Standard References:**

- [SWE Common Data Model 3.0 Specification](https://docs.ogc.org/is/18-003r2/18-003r2.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - Observations and Commands encoding
- [SWE Common 3.0 JSON Schema](https://schemas.opengis.net/sweCommon/3.0/sweCommon.json)

---

### 1. CSAPI Resources Using SWE Common

#### 1.1 Part 2 Dynamic Data Resources

**Observations (Required):**

- **Result Schema:** DataStream defines `resultSchema` as SWE Common DataRecord/DataArray
- **Result Data:** Observation `result` field encoded per DataStream `encoding` specification
- **Formats:** JSON (application/swe+json), CSV (application/swe+csv), Binary (application/swe+binary)
- **Use Case:** Sensor measurements, time series data, complex observations

**Commands (Required):**

- **Parameters Schema:** ControlStream defines `parametersSchema` as SWE Common DataRecord
- **Parameters Data:** Command `parameters` field encoded per ControlStream `encoding`
- **Result Schema:** ControlStream defines `resultSchema` for command results (optional)
- **Formats:** JSON (application/swe+json), CSV (application/swe+csv)
- **Use Case:** Actuator control parameters, configuration commands

**DataStreams (Metadata):**

- **Schema Definition:** `resultSchema` property defines observation structure
- **Encoding Definition:** `encoding` property specifies how observations are serialized
- **Not Data:** DataStream itself uses JSON, not SWE Common encoding

**ControlStreams (Metadata):**

- **Schema Definition:** `parametersSchema` and `resultSchema` properties
- **Encoding Definition:** `encoding` property specifies command/result serialization
- **Not Data:** ControlStream itself uses JSON

#### 1.2 Part 1 Resources (Limited Use)

**Systems/Procedures (SensorML):**

- SensorML inputs/outputs/parameters use SWE Common component definitions
- SWE Common types: Quantity, Count, Boolean, Text, Category, Time, DataRecord, Vector, Matrix
- Inline definitions only (not separate encoding)

**Not Applicable:**

- Deployments, Sampling Features, Properties - Do not use SWE Common

---

### 2. SWE Common Data Components Required

#### 2.1 Simple Components (Scalars)

**Quantity:**

- Numeric value with unit of measure
- Used for: Temperature, pressure, voltage, length, etc.
- Properties: `value` (number), `uom` (unit), `constraint` (range), `nilValues`
- Example: `{"type": "Quantity", "value": 23.5, "uom": {"code": "Cel"}}`

**Count:**

- Integer value
- Used for: Counters, indices, discrete quantities
- Properties: `value` (integer), `constraint` (range, allowedValues)
- Example: `{"type": "Count", "value": 42}`

**Boolean:**

- True/false value
- Used for: Flags, status indicators, binary states
- Properties: `value` (boolean)
- Example: `{"type": "Boolean", "value": true}`

**Text:**

- String value
- Used for: Descriptions, codes, identifiers
- Properties: `value` (string), `constraint` (pattern, allowedValues)
- Example: `{"type": "Text", "value": "CLEAR_SKY"}`

**Category:**

- Categorical value from controlled vocabulary
- Used for: Enumerated types, classification codes
- Properties: `value` (string), `codeSpace` (vocabulary URI), `constraint` (allowedValues)
- Example: `{"type": "Category", "value": "cloudy", "codeSpace": "http://example.org/weather-codes"}`

**Time:**

- Temporal value (instant or period)
- Used for: Timestamps, time instants, durations
- Properties: `value` (ISO 8601 string), `referenceFrame` (time system), `uom` (for durations)
- Example: `{"type": "Time", "value": "2024-01-15T12:00:00Z"}`

#### 2.2 Composite Components (Structures)

**DataRecord:**

- Ordered collection of named fields
- Used for: Structured observations, multi-parameter results
- Properties: `fields` (array of named components)
- Fields: Each field has `name`, `type`, and component-specific properties
- Example:
  ```json
  {
    "type": "DataRecord",
    "fields": [
      { "name": "time", "type": "Time", "value": "2024-01-15T12:00:00Z" },
      {
        "name": "temp",
        "type": "Quantity",
        "value": 23.5,
        "uom": { "code": "Cel" }
      },
      {
        "name": "humidity",
        "type": "Quantity",
        "value": 65.0,
        "uom": { "code": "%" }
      }
    ]
  }
  ```

**DataArray:**

- Array of values with same component type
- Used for: Time series, arrays of measurements, matrices
- Properties: `elementType` (component schema), `values` (array), `elementCount` (size)
- Example:
  ```json
  {
    "type": "DataArray",
    "elementCount": { "type": "Count", "value": 3 },
    "elementType": { "type": "Quantity", "uom": { "code": "Cel" } },
    "values": [23.5, 24.1, 23.8]
  }
  ```

**Vector:**

- Multi-dimensional vector with labeled axes
- Used for: Position (x,y,z), velocity, acceleration, orientation
- Properties: `coordinates` (array of Quantity components), `referenceFrame` (CRS/coordinate system)
- Example:
  ```json
  {
    "type": "Vector",
    "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4979",
    "coordinates": [
      {
        "name": "lat",
        "type": "Quantity",
        "axisID": "Lat",
        "uom": { "code": "deg" },
        "value": 37.42
      },
      {
        "name": "lon",
        "type": "Quantity",
        "axisID": "Lon",
        "uom": { "code": "deg" },
        "value": -122.08
      },
      {
        "name": "h",
        "type": "Quantity",
        "axisID": "h",
        "uom": { "code": "m" },
        "value": 25.5
      }
    ]
  }
  ```

**Matrix:**

- 2D matrix of values
- Used for: Images, grids, correlation matrices
- Properties: `elementType` (component schema), `values` (2D array), `elementCount` (dimensions)
- Less common in CSAPI

#### 2.3 Component Type Matrix

| Component Type | Value Type        | Unit Support         | Primary Use Cases         |
| -------------- | ----------------- | -------------------- | ------------------------- |
| **Quantity**   | number            | Yes (required)       | Measurements with units   |
| **Count**      | integer           | No                   | Counters, indices         |
| **Boolean**    | boolean           | No                   | Flags, binary states      |
| **Text**       | string            | No                   | Descriptions, identifiers |
| **Category**   | string            | No (codeSpace)       | Enumerated types          |
| **Time**       | ISO 8601 string   | Yes (for durations)  | Timestamps, time periods  |
| **DataRecord** | object            | N/A                  | Multi-field structures    |
| **DataArray**  | array             | N/A                  | Homogeneous arrays        |
| **Vector**     | array of Quantity | Yes (per coordinate) | Multi-dimensional vectors |
| **Matrix**     | 2D array          | N/A                  | Grids, images             |

**All Components Required:** Client library MUST support all component types for observation/command parsing

---

### 3. SWE Common Encoding Formats

#### 3.1 JSON Encoding (application/swe+json)

**Purpose:** Human-readable, structured format preserving SWE Common semantics

**Media Type:** `application/swe+json`

**Structure:** JSON representation of SWE Common data components

**DataRecord Encoding Options:**

- **Object Mode (default):** Fields encoded as JSON object with field names as keys
  ```json
  {
    "time": "2024-01-15T12:00:00Z",
    "temp": 23.5,
    "humidity": 65.0
  }
  ```
- **Array Mode:** Fields encoded as JSON array (preserves order, more compact)
  ```json
  ["2024-01-15T12:00:00Z", 23.5, 65.0]
  ```

**JSONEncoding Configuration:**

```json
{
  "type": "JSONEncoding",
  "includeNilValues": false
}
```

**Properties:**

- `includeNilValues` (boolean, default: false) - Include nil values in output
- No additional encoding parameters (JSON is self-describing)

**Characteristics:**

- **Size:** Moderate (larger than CSV/Binary, smaller than plain JSON with full metadata)
- **Readability:** High (human-readable)
- **Efficiency:** Moderate
- **Best For:** Moderate-frequency data, debugging, development

#### 3.2 Text/CSV Encoding (application/swe+csv)

**Purpose:** Compact, human-readable tabular format

**Media Type:** `application/swe+csv` or `application/swe+text`

**Structure:** Delimited text (CSV-like) with configurable separators

**TextEncoding Configuration:**

```json
{
  "type": "TextEncoding",
  "tokenSeparator": ",",
  "blockSeparator": "\n",
  "decimalSeparator": ".",
  "collapseWhiteSpaces": true
}
```

**Properties:**

- `tokenSeparator` (string, default: ",") - Field delimiter (typically comma or tab)
- `blockSeparator` (string, default: "\n") - Record delimiter (typically newline)
- `decimalSeparator` (string, default: ".") - Decimal point character
- `collapseWhiteSpaces` (boolean, default: true) - Trim whitespace

**Example:**

```
2024-01-15T12:00:00Z,23.5,65.0
2024-01-15T12:01:00Z,23.6,64.8
2024-01-15T12:02:00Z,23.4,65.2
```

**Characteristics:**

- **Size:** Small (~2-5x smaller than JSON)
- **Readability:** High (spreadsheet-compatible)
- **Efficiency:** Good
- **Best For:** Time series data, batch processing, spreadsheet integration
- **Limitations:** No nested structures (DataRecord only), field order matters

#### 3.3 Binary Encoding (application/swe+binary)

**Purpose:** Maximum efficiency for high-frequency data

**Media Type:** `application/swe+binary`

**Structure:** Binary-packed data with schema-defined layout

**BinaryEncoding Configuration:**

```json
{
  "type": "BinaryEncoding",
  "byteOrder": "BIG_ENDIAN",
  "byteEncoding": "RAW",
  "members": [
    { "component": "fields/time", "dataType": "INT64", "byteLength": 8 },
    { "component": "fields/temp", "dataType": "FLOAT32", "byteLength": 4 },
    { "component": "fields/humidity", "dataType": "FLOAT32", "byteLength": 4 }
  ]
}
```

**Properties:**

- `byteOrder` (enum) - BIG_ENDIAN or LITTLE_ENDIAN
- `byteEncoding` (enum) - RAW (no compression) or BASE64 (for transmission)
- `members` (array) - Field-by-field encoding specification
  - `component` (string) - JSON path to component
  - `dataType` (enum) - INT8, INT16, INT32, INT64, UINT8, UINT16, UINT32, UINT64, FLOAT32, FLOAT64, UTF8
  - `byteLength` (integer) - Size in bytes

**Characteristics:**

- **Size:** Very small (~10-100x smaller than JSON)
- **Readability:** None (binary)
- **Efficiency:** Excellent
- **Best For:** High-frequency sensor data (>1 Hz), bandwidth-constrained applications, long-term storage
- **Limitations:** Requires schema for parsing, not human-readable, more complex implementation

**Byte Order Considerations:**

- Most modern systems use LITTLE_ENDIAN
- Network protocols typically use BIG_ENDIAN
- Client library MUST support both

#### 3.4 Encoding Selection Matrix

| Format     | Size       | Speed     | Readable | Best Use Case                                                      |
| ---------- | ---------- | --------- | -------- | ------------------------------------------------------------------ |
| **JSON**   | Large      | Moderate  | Yes      | Development, debugging, moderate-frequency (<0.1 Hz)               |
| **CSV**    | Small      | Fast      | Yes      | Batch processing, time series, spreadsheet integration (0.1-10 Hz) |
| **Binary** | Very Small | Very Fast | No       | High-frequency sensors (>10 Hz), bandwidth-constrained, archival   |

**Format Negotiation:**

```
GET /datastreams/ds123/observations
Accept: application/swe+binary
// Server returns observations in binary format
```

---

### 4. DataStream Schema Configuration

#### 4.1 resultSchema Property

**Purpose:** Defines structure of observation `result` field

**Type:** SWE Common DataRecord or DataArray

**Example:**

```json
{
  "type": "DataStream",
  "resultSchema": {
    "type": "DataRecord",
    "fields": [
      {
        "name": "time",
        "type": "Time",
        "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
        "referenceFrame": "http://www.opengis.net/def/trs/BIPM/0/UTC",
        "label": "Sampling Time",
        "uom": { "href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian" }
      },
      {
        "name": "temp",
        "type": "Quantity",
        "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
        "label": "Air Temperature",
        "uom": { "code": "Cel" },
        "constraint": { "interval": [-40, 85] },
        "nilValues": [
          {
            "reason": "http://www.opengis.net/def/nil/OGC/0/missing",
            "value": "NaN"
          },
          {
            "reason": "http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange",
            "value": "-Infinity"
          },
          {
            "reason": "http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange",
            "value": "+Infinity"
          }
        ]
      }
    ]
  },
  "encoding": {
    "type": "JSONEncoding"
  }
}
```

**Validation:**

- All observations in DataStream MUST conform to `resultSchema`
- Server rejects observations with invalid result (400 Bad Request)
- Schema cannot be changed if observations exist (409 Conflict)

#### 4.2 encoding Property

**Purpose:** Specifies how observation results are serialized

**Type:** JSONEncoding, TextEncoding, or BinaryEncoding

**Per-Format Schemas:**
DataStream can have different encoding per format:

```
GET /datastreams/ds123/schema?obsFormat=application/swe+json
GET /datastreams/ds123/schema?obsFormat=application/swe+csv
GET /datastreams/ds123/schema?obsFormat=application/swe+binary
```

Each returns appropriate `encoding` configuration for that format.

#### 4.3 Schema Evolution

**Challenge:** Cannot modify schema if observations exist

**Workarounds:**

1. **Create New DataStream:** New schema, migrate data if needed
2. **Versioned DataStreams:** Name includes version (ds-temp-v1, ds-temp-v2)
3. **Delete All Observations:** Clear data, update schema, re-ingest

**Client Library Implications:**

- Cache DataStream schemas to avoid repeated fetches
- Validate observation data against schema before POST
- Handle 409 Conflict errors on schema updates

---

### 5. Units of Measure (UoM)

#### 5.1 UCUM Code System

**Standard:** Unified Code for Units of Measure (UCUM)

**Format:**

```json
{
  "uom": {
    "code": "Cel" // UCUM code
  }
}
```

**Common UCUM Codes:**

- Temperature: `Cel` (Celsius), `[degF]` (Fahrenheit), `K` (Kelvin)
- Length: `m` (meter), `cm`, `mm`, `km`, `ft` (foot), `mi` (mile)
- Time: `s` (second), `min`, `h`, `d`, `a` (year)
- Speed: `m/s`, `km/h`, `mi/h`
- Percentage: `%`
- Angle: `deg` (degree), `rad` (radian)
- Frequency: `Hz`, `kHz`, `MHz`
- Pressure: `Pa`, `hPa`, `bar`, `atm`
- Mass: `kg`, `g`, `lb`

**UCUM Resources:**

- [UCUM Specification](https://ucum.org/)
- [UCUM Validator](https://ucum.org/ucum-lhc/demo.html)

#### 5.2 URI-Based Units

**Format:**

```json
{
  "uom": {
    "href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"
  }
}
```

**Usage:** Time units, specialized domains, OGC unit URIs

**Common URIs:**

- Time: `http://www.opengis.net/def/uom/ISO-8601/0/Gregorian`
- Angle: `http://www.opengis.net/def/uom/OGC/0/deg`

#### 5.3 Client Library UoM Handling

**Requirements:**

- **Parse:** Extract UoM code or href from components
- **Validate:** Check UCUM code syntax (optional, basic validation)
- **Preserve:** Maintain UoM in round-trip operations
- **Display:** Format units for user presentation

**Optional Features:**

- **Unit Conversion:** Convert between compatible units (e.g., Cel ↔ K)
- **Unit Validation:** Full UCUM validation against grammar
- **Unit Normalization:** Convert to canonical UCUM form

**Recommended External Library:** `ucum-js` or similar for unit operations

---

### 6. Nil Values and Quality

#### 6.1 Nil Values

**Purpose:** Represent missing, invalid, or special values

**Structure:**

```json
{
  "nilValues": [
    {
      "reason": "http://www.opengis.net/def/nil/OGC/0/missing",
      "value": "NaN"
    },
    {
      "reason": "http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange",
      "value": "-Infinity"
    },
    {
      "reason": "http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange",
      "value": "+Infinity"
    }
  ]
}
```

**Properties:**

- `reason` (uri) - Semantic reason for nil value
- `value` (any) - Special value representing nil (NaN, Infinity, null, sentinel number)

**Common Nil Reasons:**

- `missing` - Value not available
- `unknown` - Value cannot be determined
- `BelowDetectionRange` - Below sensor detection limit
- `AboveDetectionRange` - Above sensor detection limit
- `inapplicable` - Measurement not applicable
- `withheld` - Value withheld (privacy, security)

**Client Handling:**

- Detect nil values in observation data
- Display reason to user instead of raw value
- Filter out nil values for analysis (optional)
- Preserve nil values in round-trip

#### 6.2 Quality Metadata

**Purpose:** Attach quality indicators to component values

**Structure:**

```json
{
  "name": "temp",
  "type": "Quantity",
  "value": 23.5,
  "uom": { "code": "Cel" },
  "quality": [
    {
      "type": "Quantity",
      "definition": "http://www.opengis.net/def/property/OGC/0/Accuracy",
      "uom": { "code": "Cel" },
      "value": 0.1
    },
    {
      "type": "Category",
      "definition": "http://www.opengis.net/def/property/OGC/0/QualityFlag",
      "value": "GOOD"
    }
  ]
}
```

**Quality Types:**

- **Accuracy** - Measurement accuracy/uncertainty
- **Confidence** - Statistical confidence level
- **QualityFlag** - Categorical quality indicator (GOOD, FAIR, POOR, BAD)
- **Status** - Instrument status during measurement

**Client Handling:**

- Parse quality array
- Display quality alongside value
- Filter by quality for analysis
- Preserve in round-trip

---

### 7. Client Library Parsing Requirements

#### 7.1 Parse vs Opaque Handling

**Recommended Approach: Schema-Driven Parsing**

**What to Parse (Required):**

- **Schema Definitions:** Parse `resultSchema`/`parametersSchema` to understand structure
- **Component Types:** Identify Quantity, Count, Boolean, Text, Time, Category, DataRecord, DataArray, Vector
- **Component Properties:** Extract `name`, `type`, `uom`, `definition`, `label`, `constraint`
- **Encoding Configuration:** Parse `encoding` type and parameters
- **Data Values:** Parse observation/command data according to schema and encoding

**What to Preserve:**

- **Unknown Component Types:** Store as opaque objects for forward compatibility
- **Extension Properties:** Preserve unrecognized properties
- **Encoding Details:** Preserve full encoding configuration

**Rationale:**

- Client needs schema to validate data before POST
- Client needs to parse data values for display/analysis
- Schema-driven approach enables generic handling of any observation structure
- Preservation ensures round-trip fidelity

#### 7.2 TypeScript Type Definitions

**Base SWE Common Types:**

```typescript
// Base component interface
interface AbstractComponent {
  type: string;
  id?: string;
  definition?: string; // URI to observable property
  label?: string;
  description?: string;
  optional?: boolean;
  updatable?: boolean;
}

// Simple component types
interface Quantity extends AbstractComponent {
  type: 'Quantity';
  value?: number;
  uom: UnitOfMeasure;
  constraint?: QuantityConstraint;
  nilValues?: NilValue[];
  quality?: AbstractComponent[];
}

interface Count extends AbstractComponent {
  type: 'Count';
  value?: number;
  constraint?: CountConstraint;
}

interface Boolean extends AbstractComponent {
  type: 'Boolean';
  value?: boolean;
}

interface Text extends AbstractComponent {
  type: 'Text';
  value?: string;
  constraint?: TextConstraint;
}

interface Category extends AbstractComponent {
  type: 'Category';
  value?: string;
  codeSpace?: string; // URI to vocabulary
  constraint?: CategoryConstraint;
}

interface Time extends AbstractComponent {
  type: 'Time';
  value?: string; // ISO 8601
  referenceFrame?: string; // Time system URI
  uom?: UnitOfMeasure; // For durations
}

// Composite types
interface DataRecord extends AbstractComponent {
  type: 'DataRecord';
  fields: NamedComponent[];
}

interface DataArray extends AbstractComponent {
  type: 'DataArray';
  elementType: AbstractComponent;
  elementCount?: Count;
  values?: any[];
  encoding?: AbstractEncoding;
}

interface Vector extends AbstractComponent {
  type: 'Vector';
  referenceFrame?: string; // CRS URI
  coordinates: NamedComponent[]; // Array of Quantity
}

// Union type for all components
type SWEComponent =
  | Quantity
  | Count
  | Boolean
  | Text
  | Category
  | Time
  | DataRecord
  | DataArray
  | Vector;

// Named component (for DataRecord fields, Vector coordinates)
interface NamedComponent {
  name: string;
  component?: SWEComponent; // For nested structures
  // Or inline component properties:
  type?: string;
  value?: any;
  uom?: UnitOfMeasure;
  // ... other properties
}

// Unit of measure
interface UnitOfMeasure {
  code?: string; // UCUM code
  href?: string; // URI
}

// Nil value
interface NilValue {
  reason: string; // URI
  value: any; // Special value (NaN, Infinity, null, etc.)
}

// Constraints
interface QuantityConstraint {
  interval?: [number, number]; // [min, max]
  significantFigures?: number;
}

interface CountConstraint {
  interval?: [number, number];
  allowedValues?: number[];
}

interface TextConstraint {
  pattern?: string; // Regex
  length?: number;
}

interface CategoryConstraint {
  allowedValues?: string[];
}
```

**Encoding Types:**

```typescript
interface JSONEncoding {
  type: 'JSONEncoding';
  includeNilValues?: boolean;
}

interface TextEncoding {
  type: 'TextEncoding';
  tokenSeparator?: string;
  blockSeparator?: string;
  decimalSeparator?: string;
  collapseWhiteSpaces?: boolean;
}

interface BinaryEncoding {
  type: 'BinaryEncoding';
  byteOrder?: 'BIG_ENDIAN' | 'LITTLE_ENDIAN';
  byteEncoding?: 'RAW' | 'BASE64';
  members: BinaryMember[];
}

interface BinaryMember {
  component: string; // JSON path
  dataType:
    | 'INT8'
    | 'INT16'
    | 'INT32'
    | 'INT64'
    | 'UINT8'
    | 'UINT16'
    | 'UINT32'
    | 'UINT64'
    | 'FLOAT32'
    | 'FLOAT64'
    | 'UTF8';
  byteLength: number;
}

type AbstractEncoding = JSONEncoding | TextEncoding | BinaryEncoding;
```

**Observation Schema:**

```typescript
interface ObservationSchema {
  obsFormat: string; // Media type
  recordSchema: DataRecord; // Result schema
  encoding?: AbstractEncoding;
}
```

#### 7.3 Validation Requirements

**Schema Validation:**

- Validate observation `result` against DataStream `resultSchema`
- Check component types match schema
- Validate values within constraints (interval, allowedValues)
- Validate UoM codes (basic UCUM syntax)

**Encoding Validation:**

- Validate encoding type matches format
- Check required encoding parameters present
- Validate binary encoding members reference valid components

**Data Validation:**

- Validate values are correct type (number, string, boolean)
- Validate nil values match declared nilValues
- Validate array lengths match elementCount

**Error Handling:**

- Throw `ValidationError` with component path and specific error
- Example: "Invalid value for fields/temp: 150 exceeds maximum 85"

---

### 8. Encoding/Decoding Implementation

#### 8.1 JSON Encoding

**Encoding (DataRecord → JSON):**

```typescript
function encodeJSON(data: DataRecord, encoding: JSONEncoding): any {
  const result: any = {};
  for (const field of data.fields) {
    const value = getComponentValue(field);
    if (value !== undefined || encoding.includeNilValues) {
      result[field.name] = value;
    }
  }
  return result;
}

function getComponentValue(component: SWEComponent): any {
  switch (component.type) {
    case 'Quantity':
    case 'Count':
    case 'Boolean':
    case 'Text':
    case 'Category':
    case 'Time':
      return component.value;
    case 'DataRecord':
      return encodeJSON(component, { type: 'JSONEncoding' });
    case 'DataArray':
      return component.values;
    case 'Vector':
      return component.coordinates.map((c) => c.value);
    default:
      return component.value;
  }
}
```

**Decoding (JSON → DataRecord):**

```typescript
function decodeJSON(json: any, schema: DataRecord): DataRecord {
  const result: DataRecord = { ...schema, fields: [] };
  for (const fieldSchema of schema.fields) {
    const value = json[fieldSchema.name];
    const field = { ...fieldSchema };
    setComponentValue(field, value);
    result.fields.push(field);
  }
  return result;
}

function setComponentValue(component: SWEComponent, value: any): void {
  switch (component.type) {
    case 'Quantity':
    case 'Count':
      component.value = typeof value === 'number' ? value : parseFloat(value);
      break;
    case 'Boolean':
      component.value = !!value;
      break;
    case 'Text':
    case 'Category':
    case 'Time':
      component.value = String(value);
      break;
    case 'DataRecord':
      decodeJSON(value, component);
      break;
    case 'DataArray':
      component.values = Array.isArray(value) ? value : [];
      break;
    case 'Vector':
      if (Array.isArray(value)) {
        component.coordinates.forEach((coord, i) => {
          coord.value = value[i];
        });
      }
      break;
  }
}
```

#### 8.2 CSV Encoding

**Encoding (DataRecord → CSV):**

```typescript
function encodeCSV(data: DataRecord, encoding: TextEncoding): string {
  const values: string[] = [];
  for (const field of data.fields) {
    const value = formatCSVValue(getComponentValue(field), encoding);
    values.push(value);
  }
  return values.join(encoding.tokenSeparator || ',');
}

function formatCSVValue(value: any, encoding: TextEncoding): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number') {
    const str = value.toString();
    return str.replace('.', encoding.decimalSeparator || '.');
  }
  return String(value);
}
```

**Decoding (CSV → DataRecord):**

```typescript
function decodeCSV(
  csv: string,
  schema: DataRecord,
  encoding: TextEncoding
): DataRecord {
  const separator = encoding.tokenSeparator || ',';
  const tokens = csv.split(separator);

  if (encoding.collapseWhiteSpaces) {
    tokens.forEach((t, i) => (tokens[i] = t.trim()));
  }

  const result: DataRecord = { ...schema, fields: [] };
  schema.fields.forEach((fieldSchema, i) => {
    const field = { ...fieldSchema };
    const token = tokens[i] || '';
    const value = parseCSVValue(token, field.type, encoding);
    setComponentValue(field, value);
    result.fields.push(field);
  });

  return result;
}

function parseCSVValue(
  token: string,
  type: string,
  encoding: TextEncoding
): any {
  if (!token) return undefined;

  switch (type) {
    case 'Quantity':
    case 'Count':
      const normalized = token.replace(encoding.decimalSeparator || '.', '.');
      return parseFloat(normalized);
    case 'Boolean':
      return token.toLowerCase() === 'true' || token === '1';
    case 'Text':
    case 'Category':
    case 'Time':
      return token;
    default:
      return token;
  }
}
```

#### 8.3 Binary Encoding

**Encoding (DataRecord → Binary):**

```typescript
function encodeBinary(data: DataRecord, encoding: BinaryEncoding): ArrayBuffer {
  const buffer = new ArrayBuffer(calculateByteLength(data, encoding));
  const view = new DataView(buffer);

  let offset = 0;
  for (const member of encoding.members) {
    const component = resolveComponent(data, member.component);
    const value = getComponentValue(component);

    writeValue(view, offset, value, member, encoding);
    offset += member.byteLength;
  }

  return buffer;
}

function writeValue(
  view: DataView,
  offset: number,
  value: any,
  member: BinaryMember,
  encoding: BinaryEncoding
): void {
  const littleEndian = encoding.byteOrder === 'LITTLE_ENDIAN';

  switch (member.dataType) {
    case 'FLOAT32':
      view.setFloat32(offset, value, littleEndian);
      break;
    case 'FLOAT64':
      view.setFloat64(offset, value, littleEndian);
      break;
    case 'INT32':
      view.setInt32(offset, value, littleEndian);
      break;
    case 'INT64':
      view.setBigInt64(offset, BigInt(value), littleEndian);
      break;
    case 'UINT32':
      view.setUint32(offset, value, littleEndian);
      break;
    // ... other data types
  }
}
```

**Decoding (Binary → DataRecord):**

```typescript
function decodeBinary(
  buffer: ArrayBuffer,
  schema: DataRecord,
  encoding: BinaryEncoding
): DataRecord {
  const view = new DataView(buffer);
  const result: DataRecord = { ...schema, fields: [] };

  let offset = 0;
  for (const member of encoding.members) {
    const value = readValue(view, offset, member, encoding);
    const component = resolveComponent(schema, member.component);
    setComponentValue(component, value);
    offset += member.byteLength;
  }

  return result;
}

function readValue(
  view: DataView,
  offset: number,
  member: BinaryMember,
  encoding: BinaryEncoding
): any {
  const littleEndian = encoding.byteOrder === 'LITTLE_ENDIAN';

  switch (member.dataType) {
    case 'FLOAT32':
      return view.getFloat32(offset, littleEndian);
    case 'FLOAT64':
      return view.getFloat64(offset, littleEndian);
    case 'INT32':
      return view.getInt32(offset, littleEndian);
    case 'INT64':
      return Number(view.getBigInt64(offset, littleEndian));
    case 'UINT32':
      return view.getUint32(offset, littleEndian);
    // ... other data types
  }
}
```

---

### 9. Client API Implications

#### 9.1 Schema Management

**Fetching Schemas:**

```typescript
class CSAPIClient {
  // Get observation schema for specific format
  async getObservationSchema(
    dataStreamId: string,
    format:
      | 'application/swe+json'
      | 'application/swe+csv'
      | 'application/swe+binary'
  ): Promise<ObservationSchema> {
    const response = await fetch(
      `/datastreams/${dataStreamId}/schema?obsFormat=${encodeURIComponent(
        format
      )}`
    );
    return response.json();
  }

  // Get command schema
  async getCommandSchema(controlStreamId: string): Promise<ObservationSchema> {
    return this.getObservationSchema(controlStreamId, 'application/swe+json');
  }
}
```

**Schema Caching:**

```typescript
class SchemaCache {
  private cache = new Map<string, ObservationSchema>();

  async get(
    dataStreamId: string,
    format: string,
    client: CSAPIClient
  ): Promise<ObservationSchema> {
    const key = `${dataStreamId}:${format}`;
    if (!this.cache.has(key)) {
      const schema = await client.getObservationSchema(
        dataStreamId,
        format as any
      );
      this.cache.set(key, schema);
    }
    return this.cache.get(key)!;
  }

  invalidate(dataStreamId: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(`${dataStreamId}:`)) {
        this.cache.delete(key);
      }
    }
  }
}
```

#### 9.2 Observation Creation with Validation

**Creating Observations:**

```typescript
class CSAPIClient {
  async createObservation(
    dataStreamId: string,
    observation: {
      phenomenonTime: string;
      resultTime: string;
      result: any; // Raw data matching schema
    },
    options?: {
      format?: 'application/swe+json' | 'application/swe+csv';
      validate?: boolean; // Default: true
    }
  ): Promise<Observation> {
    const format = options?.format || 'application/swe+json';

    // Validate against schema
    if (options?.validate !== false) {
      const schema = await this.getObservationSchema(dataStreamId, format);
      this.validateObservationResult(observation.result, schema.recordSchema);
    }

    // Encode result
    const body = {
      ...observation,
      result: this.encodeResult(observation.result, format, schema),
    };

    const response = await fetch(`/datastreams/${dataStreamId}/observations`, {
      method: 'POST',
      headers: {
        'Content-Type': format,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Failed to create observation: ${response.statusText}`);
    }

    return response.json();
  }

  private validateObservationResult(result: any, schema: DataRecord): void {
    for (const field of schema.fields) {
      const value = result[field.name];

      // Check type
      if (value === undefined && !field.optional) {
        throw new ValidationError(field.name, 'Required field missing');
      }

      // Check constraints
      if (field.type === 'Quantity' && field.constraint?.interval) {
        const [min, max] = field.constraint.interval;
        if (value < min || value > max) {
          throw new ValidationError(
            field.name,
            `Value ${value} outside range [${min}, ${max}]`
          );
        }
      }
    }
  }
}
```

#### 9.3 Observation Retrieval and Decoding

**Fetching Observations:**

```typescript
class CSAPIClient {
  async getObservations(
    dataStreamId: string,
    options?: {
      format?:
        | 'application/swe+json'
        | 'application/swe+csv'
        | 'application/swe+binary';
      phenomenonTime?: string;
      resultTime?: string;
      limit?: number;
    }
  ): Promise<Observation[]> {
    const format = options?.format || 'application/swe+json';

    // Build query parameters
    const params = new URLSearchParams();
    if (options?.phenomenonTime)
      params.set('phenomenonTime', options.phenomenonTime);
    if (options?.resultTime) params.set('resultTime', options.resultTime);
    if (options?.limit) params.set('limit', options.limit.toString());

    // Fetch observations
    const response = await fetch(
      `/datastreams/${dataStreamId}/observations?${params}`,
      {
        headers: { Accept: format },
      }
    );

    // Get schema for decoding
    const schema = await this.getObservationSchema(dataStreamId, format);

    // Decode response
    if (format === 'application/swe+json') {
      const json = await response.json();
      return json.items.map((obs: any) => ({
        ...obs,
        result: this.decodeJSON(obs.result, schema.recordSchema),
      }));
    } else if (format === 'application/swe+csv') {
      const csv = await response.text();
      return this.decodeCSVObservations(csv, schema);
    } else if (format === 'application/swe+binary') {
      const buffer = await response.arrayBuffer();
      return this.decodeBinaryObservations(buffer, schema);
    }

    throw new Error(`Unsupported format: ${format}`);
  }
}
```

#### 9.4 Format Conversion

**Converting Between Formats:**

```typescript
class SWEConverter {
  // Convert observation result from one format to another
  convertResult(
    result: any,
    fromFormat: string,
    toFormat: string,
    schema: DataRecord
  ): any {
    // Step 1: Decode from source format
    let decoded: DataRecord;
    switch (fromFormat) {
      case 'application/swe+json':
        decoded = decodeJSON(result, schema);
        break;
      case 'application/swe+csv':
        decoded = decodeCSV(result, schema, { type: 'TextEncoding' });
        break;
      case 'application/swe+binary':
        decoded = decodeBinary(result, schema, {
          type: 'BinaryEncoding',
          members: [],
        });
        break;
      default:
        throw new Error(`Unsupported source format: ${fromFormat}`);
    }

    // Step 2: Encode to target format
    switch (toFormat) {
      case 'application/swe+json':
        return encodeJSON(decoded, { type: 'JSONEncoding' });
      case 'application/swe+csv':
        return encodeCSV(decoded, { type: 'TextEncoding' });
      case 'application/swe+binary':
        return encodeBinary(decoded, { type: 'BinaryEncoding', members: [] });
      default:
        throw new Error(`Unsupported target format: ${toFormat}`);
    }
  }
}
```

---

### 10. Error Handling

#### 10.1 Schema Validation Errors

**Schema Mismatch:**

```typescript
class SchemaValidationError extends Error {
  constructor(
    public componentPath: string,
    public expectedType: string,
    public actualValue: any
  ) {
    super(
      `Schema validation failed at ${componentPath}: expected ${expectedType}, got ${typeof actualValue}`
    );
  }
}
```

**Constraint Violation:**

```typescript
class ConstraintViolationError extends Error {
  constructor(
    public componentPath: string,
    public constraint: string,
    public value: any
  ) {
    super(
      `Constraint violation at ${componentPath}: ${constraint}, value: ${value}`
    );
  }
}
```

#### 10.2 Encoding/Decoding Errors

**Invalid Encoding:**

```typescript
class EncodingError extends Error {
  constructor(public format: string, public details: string) {
    super(`Failed to encode data as ${format}: ${details}`);
  }
}
```

**Corrupt Data:**

```typescript
class DecodingError extends Error {
  constructor(
    public format: string,
    public offset?: number,
    public details?: string
  ) {
    super(
      `Failed to decode ${format} data${
        offset !== undefined ? ` at offset ${offset}` : ''
      }: ${details}`
    );
  }
}
```

---

### 11. Dependencies and Libraries

#### 11.1 Recommended External Libraries

**Unit Handling:**

- **ucum-js** - UCUM code validation and conversion
- Usage: Validate UoM codes, convert between units

**Schema Validation:**

- **ajv** - JSON Schema validator
- Usage: Validate SWE Common component structures against JSON Schema

**Binary Encoding:**

- **DataView** (built-in) - Read/write binary data
- **Buffer** (Node.js) - Binary data manipulation
- Usage: Encode/decode SWE Common binary format

**CSV Parsing:**

- **csv-parse** - Robust CSV parsing
- Usage: Handle edge cases in CSV decoding (quoted values, escaping)

#### 11.2 Built-in vs External

**Built-in (Client Library):**

- TypeScript type definitions for SWE Common components
- Basic JSON encoding/decoding
- Basic CSV encoding/decoding
- Basic binary encoding/decoding (DataView)
- Schema-driven validation (type checking, constraints)
- Format negotiation

**External Libraries (Optional Dependencies):**

- Advanced UCUM operations (ucum-js)
- Robust CSV parsing (csv-parse)
- JSON Schema validation (ajv)

**Rationale:** Core SWE Common functionality is manageable without heavy dependencies. External libraries provide enhanced capabilities for production use.

---

## Summary

**Section 3.4 Complete:** SWE Common Format Requirements (~1,200 lines documenting all SWE Common aspects)

### Key Requirements

**Resources Using SWE Common:**

- Part 2: Observations (result field), Commands (parameters/result fields)
- DataStreams/ControlStreams define schemas and encodings
- Part 1: SensorML inputs/outputs use SWE Common component definitions

**Data Components:**

- **Simple:** Quantity, Count, Boolean, Text, Category, Time (all required)
- **Composite:** DataRecord, DataArray, Vector, Matrix (all required)
- **All types MUST be supported** for observation/command parsing

**Encoding Formats:**

- **JSON (application/swe+json):** Human-readable, structured, moderate size
- **CSV (application/swe+csv):** Compact, tabular, spreadsheet-compatible
- **Binary (application/swe+binary):** Very compact, high-frequency data, requires schema

**Units of Measure:**

- UCUM codes (standard: `Cel`, `m`, `s`, `Hz`, etc.)
- URI-based units (for time, specialized domains)
- Client must parse, preserve, optionally validate/convert

**Nil Values & Quality:**

- Nil values for missing/invalid data with semantic reasons
- Quality metadata for accuracy, confidence, status

**Client Library Must:**

- Parse schemas (resultSchema, parametersSchema, encoding)
- Validate observation/command data against schemas
- Encode/decode all three formats (JSON, CSV, Binary)
- Support all component types
- Cache schemas to avoid repeated fetches
- Handle units of measure, nil values, quality
- Provide TypeScript types for all components

**Complex Handling:**

- Schema-driven parsing (generic handling of any structure)
- Binary encoding with byte order (BIG_ENDIAN/LITTLE_ENDIAN)
- CSV with configurable separators
- Nested DataRecords, DataArrays

**Optional (External Libraries):**

- UCUM validation/conversion (ucum-js)
- Robust CSV parsing (csv-parse)
- JSON Schema validation (ajv)

**Section 3 Complete:** All format requirements documented (GeoJSON, SensorML, SWE Common)
