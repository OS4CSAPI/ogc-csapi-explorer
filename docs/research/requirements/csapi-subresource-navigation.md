# Section 6: Sub-Resource Navigation Requirements

## Overview

This section documents all sub-resource (nested) navigation patterns in CSAPI Part 1 and Part 2, including relationship endpoints, nesting depth, query parameter support, link relations, canonical vs relationship URLs, and client library navigation patterns. Understanding sub-resource navigation is critical for building intuitive client APIs that model parent-child and associative relationships.

**Key Objectives:**

- Document all sub-resource relationship endpoints
- Define nesting depth and hierarchy patterns
- Specify query parameter support for sub-resources
- Document canonical vs relationship URL patterns
- Define bidirectional relationship navigation
- Establish link relation types and usage
- Define client API navigation patterns

---

## Sub-Resource Relationship Matrix

### Part 1: Core Resources

| Parent Resource | Sub-Resource            | Endpoint Pattern                   | Relationship Type | Nesting Depth | Recursive Support |
| --------------- | ----------------------- | ---------------------------------- | ----------------- | ------------- | ----------------- |
| System          | Subsystems              | `/systems/{id}/subsystems`         | Hierarchical      | Unlimited     | Yes               |
| System          | Deployments             | `/systems/{id}/deployments`        | Associative       | 1             | No                |
| System          | SamplingFeatures        | `/systems/{id}/samplingFeatures`   | Compositional     | 1             | No                |
| System          | DataStreams (Part 2)    | `/systems/{id}/datastreams`        | Compositional     | 1             | No                |
| System          | ControlStreams (Part 2) | `/systems/{id}/controlstreams`     | Compositional     | 1             | No                |
| System          | SystemEvents (Part 2)   | `/systems/{id}/events`             | Compositional     | 1             | No                |
| Deployment      | Subdeployments          | `/deployments/{id}/subdeployments` | Hierarchical      | Unlimited     | Yes               |
| Deployment      | Systems (deployed)      | N/A (reverse only)                 | Associative       | -             | -                 |
| Collection      | Items                   | `/collections/{id}/items`          | Compositional     | 1             | No                |

**Relationship Types:**

- **Hierarchical:** Parent-child with recursive nesting (subsystems, subdeployments)
- **Compositional:** Parent owns child, child can't exist independently (sampling features, datastreams)
- **Associative:** Many-to-many relationship, both resources independent (systems ↔ deployments)

### Part 2: Dynamic Data

| Parent Resource | Sub-Resource | Endpoint Pattern                   | Relationship Type | Nesting Depth | Recursive Support |
| --------------- | ------------ | ---------------------------------- | ----------------- | ------------- | ----------------- |
| DataStream      | Observations | `/datastreams/{id}/observations`   | Compositional     | 1             | No                |
| ControlStream   | Commands     | `/controlstreams/{id}/commands`    | Compositional     | 1             | No                |
| ControlStream   | Feasibility  | `/controlstreams/{id}/feasibility` | Compositional     | 1             | No                |
| Command         | Status       | `/commands/{id}/status`            | Compositional     | 1             | No                |
| Command         | Result       | `/commands/{id}/result`            | Compositional     | 1             | No                |
| Feasibility     | Status       | `/feasibility/{id}/status`         | Compositional     | 1             | No                |
| Feasibility     | Result       | `/feasibility/{id}/result`         | Compositional     | 1             | No                |

**Key Observations:**

- Part 2 relationships are strictly compositional (no hierarchical nesting)
- DataStreams and ControlStreams are created under Systems (cross-part relationship)
- Observations/Commands cannot be further nested (max depth 1 from parent)
- Command status/result are single-level sub-resources

---

## Hierarchical Navigation (Recursive Relationships)

### Systems → Subsystems

**Hierarchy Pattern:**

```
System (root)
├── Subsystem A
│   ├── Sub-subsystem A1
│   │   └── Sub-sub-subsystem A1a
│   └── Sub-subsystem A2
├── Subsystem B
└── Subsystem C
    └── Sub-subsystem C1
```

**Endpoints:**

**Direct children only (recursive=false or omitted):**

```
GET /systems/{parentId}/subsystems
GET /systems/{parentId}/subsystems?recursive=false
```

Returns: Only immediate children (Subsystem A, B, C)

**All descendants (recursive=true):**

```
GET /systems/{parentId}/subsystems?recursive=true
```

Returns: All nested subsystems at all levels (A, A1, A1a, A2, B, C, C1)

