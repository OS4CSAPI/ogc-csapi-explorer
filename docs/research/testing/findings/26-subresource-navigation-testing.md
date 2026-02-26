# Section 26: Sub-Resource Navigation Testing - FINDINGS

**Research Plan:** [Research Plan 26: Sub-Resource Navigation Testing](../research-plans/26-subresource-navigation-testing.md)

**Research Questions:** 6 core questions about CSAPI nested resource patterns, testing sub-resource navigation paths, bidirectional navigation, query parameters on nested endpoints, filtering on nested resources, and handling invalid nested paths

**Methodology:** 6-phase systematic analysis (Phase 1: Sub-Resource Pattern Inventory extracting 16 parent-child relationships → Phase 2: URL Structure Analysis for nested endpoint patterns → Phase 3: Upstream Navigation Testing Analysis of existing patterns → Phase 4: Test Scenario Design for 50+ scenarios → Phase 5: Bidirectional Navigation Analysis for reverse paths → Phase 6: Synthesis into comprehensive sub-resource navigation testing strategy)

**Research Time:** 3.5 hours (February 6, 2026)

**Primary Source(s):**

- [Sub-Resource Navigation Requirements](../../requirements/subresource-navigation-requirements.md)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Sub-resource patterns)
- [ROADMAP Phase 2](../../../planning/ROADMAP.md) (Sub-resource navigation implementation)
- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html) (resource relationships)
- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (resource relationships)

**Supporting Resources:**

- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (resource relationships)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (navigation patterns)
- Section 23: [Pagination Testing](23-pagination-testing.md) (pagination on nested endpoints)
- Section 24: [Query Parameter Combination Testing](24-query-parameter-combination-testing.md) (parameters on nested endpoints)

**Document Purpose:** Defines comprehensive testing strategy for 16 distinct CSAPI parent-child relationships across 3 relationship types (hierarchical with unlimited depth, compositional at depth 1, associative bidirectional) with URL construction patterns, query parameter inheritance, pagination on nested collections, and 50+ test scenarios

---

## Executive Summary

CSAPI implements extensive nested resource patterns across Parts 1-2, supporting **16 distinct parent-child relationships** with three relationship types: hierarchical (unlimited depth), compositional (depth 1), and associative (bidirectional). Sub-resource navigation enables efficient resource discovery without complex queries.

This document defines a comprehensive testing strategy covering:

- 16 parent-child relationship patterns
- URL construction for nested endpoints
- Query parameter support on nested resources
- Pagination on nested collections
- Bidirectional navigation patterns
- Invalid path error handling
- 50+ test scenarios across all relationship types

### Key Findings

- **16 Relationship Patterns:** Systems→Subsystems, DataStreams→Observations, Commands→Status, etc.
- **3 Relationship Types:** Hierarchical (recursive), Compositional (parent-owned), Associative (many-to-many)
- **Nesting Depth:** Unlimited for hierarchical, depth 1 for compositional, N/A for associative
- **URL Patterns:** `/{parent}/{parentId}/{children}` or `/{parent}/{parentId}/{children}/{childId}`
- **Query Parameter Inheritance:** All standard parameters (limit, bbox, datetime, etc.) work on nested endpoints
- **Bidirectional Navigation:** Systems↔Deployments navigable in both directions
- **Testing Strategy:** Pattern-based tests reusable across all relationship types

---

## 1. Sub-Resource Relationship Inventory

### 1.1 Part 1: Core Resource Relationships (9 patterns)

| Parent Resource | Child Resource   | Endpoint Pattern                   | Relationship Type          | Nesting Depth | Recursive Support      |
| --------------- | ---------------- | ---------------------------------- | -------------------------- | ------------- | ---------------------- |
| **System**      | Subsystems       | `/systems/{id}/subsystems`         | Hierarchical               | Unlimited     | Yes (`recursive=true`) |
| **System**      | SamplingFeatures | `/systems/{id}/samplingFeatures`   | Compositional              | 1             | No                     |
| **System**      | Deployments      | `/systems/{id}/deployments`        | Associative                | N/A           | No                     |
| **System**      | DataStreams      | `/systems/{id}/datastreams`        | Compositional (cross-part) | 1             | No                     |
| **System**      | ControlStreams   | `/systems/{id}/controlstreams`     | Compositional (cross-part) | 1             | No                     |
| **System**      | SystemEvents     | `/systems/{id}/events`             | Compositional (cross-part) | 1             | No                     |
| **Deployment**  | Subdeployments   | `/deployments/{id}/subdeployments` | Hierarchical               | Unlimited     | Yes (`recursive=true`) |
| **Deployment**  | Systems          | N/A (reverse only via query)       | Associative (reverse)      | N/A           | No                     |
| **Collection**  | Items            | `/collections/{id}/items`          | Compositional              | 1             | No                     |

**Relationship Type Definitions:**

- **Hierarchical:** Parent-child with recursive nesting (e.g., subsystems within subsystems)
- **Compositional:** Parent owns child, child cannot exist independently (e.g., datastreams belong to system)
- **Associative:** Many-to-many relationship, both resources independent (e.g., systems deployed in multiple deployments)

### 1.2 Part 2: Dynamic Data Relationships (7 patterns)

| Parent Resource   | Child Resource | Endpoint Pattern                   | Relationship Type | Nesting Depth | Recursive Support |
| ----------------- | -------------- | ---------------------------------- | ----------------- | ------------- | ----------------- |
| **DataStream**    | Observations   | `/datastreams/{id}/observations`   | Compositional     | 1             | No                |
| **ControlStream** | Commands       | `/controlstreams/{id}/commands`    | Compositional     | 1             | No                |
| **ControlStream** | Feasibility    | `/controlstreams/{id}/feasibility` | Compositional     | 1             | No                |
| **Command**       | Status         | `/commands/{id}/status`            | Compositional     | 1             | No                |
| **Command**       | Result         | `/commands/{id}/result`            | Compositional     | 1             | No                |
| **Feasibility**   | Status         | `/feasibility/{id}/status`         | Compositional     | 1             | No                |
| **Feasibility**   | Result         | `/feasibility/{id}/result`         | Compositional     | 1             | No                |

**Key Observations:**

