# Section 32: Real-World Server Compatibility Testing

> **⚠️ REVIEW NOTICE (Phase 2E — C1): CRITICAL ANTI-PATTERN IDENTIFIED**
>
> This document's fundamental architecture is a **hybrid fixture/live test execution model** — the exact architecture the senior developer identified as the primary failure mode in the previous attempt (see [Phase 0: Lessons from Failed Attempt](../../review/phase-0-lessons-from-failed-attempt.md), Anti-Pattern AP2). Tests that run against live OpenSensorHub and 52°North servers, conditionally skip based on server availability, and validate server response content rather than client code are **not acceptable** for contribution to upstream `ogc-client`.
>
> **~35% of this document is client-oriented and valuable:** Section 5.1 (Conformance Detection) and Section 5.5 (Graceful Degradation) correctly test client behavior using mocked fetch and fixture data. These sections should be used during implementation.
>
> **~65% of this document tests server behavior and must NOT be implemented as written:** Sections 4 (hybrid execution strategy), 5.2 (OpenSensorHub live tests), 5.3 (52°North live tests), 5.4 (server availability gating), 6 (live infrastructure), and 7 (rate limiting). The server profile research in Sections 1-3 remains useful as reference context for fixture design, similar to Doc 22 Section 2.
>
> Key anti-pattern instances: `checkServerAvailability()` gating, `console.warn('...skipping')` × 5+, hardcoded credentials (`username: 'ogc'`), `npm run test:live` nightly scripts, `*.live.spec.ts` / `*.offline.spec.ts` dual jest projects.

**Research Plan:** [Research Plan 32: Real-World Server Compatibility Testing](../research-plans/32-real-world-server-compatibility-testing.md)

**Research Questions:** 6 core questions about OpenSensorHub testing, 52°North testing, server variations, partial conformance scenarios, server-specific quirks, and compatibility test suite structure.

**Methodology:** 6-phase systematic analysis (Phase 1: Server Inventory and Analysis → Phase 2: Server Profile Analysis → Phase 3: Upstream Compatibility Testing Analysis → Phase 4: Test Scenario Design → Phase 5: Test Infrastructure Design → Phase 6: Synthesis)

**Research Time:** 75 minutes – February 6, 2026

**Primary Source(s):**

- [OpenSensorHub Analysis](../../requirements/csapi-opensensorhub-analysis.md)
- [52°North Analysis](../../requirements/csapi-52north-analysis.md)
- [Conformance Capabilities](../../requirements/csapi-conformance-capabilities.md)
- [Implementation Guide](../../../planning/csapi-implementation-guide.md)

**Supporting Resources:**

- Section 22: [Conformance and Capability Testing](22-conformance-capability-testing.md) (conformance detection)
- Section 8: [CSAPI Specification Review](08-csapi-specification-review.md) (conformance classes)

**Document Purpose:** Validation strategy for testing the TypeScript CSAPI client library against multiple real-world servers (OpenSensorHub with full conformance, 52°North with partial conformance) to ensure interoperability and graceful degradation.

---

## Executive Summary

This document defines strategies for validating the TypeScript CSAPI client library against multiple real-world CSAPI servers with different conformance profiles. Two production-ready servers are available for testing:

**OpenSensorHub (Full Conformance):**

- URL: http://45.55.99.236:8080/sensorhub/api
- Conformance: 33/33 classes (100%) - Parts 1, 2, 3
- Live data: 6 systems, 28 datastreams, thousands of observations
- Authentication: HTTP Basic Auth

**52°North (Partial Conformance):**

- URL: https://csa.demo.52north.org/
- Conformance: ~15-18 classes (Part 1 full, Part 2 partial)
- Live data: 3 systems, 1 deployment, limited Part 2
- Authentication: None (public access)
- ⚠️ Issues: Expired SSL certificate, incomplete conformance declaration, Part 2 non-functional

### Key Findings

**Server Capability Profiles:**

- **Full Conformance (OSH)**: All resources, full CRUD, all encodings, streaming
- **Partial Conformance (52N)**: Part 1 complete, Part 2 DataStreams only (no ControlStreams)
- **Minimal Conformance**: Read-only systems or deployments (hypothetical)

**Testing Strategies:**

- **Live Testing**: Validate against real servers, catch interoperability issues
- **Offline Mocking**: Recorded responses, reliable CI/CD execution
- **Hybrid Approach**: Live tests nightly/manual, offline tests in CI

**Server-Specific Quirks:**

- **OSH**: Base32-encoded IDs, async servlet patterns, WebSocket/MQTT streaming
- **52N**: UUID IDs, incomplete conformance declaration, Part 2 500 errors, SSL issues

**Test Scope:**

- **Conformance detection**: ~6 tests (100 lines)
- **Full conformance (OSH)**: ~20 tests (400-500 lines)
- **Partial conformance (52N)**: ~15 tests (300-400 lines)
- **Server availability**: ~5 tests (100 lines)
- **Graceful degradation**: ~10 tests (200-250 lines)
- **Total**: ~56 tests, 1100-1400 lines

**Implementation Priority:**

1. **CRITICAL**: Conformance detection, server availability checks
2. **HIGH**: Full conformance tests (OSH), partial conformance tests (52N)
3. **MEDIUM**: Graceful degradation, server quirk handling

**Key Testing Challenges:**

1. **Live server dependencies**: Network reliability, server uptime
2. **Data variability**: Live data changes over time
3. **Authentication**: Credential management for OSH
4. **SSL issues**: Certificate validation for 52N
5. **Rate limiting**: Unknown limits on live servers

**Mitigation Strategies:**

- Record live server responses as fixtures for offline testing
- Implement server availability checks before tests
- Make live tests optional (skip if server unavailable)
- Run live tests nightly or manually, not in every CI run
- Document expected live data patterns

---

## 1. CSAPI Server Inventory

> **ℹ️ REVIEW NOTICE (Phase 2E — C1 supplement):** Sections 1-3 document real server profiles (OpenSensorHub, 52°North) with live URLs, credentials, pagination limits, and backend details. Like Doc 22 Section 2, these profiles are **reference context only** — they inform fixture design and explain why certain test scenarios exist. When implementing tests, derive fixtures from these profiles but never connect to live servers or import server-specific behaviors into test assertions.

### 1.1 OpenSensorHub (Full Conformance)

**Server Details:**

- **Implementation**: Java/Spring Boot, production-ready
- **Repository**: https://github.com/opensensorhub/osh-core
- **Live Server**: http://45.55.99.236:8080/sensorhub/api
- **Authentication**: HTTP Basic Auth (username/password)
- **Version**: CSAPI Parts 1, 2, 3 (full implementation)
- **Status**: ✅ Active, production-ready

**Conformance Classes (33 total):**

**Part 1 (13 classes):**

- ✅ A.1: Common
- ✅ A.2: System Features
- ✅ A.3: Subsystems
- ✅ A.4: Deployment Features
- ✅ A.5: Subdeployments
- ✅ A.6: Procedure Features
- ✅ A.7: Sampling Features
- ✅ A.8: Property Definitions
- ✅ A.9: Advanced Filtering
- ✅ A.10: Create/Replace/Delete
- ✅ A.11: Update
- ✅ A.12: GeoJSON Format
- ✅ A.13: SensorML Format

**Part 2 (12 classes):**

- ✅ A.1: Common
- ✅ A.2: DataStreams & Observations
- ✅ A.3: Control Streams & Commands
- ✅ A.4: Command Feasibility
- ✅ A.5: System Events
- ✅ A.6: Advanced Filtering
- ✅ A.7: Create/Replace/Delete
- ✅ A.8: Update
- ✅ A.9: O&M JSON Encoding
- ✅ A.10: SWE JSON Encoding
- ✅ A.11: SWE Text Encoding
- ✅ A.12: SWE Binary Encoding

**Part 3 (8+ classes):**

- ✅ System Events
- ✅ WebSocket Streaming
- ✅ MQTT Streaming
- (Additional Part 3 classes beyond CSAPI 1.0 scope)

**Live Data Inventory:**

- **Systems**: 6 (3 LIVE replay drones, 3 archived Android devices)
- **Deployments**: 3 (drone missions)
- **Procedures**: 6 (sensor type definitions)
- **Sampling Features**: 2 (geographic areas)
- **DataStreams**: 28 (telemetry, IMU, GPS, health)
- **Observations**: Thousands (historical + live streaming)
- **ControlStreams**: Available (command capabilities)
- **Commands**: Historical command records

**Data Characteristics:**

- **ID Format**: Base32-encoded strings (e.g., `03tbj7mvqg50`, `0406fcgwtjk5`)
- **Live Streaming**: `validTime: [..., "now"]` for active systems
- **Time Range**: Historical data from 2023-2024, live data current
- **Coordinate System**: WGS84 (EPSG:4326)
- **Formats Supported**: JSON, GeoJSON, SensorML JSON, O&M JSON, SWE JSON/Text/Binary/CSV/XML, HTML

**Authentication Details:**

```http
GET /systems HTTP/1.1
Host: 45.55.99.236:8080
Authorization: Basic <base64-encoded-credentials>
```

**Rate Limiting**: Unknown (assumed generous for public demo server)

**Server Behaviors:**

- Default pagination limit: 100 items
- Maximum limit: 10,000 items
- Async servlet architecture (non-blocking)
- WebSocket endpoint: `ws://45.55.99.236:8080/sensorhub/api/...`
- MQTT endpoint available
- Full CRUD on all resources
- Complex CQL2 filtering support (30+ query parameters)

