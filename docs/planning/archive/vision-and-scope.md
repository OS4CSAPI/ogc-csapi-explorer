# CSAPI Client Library - Vision and Scope

**Version:** 1.0  
**Date:** 2026-01-31  
**Status:** Final

---

## Vision Statement

Create a comprehensive, production-ready TypeScript client library for the OGC Connected Systems API (CSAPI) specification that seamlessly integrates into [camptocamp/ogc-client](https://github.com/camptocamp/ogc-client), enabling developers to discover, query, and interact with IoT sensor systems, observations, and commands with the same ease and reliability as existing OGC service clients (WFS, WMS, WMTS).

---

## Project Goals

### Primary Goals

1. **Complete CSAPI Coverage** - Support all resource types defined in CSAPI Parts 1 and 2
2. **Format Excellence** - Robust parsing and validation of all CSAPI formats (GeoJSON, SensorML, SWE Common)
3. **Upstream Integration** - Follow camptocamp/ogc-client patterns and architecture for seamless adoption
4. **Production Ready** - High test coverage, comprehensive documentation, excellent performance

### Success Criteria

- All 9 CSAPI resource types accessible via intuitive API
- GeoJSON, SensorML 2.0+, and SWE Common 2.0 formats fully supported
- 90%+ test coverage with integration tests against real servers
- PR accepted and merged to camptocamp/ogc-client main branch
- Documentation complete (JSDoc + examples + README)

---

## What This Library Will Do

### 1. Service Discovery and Metadata

**Capabilities:**

- ✅ Parse CSAPI landing page (service title, description, provider info)
- ✅ List all conformance classes supported by the server
- ✅ Discover all collections (resource catalogs) available
- ✅ Extract collection metadata (title, description, spatial/temporal extent)
- ✅ Identify API version and available features

**Use Cases:**

- Application startup: discover what resources are available
- Display service information to users
- Validate server capabilities before making requests
- Build dynamic UIs based on available collections

**Example:**

```typescript
const endpoint = new CSAPIEndpoint('https://api.example.com/csapi');
await endpoint.isReady();

// Get service info
const info = endpoint.getServiceInfo();
console.log(`Connected to: ${info.title}`);
console.log(`Provider: ${info.contact?.organization}`);

// Check conformance
const conformance = endpoint.getConformanceClasses();
if (
  conformance.includes(
    'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/datastream'
  )
) {
  console.log('Server supports DataStreams');
}

// List collections
const collections = endpoint.getCollections();
collections.forEach((col) => {
  console.log(`${col.id}: ${col.title} (${col.itemType})`);
});
```

---

### 2. System Discovery and Management

**Capabilities:**

- ✅ Query all systems (IoT devices, sensor networks, platforms)
- ✅ Filter systems by bounding box (spatial query)
- ✅ Filter systems by time period (temporal query)
- ✅ Get individual system by ID
- ✅ Create new systems
- ✅ Update existing systems
- ✅ Delete systems
- ✅ Parse system descriptions in GeoJSON or SensorML formats
- ✅ Extract system metadata (name, description, identifiers, classifications)
- ✅ Access system characteristics (physical properties, capabilities)
- ✅ Navigate system hierarchies (components, subsystems)

**Use Cases:**

- Discovery: find all weather stations in a region
- Monitoring: get list of all active sensor systems
- Management: register new IoT devices
- Inventory: maintain catalog of deployed sensors
- Analysis: understand system capabilities and specifications

**Example:**

```typescript
// Find all systems in a geographic area
const systems = await endpoint.getSystems({
  bbox: [-122.5, 37.7, -122.3, 37.9], // San Francisco Bay Area
  limit: 50,
});

console.log(`Found ${systems.features.length} systems`);
systems.features.forEach((system) => {
  console.log(`${system.properties.name} at ${system.geometry.coordinates}`);
});

// Get detailed info about specific system
const system = await endpoint.getSystemById('weather-station-01');
console.log(`System type: ${system.properties.featureType}`);
console.log(`Valid from: ${system.properties.validTime?.begin}`);

// Register new system
const newSystemId = await endpoint.createSystem({
  geometry: { type: 'Point', coordinates: [-122.4, 37.8] },
  properties: {
    name: 'New Weather Station',
    description: 'Rooftop weather monitoring',
    featureType: 'http://www.w3.org/ns/sosa/Platform',
  },
});
```

---

### 3. Deployment Management

**Capabilities:**

- ✅ Query all deployments (system installations over time)
- ✅ Filter deployments by location and time
- ✅ Get individual deployment by ID
- ✅ Create new deployments
- ✅ Update deployment information
- ✅ Delete deployments
- ✅ Track deployment validity periods
- ✅ Link deployments to systems and locations

**Use Cases:**

- Planning: track where and when systems are deployed
- History: maintain deployment records for compliance
- Maintenance: schedule system relocations
- Operations: know which systems are currently active

**Example:**

```typescript
// Find all active deployments
const deployments = await endpoint.getDeployments({
  datetime: '2026-01-01T00:00:00Z/..', // From Jan 1, 2026 to present
});

console.log(`${deployments.features.length} active deployments`);

// Create new deployment
const deploymentId = await endpoint.createDeployment({
  geometry: { type: 'Point', coordinates: [-122.4, 37.8] },
  properties: {
    name: 'Rooftop Installation Jan 2026',
    description: 'Weather station deployed on Building A',
    validTime: {
      begin: '2026-01-15T00:00:00Z',
      end: '2027-01-15T00:00:00Z',
    },
  },
});
```

---

### 4. Procedure (Methodology) Access

**Capabilities:**

- ✅ Query all procedures (measurement methods, algorithms, calibrations)
- ✅ Get individual procedure by ID
- ✅ Create new procedures
- ✅ Update procedures
- ✅ Delete procedures
- ✅ Parse SensorML process descriptions
- ✅ Extract procedure metadata (inputs, outputs, parameters)

**Use Cases:**

- Documentation: understand how measurements are made
- Quality: verify calibration procedures
- Traceability: link observations to specific methodologies
- Metadata: comply with data quality standards

**Example:**

```typescript
// Get all measurement procedures
const procedures = await endpoint.getProcedures({ limit: 100 });

// Get details of specific procedure
const procedure = await endpoint.getProcedureById('temperature-calibration-v2');
console.log(`Procedure: ${procedure.name}`);
console.log(`Description: ${procedure.description}`);
```

---

### 5. Sampling Feature Management

**Capabilities:**

- ✅ Query all sampling features (locations where observations are made)
- ✅ Filter sampling features spatially and temporally
- ✅ Get individual sampling feature by ID
- ✅ Create new sampling features
- ✅ Update sampling features
- ✅ Delete sampling features
- ✅ Support various sampling feature types (points, regions, paths)

**Use Cases:**

- Spatial analysis: identify observation locations
- Site management: maintain catalog of monitoring sites
- Relationships: link observations to specific locations
- Coverage: understand spatial distribution of measurements

**Example:**

```typescript
// Find all monitoring sites in region
const samplingFeatures = await endpoint.getSamplingFeatures({
  bbox: [-122.5, 37.7, -122.3, 37.9],
});

// Create new monitoring site
const siteId = await endpoint.createSamplingFeature({
  geometry: { type: 'Point', coordinates: [-122.4, 37.8] },
  properties: {
    name: 'Building A Rooftop',
    featureType:
      'http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint',
  },
});
```

---

### 6. Property Discovery

**Capabilities:**

- ✅ Query all observable properties (temperature, humidity, wind speed, etc.)
- ✅ Get individual property by ID
- ✅ Extract property metadata (definition, units, description)

**Use Cases:**

- Discovery: what can be measured by this system?
- Standardization: ensure consistent property definitions
- Metadata: understand measurement semantics

**Example:**

```typescript
// Get all observable properties
const properties = await endpoint.getProperties();

properties.items.forEach((prop) => {
  console.log(`${prop.label}: ${prop.definition}`);
});

// Get specific property details
const temp = await endpoint.getPropertyById('air-temperature');
console.log(`Standard: ${temp.definition}`);
console.log(`Units: ${temp.uom?.code}`);
```

---

### 7. DataStream Discovery and Management

**Capabilities:**

- ✅ Query all datastreams (observation series)
- ✅ Filter datastreams by system, property, time, location
- ✅ Get datastreams for specific system
- ✅ Get individual datastream by ID
- ✅ Create new datastreams
- ✅ Update datastream metadata
- ✅ Delete datastreams
- ✅ Parse SWE Common result schemas (defines observation structure)
- ✅ Understand result encodings (JSON, text, binary)

**Use Cases:**

- Discovery: what data is available from this system?
- Schema understanding: how are observations structured?
- Data access: which datastream has temperature readings?
- Management: register new data series

**Example:**

```typescript
// Find all temperature datastreams
const datastreams = await endpoint.getDataStreams({
  filter: "properties/observedProperty eq 'air-temperature'",
  limit: 50,
});

// Get datastreams for specific system
const systemStreams = await endpoint.getSystemDataStreams('weather-station-01');

console.log(`System has ${systemStreams.items.length} datastreams:`);
systemStreams.items.forEach((ds) => {
  console.log(`- ${ds.name}: ${ds.observedProperty.title}`);
  console.log(`  Schema: ${ds.schema.type}`);
  console.log(`  Encoding: ${ds.encoding?.type}`);
});

// Create new datastream
const streamId = await endpoint.createDataStream({
  name: 'Temperature Readings',
  observedProperty: { href: 'http://example.com/properties/air-temp' },
  system: { href: 'http://example.com/systems/weather-station-01' },
  schema: {
    type: 'DataRecord',
    fields: [
      {
        name: 'temperature',
        component: {
          type: 'Quantity',
          definition: 'http://mmisw.org/ont/cf/parameter/air_temperature',
          uom: { code: 'Cel' },
        },
      },
    ],
  },
});
```

---

### 8. Observation Query and Ingestion

**Capabilities:**

- ✅ Query observations across all datastreams
- ✅ Query observations for specific datastream
- ✅ Filter by time range (get last 24 hours, specific date range, etc.)
- ✅ Filter by location (bounding box)
- ✅ Pagination (limit, offset) for large datasets
- ✅ Get individual observation by ID
- ✅ Parse observation results according to datastream schema
- ✅ Handle multiple encoding formats (JSON, CSV-like text, binary)
- ✅ Bulk insert observations (multiple at once)
- ✅ Validate observations against schema

**Use Cases:**

- Real-time monitoring: get latest observations
- Historical analysis: query time series data
- Data ingestion: upload sensor readings in bulk
- Quality control: validate data before storage
- Visualization: feed data to charts/maps

**Example:**

```typescript
// Get latest 100 observations from datastream
const observations = await endpoint.getDataStreamObservations(
  'temperature-series-01',
  {
    datetime: '2026-01-31T00:00:00Z/..',
    limit: 100,
    sortby: '-phenomenonTime', // Most recent first
  }
);

console.log(`Retrieved ${observations.items.length} observations`);
observations.items.forEach((obs) => {
  console.log(`${obs.phenomenonTime}: ${obs.result.temperature} °C`);
});

// Query observations in spatial area
const spatialObs = await endpoint.getObservations({
  bbox: [-122.5, 37.7, -122.3, 37.9],
  datetime: '2026-01-30T00:00:00Z/2026-01-31T00:00:00Z',
});

// Bulk insert observations (e.g., from data logger)
const obsIds = await endpoint.createObservations([
  {
    phenomenonTime: '2026-01-31T12:00:00Z',
    resultTime: '2026-01-31T12:00:01Z',
    result: { temperature: 22.5 },
    datastream: { href: 'http://example.com/datastreams/temp-01' },
  },
  {
    phenomenonTime: '2026-01-31T12:05:00Z',
    resultTime: '2026-01-31T12:05:01Z',
    result: { temperature: 22.7 },
    datastream: { href: 'http://example.com/datastreams/temp-01' },
  },
  // ... thousands more
]);

console.log(`Inserted ${obsIds.length} observations`);
```

---

### 9. Control Stream Management (Commands & Tasking)

**Capabilities:**

- ✅ Query all control streams (command channels)
- ✅ Get control streams for specific system
- ✅ Get individual control stream by ID
- ✅ Create new control streams
- ✅ Update control stream metadata
- ✅ Delete control streams
- ✅ Parse SWE Common control schemas (defines command structure)

**Use Cases:**

- System control: understand how to send commands to devices
- Tasking: configure sensors remotely
- Automation: program system behaviors
- Management: maintain catalog of control capabilities

**Example:**

```typescript
// Get all control channels for system
const controlStreams = await endpoint.getSystemControlStreams('camera-01');

console.log(`Camera supports ${controlStreams.items.length} control streams:`);
controlStreams.items.forEach((cs) => {
  console.log(`- ${cs.name}: ${cs.description}`);
  console.log(`  Schema: ${cs.schema.type}`);
});

// Create new control stream
const streamId = await endpoint.createControlStream({
  name: 'Pan/Tilt Control',
  description: 'Control camera orientation',
  system: { href: 'http://example.com/systems/camera-01' },
  schema: {
    type: 'DataRecord',
    fields: [
      {
        name: 'pan',
        component: {
          type: 'Quantity',
          definition: 'http://example.com/def/pan',
          uom: { code: 'deg' },
          constraint: { interval: [[-180, 180]] },
        },
      },
      {
        name: 'tilt',
        component: {
          type: 'Quantity',
          definition: 'http://example.com/def/tilt',
          uom: { code: 'deg' },
          constraint: { interval: [[-90, 90]] },
        },
      },
    ],
  },
});
```

---

### 10. Command Submission and Tracking

**Capabilities:**

- ✅ Query all commands
- ✅ Query commands for specific control stream
- ✅ Get individual command by ID
- ✅ Submit commands to systems (single)
- ✅ Bulk submit commands (multiple at once)
- ✅ Parse command parameters according to control stream schema
- ✅ Validate commands against schema

**Use Cases:**

- Remote control: send commands to IoT devices
- Tasking: schedule sensor operations
- Batch operations: send multiple commands efficiently
- History: track what commands were sent when

**Example:**

```typescript
// Get recent commands for control stream
const commands = await endpoint.getControlStreamCommands('camera-pan-tilt', {
  datetime: '2026-01-31T00:00:00Z/..',
  limit: 50,
});

// Submit single command
const cmdIds = await endpoint.createCommands([
  {
    executionTime: '2026-01-31T13:00:00Z',
    parameters: {
      pan: 45,
      tilt: 30,
    },
    controlStream: {
      href: 'http://example.com/controlstreams/camera-pan-tilt',
    },
  },
]);

// Bulk submit (e.g., scheduled tasking sequence)
const bulkCmdIds = await endpoint.createCommands([
  {
    executionTime: '2026-01-31T14:00:00Z',
    parameters: { pan: 0, tilt: 0 },
    controlStream: {
      href: 'http://example.com/controlstreams/camera-pan-tilt',
    },
  },
  {
    executionTime: '2026-01-31T14:05:00Z',
    parameters: { pan: 90, tilt: 45 },
    controlStream: {
      href: 'http://example.com/controlstreams/camera-pan-tilt',
    },
  },
  {
    executionTime: '2026-01-31T14:10:00Z',
    parameters: { pan: 180, tilt: 0 },
    controlStream: {
      href: 'http://example.com/controlstreams/camera-pan-tilt',
    },
  },
]);

console.log(`Scheduled ${bulkCmdIds.length} commands`);
```

---

## Format Support

### GeoJSON (RFC 7946)

**What We Parse:**

- ✅ All geometry types: Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection
- ✅ Feature objects (individual items)
- ✅ FeatureCollection objects (lists)
- ✅ Coordinate reference systems (CRS)
- ✅ Bounding boxes

**Use Cases:**

- Display systems/deployments/sampling features on maps
- Spatial queries (find devices in area)
- Interoperability with GIS tools

---

### SensorML 2.0+ (OGC 12-000)

**What We Parse:**

- ✅ SimpleProcess - basic procedure descriptions
- ✅ PhysicalSystem - complete sensor systems (weather stations, monitoring networks)
- ✅ PhysicalComponent - individual sensors (thermometer, camera, etc.)
- ✅ AggregateProcess - combined systems
- ✅ ProcessChain - connected processing workflows

**System Description Elements:**

- ✅ Identification - unique IDs, classifiers, long/short names
- ✅ Classification - types, categories, taxonomies
- ✅ Characteristics - physical properties (size, weight, power consumption)
- ✅ Capabilities - measurement ranges, resolution, accuracy
- ✅ Contacts - manufacturer, operator, owner
- ✅ Documentation - manuals, specifications, papers
- ✅ History - events, changes, calibrations
- ✅ Position - location, orientation, reference frame
- ✅ Components - nested subsystems (recursive hierarchy)
- ✅ Connections - data flow between components

**Use Cases:**

- Understand sensor specifications
- Verify measurement capabilities
- Navigate system hierarchies
- Compliance with metadata standards

---

### SWE Common 2.0 (OGC 08-094r1)

**What We Parse:**

**Simple Components:**

- ✅ Quantity - numeric values with units (temperature: 25.5 °C)
- ✅ Count - integer values (number of particles: 42)
- ✅ Boolean - true/false flags (heater on/off)
- ✅ Text - string values (status: "operational")
- ✅ Category - enumerated values (quality: "good" | "bad")
- ✅ Time - temporal values (timestamp: 2026-01-31T12:00:00Z)

**Structured Components:**

- ✅ DataRecord - structured records with named fields
- ✅ Vector - geometric vectors (3D position, velocity)
- ✅ DataArray - arrays of values (time series)
- ✅ DataChoice - conditional/variant types (different result formats)
- ✅ Matrix - 2D arrays (images, grids)

**Encodings:**

- ✅ JSON Encoding - native JavaScript objects/arrays
- ✅ Text Encoding - CSV-like text with configurable separators
- ✅ Binary Encoding - compact binary formats (base64 or raw)
- ✅ XML Encoding - XML representations

**Use Cases:**

- Parse observation results (understand what sensor returned)
- Validate data structure (ensure observations match schema)
- Handle multiple formats (JSON, text, binary) transparently
- Type-safe data access (know units, constraints, allowed values)

**Example Schemas:**

```typescript
// Simple quantity (single value)
const tempSchema = {
  type: 'Quantity',
  definition: 'http://mmisw.org/ont/cf/parameter/air_temperature',
  uom: { code: 'Cel' },
};
// Result: 25.5

// Structured record (multiple fields)
const weatherSchema = {
  type: 'DataRecord',
  fields: [
    {
      name: 'temperature',
      component: { type: 'Quantity', uom: { code: 'Cel' } },
    },
    {
      name: 'humidity',
      component: { type: 'Quantity', uom: { code: '%' } },
    },
    {
      name: 'pressure',
      component: { type: 'Quantity', uom: { code: 'hPa' } },
    },
  ],
};
// Result: { temperature: 25.5, humidity: 60.2, pressure: 1013.2 }

// Time series (array)
const timeSeriesSchema = {
  type: 'DataArray',
  elementType: {
    type: 'DataRecord',
    fields: [
      { name: 'time', component: { type: 'Time' } },
      { name: 'value', component: { type: 'Quantity', uom: { code: 'Cel' } } },
    ],
  },
};
// Result: [
//   { time: '2026-01-31T12:00:00Z', value: 25.5 },
//   { time: '2026-01-31T12:05:00Z', value: 25.7 },
//   ...
// ]
```

---

## Query Capabilities

### Query Parameters Supported

**Spatial Filtering:**

- ✅ `bbox` - Bounding box filter [minx, miny, maxx, maxy]
  - Example: `bbox=-122.5,37.7,-122.3,37.9` (San Francisco Bay Area)

**Temporal Filtering:**

- ✅ `datetime` - ISO 8601 time intervals
  - Single instant: `2026-01-31T12:00:00Z`
  - Interval: `2026-01-01T00:00:00Z/2026-01-31T23:59:59Z`
  - Open-ended: `2026-01-01T00:00:00Z/..` (from date to present)
  - Open-ended: `../2026-01-31T23:59:59Z` (from past to date)

**Pagination:**

- ✅ `limit` - Maximum number of results (default varies by server)
- ✅ `offset` - Skip N results (for paging through large datasets)

**Property Selection:**

- ✅ `properties` - Comma-separated list of properties to include
  - Example: `properties=name,description,validTime`
  - Reduces bandwidth for large datasets

**Sorting:**

- ✅ `sortby` - Sort by property name
  - Ascending: `sortby=name`
  - Descending: `sortby=-name`
  - Multiple: `sortby=validTime,-name`

**Format Negotiation:**

- ✅ `f` - Explicit format parameter
  - Example: `f=application/geo+json`
  - Example: `f=application/sensorml+json`

**Advanced Filtering:**

- ✅ `filter` - CQL2 filter expressions
  - Example: `filter=properties/name LIKE 'Weather%'`
  - Example: `filter=properties/validTime DURING 2026-01-01T00:00:00Z/2026-12-31T23:59:59Z`

### Query Examples

```typescript
// Spatial + temporal + pagination
const systems = await endpoint.getSystems({
  bbox: [-122.5, 37.7, -122.3, 37.9],
  datetime: '2026-01-01T00:00:00Z/..',
  limit: 50,
  offset: 0,
});

// Property selection (performance)
const observations = await endpoint.getObservations({
  properties: ['phenomenonTime', 'result'], // Omit metadata
  limit: 1000,
});

// Sorting
const recentObs = await endpoint.getDataStreamObservations('temp-01', {
  sortby: '-phenomenonTime', // Newest first
  limit: 100,
});

// CQL2 filter
const activeWeatherStations = await endpoint.getSystems({
  filter:
    "properties/featureType eq 'http://www.w3.org/ns/sosa/Platform' AND properties/name LIKE 'Weather%'",
  limit: 100,
});
```

---

## Advanced Features

### 1. Format Detection

**Capability:** Automatically detect format from response

**How It Works:**

1. Check Content-Type header (most reliable)
2. Analyze response structure (JSON keys, type fields)
3. Use context (resource type, operation)
4. Apply heuristics (educated guesses)

**Benefit:** Developers don't need to specify format - library figures it out

**Example:**

```typescript
// Works regardless of server's response format (GeoJSON or SensorML)
const system = await endpoint.getSystemById('weather-01');
// Library automatically detects and parses correct format
```

---

### 2. Format Validation

**Capability:** Validate data structure and content

**Validation Modes:**

- `strict` - Throw errors on any validation failure
- `lenient` - Log warnings but continue parsing

**Validation Levels:**

- Structural: JSON matches expected format
- Types: Fields have correct types (string, number, array)
- Required: Required fields present
- Constraints: Values within allowed ranges
- Semantic: Relationships valid (bbox matches geometry)

**Example:**

```typescript
// Strict validation (throw on errors)
const endpoint = new CSAPIEndpoint('https://api.example.com/csapi', {
  validationMode: 'strict',
});

// Lenient validation (log warnings)
const endpoint2 = new CSAPIEndpoint('https://api.example.com/csapi', {
  validationMode: 'lenient',
});
```

---

### 3. Worker Support

**Capability:** Offload heavy parsing to Web Workers (browsers) or worker threads (Node.js)

**What Runs in Worker:**

- Conformance parsing
- Collections parsing
- SensorML parsing (most expensive)
- SWE Common parsing (complex schemas)
- Large observation datasets

**Benefits:**

- Non-blocking UI (browser stays responsive)
- Better performance for large datasets
- Automatic fallback when workers not available

**Example:**

```typescript
// Automatically uses worker if available
const observations = await endpoint.getDataStreamObservations('temp-01', {
  limit: 10000, // Parse 10K observations without blocking UI
});
```

---

### 4. Caching

**Capability:** Cache static metadata to reduce network requests

**What Gets Cached:**

- Landing page (service info)
- Conformance classes
- Collections
- Parsed schemas (reused for observations)

**Benefits:**

- Faster subsequent requests
- Reduced server load
- Offline-capable (once cached)

**Cache Control:**

```typescript
// Automatic caching enabled by default
const endpoint = new CSAPIEndpoint('https://api.example.com/csapi');

// Clear cache if needed (e.g., server updated)
endpoint.clearCache();
```

---

### 5. Error Handling

**Capability:** Comprehensive error types for debugging

**Error Types:**

- `CSAPIError` - Base error class
- `FormatParseError` - Failed to parse GeoJSON/SensorML/SWE Common
- `ValidationError` - Data doesn't match expected schema
- `ServerError` - HTTP 4xx/5xx errors
- `NetworkError` - Connection failures

**Error Details:**

- Clear error messages
- JSON path to problematic field
- Expected vs actual values
- Original cause chain

**Example:**

```typescript
try {
  const system = await endpoint.getSystemById('invalid-id');
} catch (error) {
  if (error instanceof ServerError) {
    console.error(`Server error: ${error.statusCode} - ${error.message}`);
  } else if (error instanceof FormatParseError) {
    console.error(`Parse error at ${error.path}: ${error.message}`);
  } else if (error instanceof NetworkError) {
    console.error(`Network error: ${error.message}`);
  }
}
```

---

## Complete Feature Matrix

| Feature                        | Support Level | Notes                         |
| ------------------------------ | ------------- | ----------------------------- |
| **Part 1 Resources**           |               |                               |
| Systems                        | Full CRUD     | GET, POST, PUT, DELETE        |
| Deployments                    | Full CRUD     | GET, POST, PUT, DELETE        |
| Procedures                     | Full CRUD     | GET, POST, PUT, DELETE        |
| Sampling Features              | Full CRUD     | GET, POST, PUT, DELETE        |
| Properties                     | Read-only     | GET                           |
| **Part 2 Resources**           |               |                               |
| DataStreams                    | Full CRUD     | GET, POST, PUT, DELETE        |
| Observations                   | Read + Create | GET, POST (bulk insert)       |
| Control Streams                | Full CRUD     | GET, POST, PUT, DELETE        |
| Commands                       | Read + Create | GET, POST (bulk submit)       |
| **Formats**                    |               |                               |
| GeoJSON                        | Full          | All geometry types            |
| SensorML 2.0                   | Full          | All process types             |
| SensorML 2.1                   | Full          | All process types             |
| SWE Common 2.0                 | Full          | All components, all encodings |
| **Query Parameters**           |               |                               |
| bbox                           | ✅            | Spatial filtering             |
| datetime                       | ✅            | Temporal filtering            |
| limit                          | ✅            | Pagination                    |
| offset                         | ✅            | Pagination                    |
| properties                     | ✅            | Field selection               |
| sortby                         | ✅            | Sorting                       |
| filter (CQL2)                  | ✅            | Advanced filtering            |
| f (format)                     | ✅            | Format negotiation            |
| **Advanced Features**          |               |                               |
| Format Detection               | ✅            | Automatic                     |
| Format Validation              | ✅            | Strict/lenient modes          |
| Worker Support                 | ✅            | Browser + Node.js             |
| Caching                        | ✅            | Metadata caching              |
| Error Handling                 | ✅            | Comprehensive error types     |
| TypeScript                     | ✅            | Full type definitions         |
| JSDoc                          | ✅            | 100% public API               |
| **Nested Resources**           |               |                               |
| /systems/{id}/datastreams      | ✅            | Get system's datastreams      |
| /datastreams/{id}/observations | ✅            | Get datastream's observations |
| /systems/{id}/controlstreams   | ✅            | Get system's control streams  |
| /controlstreams/{id}/commands  | ✅            | Get control stream's commands |

---

## Use Case Scenarios

### Scenario 1: Environmental Monitoring Dashboard

**Goal:** Build web dashboard showing real-time air quality from sensor network

**What Library Provides:**

1. Discover all air quality monitoring systems in city
2. Get datastreams for each system (PM2.5, PM10, CO, NO2, O3)
3. Fetch latest observations (last hour)
4. Display on map (GeoJSON geometries)
5. Update every 5 minutes (polling)

**Code Outline:**

```typescript
// Initialize
const endpoint = new CSAPIEndpoint('https://airquality.example.com/csapi');
await endpoint.isReady();

// Find air quality stations
const systems = await endpoint.getSystems({
  bbox: cityBounds,
  filter: "properties/featureType eq 'air-quality-station'",
});

// For each system, get datastreams and latest observations
for (const system of systems.features) {
  const datastreams = await endpoint.getSystemDataStreams(system.id);

  for (const ds of datastreams.items) {
    const observations = await endpoint.getDataStreamObservations(ds.id, {
      datetime: 'PT1H/..', // Last 1 hour to now
      limit: 1,
      sortby: '-phenomenonTime',
    });

    // Display on map/chart
    displayOnDashboard(system, ds, observations[0]);
  }
}
```

---

### Scenario 2: IoT Data Logger Upload

**Goal:** Upload sensor readings from offline data logger to server

**What Library Provides:**

1. Authenticate to server
2. Find or create datastream for sensor
3. Bulk upload thousands of observations efficiently
4. Validate data before upload
5. Handle errors gracefully

**Code Outline:**

```typescript
// Read data from logger file
const loggedData = readDataLogger('sensor-001-2026-01.csv');

// Initialize endpoint
const endpoint = new CSAPIEndpoint('https://api.example.com/csapi', {
  auth: { token: 'bearer-token-here' },
});
await endpoint.isReady();

// Find existing datastream or create new one
let datastreamId;
const existingStreams = await endpoint.getDataStreams({
  filter: "properties/outputName eq 'temperature-sensor-001'",
});

if (existingStreams.items.length > 0) {
  datastreamId = existingStreams.items[0].id;
} else {
  datastreamId = await endpoint.createDataStream({
    name: 'Temperature Sensor 001',
    outputName: 'temperature-sensor-001',
    system: { href: 'http://api.example.com/systems/sensor-001' },
    observedProperty: { href: 'http://api.example.com/properties/air-temp' },
    schema: { type: 'Quantity', uom: { code: 'Cel' } },
  });
}

// Upload observations in batches
const batchSize = 1000;
for (let i = 0; i < loggedData.length; i += batchSize) {
  const batch = loggedData.slice(i, i + batchSize).map((row) => ({
    phenomenonTime: row.timestamp,
    resultTime: row.timestamp,
    result: row.temperature,
    datastream: { href: `http://api.example.com/datastreams/${datastreamId}` },
  }));

  try {
    await endpoint.createObservations(batch);
    console.log(`Uploaded batch ${i / batchSize + 1}`);
  } catch (error) {
    console.error(`Failed to upload batch: ${error.message}`);
  }
}
```

---

### Scenario 3: Automated Camera Control

**Goal:** Remotely control PTZ camera to scan monitoring area

**What Library Provides:**

1. Discover camera's control streams
2. Understand command schema (pan, tilt, zoom parameters)
3. Submit command sequence
4. Track command execution status

**Code Outline:**

```typescript
const endpoint = new CSAPIEndpoint('https://cameras.example.com/csapi');
await endpoint.isReady();

