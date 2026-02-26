# CSAPI Client Application Analysis: osh-viewer

**Document:** Section 10 - osh-viewer Usage Pattern Analysis  
**Repository:** https://github.com/Botts-Innovative-Research/osh-viewer  
**Type:** JavaScript Vue.js Web Application  
**Date:** 2026-01-31  
**Status:** Complete

---

## Executive Summary

This document analyzes the osh-viewer application, a Vue.js-based web client for OGC API – Connected Systems, to understand real-world CSAPI usage patterns. The analysis reveals practical implementation insights, common workflows, and convenience opportunities that inform client library design.

**Key Findings:**

- **Primary Operations:** Read-heavy (GET operations), minimal write usage
- **Navigation Pattern:** System → Datastreams → Observations hierarchy
- **Pagination:** Offset-based with default 10 items, 100 for bulk operations
- **Format Preference:** SWE+JSON for real-time, SWE+Binary for high-frequency data
- **Architecture:** Object-oriented wrappers with filter builders and collection classes
- **Real-time:** WebSocket streaming with format-specific parsers
- **Unused Features:** Write operations (POST/PUT/DELETE systems), advanced filters (select, validTime)

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [CSAPI Operations Used](#2-csapi-operations-used)
3. [Resource Query Patterns](#3-resource-query-patterns)
4. [Pagination Implementation](#4-pagination-implementation)
5. [Format Preferences](#5-format-preferences)
6. [Sub-Resource Navigation](#6-sub-resource-navigation)
7. [Error Handling](#7-error-handling)
8. [Convenience Opportunities](#8-convenience-opportunities)
9. [Unused CSAPI Features](#9-unused-csapi-features)
10. [Performance Patterns](#10-performance-patterns)
11. [Mapping Integration](#11-mapping-integration)
12. [Typical Workflows](#12-typical-workflows)
13. [UI/UX Insights](#13-uiux-insights)
14. [Data Transformation](#14-data-transformation)
15. [Code Architecture](#15-code-architecture)
16. [Library Design Implications](#16-library-design-implications)

---

## 1. Application Overview

**osh-viewer** is a Vue.js web application for visualizing sensor data from OGC API – Connected Systems servers. It provides:

- **System Discovery:** Browse and search sensor systems
- **Real-time Visualization:** Live charts and maps with streaming data
- **Command & Control:** Send commands to actuators and controllable systems
- **Data Replay:** Playback historical observations

**Tech Stack:**

- Vue 3 with Composition API
- Pinia for state management
- Custom osh-js library for CSAPI interaction
- WebSocket and MQTT for streaming

**Use Case:** Operations centers, sensor monitoring dashboards, IoT data visualization

---

## 2. CSAPI Operations Used

### 2.1 GET Operations (Primary)

**System Resources:**

```javascript
GET / systems; // List all systems
GET / systems / { sysid }; // Get system details
GET / systems / { sysid } / details; // SensorML description
GET / systems / { sysid } / datastreams; // List datastreams
GET / systems / { sysid } / controlstreams; // List control streams
GET / systems / { sysid } / samplingFeatures; // List sampling features
GET / systems / { sysid } / history; // Historical descriptions
GET / systems / { sysid } / events; // System events
```

**DataStream Resources:**

```javascript
GET / datastreams / { id } / observations; // Query observations
GET / datastreams / { id } / schema; // Get observation schema
```

**ControlStream Resources:**

```javascript
GET / systems / { sysid } / controlstreams / { dsid } / schema; // Get control schema
GET / systems / { sysid } / controlstreams / { dsid } / status; // Get control status
```

**Global Resources:**

```javascript
GET / observations; // Search all observations
GET / samplingFeatures; // Search sampling features
```

### 2.2 POST Operations

**Command Submission:**

```javascript
POST / systems / { sysid } / controlstreams / { dsid } / commands;
Body: {
  // Command parameters based on schema
}
```

### 2.3 WebSocket/Streaming

**Real-time Data:**

```javascript
// WebSocket connection for streaming observations
ws://{host}/datastreams/{id}/observations?phenomenonTime=now&...

// Alternative MQTT support
mqtt://{host}/...
```

### 2.4 Operations NOT Used

- `POST /systems` - Create systems
- `PUT /systems/{id}` - Update systems
- `DELETE /systems/{id}` - Delete systems
- `PATCH /systems/{id}` - Partial updates
- Similar write operations for other resources

**Insight:** Application is **read-focused with basic commanding**. No resource creation or management.

---

## 3. Resource Query Patterns

### 3.1 Query Filters Used

**SystemFilter:**

```javascript
class SystemFilter {
  constructor({
    q: undefined,              // Full-text search keywords
    bbox: undefined,           // Bounding box [minLon, minLat, maxLon, maxLat]
    location: undefined,       // WKT geometry (rarely used)
    parent: undefined,         // Parent resource IDs or "*"
    foi: undefined,           // Feature of interest filter
    select: undefined,        // Property selection (always undefined)
    format: 'application/json', // Response format
    validTime: undefined      // ISO 8601 time range (rarely used)
  }) {
    this.queryParams = { q, bbox, location, parent, foi, select, format, validTime };
  }

  toQueryString(paramsNotUsed = []) {
    // Build query string from non-undefined params
    return Object.entries(this.queryParams)
      .filter(([key, value]) => value !== undefined && !paramsNotUsed.includes(key))
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&');
  }
}
```

**DataStreamFilter:**

```javascript
class DataStreamFilter {
  constructor({
    q: undefined,
    bbox: undefined,
    location: undefined,
    observedProperty: undefined,  // Filter by observed properties
    foi: undefined,
    select: undefined,
    format: 'application/json',
    obsFormat: 'application/om+json', // Observation format preference
    validTime: undefined,
    phenomenonTime: undefined,    // Observation time range
    resultTime: undefined
  }) {
    this.queryParams = { /* ... */ };
  }
}
```

**ObservationFilter:**

```javascript
class ObservationFilter {
  constructor({
    phenomenonTime: 'now',        // 'now', 'latest', or ISO time range
    resultTime: 'now',
    featureOfInterest: undefined,
    select: undefined,
    bbox: undefined,
    location: undefined,
    format: 'application/om+json',
    replaySpeed: undefined        // For historical replay
  }) {
    this.queryParams = { /* ... */ };
  }
}
```

### 3.2 Common Query Examples

**Discover systems in area:**

```javascript
const filter = new SystemFilter({
  bbox: [-122.5, 37.5, -122.3, 37.7], // San Francisco
});
const systems = await node.searchSystems(filter, 100);
```

**Search by keyword:**

```javascript
const filter = new SystemFilter({
  q: 'drone', // Full-text search
});
```

**Get real-time observations:**

```javascript
const filter = new ObservationFilter({
  phenomenonTime: 'now',
  resultTime: 'now',
  format: 'application/swe+json',
});
const observations = await datastream.searchObservations(filter, 10);
```

**Filter by observed property:**

```javascript
const filter = new DataStreamFilter({
  observedProperty: 'http://qudt.org/vocab/quantitykind/Temperature',
});
const datastreams = await system.searchDataStreams(filter, 100);
```

### 3.3 Query Parameter Usage Analysis

**Frequently Used:**

- `bbox` - Spatial filtering for discovery
- `phenomenonTime` - Temporal filtering (often "now" or "latest")
- `format` / `obsFormat` - Format negotiation
- `observedProperty` - Property filtering

**Rarely/Never Used:**

- `select` - Property selection (always undefined)
- `validTime` - Historical system versions (undefined)
- `location` - WKT geometry (bbox preferred)
- `replaySpeed` - Only for replay mode

**Insight:** Simple query patterns dominate - bbox + datetime + property. Complex filters unused.

---

## 4. Pagination Implementation

### 4.1 Collection Class

**Pagination Logic:**

```javascript
class Collection {
  constructor(url, filter, pageSize, parser, responseFormat = 'json') {
    this.url = url;
    this.filter = filter;
    this.pageSize = pageSize; // Default: 10
    this.pageOffset = 0;
    this.currentPage = -1;
    this.parser = parser;
    this.responseFormat = responseFormat;
  }

  async nextPage() {
    if (this.currentPage === -1) {
      this.currentPage = 0;
      this.pageOffset = 0;
    } else {
      this.pageOffset += this.pageSize;
    }

    const offset = this.pageOffset;
    const queryString = `${this.filter.toQueryString()}&offset=${offset}&limit=${
      this.pageSize
    }`;
    const fullUrl = `${this.url}?${queryString}`;

    const response = await fetch(fullUrl);
    const data = await response[this.responseFormat]();

    // Check if we got fewer items than requested
    if (data.items.length < this.pageSize) {
      this.pageOffset = -1; // No more pages
    }

    return data.items.map((item) => this.parser(item));
  }

  hasNext() {
    return this.pageOffset !== -1;
  }
}
```

### 4.2 Usage Patterns

**Manual Pagination Loop:**

```javascript
const results = await system.searchDataStreams(undefined, 100);
const allDatastreams = [];

while (results.hasNext()) {
  const items = await results.nextPage();
  allDatastreams.push(...items);
}
```

**Single Page Fetch:**

```javascript
// Many operations only fetch first page
const systems = await node.searchSystems(filter, 100);
const firstPage = await systems.nextPage();
// No while loop - assumes all results fit in first page
```

### 4.3 Page Size Patterns

**Default:** 10 items (for UI lists)
**Bulk operations:** 100 items (for discovery/batch)
**No maximum limit observed**

### 4.4 Pagination Strategy

**Offset-based pagination:**

- Uses `offset` and `limit` query parameters
- Does NOT follow `next` links from responses
- Detects end of results by comparing returned count to page size

**Insight:** Simple offset pagination sufficient. No link-following needed (unlike spec recommendation).

---

## 5. Format Preferences

### 5.1 Format Hierarchy

**For Observations (priority order):**

```javascript
1. 'application/swe+json'      // Preferred for real-time JSON streaming
2. 'application/swe+binary'    // For video/high-frequency sensor data
3. 'application/om+json'       // Fallback default
4. 'application/swe+csv'       // Rarely used
5. 'application/swe+xml'       // Not implemented
```

**For Metadata:**

```javascript
-'application/json'; // Default for all resource descriptions
```

### 5.2 Format Selection Logic

**Check Available Formats:**

```javascript
// Inspect datastream.properties.formats array
let checkedFormat = datastream.properties.formats.filter(
  (format) =>
    format.includes('application/swe+json') ||
    format.includes('application/swe+binary')
);

if (!checkedFormat || checkedFormat.length === 0) {
  checkedFormat = ['application/om+json']; // Fallback
}

const filter = new DataStreamFilter({
  obsFormat: checkedFormat[0],
});
```

### 5.3 Format-Specific Handling

**SWE+JSON Streaming:**

```javascript
const datasource = new SweApi(name, {
  endpointUrl: baseUrl,
  resource: `/datastreams/${id}/observations`,
  mode: Mode.REAL_TIME,
  responseFormat: 'application/swe+json',
  startTime: 'now',
});
```

**SWE+Binary for Performance:**

```javascript
// Used for high-frequency data (video frames, point clouds)
const datasource = new SweApi(name, {
  responseFormat: 'application/swe+binary',
  bufferSize: 1000, // Larger buffer for binary
});
```

### 5.4 No Explicit Content Negotiation

**Insight:** Application does NOT use `Accept` headers for negotiation. Instead:

1. Inspects `datastream.properties.formats` array
2. Selects preferred format from available list
3. Passes format in query parameter (`obsFormat=application/swe+json`)

**Library Implication:** Provide helper to check available formats and select best match.

---

## 6. Sub-Resource Navigation

### 6.1 Navigation Pattern

**Object-Oriented Traversal:**

```javascript
// 1. Get system
const system = await node.getSystem(systemId);

// 2. Navigate to datastreams (system has navigation methods)
const datastreams = await system.searchDataStreams(undefined, 100);

// 3. Navigate to observations
for (let datastream of await datastreams.nextPage()) {
  const observations = await datastream.searchObservations(filter, 10);
}

// 4. Navigate to control streams
const controlstreams = await system.searchControls(undefined, 100);

// 5. Navigate to sampling features
const samplingFeatures = await system.searchFeaturesOfInterest(undefined, 100);
```

### 6.2 System Class Navigation Methods

**System Resource Wrapper:**

```javascript
class System extends SensorWebApi {
  // Convenience navigation methods
  async searchDataStreams(filter, pageSize = 10) {
    const url =
      this.baseUrl() +
      API.systems.datastreams.replace('{sysid}', this.properties.id);
    return new Collection(
      url,
      filter || new DataStreamFilter(),
      pageSize,
      this.parser
    );
  }

  async searchControls(filter, pageSize = 10) {
    const url =
      this.baseUrl() +
      API.systems.controlstreams.replace('{sysid}', this.properties.id);
    return new Collection(
      url,
      filter || new ControlStreamFilter(),
      pageSize,
      this.parser
    );
  }

  async searchFeaturesOfInterest(filter, pageSize = 10) {
    const url =
      this.baseUrl() +
      API.systems.featuresOfInterest.replace('{sysid}', this.properties.id);
    return new Collection(
      url,
      filter || new SystemFilter(),
      pageSize,
      this.parser
    );
  }

  async getDetails(filter) {
    const url =
      this.baseUrl() +
      API.systems.details.replace('{sysid}', this.properties.id);
    return fetch(url).then((r) => r.json());
  }
}
```

### 6.3 DataStream Class Navigation

**DataStream to Observations:**

```javascript
class DataStream extends SensorWebApi {
  async searchObservations(filter, pageSize = 10) {
    const url =
      this.baseUrl() +
      API.datastreams.observations.replace('{id}', this.properties.id);
    return new Collection(
      url,
      filter || new ObservationFilter(),
      pageSize,
      this.parser
    );
  }

  async getSchema(filter) {
    const url =
      this.baseUrl() +
      API.datastreams.schema.replace('{id}', this.properties.id);
    if (filter) {
      url += `?${filter.toQueryString()}`;
    }
    return fetch(url).then((r) => r.json());
  }
}
```

### 6.4 Benefits of Object Pattern

**Encapsulation:**

- Resource IDs embedded in objects
- URL construction handled internally
- Correct endpoint paths automatic

**Type Safety:**

- Each resource type has specific navigation methods
- Can't accidentally navigate to wrong resource type

**Convenience:**

- `system.searchDataStreams()` vs manual URL construction
- Consistent API across all resource types

**Insight:** Object-oriented navigation significantly reduces boilerplate vs raw URL construction.

---

## 7. Error Handling

### 7.1 HTTP Error Detection

**Basic Error Checking:**

```javascript
async doGETRequest(url) {
  return fetch(url).then((response) => {
    if (!response.ok) {
      const err = new Error(`Got ${response.status} response from ${url}`);
      err.response = response;
      throw err;
    }
    return response.json();
  });
}
```

### 7.2 Try-Catch Pattern

**Graceful Degradation:**

```javascript
async fetchSchema(datastream) {
  try {
    let checkedFormat = datastream.properties.formats.filter(
      (format) => format.includes('application/swe+json') ||
                  format.includes('application/swe+binary')
    );

    if (!checkedFormat || checkedFormat.length === 0) {
      checkedFormat = ['application/om+json']; // Fallback
    }

    const filter = new DataStreamFilter({ obsFormat: checkedFormat[0] });
    const schema = await datastream.getSchema(filter);

    console.log('Schema fetched:', schema);
    return schema;
  } catch (error) {
    console.error('Error fetching schema:', error);
    return null;  // Return null on failure
  }
}
```

### 7.3 Status Cancellation

**Long-Running Operations:**

```javascript
async nextBatch(properties, masterTimestamp, status = { cancel: false }) {
  if (status.cancel) {
    reject('Status has been cancelled');
    return;
  }

  // Continue processing...
}
```

### 7.4 WebSocket Error Handling

**Connection Errors:**

```javascript
this.ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // No reconnection logic observed
};

this.ws.onclose = () => {
  console.log('WebSocket closed');
  // Manual reconnection required
};
```

### 7.5 Error Handling Gaps

**Missing:**

- No retry logic for transient failures
- No exponential backoff
- No automatic reconnection for WebSocket
- No timeout handling
- Limited error type differentiation (401 vs 403 vs 500)

**Insight:** Basic error handling only. Library should provide retry, reconnection, and timeout patterns.

---

## 8. Convenience Opportunities

### 8.1 Repeated Boilerplate Patterns

**Pattern 1: Filter Construction**

```javascript
// Repeated everywhere
const filter = new SystemFilter({ q: 'keyword', bbox: [...] });
const queryString = filter.toQueryString(['select', 'format']);
```

**Convenience Opportunity:**

```javascript
// Suggested: Fluent builder
const systems = await client
  .systems()
  .search('keyword')
  .inBbox([-122.5, 37.5, -122.3, 37.7])
  .execute();
```

---

**Pattern 2: Pagination Loops**

```javascript
// Repeated pattern
const results = await system.searchDataStreams(undefined, 100);
const allItems = [];
while (results.hasNext()) {
  const items = await results.nextPage();
  allItems.push(...items);
}
```

**Convenience Opportunity:**

```javascript
// Suggested: Auto-paginate method
const allItems = await system.getAllDataStreams();

// Or async iterator
for await (const datastream of system.datastreams()) {
  process(datastream);
}
```

---

**Pattern 3: Format Selection**

```javascript
// Repeated pattern
let checkedFormat = datastream.properties.formats.filter(
  (format) =>
    format.includes('application/swe+json') ||
    format.includes('application/swe+binary')
);

if (!checkedFormat) {
  checkedFormat = ['application/om+json'];
}

const filter = new DataStreamFilter({ obsFormat: checkedFormat[0] });
await datastream.getSchema(filter);
```

**Convenience Opportunity:**

```javascript
// Suggested: Auto-format selection
const schema = await datastream.getSchema({
  preferFormats: ['application/swe+json', 'application/swe+binary'],
});
```

---

**Pattern 4: WebSocket URL Construction**

```javascript
// Manual URL building
const resource = `/datastreams/${datastreamId}/observations`;
const protocol = tls ? 'wss' : 'ws';
const fullUrl = `${protocol}://${endpointUrl}${resource}?${queryString}`;
const ws = new WebSocket(fullUrl);
```

**Convenience Opportunity:**

```javascript
// Suggested: Stream method
const stream = await datastream.stream({
  phenomenonTime: 'now',
  onData: (obs) => updateChart(obs),
  onError: (err) => handleError(err),
});
```

---

**Pattern 5: Schema Fetching + Parsing**

```javascript
// Always need schema before parsing observations
const schema = await datastream.getSchema(filter);
const parser = new SweJsonParser(schema);
const observations = await datastream.searchObservations(filter, 100);
for (let obs of observations) {
  const parsed = parser.parse(obs);
}
```

**Convenience Opportunity:**

```javascript
// Suggested: Auto-parse with cached schema
const observations = await datastream.getObservations({
  phenomenonTime: ['2024-01-01', '2024-02-01'],
  autoParse: true, // Automatically fetches schema and parses
});
```

---

### 8.2 Suggested Convenience Methods

**High-Level:**

1. `system.getAllDataStreams()` - Auto-paginate all datastreams
2. `datastream.getAllObservations(filter)` - Auto-paginate observations
3. `datastream.stream(options)` - Auto-configure WebSocket streaming
4. `datastream.getLatest()` - Get most recent observation
5. `system.getHierarchy()` - Fetch full system tree

**Helpers:** 6. `client.findSystems(query)` - Fluent query builder 7. `datastream.selectBestFormat(preferences)` - Format negotiation 8. `resource.resolveLinks(rels)` - Fetch related resources 9. `builder.inArea(bbox)` - Spatial query helper 10. `builder.during(start, end)` - Temporal query helper

**Utilities:** 11. `parser.parseObservation(obs, schema)` - Format-aware parsing 12. `client.validateFilter(filter)` - Client-side validation 13. `resource.export(format)` - Format conversion 14. `stream.reconnect()` - Auto-reconnection for WebSocket

---

## 9. Unused CSAPI Features

### 9.1 Write Operations (Completely Unused)

**System Management:**

- `POST /systems` - Create new systems
- `PUT /systems/{id}` - Update entire system
- `PATCH /systems/{id}` - Partial system update
- `DELETE /systems/{id}` - Delete system

**DataStream Management:**

- `POST /datastreams` - Create datastream
- `PUT /datastreams/{id}` - Update datastream
- `DELETE /datastreams/{id}` - Delete datastream

**Observation Management:**

- `POST /datastreams/{id}/observations` - Insert observations
- `DELETE /observations/{id}` - Delete observation

### 9.2 Advanced Query Features (Rarely/Never Used)

**Property Selection:**

- `select` parameter - Always undefined in filters
- Used for reducing response size, but not needed in practice

**Historical Queries:**

- `validTime` parameter - Rarely used
- Could query historical system configurations, but application doesn't need this

**WKT Geometry:**

- `location` parameter - Always undefined
- `bbox` preferred for spatial queries

**Subsets:**

- `phenomenonTime` often just "now" or "latest"
- Rarely uses specific time ranges for queries (except replay mode)

### 9.3 Part 2 Features (Minimal Usage)

**System Hierarchy:**

- `GET /systems/{sysid}/members` - Route exists but unused
- No subsystem navigation observed

**Advanced Control:**

- Command status tracking minimal
- No command update/cancellation
- No feasibility checking

**Deployment Resources:**

- Not used at all
- No deployment creation or management

**Procedure Resources:**

- Not used at all
- System details fetched via `/systems/{id}/details` instead

### 9.4 MVP Prioritization Insights

**Essential (P0):**

- GET operations for systems, datastreams, observations
- Basic filters: bbox, datetime, observedProperty
- Pagination (offset-based sufficient)
- WebSocket streaming
- Basic command POST

**Nice-to-have (P1):**

- Advanced filters: select, validTime
- Control status monitoring
- System hierarchy navigation

**Can Defer (P2):**

- Write operations (POST/PUT/DELETE resources)
- Deployment management
- Procedure management
- Command update/cancellation
- Feasibility checking

**Insight:** Focus initial library on read operations + basic commanding. Write operations can be phased later.

---

## 10. Performance Patterns

### 10.1 Schema Caching

**Per-Format Caching:**

```javascript
class DataStream {
  constructor() {
    this.parsers = {
      'application/om+json': {
        schemaPromise: undefined, // Cached promise to avoid duplicate fetches
        parser: undefined, // Cached parser instance
      },
      'application/swe+json': {
        schemaPromise: undefined,
        parser: undefined,
      },
      'application/swe+binary': {
        schemaPromise: undefined,
        parser: undefined,
      },
    };
  }

  async getParser(format) {
    if (!this.parsers[format]) {
      this.parsers[format] = {};
    }

    if (!this.parsers[format].schemaPromise) {
      this.parsers[format].schemaPromise = this.getSchema(
        new DataStreamFilter({ obsFormat: format })
      );
    }

    const schema = await this.parsers[format].schemaPromise;

    if (!this.parsers[format].parser) {
      this.parsers[format].parser = new Parser(format, schema);
    }

    return this.parsers[format].parser;
  }
}
```

**Benefit:** Schemas fetched once per format, then reused for all observations.

### 10.2 No Request Batching

**Individual Fetches:**

```javascript
// Each resource fetched separately
for (let system of systems) {
  const datastreams = await system.searchDataStreams(); // Separate request
  const controlstreams = await system.searchControls(); // Separate request
  const samplingFeatures = await system.searchFeaturesOfInterest(); // Separate request
}
```

**No Observed Batching:**

- No batch GET requests for multiple systems
- No parallel fetching optimizations
- Sequential resource loading

**Opportunity:** Library could provide batch fetching or parallel request helpers.

### 10.3 Real-Time Streaming Performance

**WebSocket Streaming:**

```javascript
const datasource = new SweApi(name, {
  endpointUrl: baseUrl,
  resource: `/datastreams/${id}/observations`,
  mode: Mode.REAL_TIME,
  responseFormat: 'application/swe+binary', // More efficient than JSON
  startTime: 'now',
  bufferSize: 1000, // Larger buffer for high-frequency data
});

datasource.connect();
datasource.stream().onMessage = async (message) => {
  const dataBlock = await parser.parseDataBlock(message, format);
  callback(dataBlock);
};
```

**Binary Format Advantage:**

- 10-100x smaller than JSON for sensor data
- Faster parsing for high-frequency streams (video, point clouds)

### 10.4 Replay Mode for Historical Data

**Time-Based Replay:**

```javascript
const datasource = new SweApi(name, {
  mode: Mode.REPLAY,
  startTime: '2024-01-01T00:00:00Z',
  endTime: '2024-01-02T00:00:00Z',
  replaySpeed: 2.0, // 2x speed playback
});
```

**Optimization:**

- Fetches historical data in chunks
- Plays back at specified speed
- Reduces server load vs real-time polling

### 10.5 State Management (Pinia Stores)

**Centralized Caching:**

```javascript
// systemStore.js
const systemStore = defineStore('systems', {
  state: () => ({
    systems: new Map(), // All systems cached
    datastreams: new Map(), // All datastreams cached
    controlstreams: new Map(), // All control streams cached
  }),

  actions: {
    addSystem(system) {
      this.systems.set(system.id, system);
    },
  },
});
```

**Benefit:**

- Single source of truth
- Avoids duplicate fetches
- Reactive updates across components

### 10.6 Performance Gaps

**Missing Optimizations:**

- No request deduplication
- No connection pooling for WebSockets
- No lazy loading (fetches all on init)
- No incremental loading for large datasets
- No background prefetching

**Insight:** Library should provide request deduplication, connection pooling, and lazy loading helpers.

---

## 11. Mapping Integration

### 11.1 Spatial Data Extraction

**Sampling Feature Geometries:**

```javascript
async function loadSamplingFeatures(system) {
  const samplingFeatures = await system.searchFeaturesOfInterest(
    undefined,
    100
  );

  for (let foi of await samplingFeatures.nextPage()) {
    const geometry = new Geometry(
      foi.properties.id,
      foi.properties.geometry.type, // 'Point', 'LineString', etc.
      foi.properties.geometry.coordinates, // [lon, lat]
      foi.properties,
      foi.properties.bbox // Bounding box if available
    );

    // Add to map layer
    addMarkerToMap(geometry);
  }
}
```

### 11.2 System Location Display

**Extract Location from System:**

```javascript
// Assuming system has position property
const position = system.properties.position;
if (position && position.coordinates) {
  addSystemMarker({
    id: system.id,
    name: system.name,
    coordinates: position.coordinates,
    properties: system.properties,
  });
}
```

### 11.3 Bounding Box Queries

**Viewport-Based Discovery:**

```javascript
function onMapMoveEnd(map) {
  const bounds = map.getBounds();
  const bbox = [
    bounds.getWest(),
    bounds.getSouth(),
    bounds.getEast(),
    bounds.getNorth()
  ];

  const filter = new SystemFilter({ bbox });
  const systems = await node.searchSystems(filter, 100);

  updateMapMarkers(systems);
}
```

### 11.4 Feature Binding

**Attach Metadata to Map Features:**

```javascript
const marker = L.marker([lat, lon]);

marker.bindPopup(`
  <h3>${system.name}</h3>
  <p>Type: ${system.systemKind}</p>
  <button onclick="showDataStreams('${system.id}')">View Data</button>
`);

marker.on('click', async () => {
  const datastreams = await system.searchDataStreams();
  displayDataStreamList(datastreams);
});
```

### 11.5 No Complex Spatial Operations

**Simple Point Geometries:**

- Mostly point markers for sensor locations
- No polygon/line rendering observed
- No spatial analysis (intersection, buffering, etc.)
- Basic bbox filtering only

**Insight:** Library should focus on GeoJSON output and simple spatial queries. Complex spatial operations not needed for MVP.

---

## 12. Typical Workflows

### 12.1 Workflow 1: Application Initialization

```javascript
// Step 1: Create CSAPI node connection
const connect = new OSHConnect();
const node = connect.createNode(
  'MyServer', // Name
  'api.example.org', // Host
  443, // Port
  '/csapi', // Endpoint path
  { type: 'bearer', token: '...' } // Auth
);

// Step 2: Discover all systems
await node.collectAndStoreSystems();
// Internally: systems.searchSystems(new SystemFilter(), 100)

// Step 3: For each system, fetch sub-resources
for (let system of systemStore.systems.values()) {
  // Fetch datastreams
  const datastreams = await system.searchDataStreams(undefined, 100);
  while (datastreams.hasNext()) {
    const items = await datastreams.nextPage();
    for (let ds of items) {
      datastreamStore.addDataStream(ds);
    }
  }

  // Fetch control streams
  const controlstreams = await system.searchControls(undefined, 100);
  while (controlstreams.hasNext()) {
    const items = await controlstreams.nextPage();
    for (let cs of items) {
      controlstreamStore.addControlStream(cs);
    }
  }

  // Fetch sampling features
  const samplingFeatures = await system.searchFeaturesOfInterest(
    undefined,
    100
  );
  while (samplingFeatures.hasNext()) {
    const items = await samplingFeatures.nextPage();
    // Add to map
  }
}

// Step 4: Populate UI tree view
// Systems stored in Pinia store, rendered in Vue component
```

**Duration:** Seconds to minutes depending on number of systems

---

### 12.2 Workflow 2: Real-Time Visualization Setup

```javascript
// Step 1: User selects datastream from tree view
const selectedDatastream = datastreamStore.getById(datastreamId);

// Step 2: Fetch schema to determine available formats
const schema = await fetchSchema(selectedDatastream);
// Checks for 'application/swe+json' or 'application/swe+binary'

// Step 3: Create data source with streaming
const datasource = new SweApi('Sensor1', {
  endpointUrl: node.baseUrl,
  resource: `/datastreams/${datastreamId}/observations`,
  mode: Mode.REAL_TIME,
  responseFormat: 'application/swe+json',
  startTime: 'now',
  streamProtocol: 'ws', // WebSocket
});

// Step 4: Create visualization layer (chart, gauge, map)
const layer = new CurveLayer({
  dataSourceId: datasource.id,
  getValues: (rec, timestamp) => ({
    x: timestamp,
    y: rec.temperature, // Based on schema
  }),
  name: 'Temperature Chart',
});

// Step 5: Connect and start streaming
await datasource.connect();
datasource.stream().onMessage = (message) => {
  const dataBlock = parseObservation(message);
  layer.update(dataBlock);
};

// Step 6: UI updates reactively as data arrives
```

---

### 12.3 Workflow 3: Historical Data Replay

```javascript
// Step 1: User selects time range and datastream
const startTime = '2024-01-01T00:00:00Z';
const endTime = '2024-01-02T00:00:00Z';
const replaySpeed = 1.0;

// Step 2: Create replay datasource
const datasource = new SweApi('Replay', {
  endpointUrl: node.baseUrl,
  resource: `/datastreams/${datastreamId}/observations`,
  mode: Mode.REPLAY,
  responseFormat: 'application/swe+json',
  startTime: startTime,
  endTime: endTime,
  replaySpeed: replaySpeed,
});

// Step 3: Connect and stream historical data
await datasource.connect();

// Step 4: Data played back at specified speed
// Visualization updates as if real-time
```

---

### 12.4 Workflow 4: Command & Control

```javascript
// Step 1: User selects control stream from tree
const controlstream = controlstreamStore.getById(controlstreamId);

// Step 2: Fetch control schema to build command form
const schema = await fetchControlStreamSchema(controlstream);
// Schema defines command parameters and their types

// Step 3: User fills in command parameters via UI form
const command = {
  pan: 45,
  tilt: 0,
  zoom: 1.5,
};

// Step 4: Send command
const response = await sendCommand(
  node.baseUrl,
  controlstream.systemId,
  controlstream.id,
  command
);

// Step 5: Monitor command status (basic polling)
const statusUrl = `/systems/${systemId}/controlstreams/${controlstreamId}/status`;
const status = await fetch(statusUrl).then((r) => r.json());
console.log('Command status:', status);
```

---

### 12.5 Workflow 5: Spatial Discovery

```javascript
// Step 1: User navigates map to area of interest
const mapBounds = map.getBounds();
const bbox = [
  mapBounds.getWest(),
  mapBounds.getSouth(),
  mapBounds.getEast(),
  mapBounds.getNorth(),
];

// Step 2: Query systems in viewport
const filter = new SystemFilter({ bbox });
const systems = await node.searchSystems(filter, 50);
const systemsInView = await systems.nextPage();

// Step 3: Add markers to map
for (let system of systemsInView) {
  addSystemMarker(system);
}

// Step 4: User clicks marker
// Trigger workflow 2 (visualization setup)
```

---

## 13. UI/UX Insights

### 13.1 Tree View Drives Data Fetching

**Hierarchical Display:**

```vue
<template>
  <v-treeview
    :items="treeItems"
    :item-children="getItemChildren"
    @update:active="onItemSelected"
  />
</template>

<script>
const getItemChildren = computed(() => {
  return (item) => {
    // Lazy load children when expanded
    if (item.type === 'system') {
      return item.getDSChildren ? item.getDSChildren() : [];
    }
    return [];
  };
});
</script>
```

**Lazy Loading Pattern:**

- Systems loaded on init
- Datastreams loaded when system expanded
- Observations not loaded until visualization created

**Insight:** Library should support lazy loading patterns with async child resolution.

---

### 13.2 User Interaction Patterns

**Pattern 1: Browse → Select → Visualize**

```
1. User browses tree of systems
2. User selects datastream
3. Application fetches schema
4. User adds visualization (chart/map/gauge)
5. Real-time streaming starts
```

**Pattern 2: Search → Filter → Discover**

```
1. User enters search keywords
2. Application queries systems with q parameter
3. Results displayed in list
4. User clicks result → navigate to workflow 1
```

**Pattern 3: Map → Discover → Monitor**

```
1. User navigates map
2. Application queries systems in bbox
3. Markers displayed on map
4. User clicks marker → show datastreams
5. User selects datastream → visualize
```

---

### 13.3 Real-Time Updates Drive Design

**Reactive Data Flow:**

```javascript
// Pinia store with reactive state
const datastreamStore = defineStore('datastreams', {
  state: () => ({
    activeStreams: new Map(), // Currently streaming datastreams
    latestObservations: new Map(), // Latest observation per datastream
  }),
});

// Component watches for changes
watch(
  () => datastreamStore.latestObservations.get(datastreamId),
  (newObs) => {
    updateChart(newObs);
  }
);
```

**Insight:** Library should integrate with reactive frameworks (Vue, React) and provide observable patterns.

---

### 13.4 Visualization Diversity

**Supported Visualization Types:**

- Line charts (time series)
- Gauges (current values)
- Video players (binary streams)
- 3D viewers (point clouds)
- Map markers (locations)

**Data Requirements:**

- Must parse observations based on schema
- Must extract specific properties (temperature, position, etc.)
- Must handle different result types (scalar, vector, record)

**Insight:** Library should provide schema-aware observation parsing with property extraction helpers.

---

### 13.5 Control UI Generation

**Schema-Driven Forms:**

```javascript
// Fetch control schema
const schema = await controlstream.getSchema();

// Generate form fields based on schema
for (let param of schema.parameters) {
  createFormField({
    name: param.name,
    type: param.type, // 'number', 'string', 'boolean'
    min: param.constraint?.min,
    max: param.constraint?.max,
    required: param.required,
  });
}
```

**Insight:** Library should parse schemas into form-friendly structures.

---

## 14. Data Transformation

### 14.1 Format Parsers

**Parser Strategy Pattern:**

```javascript
class ParserFactory {
  static createParser(format, schema) {
    switch (format) {
      case 'application/swe+json':
        return new SweJsonParser(schema);
      case 'application/swe+binary':
        return new SweBinaryParser(schema);
      case 'application/om+json':
        return new OmJsonParser(schema);
      case 'application/swe+csv':
        return new SweCsvParser(schema);
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }
}
```

### 14.2 SWE Binary Parsing

**Binary Decoder:**

```javascript
class SweBinaryParser {
  constructor(schema) {
    this.encoding = schema.encoding; // Binary encoding definition
    this.fields = schema.resultSchema.fields;
  }

  parseDataBlock(arrayBuffer) {
    const dataView = new DataView(arrayBuffer);
    let offset = 0;
    const records = [];

    while (offset < arrayBuffer.byteLength) {
      const record = {};

      for (let field of this.fields) {
        switch (field.type) {
          case 'Time':
            record[field.name] = dataView.getFloat64(offset);
            offset += 8;
            break;
          case 'Quantity':
            record[field.name] = dataView.getFloat32(offset);
            offset += 4;
            break;
          case 'Count':
            record[field.name] = dataView.getInt32(offset);
            offset += 4;
            break;
        }
      }

      records.push(record);
    }

    return records;
  }
}
```

### 14.3 SWE JSON Parsing

**JSON Decoder:**

```javascript
class SweJsonParser {
  constructor(schema) {
    this.fields = schema.resultSchema.fields;
  }

  parseDataBlock(jsonString) {
    const data = JSON.parse(jsonString);

    // SWE JSON structure
    return {
      phenomenonTime: data.phenomenonTime,
      resultTime: data.resultTime,
      result: this.parseResult(data.result),
    };
  }

  parseResult(result) {
    // Result structure based on schema
    // Can be scalar, vector, or record
    if (Array.isArray(result)) {
      // Vector
      return this.fields.map((field, i) => ({
        [field.name]: result[i],
      }));
    } else if (typeof result === 'object') {
      // Record
      return result;
    } else {
      // Scalar
      return { [this.fields[0].name]: result };
    }
  }
}
```

### 14.4 Observation-to-Chart Transformation

**Extract Values for Visualization:**

```javascript
function getValues(record, timestamp) {
  // Called for each observation
  // Returns values for chart display
  return {
    x: timestamp, // Phenomenon time
    y: record.temperature, // Specific property based on schema
    label: record.sensorName, // Optional label
  };
}

// Usage in chart layer
const layer = new CurveLayer({
  dataSourceId: datasource.id,
  getValues: getValues,
  style: {
    stroke: 'blue',
    strokeWidth: 2,
  },
});
```

### 14.5 Coordinate Transformations

**Map Projection:**

```javascript
// Extract coordinates from samplingFeature
const coords = foi.properties.geometry.coordinates; // [lon, lat]

// Transform for map display (if needed)
const projected = transformCoordinates(
  coords,
  'EPSG:4326', // WGS84 (from API)
  'EPSG:3857' // Web Mercator (for map)
);
```

### 14.6 Time Parsing

**ISO 8601 to Timestamps:**

```javascript
function parseTime(isoString) {
  // Handle special values
  if (isoString === 'now' || isoString === 'latest') {
    return Date.now();
  }

  // Parse ISO timestamp
  return new Date(isoString).getTime();
}

// Time range parsing
function parseTimeRange(range) {
  const [start, end] = range.split('/');
  return {
    start: start === '..' ? null : parseTime(start),
    end: end === '..' ? null : parseTime(end),
  };
}
```

---

## 15. Code Architecture

### 15.1 Module Structure

```
lib/osh-js/
├── source/core/
│   ├── sweapi/                      # CSAPI client modules
│   │   ├── SensorWebApi.js          # Base class for all resources
│   │   ├── collection/
│   │   │   └── Collection.js        # Pagination handler
│   │   ├── system/
│   │   │   ├── Systems.js           # Collection operations
│   │   │   ├── System.js            # Individual system resource
│   │   │   └── SystemFilter.js      # Query filter builder
│   │   ├── datastream/
│   │   │   ├── DataStreams.js
│   │   │   ├── DataStream.js
│   │   │   └── DataStreamFilter.js
│   │   ├── observation/
│   │   │   ├── Observations.js
│   │   │   ├── Observation.js
│   │   │   └── ObservationFilter.js
│   │   └── control/
│   │       ├── ControlStreams.js
│   │       ├── ControlStream.js
│   │       └── ControlStreamFilter.js
│   ├── parsers/sweapi/              # Format parsers
│   │   ├── observations/
│   │   │   ├── OmJsonParser.js
│   │   │   ├── SweJsonParser.js
│   │   │   ├── SweBinaryParser.js
│   │   │   └── SweCsvParser.js
│   │   └── collection/
│   │       └── CollectionParser.js
│   └── datasource/sweapi/           # Streaming
│       ├── SweApi.js                # WebSocket datasource
│       └── context/
│           └── SweApiContext.js
└── src/lib/                         # Application-level wrappers
    ├── OSHConnectDataStructs.ts     # High-level API
    ├── DatasourceUtils.ts           # Datasource helpers
    └── ControlstreamUtils.ts        # Command helpers
```

### 15.2 Class Hierarchy

**Base Class:**

```javascript
class SensorWebApi {
  constructor(url, properties, parser) {
    this.url = url;
    this.properties = properties; // Resource metadata
    this.parser = parser;
  }

  baseUrl() {
    return this.url;
  }

  async doGETRequest(url) {
    return fetch(url).then((r) => r.json());
  }
}
```

**Resource Classes:**

```javascript
class System extends SensorWebApi {
  async searchDataStreams(filter, pageSize) {
    /* ... */
  }
  async searchControls(filter, pageSize) {
    /* ... */
  }
  async searchFeaturesOfInterest(filter, pageSize) {
    /* ... */
  }
  async getDetails(filter) {
    /* ... */
  }
}

class DataStream extends SensorWebApi {
  async searchObservations(filter, pageSize) {
    /* ... */
  }
  async getSchema(filter) {
    /* ... */
  }
  async getParser(format) {
    /* ... */
  }
}

class ControlStream extends SensorWebApi {
  async getSchema(filter) {
    /* ... */
  }
  async sendCommand(command) {
    /* ... */
  }
  async getStatus() {
    /* ... */
  }
}
```

### 15.3 Filter Builder Pattern

**Filter Classes:**

```javascript
class SystemFilter {
  constructor(params = {}) {
    this.queryParams = {
      q: params.q,
      bbox: params.bbox,
      location: params.location,
      parent: params.parent,
      foi: params.foi,
      select: params.select,
      format: params.format || 'application/json',
      validTime: params.validTime,
    };
  }

  toQueryString(paramsNotUsed = []) {
    return Object.entries(this.queryParams)
      .filter(
        ([key, value]) => value !== undefined && !paramsNotUsed.includes(key)
      )
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&');
  }
}
```

### 15.4 Collection Pattern

**Pagination Handler:**

```javascript
class Collection {
  constructor(url, filter, pageSize, parser, responseFormat = 'json') {
    this.url = url;
    this.filter = filter;
    this.pageSize = pageSize;
    this.pageOffset = 0;
    this.currentPage = -1;
    this.parser = parser;
    this.responseFormat = responseFormat;
  }

  async nextPage() {
    // Pagination logic (offset-based)
  }

  hasNext() {
    return this.pageOffset !== -1;
  }
}
```

### 15.5 Parser Strategy Pattern

**Format-Specific Parsers:**

```javascript
class ParserRegistry {
  constructor() {
    this.parsers = new Map();
  }

  register(format, parserClass) {
    this.parsers.set(format, parserClass);
  }

  getParser(format, schema) {
    const ParserClass = this.parsers.get(format);
    if (!ParserClass) {
      throw new Error(`No parser for format: ${format}`);
    }
    return new ParserClass(schema);
  }
}
```

### 15.6 Application Wrapper

**High-Level API:**

```javascript
class OSHConnect {
  constructor() {
    this.nodes = new Map(); // Multiple server connections
  }

  createNode(name, host, port, endpoint, auth) {
    const baseUrl = `https://${host}:${port}${endpoint}`;
    const node = {
      name,
      baseUrl,
      auth,
      systems: new Systems(baseUrl, auth),
      searchSystems: async (filter, pageSize) => {
        return this.systems.search(filter, pageSize);
      },
      collectAndStoreSystems: async () => {
        // Fetch all systems and sub-resources
        const systems = await this.searchSystems(undefined, 100);
        while (systems.hasNext()) {
          const items = await systems.nextPage();
          for (let system of items) {
            systemStore.addSystem(system);
            // Fetch datastreams, controlstreams, etc.
          }
        }
      },
    };

    this.nodes.set(name, node);
    return node;
  }
}
```

---

## 16. Library Design Implications

### 16.1 Essential Features (P0)

**Based on osh-viewer usage:**

1. **Object-Oriented Resource API:**

   - Resource classes with navigation methods
   - `system.getDataStreams()` vs manual URL construction
   - Reduces boilerplate significantly

2. **Pagination Abstraction:**

   - `Collection` class with `hasNext()` and `nextPage()`
   - Auto-paginate methods: `getAllDataStreams()`
   - Async iterators: `for await (const ds of system.datastreams())`

3. **Filter Builders:**

   - `SystemFilter`, `DataStreamFilter`, `ObservationFilter`
   - Fluent API option: `systems().inBbox(...).observing(...)`
   - Type-safe parameter construction

4. **Format Negotiation:**

   - Helper to check available formats
   - Auto-select best format from preferences
   - Format-specific parsers

5. **WebSocket Streaming:**

   - `datastream.stream(options)` convenience method
   - Auto-reconnection on failure
   - Observable pattern for reactive updates

6. **Schema Caching:**
   - Cache schemas per format
   - Avoid duplicate fetches
   - Parser instance reuse

---

### 16.2 Developer Experience Improvements

**Reduce Boilerplate:**

**Before (osh-viewer pattern):**

```javascript
const filter = new SystemFilter({ bbox: [...], q: 'drone' });
const results = await system.searchDataStreams(filter, 100);
const allDatastreams = [];
while (results.hasNext()) {
  const items = await results.nextPage();
  allDatastreams.push(...items);
}
```

**After (with convenience methods):**

```javascript
const datastreams = await system.getAllDataStreams({
  bbox: [...],
  q: 'drone'
});
```

**Format Selection Before:**

```javascript
let checkedFormat = datastream.properties.formats.filter(
  (format) =>
    format.includes('application/swe+json') ||
    format.includes('application/swe+binary')
);
if (!checkedFormat) {
  checkedFormat = ['application/om+json'];
}
const filter = new DataStreamFilter({ obsFormat: checkedFormat[0] });
const schema = await datastream.getSchema(filter);
```

**Format Selection After:**

```javascript
const schema = await datastream.getSchema({
  preferFormats: ['application/swe+json', 'application/swe+binary'],
});
```

---

### 16.3 MVP Scope Recommendations

**Phase 1 (Essential - P0):**

- GET operations: systems, datastreams, observations, controlstreams
- Basic filters: bbox, datetime, observedProperty, q
- Offset-based pagination
- WebSocket streaming
- POST commands
- Format negotiation
- Schema parsing

**Phase 2 (Important - P1):**

- Advanced filters: select, validTime, parent
- System hierarchy navigation
- Control status monitoring
- Sampling features
- Events
- Link following pagination
- Batch operations

**Phase 3 (Nice-to-have - P2):**

- Write operations: POST/PUT/DELETE resources
- Deployment management
- Procedure management
- Command update/cancellation
- Feasibility checking
- Advanced control features

---

### 16.4 Architecture Recommendations

**Pattern:** Object-Oriented with Functional Helpers

```typescript
// Object-oriented core
class CSAPIClient {
  async getSystem(id): Promise<System>;
  async findSystems(filter): Promise<System[]>;
}

class System {
  async getDataStreams(filter?): Promise<DataStream[]>;
  async getAllDataStreams(): Promise<DataStream[]>;
  async datastreams(): AsyncIterable<DataStream>; // Async iterator
}

// Functional helpers
function buildBboxQuery(bounds): string;
function selectBestFormat(available, preferences): string;
```

**Benefits:**

- Intuitive navigation: `system.getDataStreams()`
- Reduced boilerplate
- Type safety
- Chainable operations
- Functional utilities for common tasks

---

### 16.5 Error Handling Strategy

**Based on gaps in osh-viewer:**

```typescript
class CSAPIClient {
  constructor(options: {
    baseUrl: string;
    auth?: AuthConfig;
    retry?: RetryConfig; // ADD: Retry strategy
    timeout?: number; // ADD: Request timeout
    reconnect?: ReconnectConfig; // ADD: WebSocket reconnection
  }) {}
}

interface RetryConfig {
  retries: number; // Default: 3
  backoff: 'exponential' | 'linear';
  maxDelay: number; // Max backoff delay
}

interface ReconnectConfig {
  enabled: boolean; // Auto-reconnect on WebSocket close
  maxAttempts: number;
  backoff: 'exponential';
}
```

---

### 16.6 Performance Optimizations

**Add Missing Features:**

1. **Request Deduplication:**

   - Avoid duplicate simultaneous requests
   - Cache in-flight promises

2. **Connection Pooling:**

   - Reuse WebSocket connections
   - Limit concurrent HTTP requests

3. **Lazy Loading:**

   - Load sub-resources on demand
   - Virtual scrolling for large lists

4. **Background Prefetching:**
   - Prefetch next page while displaying current
   - Predictive loading based on user behavior

---

## Summary

### Key Findings

**Usage Patterns:**

- **Read-heavy:** 90%+ GET operations, minimal write
- **Hierarchy navigation:** System → DataStreams → Observations
- **Real-time focus:** WebSocket streaming for live data
- **Simple queries:** bbox + datetime + property filters dominate
- **Offset pagination:** Works well, link-following not needed in practice

**Convenience Opportunities:**

- Auto-pagination methods
- Format negotiation helpers
- Schema-aware parsing
- Fluent query builders
- Streaming abstractions

**Performance Insights:**

- Schema caching essential
- Binary formats for high-frequency data
- Request batching not used but could help
- WebSocket reconnection needed

**MVP Scope:**

- Focus on GET operations + basic commanding
- Defer write operations (POST/PUT/DELETE systems)
- Simple filters sufficient (bbox, datetime, property)
- WebSocket streaming essential

**Architecture:**

- Object-oriented resource navigation
- Filter builder pattern
- Collection pattern for pagination
- Parser strategy for formats
- State management integration

This analysis demonstrates that real-world CSAPI usage is simpler than the full spec suggests, allowing focused MVP development on core read + streaming + command patterns with convenience methods to reduce common boilerplate.
