# Section 5: CRUD Operation Requirements

## Overview

This section documents all Create, Read, Update, and Delete (CRUD) operations defined in CSAPI Part 1 and Part 2, their HTTP method mappings, request/response requirements, and client library implementation needs. Understanding CRUD operations is essential for building a complete client library that supports both read-only and transactional use cases.

**Key Objectives:**

- Document which resources support full CRUD vs read-only
- Map HTTP methods (GET, POST, PUT, PATCH, DELETE) to CRUD operations
- Define request body requirements for write operations
- Specify response codes and headers for each operation type
- Document operation-specific constraints and validation rules
- Define error handling patterns for CRUD operations
- Establish client API design for transactional operations

---

## CRUD Support Matrix

### Part 1: Core Resources

| Resource         | Create (POST) | Read (GET) | Update (PATCH) | Replace (PUT) | Delete (DELETE) | Conformance Class             |
| ---------------- | ------------- | ---------- | -------------- | ------------- | --------------- | ----------------------------- |
| Systems          | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| Deployments      | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| Procedures       | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| SamplingFeatures | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| Properties       | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| Collections      | -             | ✓          | -              | -             | -               | API-Common (read-only)        |

**Notes:**

- Collections are read-only (server-managed, no CRUD operations)
- All Part 1 resources support full CRUD when conformance classes implemented
- Create/Replace/Delete conformance class: POST, PUT, DELETE
- Update conformance class: PATCH (follows OGC API - Features Part 4)

### Part 2: Dynamic Data

| Resource       | Create (POST) | Read (GET) | Update (PATCH) | Replace (PUT) | Delete (DELETE) | Conformance Class             |
| -------------- | ------------- | ---------- | -------------- | ------------- | --------------- | ----------------------------- |
| DataStreams    | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| Observations   | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| ControlStreams | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| Commands       | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| CommandStatus  | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| CommandResult  | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| Feasibility    | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |
| SystemEvents   | ✓             | ✓          | ✓              | ✓             | ✓               | Create/Replace/Delete, Update |

**Notes:**

- All Part 2 resources support full CRUD when conformance classes implemented
- Observations/Commands have schema validation requirements
- DataStreams/ControlStreams have schema evolution constraints

---

## HTTP Method Mappings

### GET (Read)

**Purpose:** Retrieve resource(s)  
**Idempotent:** Yes  
**Safe:** Yes  
**Request Body:** Not used

**Endpoints:**

- **Collection endpoints:** `GET /{resourceType}` (list resources)
- **Single resource endpoints:** `GET /{resourceType}/{id}` (retrieve one resource)
- **Nested endpoints:** `GET /{parentType}/{parentId}/{childType}` (list child resources)

**Query Parameters:**

- Filtering: bbox, datetime, id, uid, q, {propertyName}
- Pagination: limit, offset (Part 1), cursor (Part 2)
- Relationship: parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType
- Hierarchical: recursive
- Format: f, format
- Temporal (Part 2): phenomenonTime, resultTime, executionTime, issueTime

**Response Codes:**

- 200 OK - Success, resource(s) returned
- 400 Bad Request - Invalid query parameters
- 401 Unauthorized - Authentication required
- 403 Forbidden - Access denied
- 404 Not Found - Resource not found (single resource endpoints only)
- 406 Not Acceptable - Requested format not supported
- 500 Internal Server Error - Server error

**Response Headers:**

- Content-Type - Media type of response (application/json, application/geo+json, application/sml+json, etc.)
- Link - Pagination links (rel=next, rel=prev), canonical links

**Response Body:**

- Collection endpoints: FeatureCollection (GeoJSON) or Collection (JSON)
- Single resource: Feature (GeoJSON) or Resource (JSON)

---

### POST (Create)

**Purpose:** Create new resource  
**Idempotent:** No  
**Safe:** No  
**Conformance Class:** Create/Replace/Delete

**Endpoints:**

**Part 1 Canonical Endpoints:**

- `POST /systems` - Create system at root level
- `POST /deployments` - Create deployment
- `POST /procedures` - Create procedure
- `POST /properties` - Create property

**Part 1 Nested Endpoints:**

- `POST /systems/{parentId}/subsystems` - Create subsystem under parent
- `POST /deployments/{parentId}/subdeployments` - Create subdeployment under parent
- `POST /systems/{systemId}/samplingFeatures` - Create sampling feature for system
- `POST /collections/{collectionId}/items` - Add resource to collection

**Part 2 Canonical Endpoints:**

- POST not typically used at canonical level (resources created via nested endpoints)

**Part 2 Nested Endpoints:**