**Test Value:**

- ✅ **Full conformance baseline** - All features should work
- ✅ **Production behavior** - Real-world performance characteristics
- ✅ **Live data** - Test temporal queries with current time
- ✅ **Streaming** - WebSocket/MQTT real-time data
- ⚠️ **Network dependency** - Requires internet connection
- ⚠️ **Shared credentials** - Single user account
- ⚠️ **Write operations** - Should avoid (shared server)

---

### 1.2 52°North (Partial Conformance)

**Server Details:**

- **Implementation**: Python/Quart/pygeoapi
- **Repository**: https://github.com/52North/connected-systems-pygeoapi
- **Live Server**: https://csa.demo.52north.org/
- **Authentication**: None (public access)
- **Version**: CSAPI Part 1 (full), Part 2 (partial - in development)
- **Status**: 🚧 Development/testing deployment

**Conformance Classes (~15-18 total):**

**Part 1 (13 classes - Full):**

- ✅ A.1: Common
- ✅ A.2: System Features
- ✅ A.3: Subsystems
- ✅ A.4: Deployment Features
- ✅ A.5: Subdeployments
- ✅ A.6: Procedure Features
- ✅ A.7: Sampling Features
- ✅ A.8: Property Definitions
- ✅ A.9: Advanced Filtering
- ✅ A.10: Create/Replace/Delete
- ✅ A.11: Update
- ✅ A.12: GeoJSON Format
- ✅ A.13: SensorML Format

**Part 2 (Partial - 2-5 classes):**

- ⚠️ A.1: Common (expected but not declared)
- 🚧 A.2: DataStreams & Observations (in development)
- ❌ A.3: Control Streams & Commands (not implemented)
- ❌ A.4: Command Feasibility (not implemented)
- ❌ A.5: System Events (not implemented)
- ⚠️ A.9: O&M JSON Encoding (expected if A.2 complete)

**Live Data Inventory:**

- **Systems**: 3 (YSI sensor, Valeport CTD, RBR platform)
- **Deployments**: 1 (Baltic Sea buoy testing)
- **Procedures**: 1 (Aanderaa sensor type definition)
- **Sampling Features**: 0
- **Properties**: 0
- **DataStreams**: Not accessible (500 errors)
- **Observations**: Not accessible (500 errors)

**Data Characteristics:**

- **ID Format**: Mixed (UUIDs, URNs, strings)
  - UUID: `4e09de42-674d-4e03-a620-2d219b030a50`
  - URN: `urn:sensor:5400-526`, `urn:platform:5300-909`
  - String: `5400-526`, `YSI599503-00-1`
- **Coordinate System**: WGS84 (EPSG:4326)
- **Formats Supported**: GeoJSON, SensorML JSON

**Server Issues:**

- ⚠️ **Expired SSL Certificate**: Requires certificate validation bypass
- ⚠️ **Incomplete Conformance Declaration**: Only 1 class declared (should be 13+)
- ❌ **Part 2 Non-Functional**: DataStreams/Observations return 500 Internal Server Error
- ⚠️ **Small Dataset**: Only 3 systems for testing

**Conformance Declaration Issue:**

**Actual Response** (GET /conformance):

```json
{
  "conformsTo": ["http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core"]
}
```

**Expected Response** (based on functional endpoints):

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sensorml"
  ]
}
```

**Test Value:**

- ✅ **Incomplete conformance testing** - Test client fallback logic
- ✅ **Partial conformance scenario** - Part 1 only
- ✅ **Error handling** - Part 2 500 errors
- ✅ **SSL issues** - Certificate validation handling
- ✅ **Real-world metadata** - Oceanographic use case
- ⚠️ **Small dataset** - Limited test coverage
- ⚠️ **Development server** - May be unstable

---

### 1.3 Server Capability Matrix

| Capability                     | OpenSensorHub               | 52°North                          | Notes                 |
| ------------------------------ | --------------------------- | --------------------------------- | --------------------- |
| **Conformance Classes**        | 33 (100%)                   | ~15-18 (Part 1 only)              | OSH full, 52N partial |
| **Part 1: Systems**            | ✅ Full CRUD                | ✅ Full CRUD                      | Both complete         |
| **Part 1: Deployments**        | ✅ Full CRUD                | ✅ Full CRUD                      | Both complete         |
| **Part 1: Procedures**         | ✅ Full CRUD                | ✅ Full CRUD                      | Both complete         |
| **Part 1: Sampling Features**  | ✅ Full CRUD                | ✅ Full CRUD                      | Both complete         |
| **Part 1: Properties**         | ✅ Full CRUD                | ✅ Full CRUD                      | Both complete         |
| **Part 1: Subsystems**         | ✅ Hierarchical             | ✅ Hierarchical                   | Both complete         |
| **Part 1: Subdeployments**     | ✅ Hierarchical             | ✅ Hierarchical                   | Both complete         |
| **Part 2: DataStreams**        | ✅ Full CRUD                | ❌ 500 errors                     | OSH only              |
| **Part 2: Observations**       | ✅ Full CRUD                | ❌ 500 errors                     | OSH only              |
| **Part 2: ControlStreams**     | ✅ Full CRUD                | ❌ Not implemented                | OSH only              |
| **Part 2: Commands**           | ✅ Full CRUD                | ❌ Not implemented                | OSH only              |
| **Advanced Filtering**         | ✅ CQL2 (30+ params)        | ✅ CQL2                           | Both complete         |
| **GeoJSON Format**             | ✅ Supported                | ✅ Supported                      | Both complete         |
| **SensorML Format**            | ✅ Supported                | ✅ Supported                      | Both complete         |
| **SWE Common Formats**         | ✅ JSON/Text/Binary/CSV/XML | ❌ Not available                  | OSH only              |
| **WebSocket Streaming**        | ✅ Available                | ❌ Not available                  | OSH only (Part 3)     |
| **MQTT Streaming**             | ✅ Available                | ❌ Not available                  | OSH only (Part 3)     |
| **Authentication**             | ✅ HTTP Basic Auth          | ❌ None (public)                  | OSH requires auth     |
| **SSL Certificate**            | ✅ Valid                    | ⚠️ Expired                        | 52N requires bypass   |
| **Conformance Declaration**    | ✅ Complete (33 classes)    | ⚠️ Incomplete (1 class)           | 52N misleading        |
| **Live Systems**               | 6                           | 3                                 | OSH more data         |
| **Live Deployments**           | 3                           | 1                                 | OSH more data         |
| **Live DataStreams**           | 28                          | 0 (inaccessible)                  | OSH only              |
| **Live Observations**          | Thousands                   | 0 (inaccessible)                  | OSH only              |
| **ID Format**                  | Base32 strings              | UUIDs/URNs/strings                | Different formats     |
| **Pagination Limit (Default)** | 100                         | Unknown (~20-50 typical pygeoapi) | OSH documented        |
| **Pagination Limit (Max)**     | 10,000                      | Unknown (~1000 typical pygeoapi)  | OSH documented        |
| **Use Case**                   | Drones, mobile sensors      | Oceanographic buoys               | Different domains     |

---

## 2. Server Profile Definitions

### 2.1 Full Conformance Profile (OpenSensorHub)

**Definition**: Server implements all CSAPI Part 1 and Part 2 conformance classes with complete CRUD operations and multiple encoding formats.

**Characteristics:**

- ✅ All 11 CSAPI resources available
- ✅ Full CRUD (GET, POST, PUT, PATCH, DELETE) on all resources
- ✅ All encoding formats (GeoJSON, SensorML, SWE Common JSON/Text/Binary)
- ✅ Advanced filtering (CQL2, 30+ query parameters)
- ✅ Hierarchical navigation (subsystems, subdeployments)
- ✅ Real-time streaming (WebSocket, MQTT)
- ✅ Pagination (configurable, up to 10,000 items)

**Expected Client Behavior:**

```typescript
// All resource classes should be available
const client = new CSAPIClient('http://45.55.99.236:8080/sensorhub/api', {
  auth: { type: 'basic', username: 'ogc', password: 'ogc' },
});

await client.initialize();

// All resources available
expect(client.systems).toBeDefined();
expect(client.deployments).toBeDefined();
expect(client.procedures).toBeDefined();
expect(client.samplingFeatures).toBeDefined();
expect(client.properties).toBeDefined();
expect(client.datastreams).toBeDefined();
expect(client.observations).toBeDefined();
expect(client.controlstreams).toBeDefined();
expect(client.commands).toBeDefined();

// All CRUD methods available
await client.systems.create(systemData);
await client.systems.update(systemId, patch);
await client.systems.replace(systemId, systemData);
await client.systems.delete(systemId);

// Nested resources available
const subsystems = await client.systems.subsystems(systemId).list();
const systemDatastreams = await client.systems.datastreams(systemId).list();
const systemEvents = await client.systems.events(systemId).list();

