# CSAPI Part 2: Dynamic Data - Requirements Analysis

**Document:** Requirements Analysis for OGC API – Connected Systems Part 2: Dynamic Data  
**Primary Source:** [OGC API – Connected Systems Part 2: Dynamic Data (OGC 23-002)](https://docs.ogc.org/is/23-002/23-002.html)  
**Date:** 2026-01-31

---

## Table of Contents

1. [Section 2.1: CSAPI Part 2 Standard Document Analysis](#section-21-csapi-part-2-standard-document-analysis)
   1. [Overview](#overview)
   2. [Dynamic Data Resource Types](#dynamic-data-resource-types)
   3. [HTTP Methods for Dynamic Data](#http-methods-for-dynamic-data)
   4. [Canonical Endpoints](#canonical-endpoints)
   5. [Schema Operations](#schema-operations)
   6. [Status and Result Operations](#status-and-result-operations)
   7. [Streaming and Pagination](#streaming-and-pagination)
   8. [Temporal Query Requirements](#temporal-query-requirements)
   9. [Observation-DataStream Relationships](#observation-datastream-relationships)
   10. [Command-ControlStream Relationships](#command-controlstream-relationships)
   11. [Format Options](#format-options)
   12. [Real-Time and Near-Real-Time Requirements](#real-time-and-near-real-time-requirements)
   13. [Conformance Classes](#conformance-classes)
   14. [Examples](#examples)

---

## Section 2.1: CSAPI Part 2 Standard Document Analysis

**Document:** [OGC API – Connected Systems Part 2: Dynamic Data](https://docs.ogc.org/is/23-002/23-002.html)  
**Date:** 2026-01-31  
**Status:** Complete

---

### Overview

CSAPI Part 2 extends Part 1 (Feature Resources) to handle **dynamic data** flowing to and from connected systems. While Part 1 focused on static metadata (Systems, Deployments, Procedures, Sampling Features, Properties), Part 2 defines resources for observations and commands that change over time.

**Key Architectural Principles:**

1. **Observations and Commands Are Not Features:** Deliberate design choice to separate concrete/virtual objects (Features of Interest) from dynamic data containers
2. **Bridge Between Static and Dynamic:** Part 1 Systems connect to Part 2 DataStreams and ControlStreams
3. **Real-Time and Historical:** Resources support both live streaming and historical data access
4. **Multiple Encoding Formats:** JSON, SWE Common JSON, SWE Common Text (CSV), SWE Common Binary for efficient transmission
5. **Pub/Sub Integration:** Part 3 (future) will define pub/sub protocol bindings

**Scope Statement:**
"Part 2 of the API implements the SSN concepts allowing exchange of dynamic (possibly real-time) data flowing to and from various types of connected systems (e.g., sensors, actuators, platforms)."

---

### Dynamic Data Resource Types

Part 2 defines **6 new resource types** for dynamic data:

#### 2.1 DataStream

**Definition:** Collection of Observations acquired by the same System, sharing the same observed properties

**Purpose:**

- Represents data feeds coming out of Systems
- Containers for Observations
- Used for receiving/ingesting real-time Observations
- Accessing historical Observations

**Key Characteristics:**

- Implements `sosa:ObservationCollection` concept
- All observations from same System
- All observations share same observed properties and result schema
- Can provide real-time data only, archived data only, or both

**Required Associations:**

- system (producer System)
- observations (list of Observation resources)

**Optional Associations:**

- procedure (Procedure used to generate observations)
- deployment (Deployment during which datastream generated)
- samplingFeatures (subject Sampling Features)
- featuresOfInterest (ultimate features of interest)

**DataStream Types:**

- `status` - Status observations of parent system or subsystems
- `observation` - Observations of other features of interest (not the system itself)

#### 2.2 Observation

**Definition:** Records all information regarding an act of observation (automated or human)

**Purpose:**

- Carry observation result structured according to defined schema
- Grouped into DataStreams

**Key Characteristics:**

- Implements `sosa:Observation` concept
- Always associated to a DataStream
- Some properties can be omitted (provided at datastream level)
- Can package observation result of several properties in single resource

**Required Attributes:**

- phenomenonTime (DateTime) - When observed property value applies to FOI
- resultTime (DateTime) - When result value obtained
- result (Any) - Observation result with estimated values

**Optional Attributes:**

- parameters (Any) - Information about how procedure used for this observation

**Required Association:**

- datastream (parent DataStream)

**Optional Associations:**

- samplingFeature (subject of observation)
- procedure (used for observation)

#### 2.3 ControlStream

**Definition:** Collection of Commands targeted at the same System, sharing the same controlled properties

**Purpose:**

- Represents data feeds going into Systems
- Containers for Commands
- Used for receiving/ingesting real-time Commands
- Accessing historical Commands

**Key Characteristics:**

- Implements `sosa:ActuationCollection` concept
- All commands received by same System
- All commands share same controlled properties and parameter schema
- Can provide real-time commands only, archived commands only, or both

**Required Associations:**

- system (receiver System)
- commands (list of Command resources)

**Optional Associations:**

- procedure (Procedure used to process commands)
- deployment (Deployment during which control stream active)
- samplingFeatures (subject Sampling Features)
- featuresOfInterest (ultimate features of interest affected)

**ControlStream Types:**

- `self` - Affect parent system or subsystems
- `external` - Affect external features of interest

#### 2.4 Command

**Definition:** Messages sent to System to control parameters of feature of interest

**Purpose:**

- Carry desired values of controlled parameters
- Structured according to defined schema
- Processing can result in actions on several properties at once

**Key Characteristics:**

- Implements generalization of `sosa:Actuation` concept
- Always associated to a ControlStream
- Some properties can be omitted (provided at control stream level)
- Can package desired value of several controlled parameters in single command
- Cancelling a command different from deleting Command resource (status changes to CANCELED)

**Required Attributes:**

- issueTime (DateTime) - When command issued
- executionTime (DateTime) - When command should be executed
- parameters (Any) - Command parameters with desired values

**Required Association:**

- controlstream (parent ControlStream)

**Optional Associations:**

- samplingFeature (feature of interest whose properties changed)
- procedure (used to process command)
- status (list of CommandStatus resources)
- result (list of CommandResult resources)

#### 2.5 CommandStatus

**Definition:** Status reports during execution of a command

**Purpose:**

- Provide progress updates during command execution
- Report success, failure, or intermediate states
- Support both synchronous and asynchronous command processing

**Required Attributes:**

- reportTime (DateTime) - When status reported
- executionTime (DateTime) - Time command executed or will execute
- statusCode (Enum) - Status of command execution
- percentCompletion (Integer 0-100) - Progress percentage
- message (String) - Human-readable status message

**Status Code Values:**

- `PENDING` - Command accepted, waiting for execution
- `ACCEPTED` - Command being processed
- `EXECUTING` - Command currently executing
- `COMPLETED` - Command successfully completed
- `FAILED` - Command failed
- `CANCELED` - Command canceled by user or system

**Required Association:**

- command (parent Command)

#### 2.6 CommandResult

**Definition:** Result of a command execution

**Purpose:**

- Attach data produced by command execution (e.g., data collection tasks, simulation runs)
- Support multiple result types (inline data, datastream references, observation references, external resources)

**Result Types:**

- Reference to one or more datastreams (with optional time range)
- Reference to one or more individual observations
- Reference to observation collection
- Inline result data encoded per control stream result schema

**At Least One Property Required:**

- inline (Any) - Result data inline
- observation (List<Observation>) - Observations resulting from command
- datastream (DataStream) - DataStream containing result observations
- external (Any) - External dataset reference

**Use Case Examples from Standard:**

1. **Chemical Plume Simulation:** Command triggers model run, creates new datastream with time series
2. **UAV Video Footage Task:** Command collects video, appends to existing datastream with time range
3. **UAV Picture Task:** Command collects single image, appends to datastream, returns observation reference
4. **Satellite Imagery Acquisition:** Coverage request creates multiple observations, returns references
5. **System State Retrieval:** Query returns inline state data

**Required Association:**

- command (parent Command)

---

### HTTP Methods for Dynamic Data

Part 2 specifies the same HTTP methods as Part 1 but applied to dynamic data resources:

#### 3.1 GET (Retrieval)

**Supported At:**

- Canonical resources endpoints: `/datastreams`, `/observations`, `/controlstreams`, `/commands`, `/feasibility`, `/systemEvents`
- Canonical resource endpoints: `/datastreams/{id}`, `/observations/{id}`, `/controlstreams/{id}`, `/commands/{id}`, `/feasibility/{id}`, `/systemEvents/{id}`
- Nested resources endpoints: `/systems/{sysId}/datastreams`, `/datastreams/{dsId}/observations`, `/deployments/{depId}/datastreams`, etc.
- Schema endpoints: `/datastreams/{id}/schema?obsFormat={format}`, `/controlstreams/{id}/schema?cmdFormat={format}`
- Status/result endpoints: `/commands/{cmdId}/status`, `/commands/{cmdId}/result`, `/feasibility/{feasId}/status`, `/feasibility/{feasId}/result`

**Parameters Supported:**

- `limit` - Pagination (min 1, max 10000)
- `datetime` - Temporal filter (for resources with validTime property)
- `phenomenonTime` - Temporal filter for DataStreams (filter by observation phenomenon times)
- `resultTime` - Temporal filter for DataStreams and Observations (filter by result times)
- `observedProperty` - Filter DataStreams by observed properties (ID or URI list)
- `foi` - Filter by feature of interest (transitive via sampling features)
- `controlledProperty` - Filter ControlStreams by controlled properties
- `executionTime` - Temporal filter for ControlStreams
- `issueTime` - Temporal filter for ControlStreams and Commands
- `statusCode` - Filter CommandStatus by status code

**Status Codes:**

- 200 (OK) - Successful retrieval
- 400 (Bad Request) - Invalid parameters
- 401 (Unauthorized) - Authentication required
- 403 (Forbidden) - Access denied
- 404 (Not Found) - Resource doesn't exist
- 5XX (Server Error) - Internal server error

#### 3.2 POST (Create)

**Supported At (when Create/Replace/Delete conformance class implemented):**

- DataStream resources endpoints: `/systems/{sysId}/datastreams`
- Observation resources endpoints: `/datastreams/{dsId}/observations`
- ControlStream resources endpoints: `/systems/{sysId}/controlstreams`
- Command resources endpoints: `/controlstreams/{csId}/commands`
- CommandStatus resources endpoints: `/commands/{cmdId}/status`
- CommandResult resources endpoints: `/commands/{cmdId}/result`
- Feasibility resources endpoints: `/controlstreams/{csId}/feasibility`
- SystemEvent resources endpoints: `/systems/{sysId}/events`

**Request Body:**

- Media type: Specified in Content-Type header (application/json, application/swe+json, application/swe+text, application/swe+binary)
- Must conform to schema (DataStream observation schema, ControlStream command schema)

**Response:**

- 201 (Created) - Resource created successfully
- Location header - URL of created resource (canonical URL)
- 400 (Bad Request) - Invalid payload or schema violation
- 409 (Conflict) - Resource already exists or constraint violation

**Schema Validation:**

- Server MUST reject Observation CREATE if result structure incompatible with datastream observation schema
- Server MUST reject Command CREATE if parameter structure incompatible with control stream command schema

#### 3.3 PUT (Replace)

**Supported At (when Create/Replace/Delete conformance class implemented):**

- DataStream resource endpoints: `/systems/{sysId}/datastreams/{id}`, `/datastreams/{id}`
- Observation resource endpoints: `/datastreams/{dsId}/observations/{id}`, `/observations/{id}`
- ControlStream resource endpoints: `/systems/{sysId}/controlstreams/{id}`, `/controlstreams/{id}`
- Command resource endpoints: `/controlstreams/{csId}/commands/{id}`, `/commands/{id}`
- CommandStatus resource endpoints: `/commands/{cmdId}/status/{id}`
- CommandResult resource endpoints: `/commands/{cmdId}/result/{id}`
- Feasibility resource endpoints: `/controlstreams/{csId}/feasibility/{id}`, `/feasibility/{id}`
- SystemEvent resource endpoints: `/systems/{sysId}/events/{id}`, `/systemEvents/{id}`

**Constraints:**

- Server MUST reject REPLACE on DataStream if modifies observation schema and datastream has observations (409 error)
- Server MUST reject REPLACE on ControlStream if modifies command schema and control stream has commands (409 error)

**Response:**

- 204 (No Content) - Resource replaced successfully
- 400 (Bad Request) - Invalid payload
- 404 (Not Found) - Resource doesn't exist
- 409 (Conflict) - Constraint violation (e.g., schema change with existing data)

#### 3.4 PATCH (Update)

**Supported At (when Update conformance class implemented):**

- Same resource endpoints as PUT
- Uses JSON Merge Patch (RFC 7396) format

**Constraints:**

- Same schema constraints as PUT
- Server MUST reject UPDATE on DataStream/ControlStream if modifies schema with existing observations/commands (409 error)

**Response:**

- 204 (No Content) - Resource updated successfully
- 400 (Bad Request) - Invalid patch
- 404 (Not Found) - Resource doesn't exist
- 409 (Conflict) - Constraint violation

**Note:** PATCH method follows OGC API - Features Part 4: Update

#### 3.5 DELETE (Delete)

**Supported At (when Create/Replace/Delete conformance class implemented):**

- Same resource endpoints as PUT

**Cascade Delete:**

- `cascade` parameter (boolean, default false)
- Without cascade: Server MUST reject DELETE on DataStream if has observations (409 error)
- Without cascade: Server MUST reject DELETE on ControlStream if has commands (409 error)
- With cascade=true: Deletes resource AND all nested resources

**Nested Resources Deleted by Cascade:**

- DataStream: All observations
- ControlStream: All commands

**Response:**

- 204 (No Content) - Resource deleted successfully
- 404 (Not Found) - Resource doesn't exist
- 409 (Conflict) - Cascade required but not provided

---

### Canonical Endpoints

Part 2 defines canonical endpoints following Part 1 patterns:

#### 4.1 Canonical Resources Endpoints (Collections)

Expose all resources of a type, support filtering via query parameters:

| Endpoint          | Resource Type | Description              |
| ----------------- | ------------- | ------------------------ |
| `/datastreams`    | DataStream    | All datastreams          |
| `/observations`   | Observation   | All observations         |
| `/controlstreams` | ControlStream | All control streams      |
| `/commands`       | Command       | All commands             |
| `/feasibility`    | Feasibility   | All feasibility requests |
| `/systemEvents`   | SystemEvent   | All system events        |

**Mandatory Parameters:**

- `limit` (integer, 1-10000, default 10) - Pagination
- `datetime` (string) - Temporal filter (ISO 8601 or intervals)

**Optional Parameters (if Advanced Filtering conformance class implemented):**

- Resource-type-specific filters (see Section 8)

#### 4.2 Canonical Resource Endpoints (Single Resource)

Access individual resources by local ID:

| Endpoint               | Resource Type | Description                |
| ---------------------- | ------------- | -------------------------- |
| `/datastreams/{id}`    | DataStream    | Single datastream          |
| `/observations/{id}`   | Observation   | Single observation         |
| `/controlstreams/{id}` | ControlStream | Single control stream      |
| `/commands/{id}`       | Command       | Single command             |
| `/feasibility/{id}`    | Feasibility   | Single feasibility request |
| `/systemEvents/{id}`   | SystemEvent   | Single system event        |

**Canonical URL Requirement:**

- Every resource MUST be accessible via canonical URL
- If retrieved through other URL, response MUST include link to canonical URL with `rel=canonical`

#### 4.3 Nested Resources Endpoints

Resources accessible through parent resource relationships:

**DataStreams nested under Systems:**

- `/systems/{sysId}/datastreams` - All datastreams associated to System
- Exposes ONLY datastreams where system is producer

**DataStreams nested under Deployments:**

- `/deployments/{depId}/datastreams` - All datastreams associated to Deployment
- Exposes ONLY datastreams whose system was deployed during deployment, with validTime intersecting deployment time

**Observations nested under DataStreams:**

- `/datastreams/{dsId}/observations` - All observations in DataStream
- Exposes ONLY observations that are part of parent datastream

**Sampling Features nested under DataStreams:**

- `/datastreams/{dsId}/samplingFeatures` - All sampling features associated to DataStream observations
- Requires Part 1 Sampling Features conformance class

**Features of Interest nested under DataStreams:**

- `/datastreams/{dsId}/featuresOfInterest` - Ultimate features of interest of DataStream observations
- Requires server hosts FOI locally and provides featuresOfInterest association

**ControlStreams nested under Systems:**

- `/systems/{sysId}/controlstreams` - All control streams for System
- Exposes ONLY control streams where system is receiver

**ControlStreams nested under Deployments:**

- `/deployments/{depId}/controlstreams` - All control streams associated to Deployment
- Optional (server provides controlstreams association in Deployment)
- Exposes ONLY control streams whose system was deployed during deployment, with validTime intersecting deployment time

**Commands nested under ControlStreams:**

- `/controlstreams/{csId}/commands` - All commands in ControlStream
- Exposes ONLY commands that are part of parent control stream

**Sampling Features nested under ControlStreams:**

- `/controlstreams/{csId}/samplingFeatures` - All sampling features associated to ControlStream commands
- Requires Part 1 Sampling Features conformance class

**Features of Interest nested under ControlStreams:**

- `/controlstreams/{csId}/featuresOfInterest` - Ultimate features of interest of ControlStream commands
- Requires server hosts FOI locally and provides featuresOfInterest association

**CommandStatus nested under Commands:**

- `/commands/{cmdId}/status` - All status reports for Command
- Exposes ONLY status reports related to parent command

**CommandResult nested under Commands:**

- `/commands/{cmdId}/result` - All result items for Command
- Exposes ONLY results related to parent command
- Only if command can be associated to result

**Feasibility nested under ControlStreams:**

- `/controlstreams/{csId}/feasibility` - All feasibility requests for ControlStream
- Exposes ONLY feasibility requests for parent control stream

**Feasibility Status:**

- `/feasibility/{feasId}/status` - All status reports for Feasibility request

**Feasibility Result:**

- `/feasibility/{feasId}/result` - All result items for Feasibility request

**SystemEvents nested under Systems:**

- `/systems/{sysId}/events` - All system events for System
- Exposes ONLY events related to parent system

---

### Schema Operations

Part 2 provides schema operations for variable-structure resources:

#### 5.1 DataStream Schema Operation

**Purpose:** Different observation schema needed for each datastream (result type and observed properties vary)

**Endpoint:** `/datastreams/{id}/schema`

**Parameter:**

- `obsFormat` (required, string) - Media type of desired observation format
- Examples: `application/json`, `application/swe+csv`, `application/swe+binary`

**Response:**

- 200 (OK) - Single schema corresponding to format
- Schema resource content defined by encoding (not necessarily JSON schema)
- 400 (Bad Request) - Invalid format parameter

**Multiple Formats:**

- Server MAY offer multiple observation formats per datastream
- DataStream resource lists supported formats in `formats` property (List<String>)
- Client requests schema for each format separately
- Server MAY automatically convert observations between formats and generate equivalent schemas

**URL Encoding:**

- Media type must be URL encoded (`+` becomes `%2B`)
- Example: `application/swe+csv` → `application/swe%2Bcsv`

**Example Requests:**

```
GET /datastreams/abc123/schema?obsFormat=application/json
GET /datastreams/abc123/schema?obsFormat=application/swe%2Bcsv
GET /datastreams/abc123/schema?obsFormat=application/swe%2Bbinary
```

**Schema Lifecycle:**

- Schema provided when DataStream created (only one format initially)
- Server can auto-generate schemas for other supported formats
- Schema changes rejected if observations already exist (409 error on PUT/PATCH)
- Workaround: Create new datastream if schema needs to change

#### 5.2 ControlStream Schema Operation

**Purpose:** Different command schema needed for each control stream (controlled properties vary)

**Endpoint:** `/controlstreams/{id}/schema`

**Parameter:**

- `cmdFormat` (required, string) - Media type of desired command format
- Examples: `application/json`, `application/swe+csv`, `application/swe+binary`

**Response:**

- Same as DataStream schema operation

**Multiple Formats:**

- Same pattern as DataStream (server offers multiple formats, client requests specific format)

**URL Encoding:**

- Same as DataStream

**Example Requests:**

```
GET /controlstreams/xyz789/schema?cmdFormat=application/json
GET /controlstreams/xyz789/schema?cmdFormat=application/swe%2Bcsv
GET /controlstreams/xyz789/schema?cmdFormat=application/swe%2Bbinary
```

**Schema Lifecycle:**

- Same constraints as DataStream (schema changes rejected if commands exist)

**Feasibility Channels:**

- Feasibility requests share same parameter schema as corresponding commands
- Both commands and feasibility use schema from parent ControlStream

---

### Status and Result Operations

Part 2 provides specialized operations for command lifecycle management:

#### 6.1 CommandStatus Resources Endpoint

**Purpose:** Retrieve status reports for command execution

**Definition:** Resources endpoint exposing set of CommandStatus resources

**Mandatory Endpoint (nested):**

- `/commands/{cmdId}/status` - Status reports for specific command

**HTTP GET Operation:**

- Supports `limit` and `datetime` parameters (OGC API - Features Part 1 requirements)
- Returns only CommandStatus resources related to parent command

**Response:**

- 200 (OK) - CommandStatus resources selected by request
- Error cases per OGC API - Features Part 1 Clause 7.5.1

**Usage Patterns:**

1. **Polling for Updates:**

```
GET /commands/cmd123/status
// Returns all status reports, client checks latest
```

2. **Filtered by Time:**

```
GET /commands/cmd123/status?datetime=2024-01-15T00:00:00Z/..
// Returns status reports since specific time
```

3. **Pagination:**

```
GET /commands/cmd123/status?limit=10
// Returns up to 10 status reports
```

**Creating Status Reports:**

- POST to `/commands/{cmdId}/status` (when Create/Replace/Delete conformance class implemented)
- Enables both client and server to post status updates
- Command cancellation: POST new status with statusCode=CANCELED (different from DELETE)

#### 6.2 CommandResult Resources Endpoint

**Purpose:** Retrieve result items for command execution

**Definition:** Resources endpoint exposing set of CommandResult resources

**Mandatory Endpoint (nested):**

- `/commands/{cmdId}/result` - Results for specific command
- Only required for commands that can be associated to result

**HTTP GET Operation:**

- Supports `limit` parameter (OGC API - Features Part 1 requirements)
- Returns only CommandResult resources related to parent command

**Response:**

- 200 (OK) - CommandResult resources selected by request
- Error cases per OGC API - Features Part 1 Clause 7.5.1

**Result Types Support:**

1. **Datastream Reference:**

```json
{
  "datastream@link": {
    "href": "https://api.example.org/datastreams/ds456",
    "title": "Plume Simulation Results",
    "type": "application/json"
  },
  "timeRange": "2024-01-15T00:00:00Z/2024-01-15T12:00:00Z"
}
```

2. **Observation Reference:**

```json
{
  "observation@link": {
    "href": "https://api.example.org/observations/obs789",
    "title": "UAV Image",
    "type": "image/jpeg"
  }
}
```

3. **Inline Result:**

```json
{
  "inline": {
    "temperature": 23.5,
    "pressure": 101325,
    "humidity": 65.2
  }
}
```

4. **External Resource:**

```json
{
  "external@link": {
    "href": "https://data.example.org/datasets/sim-run-123",
    "title": "Full Simulation Output",
    "type": "application/netcdf"
  }
}
```

**Synchronous vs Asynchronous:**

- Synchronous commands: Result can be provided in HTTP response
- Asynchronous commands: Client polls result endpoint or uses pub/sub (Part 3)

#### 6.3 Command Feasibility

**Purpose:** Check if command/task feasible without sending actual command

**Feasibility Channel:**

- Created at `/controlstreams/{csId}/feasibility`
- Uses same parameter schema as corresponding commands
- Responds synchronously or asynchronously like regular commands

**Response Types:**

1. **Binary (YES/NO):**

```json
{
  "feasible": true,
  "message": "Task can be scheduled"
}
```

2. **Detailed Analysis:**

```json
{
  "feasible": true,
  "successProbability": 0.85,
  "executionSteps": [
    { "step": 1, "action": "Orient sensor", "duration": "PT5S" },
    { "step": 2, "action": "Capture image", "duration": "PT1S" }
  ],
  "alternatives": [{ "taskId": "alt1", "probability": 0.92, "delay": "PT30M" }]
}
```

**Feasibility Status and Result:**

- Follows same pattern as Command
- `/feasibility/{feasId}/status` - Status reports
- `/feasibility/{feasId}/result` - Feasibility analysis results

**Use Cases:**

- Check availability before tasking UAV
- Validate command parameters before submission
- Evaluate scheduling conflicts
- Provide cost/risk estimates

---

### Streaming and Pagination

Part 2 supports efficient data streaming and pagination for large result sets:

#### 7.1 Pagination Parameters

**limit Parameter:**

- Type: integer
- Range: 1 to 10000
- Default: 10 (if not specified)
- Inherited from OGC API - Features Part 1 Clause 7.15.2
- Applies to all resources endpoints (DataStreams, Observations, ControlStreams, Commands, etc.)

**Usage:**

```
GET /observations?limit=100
// Returns up to 100 observations
```

**Pagination Links:**

- Response includes `next` link for next page
- Client follows links to retrieve all pages
- Cursor-based pagination (implementation-specific)

**Example Response:**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 100 observations */
  ],
  "links": [
    {
      "rel": "next",
      "href": "https://api.example.org/observations?limit=100&cursor=abc123",
      "type": "application/json"
    }
  ]
}
```

#### 7.2 Temporal Windowing

**datetime Parameter:**

- Type: string (ISO 8601)
- Formats: Single instant, closed interval, open interval
- Inherited from OGC API - Features Part 1 Clause 7.15.4

**Single Instant:**

```
GET /datastreams?datetime=2024-01-15T12:00:00Z
// DataStreams with validTime intersecting instant
```

**Closed Interval:**

```
GET /observations?datetime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// Observations with phenomenonTime intersecting interval
```

**Open Start:**

```
GET /observations?datetime=../2024-01-16T00:00:00Z
// Observations with phenomenonTime before end time
```

**Open End:**

```
GET /observations?datetime=2024-01-15T00:00:00Z/..
// Observations with phenomenonTime after start time
```

**Special Value - latest:**

```
GET /observations?resultTime=latest
// Only observations with latest resultTime
```

**Resource-Specific Temporal Filters:**

- `datetime` - Applies to validTime (DataStreams, ControlStreams)
- `phenomenonTime` - Applies to phenomenonTime (DataStreams filter by obs phenomenon times)
- `resultTime` - Applies to resultTime (DataStreams, Observations)
- `executionTime` - Applies to executionTime (ControlStreams)
- `issueTime` - Applies to issueTime (ControlStreams, Commands)

#### 7.3 Streaming Patterns

**Live Data Access:**

- DataStream `live` property (boolean) indicates if live data available
- ControlStream `live` property (boolean) indicates if currently accepts commands

**Pattern 1: Polling Latest:**

```
// Poll every 5 seconds for new observations
GET /datastreams/ds123/observations?resultTime=latest
```

**Pattern 2: Incremental Fetch:**

```
// First request
GET /datastreams/ds123/observations?resultTime=2024-01-15T00:00:00Z/..&limit=1000

// Subsequent requests using last observation resultTime
GET /datastreams/ds123/observations?resultTime=2024-01-15T12:34:56Z/..&limit=1000
```

**Pattern 3: Time-Windowed Pagination:**

```
// Day 1
GET /observations?datetime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z&limit=10000

// Day 2
GET /observations?datetime=2024-01-16T00:00:00Z/2024-01-17T00:00:00Z&limit=10000
```

**Pattern 4: Pub/Sub (Part 3):**

- For true real-time streaming
- Avoids polling overhead
- WebSocket, MQTT, or other pub/sub protocols
- Part 3 specification (future)

#### 7.4 Efficient Encodings

**SWE Common Binary:**

- Most compact format
- ~10-100x smaller than JSON for time series
- Requires schema parsing
- Best for high-frequency sensor data

**SWE Common Text (CSV):**

- Human-readable
- ~2-5x smaller than JSON
- Easy integration with spreadsheets/analysis tools
- Good for moderate-frequency data

**SWE Common JSON:**

- Structured like JSON
- More compact than plain JSON
- Preserves SWE Common data component structure
- Good balance of efficiency and readability

**Format Selection:**

```
GET /datastreams/ds123/observations
Accept: application/swe+binary
// Server returns observations in binary format
```

---

### Temporal Query Requirements

Part 2 extends temporal query capabilities from Part 1:

#### 8.1 phenomenonTime Filter (Advanced Filtering)

**Applies To:** DataStreams, Observations

**Purpose:** Filter by time the observed property value applies to feature of interest

**DataStream Filtering:**

```
GET /datastreams?phenomenonTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// Returns datastreams whose phenomenonTime property intersects interval
```

**Observation Filtering:**

```
GET /observations?phenomenonTime=2024-01-15T12:00:00Z
// Returns observations whose phenomenonTime equals or intersects instant
```

**Nested Endpoint:**

```
GET /datastreams/ds123/observations?phenomenonTime=2024-01-15T00:00:00Z/..
// Returns observations in ds123 with phenomenonTime after start
```

**DataStream phenomenonTime Property:**

- Automatically generated by server
- Spans phenomenon times of all observations in datastream
- Set to null if no observations

**Observation phenomenonTime Property:**

- Required attribute
- DateTime type
- When observed property value applies to FOI

#### 8.2 resultTime Filter (Advanced Filtering)

**Applies To:** DataStreams, Observations

**Purpose:** Filter by time the result value was obtained

**DataStream Filtering:**

```
GET /datastreams?resultTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// Returns datastreams whose resultTime property intersects interval
```

**Observation Filtering:**

```
GET /observations?resultTime=latest
// Returns observations with latest resultTime (special value)
```

**Nested Endpoint:**

```
GET /datastreams/ds123/observations?resultTime=2024-01-15T12:00:00Z/..
// Returns observations in ds123 with resultTime after start
```

**Special Value - latest:**

- Only for Observation filtering
- Returns observations with most recent resultTime
- Useful for real-time monitoring dashboards

**DataStream resultTime Property:**

- Automatically generated by server
- Spans result times of all observations in datastream
- Set to null if no observations

**Observation resultTime Property:**

- Required attribute
- DateTime type
- When result value obtained (may differ from phenomenonTime)

#### 8.3 executionTime Filter (Advanced Filtering)

**Applies To:** ControlStreams

**Purpose:** Filter by time commands should be or were executed

**ControlStream Filtering:**

```
GET /controlstreams?executionTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// Returns control streams whose executionTime property intersects interval
```

**ControlStream executionTime Property:**

- Automatically generated by server
- Spans execution times of all commands in control stream
- Set to null if no commands

**Command executionTime Property:**

- Required attribute
- DateTime type
- When command should be executed

#### 8.4 issueTime Filter (Advanced Filtering)

**Applies To:** ControlStreams

**Purpose:** Filter by time commands were issued

**ControlStream Filtering:**

```
GET /controlstreams?issueTime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// Returns control streams whose issueTime property intersects interval
```

**ControlStream issueTime Property:**

- Automatically generated by server
- Spans issue times of all commands in control stream
- Set to null if no commands

**Command issueTime Property:**

- Required attribute
- DateTime type
- When command issued

#### 8.5 validTime Filter (Part 1 Inheritance)

**Applies To:** DataStreams, ControlStreams (resources with validTime property)

**Purpose:** Filter by validity period of resource description

**Usage:**

```
GET /datastreams?datetime=2024-01-15T00:00:00Z/2024-01-16T00:00:00Z
// Returns datastreams with validTime intersecting interval
```

**Note:** `datetime` parameter applies to validTime per OGC API - Features Part 1

**DataStream validTime Property:**

- Optional attribute
- TimeExtent type
- Validity period of datastream's description

**ControlStream validTime Property:**

- Optional attribute
- TimeExtent type
- Validity period of control stream's description

---

### Observation-DataStream Relationships

Part 2 defines tight coupling between Observations and DataStreams:

#### 9.1 Containment Relationship

**DataStream as Container:**

- DataStream implements `sosa:ObservationCollection` concept
- Observations MUST be part of exactly one DataStream
- Observations accessed through parent DataStream

**Required Association:**

```json
{
  "type": "Observation",
  "datastream@id": "ds123",
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": 23.5
}
```

**Canonical vs Nested Access:**

- Canonical: `/observations/{id}` - Direct access by observation ID
- Nested: `/datastreams/{dsId}/observations` - Access via parent datastream
- Both return same Observation resource (with canonical link)

#### 9.2 Schema Inheritance

**Observation Schema from DataStream:**

- DataStream defines observation schema for all contained observations
- Observation result MUST conform to DataStream resultSchema
- Observation parameters (if any) MUST conform to DataStream parametersSchema

**Schema Properties in DataStream:**

```json
{
  "type": "DataStream",
  "resultSchema": {
    /* JSON Schema or SWE Common DataComponent */
  },
  "parametersSchema": {
    /* JSON Schema or SWE Common DataComponent */
  }
}
```

**Validation:**

- Server MUST reject Observation CREATE/REPLACE if result invalid per schema (400 error)
- Server MUST reject Observation UPDATE if modifies result to be invalid per schema (400 error)

**Schema Evolution:**

- DataStream schema changes rejected if observations exist (409 error)
- Workaround: Create new DataStream with new schema

#### 9.3 Property Inheritance

**Properties Provided at DataStream Level:**

- observedProperties (List<URI>) - Properties for which observations provide measurements
- resultType (Enum) - Type of result (measure, vector, record, coverage, complex)
- system (System) - Producer of datastream
- procedure (Procedure) - Used to generate observations
- deployment (Deployment) - During which datastream generated
- samplingFeatures (List<SamplingFeature>) - Subject sampling features
- featuresOfInterest (List<Feature>) - Ultimate features of interest

**Properties Omitted from Observation:**

- Observation doesn't repeat system, observedProperties (from parent DataStream)
- Reduces payload size for large observation collections

**Properties Specific to Each Observation:**

- phenomenonTime (DateTime) - When observed property value applies
- resultTime (DateTime) - When result obtained
- result (Any) - Observation result
- parameters (Any) - Observation-specific parameters (optional)
- samplingFeature (SamplingFeature) - Subject of observation (optional, can differ per observation)
- procedure (Procedure) - Used for observation (optional, can override DataStream procedure)

#### 9.4 Aggregation Properties

**DataStream Aggregates Observation Properties:**

- phenomenonTime (TimeExtent) - Spans all observation phenomenon times
- resultTime (TimeExtent) - Spans all observation result times
- observedProperties (List<URI>) - All observed properties in observations
- resultType (Enum) - Common result type for all observations

**Auto-Generated by Server:**

- Server automatically updates these properties based on contained observations
- Set to null if no observations
- Server MAY ignore client updates to these properties (they're derived)

**Example:**

```json
{
  "type": "DataStream",
  "phenomenonTime": "2024-01-15T00:00:00Z/2024-01-16T00:00:00Z",
  "resultTime": "2024-01-15T00:00:01Z/2024-01-16T00:00:01Z",
  "observedProperties": ["http://example.org/properties/temperature"],
  "resultType": "measure"
}
```

#### 9.5 Live Data Indicator

**live Property (Boolean):**

- Indicates whether live data available from datastream
- Required attribute
- Server MAY auto-generate and ignore updates

**Use Cases:**

- `live=true` - DataStream provides real-time observations (polling or pub/sub)
- `live=false` - DataStream contains only historical observations
- `live=true` + archived data - DataStream provides both real-time and historical

**Client Behavior:**

- Check `live` before polling or subscribing
- Use polling/pub/sub patterns if `live=true`
- Use batch queries if `live=false`

#### 9.6 Nested Resources Access

**Sampling Features from DataStream:**

```
GET /datastreams/ds123/samplingFeatures
// Returns sampling features associated to observations in ds123
```

**Requirements:**

- Server implements Part 1 Sampling Features conformance class
- Endpoint exposes ONLY sampling features associated to observations in parent datastream

**Features of Interest from DataStream:**

```
GET /datastreams/ds123/featuresOfInterest
// Returns ultimate features of interest of observations in ds123
```

**Requirements:**

- Server provides featuresOfInterest association in DataStream
- Server hosts FOI descriptions locally
- Endpoint exposes ONLY features that are ultimate FOI of observations in parent datastream

---

### Command-ControlStream Relationships

Part 2 defines parallel structure for Commands and ControlStreams (mirrors Observation-DataStream):

#### 10.1 Containment Relationship

**ControlStream as Container:**

- ControlStream implements `sosa:ActuationCollection` concept
- Commands MUST be part of exactly one ControlStream
- Commands accessed through parent ControlStream

**Required Association:**

```json
{
  "type": "Command",
  "controlstream@id": "cs456",
  "issueTime": "2024-01-15T12:00:00Z",
  "executionTime": "2024-01-15T12:01:00Z",
  "parameters": {
    "pan": 45.0,
    "tilt": 30.0,
    "zoom": 2.5
  }
}
```

**Canonical vs Nested Access:**

- Canonical: `/commands/{id}` - Direct access by command ID
- Nested: `/controlstreams/{csId}/commands` - Access via parent control stream
- Both return same Command resource (with canonical link)

#### 10.2 Schema Inheritance

**Command Schema from ControlStream:**

- ControlStream defines command schema for all contained commands
- Command parameters MUST conform to ControlStream parametersSchema

**Schema Properties in ControlStream:**

```json
{
  "type": "ControlStream",
  "parametersSchema": {
    /* JSON Schema or SWE Common DataComponent */
  }
}
```

**Validation:**

- Server MUST reject Command CREATE/REPLACE if parameters invalid per schema (400 error)
- Server MUST reject Command UPDATE if modifies parameters to be invalid per schema (400 error)

**Schema Evolution:**

- ControlStream schema changes rejected if commands exist (409 error)
- Workaround: Create new ControlStream with new schema

#### 10.3 Property Inheritance

**Properties Provided at ControlStream Level:**

- controlledProperties (List<URI>) - Properties whose value can be changed by commands
- system (System) - Receiver of control stream
- procedure (Procedure) - Used to process commands
- deployment (Deployment) - During which control stream active
- samplingFeatures (List<SamplingFeature>) - Subject sampling features
- featuresOfInterest (List<Feature>) - Ultimate features of interest affected

**Properties Omitted from Command:**

- Command doesn't repeat system, controlledProperties (from parent ControlStream)
- Reduces payload size for large command collections

**Properties Specific to Each Command:**

- issueTime (DateTime) - When command issued
- executionTime (DateTime) - When command should execute
- parameters (Any) - Command parameters
- samplingFeature (SamplingFeature) - FOI whose properties changed (optional, can differ per command)
- procedure (Procedure) - Used to process command (optional, can override ControlStream procedure)
- status (List<CommandStatus>) - Status reports
- result (List<CommandResult>) - Result items

#### 10.4 Aggregation Properties

**ControlStream Aggregates Command Properties:**

- issueTime (TimeExtent) - Spans all command issue times
- executionTime (TimeExtent) - Spans all command execution times
- controlledProperties (List<URI>) - All controlled properties in commands

**Auto-Generated by Server:**

- Server automatically updates these properties based on contained commands
- Set to null if no commands
- Server MAY ignore client updates to these properties (they're derived)

**Example:**

```json
{
  "type": "ControlStream",
  "issueTime": "2024-01-15T00:00:00Z/2024-01-16T00:00:00Z",
  "executionTime": "2024-01-15T00:01:00Z/2024-01-16T00:01:00Z",
  "controlledProperties": [
    "http://example.org/properties/pan",
    "http://example.org/properties/tilt",
    "http://example.org/properties/zoom"
  ]
}
```

#### 10.5 Live and Async Indicators

**live Property (Boolean):**

- Indicates whether control stream currently accepts commands
- Required attribute
- `live=true` - System available to receive commands
- `live=false` - System unavailable or control stream archived only

**async Property (Boolean):**

- Indicates whether commands processed asynchronously
- Required attribute
- `async=true` - Commands processed asynchronously (status reports via polling or pub/sub)
- `async=false` - Commands processed synchronously (result in HTTP response)

**Client Behavior:**

- Check `live` before sending commands
- If `async=true`, poll `/commands/{cmdId}/status` or subscribe (Part 3)
- If `async=false`, expect result in immediate HTTP response

#### 10.6 Command Lifecycle

**State Transitions:**

```
PENDING → ACCEPTED → EXECUTING → COMPLETED
                               → FAILED
           ↘ CANCELED
```

**Status Codes:**

- `PENDING` - Command accepted, waiting for execution
- `ACCEPTED` - Command being processed
- `EXECUTING` - Command currently executing
- `COMPLETED` - Successfully completed
- `FAILED` - Failed (see message for reason)
- `CANCELED` - Canceled by user or system

**Reporting Status:**

- POST new status to `/commands/{cmdId}/status`
- Both client and server can post updates
- Cancellation: POST status with statusCode=CANCELED (not DELETE command)

**Retrieving Status:**

- GET from `/commands/{cmdId}/status`
- Poll for updates if `async=true`
- Check percentCompletion for progress

#### 10.7 Command Results

**When Results Generated:**

- Commands that trigger data collection (UAV imagery, sensor sampling)
- Commands that run simulations (plume modeling, forecasts)
- Commands that query system state

**Result Attachment:**

- POST result to `/commands/{cmdId}/result`
- Multiple results per command possible (e.g., each model timestep)

**Result Retrieval:**

- GET from `/commands/{cmdId}/result`
- Provides datastream references, observation references, inline data, or external resources

#### 10.8 Nested Resources Access

**Sampling Features from ControlStream:**

```
GET /controlstreams/cs456/samplingFeatures
// Returns sampling features associated to commands in cs456
```

**Requirements:**

- Server implements Part 1 Sampling Features conformance class
- Endpoint exposes ONLY sampling features associated to commands in parent control stream

**Features of Interest from ControlStream:**

```
GET /controlstreams/cs456/featuresOfInterest
// Returns ultimate features of interest of commands in cs456
```

**Requirements:**

- Server provides featuresOfInterest association in ControlStream
- Server hosts FOI descriptions locally
- Endpoint exposes ONLY features that are ultimate FOI of commands in parent control stream

---

### Format Options

Part 2 supports multiple encoding formats for observations and commands:

#### 11.1 JSON Encoding

**Media Type:** `application/json`

**Supported For:**

- All resource types (DataStreams, Observations, ControlStreams, Commands, CommandStatus, CommandResult, SystemEvents)
- DataStream/ControlStream representations
- Observation/Command schemas

**Characteristics:**

- Human-readable
- Easy to parse with standard JSON libraries
- Verbose (larger payload sizes)
- Good for small datasets and interactive debugging

**Example DataStream:**

```json
{
  "type": "DataStream",
  "id": "ds123",
  "name": "Temperature Sensor Data",
  "observedProperties": ["http://example.org/properties/temperature"],
  "resultType": "measure",
  "live": true,
  "formats": ["application/json", "application/swe+json"]
}
```

**Example Observation:**

```json
{
  "type": "Observation",
  "id": "obs456",
  "datastream@id": "ds123",
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": 23.5
}
```

**Mandatory Support:**

- All servers MUST support JSON encoding for retrieval (GET)
- Servers implementing Create/Replace/Delete MUST advertise JSON support for transactional operations

#### 11.2 SWE Common JSON Encoding

**Media Type:** `application/swe+json`

**Supported For:**

- Observations
- Commands
- Observation schemas
- Command schemas

**Characteristics:**

- Structured according to SWE Common Data Model 3.0
- More compact than plain JSON
- Preserves SWE Common data component structure
- Machine-readable with SWE Common parsers

**Example Observation Schema:**

```json
{
  "type": "DataRecord",
  "fields": [
    {
      "name": "phenomenonTime",
      "type": "Time",
      "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
      "uom": { "code": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian" }
    },
    {
      "name": "result",
      "type": "Quantity",
      "definition": "http://example.org/properties/temperature",
      "uom": { "code": "Cel" }
    }
  ],
  "encoding": {
    "type": "JSONEncoding"
  }
}
```

**Example Observation:**

```json
{
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "result": 23.5
}
```

**Optional Support:**

- Servers MAY support SWE Common JSON encoding
- If supported, MUST be advertised in DataStream/ControlStream `formats` property

#### 11.3 SWE Common Text Encoding (CSV/DSV)

**Media Type:** `application/swe+text`

**Supported For:**

- Observations
- Commands

**Characteristics:**

- Delimiter-separated values (CSV with custom delimiters)
- Human-readable
- ~2-5x more compact than JSON
- Easy integration with spreadsheets and analysis tools
- Requires schema for parsing

**Example Observation Schema:**

```json
{
  "type": "DataRecord",
  "fields": [
    { "name": "phenomenonTime", "type": "Time" },
    { "name": "result", "type": "Quantity" }
  ],
  "encoding": {
    "type": "TextEncoding",
    "tokenSeparator": ",",
    "blockSeparator": "\n",
    "decimalSeparator": "."
  }
}
```

**Example Observations:**

```
2024-01-15T12:00:00Z,23.5
2024-01-15T12:01:00Z,23.6
2024-01-15T12:02:00Z,23.4
```

**Optional Support:**

- Servers MAY support SWE Common Text encoding
- If supported, MUST be advertised in DataStream/ControlStream `formats` property

#### 11.4 SWE Common Binary Encoding

**Media Type:** `application/swe+binary`

**Supported For:**

- Observations
- Commands

**Characteristics:**

- Binary encoding according to SWE Common specification
- Most compact (~10-100x smaller than JSON for time series)
- Requires schema for parsing
- Best for high-frequency sensor data
- Not human-readable

**Example Observation Schema:**

```json
{
  "type": "DataRecord",
  "fields": [
    { "name": "phenomenonTime", "type": "Time" },
    { "name": "result", "type": "Quantity" }
  ],
  "encoding": {
    "type": "BinaryEncoding",
    "byteOrder": "BIG_ENDIAN",
    "byteEncoding": "BASE64",
    "members": [
      { "component": "phenomenonTime", "dataType": "DOUBLE" },
      { "component": "result", "dataType": "FLOAT" }
    ]
  }
}
```

**Example Observations (Base64-encoded binary):**

```
QdZeP4AAAABBuZmZmUHWXkAAAAABQbmZmaVB1l5BAAAAQbpmZpk=
```

**Optional Support:**

- Servers MAY support SWE Common Binary encoding
- If supported, MUST be advertised in DataStream/ControlStream `formats` property

#### 11.5 Format Negotiation

**Content Negotiation via Accept Header:**

```
GET /datastreams/ds123/observations
Accept: application/swe+binary
```

**Format Parameter:**

```
GET /datastreams/ds123/observations?f=application/swe+binary
```

**Schema Query:**

```
GET /datastreams/ds123/schema?obsFormat=application/swe+binary
```

**Multiple Format Support:**

- Server lists supported formats in DataStream/ControlStream `formats` property
- Client selects appropriate format based on use case
- Server MAY automatically convert between formats

**Format Selection Guidance:**

- **JSON** - Interactive debugging, small datasets, human review
- **SWE Common JSON** - Structured data with SWE Common tooling
- **SWE Common Text** - Spreadsheet import, moderate-frequency data, human readability
- **SWE Common Binary** - High-frequency sensor data, bandwidth-constrained environments, archival storage

---

### Real-Time and Near-Real-Time Requirements

Part 2 supports real-time data delivery through multiple mechanisms:

#### 12.1 Live Data Indicators

**DataStream live Property:**

- Boolean flag indicating real-time data availability
- `live=true` - DataStream provides real-time observations
- `live=false` - Historical data only

**ControlStream live Property:**

- Boolean flag indicating command acceptance status
- `live=true` - System currently accepts commands
- `live=false` - System unavailable or archived control stream

**Server Responsibilities:**

- Update `live` flag when system availability changes
- Server MAY auto-generate and ignore client updates

**Client Responsibilities:**

- Check `live` before attempting real-time operations
- Handle `live=false` gracefully (use historical data or retry later)

#### 12.2 Polling Patterns

**Latest Data Polling:**

```
// Poll every N seconds
GET /datastreams/ds123/observations?resultTime=latest
```

**Incremental Polling:**

```
// First poll
GET /datastreams/ds123/observations?resultTime=2024-01-15T12:00:00Z/..&limit=1000

// Subsequent polls using last resultTime
GET /datastreams/ds123/observations?resultTime=2024-01-15T12:05:23Z/..&limit=1000
```

**Polling Frequency Considerations:**

- Check DataStream metadata for expected update frequency
- Balance between latency and server load
- Use limit parameter to control result set size
- Consider server rate limiting

#### 12.3 Asynchronous Command Processing

**async Property:**

- Boolean flag in ControlStream
- `async=true` - Commands processed asynchronously with status updates
- `async=false` - Commands processed synchronously with immediate response

**Asynchronous Workflow:**

```
1. POST command to /controlstreams/cs456/commands
   → 201 Created, Location: /commands/cmd789

2. Poll status endpoint
   GET /commands/cmd789/status
   → Returns status reports (PENDING → ACCEPTED → EXECUTING → COMPLETED)

3. Retrieve result (if applicable)
   GET /commands/cmd789/result
   → Returns CommandResult resources
```

**Synchronous Workflow:**

```
1. POST command to /controlstreams/cs456/commands
   → 200 OK with command result in response body
```

**Status Polling:**

- Poll `/commands/{cmdId}/status` periodically
- Check `percentCompletion` for progress
- Check `statusCode` for terminal states (COMPLETED, FAILED, CANCELED)

#### 12.4 Pub/Sub Integration (Part 3)

**Future Specification:**

- Part 3 will define pub/sub protocol bindings
- Alternatives to HTTP polling
- Lower latency, reduced server load

**Anticipated Protocols:**

- WebSocket
- MQTT
- Server-Sent Events (SSE)
- gRPC streaming

**Current Status:**

- Part 2 defines HTTP-based interfaces only
- Part 3 not yet published
- Servers MAY implement proprietary pub/sub until Part 3 available

**Benefits of Pub/Sub:**

- Push-based updates (no polling)
- Lower latency (<1 second vs 5-10 second polling)
- Reduced bandwidth (only changed data sent)
- Better scaling for many concurrent clients

#### 12.5 Real-Time Use Cases

**Sensor Monitoring Dashboard:**

- Poll latest observations every 5 seconds
- Display real-time charts
- Alert on threshold violations

**UAV Control:**

- Send commands asynchronously
- Poll status for execution confirmation
- Display telemetry from datastreams

**Weather Forecast Model:**

- Trigger model run via command
- Poll status for progress updates
- Retrieve result datastream when complete

**Industrial Process Control:**

- Send control commands to actuators
- Monitor sensor datastreams for feedback
- Implement closed-loop control algorithms

**Emergency Response:**

- Monitor multiple sensor datastreams
- Detect anomalies in real-time
- Dispatch commands to response systems

---

### Conformance Classes

Part 2 defines **8 requirements classes** and corresponding conformance classes:

#### 13.1 Conformance Class A.1: Common

**Identifier:** `/conf/api-common`  
**Requirements Class:** `/req/api-common`  
**Prerequisite:** OGC API - Features Part 1: Core  
**Target Type:** Web API

**Purpose:** Requirements shared by several other requirements classes

**Key Requirements:**

- Non-feature resources (Observations, Commands, etc. are not Features)
- Resource collections (grouping resources with `itemType` property)

**Note:** This conformance class is prerequisite for all Part 2 conformance classes

#### 13.2 Conformance Class A.2: Datastreams & Observations

**Identifier:** `/conf/datastream`  
**Requirements Class:** `/req/datastream`  
**Prerequisite:** Conformance class A.1: `/conf/api-common`  
**Target Type:** Web API

**Resources Defined:**

- DataStream resources
- Observation resources

**Endpoints Required:**

- Canonical: `/datastreams`, `/datastreams/{id}`
- Canonical: `/observations`, `/observations/{id}`
- Nested: `/systems/{sysId}/datastreams`
- Nested: `/deployments/{depId}/datastreams`
- Nested: `/datastreams/{dsId}/observations`
- Schema: `/datastreams/{id}/schema?obsFormat={format}`
- Optional nested: `/datastreams/{dsId}/samplingFeatures`, `/datastreams/{dsId}/featuresOfInterest`

**Collections Support:**

- Collections with `itemType=DataStream`
- Collections with `itemType=Observation`

**Key Requirements (16 total):**

- Requirement 3-4: Sampling features / FOI references from datastream
- Requirement 5: DataStream canonical URL
- Requirement 6-7: DataStream resources endpoints
- Requirement 8-9: DataStream references from System/Deployment
- Requirement 10: DataStream collections
- Requirement 11: DataStream schema operation
- Requirement 12: Observation canonical URL
- Requirement 13-14: Observation resources endpoints
- Requirement 15: Observation references from DataStream
- Requirement 16: Observation collections

**Mandatory:** Minimum server MUST implement this OR ControlStreams & Commands conformance class

#### 13.3 Conformance Class A.3: Control Streams & Commands

**Identifier:** `/conf/controlstream`  
**Requirements Class:** `/req/controlstream`  
**Prerequisite:** Conformance class A.1: `/conf/api-common`  
**Target Type:** Web API

**Resources Defined:**

- ControlStream resources
- Command resources
- CommandStatus resources
- CommandResult resources

**Endpoints Required:**

- Canonical: `/controlstreams`, `/controlstreams/{id}`
- Canonical: `/commands`, `/commands/{id}`
- Nested: `/systems/{sysId}/controlstreams`
- Nested: `/deployments/{depId}/controlstreams` (optional)
- Nested: `/controlstreams/{csId}/commands`
- Nested: `/commands/{cmdId}/status`
- Nested: `/commands/{cmdId}/result`
- Schema: `/controlstreams/{id}/schema?cmdFormat={format}`
- Optional nested: `/controlstreams/{csId}/samplingFeatures`, `/controlstreams/{csId}/featuresOfInterest`

**Collections Support:**

- Collections with `itemType=ControlStream`
- Collections with `itemType=Command`

**Key Requirements (18 total):**

- Requirement 17-18: Sampling features / FOI references from control stream
- Requirement 19: ControlStream canonical URL
- Requirement 20-21: ControlStream resources endpoints
- Requirement 22-23: ControlStream references from System/Deployment
- Requirement 24: ControlStream collections
- Requirement 25: ControlStream schema operation
- Requirement 26: Command canonical URL
- Requirement 27-28: Command resources endpoints
- Requirement 29: Command references from ControlStream
- Requirement 30: Command collections
- Requirement 31-32: CommandStatus endpoints
- Requirement 33-34: CommandResult endpoints

**Mandatory:** Minimum server MUST implement this OR Datastreams & Observations conformance class

#### 13.4 Conformance Class A.4: Command Feasibility

**Identifier:** `/conf/feasibility`  
**Requirements Class:** `/req/feasibility`  
**Prerequisite:** Conformance class A.3: `/conf/controlstream`  
**Target Type:** Web API

**Resources Defined:**

- Feasibility resources (reuses Command structure)
- Status resources (reuses CommandStatus structure)
- Result resources (reuses CommandResult structure)

**Endpoints Required:**

- Canonical: `/feasibility`, `/feasibility/{id}`
- Nested: `/controlstreams/{csId}/feasibility`
- Nested: `/feasibility/{feasId}/status`
- Nested: `/feasibility/{feasId}/result`

**Collections Support:**

- Collections with `itemType=Feasibility`

**Key Requirements (5 total):**

- Requirement 35: Feasibility canonical URL
- Requirement 36: Feasibility references from ControlStream
- Requirement 37: Feasibility status endpoint
- Requirement 38: Feasibility result endpoint
- Requirement 39: Feasibility collections

**Optional:** Servers MAY implement feasibility channels

#### 13.5 Conformance Class A.5: System Events

**Identifier:** `/conf/system-event`  
**Requirements Class:** `/req/system-event`  
**Prerequisite:** Conformance class A.1: `/conf/api-common`, Part 1 System conformance class  
**Target Type:** Web API

**Resources Defined:**

- SystemEvent resources

**Event Types:**

- Sensor activation
- Recalibration
- Maintenance
- Configuration changes
- Other system events

**Endpoints Required:**

- Canonical: `/systemEvents`, `/systemEvents/{id}`
- Nested: `/systems/{sysId}/events`

**Collections Support:**

- Collections with `itemType=SystemEvent`

**Key Requirements (4 total):**

- Requirement 40: SystemEvent canonical URL
- Requirement 41: SystemEvent resources endpoints
- Requirement 42: Canonical SystemEvent resources endpoint
- Requirement 43: SystemEvent references from System
- Requirement 44: SystemEvent collections

**Optional:** Servers MAY implement system events

#### 13.6 Conformance Class A.6: Advanced Filtering

**Identifier:** `/conf/advanced-filtering`  
**Requirements Class:** `/req/advanced-filtering`  
**Prerequisite:** Part 1 Advanced Filtering conformance class  
**Target Type:** Web API

**Additional Query Parameters:**

**For DataStreams:**

- `phenomenonTime` - Filter by observation phenomenon times
- `resultTime` - Filter by observation result times
- `observedProperty` - Filter by observed properties (ID or URI list)
- `foi` - Filter by feature of interest (transitive)

**For Observations:**

- `phenomenonTime` - Filter by phenomenon time
- `resultTime` - Filter by result time (supports special value `latest`)
- `foi` - Filter by feature of interest

**For ControlStreams:**

- `executionTime` - Filter by command execution times
- `issueTime` - Filter by command issue times (optional)
- `controlledProperty` - Filter by controlled properties (ID or URI list)
- `foi` - Filter by feature of interest (transitive)

**For Commands:**

- `executionTime` - Filter by execution time
- `issueTime` - Filter by issue time
- `foi` - Filter by feature of interest

**For CommandStatus:**

- `statusCode` - Filter by status code (PENDING, ACCEPTED, EXECUTING, COMPLETED, FAILED, CANCELED)

**For SystemEvents:**

- `type` - Filter by event type

**Key Requirements (17 total):**

- Requirement 45-47: DataStream filters (phenomenonTime, resultTime, observedProperty, foi)
- Requirement 48-51: Observation filters (phenomenonTime, resultTime, foi)
- Requirement 52-55: ControlStream filters (issueTime, executionTime, controlledProperty, foi)
- Requirement 56-58: Command filters (issueTime, executionTime, foi)
- Requirement 59-60: CommandStatus filters (statusCode)
- Requirement 61-62: SystemEvent filters (type)

**Optional:** Servers MAY implement advanced filtering

#### 13.7 Conformance Class A.7: Create/Replace/Delete

**Identifier:** `/conf/create-replace-delete`  
**Requirements Class:** `/req/create-replace-delete`  
**Prerequisite:** OGC API - Features Part 4: Create, Replace, Update and Delete  
**Target Type:** Web API

**HTTP Methods Enabled:**

- POST (Create) - Create new resources
- PUT (Replace) - Replace existing resources
- DELETE (Delete) - Delete existing resources

**Resources Supported:**

- DataStreams, Observations
- ControlStreams, Commands, CommandStatus, CommandResult
- Feasibility, Feasibility Status, Feasibility Result
- SystemEvents

**Constraints:**

- DataStream schema changes rejected if observations exist (409)
- ControlStream schema changes rejected if commands exist (409)
- DataStream deletion requires `cascade=true` if observations exist (409 without cascade)
- ControlStream deletion requires `cascade=true` if commands exist (409 without cascade)
- Observation validation against DataStream schema (400 if invalid)
- Command validation against ControlStream schema (400 if invalid)

**Key Requirements (16 total):**

- Requirement 63-65: DataStream operations and constraints
- Requirement 66-67: Observation operations and constraints
- Requirement 68-70: ControlStream operations and constraints
- Requirement 71-72: Command operations and constraints
- Requirement 73-74: CommandStatus and CommandResult operations
- Requirement 75-77: Feasibility operations
- Requirement 78: SystemEvent operations

**Optional:** Servers MAY implement create/replace/delete operations

#### 13.8 Conformance Class A.8: Update

**Identifier:** `/conf/update`  
**Requirements Class:** `/req/update`  
**Prerequisite:** OGC API - Features Part 4: Create, Replace, Update and Delete, Conformance class A.7: `/conf/create-replace-delete`  
**Target Type:** Web API

**HTTP Method Enabled:**

- PATCH (Update) - Partial update using JSON Merge Patch (RFC 7396)

**Resources Supported:**

- DataStreams, Observations
- ControlStreams, Commands, CommandStatus, CommandResult
- Feasibility, Feasibility Status, Feasibility Result
- SystemEvents

**Constraints:**

- Same constraints as Create/Replace/Delete conformance class
- Schema changes rejected if data exists

**Key Requirements (14 total):**

- Requirement 79-80: DataStream update and constraints
- Requirement 81-82: Observation update and constraints
- Requirement 83-84: ControlStream update and constraints
- Requirement 85-86: Command update and constraints
- Requirement 87-88: CommandStatus and CommandResult update
- Requirement 89-91: Feasibility update
- Requirement 92: SystemEvent update

**Optional:** Servers MAY implement update operations

#### 13.9 Additional Encoding Conformance Classes

**A.9: JSON Encoding** (`/conf/json`)

- Mandatory for all servers
- Requirement 93-106: JSON schemas for all resource types

**A.10: SWE Common JSON Encoding** (`/conf/swecommon-json`)

- Optional
- Requirement 107-114: SWE Common JSON for observations/commands

**A.11: SWE Common Text Encoding** (`/conf/swecommon-text`)

- Optional
- Requirement 115-122: SWE Common Text (CSV) for observations/commands

**A.12: SWE Common Binary Encoding** (`/conf/swecommon-binary`)

- Optional
- Requirement 123-130: SWE Common Binary for observations/commands

---

### Examples

Part 2 provides comprehensive examples throughout the specification:

#### 14.1 DataStream Examples

**Simple Temperature DataStream (JSON):**

```json
{
  "type": "DataStream",
  "id": "temp-sensor-01-ds",
  "name": "Temperature Sensor 01 Data",
  "description": "Temperature measurements from sensor 01 in building A",
  "type": "observation",
  "validTime": "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z",
  "phenomenonTime": "2024-01-15T00:00:00Z/2024-01-16T00:00:00Z",
  "resultTime": "2024-01-15T00:00:01Z/2024-01-16T00:00:01Z",
  "observedProperties": ["http://example.org/properties/temperature"],
  "resultType": "measure",
  "live": true,
  "formats": [
    "application/json",
    "application/swe+json",
    "application/swe+binary"
  ],
  "links": [
    {
      "rel": "system",
      "href": "https://api.example.org/systems/temp-sensor-01",
      "title": "Temperature Sensor 01"
    },
    {
      "rel": "observations",
      "href": "https://api.example.org/datastreams/temp-sensor-01-ds/observations",
      "title": "Observations"
    },
    {
      "rel": "schema",
      "href": "https://api.example.org/datastreams/temp-sensor-01-ds/schema?obsFormat=application/json",
      "type": "application/schema+json",
      "title": "Observation Schema"
    }
  ]
}
```

**Multi-Property Weather DataStream:**

```json
{
  "type": "DataStream",
  "id": "weather-station-01-ds",
  "name": "Weather Station 01 Data",
  "observedProperties": [
    "http://example.org/properties/temperature",
    "http://example.org/properties/humidity",
    "http://example.org/properties/pressure",
    "http://example.org/properties/windSpeed",
    "http://example.org/properties/windDirection"
  ],
  "resultType": "record",
  "live": true,
  "formats": ["application/json", "application/swe+json"]
}
```

#### 14.2 Observation Examples

**Simple Scalar Observation:**

```json
{
  "type": "Observation",
  "id": "obs-2024-01-15-120000",
  "datastream@id": "temp-sensor-01-ds",
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": 23.5
}
```

**Vector Result Observation:**

```json
{
  "type": "Observation",
  "id": "obs-wind-2024-01-15-120000",
  "datastream@id": "wind-sensor-01-ds",
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": [5.2, 45.0, 0.0] // [speed m/s, direction degrees, vertical m/s]
}
```

**Record Result Observation:**

```json
{
  "type": "Observation",
  "id": "obs-weather-2024-01-15-120000",
  "datastream@id": "weather-station-01-ds",
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "resultTime": "2024-01-15T12:00:01Z",
  "result": {
    "temperature": 23.5,
    "humidity": 65.2,
    "pressure": 101325,
    "windSpeed": 5.2,
    "windDirection": 45.0
  }
}
```

#### 14.3 ControlStream Examples

**UAV PTZ Camera Control:**

```json
{
  "type": "ControlStream",
  "id": "uav-camera-ptz-cs",
  "name": "UAV Camera PTZ Control",
  "description": "Control stream for UAV camera pan/tilt/zoom",
  "type": "self",
  "validTime": "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z",
  "issueTime": "2024-01-15T00:00:00Z/2024-01-16T00:00:00Z",
  "executionTime": "2024-01-15T00:01:00Z/2024-01-16T00:01:00Z",
  "controlledProperties": [
    "http://example.org/properties/pan",
    "http://example.org/properties/tilt",
    "http://example.org/properties/zoom"
  ],
  "live": true,
  "async": true,
  "formats": ["application/json", "application/swe+json"],
  "links": [
    {
      "rel": "system",
      "href": "https://api.example.org/systems/uav-01",
      "title": "UAV-01"
    },
    {
      "rel": "commands",
      "href": "https://api.example.org/controlstreams/uav-camera-ptz-cs/commands",
      "title": "Commands"
    }
  ]
}
```

#### 14.4 Command Examples

**PTZ Camera Command:**

```json
{
  "type": "Command",
  "id": "cmd-ptz-2024-01-15-120000",
  "controlstream@id": "uav-camera-ptz-cs",
  "issueTime": "2024-01-15T12:00:00Z",
  "executionTime": "2024-01-15T12:01:00Z",
  "parameters": {
    "pan": 45.0,
    "tilt": 30.0,
    "zoom": 2.5
  }
}
```

**Satellite Imagery Tasking Command:**

```json
{
  "type": "Command",
  "id": "cmd-sat-task-2024-01-15",
  "controlstream@id": "eo-sat-01-cs",
  "issueTime": "2024-01-15T08:00:00Z",
  "executionTime": "2024-01-16T14:23:00Z",
  "parameters": {
    "targetArea": {
      "type": "Polygon",
      "coordinates": [
        [
          [-122.5, 37.5],
          [-122.3, 37.5],
          [-122.3, 37.7],
          [-122.5, 37.7],
          [-122.5, 37.5]
        ]
      ]
    },
    "bands": ["red", "green", "blue", "nir"],
    "resolution": 10.0
  }
}
```

#### 14.5 CommandStatus Examples

**Accepted Status:**

```json
{
  "type": "CommandStatus",
  "id": "status-001",
  "command@id": "cmd-sat-task-2024-01-15",
  "reportTime": "2024-01-15T08:00:05Z",
  "executionTime": "2024-01-16T14:23:00Z",
  "statusCode": "ACCEPTED",
  "percentCompletion": 0,
  "message": "Command accepted and scheduled for execution"
}
```

**Executing Status:**

```json
{
  "type": "CommandStatus",
  "id": "status-002",
  "command@id": "cmd-sat-task-2024-01-15",
  "reportTime": "2024-01-16T14:23:15Z",
  "executionTime": "2024-01-16T14:23:00Z",
  "statusCode": "EXECUTING",
  "percentCompletion": 25,
  "message": "Image acquisition in progress (pass 1 of 4)"
}
```

**Completed Status:**

```json
{
  "type": "CommandStatus",
  "id": "status-003",
  "command@id": "cmd-sat-task-2024-01-15",
  "reportTime": "2024-01-16T14:35:42Z",
  "executionTime": "2024-01-16T14:23:00Z",
  "statusCode": "COMPLETED",
  "percentCompletion": 100,
  "message": "Image acquisition completed successfully (4 images)"
}
```

#### 14.6 CommandResult Examples

**Datastream Reference Result:**

```json
{
  "type": "CommandResult",
  "id": "result-001",
  "command@id": "cmd-plume-sim-2024-01-15",
  "datastream@link": {
    "href": "https://api.example.org/datastreams/plume-sim-run-123",
    "title": "Chemical Plume Simulation Run 123",
    "type": "application/json"
  }
}
```

**Observation Reference Result:**

```json
{
  "type": "CommandResult",
  "id": "result-002",
  "command@id": "cmd-uav-photo-2024-01-15",
  "observation@link": [
    {
      "href": "https://api.example.org/observations/obs-image-001",
      "title": "UAV Image 001",
      "type": "image/jpeg"
    }
  ]
}
```

**Inline Result:**

```json
{
  "type": "CommandResult",
  "id": "result-003",
  "command@id": "cmd-system-status-query",
  "inline": {
    "batteryLevel": 87.5,
    "temperature": 45.2,
    "dataStorageUsed": 2345678901,
    "lastMaintenance": "2024-01-10T00:00:00Z"
  }
}
```

#### 14.7 SWE Common Examples

**Observation Schema (SWE Common JSON):**

```json
{
  "type": "DataRecord",
  "fields": [
    {
      "name": "phenomenonTime",
      "type": "Time",
      "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
      "label": "Phenomenon Time",
      "uom": {
        "code": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"
      }
    },
    {
      "name": "temperature",
      "type": "Quantity",
      "definition": "http://mmisw.org/ont/cf/parameter/air_temperature",
      "label": "Air Temperature",
      "uom": {
        "code": "Cel"
      }
    }
  ],
  "encoding": {
    "type": "JSONEncoding"
  }
}
```

**Observations (SWE Common Text/CSV):**

```
2024-01-15T12:00:00Z,23.5
2024-01-15T12:01:00Z,23.6
2024-01-15T12:02:00Z,23.4
2024-01-15T12:03:00Z,23.5
2024-01-15T12:04:00Z,23.7
```

---

---

## Section 2.2: CSAPI Part 2 OpenAPI Schema Analysis

**Schema:** [ogcapi-connectedsystems-2.bundled.oas31.yaml](../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml)  
**Date:** 2026-01-31  
**Status:** Complete

---

### Overview

The OpenAPI 3.1.0 specification for CSAPI Part 2 (Dynamic Data) defines 48 endpoints across 6 resource categories. The schema is 8,358 lines, compared to Part 1's schema, providing comprehensive machine-readable specifications for all dynamic data operations.

**API Information:**

- **Title:** OGC API - Connected Systems - Part 2: Dynamic Data
- **Version:** 0.0.1
- **Servers:**
  - Production: `https://api.georobotix.io/ogc/t18/api`
  - Development: `http://localhost:8181/sensorhub/api`

**Resource Categories:**

1. **Data Streams** (8 endpoints) - Observation containers and metadata
2. **Observations** (6 endpoints) - Dynamic sensor data records
3. **Control Streams** (8 endpoints) - Command containers and metadata
4. **Commands** (15 endpoints) - Control messages with status/result tracking
5. **System Events** (6 endpoints) - System state change notifications
6. **System History** (5 endpoints) - Historical system descriptions

**Format Support:**

- JSON (application/json) - Default, human-readable
- SWE Common JSON (application/swe+json) - Structured per SWE Common Data Model
- SWE Common Text (application/swe+csv, application/swe+text) - DSV formats
- SWE Common Binary (application/swe+binary) - Efficient binary encoding
- GeoJSON (application/geo+json) - Geospatial features
- SensorML JSON (application/sml+json) - Sensor metadata
- Protocol Buffers (application/x-protobuf) - Alternative binary format

---

### Path Definitions

The schema defines 48 endpoints organized into 6 categories:

#### 2.1 Datastream Paths (8 endpoints)

**Canonical Resources Endpoint:**

```yaml
GET /datastreams
```

- **Summary:** List all available datastreams
- **Query Parameters:** id, q, system, foi, observedProperty, phenomenonTime, resultTime, limit
- **Response:** 200 (DataStreamCollection), 400 (Bad Request)
- **Content Types:** application/json, application/geo+json

**Nested Resources Endpoint (from System):**

```yaml
GET /systems/{systemId}/datastreams
POST /systems/{systemId}/datastreams
```

- **GET Summary:** List datastreams of specific system
- **POST Summary:** Add datastream to system
- **Path Parameters:** systemId (string, minLength: 1, required)
- **Query Parameters (GET):** Same as canonical endpoint
- **Request Body (POST):** DataStream object
- **Response (POST):** 201 Created with Location header, 400 (Bad Request), 409 (Conflict)

**Canonical Resource Endpoint:**

```yaml
GET /datastreams/{dataStreamId}
PUT /datastreams/{dataStreamId}
DELETE /datastreams/{dataStreamId}
```

- **GET Summary:** Get datastream by ID
- **PUT Summary:** Update datastream
- **DELETE Summary:** Delete datastream
- **Path Parameters:** dataStreamId (string, minLength: 1, required)
- **Query Parameters (DELETE):** cascade (boolean, default: false)
- **Response (GET):** 200 (DataStream), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found), 409 (Conflict - if cascade=false and observations exist)

**Schema Endpoint:**

```yaml
GET /datastreams/{dataStreamId}/schema
PUT /datastreams/{dataStreamId}/schema
```

- **GET Summary:** Get observation schema for datastream
- **PUT Summary:** Update observation schema
- **Path Parameters:** dataStreamId (string, minLength: 1, required)
- **Query Parameters (GET):** obsFormat (string, required) - Media type of desired observation format
- **Request Body (PUT):** ObservationSchema object
- **Response (GET):** 200 (ObservationSchema), 400 (Bad Request), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict - if observations already exist)
- **Content Types:** application/json, application/schema+json, text/plain

#### 2.2 Observation Paths (6 endpoints)

**Canonical Resources Endpoint:**

```yaml
GET /observations
```

- **Summary:** List all available observations
- **Query Parameters:** id, q, dataStream, foi, phenomenonTime, resultTime, limit
- **Response:** 200 (ObservationCollection), 400 (Bad Request)
- **Content Types:** application/json, application/swe+json, application/swe+csv

**Nested Resources Endpoint (from DataStream):**

```yaml
GET /datastreams/{dataStreamId}/observations
POST /datastreams/{dataStreamId}/observations
```

- **GET Summary:** List observations from datastream
- **POST Summary:** Add observation to datastream
- **Path Parameters:** dataStreamId (string, minLength: 1, required)
- **Query Parameters (GET):** id, phenomenonTime, resultTime, limit
- **Request Body (POST):** Observation object (validated against datastream schema)
- **Response (POST):** 201 Created with Location header, 400 (Bad Request - schema violation), 409 (Conflict)

**Canonical Resource Endpoint:**

```yaml
GET /observations/{obsId}
PUT /observations/{obsId}
DELETE /observations/{obsId}
```

- **GET Summary:** Get observation by ID
- **PUT Summary:** Update observation
- **DELETE Summary:** Delete observation
- **Path Parameters:** obsId (string, minLength: 1, required)
- **Response (GET):** 200 (Observation), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request - schema violation), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found)

#### 2.3 ControlStream Paths (8 endpoints)

**Canonical Resources Endpoint:**

```yaml
GET /controlstreams
```

- **Summary:** List all available control streams
- **Query Parameters:** id, q, system, foi, controlledProperty, issueTime, executionTime, limit
- **Response:** 200 (ControlStreamCollection), 400 (Bad Request)
- **Content Types:** application/json, application/geo+json

**Nested Resources Endpoint (from System):**

```yaml
GET /systems/{systemId}/controlstreams
POST /systems/{systemId}/controlstreams
```

- **GET Summary:** List control streams of specific system
- **POST Summary:** Add control stream to system
- **Path Parameters:** systemId (string, minLength: 1, required)
- **Query Parameters (GET):** Same as canonical endpoint
- **Request Body (POST):** ControlStream object
- **Response (POST):** 201 Created with Location header, 400 (Bad Request), 409 (Conflict)

**Canonical Resource Endpoint:**

```yaml
GET /controlstreams/{controlStreamId}
PUT /controlstreams/{controlStreamId}
DELETE /controlstreams/{controlStreamId}
```

- **GET Summary:** Get control stream by ID
- **PUT Summary:** Update control stream
- **DELETE Summary:** Delete control stream
- **Path Parameters:** controlStreamId (string, minLength: 1, required)
- **Query Parameters (DELETE):** cascade (boolean, default: false)
- **Response (GET):** 200 (ControlStream), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found), 409 (Conflict - if cascade=false and commands exist)

**Schema Endpoint:**

```yaml
GET /controlstreams/{controlStreamId}/schema
PUT /controlstreams/{controlStreamId}/schema
```

- **GET Summary:** Get command schema for control stream
- **PUT Summary:** Update command schema
- **Path Parameters:** controlStreamId (string, minLength: 1, required)
- **Query Parameters (GET):** cmdFormat (string, optional) - Media type of desired command format
- **Request Body (PUT):** CommandSchema object
- **Response (GET):** 200 (CommandSchema), 400 (Bad Request), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict - if commands already issued)
- **Content Types:** application/json, application/schema+json, text/plain

#### 2.4 Command Paths (15 endpoints)

**Canonical Resources Endpoint:**

```yaml
GET /commands
```

- **Summary:** List all available commands
- **Query Parameters:** id, q, controlStream, foi, sender, issueTime, executionTime, statusCode, limit
- **Response:** 200 (CommandCollection), 400 (Bad Request)
- **Content Types:** application/json, application/swe+json, application/swe+csv

**Nested Resources Endpoint (from ControlStream):**

```yaml
GET /controlstreams/{controlStreamId}/commands
POST /controlstreams/{controlStreamId}/commands
```

- **GET Summary:** List commands from control stream
- **POST Summary:** Send command to control stream
- **Path Parameters:** controlStreamId (string, minLength: 1, required)
- **Query Parameters (GET):** id, sender, issueTime, executionTime, statusCode, limit
- **Request Body (POST):** Command object (validated against control stream schema)
- **Response (POST):** 201 Created with Location header, 200 OK (synchronous execution), 400 (Bad Request - schema violation), 409 (Conflict)

**Canonical Resource Endpoint:**

```yaml
GET /commands/{cmdId}
PUT /commands/{cmdId}
DELETE /commands/{cmdId}
```

- **GET Summary:** Get command by ID
- **PUT Summary:** Update command
- **DELETE Summary:** Delete command
- **Path Parameters:** cmdId (string, minLength: 1, required)
- **Response (GET):** 200 (Command), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request - schema violation), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found)

**Command Status Endpoints:**

```yaml
GET /commands/{cmdId}/status
POST /commands/{cmdId}/status
GET /commands/{cmdId}/status/{statusId}
PUT /commands/{cmdId}/status/{statusId}
DELETE /commands/{cmdId}/status/{statusId}
```

- **GET (collection) Summary:** List command status reports
- **POST Summary:** Add command status report
- **GET (single) Summary:** Get status report by ID
- **PUT Summary:** Update status report
- **DELETE Summary:** Delete status report
- **Path Parameters:** cmdId (string, minLength: 1, required), statusId (string, minLength: 1, required)
- **Query Parameters (GET collection):** id, reportTime, statusCode, limit
- **Request Body (POST/PUT):** CommandStatus object
- **Response (POST):** 201 Created with Location header, 400 (Bad Request), 409 (Conflict)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found), 409 (Conflict - if dependencies exist)

**Command Result Endpoints:**

```yaml
GET /commands/{cmdId}/result
POST /commands/{cmdId}/result
GET /commands/{cmdId}/result/{resultId}
PUT /commands/{cmdId}/result/{resultId}
DELETE /commands/{cmdId}/result/{resultId}
```

- **GET (collection) Summary:** List command results
- **POST Summary:** Add command result
- **GET (single) Summary:** Get command result by ID
- **PUT Summary:** Update command result
- **DELETE Summary:** Delete command result
- **Path Parameters:** cmdId (string, minLength: 1, required), resultId (string, minLength: 1, required)
- **Query Parameters (GET collection):** id, limit
- **Request Body (POST/PUT):** CommandResult object
- **Response (POST):** 201 Created with Location header, 400 (Bad Request), 409 (Conflict)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found), 409 (Conflict - if dependencies exist)

#### 2.5 SystemEvent Paths (6 endpoints)

**Canonical Resources Endpoint:**

```yaml
GET /systemEvents
```

- **Summary:** List all available system events
- **Query Parameters:** id, q, system, eventType, datetime, limit
- **Response:** 200 (SystemEventCollection), 400 (Bad Request)
- **Content Types:** application/json

**Nested Resources Endpoint (from System):**

```yaml
GET /systems/{systemId}/events
POST /systems/{systemId}/events
```

- **GET Summary:** List events of specific system
- **POST Summary:** Publish system event
- **Path Parameters:** systemId (string, minLength: 1, required)
- **Query Parameters (GET):** id, eventType, datetime, limit
- **Request Body (POST):** SystemEvent object
- **Response (POST):** 201 Created with Location header, 400 (Bad Request), 409 (Conflict)

**Canonical Resource Endpoint:**

```yaml
GET /systems/{systemId}/events/{eventId}
PUT /systems/{systemId}/events/{eventId}
DELETE /systems/{systemId}/events/{eventId}
```

- **GET Summary:** Get event by ID
- **PUT Summary:** Update event
- **DELETE Summary:** Delete event
- **Path Parameters:** systemId (string, minLength: 1, required), eventId (string, minLength: 1, required)
- **Response (GET):** 200 (SystemEvent), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found)

**Note:** SystemEvent canonical resource endpoint uses nested path (not top-level /systemEvents/{eventId})

#### 2.6 SystemHistory Paths (5 endpoints)

**Resources Endpoint:**

```yaml
GET /systems/{systemId}/history
```

- **Summary:** List system history (historical descriptions)
- **Query Parameters:** id, validTime, limit
- **Response:** 200 (SystemHistoryCollection), 400 (Bad Request)
- **Content Types:** application/json, application/geo+json, application/sml+json

**Resource Endpoint:**

```yaml
GET /systems/{systemId}/history/{revId}
PUT /systems/{systemId}/history/{revId}
DELETE /systems/{systemId}/history/{revId}
```

- **GET Summary:** Get historical description by ID
- **PUT Summary:** Update historical description
- **DELETE Summary:** Delete historical description
- **Path Parameters:** systemId (string, minLength: 1, required), revId (string, minLength: 1, required)
- **Response (GET):** 200 (System), 404 (Not Found)
- **Response (PUT):** 204 No Content, 400 (Bad Request), 404 (Not Found), 409 (Conflict)
- **Response (DELETE):** 204 No Content, 404 (Not Found)

**Note:** No POST endpoint - history entries created automatically on System updates

---

### HTTP Methods by Path

Complete HTTP method support matrix:

#### GET Operations (All 48 endpoints support GET)

- **Collections:** All resources and nested resources endpoints
- **Single Resources:** All resource and nested resource item endpoints
- **Special:** Schema endpoints, status endpoints, result endpoints, history endpoints

#### POST Operations (15 endpoints)

- `/systems/{systemId}/datastreams` - Create datastream
- `/datastreams/{dataStreamId}/observations` - Create observation
- `/systems/{systemId}/controlstreams` - Create control stream
- `/controlstreams/{controlStreamId}/commands` - Send command
- `/commands/{cmdId}/status` - Create status report
- `/commands/{cmdId}/result` - Create command result
- `/systems/{systemId}/events` - Publish event

#### PUT Operations (19 endpoints)

- `/datastreams/{dataStreamId}` - Replace datastream
- `/datastreams/{dataStreamId}/schema` - Replace observation schema
- `/observations/{obsId}` - Replace observation
- `/controlstreams/{controlStreamId}` - Replace control stream
- `/controlstreams/{controlStreamId}/schema` - Replace command schema
- `/commands/{cmdId}` - Replace command
- `/commands/{cmdId}/status/{statusId}` - Replace status report
- `/commands/{cmdId}/result/{resultId}` - Replace command result
- `/systems/{systemId}/events/{eventId}` - Replace event
- `/systems/{systemId}/history/{revId}` - Replace historical description

#### DELETE Operations (14 endpoints)

- `/datastreams/{dataStreamId}` - Delete datastream
- `/observations/{obsId}` - Delete observation
- `/controlstreams/{controlStreamId}` - Delete control stream
- `/commands/{cmdId}` - Delete command
- `/commands/{cmdId}/status/{statusId}` - Delete status report
- `/commands/{cmdId}/result/{resultId}` - Delete command result
- `/systems/{systemId}/events/{eventId}` - Delete event
- `/systems/{systemId}/history/{revId}` - Delete historical description

**Note:** PATCH method not defined in schema (referenced in standard but not implemented in OpenAPI)

---

### Query Parameters

The schema defines 23 distinct query parameters across all endpoints:

#### 3.1 Identifier Parameters

**id** (All collection endpoints)

- **Type:** `oneOf[array<string>, array<string format:uri>]`
- **Description:** List of resource local IDs or unique URIs
- **Explode:** false (comma-separated)
- **Examples:**
  - Local IDs: `RES_ID1,RES_ID2,RES_ID63`
  - Unique IDs: `urn:example:resource:001,urn:example:resource:033`
- **Used By:** All collection endpoints (datastreams, observations, controlstreams, commands, systemEvents, history)

**q** (Full-text search)

- **Type:** `array<string>`
- **Item Constraints:** minLength: 1, maxLength: 50
- **Description:** Keywords for full-text search (searches name, description, and other textual fields)
- **Explode:** false (comma-separated)
- **Examples:**
  - Single keyword: `temp`
  - Multiple keywords: `gps,imu`
- **Used By:** All collection endpoints except history

#### 3.2 Association Parameters

**system** (DataStreams, ControlStreams)

- **Type:** `oneOf[array<string>, array<string format:uri>]`
- **Description:** Filter by associated system IDs or URIs
- **Explode:** false
- **Used By:** /datastreams, /controlstreams, /systemEvents

**dataStream** (Observations)

- **Type:** `oneOf[array<string>, array<string format:uri>]`
- **Description:** Filter observations by datastream IDs
- **Explode:** false
- **Used By:** /observations

**controlStream** (Commands)

- **Type:** `oneOf[array<string>, array<string format:uri>]`
- **Description:** Filter commands by control stream IDs
- **Explode:** false
- **Used By:** /commands

**foi** (Feature of Interest)

- **Type:** `oneOf[array<string>, array<string format:uri>]`
- **Description:** Filter by feature of interest IDs (transitive via sampling features)
- **Explode:** false
- **Used By:** /datastreams, /observations, /controlstreams, /commands

#### 3.3 Property Parameters

**observedProperty** (DataStreams, Observations)

- **Type:** `oneOf[array<string>, array<string format:uri>]`
- **Description:** Filter by observable property IDs or URIs
- **Explode:** false
- **Used By:** /datastreams

**controlledProperty** (ControlStreams)

- **Type:** `oneOf[array<string>, array<string format:uri>]`
- **Description:** Filter by controllable property IDs or URIs
- **Explode:** false
- **Used By:** /controlstreams

#### 3.4 Temporal Parameters

**phenomenonTime** (DataStreams, Observations)

- **Type:** `oneOf[timeInstant, timePeriod]`
- **Time Instant:** ISO 8601 date-time string (format: date-time)
- **Time Period:** Array of 2 date-times [startTime, endTime]
- **Special Values:** `now`, `latest`
- **Examples:**
  - Instant: `2018-02-12T23:20:50Z`
  - Closed period: `2018-02-12T00:00:00Z/2018-03-18T12:31:12Z`
  - Open start: `../2018-03-18T12:31:12Z`
  - Open end: `2018-02-12T00:00:00Z/..`
  - Half-bounded with now: `2018-02-12T00:00:00Z/now`
  - Latest: `latest` (Observations only)
- **Description:** Filter by observation phenomenon time (when observed property value applies to FOI)
- **Used By:** /datastreams, /observations, /datastreams/{id}/observations

**resultTime** (DataStreams, Observations)

- **Type:** Same as phenomenonTime
- **Description:** Filter by observation result generation time
- **Used By:** /datastreams, /observations, /datastreams/{id}/observations

**issueTime** (ControlStreams, Commands)

- **Type:** Same as phenomenonTime
- **Description:** Filter by command issue time
- **Used By:** /controlstreams, /commands, /controlstreams/{id}/commands

**executionTime** (ControlStreams, Commands)

- **Type:** Same as phenomenonTime
- **Description:** Filter by command execution time
- **Used By:** /controlstreams, /commands, /controlstreams/{id}/commands

**reportTime** (CommandStatus)

- **Type:** Same as phenomenonTime
- **Description:** Filter by status report generation time
- **Used By:** /commands/{cmdId}/status

**validTime** (SystemHistory)

- **Type:** Same as phenomenonTime
- **Description:** Filter by system description validity period
- **Used By:** /systems/{systemId}/history

**datetime** (SystemEvents)

- **Type:** Same as phenomenonTime
- **Description:** Filter by event occurrence time
- **Used By:** /systemEvents, /systems/{systemId}/events

#### 3.5 Status and Sender Parameters

**statusCode** (Commands)

- **Type:** `array<enum>`
- **Enum Values:** PENDING, ACCEPTED, REJECTED, SCHEDULED, UPDATED, CANCELED, EXECUTING, FAILED, COMPLETED
- **Description:** Filter commands by current status code
- **Explode:** false
- **Used By:** /commands, /controlstreams/{id}/commands, /commands/{cmdId}/status

**sender** (Commands)

- **Type:** `array<string>`
- **Description:** Filter commands by sender IDs
- **Explode:** false
- **Used By:** /commands, /controlstreams/{id}/commands

**eventType** (SystemEvents)

- **Type:** `array<string>`
- **Description:** Filter events by type
- **Explode:** false
- **Used By:** /systemEvents, /systems/{systemId}/events

#### 3.6 Pagination Parameters

**limit** (All collection endpoints)

- **Type:** `integer`
- **Minimum:** 1
- **Maximum:** 10000
- **Default:** 10
- **Description:** Maximum number of items in response
- **Examples:** 10, 100, 1000
- **Used By:** All collection endpoints

**Note:** No explicit offset parameter - pagination uses cursor-based links in response

#### 3.7 Format Parameters

**obsFormat** (DataStream schema)

- **Type:** `string`
- **Required:** true
- **Description:** Media type of desired observation format
- **Examples:** `application/json`, `application/swe+json`, `application/swe+csv`, `application/swe+binary`, `application/x-protobuf`
- **URL Encoding Required:** Yes (e.g., `application/swe%2Bjson`)
- **Used By:** /datastreams/{id}/schema (GET)

**cmdFormat** (ControlStream schema)

- **Type:** `string`
- **Required:** false
- **Description:** Media type of desired command format
- **Examples:** Same as obsFormat
- **Used By:** /controlstreams/{id}/schema (GET)

#### 3.8 Delete Parameters

**cascade** (DELETE operations)

- **Type:** `boolean`
- **Default:** false
- **Description:** If true, dependent nested resources are also deleted
- **Used By:** DELETE /datastreams/{id}, DELETE /controlstreams/{id}

---

### Request Body Schemas

The schema defines 8 main request body schemas:

#### 4.1 DataStream Schema

**Used By:** POST /systems/{systemId}/datastreams, PUT /datastreams/{dataStreamId}

**Structure:**

```yaml
type: object
required:
  - name
  - system@link
  - observedProperties
  - phenomenonTime
  - resultTime
  - resultType
  - live
  - formats

properties:
  id:
    type: string
    readOnly: true
  name:
    type: string
  description:
    type: string
  validTime:
    type: array
    minItems: 2
    maxItems: 2
    items:
      oneOf:
        - type: string (format: date-time)
        - type: string (enum: [now])
  formats:
    type: array
    readOnly: true
    items:
      type: string
  system@link:
    $ref: '#/components/schemas/link'
    readOnly: true
  outputName:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  deployment@link:
    $ref: '#/components/schemas/link'
  featureOfInterest@link:
    $ref: '#/components/schemas/link'
  samplingFeature@link:
    $ref: '#/components/schemas/link'
  observedProperties:
    oneOf:
      - type: array
        items:
          type: object
          properties:
            definition:
              type: string
              format: uri
            label:
              type: string
            description:
              type: string
      - type: 'null'
    readOnly: true
  phenomenonTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  phenomenonTimeInterval:
    type: string
    description: ISO 8601 duration
  resultTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  resultTimeInterval:
    type: string
    description: ISO 8601 duration
  type:
    type: string
    enum: [status, observation]
  resultType:
    oneOf:
      - type: string
        enum: [measure, vector, record, coverage, complex]
      - type: 'null'
    readOnly: true
  live:
    oneOf:
      - type: boolean
      - type: 'null'
  schema:
    $ref: '#/components/schemas/ObservationSchema'
    writeOnly: true
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**Read-Only Properties:** id, system@link, observedProperties, phenomenonTime, resultTime, resultType, formats (server-generated)

**Write-Only Properties:** schema (submitted on create, not returned on read)

#### 4.2 Observation Schema

**Used By:** POST /datastreams/{dataStreamId}/observations, PUT /observations/{obsId}

**Structure:**

```yaml
type: object
required:
  - id
  - datastream@id
  - resultTime
  - (result OR result@link)

properties:
  id:
    type: string
    readOnly: true
  datastream@id:
    type: string
    readOnly: true
  samplingFeature@id:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  phenomenonTime:
    type: string
    format: date-time
  resultTime:
    type: string
    format: date-time
  parameters:
    type: object
    description: Validated against datastream parametersSchema
  result:
    description: Validated against datastream resultSchema
  result@link:
    $ref: '#/components/schemas/link'
    description: Alternative to inline result

oneOf:
  - required: [result]
  - required: [result@link]
```

**Validation:**

- `result` MUST conform to DataStream's `resultSchema`
- `parameters` MUST conform to DataStream's `parametersSchema` (if provided)
- Server MUST reject with 400 if validation fails

**Default Behavior:**

- If `phenomenonTime` omitted, defaults to `resultTime`

#### 4.3 ControlStream Schema

**Used By:** POST /systems/{systemId}/controlstreams, PUT /controlstreams/{controlStreamId}

**Structure:**

```yaml
type: object
required:
  - name
  - system@link
  - controlledProperties
  - issueTime
  - executionTime
  - live
  - async
  - formats

properties:
  id:
    type: string
    readOnly: true
  name:
    type: string
  description:
    type: string
  validTime:
    type: array
    minItems: 2
    maxItems: 2
    items:
      oneOf:
        - type: string (format: date-time)
        - type: string (enum: [now])
  formats:
    type: array
    readOnly: true
    items:
      type: string
  system@link:
    $ref: '#/components/schemas/link'
    readOnly: true
  inputName:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  deployment@link:
    $ref: '#/components/schemas/link'
  featureOfInterest@link:
    $ref: '#/components/schemas/link'
  samplingFeature@link:
    $ref: '#/components/schemas/link'
  controlledProperties:
    oneOf:
      - type: array
        items:
          type: object
          properties:
            definition:
              type: string
              format: uri
            label:
              type: string
            description:
              type: string
      - type: 'null'
    readOnly: true
  issueTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  executionTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  live:
    oneOf:
      - type: boolean
      - type: 'null'
    readOnly: true
  async:
    type: boolean
  schema:
    $ref: '#/components/schemas/CommandSchema'
    writeOnly: true
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**Read-Only Properties:** id, system@link, controlledProperties, issueTime, executionTime, live, formats

**Write-Only Properties:** schema

#### 4.4 Command Schema

**Used By:** POST /controlstreams/{controlStreamId}/commands, PUT /commands/{cmdId}

**Structure:**

```yaml
type: object
required:
  - id
  - controlstream@id
  - issueTime
  - parameters

properties:
  id:
    type: string
    readOnly: true
  controlstream@id:
    type: string
    readOnly: true
  samplingFeature@id:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  issueTime:
    type: string
    format: date-time
    readOnly: true
  executionTime:
    type: array
    minItems: 2
    maxItems: 2
    items:
      oneOf:
        - type: string (format: date-time)
        - type: string (enum: [now])
    readOnly: true
  sender:
    type: string
    readOnly: true
  currentStatus:
    type: string
    enum: [PENDING, ACCEPTED, REJECTED, SCHEDULED, UPDATED, CANCELED, EXECUTING, FAILED, COMPLETED]
    readOnly: true
  parameters:
    type: object
    description: Validated against control stream parametersSchema
```

**Validation:**

- `parameters` MUST conform to ControlStream's `parametersSchema`
- Server MUST reject with 400 if validation fails

**Server Behavior:**

- Server sets `issueTime` to current time on POST
- Server sets `currentStatus` to PENDING on POST
- Server may update `executionTime` based on command processing

#### 4.5 CommandStatus Schema

**Used By:** POST /commands/{cmdId}/status, PUT /commands/{cmdId}/status/{statusId}

**Structure:**

```yaml
type: object
required:
  - id
  - command@id
  - reportTime
  - statusCode

properties:
  id:
    type: string
    readOnly: true
  command@id:
    type: string
    readOnly: true
  reportTime:
    type: string
    format: date-time
    readOnly: true
  statusCode:
    type: string
    enum: [PENDING, ACCEPTED, REJECTED, SCHEDULED, UPDATED, CANCELED, EXECUTING, FAILED, COMPLETED]
  percentCompletion:
    type: number
    minimum: 0
    maximum: 100
  executionTime:
    type: array
    minItems: 2
    maxItems: 2
    items:
      oneOf:
        - type: string (format: date-time)
        - type: string (enum: [now])
  message:
    type: string
  results:
    type: array
    items:
      $ref: '#/components/schemas/CommandResult'
```

**Status Code Semantics:**

- **PENDING:** Command received, awaiting decision
- **ACCEPTED:** Command accepted, may be scheduled
- **REJECTED:** Command rejected (final state)
- **SCHEDULED:** Command scheduled with execution time
- **UPDATED:** Command update accepted
- **CANCELED:** User-canceled (final state)
- **EXECUTING:** Currently executing
- **FAILED:** Execution failed (final state)
- **COMPLETED:** Successfully completed (final state)

**Server Behavior:**

- Server sets `reportTime` to current time on POST

#### 4.6 CommandResult Schema

**Used By:** POST /commands/{cmdId}/result, PUT /commands/{cmdId}/result/{resultId}

**Structure:**

```yaml
type: object
required:
  - id
  - command@id
  - (one of: data, observation@link, observationSet@link, datastream@link, external@link)

properties:
  id:
    type: string
    readOnly: true
  command@id:
    type: string
    readOnly: true
  data:
    type: object
    description: Inline JSON result data
  observation@link:
    $ref: '#/components/schemas/link'
    description: Link to single observation result
  observationSet@link:
    $ref: '#/components/schemas/link'
    description: Link to observation collection
  datastream@link:
    type: object
    properties:
      href:
        type: string
        format: uri
      resultTime:
        $ref: '#/components/schemas/timePeriod'
        description: Optional time range within datastream
  external@link:
    $ref: '#/components/schemas/link'
    description: Link to external dataset

oneOf:
  - required: [data]
  - required: [observation@link]
  - required: [observationSet@link]
  - required: [datastream@link]
  - required: [external@link]
```

**Result Types:**

1. **Inline Data:** JSON object with command output
2. **Observation Reference:** Link to single observation
3. **Observation Set:** Link to collection of observations
4. **Datastream Reference:** Link to datastream with optional time range filter
5. **External Reference:** Link to external dataset (e.g., NetCDF file, video)

#### 4.7 SystemEvent Schema

**Used By:** POST /systems/{systemId}/events, PUT /systems/{systemId}/events/{eventId}

**Structure:**

```yaml
type: object
required:
  - id
  - system@id
  - time
  - eventType

properties:
  id:
    type: string
    readOnly: true
  system@id:
    type: string
    readOnly: true
  time:
    type: string
    format: date-time
  eventType:
    type: string
  description:
    type: string
  properties:
    type: object
    description: Event-specific properties
```

**Event Types (examples):**

- System activation/deactivation
- Configuration change
- Calibration
- Maintenance
- Fault/error
- Status change

#### 4.8 ObservationSchema and CommandSchema

**Used By:** DataStream schema property (writeOnly), ControlStream schema property (writeOnly)

**ObservationSchema Structure:**

```yaml
type: object
required:
  - obsFormat
  - (recordSchema OR resultSchema)

properties:
  obsFormat:
    type: string
    description: Media type (application/json, application/swe+json, etc.)

  # For JSON format
  parametersSchema:
    $ref: '#/components/schemas/AbstractDataComponent'
  resultSchema:
    $ref: '#/components/schemas/AbstractDataComponent'
  resultLink:
    type: object
    properties:
      mediaType:
        type: string

  # For SWE Common formats
  recordSchema:
    $ref: '#/components/schemas/DataRecord'
  encoding:
    oneOf:
      - $ref: '#/components/schemas/JSONEncoding'
      - $ref: '#/components/schemas/TextEncoding'
      - $ref: '#/components/schemas/BinaryEncoding'

  # For Protobuf format
  messageSchema:
    oneOf:
      - type: string
      - $ref: '#/components/schemas/link'

discriminator:
  propertyName: obsFormat
  mapping:
    application/json: JSONObservationSchema
    application/swe+json: SWECommonJSONObservationSchema
    application/swe+csv: SWECommonTextObservationSchema
    application/swe+binary: SWECommonBinaryObservationSchema
    application/x-protobuf: ProtobufObservationSchema
```

**CommandSchema Structure:** Same as ObservationSchema but with `commandFormat` instead of `obsFormat`

---

### Response Schemas

The schema defines comprehensive response structures for all endpoints:

#### 5.1 Success Response Codes

**200 OK** - Successful retrieval

- **Content Types:** application/json, application/geo+json, application/sml+json, application/swe+json, application/swe+csv, application/schema+json, text/plain
- **Body:** Single resource or collection with items array and links

**201 Created** - Resource successfully created

- **Headers:** Location (URI of newly created resource)
- **Content Types:** application/json
- **Body:** Created resource representation (optional)

**204 No Content** - Successful update or deletion

- **No response body**

#### 5.2 Error Response Codes

**400 Bad Request** - Invalid query parameters or request body

- **Causes:**
  - Invalid parameter format
  - Missing required parameters
  - Schema validation failure (observation/command doesn't conform to datastream/control stream schema)
  - Invalid temporal parameter format

**401 Unauthorized** - No authentication information provided

- **Causes:**
  - Missing authentication credentials
  - Invalid authentication token

**403 Forbidden** - Insufficient permissions

- **Causes:**
  - User lacks permission to access resource
  - User lacks permission to perform operation

**404 Not Found** - Resource not found at specified URL

- **Causes:**
  - Resource ID doesn't exist
  - Invalid path parameter
  - Resource deleted

**409 Conflict** - Operation conflicts with current resource state

- **Causes:**
  - DELETE without cascade when nested resources exist
  - PUT/PATCH schema change when observations/commands already exist
  - Resource already exists with same ID (on POST)
  - Concurrent modification conflict

**5XX Server Error** - Unexpected server error

- **502, 503:** Temporary errors, client MAY retry
- **500, 501, 504:** Permanent errors, client SHOULD NOT retry

#### 5.3 Collection Response Structure

**Used By:** All GET collection endpoints

```yaml
type: object
required:
  - items

properties:
  items:
    type: array
    items:
      # Resource-specific schema (DataStream, Observation, etc.)
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**Pagination Links:**

- `rel: "self"` - Current page
- `rel: "next"` - Next page (if more items exist)
- `rel: "prev"` - Previous page (if not first page)
- `rel: "first"` - First page
- `rel: "last"` - Last page (if known)

**Example:**

```json
{
  "items": [
    {
      /* datastream 1 */
    },
    {
      /* datastream 2 */
    }
  ],
  "links": [
    { "rel": "self", "href": "/datastreams?limit=10" },
    { "rel": "next", "href": "/datastreams?limit=10&cursor=abc123" }
  ]
}
```

#### 5.4 Link Object Schema

**Used Throughout:** All resource associations and pagination

```yaml
type: object
required:
  - href

properties:
  href:
    type: string
    format: uri
  rel:
    type: string
    description: Link relation type (canonical, system, procedure, etc.)
  type:
    type: string
    description: Media type of linked resource
  hreflang:
    type: string
    pattern: ^([a-z]{2}(-[A-Z]{2})?)|x-default$
    description: Language code (e.g., en, en-US, x-default)
  title:
    type: string
    description: Human-readable link description
  uid:
    type: string
    format: uri
    description: Unique identifier of linked resource
  rt:
    type: string
    format: uri
    description: Semantic type URI
  if:
    type: string
    format: uri
    description: Interface URI
```

**Common Link Relations:**

- `canonical` - Canonical URL of resource
- `self` - Current resource/page
- `next` / `prev` / `first` / `last` - Pagination
- `system` - Associated system
- `procedure` - Associated procedure
- `deployment` - Associated deployment
- `samplingFeature` - Associated sampling feature
- `featureOfInterest` - Associated feature of interest
- `datastream` - Associated datastream
- `controlstream` - Associated control stream
- `observations` - Observations collection
- `commands` - Commands collection
- `status` - Status reports collection
- `result` - Results collection
- `schema` - Schema endpoint

---

### Schema Operation Endpoints

The schema provides detailed specifications for dynamic schema operations:

#### 6.1 Datastream Schema GET Response

**Endpoint:** GET /datastreams/{dataStreamId}/schema?obsFormat={format}

**Response Structure by Format:**

**JSON Format (obsFormat=application/json):**

```yaml
type: object
properties:
  obsFormat:
    type: string
    const: application/json
  parametersSchema:
    $ref: '#/components/schemas/AbstractDataComponent'
    description: Optional schema for observation parameters
  resultSchema:
    $ref: '#/components/schemas/AbstractDataComponent'
    description: Required schema for inline observation results
  resultLink:
    type: object
    properties:
      mediaType:
        type: string
    description: For out-of-band results (images, files, etc.)

oneOf:
  - required: [obsFormat, resultSchema]
  - required: [obsFormat, resultLink]
```

**SWE Common JSON Format (obsFormat=application/swe+json):**

```yaml
type: object
required:
  - obsFormat
  - recordSchema
  - encoding

properties:
  obsFormat:
    type: string
    const: application/swe+json
  recordSchema:
    $ref: '#/components/schemas/DataRecord'
    description: DataRecord with fields for phenomenonTime, resultTime, parameters, result
  encoding:
    $ref: '#/components/schemas/JSONEncoding'
    properties:
      type:
        const: JSONEncoding
      recordsAsArrays:
        type: boolean
        default: false
      vectorsAsArrays:
        type: boolean
        default: false
```

**SWE Common Text Format (obsFormat=application/swe+csv):**

```yaml
type: object
required:
  - obsFormat
  - recordSchema
  - encoding

properties:
  obsFormat:
    type: string
    enum: [application/swe+csv, application/swe+text]
  recordSchema:
    $ref: '#/components/schemas/DataRecord'
  encoding:
    $ref: '#/components/schemas/TextEncoding'
    properties:
      type:
        const: TextEncoding
      collapseWhiteSpaces:
        type: boolean
      decimalSeparator:
        type: string
        minLength: 1
      tokenSeparator:
        type: string
        minLength: 1
      blockSeparator:
        type: string
        minLength: 1
```

**SWE Common Binary Format (obsFormat=application/swe+binary):**

```yaml
type: object
required:
  - obsFormat
  - recordSchema
  - encoding

properties:
  obsFormat:
    type: string
    const: application/swe+binary
  recordSchema:
    $ref: '#/components/schemas/DataRecord'
  encoding:
    $ref: '#/components/schemas/BinaryEncoding'
    properties:
      type:
        const: BinaryEncoding
      byteOrder:
        type: string
        enum: [bigEndian, littleEndian]
      byteEncoding:
        type: string
        enum: [base64, raw]
      byteLength:
        type: integer
      members:
        type: array
        items:
          oneOf:
            - $ref: '#/components/schemas/Component'
            - $ref: '#/components/schemas/Block'
```

**Protobuf Format (obsFormat=application/x-protobuf):**

```yaml
type: object
required:
  - obsFormat
  - messageSchema

properties:
  obsFormat:
    type: string
    const: application/x-protobuf
  messageSchema:
    oneOf:
      - type: string
        description: Inline .proto schema definition
      - $ref: '#/components/schemas/link'
        description: Link to .proto file
```

#### 6.2 ControlStream Schema GET Response

**Endpoint:** GET /controlstreams/{controlStreamId}/schema?cmdFormat={format}

**Structure:** Same as DataStream schema but:

- `commandFormat` instead of `obsFormat`
- `parametersSchema` is required (not optional)
- Additional optional `feasibilityResultSchema` for feasibility channels

---

### Status and Result Endpoint Definitions

The schema provides detailed specifications for command lifecycle tracking:

#### 7.1 CommandStatus Collection Response

**Endpoint:** GET /commands/{cmdId}/status

```yaml
type: object
required:
  - items

properties:
  items:
    type: array
    items:
      $ref: '#/components/schemas/CommandStatus'
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**Ordered:** Status reports typically ordered by reportTime (chronological)

#### 7.2 CommandStatus Single Resource Response

**Endpoints:**

- GET /commands/{cmdId}/status/{statusId}
- POST /commands/{cmdId}/status (201 response body)

```yaml
type: object
required:
  - id
  - command@id
  - reportTime
  - statusCode

properties:
  id:
    type: string
  command@id:
    type: string
  reportTime:
    type: string
    format: date-time
  statusCode:
    type: string
    enum: [PENDING, ACCEPTED, REJECTED, SCHEDULED, UPDATED, CANCELED, EXECUTING, FAILED, COMPLETED]
  percentCompletion:
    type: number
    minimum: 0
    maximum: 100
  executionTime:
    type: array
    minItems: 2
    maxItems: 2
    items:
      oneOf:
        - type: string (format: date-time)
        - type: string (enum: [now])
  message:
    type: string
  results:
    type: array
    items:
      $ref: '#/components/schemas/CommandResult'
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**Status Code State Machine:**

```
Initial: PENDING

PENDING → ACCEPTED → SCHEDULED → EXECUTING → COMPLETED
                                           → FAILED
        → REJECTED
        → CANCELED

SCHEDULED → UPDATED → EXECUTING
         → CANCELED

EXECUTING → UPDATED → EXECUTING (progress updates)
```

#### 7.3 CommandResult Collection Response

**Endpoint:** GET /commands/{cmdId}/result

```yaml
type: object
required:
  - items

properties:
  items:
    type: array
    items:
      $ref: '#/components/schemas/CommandResult'
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**Multiple Results:** A command can produce multiple results (e.g., multiple images, multiple model timesteps)

#### 7.4 CommandResult Single Resource Response

**Endpoints:**

- GET /commands/{cmdId}/result/{resultId}
- POST /commands/{cmdId}/result (201 response body)

```yaml
type: object
required:
  - id
  - command@id

properties:
  id:
    type: string
  command@id:
    type: string
  data:
    type: object
  observation@link:
    $ref: '#/components/schemas/link'
  observationSet@link:
    $ref: '#/components/schemas/link'
  datastream@link:
    type: object
    properties:
      href:
        type: string
        format: uri
      resultTime:
        type: array
        minItems: 2
        maxItems: 2
        items:
          type: string
          format: date-time
  external@link:
    $ref: '#/components/schemas/link'
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'

oneOf:
  - required: [data]
  - required: [observation@link]
  - required: [observationSet@link]
  - required: [datastream@link]
  - required: [external@link]
```

**Result Type Examples:**

1. **Inline Data:**

```json
{
  "id": "result-001",
  "command@id": "cmd-123",
  "data": {
    "battery": 87.5,
    "temperature": 45.2
  }
}
```

2. **Observation Reference:**

```json
{
  "id": "result-002",
  "command@id": "cmd-456",
  "observation@link": {
    "href": "/observations/obs-789",
    "type": "image/jpeg"
  }
}
```

3. **Datastream with Time Range:**

```json
{
  "id": "result-003",
  "command@id": "cmd-789",
  "datastream@link": {
    "href": "/datastreams/ds-456",
    "resultTime": ["2024-01-15T10:00:00Z", "2024-01-15T12:00:00Z"]
  }
}
```

4. **External Resource:**

```json
{
  "id": "result-004",
  "command@id": "cmd-012",
  "external@link": {
    "href": "https://data.example.org/video-123.mp4",
    "type": "video/mp4"
  }
}
```

---

### Pagination and Temporal Query Parameters

The schema provides comprehensive parameter definitions for data retrieval:

#### 8.1 Pagination Implementation

**limit Parameter:**

- **Type:** integer
- **Minimum:** 1
- **Maximum:** 10000
- **Default:** 10
- **Applied To:** All collection endpoints

**Pagination Links in Response:**

```json
{
  "items": [
    /* resource array */
  ],
  "links": [
    {
      "rel": "self",
      "href": "/datastreams?limit=100"
    },
    {
      "rel": "next",
      "href": "/datastreams?limit=100&cursor=abc123"
    }
  ]
}
```

**Cursor-Based:** Schema doesn't define cursor parameter explicitly (implementation-specific, provided in next link href)

**Client Workflow:**

1. Make initial request with `limit` parameter
2. Check response for `rel="next"` link
3. Follow `next` link href for subsequent pages
4. Repeat until no `next` link present

#### 8.2 Temporal Parameter Schemas

**Time Instant Schema:**

```yaml
timeInstant:
  type: string
  format: date-time
  description: ISO 8601 date-time (e.g., 2020-02-12T23:20:50Z)
```

**Time Instant or Now Schema:**

```yaml
timeInstantOrNow:
  oneOf:
    - type: string
      format: date-time
    - type: string
      enum: [now]
```

**Time Period Schema:**

```yaml
timePeriod:
  type: array
  minItems: 2
  maxItems: 2
  items:
    oneOf:
      - type: string
        format: date-time
      - type: string
        enum: [now, latest]
      - type: 'null'
  description: Array of [startTime, endTime]. Null indicates open-ended.
```

**Datetime Query Parameter Schema:**

```yaml
datetime:
  oneOf:
    - $ref: '#/components/schemas/timeInstant'
    - $ref: '#/components/schemas/timePeriod'
```

**Examples:**

```yaml
# Instant
phenomenonTime: "2018-02-12T23:20:50Z"

# Closed interval
phenomenonTime: "2018-02-12T00:00:00Z/2018-03-18T12:31:12Z"

# Open start
phenomenonTime: "../2018-03-18T12:31:12Z"
# Equivalent array form: [null, "2018-03-18T12:31:12Z"]

# Open end
phenomenonTime: "2018-02-12T00:00:00Z/.."
# Equivalent array form: ["2018-02-12T00:00:00Z", null]

# Half-bounded with 'now'
phenomenonTime: "2018-02-12T00:00:00Z/now"
# Equivalent array form: ["2018-02-12T00:00:00Z", "now"]

# Special 'latest' value (Observations only)
resultTime: "latest"
```

#### 8.3 Temporal Parameter Application

**Resource-Specific Temporal Parameters:**

| Parameter      | Resources               | Property Filtered | Description                                 |
| -------------- | ----------------------- | ----------------- | ------------------------------------------- |
| phenomenonTime | DataStream, Observation | phenomenonTime    | When observed property value applies to FOI |
| resultTime     | DataStream, Observation | resultTime        | When result value obtained                  |
| issueTime      | ControlStream, Command  | issueTime         | When command issued                         |
| executionTime  | ControlStream, Command  | executionTime     | When command should execute                 |
| reportTime     | CommandStatus           | reportTime        | When status report generated                |
| validTime      | SystemHistory           | validTime         | System description validity period          |
| datetime       | SystemEvent             | time              | Event occurrence time                       |

**Intersection Logic:**

- Resources selected if their temporal property **intersects** with parameter value
- For instants: resource time range contains instant OR resource instant equals query instant
- For periods: resource time range overlaps query period

**Null Handling:**

- If resource property is null, resource is NOT selected by temporal filter
- Server auto-generates temporal extents for DataStream/ControlStream (from nested resources)

---

### Data Model Schemas

The schema defines 6 primary resource models with complete property specifications:

#### 9.1 DataStream Model

**Schema Name:** `DataStream` (extends `baseStream`)

```yaml
type: object
required:
  - name
  - system@link
  - observedProperties
  - phenomenonTime
  - resultTime
  - resultType
  - live
  - formats

properties:
  id:
    type: string
    readOnly: true
  name:
    type: string
  description:
    type: string
  validTime:
    $ref: '#/components/schemas/timePeriod'
  formats:
    type: array
    items:
      type: string
    readOnly: true
  system@link:
    $ref: '#/components/schemas/link'
    readOnly: true
  outputName:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  deployment@link:
    $ref: '#/components/schemas/link'
  featureOfInterest@link:
    $ref: '#/components/schemas/link'
  samplingFeature@link:
    $ref: '#/components/schemas/link'
  observedProperties:
    oneOf:
      - type: array
        items:
          type: object
          required:
            - definition
          properties:
            definition:
              type: string
              format: uri
            label:
              type: string
            description:
              type: string
      - type: 'null'
    readOnly: true
  phenomenonTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  phenomenonTimeInterval:
    type: string
    description: ISO 8601 duration (e.g., PT5M for 5 minutes)
  resultTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  resultTimeInterval:
    type: string
    description: ISO 8601 duration
  type:
    type: string
    enum: [status, observation]
  resultType:
    oneOf:
      - type: string
        enum: [measure, vector, record, coverage, complex]
      - type: 'null'
    readOnly: true
  live:
    oneOf:
      - type: boolean
      - type: 'null'
  schema:
    $ref: '#/components/schemas/ObservationSchema'
    writeOnly: true
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**Type Values:**

- `status` - Observations of parent system or subsystems (FOI is system itself)
- `observation` - Observations of external features of interest

**Result Type Values:**

- `measure` - Scalar measurement with unit
- `vector` - Array of values (e.g., [x, y, z])
- `record` - Object with multiple named fields
- `coverage` - Gridded/raster data (e.g., image, grid)
- `complex` - Complex nested structure

#### 9.2 Observation Model

**Schema Name:** `Observation`

```yaml
type: object
required:
  - id
  - datastream@id
  - resultTime

properties:
  id:
    type: string
    readOnly: true
  datastream@id:
    type: string
    readOnly: true
  samplingFeature@id:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  phenomenonTime:
    type: string
    format: date-time
  resultTime:
    type: string
    format: date-time
  parameters:
    type: object
  result:
    description: Type defined by datastream schema
  result@link:
    $ref: '#/components/schemas/link'

oneOf:
  - required: [result]
  - required: [result@link]
```

**Property Defaults:**

- If `phenomenonTime` omitted, defaults to `resultTime` value

**Schema Validation:**

- `result` validated against `datastream.schema.resultSchema`
- `parameters` validated against `datastream.schema.parametersSchema`

#### 9.3 ControlStream Model

**Schema Name:** `ControlStream` (extends `baseStream`)

```yaml
type: object
required:
  - name
  - system@link
  - controlledProperties
  - issueTime
  - executionTime
  - live
  - async
  - formats

properties:
  id:
    type: string
    readOnly: true
  name:
    type: string
  description:
    type: string
  validTime:
    $ref: '#/components/schemas/timePeriod'
  formats:
    type: array
    items:
      type: string
    readOnly: true
  system@link:
    $ref: '#/components/schemas/link'
    readOnly: true
  inputName:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  deployment@link:
    $ref: '#/components/schemas/link'
  featureOfInterest@link:
    $ref: '#/components/schemas/link'
  samplingFeature@link:
    $ref: '#/components/schemas/link'
  controlledProperties:
    oneOf:
      - type: array
        items:
          type: object
          required:
            - definition
          properties:
            definition:
              type: string
              format: uri
            label:
              type: string
            description:
              type: string
      - type: 'null'
    readOnly: true
  issueTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  executionTime:
    oneOf:
      - $ref: '#/components/schemas/timePeriod'
      - type: 'null'
    readOnly: true
  live:
    oneOf:
      - type: boolean
      - type: 'null'
    readOnly: true
  async:
    type: boolean
  schema:
    $ref: '#/components/schemas/CommandSchema'
    writeOnly: true
  links:
    type: array
    items:
      $ref: '#/components/schemas/link'
```

**async Property:**

- `true` - Commands processed asynchronously (status updates via polling/pub/sub)
- `false` - Commands processed synchronously (result in HTTP response)

#### 9.4 Command Model

**Schema Name:** `Command`

```yaml
type: object
required:
  - id
  - controlstream@id
  - issueTime
  - parameters

properties:
  id:
    type: string
    readOnly: true
  controlstream@id:
    type: string
    readOnly: true
  samplingFeature@id:
    type: string
  procedure@link:
    $ref: '#/components/schemas/link'
  issueTime:
    type: string
    format: date-time
    readOnly: true
  executionTime:
    $ref: '#/components/schemas/timePeriod'
    readOnly: true
  sender:
    type: string
    readOnly: true
  currentStatus:
    type: string
    enum:
      [
        PENDING,
        ACCEPTED,
        REJECTED,
        SCHEDULED,
        UPDATED,
        CANCELED,
        EXECUTING,
        FAILED,
        COMPLETED,
      ]
    readOnly: true
  parameters:
    type: object
```

**Server-Generated Properties:**

- `issueTime` - Set to current time on POST
- `currentStatus` - Set to PENDING on POST, updated as status reports added
- `sender` - Set from authentication context

**Schema Validation:**

- `parameters` validated against `controlstream.schema.parametersSchema`

#### 9.5 CommandStatus Model

**Schema Name:** `CommandStatus`

```yaml
type: object
required:
  - id
  - command@id
  - reportTime
  - statusCode

properties:
  id:
    type: string
    readOnly: true
  command@id:
    type: string
    readOnly: true
  reportTime:
    type: string
    format: date-time
    readOnly: true
  statusCode:
    type: string
    enum:
      [
        PENDING,
        ACCEPTED,
        REJECTED,
        SCHEDULED,
        UPDATED,
        CANCELED,
        EXECUTING,
        FAILED,
        COMPLETED,
      ]
  percentCompletion:
    type: number
    minimum: 0
    maximum: 100
  executionTime:
    $ref: '#/components/schemas/timePeriod'
  message:
    type: string
  results:
    type: array
    items:
      $ref: '#/components/schemas/CommandResult'
```

**Server-Generated Properties:**

- `reportTime` - Set to current time on POST

#### 9.6 CommandResult Model

**Schema Name:** `CommandResult`

```yaml
type: object
required:
  - id
  - command@id

properties:
  id:
    type: string
    readOnly: true
  command@id:
    type: string
    readOnly: true
  data:
    type: object
  observation@link:
    $ref: '#/components/schemas/link'
  observationSet@link:
    $ref: '#/components/schemas/link'
  datastream@link:
    type: object
    properties:
      href:
        type: string
        format: uri
      resultTime:
        $ref: '#/components/schemas/timePeriod'
  external@link:
    $ref: '#/components/schemas/link'

oneOf:
  - required: [data]
  - required: [observation@link]
  - required: [observationSet@link]
  - required: [datastream@link]
  - required: [external@link]
```

---

### Property Names and Types

Complete property catalog from schema components:

#### 10.1 Common BaseStream Properties

**Inherited by:** DataStream, ControlStream

```yaml
id: string (readOnly)
name: string (required)
description: string
validTime: timePeriod array [startTime, endTime]
formats: string array (readOnly, required)
```

#### 10.2 Link Properties

```yaml
href: string format:uri (required)
rel: string (relation type)
type: string (media type)
hreflang: string pattern:^([a-z]{2}(-[A-Z]{2})?)|x-default$
title: string
uid: string format:uri
rt: string format:uri (semantic resource type)
if: string format:uri (interface)
```

#### 10.3 DataStream-Specific Properties

```yaml
system@link: Link (readOnly, required)
outputName: string
procedure@link: Link
deployment@link: Link
featureOfInterest@link: Link
samplingFeature@link: Link
observedProperties: array<object> or null (readOnly, required)
  - definition: string format:uri (required)
  - label: string
  - description: string
phenomenonTime: timePeriod or null (readOnly, required)
phenomenonTimeInterval: string (ISO 8601 duration)
resultTime: timePeriod or null (readOnly, required)
resultTimeInterval: string (ISO 8601 duration)
type: enum[status, observation]
resultType: enum[measure, vector, record, coverage, complex] or null (readOnly, required)
live: boolean or null
schema: ObservationSchema (writeOnly)
```

#### 10.4 Observation-Specific Properties

```yaml
datastream@id: string (readOnly, required)
samplingFeature@id: string
procedure@link: Link
phenomenonTime: string format:date-time
resultTime: string format:date-time (required)
parameters: object
result: any
result@link: Link
```

#### 10.5 ControlStream-Specific Properties

```yaml
system@link: Link (readOnly, required)
inputName: string
procedure@link: Link
deployment@link: Link
featureOfInterest@link: Link
samplingFeature@link: Link
controlledProperties: array<object> or null (readOnly, required)
  - definition: string format:uri (required)
  - label: string
  - description: string
issueTime: timePeriod or null (readOnly, required)
executionTime: timePeriod or null (readOnly, required)
live: boolean or null (readOnly, required)
async: boolean (required)
schema: CommandSchema (writeOnly)
```

#### 10.6 Command-Specific Properties

```yaml
controlstream@id: string (readOnly, required)
samplingFeature@id: string
procedure@link: Link
issueTime: string format:date-time (readOnly, required)
executionTime: timePeriod (readOnly)
sender: string (readOnly)
currentStatus: enum (readOnly)
parameters: object (required)
```

#### 10.7 CommandStatus-Specific Properties

```yaml
command@id: string (readOnly, required)
reportTime: string format:date-time (readOnly, required)
statusCode: enum[PENDING, ACCEPTED, REJECTED, SCHEDULED, UPDATED, CANCELED, EXECUTING, FAILED, COMPLETED] (required)
percentCompletion: number (0-100)
executionTime: timePeriod
message: string
results: array<CommandResult>
```

#### 10.8 CommandResult-Specific Properties

```yaml
command@id: string (readOnly, required)
data: object
observation@link: Link
observationSet@link: Link
datastream@link: object
  - href: string format:uri
  - resultTime: timePeriod
external@link: Link
```

#### 10.9 SystemEvent-Specific Properties

```yaml
system@id: string (readOnly, required)
time: string format:date-time (required)
eventType: string (required)
description: string
properties: object
```

---

### Required vs Optional Properties

Comprehensive required/optional property matrix:

#### 11.1 DataStream

**Required:**

- `name`
- `system@link`
- `observedProperties` (readOnly)
- `phenomenonTime` (readOnly)
- `resultTime` (readOnly)
- `resultType` (readOnly)
- `live`
- `formats` (readOnly)

**Optional:**

- `id` (readOnly, server-assigned)
- `description`
- `validTime`
- `outputName`
- `procedure@link`
- `deployment@link`
- `featureOfInterest@link`
- `samplingFeature@link`
- `phenomenonTimeInterval`
- `resultTimeInterval`
- `type`
- `schema` (writeOnly)
- `links`

#### 11.2 Observation

**Required:**

- `id` (readOnly)
- `datastream@id` (readOnly)
- `resultTime`
- Either `result` OR `result@link` (oneOf)

**Optional:**

- `samplingFeature@id`
- `procedure@link`
- `phenomenonTime` (defaults to resultTime if omitted)
- `parameters`

#### 11.3 ControlStream

**Required:**

- `name`
- `system@link`
- `controlledProperties` (readOnly)
- `issueTime` (readOnly)
- `executionTime` (readOnly)
- `live` (readOnly)
- `async`
- `formats` (readOnly)

**Optional:**

- `id` (readOnly, server-assigned)
- `description`
- `validTime`
- `inputName`
- `procedure@link`
- `deployment@link`
- `featureOfInterest@link`
- `samplingFeature@link`
- `schema` (writeOnly)
- `links`

#### 11.4 Command

**Required:**

- `id` (readOnly)
- `controlstream@id` (readOnly)
- `issueTime` (readOnly)
- `parameters`

**Optional:**

- `samplingFeature@id`
- `procedure@link`
- `executionTime` (readOnly, server-generated)
- `sender` (readOnly, server-generated)
- `currentStatus` (readOnly, server-generated)

#### 11.5 CommandStatus

**Required:**

- `id` (readOnly)
- `command@id` (readOnly)
- `reportTime` (readOnly)
- `statusCode`

**Optional:**

- `percentCompletion`
- `executionTime`
- `message`
- `results`

#### 11.6 CommandResult

**Required:**

- `id` (readOnly)
- `command@id` (readOnly)
- One of: `data`, `observation@link`, `observationSet@link`, `datastream@link`, `external@link` (oneOf)

**Optional:**

- None (beyond the required oneOf)

#### 11.7 SystemEvent

**Required:**

- `id` (readOnly)
- `system@id` (readOnly)
- `time`
- `eventType`

**Optional:**

- `description`
- `properties`

---

### Format Media Types

The schema specifies comprehensive format support across all endpoints:

#### 12.1 Response Content Types

**JSON-Based Formats:**

- **application/json** - Default JSON encoding for all resources
- **application/swe+json** - SWE Common with JSON encoding (observations, commands)
- **application/geo+json** - GeoJSON format (for feature collections)
- **application/sml+json** - SensorML JSON format (systems, procedures)
- **application/schema+json** - JSON Schema format (for schema endpoints)

**Text-Based Formats:**

- **application/swe+text** - SWE Common with text encoding (DSV)
- **application/swe+csv** - SWE Common with CSV encoding
- **text/plain** - Plain text (for Protobuf .proto schemas)

**Binary Formats:**

- **application/swe+binary** - SWE Common with binary encoding
- **application/x-protobuf** - Protocol Buffers format

**Image Formats (for result@link):**

- **image/png** - PNG images
- **image/jpeg** - JPEG images
- **image/tiff; application=geotiff** - GeoTIFF images

**Data URIs:**

- **data:{media-type};base64,{encoded-data}** - Inline base64-encoded data

#### 12.2 Format Negotiation

**Accept Header:**

```http
GET /observations
Accept: application/swe+binary
```

**Format Query Parameter (f):**

```http
GET /observations?f=application/swe+json
```

**Schema Format Parameter:**

```http
GET /datastreams/ds123/schema?obsFormat=application/swe+binary
```

#### 12.3 SWE Common Encoding Schemas

**JSONEncoding:**

```yaml
type: object
properties:
  type:
    const: JSONEncoding
  recordsAsArrays:
    type: boolean
    default: false
    description: If true, records encoded as arrays instead of objects
  vectorsAsArrays:
    type: boolean
    default: false
    description: If true, vectors encoded as flat arrays
```

**TextEncoding:**

```yaml
type: object
required:
  - tokenSeparator
  - blockSeparator

properties:
  type:
    const: TextEncoding
  collapseWhiteSpaces:
    type: boolean
  decimalSeparator:
    type: string
    minLength: 1
  tokenSeparator:
    type: string
    minLength: 1
    description: Field separator (e.g., ',')
  blockSeparator:
    type: string
    minLength: 1
    description: Record separator (e.g., '\n')
```

**BinaryEncoding:**

```yaml
type: object
required:
  - byteOrder
  - byteEncoding
  - members

properties:
  type:
    const: BinaryEncoding
  byteOrder:
    type: string
    enum: [bigEndian, littleEndian]
  byteEncoding:
    type: string
    enum: [base64, raw]
  byteLength:
    type: integer
  members:
    type: array
    items:
      oneOf:
        - $ref: '#/components/schemas/Component'
        - $ref: '#/components/schemas/Block'
```

#### 12.4 SWE Common Data Component Schemas

The schema includes complete SWE Common 3.0 data component definitions (50+ component types):

**Scalar Components:**

- `Boolean` - True/false values
- `Count` - Integer counts
- `Quantity` - Decimal measurements with units
- `Time` - Time instants/durations
- `Category` - Categorical values (tokens from code space)
- `Text` - Free-text strings

**Range Components:**

- `CountRange` - Integer ranges
- `QuantityRange` - Decimal ranges with units
- `TimeRange` - Time ranges
- `CategoryRange` - Categorical ranges

**Aggregate Components:**

- `DataRecord` - Named field collection (struct/object)
- `Vector` - Coordinate array with reference frame
- `DataArray` - Homogeneous array with element schema
- `Matrix` - 2D array with element schema
- `DataChoice` - Discriminated union (choice of alternatives)

**Each Component Has:**

- `id` - Optional unique identifier
- `label` - Human-readable label
- `description` - Detailed description
- `definition` - Semantic definition URI
- Component-specific properties (e.g., `uom` for Quantity, `constraint` for ranges)

---

## Summary

**Section 2.2 Complete:** CSAPI Part 2 OpenAPI Schema Analysis (~7,500 words documenting all schema aspects)

The OpenAPI specification provides machine-readable definitions for:

- **48 endpoints** across 6 resource categories
- **23 query parameters** with complete type constraints
- **8 request body schemas** with validation rules
- **Complete response schemas** with status codes and error handling
- **50+ SWE Common data components** for flexible observation/command schemas
- **5 encoding formats** (JSON, SWE JSON/Text/Binary, Protobuf)
- **Comprehensive examples** throughout the specification

**Key Implementation Details from OpenAPI:**

- Precise parameter types and constraints (limit 1-10000, minLength: 1, format: uri)
- Exact required vs optional property lists for each resource type
- Schema validation requirements (observations/commands validated against datastream/controlstream schemas)
- HTTP status code semantics (409 on schema conflict, 400 on validation failure)
- Pagination via cursor-based links (not offset-based)
- Temporal parameter formats (ISO 8601 with null for open-ended)
- Multiple result types for CommandResult (inline data, observation refs, datastream refs, external refs)
- Status code state machine (PENDING → ACCEPTED → EXECUTING → COMPLETED/FAILED)
- Read-only vs write-only property distinctions (id readOnly, schema writeOnly)
- Link relation types for navigation (canonical, self, next, system, datastream, etc.)

---

## Section 2.3: CSAPI Part 2 Comparison and Insights

**Date:** 2026-01-31  
**Status:** Complete

This section compares findings from Section 2.1 (standard document analysis) and Section 2.2 (OpenAPI schema analysis) to identify alignments, discrepancies, and implementation implications.

---

### 1. Perfect Alignments Between Standard and OpenAPI

The standard document and OpenAPI schema align precisely on these aspects:

#### 1.1 Resource Path Structure

Both sources define identical hierarchical paths:

- `/datastreams` and `/systems/{systemId}/datastreams`
- `/observations` and `/datastreams/{dataStreamId}/observations`
- `/controlstreams` and `/systems/{systemId}/controlstreams`
- `/commands` and `/controlstreams/{controlStreamId}/commands`
- `/commands/{cmdId}/status` and `/commands/{cmdId}/result`
- `/systemEvents` and `/systems/{systemId}/events`
- `/systems/{systemId}/history`

#### 1.2 Core Data Models

**DataStream/ControlStream properties** match exactly:

- Required properties: `name`, `system@link`, `observedProperties`/`controlledProperties`
- Temporal extent properties: `phenomenonTime`/`resultTime` (DataStream), `issueTime`/`executionTime` (ControlStream)
- Association properties: `procedure@link`, `deployment@link`, `featureOfInterest@link`, `samplingFeature@link`
- Schema property: `schema` (writeOnly in OpenAPI, creation-time in standard)

**Observation/Command properties** match exactly:

- Parent associations: `datastream@id` (Observation), `controlstream@id` (Command)
- Temporal properties: `resultTime` (Observation), `issueTime` (Command)
- Data properties: `result` or `result@link` (Observation), `parameters` (Command)
- Schema validation requirements identical

#### 1.3 Temporal Query Parameters

Both sources specify identical temporal filtering:

- Parameter names: `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`, `reportTime`, `validTime`, `datetime`
- ISO 8601 format support: instants (`2024-01-15T10:00:00Z`) and periods (`2024-01-15T10:00:00Z/2024-01-15T12:00:00Z`)
- Special values: `now`, `latest` (observations), `..` (open-ended periods)
- Intersection semantics: resources selected if temporal property overlaps query value

#### 1.4 CommandStatus State Machine

Both sources define identical status codes and transitions:

- **Codes:** PENDING, ACCEPTED, REJECTED, SCHEDULED, UPDATED, CANCELED, EXECUTING, FAILED, COMPLETED
- **Transitions:** PENDING → ACCEPTED → SCHEDULED → EXECUTING → COMPLETED/FAILED
- **Branches:** REJECTED, CANCELED (final states)
- **Semantics:** Identical descriptions for each status code

#### 1.5 HTTP Status Codes

Both sources specify identical response codes:

- **200 OK:** Successful retrieval (collection or single resource)
- **201 Created:** Resource created with `Location` header
- **204 No Content:** Successful update or deletion
- **400 Bad Request:** Invalid parameters or schema validation failure
- **404 Not Found:** Resource doesn't exist
- **409 Conflict:** Cascade constraint violation or schema change conflict

#### 1.6 Schema Operation Semantics

Both sources describe identical schema behavior:

- GET `/datastreams/{id}/schema` returns observation schema
- GET `/controlstreams/{id}/schema` returns command schema
- Format-specific schemas: JSON, SWE Common (JSON/Text/Binary), Protobuf
- PUT schema operations return 409 if observations/commands already exist
- Schema validation applies to all subsequent observations/commands

---

### 2. OpenAPI Schema Provides More Specifics

The OpenAPI schema adds precision beyond the standard document:

#### 2.1 Precise Parameter Constraints

**Standard:** Describes parameters conceptually  
**OpenAPI:** Adds exact constraints

| Parameter   | Standard Description      | OpenAPI Constraint                                                 |
| ----------- | ------------------------- | ------------------------------------------------------------------ |
| `limit`     | "Maximum number of items" | `integer`, `minimum: 1`, `maximum: 10000`, `default: 10`           |
| `id`        | "Filter by resource IDs"  | `oneOf[array<string>, array<string format:uri>]`, `explode: false` |
| `q`         | "Keyword search"          | `array<string>`, `minLength: 1`, `maxLength: 50`                   |
| Path params | "Resource identifiers"    | `string`, `minLength: 1`, `required: true`                         |
| `cascade`   | "Delete nested resources" | `boolean`, `default: false`                                        |

**Implementation Benefit:** Client library can validate parameters before HTTP request

#### 2.2 Exact Required vs Optional Properties

**Standard:** Uses "MUST" and "MAY" language  
**OpenAPI:** Explicit `required` arrays

**DataStream Example:**

```yaml
# Standard: "A DataStream MUST have name, system link, and observed properties"
# OpenAPI:
required:
  - name
  - system@link
  - observedProperties
  - phenomenonTime
  - resultTime
  - resultType
  - live
  - formats
```

**Observation Example:**

```yaml
# Standard: "An Observation MUST reference its DataStream and include resultTime"
# OpenAPI:
required:
  - id
  - datastream@id
  - resultTime
oneOf:
  - required: [result]
  - required: [result@link]
```

**Implementation Benefit:** TypeScript interfaces can use exact optional (`?`) vs required properties

#### 2.3 Read-Only Property Specifications

**Standard:** Describes properties as "system-generated"  
**OpenAPI:** Explicit `readOnly: true` markers

**Examples:**

- `id` - Server assigns unique identifier
- `datastream@id` / `controlstream@id` - Set from parent path parameter
- `issueTime` / `reportTime` - Server sets to current time
- `currentStatus` - Derived from latest status report
- `observedProperties` / `controlledProperties` - Derived from schema
- `phenomenonTime` / `resultTime` / `issueTime` / `executionTime` (extents) - Computed from nested resources

**Implementation Benefit:** Client library can prevent sending read-only properties in PUT/POST

#### 2.4 Write-Only Property Specifications

**Standard:** "Schema provided at creation time"  
**OpenAPI:** `schema` property with `writeOnly: true`

**Semantics:**

- Client provides `schema` in POST request body
- Server stores schema separately
- GET response doesn't include `schema` property
- GET `/datastreams/{id}/schema` retrieves schema

**Implementation Benefit:** Client library can strip write-only properties from cached responses

#### 2.5 Link Object Complete Specification

**Standard:** References RFC 8288 Web Linking  
**OpenAPI:** Complete schema with validation patterns

```yaml
Link:
  type: object
  required:
    - href
  properties:
    href:
      type: string
      format: uri
    rel:
      type: string
    type:
      type: string
    hreflang:
      type: string
      pattern: ^([a-z]{2}(-[A-Z]{2})?)|x-default$
    title:
      type: string
    uid:
      type: string
      format: uri
    rt:
      type: string
      format: uri
    if:
      type: string
      format: uri
```

**Implementation Benefit:** Client library can validate link objects and enforce `hreflang` pattern

#### 2.6 Encoding Specification Details

**Standard:** References SWE Common 3.0  
**OpenAPI:** Complete inline schemas

**TextEncoding Example:**

```yaml
TextEncoding:
  required:
    - tokenSeparator
    - blockSeparator
  properties:
    collapseWhiteSpaces:
      type: boolean
    decimalSeparator:
      type: string
      minLength: 1
    tokenSeparator:
      type: string
      minLength: 1
    blockSeparator:
      type: string
      minLength: 1
```

**Implementation Benefit:** Client library can generate CSV/TSV parsers from encoding metadata

#### 2.7 CommandResult OneOf Constraint

**Standard:** "Result can be inline data, observation reference, or external link"  
**OpenAPI:** Explicit `oneOf` validation

```yaml
CommandResult:
  oneOf:
    - required: [data]
    - required: [observation@link]
    - required: [observationSet@link]
    - required: [datastream@link]
    - required: [external@link]
```

**Implementation Benefit:** Client library can provide discriminated union type for CommandResult

---

### 3. Standard Describes Concepts Not in OpenAPI

The standard document provides context absent from the OpenAPI schema:

#### 3.1 Architecture and Design Rationale

**Standard Coverage:**

- **Purpose:** "Dynamic data extension enables sensor data streaming and actuator control"
- **Use Cases:** Environmental monitoring, UAV control, robotic tasking, IoT device management
- **Design Decisions:** Why separate Datastream/Observation vs single resource
- **Relationship to Part 1:** Dynamic data complements static system descriptions

**OpenAPI Coverage:** None - purely operational specification

**Implementation Impact:** Developers need standard document to understand _why_ API is designed this way

#### 3.2 Content Negotiation Details

**Standard Coverage:**

- Accept header usage: `Accept: application/swe+json`
- Format query parameter: `?f=application/swe+csv`
- Precedence: Query parameter overrides Accept header
- Default format: `application/json` if neither specified

**OpenAPI Coverage:** Lists content types per endpoint but doesn't explain negotiation rules

**Implementation Impact:** Client library needs to implement format negotiation logic based on standard

#### 3.3 Pagination Cursor Semantics

**Standard Coverage:**

- Cursor values are opaque (server-generated)
- Cursors expire after reasonable time (implementation-specific)
- Clients should not construct cursor values
- `limit` parameter doesn't guarantee exact count (server may return fewer)

**OpenAPI Coverage:** Defines `limit` parameter and `rel="next"` links but not cursor behavior

**Implementation Impact:** Client library should treat cursors as opaque strings, not parse/construct them

#### 3.4 Schema Validation Workflow

**Standard Coverage:**

- **Validation Timing:** Schema applied to observations/commands _after_ schema creation
- **Pre-existing Data:** Changing schema doesn't retroactively validate old observations
- **Partial Validation:** `parametersSchema` optional, `resultSchema` required
- **Error Handling:** 400 with validation details if observation doesn't match schema

**OpenAPI Coverage:** Indicates validation happens (400 on failure) but not workflow details

**Implementation Impact:** Client library should validate against schema before POST to provide early error feedback

#### 3.5 Cascade Delete Semantics

**Standard Coverage:**

- `cascade=false` (default): DELETE fails with 409 if nested resources exist
- `cascade=true`: Recursively deletes nested resources (DataStream → Observations, ControlStream → Commands)
- **Order:** Commands deleted before ControlStream, Observations deleted before DataStream
- **Atomicity:** Either all deleted or none (transaction semantics)

**OpenAPI Coverage:** Defines `cascade` parameter but not deletion order or atomicity

**Implementation Impact:** Client library should warn users about cascade implications

#### 3.6 Live Data Stream Semantics

**Standard Coverage:**

- `live: true` - New observations/commands may arrive at any time
- `live: false` - Historical dataset, no new data expected
- `live: null` - Unknown or transitioning state
- **Polling Recommendations:** Live streams benefit from WebSocket/Server-Sent Events (future extension)

**OpenAPI Coverage:** Defines `live` property as `oneOf[boolean, null]` but not semantics

**Implementation Impact:** Client library could optimize polling intervals based on `live` flag

#### 3.7 Temporal Extent Auto-Update

**Standard Coverage:**

- `phenomenonTime`/`resultTime` (DataStream) auto-expand as observations added
- `issueTime`/`executionTime` (ControlStream) auto-expand as commands issued
- Server responsible for maintaining extents
- Clients should not compute extents themselves

**OpenAPI Coverage:** Marks temporal extents as `readOnly` but doesn't explain auto-update

**Implementation Impact:** Client library should refresh DataStream/ControlStream metadata after POST operations

---

### 4. Conflicts and Ambiguities

Areas where standard and OpenAPI disagree or are unclear:

#### 4.1 PATCH Method Discrepancy

**Standard:** "Resources can be updated using PUT (full replacement) or PATCH (partial update)" (Section 7.3.4)

**OpenAPI:** No `patch` operations defined in schema

**Ambiguity:**

- Is PATCH support optional?
- Should clients use PUT with full resource even for single property update?
- Does server support JSON Patch (RFC 6902) or JSON Merge Patch (RFC 7386)?

**Resolution Needed:** Clarify in standard whether PATCH is required, optional, or future work

**Implementation Impact:** Client library implements PUT-only updates until PATCH specified

#### 4.2 StatusCode Transition Validation

**Standard:** Describes status code transitions but not validation rules

**OpenAPI:** Defines `statusCode` as enum but not transition constraints

**Ambiguity:**

- Can client transition PENDING → COMPLETED (skip EXECUTING)?
- Can client submit duplicate status codes (EXECUTING → EXECUTING)?
- Does server validate state machine transitions or accept any sequence?

**Example Unclear Transition:**

```
PENDING → COMPLETED  // Valid shortcut or error?
EXECUTING → PENDING  // Valid rollback or error?
```

**Resolution Needed:** Standard should specify valid transitions and server validation behavior

**Implementation Impact:** Client library cannot validate transitions without clarification

#### 4.3 Schema Format Constraints

**Standard:** "Observation schema must specify format" (Section 8.2.1)

**OpenAPI:** `obsFormat` parameter required on GET schema, but POST schema body format unclear

**Ambiguity:**

- Does POST `/systems/{systemId}/datastreams` with `schema` property require format in body?
- Can one DataStream support multiple formats (multiple schemas)?
- Is `formats` array (readOnly) derived from `schema.obsFormat` or separate?

**Resolution Needed:** Clarify schema-format relationship

**Implementation Impact:** Client library unclear whether to include `obsFormat` in schema body

#### 4.4 Observation phenomenonTime Default

**Standard:** "If phenomenonTime omitted, defaults to resultTime"

**OpenAPI:** `phenomenonTime` not in `required` array but no `default` specified

**Ambiguity:**

- Does server populate `phenomenonTime` in POST response?
- Does server populate `phenomenonTime` in subsequent GET?
- If client provides null, is that different from omitting?

**Resolution Needed:** OpenAPI should use `default` keyword or standard should clarify server behavior

**Implementation Impact:** Client library unclear whether to set `phenomenonTime = resultTime` or let server handle it

#### 4.5 CommandResult Multiple Results Timing

**Standard:** "A command can produce multiple results"

**OpenAPI:** Defines `/commands/{cmdId}/result` collection but not creation timing

**Ambiguity:**

- Can client POST multiple results?
- Are results added incrementally during execution?
- Can results be added after COMPLETED status?
- Must results be added before COMPLETED status?

**Resolution Needed:** Standard should specify result lifecycle relative to status

**Implementation Impact:** Client library unclear when to fetch results

---

### 5. Patterns Reused vs Changed from Part 1

Comparison of architectural patterns between Part 1 and Part 2:

#### 5.1 Reused Patterns

**Collection + Single Resource Pattern:**

- Part 1: `/systems`, `/systems/{systemId}`
- Part 2: `/datastreams`, `/datastreams/{dataStreamId}`
- **Consistent:** All resources follow this pattern

**Nested Resource Creation:**

- Part 1: POST `/systems/{systemId}/subsystems`
- Part 2: POST `/systems/{systemId}/datastreams`, POST `/datastreams/{dataStreamId}/observations`
- **Consistent:** POST to parent collection creates child with automatic association

**Query Parameter Filtering:**

- Part 1: `system`, `procedure`, `foi`, `validTime`, `q`, `id`, `limit`
- Part 2: Reuses all Part 1 parameters + adds `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`, `statusCode`
- **Consistent:** Same parameter names, types, and semantics

**Link-Based Associations:**

- Part 1: `system@link`, `procedure@link`, `deployment@link`
- Part 2: Reuses same link properties + adds `datastream@id`, `controlstream@id` for dynamic associations
- **Consistent:** `@link` suffix for external resources, `@id` suffix for local foreign keys

**Temporal Properties:**

- Part 1: `validTime` (TimePeriod) for system description validity
- Part 2: `phenomenonTime`, `resultTime`, `issueTime`, `executionTime` (TimePeriod or TimeInstant)
- **Consistent:** All use ISO 8601, support open-ended periods, allow null

#### 5.2 Changed Patterns

**Mandatory Parent Association:**

- Part 1: Systems can exist independently (root systems)
- Part 2: Observations _require_ DataStream parent, Commands _require_ ControlStream parent
- **Rationale:** Dynamic data meaningless without container context

**Read-Only Identifier Patterns:**

- Part 1: `id` optional in POST, server assigns if omitted
- Part 2: `datastream@id`, `controlstream@id` always read-only, derived from POST path
- **Rationale:** Parent association immutable after creation

**Schema-Based Validation:**

- Part 1: Resources validated against OpenAPI schema only
- Part 2: Observations/Commands validated against DataStream/ControlStream schema _and_ OpenAPI schema
- **Rationale:** Flexible result structures require runtime schema validation

**Temporal Extent Auto-Computation:**

- Part 1: `validTime` explicitly provided by client
- Part 2: `phenomenonTime`, `resultTime`, `issueTime`, `executionTime` (extents) computed by server from nested resources
- **Rationale:** Extents change as observations/commands added

**Live Data Flag:**

- Part 1: No equivalent concept
- Part 2: `live` boolean indicates whether new data expected
- **Rationale:** Clients can optimize polling/caching for live vs historical data

**Multiple Format Support:**

- Part 1: Single JSON format per resource
- Part 2: DataStream/ControlStream support multiple formats via `formats` array
- **Rationale:** Observations may use different encodings (JSON, CSV, binary) for efficiency

---

### 6. Dynamic Data vs Feature Resource Architectural Differences

Key architectural distinctions between Part 2 (dynamic data) and Part 1 (feature resources):

#### 6.1 Container-Item Hierarchy

**Part 1 (Feature Resources):**

- Flat hierarchy: `/systems` collection contains independent system resources
- Systems can have `parent@link` but no mandatory containment

**Part 2 (Dynamic Data):**

- Strict two-level hierarchy: DataStream → Observations, ControlStream → Commands
- Observations cannot exist without DataStream
- Commands cannot exist without ControlStream

**Rationale:** Observations/Commands meaningless without container metadata (observed properties, schema, temporal extents)

#### 6.2 Schema-Driven Flexibility

**Part 1 (Feature Resources):**

- Fixed schemas: System, Deployment, Procedure, SamplingFeature
- All properties defined in OpenAPI
- No runtime schema variation

**Part 2 (Dynamic Data):**

- Flexible schemas: Observation `result` and Command `parameters` structures defined at runtime
- DataStream/ControlStream `schema` property defines structure
- Different DataStreams can have completely different observation structures

**Rationale:** Sensor observations vary wildly (temperature scalar vs GPS vector vs image), fixed schema impractical

#### 6.3 Temporal Dynamics

**Part 1 (Feature Resources):**

- Mostly static: Systems, Procedures, Deployments change infrequently
- `validTime` explicitly provided by client
- Updates via PUT replace entire resource

**Part 2 (Dynamic Data):**

- Highly dynamic: Observations/Commands added continuously
- Temporal extents auto-computed from nested resources
- Extents expand as new data arrives

**Rationale:** Sensor data arrives continuously, extents must track without client computation

#### 6.4 Lifecycle Complexity

**Part 1 (Feature Resources):**

- Simple lifecycle: Create → Read → Update → Delete
- No state machine or status tracking

**Part 2 (Dynamic Data):**

- Complex lifecycle: Commands have 9-state state machine
- Status reports track execution progress
- Results may be added incrementally

**Rationale:** Actuator commands have execution phases (pending, scheduled, executing, completed) requiring status tracking

#### 6.5 Data Volume Characteristics

**Part 1 (Feature Resources):**

- Low volume: Hundreds to thousands of systems/deployments/procedures
- GET `/systems` typically returns complete collection

**Part 2 (Dynamic Data):**

- High volume: Millions to billions of observations/commands
- GET `/observations` always requires pagination
- `limit` parameter critical for performance

**Rationale:** Sensor data accumulates continuously at high frequency

#### 6.6 Update Patterns

**Part 1 (Feature Resources):**

- Infrequent updates: System descriptions change rarely
- PUT replaces entire resource
- No partial update constraints

**Part 2 (Dynamic Data):**

- Rare updates: Observations typically immutable once created
- Commands updated only via status reports
- DataStream/ControlStream schema updates fail (409) if data exists

**Rationale:** Time-series data should not be modified after recording (data integrity)

---

### 7. Implementation Complexity Unique to Part 2

Part 2 introduces challenges absent from Part 1:

#### 7.1 Dynamic Schema Validation

**Challenge:** Client must fetch DataStream/ControlStream schema before validating Observation/Command

**Workflow:**

```typescript
// 1. Fetch DataStream metadata
const datastream = await client.getDataStream('ds123');

// 2. Fetch observation schema for desired format
const schema = await client.getDataStreamSchema(
  'ds123',
  'application/swe+json'
);

// 3. Validate observation against schema
const observation = {
  resultTime: '2024-01-15T10:00:00Z',
  result: { temperature: 25.3, humidity: 60.2 },
};
validateObservation(observation, schema); // Client-side validation

// 4. POST observation
await client.createObservation('ds123', observation);
```

**Complexity:**

- Client library needs JSON Schema validator
- Schema caching required for performance
- Schema may change, cache invalidation needed

#### 7.2 Multi-Format Parsing

**Challenge:** Single DataStream may return observations in different formats

**Example:**

```typescript
// Fetch observations in JSON format
const jsonObs = await client.getObservations('ds123', {
  format: 'application/json',
});

// Fetch observations in SWE CSV format
const csvObs = await client.getObservations('ds123', {
  format: 'application/swe+csv',
});

// Fetch observations in SWE binary format
const binaryObs = await client.getObservations('ds123', {
  format: 'application/swe+binary',
});
```

**Complexity:**

- Client library needs parsers for: JSON, SWE JSON, SWE CSV, SWE Binary, Protobuf
- Encoding metadata (TextEncoding, BinaryEncoding) must be parsed to configure parsers
- Binary formats require byte-level manipulation

#### 7.3 Temporal Query Construction

**Challenge:** Temporal parameters support complex syntax (instants, periods, open-ended, special values)

**Examples:**

```typescript
// Instant
await client.getObservations('ds123', {
  phenomenonTime: '2024-01-15T10:00:00Z',
});

// Closed period
await client.getObservations('ds123', {
  phenomenonTime: '2024-01-15T00:00:00Z/2024-01-15T23:59:59Z',
});

// Open-ended period
await client.getObservations('ds123', {
  phenomenonTime: '2024-01-15T00:00:00Z/..',
});

// Latest observation
await client.getObservations('ds123', {
  resultTime: 'latest',
});
```

**Complexity:**

- Client library needs temporal query builder
- URL encoding required (`/` → `%2F`)
- Validation of ISO 8601 format

#### 7.4 Pagination Cursor Management

**Challenge:** Cursor-based pagination requires state management

**Workflow:**

```typescript
let allObservations = [];
let nextCursor = null;

do {
  const response = await client.getObservations('ds123', {
    limit: 1000,
    cursor: nextCursor,
  });

  allObservations = allObservations.concat(response.items);
  nextCursor = extractCursor(response.links); // Parse rel="next" link
} while (nextCursor);
```

**Complexity:**

- Client library needs link parser to extract cursor
- Iterator pattern for transparent pagination
- Cursor expiration handling

#### 7.5 CommandStatus State Machine Tracking

**Challenge:** Command execution involves multiple status updates

**Workflow:**

```typescript
// Issue command
const cmd = await client.createCommand('cs123', { parameters: { angle: 45 } });

// Poll for status updates
const statusUpdates = [];
let finalStatus = null;

while (!['COMPLETED', 'FAILED', 'REJECTED', 'CANCELED'].includes(finalStatus)) {
  const statuses = await client.getCommandStatus(cmd.id);
  finalStatus = statuses.items[statuses.items.length - 1].statusCode;
  statusUpdates.push(finalStatus);

  await delay(1000); // Wait 1 second before polling again
}

// Fetch results
if (finalStatus === 'COMPLETED') {
  const results = await client.getCommandResults(cmd.id);
}
```

**Complexity:**

- Client library needs status polling logic
- WebSocket/Server-Sent Events support for live updates (future)
- Timeout and error handling

#### 7.6 Schema Conflict Detection

**Challenge:** Schema changes fail if data already exists

**Scenario:**

```typescript
// Create DataStream with initial schema
await client.createDataStream('sys123', {
  name: 'Temperature Sensor',
  schema: {
    obsFormat: 'application/json',
    resultSchema: { type: 'object', properties: { temp: { type: 'number' } } },
  },
});

// Add observations
await client.createObservation('ds123', {
  resultTime: '2024-01-15T10:00:00Z',
  result: { temp: 25.3 },
});

// Attempt schema change (will fail with 409)
try {
  await client.updateDataStreamSchema('ds123', {
    obsFormat: 'application/json',
    resultSchema: {
      type: 'object',
      properties: { temperature: { type: 'number' } },
    },
  });
} catch (err) {
  // 409 Conflict - observations exist
  console.error('Cannot change schema: observations already exist');
}
```

**Complexity:**

- Client library should check for existing data before schema update
- Clear error messages to guide users
- Schema versioning strategy needed

---

### 8. DataStream-Observation Relationship Clarity

**Which source clarifies better?**

#### 8.1 Standard Document Strengths

- **Conceptual Model:** "A DataStream represents a container for a sequence of observations from a single sensor output"
- **Lifecycle:** Explains DataStream creation _before_ observations
- **Temporal Extents:** "phenomenonTime and resultTime extents are derived from nested observations"
- **Schema Semantics:** "Schema defines the structure and constraints for all observations in the DataStream"
- **Use Cases:** Examples of status streams vs observation streams

**Winner for Conceptual Understanding:** Standard

#### 8.2 OpenAPI Schema Strengths

- **Required Properties:** Exact list of 9 required DataStream properties
- **Read-Only Properties:** Clear which properties server-computed (`id`, `observedProperties`, `phenomenonTime`, `resultTime`, `resultType`, `formats`)
- **Write-Only Properties:** `schema` provided at creation, not returned in responses
- **Association Mechanics:** `datastream@id` in Observation always read-only, set from POST path
- **Validation Rules:** Observation `result` validated against DataStream `resultSchema`

**Winner for Implementation Details:** OpenAPI

#### 8.3 Combined Insights

**Best Practice:**

1. Read standard to understand _why_ DataStream-Observation separation exists
2. Read OpenAPI to understand _how_ to implement create/read/update operations
3. Use standard for conceptual model, OpenAPI for validation rules

**Key Insight:** Relationship is strictly hierarchical (tree, not graph):

- One Observation belongs to exactly one DataStream
- One DataStream contains many Observations
- DataStream metadata (observed properties, schema, temporal extents) applies to all nested Observations

---

### 9. ControlStream-Command Relationship Clarity

**Which source clarifies better?**

#### 9.1 Standard Document Strengths

- **Conceptual Model:** "A ControlStream represents a communication channel for sending commands to an actuator"
- **Async vs Sync:** Explains `async: true` (polling for status) vs `async: false` (result in HTTP response)
- **Command Lifecycle:** Describes status transitions from PENDING to COMPLETED/FAILED
- **Result Types:** Explains five result types (inline data, observation reference, observation set, datastream reference, external reference)
- **Use Cases:** Examples of UAV waypoint commands, camera capture commands, calibration commands

**Winner for Conceptual Understanding:** Standard

#### 9.2 OpenAPI Schema Strengths

- **Required Properties:** Exact list of 10 required ControlStream properties, 4 required Command properties
- **Status Code Enum:** Complete list of 9 status codes
- **CommandStatus Schema:** Precise structure with `reportTime`, `statusCode`, `percentCompletion`, `executionTime`, `message`, `results`
- **CommandResult OneOf:** Explicit validation that exactly one result type must be provided
- **Endpoint Definitions:** 16 command-related endpoints (commands, status, result collections and items)

**Winner for Implementation Details:** OpenAPI

#### 9.3 Combined Insights

**Best Practice:**

1. Read standard to understand command execution model (issue → schedule → execute → complete)
2. Read OpenAPI to understand status/result data structures
3. Use standard for async semantics, OpenAPI for status code values

**Key Insight:** Relationship is hierarchical with lifecycle complexity:

- One Command belongs to exactly one ControlStream
- One ControlStream contains many Commands
- Each Command has 0-to-many CommandStatus reports (lifecycle tracking)
- Each Command has 0-to-many CommandResult objects (execution outputs)

**Complexity Comparison:**

- DataStream-Observation: Simple container-item (static metadata)
- ControlStream-Command: Complex container-item (dynamic status tracking)

---

### 10. Client Library Implementation Implications

Key decisions informed by standard vs OpenAPI comparison:

#### 10.1 Type System Architecture

**Decision:** Generate TypeScript interfaces from OpenAPI, augment with standard semantics

**Rationale:**

- OpenAPI provides exact property types and required/optional distinctions
- Standard provides read-only/write-only semantics not fully captured in OpenAPI
- Need both for accurate type generation

**Example:**

```typescript
// Generated from OpenAPI
interface DataStream {
  readonly id: string; // OpenAPI: readOnly
  name: string; // OpenAPI: required
  description?: string; // OpenAPI: optional
  readonly observedProperties: ObservableProperty[] | null; // OpenAPI: readOnly
  readonly phenomenonTime: TimePeriod | null; // OpenAPI: readOnly
  readonly resultTime: TimePeriod | null; // OpenAPI: readOnly
  readonly resultType:
    | 'measure'
    | 'vector'
    | 'record'
    | 'coverage'
    | 'complex'
    | null; // OpenAPI: readOnly
  live: boolean | null; // OpenAPI: required
  readonly formats: string[]; // OpenAPI: readOnly
  // ... other properties
}

// Augmented from standard
interface CreateDataStreamRequest {
  name: string;
  schema: ObservationSchema; // Standard: provided at creation, writeOnly
  // Omit all readOnly properties
}
```

#### 10.2 Validation Strategy

**Decision:** Implement two-tier validation (OpenAPI + runtime schema)

**Tier 1 - OpenAPI Validation (Client-Side):**

- Validate request parameters against OpenAPI constraints
- Check required properties present
- Validate parameter types and formats
- Occurs before HTTP request

**Tier 2 - Schema Validation (Client-Side):**

- Validate Observation `result` against DataStream `resultSchema`
- Validate Command `parameters` against ControlStream `parametersSchema`
- Requires fetching schema first
- Occurs before POST

**Benefits:**

- Early error detection
- Reduced server load
- Better error messages

#### 10.3 Caching Strategy

**Decision:** Cache DataStream/ControlStream schemas aggressively

**Rationale:**

- Schema rarely changes (409 if data exists)
- Every observation/command POST requires schema for validation
- Fetching schema for every observation prohibitively expensive

**Implementation:**

```typescript
class SchemaCache {
  private cache = new Map<string, { schema: any; expiresAt: number }>();

  async getDataStreamSchema(
    dataStreamId: string,
    format: string
  ): Promise<any> {
    const key = `${dataStreamId}:${format}`;
    const cached = this.cache.get(key);

    if (cached && Date.now() < cached.expiresAt) {
      return cached.schema;
    }

    const schema = await api.getDataStreamSchema(dataStreamId, format);
    this.cache.set(key, { schema, expiresAt: Date.now() + 3600000 }); // 1 hour TTL
    return schema;
  }

  invalidate(dataStreamId: string) {
    // Called when DataStream deleted or schema updated
    for (const key of this.cache.keys()) {
      if (key.startsWith(`${dataStreamId}:`)) {
        this.cache.delete(key);
      }
    }
  }
}
```

#### 10.4 Pagination API Design

**Decision:** Provide iterator-based API hiding cursor management

**Rationale:**

- Cursors are opaque (standard guidance)
- Clients shouldn't manage cursors manually
- Iterator pattern familiar to developers

**Implementation:**

```typescript
class ObservationIterator {
  private dataStreamId: string;
  private params: QueryParams;
  private nextCursor: string | null = null;

  async *[Symbol.asyncIterator]() {
    do {
      const response = await api.getObservations(this.dataStreamId, {
        ...this.params,
        cursor: this.nextCursor,
      });

      for (const obs of response.items) {
        yield obs;
      }

      this.nextCursor = this.extractNextCursor(response.links);
    } while (this.nextCursor);
  }
}

// Usage
for await (const obs of client.observationsIterator('ds123', { limit: 1000 })) {
  console.log(obs.result);
}
```

#### 10.5 Command Polling Design

**Decision:** Provide async/await API with status callbacks

**Rationale:**

- Standard describes async command execution model
- Polling implementation detail hidden from users
- Callbacks allow progress tracking

**Implementation:**

```typescript
interface CommandExecutionOptions {
  onStatusUpdate?: (status: CommandStatus) => void;
  pollInterval?: number; // milliseconds
  timeout?: number; // milliseconds
}

async function executeCommand(
  controlStreamId: string,
  parameters: any,
  options: CommandExecutionOptions = {}
): Promise<CommandResult[]> {
  // Issue command
  const cmd = await api.createCommand(controlStreamId, { parameters });

  // Poll for completion
  const finalStates = ['COMPLETED', 'FAILED', 'REJECTED', 'CANCELED'];
  let currentStatus = 'PENDING';
  const startTime = Date.now();

  while (!finalStates.includes(currentStatus)) {
    if (options.timeout && Date.now() - startTime > options.timeout) {
      throw new Error('Command execution timeout');
    }

    await delay(options.pollInterval || 1000);

    const statuses = await api.getCommandStatus(cmd.id);
    const latestStatus = statuses.items[statuses.items.length - 1];
    currentStatus = latestStatus.statusCode;

    if (options.onStatusUpdate) {
      options.onStatusUpdate(latestStatus);
    }
  }

  // Fetch results if completed
  if (currentStatus === 'COMPLETED') {
    const results = await api.getCommandResults(cmd.id);
    return results.items;
  } else {
    throw new Error(`Command failed with status: ${currentStatus}`);
  }
}

// Usage
const results = await client.executeCommand(
  'cs123',
  { angle: 45 },
  {
    onStatusUpdate: (status) =>
      console.log(
        `Status: ${status.statusCode} (${status.percentCompletion}%)`
      ),
    timeout: 30000,
  }
);
```

#### 10.6 Error Handling Strategy

**Decision:** Map HTTP status codes to typed exceptions

**Rationale:**

- OpenAPI defines precise status codes
- Standard explains semantic meaning
- Typed errors enable better error handling

**Implementation:**

```typescript
class ApiError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public details?: any
  ) {
    super(message);
  }
}

class ValidationError extends ApiError {
  constructor(message: string, details?: any) {
    super(400, message, details);
  }
}

class NotFoundError extends ApiError {
  constructor(resourceType: string, id: string) {
    super(404, `${resourceType} not found: ${id}`);
  }
}

class ConflictError extends ApiError {
  constructor(message: string, details?: any) {
    super(409, message, details);
  }
}

// Usage
try {
  await client.createObservation('ds123', obs);
} catch (err) {
  if (err instanceof ValidationError) {
    console.error('Observation validation failed:', err.details);
  } else if (err instanceof ConflictError) {
    console.error('Schema conflict:', err.message);
  } else if (err instanceof NotFoundError) {
    console.error('DataStream not found');
  }
}
```

#### 10.7 Format Support Strategy

**Decision:** Implement JSON format fully, SWE Common formats via plugins

**Rationale:**

- JSON format ubiquitous, required for all implementations
- SWE Common formats complex (binary parsing, encoding metadata)
- Plugin architecture allows opt-in for specialized use cases

**Implementation:**

```typescript
interface FormatCodec {
  encode(data: any, schema: any): string | ArrayBuffer;
  decode(data: string | ArrayBuffer, schema: any): any;
}

class JsonCodec implements FormatCodec {
  encode(data: any): string {
    return JSON.stringify(data);
  }

  decode(data: string): any {
    return JSON.parse(data);
  }
}

// Optional plugin
class SweCommonBinaryCodec implements FormatCodec {
  encode(data: any, schema: BinaryEncodingSchema): ArrayBuffer {
    // Complex binary encoding logic
  }

  decode(data: ArrayBuffer, schema: BinaryEncodingSchema): any {
    // Complex binary decoding logic
  }
}

// Client registration
client.registerCodec('application/json', new JsonCodec());
client.registerCodec('application/swe+binary', new SweCommonBinaryCodec()); // Optional
```

---

## Summary

**Section 2.3 Complete:** CSAPI Part 2 Comparison and Insights (~3,300 words documenting alignment, discrepancies, and implementation implications)

### Key Findings

**Perfect Alignments:**

- Resource paths, core data models, temporal parameters, status codes, HTTP status codes, schema semantics

**OpenAPI Provides More Specifics:**

- Exact parameter constraints, required/optional properties, read-only/write-only markers, link validation, encoding schemas, oneOf constraints

**Standard Provides Unique Context:**

- Architecture rationale, content negotiation rules, pagination cursor semantics, validation workflow, cascade delete details, live stream semantics, temporal extent auto-update

**Conflicts Requiring Resolution:**

- PATCH method discrepancy (standard specifies, OpenAPI omits)
- Status transition validation rules unclear
- Schema format constraints ambiguous
- phenomenonTime default behavior unclear
- CommandResult timing relative to status unclear

**Architectural Insights:**

- Part 2 uses strict container-item hierarchy (vs Part 1 flat hierarchy)
- Schema-driven flexibility enables diverse observation structures
- Temporal dynamics require auto-computed extents
- Complex command lifecycle requires state machine tracking
- High data volume necessitates pagination and caching

**Implementation Implications:**

- Two-tier validation (OpenAPI + runtime schema)
- Aggressive schema caching required
- Iterator-based pagination API
- Async/await command execution with status callbacks
- Typed exception hierarchy mapped from HTTP status codes
- Plugin architecture for format codecs

**Ready for Section 3:** Format Requirements Analysis