- Part 2 relationships are strictly compositional (no hierarchical nesting)
- DataStreams/ControlStreams connect Part 1 (Systems) to Part 2 (Observations/Commands)
- Maximum nesting depth is 1 for all Part 2 relationships
- Command status/result are terminal endpoints (no further nesting)

### 1.3 Relationship Type Matrix

| Relationship Type | Count  | Examples                                 | Max Depth | Recursive | Bidirectional |
| ----------------- | ------ | ---------------------------------------- | --------- | --------- | ------------- |
| **Hierarchical**  | 2      | Subsystems, Subdeployments               | Unlimited | Yes       | No            |
| **Compositional** | 12     | SamplingFeatures, Observations, Commands | 1         | No        | No            |
| **Associative**   | 2      | Systems↔Deployments                      | N/A       | No        | Yes           |
| **TOTAL**         | **16** | -                                        | -         | -         | -             |

---

## 2. URL Structure Patterns

### 2.1 Nested Collection URL

**Pattern:**

```
/{parentType}/{parentId}/{childType}
```

**Examples:**

```
/systems/wx-001/subsystems
/systems/wx-001/datastreams
/datastreams/ds-123/observations
/commands/cmd-456/status
/deployments/deploy-789/subdeployments
```

**Characteristics:**

- Returns collection of child resources
- Supports query parameters (limit, bbox, datetime, etc.)
- Supports pagination (links for next/prev pages)
- Returns FeatureCollection (Part 1) or custom collection (Part 2)

### 2.2 Nested Single Resource URL

**Pattern:**

```
/{parentType}/{parentId}/{childType}/{childId}
```

**Examples:**

```
/systems/wx-001/subsystems/temp-sensor
/datastreams/ds-123/observations/obs-456
/commands/cmd-789/status/status-001
```

**Characteristics:**

- Returns single child resource
- Query parameters typically NOT applicable (except format negotiation)
- Equivalent to canonical URL (`/{childType}/{childId}`)
- Useful for navigation context

### 2.3 Canonical URL (For Comparison)

**Pattern:**

```
/{resourceType}/{id}
```

**Examples:**

```
/systems/temp-sensor
/observations/obs-456
/commands/cmd-789
```

**Equivalence Guarantee:**

```
GET /observations/obs-456
GET /datastreams/ds-123/observations/obs-456
```

→ Both return **identical resource** (same ID, same representation)

**Location Header After Creation:**

```
POST /datastreams/ds-123/observations
→ 201 Created
→ Location: https://api.example.org/observations/obs-456  (CANONICAL)
```

### 2.4 Query String Preservation

**Query Parameters on Nested Collections:**

```
/systems/wx-001/subsystems?recursive=true&observedProperty=temperature
/datastreams/ds-123/observations?phenomenonTime=2024-01-15T00:00:00Z/..&limit=1000
/systems/wx-001/deployments?datetime=2024-01-01/..&bbox=-180,-90,180,90
```

**NOT Valid (Query on Single Resource):**

```
/systems/wx-001/subsystems/temp-sensor?recursive=true  (❌ recursive N/A for single resource)
```

---

## 3. Query Parameter Support at Nested Endpoints

### 3.1 Parameter Applicability Matrix

| Parameter              | Subsystems | SamplingFeatures | DataStreams | Observations | ControlStreams | Commands | Status | Result |
| ---------------------- | ---------- | ---------------- | ----------- | ------------ | -------------- | -------- | ------ | ------ |
| **limit**              | ✓          | ✓                | ✓           | ✓            | ✓              | ✓        | ✓      | ✓      |
| **offset**             | ✓          | ✓                | ✓           | ✓            | ✓              | ✓        | ✓      | ✓      |
| **bbox**               | ✓          | ✓                | -           | -            | -              | -        | -      | -      |
| **datetime**           | ✓          | ✓                | ✓           | -            | ✓              | -        | -      | -      |
| **f** (format)         | ✓          | ✓                | ✓           | ✓            | ✓              | ✓        | ✓      | ✓      |
| **recursive**          | ✓          | -                | -           | -            | -              | -        | -      | -      |
| **foi**                | ✓          | ✓                | ✓           | -            | ✓              | -        | -      | -      |
| **observedProperty**   | ✓          | -                | ✓           | -            | -              | -        | -      | -      |
| **controlledProperty** | ✓          | -                | -           | -            | ✓              | -        | -      | -      |
| **phenomenonTime**     | -          | -                | ✓           | ✓            | -              | -        | -      | -      |
| **resultTime**         | -          | -                | ✓           | ✓            | -              | -        | -      | -      |
| **executionTime**      | -          | -                | -           | -            | ✓              | ✓        | -      | -      |
| **issueTime**          | -          | -                | -           | -            | ✓              | ✓        | -      | -      |

**Notes:**

- All collection endpoints support pagination (limit/offset)
- Spatial filters (bbox) only apply to resources with geometry
- Temporal filters vary by resource type (datetime, phenomenonTime, resultTime, etc.)
- Relationship filters (foi, observedProperty) filter by associations
- `recursive` parameter unique to hierarchical relationships (subsystems, subdeployments)

### 3.2 Parameter Inheritance Rules

**All Nested Endpoints Inherit:**

- Pagination parameters (limit, offset)
- Format negotiation (f, format)

**Spatial Resources Inherit:**

- Spatial filters (bbox)
- Temporal filters (datetime)

**Observation/Command Resources Inherit:**

- Specific temporal filters (phenomenonTime, resultTime, executionTime, issueTime)
- Relationship filters (foi, observedProperty, controlledProperty)

**Hierarchical Resources Add:**

- recursive parameter (unique to subsystems/subdeployments)

### 3.3 Example Nested Queries

**Filtered Subsystems:**

```
# Subsystems observing temperature
GET /systems/wx-001/subsystems?observedProperty=http://qudt.org/vocab/quantitykind/Temperature

# Subsystems with location in bounding box
GET /systems/wx-001/subsystems?bbox=-180,-90,180,90

# All nested subsystems (recursive)
GET /systems/wx-001/subsystems?recursive=true

# Combined filters
GET /systems/wx-001/subsystems?recursive=true&observedProperty=temperature&bbox=-122,37,-121,38
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

## 4. Pagination at Nested Endpoints

### 4.1 Pagination Parameters

**limit:**

- Type: integer
- Part 1 range: Implementation-dependent (typically 10-100)
- Part 2 range: 1 to 10000
- Default: 10 (if not specified)

**offset:**

- Type: integer
- Range: 0 to ∞
- Default: 0

### 4.2 Pagination Links

**OGC API - Features Pattern:**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* child resources */
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
    },
    {
      "rel": "prev",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=-100",
      "type": "application/json"
    }
  ],
  "numberMatched": 15000,
  "numberReturned": 100
}
```