**All systems (canonical endpoint with recursive):**

```
GET /systems
GET /systems?recursive=false
```

Returns: Only root-level systems (no subsystems)

```
GET /systems?recursive=true
```

Returns: All systems including all subsystems (flat list at all nesting levels)

**Query Behavior with recursive=true:**

- All query parameters apply to ALL systems in hierarchy
- Example: `/systems/{parentId}/subsystems?recursive=true&observedProperty=temp`
  - Returns all subsystems (at any depth) that observe temperature
  - Includes sub-subsystems, sub-sub-subsystems, etc.

**Requirements:**

- Server MUST support `recursive` parameter (boolean) (Requirement 10)
- Default behavior (recursive=false or omitted): direct subsystems only (Requirement 11)
- With recursive=true: all nested subsystems at all levels (Requirement 11)
- Recursive associations: subsystem datastreams/controlstreams/samplingFeatures include parent's (Requirement 13)

**Use Cases:**

- Component hierarchy: Weather station → Temperature sensor → Thermistor
- Payload hierarchy: Satellite → Instrument package → Individual sensors
- Vehicle hierarchy: Aircraft → Avionics suite → GPS module

---

### Deployments → Subdeployments

**Hierarchy Pattern:**

```
Deployment (campaign)
├── Subdeployment Phase1
│   ├── Sub-subdeployment Region1
│   └── Sub-subdeployment Region2
├── Subdeployment Phase2
└── Subdeployment Phase3
```

**Endpoints:**

**Direct children only (recursive=false or omitted):**

```
GET /deployments/{parentId}/subdeployments
GET /deployments/{parentId}/subdeployments?recursive=false
```

Returns: Only immediate children (Phase1, Phase2, Phase3)

**All descendants (recursive=true):**

```
GET /deployments/{parentId}/subdeployments?recursive=true
```

Returns: All nested subdeployments at all levels

**All deployments (canonical endpoint with recursive):**

```
GET /deployments
GET /deployments?recursive=false
```

Returns: Only root-level deployments

```
GET /deployments?recursive=true
```

Returns: All deployments including all subdeployments

**Query Behavior with recursive=true:**

- All query parameters apply to ALL deployments in hierarchy
- Example: `/deployments?recursive=true&datetime=2024-01-01/2024-12-31`
  - Returns all deployments and subdeployments with validTime overlapping 2024

**Requirements:**

- Server MUST support `recursive` parameter (boolean) (Requirement 20)
- Default (recursive=false or omitted): direct subdeployments only (Requirement 21)
- With recursive=true: all nested subdeployments at all levels (Requirement 21)
- Recursive associations: nested deployedSystems/featuresOfInterest/samplingFeatures/datastreams/controlstreams include subdeployment resources (Requirement 23)

**Use Cases:**

- Multi-phase campaigns: Arctic expedition with weekly phases
- Geographic hierarchy: Global campaign → Regional campaigns → Local deployments
- Temporal hierarchy: Year-long study → Quarterly periods → Monthly intervals

---

## Compositional Navigation (Parent-Owned Children)

### System → SamplingFeatures

**Relationship:** Compositional (sampling features always belong to one system)

**Endpoints:**

```
GET /systems/{systemId}/samplingFeatures
POST /systems/{systemId}/samplingFeatures
```

**Canonical Access:**

```
GET /samplingFeatures/{id}
PUT /samplingFeatures/{id}
PATCH /samplingFeatures/{id}
DELETE /samplingFeatures/{id}
```

**Characteristics:**

- Sampling features MUST be created under specific system
- Each sampling feature belongs to exactly one parent system
- Sampling features accessible at canonical URL after creation
- Deleting system (with cascade) deletes all its sampling features

**Query Parameters:**

- All standard query parameters supported at nested endpoint
- `foi` - Filter by feature of interest
- `bbox`, `datetime` - Spatial/temporal filters
- `limit`, `offset` - Pagination

**Example:**

```
# Create sampling feature under system
POST /systems/wx-001/samplingFeatures
{
  "type": "Feature",
  "geometry": {"type": "Point", "coordinates": [30.706, -134.196]},
  "properties": {
    "uid": "urn:x-sample:station-A-01",
    "name": "Sampling Point A-01",
    "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint"
  }
}

# Response: 201 Created
# Location: https://api.example.org/samplingFeatures/sf-001

# Later access via canonical URL
GET /samplingFeatures/sf-001
```

---