// Get camera's control streams
const controlStreams = await endpoint.getSystemControlStreams('ptz-camera-01');

// Find pan/tilt control stream
const panTiltStream = controlStreams.items.find(
  (cs) => cs.name === 'Pan/Tilt Control'
);

// Understand command parameters from schema
console.log('Pan range:', panTiltStream.schema.fields[0].component.constraint);
console.log('Tilt range:', panTiltStream.schema.fields[1].component.constraint);

// Submit scan sequence (5 positions)
const scanPositions = [
  { pan: -90, tilt: 0 },
  { pan: -45, tilt: 30 },
  { pan: 0, tilt: 45 },
  { pan: 45, tilt: 30 },
  { pan: 90, tilt: 0 },
];

const commandIds = await endpoint.createCommands(
  scanPositions.map((pos, idx) => ({
    executionTime: new Date(Date.now() + idx * 10000).toISOString(), // 10s apart
    parameters: pos,
    controlStream: {
      href: `http://cameras.example.com/controlstreams/${panTiltStream.id}`,
    },
  }))
);

console.log(`Scheduled ${commandIds.length} commands`);
```

---

### Scenario 4: Sensor Network Inventory

**Goal:** Generate report of all deployed sensors and their specifications

**What Library Provides:**

1. List all systems in network
2. Parse SensorML descriptions to extract specifications
3. Export inventory report

**Code Outline:**

```typescript
const endpoint = new CSAPIEndpoint('https://network.example.com/csapi');
await endpoint.isReady();

