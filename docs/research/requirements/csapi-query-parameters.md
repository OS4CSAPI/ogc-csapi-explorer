# Section 4: Query Parameter Requirements

## Overview

This section documents ALL query parameters defined in CSAPI Part 1 and Part 2, their encoding rules, validation requirements, and client library implementation needs. Query parameters enable filtering, pagination, format negotiation, and relationship-based queries across all CSAPI resource types.

**Key Objectives:**

- Catalog all standard OGC API and CSAPI-specific query parameters
- Define parameter types (spatial, temporal, pagination, format, relationship)
- Document encoding rules for each parameter type
- Establish validation requirements and constraints
- Define parameter combination rules and precedence
- Document resource-specific parameter applicability
- Define client API surface for query building

---

## Query Parameter Classification

### Parameter Categories

1. **Standard OGC API Parameters** (inherited from OGC API - Common / Features)

   - bbox, datetime, limit, offset, f

2. **CSAPI Common Parameters** (apply to all Part 1 resources)

   - id, uid, q, {propertyName}

3. **CSAPI Hierarchical Parameters** (Part 1)

   - recursive

4. **CSAPI Relationship Parameters** (Part 1 resource-specific)

   - parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType

5. **CSAPI Temporal Parameters** (Part 2 observation/command-specific)

   - phenomenonTime, resultTime, executionTime, issueTime

6. **Format Negotiation Parameters**

   - f, format, obsFormat, cmdFormat

7. **Pagination Parameters**
   - limit, offset, cursor (Part 2)

---

## Standard OGC API Parameters

### bbox (Bounding Box Filter)

**Standard:** OGC API - Features Part 1, Clause 7.15.3  
**Type:** Spatial filter  
**Format:** Comma-separated coordinates  
**Encoding:** `minLon,minLat,maxLon,maxLat[,minElev,maxElev]`

**Applies To:**

- Part 1: Systems, Deployments, Procedures, SamplingFeatures (resources with geometry)
- Filters resources whose geometry intersects bounding box

**Coordinate Reference System:**

- Default: WGS84 (lon, lat order)
- Optional: CRS84 (lon, lat order) - explicitly specified via bbox-crs parameter
- CSAPI uses WGS84/CRS84 only (no other CRS support)

**2D Bounding Box:**

```
GET /systems?bbox=-180,-90,180,90
// minLon=-180, minLat=-90, maxLon=180, maxLat=90
```

**3D Bounding Box:**

```
GET /systems?bbox=-180,-90,0,180,90,1000
// minLon=-180, minLat=-90, minElev=0, maxLon=180, maxLat=90, maxElev=1000
```

**Validation Rules:**

- minLon ≤ maxLon
- minLat ≤ maxLat
- minElev ≤ maxElev (if provided)
- Latitude range: -90 to 90
- Longitude range: -180 to 180
- Elevation: any numeric value (meters above WGS84 ellipsoid)

**Edge Cases:**

- Antimeridian crossing: minLon > maxLon is INVALID (server returns 400)
- Point geometry: minLon = maxLon and minLat = maxLat is VALID
- Empty result: bbox with no intersecting resources returns empty collection

**Client API Implications:**

```typescript
interface BBoxFilter {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
  minElev?: number;
  maxElev?: number;
}

// Usage
client.systems.list({
  bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
});

// Encodes to: ?bbox=-180,-90,180,90
```

---

### datetime (Temporal Filter)

**Standard:** OGC API - Features Part 1, Clause 7.15.4  
**Type:** Temporal filter  
**Format:** ISO 8601 datetime or interval  
**Encoding:** `instant`, `start/end`, `start/..`, `../end`

**Applies To:**

- Part 1: Systems, Deployments (filters by validTime property)
- Part 2: DataStreams, ControlStreams (filters by validTime property)
- Part 2: Observations (filters by phenomenonTime - use phenomenonTime parameter instead)
- Part 2: Commands (filters by executionTime - use executionTime parameter instead)

**Single Instant:**

```
GET /systems?datetime=2024-01-15T12:00:00Z
// Resources with validTime intersecting instant
```

**Closed Interval:**

```
GET /deployments?datetime=2024-01-01T00:00:00Z/2024-12-31T23:59:59Z
// Resources with validTime intersecting interval [start, end]
```

**Open Start (before end):**

```
GET /systems?datetime=../2024-12-31T23:59:59Z
// Resources with validTime before end time
```

**Open End (after start):**

```
GET /deployments?datetime=2024-01-01T00:00:00Z/..
// Resources with validTime after start time
```

**ISO 8601 Formats Supported:**

- Date only: `2024-01-15` (treated as start of day UTC)
- Date + time: `2024-01-15T12:00:00Z`
- Date + time + timezone: `2024-01-15T12:00:00+05:00`
- Date + time + fractional seconds: `2024-01-15T12:00:00.123Z`

**Validation Rules:**

- MUST be valid ISO 8601 format
- Start MUST be before end (for closed intervals)
- Timezone SHOULD be specified (defaults to UTC if omitted)
- Open intervals MUST use `..` for open end

**Resource-Specific Behavior:**

- Part 1: Applies to `validTime` property (time period description is valid)
- Part 2 DataStreams: Applies to `validTime` property (description validity)
- Part 2 Observations: Use `phenomenonTime` parameter instead
- Part 2 Commands: Use `executionTime` parameter instead

**Client API Implications:**

```typescript
type DateTimeFilter =
  | string // ISO 8601 instant or interval
  | Date // Single instant
  | { start: Date | string; end?: Date | string } // Interval
  | { start?: Date | string; end: Date | string }; // Interval

// Usage examples
client.systems.list({ datetime: '2024-01-15T12:00:00Z' });
client.systems.list({ datetime: new Date('2024-01-15') });
client.systems.list({ datetime: { start: '2024-01-01', end: '2024-12-31' } });
client.systems.list({ datetime: { start: '2024-01-01' } }); // Open end

// Encodes to: ?datetime=2024-01-15T12:00:00Z
// Encodes to: ?datetime=2024-01-01T00:00:00.000Z/2024-12-31T00:00:00.000Z
// Encodes to: ?datetime=2024-01-01T00:00:00.000Z/..
```

---

### limit (Pagination)