### System → DataStreams (Part 2)

**Relationship:** Compositional (datastreams belong to one system)

**Endpoints:**

```
GET /systems/{systemId}/datastreams
POST /systems/{systemId}/datastreams
```

**Canonical Access:**

```
GET /datastreams/{id}
PUT /datastreams/{id}
PATCH /datastreams/{id}
DELETE /datastreams/{id}
```

**Characteristics:**

- DataStreams created under specific system
- Each datastream belongs to exactly one system
- Datastreams accessible at canonical URL after creation
- Deleting system (with cascade) deletes all its datastreams

**Query Parameters at Nested Endpoint:**

- `phenomenonTime` - Filter by observation phenomenon time range
- `resultTime` - Filter by observation result time range
- `observedProperty` - Filter by observed properties
- `foi` - Filter by feature of interest
- `limit`, `offset` - Pagination

**Example:**

```
# Get all datastreams for system observing temperature after 2024-01-01
GET /systems/wx-001/datastreams?observedProperty=http://qudt.org/vocab/quantitykind/Temperature&phenomenonTime=2024-01-01T00:00:00Z/..
```

---

### System → ControlStreams (Part 2)

**Relationship:** Compositional (control streams belong to one system)

**Endpoints:**

```
GET /systems/{systemId}/controlstreams
POST /systems/{systemId}/controlstreams
```

**Canonical Access:**

```
GET /controlstreams/{id}
PUT /controlstreams/{id}
PATCH /controlstreams/{id}
DELETE /controlstreams/{id}
```

**Characteristics:**

- ControlStreams created under specific system
- Each control stream belongs to exactly one system
- Control streams accessible at canonical URL after creation
- Deleting system (with cascade) deletes all its control streams

**Query Parameters at Nested Endpoint:**

- `executionTime` - Filter by command execution time range
- `issueTime` - Filter by command issue time range
- `controlledProperty` - Filter by controlled properties
- `foi` - Filter by feature of interest
- `limit`, `offset` - Pagination

---

### DataStream → Observations (Part 2)

**Relationship:** Compositional (observations belong to one datastream)

**Endpoints:**

```
GET /datastreams/{datastreamId}/observations
POST /datastreams/{datastreamId}/observations
```

**Canonical Access:**

```
GET /observations/{id}
PUT /observations/{id}
PATCH /observations/{id}
DELETE /observations/{id}
```

**Characteristics:**

- Observations created under specific datastream
- Each observation belongs to exactly one datastream
- Observations accessible at canonical URL after creation
- Deleting datastream (with cascade) deletes all its observations

**Query Parameters at Nested Endpoint:**

- `phenomenonTime` - Filter by phenomenon time
- `resultTime` - Filter by result time
- `limit`, `offset` - Pagination (max limit: 10000)

**Pagination:**

- Critical for large datasets (millions of observations)
- Cursor-based pagination recommended for streaming data
- `next` link relation in response for next page

**Example:**

```
# Get latest 1000 observations
GET /datastreams/ds-123/observations?resultTime=latest&limit=1000

# Get observations in time range
GET /datastreams/ds-123/observations?phenomenonTime=2024-01-15T00:00:00Z/2024-01-15T23:59:59Z&limit=10000
```

---

### ControlStream → Commands (Part 2)

**Relationship:** Compositional (commands belong to one control stream)

**Endpoints:**

```
GET /controlstreams/{controlstreamId}/commands
POST /controlstreams/{controlstreamId}/commands
```

**Canonical Access:**

```
GET /commands/{id}
PUT /commands/{id}
PATCH /commands/{id}
DELETE /commands/{id}
```

**Characteristics:**

- Commands created under specific control stream
- Each command belongs to exactly one control stream
- Commands accessible at canonical URL after creation
- Deleting control stream (with cascade) deletes all its commands

**Query Parameters at Nested Endpoint:**

- `executionTime` - Filter by execution time
- `issueTime` - Filter by issue time
- `limit`, `offset` - Pagination

---

### Command → Status (Part 2)

**Relationship:** Compositional (status reports belong to one command)

**Endpoints:**

```
GET /commands/{commandId}/status
POST /commands/{commandId}/status
```

**Canonical Access:**

```
GET /commandStatus/{id}
PUT /commandStatus/{id}
DELETE /commandStatus/{id}
```

**Characteristics:**

- Status reports created under specific command
- Each status report belongs to exactly one command
- Typically multiple status reports per command (progress updates)
- Deleting command (with cascade) deletes all its status reports