- `POST /systems/{sysId}/datastreams` - Create datastream for system
- `POST /datastreams/{dsId}/observations` - Create observation in datastream
- `POST /systems/{sysId}/controlstreams` - Create control stream for system
- `POST /controlstreams/{csId}/commands` - Create command in control stream
- `POST /commands/{cmdId}/status` - Create command status report
- `POST /commands/{cmdId}/result` - Create command result
- `POST /controlstreams/{csId}/feasibility` - Create feasibility request
- `POST /systems/{sysId}/events` - Create system event

**Request Headers:**

- Content-Type (required) - Media type of request body
  - Part 1: application/geo+json, application/sml+json, application/json
  - Part 2: application/json, application/swe+json, application/swe+text, application/swe+binary

**Request Body:**

- MUST conform to resource schema
- MUST include required properties
- MAY include optional properties
- MUST NOT include server-generated properties (id, generated timestamps)

**Response Codes:**

- 201 Created - Resource created successfully
- 400 Bad Request - Invalid request body, missing required properties, schema violation
- 401 Unauthorized - Authentication required
- 403 Forbidden - Access denied
- 409 Conflict - Resource already exists, constraint violation
- 500 Internal Server Error - Server error

**Response Headers:**

- Location (required) - URL of created resource (canonical URL)
- Content-Type - Media type of response body (if body returned)

**Response Body:**

- Typically empty (201 with Location header)
- MAY return created resource representation
- If returned, MUST be same as subsequent GET on Location URL

**Part 1 Examples:**

```http
POST /systems HTTP/1.1
Content-Type: application/geo+json

{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.08, 37.42]
  },
  "properties": {
    "uid": "urn:x-sensor:id:wx-001",
    "name": "Weather Station Alpha",
    "featureType": "sosa:Sensor",
    "assetType": "Equipment"
  }
}
```

```http
HTTP/1.1 201 Created
Location: https://api.example.org/systems/sys123
```

**Part 2 Examples:**

```http
POST /datastreams/ds123/observations HTTP/1.1
Content-Type: application/json

{
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": 23.5
}
```

```http
HTTP/1.1 201 Created
Location: https://api.example.org/observations/obs456
```

---

### PUT (Replace)

**Purpose:** Replace entire resource  
**Idempotent:** Yes  
**Safe:** No  
**Conformance Class:** Create/Replace/Delete

**Endpoints:**

**Part 1 Single Resource Endpoints:**

- `PUT /systems/{id}` - Replace system
- `PUT /deployments/{id}` - Replace deployment
- `PUT /procedures/{id}` - Replace procedure
- `PUT /samplingFeatures/{id}` - Replace sampling feature
- `PUT /properties/{id}` - Replace property
- `PUT /collections/{collectionId}/items/{id}` - Replace resource in collection

**Part 2 Single Resource Endpoints:**

- `PUT /datastreams/{id}` - Replace datastream
- `PUT /systems/{sysId}/datastreams/{id}` - Replace datastream (nested)
- `PUT /observations/{id}` - Replace observation
- `PUT /datastreams/{dsId}/observations/{id}` - Replace observation (nested)
- `PUT /controlstreams/{id}` - Replace control stream
- `PUT /systems/{sysId}/controlstreams/{id}` - Replace control stream (nested)
- `PUT /commands/{id}` - Replace command
- `PUT /controlstreams/{csId}/commands/{id}` - Replace command (nested)
- `PUT /commandStatus/{id}` - Replace command status
- `PUT /commandResult/{id}` - Replace command result
- `PUT /feasibility/{id}` - Replace feasibility request
- `PUT /systemEvents/{id}` - Replace system event

**Request Headers:**

- Content-Type (required) - Media type of request body

**Request Body:**

- MUST be complete resource representation
- MUST include all required properties
- MUST include resource id (matches path parameter)
- Replaces entire resource (not partial update)

**Response Codes:**

- 204 No Content - Resource replaced successfully
- 200 OK - Resource replaced, representation returned
- 400 Bad Request - Invalid request body
- 401 Unauthorized - Authentication required
- 403 Forbidden - Access denied
- 404 Not Found - Resource doesn't exist
- 409 Conflict - Constraint violation (see special constraints below)
- 500 Internal Server Error - Server error

**Response Headers:**

- Content-Type (if response body returned)

**Response Body:**

- Typically empty (204 No Content)
- MAY return updated resource representation (200 OK)

**Special Constraints (Part 2):**

**DataStream Schema Evolution:**

- Server MUST reject PUT on DataStream if observation schema modified AND datastream has observations
- Returns 409 Conflict with error message
- Rationale: Existing observations may become invalid with new schema

**ControlStream Schema Evolution:**

- Server MUST reject PUT on ControlStream if command schema modified AND control stream has commands
- Returns 409 Conflict with error message
- Rationale: Existing commands may become invalid with new schema

