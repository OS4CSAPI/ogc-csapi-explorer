# Section 7: Conformance and Capability Requirements

## Overview

This section documents all conformance classes defined in CSAPI Part 1 and Part 2, their requirements, detection mechanisms, and capability discovery patterns. Understanding conformance is critical for building client libraries that adapt to varying server capabilities and can detect which features are available at runtime.

**Key Objectives:**

- Document all conformance classes and their identifiers
- Define requirements for each conformance class
- Specify conformance detection via /conformance endpoint
- Define minimum viable CSAPI server configuration
- Document capability discovery at collection level
- Establish client library conformance checking patterns
- Define graceful degradation strategies

---

## Conformance Classes Overview

### Part 1: Core Resources (13 Conformance Classes)

| #    | Conformance Class     | Identifier                    | Prerequisite                                             | Mandatory    |
| ---- | --------------------- | ----------------------------- | -------------------------------------------------------- | ------------ |
| A.1  | Common                | `/conf/api-common`            | OGC API - Features Part 1, OGC API - Common Part 1       | Yes (always) |
| A.2  | System Features       | `/conf/system`                | `/conf/api-common`                                       | No\*         |
| A.3  | Subsystems            | `/conf/subsystem`             | `/conf/system`                                           | No           |
| A.4  | Deployment Features   | `/conf/deployment`            | `/conf/api-common`                                       | No\*         |
| A.5  | Subdeployments        | `/conf/subdeployment`         | `/conf/deployment`                                       | No           |
| A.6  | Procedure Features    | `/conf/procedure`             | `/conf/api-common`                                       | No\*         |
| A.7  | Sampling Features     | `/conf/sf`                    | `/conf/api-common`, `/conf/system`                       | No           |
| A.8  | Property Definitions  | `/conf/property`              | `/conf/api-common`                                       | No\*         |
| A.9  | Advanced Filtering    | `/conf/advanced-filtering`    | `/conf/api-common`                                       | No           |
| A.10 | Create/Replace/Delete | `/conf/create-replace-delete` | `/conf/api-common`, OGC API - Features Part 4            | No           |
| A.11 | Update                | `/conf/update`                | `/conf/create-replace-delete`, OGC API - Features Part 4 | No           |
| A.12 | GeoJSON Format        | `/conf/geojson`               | `/conf/api-common`, OGC API - Features Part 1 GeoJSON    | No†          |
| A.13 | SensorML Format       | `/conf/sensorml`              | `/conf/api-common`, SensorML 3.0 JSON                    | No†          |

**Notes:**

- \*At least ONE resource type must be implemented (System, Deployment, Procedure, or Property)
- †At least ONE encoding must be implemented (GeoJSON or SensorML)
- **No Core Class:** Standard explicitly states "There is no Core requirements class"

### Part 2: Dynamic Data (12 Conformance Classes)

| #    | Conformance Class          | Identifier                    | Prerequisite                                             | Mandatory    |
| ---- | -------------------------- | ----------------------------- | -------------------------------------------------------- | ------------ |
| A.1  | Common                     | `/conf/api-common`            | OGC API - Features Part 1                                | Yes (always) |
| A.2  | Datastreams & Observations | `/conf/datastream`            | `/conf/api-common`                                       | No\*         |
| A.3  | Control Streams & Commands | `/conf/controlstream`         | `/conf/api-common`                                       | No\*         |
| A.4  | Command Feasibility        | `/conf/feasibility`           | `/conf/controlstream`                                    | No           |
| A.5  | System Events              | `/conf/system-event`          | `/conf/api-common`, Part 1 `/conf/system`                | No           |
| A.6  | Advanced Filtering         | `/conf/advanced-filtering`    | Part 1 `/conf/advanced-filtering`                        | No           |
| A.7  | Create/Replace/Delete      | `/conf/create-replace-delete` | OGC API - Features Part 4                                | No           |
| A.8  | Update                     | `/conf/update`                | `/conf/create-replace-delete`, OGC API - Features Part 4 | No           |
| A.9  | JSON Encoding              | `/conf/json`                  | `/conf/api-common`                                       | Yes (always) |
| A.10 | SWE Common JSON Encoding   | `/conf/swecommon-json`        | `/conf/json`                                             | No           |
| A.11 | SWE Common Text Encoding   | `/conf/swecommon-text`        | `/conf/json`                                             | No           |
| A.12 | SWE Common Binary Encoding | `/conf/swecommon-binary`      | `/conf/json`                                             | No           |

**Notes:**

- \*At least ONE dynamic data type must be implemented (Datastreams OR Control Streams)
- JSON encoding is mandatory for all Part 2 servers
- SWE Common encodings are optional (additional formats)

---

## Minimum Viable Server Configurations

### Absolute Minimum (Part 1 Only)

**Configuration 1: Read-Only System Registry**

```
Required:
- Part 1: /conf/api-common
- Part 1: /conf/system
- Part 1: /conf/geojson OR /conf/sensorml

Optional:
- None

Capabilities:
- GET /systems
- GET /systems/{id}
- GET /collections/{id}/items (Systems)
```

**Configuration 2: Read-Only Deployment Registry**

```
Required:
- Part 1: /conf/api-common
- Part 1: /conf/deployment
- Part 1: /conf/geojson OR /conf/sensorml

Optional:
- None

Capabilities:
- GET /deployments
- GET /deployments/{id}
- GET /collections/{id}/items (Deployments)
```

### Minimum with CRUD (Part 1 Only)

**Configuration 3: Transactional System Registry**

```
Required:
- Part 1: /conf/api-common
- Part 1: /conf/system
- Part 1: /conf/geojson OR /conf/sensorml
- Part 1: /conf/create-replace-delete

Optional:
- Part 1: /conf/update (for PATCH)

Capabilities:
- All GET operations
- POST /systems (create)
- PUT /systems/{id} (replace)
- PATCH /systems/{id} (update, if /conf/update)
- DELETE /systems/{id}
```