**Query Parameters:**

- `limit`, `offset` - Pagination
- Sorted by reportTime (most recent first)

**Example:**

```
# Get latest status for command
GET /commands/cmd-456/status?limit=1

# Get all status reports
GET /commands/cmd-456/status
```

---

### Command → Result (Part 2)

**Relationship:** Compositional (results belong to one command)

**Endpoints:**

```
GET /commands/{commandId}/result
POST /commands/{commandId}/result
```

**Canonical Access:**

```
GET /commandResult/{id}
PUT /commandResult/{id}
DELETE /commandResult/{id}
```

**Characteristics:**

- Results created under specific command
- Typically one result per command (can be multiple)
- Result types: inline data, datastream references, observation references, external resources
- Deleting command (with cascade) deletes all its results

**Query Parameters:**

- `limit`, `offset` - Pagination (if multiple results)

---

## Associative Navigation (Many-to-Many Relationships)

### System ↔ Deployment

**Bidirectional Relationship:** Systems deployed in multiple deployments, deployments contain multiple systems

**Forward Navigation (System → Deployments):**

```
GET /systems/{systemId}/deployments
```

Returns: All deployments where this system was/is deployed

**Reverse Navigation (Deployment → Systems):**

- No dedicated endpoint (use query parameter instead)

```
GET /deployments?system={systemId}
```

OR access `deployedSystems` property in deployment representation

**Characteristics:**

- Many-to-many relationship
- Both resources exist independently
- Deleting system doesn't delete deployments (just removes association)
- Deleting deployment doesn't delete systems

**Query Parameters at System→Deployments Endpoint:**

- `datetime` - Filter by deployment validTime
- `bbox` - Filter by deployment spatial extent
- `limit`, `offset` - Pagination

**Example:**

```
# Find all deployments for system wx-001
GET /systems/wx-001/deployments

# Find all deployments that included system wx-001
GET /deployments?system=wx-001

# Find active deployments for system wx-001
GET /systems/wx-001/deployments?datetime=2024-01-15T00:00:00Z/..
```

---

## Canonical vs Relationship URLs

### URL Patterns

**Canonical URL:**

- Primary resource identifier
- Unique for each resource instance
- Pattern: `/{resourceType}/{id}`
- Examples:
  - `/systems/wx-001`
  - `/datastreams/ds-123`
  - `/observations/obs-456`

**Relationship URL (Nested):**

- Access resource via parent relationship
- Pattern: `/{parentType}/{parentId}/{childType}` or `/{parentType}/{parentId}/{childType}/{childId}`
- Examples:
  - `/systems/wx-001/subsystems` (collection)
  - `/systems/wx-001/subsystems/temp-sensor` (single resource)
  - `/datastreams/ds-123/observations` (collection)
  - `/datastreams/ds-123/observations/obs-456` (single resource)

### Equivalence Guarantee

**Resource Identity:**

- Resource accessible at multiple URLs (canonical + nested)
- All URLs return same resource representation
- Updates at any URL reflected at all URLs

**Example:**

```
# These return the SAME resource
GET /observations/obs-456
GET /datastreams/ds-123/observations/obs-456
```

**Recommendation:**

- Use canonical URL for resource identity (links, references)
- Use nested URL for navigation/discovery
- Location header in 201 Created MUST use canonical URL

### Create Operations

**Creation via Nested Endpoint:**

```
POST /systems/{parentId}/subsystems
POST /systems/{systemId}/samplingFeatures
POST /datastreams/{dsId}/observations
```

**Response:**

```
HTTP/1.1 201 Created
Location: https://api.example.org/systems/sub-001  (CANONICAL URL)
Location: https://api.example.org/observations/obs-456  (CANONICAL URL)
```

**After Creation:**

- Resource accessible at canonical URL immediately
- Resource also accessible via nested URL
- Both URLs return identical representation

---

## Query Parameter Support at Nested Endpoints

### General Rules

**Inheritance from OGC API - Features:**

- All nested collection endpoints support standard query parameters
- `limit`, `offset` - Pagination
- `bbox` - Spatial filter (for resources with geometry)
- `datetime` - Temporal filter
- `f` - Format negotiation

**CSAPI-Specific Parameters:**

- Relationship filters (foi, observedProperty, controlledProperty, system, etc.)
- Hierarchical filters (recursive)
- Temporal filters (phenomenonTime, resultTime, executionTime, issueTime)

### Parameter Applicability Matrix