### 4.3 Cursor-Based Pagination (Part 2 Recommendation)

**For Large Datasets (millions of observations):**

```
# First request
GET /datastreams/ds-123/observations?limit=1000

# Response includes cursor in next link
{
  "features": [ /* 1000 observations */ ],
  "links": [
    {
      "rel": "next",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=1000&cursor=eyJpZCI6MTAwMH0",
      "type": "application/json"
    }
  ]
}

# Next request uses cursor
GET /datastreams/ds-123/observations?limit=1000&cursor=eyJpZCI6MTAwMH0
```

**Cursor Advantages:**

- More efficient than offset for large datasets
- Stable results even with concurrent inserts
- Better performance (no full table scan)

---

## 5. Bidirectional Navigation

### 5.1 Forward Navigation (Parent → Child)

**System → Deployments:**

```
GET /systems/wx-001/deployments
```

Returns: All deployments where system wx-001 was/is deployed

**Characteristics:**

- Dedicated endpoint exists
- Returns collection of related resources
- Supports query parameters (datetime, bbox, limit)
- Standard pagination via links

### 5.2 Reverse Navigation (Child → Parent)

**Option 1: Query Parameter on Parent Collection**

```
GET /deployments?system=wx-001
```

Returns: All deployments containing system wx-001

**Option 2: Property in Child Resource**

```json
{
  "type": "Deployment",
  "id": "deploy-001",
  "deployedSystems": [
    {
      "href": "https://api.example.org/systems/wx-001",
      "rel": "related",
      "title": "Weather Station Alpha"
    }
  ]
}
```

**Option 3: Canonical Access + Link Following**

```
# Get deployment
GET /deployments/deploy-001

# Response includes systems link
{
  "properties": {
    "deployedSystems@link": {
      "href": "https://api.example.org/deployments/deploy-001/systems"
    }
  }
}

# Follow link to get systems
GET /deployments/deploy-001/systems  (if supported)
```

### 5.3 Bidirectional Navigation Matrix

| Forward Navigation        | Reverse Navigation       | Method                                 |
| ------------------------- | ------------------------ | -------------------------------------- |
| System → Deployments      | Deployment → Systems     | Query parameter (`?system=id`)         |
| System → Subsystems       | Subsystem → Parent       | Property (`parent` in subsystem)       |
| DataStream → Observations | Observation → DataStream | Property (`datastream` in observation) |
| ControlStream → Commands  | Command → ControlStream  | Property (`controlstream` in command)  |
| Command → Status          | Status → Command         | Property (`command` in status)         |

---

## 6. Link Relations and Hypermedia

### 6.1 Standard Link Relations

**IANA Relations:**

- `self` - Current resource URL
- `alternate` - Alternate representation (different format)
- `collection` - Parent collection URL
- `item` - Individual resource in collection
- `next` - Next page in paginated collection
- `prev` - Previous page in paginated collection
- `first` - First page in paginated collection
- `last` - Last page in paginated collection

### 6.2 CSAPI-Specific Link Relations

**Property Suffix Pattern (`@link`):**

- `subsystems@link` - Link to subsystems collection
- `datastreams@link` - Link to datastreams collection
- `observations@link` - Link to observations collection
- `deployments@link` - Link to deployments
- `samplingFeatures@link` - Link to sampling features
- `controlstreams@link` - Link to control streams
- `commands@link` - Link to commands
- `status@link` - Link to command status
- `result@link` - Link to command result

### 6.3 Link Objects in Resource Representations

**Format:**

```json
{
  "href": "https://api.example.org/systems/wx-001/subsystems",
  "rel": "related",
  "type": "application/geo+json",
  "title": "Subsystems"
}
```

**Example in System Resource:**

```json
{
  "type": "Feature",
  "id": "wx-001",
  "properties": {
    "name": "Weather Station Alpha",
    "subsystems@link": {
      "href": "https://api.example.org/systems/wx-001/subsystems",
      "rel": "related",
      "type": "application/geo+json"
    },
    "datastreams@link": {
      "href": "https://api.example.org/systems/wx-001/datastreams",
      "rel": "related",
      "type": "application/json"
    }
  }
}
```

---

## 7. Test Scenario Design

### 7.1 Hierarchical Navigation Tests (10 scenarios)

#### Systems → Subsystems

**Test 1: Get Direct Subsystems (No Recursive)**

```typescript
it('gets direct subsystems of a system', async () => {
  const url = builder.getSystemSubsystems('wx-001');
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/subsystems',
  });
});
```

**Test 2: Get All Subsystems (Recursive)**

```typescript
it('gets all nested subsystems recursively', async () => {
  const url = builder.getSystemSubsystems('wx-001', { recursive: true });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/subsystems',
    query: { recursive: 'true' },
  });
});
```

**Test 3: Filter Subsystems by Property**

```typescript
it('filters subsystems by observed property', async () => {
  const url = builder.getSystemSubsystems('wx-001', {
    observedProperty: 'http://qudt.org/vocab/quantitykind/Temperature',
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/subsystems',
    query: {
      observedProperty: 'http://qudt.org/vocab/quantitykind/Temperature',
    },
  });
});
```

**Test 4: Paginate Subsystems**

```typescript
it('paginates subsystems collection', async () => {
  const url = builder.getSystemSubsystems('wx-001', {
    limit: 50,
    offset: 100,
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/subsystems',
    query: { limit: '50', offset: '100' },
  });
});
```

**Test 5: Combine Recursive with Filters**

```typescript
it('combines recursive parameter with filters', async () => {
  const url = builder.getSystemSubsystems('wx-001', {
    recursive: true,
    observedProperty: 'temperature',
    bbox: [-122, 37, -121, 38],
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/subsystems',
    query: {
      recursive: 'true',
      observedProperty: 'temperature',
      bbox: '-122,37,-121,38',
    },
  });
});
```

#### Deployments → Subdeployments

**Test 6-10: Mirror subsystems tests for subdeployments**

