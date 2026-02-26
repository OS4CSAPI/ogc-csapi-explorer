# CSAPI Client Application Analysis: oscar-viewer

**Document:** Section 11 - oscar-viewer Usage Pattern Analysis  
**Repository:** https://github.com/Botts-Innovative-Research/oscar-viewer  
**Type:** TypeScript React Web Application  
**Date:** 2026-01-31  
**Status:** Complete

---

## Executive Summary

This document analyzes oscar-viewer, a TypeScript React application for OGC API – Connected Systems focused on radiation detection monitoring. The analysis reveals production-grade patterns, TypeScript usage insights, and comparative learnings versus osh-viewer that inform type-safe client library design.

**Key Findings:**

- **TypeScript Adoption:** Strong interfaces but extensive `any` usage and type bypasses
- **Specialized Focus:** Radiation portal monitoring (gamma, neutron, occupancy, tamper sensors)
- **Multi-Server Support:** Node abstraction for federated server queries
- **Property-Based Discovery:** Heavy reliance on observedProperty URIs for datastream identification
- **Real-time Pattern:** MQTT subscriptions with Redux state management
- **Performance:** Large page sizes (1000), batching, pre-fetching, caching in state
- **Similar to osh-viewer:** Both use osh-js library, pagination loops, filter construction
- **Unique Patterns:** Redux persistence, domain-specific models, type guard utilities

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [CSAPI Operations Used](#2-csapi-operations-used)
3. [Resource Query Patterns](#3-resource-query-patterns)
4. [Pagination Implementation](#4-pagination-implementation)
5. [Format Preferences](#5-format-preferences)
6. [Sub-Resource Navigation](#6-sub-resource-navigation)
7. [Error Handling](#7-error-handling)
8. [TypeScript Usage](#8-typescript-usage)
9. [Convenience Opportunities](#9-convenience-opportunities)
10. [Unused CSAPI Features](#10-unused-csapi-features)
11. [Performance Patterns](#11-performance-patterns)
12. [Mapping Integration](#12-mapping-integration)
13. [Typical Workflows](#13-typical-workflows)
14. [UI/UX Insights](#14-uiux-insights)
15. [Data Transformation](#15-data-transformation)
16. [Comparison with osh-viewer](#16-comparison-with-osh-viewer)
17. [Code Architecture](#17-code-architecture)
18. [Library Design Implications](#18-library-design-implications)

---

## 1. Application Overview

**oscar-viewer** is a TypeScript React application for monitoring radiation detection systems at border crossings and ports. It provides:

- **Real-time Monitoring:** Live gamma/neutron counts, occupancy, tamper status
- **Event Analysis:** Historical events with video playback
- **Multi-Site Support:** Federated queries across multiple CSAPI servers
- **Command & Control:** Send commands to detection systems

**Tech Stack:**

- React 18 with TypeScript
- Redux Toolkit for state management
- Material-UI (MUI) components
- osh-js library for CSAPI interaction
- Leaflet for mapping

**Use Case:** Border security operations, radiation portal monitoring, event investigation

---

## 2. CSAPI Operations Used

### 2.1 GET Operations (Primary)

**System Resources:**

```typescript
GET /systems                                 // Fetch all systems
GET /systems?searchMembers=true              // Include subsystems
GET /systems?validTime=latest                // Current valid systems
GET /systems/{id}/subsystems                 // Get subsystems of a system
GET /systems/{id}/datastreams                // Get datastreams
```

**DataStream Resources:**

```typescript
GET /datastreams                             // Search all datastreams
GET /datastreams?system={ids}                // Filter by system IDs
GET /datastreams?validTime=latest            // Current valid datastreams
GET /datastreams/{id}/observations           // Get observations
```

**Observation Resources:**

```typescript
GET /observations                            // Search observations
GET /observations?dataStream={ids}           // Filter by datastream
GET /observations?resultTime={range}         // Time range filter
GET /observations?filter={conditions}        // Property filter
GET /observations?order=desc                 // Sort order
GET /observations/count                      // Get total count
```

**ControlStream Resources:**

```typescript
GET / controlstreams; // Fetch control streams
GET / controlstreams / { id } / status; // Get command status
```

### 2.2 POST Operations

**Command Submission:**

```typescript
POST / controlstreams / { id } / commands;
Body: {
  // Command parameters
}
```

### 2.3 Real-time Streaming

**MQTT Subscriptions:**

- Uses MQTT protocol for live observation streaming
- Subscribes to datastream topics
- Receives observations as MQTT messages

**No WebSocket observed** (uses MQTT instead)

---

## 3. Resource Query Patterns

### 3.1 Common Query Parameters

**System Queries:**

```typescript
// Fetch all systems including members
{
  searchMembers: true,
  validTime: 'latest'
}
```

**DataStream Queries:**

```typescript
// Fetch datastreams for specific systems
{
  system: 'lane1,lane2,lane3',  // Comma-separated IDs
  validTime: 'latest'
}

// No additional filters observed
```

**Observation Queries:**

```typescript
// Time range with property filter
{
  dataStream: 'ds1,ds2,ds3',
  resultTime: '../2024-01-31T12:00:00Z',  // Open-ended range
  filter: "tamperStatus=true OR alarmState='Fault - Neutron High'",
  order: 'desc'
}

// Latest observations
{
  dataStream: 'ds1,ds2,ds3',
  resultTime: 'latest'
}

// Specific time window
{
  dataStream: 'ds1',
  resultTime: '2024-01-15T10:00:00Z/2024-01-15T11:00:00Z'
}
```

### 3.2 Property-Based Filtering

**Heavy Use of observedProperty URIs:**

```typescript
// Define property URIs
const GAMMA_COUNT_DEF = 'http://www.opengis.net/def/GammaGrossCount';
const NEUTRON_COUNT_DEF = 'http://www.opengis.net/def/NeutronGrossCount';
const OCCUPANCY_DEF = 'http://www.opengis.net/def/PillarOccupancyCount';
const TAMPER_STATUS_DEF = 'http://www.opengis.net/def/TamperStatus';
const ALARM_DEF = 'http://www.opengis.net/def/Alarm';
const LOCATION_DEF = 'http://www.opengis.net/def/property/OGC/0/SensorLocation';

// Find datastreams by property
const gammaStreams = allDatastreams.filter((ds) =>
  ds.properties.observedProperties[0].definition.includes(GAMMA_COUNT_DEF)
);

const tamperStreams = allDatastreams.filter((ds) =>
  ds.properties.observedProperties[0].definition.includes(TAMPER_STATUS_DEF)
);
```

**Insight:** Client library should provide first-class support for property-based discovery and filtering.

### 3.3 Query Patterns Analysis

**Most Common:**

1. Fetch all systems with members
2. Fetch datastreams filtered by system IDs
3. Fetch observations with time range + property filter
4. Latest observations for real-time status

**Rarely Used:**

- Spatial queries (bbox, geometry)
- Complex temporal operators
- Multi-property queries

---

## 4. Pagination Implementation

### 4.1 Collection Pattern (osh-js)

**Identical to osh-viewer:**

```typescript
const dataStreamCollection = await node
  .getDataStreamsApi()
  .searchDataStreams(filter, 1000);

const allDataStreams: (typeof DataStream)[] = [];

while (dataStreamCollection.hasNext()) {
  const dataStreams = await dataStreamCollection.nextPage();
  allDataStreams.push(...dataStreams);
}
```

### 4.2 Page Sizes

**Observed page sizes:**

- **Systems:** 500
- **DataStreams:** 100-1000 (typically 1000 for bulk fetch)
- **Observations:** 1-10,000 (varies by use case)
- **Control Streams:** 100

**Strategy:** Large page sizes to minimize requests, then fetch all pages.

### 4.3 Custom Count Endpoint

**Uses `/observations/count` for metadata:**

```typescript
async function fetchTotalObservationCount(
  nodeEndpoint: string,
  dsIds: string[],
  timeRange: string
): Promise<number> {
  const endpoint = `${nodeEndpoint}/observations/count?dataStream=${dsIds.join(
    ','
  )}&resultTime=${timeRange}`;

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: getAuthHeaderFromLocalStorage(),
    });

    if (!response.ok) {
      console.error('Cannot fetch total count');
      return 0;
    }

    const count = await response.json();
    return count;
  } catch (error) {
    console.error('Error fetching observation count:', error);
    return 0;
  }
}
```

**Insight:** Custom endpoints like `/count` are valuable for pagination UI without fetching data.

---

## 5. Format Preferences

### 5.1 Format Selection

**Primary Formats:**

```typescript
// For observations
responseFormat: isVideoDataStream(dsObj)
  ? 'application/swe+binary' // Video streams only
  : 'application/swe+json'; // Default for all others

// For API responses (metadata)
('application/om+json');
('application/sml+json');
```

### 5.2 No Explicit Negotiation

**Relies on osh-js defaults:**

- No `Accept` header configuration observed
- Format selection based on datastream type detection
- Falls back to library defaults

**Type Detection:**

```typescript
function isVideoDataStream(dataStream: typeof DataStream): boolean {
  const videoOutputName = dataStream.properties.outputName;
  return videoOutputName?.toLowerCase().includes('video') ?? false;
}
```

**Insight:** Format selection often driven by output name conventions rather than MIME types.

---

## 6. Sub-Resource Navigation

### 6.1 Hierarchical Navigation

**System Hierarchy:**

```typescript
// Fetch systems
const systems = await node.fetchSystems();

// For each system, fetch subsystems
for (const system of systems) {
  const subsystems = await node.fetchSubsystems(system.id);

  // Fetch datastreams
  const datastreams = await node.fetchDataStreams(system.id);
}
```

**DataStream to Observations:**

```typescript
// Get datastreams
const datastreams = await node
  .getDataStreamsApi()
  .searchDataStreams(filter, 1000);

// For each datastream, query observations
for (const ds of datastreams) {
  const observations = await node.getObservationsApi().searchObservations(
    new ObservationFilter({
      dataStream: ds.id,
      resultTime: timeRange,
    }),
    100
  );
}
```

### 6.2 Cross-Reference Pattern

**Using embedded IDs:**

```typescript
// Datastreams contain system@id
const systemId = datastream.properties['system@id'];

// Match datastreams to systems
const systemDatastreams = allDatastreams.filter(
  (ds) => ds.properties['system@id'] === system.id
);

// Extract IDs from resource paths
const dsId = datasource.properties.resource.split('/')[2];
// From: /datastreams/{dsId}/observations
```

**Insight:** Library should provide helpers to extract and match cross-referenced IDs.

---

## 7. Error Handling

### 7.1 Try-Catch with Defaults

**Common Pattern:**

```typescript
try {
  const response = await fetch(endpoint, options);

  if (!response.ok) {
    console.error('Cannot fetch data');
    return defaultValue; // Return default instead of throwing
  }

  const data = await response.json();
  return data;
} catch (error) {
  console.error('Error fetching:', error);
  return defaultValue;
}
```

### 7.2 Silent Failures

**Graceful Degradation:**

```typescript
// Continue operation even if sub-resource fails
const datastreams = await node.fetchDataStreams(systemId).catch(() => []);
```

### 7.3 Retry Logic (Limited)

**Video Stream Retries:**

```typescript
const MAX_RETRIES = 5;
const RETRY_DELAY = 750; // ms

for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
  try {
    await loadVideoSegment(url);
    break; // Success
  } catch (error) {
    if (attempt < MAX_RETRIES - 1) {
      await sleep(RETRY_DELAY);
    } else {
      console.error('Failed after retries');
    }
  }
}
```

### 7.4 Error Handling Gaps

**Missing:**

- No HTTP status code differentiation (401 vs 403 vs 500)
- No exponential backoff
- No circuit breaker pattern
- No error boundaries for component failures
- Limited user-facing error messages

**Insight:** Library should provide configurable retry/backoff strategies and typed error responses.

---

## 8. TypeScript Usage

### 8.1 Type Imports from osh-js

**Using `typeof` Pattern:**

```typescript
import { System, DataStream, ConSysApi, Observations } from 'osh-js';

// Type references
const systems: (typeof System)[] = [];
const datastreams: (typeof DataStream)[] = [];
const api: typeof ConSysApi;
```

**Insight:** This pattern works but is awkward. Library should export proper types separately from classes.

### 8.2 Custom Interfaces

**Domain Models:**

```typescript
interface INode {
  id: string;
  name: string;
  address: string;
  port: number;
  pathRoot: string;
  csAPIEndpoint: string;
  getConnectedSystemsEndpoint(noProtocolPrefix: boolean): string;
  fetchSystems(): Promise<any[]>;
  getSystemsApi(): typeof Systems;
  getDataStreamsApi(): typeof DataStreams;
  getObservationsApi(): typeof Observations;
  getControlStreamsApi(): typeof ControlStreams;
}

interface IEventTableData {
  id: number;
  laneId: string;
  occupancyObsId: string;
  startTime: string;
  endTime: string;
  vehicleClass: string;
  gammaAlarm: boolean;
  neutronAlarm: boolean;
  occupancyCount: number;
}
```

**Collection Wrapper:**

```typescript
interface LaneDSColl {
  gamma: typeof DataStream | undefined;
  neutron: typeof DataStream | undefined;
  occupancy: typeof DataStream | undefined;
  tamper: typeof DataStream | undefined;
  gammaAlarm: typeof DataStream | undefined;
  neutronAlarm: typeof DataStream | undefined;
  location: typeof DataStream | undefined;
  video: typeof DataStream | undefined;
}
```

### 8.3 Type Safety Issues

**Extensive `any` Usage:**

```typescript
// @ts-ignore
const systemId = datastream.properties['system@id'];

// Untyped API responses
const response: any = await fetch(url).then((r) => r.json());

// Untyped event handlers
const handleClick = (event: any) => {
  /* ... */
};
```

**Missing Type Guards:**

```typescript
// Should have type narrowing
if (datastream.properties.observedProperties) {
  const prop = datastream.properties.observedProperties[0];
  // prop is 'any', no type safety
}
```

**Insight:** Library should provide strong types for all CSAPI resources with proper type guards.

### 8.4 Type Utility Functions

**Custom Type Guards:**

```typescript
export function isGammaDataStream(dataStream: typeof DataStream): boolean {
  return dataStream.properties.observedProperties[0].definition.includes(
    GAMMA_COUNT_DEF
  );
}

export function isTamperDataStream(dataStream: typeof DataStream): boolean {
  return dataStream.properties.observedProperties[0].definition.includes(
    TAMPER_STATUS_DEF
  );
}

export function isVideoDataStream(dataStream: typeof DataStream): boolean {
  const videoOutputName = dataStream.properties.outputName;
  return videoOutputName?.toLowerCase().includes('video') ?? false;
}
```

**Insight:** Library should provide predicate helpers for common property-based filtering.

---

## 9. Convenience Opportunities

### 9.1 Repeated Pagination Boilerplate

**Pattern appears everywhere:**

```typescript
// Repeated ~20 times across codebase
const collection = await api.searchDataStreams(filter, 1000);
const results: (typeof DataStream)[] = [];

while (collection.hasNext()) {
  const items = await collection.nextPage();
  results.push(...items);
}
```

**Convenience Method Needed:**

```typescript
// Suggested
const results = await api.fetchAllDataStreams(filter);

// Or async iterator
for await (const datastream of api.datastreamsIterator(filter)) {
  process(datastream);
}
```

---

### 9.2 Property-Based Lookup

**Current Pattern:**

```typescript
const gammaStreams = allDatastreams.filter(
  (ds) =>
    ds.properties.observedProperties &&
    ds.properties.observedProperties[0] &&
    ds.properties.observedProperties[0].definition &&
    ds.properties.observedProperties[0].definition.includes(GAMMA_COUNT_DEF)
);
```

**Convenience Method Needed:**

```typescript
const gammaStreams = await api.findDataStreamsByProperty(GAMMA_COUNT_DEF, {
  matchType: 'contains',
});
```

---

### 9.3 Multi-DataStream Observation Query

**Current Pattern:**

```typescript
const dsIds = datastreams.map((ds) => ds.id).join(',');
const filter = new ObservationFilter({
  dataStream: dsIds,
  resultTime: timeRange,
});
const observations = await api.searchObservations(filter, 1000);
```

**Convenience Method Needed:**

```typescript
const observations = await api.fetchObservationsForDataStreams(datastreams, {
  resultTime: timeRange,
});
```

---

### 9.4 Auth Header Construction

**Current Pattern:**

```typescript
function getAuthHeaderFromLocalStorage(): HeadersInit {
  const credentials = localStorage.getItem('credentials');
  if (!credentials) return {};

  const { username, password } = JSON.parse(credentials);
  const encoded = btoa(`${username}:${password}`);
  return { Authorization: `Basic ${encoded}` };
}

// Used everywhere
const response = await fetch(url, {
  headers: getAuthHeaderFromLocalStorage(),
});
```

**Convenience Needed:**

```typescript
// Library should handle auth automatically
const client = new CSAPIClient({
  baseUrl: 'https://api.example.org',
  auth: {
    type: 'basic',
    username: 'user',
    password: 'pass',
  },
});

// No manual header construction needed
const systems = await client.getSystems();
```

---

### 9.5 Node/Endpoint Management

**Current Pattern:**

```typescript
const protocol = node.protocol || 'https';
const address = node.address;
const port = node.port;
const pathRoot = node.pathRoot || '';
const csAPIEndpoint = node.csAPIEndpoint || '/api';

const fullUrl = `${protocol}://${address}:${port}${pathRoot}${csAPIEndpoint}`;
```

**Convenience Needed:**

```typescript
// Library should provide URL builder
const client = CSAPIClient.fromNodeConfig({
  protocol: 'https',
  host: 'api.example.org',
  port: 443,
  pathPrefix: '/api/v1',
  csapiPath: '/consys',
});

// Or from URL
const client = new CSAPIClient('https://api.example.org:443/api/v1/consys');
```

---

### 9.6 Observation Count Helper

**Current Pattern:**

```typescript
async function fetchTotalObservationCount(
  nodeEndpoint: string,
  dsIds: string[],
  timeRange: string
): Promise<number> {
  const url = `${nodeEndpoint}/observations/count?dataStream=${dsIds.join(
    ','
  )}&resultTime=${timeRange}`;
  const response = await fetch(url, { headers: auth() });
  return response.json();
}
```

**Convenience Needed:**

```typescript
const count = await api.getObservationCount({
  dataStreams: dsIds,
  resultTime: timeRange,
});
```

---

## 10. Unused CSAPI Features

### 10.1 Not Used in oscar-viewer

**Spatial Operations:**

- No `bbox` queries
- No `geometry` filters
- No spatial relationships
- Relies on datastream metadata for location

**Advanced Temporal:**

- Only uses basic time ranges and `latest`
- No `validTime` queries on observations
- No complex temporal operators

**Linked Data:**

- No traversal via `@id` references
- No `$expand` queries
- Manually constructs relationships

**Content Negotiation:**

- No multiple format preferences
- No `Accept` header usage
- Hardcoded format selection

**Conditional Requests:**

- No ETags
- No `If-Modified-Since`
- No caching headers

**Resource Management:**

- No POST/PUT/DELETE for systems/datastreams
- Only POST commands to control streams

**Part 2 Advanced Features:**

- No sampling features queries
- No procedures
- No complex system hierarchies (only parent-child)
- No deployment resources

### 10.2 MVP Prioritization Insights

**Essential (P0):**

- GET systems, datastreams, observations
- Basic filters: system IDs, time ranges, property filters
- Pagination with large page sizes
- POST commands
- Real-time subscriptions (MQTT/WebSocket)

**Important (P1):**

- Observation counts
- Property-based discovery
- Multi-server support

**Can Defer (P2):**

- Spatial queries
- Advanced temporal operators
- Write operations (except commands)
- Sampling features, procedures, deployments

---

## 11. Performance Patterns

### 11.1 Redux State Caching

**Centralized State:**

```typescript
// Redux store caches fetched data
interface AppState {
  nodes: INode[];
  systems: (typeof System)[];
  datastreams: (typeof DataStream)[];
  observations: Map<string, Observation[]>;
  controlStreams: (typeof ControlStream)[];
}

// Persisted to localStorage
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['nodes', 'systems'], // Persist selected slices
};
```

**Benefits:**

- Avoids re-fetching on page reload
- Shared across components
- Survives browser refresh

### 11.2 Large Page Sizes

**Aggressive Pagination:**

```typescript
// Systems: 500 per page
const systems = await api.searchSystems(filter, 500);

// DataStreams: 1000 per page
const datastreams = await api.searchDataStreams(filter, 1000);

// Observations: up to 10,000
const observations = await api.searchObservations(filter, 10000);
```

**Strategy:** Minimize round trips by fetching large batches.

### 11.3 Batching with Comma-Separated IDs

**Query Multiple Resources:**

```typescript
// Fetch datastreams for multiple systems at once
const systemIds = ['sys1', 'sys2', 'sys3'];
const filter = new DataStreamFilter({
  system: systemIds.join(','),
});

// Fetch observations for multiple datastreams
const datastreamIds = ['ds1', 'ds2', 'ds3'];
const obsFilter = new ObservationFilter({
  dataStream: datastreamIds.join(','),
});
```

**Benefit:** Single request instead of N requests.

### 11.4 Pre-fetching and Parallel Requests

**Initialization Pre-fetch:**

```typescript
// Fetch all data on app load
useEffect(() => {
  Promise.all([fetchSystems(), fetchDataStreams(), fetchControlStreams()]).then(
    () => {
      setInitialized(true);
    }
  );
}, []);
```

**Parallel Node Queries:**

```typescript
// Query multiple servers concurrently
await Promise.all(
  nodes.map(async (node) => {
    const systems = await node.fetchSystems();
    const datastreams = await node.fetchDataStreams();
    return { node, systems, datastreams };
  })
);
```

### 11.5 Time Range Caching

**Cache Query Results:**

```typescript
// React ref for mutable cache
const timeRangeCache = useRef<Map<string, Observation[]>>(new Map());

function getCachedObservations(
  dsId: string,
  timeRange: string
): Observation[] | undefined {
  const key = `${dsId}:${timeRange}`;
  return timeRangeCache.current.get(key);
}

function cacheObservations(
  dsId: string,
  timeRange: string,
  obs: Observation[]
): void {
  const key = `${dsId}:${timeRange}`;
  timeRangeCache.current.set(key, obs);
}
```

### 11.6 MQTT Connection Pooling

**Shared Client:**

```typescript
// Single MQTT client for all subscriptions
let mqttClientInstance: MQTTClient | null = null;

export function getMQTTClient(): MQTTClient {
  if (!mqttClientInstance) {
    mqttClientInstance = new MQTTClient(brokerUrl);
  }
  return mqttClientInstance;
}

// Subscribe multiple datastreams to same client
const client = getMQTTClient();
datastreams.forEach((ds) => {
  client.subscribe(`/datastreams/${ds.id}/observations`, handleMessage);
});
```

**Benefit:** Reduces connection overhead.

---

## 12. Mapping Integration

### 12.1 Leaflet Integration

**Image Overlay for Site Diagrams:**

```typescript
import LeafletView from 'osh-js';
import L from 'leaflet';

const leafletView = new LeafletView({
  container: 'map-container',
  layers: [
    /* base layers */
  ],
});

// Add site diagram as image overlay
const imageBounds = [
  [lat1, lon1],
  [lat2, lon2],
];
leafletView.addImageOverlay('/assets/site-diagram.png', imageBounds, {
  opacity: 0.8,
});
```

### 12.2 Point Markers for Lane Locations

**Extract Location from DataStream:**

```typescript
// Find location datastream
const locationDS = datastreams.find((ds) =>
  ds.properties.observedProperties[0].definition.includes(LOCATION_DEF)
);

if (locationDS) {
  // Fetch latest observation for location
  const observations = await api.searchObservations(
    new ObservationFilter({
      dataStream: locationDS.id,
      resultTime: 'latest',
    }),
    1
  );

  const latestObs = observations.items[0];
  const [lon, lat] = latestObs.result; // Assumes [lon, lat] format

  // Add marker
  const marker = L.marker([lat, lon], {
    icon: customIcon,
    title: laneName,
  });

  marker.addTo(leafletView.map);
  marker.bindPopup(`Lane ${laneId}`);
}
```

### 12.3 No Spatial Queries

**Static Location Display:**

- No bbox queries for viewport
- No dynamic loading based on map extent
- Locations determined by datastream observations
- Static site diagrams, not tiled maps

**Insight:** For specialized applications, spatial queries may not be needed if locations are known upfront.

---

## 13. Typical Workflows

### 13.1 Application Initialization

```typescript
// Workflow A: Startup Sequence

1. Load saved nodes from Redux store (if persisted)
   → const nodes = useSelector(state => state.nodes);

2. For each node, verify connectivity
   → await node.checkForEndpoint();

3. Fetch all systems (including subsystems)
   → const systems = await node.fetchSystems();
   → Filter for lane systems

4. Fetch datastreams for all systems
   → const dsFilter = new DataStreamFilter({
       system: systemIds.join(','),
       validTime: 'latest'
     });
   → const datastreams = await node.fetchAllDataStreams(dsFilter);

5. Group datastreams by observed property
   → const grouped = groupDataStreamsByProperty(datastreams);
   → Store in LaneMapEntry per lane

6. Fetch control streams
   → const controlStreams = await node.fetchControlStreams();

7. Create MQTT datasources for real-time
   → datastreams.forEach(ds => createMQTTDatasource(ds));

8. Subscribe and connect
   → datasources.forEach(ds => ds.connect());

9. Update Redux state
   → dispatch(setInitialized(true));
```

**Duration:** 5-15 seconds for typical deployment (10-50 lanes)

---

### 13.2 Real-Time Status Monitoring

```typescript
// Workflow B: Live Dashboard Updates

1. MQTT connection established during init
   → const client = getMQTTClient();

2. Subscribe to datastream topics
   → client.subscribe(`/datastreams/${dsId}/observations`);

3. Handle incoming messages
   → client.on('message', (topic, payload) => {
       const observation = parseObservation(payload);
       dispatch(updateLatestObservation({ dsId, observation }));
     });

4. React components watch Redux state
   → const latestGamma = useSelector(state =>
       state.observations[gammaDatastreamId]
     );

5. UI updates automatically on state change
   → <StatusBadge value={latestGamma.result} />
```

---

### 13.3 Historical Event Analysis

```typescript
// Workflow C: Investigate Past Event

1. User selects event from table
   → const event: EventTableData = selectedRow;

2. Parse time range from event
   → const timeRange = `${event.startTime}/${event.endTime}`;

3. Identify relevant datastreams
   → const dsIds = [
       event.gammaDatastreamId,
       event.neutronDatastreamId,
       event.videoDatastreamId
     ];

4. Query observations for time range
   → const observations = await api.fetchObservationsForDataStreams(
       dsIds,
       { resultTime: timeRange }
     );

5. Display on chart
   → <LineChart data={observations} />

6. Load video for time range
   → <VideoPlayer
       datastream={videoDS}
       startTime={event.startTime}
       endTime={event.endTime}
     />
```

---

### 13.4 Command Execution

```typescript
// Workflow D: Send Command to Lane System

1. Identify control stream by controlled property
   → const controlStream = controlStreams.find(cs =>
       cs.properties.controlledProperties[0].definition
         .includes(RESET_COMMAND_DEF)
     );

2. Fetch command schema
   → const schema = await api.getControlStreamSchema(controlStream.id);

3. Build command JSON from schema
   → const command = {
       resetType: 'soft',
       timestamp: new Date().toISOString()
     };

4. Send command
   → const response = await api.sendCommand(
       controlStream.id,
       command
     );

5. Poll status endpoint for completion
   → const checkStatus = setInterval(async () => {
       const status = await api.getCommandStatus(
         controlStream.id,
         response.commandId
       );
       if (status.state === 'COMPLETED') {
         clearInterval(checkStatus);
         dispatch(showNotification('Command completed'));
       }
     }, 1000);
```

---

### 13.5 Multi-Server Federated Query

```typescript
// Workflow E: Query Across Multiple Sites

1. User selects "All Sites" filter
   → const selectedNodes = allNodes;

2. Query each node in parallel
   → const results = await Promise.all(
       selectedNodes.map(async (node) => {
         const systems = await node.fetchSystems();
         const datastreams = await node.fetchAllDataStreams(filter);
         return { node, systems, datastreams };
       })
     );

3. Merge results
   → const allSystems = results.flatMap(r => r.systems);
   → const allDatastreams = results.flatMap(r => r.datastreams);

4. Display aggregated data
   → <SiteComparisonTable data={allSystems} />
```

---

## 14. UI/UX Insights

### 14.1 Display Patterns Driving Queries

**Real-Time Status Badges:**

- Require continuous updates (MQTT subscriptions)
- Display latest observation result
- Color-coded by threshold values

**Event Table (DataGrid):**

- Paginated queries with `order=desc`
- Fetches on page change
- Requires total count for pagination UI

**Video Playback:**

- Requires time-range observation queries
- Binary format for efficiency
- HLS streaming with segment requests

**Charts (Time Series):**

- Historical observations over time range
- Aggregated from multiple datastreams
- Requires bulk pagination

### 14.2 User Interactions

**Lane Selection:**

- Filters all queries by system IDs
- Updates real-time subscriptions
- Reloads relevant datastreams

**Time Range Picker:**

- Modifies `resultTime` parameter
- Triggers new observation queries
- Updates chart data

**Site Selector:**

- Changes active node
- Switches CSAPI endpoint
- Re-initializes data

**Status Filters:**

- Uses observation property filters
- `filter=alarmState='Fault'`
- Client-side filtering on cached data for speed

### 14.3 Performance Requirements

**User Expectations:**

- Initial load: < 10 seconds
- Status updates: < 1 second (real-time)
- Video playback: < 3 seconds to start
- Table pagination: < 500ms per page
- Chart updates: < 1 second

**Drives Design:**

- Pre-fetching on init
- Large page sizes for bulk data
- MQTT for real-time (not polling)
- Caching in Redux

---

## 15. Data Transformation

### 15.1 Observation to Domain Object

**Event Construction:**

```typescript
class EventTableData {
  id: number;
  laneId: string;
  occupancyObsId: string;
  startTime: string;
  endTime: string;
  vehicleClass: string;
  gammaAlarm: boolean;
  neutronAlarm: boolean;
  occupancyCount: number;

  constructor(
    id: number,
    laneId: string,
    result: any,
    obsId: string,
    foi: string
  ) {
    this.id = id;
    this.laneId = laneId;
    this.occupancyObsId = obsId;
    this.startTime = result.startTime;
    this.endTime = result.endTime;
    this.vehicleClass = result.vehicleClass;
    this.gammaAlarm = result.gammaAlarm;
    this.neutronAlarm = result.neutronAlarm;
    this.occupancyCount = result.occupancyCount;
  }
}

function eventFromObservation(obs: any): EventTableData {
  return new EventTableData(
    obs.id,
    obs.foi, // Feature of interest = lane ID
    obs.result,
    obs.id,
    obs.properties.foi
  );
}
```

### 15.2 Redux Serialization

**Map to Object Conversion:**

```typescript
// Redux can't serialize Map objects
const convertToMap = (obj: any): Map<string, any> => {
  if (obj instanceof Map) return obj;
  return new Map(Object.entries(obj));
};

// Store as plain object
const serializeMap = (map: Map<string, any>): Record<string, any> => {
  return Object.fromEntries(map);
};
```

### 15.3 Property Extraction

**Cross-Reference Resolution:**

```typescript
// Extract system ID from datastream
const systemId = datastream.properties['system@id'];

// Extract datastream ID from resource path
// Resource: "/datastreams/{dsId}/observations"
const dsId = datasource.properties.resource.split('/')[2];

// Extract observed property URI
const propUri = datastream.properties.observedProperties[0].definition;
```

### 15.4 Time Formatting

**Display Formatting:**

```typescript
// Epoch to ISO string
const isoString = new Date(epochMs).toISOString();

// Localized display
const displayTime = new Date(epochMs).toLocaleString('en-US', {
  dateStyle: 'short',
  timeStyle: 'medium',
});

// UTC formatted (custom utility)
const utcFormatted = TimePeriod.getUtcFormattedTime(epochMs);
// Returns: "2024-01-31 12:34:56"
```

### 15.5 Result Type Handling

**Scalar vs Record:**

```typescript
// Gamma count: scalar result
const gammaCount: number = observation.result;

// Occupancy event: record result
const eventData: {
  startTime: string;
  endTime: string;
  vehicleClass: string;
  gammaAlarm: boolean;
  neutronAlarm: boolean;
} = observation.result;
```

---

## 16. Comparison with osh-viewer

### 16.1 Similarities

**Both Applications:**

- Use osh-js library for CSAPI interaction
- Pagination pattern: `hasNext()` / `nextPage()` loops
- Filter construction with dedicated classes
- Real-time streaming (WebSocket or MQTT)
- Large page sizes for bulk fetches
- Property-based datastream identification
- No spatial queries
- Read-focused (minimal write operations)

### 16.2 Differences

| Aspect                 | osh-viewer (JavaScript)      | oscar-viewer (TypeScript)      |
| ---------------------- | ---------------------------- | ------------------------------ |
| **Language**           | JavaScript (Vue 3)           | TypeScript (React)             |
| **State Management**   | Pinia stores                 | Redux Toolkit + persist        |
| **Type Safety**        | None                         | Partial (many `any` types)     |
| **Domain Focus**       | General sensor visualization | Radiation detection monitoring |
| **Multi-Server**       | Single server                | Multiple federated servers     |
| **Real-time Protocol** | WebSocket                    | MQTT                           |
| **Streaming Format**   | SWE+JSON, SWE+Binary         | Primarily SWE+JSON             |
| **UI Framework**       | Vuetify                      | Material-UI                    |
| **Code Organization**  | Component-driven             | Service layer + components     |
| **Error Handling**     | Try-catch with logging       | Try-catch with defaults        |
| **Caching**            | Per-format schema caching    | Redux state persistence        |
| **Custom Endpoints**   | None                         | `/observations/count`          |

### 16.3 Architectural Differences

**osh-viewer:**

- Framework-like with osh-js at core
- Vue composition API patterns
- Inline CSAPI calls in components
- Schema parsers per format

**oscar-viewer:**

- Application-specific
- Node abstraction layer
- Domain models (EventTableData, LaneMapEntry)
- Redux for state management
- TypeScript interfaces (though underutilized)

### 16.4 Lessons from Comparison

**Common Pain Points:**

1. Pagination boilerplate repeated everywhere
2. Property-based filtering requires manual string matching
3. Auth headers manually constructed
4. Format selection logic duplicated

**TypeScript Advantages (When Used Properly):**

- Clearer interfaces for domain models
- Better IDE autocomplete
- Compile-time checks for typos

**TypeScript Disadvantages (As Implemented):**

- `typeof` pattern awkward for importing types
- Extensive `any` usage defeats purpose
- `@ts-ignore` comments indicate type system fighting

**Insight:** Library should provide clean TypeScript types without class-based exports requiring `typeof`.

---

## 17. Code Architecture

### 17.1 Module Structure

```
src/
├── lib/
│   ├── data/
│   │   ├── osh/
│   │   │   └── Node.ts              # Server abstraction
│   │   └── oscar/
│   │       ├── LaneCollection.ts    # Domain models
│   │       └── Utilities.ts         # Type guards
│   └── utils/
│       └── TimePeriod.ts            # Time utilities
├── app/
│   ├── contexts/
│   │   └── DataSourceContext.tsx    # Global data provider
│   ├── store/
│   │   └── slices/                  # Redux state slices
│   ├── _components/
│   │   ├── Dashboard/
│   │   ├── EventTable/
│   │   └── VideoPlayer/
│   └── pages/
│       └── [routes].tsx
```

### 17.2 Node Abstraction Layer

**Server Wrapper:**

```typescript
// Node.ts
export class Node implements INode {
  id: string;
  name: string;
  address: string;
  port: number;
  pathRoot: string;
  csAPIEndpoint: string;

  private systemsApi: typeof Systems;
  private dataStreamsApi: typeof DataStreams;
  private observationsApi: typeof Observations;
  private controlStreamsApi: typeof ControlStreams;

  constructor(config: NodeConfig) {
    this.id = config.id;
    this.name = config.name;
    // Initialize API clients
    this.systemsApi = new Systems(this.getEndpoint());
    this.dataStreamsApi = new DataStreams(this.getEndpoint());
    // ...
  }

  getEndpoint(): string {
    return `${this.protocol}://${this.address}:${this.port}${this.pathRoot}${this.csAPIEndpoint}`;
  }

  async fetchSystems(): Promise<(typeof System)[]> {
    const collection = await this.systemsApi.searchSystems(
      new SystemFilter({ searchMembers: true, validTime: 'latest' }),
      500
    );

    const systems: (typeof System)[] = [];
    while (collection.hasNext()) {
      systems.push(...(await collection.nextPage()));
    }
    return systems;
  }

  // Similar methods for datastreams, observations, etc.
}
```

**Benefits:**

- Multi-server support
- Encapsulates endpoint construction
- Consistent API across servers
- Easy to add/remove servers

### 17.3 Domain Models

**Lane Collection:**

```typescript
// LaneCollection.ts
export interface LaneDSColl {
  gamma: typeof DataStream | undefined;
  neutron: typeof DataStream | undefined;
  occupancy: typeof DataStream | undefined;
  tamper: typeof DataStream | undefined;
  gammaAlarm: typeof DataStream | undefined;
  neutronAlarm: typeof DataStream | undefined;
  location: typeof DataStream | undefined;
  video: typeof DataStream | undefined;
}

export class LaneMapEntry {
  laneId: string;
  primarySystem: typeof System;
  subsystems: (typeof System)[];
  datastreams: LaneDSColl;
  controlStreams: (typeof ControlStream)[];

  constructor(laneId: string, primarySystem: typeof System) {
    this.laneId = laneId;
    this.primarySystem = primarySystem;
    this.subsystems = [];
    this.datastreams = {};
    this.controlStreams = [];
  }

  addDataStream(ds: typeof DataStream): void {
    if (isGammaDataStream(ds)) {
      this.datastreams.gamma = ds;
    } else if (isTamperDataStream(ds)) {
      this.datastreams.tamper = ds;
    }
    // ... other types
  }
}
```

### 17.4 Redux State Management

**State Slices:**

```typescript
// nodesSlice.ts
interface NodesState {
  nodes: INode[];
  selectedNode: string | null;
}

export const nodesSlice = createSlice({
  name: 'nodes',
  initialState,
  reducers: {
    addNode: (state, action: PayloadAction<INode>) => {
      state.nodes.push(action.payload);
    },
    setSelectedNode: (state, action: PayloadAction<string>) => {
      state.selectedNode = action.payload;
    },
  },
});

// datastreamsSlice.ts
interface DatastreamsState {
  datastreams: Map<string, typeof DataStream>;
  latestObservations: Map<string, Observation>;
}

// Redux Persist Configuration
const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['nodes', 'systems'], // Only persist these
  blacklist: ['observations'], // Don't persist real-time data
};
```

### 17.5 Context Provider Pattern

**Global Data Context:**

```typescript
// DataSourceContext.tsx
export const DataSourceContext = React.createContext<DataSourceContextType>({
  nodes: [],
  laneMap: new Map(),
  initialized: false,
});

export function DataSourceProvider({ children }: Props) {
  const [initialized, setInitialized] = useState(false);
  const laneMapRef = useRef(new Map<string, LaneMapEntry>());

  useEffect(() => {
    // Initialize on mount
    async function init() {
      const nodes = await loadNodes();
      const laneMap = await buildLaneMap(nodes);
      laneMapRef.current = laneMap;
      setInitialized(true);
    }

    init();
  }, []);

  return (
    <DataSourceContext.Provider
      value={{
        nodes,
        laneMap: laneMapRef.current,
        initialized,
      }}
    >
      {children}
    </DataSourceContext.Provider>
  );
}
```

### 17.6 Component Pattern

**Typical Component:**

```typescript
// EventTable.tsx
export function EventTable() {
  const { laneMap } = useContext(DataSourceContext);
  const selectedNode = useSelector((state) => state.nodes.selectedNode);
  const [events, setEvents] = useState<EventTableData[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    async function fetchEvents() {
      const node = nodes.find((n) => n.id === selectedNode);
      if (!node) return;

      const dsIds = getOccupancyDatastreamIds(laneMap);
      const observations = await node.getObservationsApi().searchObservations(
        new ObservationFilter({
          dataStream: dsIds.join(','),
          resultTime: timeRange,
          order: 'desc',
        }),
        rowsPerPage
      );

      const eventData = observations.items.map(eventFromObservation);
      setEvents(eventData);
    }

    fetchEvents();
  }, [selectedNode, page, rowsPerPage]);

  return (
    <DataGrid
      rows={events}
      columns={columns}
      page={page}
      onPageChange={setPage}
    />
  );
}
```

---

## 18. Library Design Implications

### 18.1 Essential Features (P0) - From oscar-viewer

**1. Multi-Server Support:**

```typescript
// Must support multiple endpoints
const client1 = new CSAPIClient('https://site1.example.org/api');
const client2 = new CSAPIClient('https://site2.example.org/api');

// Or federated client
const federatedClient = new FederatedCSAPIClient([
  'https://site1.example.org/api',
  'https://site2.example.org/api',
]);

const allSystems = await federatedClient.getAllSystems();
// Aggregates from all servers
```

**2. Property-Based Discovery:**

```typescript
// First-class support
const gammaStreams = await client.findDataStreamsByProperty(
  'http://www.opengis.net/def/GammaGrossCount',
  { matchType: 'contains' | 'exact' }
);

// Or predicate
const gammaStreams = await client.findDataStreams({
  observedProperty: {
    uri: 'http://www.opengis.net/def/GammaGrossCount',
    match: 'contains',
  },
});
```

**3. Fetch All Helper:**

```typescript
// No more while (hasNext()) loops
const allDataStreams = await client.fetchAllDataStreams(filter);

// Or async iterator
for await (const datastream of client.datastreamsIterator(filter)) {
  process(datastream);
}
```

**4. Observation Count:**

```typescript
// Built-in count endpoint support
const count = await client.getObservationCount({
  dataStreams: ['ds1', 'ds2'],
  resultTime: '2024-01-01/2024-02-01',
});
```

**5. Auth Built-In:**

```typescript
const client = new CSAPIClient({
  baseUrl: 'https://api.example.org',
  auth: {
    type: 'basic',
    username: 'user',
    password: 'pass',
  },
});

// Auth headers added automatically
const systems = await client.getSystems();
```

---

### 18.2 TypeScript Type System

**Clean Type Exports:**

```typescript
// Library should export types separately
import { System, DataStream, Observation } from 'csapi-client';
import type { ISystem, IDataStream, IObservation } from 'csapi-client/types';

// NOT: typeof System (awkward)
```

**Strong Typing:**

```typescript
interface System {
  id: string;
  name: string;
  properties: {
    'system@id'?: string;
    observedProperties?: ObservedProperty[];
    // ... all properties typed
  };
}

// Type guards
function isSystem(obj: any): obj is System {
  return obj && typeof obj.id === 'string' && typeof obj.name === 'string';
}
```

**Generic Collections:**

```typescript
interface Collection<T> {
  items: T[];
  links: Link[];
  hasNext(): boolean;
  nextPage(): Promise<T[]>;
  fetchAll(): Promise<T[]>;
}

const systems: Collection<System> = await client.searchSystems(filter);
```

---

### 18.3 Convenience API Design

**Fluent Builder:**

```typescript
const observations = await client
  .observations()
  .forDataStreams(['ds1', 'ds2'])
  .during('2024-01-01', '2024-02-01')
  .orderBy('resultTime', 'desc')
  .limit(1000)
  .fetchAll();
```

**Property Helpers:**

```typescript
// Built-in property URI constants
import { ObservedProperties } from 'csapi-client/properties';

const gammaStreams = await client.findDataStreamsByProperty(
  ObservedProperties.GAMMA_GROSS_COUNT
);
```

**Type Guards:**

```typescript
// Exported utilities
import { isGammaDataStream, isTamperDataStream } from 'csapi-client/utils';

if (isGammaDataStream(datastream)) {
  // TypeScript knows this is a gamma datastream
  const gammaCount = await getLatestReading(datastream);
}
```

---

### 18.4 Error Handling Strategy

**Based on oscar-viewer patterns:**

```typescript
interface CSAPIClientOptions {
  // Error handling
  throwOnError?: boolean; // Default: false (return defaults)
  onError?: (error: CSAPIError) => void; // Optional callback

  // Retry
  retry?: {
    retries: number;
    backoff: 'exponential' | 'linear';
    maxDelay: number;
  };
}

// Usage
const client = new CSAPIClient({
  baseUrl: 'https://api.example.org',
  throwOnError: false, // Return empty/null instead of throwing
  onError: (error) => console.error(error),
  retry: { retries: 3, backoff: 'exponential', maxDelay: 5000 },
});

// No try-catch needed
const systems = await client.getSystems(); // Returns [] on error
```

---

### 18.5 Real-time Support

**MQTT and WebSocket:**

```typescript
// Both protocols supported
const stream = await datastream.stream({
  protocol: 'mqtt' | 'ws',
  onMessage: (observation) => updateUI(observation),
  onError: (error) => handleError(error),
  onConnect: () => console.log('Connected'),
  onDisconnect: () => console.log('Disconnected'),
});

// Auto-reconnect
stream.reconnect();

// Unsubscribe
stream.close();
```

---

### 18.6 Performance Optimizations

**Based on oscar-viewer needs:**

1. **Large Page Sizes:**

   - Default limits: 100-1000
   - Allow override for specific queries

2. **Batch Queries:**

   - Accept array of IDs, auto-convert to comma-separated
   - Parallel requests for independent queries

3. **State Integration:**

   - Redux/Zustand/Recoil adapters
   - Reactive wrappers for Vue/React

4. **Caching:**
   - Built-in cache for schemas, conformance
   - Optional cache for systems/datastreams
   - Never cache observations

---

## Summary

### Key Findings

**oscar-viewer Patterns:**

- **TypeScript:** Partial adoption with many type bypasses
- **Multi-server:** Node abstraction for federated queries
- **Property-based:** Heavy reliance on observedProperty URIs
- **Large pages:** 1000 items typical for bulk fetches
- **MQTT:** Preferred for real-time over WebSocket
- **Redux:** State persistence and management
- **Custom endpoints:** `/observations/count` for pagination

**Common with osh-viewer:**

- Same osh-js library and patterns
- Pagination loops everywhere
- Filter construction boilerplate
- Property-based datastream identification
- No spatial queries
- Read-focused operations

**Unique to oscar-viewer:**

- Multi-server federation
- Domain-specific models (lanes, events)
- Type guards for datastream classification
- Redux with persistence
- Observation count endpoint

**Convenience Needs:**

1. `fetchAll()` to eliminate pagination loops
2. Property-based lookup helpers
3. Multi-datastream observation queries
4. Built-in auth handling
5. Type-safe interfaces
6. Multi-server client
7. Observation count helper

**MVP Scope Validation:**

- Confirms osh-viewer findings: read operations dominate
- Property filtering critical
- Multi-server support important
- Custom endpoints valuable (`/count`)
- Spatial queries not needed for many applications

**TypeScript Lessons:**

- Export types separately from classes
- Avoid `typeof` pattern
- Minimize `any` usage
- Provide strong type guards
- Generic collection types

This analysis reinforces that client library should prioritize:

1. Clean TypeScript types
2. Property-based discovery
3. Pagination abstraction
4. Multi-server support
5. Built-in auth
6. Real-time subscriptions (MQTT + WebSocket)
7. Performance optimizations (batching, caching, large pages)