| Parameter          | Subsystems | SamplingFeatures | DataStreams | Observations | ControlStreams | Commands |
| ------------------ | ---------- | ---------------- | ----------- | ------------ | -------------- | -------- |
| limit              | ✓          | ✓                | ✓           | ✓            | ✓              | ✓        |
| offset             | ✓          | ✓                | ✓           | ✓            | ✓              | ✓        |
| bbox               | ✓          | ✓                | -           | -            | -              | -        |
| datetime           | ✓          | ✓                | ✓           | -            | ✓              | -        |
| recursive          | ✓          | -                | -           | -            | -              | -        |
| foi                | ✓          | ✓                | ✓           | -            | ✓              | -        |
| observedProperty   | ✓          | -                | ✓           | -            | -              | -        |
| controlledProperty | ✓          | -                | -           | -            | ✓              | -        |
| phenomenonTime     | -          | -                | ✓           | ✓            | -              | -        |
| resultTime         | -          | -                | ✓           | ✓            | -              | -        |
| executionTime      | -          | -                | -           | -            | ✓              | ✓        |
| issueTime          | -          | -                | -           | -            | ✓              | ✓        |

**Notes:**

- Temporal parameters apply to different properties per resource type
- Spatial parameters only apply to resources with geometry (Systems, SamplingFeatures)
- Relationship parameters filter by associations

### Examples

**Filtered Subsystems:**

```
# Subsystems observing temperature
GET /systems/wx-001/subsystems?observedProperty=http://qudt.org/vocab/quantitykind/Temperature

# Subsystems with location in bounding box
GET /systems/wx-001/subsystems?bbox=-180,-90,180,90

# All nested subsystems (recursive)
GET /systems/wx-001/subsystems?recursive=true

# Combine filters
GET /systems/wx-001/subsystems?recursive=true&observedProperty=temperature&bbox=-122,-37,-121,-36
```

**Filtered DataStreams:**

```
# DataStreams with observations after 2024-01-01
GET /systems/wx-001/datastreams?phenomenonTime=2024-01-01T00:00:00Z/..

# Live datastreams only
GET /systems/wx-001/datastreams?live=true

# DataStreams observing multiple properties
GET /systems/wx-001/datastreams?observedProperty=temperature,pressure
```

**Filtered Observations:**

```
# Observations in time range
GET /datastreams/ds-123/observations?phenomenonTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z

# Latest observations
GET /datastreams/ds-123/observations?resultTime=latest&limit=100

# Paginated observations
GET /datastreams/ds-123/observations?limit=1000&offset=5000
```

---

## Pagination at Nested Endpoints

### Pagination Parameters

**limit:**

- Type: integer
- Part 1 range: Implementation-dependent (typically 10-100)
- Part 2 range: 1 to 10000
- Default: 10 (if not specified)

**offset:**

- Type: integer
- Range: 0 to ∞
- Default: 0

### Pagination Links

**OGC API - Features Pattern:**

- Response includes `links` array
- `rel="next"` - Next page URL
- `rel="prev"` - Previous page URL
- Clients follow links for pagination

**Example Response:**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* resources */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=0",
      "type": "application/json"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=100",
      "type": "application/json"
    }
  ],
  "numberMatched": 15000,
  "numberReturned": 100
}
```

### Cursor-Based Pagination (Part 2 Recommendation)

**For Large Datasets:**

- Offset pagination inefficient for millions of observations
- Cursor-based pagination recommended
- Server generates opaque cursor token
- Client includes cursor in next request

**Example:**

```
# First request
GET /datastreams/ds-123/observations?limit=1000

# Response includes cursor in next link
{
  "features": [ /* 1000 observations */ ],
  "links": [
    {
      "rel": "next",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=1000&cursor=eyJwaGVub21lbm9uVGltZSI6IjIwMjQtMDEtMTVUMTI6MDA6MDBaIiwiaWQiOjEwMDB9",
      "type": "application/json"
    }
  ]
}