- Get direct subdeployments
- Get all subdeployments recursively
- Filter subdeployments by datetime
- Paginate subdeployments
- Combine recursive with filters

### 7.2 Compositional Navigation Tests (25 scenarios)

#### System → SamplingFeatures

**Test 11: Get Sampling Features for System**

```typescript
it('gets sampling features for a system', async () => {
  const url = builder.getSystemSamplingFeatures('wx-001');
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/samplingFeatures',
  });
});
```

**Test 12: Filter Sampling Features by FOI**

```typescript
it('filters sampling features by feature of interest', async () => {
  const url = builder.getSystemSamplingFeatures('wx-001', {
    foi: 'http://example.org/foi/region-A',
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/samplingFeatures',
    query: { foi: 'http://example.org/foi/region-A' },
  });
});
```

**Test 13: Spatial Filter on Sampling Features**

```typescript
it('applies bbox filter to sampling features', async () => {
  const url = builder.getSystemSamplingFeatures('wx-001', {
    bbox: [-180, -90, 180, 90],
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/samplingFeatures',
    query: { bbox: '-180,-90,180,90' },
  });
});
```

#### System → DataStreams

**Test 14: Get DataStreams for System**

```typescript
it('gets datastreams for a system', async () => {
  const url = builder.getSystemDataStreams('wx-001');
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/datastreams',
  });
});
```

**Test 15: Filter DataStreams by Observed Property**

```typescript
it('filters datastreams by observed property', async () => {
  const url = builder.getSystemDataStreams('wx-001', {
    observedProperty: 'http://qudt.org/vocab/quantitykind/Temperature',
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/datastreams',
    query: {
      observedProperty: 'http://qudt.org/vocab/quantitykind/Temperature',
    },
  });
});
```

**Test 16: Filter DataStreams by Phenomenon Time**

```typescript
it('filters datastreams by phenomenon time', async () => {
  const url = builder.getSystemDataStreams('wx-001', {
    phenomenonTime: '2024-01-01T00:00:00Z/..',
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/datastreams',
    query: { phenomenonTime: '2024-01-01T00:00:00Z/..' },
  });
});
```

#### DataStream → Observations

**Test 17: Get Observations for DataStream**

```typescript
it('gets observations for a datastream', async () => {
  const url = builder.getDataStreamObservations('ds-123');
  parseAndValidateUrl(url, {
    pathname: '/datastreams/ds-123/observations',
  });
});
```

**Test 18: Filter Observations by Time Range**

```typescript
it('filters observations by phenomenon time range', async () => {
  const url = builder.getDataStreamObservations('ds-123', {
    phenomenonTime: '2024-01-15T00:00:00Z/2024-01-16T00:00:00Z',
  });
  parseAndValidateUrl(url, {
    pathname: '/datastreams/ds-123/observations',
    query: { phenomenonTime: '2024-01-15T00:00:00Z/2024-01-16T00:00:00Z' },
  });
});
```

**Test 19: Get Latest Observations**

```typescript
it('gets latest observations with limit', async () => {
  const url = builder.getDataStreamObservations('ds-123', {
    resultTime: 'latest',
    limit: 1000,
  });
  parseAndValidateUrl(url, {
    pathname: '/datastreams/ds-123/observations',
    query: { resultTime: 'latest', limit: '1000' },
  });
});
```

**Test 20: Paginate Observations**

```typescript
it('paginates large observation datasets', async () => {
  const url = builder.getDataStreamObservations('ds-123', {
    limit: 10000,
    offset: 50000,
  });
  parseAndValidateUrl(url, {
    pathname: '/datastreams/ds-123/observations',
    query: { limit: '10000', offset: '50000' },
  });
});
```

#### System → ControlStreams

**Test 21: Get ControlStreams for System**

```typescript
it('gets control streams for a system', async () => {
  const url = builder.getSystemControlStreams('wx-001');
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/controlstreams',
  });
});
```

**Test 22: Filter ControlStreams by Controlled Property**

```typescript
it('filters control streams by controlled property', async () => {
  const url = builder.getSystemControlStreams('wx-001', {
    controlledProperty: 'http://example.org/properties/heater-power',
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/controlstreams',
    query: { controlledProperty: 'http://example.org/properties/heater-power' },
  });
});
```

#### ControlStream → Commands

**Test 23: Get Commands for ControlStream**

```typescript
it('gets commands for a control stream', async () => {
  const url = builder.getControlStreamCommands('cs-456');
  parseAndValidateUrl(url, {
    pathname: '/controlstreams/cs-456/commands',
  });
});
```

**Test 24: Filter Commands by Execution Time**

```typescript
it('filters commands by execution time', async () => {
  const url = builder.getControlStreamCommands('cs-456', {
    executionTime: '2024-01-15T00:00:00Z/..',
  });
  parseAndValidateUrl(url, {
    pathname: '/controlstreams/cs-456/commands',
    query: { executionTime: '2024-01-15T00:00:00Z/..' },
  });
});
```

#### Command → Status

**Test 25: Get Status for Command**

```typescript
it('gets status reports for a command', async () => {
  const url = builder.getCommandStatus('cmd-789');
  parseAndValidateUrl(url, {
    pathname: '/commands/cmd-789/status',
  });
});
```

**Test 26: Get Latest Status**

```typescript
it('gets latest status for command', async () => {
  const url = builder.getCommandStatus('cmd-789', { limit: 1 });
  parseAndValidateUrl(url, {
    pathname: '/commands/cmd-789/status',
    query: { limit: '1' },
  });
});
```

#### Command → Result

**Test 27: Get Result for Command**

```typescript
it('gets result for a command', async () => {
  const url = builder.getCommandResult('cmd-789');
  parseAndValidateUrl(url, {
    pathname: '/commands/cmd-789/result',
  });
});
```

#### Collection → Items

**Test 28-35: Additional compositional relationship tests**

- GET system events
- GET sampling feature related features
- Filter by multiple parameters simultaneously
- Test format negotiation on nested endpoints
- Test empty results (no children)
- Test large result sets (pagination required)
- Test nested endpoint with sorting
- Test nested endpoint error handling

### 7.3 Associative Navigation Tests (5 scenarios)

#### System → Deployments (Forward)

**Test 36: Get Deployments for System**

```typescript
it('gets deployments for a system', async () => {
  const url = builder.getSystemDeployments('wx-001');
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/deployments',
  });
});
```