// Get all systems
const systems = await endpoint.getSystems({ limit: 1000 });

const inventory = [];

for (const system of systems.features) {
  const details = await endpoint.getSystemById(system.id);

  // Extract from SensorML
  const specs = {
    id: details.id,
    name: details.properties.name,
    type: details.properties.featureType,
    manufacturer: details.properties.contacts?.find(
      (c) => c.role === 'manufacturer'
    )?.organization,
    model: details.properties.identification?.find(
      (i) => i.definition === 'model'
    )?.value,
    serialNumber: details.properties.identification?.find(
      (i) => i.definition === 'serialNumber'
    )?.value,
    location: details.geometry?.coordinates,
    capabilities: details.properties.capabilities?.map((c) => ({
      name: c.name,
      range: c.constraint?.interval,
      resolution: c.quality?.find((q) => q.definition === 'resolution')?.value,
    })),
    deployedSince: details.properties.validTime?.begin,
  };

  inventory.push(specs);
}

// Export as CSV, JSON, or database
exportInventory(inventory);
```

---

## Developer Experience

### Type Safety

**TypeScript First:**

- All public APIs fully typed
- Autocomplete in IDEs (VSCode, WebStorm, etc.)
- Compile-time error checking
- IntelliSense documentation

**Example:**

```typescript
// TypeScript knows exact shape of system
const system: SystemFeature = await endpoint.getSystemById('weather-01');