# Next request uses cursor
GET /datastreams/ds-123/observations?limit=1000&cursor=eyJwaGVub21lbm9uVGltZSI6IjIwMjQtMDEtMTVUMTI6MDA6MDBaIiwiaWQiOjEwMDB9
```

---

## Link Relations and Hypermedia

### Link Relation Types

**IANA Standard Relations:**

- `self` - Current resource URL
- `alternate` - Alternate representation (different format)
- `collection` - Parent collection URL
- `item` - Individual resource in collection
- `next` - Next page in paginated collection
- `prev` - Previous page in paginated collection
- `first` - First page in paginated collection
- `last` - Last page in paginated collection

**CSAPI-Specific Relations (via `@link` suffix):**

- `subsystems@link` - Link to subsystems collection
- `deployedSystems@link` - Link to deployed systems
- `deployments@link` - Link to deployments
- `samplingFeatures@link` - Link to sampling features
- `datastreams@link` - Link to datastreams
- `controlstreams@link` - Link to control streams
- `observations@link` - Link to observations collection
- `commands@link` - Link to commands collection
- `status@link` - Link to command status
- `result@link` - Link to command result
- `foi@link` - Link to feature of interest
- `procedure@link` - Link to procedure
- `system@link` - Link to parent system
- `datastream@link` - Link to parent datastream
- `controlstream@link` - Link to parent control stream

### Link Objects in Resource Representations

**Format:**

```json
{
  "href": "https://api.example.org/systems/wx-001",
  "rel": "related",
  "type": "application/geo+json",
  "title": "Weather Station Alpha"
}
```

**Properties:**

- `href` (required) - Target URL
- `rel` (optional) - Link relation type
- `type` (optional) - Media type of target
- `title` (optional) - Human-readable title

**Example in System Resource:**

```json
{
  "type": "Feature",
  "id": "wx-001",
  "geometry": {
    /* ... */
  },
  "properties": {
    "uid": "urn:x-sensor:id:wx-001",
    "name": "Weather Station Alpha",
    "subsystems@link": {
      "href": "https://api.example.org/systems/wx-001/subsystems",
      "rel": "related",
      "type": "application/geo+json",
      "title": "Subsystems"
    },
    "datastreams@link": {
      "href": "https://api.example.org/systems/wx-001/datastreams",
      "rel": "related",
      "type": "application/json",
      "title": "Data Streams"
    },
    "samplingFeatures@link": {
      "href": "https://api.example.org/systems/wx-001/samplingFeatures",
      "rel": "related",
      "type": "application/geo+json",
      "title": "Sampling Features"
    }
  },
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems/wx-001",
      "type": "application/geo+json"
    },
    {
      "rel": "collection",
      "href": "https://api.example.org/systems",
      "type": "application/geo+json"
    }
  ]
}
```

### Hypermedia Navigation Pattern

**Client starts at root:**

```
GET /
```

**Discovers systems collection:**

```json
{
  "links": [
    {
      "rel": "http://www.opengis.net/def/rel/ogc/1.0/systems",
      "href": "https://api.example.org/systems",
      "type": "application/geo+json"
    }
  ]
}
```

**Navigates to system:**

```
GET /systems/wx-001
```

**Follows subsystems link:**

```json
{
  "properties": {
    "subsystems@link": {
      "href": "https://api.example.org/systems/wx-001/subsystems"
    }
  }
}
```

**Retrieves subsystems:**

```
GET /systems/wx-001/subsystems
```

**Advantage:** Client doesn't hardcode URL patterns, follows links dynamically

---

## Client API Navigation Patterns

### Fluent Navigation API

**Design Goal:** Intuitive method chaining for relationship traversal

```typescript
// System → Subsystems
const subsystems = await client.systems.get('wx-001').subsystems.list();

// System → DataStreams
const datastreams = await client.systems.get('wx-001').datastreams.list();

// DataStream → Observations
const observations = await client.datastreams.get('ds-123').observations.list();

// System → Subsystems (recursive)
const allSubsystems = await client.systems
  .get('wx-001')
  .subsystems.list({ recursive: true });

// Filtered navigation
const tempDatastreams = await client.systems.get('wx-001').datastreams.list({
  observedProperty: 'http://qudt.org/vocab/quantitykind/Temperature',
});

// Paginated navigation
const recentObs = await client.datastreams.get('ds-123').observations.list({
  phenomenonTime: '2024-01-15T00:00:00Z/..',
  limit: 1000,
});
```

### Lazy Loading Pattern

**Design Goal:** Load related resources on demand

```typescript
interface System {
  id: string;
  name: string;

  // Lazy loaders
  subsystems(): Promise<SystemCollection>;
  deployments(): Promise<DeploymentCollection>;
  samplingFeatures(): Promise<SamplingFeatureCollection>;
  datastreams(): Promise<DataStreamCollection>;
  controlstreams(): Promise<ControlStreamCollection>;
}