**Workaround for Schema Changes:**

1. Delete all observations/commands (or use cascade delete)
2. Replace datastream/control stream with new schema
3. Re-create observations/commands if needed

**Example:**

```http
PUT /systems/sys123 HTTP/1.1
Content-Type: application/geo+json

{
  "type": "Feature",
  "id": "sys123",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.08, 37.42]
  },
  "properties": {
    "uid": "urn:x-sensor:id:wx-001",
    "name": "Weather Station Alpha Updated",
    "description": "Updated description",
    "featureType": "sosa:Sensor",
    "assetType": "Equipment"
  }
}
```

```http
HTTP/1.1 204 No Content
```

---

### PATCH (Update)

**Purpose:** Partial update of resource  
**Idempotent:** Yes (with same patch)  
**Safe:** No  
**Conformance Class:** Update (OGC API - Features Part 4)

**Endpoints:**

- Same as PUT endpoints (all single resource endpoints)

**Request Headers:**

- Content-Type (required) - MUST be `application/merge-patch+json` or `application/json` (JSON Merge Patch)

**Request Body Format:**

- JSON Merge Patch (RFC 7396)
- Only properties to update included
- Null value removes property
- Nested objects merged recursively

**Response Codes:**

- Same as PUT

**Special Constraints:**

- Same schema evolution constraints as PUT (Part 2 DataStreams/ControlStreams)

**JSON Merge Patch Examples:**

**Update single property:**

```json
{
  "description": "Updated description"
}
```

**Update nested property (GeoJSON):**

```json
{
  "properties": {
    "description": "Updated description"
  }
}
```

**Remove property:**

```json
{
  "description": null
}
```

**Update multiple properties:**

```json
{
  "name": "New Name",
  "description": "New description",
  "validTime": ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]
}
```

**Example:**

```http
PATCH /systems/sys123 HTTP/1.1
Content-Type: application/merge-patch+json

{
  "properties": {
    "description": "Updated weather station description"
  }
}
```

```http
HTTP/1.1 204 No Content
```

---

### DELETE (Delete)

**Purpose:** Delete resource  
**Idempotent:** Yes  
**Safe:** No  
**Conformance Class:** Create/Replace/Delete

**Endpoints:**

**Part 1 Single Resource Endpoints:**

- `DELETE /systems/{id}` - Delete system
- `DELETE /deployments/{id}` - Delete deployment
- `DELETE /procedures/{id}` - Delete procedure
- `DELETE /samplingFeatures/{id}` - Delete sampling feature
- `DELETE /properties/{id}` - Delete property
- `DELETE /collections/{collectionId}/items/{id}` - Remove from collection

**Part 2 Single Resource Endpoints:**

- `DELETE /datastreams/{id}` - Delete datastream
- `DELETE /observations/{id}` - Delete observation
- `DELETE /controlstreams/{id}` - Delete control stream
- `DELETE /commands/{id}` - Delete command
- `DELETE /commandStatus/{id}` - Delete command status
- `DELETE /commandResult/{id}` - Delete command result
- `DELETE /feasibility/{id}` - Delete feasibility request
- `DELETE /systemEvents/{id}` - Delete system event

**Query Parameters:**

**cascade (Part 1 and Part 2):**

- Type: boolean
- Default: false
- Purpose: Delete dependent resources recursively

**Cascade Behavior:**

**Without cascade (default):**

- Server MUST reject DELETE if resource has dependent resources
- Returns 409 Conflict
- Part 1 examples: System with subsystems, Deployment with subdeployments
- Part 2 examples: DataStream with observations, ControlStream with commands

**With cascade=true:**

- Deletes resource AND all dependent resources recursively
- Part 1: System → subsystems → subsystem's subsystems, etc.
- Part 2: DataStream → all observations
- Part 2: ControlStream → all commands (and command status/results)

**Nested Resources Deleted by Cascade:**

**Part 1:**

- System cascade: All subsystems (recursively), all sampling features, all datastreams (Part 2), all control streams (Part 2)
- Deployment cascade: All subdeployments (recursively)

**Part 2:**

- DataStream cascade: All observations
- ControlStream cascade: All commands, all command status reports, all command results
- Command cascade: All command status reports, all command results

**Response Codes:**

- 204 No Content - Resource deleted successfully
- 404 Not Found - Resource doesn't exist (may also return 204 for idempotency)
- 401 Unauthorized - Authentication required
- 403 Forbidden - Access denied
- 409 Conflict - Cascade required but not provided, constraint violation
- 500 Internal Server Error - Server error

**Response Headers:**

- None (empty response)

**Response Body:**

- Empty (204 No Content)

**Examples:**