**Standard:** OGC API - Features Part 1, Clause 7.15.7  
**Type:** Pagination  
**Format:** Positive integer  
**Default:** Implementation-dependent (typically 10-100)

**Applies To:**

- All collection endpoints (systems, deployments, procedures, samplingFeatures, properties)
- Part 2: DataStreams, ControlStreams, Observations, Commands, CommandStatus, CommandResult, SystemEvents

**Constraints:**

- Part 1: Minimum 1, maximum implementation-dependent
- Part 2: Minimum 1, maximum 10,000 (specified in Part 2)
- Server MAY return fewer than requested (e.g., last page)
- Server MAY enforce lower maximum than client requests

**Usage:**

```
GET /systems?limit=50
// Return at most 50 systems
```

**Combined with Other Filters:**

```
GET /systems?bbox=-180,-90,180,90&datetime=2024-01-01T00:00:00Z/..&limit=100
// Return at most 100 systems matching bbox AND datetime filters
```

**Pagination Pattern:**

```
GET /systems?limit=10
// First page (10 items)

GET /systems?limit=10&offset=10
// Second page (next 10 items)

GET /systems?limit=10&offset=20
// Third page (next 10 items)
```

**Validation Rules:**

- MUST be positive integer
- MUST be ≥ 1
- MUST be ≤ server maximum (Part 2: 10,000)
- Invalid value → 400 Bad Request

**Client API Implications:**

```typescript
interface PaginationOptions {
  limit?: number; // Default: server default (10-100)
  offset?: number; // Default: 0
}

// Usage
client.systems.list({ limit: 50 });
client.systems.list({ limit: 50, offset: 100 });

// Auto-pagination helper
for await (const system of client.systems.listAll({ limit: 100 })) {
  console.log(system.name);
}
```

---

### offset (Pagination)

**Standard:** OGC API - Features Part 1, Clause 7.15.7  
**Type:** Pagination  
**Format:** Non-negative integer  
**Default:** 0

**Applies To:**

- All collection endpoints (Part 1 and Part 2)
- Works in conjunction with `limit` parameter

**Usage:**

```
GET /systems?offset=20
// Skip first 20 systems, return remaining (up to limit)

GET /systems?limit=10&offset=20
// Skip first 20 systems, return next 10
```

**Validation Rules:**

- MUST be non-negative integer (≥ 0)
- offset=0 is equivalent to omitting parameter
- offset beyond result set → empty collection (not error)
- Invalid value → 400 Bad Request

**Performance Considerations:**

- Large offset values can be inefficient (server must count and skip N items)
- For Part 2 observations, prefer cursor-based pagination or temporal windowing
- Part 2 servers MAY support cursor-based pagination as alternative

**Client API Implications:**

```typescript
// Standard offset pagination
client.systems.list({ limit: 10, offset: 0 }); // Page 1
client.systems.list({ limit: 10, offset: 10 }); // Page 2
client.systems.list({ limit: 10, offset: 20 }); // Page 3

// Helper for calculating offset
function getPage(pageNumber: number, pageSize: number) {
  return client.systems.list({
    limit: pageSize,
    offset: (pageNumber - 1) * pageSize,
  });
}
```

---

### f (Format Negotiation)

**Standard:** OGC API - Common Part 1  
**Type:** Format negotiation  
**Format:** String (short format name or full media type)  
**Aliases:** `format` (full media type)

**Applies To:**

- All resource endpoints (both individual and collections)
- Takes precedence over Accept header

**Part 1 Short Format Names:**

- `geojson` → `application/geo+json`
- `sml` → `application/sml+json`
- `json` → `application/json`

**Part 2 Format Names:**

- MUST use full media type (no short names defined)
- `application/json`
- `application/swe+json`
- `application/swe+text` (or `application/swe+csv`)
- `application/swe+binary`

**Usage:**

```
GET /systems/sys123?f=geojson
// Returns system in GeoJSON format

GET /systems/sys123?f=sml
// Returns system in SensorML format

GET /datastreams/ds123/observations?f=application/swe+binary
// Returns observations in SWE Common binary format
```

**URL Encoding:**

- `+` character MUST be URL-encoded as `%2B`
- Example: `application/swe+json` → `application/swe%2Bjson`
- Correct: `?f=application/swe%2Bjson`
- Incorrect: `?f=application/swe+json` (+ interpreted as space)

**Validation Rules:**

- Server returns 406 Not Acceptable if format not supported
- Client SHOULD check supported formats before requesting
- Server MUST advertise supported formats (Part 2: `formats` property)

**Format Selection Precedence:**

1. Query parameter `f` or `format` (highest priority)
2. Accept header
3. Server default format
4. 406 Not Acceptable if none match

**Client API Implications:**

```typescript
// Format parameter
client.systems.get('sys123', { format: 'application/geo+json' });
client.observations.list('ds123', { format: 'application/swe+binary' });

// Automatic URL encoding
const format = 'application/swe+json';
const encoded = encodeURIComponent(format); // 'application%2Fswe%2Bjson'

// Format-specific convenience methods
client.systems.getAsGeoJSON('sys123');
client.systems.getAsSensorML('sys123');
client.observations.listAsBinary('ds123');
```

**See Also:** Section 3.1 (Common Format Requirements) for complete format negotiation details

---

## CSAPI Common Parameters (Part 1)

### id (Identifier Filter)

**Standard:** CSAPI Part 1  
**Type:** Identifier filter  
**Format:** Comma-separated list of local IDs  
**Applies To:** All Part 1 resources

**Usage:**

```
GET /systems?id=sys123
// Single system by local ID

GET /systems?id=sys123,sys456,sys789
// Multiple systems by local IDs (logical OR)
```

**Behavior:**

- Filters resources by local resource ID (assigned by server)
- Multiple IDs treated as logical OR
- Case-sensitive matching
- Unknown IDs silently excluded (no error)
- Empty result if no IDs match

**Validation Rules:**

- Each ID must be valid local identifier format
- No whitespace around commas (or must be URL-encoded)
- Empty ID value → 400 Bad Request

**Client API Implications:**

```typescript
type IDFilter = string | string[];

// Usage
client.systems.list({ id: 'sys123' });
client.systems.list({ id: ['sys123', 'sys456', 'sys789'] });

// Encodes to: ?id=sys123,sys456,sys789
```

---

### uid (Unique Identifier Filter)