// Usage
const system = await client.systems.get('wx-001');
const subsystems = await system.subsystems(); // Load on demand
const datastreams = await system.datastreams(); // Load on demand
```

### Eager Loading Pattern

**Design Goal:** Load related resources in single request (if server supports)

```typescript
// Load system with subsystems included
const system = await client.systems.get('wx-001', {
  include: ['subsystems', 'datastreams'],
});

// Subsystems already loaded (no additional request)
console.log(system.subsystems); // Array of subsystems

// DataStreams already loaded
console.log(system.datastreams); // Array of datastreams
```

**Note:** Eager loading requires server support (not in standard, server-specific)

### Async Iterator Pattern

**Design Goal:** Iterate through large collections efficiently

```typescript
// Iterate through all observations (auto-pagination)
for await (const observation of client.datastreams
  .get('ds-123')
  .observations.iterate()) {
  console.log(observation.phenomenonTime, observation.result);
}

// Iterate through all subsystems (recursive)
for await (const subsystem of client.systems
  .get('wx-001')
  .subsystems.iterate({ recursive: true })) {
  console.log(subsystem.name);
}

// Iterate with filtering
for await (const obs of client.datastreams.get('ds-123').observations.iterate({
  phenomenonTime: '2024-01-15T00:00:00Z/2024-01-16T00:00:00Z',
  limit: 1000, // Page size
})) {
  processObservation(obs);
}
```

### Bidirectional Navigation

**Design Goal:** Navigate relationships in both directions

```typescript
// System → Deployments (forward)
const deployments = await client.systems.get('wx-001').deployments.list();

// Deployment → Systems (reverse via query)
const systems = await client.deployments.get('mission-001').systems.list();
// OR
const systems = await client.systems.list({ deployment: 'mission-001' });

// Observation → DataStream (reverse via property)
const observation = await client.observations.get('obs-456');
const datastream = await client.datastreams.get(observation.datastream);
// OR with convenience method
const datastream = await observation.datastream(); // Lazy load
```

### Path-Based Navigation

**Design Goal:** Navigate complex paths in single call

```typescript
// System → DataStream → Observations
const observations = await client.systems
  .get('wx-001')
  .datastreams.get('ds-123')
  .observations.list({ limit: 100 });

// Command → Status
const status = await client.commands.get('cmd-456').status.list();

// Command → Result
const result = await client.commands.get('cmd-456').result.get();
```

### Builder Pattern for Complex Queries

**Design Goal:** Build complex nested queries with filters

```typescript
// Builder for subsystem query
const subsystems = await client.systems
  .get('wx-001')
  .subsystems.where({ observedProperty: 'temperature' })
  .where({ bbox: [-122, 37, -121, 38] })
  .recursive(true)
  .limit(50)
  .list();

// Builder for observation query
const observations = await client.datastreams
  .get('ds-123')
  .observations.where({ phenomenonTime: '2024-01-15T00:00:00Z/..' })
  .where({ resultTime: 'latest' })
  .limit(1000)
  .list();
```

---

## Nesting Depth Limits

### Part 1 Depth Limits

**Hierarchical Resources (Unlimited Depth):**

- Systems → Subsystems → Sub-subsystems → ... (unlimited)
- Deployments → Subdeployments → Sub-subdeployments → ... (unlimited)

**Compositional Resources (Depth 1):**

- Systems → SamplingFeatures (depth 1, no further nesting)
- Systems → DataStreams (depth 1, then cross to Part 2)
- Systems → ControlStreams (depth 1, then cross to Part 2)

### Part 2 Depth Limits

**All Part 2 Resources (Depth 1):**

- DataStreams → Observations (depth 1)
- ControlStreams → Commands (depth 1)
- Commands → Status (depth 1)
- Commands → Result (depth 1)

**Maximum Path Depth Example:**

```
System (root)
  → Subsystem
    → Sub-subsystem
      → Sub-sub-subsystem
        → DataStream  (cross to Part 2)
          → Observation