// Advanced features available
const stream = await client.datastreams.streamObservations(datastreamId);
stream.on('data', (obs) => console.log(obs));
```

**Test Scenarios:**

1. **Full CRUD operations** on all resources
2. **Hierarchical navigation** (subsystems, subdeployments)
3. **Cross-resource queries** (system → datastreams → observations)
4. **Advanced filtering** (CQL2, temporal, spatial, keyword)
5. **Multiple formats** (GeoJSON, SensorML, SWE JSON/Text/Binary)
6. **Pagination** (limit/offset, large datasets)
7. **Real-time streaming** (WebSocket, MQTT)
8. **Authentication** (HTTP Basic Auth)

---

### 2.2 Partial Conformance Profile (52°North)

**Definition**: Server implements CSAPI Part 1 fully but Part 2 only partially or not at all. Client must gracefully degrade to Part 1-only mode.

**Characteristics:**

- ✅ Part 1 resources fully available (Systems, Deployments, Procedures, Sampling Features, Properties)
- ✅ Full CRUD on Part 1 resources
- ✅ Part 1 encodings (GeoJSON, SensorML)
- ✅ Advanced filtering on Part 1 resources
- ⚠️ Part 2 resources unavailable or incomplete
- ❌ No real-time streaming
- ⚠️ Incomplete conformance declaration

**Expected Client Behavior:**

```typescript
// Client detects partial conformance
const client = new CSAPIClient('https://csa.demo.52north.org/', {
  ssl: { rejectUnauthorized: false }, // Skip cert validation
});

await client.initialize();

// Part 1 resources available
expect(client.systems).toBeDefined();
expect(client.deployments).toBeDefined();
expect(client.procedures).toBeDefined();

// Part 2 resources unavailable or return null
expect(client.datastreams).toBeNull(); // or throws ConformanceError
expect(client.observations).toBeNull();
expect(client.controlstreams).toBeNull();
expect(client.commands).toBeNull();

// Part 1 CRUD works
await client.systems.list();
await client.deployments.get(deploymentId);

// Part 2 methods throw errors
try {
  await client.datastreams.list();
} catch (error) {
  expect(error).toBeInstanceOf(ConformanceError);
  expect(error.message).toMatch(/datastreams.*not.*supported/i);
}
```

**Test Scenarios:**

1. **Conformance detection** with incomplete declaration
2. **Endpoint probing** when conformance insufficient
3. **Part 1 full CRUD** operations
4. **Part 2 graceful degradation** (null or error)
5. **SSL certificate bypass** handling
6. **Error recovery** from 500 responses

---

### 2.3 Minimal Conformance Profile (Hypothetical)

**Definition**: Server implements only one CSAPI resource type (e.g., Systems only) with read-only operations. Represents minimum viable CSAPI server.

**Characteristics:**

- ✅ One Part 1 resource type (Systems OR Deployments OR Procedures OR Properties)
- ✅ Read operations only (GET list, GET item)
- ✅ At least one encoding (GeoJSON OR SensorML)
- ❌ No CRUD (POST/PUT/PATCH/DELETE)
- ❌ No hierarchical navigation
- ❌ No Part 2 resources
- ❌ No advanced filtering

**Expected Client Behavior:**

```typescript
const client = new CSAPIClient('https://minimal.csapi.org/');
await client.initialize();

// Only systems available
expect(client.systems).toBeDefined();
expect(client.deployments).toBeNull();
expect(client.datastreams).toBeNull();

// Only read operations available
const systems = await client.systems.list();
const system = await client.systems.get(systemId);

// CRUD throws errors
try {
  await client.systems.create(systemData);
} catch (error) {
  expect(error).toBeInstanceOf(ConformanceError);
  expect(error.capability).toBe('hasCRUD');
}
```

**Test Scenarios:**

1. **Single resource type** detection
2. **Read-only operations** validation
3. **CRUD method unavailability** error handling
4. **Minimal conformance acceptance** (not rejection)

---

## 3. Server-Specific Quirks and Workarounds

### 3.1 OpenSensorHub Quirks

**1. Base32-Encoded IDs**

**Issue:** OSH uses Base32-encoded internal IDs (e.g., `03tbj7mvqg50`), not UUIDs or URNs.

**Impact:** Client must accept non-UUID string IDs, not validate ID format.

**Workaround:**

```typescript
// Don't assume UUID format
function isValidCSAPIId(id: string): boolean {
  // Accept any non-empty string
  return typeof id === 'string' && id.length > 0;
}
```

**2. Async Servlet Architecture**

**Issue:** OSH uses async servlet patterns, may return 202 Accepted for long operations.

**Impact:** Client must handle async responses with polling.

**Workaround:**

```typescript
async function createResource(data: any): Promise<Resource> {
  const response = await post('/systems', data);

  if (response.status === 202) {
    // Async creation - poll for completion
    const location = response.headers.get('Location');
    return await pollUntilAvailable(location);
  } else if (response.status === 201) {
    // Sync creation - resource available immediately
    return response.data;
  }
}
```

**3. WebSocket/MQTT Streaming**

**Issue:** OSH provides WebSocket and MQTT endpoints for real-time streaming, not standard REST.

**Impact:** Client must support streaming protocols for Part 3 features.

**Workaround:**

```typescript
// Detect streaming capabilities
if (client.capabilities.hasWebSocketStreaming) {
  const ws = new WebSocket(`ws://${baseUrl}/datastreams/${id}/observations`);
  ws.onmessage = (event) => {
    const obs = JSON.parse(event.data);
    // Handle real-time observation
  };
}
```

**4. Authentication Required**

**Issue:** OSH requires HTTP Basic Auth for all operations (even GET).

**Impact:** Client must provide credentials.

**Workaround:**

```typescript
const client = new CSAPIClient('http://45.55.99.236:8080/sensorhub/api', {
  auth: {
    type: 'basic',
    username: process.env.OSH_USERNAME || 'ogc',
    password: process.env.OSH_PASSWORD || 'ogc',
  },
});
```

**5. Large Pagination Limits**

**Issue:** OSH supports very large pagination limits (max 10,000 items).

**Impact:** Client can request large batches, but may timeout.

**Workaround:**

```typescript
// Use reasonable default, allow override
const defaultLimit = 100;
const maxLimit = 10000;

async function list(limit: number = defaultLimit): Promise<ResourceCollection> {
  const safeLimit = Math.min(limit, maxLimit);
  return await get(`/systems?limit=${safeLimit}`);
}
```

---

### 3.2 52°North Quirks

**1. Expired SSL Certificate**

**Issue:** Demo server has expired/invalid SSL certificate.

**Impact:** Client requests fail with SSL errors.

**Workaround:**

```typescript
const client = new CSAPIClient('https://csa.demo.52north.org/', {
  ssl: {
    rejectUnauthorized: false, // Only for testing!
  },
});
```

**Production Note:** Do NOT disable SSL validation in production. This is only for testing the 52N demo server.

**2. Incomplete Conformance Declaration**

**Issue:** Server declares only 1 conformance class but actually implements 13+ classes.

**Impact:** Client cannot rely solely on conformance endpoint.

**Workaround:**

```typescript
async function detectCapabilities(
  client: CSAPIClient
): Promise<ServerCapabilities> {
  const conformance = await client.getConformance();

  if (conformance.conformsTo.length < 5) {
    console.warn('Incomplete conformance declaration - probing endpoints');

    // Probe for Part 1 resources
    const probeResults = await Promise.allSettled([
      client.http.get('/systems?limit=1'),
      client.http.get('/deployments?limit=1'),
      client.http.get('/procedures?limit=1'),
      client.http.get('/samplingFeatures?limit=1'),
      client.http.get('/properties?limit=1'),
    ]);

    return {
      hasSystems: probeResults[0].status === 'fulfilled',
      hasDeployments: probeResults[1].status === 'fulfilled',
      hasProcedures: probeResults[2].status === 'fulfilled',
      hasSamplingFeatures: probeResults[3].status === 'fulfilled',
      hasProperties: probeResults[4].status === 'fulfilled',
    };
  }

  // Normal conformance-based detection
  return parseConformance(conformance);
}
```

**3. Part 2 500 Errors**

**Issue:** DataStreams and Observations endpoints return 500 Internal Server Error.

**Impact:** Client must handle Part 2 unavailability gracefully.

**Workaround:**

```typescript
async function initializePart2(client: CSAPIClient): Promise<void> {
  try {
    await client.http.get('/datastreams?limit=1');
    client.capabilities.hasDataStreams = true;
  } catch (error) {
    if (error.status === 500) {
      console.warn(
        'Part 2 not available (500 error) - continuing with Part 1 only'
      );
      client.capabilities.hasDataStreams = false;
    } else {
      throw error; // Other errors are unexpected
    }
  }
}
```

**4. Mixed ID Formats**

**Issue:** 52N uses UUIDs, URNs, and plain strings inconsistently.

**Impact:** Client must accept all ID formats.

**Examples:**

- UUID: `4e09de42-674d-4e03-a620-2d219b030a50`
- URN: `urn:sensor:5400-526`
- String: `YSI599503-00-1`

**Workaround:**

```typescript
// Accept any ID format
function isValidCSAPIId(id: string): boolean {
  return typeof id === 'string' && id.length > 0;
}
```

**5. Small Dataset**

**Issue:** Only 3 systems, 1 deployment available for testing.

**Impact:** Limited test coverage, cannot test large-scale scenarios.

**Workaround:**

- Use 52N for basic connectivity and error handling tests
- Use OSH for comprehensive feature validation
- Use mock fixtures for large-scale scenarios

---

## 4. Test Execution Strategies

> **⚠️ REVIEW NOTICE (Phase 2E — C1, AP2):** This entire section describes a hybrid fixture/live execution model that mirrors the failed attempt's architecture. **Do not implement this.** All tests must use `globalThis.fetch` mocking with deterministic fixtures per upstream conventions. There should be no `test:live` scripts, no nightly CI runs against external servers, no `checkServerAvailability()` gating. The server profile information from Sections 1-3 should inform fixture design, but tests must never make real HTTP requests.

### 4.1 Live Testing (Nightly/Manual)

**When to Use:**

- Real-world interoperability validation
- Catch server behavior changes
- Test with live data patterns
- Manual exploratory testing

**Characteristics:**

- ✅ Real server behavior
- ✅ Real network conditions
- ✅ Catch API changes early
- ⚠️ Network dependency
- ⚠️ Server uptime dependency
- ⚠️ Slower execution
- ⚠️ Data variability

**Implementation:**

```typescript
describe('Live Server Integration Tests', () => {
  // Skip if server unavailable
  beforeAll(async () => {
    const available = await checkServerAvailability(
      'http://45.55.99.236:8080/sensorhub/api'
    );
    if (!available) {
      console.warn('OSH server unavailable - skipping live tests');
      return;
    }
  });

  it('should list live systems', async () => {
    const client = new CSAPIClient('http://45.55.99.236:8080/sensorhub/api', {
      auth: { type: 'basic', username: 'ogc', password: 'ogc' },
    });

    const systems = await client.systems.list({ limit: 10 });

    expect(systems.items.length).toBeGreaterThan(0);
    expect(systems.items[0]).toHaveProperty('id');
    expect(systems.items[0]).toHaveProperty('name');
  });
});
```

**Execution:**

```bash
# Run live tests manually
npm run test:live