**Simple delete:**

```http
DELETE /observations/obs456 HTTP/1.1
```

```http
HTTP/1.1 204 No Content
```

**Cascade delete (Part 1):**

```http
DELETE /systems/sys123?cascade=true HTTP/1.1
```

```http
HTTP/1.1 204 No Content
```

**Cascade delete (Part 2):**

```http
DELETE /datastreams/ds123?cascade=true HTTP/1.1
```

```http
HTTP/1.1 204 No Content
```

**Error without cascade:**

```http
DELETE /datastreams/ds123 HTTP/1.1
```

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "type": "ConstraintViolation",
  "title": "Cannot delete datastream with observations",
  "detail": "DataStream ds123 has 1500 observations. Use cascade=true to delete datastream and all observations.",
  "status": 409
}
```

---

## Request Body Requirements

### Part 1: Core Resources

#### Systems

**Formats Supported:**

- application/geo+json (GeoJSON Feature)
- application/sml+json (SensorML 3.0 JSON)
- application/json (plain JSON)

**Required Properties (GeoJSON):**

- `type: "Feature"`
- `properties.uid` (string, URI format)
- `properties.name` (string, minLength: 1)
- `properties.featureType` (SystemTypeURI enum)

**Optional Properties (GeoJSON):**

- `geometry` (Point, Polygon, LineString, etc.)
- `properties.description` (string)
- `properties.assetType` (enum: Equipment, Human, LivingThing, Simulation, Process, Group, Other)
- `properties.validTime` (array of 2 ISO 8601 strings)
- `properties.systemKind@link` (link object)
- `properties.*@link` (relationship links)

**SystemTypeURI Values:**

- `http://www.w3.org/ns/sosa/Sensor`
- `http://www.w3.org/ns/sosa/Actuator`
- `http://www.w3.org/ns/sosa/Platform`
- `http://www.w3.org/ns/sosa/Sampler`
- `http://www.w3.org/ns/sosa/System`
- Short forms: `sosa:Sensor`, `sosa:Actuator`, `sosa:Platform`, `sosa:Sampler`, `sosa:System`

**Example (GeoJSON):**

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.08, 37.42, 100]
  },
  "properties": {
    "uid": "urn:x-sensor:id:wx-001",
    "name": "Weather Station Alpha",
    "description": "Automated weather monitoring station",
    "featureType": "sosa:Sensor",
    "assetType": "Equipment",
    "validTime": ["2024-01-01T00:00:00Z", null]
  }
}
```

**Required Properties (SensorML):**

- `type` (component type: PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess)
- `uniqueId` (string, URI format)
- `label` (string)

**Optional Properties (SensorML):**

- `definition` (URI, system type)
- `description` (string)
- `position` (GeoJSON geometry)
- `validTime` (ISO 8601 interval)
- `identifiers` (array of identifier objects)
- `classifiers` (array of classifier objects)
- `inputs` (array of input definitions)
- `outputs` (array of output definitions)
- `parameters` (array of parameter definitions)
- `characteristics` (array of characteristics)
- `capabilities` (array of capabilities)
- `components` (array of nested components)

**Example (SensorML):**

```json
{
  "type": "PhysicalSystem",
  "uniqueId": "urn:x-sensor:id:wx-001",
  "label": "Weather Station Alpha",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "description": "Automated weather monitoring station",
  "position": {
    "type": "Point",
    "coordinates": [-122.08, 37.42, 100]
  },
  "validTime": ["2024-01-01T00:00:00Z", null]
}
```

#### Deployments

**Formats Supported:**

- application/geo+json (GeoJSON Feature)
- application/sml+json (SensorML Deployment)
- application/json (plain JSON)

**Required Properties (GeoJSON):**

- `type: "Feature"`
- `properties.uid` (string, URI format)
- `properties.name` (string, minLength: 1)
- `properties.featureType: "http://www.w3.org/ns/sosa/Deployment"`
- `properties.validTime` (array of 2 ISO 8601 strings, required for deployments)

**Optional Properties:**

- `geometry` (spatial extent of deployment)
- `properties.description` (string)
- `properties.deployedSystems@link` (array of link objects)
- `properties.platform@link` (link object)

**Example:**

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[...]]]
  },
  "properties": {
    "uid": "urn:x-deployment:mission-001",
    "name": "Arctic Mission 2024",
    "description": "Multi-platform Arctic observation campaign",
    "featureType": "http://www.w3.org/ns/sosa/Deployment",
    "validTime": ["2024-07-01T00:00:00Z", "2024-09-30T00:00:00Z"],
    "deployedSystems@link": [
      {"href": "https://api.example.org/systems/sys123"},
      {"href": "https://api.example.org/systems/sys456"}
    ]
  }
}
```