```

**Path depth:** 6 levels (unlimited Part 1 hierarchy + 1 Part 2 level + 1 observation level)

**Practical Limit:**

- No technical depth limit in standard
- Practical: 3-5 levels for hierarchical resources
- Performance considerations for deep hierarchies

---

## Relationship URL Construction Rules

### Pattern Rules

**Single Resource via Nested URL:**

```
/{parentType}/{parentId}/{childType}/{childId}
```

**Collection via Nested URL:**

```
/{parentType}/{parentId}/{childType}
```

**Examples:**

```
/systems/wx-001/subsystems
/systems/wx-001/subsystems/temp-sensor
/datastreams/ds-123/observations
/datastreams/ds-123/observations/obs-456
/commands/cmd-789/status
/commands/cmd-789/status/status-001
```

### Query String Preservation

**Query parameters apply to nested collection:**

```
/systems/wx-001/subsystems?recursive=true&observedProperty=temperature
/datastreams/ds-123/observations?phenomenonTime=2024-01-15T00:00:00Z/..&limit=1000
```

**NOT valid (query on single resource):**

```
/systems/wx-001/subsystems/temp-sensor?recursive=true  (❌ recursive N/A for single resource)
```

### URL Equivalence

**These return the SAME resource:**

```
GET /observations/obs-456
GET /datastreams/ds-123/observations/obs-456
```

**These return the SAME collection:**

```
GET /systems (all root systems)
GET /systems/{parent}/subsystems (subsystems of specific parent)
```

**NOT equivalent:**

```
GET /systems (root systems only if recursive=false)
GET /systems?recursive=true (all systems including all subsystems)
```

---

## Special Cases and Constraints

### Read-Only Sub-Resources

**Collections → Items:**

- Collections are server-managed (read-only)
- Items can be added/removed via POST/DELETE at `/collections/{id}/items`
- Items can be created/updated/deleted at canonical URLs
- Canonical URL operations reflected in collection membership

### Cascade Delete Impact on Sub-Resources

**System Cascade Delete:**

```
DELETE /systems/wx-001?cascade=true
```

Deletes:

- System wx-001
- All subsystems (recursively)
- All sampling features
- All datastreams (Part 2)
- All control streams (Part 2)
- All observations (via datastream cascade)
- All commands (via control stream cascade)

**DataStream Cascade Delete:**

```
DELETE /datastreams/ds-123?cascade=true
```

Deletes:

- DataStream ds-123
- All observations

**ControlStream Cascade Delete:**

```
DELETE /controlstreams/cs-456?cascade=true
```

Deletes:

- ControlStream cs-456
- All commands
- All command status reports
- All command results

### Schema Validation at Nested Endpoints

**Observation Creation:**

```
POST /datastreams/ds-123/observations
```

- Server MUST validate result against DataStream observation schema
- 400 Bad Request if result incompatible with schema

**Command Creation:**

```
POST /controlstreams/cs-456/commands
```

- Server MUST validate parameters against ControlStream command schema
- 400 Bad Request if parameters incompatible with schema

### Forbidden Operations

**Cannot create subsystem at canonical endpoint:**

```
POST /systems  (❌ creates root system, not subsystem)
POST /systems/{parent}/subsystems  (✓ creates subsystem)
```

**Cannot create observation at canonical endpoint:**

```
POST /observations  (❌ forbidden, no canonical POST)
POST /datastreams/{id}/observations  (✓ creates observation)
```

**Cannot create command at canonical endpoint:**

```
POST /commands  (❌ forbidden, no canonical POST)
POST /controlstreams/{id}/commands  (✓ creates command)
```

---

## Summary

This section documents sub-resource navigation patterns for CSAPI client library:

**Sub-Resource Relationships:**

- Part 1: 9 relationship types (subsystems, subdeployments, sampling features, deployments, datastreams, control streams, events, collection items)
- Part 2: 7 relationship types (observations, commands, status, result, feasibility)
- Hierarchical: Unlimited depth (subsystems, subdeployments)
- Compositional: Depth 1 (sampling features, datastreams, observations, commands)
- Associative: Bidirectional (systems ↔ deployments)

**Navigation Patterns:**

- Nested endpoints: `/{parent}/{parentId}/{children}`
- Canonical access: `/{resourceType}/{id}`
- Equivalence: Same resource accessible via multiple URLs
- Query parameters: Full support at nested endpoints
- Pagination: limit/offset + cursor-based for large datasets

**Client API Design:**

- Fluent navigation: Method chaining for relationship traversal
- Lazy loading: Load related resources on demand
- Async iterators: Efficient iteration with auto-pagination
- Bidirectional: Navigate relationships in both directions
- Path-based: Complex multi-level navigation

**Special Constraints:**

- recursive parameter for hierarchical resources
- Schema validation for nested create operations
- Cascade delete for compositional relationships
- No canonical POST for observations/commands (nested only)

See Section 5 (CRUD Operations) for write operation details and Section 4 (Query Parameters) for filtering options.