### Minimum with Dynamic Data (Part 2)

**Configuration 4: Sensor Data Server**

```
Required:
- Part 1: /conf/api-common
- Part 1: /conf/system
- Part 1: /conf/geojson OR /conf/sensorml
- Part 2: /conf/api-common
- Part 2: /conf/datastream
- Part 2: /conf/json

Optional:
- Part 2: /conf/create-replace-delete (for data ingestion)
- Part 2: /conf/swecommon-json (binary-efficient format)

Capabilities:
- GET /systems, /systems/{id}
- GET /systems/{id}/datastreams
- GET /datastreams, /datastreams/{id}
- GET /datastreams/{id}/observations
- POST /datastreams/{id}/observations (if CRUD enabled)
```

**Configuration 5: Actuator Control Server**

```
Required:
- Part 1: /conf/api-common
- Part 1: /conf/system
- Part 1: /conf/geojson OR /conf/sensorml
- Part 2: /conf/api-common
- Part 2: /conf/controlstream
- Part 2: /conf/json

Optional:
- Part 2: /conf/create-replace-delete (for commanding)
- Part 2: /conf/feasibility (for pre-checking)

Capabilities:
- GET /systems, /systems/{id}
- GET /systems/{id}/controlstreams
- GET /controlstreams, /controlstreams/{id}
- GET /controlstreams/{id}/commands
- POST /controlstreams/{id}/commands (if CRUD enabled)
- GET /commands/{id}/status
- GET /commands/{id}/result
```

### Comprehensive Configuration

**Configuration 6: Full-Featured Server**

```
Required:
- Part 1: All conformance classes
- Part 2: All conformance classes

Capabilities:
- All resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties)
- All dynamic data (DataStreams, Observations, ControlStreams, Commands)
- Full CRUD (POST, PUT, PATCH, DELETE)
- Advanced filtering (30+ query parameters)
- Hierarchical navigation (subsystems, subdeployments with recursive)
- Multiple encodings (GeoJSON, SensorML, SWE Common JSON/Text/Binary)
- System events
- Command feasibility
```

---

## Conformance Class Details

### Part 1: A.1 Common

**Identifier:** `/conf/api-common`  
**Requirement Class:** `/req/api-common`  
**Target Type:** Web API

**Prerequisites:**

- OGC API – Features – Part 1: Core `/req/core`
- OGC API – Common – Part 1: Core `/req/core`
- OGC API – Common – Part 1: Landing Page `/req/landing-page`
- OGC API – Common – Part 1: JSON `/req/json`

**Requirements (3 total):**

1. **Resource IDs:** All resources MUST have local ID (Requirement 1)
2. **Unique Identifiers:** All resources MUST have UID as URI or URN (Requirement 2)
3. **DateTime Query:** Support `datetime` parameter applying to `validTime` (Requirement 3)

**Endpoints Required:**

- `/` - Landing page
- `/conformance` - Conformance declaration
- `/collections` - Collections metadata
- `/api` or `/api.html` or `/api.json` - API definition (OpenAPI)

**Key Capabilities:**

- Resource identification (local ID + UID)
- Temporal filtering via validTime
- JSON encoding for metadata

**Client Library Impact:**

- Must support conformance detection at `/conformance`
- Must handle both local ID and UID for resource identification
- Must support datetime parameter for temporal queries

---

### Part 1: A.2 System Features

**Identifier:** `/conf/system`  
**Requirement Class:** `/req/system`  
**Prerequisite:** `/conf/api-common`

**Requirements (5 total):**

1. System location MUST update when system moves (Requirement 4)
2. Systems accessible at canonical URL `/systems/{id}` (Requirement 5)
3. System resources endpoints support (Requirement 6)
4. Canonical endpoint `/systems` exists (Requirement 7)
5. At least one System collection exposed (Requirement 8)

**Endpoints Required:**

- `/systems` - List all systems
- `/systems/{id}` - Get single system
- `/collections` - Includes at least one collection with Systems
- `/collections/{id}/items` - Systems in collection

**Collections Required:**

- At least one collection with `featureType=sosa:System`

**Key Capabilities:**

- System resource CRUD (if create/replace/delete conformance implemented)
- System querying with filters (if advanced filtering implemented)
- Collection-based organization

**Client Library Impact:**

- `client.systems.list()` - Available
- `client.systems.get(id)` - Available
- `client.collections.get(id).items()` - May contain systems

---

### Part 1: A.3 Subsystems

**Identifier:** `/conf/subsystem`  
**Requirement Class:** `/req/subsystem`  
**Prerequisite:** `/conf/system`

**Requirements (5 total):**

1. Subsystems exposed at `/systems/{parentId}/subsystems` (Requirement 9)
2. `recursive` parameter supported (boolean) (Requirement 10)
3. Default behavior (recursive=false): direct subsystems only (Requirement 11)
4. With recursive=true: all nested subsystems at all levels (Requirement 12)
5. Recursive associations: subsystem resources include parent's (Requirement 13)

**Endpoints Required:**

- `/systems/{parentId}/subsystems` - List subsystems
- `/systems/{parentId}/subsystems?recursive=true` - List all descendants

**Key Capabilities:**

- Hierarchical system navigation
- Recursive queries (unlimited depth)
- Component/payload modeling

**Client Library Impact:**

- `client.systems.get(id).subsystems.list()` - Available
- `client.systems.get(id).subsystems.list({recursive: true})` - Available
- Unlimited nesting depth support required

---

### Part 1: A.4 Deployment Features