**Standard:** CSAPI Part 1  
**Type:** Identifier filter  
**Format:** Comma-separated list of URIs  
**Applies To:** All Part 1 resources

**Usage:**

```
GET /systems?uid=urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255
// Single system by UID

GET /systems?uid=urn:uuid:abc,urn:example:sys:123
// Multiple systems by UIDs (logical OR)
```

**UID Formats:**

- URN: `urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255`
- HTTP URI: `http://example.org/sensors/wx-001`
- Custom URI scheme: `urn:example:sensor:12345`

**Behavior:**

- Filters resources by globally unique identifier
- Multiple UIDs treated as logical OR
- Exact match (case-sensitive for URI schemes, case-insensitive for domain names per URI spec)
- Unknown UIDs silently excluded
- Empty result if no UIDs match

**URL Encoding:**

- URI special characters MUST be URL-encoded
- `:` → `%3A`
- `/` → `%2F`
- Example: `urn:uuid:abc` → `urn%3Auuid%3Aabc`

**Validation Rules:**

- Each UID must be valid URI format
- No whitespace around commas
- Invalid URI format → 400 Bad Request

**Client API Implications:**

```typescript
type UIDFilter = string | string[];

// Usage
client.systems.list({ uid: 'urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255' });
client.systems.list({
  uid: ['urn:uuid:abc', 'http://example.org/sensors/wx-001'],
});

// Automatic URL encoding
function encodeUID(uid: string): string {
  return encodeURIComponent(uid);
}

// Encodes to: ?uid=urn%3Auuid%3A31f6865e-f438-430e-9b57-f965a21ee255
```

---

### q (Keyword Search)

**Standard:** CSAPI Part 1  
**Type:** Full-text search filter  
**Format:** String (keyword or phrase)  
**Applies To:** All Part 1 resources

**Usage:**

```
GET /systems?q=weather%20station
// Search for "weather station" across system properties

GET /deployments?q=arctic
// Search for "arctic" across deployment properties
```

**Search Scope:**

- Searches across multiple resource properties
- Implementation-dependent which properties are searchable
- Typically: name, description, label, keywords
- May include nested properties (e.g., system names in deployment)

**Search Behavior:**

- Implementation-dependent (case-insensitive recommended)
- May support partial matching (substring search)
- May support tokenization (word boundaries)
- May support stemming (run → running, runs)
- May support stop word removal (the, a, an)

**URL Encoding:**

- Spaces MUST be URL-encoded as `%20` or `+`
- Special characters MUST be URL-encoded
- Example: `weather station` → `weather%20station` or `weather+station`

**Validation Rules:**

- Empty string → ignored (no filtering)
- Whitespace-only → ignored
- No length limit (server may impose limits)

**Client API Implications:**

```typescript
type KeywordFilter = string;

// Usage
client.systems.list({ q: 'weather station' });
client.deployments.list({ q: 'arctic mission' });

// Automatic URL encoding
function encodeKeyword(keyword: string): string {
  return encodeURIComponent(keyword);
}

// Encodes to: ?q=weather%20station
```

---

### {propertyName} (Property Filter)

**Standard:** CSAPI Part 1  
**Type:** Property-value filter  
**Format:** `{propertyName}={value}`  
**Applies To:** All Part 1 resources

**Usage:**

```
GET /systems?name=Weather%20Station
// Filter systems by exact name match

GET /systems?featureType=sosa:Sensor
// Filter systems by featureType property

GET /deployments?assetType=Equipment
// Filter deployments by assetType property
```

**Supported Properties:**

- Any resource property can be filtered
- Common properties: name, description, featureType, assetType
- Nested properties: Not supported (only top-level properties)

**Matching Behavior:**

- Exact match (case-sensitive recommended)
- String properties: Exact string match
- Enum properties: Exact enum value match
- Numeric properties: Exact numeric match
- URI properties: Exact URI match

**Multiple Values:**

- Not supported in Part 1 (use multiple requests or relationship parameters)
- Comma-separated values NOT treated as OR (literal comma in value)

**URL Encoding:**

- Property name: No encoding needed (alphanumeric + underscore)
- Property value: MUST be URL-encoded
- Example: `name=Weather%20Station%20Alpha`

**Validation Rules:**

- Property name must exist on resource type
- Unknown property → 400 Bad Request or ignored (implementation-dependent)
- Property value must match property type
- Invalid value for property type → 400 Bad Request

**Client API Implications:**

```typescript
interface PropertyFilters {
  [propertyName: string]: string | number | boolean;
}

// Usage
client.systems.list({
  name: 'Weather Station',
  featureType: 'sosa:Sensor',
  assetType: 'Equipment',
});

// Encodes to: ?name=Weather%20Station&featureType=sosa%3ASensor&assetType=Equipment

// Type-safe property filters (recommended)
interface SystemFilters {
  name?: string;
  featureType?: SystemTypeURI;
  assetType?: AssetType;
}
```

---

## CSAPI Hierarchical Parameters (Part 1)

### recursive (Hierarchical Traversal)

**Standard:** CSAPI Part 1  
**Type:** Hierarchical query control  
**Format:** Boolean (`true` or `false`)  
**Default:** `false`  
**Applies To:** Systems (subsystems), Deployments (subdeployments)

**Usage:**

```
GET /systems?recursive=true
// All systems + subsystems recursively

GET /systems/sys123/subsystems?recursive=true
// All subsystems of sys123 recursively (nested hierarchy)

GET /deployments?recursive=true
// All deployments + subdeployments recursively
```

**Behavior:**

- `false` or omitted: Direct children only (1 level)
- `true`: All descendants recursively (unlimited depth)
- Combined with other filters: Filters apply to ALL processed resources (parents + descendants)

**Examples:**

**Without recursive (default):**

```
GET /systems/sys123/subsystems
// Returns: [sub1, sub2] (direct children only)
```

**With recursive:**

```
GET /systems/sys123/subsystems?recursive=true
// Returns: [sub1, sub2, sub1.1, sub1.2, sub2.1] (all descendants)
```

**With filters:**

```
GET /systems?recursive=true&observedProperty=temperature
// Returns: All systems (including subsystems) that observe temperature
```

**Performance Considerations:**

- Recursive queries can be expensive (large hierarchies)
- Server may impose depth limits
- Client should use pagination with recursive queries
- Consider fetching incrementally (parent → children → grandchildren)