# Run live tests nightly (CI/CD)
# .github/workflows/nightly.yml
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
jobs:
  live-tests:
    runs-on: ubuntu-latest
    steps:
      - run: npm run test:live
```

---

### 4.2 Offline Testing (CI/CD)

**When to Use:**

- Continuous integration (every commit)
- Fast, reliable test execution
- No network dependencies
- Deterministic results

**Characteristics:**

- ✅ Fast execution
- ✅ No network dependency
- ✅ No server uptime dependency
- ✅ Deterministic data
- ⚠️ May miss real server changes
- ⚠️ Fixtures may become stale

**Implementation:**

```typescript
describe('Offline Server Compatibility Tests', () => {
  beforeAll(() => {
    // Mock fetch with recorded responses
    globalThis.fetch = jest.fn().mockImplementation((url: string) => {
      if (url.includes('/conformance')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(oshConformanceFixture),
        });
      } else if (url.includes('/systems')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(oshSystemsFixture),
        });
      }
      // ... more fixtures
    });
  });

  it('should handle OpenSensorHub conformance', async () => {
    const client = new CSAPIClient('http://mock-osh-server');
    await client.initialize();

    expect(client.capabilities.hasSystems).toBe(true);
    expect(client.capabilities.hasDataStreams).toBe(true);
    expect(client.capabilities.hasControlStreams).toBe(true);
  });
});
```

**Fixture Recording:**

```typescript
// Record live server responses as fixtures
async function recordFixtures() {
  const servers = [
    { name: 'osh', url: 'http://45.55.99.236:8080/sensorhub/api' },
    { name: '52n', url: 'https://csa.demo.52north.org/' },
  ];

  for (const server of servers) {
    const conformance = await fetch(`${server.url}/conformance`);
    const systems = await fetch(`${server.url}/systems?limit=10`);
    const deployments = await fetch(`${server.url}/deployments?limit=10`);

    // Save fixtures
    await fs.writeFile(
      `fixtures/servers/${server.name}/conformance.json`,
      JSON.stringify(await conformance.json(), null, 2)
    );
    await fs.writeFile(
      `fixtures/servers/${server.name}/systems.json`,
      JSON.stringify(await systems.json(), null, 2)
    );
    await fs.writeFile(
      `fixtures/servers/${server.name}/deployments.json`,
      JSON.stringify(await deployments.json(), null, 2)
    );
  }
}
```

---

### 4.3 Hybrid Approach (Recommended)

**Strategy:**

- **CI/CD (every commit)**: Offline tests with fixtures
- **Nightly (scheduled)**: Live tests against real servers
- **Manual (as needed)**: Exploratory testing, fixture updates

**Benefits:**

- ✅ Fast CI/CD feedback (offline)
- ✅ Real-world validation (nightly live)
- ✅ Fixture staleness detection (nightly)
- ✅ Best of both worlds

**Implementation:**

```bash
# CI/CD (fast)
npm run test:offline

# Nightly (comprehensive)
npm run test:live
npm run test:fixtures:update  # Re-record fixtures if live tests pass

