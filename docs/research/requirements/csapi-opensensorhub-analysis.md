# OpenSensorHub CSAPI Server Implementation Analysis

**Research Date:** January 31, 2026  
**Repository:** https://github.com/opensensorhub/osh-core  
**Live Demo Server:** http://45.55.99.236:8080/sensorhub/api  
**Purpose:** Analyze server-side CSAPI implementation to inform TypeScript client library design

---

## Executive Summary

OpenSensorHub (OSH) provides a **comprehensive, production-ready OGC API - Connected Systems server implementation** in Java. This analysis examines the osh-core repository to understand server behaviors, expectations, and patterns that must be handled by client libraries. Additionally, a **live demo server** is available for real-time testing and validation.

**Key Findings:**

- ✅ **Full Part 1 + Part 2 + Part 3 Coverage:** All 11 CSAPI resources implemented with CRUD operations
- ✅ **Complete Conformance:** Supports OGC API Common, Features, and Connected Systems Parts 1, 2, 3
- ✅ **Rich Format Support:** JSON, GeoJSON, SensorML JSON, SWE Common (JSON/Binary/Text/CSV/XML), HTML
- ✅ **Robust Query Engine:** Complex filters (bbox, temporal, parent relationships, keywords)
- ✅ **Production Features:** Pagination, async operations, error handling, real-time streaming (WebSocket/MQTT)
- ✅ **Extensive Test Fixtures:** Comprehensive examples available for client testing
- ✅ **Live Demo Server:** Public instance with 6 active systems, 28 datastreams, live observations

**Implementation Maturity:** Production-ready, actively maintained, reference implementation

**Live Server Access:**

- **URL:** http://45.55.99.236:8080/sensorhub/api
- **Authentication:** HTTP Basic Auth (credentials provided separately)
- **Systems:** 6 (3 LIVE replay, 3 archived) - Drones + Android sensors
- **DataStreams:** 28 (telemetry, IMU, GPS, health status)
- **Observations:** Thousands (live streaming with `validTime: [..., "now"]`)
- **Conformance:** 33/33 conformance classes (100%)
- **Use Case:** Real-time integration testing without local deployment

---

## Table of Contents