**Validation Rules:**

- Value must be `true` or `false` (case-insensitive)
- Invalid value → 400 Bad Request
- Other values (1, 0, yes, no) → implementation-dependent (may accept or reject)

**Client API Implications:**

```typescript
interface HierarchicalOptions {
  recursive?: boolean; // Default: false
}

// Usage
client.systems.list({ recursive: true });
client.systems.listSubsystems('sys123', { recursive: true });
client.deployments.list({ recursive: true });

// Helper for incremental fetch
async function fetchHierarchy(systemId: string, maxDepth: number) {
  const systems = [];
  async function fetchLevel(id: string, depth: number) {
    if (depth > maxDepth) return;
    const subsystems = await client.systems.listSubsystems(id);
    systems.push(...subsystems);
    for (const sub of subsystems) {
      await fetchLevel(sub.id, depth + 1);
    }
  }
  await fetchLevel(systemId, 0);
  return systems;
}
```

---

## CSAPI Relationship Parameters (Part 1)

### parent (Parent Relationship Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of IDs or UIDs  
**Applies To:** Systems (find subsystems), Deployments (find subdeployments)

**Usage:**

```
GET /systems?parent=sys123
// Find subsystems of sys123

GET /systems?parent=sys123,sys456
// Find subsystems of sys123 OR sys456

GET /deployments?parent=dep789
// Find subdeployments of dep789
```

**Behavior:**

- Filters resources by parent relationship
- Multiple parent IDs treated as logical OR
- Can use local IDs or UIDs (URIs)
- Equivalent to nested endpoint: `/systems/{parentId}/subsystems`
- But allows filtering subsystems of multiple parents simultaneously

**Validation Rules:**

- Parent ID must be valid local ID or UID
- Unknown parent IDs silently excluded
- Invalid ID format → 400 Bad Request

**Client API Implications:**

```typescript
type ParentFilter = string | string[];

// Usage
client.systems.list({ parent: 'sys123' });
client.systems.list({ parent: ['sys123', 'sys456'] });

// Equivalent to:
client.systems.listSubsystems('sys123');

// But parent parameter allows multi-parent query:
client.systems.list({ parent: ['sys123', 'sys456'] });
// Not possible with nested endpoint
```

---

### procedure (Procedure Relationship Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of IDs or UIDs  
**Applies To:** Systems

**Usage:**

```
GET /systems?procedure=proc456
// Find systems that implement procedure proc456

GET /systems?procedure=proc456,proc789
// Find systems that implement procedure proc456 OR proc789

GET /systems?procedure=urn:example:procedure:wx-2000-datasheet
// Find systems that implement procedure by UID
```

**Behavior:**

- Filters systems by implemented procedure
- System → Procedure relationship (many-to-many)
- Multiple procedure IDs treated as logical OR
- Can use local IDs or UIDs

**Use Cases:**

- Find all sensors of specific type (share same datasheet)
- Find all systems using specific methodology
- Discover systems based on procedure capabilities

**Validation Rules:**

- Procedure ID must be valid local ID or UID
- Unknown procedure IDs silently excluded
- Invalid ID format → 400 Bad Request

**Client API Implications:**

```typescript
type ProcedureFilter = string | string[];

// Usage
client.systems.list({ procedure: 'proc456' });
client.systems.list({ procedure: ['proc456', 'proc789'] });

// Find systems by procedure UID
client.systems.list({
  procedure: 'urn:example:procedure:wx-2000-datasheet',
});
```

---

### foi (Feature of Interest Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of IDs or UIDs  
**Applies To:** Systems, Deployments, SamplingFeatures

**Usage:**

```
GET /systems?foi=river123
// Find systems observing/controlling river123

GET /deployments?foi=ocean456
// Find deployments where systems observe ocean456

GET /samplingFeatures?foi=atmosphere789
// Find sampling features sampling atmosphere789
```

**Feature of Interest Types:**

- Sampling features (resources in /samplingFeatures collection)
- Domain features (external features referenced by URI)

**Behavior:**

- **Systems:** Find systems observing or controlling specified FOI
  - Recursive: If system has subsystems, included if ANY subsystem observes FOI
- **Deployments:** Find deployments where deployed systems observe/control FOI
- **Sampling Features:** Find sampling features that sample specified FOI
- Multiple FOI IDs treated as logical OR
- Can use local IDs or UIDs

**Validation Rules:**

- FOI ID must be valid local ID or UID
- Unknown FOI IDs silently excluded
- Invalid ID format → 400 Bad Request

**Client API Implications:**

```typescript
type FOIFilter = string | string[];

// Usage
client.systems.list({ foi: 'river123' });
client.deployments.list({ foi: 'ocean456' });
client.samplingFeatures.list({ foi: 'atmosphere789' });

// Multi-FOI query
client.systems.list({ foi: ['river123', 'ocean456'] });
```

---

### observedProperty (Observed Property Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of IDs or UIDs  
**Applies To:** Systems, Deployments, Procedures, SamplingFeatures

**Usage:**

```
GET /systems?observedProperty=temperature
// Find systems that can observe temperature

GET /systems?observedProperty=4578441
// Find systems by property local ID

GET /systems?observedProperty=http://qudt.org/vocab/quantitykind/Temperature
// Find systems by property URI

GET /deployments?observedProperty=temperature
// Find deployments where systems observe temperature

GET /procedures?observedProperty=pressure
// Find procedures designed to observe pressure

GET /samplingFeatures?observedProperty=salinity
// Find sampling features with salinity observations
```

**Behavior:**

- **Systems:** Find systems that can observe specified property
  - Recursive: If system has subsystems, included if ANY subsystem observes property
- **Deployments:** Find deployments where deployed systems observe property
- **Procedures:** Find procedures designed to observe property
- **Sampling Features:** Find sampling features with observations of property
- Multiple property IDs treated as logical OR
- Can use local IDs or UIDs (URIs)

**Property URIs:**

- QUDT: `http://qudt.org/vocab/quantitykind/Temperature`
- CF Standard Names: `http://mmisw.org/ont/cf/parameter/air_temperature`
- Custom ontologies: `urn:example:property:wx-temp`

**Validation Rules:**