// Autocomplete available for all properties
system.properties.name; // ✅
system.properties.invalid; // ❌ TypeScript error

// Type-safe query options
const observations = await endpoint.getObservations({
  bbox: [-180, -90, 180, 90], // ✅
  bbox: 'invalid', // ❌ TypeScript error
  limit: 100, // ✅
  limit: 'invalid', // ❌ TypeScript error
});
```

---

### Comprehensive Documentation

**JSDoc Coverage:**

- 100% of public APIs documented
- Parameter descriptions
- Return type descriptions
- Usage examples
- Links to specifications

**Example:**

````typescript
/**
 * Query observations from a specific datastream.
 *
 * @param datastreamId - Unique identifier of the datastream
 * @param options - Query options (temporal filter, pagination, etc.)
 * @returns Promise resolving to observation collection
 * @throws {ServerError} If server returns error
 * @throws {NetworkError} If connection fails
 *
 * @example
 * ```typescript
 * const observations = await endpoint.getDataStreamObservations('temp-01', {
 *   datetime: '2026-01-31T00:00:00Z/..',
 *   limit: 100
 * });
 * ```
 *
 * @see https://docs.ogc.org/DRAFTS/23-001.html#observations
 */
getDataStreamObservations(
  datastreamId: string,
  options?: QueryOptions
): Promise<ObservationCollection>;
````

---

### Simple, Intuitive API

**Consistent Patterns:**

- All resources follow same method naming (getSystems, getDataStreams, etc.)
- All query options use same parameter names (bbox, datetime, limit, etc.)
- All create operations return created ID
- All errors inherit from base CSAPIError class

**Minimal Boilerplate:**

```typescript
// Get started in 3 lines
const endpoint = new CSAPIEndpoint('https://api.example.com/csapi');
await endpoint.isReady();
const systems = await endpoint.getSystems();
```

---

## Integration with camptocamp/ogc-client

**Consistency with Existing Services:**

- Same endpoint pattern as WFS/WMS/WMTS
- Same worker architecture
- Same caching strategy
- Same error handling approach
- Same testing standards

**Example (Compare with WFS):**

```typescript
// WFS endpoint
const wfs = new WfsEndpoint('https://example.com/wfs');
await wfs.isReady();
const featureTypes = wfs.getFeatureTypes();
const features = await wfs.getFeatures('roads', { maxFeatures: 100 });