**Identifier:** `/conf/deployment`  
**Requirement Class:** `/req/deployment`  
**Prerequisite:** `/conf/api-common`

**Requirements (5 total):**

1. Deployments accessible at canonical URL `/deployments/{id}` (Requirement 14)
2. Deployment resources endpoints support (Requirement 15)
3. Canonical endpoint `/deployments` exists (Requirement 16)
4. Nested endpoint from systems `/systems/{sysId}/deployments` (Requirement 17)
5. At least one Deployment collection (Requirement 18)

**Endpoints Required:**

- `/deployments` - List all deployments
- `/deployments/{id}` - Get single deployment
- `/systems/{sysId}/deployments` - Deployments for system
- `/collections/{id}/items` - Deployments in collection

**Collections Required:**

- At least one collection with `featureType=sosa:Deployment`

**Key Capabilities:**

- Deployment resource CRUD
- System-deployment association (many-to-many)
- Temporal and spatial extent modeling

**Client Library Impact:**

- `client.deployments.list()` - Available
- `client.systems.get(id).deployments.list()` - Available
- Bidirectional navigation (system↔deployment)

---

### Part 1: A.5 Subdeployments

**Identifier:** `/conf/subdeployment`  
**Requirement Class:** `/req/subdeployment`  
**Prerequisite:** `/conf/deployment`

**Requirements (5 total):**

1. Subdeployments exposed at `/deployments/{parentId}/subdeployments` (Requirement 19)
2. `recursive` parameter supported (Requirement 20)
3. Default behavior: direct subdeployments only (Requirement 21)
4. With recursive=true: all nested subdeployments (Requirement 22)
5. Recursive associations for nested resources (Requirement 23)

**Endpoints Required:**

- `/deployments/{parentId}/subdeployments` - List subdeployments
- `/deployments/{parentId}/subdeployments?recursive=true` - All descendants

**Key Capabilities:**

- Hierarchical deployment navigation
- Multi-phase campaign modeling
- Geographic/temporal hierarchy

**Client Library Impact:**

- `client.deployments.get(id).subdeployments.list()` - Available
- `client.deployments.get(id).subdeployments.list({recursive: true})` - Available

---

### Part 1: A.6 Procedure Features

**Identifier:** `/conf/procedure`  
**Requirement Class:** `/req/procedure`  
**Prerequisite:** `/conf/api-common`

**Requirements (5 total):**

1. Procedures have NO location (Requirement 24)
2. Procedures accessible at canonical URL `/procedures/{id}` (Requirement 25)
3. Procedure resources endpoints support (Requirement 26)
4. Canonical endpoint `/procedures` exists (Requirement 27)
5. At least one Procedure collection (Requirement 28)

**Endpoints Required:**

- `/procedures` - List all procedures
- `/procedures/{id}` - Get single procedure
- `/collections/{id}/items` - Procedures in collection

**Collections Required:**

- At least one collection with `featureType=sosa:Procedure`

**Key Capabilities:**

- Procedure/datasheet management
- Type-instance relationship (Procedure→Systems)
- Methodology documentation

**Client Library Impact:**

- `client.procedures.list()` - Available
- Procedures are non-spatial (geometry = null)

---

### Part 1: A.7 Sampling Features

**Identifier:** `/conf/sf`  
**Requirement Class:** `/req/sf`  
**Prerequisites:** `/conf/api-common`, `/conf/system`

**Requirements (5 total):**

1. Sampling features accessible at `/samplingFeatures/{id}` (Requirement 29)
2. Sampling feature resources endpoints support (Requirement 30)
3. Canonical endpoint `/samplingFeatures` exists (Requirement 31)
4. Nested endpoint from systems `/systems/{sysId}/samplingFeatures` (Requirement 32)
5. At least one Sampling Feature collection (Requirement 33)

**Endpoints Required:**

- `/samplingFeatures` - List all sampling features
- `/samplingFeatures/{id}` - Get single sampling feature
- `/systems/{sysId}/samplingFeatures` - Sampling features for system
- `/collections/{id}/items` - Sampling features in collection

**Collections Required:**

- At least one collection with `featureType=sosa:Sample`

**Key Capabilities:**

- Sampling strategy modeling
- FOI vs sampling feature distinction
- Sub-sampling hierarchy

**Client Library Impact:**

- `client.samplingFeatures.list()` - Available
- `client.systems.get(id).samplingFeatures.list()` - Available
- Must handle sampledFeature (ultimate FOI) vs sampleOf (sub-sampling)

---

### Part 1: A.8 Property Definitions

**Identifier:** `/conf/property`  
**Requirement Class:** `/req/property`  
**Prerequisite:** `/conf/api-common`

**Requirements (4 total):**

1. Properties accessible at `/properties/{id}` (Requirement 34)
2. Property resources endpoints support (Requirement 35)
3. Canonical endpoint `/properties` exists (Requirement 36)
4. At least one Property collection (Requirement 37)

**Endpoints Required:**

- `/properties` - List all properties
- `/properties/{id}` - Get single property
- `/collections/{id}/items` - Properties in collection

**Collections Required:**

- At least one collection with `itemType=sosa:Property`

**Key Capabilities:**

- Observable/controllable property definitions
- Property derivation hierarchy (baseProperty)
- Property-object type association

**Client Library Impact:**

- `client.properties.list()` - Available
- Properties are non-spatial resources (not Features)
- Terminology: "resources" not "features"

---

### Part 1: A.9 Advanced Filtering

**Identifier:** `/conf/advanced-filtering`  
**Requirement Class:** `/req/advanced-filtering`  
**Prerequisite:** `/conf/api-common`

**Requirements (22 total):**