- Property ID must be valid local ID or UID
- Unknown property IDs silently excluded
- Invalid ID format → 400 Bad Request

**Client API Implications:**

```typescript
type PropertyFilter = string | string[];

// Usage
client.systems.list({ observedProperty: 'temperature' });
client.systems.list({
  observedProperty: 'http://qudt.org/vocab/quantitykind/Temperature',
});

// Multi-property query
client.systems.list({
  observedProperty: ['temperature', 'pressure', 'humidity'],
});
```

---

### controlledProperty (Controlled Property Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of IDs or UIDs  
**Applies To:** Systems, Deployments, Procedures, SamplingFeatures

**Usage:**

```
GET /systems?controlledProperty=valve-position
// Find systems that can control valve position

GET /systems?controlledProperty=http://qudt.org/vocab/quantitykind/Velocity
// Find systems by property URI

GET /deployments?controlledProperty=thrust
// Find deployments where systems control thrust

GET /procedures?controlledProperty=ph
// Find procedures designed to control pH

GET /samplingFeatures?controlledProperty=flow-rate
// Find sampling features with flow rate control
```

**Behavior:**

- Same as observedProperty but for controlled (actuated) properties
- **Systems:** Find systems (actuators) that can control specified property
  - Recursive: If system has subsystems, included if ANY subsystem controls property
- **Deployments:** Find deployments where deployed systems control property
- **Procedures:** Find procedures designed to control property
- **Sampling Features:** Find sampling features with controlled properties
- Multiple property IDs treated as logical OR

**Validation Rules:**

- Property ID must be valid local ID or UID
- Unknown property IDs silently excluded
- Invalid ID format → 400 Bad Request

**Client API Implications:**

```typescript
type PropertyFilter = string | string[];

// Usage
client.systems.list({ controlledProperty: 'valve-position' });
client.systems.list({
  controlledProperty: 'http://qudt.org/vocab/quantitykind/Velocity',
});

// Multi-property query
client.systems.list({
  controlledProperty: ['valve-position', 'thrust', 'ph'],
});
```

---

### system (Deployed System Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of IDs or UIDs  
**Applies To:** Deployments

**Usage:**

```
GET /deployments?system=sys123
// Find deployments where sys123 was deployed

GET /deployments?system=sys123,sys456
// Find deployments where sys123 OR sys456 was deployed

GET /deployments?system=urn:mrn:itu:mmsi:538070999
// Find deployments by system UID
```

**Behavior:**

- Filters deployments by deployed system
- Deployment → System relationship (many-to-many)
- Multiple system IDs treated as logical OR
- Can use local IDs or UIDs

**Use Cases:**

- Find all deployments of specific sensor
- Track deployment history of system
- Discover where system has been deployed

**Validation Rules:**

- System ID must be valid local ID or UID
- Unknown system IDs silently excluded
- Invalid ID format → 400 Bad Request

**Client API Implications:**

```typescript
type SystemFilter = string | string[];

// Usage
client.deployments.list({ system: 'sys123' });
client.deployments.list({ system: ['sys123', 'sys456'] });

// Find deployment history
async function getDeploymentHistory(systemId: string) {
  return await client.deployments.list({ system: systemId });
}
```

---

### baseProperty (Base Property Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of IDs or UIDs  
**Applies To:** Properties

**Usage:**

```
GET /properties?baseProperty=pressure
// Find properties derived from pressure

GET /properties?baseProperty=http://qudt.org/vocab/quantitykind/Pressure
// Find properties by base property URI
```

**Behavior:**

- Filters properties by base property relationship
- Searches both directly and indirectly (transitive)
- Property specialization hierarchy: base → specialized → more specialized
- Multiple base property IDs treated as logical OR

**Use Cases:**

- Find all pressure types (absolute, gauge, differential)
- Find all temperature types (air, water, surface)
- Discover property taxonomies

**Transitive Search:**

```
Base Property: Pressure
  ↓ derived
  Absolute Pressure
    ↓ derived
    Atmospheric Pressure

GET /properties?baseProperty=pressure
// Returns: Absolute Pressure, Atmospheric Pressure (transitive)
```

**Validation Rules:**

- Base property ID must be valid local ID or UID
- Unknown property IDs silently excluded
- Invalid ID format → 400 Bad Request

**Client API Implications:**

```typescript
type BasePropertyFilter = string | string[];

// Usage
client.properties.list({ baseProperty: 'pressure' });
client.properties.list({
  baseProperty: 'http://qudt.org/vocab/quantitykind/Pressure',
});

// Find property hierarchy
async function getPropertyHierarchy(basePropertyId: string) {
  return await client.properties.list({ baseProperty: basePropertyId });
}
```

---

### objectType (Object Type Filter)

**Standard:** CSAPI Part 1  
**Type:** Relationship filter  
**Format:** Comma-separated list of URIs  
**Applies To:** Properties

**Usage:**

```
GET /properties?objectType=https://dbpedia.org/page/Watercraft
// Find properties associated with watercraft

GET /properties?objectType=https://dbpedia.org/page/Engine
// Find properties associated with engines
```

**Behavior:**

- Filters properties by associated object/feature type
- Object types typically referenced by URI (external ontologies)
- Multiple object type URIs treated as logical OR

**Use Cases:**

- Find all properties relevant to specific domain (watercraft, engines)
- Discover measurable properties for object type
- Build domain-specific property catalogs

**Object Type Sources:**

- DBpedia: `https://dbpedia.org/page/Watercraft`
- Schema.org: `https://schema.org/Vehicle`
- Custom ontologies: `urn:example:objecttype:sensor`

**Validation Rules:**

- Object type must be valid URI
- Unknown object types silently excluded
- Invalid URI format → 400 Bad Request

**Client API Implications:**

```typescript
type ObjectTypeFilter = string | string[];

// Usage
client.properties.list({
  objectType: 'https://dbpedia.org/page/Watercraft',
});

// Multi-object-type query
client.properties.list({
  objectType: [
    'https://dbpedia.org/page/Watercraft',
    'https://dbpedia.org/page/Engine',
  ],
});
```

---

## CSAPI Temporal Parameters (Part 2)

### phenomenonTime (Phenomenon Time Filter)

**Standard:** CSAPI Part 2  
**Type:** Temporal filter  
**Format:** ISO 8601 datetime or interval  
**Applies To:** DataStreams, Observations