// CSAPI endpoint (same pattern!)
const csapi = new CSAPIEndpoint('https://example.com/csapi');
await csapi.isReady();
const collections = csapi.getCollections();
const systems = await csapi.getSystems({ limit: 100 });
```

**Bundle Size:**

- Tree-shakable (import only what you need)
- Format parsers optional (exclude if not needed)
- Total: ~150KB gzipped (all formats included)

---

## Performance Expectations

| Operation               | Target Performance | Notes                                          |
| ----------------------- | ------------------ | ---------------------------------------------- |
| Endpoint initialization | < 2 seconds        | Parse landing page + conformance + collections |
| Get 100 systems         | < 1 second         | Including format detection + parsing           |
| Parse SensorML          | < 100ms            | PhysicalSystem with 5 components               |
| Parse 1K observations   | < 500ms            | JSON encoding, DataRecord schema               |
| Parse 10K observations  | < 5 seconds        | Worker mode, complex schema                    |
| Binary encoding parse   | < 1 second         | 10K observations, compact format               |

---

## Browser/Platform Support

| Platform    | Support    | Notes                            |
| ----------- | ---------- | -------------------------------- |
| Chrome 90+  | ✅ Full    | Worker support, all features     |
| Firefox 88+ | ✅ Full    | Worker support, all features     |
| Safari 14+  | ✅ Full    | Worker support, all features     |
| Edge 90+    | ✅ Full    | Worker support, all features     |
| Node.js 18+ | ✅ Full    | Worker threads, all features     |
| Node.js 16+ | ⚠️ Limited | No worker threads, sync fallback |
| Deno        | ✅ Full    | Worker support, all features     |

---

## Summary: What You Get

**9 Resource Types** - Complete access to all CSAPI resources:

1. Systems (IoT devices, sensor networks)
2. Deployments (installation history)
3. Procedures (measurement methods)
4. Sampling Features (observation locations)
5. Properties (observable phenomena)
6. DataStreams (observation series)
7. Observations (sensor readings)
8. Control Streams (command channels)
9. Commands (tasking/control)

**3 Format Parsers** - Robust parsing of all CSAPI formats:

1. GeoJSON (all geometry types, features, collections)
2. SensorML 2.0+ (all process types, complete metadata)
3. SWE Common 2.0 (all components, all encodings)

**Complete Query Capabilities:**

- Spatial filtering (bounding boxes)
- Temporal filtering (time ranges)
- Pagination (limit, offset)
- Property selection (reduce bandwidth)
- Sorting (ascending, descending)
- Advanced filtering (CQL2 expressions)

**Production-Ready Features:**

- Automatic format detection
- Comprehensive validation
- Worker support (non-blocking)
- Intelligent caching
- Detailed error handling
- Full TypeScript types
- 100% JSDoc coverage
- 90%+ test coverage

**Developer-Friendly:**

- Simple, intuitive API
- Consistent patterns
- Minimal boilerplate
- Great IDE support
- Comprehensive examples
- Excellent documentation

---

**This library enables developers to build sophisticated IoT and sensor applications with minimal effort, leveraging the full power of the OGC Connected Systems API.**

---

## Document Change Log

| Version | Date       | Changes                  |
| ------- | ---------- | ------------------------ |
| 1.0     | 2026-01-31 | Initial vision and scope |