1. ID list schema (Requirement 38)
2. Filter by ID (Requirement 39)
3. Filter by keyword `q` (Requirement 40)
4. Filter by geometry (Requirement 41)
   5-7. System filters: parent, procedure, foi (Requirements 42-44)
   8-9. System filters: observedProperty, controlledProperty (Requirements 45-46)
   10-12. Deployment filters: parent, system, foi (Requirements 47-49)
   13-14. Deployment filters: observedProperty, controlledProperty (Requirements 50-51)
   15-16. Procedure filters: observedProperty, controlledProperty (Requirements 52-53)
   17-19. Sampling Feature filters: foi, observedProperty, controlledProperty (Requirements 54-56)
   20-21. Property filters: baseProperty, objectType (Requirements 57-58)
5. Combined filters (logical AND) (Requirement 59)

**Query Parameters Enabled:**

- `id` - Filter by local ID(s)
- `uid` - Filter by unique identifier(s)
- `q` - Keyword search
- `bbox`, `geom` - Spatial filters
- `parent` - Parent resource filter
- `procedure` - Procedure filter (Systems)
- `foi` - Feature of interest filter
- `observedProperty` - Observed property filter
- `controlledProperty` - Controlled property filter
- `system` - System filter (Deployments)
- `baseProperty` - Base property filter (Properties)
- `objectType` - Object type filter (Properties)

**Key Capabilities:**

- Relationship-based filtering
- Transitive queries (baseProperty, foi)
- Multi-value filters (OR within parameter)
- Cross-parameter AND logic

**Client Library Impact:**

- All query methods gain extensive filter options
- Type-safe filter builders required
- Must handle comma-separated ID lists

---

### Part 1: A.10 Create/Replace/Delete

**Identifier:** `/conf/create-replace-delete`  
**Requirement Class:** `/req/create-replace-delete`  
**Prerequisites:** `/conf/api-common`, OGC API – Features Part 4

**Requirements (12 total):**
1-3. System CRUD operations (Requirements 60-62)
4-5. Deployment CRUD operations (Requirements 63-64) 6. Procedure CRUD operations (Requirement 65) 7. Sampling Feature CRUD operations (Requirement 66) 8. Property CRUD operations (Requirement 67)
9-12. Collection operations (Requirements 68-71)

**HTTP Methods Enabled:**

- POST - Create resources at canonical/nested endpoints
- PUT - Replace resources at canonical endpoint
- DELETE - Delete resources at canonical endpoint

**Endpoints Impacted:**

- `POST /systems`, `POST /systems/{parentId}/subsystems`
- `POST /deployments`, `POST /deployments/{parentId}/subdeployments`
- `POST /procedures`, `POST /samplingFeatures`
- `POST /systems/{sysId}/samplingFeatures`
- `POST /properties`
- `PUT /{resourceType}/{id}`
- `DELETE /{resourceType}/{id}`, `DELETE /{resourceType}/{id}?cascade=true`

**Special Behaviors:**

- Cascade delete for Systems/Deployments with nested resources
- Location header in 201 Created responses
- 409 Conflict for constraint violations

**Client Library Impact:**

- `client.{resource}.create(data)` - Available
- `client.{resource}.replace(id, data)` - Available
- `client.{resource}.delete(id, {cascade})` - Available
- Type-safe request body builders required

---

### Part 1: A.11 Update

**Identifier:** `/conf/update`  
**Requirement Class:** `/req/update`  
**Prerequisites:** `/conf/create-replace-delete`, OGC API – Features Part 4

**Requirements (5 total):**

1. System PATCH operations (Requirement 72)
2. Deployment PATCH operations (Requirement 73)
3. Procedure PATCH operations (Requirement 74)
4. Sampling Feature PATCH operations (Requirement 75)
5. Property PATCH operations (Requirement 76)

**HTTP Methods Enabled:**

- PATCH - Partial update using JSON Merge Patch (RFC 7396)

**Endpoints Impacted:**

- `PATCH /{resourceType}/{id}`
- `PATCH /collections/{id}/items/{itemId}`

**Key Capabilities:**

- Partial updates (only specified properties)
- JSON Merge Patch format (null = remove)
- Efficient for single-property updates

**Client Library Impact:**

- `client.{resource}.update(id, patch)` - Available
- Patch format: `{ propertyName: newValue }` or `{ propertyName: null }`

---

### Part 1: A.12 GeoJSON Format

**Identifier:** `/conf/geojson`  
**Requirement Class:** `/req/geojson`  
**Prerequisites:** `/conf/api-common`, OGC API – Features Part 1 GeoJSON

**Requirements (12 total):**
1-2. Media type for read/write operations (Requirements 77-78) 3. Link relation types with `ogc-rel:` prefix (Requirement 79) 4. Feature attribute mappings (Requirement 80)
5-6. System schema and mappings (Requirements 81-82)
7-8. Deployment schema and mappings (Requirements 83-84)
9-10. Procedure schema and mappings (Requirements 85-86)
11-12. Sampling Feature schema and mappings (Requirements 87-88)

**Media Types:**

- `application/geo+json` - GeoJSON format
- `application/json` - Generic JSON (for non-spatial)

**Supported Resources:**

- Systems (GeoJSON Feature with geometry)
- Deployments (GeoJSON Feature with spatial extent)
- Procedures (GeoJSON Feature with geometry = null)
- Sampling Features (GeoJSON Feature with geometry)

**Key Capabilities:**

- Spatial resource representation
- W3C SOSA/SSN property mappings
- Link relations with `ogc-rel:` prefix

**Client Library Impact:**

- Must parse/generate GeoJSON Feature format
- Must handle `@link` suffix for relationships
- Geometry types: Point, LineString, Polygon, etc.

---

### Part 1: A.13 SensorML Format

