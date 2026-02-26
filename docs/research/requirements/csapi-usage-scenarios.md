# CSAPI Real-World Usage Scenario Requirements

**Document:** Section 9 - Usage Scenario Requirements and Priorities  
**Source:** OGC API – Connected Systems Part 1 & Part 2 standard analysis  
**Date:** 2026-01-31  
**Status:** Complete

---

## Executive Summary

This document identifies real-world usage scenarios for OGC API – Connected Systems based on comprehensive analysis of the standard specifications, requirements documents, and common sensor web application patterns. The analysis prioritizes 15 core scenarios, defines 6 essential workflows, documents common query patterns, and recommends 17 convenience methods to simplify client library usage.

**Key Findings:**

- **15 Core Usage Scenarios** covering discovery, monitoring, control, and deployment
- **6 Essential Workflows** from initialization through real-time monitoring and commanding
- **8 Common Error Patterns** requiring specific handling strategies
- **17 Convenience Methods** to reduce boilerplate and simplify common tasks
- **4 Integration Patterns** for mapping, charting, real-time updates, and binary parsing
- **Performance Recommendations** for pagination, caching, and streaming

---

## Table of Contents

1. [Top Usage Scenarios](#1-top-usage-scenarios)
2. [Essential Workflows](#2-essential-workflows)
3. [Common Query Patterns](#3-common-query-patterns)
4. [Convenience Methods](#4-convenience-methods)
5. [Error Handling Requirements](#5-error-handling-requirements)
6. [Integration Patterns](#6-integration-patterns)
7. [Data Transformation Requirements](#7-data-transformation-requirements)
8. [Performance Considerations](#8-performance-considerations)
9. [Library Design Implications](#9-library-design-implications)

---

## 1. Top Usage Scenarios

### 1.1 Scenario: Discover Available Sensor Systems in Geographic Area

**Description:** Find all sensor systems within a geographic region, optionally filtered by sensor type or observed property.

**User Story:** "As a user, I want to find all temperature sensors within San Francisco so I can monitor local weather conditions."

**API Operations:**

```
GET /systems?bbox=-122.5,37.5,-122.3,37.7&observedProperty=temperature
```

**Client Library Requirements:**

- Spatial query builder for bbox construction
- Property filter support (URI or CURIE format)
- GeoJSON response parsing
- Optional: integrate with mapping libraries for visualization

**Frequency:** High - Every application initialization and when changing viewing area

**Complexity:** Low-Medium

**Priority:** P0 (Must-have)

---

### 1.2 Scenario: Query Real-Time Sensor Observations

**Description:** Poll a sensor's latest observations to display current conditions on a dashboard.

**User Story:** "As a dashboard user, I want to see the current temperature reading from sensor X updated every 5 seconds."

**API Operations:**

```
1. GET /systems/{id}/datastreams
2. GET /datastreams/{id}/observations?resultTime=latest
   (repeated every N seconds)
```

**Client Library Requirements:**

- Check `datastream.live` property for availability
- Polling abstraction with configurable interval
- Incremental fetch using resultTime filter
- Observable pattern or callback support for updates

**Frequency:** Very High - Continuous during dashboard usage

**Complexity:** Medium

**Priority:** P0 (Must-have)

---

### 1.3 Scenario: Retrieve Historical Sensor Data

**Description:** Fetch historical observations over a time range for analysis, charting, or export.

**User Story:** "As an analyst, I want to download all temperature observations from January 2024 so I can analyze monthly trends."

**API Operations:**

```
GET /datastreams/{id}/observations?phenomenonTime=2024-01-01T00:00:00Z/2024-02-01T00:00:00Z&limit=1000
→ Follow pagination links for complete dataset
```

**Client Library Requirements:**

- Temporal query builder (ISO 8601 intervals)
- Automatic pagination handling
- Streaming large result sets
- Format negotiation (JSON, CSV, binary)
- Progress callbacks for large downloads

**Frequency:** Medium - Regular analysis tasks

**Complexity:** Medium-High (pagination, streaming)

**Priority:** P0 (Must-have)

---

### 1.4 Scenario: Send Commands to Actuators/Controllers

**Description:** Issue commands to controllable systems (actuators, PTZ cameras, UAVs) and monitor execution status.

**User Story:** "As a camera operator, I want to send a pan command to camera X and wait for confirmation that it completed."

**API Operations:**

```
1. GET /systems/{id}/controlstreams
2. POST /controlstreams/{id}/commands
   → 201 Created with Location header
3. GET /commands/{id}/status (poll until COMPLETED)
4. GET /commands/{id}/result (optional)
```

**Client Library Requirements:**

- Schema validation before submission
- Async command handling with polling
- Status monitoring with timeout
- Promise-based API for async execution
- Synchronous command support

**Frequency:** Medium-High - Operational control scenarios

**Complexity:** High (async handling, status monitoring)

**Priority:** P0 (Must-have)

---

### 1.5 Scenario: Monitor Real-Time Data Streams

**Description:** Subscribe to continuous data from live datastreams with automatic updates.

**User Story:** "As a monitoring operator, I want to watch live video telemetry from a UAV and see position updates in real-time."

**API Operations:**

```
1. GET /datastreams/{id} → Check live=true
2. Poll: GET /datastreams/{id}/observations?resultTime=2024-01-15T12:00:00Z/..
   (incremental fetch with advancing timestamp)
```

**Client Library Requirements:**

- Polling with incremental time window
- Back-pressure handling if observations arrive faster than consumed
- Reconnection on failure
- Observable/EventEmitter pattern
- Configurable poll interval

**Frequency:** High - Continuous monitoring applications

**Complexity:** High (streaming, state management)

**Priority:** P0 (Must-have)

---

### 1.6 Scenario: Deploy Sensor Networks

**Description:** Register a new deployment with multiple systems, spatial extent, and temporal validity.

**User Story:** "As a project manager, I want to register a river monitoring deployment with 10 sensors along the waterway for Q1 2024."

**API Operations:**

```
1. POST /deployments
   Body: {
     name: "River Monitoring Q1 2024",
     validTime: ["2024-01-01T00:00:00Z", "2024-04-01T00:00:00Z"],
     geometry: { type: "LineString", coordinates: [...] },
     deployedSystems: [...]
   }
2. For each system: POST /systems/{sysId}/samplingFeatures (optional)
3. GET /deployments/{id}/datastreams → Monitor all deployment data
```

**Client Library Requirements:**

- Deployment creation with validation
- Bulk system association
- Subdeployment support
- Deployment hierarchy navigation

**Frequency:** Low-Medium - Project initialization

**Complexity:** Medium

**Priority:** P1 (Should-have)

---

### 1.7 Scenario: Navigate System Hierarchies

**Description:** Traverse parent-child system relationships to understand complex platforms with multiple sensors.

**User Story:** "As a systems engineer, I want to see all sensors on a UAV platform, including those on gimbals and payloads."

**API Operations:**

```
GET /systems/{platformId}/subsystems?recursive=true
→ Returns all nested subsystems at all levels
```

**Client Library Requirements:**

- Recursive query support
- Tree structure building
- Lazy loading of subsystem details
- Aggregation of datastreams from system + subsystems

**Frequency:** Medium - System inspection and configuration

**Complexity:** Medium

**Priority:** P1 (Should-have)

---

### 1.8 Scenario: Track System History

**Description:** Access historical system configurations to understand how a system changed over time.

**User Story:** "As a data curator, I want to see all versions of a sensor's configuration to understand calibration changes."

**API Operations:**

```
GET /systems/{id}?datetime=2023-01-01T00:00:00Z
→ System as it was on specific date (via validTime)
```

**Client Library Requirements:**

- Temporal queries on system resources
- Version comparison utilities
- ValidTime handling

**Frequency:** Low - Auditing and troubleshooting

**Complexity:** Low-Medium

**Priority:** P2 (Nice-to-have)

---

### 1.9 Scenario: Manage Sampling Strategies

**Description:** Create and manage sampling features that describe how systems observe features of interest.

**User Story:** "As a data scientist, I want to register water sampling points along a river and link them to the sensors that collect samples."

**API Operations:**

```
1. POST /systems/{sysId}/samplingFeatures
   Body: {
     featureType: "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint",
     geometry: { type: "Point", coordinates: [...] },
     sampledFeature: { href: "rivers/123" }
   }
2. Link to datastreams: datastream.samplingFeature@link
```

**Client Library Requirements:**

- Sampling feature creation
- FOI relationship management
- Spatial sampling geometry support

**Frequency:** Low-Medium - Data collection setup

**Complexity:** Medium

**Priority:** P2 (Nice-to-have)

---

### 1.10 Scenario: Command Feasibility Checking

**Description:** Check if a command is feasible before issuing it (e.g., satellite tasking conflicts).

**User Story:** "As a mission planner, I want to check if a satellite imaging task is feasible before submitting the actual command."

**API Operations:**

```
1. POST /controlstreams/{id}/feasibility
   Body: { same as command parameters }
2. GET /feasibility/{id}/status → Check COMPLETED
3. GET /feasibility/{id}/result → Get feasibility assessment
```

**Client Library Requirements:**

- Feasibility request creation
- Status monitoring
- Result interpretation

**Frequency:** Low - Advanced commanding scenarios

**Complexity:** Medium

**Priority:** P2 (Nice-to-have)

---

### 1.11 Scenario: Monitor System Events

**Description:** Track system lifecycle events (activation, maintenance, calibration, failure).

**User Story:** "As a fleet manager, I want to see all maintenance events for my sensor network in the past month."

**API Operations:**

```
GET /systems/{id}/events?time=2024-01-01T00:00:00Z/..
```

**Client Library Requirements:**

- Event querying and filtering
- Event classification handling
- Timeline visualization support

**Frequency:** Low-Medium - System administration

**Complexity:** Low

**Priority:** P2 (Nice-to-have)

---

### 1.12 Scenario: Integrate with Mapping Applications

**Description:** Display sensor locations on interactive maps using OpenLayers, Leaflet, or Mapbox.

**User Story:** "As a GIS analyst, I want to see all sensors on a map with popups showing current readings."

**API Operations:**

```
GET /systems?bbox={viewport}&format=application/geo+json
→ Returns GeoJSON FeatureCollection
```

**Client Library Requirements:**

- GeoJSON format support
- Easy integration with map libraries
- Coordinate system handling (CRS)
- Feature styling helpers

**Frequency:** High - Map-based applications

**Complexity:** Low (with library integration)

**Priority:** P0 (Must-have)

---

### 1.13 Scenario: Build Sensor Monitoring Dashboards

**Description:** Create real-time dashboards displaying multiple sensors with charts, maps, and alerts.

**User Story:** "As an operations center, I want a dashboard showing 50 sensors with live charts updating every 5 seconds."

**API Operations:**

```
For each sensor:
1. GET /datastreams/{id}/observations?resultTime=latest
2. Poll every 5 seconds
Display on charts/gauges
```

**Client Library Requirements:**

- Batch fetching multiple datastreams
- Efficient polling with backoff
- Observable pattern for reactive updates
- Integration with charting libraries

**Frequency:** Very High - Dashboard applications

**Complexity:** High (multiple concurrent requests)

**Priority:** P0 (Must-have)

---

### 1.14 Scenario: Control UAV/Satellite Tasking

**Description:** Issue imaging or data collection tasks to remote platforms and retrieve resulting data.

**User Story:** "As a remote sensing operator, I want to task a satellite to image a specific area and download the resulting observations."

**API Operations:**

```
1. POST /controlstreams/{id}/commands
   Body: { target area, parameters }
2. Poll status until COMPLETED
3. GET /commands/{id}/result
   → Returns datastream link or observation references
4. Fetch observations from result datastream
```

**Client Library Requirements:**

- Complex command parameters
- Long-running task support (hours/days)
- Result datastream resolution
- Callback on completion

**Frequency:** Low-Medium - Mission planning

**Complexity:** High (async, long-running)

**Priority:** P1 (Should-have)

---

### 1.15 Scenario: Manage Procedure Definitions

**Description:** Store and query sensor datasheets, calibration procedures, and methodologies.

**User Story:** "As a sensor manufacturer, I want to publish datasheets for my sensor models so users can query specifications."

**API Operations:**

```
1. POST /procedures
   Body: SensorML PhysicalComponent description
2. Link systems to procedure: system.systemKind@link
3. GET /systems?procedure={procId}
   → Find all instances of sensor model
```

**Client Library Requirements:**

- SensorML format support
- Procedure-system association
- Type-instance relationship queries

**Frequency:** Low - Catalog management

**Complexity:** Medium (SensorML parsing)

**Priority:** P2 (Nice-to-have)

---

## 2. Essential Workflows

### 2.1 Workflow: Discovery and Initial Connection

**Purpose:** Establish connection to CSAPI server and discover available resources.

**Steps:**

```
1. Initialize client with base URL
   → client = new CSAPIClient('https://api.example.org/csapi')

2. Fetch conformance
   → GET /conformance
   → Cache conformance URIs for capability checks

3. List collections
   → GET /collections
   → Identify systems, datastreams, deployments collections

4. Select target resources
   → Decide which collections to work with based on application needs

5. Ready for operations
```

**Client Library API:**

```typescript
// Simplified API
const client = new CSAPIClient({
  baseUrl: 'https://api.example.org/csapi',
  auth: { token: '...' },
});

await client.initialize(); // Steps 2-3 automatically
const capabilities = client.getCapabilities(); // Cached conformance

const collections = await client.getCollections();
```

**Requirements:**

- Automatic conformance detection on initialization
- Capability caching (rarely changes)
- Collection metadata parsing
- Connection validation

---

### 2.2 Workflow: Real-Time Sensor Monitoring

**Purpose:** Poll sensor observations continuously for live monitoring.

**Steps:**

```
1. Find system
   → GET /systems?observedProperty={prop}&bbox={area}

2. Get datastreams
   → GET /systems/{id}/datastreams
   → Filter to desired observed properties

3. Check live availability
   → Verify datastream.live === true

4. Fetch latest observation
   → GET /datastreams/{id}/observations?resultTime=latest

5. Poll for updates (repeat step 4)
   → Every 5 seconds
   → Update UI with new observations

6. Handle errors and reconnection
   → Exponential backoff on failures
```

**Client Library API:**

```typescript
// High-level polling abstraction
const systems = await client.findSystems({
  bbox: [-122.5, 37.5, -122.3, 37.7],
  observedProperty: 'temperature',
});

const datastreams = await systems[0].getDataStreams();
const liveStream = datastreams.find((ds) => ds.live);

// Observable pattern
liveStream.observe({
  interval: 5000,
  onData: (observation) => updateUI(observation),
  onError: (error) => handleError(error),
});
```

**Requirements:**

- Polling abstraction with configurable interval
- Observable/EventEmitter pattern
- Automatic error handling and reconnection
- Efficient incremental fetching

---

### 2.3 Workflow: Historical Data Retrieval

**Purpose:** Download historical observations for analysis.

**Steps:**

```
1. Find system and datastream
   → GET /systems/{id}/datastreams

2. Request observations with time range
   → GET /datastreams/{id}/observations?phenomenonTime={start}/{end}&limit=1000

3. Process first page
   → Parse observations

4. Follow pagination links
   → GET {next_url}
   → Repeat until no more pages

5. Aggregate results
   → Combine all observations
   → Export or analyze
```

**Client Library API:**

```typescript
// Automatic pagination handling
const observations = await datastream.getObservations({
  phenomenonTime: ['2024-01-01', '2024-02-01'],
  autoPaginate: true, // Fetches all pages
  onProgress: (page, total) => updateProgress(page, total),
});

// Streaming for large datasets
for await (const observation of datastream.observationStream({
  phenomenonTime: ['2024-01-01', '2024-02-01'],
})) {
  process(observation);
}
```

**Requirements:**

- Automatic pagination handling
- Streaming API for large datasets
- Progress callbacks
- Format negotiation (CSV, binary)

---

### 2.4 Workflow: Command and Control (Asynchronous)

**Purpose:** Issue commands to actuators and monitor execution.

**Steps:**

```
1. Find actuator system
   → GET /systems?controlledProperty={prop}

2. Get control streams
   → GET /systems/{id}/controlstreams

3. Check command acceptance
   → Verify controlstream.live === true

4. Validate command parameters
   → Check against controlstream.schema

5. Issue command
   → POST /controlstreams/{id}/commands
   → Receive 201 with command ID

6. Poll status
   → GET /commands/{id}/status
   → Wait for PENDING → ACCEPTED → EXECUTING → COMPLETED

7. Retrieve result (optional)
   → GET /commands/{id}/result
```

**Client Library API:**

```typescript
// Promise-based async command
const systems = await client.findSystems({
  controlledProperty: 'pan',
});

const controlStreams = await systems[0].getControlStreams();
const panStream = controlStreams[0];

// Async/await pattern
const command = await panStream.sendCommand({
  params: { pan: 45 },
  executionTime: 'now',
});

await command.waitForCompletion({ timeout: 30000 });
const result = await command.getResult();
```

**Requirements:**

- Schema validation before submission
- Promise-based async API
- Status polling with timeout
- Cancellation support
- Result retrieval

---

### 2.5 Workflow: Deployment Tracking

**Purpose:** Register and monitor sensor network deployments.

**Steps:**

```
1. Create deployment resource
   → POST /deployments
   Body: {
     name, validTime, geometry,
     deployedSystems: [system links]
   }

2. Associate systems
   → Systems linked via deployedSystems array

3. Create sampling features (optional)
   → POST /systems/{id}/samplingFeatures for each sensor

4. Monitor deployment data
   → GET /deployments/{id}/datastreams
   → Aggregate observations from all deployed systems

5. Track subdeployments (optional)
   → GET /deployments/{id}/subdeployments?recursive=true

6. Update deployment when ended
   → PATCH /deployments/{id}
   Update validTime end date
```

**Client Library API:**

```typescript
// Deployment creation
const deployment = await client.createDeployment({
  name: 'River Monitoring Q1 2024',
  validTime: ['2024-01-01', '2024-04-01'],
  geometry: riverLineString,
  deployedSystems: systemIds,
});

// Monitor all deployment data
const datastreams = await deployment.getDataStreams();
const observations = await deployment.getAllObservations({
  phenomenonTime: ['2024-01-01', '2024-02-01'],
});
```

**Requirements:**

- Deployment CRUD operations
- System association handling
- Hierarchy navigation
- Aggregated data queries

---

### 2.6 Workflow: Feasibility Check Before Commanding

**Purpose:** Validate command feasibility before execution.

**Steps:**

```
1. Find control stream
   → GET /controlstreams/{id}

2. Create feasibility request
   → POST /controlstreams/{id}/feasibility
   Body: { same parameters as actual command }

3. Monitor feasibility status
   → GET /feasibility/{id}/status
   → Wait for COMPLETED

4. Check feasibility result
   → GET /feasibility/{id}/result
   → Evaluate success probability, conflicts, etc.

5. If feasible, issue actual command
   → POST /controlstreams/{id}/commands

6. Monitor command execution
   → Same as command workflow
```

**Client Library API:**

```typescript
// Feasibility check
const feasibility = await controlStream.checkFeasibility({
  params: { target: targetArea },
  executionTime: '2024-01-15T12:00:00Z',
});

if (feasibility.isFeasible) {
  const command = await controlStream.sendCommand({
    params: { target: targetArea },
    executionTime: '2024-01-15T12:00:00Z',
  });
  await command.waitForCompletion();
}
```

**Requirements:**

- Feasibility request creation
- Status monitoring
- Result interpretation
- Integration with command workflow

---

## 3. Common Query Patterns

### 3.1 Spatial Filtering

**Pattern:** Find resources within geographic bounds

**Examples:**

```
# City area
GET /systems?bbox=-122.5,37.5,-122.3,37.7

# Global
GET /deployments?bbox=-180,-90,180,90

# Custom CRS (if supported)
GET /systems?bbox=500000,4500000,600000,4600000&bbox-crs=EPSG:3857
```

**Library Support:**

```typescript
// BBox builder
const systems = await client.findSystems({
  bbox: {
    west: -122.5,
    south: 37.5,
    east: -122.3,
    north: 37.7,
  },
});

// Or array format
const systems = await client.findSystems({
  bbox: [-122.5, 37.5, -122.3, 37.7],
});
```

---

### 3.2 Temporal Filtering

**Pattern:** Query resources by time range or instant

**Examples:**

```
# Specific day
GET /observations?phenomenonTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z

# Since timestamp
GET /datastreams?resultTime=2024-01-01T00:00:00Z/..

# Before timestamp
GET /systems?datetime=../2024-01-01T00:00:00Z

# Latest observation
GET /observations?resultTime=latest

# Current systems (validTime contains now)
GET /systems?datetime=now
```

**Library Support:**

```typescript
// Time range builder
const observations = await datastream.getObservations({
  phenomenonTime: {
    start: '2024-01-15',
    end: '2024-01-16',
  },
});

// Or ISO interval
const observations = await datastream.getObservations({
  phenomenonTime: '2024-01-15/2024-01-16',
});

// Special values
const latest = await datastream.getLatestObservation();

const active = await client.findSystems({
  datetime: 'now',
});
```

---

### 3.3 Property-Based Filtering

**Pattern:** Find resources by observed or controlled properties

**Examples:**

```
# Temperature sensors
GET /systems?observedProperty=http://qudt.org/vocab/quantitykind/Temperature

# Or CURIE format
GET /systems?observedProperty=qudt:Temperature

# Multiple properties
GET /systems?observedProperty=temperature,humidity

# PTZ control
GET /controlstreams?controlledProperty=http://example.org/properties/pan
```

**Library Support:**

```typescript
// Property filter
const sensors = await client.findSystems({
  observedProperty: ['temperature', 'humidity'],
});

const actuators = await client.findSystems({
  controlledProperty: 'pan',
});
```

---

### 3.4 Combined Filters

**Pattern:** Multiple filters for precise queries

**Examples:**

```
# Active temp sensors in SF
GET /systems?bbox=-122.5,37.5,-122.3,37.7&observedProperty=temperature&datetime=now

# Recent observations from specific datastream
GET /observations?datastream={id}&phenomenonTime=2024-01-15T00:00:00Z/..&limit=1000

# Deployments in area during time period
GET /deployments?bbox={bbox}&datetime=2024-01-01T00:00:00Z/2024-02-01T00:00:00Z
```

**Library Support:**

```typescript
// Combine multiple filters
const systems = await client.findSystems({
  bbox: [-122.5, 37.5, -122.3, 37.7],
  observedProperty: 'temperature',
  datetime: 'now',
  limit: 50,
});
```

---

### 3.5 Recursive Traversal

**Pattern:** Navigate hierarchical relationships

**Examples:**

```
# All nested subsystems
GET /systems/{id}/subsystems?recursive=true

# All deployments including subdeployments
GET /deployments?recursive=true

# Top-level only (default)
GET /systems/{id}/subsystems
GET /systems/{id}/subsystems?recursive=false
```

**Library Support:**

```typescript
// Recursive query
const allSubsystems = await system.getSubsystems({
  recursive: true,
});

// Build tree structure
const tree = await system.getHierarchy();
// Returns nested structure: { system, subsystems: [...] }
```

---

### 3.6 Relationship Traversal

**Pattern:** Follow links between related resources

**Examples:**

```
# System relationships
GET /systems/{id}/datastreams
GET /systems/{id}/controlstreams
GET /systems/{id}/deployments
GET /systems/{id}/samplingFeatures
GET /systems/{id}/subsystems

# Datastream relationships
GET /datastreams/{id}/observations
GET /datastreams/{id}/system

# Command relationships
GET /commands/{id}/status
GET /commands/{id}/result
```

**Library Support:**

```typescript
// Relationship navigation
const system = await client.getSystem(id);
const datastreams = await system.getDataStreams();
const observations = await datastreams[0].getObservations();

// Or fluent API
const observations = await client
  .getSystem(id)
  .getDataStreams()
  .then((ds) => ds[0].getObservations());
```

---

### 3.7 Pagination Patterns

**Pattern:** Handle large result sets

**Examples:**

```
# First page (default limit: 10)
GET /observations

# Custom page size
GET /observations?limit=1000

# Follow next link
GET /observations?limit=1000
→ Response includes: links: [{ rel: 'next', href: '...' }]
GET {next_href}
```

**Library Support:**

```typescript
// Manual pagination
const page1 = await datastream.getObservations({ limit: 1000 });
if (page1.links.next) {
  const page2 = await client.fetch(page1.links.next);
}

// Auto-pagination
const allObservations = await datastream.getObservations({
  limit: 1000,
  autoPaginate: true,
});

// Streaming
for await (const obs of datastream.observationStream()) {
  process(obs);
}
```

---

### 3.8 ID-Based Queries

**Pattern:** Query specific resources by ID

**Examples:**

```
# Single resource
GET /systems/{id}
GET /datastreams/{id}

# Multiple resources by ID list
GET /systems?id=sys1,sys2,sys3

# By unique ID (UID)
GET /systems?uid=urn:uuid:550e8400-e29b-41d4-a716-446655440000
```

**Library Support:**

```typescript
// Single resource
const system = await client.getSystem('sys1');

// Batch fetch
const systems = await client.getSystems(['sys1', 'sys2', 'sys3']);

// By UID
const system = await client.findSystemByUID('urn:uuid:...');
```

---

## 4. Convenience Methods

### 4.1 High-Level Discovery Methods

#### 4.1.1 `findSystemsInArea(bbox, options?)`

**Purpose:** Discover sensors in geographic area

**Usage:**

```typescript
const systems = await client.findSystemsInArea([-122.5, 37.5, -122.3, 37.7], {
  observedProperty: ['temperature', 'humidity'],
  datetime: 'now',
  systemType: 'sosa:Sensor',
});
```

**Benefits:**

- Simplified spatial queries
- Common filter combinations
- GeoJSON output ready for mapping

---

#### 4.1.2 `findDataStreams(filters)`

**Purpose:** Search for datastreams across systems

**Usage:**

```typescript
const streams = await client.findDataStreams({
  bbox: [-122.5, 37.5, -122.3, 37.7],
  observedProperty: 'temperature',
  live: true,
  resultType: 'measure',
});
```

**Benefits:**

- Cross-system datastream discovery
- Filter by live status
- Filter by result type

---

### 4.2 Data Access Methods

#### 4.2.1 `getLatestObservations(datastreamId, count?)`

**Purpose:** Quick access to most recent observations

**Usage:**

```typescript
const latest = await client.getLatestObservations(datastreamId);
// Returns single latest observation

const recent = await client.getLatestObservations(datastreamId, 10);
// Returns 10 most recent observations
```

**Benefits:**

- No need to construct temporal queries
- Common dashboard pattern
- Efficient single-request operation

---

#### 4.2.2 `streamObservations(datastreamId, callback, options?)`

**Purpose:** Polling abstraction for real-time monitoring

**Usage:**

```typescript
const subscription = client.streamObservations(
  datastreamId,
  (observation) => updateChart(observation),
  {
    interval: 5000,
    onError: (err) => console.error(err),
    backoff: 'exponential',
  }
);

// Later: stop streaming
subscription.unsubscribe();
```

**Benefits:**

- Observable pattern
- Automatic error handling
- Configurable polling strategy
- Memory-safe unsubscribe

---

#### 4.2.3 `getObservationsInRange(datastreamId, start, end, options?)`

**Purpose:** Simplified historical data retrieval

**Usage:**

```typescript
const observations = await client.getObservationsInRange(
  datastreamId,
  '2024-01-01',
  '2024-02-01',
  {
    autoPaginate: true,
    format: 'csv',
    onProgress: (page, total) => updateProgress(page, total),
  }
);
```

**Benefits:**

- Automatic pagination
- Format conversion
- Progress tracking
- Date parsing

---

### 4.3 Command and Control Methods

#### 4.3.1 `sendCommandAndWait(controlstreamId, params, options?)`

**Purpose:** Async command with automatic status polling

**Usage:**

```typescript
const result = await client.sendCommandAndWait(
  controlstreamId,
  { pan: 45, tilt: 0 },
  {
    executionTime: 'now',
    timeout: 30000,
    onStatus: (status) => updateUI(status),
  }
);
```

**Benefits:**

- Promise-based async handling
- Automatic status polling
- Timeout protection
- Progress callbacks

---

#### 4.3.2 `checkCommandFeasibility(controlstreamId, params)`

**Purpose:** Pre-validate commands

**Usage:**

```typescript
const feasibility = await client.checkCommandFeasibility(controlstreamId, {
  target: area,
  time: '2024-01-15T12:00:00Z',
});

if (feasibility.isFeasible) {
  await client.sendCommand(controlstreamId, params);
}
```

**Benefits:**

- Validation before execution
- Conflict detection
- Cost/risk assessment

---

### 4.4 Navigation Methods

#### 4.4.1 `getSystemHierarchy(systemId, recursive?)`

**Purpose:** Build system tree structure

**Usage:**

```typescript
const tree = await client.getSystemHierarchy(systemId, true);
// Returns:
// {
//   system: {...},
//   subsystems: [
//     { system: {...}, subsystems: [...] },
//     ...
//   ]
// }
```

**Benefits:**

- Tree structure building
- Recursive relationships
- Ready for UI rendering

---

#### 4.4.2 `getDeploymentData(deploymentId, options?)`

**Purpose:** Aggregate data from all deployed systems

**Usage:**

```typescript
const data = await client.getDeploymentData(deploymentId, {
  phenomenonTime: ['2024-01-01', '2024-02-01'],
  limit: 1000,
});
// Returns all observations from all datastreams of all deployed systems
```

**Benefits:**

- Cross-system aggregation
- Simplified deployment monitoring
- Single query for complex data

---

### 4.5 Utility Methods

#### 4.5.1 `buildBboxQuery(bounds)`

**Purpose:** Spatial query builder

**Usage:**

```typescript
const bbox = client.buildBboxQuery({
  west: -122.5,
  south: 37.5,
  east: -122.3,
  north: 37.7,
});
// Returns: "-122.5,37.5,-122.3,37.7"
```

**Benefits:**

- Named parameters
- Validation
- Array conversion

---

#### 4.5.2 `buildTimeRange(start, end)`

**Purpose:** Temporal query builder

**Usage:**

```typescript
const range = client.buildTimeRange('2024-01-01', '2024-02-01');
// Returns: "2024-01-01T00:00:00Z/2024-02-01T00:00:00Z"

const openStart = client.buildTimeRange(null, '2024-01-01');
// Returns: "../2024-01-01T00:00:00Z"
```

**Benefits:**

- ISO 8601 formatting
- Open interval support
- Date parsing

---

#### 4.5.3 `paginateAll(url, options?)`

**Purpose:** Auto-pagination iterator

**Usage:**

```typescript
const allPages = await client.paginateAll(url, { limit: 1000 });
// Returns all results from all pages

// Or streaming
for await (const page of client.paginateAllStream(url)) {
  process(page.items);
}
```

**Benefits:**

- Automatic link following
- Memory-efficient streaming
- Progress tracking

---

#### 4.5.4 `resolveLinks(resource, linkRels?)`

**Purpose:** Fetch related resources

**Usage:**

```typescript
const system = await client.getSystem(id);
const resolved = await client.resolveLinks(system, [
  'datastreams',
  'subsystems',
]);
// Returns system with datastreams and subsystems populated
```

**Benefits:**

- Lazy loading
- Selective resolution
- Reduced round trips

---

#### 4.5.5 `formatObservation(observation, schema)`

**Purpose:** Schema-aware observation formatting

**Usage:**

```typescript
const schema = await datastream.getSchema();
const formatted = client.formatObservation(observation, schema);
// Converts result based on schema (units, labels, etc.)
```

**Benefits:**

- Schema interpretation
- Unit formatting
- Label resolution

---

### 4.6 Validation Methods

#### 4.6.1 `validateObservationSchema(observation, schema)`

**Purpose:** Client-side validation before submission

**Usage:**

```typescript
const valid = client.validateObservationSchema(observation, schema);
if (!valid) {
  console.error(client.getValidationErrors());
} else {
  await datastream.createObservation(observation);
}
```

**Benefits:**

- Prevent 400 errors
- Early error detection
- Schema compliance checking

---

#### 4.6.2 `checkServerCapabilities(endpoint?)`

**Purpose:** Feature detection

**Usage:**

```typescript
const caps = await client.checkServerCapabilities();
// Returns:
// {
//   hasAdvancedFiltering: true,
//   hasCRUD: true,
//   hasUpdate: true,
//   supportedFormats: ['application/geo+json', 'application/sml+json'],
//   ...
// }

if (caps.hasCRUD) {
  await client.createSystem(system);
}
```

**Benefits:**

- Conformance detection
- Graceful degradation
- Feature availability checks

---

## 5. Error Handling Requirements

### 5.1 Common Failure Scenarios

#### 5.1.1 Network Errors

**Scenarios:**

- Connection timeout
- DNS resolution failure
- SSL/TLS errors
- Network interruption

**Handling Strategy:**

```typescript
try {
  const systems = await client.findSystems({...});
} catch (error) {
  if (error instanceof NetworkError) {
    // Retry with exponential backoff
    await retry(() => client.findSystems({...}), {
      retries: 3,
      backoff: 'exponential'
    });
  }
}
```

**Requirements:**

- Automatic retry for transient failures
- Exponential backoff
- Configurable retry limits
- Timeout configuration

---

#### 5.1.2 Authentication Errors (401)

**Scenarios:**

- Missing credentials
- Expired token
- Invalid token

**Handling Strategy:**

```typescript
client.on('authError', async () => {
  // Refresh token
  const newToken = await refreshAuthToken();
  client.setAuthToken(newToken);
  // Retry failed request
});
```

**Requirements:**

- Token refresh callback
- Automatic retry after refresh
- OAuth2/OIDC integration support

---

#### 5.1.3 Authorization Errors (403)

**Scenarios:**

- Insufficient permissions
- Resource access denied

**Handling Strategy:**

```typescript
try {
  await client.createSystem(system);
} catch (error) {
  if (error.status === 403) {
    console.error('Permission denied:', error.message);
    // Don't retry - inform user
  }
}
```

**Requirements:**

- Clear error messages
- Don't retry (permanent failure)
- User notification

---

#### 5.1.4 Invalid Queries (400)

**Scenarios:**

- Malformed query parameters
- Invalid temporal format
- Invalid spatial bbox
- Schema validation failure

**Examples:**

```
GET /observations?resultTime=invalid
→ 400 Bad Request

POST /datastreams/{id}/observations
Body: { result: "wrong type" }
→ 400 Bad Request - schema validation failure
```

**Handling Strategy:**

```typescript
try {
  await datastream.createObservation(obs);
} catch (error) {
  if (error.status === 400) {
    console.error('Validation failed:', error.details);
    // Fix data and retry
  }
}
```

**Requirements:**

- Client-side validation before submission
- Detailed error messages from server
- Validation error parsing
- User-friendly error display

---

#### 5.1.5 Missing Resources (404)

**Scenarios:**

- Resource ID doesn't exist
- Deleted resource
- Wrong endpoint URL

**Handling Strategy:**

```typescript
const system = await client.getSystem(id);
if (!system) {
  // Handle missing resource
  console.error(`System ${id} not found`);
}

// Or with try/catch
try {
  const system = await client.getSystem(id);
} catch (error) {
  if (error.status === 404) {
    // Resource doesn't exist
  }
}
```

**Requirements:**

- Null vs exception handling (configurable)
- Clear error messages
- Suggestion for similar resources

---

#### 5.1.6 Conflict Errors (409)

**Scenarios:**

- Delete datastream with observations (cascade required)
- Update schema when observations exist
- Duplicate resource creation

**Examples:**

```
DELETE /datastreams/{id}
→ 409 Conflict "Datastream has observations, use cascade=true"

PUT /datastreams/{id}/schema
→ 409 Conflict "Cannot modify schema when observations exist"
```

**Handling Strategy:**

```typescript
try {
  await datastream.delete();
} catch (error) {
  if (error.status === 409 && error.code === 'CASCADE_REQUIRED') {
    // Retry with cascade
    await datastream.delete({ cascade: true });
  }
}
```

**Requirements:**

- Parse conflict reason from error
- Suggest resolution (cascade, create new, etc.)
- Automatic resolution for common cases

---

#### 5.1.7 Server Errors (5XX)

**Scenarios:**

- Internal server error (500)
- Service unavailable (503)
- Gateway timeout (504)

**Handling Strategy:**

```typescript
try {
  await client.findSystems({...});
} catch (error) {
  if (error.status >= 500) {
    // Retry with backoff
    await retry(() => client.findSystems({...}), {
      retries: 5,
      backoff: 'exponential',
      maxDelay: 60000
    });
  }
}
```

**Requirements:**

- Automatic retry for 5XX
- Exponential backoff
- Circuit breaker pattern
- Fallback to cached data

---

#### 5.1.8 Rate Limiting (429)

**Scenarios:**

- Too many requests
- Quota exceeded

**Handling Strategy:**

```typescript
try {
  await client.findSystems({...});
} catch (error) {
  if (error.status === 429) {
    const retryAfter = error.headers['Retry-After'];
    await sleep(retryAfter * 1000);
    // Retry request
  }
}
```

**Requirements:**

- Respect Retry-After header
- Automatic backoff
- Request throttling
- Queue management

---

### 5.2 Error Recovery Strategies

**Strategy Matrix:**

| Error Type              | Retry?               | Backoff     | User Action       |
| ----------------------- | -------------------- | ----------- | ----------------- |
| Network timeout         | Yes                  | Exponential | Inform user       |
| 401 Unauthorized        | Yes (after refresh)  | None        | Prompt login      |
| 403 Forbidden           | No                   | -           | Show error        |
| 400 Bad Request         | No                   | -           | Fix input         |
| 404 Not Found           | No                   | -           | Handle gracefully |
| 409 Conflict            | Maybe (with cascade) | None        | Resolve conflict  |
| 500 Server Error        | Yes                  | Exponential | Inform user       |
| 503 Service Unavailable | Yes                  | Exponential | Wait + retry      |
| 429 Rate Limit          | Yes                  | Retry-After | Throttle requests |

---

## 6. Integration Patterns

### 6.1 Map Integration (OpenLayers, Leaflet)

**Purpose:** Display sensor locations on interactive maps

**OpenLayers Example:**

```typescript
import { Vector as VectorLayer } from 'ol/layer';
import { Vector as VectorSource } from 'ol/source';
import { GeoJSON } from 'ol/format';

// Fetch systems as GeoJSON
const systems = await client.findSystems({
  bbox: map.getView().calculateExtent(),
  format: 'application/geo+json',
});

// Add to map
const vectorSource = new VectorSource({
  features: new GeoJSON().readFeatures(systems),
});

const vectorLayer = new VectorLayer({
  source: vectorSource,
  style: styleFunction,
});

map.addLayer(vectorLayer);

// Click handler
map.on('click', async (evt) => {
  const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
  if (feature) {
    const systemId = feature.getId();
    const datastreams = await client.getSystem(systemId).getDataStreams();
    // Show popup with datastreams
  }
});
```

**Requirements:**

- GeoJSON format support
- Accept header negotiation
- Feature ID preservation
- CRS handling
- Popup content generation

---

### 6.2 Charting Integration (Chart.js, D3)

**Purpose:** Visualize observation time series

**Chart.js Example:**

```typescript
import { Line } from 'react-chartjs-2';

// Fetch observations
const observations = await datastream.getObservations({
  phenomenonTime: ['2024-01-01', '2024-02-01'],
  autoPaginate: true,
});

// Extract time series
const data = {
  labels: observations.map((o) => new Date(o.phenomenonTime)),
  datasets: [
    {
      label: datastream.name,
      data: observations.map((o) => o.result),
      borderColor: 'rgb(75, 192, 192)',
    },
  ],
};

// Render chart
<Line data={data} options={options} />;

// Live updates
client.streamObservations(datastream.id, (obs) => {
  data.labels.push(new Date(obs.phenomenonTime));
  data.datasets[0].data.push(obs.result);
  chart.update();
});
```

**Requirements:**

- Simple observation result extraction
- Temporal parsing
- Real-time update support
- Data transformation helpers

---

### 6.3 Real-Time Update Integration

**Purpose:** Reactive UI updates with observables

**RxJS Example:**

```typescript
import { Observable } from 'rxjs';

// Create observable from datastream
const observable = new Observable((subscriber) => {
  const subscription = client.streamObservations(
    datastreamId,
    (obs) => subscriber.next(obs),
    { interval: 5000, onError: (err) => subscriber.error(err) }
  );

  return () => subscription.unsubscribe();
});

// Subscribe in component
observable.subscribe({
  next: (observation) => updateUI(observation),
  error: (error) => showError(error),
});
```

**React Hook Example:**

```typescript
function useObservations(datastreamId, interval = 5000) {
  const [observation, setObservation] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const subscription = client.streamObservations(
      datastreamId,
      (obs) => setObservation(obs),
      {
        interval,
        onError: (err) => setError(err),
      }
    );

    return () => subscription.unsubscribe();
  }, [datastreamId, interval]);

  return { observation, error };
}
```

**Requirements:**

- Observable/EventEmitter pattern
- Subscription management
- Error propagation
- Memory leak prevention

---

### 6.4 Binary Data Integration (SWE Common)

**Purpose:** Efficient large dataset handling

**Example:**

```typescript
// Request binary format
const observations = await datastream.getObservations({
  phenomenonTime: ['2024-01-01', '2024-02-01'],
  format: 'application/swe+binary',
});

// Parse with SWE Common library
import { SWEBinaryDecoder } from 'swe-common';

const schema = await datastream.getSchema();
const decoder = new SWEBinaryDecoder(schema.observationEncoding);
const decoded = decoder.decode(observations);

// Use decoded observations
decoded.forEach((obs) => {
  console.log(obs.phenomenonTime, obs.result);
});
```

**Requirements:**

- Format negotiation
- Schema retrieval
- Binary decoding integration
- Fallback to JSON if binary not supported

---

## 7. Data Transformation Requirements

### 7.1 Format Conversions

#### 7.1.1 GeoJSON ↔ SensorML

**Use Case:** Toggle between spatial view and detailed description

**GeoJSON to SensorML:**

```typescript
const systemGeoJSON = await client.getSystem(id, {
  format: 'application/geo+json',
});

const systemSensorML = await client.getSystem(id, {
  format: 'application/sml+json',
});
// More detailed: inputs, outputs, parameters, etc.
```

**Requirements:**

- Format negotiation via Accept header
- Automatic parsing based on Content-Type
- Format detection helpers

---

#### 7.1.2 JSON ↔ SWE Common Formats

**Use Case:** Efficient transmission vs human readability

**JSON Observations:**

```json
{
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": 23.5
}
```

**SWE Common CSV:**

```
2024-01-15T12:00:00Z,2024-01-15T12:00:01Z,23.5
2024-01-15T12:05:00Z,2024-01-15T12:05:01Z,23.7
```

**SWE Common Binary:**

- 10-100x smaller than JSON
- Structured binary encoding
- Requires schema for decoding

**Requirements:**

- Format conversion helpers
- Schema-aware parsing
- Encoding/decoding utilities

---

### 7.2 Observation Result Parsing

**Result Types:**

1. **Measure (single value):**

```typescript
const obs = { result: 23.5 };
const value = obs.result; // number
```

2. **Vector (array of values):**

```typescript
const obs = { result: [23.5, 45.2, 67.8] };
const [x, y, z] = obs.result;
```

3. **Record (structured data):**

```typescript
const obs = {
  result: {
    temperature: 23.5,
    humidity: 45.2,
    pressure: 1013.25,
  },
};
const temp = obs.result.temperature;
```

4. **Complex (SWE Common structures):**

```typescript
const obs = {
  result: {
    type: 'DataRecord',
    fields: [
      { name: 'temp', component: { type: 'Quantity', value: 23.5 } },
      { name: 'unit', component: { type: 'Text', value: '°C' } },
    ],
  },
};
```

**Requirements:**

- Result type detection
- Schema-aware parsing
- Type-safe accessors
- Unit extraction

---

### 7.3 Temporal Data Handling

**ISO 8601 Parsing:**

```typescript
// Instant
const instant = parseDateTime('2024-01-15T12:00:00Z');
// Returns Date object

// Interval
const interval = parseInterval('2024-01-01/2024-02-01');
// Returns { start: Date, end: Date }

// Duration
const duration = parseDuration('PT5M');
// Returns 300000 (milliseconds)
```

**Special Values:**

```typescript
// "now" - current time
// "latest" - most recent observation
// ".." - open interval (../2024-01-01 or 2024-01-01/..)
```

**Requirements:**

- ISO 8601 parsing library
- Date/time utilities
- Timezone handling
- Special value support

---

### 7.4 Unit Conversions

**UOM Extraction:**

```typescript
const schema = await datastream.getSchema();
const uom = schema.resultSchema.uom;
// { code: 'Cel', symbol: '°C', label: 'degree Celsius' }
```

**Conversion:**

```typescript
const observation = { result: 23.5 }; // Celsius
const fahrenheit = convertUnit(observation.result, 'Cel', '[degF]');
// 74.3
```

**Requirements:**

- UCUM code parsing
- Unit conversion library
- Unit compatibility checking
- Display formatting

---

## 8. Performance Considerations

### 8.1 Pagination Strategies

**Optimal Page Sizes:**

- **Systems/Deployments:** 10-50 (rich metadata)
- **Datastreams:** 50-100 (moderate metadata)
- **Observations:** 100-1000 (lightweight data)
- **Binary format:** 1000-10000 (highly compressed)

**Pagination Patterns:**

1. **Cursor-based (follow links):**

```typescript
let page = await client.getObservations({ limit: 1000 });
while (page.links.next) {
  process(page.items);
  page = await client.fetch(page.links.next);
}
```

2. **Offset-based:**

```typescript
for (let offset = 0; offset < total; offset += 1000) {
  const page = await client.getObservations({ limit: 1000, offset });
  process(page.items);
}
```

3. **Streaming (memory-efficient):**

```typescript
for await (const observation of datastream.observationStream()) {
  process(observation);
  // No large arrays in memory
}
```

**Requirements:**

- Configurable page sizes
- Link-based pagination
- Streaming API
- Memory management

---

### 8.2 Caching Recommendations

**Cache-Friendly Resources:**

1. **Conformance (long-lived):**

```typescript
const conformance = await client.getConformance();
cache.set('conformance', conformance, { ttl: 86400000 }); // 24 hours
```

2. **System/Deployment metadata (medium-lived):**

```typescript
const system = await client.getSystem(id);
cache.set(`system:${id}`, system, { ttl: 3600000 }); // 1 hour
```

3. **Schemas (locked once observations exist):**

```typescript
const schema = await datastream.getSchema();
cache.set(`schema:${datastream.id}`, schema, { ttl: Infinity }); // Never expire
```

**Don't Cache:**

- Observations (real-time data)
- Command status (changes frequently)
- Live datastreams (current state)

**Cache Invalidation:**

- On PUT/PATCH/DELETE operations
- On 304 Not Modified response
- On ETag mismatch

**Requirements:**

- Cache API integration
- TTL configuration
- ETag support
- Conditional requests

---

### 8.3 Streaming Large Datasets

**Strategies:**

1. **Time Window Chunking:**

```typescript
const start = new Date('2024-01-01');
const end = new Date('2024-12-31');

// Process month by month
for (let month = start; month < end; month.setMonth(month.getMonth() + 1)) {
  const observations = await datastream.getObservations({
    phenomenonTime: [
      month,
      new Date(month.getFullYear(), month.getMonth() + 1, 0),
    ],
  });
  process(observations);
}
```

2. **Binary Format:**

```typescript
// 10-100x size reduction
const observations = await datastream.getObservations({
  format: 'application/swe+binary',
});
```

3. **Parallel Requests:**

```typescript
// Independent datastreams can be fetched in parallel
const results = await Promise.all(
  datastreams.map((ds) => ds.getObservations({ limit: 1000 }))
);
```

4. **Async Iteration:**

```typescript
for await (const observation of datastream.observationStream({
  phenomenonTime: ['2024-01-01', '2024-12-31'],
})) {
  await processAndStore(observation);
  // Process one at a time, no memory overflow
}
```

**Requirements:**

- Chunking utilities
- Binary format support
- Parallel request management
- Async iterators

---

### 8.4 Real-Time Update Optimization

**Polling Strategies:**

1. **Fixed interval:**

```typescript
// Simple, predictable
setInterval(() => fetchLatest(), 5000);
```

2. **Exponential backoff (no new data):**

```typescript
let interval = 5000;
const poll = async () => {
  const obs = await fetchLatest();
  if (obs.length === 0) {
    interval = Math.min(interval * 1.5, 30000); // Max 30 seconds
  } else {
    interval = 5000; // Reset
  }
  setTimeout(poll, interval);
};
```

3. **Incremental fetch:**

```typescript
let lastResultTime = null;
const poll = async () => {
  const filter = lastResultTime
    ? { resultTime: `${lastResultTime}/..` }
    : { resultTime: 'latest' };

  const observations = await datastream.getObservations(filter);
  if (observations.length > 0) {
    lastResultTime = observations[observations.length - 1].resultTime;
    update(observations);
  }
  setTimeout(poll, 5000);
};
```

**Recommendations:**

- Dashboard monitoring: 5-10 seconds
- Real-time critical: 1-2 seconds
- Historical analysis: No polling

**Requirements:**

- Configurable poll interval
- Backoff strategies
- Incremental fetch support
- Memory-efficient updates

---

## 9. Library Design Implications

### 9.1 API Design Patterns

**Resource-Centric Design:**

```typescript
// Objects represent resources
const system = await client.getSystem(id);
const datastreams = await system.getDataStreams();
const observations = await datastreams[0].getObservations();
```

**Fluent API:**

```typescript
// Method chaining
const observations = await client
  .findSystems({ bbox })
  .then((systems) => systems[0].getDataStreams())
  .then((datastreams) => datastreams[0].getObservations());
```

**Builder Pattern:**

```typescript
// Query builder
const systems = await client
  .systems()
  .inBbox([-122.5, 37.5, -122.3, 37.7])
  .observing('temperature')
  .active()
  .limit(50)
  .execute();
```

---

### 9.2 Error Handling Philosophy

**Approach:** Exceptions for programmer errors, null/empty for missing data

```typescript
// Programmer error - throw exception
const system = await client.getSystem(null); // throws TypeError

// Missing data - return null or empty
const system = await client.getSystem('nonexistent'); // returns null

// Network error - throw specific exception
const system = await client.getSystem('sys1'); // throws NetworkError on timeout
```

**Error Hierarchy:**

```
CSAPIError (base)
├── NetworkError (timeout, connection failed)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── ValidationError (400)
├── ResourceNotFoundError (404)
├── ConflictError (409)
└── ServerError (5XX)
```

---

### 9.3 Promise vs Observable

**Promises for single requests:**

```typescript
const system = await client.getSystem(id);
```

**Observables for streams:**

```typescript
const subscription = datastream.observe().subscribe({
  next: (obs) => update(obs),
  error: (err) => handle(err),
});
```

**Hybrid approach:**

```typescript
// Return promise for single value
getLatestObservation(): Promise<Observation>

// Return observable for stream
streamObservations(): Observable<Observation>
```

---

### 9.4 Configuration Options

**Client Configuration:**

```typescript
const client = new CSAPIClient({
  baseUrl: 'https://api.example.org/csapi',
  auth: {
    type: 'bearer',
    token: '...',
  },
  timeout: 30000,
  retry: {
    retries: 3,
    backoff: 'exponential',
  },
  cache: {
    enabled: true,
    ttl: {
      conformance: 86400000,
      systems: 3600000,
      schemas: Infinity,
    },
  },
  pagination: {
    defaultLimit: 100,
    maxLimit: 1000,
  },
  formats: {
    prefer: 'application/geo+json',
    fallback: 'application/json',
  },
});
```

---

## Summary

### Priority Matrix

| Scenario              | Priority | Complexity | Frequency   |
| --------------------- | -------- | ---------- | ----------- |
| Discover systems      | P0       | Low        | High        |
| Real-time monitoring  | P0       | Medium     | Very High   |
| Historical data       | P0       | Medium     | Medium      |
| Send commands         | P0       | High       | Medium-High |
| Stream data           | P0       | High       | High        |
| Map integration       | P0       | Low        | High        |
| Dashboard building    | P0       | High       | Very High   |
| Deploy networks       | P1       | Medium     | Low-Medium  |
| Navigate hierarchies  | P1       | Medium     | Medium      |
| UAV/Satellite tasking | P1       | High       | Low-Medium  |
| Track history         | P2       | Low-Medium | Low         |
| Manage sampling       | P2       | Medium     | Low-Medium  |
| Feasibility checking  | P2       | Medium     | Low         |
| Monitor events        | P2       | Low        | Low-Medium  |
| Manage procedures     | P2       | Medium     | Low         |

### Convenience Method Priorities

**P0 (Must-have):**

1. findSystemsInArea
2. getLatestObservations
3. streamObservations
4. sendCommandAndWait
5. paginateAll

**P1 (Should-have):** 6. getObservationsInRange 7. getSystemHierarchy 8. checkCommandFeasibility 9. resolveLinks 10. checkServerCapabilities

**P2 (Nice-to-have):** 11. findDataStreams 12. getDeploymentData 13. buildBboxQuery 14. buildTimeRange 15. formatObservation 16. validateObservationSchema 17. waitForCommandCompletion

### Integration Requirements

**Essential:**

- GeoJSON format for mapping
- JSON format for charting
- Polling for real-time updates

**Advanced:**

- SWE Common binary for large datasets
- Observable pattern for reactive UIs
- Streaming for memory efficiency

### Performance Targets

- **Page sizes:** 100-1000 observations
- **Poll interval:** 5-10 seconds for dashboards
- **Cache TTL:** 24h conformance, 1h systems, ∞ schemas
- **Timeout:** 30 seconds default
- **Max retries:** 3-5 with exponential backoff

This usage scenario analysis provides comprehensive guidance for implementing a client library that supports real-world CSAPI applications with optimal developer experience and performance.