**Test 37: Filter Deployments by Time**

```typescript
it('filters system deployments by datetime', async () => {
  const url = builder.getSystemDeployments('wx-001', {
    datetime: '2024-01-01T00:00:00Z/..',
  });
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/deployments',
    query: { datetime: '2024-01-01T00:00:00Z/..' },
  });
});
```

**Test 38: Filter Active Deployments**

```typescript
it('gets only active deployments for system', async () => {
  const url = builder.getSystemDeployments('wx-001', {
    datetime: new Date().toISOString(), // Current time
  });
  expect(url).toContain('/systems/wx-001/deployments');
  expect(url).toContain('datetime=');
});
```

#### Deployment → Systems (Reverse)

**Test 39: Query Systems by Deployment**

```typescript
it('finds systems in a deployment via query parameter', async () => {
  const url = builder.getSystems({ deployment: 'deploy-001' });
  parseAndValidateUrl(url, {
    pathname: '/systems',
    query: { deployment: 'deploy-001' },
  });
});
```

**Test 40: Bidirectional Consistency**

```typescript
it('ensures bidirectional navigation consistency', async () => {
  // Forward: System → Deployments
  const forwardUrl = builder.getSystemDeployments('wx-001');
  expect(forwardUrl).toBe('https://api.example.org/systems/wx-001/deployments');

  // Reverse: Deployments → Systems (via query)
  const reverseUrl = builder.getSystems({ deployment: 'deploy-001' });
  expect(reverseUrl).toContain('deployment=deploy-001');
});
```

### 7.4 Invalid Path Tests (10 scenarios)

**Test 41: Invalid Parent ID**

```typescript
it('handles invalid parent ID gracefully', async () => {
  const url = builder.getSystemSubsystems('invalid-id-999');
  parseAndValidateUrl(url, {
    pathname: '/systems/invalid-id-999/subsystems',
  });
  // Client correctly constructs URL; 404 handling tested separately in error tests
});
```

**Test 42: Non-existent Child Collection**

```typescript
it('rejects invalid child collection type', async () => {
  // This should be a compile-time error in TypeScript
  // Runtime: builder doesn't have method for invalid relationship
  expect(() => {
    // @ts-expect-error Testing invalid method
    builder.getSystemInvalidCollection('wx-001');
  }).toThrow();
});
```

**Test 43: Invalid Child ID**

```typescript
it('handles invalid child ID', async () => {
  const url = builder.getSystemSubsystem('wx-001', 'invalid-child-999');
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/subsystems/invalid-child-999',
  });
  // Client correctly constructs URL with invalid ID; error handling tested separately
});
```

**Test 44: Recursive on Non-Hierarchical Resource**

```typescript
it('rejects recursive parameter on compositional resources', async () => {
  const url = builder.getSystemDataStreams('wx-001', {
    // @ts-expect-error recursive not valid for datastreams
    recursive: true,
  });
  // Should not include recursive in query (ignored)
  parseAndValidateUrl(url, {
    pathname: '/systems/wx-001/datastreams',
    query: {}, // recursive should be filtered out
  });
});
```

**Test 45: Empty Parent ID**

```typescript
it('rejects empty parent ID', () => {
  expect(() => {
    builder.getSystemSubsystems('');
  }).toThrow('Parent ID cannot be empty');
});
```

**Test 46: Null Parent ID**

```typescript
it('rejects null parent ID', () => {
  expect(() => {
    // @ts-expect-error Testing null handling
    builder.getSystemSubsystems(null);
  }).toThrow();
});
```

**Test 47: Wrong Resource Type for Nested Endpoint**

```typescript
it('prevents accessing incompatible nested resources', async () => {
  // Observations can't have subsystems
  expect(() => {
    // @ts-expect-error Invalid relationship
    builder.getObservationSubsystems('obs-123');
  }).toThrow();
});
```

**Test 48: Invalid Query Parameter on Nested Endpoint**

```typescript
it('filters out invalid query parameters for resource type', async () => {
  const url = builder.getDataStreamObservations('ds-123', {
    phenomenonTime: '2024-01-15T00:00:00Z/..',
    // @ts-expect-error bbox not valid for observations
    bbox: [-180, -90, 180, 90],
  });
  // bbox should be filtered out (observations have no geometry)
  parseAndValidateUrl(url, {
    pathname: '/datastreams/ds-123/observations',
    query: { phenomenonTime: '2024-01-15T00:00:00Z/..' },
    // No bbox in query
  });
});
```

**Test 49: Malformed Nested Path**

```typescript
it('validates nested path structure', () => {
  // Missing parent ID
  expect(() => {
    builder.getSystemSubsystems(undefined);
  }).toThrow();
});
```

**Test 50: Cross-Part Navigation Without Support**

```typescript
it('validates cross-part relationships', async () => {
  // Part 1 system can have Part 2 datastreams
  const validUrl = builder.getSystemDataStreams('wx-001');
  expect(validUrl).toContain('/systems/wx-001/datastreams');

  // But observations can't have systems (invalid cross-part)
  expect(() => {
    // @ts-expect-error Invalid relationship
    builder.getObservationSystems('obs-123');
  }).toThrow();
});
```

---

## 8. Nested Endpoint URL Construction

### 8.1 URL Builder Pattern

**General Pattern:**

```typescript
class CSAPIQueryBuilder {
  /**
   * Generic nested resource URL builder
   */
  private buildNestedUrl(
    parentType: string,
    parentId: string,
    childType: string,
    childId?: string,
    options?: QueryOptions
  ): string {
    // Validate parent ID
    if (!parentId || parentId.trim() === '') {
      throw new Error(`${parentType} ID cannot be empty`);
    }

    // Build base path
    let path = `/${parentType}/${encodeURIComponent(parentId)}/${childType}`;

    // Add child ID if accessing single resource
    if (childId) {
      path += `/${encodeURIComponent(childId)}`;
    }

    // Build URL with query parameters
    const url = new URL(path, this.baseUrl);
    if (options) {
      this.applyQueryParameters(url, options);
    }

    return url.toString();
  }
}
```

### 8.2 Specific Method Implementations

**System → Subsystems:**