**Identifier:** `/conf/sensorml`  
**Requirement Class:** `/req/sensorml`  
**Prerequisites:** `/conf/api-common`, SensorML 3.0 JSON

**Requirements (11 total):**
1-2. Media type for read/write operations (Requirements 89-90) 3. Link relation types (Requirement 91) 4. Resource ID conventions (Requirement 92) 5. Feature attribute mappings (Requirement 93)
6-8. System schema, class selection, mappings (Requirements 94-96)
9-10. Deployment schema and mappings (Requirements 97-98)
11-13. Procedure schema, class selection, mappings (Requirements 99-101)
14-15. Property schema and mappings (Requirements 102-103)

**Media Types:**

- `application/sml+json` - SensorML 3.0 JSON format

**Supported Resources:**

- Systems (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess)
- Deployments (SensorML Deployment)
- Procedures (SimpleProcess, AggregateProcess)
- Properties (DerivedProperty)

**Key Capabilities:**

- Rich sensor/system descriptions
- Inputs/outputs/parameters modeling
- Characteristics and capabilities

**Client Library Impact:**

- Must parse/generate SensorML JSON format
- Must handle SensorML type selection (PhysicalSystem vs PhysicalComponent)
- Support for components array (nested systems)

---

### Part 2: A.1 Common

**Identifier:** `/conf/api-common`  
**Requirement Class:** `/req/api-common`  
**Prerequisite:** OGC API - Features Part 1: Core

**Requirements (2 total):**

1. Non-feature resources (Observations, Commands, etc. are not Features) (Requirement 1)
2. Resource collections with `itemType` property (Requirement 2)

**Key Capabilities:**

- Distinguishes Features (Part 1) from non-Features (Part 2)
- Collections use `itemType` instead of `featureType`

**Client Library Impact:**

- Must handle both Feature collections (`featureType`) and resource collections (`itemType`)
- Observations/Commands/etc. are NOT GeoJSON Features

---

### Part 2: A.2 Datastreams & Observations

**Identifier:** `/conf/datastream`  
**Requirement Class:** `/req/datastream`  
**Prerequisite:** Part 2 `/conf/api-common`

**Requirements (16 total):**
1-2. Sampling features / FOI references from datastream (Requirements 3-4) 3. DataStream canonical URL (Requirement 5)
4-5. DataStream resources endpoints (Requirements 6-7)
6-7. DataStream references from System/Deployment (Requirements 8-9) 8. DataStream collections (Requirement 10) 9. DataStream schema operation (Requirement 11) 10. Observation canonical URL (Requirement 12)
11-12. Observation resources endpoints (Requirements 13-14) 13. Observation references from DataStream (Requirement 15) 14. Observation collections (Requirement 16)

**Endpoints Required:**

- `/datastreams`, `/datastreams/{id}`
- `/observations`, `/observations/{id}`
- `/systems/{sysId}/datastreams`
- `/deployments/{depId}/datastreams` (optional)
- `/datastreams/{dsId}/observations`
- `/datastreams/{id}/schema?obsFormat={format}`

**Collections Required:**

- At least one collection with `itemType=DataStream`
- At least one collection with `itemType=Observation`

**Key Capabilities:**

- Observation data retrieval
- Real-time data streaming (if `live=true`)
- Schema-based validation
- Multi-property observations

**Client Library Impact:**

- `client.datastreams.list()` - Available
- `client.datastreams.get(id).observations.list()` - Available
- Must support pagination (limit up to 10000)
- Must handle various result types (scalar, vector, record, array)

---

### Part 2: A.3 Control Streams & Commands

**Identifier:** `/conf/controlstream`  
**Requirement Class:** `/req/controlstream`  
**Prerequisite:** Part 2 `/conf/api-common`

**Requirements (18 total):**
1-2. Sampling features / FOI references from control stream (Requirements 17-18) 3. ControlStream canonical URL (Requirement 19)
4-5. ControlStream resources endpoints (Requirements 20-21)
6-7. ControlStream references from System/Deployment (Requirements 22-23) 8. ControlStream collections (Requirement 24) 9. ControlStream schema operation (Requirement 25) 10. Command canonical URL (Requirement 26)
11-12. Command resources endpoints (Requirements 27-28) 13. Command references from ControlStream (Requirement 29) 14. Command collections (Requirement 30)
15-16. CommandStatus endpoints (Requirements 31-32)
17-18. CommandResult endpoints (Requirements 33-34)

**Endpoints Required:**

- `/controlstreams`, `/controlstreams/{id}`
- `/commands`, `/commands/{id}`
- `/systems/{sysId}/controlstreams`
- `/deployments/{depId}/controlstreams` (optional)
- `/controlstreams/{csId}/commands`
- `/commands/{cmdId}/status`
- `/commands/{cmdId}/result`
- `/controlstreams/{id}/schema?cmdFormat={format}`

**Collections Required:**

- At least one collection with `itemType=ControlStream`
- At least one collection with `itemType=Command`

**Key Capabilities:**

- Command/tasking interface
- Asynchronous command processing
- Status tracking and result retrieval
- Schema-based validation

**Client Library Impact:**

- `client.controlstreams.list()` - Available
- `client.commands.get(id).status.list()` - Available
- `client.commands.get(id).result.get()` - Available
- Must handle async command patterns (polling status)

---

### Part 2: A.4 Command Feasibility

**Identifier:** `/conf/feasibility`  
**Requirement Class:** `/req/feasibility`  
**Prerequisite:** Part 2 `/conf/controlstream`

**Requirements (5 total):**

1. Feasibility canonical URL (Requirement 35)
2. Feasibility references from ControlStream (Requirement 36)
3. Feasibility status endpoint (Requirement 37)
4. Feasibility result endpoint (Requirement 38)
5. Feasibility collections (Requirement 39)

**Endpoints Required:**