#### Procedures

**Formats Supported:**

- application/geo+json (GeoJSON Feature, geometry typically null)
- application/sml+json (SensorML SimpleProcess or other process types)
- application/json (plain JSON)

**Required Properties (GeoJSON):**

- `type: "Feature"`
- `properties.uid` (string, URI format)
- `properties.name` (string, minLength: 1)
- `properties.featureType` (URI, procedure type)

**Optional Properties:**

- `geometry` (typically null for procedures)
- `properties.description` (string)
- `properties.procedureType` (URI)

**Example:**

```json
{
  "type": "Feature",
  "geometry": null,
  "properties": {
    "uid": "urn:x-procedure:datasheet:wx-2000",
    "name": "Weather Sensor Model WX-2000",
    "description": "Technical datasheet for WX-2000 multi-sensor",
    "featureType": "sosa:Sensor",
    "procedureType": "sosa:Sensor"
  }
}
```

#### Sampling Features

**Formats Supported:**

- application/geo+json (GeoJSON Feature)
- application/json (plain JSON)

**Required Properties (GeoJSON):**

- `type: "Feature"`
- `properties.uid` (string, URI format)
- `properties.name` (string, minLength: 1)
- `properties.featureType` (URI, sampling feature type)

**Optional Properties:**

- `geometry` (Point, LineString, Polygon, etc.)
- `properties.description` (string)
- `properties.sampledFeature@link` (link object, ultimate FOI)
- `properties.sampleOf@link` (array of link objects, sub-sampling hierarchy)

**Sampling Feature Types:**

- `http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint`
- `http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingCurve`
- `http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingSurface`
- `http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_Specimen`
- Other types from OGC O&M specification