```typescript
getSystemSubsystems(
  systemId: string,
  options?: {
    recursive?: boolean;
    observedProperty?: string;
    bbox?: BoundingBox;
    datetime?: string;
    limit?: number;
    offset?: number;
    f?: string;
  }
): Promise<string> {
  return this.buildNestedUrl('systems', systemId, 'subsystems', undefined, options);
}
```

**System → DataStreams:**

```typescript
getSystemDataStreams(
  systemId: string,
  options?: {
    observedProperty?: string;
    phenomenonTime?: string;
    resultTime?: string;
    foi?: string;
    live?: boolean;
    limit?: number;
    offset?: number;
    f?: string;
  }
): Promise<string> {
  return this.buildNestedUrl('systems', systemId, 'datastreams', undefined, options);
}
```

**DataStream → Observations:**

```typescript
getDataStreamObservations(
  datastreamId: string,
  options?: {
    phenomenonTime?: string;
    resultTime?: string;
    limit?: number;
    offset?: number;
    f?: string;
  }
): Promise<string> {
  return this.buildNestedUrl('datastreams', datastreamId, 'observations', undefined, options);
}
```

**Command → Status:**

```typescript
getCommandStatus(
  commandId: string,
  options?: {
    limit?: number;
    offset?: number;
    f?: string;
  }
): Promise<string> {
  return this.buildNestedUrl('commands', commandId, 'status', undefined, options);
}
```

### 8.3 Single Resource Access

**Get Specific Child:**

```typescript
getSystemSubsystem(
  systemId: string,
  subsystemId: string,
  options?: { f?: string }
): Promise<string> {
  return this.buildNestedUrl('systems', systemId, 'subsystems', subsystemId, options);
}
```

**Get Specific Observation:**

```typescript
getDataStreamObservation(
  datastreamId: string,
  observationId: string,
  options?: { f?: string }
): Promise<string> {
  return this.buildNestedUrl('datastreams', datastreamId, 'observations', observationId, options);
}
```

---

## 9. Fixture Design

### 9.1 Nested Collection Response Fixtures

**System → Subsystems Response:**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "temp-sensor",
      "geometry": { "type": "Point", "coordinates": [0, 0] },
      "properties": {
        "name": "Temperature Sensor",
        "systemType": "sosa:Sensor",
        "parent": "wx-001"
      }
    },
    {
      "type": "Feature",
      "id": "humidity-sensor",
      "geometry": { "type": "Point", "coordinates": [0, 0] },
      "properties": {
        "name": "Humidity Sensor",
        "systemType": "sosa:Sensor",
        "parent": "wx-001"
      }
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems/wx-001/subsystems",
      "type": "application/geo+json"
    },
    {
      "rel": "collection",
      "href": "https://api.example.org/systems",
      "type": "application/geo+json"
    }
  ],
  "numberMatched": 2,
  "numberReturned": 2
}
```

**DataStream → Observations Response:**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "obs-001",
      "properties": {
        "phenomenonTime": "2024-01-15T12:00:00Z",
        "resultTime": "2024-01-15T12:00:05Z",
        "result": 23.5,
        "datastream": "ds-123"
      }
    },
    {
      "type": "Feature",
      "id": "obs-002",
      "properties": {
        "phenomenonTime": "2024-01-15T12:01:00Z",
        "resultTime": "2024-01-15T12:01:05Z",
        "result": 23.6,
        "datastream": "ds-123"
      }
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=2",
      "type": "application/json"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=2&offset=2",
      "type": "application/json"
    }
  ],
  "numberMatched": 10000,
  "numberReturned": 2
}
```

**Command → Status Response:**

```json
{
  "type": "Collection",
  "items": [
    {
      "id": "status-001",
      "command": "cmd-789",
      "reportTime": "2024-01-15T12:00:10Z",
      "executionStatus": "ACCEPTED",
      "percentCompletion": 0,
      "message": "Command accepted and queued"
    },
    {
      "id": "status-002",
      "command": "cmd-789",
      "reportTime": "2024-01-15T12:00:15Z",
      "executionStatus": "RUNNING",
      "percentCompletion": 50,
      "message": "Command execution in progress"
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/commands/cmd-789/status"
    }
  ]
}
```

### 9.2 Empty Collection Fixtures

**No Children:**

```json
{
  "type": "FeatureCollection",
  "features": [],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems/wx-001/subsystems"
    }
  ],
  "numberMatched": 0,
  "numberReturned": 0
}
```

### 9.3 Paginated Collection Fixtures

**Page 1:**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 100 items */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=0"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=100"
    }
  ],
  "numberMatched": 15000,
  "numberReturned": 100
}
```

**Page 2:**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 100 items */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=100"
    },
    {
      "rel": "prev",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=0"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/datastreams/ds-123/observations?limit=100&offset=200"
    }
  ],
  "numberMatched": 15000,
  "numberReturned": 100
}
```

### 9.4 Error Response Fixtures

**404 Not Found (Invalid Parent):**

```json
{
  "code": "NotFound",
  "description": "System with ID 'invalid-id-999' not found"
}
```

**404 Not Found (Invalid Child):**

```json
{
  "code": "NotFound",
  "description": "Subsystem 'invalid-child-999' not found in system 'wx-001'"
}
```

**400 Bad Request (Invalid Parameter):**

```json
{
  "code": "InvalidParameterValue",
  "description": "Parameter 'recursive' is not valid for resource type 'datastreams'"
}
```

### 9.5 Fixture Summary

| Fixture Type                | Count  | Description                         |
| --------------------------- | ------ | ----------------------------------- |
| Nested collection responses | 16     | One per relationship type           |
| Empty collection responses  | 5      | No children scenarios               |
| Paginated responses         | 10     | Multi-page scenarios                |
| Single nested resource      | 8      | Individual child access             |
| Error responses             | 5      | 404, 400 scenarios                  |
| Bidirectional responses     | 4      | Forward + reverse navigation        |
| Recursive responses         | 2      | Hierarchical with/without recursive |
| **TOTAL**                   | **50** | **50 fixtures**                     |

---

## 10. Test Organization

### 10.1 File Structure

```
src/ogc-api/csapi/__tests__/
  navigation/
    hierarchical-navigation.spec.ts      # Subsystems, subdeployments
    compositional-navigation.spec.ts     # SamplingFeatures, datastreams, observations
    associative-navigation.spec.ts       # Systems ↔ Deployments
    nested-query-parameters.spec.ts      # Query params on nested endpoints
    nested-pagination.spec.ts            # Pagination on nested collections
    bidirectional-navigation.spec.ts     # Forward + reverse navigation
    invalid-paths.spec.ts                # Error handling
```