**Usage:**

```
GET /datastreams?phenomenonTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// DataStreams with observations in time range

GET /observations?phenomenonTime=2024-01-15T12:00:00Z
// Observations at specific phenomenon time

GET /datastreams/ds123/observations?phenomenonTime=2024-01-15T00:00:00Z/..
// Observations after start time
```

**Behavior:**

- **DataStreams:** Filters by phenomenonTime property (spans phenomenon times of all observations)
  - Automatically generated by server
  - Null if no observations
- **Observations:** Filters by phenomenonTime property (when observed value applies to FOI)
  - Required property on every observation
  - Can be instant or interval

**Special Value:**

- `latest` - NOT supported for phenomenonTime (use resultTime=latest instead)

**Validation Rules:**

- Same as `datetime` parameter (ISO 8601 format)
- Start must be before end (closed intervals)
- Open intervals use `..` for open end

**Client API Implications:**

```typescript
// Same as datetime parameter
client.datastreams.list({
  phenomenonTime: { start: '2024-01-15', end: '2024-01-16' },
});

client.observations.list({
  phenomenonTime: '2024-01-15T12:00:00Z',
});

// Nested endpoint
client.observations.list('ds123', {
  phenomenonTime: { start: '2024-01-15' },
});
```

---

### resultTime (Result Time Filter)

**Standard:** CSAPI Part 2  
**Type:** Temporal filter  
**Format:** ISO 8601 datetime or interval, or `latest`  
**Applies To:** DataStreams, Observations

**Usage:**

```
GET /datastreams?resultTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// DataStreams with observations obtained in time range

GET /observations?resultTime=latest
// Observations with latest result time (most recent)

GET /datastreams/ds123/observations?resultTime=2024-01-15T12:00:00Z/..
// Observations obtained after start time
```

**Behavior:**

- **DataStreams:** Filters by resultTime property (spans result times of all observations)
  - Automatically generated by server
  - Null if no observations
- **Observations:** Filters by resultTime property (when result obtained)
  - Required property on every observation
  - Can differ from phenomenonTime (sampling/processing delay)

**Special Value - `latest`:**

- Only for Observation filtering
- Returns observations with most recent resultTime
- Useful for real-time monitoring dashboards
- Single instant (not interval)

**Use Cases:**

- Real-time dashboards: `resultTime=latest`
- Incremental fetch: `resultTime=lastFetchTime/..`
- Recent data: `resultTime=2024-01-15T00:00:00Z/..`

**Validation Rules:**

- Same as `datetime` parameter (ISO 8601 format)
- Special value `latest` only for Observations
- Start must be before end (closed intervals)

**Client API Implications:**

```typescript
// Latest observations
client.observations.list({ resultTime: 'latest' });

// Incremental polling
let lastFetch = new Date('2024-01-15T00:00:00Z');
setInterval(async () => {
  const obs = await client.observations.list({
    resultTime: { start: lastFetch },
  });
  if (obs.features.length > 0) {
    lastFetch = new Date(obs.features[obs.features.length - 1].resultTime);
  }
}, 5000);
```

---

### executionTime (Execution Time Filter)

**Standard:** CSAPI Part 2  
**Type:** Temporal filter  
**Format:** ISO 8601 datetime or interval  
**Applies To:** ControlStreams

**Usage:**

```
GET /controlstreams?executionTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// ControlStreams with commands executed in time range
```

**Behavior:**

- **ControlStreams:** Filters by executionTime property (spans execution times of all commands)
  - Automatically generated by server
  - Null if no commands
- **Commands:** executionTime is required property (when command should be/was executed)

**Validation Rules:**

- Same as `datetime` parameter (ISO 8601 format)
- Start must be before end (closed intervals)
- Open intervals use `..` for open end

**Client API Implications:**

```typescript
client.controlstreams.list({
  executionTime: { start: '2024-01-15', end: '2024-01-16' },
});

// Find control streams with future commands
client.controlstreams.list({
  executionTime: { start: new Date() },
});
```

---

### issueTime (Issue Time Filter)

**Standard:** CSAPI Part 2  
**Type:** Temporal filter  
**Format:** ISO 8601 datetime or interval  
**Applies To:** ControlStreams

**Usage:**

```
GET /controlstreams?issueTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// ControlStreams with commands issued in time range
```

**Behavior:**

- **ControlStreams:** Filters by issueTime property (spans issue times of all commands)
  - Automatically generated by server
  - Null if no commands
- **Commands:** issueTime is required property (when command was issued)

**Difference from executionTime:**

- issueTime: When command was issued/submitted
- executionTime: When command should be/was executed
- executionTime usually ≥ issueTime (commands issued before execution)

**Validation Rules:**

- Same as `datetime` parameter (ISO 8601 format)
- Start must be before end (closed intervals)

**Client API Implications:**

```typescript
client.controlstreams.list({
  issueTime: { start: '2024-01-15', end: '2024-01-16' },
});

// Find recently issued commands
const oneHourAgo = new Date(Date.now() - 3600000);
client.controlstreams.list({
  issueTime: { start: oneHourAgo },
});
```

---

## Part 2 Schema Parameters

### obsFormat (Observation Format Parameter)

**Standard:** CSAPI Part 2  
**Type:** Format specification for schema endpoint  
**Format:** Media type string  
**Applies To:** DataStream schema endpoint

**Usage:**

```
GET /datastreams/ds123/schema?obsFormat=application/swe+json
// Schema for SWE Common JSON encoding

GET /datastreams/ds123/schema?obsFormat=application/swe+binary
// Schema for SWE Common binary encoding

GET /datastreams/ds123/schema?obsFormat=application/json
// Schema for plain JSON encoding
```

**Behavior:**

- Returns observation schema for specified format
- Schema structure depends on format (JSON Schema vs SWE Common DataComponent)
- Server returns 400 Bad Request if format not supported

**URL Encoding:**

- `+` character MUST be URL-encoded as `%2B`
- Example: `application/swe+json` → `application/swe%2Bjson`

**Validation Rules:**

- Format must be supported by DataStream (check `formats` property)
- Invalid format → 400 Bad Request

**Client API Implications:**