# Manual
npm run test:exploratory
```

---

## 5. Compatibility Test Scenarios

### 5.1 Conformance Detection Tests (~6 tests, 100 lines)

> **✅ REVIEW NOTICE (Phase 2E — C1 supplement):** This section is **client-oriented and should be used during implementation.** The conformance detection test scenarios (COMPAT-CONF-001 through -006) test how the client parses conformance declarations, probes endpoints, and adapts behavior — genuine client code testing. These scenarios complement [Doc 22 (Conformance and Capability Testing)](22-conformance-capability-testing.md) and should be cross-referenced during implementation.

**Priority:** **CRITICAL**

| Test ID         | Scenario                                  | Expected Behavior                                | Lines |
| --------------- | ----------------------------------------- | ------------------------------------------------ | ----- |
| COMPAT-CONF-001 | Detect full conformance (OSH)             | All 33 classes detected, all resources available | 20    |
| COMPAT-CONF-002 | Detect partial conformance (52N)          | Part 1 detected, Part 2 unavailable              | 20    |
| COMPAT-CONF-003 | Handle incomplete conformance declaration | Probe endpoints, detect actual capabilities      | 25    |
| COMPAT-CONF-004 | Handle conformance endpoint failure       | Throw error or probe endpoints                   | 15    |
| COMPAT-CONF-005 | Validate conformance class URIs           | Parse conformance URIs correctly                 | 10    |
| COMPAT-CONF-006 | Cache conformance results                 | Don't re-query conformance on every request      | 10    |

**Test Implementation:**

```typescript
describe('Conformance Detection', () => {
  describe('Full Conformance (OpenSensorHub)', () => {
    it('detects all 33 conformance classes', async () => {
      const client = new CSAPIClient('http://45.55.99.236:8080/sensorhub/api', {
        auth: { type: 'basic', username: 'ogc', password: 'ogc' },
      });

      await client.initialize();

      // Part 1 resources
      expect(client.capabilities.hasSystems).toBe(true);
      expect(client.capabilities.hasDeployments).toBe(true);
      expect(client.capabilities.hasProcedures).toBe(true);
      expect(client.capabilities.hasSamplingFeatures).toBe(true);
      expect(client.capabilities.hasProperties).toBe(true);

      // Part 2 resources
      expect(client.capabilities.hasDataStreams).toBe(true);
      expect(client.capabilities.hasObservations).toBe(true);
      expect(client.capabilities.hasControlStreams).toBe(true);
      expect(client.capabilities.hasCommands).toBe(true);

      // Features
      expect(client.capabilities.hasSubsystems).toBe(true);
      expect(client.capabilities.hasSubdeployments).toBe(true);
      expect(client.capabilities.hasCRUD).toBe(true);
      expect(client.capabilities.hasUpdate).toBe(true);
      expect(client.capabilities.hasAdvancedFiltering).toBe(true);

      // Formats
      expect(client.capabilities.hasGeoJSON).toBe(true);
      expect(client.capabilities.hasSensorML).toBe(true);
      expect(client.capabilities.hasSWEJSON).toBe(true);
    });
  });

  describe('Partial Conformance (52North)', () => {
    it('detects Part 1 only', async () => {
      const client = new CSAPIClient('https://csa.demo.52north.org/', {
        ssl: { rejectUnauthorized: false },
      });

      await client.initialize();

      // Part 1 resources available
      expect(client.capabilities.hasSystems).toBe(true);
      expect(client.capabilities.hasDeployments).toBe(true);
      expect(client.capabilities.hasProcedures).toBe(true);

      // Part 2 resources unavailable
      expect(client.capabilities.hasDataStreams).toBe(false);
      expect(client.capabilities.hasObservations).toBe(false);
      expect(client.capabilities.hasControlStreams).toBe(false);
      expect(client.capabilities.hasCommands).toBe(false);
    });
  });

  describe('Incomplete Conformance Declaration', () => {
    it('probes endpoints when conformance < 5 classes', async () => {
      // Mock 52N incomplete conformance
      globalThis.fetch = jest.fn().mockImplementation((url: string) => {
        if (url.includes('/conformance')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                conformsTo: [
                  'http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core',
                ],
              }),
          });
        } else if (url.includes('/systems')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ items: [], links: [] }),
          });
        } else if (url.includes('/deployments')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ items: [], links: [] }),
          });
        } else {
          return Promise.resolve({ ok: false, status: 404 });
        }
      });

      const client = new CSAPIClient('https://test.csapi.org/');
      await client.initialize();

      // Should probe and detect actual capabilities
      expect(client.capabilities.hasSystems).toBe(true);
      expect(client.capabilities.hasDeployments).toBe(true);
      expect(client.capabilities.hasProcedures).toBe(false); // 404
    });
  });

  describe('Conformance Caching', () => {
    it('caches conformance results', async () => {
      let conformanceRequests = 0;

      globalThis.fetch = jest.fn().mockImplementation((url: string) => {
        if (url.includes('/conformance')) {
          conformanceRequests++;
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(oshConformanceFixture),
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      });

      const client = new CSAPIClient('http://test.csapi.org/');
      await client.initialize();
      await client.systems.list();
      await client.deployments.list();

      // Should only query conformance once
      expect(conformanceRequests).toBe(1);
    });
  });
});
```

---

### 5.2 Full Conformance Tests (OpenSensorHub) (~20 tests, 400-500 lines)

> **⚠️ REVIEW NOTICE (Phase 2E — C1, AP1/AP4/AP5):** The test implementation below connects to a live OpenSensorHub server with hardcoded credentials, conditionally skips via `console.warn('OSH unavailable - skipping tests'); return;`, and asserts server response content (`expect(systems.items.length).toBeGreaterThan(0)`, `expect(system.id).toMatch(/^[a-z0-9]+$/)`, `expect(ds).toHaveProperty('observedProperty')`). These all test server behavior, not client code. **Do not implement as written.** Instead, use the test scenario IDs (COMPAT-OSH-001 through -020) as inspiration for fixture-based client tests: mock fetch → call client methods → assert client's parsed outputs, constructed URLs, and set capability flags.

**Priority:** **HIGH**

| Test ID        | Scenario                                | Expected Behavior                   | Lines |
| -------------- | --------------------------------------- | ----------------------------------- | ----- |
| COMPAT-OSH-001 | List systems with pagination            | Returns paginated systems           | 20    |
| COMPAT-OSH-002 | Get single system by ID                 | Returns system with metadata        | 20    |
| COMPAT-OSH-003 | Query systems with filters              | Returns filtered systems            | 25    |
| COMPAT-OSH-004 | List deployments                        | Returns deployments                 | 20    |
| COMPAT-OSH-005 | List procedures                         | Returns procedures                  | 20    |
| COMPAT-OSH-006 | List sampling features                  | Returns sampling features           | 20    |
| COMPAT-OSH-007 | List properties                         | Returns properties                  | 20    |
| COMPAT-OSH-008 | Navigate subsystems hierarchy           | Returns subsystems                  | 25    |
| COMPAT-OSH-009 | Navigate subdeployments hierarchy       | Returns subdeployments              | 25    |
| COMPAT-OSH-010 | List datastreams                        | Returns datastreams                 | 20    |
| COMPAT-OSH-011 | Query observations                      | Returns observations                | 25    |
| COMPAT-OSH-012 | Query observations with temporal filter | Returns filtered observations       | 30    |
| COMPAT-OSH-013 | Test HTTP Basic Auth                    | Authentication successful           | 20    |
| COMPAT-OSH-014 | Test multiple formats                   | GeoJSON, SensorML, SWE formats work | 30    |
| COMPAT-OSH-015 | Test advanced filtering                 | CQL2 queries work                   | 25    |
| COMPAT-OSH-016 | Test large pagination                   | Pagination up to 10,000 items       | 20    |
| COMPAT-OSH-017 | Cross-resource navigation               | System → DataStreams → Observations | 30    |
| COMPAT-OSH-018 | Live streaming check                    | WebSocket endpoint available        | 20    |
| COMPAT-OSH-019 | Test control streams                    | ControlStreams available            | 20    |
| COMPAT-OSH-020 | Test commands                           | Commands available                  | 20    |

**Sample Test Implementation:**

```typescript
describe('OpenSensorHub Full Conformance', () => {
  let client: CSAPIClient;

  beforeAll(async () => {
    const available = await checkServerAvailability(
      'http://45.55.99.236:8080/sensorhub/api'
    );
    if (!available) {
      console.warn('OSH unavailable - skipping tests');
      return;
    }

    client = new CSAPIClient('http://45.55.99.236:8080/sensorhub/api', {
      auth: { type: 'basic', username: 'ogc', password: 'ogc' },
    });
    await client.initialize();
  });

  describe('Part 1 Resources', () => {
    it('lists systems with pagination', async () => {
      const systems = await client.systems.list({ limit: 5 });

      expect(systems.items).toBeDefined();
      expect(systems.items.length).toBeGreaterThan(0);
      expect(systems.items.length).toBeLessThanOrEqual(5);
      expect(systems.links).toBeDefined();

      // Validate system structure
      const system = systems.items[0];
      expect(system.id).toMatch(/^[a-z0-9]+$/); // Base32 format
      expect(system.name).toBeDefined();
      expect(system.description).toBeDefined();
    });

    it('gets single system by ID', async () => {
      const systems = await client.systems.list({ limit: 1 });
      const systemId = systems.items[0].id;

      const system = await client.systems.get(systemId);

      expect(system.id).toBe(systemId);
      expect(system.name).toBeDefined();
      expect(system).toHaveProperty('properties');
    });

    it('queries systems with keyword filter', async () => {
      const systems = await client.systems.list({ q: 'drone' });

      expect(systems.items).toBeDefined();
      systems.items.forEach((sys) => {
        expect(
          sys.name.toLowerCase().includes('drone') ||
            sys.description?.toLowerCase().includes('drone')
        ).toBe(true);
      });
    });

    it('navigates subsystems hierarchy', async () => {
      const systems = await client.systems.list({ limit: 10 });

      // Find system with subsystems
      let parentSystem;
      for (const sys of systems.items) {
        const subsystems = await client.systems.subsystems(sys.id).list();
        if (subsystems.items.length > 0) {
          parentSystem = sys;
          break;
        }
      }

      if (parentSystem) {
        const subsystems = await client.systems
          .subsystems(parentSystem.id)
          .list();
        expect(subsystems.items.length).toBeGreaterThan(0);
        expect(subsystems.items[0]).toHaveProperty('id');
      }
    });
  });

  describe('Part 2 Resources', () => {
    it('lists datastreams', async () => {
      const datastreams = await client.datastreams.list({ limit: 5 });

      expect(datastreams.items).toBeDefined();
      expect(datastreams.items.length).toBeGreaterThan(0);

      const ds = datastreams.items[0];
      expect(ds.id).toBeDefined();
      expect(ds.name).toBeDefined();
      expect(ds).toHaveProperty('observedProperty');
    });

    it('queries observations with temporal filter', async () => {
      // Get a datastream
      const datastreams = await client.datastreams.list({ limit: 1 });
      const datastreamId = datastreams.items[0].id;

      // Query observations from last 24 hours
      const oneDayAgo = new Date(
        Date.now() - 24 * 60 * 60 * 1000
      ).toISOString();
      const now = new Date().toISOString();

      const observations = await client.datastreams
        .observations(datastreamId)
        .list({
          phenomenonTime: `${oneDayAgo}/${now}`,
          limit: 10,
        });

      expect(observations.items).toBeDefined();
      observations.items.forEach((obs) => {
        expect(obs).toHaveProperty('phenomenonTime');
        expect(obs).toHaveProperty('result');
      });
    });

    it('tests control streams availability', async () => {
      const controlstreams = await client.controlstreams.list({ limit: 1 });

      expect(controlstreams).toBeDefined();
      // May be empty if no control streams defined
    });
  });

  describe('Advanced Features', () => {
    it('tests HTTP Basic Auth', async () => {
      // Should have authenticated successfully in beforeAll
      const systems = await client.systems.list({ limit: 1 });
      expect(systems.items.length).toBeGreaterThan(0);
    });

    it('tests multiple format support', async () => {
      const systemsGeoJSON = await client.systems.list({
        f: 'geojson',
        limit: 1,
      });
      expect(systemsGeoJSON.type).toBe('FeatureCollection');

      const systemsSensorML = await client.systems.list({
        f: 'sml+json',
        limit: 1,
      });
      expect(systemsSensorML).toHaveProperty('items');
    });

    it('cross-navigates System → DataStreams → Observations', async () => {
      // Get a system
      const systems = await client.systems.list({ limit: 1 });
      const systemId = systems.items[0].id;

      // Get its datastreams
      const datastreams = await client.systems.datastreams(systemId).list();
      if (datastreams.items.length === 0) {
        console.warn('No datastreams for system - skipping');
        return;
      }

      const datastreamId = datastreams.items[0].id;

      // Get observations from that datastream
      const observations = await client.datastreams
        .observations(datastreamId)
        .list({
          limit: 5,
        });

      expect(observations.items).toBeDefined();
    });
  });
});
```

---

### 5.3 Partial Conformance Tests (52°North) (~15 tests, 300-400 lines)

> **⚠️ REVIEW NOTICE (Phase 2E — C1, AP1/AP4):** Same issues as Section 5.2. These tests connect to a live 52°North server, assert server response content (`expect(deployment.geometry.coordinates).toHaveLength(2)`, `expect(lon).toBeCloseTo(14.03, 0)` — specific Baltic Sea coordinates), and validate server data shapes (`expect(sys.id)` UUID/URN format checks). The partial conformance _scenarios_ are valuable — they describe how the client should handle missing ControlStreams and incomplete Part 2 — but must be rewritten as fixture-based client behavior tests. See Section 5.5 for the correct approach.

**Priority:** **HIGH**

| Test ID        | Scenario                          | Expected Behavior                     | Lines |
| -------------- | --------------------------------- | ------------------------------------- | ----- |
| COMPAT-52N-001 | Detect incomplete conformance     | Probe endpoints successfully          | 25    |
| COMPAT-52N-002 | List systems                      | Returns 3 systems                     | 20    |
| COMPAT-52N-003 | Get single system                 | Returns system metadata               | 20    |
| COMPAT-52N-004 | List deployments                  | Returns 1 deployment                  | 20    |
| COMPAT-52N-005 | Get single deployment             | Returns deployment with location      | 25    |
| COMPAT-52N-006 | List procedures                   | Returns 1 procedure                   | 20    |
| COMPAT-52N-007 | Handle SSL certificate issues     | Bypass certificate validation         | 15    |
| COMPAT-52N-008 | Test Part 2 unavailability        | DataStreams return 500 or unavailable | 25    |
| COMPAT-52N-009 | Graceful Part 2 degradation       | Client continues with Part 1 only     | 25    |
| COMPAT-52N-010 | Handle mixed ID formats           | Accept UUIDs, URNs, strings           | 20    |
| COMPAT-52N-011 | Test oceanographic metadata       | Validate real-world deployment data   | 30    |
| COMPAT-52N-012 | Navigate deployment systems       | Query deployed systems                | 25    |
| COMPAT-52N-013 | Test external documentation links | Validate PDF links                    | 20    |
| COMPAT-52N-014 | Handle small dataset              | Test with limited data (3 systems)    | 20    |
| COMPAT-52N-015 | Validate GeoJSON coordinates      | WGS84 format correct                  | 20    |

**Sample Test Implementation:**

```typescript
describe('52North Partial Conformance', () => {
  let client: CSAPIClient;

  beforeAll(async () => {
    const available = await checkServerAvailability(
      'https://csa.demo.52north.org/'
    );
    if (!available) {
      console.warn('52N unavailable - skipping tests');
      return;
    }

    client = new CSAPIClient('https://csa.demo.52north.org/', {
      ssl: { rejectUnauthorized: false }, // Skip cert validation
    });
    await client.initialize();
  });

  describe('Conformance Detection', () => {
    it('detects incomplete conformance and probes endpoints', async () => {
      const conformance = await client.getConformance();

      // 52N declares only 1 class
      expect(conformance.conformsTo.length).toBeLessThan(5);

      // But resources are available (detected via probing)
      expect(client.capabilities.hasSystems).toBe(true);
      expect(client.capabilities.hasDeployments).toBe(true);
      expect(client.capabilities.hasProcedures).toBe(true);
    });
  });

  describe('Part 1 Resources', () => {
    it('lists systems', async () => {
      const systems = await client.systems.list();

      expect(systems.items).toBeDefined();
      expect(systems.items.length).toBe(3); // Known dataset size

      // Validate oceanographic sensors
      const systemNames = systems.items.map((s) => s.name);
      expect(
        systemNames.some(
          (name) =>
            name.includes('YSI') ||
            name.includes('Valeport') ||
            name.includes('RBR')
        )
      ).toBe(true);
    });

    it('gets deployment with location', async () => {
      const deployments = await client.deployments.list();
      expect(deployments.items.length).toBeGreaterThan(0);

      const deployment = deployments.items[0];
      expect(deployment).toHaveProperty('geometry');
      expect(deployment.geometry.type).toBe('Point');
      expect(deployment.geometry.coordinates).toHaveLength(2); // [lon, lat]

      // Baltic Sea coordinates
      const [lon, lat] = deployment.geometry.coordinates;
      expect(lon).toBeCloseTo(14.03, 0); // ~14° E
      expect(lat).toBeCloseTo(54.33, 0); // ~54° N
    });

    it('handles mixed ID formats', async () => {
      const systems = await client.systems.list();

      systems.items.forEach((sys) => {
        // Accept any ID format
        expect(typeof sys.id).toBe('string');
        expect(sys.id.length).toBeGreaterThan(0);

        // May be UUID, URN, or plain string
        const isUUID = /^[0-9a-f-]{36}$/i.test(sys.id);
        const isURN = sys.id.startsWith('urn:');
        const isString = !isUUID && !isURN;

        expect(isUUID || isURN || isString).toBe(true);
      });
    });
  });

  describe('Part 2 Unavailability', () => {
    it('handles DataStreams 500 error gracefully', async () => {
      // Attempt to list datastreams
      try {
        await client.datastreams.list();
        // If successful, Part 2 is now working (future)
        expect(true).toBe(true);
      } catch (error) {
        // Expected: 500 error or ConformanceError
        if (error.status === 500) {
          console.warn('Part 2 not available (500 error) - expected');
          expect(error.status).toBe(500);
        } else if (error instanceof ConformanceError) {
          console.warn('Part 2 not declared in conformance - expected');
          expect(error.capability).toMatch(/datastream/i);
        } else {
          throw error; // Unexpected error
        }
      }
    });

    it('continues with Part 1 after Part 2 failure', async () => {
      // Even if Part 2 fails, Part 1 should still work
      const systems = await client.systems.list();
      expect(systems.items.length).toBeGreaterThan(0);

      const deployments = await client.deployments.list();
      expect(deployments.items.length).toBeGreaterThan(0);
    });
  });

  describe('Real-World Data Validation', () => {
    it('validates oceanographic deployment metadata', async () => {
      const deployments = await client.deployments.list();
      const deployment = deployments.items[0];

      // Validate deployment metadata
      expect(deployment.name).toBeDefined();
      expect(deployment).toHaveProperty('deployedSystems');
      expect(Array.isArray(deployment.deployedSystems)).toBe(true);

      // Validate location (Baltic Sea)
      expect(deployment.geometry).toBeDefined();
      expect(deployment.geometry.type).toBe('Point');
    });

    it('validates external documentation links', async () => {
      const procedures = await client.procedures.list();
      if (procedures.items.length > 0) {
        const procedure = procedures.items[0];

        // May have external documentation links
        if (procedure.documentation) {
          procedure.documentation.forEach((doc) => {
            expect(doc).toHaveProperty('href');
            expect(doc.href).toMatch(/^https?:\/\//); // Valid URL
          });
        }
      }
    });
  });

  describe('SSL Certificate Handling', () => {
    it('bypasses invalid certificate', async () => {
      // Should have succeeded in beforeAll with rejectUnauthorized: false
      const systems = await client.systems.list();
      expect(systems.items.length).toBeGreaterThan(0);
    });
  });
});
```

---

### 5.4 Server Availability Tests (~5 tests, 100 lines)

> **⚠️ REVIEW NOTICE (Phase 2E — C1, AP2/AP5):** Server availability checking is the hallmark of a server conformance test suite, not a client library test suite. In client tests, the "server" is a mocked fetch that always returns deterministic fixtures — it is never "unavailable." The `checkServerAvailability()` function, `console.warn('...skipping')` pattern, and `expect(typeof available).toBe('boolean')` assertion all test server infrastructure, not client code. **Do not implement.** If the client needs to handle unreachable servers, test that through mocked fetch that simulates network errors — which is already covered by error handling tests (Doc 18).

**Priority:** **CRITICAL**

| Test ID          | Scenario                         | Expected Behavior        | Lines |
| ---------------- | -------------------------------- | ------------------------ | ----- |
| COMPAT-AVAIL-001 | Check server reachability        | HTTP request succeeds    | 20    |
| COMPAT-AVAIL-002 | Check conformance endpoint       | /conformance returns 200 | 20    |
| COMPAT-AVAIL-003 | Handle server timeout            | Throw timeout error      | 20    |
| COMPAT-AVAIL-004 | Handle server 500 error          | Throw server error       | 20    |
| COMPAT-AVAIL-005 | Skip tests if server unavailable | Tests skipped gracefully | 20    |

**Test Implementation:**

```typescript
describe('Server Availability', () => {
  async function checkServerAvailability(
    url: string,
    timeout: number = 5000
  ): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(`${url}/conformance`, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  it('checks OpenSensorHub availability', async () => {
    const available = await checkServerAvailability(
      'http://45.55.99.236:8080/sensorhub/api'
    );

    if (!available) {
      console.warn('OSH server unavailable - tests will be skipped');
    }

    // Don't fail test if server unavailable
    expect(typeof available).toBe('boolean');
  });

  it('checks 52North availability', async () => {
    const available = await checkServerAvailability(
      'https://csa.demo.52north.org/'
    );

    if (!available) {
      console.warn('52N server unavailable - tests will be skipped');
    }

    expect(typeof available).toBe('boolean');
  });

  it('handles server timeout', async () => {
    const available = await checkServerAvailability(
      'http://slow.example.com',
      1000
    );
    expect(available).toBe(false);
  });

  it('handles server 500 error', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    const available = await checkServerAvailability('http://error.example.com');
    expect(available).toBe(false);
  });

  describe('Test Skipping', () => {
    it('skips tests when server unavailable', async () => {
      const available = await checkServerAvailability(
        'http://unavailable.example.com'
      );

      if (!available) {
        console.warn('Server unavailable - skipping test suite');
        return; // Skip remaining tests
      }

      // Run tests only if available
      const client = new CSAPIClient('http://unavailable.example.com');
      await client.initialize();
    });
  });
});
```

---

### 5.5 Graceful Degradation Tests (~10 tests, 200-250 lines)

> **✅ REVIEW NOTICE (Phase 2E — C1 supplement):** This section is the **strongest content in this document** and demonstrates the correct testing approach: `globalThis.fetch` is mocked with fixture data, assertions target client behavior (`client.datastreams` is null, CRUD throws `ConformanceError`), and no live server connections are used. These graceful degradation scenarios supplement [Doc 22 (Conformance and Capability Testing)](22-conformance-capability-testing.md) Section 5 and should be cross-referenced during implementation.

**Priority:** **MEDIUM**

| Test ID            | Scenario                  | Expected Behavior                 | Lines |
| ------------------ | ------------------------- | --------------------------------- | ----- |
| COMPAT-DEGRADE-001 | Part 2 unavailable        | Client works in Part 1-only mode  | 25    |
| COMPAT-DEGRADE-002 | No CRUD conformance       | Create/update/delete throw errors | 25    |
| COMPAT-DEGRADE-003 | No subsystems conformance | Subsystems method unavailable     | 20    |
| COMPAT-DEGRADE-004 | No advanced filtering     | Complex queries throw errors      | 25    |
| COMPAT-DEGRADE-005 | No SensorML format        | SensorML requests throw errors    | 20    |
| COMPAT-DEGRADE-006 | Single resource type      | Only systems available            | 25    |
| COMPAT-DEGRADE-007 | Read-only server          | All writes throw errors           | 25    |
| COMPAT-DEGRADE-008 | Missing nested resources  | Nested methods return null        | 20    |
| COMPAT-DEGRADE-009 | Partial format support    | Fallback to JSON                  | 20    |
| COMPAT-DEGRADE-010 | Feature detection caching | Don't re-probe on every request   | 15    |

**Sample Test Implementation:**

```typescript
describe('Graceful Degradation', () => {
  describe('Part 2 Unavailable', () => {
    it('works in Part 1-only mode', async () => {
      // Mock partial conformance
      globalThis.fetch = jest.fn().mockImplementation((url: string) => {
        if (url.includes('/conformance')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                conformsTo: [
                  'http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core',
                  'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common',
                  'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system',
                ],
              }),
          });
        } else if (url.includes('/systems')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ items: [], links: [] }),
          });
        } else if (url.includes('/datastreams')) {
          return Promise.resolve({ ok: false, status: 404 });
        }
      });

      const client = new CSAPIClient('http://test.csapi.org/');
      await client.initialize();

      // Part 1 available
      expect(client.systems).toBeDefined();
      await client.systems.list();

      // Part 2 unavailable
      expect(client.datastreams).toBeNull();

      try {
        await client.datastreams.list();
      } catch (error) {
        expect(error).toBeInstanceOf(ConformanceError);
      }
    });
  });

  describe('No CRUD Conformance', () => {
    it('throws errors on create/update/delete', async () => {
      globalThis.fetch = jest.fn().mockImplementation((url: string) => {
        if (url.includes('/conformance')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                conformsTo: [
                  'http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core',
                  'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common',
                  'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system',
                  // No create-replace-delete conformance
                ],
              }),
          });
        } else if (url.includes('/systems')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ items: [], links: [] }),
          });
        }
      });

      const client = new CSAPIClient('http://test.csapi.org/');
      await client.initialize();

      expect(client.capabilities.hasCRUD).toBe(false);

      // GET works
      await client.systems.list();

      // POST throws error
      await expect(client.systems.create({ name: 'Test' })).rejects.toThrow(
        ConformanceError
      );

      // PUT throws error
      await expect(
        client.systems.replace('sys-123', { name: 'Test' })
      ).rejects.toThrow(ConformanceError);

      // DELETE throws error
      await expect(client.systems.delete('sys-123')).rejects.toThrow(
        ConformanceError
      );
    });
  });

  describe('Format Fallback', () => {
    it('falls back to JSON when SensorML unavailable', async () => {
      const client = new CSAPIClient('http://test.csapi.org/');
      client.capabilities.hasSensorML = false;
      client.capabilities.hasGeoJSON = true;

      // Request SensorML but get GeoJSON
      const systems = await client.systems.list({ f: 'sml+json' });

      // Should fallback to GeoJSON
      expect(systems.type).toBe('FeatureCollection');
    });
  });
});
```

---

## 6. Test Infrastructure Design

> **⚠️ REVIEW NOTICE (Phase 2E — C1, AP2):** This entire section designs infrastructure for live server testing: `ServerConfig` with hardcoded URLs and credentials (`username: 'ogc', password: 'ogc'`), `checkServerAvailability()` with console.warn skipping, fixture recording utilities that connect to live servers, and dual jest projects (`*.offline.spec.ts` / `*.live.spec.ts`). **Do not implement any of this.** The upstream test infrastructure is simple: `globalThis.fetch` mock in `beforeEach`, fixture files as static JSON, single jest configuration. No server configs, no availability checkers, no recording utilities needed.

### 6.1 Server Configuration

```typescript
// test/config/servers.ts