- `/feasibility`, `/feasibility/{id}`
- `/controlstreams/{csId}/feasibility`
- `/feasibility/{feasId}/status`
- `/feasibility/{feasId}/result`

**Collections Required:**

- At least one collection with `itemType=Feasibility`

**Key Capabilities:**

- Pre-task validation
- Feasibility analysis without execution
- Alternative suggestion

**Client Library Impact:**

- `client.controlstreams.get(id).feasibility.create(params)` - Available
- `client.feasibility.get(id).status.list()` - Available
- `client.feasibility.get(id).result.get()` - Available

---

### Part 2: A.5 System Events

**Identifier:** `/conf/system-event`  
**Requirement Class:** `/req/system-event`  
**Prerequisites:** Part 2 `/conf/api-common`, Part 1 `/conf/system`

**Requirements (5 total):**

1. SystemEvent canonical URL (Requirement 40)
2. SystemEvent resources endpoints (Requirement 41)
3. Canonical SystemEvent resources endpoint (Requirement 42)
4. SystemEvent references from System (Requirement 43)
5. SystemEvent collections (Requirement 44)

**Endpoints Required:**

- `/systemEvents`, `/systemEvents/{id}`
- `/systems/{sysId}/events`

**Collections Required:**

- At least one collection with `itemType=SystemEvent`

**Key Capabilities:**

- System lifecycle event tracking
- Recalibration, maintenance, configuration changes
- Event history

**Client Library Impact:**

- `client.systemEvents.list()` - Available
- `client.systems.get(id).events.list()` - Available

---

### Part 2: A.6 Advanced Filtering

**Identifier:** `/conf/advanced-filtering`  
**Requirement Class:** `/req/advanced-filtering`  
**Prerequisite:** Part 1 `/conf/advanced-filtering`

**Requirements (17 total):**
1-4. DataStream filters (Requirements 45-48)
5-8. Observation filters (Requirements 49-52)
9-12. ControlStream filters (Requirements 53-56)
13-15. Command filters (Requirements 57-59)
16-17. CommandStatus filters (Requirements 60-61) 18. SystemEvent filters (Requirement 62)

**Query Parameters Enabled:**

- **DataStreams:** `phenomenonTime`, `resultTime`, `observedProperty`, `foi`
- **Observations:** `phenomenonTime`, `resultTime`, `foi`, `resultTime=latest`
- **ControlStreams:** `executionTime`, `issueTime`, `controlledProperty`, `foi`
- **Commands:** `executionTime`, `issueTime`, `foi`
- **CommandStatus:** `statusCode` (PENDING, ACCEPTED, EXECUTING, COMPLETED, FAILED, CANCELED)
- **SystemEvents:** `type`

**Key Capabilities:**

- Temporal filtering (phenomenonTime, resultTime, executionTime, issueTime)
- Latest observation queries (`resultTime=latest`)
- Status-based filtering
- Relationship-based filtering

**Client Library Impact:**

- All Part 2 query methods gain temporal filters
- Must handle ISO 8601 intervals
- Special value `latest` for most recent data

---

### Part 2: A.7 Create/Replace/Delete

**Identifier:** `/conf/create-replace-delete`  
**Requirement Class:** `/req/create-replace-delete`  
**Prerequisite:** OGC API - Features Part 4

**Requirements (16 total):**
1-3. DataStream operations and constraints (Requirements 63-65)
4-5. Observation operations and constraints (Requirements 66-67)
6-8. ControlStream operations and constraints (Requirements 68-70)
9-10. Command operations and constraints (Requirements 71-72)
11-12. CommandStatus and CommandResult operations (Requirements 73-74)
13-15. Feasibility operations (Requirements 75-77) 16. SystemEvent operations (Requirement 78)

**HTTP Methods Enabled:**

- POST - Create resources (observations, commands, etc.)
- PUT - Replace resources
- DELETE - Delete resources (with cascade option)

**Schema Constraints:**

- DataStream schema changes rejected if observations exist (409)
- ControlStream schema changes rejected if commands exist (409)
- Observation validation against DataStream schema (400 if invalid)
- Command validation against ControlStream schema (400 if invalid)

**Cascade Delete:**

- DataStream cascade deletes all observations
- ControlStream cascade deletes all commands (and status/results)

**Client Library Impact:**

- `client.observations.create(datastreamId, data)` - Available
- `client.commands.create(controlstreamId, data)` - Available
- `client.datastreams.delete(id, {cascade: true})` - Available
- Must handle schema validation errors (400)
- Must handle constraint violation errors (409)

---

### Part 2: A.8 Update

**Identifier:** `/conf/update`  
**Requirement Class:** `/req/update`  
**Prerequisites:** Part 2 `/conf/create-replace-delete`, OGC API - Features Part 4

**Requirements (14 total):**
1-2. DataStream update and constraints (Requirements 79-80)
3-4. Observation update and constraints (Requirements 81-82)
5-6. ControlStream update and constraints (Requirements 83-84)
7-8. Command update and constraints (Requirements 85-86)
9-10. CommandStatus and CommandResult update (Requirements 87-88)
11-13. Feasibility update (Requirements 89-91) 14. SystemEvent update (Requirement 92)

**HTTP Methods Enabled:**

- PATCH - Partial update using JSON Merge Patch (RFC 7396)

**Constraints:**

- Same schema constraints as Create/Replace/Delete

**Client Library Impact:**

- `client.datastreams.update(id, patch)` - Available
- `client.observations.update(id, patch)` - Available

---

### Part 2: A.9-A.12 Encoding Conformance Classes

**A.9: JSON Encoding** (`/conf/json`)

- **Mandatory** for all Part 2 servers
- Requirements 93-106: JSON schemas for all resource types
- Media type: `application/json`