```typescript
// Fetch schema
const schema = await client.datastreams.getSchema('ds123', {
  obsFormat: 'application/swe+json',
});

// Cache schemas
const schemaCache = new Map<string, any>();
async function getSchema(datastreamId: string, format: string) {
  const key = `${datastreamId}:${format}`;
  if (!schemaCache.has(key)) {
    const schema = await client.datastreams.getSchema(datastreamId, {
      obsFormat: format,
    });
    schemaCache.set(key, schema);
  }
  return schemaCache.get(key);
}
```

---

### cmdFormat (Command Format Parameter)

**Standard:** CSAPI Part 2  
**Type:** Format specification for schema endpoint  
**Format:** Media type string  
**Applies To:** ControlStream schema endpoint

**Usage:**

```
GET /controlstreams/cs456/schema?cmdFormat=application/swe+json
// Schema for SWE Common JSON encoding

GET /controlstreams/cs456/schema?cmdFormat=application/json
// Schema for plain JSON encoding
```

**Behavior:**

- Returns command schema for specified format
- Schema structure depends on format
- Server returns 400 Bad Request if format not supported

**URL Encoding:**

- Same as `obsFormat` (encode `+` as `%2B`)

**Validation Rules:**

- Format must be supported by ControlStream (check `formats` property)
- Invalid format → 400 Bad Request

**Client API Implications:**

```typescript
// Fetch schema
const schema = await client.controlstreams.getSchema('cs456', {
  cmdFormat: 'application/swe+json',
});

// Validate command before sending
async function validateCommand(
  controlstreamId: string,
  command: any,
  format: string
) {
  const schema = await client.controlstreams.getSchema(controlstreamId, {
    cmdFormat: format,
  });
  return validate(command, schema);
}
```

---

## Part 2 Pagination (Cursor-Based)

### cursor (Cursor-Based Pagination)

**Standard:** CSAPI Part 2 (implementation-dependent)  
**Type:** Pagination cursor  
**Format:** Opaque string  
**Applies To:** Part 2 collections (alternative to offset)

**Usage:**

```
GET /observations?limit=100
// First page (no cursor)

GET /observations?limit=100&cursor=abc123xyz
// Next page (cursor from previous response)
```

**Behavior:**

- Cursor-based pagination (alternative to offset pagination)
- More efficient than offset for large datasets
- Cursor value is opaque (client must not parse or construct)
- Cursor obtained from `next` link in previous response

**Response with Cursor:**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 100 observations */
  ],
  "links": [
    {
      "rel": "next",
      "href": "https://api.example.org/observations?limit=100&cursor=abc123xyz",
      "type": "application/json"
    }
  ]
}
```

**Validation Rules:**

- Cursor must be opaque string (implementation-dependent format)
- Invalid cursor → 400 Bad Request
- Expired cursor → 400 Bad Request (cursors may have TTL)

**Client API Implications:**

```typescript
// Auto-pagination with cursor
async function* paginateWithCursor<T>(
  fetchPage: (cursor?: string) => Promise<{ items: T[]; nextCursor?: string }>
) {
  let cursor: string | undefined;
  do {
    const page = await fetchPage(cursor);
    yield* page.items;
    cursor = page.nextCursor;
  } while (cursor);
}

// Usage
for await (const obs of paginateWithCursor((cursor) =>
  client.observations.list({ limit: 1000, cursor })
)) {
  console.log(obs);
}
```

---

## Parameter Combination Rules

### Logical Operators

**Between Different Parameters (Logical AND):**

```
GET /systems?bbox=-180,-90,180,90&datetime=2024-01-01/..&observedProperty=temperature
// Systems matching ALL conditions:
//   - Geometry intersects bbox AND
//   - validTime intersects datetime AND
//   - Observes temperature property
```

**Within Single Parameter (Logical OR):**

```
GET /systems?id=sys123,sys456,sys789
// Systems matching ANY id:
//   - id=sys123 OR id=sys456 OR id=sys789
```

**Recursive + Filters:**

```
GET /systems?recursive=true&observedProperty=temperature
// All systems (including subsystems) that observe temperature
// - recursive applies to traversal depth
// - observedProperty applies to ALL processed resources (parents + descendants)
```

---

### Parameter Precedence

**Format Negotiation Precedence:**

1. Query parameter (`f` or `format`) - highest priority
2. Accept header
3. Server default format
4. 406 Not Acceptable if no match

**Temporal Filter Precedence (Part 2):**

- `phenomenonTime` takes precedence over `datetime` for Observations
- `resultTime` filter independent of `phenomenonTime`
- `executionTime` takes precedence over `datetime` for Commands
- `issueTime` filter independent of `executionTime`

**Pagination Precedence:**

- `cursor` takes precedence over `offset` (if server supports cursor-based pagination)
- `limit` always applies (both offset and cursor-based)

---

## Parameter Validation Requirements

### Client-Side Validation

**Before Sending Request:**

1. **Type Validation:**

   - bbox: Array of 4 or 6 numbers
   - datetime: Valid ISO 8601 string or Date object
   - limit: Positive integer (≥ 1, ≤ 10000)
   - offset: Non-negative integer (≥ 0)
   - recursive: Boolean

2. **Range Validation:**

   - bbox: Latitude [-90, 90], Longitude [-180, 180]
   - limit: [1, 10000] (Part 2)
   - offset: [0, Infinity)

3. **Format Validation:**

   - datetime: Valid ISO 8601 format
   - UIDs: Valid URI format
   - Property URIs: Valid URI format

4. **Logical Validation:**
   - bbox: minLon ≤ maxLon, minLat ≤ maxLat
   - datetime: start ≤ end (closed intervals)

**Error Handling:**

```typescript
class ParameterValidationError extends Error {
  constructor(
    public parameterName: string,
    public parameterValue: any,
    public validationRule: string
  ) {
    super(`Invalid ${parameterName}: ${validationRule}`);
  }
}