export interface ServerConfig {
  name: string;
  url: string;
  profile: 'full' | 'partial' | 'minimal';
  auth?: {
    type: 'basic' | 'bearer';
    username?: string;
    password?: string;
    token?: string;
  };
  ssl?: {
    rejectUnauthorized: boolean;
  };
  quirks?: string[];
}

export const TEST_SERVERS: ServerConfig[] = [
  {
    name: 'OpenSensorHub',
    url: 'http://45.55.99.236:8080/sensorhub/api',
    profile: 'full',
    auth: {
      type: 'basic',
      username: process.env.OSH_USERNAME || 'ogc',
      password: process.env.OSH_PASSWORD || 'ogc',
    },
    quirks: ['base32-ids', 'async-servlet', 'websocket-streaming'],
  },
  {
    name: '52North',
    url: 'https://csa.demo.52north.org/',
    profile: 'partial',
    ssl: {
      rejectUnauthorized: false,
    },
    quirks: [
      'expired-ssl',
      'incomplete-conformance',
      'part2-500-errors',
      'mixed-id-formats',
    ],
  },
];
```

### 6.2 Server Availability Checker

```typescript
// test/utils/server-availability.ts

export async function checkServerAvailability(
  url: string,
  timeout: number = 5000
): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(`${url}/conformance`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    return false;
  }
}