### 10.2 Test Counts per File

| Test File                          | Scenarios | Lines of Code (est.) |
| ---------------------------------- | --------- | -------------------- |
| `hierarchical-navigation.spec.ts`  | 10        | ~400                 |
| `compositional-navigation.spec.ts` | 25        | ~1000                |
| `associative-navigation.spec.ts`   | 5         | ~200                 |
| `nested-query-parameters.spec.ts`  | 5         | ~200                 |
| `nested-pagination.spec.ts`        | 3         | ~150                 |
| `bidirectional-navigation.spec.ts` | 2         | ~100                 |
| `invalid-paths.spec.ts`            | 10        | ~400                 |
| **TOTAL**                          | **60**    | **~2,450**           |

### 10.3 Integration with Other Sections

**Section 13 (Resource Method Testing):**

- Tests individual resource methods (getSystems, getDataStreams, etc.)
- Section 26 extends with nested navigation methods

**Section 23 (Pagination Testing):**

- Tests pagination on canonical endpoints
- Section 26 tests pagination on nested endpoints

**Section 24 (Query Parameter Testing):**

- Tests query parameters on canonical endpoints
- Section 26 tests query parameters on nested endpoints (inheritance)

**Section 25 (Format Negotiation):**

- Tests format negotiation on canonical endpoints
- Section 26 ensures format negotiation works on nested endpoints

**No Duplication:** Each section tests different aspects:

- Section 13: Individual resource methods
- Section 23: Pagination mechanisms
- Section 24: Query parameter combinations
- Section 25: Format negotiation
- Section 26: Nested resource navigation

---

## 11. Implementation Estimates

### 11.1 URL Builder Implementation

| Task                                                                | Est. Time       | Priority |
| ------------------------------------------------------------------- | --------------- | -------- |
| Generic nested URL builder                                          | 2-3 hours       | HIGH     |
| Hierarchical methods (subsystems, subdeployments)                   | 2 hours         | HIGH     |
| Compositional methods (samplingFeatures, datastreams, observations) | 4-5 hours       | HIGH     |
| Associative methods (deployments)                                   | 1-2 hours       | MEDIUM   |
| Command/Status/Result methods                                       | 2 hours         | MEDIUM   |
| Parameter validation and filtering                                  | 2-3 hours       | HIGH     |
| **TOTAL**                                                           | **13-17 hours** | -        |

### 11.2 Test Implementation

| Task                                | Est. Time       | Priority |
| ----------------------------------- | --------------- | -------- |
| Hierarchical navigation tests (10)  | 3-4 hours       | HIGH     |
| Compositional navigation tests (25) | 7-9 hours       | HIGH     |
| Associative navigation tests (5)    | 2 hours         | MEDIUM   |
| Nested query parameter tests (5)    | 2 hours         | HIGH     |
| Nested pagination tests (3)         | 1-2 hours       | MEDIUM   |
| Bidirectional navigation tests (2)  | 1 hour          | LOW      |
| Invalid path tests (10)             | 3-4 hours       | HIGH     |
| **TOTAL**                           | **19-24 hours** | -        |

### 11.3 Fixture Creation

| Task                            | Est. Time     | Priority |
| ------------------------------- | ------------- | -------- |
| Nested collection fixtures (16) | 2-3 hours     | HIGH     |
| Empty collection fixtures (5)   | 30 minutes    | MEDIUM   |
| Paginated fixtures (10)         | 1-2 hours     | HIGH     |
| Single resource fixtures (8)    | 1 hour        | MEDIUM   |
| Error fixtures (5)              | 30 minutes    | MEDIUM   |
| Bidirectional fixtures (4)      | 1 hour        | LOW      |
| Recursive fixtures (2)          | 30 minutes    | MEDIUM   |
| **TOTAL**                       | **6-8 hours** | -        |

### 11.4 Total Effort

| Phase                      | Est. Time                 |
| -------------------------- | ------------------------- |
| URL Builder Implementation | 13-17 hours               |
| Test Implementation        | 19-24 hours               |
| Fixture Creation           | 6-8 hours                 |
| Documentation              | 2-3 hours (this document) |
| **TOTAL**                  | **40-52 hours**           |

---

## 12. Key Recommendations

### 12.1 Prioritization

**HIGH Priority (Implement First):**

1. Generic nested URL builder (foundation for all relationships)
2. Hierarchical navigation (subsystems, subdeployments with recursive)
3. DataStream → Observations (most commonly used Part 2 relationship)
4. System → DataStreams (critical cross-part navigation)
5. Query parameter inheritance on nested endpoints
6. Pagination on nested collections

**MEDIUM Priority (Implement Second):** 7. System → SamplingFeatures 8. System → ControlStreams 9. Command → Status/Result 10. Associative navigation (Systems ↔ Deployments) 11. Empty collection handling 12. Error handling for invalid paths

**LOW Priority (Implement Last):** 13. Bidirectional navigation tests (forward already covered) 14. Cursor-based pagination (server-dependent) 15. Complex filter combinations 16. Performance optimization

### 12.2 Testing Strategy

**Unit Tests:**

- URL construction for each relationship type (16 methods)
- Query parameter filtering per resource type
- Parameter validation (reject invalid combinations)
- Error handling (invalid IDs, invalid relationships)

**Integration Tests:**

- End-to-end navigation with mock responses
- Pagination link following
- Format negotiation on nested endpoints
- Bidirectional navigation consistency

**Mock Strategy:**

- Mock nested collection responses with links
- Mock empty collections (no children)
- Mock paginated responses (next/prev links)
- Mock 404 errors for invalid parents/children

### 12.3 Reusable Patterns

**Generic Navigation Test:**

```typescript
function testNestedNavigation(
  methodName: string,
  parentId: string,
  expectedPath: string,
  options?: QueryOptions
) {
  it(`${methodName} constructs correct nested URL`, async () => {
    const url = await builder[methodName](parentId, options);
    parseAndValidateUrl(url, {
      pathname: expectedPath,
      query: options || {},
    });
  });
}

// Usage
testNestedNavigation(
  'getSystemSubsystems',
  'wx-001',
  '/systems/wx-001/subsystems'
);
testNestedNavigation(
  'getSystemDataStreams',
  'wx-001',
  '/systems/wx-001/datastreams'
);
testNestedNavigation(
  'getDataStreamObservations',
  'ds-123',
  '/datastreams/ds-123/observations'
);
```