**Example:**

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [30.706, -134.196]
  },
  "properties": {
    "uid": "urn:x-sample:station-A-01",
    "name": "Sampling Point A-01",
    "description": "Fixed sampling location at river confluence",
    "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint",
    "sampledFeature@link": {
      "href": "http://example.org/features/river-123",
      "title": "Colorado River"
    }
  }
}
```

#### Properties

**Formats Supported:**

- application/json (plain JSON)

**Required Properties:**

- `uid` (string, URI format)
- `name` (string, minLength: 1)
- `definition` (URI, property definition)

**Optional Properties:**

- `description` (string)
- `baseProperty@link` (link object, base property URI)
- `objectType@link` (link object, object type URI)

**Example:**

```json
{
  "uid": "urn:x-property:air-temperature",
  "name": "Air Temperature",
  "description": "Temperature of air at 2m above ground",
  "definition": "http://qudt.org/vocab/quantitykind/Temperature",
  "baseProperty@link": {
    "href": "http://qudt.org/vocab/quantitykind/Temperature",
    "title": "Temperature"
  },
  "objectType@link": {
    "href": "https://dbpedia.org/page/Atmosphere",
    "title": "Atmosphere"
  }
}
```

### Part 2: Dynamic Data

#### DataStreams

**Formats Supported:**

- application/json (plain JSON, required)
- application/geo+json (optional, for spatial discovery)

**Required Properties:**

- `name` (string)
- `observedProperties` (array of URI strings, observed property definitions)
- `resultType` (string: measure, record, array, other types from SWE Common)

**Optional Properties:**

- `description` (string)
- `validTime` (ISO 8601 interval)
- `phenomenonTime` (ISO 8601 interval, auto-generated by server)
- `resultTime` (ISO 8601 interval, auto-generated by server)
- `live` (boolean, indicates real-time data availability)
- `formats` (array of strings, supported encoding formats)
- `resultSchema` (JSON Schema or SWE Common DataComponent)
- `parametersSchema` (JSON Schema or SWE Common DataComponent)
- `encoding` (SWE Common encoding specification)
- `sampling@link` (link to sampling feature)
- `foi@link` (link to ultimate feature of interest)

**Example:**

```json
{
  "name": "Temperature Sensor Data",
  "description": "Ambient temperature measurements",
  "observedProperties": ["http://qudt.org/vocab/quantitykind/Temperature"],
  "resultType": "measure",
  "live": true,
  "formats": [
    "application/json",
    "application/swe+json",
    "application/swe+binary"
  ],
  "resultSchema": {
    "type": "Quantity",
    "definition": "http://qudt.org/vocab/quantitykind/Temperature",
    "uom": { "code": "Cel" }
  }
}
```

#### Observations

**Formats Supported:**

- application/json (plain JSON)
- application/swe+json (SWE Common JSON)
- application/swe+text (SWE Common CSV/DSV)
- application/swe+binary (SWE Common binary)

**Required Properties:**

- `phenomenonTime` (ISO 8601 datetime)
- `resultTime` (ISO 8601 datetime)
- `result` (any type, MUST conform to DataStream resultSchema)

**Optional Properties:**

- `parameters` (object, MUST conform to DataStream parametersSchema if provided)
- `foi@link` (link to feature of interest)
- `sampling@link` (link to sampling feature)

**Validation:**

- Server MUST validate result against DataStream resultSchema
- Server MUST reject CREATE/REPLACE if result invalid per schema (400 error)

**Example (plain JSON):**

```json
{
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": 23.5
}
```

**Example (SWE Common JSON):**

```json
{
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "result": 23.5
}
```

#### ControlStreams

**Formats Supported:**

- application/json (plain JSON, required)

**Required Properties:**

- `name` (string)
- `controlledProperties` (array of URI strings, controlled property definitions)

**Optional Properties:**

- `description` (string)
- `validTime` (ISO 8601 interval)
- `executionTime` (ISO 8601 interval, auto-generated by server)
- `issueTime` (ISO 8601 interval, auto-generated by server)
- `live` (boolean, indicates if accepts commands)
- `async` (boolean, indicates asynchronous command processing)
- `formats` (array of strings, supported encoding formats)
- `commandSchema` (JSON Schema or SWE Common DataComponent)
- `encoding` (SWE Common encoding specification)

**Example:**

```json
{
  "name": "UAV Flight Control",
  "description": "Control stream for UAV flight commands",
  "controlledProperties": ["http://example.org/properties/flight-path"],
  "live": true,
  "async": true,
  "formats": ["application/json", "application/swe+json"]
}
```

#### Commands

**Formats Supported:**

- application/json (plain JSON)
- application/swe+json (SWE Common JSON)

**Required Properties:**

- `issueTime` (ISO 8601 datetime)
- `executionTime` (ISO 8601 datetime, when command should execute)
- `parameters` (object, MUST conform to ControlStream commandSchema)

**Optional Properties:**

- `foi@link` (link to feature of interest)

**Validation:**

- Server MUST validate parameters against ControlStream commandSchema
- Server MUST reject CREATE/REPLACE if parameters invalid per schema (400 error)

**Example:**

```json
{
  "issueTime": "2024-01-15T12:00:00Z",
  "executionTime": "2024-01-15T12:05:00Z",
  "parameters": {
    "altitude": 100,
    "speed": 15,
    "waypoints": [
      { "lat": 37.42, "lon": -122.08 },
      { "lat": 37.43, "lon": -122.09 }
    ]
  }
}
```

#### CommandStatus

**Formats Supported:**

- application/json (plain JSON)

**Required Properties:**

- `reportTime` (ISO 8601 datetime)
- `executionStatus` (enum: PENDING, ACCEPTED, EXECUTING, COMPLETED, FAILED, REJECTED, CANCELLED)

**Optional Properties:**

- `statusMessage` (string, human-readable status description)
- `percentCompletion` (integer, 0-100)

**Example:**

```json
{
  "reportTime": "2024-01-15T12:05:30Z",
  "executionStatus": "EXECUTING",
  "percentCompletion": 45,
  "statusMessage": "En route to waypoint 2 of 5"
}
```

#### CommandResult

**Formats Supported:**

- application/json (plain JSON)

**Properties:**

- One of: `datastream@link`, `observation@link`, `inline`, `external@link`

**Result Types:**

**Datastream Reference:**

```json
{
  "datastream@link": {
    "href": "https://api.example.org/datastreams/ds456",
    "title": "Simulation Results"
  },
  "timeRange": "2024-01-15T00:00:00Z/2024-01-15T12:00:00Z"
}
```

**Observation Reference:**

```json
{
  "observation@link": {
    "href": "https://api.example.org/observations/obs789",
    "title": "UAV Image",
    "type": "image/jpeg"
  }
}
```

**Inline Result:**

```json
{
  "inline": {
    "temperature": 23.5,
    "pressure": 101325,
    "humidity": 65.2
  }
}
```

**External Resource:**

```json
{
  "external@link": {
    "href": "https://data.example.org/datasets/sim-run-123",
    "title": "Full Simulation Output",
    "type": "application/netcdf"
  }
}
```

---

## Response Requirements

### Success Response Codes

**200 OK:**

- Operation: GET (read), PUT (replace with body), PATCH (update with body)
- Response Body: Resource representation
- When: Resource successfully retrieved or updated

**201 Created:**

- Operation: POST (create)
- Response Headers: Location (required, canonical URL of created resource)
- Response Body: Empty or created resource representation
- When: Resource successfully created

**204 No Content:**

- Operation: PUT (replace), PATCH (update), DELETE (delete)
- Response Body: Empty
- When: Resource successfully updated or deleted

### Client Error Response Codes

**400 Bad Request:**

- Causes: Invalid query parameters, invalid request body, missing required properties, schema validation failure, malformed JSON
- Response Body: Error object with details

**401 Unauthorized:**

- Causes: Missing or invalid authentication credentials
- Response Headers: WWW-Authenticate
- Response Body: Error object

**403 Forbidden:**

- Causes: Authenticated but not authorized to perform operation
- Response Body: Error object

**404 Not Found:**

- Causes: Resource doesn't exist (single resource endpoints)
- Response Body: Error object
- Note: Collection endpoints return 200 with empty collection, not 404

**406 Not Acceptable:**

- Causes: Requested format not supported by server
- Response Body: Error object with supported formats

**409 Conflict:**

- Causes:
  - Resource already exists (POST)
  - Constraint violation (DELETE without cascade)
  - Schema evolution with existing data (PUT/PATCH on DataStream/ControlStream)
- Response Body: Error object with constraint details

### Server Error Response Codes

**500 Internal Server Error:**

- Causes: Unexpected server error
- Response Body: Error object

**503 Service Unavailable:**

- Causes: Server temporarily unavailable
- Response Headers: Retry-After
- Response Body: Error object

### Error Response Format

**OGC API Error Format (RFC 7807 Problem Details):**

```json
{
  "type": "https://api.example.org/errors/constraint-violation",
  "title": "Constraint Violation",
  "status": 409,
  "detail": "Cannot delete datastream ds123 with 1500 observations. Use cascade=true parameter.",
  "instance": "/datastreams/ds123"
}
```

**Properties:**

- `type` (URI) - Error type identifier
- `title` (string) - Short error summary
- `status` (integer) - HTTP status code
- `detail` (string) - Detailed error description
- `instance` (URI) - Resource that caused error

---

## Operation-Specific Constraints

### Schema Validation (Part 2)

**Observation CREATE/REPLACE:**

- Result MUST conform to DataStream resultSchema
- Parameters (if present) MUST conform to DataStream parametersSchema
- Validation failure → 400 Bad Request

**Command CREATE/REPLACE:**

- Parameters MUST conform to ControlStream commandSchema
- Validation failure → 400 Bad Request

**DataStream/ControlStream Schema Evolution:**

- Cannot modify resultSchema/commandSchema if observations/commands exist
- Attempted modification → 409 Conflict
- Workaround: Delete all observations/commands (cascade), then modify schema

### Cascade Delete Requirements

**Part 1 Systems:**

- Without cascade: Reject if has subsystems, sampling features, datastreams, or control streams
- With cascade: Delete system + all subsystems (recursive) + sampling features + datastreams + control streams

**Part 1 Deployments:**

- Without cascade: Reject if has subdeployments
- With cascade: Delete deployment + all subdeployments (recursive)

**Part 2 DataStreams:**

- Without cascade: Reject if has observations
- With cascade: Delete datastream + all observations

**Part 2 ControlStreams:**

- Without cascade: Reject if has commands
- With cascade: Delete control stream + all commands + command status + command results

**Part 2 Commands:**

- Without cascade: Reject if has status reports or results (implementation-dependent)
- With cascade: Delete command + all status reports + all results

### Idempotency Requirements

**GET (Read):**

- Idempotent: Yes
- Safe: Yes
- Multiple identical requests return same result

**POST (Create):**

- Idempotent: No
- Safe: No
- Multiple identical requests create multiple resources

**PUT (Replace):**

- Idempotent: Yes
- Safe: No
- Multiple identical requests produce same final state

**PATCH (Update):**

- Idempotent: Yes (with same patch)
- Safe: No
- Multiple identical patches produce same final state

**DELETE:**

- Idempotent: Yes
- Safe: No
- Multiple identical requests produce same final state (resource deleted)
- Server MAY return 204 for subsequent deletes (idempotent behavior)
- Server MAY return 404 for subsequent deletes

---

## Client API Design

### CRUD Method Naming

**Read Operations:**

```typescript
// Single resource
client.systems.get(id: string): Promise<System>
client.systems.getAsGeoJSON(id: string): Promise<GeoJSONFeature>
client.systems.getAsSensorML(id: string): Promise<SensorML>