export async function checkAllServersAvailability(): Promise<
  Map<string, boolean>
> {
  const availability = new Map<string, boolean>();

  for (const server of TEST_SERVERS) {
    const available = await checkServerAvailability(server.url);
    availability.set(server.name, available);

    if (!available) {
      console.warn(`Server ${server.name} unavailable - tests will be skipped`);
    }
  }

  return availability;
}
```

### 6.3 Fixture Recording

```typescript
// test/utils/fixture-recorder.ts

export async function recordServerFixtures(
  server: ServerConfig,
  outputDir: string
): Promise<void> {
  const client = new CSAPIClient(server.url, {
    auth: server.auth,
    ssl: server.ssl,
  });

  await client.initialize();

  // Record conformance
  const conformance = await client.getConformance();
  await fs.writeFile(
    path.join(outputDir, server.name, 'conformance.json'),
    JSON.stringify(conformance, null, 2)
  );

  // Record systems (first page)
  const systems = await client.systems.list({ limit: 10 });
  await fs.writeFile(
    path.join(outputDir, server.name, 'systems.json'),
    JSON.stringify(systems, null, 2)
  );

  // Record deployments
  if (client.capabilities.hasDeployments) {
    const deployments = await client.deployments.list({ limit: 10 });
    await fs.writeFile(
      path.join(outputDir, server.name, 'deployments.json'),
      JSON.stringify(deployments, null, 2)
    );
  }

  // Record datastreams
  if (client.capabilities.hasDataStreams) {
    try {
      const datastreams = await client.datastreams.list({ limit: 10 });
      await fs.writeFile(
        path.join(outputDir, server.name, 'datastreams.json'),
        JSON.stringify(datastreams, null, 2)
      );
    } catch (error) {
      console.warn(
        `DataStreams unavailable for ${server.name}: ${error.message}`
      );
    }
  }

  console.log(`Fixtures recorded for ${server.name}`);
}
```

### 6.4 Test Execution Modes

```typescript
// jest.config.js

module.exports = {
  projects: [
    {
      displayName: 'offline',
      testMatch: ['**/*.offline.spec.ts'],
      testEnvironment: 'node',
    },
    {
      displayName: 'live',
      testMatch: ['**/*.live.spec.ts'],
      testEnvironment: 'node',
      testTimeout: 30000, // Longer timeout for live tests
    },
  ],
};
```

```bash
# Package.json scripts
{
  "scripts": {
    "test:offline": "jest --selectProjects offline",
    "test:live": "jest --selectProjects live",
    "test:compat": "jest --testPathPattern=compatibility",
    "test:fixtures:record": "ts-node test/utils/record-fixtures.ts"
  }
}
```

---

## 7. Rate Limiting and Throttling

> **⚠️ REVIEW NOTICE (Phase 2E — C1, AP2):** Rate limiting and throttling are concerns for live server testing, which is not part of the client library test suite. Mocked fetch responses are instantaneous and unlimited. **Do not implement.**

### 7.1 Rate Limiting Considerations

**OpenSensorHub:**

- Unknown rate limits (assumed generous for public demo)
- Shared server - be considerate
- Avoid excessive write operations

**52°North:**

- Unknown rate limits
- Development server - may be more restrictive

**Best Practices:**

- Limit concurrent requests (max 5-10)
- Add delays between requests (100-200ms)
- Use pagination to reduce request count
- Cache responses when possible

### 7.2 Throttling Implementation

```typescript
// test/utils/throttle.ts

export class RequestThrottler {
  private queue: Array<() => Promise<any>> = [];
  private activeRequests = 0;
  private maxConcurrent: number;
  private minDelay: number;