**A.10: SWE Common JSON Encoding** (`/conf/swecommon-json`)

- **Optional**
- Requirements 107-114: SWE Common JSON for observations/commands
- Media type: `application/swe+json`
- Binary-efficient structured data

**A.11: SWE Common Text Encoding** (`/conf/swecommon-text`)

- **Optional**
- Requirements 115-122: SWE Common Text (CSV/DSV) for observations/commands
- Media type: `application/swe+text`
- Human-readable tabular format

**A.12: SWE Common Binary Encoding** (`/conf/swecommon-binary`)

- **Optional**
- Requirements 123-130: SWE Common Binary for observations/commands
- Media type: `application/swe+binary`
- Maximum efficiency for large datasets

**Client Library Impact:**

- Must support JSON encoding (mandatory)
- Should support SWE Common encodings if available
- Format negotiation via `f` parameter or `Accept` header

---

## Conformance Detection

### Conformance Endpoint

**URL:** `{api_root}/conformance`  
**Method:** GET  
**Response Format:** JSON

**Example Response:**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/subsystem",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/advanced-filtering",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/update",
    "http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/datastream",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/advanced-filtering",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/swecommon-json"
  ]
}
```

### Conformance URIs

**Part 1 Conformance URI Base:**

```
http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/
```

**Part 2 Conformance URI Base:**

```
http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/
```

**Full Conformance URIs:**

- Part 1 Common: `.../ogcapi-connected-systems-1/1.0/conf/api-common`
- Part 1 System: `.../ogcapi-connected-systems-1/1.0/conf/system`
- Part 1 Subsystem: `.../ogcapi-connected-systems-1/1.0/conf/subsystem`
- Part 1 Deployment: `.../ogcapi-connected-systems-1/1.0/conf/deployment`
- Part 1 Subdeployment: `.../ogcapi-connected-systems-1/1.0/conf/subdeployment`
- Part 1 Procedure: `.../ogcapi-connected-systems-1/1.0/conf/procedure`
- Part 1 Sampling Features: `.../ogcapi-connected-systems-1/1.0/conf/sf`
- Part 1 Property: `.../ogcapi-connected-systems-1/1.0/conf/property`
- Part 1 Advanced Filtering: `.../ogcapi-connected-systems-1/1.0/conf/advanced-filtering`
- Part 1 Create/Replace/Delete: `.../ogcapi-connected-systems-1/1.0/conf/create-replace-delete`
- Part 1 Update: `.../ogcapi-connected-systems-1/1.0/conf/update`
- Part 1 GeoJSON: `.../ogcapi-connected-systems-1/1.0/conf/geojson`
- Part 1 SensorML: `.../ogcapi-connected-systems-1/1.0/conf/sensorml`
- Part 2 Common: `.../ogcapi-connected-systems-2/1.0/conf/api-common`
- Part 2 DataStreams: `.../ogcapi-connected-systems-2/1.0/conf/datastream`
- Part 2 ControlStreams: `.../ogcapi-connected-systems-2/1.0/conf/controlstream`
- Part 2 Feasibility: `.../ogcapi-connected-systems-2/1.0/conf/feasibility`
- Part 2 System Events: `.../ogcapi-connected-systems-2/1.0/conf/system-event`
- Part 2 Advanced Filtering: `.../ogcapi-connected-systems-2/1.0/conf/advanced-filtering`
- Part 2 Create/Replace/Delete: `.../ogcapi-connected-systems-2/1.0/conf/create-replace-delete`
- Part 2 Update: `.../ogcapi-connected-systems-2/1.0/conf/update`
- Part 2 JSON: `.../ogcapi-connected-systems-2/1.0/conf/json`
- Part 2 SWE Common JSON: `.../ogcapi-connected-systems-2/1.0/conf/swecommon-json`
- Part 2 SWE Common Text: `.../ogcapi-connected-systems-2/1.0/conf/swecommon-text`
- Part 2 SWE Common Binary: `.../ogcapi-connected-systems-2/1.0/conf/swecommon-binary`

---

## Capability Discovery at Collection Level

### Collection Metadata

**Endpoint:** `GET /collections`  
**Response:** Array of collection metadata

**Example Collection:**

```json
{
  "id": "weather-systems",
  "title": "Weather Monitoring Systems",
  "description": "Collection of weather monitoring systems in California",
  "itemType": "http://www.w3.org/ns/sosa/System",
  "featureType": "http://www.w3.org/ns/sosa/System",
  "extent": {
    "spatial": {
      "bbox": [[-124.48, 32.53, -114.13, 42.01]],
      "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
    },
    "temporal": {
      "interval": [["2020-01-01T00:00:00Z", null]],
      "trs": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"
    }
  },
  "links": [
    {
      "rel": "items",
      "href": "https://api.example.org/collections/weather-systems/items",
      "type": "application/geo+json"
    },
    {
      "rel": "self",
      "href": "https://api.example.org/collections/weather-systems",
      "type": "application/json"
    }
  ]
}
```

**Key Properties:**

- `itemType` or `featureType` - Resource type contained in collection
- `extent` - Spatial and temporal extent
- `crs` - Supported coordinate reference systems
- `links` - Related resources (items, schema, etc.)

### Per-Collection Capabilities

**Varies by Collection:**

- Supported formats (`links` with different media types)
- CRS support (spatial collections)
- Temporal extent (temporal availability)
- Read-only vs writable (presence of POST/PUT/DELETE links)

**Client Detection:**

- Check for `rel=create` link (POST support)
- Check for format alternatives in `links` array
- Check `crs` array for supported coordinate systems

---

## Client Library Conformance Checking

### Initialization Pattern

```typescript
class CSAPIClient {
  private conformance: Set<string> = new Set();
  private capabilities: ServerCapabilities;