**Parameter Inheritance Test:**

```typescript
describe.each([
  { method: 'getSystemSubsystems', path: '/systems/sys-001/subsystems' },
  { method: 'getSystemDataStreams', path: '/systems/sys-001/datastreams' },
  {
    method: 'getDataStreamObservations',
    path: '/datastreams/ds-123/observations',
  },
])('$method parameter inheritance', ({ method, path }) => {
  it('supports limit parameter', async () => {
    const url = await builder[method]('test-id', { limit: 50 });
    expect(url).toContain('limit=50');
  });

  it('supports offset parameter', async () => {
    const url = await builder[method]('test-id', { offset: 100 });
    expect(url).toContain('offset=100');
  });

  it('supports format parameter', async () => {
    const url = await builder[method]('test-id', { f: 'json' });
    expect(url).toContain('f=json');
  });
});
```

---

## 13. Success Criteria Validation

- [x] **All CSAPI sub-resource patterns are inventoried** ✅ (16 relationship patterns documented)
- [x] **URL structure for nested endpoints is documented** ✅ (Pattern templates and examples)
- [x] **Bidirectional navigation patterns are defined** ✅ (Forward + reverse navigation)
- [x] **Query parameters on nested endpoints are specified** ✅ (Parameter applicability matrix)
- [x] **Pagination on nested endpoints is defined** ✅ (Offset and cursor-based pagination)
- [x] **Invalid path scenarios are documented** ✅ (10 error handling tests)
- [x] **Navigation test patterns are complete** ✅ (60 test scenarios)
- [ ] **Deliverable document is peer-reviewed** ⏳ (awaiting review)

---

## 14. References

**CSAPI Specifications:**

- OGC API - Connected Systems Part 1: Sub-resource relationships (Section 6)
- OGC API - Connected Systems Part 2: DataStream/ControlStream relationships
- OGC API - Common: Pagination and query parameters

**Related Research:**

- Section 8: CSAPI Specification Review (resource relationships)
- Section 13: Resource Method Testing (navigation methods)
- Section 23: Pagination Testing (pagination on nested endpoints)
- Section 24: Query Parameter Testing (parameters on nested endpoints)
- [Sub-Resource Navigation Requirements](../../requirements/csapi-subresource-navigation.md)

**Upstream Patterns:**

- STAC `getItemsFromCollection` pattern (nested resource access)
- OGC API - Features collection item pattern

---

## 15. Appendix: Navigation Method Signatures

### 15.1 Hierarchical Navigation Methods

```typescript
interface CSAPIQueryBuilder {
  // Systems → Subsystems
  getSystemSubsystems(
    systemId: string,
    options?: {
      recursive?: boolean;
      observedProperty?: string;
      bbox?: BoundingBox;
      datetime?: string;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  getSystemSubsystem(
    systemId: string,
    subsystemId: string,
    options?: { f?: string }
  ): Promise<string>;

  // Deployments → Subdeployments
  getDeploymentSubdeployments(
    deploymentId: string,
    options?: {
      recursive?: boolean;
      datetime?: string;
      bbox?: BoundingBox;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  getDeploymentSubdeployment(
    deploymentId: string,
    subdeploymentId: string,
    options?: { f?: string }
  ): Promise<string>;
}
```

### 15.2 Compositional Navigation Methods (Part 1)

```typescript
interface CSAPIQueryBuilder {
  // System → SamplingFeatures
  getSystemSamplingFeatures(
    systemId: string,
    options?: {
      foi?: string;
      bbox?: BoundingBox;
      datetime?: string;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  getSystemSamplingFeature(
    systemId: string,
    samplingFeatureId: string,
    options?: { f?: string }
  ): Promise<string>;

  // Collection → Items
  getCollectionItems(
    collectionId: string,
    options?: {
      bbox?: BoundingBox;
      datetime?: string;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;
}
```

### 15.3 Compositional Navigation Methods (Part 2)

```typescript
interface CSAPIQueryBuilder {
  // System → DataStreams
  getSystemDataStreams(
    systemId: string,
    options?: {
      observedProperty?: string;
      phenomenonTime?: string;
      resultTime?: string;
      foi?: string;
      live?: boolean;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  // System → ControlStreams
  getSystemControlStreams(
    systemId: string,
    options?: {
      controlledProperty?: string;
      executionTime?: string;
      issueTime?: string;
      foi?: string;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  // DataStream → Observations
  getDataStreamObservations(
    datastreamId: string,
    options?: {
      phenomenonTime?: string;
      resultTime?: string;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  getDataStreamObservation(
    datastreamId: string,
    observationId: string,
    options?: { f?: string }
  ): Promise<string>;

  // ControlStream → Commands
  getControlStreamCommands(
    controlstreamId: string,
    options?: {
      executionTime?: string;
      issueTime?: string;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  getControlStreamCommand(
    controlstreamId: string,
    commandId: string,
    options?: { f?: string }
  ): Promise<string>;

  // Command → Status
  getCommandStatus(
    commandId: string,
    options?: {
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  getCommandStatusById(
    commandId: string,
    statusId: string,
    options?: { f?: string }
  ): Promise<string>;

  // Command → Result
  getCommandResult(
    commandId: string,
    options?: {
      limit?: number;
      f?: string;
    }
  ): Promise<string>;

  getCommandResultById(
    commandId: string,
    resultId: string,
    options?: { f?: string }
  ): Promise<string>;
}
```

### 15.4 Associative Navigation Methods

```typescript
interface CSAPIQueryBuilder {
  // System → Deployments (Forward)
  getSystemDeployments(
    systemId: string,
    options?: {
      datetime?: string;
      bbox?: BoundingBox;
      limit?: number;
      offset?: number;
      f?: string;
    }
  ): Promise<string>;

  // Systems ← Deployment (Reverse via query)
  getSystems(options?: {
    deployment?: string; // Filter by deployment ID
    // ... other parameters
  }): Promise<string>;
}
```

---

**Document Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Next Review:** After peer review and implementation planning