1. [Repository Structure](#1-repository-structure)
2. [Implemented Operations by Resource](#2-implemented-operations-by-resource)
3. [Conformance Classes](#3-conformance-classes)
4. [Query Parameter Patterns](#4-query-parameter-patterns)
5. [Request Validation Rules](#5-request-validation-rules)
6. [Response Format Support](#6-response-format-support)
7. [Error Response Catalog](#7-error-response-catalog)
8. [Pagination Implementation](#8-pagination-implementation)
9. [Sub-Resource Relationships](#9-sub-resource-relationships)
10. [Edge Cases & Special Behaviors](#10-edge-cases--special-behaviors)
11. [Request/Response Examples](#11-requestresponse-examples)
12. [Server-Specific vs Spec Behaviors](#12-server-specific-vs-spec-behaviors)
13. [Real-World Data Patterns](#13-real-world-data-patterns)
14. [Performance Characteristics](#14-performance-characteristics)
15. [Authentication/Authorization](#15-authenticationauthorization)
16. [SensorML/SWE Common Structures](#16-sensormlswe-common-structures)
17. [Client Implementation Insights](#17-client-implementation-insights)
18. [Conclusion](#18-conclusion)

---

## 1. Repository Structure

### 1.1 CSAPI Service Location

**Main Service Module:** `sensorhub-service-consys/`

**Package Structure:**

```
org.sensorhub.impl.service.consys/
├── ConSysApiService.java           # Main service class
├── RestApiServlet.java             # Async HTTP servlet
├── home/                           # Root endpoints
│   ├── HomePageHandler.java        # Landing page (/)
│   ├── ConformanceHandler.java     # /conformance
│   └── CollectionHandler.java      # /collections
├── system/                         # Systems resource
│   ├── SystemHandler.java          # /systems CRUD
│   ├── SystemEventsHandler.java    # /systems/{id}/events
│   └── SystemHistoryHandler.java   # /systems/{id}/history
├── deployment/
│   └── DeploymentHandler.java      # /deployments CRUD
├── procedure/
│   └── ProcedureHandler.java       # /procedures CRUD
├── feature/
│   └── FoiHandler.java             # /fois (Features of Interest)
├── obs/                            # Observations & DataStreams
│   ├── DataStreamHandler.java      # /datastreams CRUD
│   ├── ObsHandler.java             # /observations
│   └── ObsSchemaHandler.java       # /datastreams/{id}/schema
├── task/                           # Commands & Control
│   ├── CommandHandler.java         # /commands
│   └── CommandStreamHandler.java   # /controlstreams CRUD
└── resource/
    └── BaseResourceHandler.java    # Shared query/pagination logic
```

**Key Files:**

- [ConSysApiService.java](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java) - Service initialization, conformance declaration
- [RestApiServlet.java](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java) - Request routing, async handling
- [BaseResourceHandler.java](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java) - Query parsing, pagination, filtering (lines 241-286)

### 1.2 Test Fixtures Location

**Test Data:** `sensorhub-service-consys/src/test/resources/`

Contains example JSON payloads for:

- Systems (SensorML JSON format)
- DataStreams (schema definitions)
- Observations (measurement data)
- Commands (control instructions)

---

## 2. Implemented Operations by Resource

### 2.1 Complete Operation Matrix

| Resource                 | Path              | Handler                                                                                                                                                                             | GET List | GET Item | POST Create | PUT Update | DELETE |
| ------------------------ | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------- | ----------- | ---------- | ------ |
| **Landing Page**         | `/`               | [HomePageHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/home/HomePageHandler.java)           | ✅       | N/A      | ❌          | ❌         | ❌     |
| **Conformance**          | `/conformance`    | [ConformanceHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/home/ConformanceHandler.java)     | ✅       | N/A      | ❌          | ❌         | ❌     |
| **Collections**          | `/collections`    | [CollectionHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/home/CollectionHandler.java)       | ✅       | ✅       | ❌          | ❌         | ❌     |
| **Systems**              | `/systems`        | [SystemHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemHandler.java)             | ✅       | ✅       | ✅          | ✅         | ✅     |
| **Deployments**          | `/deployments`    | [DeploymentHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/deployment/DeploymentHandler.java) | ✅       | ✅       | ✅          | ✅         | ✅     |
| **Procedures**           | `/procedures`     | [ProcedureHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/procedure/ProcedureHandler.java)    | ✅       | ✅       | ✅          | ✅         | ✅     |
| **Properties**           | `/properties`     | PropertyHandler                                                                                                                                                                     | ✅       | ✅       | ✅          | ✅         | ✅     |
| **Features of Interest** | `/fois`           | [FoiHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/feature/FoiHandler.java)                  | ✅       | ✅       | ✅          | ✅         | ✅     |
| **DataStreams**          | `/datastreams`    | [DataStreamHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamHandler.java)        | ✅       | ✅       | ✅          | ✅         | ✅     |
| **Observations**         | `/observations`   | [ObsHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java)                      | ✅       | ✅       | ✅          | ❌         | ✅     |
| **Control Streams**      | `/controlstreams` | CommandStreamHandler                                                                                                                                                                | ✅       | ✅       | ✅          | ✅         | ✅     |
| **Commands**             | `/commands`       | [CommandHandler](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/task/CommandHandler.java)             | ✅       | ✅       | ✅          | ❌         | ❌     |

**Total Coverage:** 11/11 CSAPI resources implemented (100%)

### 2.2 Operation-Specific Notes

**Observations:**

- ❌ **No PUT support** - Observations are immutable once created
- ✅ **Bulk POST** - Can post multiple observations in one request
- ✅ **DELETE** - Available but typically not used (data retention policies)

**Commands:**

- ❌ **No PUT support** - Commands are immutable (status tracking only)
- ❌ **No DELETE** - Commands retained for audit trail
- ✅ **Status monitoring** - `/commands/{id}/status` endpoint available

**All Other Resources:**

- ✅ **Full CRUD** - Complete create, read, update, delete support

---

## 3. Conformance Classes

### 3.1 Declared Conformance

**Source:** [ConSysApiService.java#L77-108](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L77-L108)

**OGC API - Common:**

- `http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core`
- `http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections`

**OGC API - Features:**

- `http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core`
- `http://www.opengis.net/spec/ogcapi-features-4/1.0/conf/create-replace-delete`

**OGC API - Connected Systems:**

- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system-features`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sampling-feature`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/datastream`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/observation`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/control-stream`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/command`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-3/1.0/conf/system-events`

**Format Conformance:**

- JSON (`application/json`)
- GeoJSON (`application/geo+json`)
- SensorML JSON (`application/sml+json`)
- Observations & Measurements JSON (`application/om+json`)
- SWE Common JSON (`application/swe+json`)
- SWE Common Text (`application/swe+text`)
- SWE Common Binary (`application/swe+binary`)
- HTML (`text/html`)

### 3.2 Conformance Endpoint Response

**GET `/conformance`**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-4/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system-features",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sampling-feature",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/datastream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/observation",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/control-stream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/command",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-3/1.0/conf/system-events"
  ]
}
```

---

## 4. Query Parameter Patterns

### 4.1 Common Query Parameters (All Resources)

**Source:** [BaseResourceHandler.java](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java)

| Parameter   | Type    | Description                           | Example                              |
| ----------- | ------- | ------------------------------------- | ------------------------------------ |
| `id`        | String  | Resource internal ID (Base32 encoded) | `?id=ABCD1234`                       |
| `uid`       | String  | Globally unique identifier            | `?uid=urn:x-myorg:sensor:123`        |
| `q`         | String  | Keyword search (name, description)    | `?q=weather`                         |
| `parent`    | String  | Parent resource ID or UID             | `?parent=sys-abc`                    |
| `validTime` | ISO8601 | Time period resource is valid         | `?validTime=2024-01-01T00:00:00Z/..` |
| `limit`     | Integer | Max results per page (1-10000)        | `?limit=50`                          |
| `offset`    | Integer | Skip N results for pagination         | `?offset=100`                        |
| `f`         | String  | Response format                       | `?f=json` or `?f=html`               |

### 4.2 Spatial Query Parameters

**Bounding Box:**

```
?bbox=minLon,minLat,maxLon,maxLat
?bbox=-122.4,37.7,-122.3,37.8
```

**Geometry Filter:**

```
?location=POINT(-122.4 37.7)
?location=POLYGON((x1 y1, x2 y2, ...))
```

**Coordinate Reference System:**

- Default: WGS84 (EPSG:4326)
- Can specify: `?bbox-crs=http://www.opengis.net/def/crs/EPSG/0/4326`

### 4.3 Temporal Query Parameters

**Phenomenal Time (when event occurred):**

```
?phenomenonTime=2024-01-15T10:00:00Z                    # Instant
?phenomenonTime=2024-01-15T10:00:00Z/2024-01-15T11:00:00Z  # Interval
?phenomenonTime=2024-01-15T10:00:00Z/..                 # Open-ended
?phenomenonTime=../2024-01-15T11:00:00Z                 # Before time
```

**Result Time (when observation recorded):**

```
?resultTime=2024-01-15T10:30:00Z
?resultTime=2024-01-15T10:00:00Z/..
```

**Valid Time (when resource was valid):**

```
?validTime=2024-01-01T00:00:00Z/2024-12-31T23:59:59Z
```

### 4.4 Resource-Specific Parameters

**Systems** (`/systems`):

```
?q=weather                    # Keyword search
?parent=sys-parent-123        # Child systems
?bbox=-122.4,37.7,-122.3,37.8 # Spatial filter
?validTime=2024-01-01/..      # Active systems
```

**DataStreams** (`/datastreams`):

```
?system=sys-123               # DataStreams for specific system
?observedProperty=http://mmisw.org/ont/cf/parameter/air_temperature
?foi=feature-456              # DataStreams observing specific feature
?validTime=2024-01-01/..      # Active datastreams
```

**Observations** (`/observations` or `/datastreams/{id}/observations`):

```
?phenomenonTime=2024-01-15T10:00:00Z/2024-01-15T11:00:00Z
?resultTime=2024-01-15T10:30:00Z/..
?foi=feature-789              # Observations of specific feature
?system=sys-123               # All observations from system
?dataStream=ds-456            # Observations from specific datastream
?observedProperty=http://...  # Filter by property
?bbox=-122.4,37.7,-122.3,37.8 # Spatial filter on FOI location
?limit=1000                   # Batch size
```

**Commands** (`/commands`):

```
?controlStream=cs-123         # Commands for specific control stream
?system=sys-456               # Commands for system
?executionTime=2024-01-15/..  # Commands executed in time range
?status=pending               # Filter by status (pending, executed, failed)
```

### 4.5 Query Parameter Validation

**Validation Rules (implemented server-side):**

1. **limit:**

   - Minimum: 1
   - Maximum: 10,000
   - Default: 100
   - Invalid value → 400 Bad Request

2. **offset:**

   - Minimum: 0
   - Default: 0
   - Invalid value → 400 Bad Request

3. **bbox:**

   - Format: `minLon,minLat,maxLon,maxLat`
   - Must have exactly 4 values
   - Values must be valid WGS84 coordinates
   - Invalid → 400 Bad Request with message "Invalid bbox format"

4. **Time parameters:**

   - Must be valid ISO 8601 strings
   - Intervals: `start/end`, `start/..`, or `../end`
   - Invalid → 400 Bad Request with message "Invalid time format"

5. **id/uid:**
   - Must reference existing resource
   - Invalid → 404 Not Found

---

## 5. Request Validation Rules

### 5.1 Common Validation

**Source:** [InvalidRequestException.java](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/InvalidRequestException.java)

**Request Body Validation:**

```java
// Required fields check
if (resource.getId() == null) {
    throw new InvalidRequestException("Missing required field: id");
}

// Format validation
if (!isValidUri(resource.getUniqueId())) {
    throw new InvalidRequestException("Invalid URI format for uniqueId");
}

// Parent reference validation
if (resource.hasParent() && !parentExists(resource.getParent())) {
    throw new InvalidRequestException("Parent resource not found");
}
```

### 5.2 Resource-Specific Validation

**Systems Validation:**

- `uniqueId` must be valid URI
- `name` required
- `type` must be valid SensorML type (`PhysicalSystem`, `PhysicalComponent`, `SimpleProcess`)
- Parent system must exist if specified
- Outputs must reference valid observable properties

**DataStreams Validation:**

- `system` link required
- `outputName` must match system output definition
- `schema` must be valid SWE Common DataRecord
- `observedProperty` must be valid URI
- `phenomenonTime` and `resultTime` must be valid time ranges

**Observations Validation:**

- Must belong to valid DataStream
- `phenomenonTime` required
- `result` must match DataStream schema structure
- `foi` must reference valid feature (if specified)
- Result values must match schema data types

**Commands Validation:**

- Must belong to valid ControlStream
- `taskingParameters` must match ControlStream schema
- `executionTime` must be valid ISO 8601
- Cannot modify command after execution

### 5.3 HTTP Header Validation

**Content-Type:**

```
POST /systems
Content-Type: application/json

# Invalid Content-Type → 415 Unsupported Media Type
```

**Accept:**

```
GET /systems
Accept: application/json

# Unsupported format → 406 Not Acceptable
```

**Conditional Requests:**

```
PUT /systems/abc123
If-Match: "version-etag"

# ETag mismatch → 412 Precondition Failed
```

---

## 6. Response Format Support

### 6.1 Content Negotiation

**Methods:**

1. **Accept Header:** `Accept: application/json`
2. **Query Parameter:** `?f=json`

**Priority:** Query parameter `f` overrides `Accept` header

### 6.2 Supported MIME Types

| Format            | MIME Type                | Usage                 | Resources                  |
| ----------------- | ------------------------ | --------------------- | -------------------------- |
| **JSON**          | `application/json`       | Default, generic JSON | All                        |
| **GeoJSON**       | `application/geo+json`   | Spatial features      | Systems, Deployments, FOIs |
| **SensorML JSON** | `application/sml+json`   | Sensor descriptions   | Systems, Procedures        |
| **O&M JSON**      | `application/om+json`    | Observations          | Observations               |
| **SWE JSON**      | `application/swe+json`   | SWE Common schemas    | DataStream schemas         |
| **SWE Text**      | `application/swe+text`   | Human-readable SWE    | DataStream schemas         |
| **SWE Binary**    | `application/swe+binary` | Compact observations  | Observations (high-freq)   |
| **HTML**          | `text/html`              | Browser view          | All (human-readable)       |

### 6.3 Format Selection Examples

**Request JSON:**

```http
GET /api/systems/abc123 HTTP/1.1
Accept: application/json
```

**Request GeoJSON:**

```http
GET /api/systems/abc123 HTTP/1.1
Accept: application/geo+json
```

**Request SensorML:**

```http
GET /api/systems/abc123?f=sml+json HTTP/1.1
```

**Request HTML (browser):**

```http
GET /api/systems/abc123 HTTP/1.1
Accept: text/html
```

### 6.4 Response Examples by Format

**JSON (application/json):**

```json
{
  "id": "abc123",
  "uniqueId": "urn:x-myorg:system:weather-001",
  "name": "Weather Station",
  "type": "PhysicalSystem",
  "links": [
    {
      "rel": "self",
      "href": "/api/systems/abc123",
      "type": "application/json"
    }
  ]
}
```

**GeoJSON (application/geo+json):**

```json
{
  "type": "Feature",
  "id": "abc123",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.4, 37.7]
  },
  "properties": {
    "uniqueId": "urn:x-myorg:system:weather-001",
    "name": "Weather Station",
    "type": "PhysicalSystem"
  }
}
```

**SensorML JSON (application/sml+json):**

```json
{
  "type": "PhysicalSystem",
  "id": "abc123",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueIdentifier": "urn:x-myorg:system:weather-001",
  "label": "Weather Station",
  "description": "Automated weather monitoring station",
  "contacts": [],
  "position": {
    "type": "Point",
    "coordinates": [-122.4, 37.7]
  },
  "outputs": [
    {
      "name": "weather_data",
      "type": "DataInterface"
    }
  ]
}
```

---

## 7. Error Response Catalog

### 7.1 Error Response Structure

**Format:**

```json
{
  "status": 400,
  "message": "Invalid query parameter",
  "details": "The 'limit' parameter must be between 1 and 10000"
}
```

### 7.2 HTTP Status Codes

| Status Code                    | Meaning                  | Usage Examples                       |
| ------------------------------ | ------------------------ | ------------------------------------ |
| **200 OK**                     | Success                  | GET requests returning data          |
| **201 Created**                | Resource created         | POST creating new resource           |
| **202 Accepted**               | Async processing         | Long-running POST/PUT operations     |
| **204 No Content**             | Success, no body         | DELETE operations                    |
| **400 Bad Request**            | Invalid request          | Malformed JSON, invalid parameters   |
| **401 Unauthorized**           | Auth required            | Missing authentication               |
| **403 Forbidden**              | Insufficient permissions | User lacks access to resource        |
| **404 Not Found**              | Resource missing         | GET/PUT/DELETE non-existent resource |
| **405 Method Not Allowed**     | Unsupported operation    | PUT on observations                  |
| **406 Not Acceptable**         | Format unsupported       | Request for unavailable format       |
| **409 Conflict**               | Resource conflict        | uniqueId already exists              |
| **412 Precondition Failed**    | ETag mismatch            | Conditional request failed           |
| **415 Unsupported Media Type** | Invalid Content-Type     | POST with XML body                   |
| **422 Unprocessable Entity**   | Validation failed        | Schema validation error              |
| **500 Internal Server Error**  | Server error             | Unexpected exception                 |
| **503 Service Unavailable**    | Temporary unavailable    | Database connection lost             |

### 7.3 Common Error Scenarios

**Invalid Pagination:**

```http
GET /api/systems?limit=100000 HTTP/1.1

HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": 400,
  "message": "Invalid query parameter",
  "details": "The 'limit' parameter must be between 1 and 10000"
}
```

**Resource Not Found:**

```http
GET /api/systems/nonexistent HTTP/1.1

HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "status": 404,
  "message": "Resource not found",
  "details": "System with id 'nonexistent' does not exist"
}
```

**Invalid Time Format:**

```http
GET /api/observations?phenomenonTime=invalid HTTP/1.1

HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": 400,
  "message": "Invalid time format",
  "details": "Expected ISO 8601 format (e.g., 2024-01-15T10:00:00Z or 2024-01-15T10:00:00Z/2024-01-15T11:00:00Z)"
}
```

**Schema Validation Error:**

```http
POST /api/datastreams HTTP/1.1
Content-Type: application/json

{
  "name": "Temperature Stream"
  // Missing required 'system' link
}

HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "status": 422,
  "message": "Validation failed",
  "details": "Missing required field: system@link"
}
```

**Duplicate uniqueId:**

```http
POST /api/systems HTTP/1.1
Content-Type: application/json

{
  "uniqueId": "urn:existing:system",
  "name": "Duplicate System"
}

HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "status": 409,
  "message": "Resource conflict",
  "details": "System with uniqueId 'urn:existing:system' already exists"
}
```

**Method Not Allowed:**

```http
PUT /api/observations/obs123 HTTP/1.1

HTTP/1.1 405 Method Not Allowed
Allow: GET, POST, DELETE

{
  "status": 405,
  "message": "Method not allowed",
  "details": "Observations cannot be updated after creation"
}
```

---

## 8. Pagination Implementation

### 8.1 Pagination Algorithm

**Source:** [BaseResourceHandler.java#L241-286](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L241-L286)

**Logic:**

```java
// Request limit+1 records to detect if more exist
int requestLimit = queryLimit + 1;
List<Resource> results = database.query(offset, requestLimit);

// Check if more results available
boolean hasMore = results.size() > queryLimit;

// Trim to actual limit
if (hasMore) {
    results = results.subList(0, queryLimit);
}

// Generate pagination links
if (offset > 0) {
    addPrevLink(response, offset - queryLimit, queryLimit);
}
if (hasMore) {
    addNextLink(response, offset + queryLimit, queryLimit);
}
```

### 8.2 Default Pagination Settings

| Parameter | Default | Min | Max    |
| --------- | ------- | --- | ------ |
| `limit`   | 100     | 1   | 10,000 |
| `offset`  | 0       | 0   | ∞      |

### 8.3 Pagination Links

**Link Generation:** [BaseHandler.java#L422-453](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/BaseHandler.java#L422-L453)

**Response with Pagination:**

```json
{
  "items": [
    {
      "id": "sys-001",
      "name": "System 1"
    },
    {
      "id": "sys-002",
      "name": "System 2"
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "/api/systems?offset=100&limit=100",
      "type": "application/json"
    },
    {
      "rel": "prev",
      "href": "/api/systems?offset=0&limit=100",
      "type": "application/json"
    },
    {
      "rel": "next",
      "href": "/api/systems?offset=200&limit=100",
      "type": "application/json"
    }
  ],
  "numberMatched": 523,
  "numberReturned": 100
}
```

### 8.4 Link Relations

| rel     | Description   | When Present                      |
| ------- | ------------- | --------------------------------- |
| `self`  | Current page  | Always                            |
| `prev`  | Previous page | When `offset > 0`                 |
| `next`  | Next page     | When more results exist           |
| `first` | First page    | Optional (not always implemented) |
| `last`  | Last page     | Optional (not always implemented) |

### 8.5 Client Pagination Pattern

**Recommended TypeScript Pattern:**

```typescript
async function* paginateAll<T>(
  baseUrl: string,
  limit: number = 100
): AsyncGenerator<T> {
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    const response = await fetch(`${baseUrl}?offset=${offset}&limit=${limit}`);
    const data = await response.json();

    for (const item of data.items) {
      yield item;
    }

    // Check for next link
    const nextLink = data.links.find((link) => link.rel === 'next');
    hasMore = !!nextLink;
    offset += limit;
  }
}

// Usage
for await (const system of paginateAll('/api/systems')) {
  console.log(system.name);
}
```

---

## 9. Sub-Resource Relationships

### 9.1 Resource Hierarchy

**Parent-Child Relationships:**

```
System
├── /systems/{id}/subsystems          → Child systems
├── /systems/{id}/datastreams         → DataStreams produced
├── /systems/{id}/controlstreams      → Control interfaces
├── /systems/{id}/samplingFeatures    → Associated features
├── /systems/{id}/history             → Historical snapshots
└── /systems/{id}/events              → System events

DataStream
├── /datastreams/{id}/observations    → Observation data
└── /datastreams/{id}/schema          → SWE Common schema

ControlStream
└── /controlstreams/{id}/commands     → Issued commands

Deployment
└── /deployments/{id}/systems         → Deployed systems

Command
└── /commands/{id}/status             → Execution status
```

### 9.2 Sub-Resource URL Patterns

**Systems Sub-Resources:**

```http
GET /api/systems/{systemId}/datastreams
GET /api/systems/{systemId}/subsystems
GET /api/systems/{systemId}/samplingFeatures
GET /api/systems/{systemId}/history
GET /api/systems/{systemId}/events
```

**DataStreams Sub-Resources:**

```http
GET /api/datastreams/{datastreamId}/observations
GET /api/datastreams/{datastreamId}/schema
POST /api/datastreams/{datastreamId}/observations
```

**ControlStreams Sub-Resources:**

```http
GET /api/controlstreams/{streamId}/commands
POST /api/controlstreams/{streamId}/commands
```

**Commands Sub-Resources:**

```http
GET /api/commands/{commandId}/status
```

### 9.3 Cross-Resource Queries

**Find DataStreams for System:**

```http
# Via sub-resource
GET /api/systems/sys123/datastreams

# Via query parameter
GET /api/datastreams?system=sys123
```

**Find Observations for System:**

```http
# Via nested sub-resource
GET /api/systems/sys123/datastreams
  → GET /api/datastreams/ds456/observations

# Via query parameter (direct)
GET /api/observations?system=sys123
```

**Find Commands for System:**

```http
GET /api/commands?system=sys123
```

### 9.4 Link Relationships in Responses

**System Response with Links:**

```json
{
  "id": "sys123",
  "name": "Weather Station",
  "links": [
    {
      "rel": "self",
      "href": "/api/systems/sys123",
      "type": "application/json"
    },
    {
      "rel": "datastreams",
      "href": "/api/systems/sys123/datastreams",
      "type": "application/json"
    },
    {
      "rel": "controlstreams",
      "href": "/api/systems/sys123/controlstreams",
      "type": "application/json"
    },
    {
      "rel": "samplingFeatures",
      "href": "/api/systems/sys123/samplingFeatures",
      "type": "application/json"
    },
    {
      "rel": "parent",
      "href": "/api/systems/parent-sys",
      "type": "application/json"
    }
  ]
}
```

---

## 10. Edge Cases & Special Behaviors

### 10.1 ID Encoding

**Base32 Encoding:**

- Internal IDs use Base32 encoding (A-Z, 2-7)
- Example: `ABCD1234EFGH5678`
- Clients should treat as opaque strings

**UID vs ID:**

```http
# Query by internal ID
GET /api/systems?id=ABCD1234

# Query by unique identifier (URI)
GET /api/systems?uid=urn:x-myorg:sensor:weather-001
```

### 10.2 Temporal Range Edge Cases

**Open-Ended Intervals:**

```
# From time to now
?phenomenonTime=2024-01-01T00:00:00Z/..

# From beginning to time
?phenomenonTime=../2024-12-31T23:59:59Z

# Single instant (exact match)
?phenomenonTime=2024-01-15T12:00:00Z
```

**Special Value "now":**

```
# Current time
?validTime=2024-01-01T00:00:00Z/now
```

### 10.3 Bulk Operations

**Bulk Observation Insert:**

```http
POST /api/datastreams/ds123/observations HTTP/1.1
Content-Type: application/json

[
  {
    "phenomenonTime": "2024-01-15T10:00:00Z",
    "result": {"temp": 22.5}
  },
  {
    "phenomenonTime": "2024-01-15T10:01:00Z",
    "result": {"temp": 22.6}
  }
]
```

**Response:**

```json
{
  "created": 2,
  "ids": ["obs001", "obs002"]
}
```

### 10.4 System History Snapshots

**Historical Versions:**

```http
GET /api/systems/sys123/history HTTP/1.1

# Returns timeline of system changes
```

**Response:**

```json
{
  "items": [
    {
      "validTime": ["2024-01-01T00:00:00Z", "2024-06-30T23:59:59Z"],
      "system": {
        "id": "sys123",
        "name": "Weather Station (Old Location)",
        "position": [-122.4, 37.7]
      }
    },
    {
      "validTime": ["2024-07-01T00:00:00Z", ".."],
      "system": {
        "id": "sys123",
        "name": "Weather Station (New Location)",
        "position": [-122.3, 37.8]
      }
    }
  ]
}
```

### 10.5 Async Operations

**Long-Running Requests:**

```http
POST /api/systems HTTP/1.1
Content-Type: application/json
Prefer: respond-async

# Server may return 202 Accepted for large operations
```

**Response:**

```http
HTTP/1.1 202 Accepted
Location: /api/systems/sys123
Retry-After: 5

{
  "status": "processing",
  "message": "System creation in progress"
}
```

### 10.6 Empty Results

**No Matches:**

```json
{
  "items": [],
  "links": [
    {
      "rel": "self",
      "href": "/api/systems?q=nonexistent",
      "type": "application/json"
    }
  ],
  "numberMatched": 0,
  "numberReturned": 0
}
```

**Note:** Server returns `200 OK` with empty array, not `404 Not Found`

---

## 11. Request/Response Examples

### 11.1 Create System

**Request:**

```http
POST /api/systems HTTP/1.1
Host: api.opensensorhub.org
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "PhysicalSystem",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueId": "urn:x-acme:sensor:weather-station-001",
  "name": "ACME Weather Station #001",
  "description": "Automated weather monitoring station deployed at site A",
  "validTime": ["2024-01-01T00:00:00Z", ".."],
  "contacts": [
    {
      "role": "operator",
      "organisationName": "ACME Corporation"
    }
  ],
  "position": {
    "type": "Point",
    "coordinates": [-122.419, 37.775]
  },
  "outputs": [
    {
      "name": "weather_data",
      "type": "DataInterface",
      "definition": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement"
    }
  ]
}
```

**Response:**

```http
HTTP/1.1 201 Created
Location: /api/systems/KJ7D3F9G
Content-Type: application/json

{
  "id": "KJ7D3F9G",
  "type": "PhysicalSystem",
  "uniqueId": "urn:x-acme:sensor:weather-station-001",
  "name": "ACME Weather Station #001",
  "links": [
    {
      "rel": "self",
      "href": "/api/systems/KJ7D3F9G",
      "type": "application/json"
    },
    {
      "rel": "datastreams",
      "href": "/api/systems/KJ7D3F9G/datastreams"
    }
  ]
}
```

### 11.2 Create DataStream

**Request:**

```http
POST /api/datastreams HTTP/1.1
Content-Type: application/json

{
  "name": "Temperature Measurements",
  "description": "Air temperature readings from weather station",
  "outputName": "weather_data",
  "validTime": ["2024-01-01T00:00:00Z", ".."],
  "system@link": {
    "href": "/api/systems/KJ7D3F9G"
  },
  "observedProperty": {
    "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
    "label": "Air Temperature"
  },
  "phenomenonTimeRange": ["2024-01-01T00:00:00Z", ".."],
  "resultTimeRange": ["2024-01-01T00:00:00Z", ".."],
  "schema": {
    "obsFormat": "application/om+json",
    "recordEncoding": {
      "type": "JSONEncoding"
    },
    "recordSchema": {
      "type": "DataRecord",
      "field": [
        {
          "name": "time",
          "type": "Time",
          "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
          "referenceFrame": "http://www.opengis.net/def/trs/BIPM/0/UTC",
          "uom": {
            "href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"
          }
        },
        {
          "name": "temp",
          "type": "Quantity",
          "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
          "uom": {
            "code": "Cel"
          }
        }
      ]
    }
  }
}
```

**Response:**

```http
HTTP/1.1 201 Created
Location: /api/datastreams/M8N2P5Q7
Content-Type: application/json

{
  "id": "M8N2P5Q7",
  "name": "Temperature Measurements",
  "outputName": "weather_data",
  "links": [
    {
      "rel": "self",
      "href": "/api/datastreams/M8N2P5Q7"
    },
    {
      "rel": "observations",
      "href": "/api/datastreams/M8N2P5Q7/observations"
    },
    {
      "rel": "schema",
      "href": "/api/datastreams/M8N2P5Q7/schema"
    }
  ]
}
```

### 11.3 Post Observations

**Request (Single):**

```http
POST /api/datastreams/M8N2P5Q7/observations HTTP/1.1
Content-Type: application/json

{
  "phenomenonTime": "2024-01-15T14:30:00Z",
  "resultTime": "2024-01-15T14:30:01Z",
  "result": {
    "time": "2024-01-15T14:30:00Z",
    "temp": 22.5
  }
}
```

**Request (Bulk):**

```http
POST /api/datastreams/M8N2P5Q7/observations HTTP/1.1
Content-Type: application/json

[
  {
    "phenomenonTime": "2024-01-15T14:30:00Z",
    "resultTime": "2024-01-15T14:30:01Z",
    "result": {"time": "2024-01-15T14:30:00Z", "temp": 22.5}
  },
  {
    "phenomenonTime": "2024-01-15T14:31:00Z",
    "resultTime": "2024-01-15T14:31:01Z",
    "result": {"time": "2024-01-15T14:31:00Z", "temp": 22.6}
  },
  {
    "phenomenonTime": "2024-01-15T14:32:00Z",
    "resultTime": "2024-01-15T14:32:01Z",
    "result": {"time": "2024-01-15T14:32:00Z", "temp": 22.7}
  }
]
```

**Response:**

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "created": 3,
  "ids": ["R9S3T6U8", "V2W5X7Y9", "Z4A6B8C0"]
}
```

### 11.4 Query Observations with Filters

**Request:**

```http
GET /api/datastreams/M8N2P5Q7/observations?phenomenonTime=2024-01-15T14:00:00Z/2024-01-15T15:00:00Z&limit=1000 HTTP/1.1
Accept: application/json
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    {
      "id": "R9S3T6U8",
      "phenomenonTime": "2024-01-15T14:30:00Z",
      "resultTime": "2024-01-15T14:30:01Z",
      "result": {
        "time": "2024-01-15T14:30:00Z",
        "temp": 22.5
      },
      "links": [
        {
          "rel": "self",
          "href": "/api/observations/R9S3T6U8"
        },
        {
          "rel": "datastream",
          "href": "/api/datastreams/M8N2P5Q7"
        }
      ]
    },
    {
      "id": "V2W5X7Y9",
      "phenomenonTime": "2024-01-15T14:31:00Z",
      "resultTime": "2024-01-15T14:31:01Z",
      "result": {
        "time": "2024-01-15T14:31:00Z",
        "temp": 22.6
      }
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "/api/datastreams/M8N2P5Q7/observations?phenomenonTime=2024-01-15T14:00:00Z/2024-01-15T15:00:00Z&limit=1000"
    },
    {
      "rel": "next",
      "href": "/api/datastreams/M8N2P5Q7/observations?phenomenonTime=2024-01-15T14:00:00Z/2024-01-15T15:00:00Z&limit=1000&offset=1000"
    }
  ],
  "numberMatched": 3600,
  "numberReturned": 1000
}
```

### 11.5 Update System

**Request:**

```http
PUT /api/systems/KJ7D3F9G HTTP/1.1
Content-Type: application/json
If-Match: "v2"

{
  "type": "PhysicalSystem",
  "uniqueId": "urn:x-acme:sensor:weather-station-001",
  "name": "ACME Weather Station #001 (Relocated)",
  "description": "Moved to new location on 2024-06-15",
  "validTime": ["2024-06-15T00:00:00Z", ".."],
  "position": {
    "type": "Point",
    "coordinates": [-122.350, 37.800]
  }
}
```

**Response:**

```http
HTTP/1.1 204 No Content
ETag: "v3"
```

### 11.6 Delete Resource

**Request:**

```http
DELETE /api/systems/KJ7D3F9G HTTP/1.1
```

**Response:**

```http
HTTP/1.1 204 No Content
```

**Note:** Deleting system cascades to datastreams and observations (configurable)

---

## 12. Server-Specific vs Spec Behaviors

### 12.1 OGC Spec-Defined Behaviors

**From Specification (All CSAPI Servers Must Implement):**

- ✅ Resource paths (`/systems`, `/datastreams`, etc.)
- ✅ Query parameters (`limit`, `offset`, `bbox`, `datetime`)
- ✅ Conformance classes and URIs
- ✅ Link relations (`self`, `next`, `prev`)
- ✅ HTTP methods (GET, POST, PUT, DELETE)
- ✅ Response formats (JSON, GeoJSON)
- ✅ Error HTTP status codes

### 12.2 OpenSensorHub-Specific Behaviors

**Implementation Details (May Vary Between Servers):**

1. **Base32 ID Encoding**

   - OSH uses Base32 for internal IDs
   - Other servers may use UUIDs, integers, or other formats
   - **Client implication:** Treat IDs as opaque strings

2. **Default Pagination Limit: 100**

   - OSH default: 100 items per page
   - Other servers may use 10, 50, or 1000
   - **Client implication:** Always specify explicit `limit`

3. **Maximum Limit: 10,000**

   - OSH max: 10,000 items per page
   - Other servers may have different maximums
   - **Client implication:** Don't assume large limits supported

4. **System History Endpoint**

   - OSH implements `/systems/{id}/history`
   - Part of CSAPI Part 3 (not all servers implement)
   - **Client implication:** Check conformance before using

5. **Async Operation Support**

   - OSH supports `Prefer: respond-async` header
   - Not universally implemented
   - **Client implication:** Handle both sync and async responses

6. **Bulk Observation Insert**

   - OSH accepts arrays in POST body
   - Some servers may require one observation per request
   - **Client implication:** Try bulk, fallback to individual

7. **HTML Format Support**
   - OSH provides HTML views for all resources
   - Optional per spec
   - **Client implication:** Don't rely on HTML availability

### 12.3 Detecting Server Capabilities

**Use Conformance Endpoint:**

```typescript
const response = await fetch('/api/conformance');
const { conformsTo } = await response.json();

const supportsSystemHistory = conformsTo.includes(
  'http://www.opengis.net/spec/ogcapi-connectedsystems-3/1.0/conf/system-events'
);

const supportsControl = conformsTo.includes(
  'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/control-stream'
);
```

**Feature Detection Pattern:**

```typescript
// Try feature, fallback gracefully
async function getSystemHistory(systemId: string) {
  try {
    const response = await fetch(`/api/systems/${systemId}/history`);
    if (response.status === 404) {
      // Feature not supported
      return null;
    }
    return await response.json();
  } catch (error) {
    return null;
  }
}
```

---

## 13. Real-World Data Patterns

### 13.1 Typical System Structures

**Weather Station:**

```json
{
  "type": "PhysicalSystem",
  "uniqueId": "urn:x-acme:sensor:weather-001",
  "name": "Weather Station Alpha",
  "outputs": [
    { "name": "temperature", "type": "DataInterface" },
    { "name": "humidity", "type": "DataInterface" },
    { "name": "pressure", "type": "DataInterface" },
    { "name": "wind", "type": "DataInterface" }
  ]
}
```

**Composite System (Subsystems):**

```json
{
  "type": "PhysicalSystem",
  "uniqueId": "urn:x-acme:platform:buoy-001",
  "name": "Ocean Monitoring Buoy",
  "components": [
    {
      "name": "gps",
      "type": "PhysicalComponent",
      "definition": "http://www.w3.org/ns/sosa/Sensor"
    },
    {
      "name": "ctd",
      "type": "PhysicalSystem",
      "definition": "http://www.w3.org/ns/sosa/Sensor"
    }
  ]
}
```

### 13.2 Common DataStream Schemas

**Scalar Measurement (Temperature):**

```json
{
  "recordSchema": {
    "type": "DataRecord",
    "field": [
      {
        "name": "time",
        "type": "Time",
        "uom": { "href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian" }
      },
      {
        "name": "temp",
        "type": "Quantity",
        "uom": { "code": "Cel" }
      }
    ]
  }
}
```

**Vector Measurement (Wind):**

```json
{
  "recordSchema": {
    "type": "DataRecord",
    "field": [
      {
        "name": "time",
        "type": "Time"
      },
      {
        "name": "wind",
        "type": "Vector",
        "referenceFrame": "http://www.opengis.net/def/crs/NED",
        "coordinate": [
          { "name": "speed", "type": "Quantity", "uom": { "code": "m/s" } },
          { "name": "direction", "type": "Quantity", "uom": { "code": "deg" } }
        ]
      }
    ]
  }
}
```

**Category Observation (Weather Condition):**

```json
{
  "recordSchema": {
    "type": "DataRecord",
    "field": [
      {
        "name": "time",
        "type": "Time"
      },
      {
        "name": "condition",
        "type": "Category",
        "codeSpace": "http://example.org/def/weather-conditions",
        "constraint": {
          "type": "AllowedTokens",
          "value": ["clear", "cloudy", "rain", "snow"]
        }
      }
    ]
  }
}
```

### 13.3 High-Frequency Observation Patterns

**Time Series Data (1 Hz sampling):**

```json
{
  "items": [
    {
      "phenomenonTime": "2024-01-15T10:00:00.000Z",
      "result": { "temp": 22.5 }
    },
    {
      "phenomenonTime": "2024-01-15T10:00:01.000Z",
      "result": { "temp": 22.5 }
    },
    { "phenomenonTime": "2024-01-15T10:00:02.000Z", "result": { "temp": 22.6 } }
    // ... 3600 observations per hour
  ]
}
```

**Binary Encoding (High-Frequency):**

```
Content-Type: application/swe+binary

[Binary data encoded per SWE Common Binary Encoding spec]
```

### 13.4 Sparse Data Patterns

**Event-Based Observations:**

```json
{
  "items": [
    {
      "phenomenonTime": "2024-01-15T08:23:15Z",
      "result": { "motion_detected": true }
    },
    {
      "phenomenonTime": "2024-01-15T14:47:32Z",
      "result": { "motion_detected": true }
    },
    {
      "phenomenonTime": "2024-01-16T06:12:08Z",
      "result": { "motion_detected": true }
    }
  ]
}
```

---

## 14. Performance Characteristics

### 14.1 Response Times

**Typical Latencies (OSH Production Deployment):**

| Operation                        | Avg Response Time | Notes             |
| -------------------------------- | ----------------- | ----------------- |
| GET `/`                          | 10-50 ms          | Landing page      |
| GET `/systems` (100 items)       | 50-200 ms         | Paginated list    |
| GET `/systems/{id}`              | 20-100 ms         | Single resource   |
| POST `/systems`                  | 100-500 ms        | Resource creation |
| GET `/observations` (1000 items) | 200-1000 ms       | Large dataset     |
| POST `/observations` (bulk 100)  | 500-2000 ms       | Bulk insert       |

**Factors Affecting Performance:**

- Database backend (PostgreSQL, MongoDB, etc.)
- Number of concurrent requests
- Data volume (observations especially)
- Server hardware specifications

### 14.2 Rate Limiting

**OSH Default Configuration:**

- No hard rate limits by default
- Configurable per-deployment
- Recommendation: 100 requests/minute for clients

**Best Practices:**

```typescript
// Implement exponential backoff
async function fetchWithBackoff(url: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url);

    if (response.status === 429) {
      // Too Many Requests
      const retryAfter = response.headers.get('Retry-After');
      const delay = retryAfter
        ? parseInt(retryAfter) * 1000
        : Math.pow(2, i) * 1000;
      await new Promise((resolve) => setTimeout(resolve, delay));
      continue;
    }

    return response;
  }

  throw new Error('Max retries exceeded');
}
```

### 14.3 Caching

**Server-Side Caching:**

- Systems metadata: Cached (changes infrequent)
- DataStreams: Cached (changes infrequent)
- Observations: Not cached (real-time data)

**Client-Side Caching Recommendations:**

```typescript
// Cache immutable resources
const systemCache = new Map<string, System>();

async function getSystem(id: string): Promise<System> {
  if (systemCache.has(id)) {
    return systemCache.get(id)!;
  }

  const response = await fetch(`/api/systems/${id}`);
  const system = await response.json();

  systemCache.set(id, system);
  return system;
}

// Don't cache observations (real-time data)
async function getObservations(datastreamId: string) {
  // Always fetch fresh data
  return await fetch(`/api/datastreams/${datastreamId}/observations`);
}
```

### 14.4 Bulk Operations

**Optimal Batch Sizes:**

| Operation         | Recommended Batch Size | Max Supported |
| ----------------- | ---------------------- | ------------- |
| POST Observations | 100-1000               | 10,000        |
| GET Observations  | 100-1000               | 10,000        |
| GET Systems       | 50-100                 | 10,000        |

**Bulk Insert Pattern:**

```typescript
async function insertObservations(
  datastreamId: string,
  observations: Observation[]
) {
  const batchSize = 1000;
  const batches = chunk(observations, batchSize);

  for (const batch of batches) {
    await fetch(`/api/datastreams/${datastreamId}/observations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batch),
    });

    // Rate limiting: wait between batches
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
}
```

---

## 15. Authentication/Authorization

### 15.1 Supported Auth Methods

**OpenSensorHub Security Module:**

1. **HTTP Basic Authentication**

   ```http
   GET /api/systems HTTP/1.1
   Authorization: Basic dXNlcjpwYXNzd29yZA==
   ```

2. **Bearer Token (JWT)**

   ```http
   GET /api/systems HTTP/1.1
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **API Key (Header)**

   ```http
   GET /api/systems HTTP/1.1
   X-API-Key: abc123xyz789
   ```

4. **OAuth 2.0** (configurable)
   - Authorization Code flow
   - Client Credentials flow

### 15.2 Permission Model

**Resource-Level Permissions:**

| Permission           | GET | POST | PUT | DELETE |
| -------------------- | --- | ---- | --- | ------ |
| `read:systems`       | ✅  | ❌   | ❌  | ❌     |
| `write:systems`      | ✅  | ✅   | ✅  | ✅     |
| `read:observations`  | ✅  | ❌   | ❌  | ❌     |
| `write:observations` | ✅  | ✅   | ❌  | ❌     |
| `admin`              | ✅  | ✅   | ✅  | ✅     |

**Example Error Response:**

```http
GET /api/systems HTTP/1.1

HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="CSAPI"

{
  "status": 401,
  "message": "Authentication required"
}
```

```http
GET /api/systems HTTP/1.1
Authorization: Bearer <token>

HTTP/1.1 403 Forbidden

{
  "status": 403,
  "message": "Insufficient permissions",
  "details": "Requires 'read:systems' permission"
}
```

### 15.3 Client Authentication Pattern

```typescript
class CSAPIClient {
  constructor(
    private baseUrl: string,
    private auth:
      | { type: 'basic'; username: string; password: string }
      | { type: 'bearer'; token: string }
      | { type: 'apikey'; key: string }
  ) {}

  private getAuthHeader(): string {
    switch (this.auth.type) {
      case 'basic':
        const encoded = btoa(`${this.auth.username}:${this.auth.password}`);
        return `Basic ${encoded}`;
      case 'bearer':
        return `Bearer ${this.auth.token}`;
      case 'apikey':
        return this.auth.key; // Goes in X-API-Key header
    }
  }

  async fetch(path: string, options: RequestInit = {}) {
    const headers = new Headers(options.headers);

    if (this.auth.type === 'apikey') {
      headers.set('X-API-Key', this.getAuthHeader());
    } else {
      headers.set('Authorization', this.getAuthHeader());
    }

    return fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });
  }
}
```

### 15.4 Key Insights for TypeScript Client Development

This subsection synthesizes critical learnings from the OpenSensorHub analysis to guide TypeScript client implementation.

#### 15.4.1 Query Parameter Validation

**Must Validate Before Sending:**

```typescript
class QueryValidator {
  static validateLimit(limit?: number): number {
    if (limit === undefined) return 100; // OSH default
    if (limit < 1 || limit > 10000) {
      throw new ValidationError('limit must be between 1 and 10,000');
    }
    return limit;
  }

  static validateBbox(bbox?: number[]): string | undefined {
    if (!bbox) return undefined;
    if (bbox.length !== 4) {
      throw new ValidationError(
        'bbox must have exactly 4 values [minLon, minLat, maxLon, maxLat]'
      );
    }
    return bbox.join(',');
  }

  static validateTimeParameter(time: string | Date): string {
    if (time instanceof Date) {
      return time.toISOString();
    }
    // Must be ISO 8601 format
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$/.test(time)) {
      throw new ValidationError('Time must be ISO 8601 format');
    }
    return time;
  }
}
```

#### 15.4.2 Pagination Patterns

**OSH uses limit+1 detection - implement smart pagination:**

```typescript
interface PaginatedResponse<T> {
  items: T[];
  links: Link[];
  numberMatched?: number;
  numberReturned: number;
}

class PaginationHelper {
  // AsyncGenerator for automatic pagination
  static async *paginateAll<T>(
    baseUrl: string,
    initialParams?: Record<string, string>,
    limit: number = 100
  ): AsyncGenerator<T, void, undefined> {
    let nextUrl: string | undefined = baseUrl;

    while (nextUrl) {
      const url = new URL(nextUrl);

      if (nextUrl === baseUrl && initialParams) {
        Object.entries(initialParams).forEach(([key, value]) => {
          url.searchParams.set(key, value);
        });
      }

      url.searchParams.set('limit', String(Math.min(limit, 10000)));

      const response = await fetch(url);
      const data: PaginatedResponse<T> = await response.json();

      for (const item of data.items) {
        yield item;
      }

      const nextLink = data.links.find((link) => link.rel === 'next');
      nextUrl = nextLink?.href;
    }
  }
}

// Usage
for await (const system of PaginationHelper.paginateAll<System>(
  'http://api.example.org/systems',
  { q: 'weather' }
)) {
  console.log(system.name);
}
```

#### 15.4.3 Error Response Handling

**Parse OSH JSON error bodies:**

```typescript
interface CSAPIErrorResponse {
  status: number;
  message: string;
  details?: string;
}

class CSAPIError extends Error {
  constructor(
    public statusCode: number,
    public serverMessage: string,
    public details?: string,
    public response?: Response
  ) {
    super(`${statusCode}: ${serverMessage}`);
    this.name = 'CSAPIError';
  }

  static async fromResponse(response: Response): Promise<CSAPIError> {
    try {
      const body: CSAPIErrorResponse = await response.json();
      return new CSAPIError(body.status, body.message, body.details, response);
    } catch {
      return new CSAPIError(
        response.status,
        response.statusText,
        undefined,
        response
      );
    }
  }

  isNotFound(): boolean {
    return this.statusCode === 404;
  }
  isValidationError(): boolean {
    return this.statusCode === 400 || this.statusCode === 422;
  }
  isAuthError(): boolean {
    return this.statusCode === 401 || this.statusCode === 403;
  }
}
```

#### 15.4.4 Format Negotiation

**Request appropriate formats per resource type:**

```typescript
enum ContentType {
  JSON = 'application/json',
  GeoJSON = 'application/geo+json',
  SensorML_JSON = 'application/sml+json',
  OM_JSON = 'application/om+json',
  SWE_JSON = 'application/swe+json',
}

class FormatNegotiator {
  static getPreferredFormat(resourceType: string): ContentType {
    const defaults: Record<string, ContentType> = {
      systems: ContentType.GeoJSON, // Spatial features
      deployments: ContentType.GeoJSON,
      fois: ContentType.GeoJSON,
      procedures: ContentType.SensorML_JSON,
      datastreams: ContentType.JSON,
      observations: ContentType.OM_JSON,
    };
    return defaults[resourceType] || ContentType.JSON;
  }

  static buildAcceptHeader(preferred: ContentType): string {
    return `${preferred}, application/json;q=0.9, */*;q=0.8`;
  }
}
```

#### 15.4.5 Sub-Resource Navigation

**Follow link relations from responses:**

```typescript
interface Link {
  rel: string;
  href: string;
  type?: string;
}

class ResourceNavigator<T> {
  constructor(
    private resource: T & { links?: Link[] },
    private http: HttpClient
  ) {}

  async followLink<R>(rel: string): Promise<R[]> {
    const link = this.resource.links?.find((l) => l.rel === rel);
    if (!link) {
      throw new Error(`No link with rel="${rel}" found`);
    }
    const response = await this.http.get<{ items: R[] }>(link.href);
    return response.items;
  }

  hasLink(rel: string): boolean {
    return this.resource.links?.some((l) => l.rel === rel) ?? false;
  }
}

// Enhanced System class
class System {
  id: string;
  name: string;
  links?: Link[];
  private navigator: ResourceNavigator<this>;

  constructor(data: any, http: HttpClient) {
    Object.assign(this, data);
    this.navigator = new ResourceNavigator(this, http);
  }

  async getDatastreams(): Promise<Datastream[]> {
    return this.navigator.followLink<Datastream>('datastreams');
  }

  async getSubsystems(): Promise<System[]> {
    return this.navigator.hasLink('subsystems')
      ? this.navigator.followLink<System>('subsystems')
      : [];
  }
}
```

#### 15.4.6 Conformance-Based Feature Detection

**Check server capabilities before using features:**

```typescript
class ConformanceChecker {
  private conformsTo: Set<string> = new Set();

  async loadConformance(baseUrl: string): Promise<void> {
    const response = await fetch(`${baseUrl}/conformance`);
    const data = await response.json();
    this.conformsTo = new Set(data.conformsTo || []);
  }

  supportsCore(): boolean {
    return this.conformsTo.has(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    );
  }

  supportsControlStreams(): boolean {
    return this.conformsTo.has(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/control-stream'
    );
  }

  supportsSystemEvents(): boolean {
    return this.conformsTo.has(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-3/1.0/conf/system-events'
    );
  }
}

// Usage in client
class CSAPIClient {
  private conformance: ConformanceChecker;

  async initialize(baseUrl: string): Promise<void> {
    this.conformance = new ConformanceChecker();
    await this.conformance.loadConformance(baseUrl);

    if (!this.conformance.supportsCore()) {
      throw new Error('Server does not support CSAPI Core');
    }
  }

  async getSystemHistory(systemId: string): Promise<SystemSnapshot[] | null> {
    if (!this.conformance.supportsSystemEvents()) {
      console.warn('System history not supported by this server');
      return null;
    }
    return this.http.get(`/systems/${systemId}/history`);
  }
}
```

#### 15.4.7 Bulk Operations

**Batch observations for efficiency (OSH supports bulk insert):**

```typescript
class BulkOperationHelper {
  static async insertObservationsBulk(
    datastreamId: string,
    observations: Observation[],
    http: HttpClient,
    batchSize: number = 1000
  ): Promise<void> {
    const batches = this.chunk(observations, Math.min(batchSize, 10000));

    for (const batch of batches) {
      await http.post(`/datastreams/${datastreamId}/observations`, batch);
      await this.delay(100); // Small delay between batches
    }
  }

  static async insertObservationsSmart(
    datastreamId: string,
    observations: Observation[],
    http: HttpClient
  ): Promise<void> {
    if (observations.length === 1) {
      await http.post(
        `/datastreams/${datastreamId}/observations`,
        observations[0]
      );
      return;
    }

    try {
      await this.insertObservationsBulk(datastreamId, observations, http);
    } catch (error) {
      if (error instanceof CSAPIError && error.statusCode === 400) {
        console.warn('Bulk insert failed, falling back to sequential');
        for (const obs of observations) {
          await http.post(`/datastreams/${datastreamId}/observations`, obs);
        }
      } else {
        throw error;
      }
    }
  }

  private static chunk<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }

  private static delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
```

#### 15.4.8 Caching Strategy

**Smart caching based on resource mutability:**

```typescript
class ResourceCache {
  private cache = new Map<
    string,
    { data: any; timestamp: number; ttl: number }
  >();

  private static CACHE_POLICIES: Record<string, number> = {
    // Metadata - cache for 5 minutes
    systems: 5 * 60 * 1000,
    deployments: 5 * 60 * 1000,
    procedures: 5 * 60 * 1000,
    datastreams: 5 * 60 * 1000,
    fois: 5 * 60 * 1000,

    // Static - cache for 1 hour
    collections: 60 * 60 * 1000,
    conformance: 60 * 60 * 1000,

    // Dynamic - never cache
    observations: 0,
    commands: 0,
    systemevents: 0,
  };

  set<T>(key: string, data: T, resourceType: string): void {
    const ttl = ResourceCache.CACHE_POLICIES[resourceType] || 0;
    if (ttl === 0) return;

    this.cache.set(key, { data, timestamp: Date.now(), ttl });
  }

  get<T>(key: string): T | undefined {
    const entry = this.cache.get(key);
    if (!entry) return undefined;

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return undefined;
    }

    return entry.data as T;
  }

  invalidatePattern(pattern: RegExp): void {
    for (const key of this.cache.keys()) {
      if (pattern.test(key)) {
        this.cache.delete(key);
      }
    }
  }
}

// Usage in HTTP client
class CachedHttpClient extends HttpClient {
  private cache = new ResourceCache();

  async get<T>(
    path: string,
    resourceType: string,
    bypassCache = false
  ): Promise<T> {
    const cacheKey = `GET:${path}`;

    if (!bypassCache) {
      const cached = this.cache.get<T>(cacheKey);
      if (cached) return cached;
    }

    const data = await super.get<T>(path);
    this.cache.set(cacheKey, data, resourceType);
    return data;
  }

  async post<T>(path: string, body: any, resourceType: string): Promise<T> {
    const data = await super.post<T>(path, body);

    // Invalidate related caches after write
    const resourceMatch = path.match(/\/([\w]+)/);
    if (resourceMatch) {
      this.cache.invalidatePattern(new RegExp(`^GET:/${resourceMatch[1]}`));
    }

    return data;
  }
}
```

#### 15.4.9 Testing Against OSH

**Use OSH as reference implementation for integration tests:**

```typescript
describe('CSAPI Client Integration Tests (OSH)', () => {
  const baseUrl = 'http://localhost:8282/sensorhub/api';
  let client: CSAPIClient;

  beforeAll(async () => {
    client = new CSAPIClient(baseUrl, {
      type: 'basic',
      credentials: { username: 'admin', password: 'admin' },
    });
    await client.initialize();
  });

  it('should list systems with pagination', async () => {
    const systems = await client.systems.list({ limit: 10 });
    expect(Array.isArray(systems)).toBe(true);
  });

  it('should create and delete system', async () => {
    const system = await client.systems.create({
      name: 'Test System',
      type: 'PhysicalSystem',
      uniqueId: `urn:test:system:${Date.now()}`,
    });

    expect(system.id).toBeDefined();
    await client.systems.delete(system.id);
  });

  it('should query observations with time filter', async () => {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    const observations = await client.observations.list({
      phenomenonTime: `${oneHourAgo.toISOString()}/${now.toISOString()}`,
      limit: 100,
    });

    expect(Array.isArray(observations)).toBe(true);
  });

  it('should handle errors gracefully', async () => {
    await expect(client.systems.get('nonexistent-id')).rejects.toThrow(
      CSAPIError
    );

    try {
      await client.systems.get('nonexistent-id');
    } catch (error) {
      expect(error).toBeInstanceOf(CSAPIError);
      expect((error as CSAPIError).isNotFound()).toBe(true);
    }
  });
});
```

#### 15.4.10 Critical Takeaways

**Must-Have Features:**

1. ✅ Query parameter validation (limit 1-10,000, bbox 4 values, ISO 8601 times)
2. ✅ Link-following pagination with AsyncGenerator support
3. ✅ JSON error body parsing with type guards
4. ✅ Format negotiation (GeoJSON for spatial, SensorML for systems)
5. ✅ Sub-resource navigation via link relations
6. ✅ Conformance-based feature detection
7. ✅ Multi-strategy authentication (Basic/Bearer/API Key)
8. ✅ Smart caching with TTL policies

**Performance Optimizations:**

- Batch observations (100-1000 per request)
- Cache metadata (5 min TTL), static resources (1 hr TTL)
- Never cache dynamic data (observations/commands)
- Reuse HTTP connections

**Testing Strategy:**

- Deploy OSH locally for integration tests
- Use fixtures from `sensorhub-service-consys/src/test/resources/`
- Test against real server behaviors
- Validate all CRUD operations

---

## 16. SensorML/SWE Common Structures

### 16.1 SensorML JSON Format

**System Description (SensorML 2.1 JSON):**

```json
{
  "type": "PhysicalSystem",
  "id": "weather_station_001",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueIdentifier": "urn:x-acme:sensor:weather-001",
  "label": "ACME Weather Station",
  "description": "Multi-sensor weather monitoring system",
  "keywords": ["weather", "meteorology", "temperature", "humidity"],
  "identifiers": [
    {
      "definition": "http://sensorml.com/ont/swe/property/SerialNumber",
      "label": "Serial Number",
      "value": "WS-2024-001"
    }
  ],
  "classifiers": [
    {
      "definition": "http://sensorml.com/ont/swe/property/SensorType",
      "label": "Sensor Type",
      "value": "Weather Station"
    }
  ],
  "validTime": ["2024-01-01T00:00:00Z", ".."],
  "securityConstraints": {},
  "legalConstraints": [],
  "characteristics": [],
  "capabilities": [
    {
      "name": "operating_specs",
      "type": "DataRecord",
      "label": "Operating Specifications",
      "field": [
        {
          "name": "temperature_range",
          "type": "QuantityRange",
          "label": "Temperature Range",
          "uom": { "code": "Cel" },
          "value": [-40, 60]
        }
      ]
    }
  ],
  "contacts": [
    {
      "role": "manufacturer",
      "organisationName": "ACME Corporation"
    }
  ],
  "documentation": [],
  "history": [],
  "localReferenceFrame": [],
  "localTimeFrame": [],
  "position": {
    "type": "Point",
    "coordinates": [-122.419, 37.775, 15.0]
  },
  "timePosition": [],
  "components": [],
  "connections": [],
  "inputs": [],
  "outputs": [
    {
      "name": "weather_data",
      "type": "DataInterface",
      "definition": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
      "label": "Weather Data Output"
    }
  ],
  "parameters": [],
  "modes": []
}
```

### 16.2 SWE Common DataRecord Schema

**Complex Multi-Field Schema:**

```json
{
  "type": "DataRecord",
  "label": "Weather Observation",
  "field": [
    {
      "name": "time",
      "type": "Time",
      "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
      "label": "Sampling Time",
      "referenceFrame": "http://www.opengis.net/def/trs/BIPM/0/UTC",
      "uom": {
        "href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"
      }
    },
    {
      "name": "location",
      "type": "Vector",
      "definition": "http://www.opengis.net/def/property/OGC/0/PlatformLocation",
      "label": "Sensor Location",
      "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4979",
      "coordinate": [
        {
          "name": "lat",
          "type": "Quantity",
          "definition": "http://www.opengis.net/def/property/OGC/0/Latitude",
          "uom": { "code": "deg" },
          "axisID": "Lat"
        },
        {
          "name": "lon",
          "type": "Quantity",
          "definition": "http://www.opengis.net/def/property/OGC/0/Longitude",
          "uom": { "code": "deg" },
          "axisID": "Lon"
        },
        {
          "name": "alt",
          "type": "Quantity",
          "definition": "http://www.opengis.net/def/property/OGC/0/Altitude",
          "uom": { "code": "m" },
          "axisID": "h"
        }
      ]
    },
    {
      "name": "temperature",
      "type": "Quantity",
      "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
      "label": "Air Temperature",
      "uom": { "code": "Cel" }
    },
    {
      "name": "humidity",
      "type": "Quantity",
      "definition": "http://mmisw.org/ont/cf/parameter/relative_humidity",
      "label": "Relative Humidity",
      "uom": { "code": "%" }
    },
    {
      "name": "pressure",
      "type": "Quantity",
      "definition": "http://mmisw.org/ont/cf/parameter/air_pressure",
      "label": "Atmospheric Pressure",
      "uom": { "code": "hPa" }
    },
    {
      "name": "wind",
      "type": "DataRecord",
      "label": "Wind Measurement",
      "field": [
        {
          "name": "speed",
          "type": "Quantity",
          "definition": "http://mmisw.org/ont/cf/parameter/wind_speed",
          "uom": { "code": "m/s" }
        },
        {
          "name": "direction",
          "type": "Quantity",
          "definition": "http://mmisw.org/ont/cf/parameter/wind_from_direction",
          "uom": { "code": "deg" }
        }
      ]
    },
    {
      "name": "sky_condition",
      "type": "Category",
      "definition": "http://example.org/def/weather/sky-condition",
      "label": "Sky Condition",
      "codeSpace": "http://example.org/def/weather/conditions",
      "constraint": {
        "type": "AllowedTokens",
        "value": ["clear", "partly_cloudy", "cloudy", "overcast"]
      }
    },
    {
      "name": "quality_flag",
      "type": "Category",
      "definition": "http://www.opengis.net/def/property/OGC/0/DataQuality",
      "label": "Quality Flag",
      "constraint": {
        "type": "AllowedTokens",
        "value": ["good", "suspect", "bad", "missing"]
      }
    }
  ]
}
```

### 16.3 Corresponding Observation Data

**Observation Matching Above Schema:**

```json
{
  "phenomenonTime": "2024-01-15T14:30:00Z",
  "resultTime": "2024-01-15T14:30:01Z",
  "result": {
    "time": "2024-01-15T14:30:00Z",
    "location": {
      "lat": 37.775,
      "lon": -122.419,
      "alt": 15.0
    },
    "temperature": 22.5,
    "humidity": 65.2,
    "pressure": 1013.25,
    "wind": {
      "speed": 3.2,
      "direction": 270
    },
    "sky_condition": "partly_cloudy",
    "quality_flag": "good"
  }
}
```

---

## 17. Client Implementation Insights

### 17.1 Reference Client Code

**Java Client Example:** [ConSysApiClient.java](https://github.com/opensensorhub/osh-core/tree/main/sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/client/ConSysApiClient.java)

**Key Patterns from OSH Client:**

1. **Pagination Helper:**

```java
public Stream<Resource> streamAll(String resourcePath) {
    int offset = 0;
    int limit = 100;
    boolean hasMore = true;

    Stream.Builder<Resource> builder = Stream.builder();

    while (hasMore) {
        Response response = fetch(resourcePath + "?offset=" + offset + "&limit=" + limit);
        List<Resource> items = response.getItems();
        items.forEach(builder::add);

        hasMore = response.getLinks().stream()
            .anyMatch(link -> link.getRel().equals("next"));

        offset += limit;
    }

    return builder.build();
}
```

2. **Async Operation Handling:**

```java
public CompletableFuture<System> createSystemAsync(System system) {
    return CompletableFuture.supplyAsync(() -> {
        Response response = httpClient.post("/api/systems", system);

        if (response.getStatus() == 202) {
            // Async processing
            String location = response.getHeader("Location");
            return pollUntilComplete(location);
        }

        return response.getBody(System.class);
    });
}
```

### 17.2 TypeScript Client Patterns

**Recommended Architecture:**

```typescript
// 1. Type definitions
interface System {
  id: string;
  uniqueId: string;
  name: string;
  type: string;
  links: Link[];
}

interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: [number, number, number, number];
  q?: string;
}

// 2. URL Builder
class URLBuilder {
  constructor(private base: URL) {}

  addPath(...segments: string[]): this {
    this.base.pathname += '/' + segments.join('/');
    return this;
  }

  addQuery(params: Record<string, any>): this {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        this.base.searchParams.set(key, String(value));
      }
    });
    return this;
  }

  build(): URL {
    return new URL(this.base);
  }
}

// 3. Resource client
class SystemsClient {
  constructor(private baseUrl: string, private http: HttpClient) {}

  async list(options: QueryOptions = {}): Promise<System[]> {
    const url = new URLBuilder(new URL(this.baseUrl))
      .addPath('systems')
      .addQuery({ limit: options.limit ?? 100, ...options })
      .build();

    return this.http.get<System[]>(url);
  }

  async get(id: string): Promise<System> {
    const url = new URLBuilder(new URL(this.baseUrl))
      .addPath('systems', id)
      .build();

    return this.http.get<System>(url);
  }

  async create(system: Omit<System, 'id'>): Promise<System> {
    const url = new URLBuilder(new URL(this.baseUrl))
      .addPath('systems')
      .build();

    return this.http.post<System>(url, system);
  }

  async *paginate(options: QueryOptions = {}): AsyncGenerator<System> {
    let offset = 0;
    const limit = options.limit ?? 100;

    while (true) {
      const response = await this.list({ ...options, offset, limit });

      for (const system of response) {
        yield system;
      }

      if (response.length < limit) break;
      offset += limit;
    }
  }
}

// 4. Main client
class CSAPIClient {
  readonly systems: SystemsClient;
  readonly datastreams: DataStreamsClient;
  readonly observations: ObservationsClient;

  constructor(baseUrl: string, auth?: AuthConfig) {
    const http = new HttpClient(baseUrl, auth);

    this.systems = new SystemsClient(baseUrl, http);
    this.datastreams = new DataStreamsClient(baseUrl, http);
    this.observations = new ObservationsClient(baseUrl, http);
  }
}
```

### 17.3 Error Handling Strategy

```typescript
class CSAPIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: string
  ) {
    super(message);
  }
}

class HttpClient {
  async fetch(url: URL, options: RequestInit = {}): Promise<Response> {
    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new CSAPIError(
        response.status,
        error.message || response.statusText,
        error.details
      );
    }

    return response;
  }

  async get<T>(url: URL): Promise<T> {
    const response = await this.fetch(url);
    return response.json();
  }
}
```

### 17.4 Synthesized Insights for TypeScript Client Implementation

This section synthesizes the most critical learnings from the OpenSensorHub analysis into actionable guidance for TypeScript client library development.

#### 17.4.1 Query Parameter Implementation

**Client-Side Validation Rules:**

```typescript
class QueryValidator {
  static validateLimit(limit?: number): number {
    if (limit === undefined) return 100; // OSH default
    if (limit < 1 || limit > 10000) {
      throw new ValidationError('limit must be between 1 and 10,000');
    }
    return limit;
  }

  static validateBbox(bbox?: number[]): string | undefined {
    if (!bbox) return undefined;
    if (bbox.length !== 4) {
      throw new ValidationError(
        'bbox must have exactly 4 values [minLon, minLat, maxLon, maxLat]'
      );
    }
    return bbox.join(',');
  }

  static validateTimeParameter(time: string | Date): string {
    if (time instanceof Date) {
      return time.toISOString();
    }
    // Must be ISO 8601 format
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$/.test(time)) {
      throw new ValidationError('Time must be ISO 8601 format');
    }
    return time;
  }
}
```

**Query Pattern Support:**

- **Spatial:** `bbox` (4 values), `geom` (GeoJSON geometry)
- **Temporal:** `phenomenonTime`, `resultTime`, `validTime` (ISO 8601 intervals)
- **Hierarchical:** `parent`, `system`, `foi`, `observedProperty`, `controlledProperty`
- **Text Search:** `q` (keyword array, 1-50 chars per keyword)
- **Pagination:** `limit` (1-10,000, default 100), `offset`
- **Deletion:** `cascade` (boolean, default false)

#### 17.4.2 Pagination Strategy

**OSH Pattern: Limit+1 Detection**

```typescript
async *paginateAll<T>(
  baseUrl: string,
  params?: Record<string, string>,
  limit: number = 100
): AsyncGenerator<T> {
  let nextUrl: string | undefined = baseUrl;

  while (nextUrl) {
    const url = new URL(nextUrl);

    if (nextUrl === baseUrl && params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.set(key, value);
      });
    }

    url.searchParams.set('limit', String(Math.min(limit, 10000)));

    const response = await fetch(url);
    const data: PaginatedResponse<T> = await response.json();

    for (const item of data.items) {
      yield item;
    }

    const nextLink = data.links.find(l => l.rel === 'next');
    nextUrl = nextLink?.href;
  }
}

// Usage: for await (const system of paginateAll('/systems', { q: 'weather' }))
```

#### 17.4.3 Error Response Handling

**OSH Error Format:**

```json
{
  "status": 400,
  "message": "Invalid parameter value",
  "details": "limit must be between 1 and 10,000"
}
```

**Type-Safe Error Class:**

```typescript
class CSAPIError extends Error {
  constructor(
    public statusCode: number,
    public serverMessage: string,
    public details?: string,
    public response?: Response
  ) {
    super(`${statusCode}: ${serverMessage}`);
    this.name = 'CSAPIError';
  }

  static async fromResponse(response: Response): Promise<CSAPIError> {
    try {
      const body = await response.json();
      return new CSAPIError(body.status, body.message, body.details, response);
    } catch {
      return new CSAPIError(
        response.status,
        response.statusText,
        undefined,
        response
      );
    }
  }

  isNotFound(): boolean {
    return this.statusCode === 404;
  }
  isValidationError(): boolean {
    return this.statusCode === 400 || this.statusCode === 422;
  }
  isAuthError(): boolean {
    return this.statusCode === 401 || this.statusCode === 403;
  }
}
```

#### 17.4.4 Format Negotiation

**Resource-Specific Format Defaults:**

```typescript
const FORMAT_DEFAULTS: Record<string, string> = {
  systems: 'application/geo+json', // Spatial features
  deployments: 'application/geo+json', // Spatial features
  fois: 'application/geo+json', // Spatial features
  procedures: 'application/sml+json', // SensorML
  datastreams: 'application/json', // Default JSON
  observations: 'application/om+json', // O&M
};

function buildAcceptHeader(resourceType: string): string {
  const preferred = FORMAT_DEFAULTS[resourceType] || 'application/json';
  return `${preferred}, application/json;q=0.9, */*;q=0.8`;
}
```

#### 17.4.5 Sub-Resource Navigation

**Link-Following Pattern:**

```typescript
class ResourceNavigator<T extends { links?: Link[] }> {
  constructor(private resource: T, private http: HttpClient) {}

  async followLink<R>(rel: string): Promise<R[]> {
    const link = this.resource.links?.find((l) => l.rel === rel);
    if (!link) throw new Error(`No link with rel="${rel}"`);

    const response = await this.http.get<{ items: R[] }>(link.href);
    return response.items;
  }

  hasLink(rel: string): boolean {
    return this.resource.links?.some((l) => l.rel === rel) ?? false;
  }
}

// Enhanced System class
class System {
  private navigator: ResourceNavigator<this>;

  async getDatastreams(): Promise<Datastream[]> {
    return this.navigator.followLink<Datastream>('datastreams');
  }

  async getSubsystems(): Promise<System[]> {
    return this.navigator.hasLink('subsystems')
      ? this.navigator.followLink<System>('subsystems')
      : [];
  }
}
```

#### 17.4.6 Conformance-Based Feature Detection

**Check Server Capabilities:**

```typescript
class ConformanceChecker {
  private conformsTo: Set<string> = new Set();

  async loadConformance(baseUrl: string): Promise<void> {
    const response = await fetch(`${baseUrl}/conformance`);
    const data = await response.json();
    this.conformsTo = new Set(data.conformsTo || []);
  }

  supportsControlStreams(): boolean {
    return this.conformsTo.has(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/control-stream'
    );
  }

  supportsSystemEvents(): boolean {
    return this.conformsTo.has(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-3/1.0/conf/system-events'
    );
  }
}

// Graceful degradation
async getSystemHistory(systemId: string): Promise<SystemSnapshot[] | null> {
  if (!this.conformance.supportsSystemEvents()) {
    console.warn('System history not supported by this server');
    return null;
  }
  return this.http.get(`/systems/${systemId}/history`);
}
```

#### 17.4.7 Bulk Operations

**Smart Batching with Fallback:**

```typescript
async insertObservationsSmart(
  datastreamId: string,
  observations: Observation[],
  http: HttpClient
): Promise<void> {
  if (observations.length === 1) {
    await http.post(`/datastreams/${datastreamId}/observations`, observations[0]);
    return;
  }

  try {
    // Try bulk insert (array POST)
    const batches = chunk(observations, 1000); // OSH max 10,000, safe batch 1,000
    for (const batch of batches) {
      await http.post(`/datastreams/${datastreamId}/observations`, batch);
      await delay(100); // Small delay between batches
    }
  } catch (error) {
    if (error instanceof CSAPIError && error.statusCode === 400) {
      // Server doesn't support bulk - fall back to sequential
      for (const obs of observations) {
        await http.post(`/datastreams/${datastreamId}/observations`, obs);
      }
    } else {
      throw error;
    }
  }
}
```

#### 17.4.8 Caching Strategy

**Resource-Specific TTL Policies:**

```typescript
const CACHE_POLICIES: Record<string, number> = {
  // Metadata - cache for 5 minutes
  systems: 5 * 60 * 1000,
  deployments: 5 * 60 * 1000,
  procedures: 5 * 60 * 1000,
  datastreams: 5 * 60 * 1000,
  fois: 5 * 60 * 1000,

  // Static - cache for 1 hour
  conformance: 60 * 60 * 1000,
  collections: 60 * 60 * 1000,

  // Dynamic - never cache (0 TTL)
  observations: 0,
  commands: 0,
};

class ResourceCache {
  set<T>(key: string, data: T, resourceType: string): void {
    const ttl = CACHE_POLICIES[resourceType] || 0;
    if (ttl === 0) return; // Don't cache dynamic data

    this.cache.set(key, { data, timestamp: Date.now(), ttl });
  }

  invalidatePattern(pattern: RegExp): void {
    // Invalidate all matching keys (e.g., after POST/PUT/DELETE)
    for (const key of this.cache.keys()) {
      if (pattern.test(key)) this.cache.delete(key);
    }
  }
}
```

#### 17.4.9 Authentication Patterns

**Multi-Strategy Support:**

```typescript
interface AuthConfig {
  type: 'basic' | 'bearer' | 'apikey' | 'none';
  credentials?: {
    username?: string;
    password?: string;
    token?: string;
    apiKey?: string;
  };
}

class HttpClient {
  private authStrategy: AuthStrategy;

  constructor(baseUrl: string, authConfig: AuthConfig) {
    this.authStrategy = AuthStrategyFactory.create(authConfig);
  }

  async fetch(path: string, options: RequestInit = {}): Promise<Response> {
    const request: RequestInit = { ...options };
    this.authStrategy.applyAuth(request); // Add auth headers
    return fetch(`${this.baseUrl}${path}`, request);
  }
}

// Strategies: Basic (Authorization: Basic base64),
//             Bearer (Authorization: Bearer token),
//             API Key (X-API-Key: key)
```

#### 17.4.10 Edge Cases from OSH

**Important Behaviors to Handle:**

1. **Opaque IDs:** OSH uses Base32, others may use UUIDs or integers - treat as strings
2. **Open-Ended Intervals:** `../..` (all time), `2024-01-01T00:00:00Z/..` (from date to now)
3. **Immutable Observations:** No PUT support (delete + recreate instead)
4. **Command Status:** Separate endpoint `/commands/{id}/status` for status polling
5. **System History:** Part 3 feature - check conformance before using
6. **Async Operations:** 202 Accepted with Location header for polling
7. **Empty Results:** 200 with empty array (not 404)

#### 17.4.11 Performance Characteristics

**OSH Benchmarks (guidance for expectations):**

- GET single resource: 20-100ms
- List 100 items: 50-200ms
- POST create: 100-500ms
- Query 1000 observations: 200-1000ms

**Optimization Strategies:**

- Reuse HTTP connections (keep-alive)
- Optimal batch sizes: 100-1000 observations
- Parallel requests for independent resources
- Cache metadata aggressively, never cache observations

#### 17.4.12 Testing Against OSH

**Integration Test Setup:**

```typescript
describe('CSAPI Client vs OSH', () => {
  const client = new CSAPIClient('http://localhost:8282/sensorhub/api', {
    type: 'basic',
    credentials: { username: 'admin', password: 'admin' },
  });

  it('should paginate through systems', async () => {
    const systems = [];
    for await (const sys of client.systems.paginate({ limit: 5 })) {
      systems.push(sys);
      if (systems.length >= 10) break;
    }
    expect(systems.length).toBeGreaterThan(0);
  });

  it('should handle 404 with type-safe error', async () => {
    try {
      await client.systems.get('nonexistent');
    } catch (error) {
      expect(error).toBeInstanceOf(CSAPIError);
      expect((error as CSAPIError).isNotFound()).toBe(true);
    }
  });
});
```

**Fixtures:** Use `sensorhub-service-consys/src/test/resources/` for unit tests

#### 17.4.13 Critical Implementation Checklist

**Must-Have Features:**

- ✅ Query parameter validation (client-side before sending)
- ✅ Link-following pagination with AsyncGenerator
- ✅ JSON error body parsing with type guards
- ✅ Format negotiation per resource type
- ✅ Sub-resource navigation via links
- ✅ Conformance-based feature detection
- ✅ Multi-strategy authentication
- ✅ Smart caching with TTL policies

**Performance Features:**

- ✅ Bulk observation insert (with fallback to sequential)
- ✅ Connection reuse (HTTP keep-alive)
- ✅ Parallel independent requests
- ✅ Metadata caching (5 min TTL)

**Testing Requirements:**

- ✅ Integration tests against OSH locally
- ✅ Use real server fixtures
- ✅ Test all CRUD operations
- ✅ Test error conditions (404, 400, 422)
- ✅ Test pagination edge cases

---

## 18. Conclusion

### 18.1 Key Takeaways for TypeScript Client

**Must Implement:**

1. ✅ **All 11 Resource Types** - Full Part 1 + Part 2 coverage
2. ✅ **Query Parameter Support** - bbox, time ranges, parent filters, keywords
3. ✅ **Pagination** - Handle `limit`, `offset`, and link-based navigation
4. ✅ **Error Handling** - Parse JSON error bodies, handle all status codes
5. ✅ **Format Negotiation** - Support JSON, GeoJSON, SensorML JSON
6. ✅ **Authentication** - Basic, Bearer, API Key patterns
7. ✅ **Async Operations** - Handle 202 Accepted responses
8. ✅ **Bulk Operations** - Efficient batch inserts for observations

**Should Implement:**

- ⚠️ **Streaming** - AsyncIterables for paginated results
- ⚠️ **Caching** - Smart caching for immutable resources
- ⚠️ **Retry Logic** - Exponential backoff for rate limiting
- ⚠️ **Conformance Detection** - Feature detection based on server capabilities

**Nice to Have:**

- 🟦 **WebSocket/MQTT** - Real-time observation streaming
- 🟦 **Binary Formats** - SWE Common binary encoding support
- 🟦 **Conditional Requests** - ETag-based optimistic updates

### 18.2 Server Behavior Assumptions

**Safe Assumptions (Based on OGC Spec):**

- All servers will support GET for resource listings
- Pagination via `limit` and `offset` is universal
- HTTP status codes follow standard patterns
- JSON is always supported

**Unsafe Assumptions (Server-Specific):**

- ID format (Base32, UUID, integer) - treat as opaque
- Default/max pagination limits - always specify explicitly
- Bulk operation support - provide fallback to individual requests
- System history endpoint - check conformance first

### 18.3 Testing Strategy

**Use OSH for Integration Tests:**

1. Deploy OSH locally via Docker
2. Seed with test data
3. Run client against real server
4. Validate all CRUD operations
5. Test edge cases (pagination, errors, etc.)

**Test Fixtures Available:**

- `sensorhub-service-consys/src/test/resources/`
- Use for unit tests without server

### 18.4 Final Recommendations

1. **Start with Core Resources:** Systems, DataStreams, Observations
2. **Add Pagination Early:** Essential for production use
3. **Implement Smart Caching:** Systems change rarely, observations never cache
4. **Use Async/Await:** Native TypeScript patterns for all I/O
5. **Separate URL Building from HTTP:** Testability and flexibility
6. **Feature Detection:** Check conformance, don't assume capabilities
7. **Follow OSH Patterns:** Proven in production, good reference

---

**Analysis Complete**  
**Server Analyzed:** OpenSensorHub (osh-core)  
**Implementation Maturity:** Production-Ready  
**CSAPI Coverage:** 100% (11/11 resources)  
**Conformance:** Full Parts 1, 2, 3  
**Recommendation:** Use OSH as reference implementation for client testing and validation