  constructor(maxConcurrent: number = 5, minDelayMs: number = 100) {
    this.maxConcurrent = maxConcurrent;
    this.minDelay = minDelayMs;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    while (this.activeRequests >= this.maxConcurrent) {
      await this.waitForSlot();
    }

    this.activeRequests++;

    try {
      const result = await fn();
      await this.delay();
      return result;
    } finally {
      this.activeRequests--;
    }
  }

  private async waitForSlot(): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, 50));
  }

  private async delay(): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, this.minDelay));
  }
}

// Usage
const throttler = new RequestThrottler(5, 100);

const systems = await throttler.execute(() => client.systems.list());
const deployments = await throttler.execute(() => client.deployments.list());
```

---

## 8. Implementation Estimates

### 8.1 Test Implementation Summary

| Test Category             | Test Count | Lines per Test | Total Lines   | Priority     |
| ------------------------- | ---------- | -------------- | ------------- | ------------ |
| Conformance Detection     | 6          | 15-20          | 100           | **CRITICAL** |
| Full Conformance (OSH)    | 20         | 20-25          | 400-500       | **HIGH**     |
| Partial Conformance (52N) | 15         | 20-27          | 300-400       | **HIGH**     |
| Server Availability       | 5          | 20             | 100           | **CRITICAL** |
| Graceful Degradation      | 10         | 15-25          | 200-250       | **MEDIUM**   |
| **TOTAL**                 | **56**     | **~22 avg**    | **1100-1400** |              |

### 8.2 Infrastructure Implementation

| Component            | Lines       | Priority     |
| -------------------- | ----------- | ------------ |
| Server Configuration | 50-75       | **CRITICAL** |
| Availability Checker | 50-75       | **CRITICAL** |
| Fixture Recorder     | 100-150     | **HIGH**     |
| Request Throttler    | 50-75       | **MEDIUM**   |
| Test Utilities       | 100-150     | **MEDIUM**   |
| **TOTAL**            | **350-525** |              |

### 8.3 Fixture Requirements

| Fixture Category | Count     | Priority     |
| ---------------- | --------- | ------------ |
| OSH Conformance  | 1         | **CRITICAL** |
| OSH Systems      | 1         | **HIGH**     |
| OSH Deployments  | 1         | **HIGH**     |
| OSH DataStreams  | 1         | **HIGH**     |
| OSH Observations | 1         | **HIGH**     |
| 52N Conformance  | 1         | **CRITICAL** |
| 52N Systems      | 1         | **HIGH**     |
| 52N Deployments  | 1         | **HIGH**     |
| Error Responses  | 5-10      | **MEDIUM**   |
| **TOTAL**        | **13-18** |              |

### 8.4 Total Implementation Effort

| Component           | Lines               | Priority          | Estimated Time  |
| ------------------- | ------------------- | ----------------- | --------------- |
| Test Implementation | 1100-1400           | **CRITICAL/HIGH** | 20-28 hours     |
| Infrastructure      | 350-525             | **CRITICAL/HIGH** | 6-10 hours      |
| Fixtures            | 13-18 files         | **CRITICAL/HIGH** | 3-5 hours       |
| Documentation       | 100-150             | **MEDIUM**        | 2-3 hours       |
| **TOTAL**           | **1550-2075 lines** |                   | **31-46 hours** |

---

## 9. Testing Priorities

### Priority 1: CRITICAL (Must Have)

**What:** Conformance detection, server availability checking

**Why:** Without these, cannot test against live servers at all

**Tests:** 11 tests, ~200 lines

**Deliverables:**

- Server availability checker
- Conformance detection tests
- Server configuration infrastructure

### Priority 2: HIGH (Should Have)

**What:** Full and partial conformance test suites

**Why:** Core validation against real servers

**Tests:** 35 tests, ~700-900 lines

**Deliverables:**

- OpenSensorHub full conformance tests
- 52°North partial conformance tests
- Fixture recording utilities

### Priority 3: MEDIUM (Nice to Have)

**What:** Graceful degradation, advanced features

**Why:** Edge cases and resilience testing

**Tests:** 10 tests, ~200-250 lines

**Deliverables:**

- Graceful degradation tests
- Request throttling
- Advanced test utilities

---

## 10. Key Testing Challenges and Mitigations

### Challenge 1: Live Server Dependencies

**Problem:** Tests depend on external servers that may be unavailable or slow.

**Mitigation:**

- Implement server availability checks before tests
- Skip tests gracefully if server unavailable
- Run live tests nightly or manually, not in CI
- Record fixtures for offline testing

### Challenge 2: Data Variability

**Problem:** Live data changes over time, tests may become inconsistent.

**Mitigation:**

- Don't assert exact values (counts, IDs)
- Assert patterns and structures instead
- Use relative time queries (last 24 hours, not absolute dates)
- Document expected data ranges

### Challenge 3: Authentication Management

**Problem:** OSH requires credentials, must not commit to repo.

**Mitigation:**

- Use environment variables for credentials
- Provide default test credentials (public demo server)
- Document credential setup in README
- Consider OAuth2 for future servers

### Challenge 4: SSL Certificate Issues

**Problem:** 52N has expired certificate, requires bypass.

**Mitigation:**

- Allow SSL validation bypass for specific test servers only
- Document security implications
- Never disable SSL in production code
- Monitor 52N for certificate renewal

### Challenge 5: Rate Limiting

**Problem:** Unknown rate limits, may hit limits during tests.

**Mitigation:**

- Implement request throttling (max 5-10 concurrent)
- Add delays between requests (100-200ms)
- Use pagination to reduce request count
- Monitor for 429 Too Many Requests errors

---

## 11. References

### 11.1 Server Documentation

**OpenSensorHub:**

- Repository: https://github.com/opensensorhub/osh-core
- Documentation: https://github.com/opensensorhub/osh-core/wiki
- Live Server: http://45.55.99.236:8080/sensorhub/api
- Authentication: HTTP Basic Auth (username: ogc, password: ogc)

**52°North:**

- Repository: https://github.com/52North/connected-systems-pygeoapi
- Documentation: https://52north.github.io/connected-systems-pygeoapi/
- Live Server: https://csa.demo.52north.org/
- Authentication: None (public access)

### 11.2 Related Research

- **Section 22**: Conformance and Capability Testing (conformance detection patterns)
- **Section 8**: CSAPI Specification Review (conformance class definitions)
- **OpenSensorHub Analysis**: Complete server implementation analysis
- **52°North Analysis**: Partial conformance server analysis
- **Conformance Capabilities**: Complete conformance class catalog

---

## 12. Appendices

### Appendix A: Server Comparison Matrix

| Feature             | OpenSensorHub     | 52°North                     | Difference              |
| ------------------- | ----------------- | ---------------------------- | ----------------------- |
| **Language**        | Java              | Python                       | Implementation approach |
| **Framework**       | Spring Boot       | Quart/pygeoapi               | Web framework           |
| **Conformance**     | 33 classes (100%) | ~15-18 classes (Part 1 only) | **Major difference**    |
| **Part 1**          | Full              | Full                         | Same                    |
| **Part 2**          | Full              | Partial (DataStreams only)   | **Major difference**    |
| **Part 3**          | Full              | None                         | **Major difference**    |
| **Systems**         | 6 live            | 3 static                     | OSH more data           |
| **Deployments**     | 3                 | 1                            | OSH more data           |
| **DataStreams**     | 28 live           | 0 (500 errors)               | **Major difference**    |
| **Observations**    | Thousands         | 0 (500 errors)               | **Major difference**    |
| **ID Format**       | Base32 strings    | UUIDs/URNs/strings           | Different formats       |
| **Authentication**  | HTTP Basic Auth   | None                         | OSH secured             |
| **SSL Certificate** | Valid             | Expired                      | 52N requires bypass     |
| **Streaming**       | WebSocket/MQTT    | None                         | **Major difference**    |
| **Use Case**        | Drones, mobile    | Oceanographic buoys          | Different domains       |
| **Maturity**        | Production        | Development                  | **Major difference**    |

### Appendix B: Quirk Catalog

**OpenSensorHub Quirks:**

1. Base32-encoded IDs (not UUIDs)
2. Async servlet architecture (may return 202 Accepted)
3. WebSocket/MQTT streaming (non-REST)
4. HTTP Basic Auth required
5. Large pagination limits (max 10,000)

**52°North Quirks:**

1. Expired SSL certificate (requires bypass)
2. Incomplete conformance declaration (only 1 class declared)
3. Part 2 500 errors (DataStreams/Observations unavailable)
4. Mixed ID formats (UUIDs, URNs, strings)
5. Small dataset (3 systems, 1 deployment)

### Appendix C: Expected Live Data

**OpenSensorHub (as of Feb 2026):**

- **Systems**: 6 (DJI Matrice drones, Android phones)
- **Deployments**: 3 (drone missions)
- **DataStreams**: 28 (location, velocity, acceleration, attitude, IMU, GPS, health)
- **Observations**: Thousands (historical from 2023-2024, live streaming)

**52°North (as of Feb 2026):**

- **Systems**: 3 (YSI 5400-526 sensor, Valeport 5300-909 CTD, RBR platform)
- **Deployments**: 1 (Baltic Sea buoy testing, coordinates ~14.03°E, 54.33°N)
- **Procedures**: 1 (Aanderaa DCPS TD304 sensor type)
- **DataStreams**: 0 (inaccessible, 500 errors)
- **Observations**: 0 (inaccessible, 500 errors)

---

**END OF DOCUMENT**