// Collection (list)
client.systems.list(options?: QueryOptions): Promise<SystemCollection>
client.systems.listAll(options?: QueryOptions): AsyncGenerator<System>
```

**Create Operations:**

```typescript
// Canonical endpoint
client.systems.create(data: SystemInput, options?: CreateOptions): Promise<System>
client.systems.createFromGeoJSON(feature: GeoJSONFeature): Promise<System>
client.systems.createFromSensorML(sensorML: SensorML): Promise<System>

// Nested endpoint
client.systems.createSubsystem(parentId: string, data: SystemInput): Promise<System>
client.samplingFeatures.create(systemId: string, data: SamplingFeatureInput): Promise<SamplingFeature>

// Part 2
client.observations.create(datastreamId: string, data: ObservationInput): Promise<Observation>
client.commands.create(controlstreamId: string, data: CommandInput): Promise<Command>
```

**Update Operations:**

```typescript
// Replace (PUT)
client.systems.replace(id: string, data: SystemInput): Promise<void>

// Partial update (PATCH)
client.systems.update(id: string, patch: Partial<SystemInput>): Promise<void>
```

**Delete Operations:**

```typescript
// Simple delete
client.systems.delete(id: string): Promise<void>

// Cascade delete
client.systems.delete(id: string, { cascade: true }): Promise<void>
client.datastreams.delete(id: string, { cascade: true }): Promise<void>
```

### Type-Safe Request Bodies

```typescript
interface SystemInput {
  uid: string; // URI format
  name: string;
  description?: string;
  featureType: SystemTypeURI;
  assetType?: AssetType;
  geometry?: GeoJSONGeometry;
  validTime?: [string, string | null];
}