// Validate bbox
function validateBBox(bbox: BBoxFilter): void {
  if (bbox.minLon > bbox.maxLon) {
    throw new ParameterValidationError('bbox', bbox, 'minLon must be ≤ maxLon');
  }
  if (bbox.minLat > bbox.maxLat) {
    throw new ParameterValidationError('bbox', bbox, 'minLat must be ≤ maxLat');
  }
  if (bbox.minLat < -90 || bbox.maxLat > 90) {
    throw new ParameterValidationError(
      'bbox',
      bbox,
      'latitude must be in [-90, 90]'
    );
  }
}
```

---

### Server-Side Validation (Expected Responses)

**400 Bad Request:**

- Invalid parameter format
- Invalid parameter value
- Parameter constraint violation
- Unknown required parameter

**406 Not Acceptable:**

- Requested format not supported

**Empty Result (200 OK):**

- Valid parameters but no matching resources
- Unknown optional parameter (silently ignored)

---

## Parameter Encoding Rules

### URL Encoding

**General Rules:**

- Space: `%20` (preferred) or `+`
- Plus: `%2B` (MUST encode for media types)
- Colon: `%3A` (for UIDs)
- Slash: `%2F` (for URIs)
- Comma: DO NOT encode (used as delimiter)

**Examples:**

```
name=Weather%20Station  // Space encoded
f=application/swe%2Bjson  // Plus encoded
uid=urn%3Auuid%3Aabc  // Colon encoded
id=sys123,sys456  // Comma NOT encoded (delimiter)
```

### Array/List Encoding

**Comma-Separated Values:**

```
id=sys123,sys456,sys789
observedProperty=temperature,pressure,humidity
```

**Not Supported (Avoid):**

- Repeated parameters: `?id=sys123&id=sys456` (implementation-dependent)
- Bracket notation: `?id[]=sys123&id[]=sys456` (not supported)

### Special Characters

**Datetime Encoding:**

```
datetime=2024-01-15T12:00:00Z/2024-01-16T12:00:00Z
// Slash used as delimiter (NOT encoded)

datetime=2024-01-15T12:00:00Z/..
// Double-dot for open end (NOT encoded)
```

**URI Encoding:**

```
uid=urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255
// Encoded as:
uid=urn%3Auuid%3A31f6865e-f438-430e-9b57-f965a21ee255
```

---

## Client API Design

### Query Builder Pattern

```typescript
class QueryBuilder {
  private params: Map<string, string> = new Map();

  bbox(bbox: BBoxFilter): this {
    const coords = [bbox.minLon, bbox.minLat, bbox.maxLon, bbox.maxLat];
    if (bbox.minElev !== undefined) coords.push(bbox.minElev);
    if (bbox.maxElev !== undefined) coords.push(bbox.maxElev);
    this.params.set('bbox', coords.join(','));
    return this;
  }

  datetime(datetime: DateTimeFilter): this {
    let value: string;
    if (typeof datetime === 'string') {
      value = datetime;
    } else if (datetime instanceof Date) {
      value = datetime.toISOString();
    } else {
      const start = datetime.start
        ? typeof datetime.start === 'string'
          ? datetime.start
          : datetime.start.toISOString()
        : '..';
      const end = datetime.end
        ? typeof datetime.end === 'string'
          ? datetime.end
          : datetime.end.toISOString()
        : '..';
      value = `${start}/${end}`;
    }
    this.params.set('datetime', value);
    return this;
  }

  limit(limit: number): this {
    if (limit < 1 || limit > 10000) {
      throw new ParameterValidationError(
        'limit',
        limit,
        'must be in [1, 10000]'
      );
    }
    this.params.set('limit', limit.toString());
    return this;
  }

  observedProperty(...properties: string[]): this {
    this.params.set('observedProperty', properties.join(','));
    return this;
  }

  build(): URLSearchParams {
    const searchParams = new URLSearchParams();
    for (const [key, value] of this.params) {
      searchParams.set(key, value);
    }
    return searchParams;
  }
}

// Usage
const query = new QueryBuilder()
  .bbox({ minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 })
  .datetime({ start: '2024-01-01', end: '2024-12-31' })
  .observedProperty('temperature', 'pressure')
  .limit(100)
  .build();

const systems = await client.systems.list(query);
```

### Type-Safe Query Options

```typescript
// Part 1 query options
interface SystemQueryOptions {
  // Standard OGC API
  bbox?: BBoxFilter;
  datetime?: DateTimeFilter;
  limit?: number;
  offset?: number;
  f?: string;

  // CSAPI common
  id?: string | string[];
  uid?: string | string[];
  q?: string;

  // CSAPI hierarchical
  recursive?: boolean;

  // CSAPI relationships
  parent?: string | string[];
  procedure?: string | string[];
  foi?: string | string[];
  observedProperty?: string | string[];
  controlledProperty?: string | string[];

  // Property filters
  [propertyName: string]: any;
}

// Part 2 query options
interface ObservationQueryOptions {
  // Standard OGC API
  limit?: number;
  offset?: number;
  cursor?: string;
  f?: string;

  // CSAPI temporal
  phenomenonTime?: DateTimeFilter;
  resultTime?: DateTimeFilter | 'latest';
}

// Usage
const systems = await client.systems.list({
  bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
  datetime: { start: '2024-01-01', end: '2024-12-31' },
  observedProperty: ['temperature', 'pressure'],
  recursive: true,
  limit: 100,
});

const observations = await client.observations.list('ds123', {
  phenomenonTime: { start: '2024-01-15' },
  resultTime: 'latest',
  limit: 1000,
});
```

---

## Summary

This section documents 30+ query parameters across CSAPI Part 1 and Part 2:

**Standard OGC API Parameters:**

- bbox (spatial filter)
- datetime (temporal filter)
- limit (pagination)
- offset (pagination)
- f (format negotiation)

**CSAPI Common Parameters:**

- id, uid (identifier filters)
- q (keyword search)
- {propertyName} (property filters)

**CSAPI Hierarchical Parameters:**

- recursive (hierarchical traversal)

**CSAPI Relationship Parameters:**

- parent, procedure, foi, observedProperty, controlledProperty (Part 1)
- system, baseProperty, objectType (Part 1 specific resources)

**CSAPI Temporal Parameters:**

- phenomenonTime, resultTime, executionTime, issueTime (Part 2)

**Schema Parameters:**

- obsFormat, cmdFormat (Part 2 schema endpoints)

**Key Implementation Requirements:**

1. URL encoding (especially `+` in media types)
2. Comma-separated values for multi-value parameters
3. ISO 8601 datetime formats with open intervals
4. Parameter validation (client-side and server-side)
5. Type-safe query builders
6. Auto-pagination helpers
7. Cursor-based pagination support (Part 2)

See Section 3.1 (Common Format Requirements) for format negotiation details.