  async initialize(baseUrl: string) {
    // Fetch conformance
    const response = await fetch(`${baseUrl}/conformance`);
    const data = await response.json();
    this.conformance = new Set(data.conformsTo);

    // Detect capabilities
    this.capabilities = this.detectCapabilities();

    // Configure client based on capabilities
    this.configureResources();
  }

  private detectCapabilities(): ServerCapabilities {
    return {
      // Part 1
      hasSystems: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/system'
      ),
      hasSubsystems: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/subsystem'
      ),
      hasDeployments: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/deployment'
      ),
      hasSubdeployments: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/subdeployment'
      ),
      hasProcedures: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/procedure'
      ),
      hasSamplingFeatures: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/sf'
      ),
      hasProperties: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/property'
      ),
      hasAdvancedFiltering: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/advanced-filtering'
      ),
      hasCRUD: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/create-replace-delete'
      ),
      hasUpdate: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/update'
      ),
      hasGeoJSON: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/geojson'
      ),
      hasSensorML: this.hasConformance(
        'ogcapi-connected-systems-1/1.0/conf/sensorml'
      ),

      // Part 2
      hasDataStreams: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/datastream'
      ),
      hasControlStreams: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/controlstream'
      ),
      hasFeasibility: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/feasibility'
      ),
      hasSystemEvents: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/system-event'
      ),
      hasAdvancedFilteringPart2: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/advanced-filtering'
      ),
      hasCRUDPart2: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/create-replace-delete'
      ),
      hasUpdatePart2: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/update'
      ),
      hasSWEJSON: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/swecommon-json'
      ),
      hasSWEText: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/swecommon-text'
      ),
      hasSWEBinary: this.hasConformance(
        'ogcapi-connected-systems-2/1.0/conf/swecommon-binary'
      ),
    };
  }

  private hasConformance(uri: string): boolean {
    // Match full URI or partial path
    return Array.from(this.conformance).some((c) => c.includes(uri));
  }

  private configureResources() {
    // Enable/disable resource interfaces based on conformance
    if (this.capabilities.hasSystems) {
      this.systems = new SystemsResource(this);
    }
    if (this.capabilities.hasDataStreams) {
      this.datastreams = new DataStreamsResource(this);
    }
    // etc.
  }
}
```

### Capability-Based Method Availability

```typescript
class SystemsResource {
  constructor(private client: CSAPIClient) {}

  async list(options?: QueryOptions): Promise<SystemCollection> {
    // Always available if /conf/system present
    return this.client.get('/systems', options);
  }

  async create(data: SystemInput): Promise<System> {
    if (!this.client.capabilities.hasCRUD) {
      throw new Error(
        'Server does not support create operations (missing /conf/create-replace-delete)'
      );
    }
    return this.client.post('/systems', data);
  }

  async update(id: string, patch: Partial<SystemInput>): Promise<void> {
    if (!this.client.capabilities.hasUpdate) {
      throw new Error(
        'Server does not support update operations (missing /conf/update)'
      );
    }
    return this.client.patch(`/systems/${id}`, patch);
  }

  subsystems(id: string): SubsystemsResource | null {
    if (!this.client.capabilities.hasSubsystems) {
      return null; // or throw error
    }
    return new SubsystemsResource(this.client, id);
  }
}
```

### Graceful Degradation

```typescript
// Try advanced filtering, fall back to client-side filtering
async function findSystemsByProperty(
  client: CSAPIClient,
  observedProperty: string
): Promise<System[]> {
  if (client.capabilities.hasAdvancedFiltering) {
    // Server-side filtering
    return client.systems.list({ observedProperty });
  } else {
    // Client-side filtering (less efficient)
    const allSystems = await client.systems.list();
    return allSystems.features.filter((system) =>
      system.properties.observedProperties?.includes(observedProperty)
    );
  }
}

// Try PATCH, fall back to PUT
async function updateSystem(
  client: CSAPIClient,
  id: string,
  changes: Partial<SystemInput>
): Promise<void> {
  if (client.capabilities.hasUpdate) {
    // Efficient partial update
    await client.systems.update(id, changes);
  } else if (client.capabilities.hasCRUD) {
    // Full replacement (less efficient)
    const existing = await client.systems.get(id);
    await client.systems.replace(id, { ...existing, ...changes });
  } else {
    throw new Error('Server does not support update operations');
  }
}
```

---

## Summary

This section documents conformance and capability detection for CSAPI client library:

**Conformance Classes:**

- Part 1: 13 conformance classes (Common, 5 resource types, 2 hierarchical, Advanced Filtering, 2 CRUD, 2 encodings)
- Part 2: 12 conformance classes (Common, 2 dynamic data types, Feasibility, System Events, Advanced Filtering, 2 CRUD, 4 encodings)
- No mandatory core class - servers choose resource types and features

**Minimum Configurations:**

- Absolute minimum: Common + 1 resource type + 1 encoding
- Read-only: Just GET operations
- Transactional: Add Create/Replace/Delete and optionally Update
- Dynamic data: Add DataStreams or ControlStreams from Part 2

**Conformance Detection:**

- `/conformance` endpoint lists all implemented conformance classes
- URI pattern: `http://www.opengis.net/spec/ogcapi-connected-systems-{1|2}/1.0/conf/{class}`
- Client fetches at initialization and caches conformance set

**Capability Discovery:**

- Server capabilities detected from conformance URIs
- Collection-level capabilities detected from metadata
- Client configures available methods based on capabilities

**Graceful Degradation:**

- Check conformance before calling methods
- Fall back to less efficient alternatives when possible
- Throw clear errors when features unavailable

See Section 5 (CRUD Operations) for write operation requirements and Section 4 (Query Parameters) for filtering details.