interface ObservationInput {
  phenomenonTime: string | Date;
  resultTime: string | Date;
  result: any; // Type depends on DataStream resultSchema
  parameters?: any; // Type depends on DataStream parametersSchema
}

interface CommandInput {
  issueTime: string | Date;
  executionTime: string | Date;
  parameters: any; // Type depends on ControlStream commandSchema
}
```

### Response Handling

```typescript
interface CreateResponse<T> {
  resource: T;
  location: string; // Canonical URL
}

interface ErrorResponse {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
}

// Usage
try {
  const system = await client.systems.create(systemData);
  console.log('Created:', system.id);
} catch (error) {
  if (error instanceof APIError) {
    if (error.status === 409) {
      console.error('Conflict:', error.detail);
    } else if (error.status === 400) {
      console.error('Validation error:', error.detail);
    }
  }
}
```

### Batch Operations

```typescript
// Batch create (multiple POST requests)
async function createBatch<T>(
  createFn: (data: T) => Promise<T>,
  items: T[]
): Promise<T[]> {
  const results = [];
  for (const item of items) {
    try {
      const created = await createFn(item);
      results.push(created);
    } catch (error) {
      console.error('Failed to create item:', error);
      // Continue or stop based on error handling strategy
    }
  }
  return results;
}

// Usage
const systems = await createBatch(
  (data) => client.systems.create(data),
  systemDataArray
);
```

### Optimistic Updates

```typescript
// Optimistic update pattern
async function updateWithOptimism<T>(
  getId: () => string,
  getResource: (id: string) => Promise<T>,
  updateResource: (id: string, data: Partial<T>) => Promise<void>,
  patch: Partial<T>,
  onSuccess: (resource: T) => void,
  onError: (error: Error) => void
) {
  const id = getId();
  const original = await getResource(id);

  // Apply optimistically
  onSuccess({ ...original, ...patch });

  try {
    await updateResource(id, patch);
  } catch (error) {
    // Revert on error
    onSuccess(original);
    onError(error);
  }
}
```

---

## Summary

This section documents CRUD operations for CSAPI client library:

**CRUD Support:**

- Part 1: All 5 resources support full CRUD (when conformance classes implemented)
- Part 2: All 8 resources support full CRUD (when conformance classes implemented)
- Collections are read-only (no CRUD)

**HTTP Method Mappings:**

- GET (read) - All endpoints
- POST (create) - Canonical and nested collection endpoints
- PUT (replace) - Single resource endpoints only
- PATCH (update) - Single resource endpoints only (JSON Merge Patch)
- DELETE (delete) - Single resource endpoints only

**Request Body Requirements:**

- Part 1: GeoJSON, SensorML, or plain JSON
- Part 2: JSON, SWE Common (JSON/CSV/Binary)
- Schema validation for Observations/Commands

**Response Codes:**

- 200 OK, 201 Created, 204 No Content (success)
- 400 Bad Request, 404 Not Found, 409 Conflict (client errors)
- 500 Internal Server Error (server errors)

**Special Constraints:**

- Schema evolution restrictions (Part 2 DataStreams/ControlStreams)
- Cascade delete requirements (Part 1 Systems/Deployments, Part 2 DataStreams/ControlStreams)

**Client API Design:**

- Type-safe request bodies
- CRUD method naming (get, list, create, replace, update, delete)
- Format-specific convenience methods
- Batch operations support
- Error handling patterns

See Section 3 (Format Requirements) for detailed format specifications and Section 4 (Query Parameters) for filtering options.
